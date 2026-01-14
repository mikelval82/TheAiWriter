"""Main PDF processor for extracting structured data from academic papers."""

import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ai_writer.processors.extraction_agent import PDFExtractionAgent
from ai_writer.processors.models import (
    Claim,
    Idea,
    PaperMetadata,
    ProcessedPaper,
    Reference,
    SectionData,
)
from ai_writer.readers.pdf_reader import PDFReader
from config.settings import settings

console = Console()


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
        self.output_dir = Path(output_dir) if output_dir else (
            settings.paths.data_dir / "processed"
        )
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
        """
        pdf_path = Path(pdf_path)
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

        # Extract sections
        console.print("[cyan]📑 Identifying sections...[/cyan]")
        sections_data = self.extraction_agent.extract_sections(full_text)
        
        sections = []
        references_content = ""
        
        for i, sec_data in enumerate(sections_data):
            section_name = sec_data.get("section_name", f"Section {i+1}")
            content = sec_data.get("content", "")
            
            # Save references content for later
            if "reference" in section_name.lower():
                references_content = content
                continue
                
            sections.append(SectionData(
                paper_id=metadata.paper_id,
                section_name=section_name,
                section_number=i + 1,
                content=content,
                word_count=len(content.split()),
            ))
            metadata.sections_found.append(section_name)
        
        console.print(f"  [green]✓ Found {len(sections)} sections[/green]")

        # Extract ideas from each section
        console.print("[cyan]💡 Extracting ideas from sections...[/cyan]")
        all_ideas: list[Idea] = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing sections...", total=len(sections))
            
            for section in sections:
                progress.update(task, description=f"[cyan]Ideas: {section.section_name}[/cyan]")
                
                ideas = self.extraction_agent.extract_ideas_from_section(
                    section_name=section.section_name,
                    section_content=section.content,
                    paper_title=metadata.title,
                    authors=metadata.authors,
                    year=metadata.year,
                    paper_id=metadata.paper_id,
                )
                all_ideas.extend(ideas)
                progress.advance(task)
        
        console.print(f"  [green]✓ Extracted {len(all_ideas)} ideas[/green]")

        # Extract claims from each section
        console.print("[cyan]📌 Extracting claims with evidence...[/cyan]")
        all_claims: list[Claim] = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing sections...", total=len(sections))
            
            for section in sections:
                progress.update(task, description=f"[cyan]Claims: {section.section_name}[/cyan]")
                
                claims = self.extraction_agent.extract_claims_from_section(
                    section_name=section.section_name,
                    section_content=section.content,
                    paper_title=metadata.title,
                    paper_id=metadata.paper_id,
                )
                all_claims.extend(claims)
                progress.advance(task)
        
        console.print(f"  [green]✓ Extracted {len(all_claims)} claims[/green]")

        # Extract references
        console.print("[cyan]📚 Extracting references...[/cyan]")
        references: list[Reference] = []
        
        if references_content:
            references = self.extraction_agent.extract_references(
                references_content,
                metadata.paper_id,
            )
        else:
            # Try to find references at the end of the document
            last_portion = full_text[-20000:]
            references = self.extraction_agent.extract_references(
                last_portion,
                metadata.paper_id,
            )
        
        console.print(f"  [green]✓ Extracted {len(references)} references[/green]")

        # Create processed paper
        processed = ProcessedPaper(
            metadata=metadata,
            sections=sections,
            ideas=all_ideas,
            claims=all_claims,
            references=references,
        )

        # Save outputs
        self._save_processed_paper(processed)
        
        console.print(Panel(
            f"[bold green]✓ Processing complete![/bold green]\n\n"
            f"Ideas: {len(all_ideas)}\n"
            f"Claims: {len(all_claims)}\n"
            f"References: {len(references)}",
            title="✅ Done",
            border_style="green",
        ))
        
        return processed

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
        
        # Save references as JSONL
        with open(paper_dir / "references.jsonl", "w", encoding="utf-8") as f:
            for ref in paper.references:
                f.write(json.dumps(ref.model_dump(), ensure_ascii=False) + "\n")
        
        # Append to global indices
        self._append_to_global_index(self.indices_dir / "all_ideas.jsonl", paper.ideas)
        self._append_to_global_index(self.indices_dir / "all_claims.jsonl", paper.claims)
        self._append_to_global_index(self.indices_dir / "all_references.jsonl", paper.references)
        
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
