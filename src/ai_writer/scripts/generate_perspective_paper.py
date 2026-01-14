"""Script to generate a perspective paper using the orchestrator."""

import sys
from pathlib import Path

from rich.console import Console

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ai_writer.orchestrators.perspective_paper_orchestrator import PerspectivePaperOrchestrator
from config.settings import settings

console = Console()


def main() -> None:
    """Run the perspective paper generation pipeline."""
    console.print("[bold blue]═══════════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]       TheAIWriter - Perspective Paper         [/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════════[/bold blue]\n")

    # Paper title (can be customized)
    title = (
        "Cuerpos Secos: Hacia Agentes Fundamentales Empáticos en el Metaverso - "
        "Una Perspectiva sobre la Convergencia de XR, IA y Cognición 4E"
    )

    # Initialize orchestrator with intelligent reference selection
    try:
        orchestrator = PerspectivePaperOrchestrator(
            review_iterations=2,  # 2 iterations of write-review per section
            top_k_references=8,   # Top 8 most relevant references per section
        )
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    # Run the pipeline (references are now selected automatically per section)
    paper_path, review_path = orchestrator.run(title=title)

    console.print("\n[bold green]═══════════════════════════════════════════════[/bold green]")
    console.print("[bold green]              ¡Proceso Completado!             [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════════[/bold green]")
    console.print(f"\n📄 Paper: {paper_path}")
    console.print(f"📋 Revisión Crítica: {review_path}")


if __name__ == "__main__":
    main()
