"""CLI for PDF processing, embedding indices, libraries and document verification.

Claude writes documents while consulting the plugin's Zotero passage tools.
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

library_app = typer.Typer(help="📚 La biblioteca de papers: estado, colecciones y migración")
app.add_typer(library_app, name="biblioteca")
document_app = typer.Typer(help="📝 Verificar las citas y el apoyo de un documento")
app.add_typer(document_app, name="documento")

# Library chosen with --biblioteca, if any
_active_library_dir: Optional[Path] = None


@app.callback()
def use_library(
    library_dir: Optional[Path] = typer.Option(
        None,
        "--biblioteca",
        envvar="THEAIWRITER_BIBLIOTECA",
        help="Library folder to read and write. Without it, the repository's data/ is used.",
    ),
) -> None:
    """🤖 TheAIWriter - AI-assisted academic writing for perspective papers"""
    global _active_library_dir
    _active_library_dir = library_dir
    if library_dir:
        from ai_writer.library import Library

        Library(library_dir).activate()


# =============================================================================
# Main Commands
# =============================================================================

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
    2. Extracts ideas and claims, each backed by a verbatim quote
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
        f"📌 Claims extracted: {stats.get('total_claims', 0)}",
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

# =============================================================================
# Library Commands
# =============================================================================

def _library(library_dir: Optional[Path]):
    from ai_writer.library import Library

    return Library(library_dir or _active_library_dir)


LIBRARY_OPTION = typer.Option(
    None, "--ruta", help="Carpeta de la biblioteca. Por defecto, la de --biblioteca o tus documentos."
)


@library_app.command("estado")
def library_status(library_dir: Optional[Path] = LIBRARY_OPTION) -> None:
    """Muestra los papers y las colecciones de la biblioteca."""
    library = _library(library_dir)
    if not library.exists():
        console.print(f"[yellow]No hay biblioteca en {library.root}[/yellow]")
        raise typer.Exit(1)

    papers = library.papers()
    table = Table(title=f"📚 {library.root} ({len(papers)} papers)")
    table.add_column("Paper", style="cyan")
    table.add_column("Ideas", justify="right")
    table.add_column("Claims", justify="right")
    table.add_column("Referencias", justify="right")
    for paper in papers:
        table.add_row(paper.title, str(paper.ideas), str(paper.claims), str(paper.references))
    console.print(table)

    collections = library.collections()
    if collections:
        for name, ids in collections.items():
            console.print(f"  • [bold]{name}[/bold]: {len(ids)} papers")
    else:
        console.print("  Sin colecciones.")


@library_app.command("migrar")
def library_migrate(
    library_dir: Optional[Path] = LIBRARY_OPTION,
    source: Path = typer.Option(
        None, "--desde", help="Carpeta procesada de origen. Por defecto, data/processed del repositorio."
    ),
) -> None:
    """Copia el corpus ya procesado a una biblioteca, sin reprocesar ni reindexar."""
    from ai_writer.library import LibraryError

    library = _library(library_dir)
    source = source or settings.paths.data_dir / "processed"
    try:
        result = library.migrate_from(source, pdfs_dir=settings.paths.data_dir / "references" / "pdfs")
    except LibraryError as error:
        console.print(f"[red]✗ {error}[/red]")
        raise typer.Exit(1)
    console.print(
        f"[green]✓ {result['papers']} papers, {result['vector_files']} ficheros de vectores "
        f"y {result['pdfs']} PDFs copiados a {library.root}[/green]"
    )


@library_app.command("procesar")
def library_process(library_dir: Optional[Path] = LIBRARY_OPTION) -> None:
    """Procesa los PDFs pendientes y deja constancia en procesado/proceso.json."""
    import os

    from ai_writer.background import now as _now
    from ai_writer.processors.batch_processor import BatchProcessor

    library = _library(library_dir)
    library.activate()
    library.write_job(estado="en_curso", pid=os.getpid(), inicio=_now(), fin=None)
    try:
        stats = BatchProcessor(
            pdfs_folder=library.pdfs_dir, output_folder=library.processed_dir
        ).process_all()
    except BaseException as error:
        library.write_job(estado="error", error=str(error) or type(error).__name__, fin=_now())
        raise
    library.write_job(
        estado="terminado",
        papers_en_biblioteca=stats.get("processed_successfully", 0),
        fallidos=stats.get("failed", 0),
        fin=_now(),
    )


@library_app.command("coleccion")
def library_collection(
    name: str = typer.Argument(..., help="Nombre de la colección"),
    papers: list[str] = typer.Argument(
        None, help="Papers: id, nombre del fichero o parte del título"
    ),
    delete: bool = typer.Option(False, "--borrar", help="Borra la colección"),
    library_dir: Optional[Path] = LIBRARY_OPTION,
) -> None:
    """Crea, reemplaza o borra una colección de papers."""
    from ai_writer.library import LibraryError

    library = _library(library_dir)
    try:
        if delete:
            library.delete_collection(name)
            console.print(f"[green]✓ Colección «{name}» borrada[/green]")
            return
        if not papers:
            raise LibraryError("Indica al menos un paper.")
        found = library.find_papers(papers)
        library.save_collection(name, found)
    except LibraryError as error:
        console.print(f"[red]✗ {error}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]✓ Colección «{name}» con {len(found)} papers[/green]")


# =============================================================================
# Document Commands
# =============================================================================

@document_app.command("verificar")
def document_verify(
    folder: Path = typer.Argument(Path("."), help="Carpeta del documento"),
) -> None:
    """Juzga si cada frase citada del borrador coincide con la obra y deja el informe en revision/."""
    from ai_writer import verificacion
    from ai_writer.library import LibraryError

    try:
        data = verificacion.run_judge(folder)
    except LibraryError as error:
        console.print(f"[red]✗ {error}[/red]")
        raise typer.Exit(1)
    console.print(verificacion.summary(data["apoyo"]))


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
