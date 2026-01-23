#!/usr/bin/env python
"""Script to generate paper outline only (Phase 1 + Phase 2).

This script performs:
- Phase 1: Cluster analysis to extract topics from embeddings
- Phase 2: Generate detailed paper outline with paragraph-level ideas

The outline is saved to data/output/drafts/ in both MD and JSON formats.
Use run_paper_from_outline.py to continue with Phase 3 (writing).
"""

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from ai_writer.orchestrators.advanced_orchestrator import AdvancedPerspectiveOrchestrator
from config.settings import settings

console = Console()


def main() -> None:
    """Run outline generation only (Phase 1 + Phase 2)."""
    parser = argparse.ArgumentParser(
        description="Generate paper outline using cluster analysis and planning"
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Hacia Agentes Empáticos Fundamentales",
        help="Title of the paper to generate",
    )
    parser.add_argument(
        "--abstract",
        type=Path,
        default=None,
        help="Path to abstract markdown file",
    )
    parser.add_argument(
        "--clusters",
        type=int,
        default=10,
        help="Number of clusters for topic extraction (default: 10)",
    )
    parser.add_argument(
        "--refine-iterations",
        type=int,
        default=0,
        help="Number of iterations for outline refinement (default: 0)",
    )
    
    args = parser.parse_args()
    
    console.print(Panel(
        f"[bold]Generador de Esquema (Outline)[/bold]\n\n"
        f"📌 Título: {args.title}\n"
        f"🔬 Clusters: {args.clusters}\n"
        f"🔄 Iteraciones de refinamiento: {args.refine_iterations}",
        title="📋 Phase 1 + Phase 2 Only",
        border_style="cyan",
    ))
    
    try:
        # Initialize orchestrator
        orchestrator = AdvancedPerspectiveOrchestrator(
            abstract_path=args.abstract,
            review_iterations=1,  # Not used in outline generation
            n_clusters=args.clusters,
            outline_review_iterations=args.refine_iterations,
        )
        
        # Phase 1: Analyze topics
        topics = orchestrator.phase1_analyze_topics(title=args.title)
        
        # Phase 2: Generate outline
        outline = orchestrator.phase2_generate_outline(
            title=args.title,
            topics=topics,
        )
        
        # Finalize logger
        if orchestrator.logger:
            log_dir = orchestrator.logger.finalize(success=True)
        
        # Summary
        output_dir = settings.paths.output_dir / "drafts"
        safe_title = args.title.replace(" ", "_").replace(":", "")
        
        console.print("\n" + "=" * 60)
        console.print("[bold green]✅ Esquema generado correctamente![/bold green]\n")
        console.print(f"  📊 Temas extraídos: {len(topics)}")
        console.print(f"  📑 Secciones: {outline.total_sections}")
        console.print(f"  📝 Párrafos totales: {outline.total_paragraphs}")
        console.print(f"\n  📄 Archivos generados:")
        console.print(f"     - {output_dir / f'{safe_title}_outline.md'}")
        console.print(f"     - {output_dir / f'{safe_title}_outline.json'}")
        console.print("\n[dim]Para continuar con la escritura, ejecuta:[/dim]")
        console.print(f"[cyan]  python run_paper_from_outline.py --outline \"{safe_title}_outline.json\"[/cyan]")
        console.print("=" * 60)
        
    except FileNotFoundError as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise SystemExit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Generación cancelada por el usuario[/yellow]")
        raise SystemExit(130)


if __name__ == "__main__":
    main()
