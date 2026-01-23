#!/usr/bin/env python
"""Script to run the advanced 3-phase perspective paper generation."""

import argparse
from pathlib import Path

from rich.console import Console

from ai_writer.orchestrators.advanced_orchestrator import AdvancedPerspectiveOrchestrator
from config.settings import settings

console = Console()


def main() -> None:
    """Run the advanced perspective paper pipeline."""
    parser = argparse.ArgumentParser(
        description="Generate a perspective paper using 3-phase advanced architecture"
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Hacia Agentes Empáticos Fundamentales: Una Nueva Perspectiva",
        help="Title of the paper to generate",
    )
    parser.add_argument(
        "--abstract",
        type=Path,
        default=None,
        help="Path to abstract markdown file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--clusters",
        type=int,
        default=12,
        help="Number of clusters for topic extraction (default: 12)",
    )
    parser.add_argument(
        "--review-iterations",
        type=int,
        default=2,
        help="Number of review iterations per section (default: 2)",
    )
    parser.add_argument(
        "--outline-iterations",
        type=int,
        default=1,
        help="Number of iterations for outline refinement (default: 1)",
    )
    
    args = parser.parse_args()
    
    console.print("\n[bold blue]🚀 Advanced Perspective Paper Generator[/bold blue]\n")
    console.print(f"  📌 Title: {args.title}")
    console.print(f"  🔬 Clusters: {args.clusters}")
    console.print(f"  🔄 Review iterations: {args.review_iterations}")
    console.print(f"  📋 Outline iterations: {args.outline_iterations}")
    
    try:
        orchestrator = AdvancedPerspectiveOrchestrator(
            abstract_path=args.abstract,
            review_iterations=args.review_iterations,
            n_clusters=args.clusters,
            outline_review_iterations=args.outline_iterations,
        )
        
        paper_path, review_path = orchestrator.run(
            title=args.title,
            output_dir=args.output_dir,
        )
        
        console.print("\n[bold green]✅ Generation Complete![/bold green]")
        console.print(f"  📄 Paper: {paper_path}")
        console.print(f"  📋 Review: {review_path}")
        
    except FileNotFoundError as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise SystemExit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Generation cancelled by user[/yellow]")
        raise SystemExit(130)


if __name__ == "__main__":
    main()
