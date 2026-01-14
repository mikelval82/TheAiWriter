"""Orchestrator for perspective paper writing workflow."""

from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ai_writer.agents.writer_agent import WriterAgent
from ai_writer.agents.reviewer_agent import ReviewerAgent
from ai_writer.models.paper import Paper, Section
from ai_writer.readers.markdown_reader import MarkdownReader
from ai_writer.writers.markdown_writer import MarkdownWriter
from ai_writer.utils.reference_index import ReferenceIndex
from ai_writer.utils.reference_context_manager import ReferenceContextManager
from config.settings import settings

console = Console()


# Estructura estándar de un paper de perspectivas
PERSPECTIVE_PAPER_SECTIONS = [
    "Introducción",
    "Estado Actual del Arte",
    "Identificación del Problema o Brecha",
    "La Nueva Perspectiva",
    "Discusión",
    "Implicaciones Futuras",
    "Desafíos y Limitaciones",
    "Conclusiones",
    "Declaración de Conflicto de Intereses",
    "Agradecimientos",
    "Referencias Bibliográficas",
]


class PerspectivePaperOrchestrator:
    """Orchestrator for generating perspective papers with iterative review."""

    def __init__(
        self,
        abstract_path: Path | str | None = None,
        review_iterations: int = 2,
        top_k_references: int = 8,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            abstract_path: Path to the abstract markdown file.
                          Defaults to data/references/markdown/ABSTRACT.md
            review_iterations: Number of write-review iterations per section.
            top_k_references: Number of top references to use per section.
        """
        self.abstract_path = Path(abstract_path) if abstract_path else (
            settings.paths.references_markdown_dir / "ABSTRACT.md"
        )
        self.review_iterations = max(1, review_iterations)
        self.top_k_references = top_k_references
        
        # Initialize components
        self.markdown_reader = MarkdownReader()
        self.markdown_writer = MarkdownWriter()
        
        # Load abstract as base context
        self.abstract_context = self._load_abstract()
        
        # Build reference index with embeddings
        console.print("\n[cyan]📚 Construyendo índice de referencias...[/cyan]")
        self.reference_index = ReferenceIndex()
        self.reference_index.build()
        
        # Initialize reference context manager
        self.context_manager = ReferenceContextManager(
            reference_index=self.reference_index,
            abstract_context=self.abstract_context,
            top_k=self.top_k_references,
        )
        
        # Initialize agents with shared context
        self.writer_agent = WriterAgent(abstract_context=self.abstract_context)
        self.reviewer_agent = ReviewerAgent(abstract_context=self.abstract_context)
        
        # Path for incremental output file
        self.output_file_path: Path | None = None
        self.current_paper_title: str = ""

    def _load_abstract(self) -> str:
        """Load the abstract from the configured path.

        Returns:
            The abstract text content.

        Raises:
            FileNotFoundError: If abstract file doesn't exist.
        """
        if not self.abstract_path.exists():
            raise FileNotFoundError(
                f"Abstract file not found: {self.abstract_path}\n"
                "Please provide an ABSTRACT.md file in data/references/markdown/"
            )
        
        content = self.markdown_reader.read(self.abstract_path)
        console.print(Panel(
            content[:500] + "..." if len(content) > 500 else content,
            title="📄 Abstract Cargado",
            border_style="green",
        ))
        return content

    def _initialize_output_file(self, title: str) -> Path:
        """Initialize the output file, overwriting any existing content.

        Args:
            title: The paper title.

        Returns:
            Path to the output file.
        """
        output_dir = settings.paths.final_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from title
        safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
        safe_title = safe_title.replace(" ", "_")[:50]
        
        self.output_file_path = output_dir / f"{safe_title}.md"
        self.current_paper_title = title
        
        # Write initial content (overwrite existing file)
        initial_content = f"# {title}\n\n## Abstract\n\n{self.abstract_context}\n\n"
        self.output_file_path.write_text(initial_content, encoding="utf-8")
        
        console.print(f"[dim]📄 Archivo de salida inicializado: {self.output_file_path}[/dim]")
        return self.output_file_path

    def _append_section_to_file(self, section: Section) -> None:
        """Append a completed section to the output file.

        Args:
            section: The section to append.
        """
        if self.output_file_path is None:
            return
        
        section_content = f"## {section.title}\n\n{section.content}\n\n"
        
        with open(self.output_file_path, "a", encoding="utf-8") as f:
            f.write(section_content)
        
        console.print(f"  [dim]💾 Sección guardada en: {self.output_file_path.name}[/dim]")

    def _write_and_review_section(
        self,
        section_name: str,
        previous_sections: list[Section],
    ) -> Section:
        """Write a section and iteratively review it.

        Args:
            section_name: Name of the section to write.
            previous_sections: Already written sections for context.

        Returns:
            The final reviewed section.
        """
        console.print(f"\n[bold cyan]📝 Escribiendo: {section_name}[/bold cyan]")
        
        # Build previous sections text for context
        previous_text = "\n\n".join(
            f"## {s.title}\n{s.content}" for s in previous_sections
        )
        
        # Get intelligently selected reference context for this section
        reference_context = self.context_manager.get_context_for_section(
            section_name=section_name,
            previous_sections_text=previous_text,
        )
        
        # Initial write with optimized references
        section = self.writer_agent.write_section(
            section_name=section_name,
            previous_sections=previous_sections,
            reference_context=reference_context,
        )
        
        # Iterative review loop
        for iteration in range(self.review_iterations):
            console.print(
                f"  [yellow]🔄 Revisión {iteration + 1}/{self.review_iterations}[/yellow]"
            )
            section = self.reviewer_agent.review_section(
                section=section,
                previous_sections=previous_sections,
            )
        
        console.print(f"  [green]✓ {section_name} completado[/green]")
        
        # Append section to output file immediately
        self._append_section_to_file(section)
        
        return section

    def generate_paper(
        self,
        title: str,
        sections: list[str] | None = None,
    ) -> Paper:
        """Generate a complete perspective paper.

        Args:
            title: The paper title.
            sections: Optional custom section list. Defaults to perspective paper structure.

        Returns:
            The complete Paper object.
        """
        console.print(Panel(
            f"[bold]Generando paper de perspectivas[/bold]\n\n"
            f"Título: {title}\n"
            f"Iteraciones de revisión: {self.review_iterations}\n"
            f"Referencias por sección: {self.top_k_references}",
            title="🚀 TheAIWriter",
            border_style="blue",
        ))

        # Initialize output file (overwrites any existing file)
        self._initialize_output_file(title)

        # Use default perspective paper sections if not specified
        section_names = sections or PERSPECTIVE_PAPER_SECTIONS

        # Create paper with abstract as first section (not generated)
        paper = Paper(
            title=title,
            sections=[Section(title="Abstract", content=self.abstract_context)],
        )

        # Generate each section with iterative review
        generated_sections = []
        for section_name in section_names:
            section = self._write_and_review_section(
                section_name=section_name,
                previous_sections=paper.sections + generated_sections,
            )
            generated_sections.append(section)

        # Add all generated sections to paper
        paper.sections.extend(generated_sections)
        
        # Add bibliography section with used citations
        citations = self.context_manager.get_all_citations()
        if citations:
            bib_content = "\n".join(f"- {cite}" for cite in citations)
            paper.sections.append(Section(
                title="Referencias Utilizadas",
                content=bib_content,
            ))

        console.print("\n[bold green]✓ Paper generado exitosamente![/bold green]")
        return paper

    def final_review(self, paper: Paper) -> tuple[Paper, str]:
        """Perform final review of the complete paper.

        Args:
            paper: The complete paper to review.

        Returns:
            Tuple of (reviewed paper, critical review document).
        """
        console.print("\n[bold magenta]🔍 Revisión Final del Paper Completo[/bold magenta]")
        
        # Final coherence review
        reviewed_paper = self.reviewer_agent.review_full_paper(paper)
        
        # Generate critical review document
        critical_review = self.reviewer_agent.generate_critical_review(paper)
        
        console.print("[green]✓ Revisión final completada[/green]")
        return reviewed_paper, critical_review

    def run(
        self,
        title: str,
        output_dir: Path | str | None = None,
    ) -> tuple[Path, Path]:
        """Run the complete paper generation pipeline.

        Args:
            title: The paper title.
            output_dir: Output directory. Defaults to data/output/drafts.

        Returns:
            Tuple of (paper path, critical review path).
        """
        output_dir = Path(output_dir) if output_dir else settings.paths.final_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from title (no timestamp for consistent naming)
        safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
        safe_title = safe_title.replace(" ", "_")[:50]

        # Generate paper (sections are saved incrementally)
        paper = self.generate_paper(title=title)

        # Paper path is already set during generate_paper
        paper_path = self.output_file_path or (output_dir / f"{safe_title}.md")

        # Final review (with error handling)
        reviewed_paper = paper
        critical_review = ""
        try:
            reviewed_paper, critical_review = self.final_review(paper)
            # Overwrite with reviewed version
            self.markdown_writer.write(reviewed_paper, paper_path)
            console.print(f"[green]📄 Paper final guardado: {paper_path}[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Error en revisión final: {e}[/yellow]")
            console.print(f"[yellow]  Paper guardado sin revisión final: {paper_path}[/yellow]")

        # Export critical review if available
        review_path = output_dir / f"{safe_title}_critical_review.md"
        if critical_review:
            review_path.write_text(critical_review, encoding="utf-8")
            console.print(f"[green]📋 Revisión crítica guardada: {review_path}[/green]")
        else:
            review_path.write_text("# Revisión Crítica\n\nNo se pudo generar debido a un error de conexión.", encoding="utf-8")
            console.print(f"[yellow]📋 Revisión crítica pendiente: {review_path}[/yellow]")
