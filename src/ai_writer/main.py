"""Main entry point for TheAIWriter application.

TheAIWriter is an AI-assisted academic writing system specialized in perspective papers.
It uses a 3-phase architecture: Cluster Analysis → Planning → Writing.

Usage:
    # Generate a perspective paper
    python -m ai_writer generate "Paper Title"
    
    # Process new PDFs
    python -m ai_writer process
    
    # Show embedding statistics
    python -m ai_writer stats
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.settings import settings

console = Console()
app = typer.Typer(
    name="ai-writer",
    help="🤖 TheAIWriter - AI-assisted academic writing for perspective papers",
    add_completion=False,
    rich_markup_mode="rich",
)


# =============================================================================
# Main Commands
# =============================================================================

@app.command()
def generate(
    title: str = typer.Argument(
        ...,
        help="Title of the perspective paper to generate"
    ),
    abstract: Optional[Path] = typer.Option(
        None,
        "--abstract", "-a",
        help="Path to abstract markdown file (defaults to data/references/markdown/ABSTRACT.md)"
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output directory for generated files"
    ),
    clusters: int = typer.Option(
        25,
        "--clusters", "-c",
        help="Number of clusters for topic extraction"
    ),
    review_iterations: int = typer.Option(
        1,
        "--reviews", "-r",
        help="Number of review iterations per section"
    ),
    outline_iterations: int = typer.Option(
        1,
        "--outline-reviews",
        help="Number of outline refinement iterations"
    ),
    no_logging: bool = typer.Option(
        False,
        "--no-log",
        help="Disable pipeline logging"
    ),
) -> None:
    """Generate a perspective paper using the 3-phase architecture.
    
    The pipeline consists of:
    
    1. **Cluster Analysis**: Extract main topics from the embedding space
    2. **Planning**: Generate detailed outline with paragraph-level ideas
    3. **Writing**: Write paragraph-by-paragraph with semantic search
    
    Example:
        ai-writer generate "Hacia Agentes Empáticos Fundamentales"
    """
    from ai_writer.orchestrators.advanced_orchestrator import AdvancedPerspectiveOrchestrator
    
    console.print(Panel(
        f"[bold cyan]TheAIWriter[/bold cyan] - Perspective Paper Generator\n\n"
        f"📌 Title: [bold]{title}[/bold]",
        border_style="blue",
    ))
    
    # Initialize orchestrator
    orchestrator = AdvancedPerspectiveOrchestrator(
        abstract_path=abstract,
        review_iterations=review_iterations,
        n_clusters=clusters,
        outline_review_iterations=outline_iterations,
        enable_logging=not no_logging,
    )
    
    # Run the pipeline
    paper_path, review_path = orchestrator.run(
        title=title,
        output_dir=output_dir,
    )
    
    console.print("\n")
    console.print(Panel(
        f"📄 Paper: [link=file://{paper_path}]{paper_path}[/link]\n"
        f"📋 Review: [link=file://{review_path}]{review_path}[/link]",
        title="[bold green]✓ Generation Complete[/bold green]",
        border_style="green",
    ))


@app.command()
def process(
    input_dir: Optional[Path] = typer.Option(
        None,
        "--input", "-i",
        help="Directory containing PDFs to process"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Reprocess all files even if already processed"
    ),
) -> None:
    """Process PDF references and build embedding indices.
    
    This command:
    
    1. Converts PDFs to Markdown using Docling
    2. Extracts ideas, claims, and references
    3. Generates embeddings and builds search indices
    
    Example:
        ai-writer process --input ./new_papers/
    """
    from ai_writer.processors.batch_processor import BatchProcessor
    
    input_dir = input_dir or settings.paths.references_pdf_dir
    
    console.print(Panel(
        f"📂 Input: {input_dir}\n"
        f"🔄 Force: {force}",
        title="Processing PDFs",
        border_style="cyan",
    ))
    
    processor = BatchProcessor(
        pdfs_folder=input_dir,
        output_folder=settings.paths.processed_dir,
    )
    
    stats = processor.process_all(force_reprocess=force)
    
    console.print("\n")
    console.print(Panel(
        f"✅ Processed: {stats.get('processed_successfully', 0)} papers\n"
        f"💡 Ideas extracted: {stats.get('total_ideas', 0)}\n"
        f"📌 Claims extracted: {stats.get('total_claims', 0)}\n"
        f"📚 References extracted: {stats.get('total_references', 0)}",
        title="[bold green]✓ Processing Complete[/bold green]",
        border_style="green",
    ))


@app.command()
def stats() -> None:
    """Show statistics about the embedding indices.
    
    Displays information about:
    - Number of papers processed
    - Ideas, claims, and references indexed
    - Embedding dimensions and storage
    """
    import json

    import numpy as np
    
    console.print(Panel(
        f"📂 {settings.paths.embeddings_dir}",
        title="📊 Index Statistics",
        border_style="cyan",
    ))
    
    # Build stats table
    table = Table(title="Embedding Indices", show_header=True)
    table.add_column("Index", style="cyan")
    table.add_column("Items", justify="right", style="green")
    table.add_column("Dimensions", justify="right")
    table.add_column("Papers", justify="right", style="yellow")
    
    for index_name in ["ideas", "claims", "references"]:
        index_path = settings.paths.embeddings_dir / f"{index_name}_index.npz"
        metadata_path = settings.paths.embeddings_dir / f"{index_name}_metadata.json"
        
        if not index_path.exists() or not metadata_path.exists():
            table.add_row(index_name.capitalize(), "Not found", "-", "-")
            continue
        
        with np.load(index_path) as data:
            count, dimensions = data["embeddings"].shape
        with open(metadata_path, encoding="utf-8") as f:
            items = json.load(f)["items"]
        # References point at the paper that cites them
        papers = {item.get("paper_id") or item.get("source_paper_id") for item in items}
        papers.discard(None)
        
        table.add_row(
            index_name.capitalize(),
            str(count),
            str(dimensions),
            str(len(papers)),
        )
    
    console.print(table)


@app.command()
def reindex() -> None:
    """Rebuild the embedding indices with the configured embedding model.
    
    Needed after changing EMBEDDING_BACKEND or EMBEDDING_MODEL: vectors from
    different models cannot be mixed. The PDFs are not processed again, and the
    previous index files are kept in a subfolder named after their model.
    
    Example:
        ai-writer reindex
    """
    import json
    import shutil

    from ai_writer.embeddings.embedder import LEGACY_EMBEDDING_MODEL, get_embedder
    from ai_writer.embeddings.rag_system import RAGSystem
    
    embeddings_dir = settings.paths.embeddings_dir
    model_name = get_embedder().model_name
    
    console.print(Panel(
        f"📂 {embeddings_dir}\n"
        f"🧠 Model: {model_name}",
        title="Rebuilding Embedding Indices",
        border_style="cyan",
    ))
    
    # Keep the previous vectors: with another backend they may not be reproducible
    for metadata_path in sorted(embeddings_dir.glob("*_metadata.json")):
        index_path = metadata_path.with_name(metadata_path.name.replace("_metadata.json", "_index.npz"))
        with open(metadata_path, encoding="utf-8") as f:
            previous_model = json.load(f).get("embedding_model", LEGACY_EMBEDDING_MODEL)
        if previous_model == model_name:
            continue
        backup_dir = embeddings_dir / f"previous_{previous_model.replace('/', '_')}"
        backup_dir.mkdir(exist_ok=True)
        for path in (metadata_path, index_path):
            if path.exists():
                shutil.move(str(path), str(backup_dir / path.name))
        console.print(f"[dim]  {metadata_path.name} ({previous_model}) → {backup_dir.name}/[/dim]")
    
    rag = RAGSystem(
        indices_dir=settings.paths.indices_dir,
        embeddings_dir=embeddings_dir,
    )
    rag.build_indices(force_rebuild=True)


@app.command()
def outline(
    title: str = typer.Argument(
        ...,
        help="Title of the paper for outline generation"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Path to save the outline (JSON and Markdown)"
    ),
    clusters: int = typer.Option(
        25,
        "--clusters", "-c",
        help="Number of clusters for topic extraction"
    ),
) -> None:
    """Generate only the outline without writing the full paper.
    
    Useful for planning and reviewing the structure before full generation.
    
    Example:
        ai-writer outline "Paper Title" --output outline.json
    """
    from ai_writer.orchestrators.advanced_orchestrator import AdvancedPerspectiveOrchestrator
    import json
    
    console.print(Panel(
        f"📌 Title: [bold]{title}[/bold]\n"
        f"🔬 Clusters: {clusters}",
        title="Generating Outline",
        border_style="cyan",
    ))
    
    orchestrator = AdvancedPerspectiveOrchestrator(
        n_clusters=clusters,
        enable_logging=True,
    )
    
    # Phase 1
    topics = orchestrator.phase1_analyze_topics()
    
    # Phase 2
    outline_obj = orchestrator.phase2_generate_outline(title, topics)
    
    # Save outline
    output_dir = output.parent if output else settings.paths.drafts_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
    safe_title = safe_title.replace(" ", "_")[:50]
    
    json_path = output or (output_dir / f"{safe_title}_outline.json")
    md_path = json_path.with_suffix(".md")
    
    # Save JSON
    json_path.write_text(
        json.dumps(outline_obj.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    # Save Markdown
    md_content = outline_obj.to_markdown()
    md_path.write_text(md_content, encoding="utf-8")
    
    console.print("\n")
    console.print(Panel(
        f"📄 JSON: [link=file://{json_path}]{json_path}[/link]\n"
        f"📝 Markdown: [link=file://{md_path}]{md_path}[/link]",
        title="[bold green]✓ Outline Generated[/bold green]",
        border_style="green",
    ))


@app.command()
def review(
    paper_path: Path = typer.Argument(
        ...,
        help="Path to the paper markdown file to review"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Path to save the critical review"
    ),
) -> None:
    """Generate a critical review of an existing paper.
    
    Analyzes the paper for:
    - Argument coherence and logical flow
    - Evidence quality and citation support
    - Gaps and areas for improvement
    
    Example:
        ai-writer review ./output/paper.md
    """
    from ai_writer.agents.reviewer_agent import ReviewerAgent
    from ai_writer.readers.markdown_reader import MarkdownReader
    from ai_writer.models.paper import Paper, Section
    
    if not paper_path.exists():
        console.print(f"[red]Error: File not found: {paper_path}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"📄 Paper: {paper_path}",
        title="Generating Critical Review",
        border_style="cyan",
    ))
    
    reader = MarkdownReader()
    content = reader.read(paper_path)
    
    # Create a simple Paper object from content
    paper = Paper(
        title=paper_path.stem.replace("_", " "),
        sections=[Section(title="Content", content=content)],
    )
    
    reviewer = ReviewerAgent()
    critical_review = reviewer.generate_critical_review(paper)
    
    # Save review
    output_path = output or paper_path.with_name(f"{paper_path.stem}_critical_review.md")
    output_path.write_text(critical_review, encoding="utf-8")
    
    console.print("\n")
    console.print(Panel(
        f"📋 Review saved: [link=file://{output_path}]{output_path}[/link]",
        title="[bold green]✓ Review Complete[/bold green]",
        border_style="green",
    ))


@app.command()
def version() -> None:
    """Show version and configuration information."""
    table = Table(title="TheAIWriter Configuration", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Version", "1.0.0")
    table.add_row("LLM Backend", settings.ai.llm_backend)
    table.add_row("Default Model", settings.ai.default_model)
    table.add_row("Reasoning Model", settings.ai.reasoning_model)
    table.add_row("Fast Model", settings.ai.fast_model)
    table.add_row("Embedding Backend", settings.ai.embedding_backend)
    table.add_row("Embedding Model", settings.ai.embedding_model)
    table.add_row("References Dir", str(settings.paths.references_markdown_dir))
    table.add_row("Output Dir", str(settings.paths.final_dir))
    table.add_row("Data Dir", str(settings.paths.data_dir))
    
    console.print(table)


# =============================================================================
# Entry Point
# =============================================================================

def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
