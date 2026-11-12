"""MCP server of the TheAIWriter plugin: the library and the document, as tools for Claude.

Claude Code starts it with ``uv run`` from the plugin folder; its working directory
is the folder where the student opened Claude, which is the document folder.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from ai_writer.library import PROJECT_FILE, Library, LibraryError, Project

server = MCPServer("theaiwriter")


def _document_folder() -> Path:
    return Path(os.getenv("CLAUDE_PROJECT_DIR") or os.getcwd())


def _current_library() -> tuple[Library, Project | None]:
    """The open document's library, or the default one outside a document."""
    folder = _document_folder()
    if (folder / PROJECT_FILE).exists():
        project = Project.load(folder)
        return project.library(), project
    return Library(), None


def _error(error: LibraryError) -> dict:
    return {"error": str(error)}


@server.tool()
def diagnostico() -> dict:
    """Informa de dónde corre el plugin: sistema, Python, carpetas y si `claude` está disponible."""
    library, project = _current_library()
    return {
        "sistema": platform.platform(),
        "python": sys.version.split()[0],
        "carpeta_del_documento": str(_document_folder()),
        "es_un_documento": project is not None,
        "biblioteca": str(library.root),
        "claude_en_path": shutil.which("claude"),
    }


@server.tool()
def probar_claude() -> dict:
    """Lanza `claude -p` con haiku y devuelve si responde con la cuenta del usuario."""
    claude = shutil.which("claude")
    if claude is None:
        return {"ok": False, "error": "claude no está en el PATH del servidor"}
    start = time.monotonic()
    completed = subprocess.run(
        [claude, "-p", "Responde solo: ok", "--model", "haiku", "--output-format", "json",
         "--tools", "", "--no-session-persistence"],
        capture_output=True, text=True, encoding="utf-8", timeout=120,
        stdin=subprocess.DEVNULL,
    )
    try:
        output = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "codigo": completed.returncode, "stderr": completed.stderr[-500:]}
    return {
        "ok": not output.get("is_error", True),
        "respuesta": output.get("result"),
        "segundos": round(time.monotonic() - start, 1),
    }


@server.tool()
def estado_biblioteca() -> dict:
    """Resume la biblioteca: carpeta, número de papers, colecciones, PDFs pendientes y el
    último procesado. Si la carpeta actual es un documento, indica qué colecciones usa."""
    library, project = _current_library()
    if not library.exists():
        return {"biblioteca": str(library.root), "existe": False}
    collections = library.collections()
    status = {
        "biblioteca": str(library.root),
        "existe": True,
        "papers": len(library.papers()),
        "colecciones": {name: len(ids) for name, ids in collections.items()},
        "pdfs_pendientes": [pdf.name for pdf in library.pending_pdfs()],
        "ultimo_procesado": library.job(),
    }
    if project is not None:
        status["documento"] = {
            "titulo": project.titulo,
            "tipo": project.tipo,
            "colecciones": project.colecciones or "toda la biblioteca",
        }
        try:
            status["documento"]["papers_disponibles"] = len(project.paper_ids())
        except LibraryError as error:
            status["documento"]["error"] = str(error)
    return status


@server.tool()
def listar_papers(coleccion: str | None = None) -> dict:
    """Lista los papers de la biblioteca, o los de una colección: id, título, autores, año y
    cuántas ideas, claims y referencias se extrajeron."""
    library, _ = _current_library()
    try:
        ids = library.paper_ids([coleccion] if coleccion else None)
    except LibraryError as error:
        return _error(error)
    papers = [asdict(paper) for paper in library.papers() if paper.id in ids]
    return {"coleccion": coleccion, "papers": papers}


@server.tool()
def guardar_coleccion(nombre: str, papers: list[str]) -> dict:
    """Crea o reemplaza una colección. Cada paper se indica por id, nombre de fichero o una
    parte de su título que lo identifique sin ambigüedad."""
    library, _ = _current_library()
    try:
        found = library.find_papers(papers)
        library.save_collection(nombre, found)
    except LibraryError as error:
        return _error(error)
    return {"coleccion": nombre, "papers": [paper.title for paper in found]}


@server.tool()
def borrar_coleccion(nombre: str) -> dict:
    """Borra una colección. Los papers siguen en la biblioteca."""
    library, _ = _current_library()
    try:
        library.delete_collection(nombre)
    except LibraryError as error:
        return _error(error)
    return {"borrada": nombre}


@server.tool()
def anadir_pdfs(rutas: list[str]) -> dict:
    """Copia PDFs, o todos los PDFs de unas carpetas, a la biblioteca. No los procesa:
    para eso está `procesar_pdfs`."""
    library, _ = _current_library()
    try:
        added = library.add_pdfs([Path(path) for path in rutas])
    except LibraryError as error:
        return _error(error)
    return {
        "anadidos": [pdf.name for pdf in added],
        "pendientes": [pdf.name for pdf in library.pending_pdfs()],
    }


@server.tool()
def procesar_pdfs() -> dict:
    """Procesa en segundo plano los PDFs pendientes: extrae ideas, claims y referencias con
    Claude (unas 6 a 10 llamadas por paper) y rehace los índices. Responde al momento;
    el progreso se consulta con `estado_biblioteca`."""
    library, _ = _current_library()
    try:
        job = library.start_processing()
    except LibraryError as error:
        return _error(error)
    return {"lanzado": job, "registro": str(library.log_file)}


@server.tool()
def crear_documento(
    tipo: str, titulo: str, idioma: str = "es", colecciones: list[str] | None = None
) -> dict:
    """Convierte la carpeta actual en un documento de TheAIWriter: crea `proyecto.yaml` y las
    carpetas materiales/, borrador/, revision/ y exportacion/. `tipo` es perspectiva,
    resultados o convocatoria; sin colecciones, el documento usa toda la biblioteca."""
    folder = _document_folder()
    try:
        project = Project.create(
            folder, tipo=tipo, titulo=titulo, idioma=idioma, colecciones=colecciones or []
        )
        papers = len(project.paper_ids())
    except LibraryError as error:
        return _error(error)
    except ValueError as error:
        return {"error": f"Datos no válidos: {error}"}
    return {"documento": str(folder / PROJECT_FILE), "papers_disponibles": papers}


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
