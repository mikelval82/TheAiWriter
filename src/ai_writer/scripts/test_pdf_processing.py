"""Script to test PDF processing with a single file."""

import sys
from pathlib import Path

from rich.console import Console

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ai_writer.processors.pdf_processor import PDFProcessor
from config.settings import settings

console = Console()


def main() -> None:
    """Run PDF processing test on a single paper."""
    console.print("[bold blue]═══════════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]    TheAIWriter - PDF Processing Test          [/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════════[/bold blue]\n")

    # Test PDF - Cognitive Architectures for Language Agents
    test_pdf = settings.paths.references_pdf_dir / "Cognitive Architectures for Language Agents.pdf"
    
    if not test_pdf.exists():
        console.print(f"[red]Error: Test PDF not found at {test_pdf}[/red]")
        console.print("\nAvailable PDFs:")
        for pdf in settings.paths.references_pdf_dir.glob("*.pdf"):
            console.print(f"  • {pdf.name}")
        sys.exit(1)

    # Initialize processor
    processor = PDFProcessor()

    # Process the PDF
    try:
        processed = processor.process_pdf(test_pdf, skip_if_exists=False)
        
        console.print("\n[bold cyan]═══ Processing Summary ═══[/bold cyan]")
        console.print(f"\n[bold]Paper:[/bold] {processed.metadata.title}")
        console.print(f"[bold]Authors:[/bold] {', '.join(processed.metadata.authors)}")
        console.print(f"[bold]Year:[/bold] {processed.metadata.year}")
        console.print(f"[bold]Sections:[/bold] {len(processed.sections)}")
        
        console.print("\n[bold]Ideas extracted by section:[/bold]")
        section_ideas = {}
        for idea in processed.ideas:
            section_ideas[idea.section] = section_ideas.get(idea.section, 0) + 1
        for section, count in section_ideas.items():
            console.print(f"  • {section}: {count} ideas")
        
        console.print("\n[bold]Sample ideas:[/bold]")
        for idea in processed.ideas[:3]:
            console.print(f"  [{idea.section}] {idea.idea[:100]}...")
        
        console.print("\n[bold]Sample claims:[/bold]")
        for claim in processed.claims[:3]:
            console.print(f"  [{claim.section}] {claim.claim[:100]}...")
        
        console.print(f"\n[bold]References extracted:[/bold] {len(processed.references)}")
        console.print("\n[bold]Sample references:[/bold]")
        for ref in processed.references[:3]:
            console.print(f"  • {ref.citation_key}: {ref.title[:60]}...")

        console.print("\n[bold green]═══════════════════════════════════════════════[/bold green]")
        console.print("[bold green]              Test Completed!                  [/bold green]")
        console.print("[bold green]═══════════════════════════════════════════════[/bold green]")
        
        # Show output location
        output_dir = processor.papers_dir / processed.metadata.paper_id
        console.print(f"\n📂 Output saved to: {output_dir}")
        
    except Exception as e:
        console.print(f"[red]Error during processing: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
