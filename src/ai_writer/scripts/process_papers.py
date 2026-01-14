"""Script to process all PDF papers and generate markdown summaries."""

import sys
import time
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_writer.agents.paper_summary_agent import PaperSummaryAgent
from ai_writer.readers.pdf_reader import PDFReader
from ai_writer.writers.markdown_writer import MarkdownWriter
from config.settings import settings

console = Console()


def get_safe_filename(original_name: str) -> str:
    """Convert a PDF filename to a safe markdown filename.

    Args:
        original_name: Original PDF filename.

    Returns:
        Safe filename for markdown output.
    """
    # Remove .pdf extension and clean up
    name = original_name.replace(".pdf", "")
    # Replace problematic characters
    for char in [':', '?', '"', '<', '>', '|', '*']:
        name = name.replace(char, '')
    # Limit length
    if len(name) > 100:
        name = name[:100]
    return f"{name}.md"


def process_papers(
    input_dir: Path | None = None,
    output_dir: Path | None = None,
    use_reasoning: bool = True,
    skip_existing: bool = True,
) -> dict:
    """Process all PDF papers in a directory and generate markdown summaries.

    Args:
        input_dir: Directory containing PDF files. Defaults to settings path.
        output_dir: Directory for markdown output. Defaults to data/references/markdown.
        use_reasoning: Whether to use GPT-5 with reasoning (True) or GPT-5.1 (False).
        skip_existing: Skip papers that already have summaries.

    Returns:
        Dictionary with processing statistics.
    """
    input_dir = input_dir or settings.paths.references_pdf_dir
    # Output to data/references/markdown (same level as pdfs)
    output_dir = output_dir or settings.paths.references_markdown_dir

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        console.print("[yellow]No PDF files found in the input directory.[/yellow]")
        return {"total": 0, "processed": 0, "skipped": 0, "failed": 0}

    # Initialize components
    pdf_reader = PDFReader()
    summary_agent = PaperSummaryAgent(use_reasoning=use_reasoning)
    md_writer = MarkdownWriter()

    # Statistics
    stats = {
        "total": len(pdf_files),
        "processed": 0,
        "skipped": 0,
        "failed": 0,
        "failed_files": [],
    }

    # Display configuration
    config_table = Table(title="📚 Paper Processing Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    config_table.add_row("Input Directory", str(input_dir))
    config_table.add_row("Output Directory", str(output_dir))
    config_table.add_row("Model", settings.ai.reasoning_model if use_reasoning else settings.ai.default_model)
    config_table.add_row("Total Papers", str(len(pdf_files)))
    config_table.add_row("Skip Existing", "Yes" if skip_existing else "No")
    console.print(config_table)
    console.print()

    # Process each PDF
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Processing papers...", total=len(pdf_files))

        for pdf_file in pdf_files:
            output_file = output_dir / get_safe_filename(pdf_file.name)

            # Skip if already processed
            if skip_existing and output_file.exists():
                progress.console.print(f"[dim]⏭️  Skipping (exists): {pdf_file.name}[/dim]")
                stats["skipped"] += 1
                progress.advance(task)
                continue

            progress.console.print(f"[blue]📄 Processing: {pdf_file.name}[/blue]")

            try:
                # Read PDF content
                start_time = time.time()
                paper_text = pdf_reader.read(pdf_file)

                # Generate summary
                summary = summary_agent.summarize(paper_text)

                # Write markdown output
                md_writer.write(output_file, summary)

                elapsed = time.time() - start_time
                progress.console.print(
                    f"[green]✅ Completed: {pdf_file.name} ({elapsed:.1f}s)[/green]"
                )
                stats["processed"] += 1

            except Exception as e:
                progress.console.print(
                    f"[red]❌ Failed: {pdf_file.name} - {str(e)}[/red]"
                )
                stats["failed"] += 1
                stats["failed_files"].append((pdf_file.name, str(e)))

            progress.advance(task)

    # Print final statistics
    console.print()
    stats_panel = Panel(
        f"""[green]✅ Processed: {stats['processed']}[/green]
[yellow]⏭️  Skipped: {stats['skipped']}[/yellow]
[red]❌ Failed: {stats['failed']}[/red]
[cyan]📊 Total: {stats['total']}[/cyan]""",
        title="📈 Processing Complete",
        border_style="green",
    )
    console.print(stats_panel)

    # Show failed files if any
    if stats["failed_files"]:
        console.print("\n[red]Failed files:[/red]")
        for filename, error in stats["failed_files"]:
            console.print(f"  • {filename}: {error}")

    return stats


def main():
    """Main entry point for the paper processing script."""
    console.print(
        Panel(
            "[bold blue]TheAIWriter - Paper Summary Generator[/bold blue]\n"
            "Processing academic papers with GPT-5.1/GPT-5",
            border_style="blue",
        )
    )

    # Process all papers with reasoning enabled for deep analysis
    stats = process_papers(
        use_reasoning=True,  # Use GPT-5 for maximum analysis quality
        skip_existing=True,  # Don't reprocess already summarized papers
    )

    return stats


if __name__ == "__main__":
    main()
