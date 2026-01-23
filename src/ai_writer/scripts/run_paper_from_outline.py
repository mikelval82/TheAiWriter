#!/usr/bin/env python
"""Script to write a paper from an existing outline (Phase 3 only).

This script reads a previously generated outline JSON and continues
with Phase 3: paragraph-by-paragraph writing.

Use run_outline_generator.py first to create the outline.
"""

import argparse
import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from ai_writer.orchestrators.advanced_orchestrator import AdvancedPerspectiveOrchestrator
from ai_writer.models.outline import PaperOutline, SectionOutline, ParagraphOutline
from config.settings import settings

console = Console()


def load_outline_from_json(outline_path: Path) -> PaperOutline:
    """Load a PaperOutline from a JSON file.
    
    Args:
        outline_path: Path to the outline JSON file.
        
    Returns:
        PaperOutline object.
    """
    with open(outline_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    sections = []
    for section_data in data.get("sections", []):
        paragraphs = []
        for para_data in section_data.get("paragraphs", []):
            paragraph = ParagraphOutline(
                paragraph_number=para_data.get("paragraph_number", len(paragraphs) + 1),
                key_idea=para_data.get("key_idea", ""),
                supporting_points=para_data.get("supporting_points", []),
                suggested_sources=para_data.get("suggested_sources", []),
            )
            paragraphs.append(paragraph)
        
        section = SectionOutline(
            section_name=section_data.get("section_name", ""),
            section_purpose=section_data.get("section_purpose", ""),
            paragraphs=paragraphs,
        )
        sections.append(section)
    
    outline = PaperOutline(
        title=data.get("title", "Paper"),
        abstract=data.get("abstract", ""),
        thesis_statement=data.get("thesis_statement", ""),
        sections=sections,
    )
    outline.available_topics = data.get("available_topics", [])
    
    return outline


def main() -> None:
    """Run paper writing from an existing outline (Phase 3)."""
    parser = argparse.ArgumentParser(
        description="Write a paper from an existing outline"
    )
    parser.add_argument(
        "--outline",
        type=str,
        required=True,
        help="Path to outline JSON file (or just filename in drafts folder)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--review-iterations",
        type=int,
        default=1,
        help="Number of review iterations per section (default: 1)",
    )
    
    args = parser.parse_args()
    
    # Resolve outline path
    outline_path = Path(args.outline)
    if not outline_path.exists():
        # Try in drafts folder
        outline_path = settings.paths.output_dir / "drafts" / args.outline
    
    if not outline_path.exists():
        console.print(f"[red]Error: No se encontró el archivo de outline: {args.outline}[/red]")
        console.print(f"[dim]Buscado en: {outline_path}[/dim]")
        raise SystemExit(1)
    
    # Load outline
    console.print(f"[cyan]📋 Cargando outline desde: {outline_path}[/cyan]")
    outline = load_outline_from_json(outline_path)
    
    console.print(Panel(
        f"[bold]Escritura de Paper desde Outline[/bold]\n\n"
        f"📌 Título: {outline.title}\n"
        f"📑 Secciones: {outline.total_sections}\n"
        f"📝 Párrafos: {outline.total_paragraphs}\n"
        f"🔄 Revisiones/sección: {args.review_iterations}",
        title="✍️ Phase 3: Writing",
        border_style="green",
    ))
    
    try:
        # Initialize orchestrator with the loaded abstract
        orchestrator = AdvancedPerspectiveOrchestrator(
            abstract_path=None,  # Will use default, but we override
            review_iterations=args.review_iterations,
            n_clusters=10,  # Not used in Phase 3
            outline_review_iterations=0,
        )
        
        # Override abstract with the one from outline
        if outline.abstract:
            orchestrator.abstract_context = outline.abstract
        
        # Set the outline
        orchestrator.current_outline = outline
        
        # Phase 3: Write paper
        paper = orchestrator.phase3_write_paper(outline)
        
        # Write final paper
        output_dir = args.output_dir or settings.paths.output_dir / "final"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        paper_path = output_dir / f"{outline.title.replace(' ', '_')}.md"
        orchestrator.markdown_writer.write(paper.to_markdown(), paper_path)
        
        console.print("\n" + "=" * 60)
        console.print("[bold green]✅ Paper completado![/bold green]\n")
        console.print(f"  📄 Archivo: {paper_path}")
        console.print("=" * 60)
        
    except FileNotFoundError as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise SystemExit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Escritura cancelada por el usuario[/yellow]")
        raise SystemExit(130)


if __name__ == "__main__":
    main()
