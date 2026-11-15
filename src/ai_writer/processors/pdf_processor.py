"""Main PDF processor for extracting structured data from academic papers."""

import json
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ai_writer.processors.extraction_agent import PDFExtractionAgent
from ai_writer.processors.models import (
    Claim,
    Idea,
    PaperMetadata,
    ProcessedPaper,
    SectionData,
)
from ai_writer.processors.quotes import QuoteChecker
from ai_writer.readers.pdf_reader import PDFReader
from config.settings import settings

console = Console()

PROCESSING_METHOD = 2  # recorded in metadata.json: one call per segment, verbatim quotes
EVIDENCE_TYPES = ("experiment", "data", "observation", "citation")


class PDFProcessor:
    """Process PDF papers to extract structured data for RAG."""

    def __init__(
        self,
        output_dir: Path | str | None = None,
    ) -> None:
        """Initialize the processor.
        
        Args:
            output_dir: Directory for processed output. Defaults to data/processed.
        """
        self.pdf_reader = PDFReader()
        self.extraction_agent = PDFExtractionAgent()
        
        # Setup output directories
        self.output_dir = Path(output_dir) if output_dir else settings.paths.processed_dir
        self.papers_dir = self.output_dir / "papers"
        self.indices_dir = self.output_dir / "indices"
        
        # Ensure directories exist
        self.papers_dir.mkdir(parents=True, exist_ok=True)
        self.indices_dir.mkdir(parents=True, exist_ok=True)

    def process_pdf(
        self,
        pdf_path: Path | str,
        skip_if_exists: bool = True,
    ) -> ProcessedPaper:
        """Process a single PDF and extract all structured data.
        
        Args:
            pdf_path: Path to the PDF file.
            skip_if_exists: Skip processing if output already exists.
            
        Returns:
            ProcessedPaper with all extracted data.

        Raises:
            ExtractionError: If the model's answer for a segment stays unreadable.
        """
        pdf_path = Path(pdf_path)
        started = time.monotonic()
        calls_before = self.extraction_agent.llm.usage.calls
        console.print(Panel(
            f"[bold]Processing: {pdf_path.name}[/bold]",
            title="📄 PDF Processor",
            border_style="blue",
        ))

        # Read PDF text
        console.print("[cyan]📖 Extracting text from PDF...[/cyan]")
        full_text = self.pdf_reader.read(pdf_path)
        pdf_metadata = self.pdf_reader.get_metadata(pdf_path)
        
        # Extract metadata
        console.print("[cyan]🔍 Extracting metadata...[/cyan]")
        metadata_dict = self.extraction_agent.extract_metadata(
            full_text[:10000],
            pdf_path.stem,
        )
        
        metadata = PaperMetadata(
            title=metadata_dict.get("title", pdf_path.stem),
            authors=metadata_dict.get("authors", []),
            year=metadata_dict.get("year"),
            doi=metadata_dict.get("doi"),
            venue=metadata_dict.get("venue"),
            source_file=str(pdf_path),
            total_pages=pdf_metadata.get("page_count", 0),
        )
        
        console.print(f"  [green]✓ Title:[/green] {metadata.title}")
        console.print(f"  [green]✓ Authors:[/green] {', '.join(metadata.authors[:3])}{'...' if len(metadata.authors) > 3 else ''}")
        console.print(f"  [green]✓ Year:[/green] {metadata.year}")

        # Cut the paper into segments
        console.print("[cyan]📑 Identifying sections...[/cyan]")
        sections = [
            SectionData(
                paper_id=metadata.paper_id,
                section_name=sec_data["section_name"],
                section_number=sec_data["section_number"],
                content=sec_data["content"],
                word_count=len(sec_data["content"].split()),
            )
            for sec_data in self.extraction_agent.extract_sections(full_text)
        ]
        metadata.sections_found = [section.section_name for section in sections]
        console.print(f"  [green]✓ {len(sections)} segments[/green]")

        # One call per segment returns its ideas and its claims
        checker = QuoteChecker(self.extraction_agent.clean_text(full_text))
        all_ideas: list[Idea] = []
        all_claims: list[Claim] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing sections...", total=len(sections))

            for section in sections:
                progress.update(task, description=f"[cyan]Ideas and claims: {section.section_name}[/cyan]")

                ideas, claims = self.extraction_agent.extract_from_section(
                    section_name=section.section_name,
                    section_content=section.content,
                    paper_title=metadata.title,
                    authors=metadata.authors,
                    year=metadata.year,
                    paper_id=metadata.paper_id,
                )
                self._finalize_items(ideas, claims, checker)
                all_ideas.extend(ideas)
                all_claims.extend(claims)
                progress.advance(task)

        metadata.procesado = {
            "metodo": PROCESSING_METHOD,
            "llamadas": self.extraction_agent.llm.usage.calls - calls_before,
            "segundos": round(time.monotonic() - started, 1),
            "tramos": len(sections),
            "motor": settings.ai.llm_backend,
            "modelo": self.extraction_agent.model,
        }

        # Create processed paper
        processed = ProcessedPaper(
            metadata=metadata,
            sections=sections,
            ideas=all_ideas,
            claims=all_claims,
        )

        # Save outputs
        self._save_processed_paper(processed)

        console.print(Panel(
            f"[bold green]✓ Processing complete![/bold green]\n\n"
            f"Segments: {len(sections)}\n"
            f"Ideas: {len(all_ideas)} ({len(processed.usable_ideas)} with a verified quote)\n"
            f"Claims: {len(all_claims)} ({len(processed.usable_claims)} with a verified quote)",
            title="✅ Done",
            border_style="green",
        ))
        
        return processed

    @staticmethod
    def _finalize_items(ideas: list[Idea], claims: list[Claim], checker: QuoteChecker) -> None:
        """Check each quote against the paper and set the derived claim fields."""
        for idea in ideas:
            idea.quote_verified = checker.has(idea.quote)
        for claim in claims:
            evidence_type = claim.evidence_type.strip().lower()
            claim.evidence_type = evidence_type if evidence_type in EVIDENCE_TYPES else "observation"
            claim.origin = "citado" if claim.evidence_type == "citation" else "propio"
            claim.quote_verified = checker.has(claim.quote)

    def _save_processed_paper(self, paper: ProcessedPaper) -> None:
        """Save processed paper data to disk.
        
        Args:
            paper: The processed paper data.
        """
        paper_id = paper.metadata.paper_id
        paper_dir = self.papers_dir / paper_id
        paper_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        with open(paper_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(paper.metadata.model_dump(), f, indent=2, ensure_ascii=False)
        
        # Save sections
        sections_dir = paper_dir / "sections"
        sections_dir.mkdir(exist_ok=True)
        for section in paper.sections:
            safe_name = f"{section.section_number:02d}_{self._safe_filename(section.section_name)}.json"
            with open(sections_dir / safe_name, "w", encoding="utf-8") as f:
                json.dump(section.model_dump(), f, indent=2, ensure_ascii=False)
        
        # Save ideas as JSONL
        with open(paper_dir / "ideas.jsonl", "w", encoding="utf-8") as f:
            for idea in paper.ideas:
                f.write(json.dumps(idea.model_dump(), ensure_ascii=False) + "\n")
        
        # Save claims as JSONL
        with open(paper_dir / "claims.jsonl", "w", encoding="utf-8") as f:
            for claim in paper.claims:
                f.write(json.dumps(claim.model_dump(), ensure_ascii=False) + "\n")
        
        # Append to global indices: items whose quote was not found stay in the paper's folder
        self._append_to_global_index(self.indices_dir / "all_ideas.jsonl", paper.usable_ideas)
        self._append_to_global_index(self.indices_dir / "all_claims.jsonl", paper.usable_claims)
        
        console.print(f"  [dim]💾 Saved to: {paper_dir}[/dim]")

    def _append_to_global_index(
        self,
        index_path: Path,
        items: list,
    ) -> None:
        """Append items to a global JSONL index.
        
        Args:
            index_path: Path to the index file.
            items: List of Pydantic models to append.
        """
        with open(index_path, "a", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item.model_dump(), ensure_ascii=False) + "\n")

    def _safe_filename(self, name: str) -> str:
        """Convert a string to a safe filename.
        
        Args:
            name: Original string.
            
        Returns:
            Safe filename string.
        """
        safe = "".join(c if c.isalnum() or c in " -_" else "" for c in name)
        return safe.replace(" ", "_")[:50]

    def process_directory(
        self,
        input_dir: Path | str | None = None,
        skip_existing: bool = True,
    ) -> list[ProcessedPaper]:
        """Process all PDFs in a directory.
        
        Args:
            input_dir: Directory with PDFs. Defaults to data/references/pdfs.
            skip_existing: Skip already processed papers.
            
        Returns:
            List of processed papers.
        """
        input_dir = Path(input_dir) if input_dir else settings.paths.references_pdf_dir
        pdf_files = list(input_dir.glob("*.pdf"))
        
        console.print(f"[bold]Found {len(pdf_files)} PDF files to process[/bold]")
        
        processed = []
        for pdf_path in pdf_files:
            try:
                paper = self.process_pdf(pdf_path, skip_if_exists=skip_existing)
                processed.append(paper)
            except Exception as e:
                console.print(f"[red]Error processing {pdf_path.name}: {e}[/red]")
                continue
        
        return processed
