"""Batch processor for processing all PDFs in the references folder."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from .pdf_processor import PDFProcessor

console = Console()


class BatchProcessor:
    """Process all PDFs in a folder and build consolidated indices."""
    
    def __init__(
        self,
        pdfs_folder: Optional[Path] = None,
        output_folder: Optional[Path] = None,
    ):
        """Initialize the batch processor.
        
        Args:
            pdfs_folder: Path to folder containing PDFs. Defaults to data/references/pdfs.
            output_folder: Path to output folder. Defaults to data/processed.
        """
        base_path = Path(__file__).parent.parent.parent.parent
        
        self.pdfs_folder = pdfs_folder or base_path / "data" / "references" / "pdfs"
        self.output_folder = output_folder or base_path / "data" / "processed"
        
        # Track processing status
        self.status_file = self.output_folder / "processing_status.json"
        self.status = self._load_status()
        
        # Initialize PDF processor
        self.pdf_processor = PDFProcessor(output_dir=self.output_folder)
    
    def _load_status(self) -> dict:
        """Load processing status from file."""
        if self.status_file.exists():
            with open(self.status_file, "r", encoding="utf-8") as f:
                status = json.load(f)
        else:
            status = {
                "processed": {},  # filename -> {paper_id, timestamp, success, error}
                "last_run": None,
                "total_processed": 0,
                "total_failed": 0,
            }
        
        # Sync with existing processed papers (detect already processed folders)
        self._sync_status_with_existing_papers(status)
        
        return status
    
    def _sync_status_with_existing_papers(self, status: dict) -> None:
        """Sync status with already processed paper folders.
        
        This detects papers that were processed before the status file existed.
        """
        papers_dir = self.output_folder / "papers"
        if not papers_dir.exists():
            return
        
        # Get all processed paper folders
        for paper_folder in papers_dir.iterdir():
            if not paper_folder.is_dir():
                continue
            
            metadata_file = paper_folder / "metadata.json"
            if not metadata_file.exists():
                continue
            
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                
                # Get the source filename
                source_file = metadata.get("source_file", "")
                if not source_file:
                    continue
                
                filename = Path(source_file).name
                
                # If not in status, add it
                if filename not in status["processed"]:
                    # Count ideas, claims, references
                    ideas_file = paper_folder / "ideas.jsonl"
                    claims_file = paper_folder / "claims.jsonl"
                    refs_file = paper_folder / "references.jsonl"
                    
                    ideas_count = sum(1 for _ in open(ideas_file)) if ideas_file.exists() else 0
                    claims_count = sum(1 for _ in open(claims_file)) if claims_file.exists() else 0
                    refs_count = sum(1 for _ in open(refs_file)) if refs_file.exists() else 0
                    
                    status["processed"][filename] = {
                        "paper_id": metadata.get("id", paper_folder.name),
                        "title": metadata.get("title", "Unknown"),
                        "timestamp": metadata.get("processed_at", "unknown"),
                        "success": True,
                        "ideas_count": ideas_count,
                        "claims_count": claims_count,
                        "references_count": refs_count,
                    }
                    
            except Exception:
                # Skip papers with invalid metadata
                continue
        
        # Update totals
        status["total_processed"] = sum(
            1 for v in status["processed"].values() if v.get("success")
        )
        status["total_failed"] = sum(
            1 for v in status["processed"].values() if not v.get("success")
        )
    
    def _save_status(self) -> None:
        """Save processing status to file."""
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.status_file, "w", encoding="utf-8") as f:
            json.dump(self.status, f, indent=2, ensure_ascii=False)
    
    def get_pdfs_to_process(self, force_reprocess: bool = False) -> list[Path]:
        """Get list of PDFs that need processing.
        
        Args:
            force_reprocess: If True, process all PDFs even if already processed.
            
        Returns:
            List of PDF paths to process.
        """
        all_pdfs = list(self.pdfs_folder.glob("*.pdf"))
        
        if force_reprocess:
            return all_pdfs
        
        # Filter out already processed PDFs
        to_process = []
        for pdf_path in all_pdfs:
            filename = pdf_path.name
            if filename not in self.status["processed"]:
                to_process.append(pdf_path)
            elif not self.status["processed"][filename].get("success", False):
                # Retry failed PDFs
                to_process.append(pdf_path)
        
        return to_process
    
    def process_all(
        self,
        force_reprocess: bool = False,
        max_pdfs: Optional[int] = None,
        build_embeddings: bool = True,
    ) -> dict:
        """Process all PDFs in the folder.
        
        Args:
            force_reprocess: If True, reprocess all PDFs.
            max_pdfs: Maximum number of PDFs to process (for testing).
            build_embeddings: If True, build embedding indices after processing.
            
        Returns:
            Summary of processing results.
        """
        console.print(Panel(
            "[bold blue]📚 Batch PDF Processor[/bold blue]\n"
            f"Source: {self.pdfs_folder}\n"
            f"Output: {self.output_folder}",
            title="TheAIWriter",
            border_style="blue"
        ))
        
        # Get PDFs to process
        pdfs_to_process = self.get_pdfs_to_process(force_reprocess)
        
        if max_pdfs:
            pdfs_to_process = pdfs_to_process[:max_pdfs]
        
        total_pdfs = len(list(self.pdfs_folder.glob("*.pdf")))
        already_processed = total_pdfs - len(pdfs_to_process)
        
        console.print(f"\n📊 Found {total_pdfs} PDFs total")
        console.print(f"   ✓ Already processed: {already_processed}")
        console.print(f"   → To process: {len(pdfs_to_process)}")
        
        if not pdfs_to_process:
            console.print("\n[green]✓ All PDFs already processed![/green]")
            if build_embeddings:
                self._build_embeddings()
            return self._get_summary()
        
        # Process each PDF
        results = {"success": 0, "failed": 0, "errors": []}
        
        console.print(f"\n[bold cyan]🔄 Processing {len(pdfs_to_process)} PDFs...[/bold cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing PDFs...", total=len(pdfs_to_process))
            
            for pdf_path in pdfs_to_process:
                progress.update(task, description=f"Processing: {pdf_path.name[:50]}...")
                
                try:
                    # Process the PDF
                    processed_paper = self.pdf_processor.process_pdf(pdf_path)
                    
                    if processed_paper:
                        # Update status
                        self.status["processed"][pdf_path.name] = {
                            "paper_id": processed_paper.metadata.id,
                            "title": processed_paper.metadata.title,
                            "timestamp": datetime.now().isoformat(),
                            "success": True,
                            "ideas_count": len(processed_paper.ideas),
                            "claims_count": len(processed_paper.claims),
                            "references_count": len(processed_paper.references),
                        }
                        results["success"] += 1
                        console.print(f"  [green]✓[/green] {pdf_path.name[:60]}")
                    else:
                        raise ValueError("Processing returned None")
                        
                except Exception as e:
                    error_msg = str(e)
                    self.status["processed"][pdf_path.name] = {
                        "timestamp": datetime.now().isoformat(),
                        "success": False,
                        "error": error_msg,
                    }
                    results["failed"] += 1
                    results["errors"].append({"file": pdf_path.name, "error": error_msg})
                    console.print(f"  [red]✗[/red] {pdf_path.name[:60]}: {error_msg[:50]}")
                
                # Save status after each PDF
                self.status["total_processed"] = sum(
                    1 for v in self.status["processed"].values() if v.get("success")
                )
                self.status["total_failed"] = sum(
                    1 for v in self.status["processed"].values() if not v.get("success")
                )
                self.status["last_run"] = datetime.now().isoformat()
                self._save_status()
                
                progress.advance(task)
        
        # Build embeddings if requested
        if build_embeddings and results["success"] > 0:
            self._build_embeddings()
        
        # Show summary
        summary = self._get_summary()
        self._print_summary(summary)
        
        return summary
    
    def _build_embeddings(self) -> None:
        """Build embedding indices from processed data."""
        console.print("\n[bold cyan]🧠 Building Embedding Indices...[/bold cyan]")
        
        try:
            # Import here to avoid circular imports
            from ..embeddings.rag_system import RAGSystem
            
            rag = RAGSystem(indices_folder=self.output_folder / "indices")
            rag.build_indices(force_rebuild=True)
            
            console.print("[green]✓ Embedding indices built successfully![/green]")
            
        except Exception as e:
            console.print(f"[red]✗ Failed to build embeddings: {e}[/red]")
    
    def _get_summary(self) -> dict:
        """Get processing summary."""
        total_ideas = 0
        total_claims = 0
        total_refs = 0
        
        for info in self.status["processed"].values():
            if info.get("success"):
                total_ideas += info.get("ideas_count", 0)
                total_claims += info.get("claims_count", 0)
                total_refs += info.get("references_count", 0)
        
        return {
            "total_pdfs": len(list(self.pdfs_folder.glob("*.pdf"))),
            "processed_successfully": self.status["total_processed"],
            "failed": self.status["total_failed"],
            "total_ideas": total_ideas,
            "total_claims": total_claims,
            "total_references": total_refs,
            "last_run": self.status["last_run"],
        }
    
    def _print_summary(self, summary: dict) -> None:
        """Print processing summary."""
        table = Table(title="Processing Summary", border_style="green")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        table.add_row("Total PDFs", str(summary["total_pdfs"]))
        table.add_row("Processed Successfully", str(summary["processed_successfully"]))
        table.add_row("Failed", str(summary["failed"]))
        table.add_row("─" * 20, "─" * 10)
        table.add_row("Total Ideas", str(summary["total_ideas"]))
        table.add_row("Total Claims", str(summary["total_claims"]))
        table.add_row("Total References", str(summary["total_references"]))
        
        console.print("\n")
        console.print(table)
    
    def get_processing_report(self) -> None:
        """Print a detailed processing report."""
        console.print(Panel(
            "[bold blue]📊 Processing Report[/bold blue]",
            border_style="blue"
        ))
        
        # Summary table
        summary = self._get_summary()
        self._print_summary(summary)
        
        # Details by paper
        if self.status["processed"]:
            console.print("\n[bold]Processed Papers:[/bold]\n")
            
            table = Table(show_header=True)
            table.add_column("#", style="dim", width=4)
            table.add_column("Title", style="cyan", max_width=50)
            table.add_column("Ideas", justify="right")
            table.add_column("Claims", justify="right")
            table.add_column("Refs", justify="right")
            table.add_column("Status", justify="center")
            
            for i, (filename, info) in enumerate(self.status["processed"].items(), 1):
                if info.get("success"):
                    title = info.get("title", filename)[:50]
                    status = "[green]✓[/green]"
                    table.add_row(
                        str(i),
                        title,
                        str(info.get("ideas_count", 0)),
                        str(info.get("claims_count", 0)),
                        str(info.get("references_count", 0)),
                        status,
                    )
                else:
                    table.add_row(
                        str(i),
                        filename[:50],
                        "-",
                        "-",
                        "-",
                        "[red]✗[/red]",
                    )
            
            console.print(table)


def main():
    """Main entry point for batch processing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch process PDFs for TheAIWriter")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing of all PDFs",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        help="Maximum number of PDFs to process",
    )
    parser.add_argument(
        "--no-embeddings",
        action="store_true",
        help="Skip building embedding indices",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Show processing report only",
    )
    
    args = parser.parse_args()
    
    processor = BatchProcessor()
    
    if args.report:
        processor.get_processing_report()
    else:
        processor.process_all(
            force_reprocess=args.force,
            max_pdfs=args.max,
            build_embeddings=not args.no_embeddings,
        )


if __name__ == "__main__":
    main()
