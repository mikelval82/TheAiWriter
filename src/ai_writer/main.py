"""Main entry point for TheAIWriter application."""

from pathlib import Path

from rich.console import Console

from ai_writer.agents.writer_agent import WriterAgent
from ai_writer.agents.reviewer_agent import ReviewerAgent
from ai_writer.models.paper import Paper
from ai_writer.readers.pdf_reader import PDFReader
from ai_writer.readers.markdown_reader import MarkdownReader
from ai_writer.writers.markdown_writer import MarkdownWriter
from ai_writer.writers.pdf_writer import PDFWriter

console = Console()


class AIWriter:
    """Main class for orchestrating the AI paper writing process."""

    def __init__(self) -> None:
        """Initialize the AIWriter with all components."""
        self.writer_agent = WriterAgent()
        self.reviewer_agent = ReviewerAgent()
        self.pdf_reader = PDFReader()
        self.markdown_reader = MarkdownReader()
        self.markdown_writer = MarkdownWriter()
        self.pdf_writer = PDFWriter()

    def load_references(self, paths: list[Path | str]) -> list[str]:
        """Load and extract text from reference documents.

        Args:
            paths: List of paths to reference documents (PDF or Markdown).

        Returns:
            List of extracted text content from each reference.
        """
        references = []
        for path in paths:
            path = Path(path)
            if path.suffix.lower() == ".pdf":
                content = self.pdf_reader.read(path)
            elif path.suffix.lower() in (".md", ".markdown"):
                content = self.markdown_reader.read(path)
            else:
                console.print(f"[yellow]Skipping unsupported file: {path}[/yellow]")
                continue
            references.append(content)
            console.print(f"[green]✓ Loaded reference: {path.name}[/green]")
        return references

    def create_paper(
        self,
        topic: str,
        references: list[Path | str] | None = None,
        sections: list[str] | None = None,
    ) -> Paper:
        """Create a new paper on the given topic.

        Args:
            topic: The main topic/title of the paper.
            references: Optional list of reference document paths.
            sections: Optional list of section names to include.

        Returns:
            A Paper object with the generated content.
        """
        console.print(f"\n[bold blue]📝 Creating paper: {topic}[/bold blue]\n")

        # Load references if provided
        reference_texts = []
        if references:
            reference_texts = self.load_references(references)

        # Default sections if not specified
        if sections is None:
            sections = ["Abstract", "Introduction", "Methodology", "Results", "Discussion", "Conclusion"]

        # Generate paper using writer agent
        console.print("[cyan]🤖 Generating paper content...[/cyan]")
        paper = self.writer_agent.write(
            topic=topic,
            sections=sections,
            references=reference_texts,
        )

        console.print("[green]✓ Paper generated successfully![/green]")
        return paper

    def review_paper(self, paper: Paper) -> Paper:
        """Review and improve an existing paper.

        Args:
            paper: The paper to review.

        Returns:
            An improved version of the paper.
        """
        console.print("\n[cyan]🔍 Reviewing paper...[/cyan]")
        reviewed_paper = self.reviewer_agent.review(paper)
        console.print("[green]✓ Review complete![/green]")
        return reviewed_paper

    def export_paper(
        self,
        paper: Paper,
        output_path: Path | str,
        format: str = "markdown",
    ) -> Path:
        """Export the paper to a file.

        Args:
            paper: The paper to export.
            output_path: Path where to save the file.
            format: Output format ("markdown" or "pdf").

        Returns:
            Path to the exported file.
        """
        output_path = Path(output_path)

        if format.lower() == "markdown":
            self.markdown_writer.write(paper, output_path)
        elif format.lower() == "pdf":
            self.pdf_writer.write(paper, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

        console.print(f"[green]✓ Paper exported to: {output_path}[/green]")
        return output_path


def main() -> None:
    """Main entry point."""
    console.print("[bold green]Welcome to TheAIWriter![/bold green]")
    console.print("Use the AIWriter class to create and manage your papers.\n")

    # Example usage
    writer = AIWriter()
    console.print("AIWriter initialized successfully.")
    console.print("\nExample usage:")
    console.print('  paper = writer.create_paper("Your Topic", references=["ref.pdf"])')
    console.print('  writer.export_paper(paper, "output.md")')


if __name__ == "__main__":
    main()
