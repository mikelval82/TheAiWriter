"""Script to translate a perspective paper using the style guide."""

import re
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ai_writer.agents.translator_agent import TranslatorAgent
from config.settings import settings

console = Console()


def parse_sections(content: str) -> list[tuple[str, str]]:
    """Parse markdown content into sections based on ## headers.
    
    Args:
        content: Full markdown content of the paper.
        
    Returns:
        List of (section_name, section_content) tuples.
    """
    # Split by ## headers while keeping the header
    pattern = r'^(## .+)$'
    parts = re.split(pattern, content, flags=re.MULTILINE)
    
    sections = []
    
    # First part is the title (# Header) and anything before first ##
    if parts[0].strip():
        # Extract title
        title_match = re.match(r'^# (.+)$', parts[0].strip(), re.MULTILINE)
        if title_match:
            sections.append(("Title", parts[0].strip()))
    
    # Process remaining parts in pairs (header, content)
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            header = parts[i].replace("## ", "").strip()
            content_part = parts[i] + parts[i + 1]
            sections.append((header, content_part.strip()))
        elif parts[i].strip():
            header = parts[i].replace("## ", "").strip()
            sections.append((header, parts[i].strip()))
    
    return sections


def translate_paper(
    input_path: Path,
    output_path: Path | None = None,
) -> Path:
    """Translate a paper from Spanish to British English.
    
    Args:
        input_path: Path to the Spanish markdown paper.
        output_path: Path for the output. Defaults to same name with _EN suffix.
        
    Returns:
        Path to the translated paper.
    """
    console.print(Panel.fit(
        "[bold blue]TheAIWriter - Academic Paper Translator[/bold blue]\n"
        "[dim]Spanish → British English with Style Guide[/dim]",
        border_style="blue"
    ))
    
    # Validate input
    if not input_path.exists():
        console.print(f"[red]Error: Input file not found: {input_path}[/red]")
        sys.exit(1)
    
    # Set output path
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_EN.md"
    
    console.print(f"\n📄 Input:  [cyan]{input_path}[/cyan]")
    console.print(f"📝 Output: [cyan]{output_path}[/cyan]")
    
    # Load content
    content = input_path.read_text(encoding="utf-8")
    
    # Parse sections
    sections = parse_sections(content)
    console.print(f"\n📑 Found [bold]{len(sections)}[/bold] sections to translate:\n")
    for i, (name, _) in enumerate(sections, 1):
        console.print(f"   {i}. {name}")
    
    # Initialize translator
    console.print("\n[cyan]🔧 Initializing translator with style guide...[/cyan]")
    translator = TranslatorAgent()
    console.print("[green]✓ Translator ready[/green]")
    
    # Translate sections
    translated_sections: list[str] = []
    abstract_context = ""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        for section_name, section_content in sections:
            task = progress.add_task(f"Translating: {section_name}...", total=None)
            
            try:
                if section_name == "Title":
                    # Translate title section (includes # header)
                    translated = translator.translate_section(
                        section_content=section_content,
                        section_name="Title",
                        abstract_context="",
                    )
                elif section_name == "Abstract":
                    # Translate abstract and save for context
                    translated = translator.translate_abstract(section_content)
                    # Extract just the abstract text for context
                    abstract_context = translated
                else:
                    # Translate with abstract context for terminology consistency
                    translated = translator.translate_section(
                        section_content=section_content,
                        section_name=section_name,
                        abstract_context=abstract_context,
                    )
                
                translated_sections.append(translated)
                progress.remove_task(task)
                console.print(f"   [green]✓[/green] {section_name}")
                
            except Exception as e:
                progress.remove_task(task)
                console.print(f"   [red]✗[/red] {section_name}: {e}")
                # Keep original on error
                translated_sections.append(section_content)
    
    # Assemble final document
    console.print("\n[cyan]📋 Assembling translated document...[/cyan]")
    
    final_content = "\n\n".join(translated_sections)
    
    # Add translation metadata as HTML comment
    metadata = f"""<!--
Translated by TheAIWriter
Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}
Source: {input_path.name}
Style Guide: Mikel Val-Calvo UK English
-->

"""
    final_content = metadata + final_content
    
    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final_content, encoding="utf-8")
    
    # Save updated glossary
    console.print("[cyan]💾 Saving glossary updates...[/cyan]")
    translator.save_glossary()
    
    console.print(Panel.fit(
        f"[bold green]✓ Translation Complete![/bold green]\n\n"
        f"📄 Output: [cyan]{output_path}[/cyan]\n"
        f"📊 Sections translated: {len(translated_sections)}",
        border_style="green"
    ))
    
    return output_path


def main() -> None:
    """Run the translation pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Translate academic papers from Spanish to British English"
    )
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=None,
        help="Path to the Spanish markdown paper"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output path (defaults to input_EN.md)"
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Translate the latest paper in data/output/final/"
    )
    
    args = parser.parse_args()
    
    # Determine input path
    if args.latest:
        # Find latest paper (excluding _EN, _critical_review, Test_ files)
        final_dir = settings.paths.final_dir
        papers = [
            f for f in final_dir.glob("*.md")
            if not f.stem.endswith("_EN")
            and not f.stem.endswith("_critical_review")
            and not f.stem.startswith("Test_")
        ]
        if not papers:
            console.print("[red]No papers found in final directory[/red]")
            sys.exit(1)
        
        # Sort by modification time, get latest
        input_path = max(papers, key=lambda p: p.stat().st_mtime)
        console.print(f"[dim]Selected latest paper: {input_path.name}[/dim]")
    elif args.input:
        input_path = args.input
    else:
        parser.print_help()
        sys.exit(1)
    
    translate_paper(input_path, args.output)


if __name__ == "__main__":
    main()
