"""MCP server of the TheAIWriter plugin: the library and the document, as tools for Claude.

Claude Code starts it with ``uv run`` from the plugin folder; its working directory
is the folder where the student opened Claude, which is the document folder.
"""

import contextlib
import functools
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


def tool(function):
    """Register a tool. Its prints (the indices report progress with rich) go to
    stderr: stdout carries the MCP protocol."""

    @functools.wraps(function)
    def quiet(*args, **kwargs):
        with contextlib.redirect_stdout(sys.stderr):
            return function(*args, **kwargs)

    server.tool()(quiet)
    return quiet


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


@tool
def diagnostico() -> dict:
    """Informa de dónde corre el plugin: sistema, Python, carpetas y si `claude` está disponible."""
    from ai_writer.zotero import Zotero, default_index_dir

    library, project = _current_library()
    try:
        zotero = Zotero()
        found = {"carpeta": str(zotero.root), "obras": len(zotero.works()),
                 "con_pdf": sum(bool(w.pdfs) for w in zotero.works())}
    except LibraryError as error:
        found = {"error": str(error)}
    return {
        "sistema": platform.platform(),
        "python": sys.version.split()[0],
        "carpeta_del_documento": str(_document_folder()),
        "es_un_documento": project is not None,
        "zotero": found,
        "indice_de_pasajes": str(default_index_dir()),
        "biblioteca": str(library.root),
        "claude_en_path": shutil.which("claude"),
    }


@tool
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


@tool
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


@tool
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


@tool
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


@tool
def borrar_coleccion(nombre: str) -> dict:
    """Borra una colección. Los papers siguen en la biblioteca."""
    library, _ = _current_library()
    try:
        library.delete_collection(nombre)
    except LibraryError as error:
        return _error(error)
    return {"borrada": nombre}


@tool
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


@tool
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


@tool
def crear_documento(
    tipo: str, titulo: str, idioma: str = "es", colecciones: list[str] | None = None,
    fuente: str = "biblioteca",
) -> dict:
    """Convierte la carpeta actual en un documento de TheAIWriter: crea `proyecto.yaml` y las
    carpetas materiales/, borrador/, revision/ y exportacion/. `tipo` es perspectiva,
    resultados o convocatoria. `fuente`: «zotero» para citar desde colecciones de Zotero
    (nombres de `colecciones_zotero`) o «biblioteca» para la biblioteca propia; sin
    colecciones, el documento usa todas las obras."""
    folder = _document_folder()
    try:
        project = Project.create(
            folder, tipo=tipo, titulo=titulo, idioma=idioma, colecciones=colecciones or [],
            fuente=fuente,
        )
        if project.fuente == "zotero":
            from ai_writer.consulta import open_index, scope

            index = open_index()
            return {"documento": str(folder / PROJECT_FILE), **index.status(scope(project, index))}
        papers = len(project.paper_ids())
    except LibraryError as error:
        return _error(error)
    except ValueError as error:
        return {"error": f"Datos no válidos: {error}"}
    return {"documento": str(folder / PROJECT_FILE), "papers_disponibles": papers}


# Zotero: passages to consult while writing


def _zotero_document() -> tuple:
    """(passage index, the open document or None, item keys it may cite or None for all)."""
    from ai_writer.consulta import open_index, scope

    folder = _document_folder()
    project = Project.load(folder) if (folder / PROJECT_FILE).exists() else None
    index = open_index()
    return index, project, scope(project, index)


@tool
def colecciones_zotero() -> dict:
    """Lista las colecciones de Zotero de este ordenador, con cuántas obras tiene cada una
    y cuántas traen PDF. Solo las obras con PDF se pueden consultar por pasajes."""
    from ai_writer.consulta import open_index

    try:
        zotero = open_index().zotero
    except LibraryError as error:
        return _error(error)
    return {
        "carpeta": str(zotero.root),
        "obras": len(zotero.works()),
        "colecciones": [
            {"ruta": c.path, "obras": len(keys := zotero.item_keys([c.key])),
             "con_pdf": sum(bool(zotero.work(key).pdfs) for key in keys)}
            for c in zotero.collections()
        ],
    }


@tool
def estado_indice(actualizar: bool = False) -> dict:
    """Cuántas obras del documento (o de todo Zotero, fuera de un documento) tienen PDF y
    están indexadas. Con `actualizar`, indexa las pendientes: no gasta llamadas a Claude,
    pero la primera vez descarga el modelo de búsqueda y tarda unos segundos por PDF."""
    try:
        index, _, allowed = _zotero_document()
        done = index.update(allowed) if actualizar else None
        status = index.status(allowed)
    except LibraryError as error:
        return _error(error)
    works = [w for w in index.zotero.works() if allowed is None or w.item_key in allowed]
    status["obras_sin_pdf"] = [f"{w.title} ({w.year or 's. f.'})" for w in works if not w.pdfs][:50]
    if done is not None:
        status["actualizacion"] = done
    return status


@tool
def buscar_pasajes(
    consulta: str, n: int = 8, claves: list[str] | None = None, por_obra: int = 3
) -> dict:
    """Busca pasajes en los PDF de las obras que el documento puede citar. Combina
    significado y palabras: funciona mejor en el idioma de los papers y con los términos
    que usarían. Cada resultado trae `id` (para `leer_pasaje`), la `clave` con la que se
    cita, `[@clave]`, la sección, las páginas y el texto literal. `claves` limita la
    búsqueda a esas obras; `por_obra` es el máximo de pasajes de una misma obra.
    Cita solo lo que hayas leído aquí o en `leer_pasaje`."""
    try:
        index, project, allowed = _zotero_document()
        indexed = index.update(allowed) if index.pending(allowed) else None
        if claves:
            wanted = {index.work_of(key.lstrip("@")) for key in claves} - {None}
            allowed = {w.item_key for w in wanted if allowed is None or w.item_key in allowed}
        results = index.search(consulta, n=n, item_keys=allowed, max_per_work=por_obra)
    except LibraryError as error:
        return _error(error)
    if project is not None:
        from ai_writer.consulta import record

        record(_document_folder(), consulta, [r["id"] for r in results])
    answer = {"consulta": consulta, "resultados": results}
    if indexed:
        answer["indexadas_ahora"] = len(indexed["indexadas"])
    return answer


@tool
def leer_pasaje(id: str, alcance: str = "vecinos") -> dict:
    """Lee alrededor de un pasaje de `buscar_pasajes`. `alcance`: «vecinos» (el anterior,
    él y el siguiente) o «seccion» (la sección entera). Úsala antes de citar un dato
    concreto, para ver su contexto."""
    try:
        index, project, _ = _zotero_document()
        passages = index.read(id, "seccion" if alcance.lower().startswith("sec") else "vecinos")
    except LibraryError as error:
        return _error(error)
    if not passages:
        return {"error": f"No existe el pasaje «{id}»."}
    if project is not None:
        from ai_writer.consulta import record

        record(_document_folder(), None, [p["id"] for p in passages])
    return {"clave": passages[0]["clave"], "titulo": passages[0]["titulo"], "pasajes": passages}


@tool
def leer_paginas(clave: str, desde: int, hasta: int | None = None) -> dict:
    """Lee los pasajes de una obra que caen en esas páginas del PDF (como mucho 6 páginas
    por llamada)."""
    try:
        index, project, _ = _zotero_document()
        last = min(hasta or desde, desde + 5)
        passages = index.pages(clave.lstrip("@"), desde, last)
    except LibraryError as error:
        return _error(error)
    if not passages:
        return {"error": f"No hay texto de «{clave}» en las páginas {desde}-{last}."}
    if project is not None:
        from ai_writer.consulta import record

        record(_document_folder(), None, [p["id"] for p in passages])
    return {"clave": passages[0]["clave"], "titulo": passages[0]["titulo"], "pasajes": passages}


# Evidence and citations


# Evidence engines are slow to build (indices, model); one is kept per document state
_engines: dict[tuple, object] = {}


def _engine(library: Library, project: Project | None):
    """An evidence engine for the open document, reused while its vectors do not change."""
    from ai_writer.evidence import EvidenceEngine

    paper_ids = project.paper_ids() if project else None
    vectors = library.embeddings_dir / "ideas_index.npz"
    stamp = vectors.stat().st_mtime if vectors.exists() else 0
    cache_key = (str(library.root), frozenset(paper_ids) if paper_ids else None, stamp)
    if cache_key not in _engines:
        _engines.clear()
        _engines[cache_key] = EvidenceEngine(library, paper_ids)
    return _engines[cache_key]


@tool
def buscar_evidencia(
    consulta: str,
    n: int = 8,
    tipo: str = "todo",
    tema: int | None = None,
    excluir: list[str] | None = None,
) -> dict:
    """Busca ideas y claims en los papers que el documento puede citar (sus colecciones).
    Cada resultado trae la clave con la que se cita, `[@clave]`, y como mucho dos
    resultados por paper. `tipo`: ideas, claims o todo. `tema`: id de
    `temas_del_corpus` para buscar solo en ese tema. `excluir`: claves que no se quieren,
    por ejemplo las ya citadas. Cita solo claves que hayan salido aquí."""
    library, project = _current_library()
    if not library.exists():
        return {"error": f"No hay biblioteca en {library.root}."}
    try:
        engine = _engine(library, project)
        results = engine.search(consulta, n=n, kind=tipo, topic=tema, exclude_keys=set(excluir or ()))
    except LibraryError as error:
        return _error(error)
    if project is not None:
        from ai_writer.validation import record_retrieved

        record_retrieved(_document_folder(), consulta, [r["clave"] for r in results])
    return {"consulta": consulta, "resultados": results}


@tool
def temas_del_corpus(n_temas: int | None = None) -> dict:
    """Agrupa por temas las ideas de los papers del documento, para planificar secciones o
    ver qué queda sin cubrir. Cada tema trae su id (para `buscar_evidencia`), cuántas
    ideas y papers reúne, palabras clave y tres ideas representativas con su clave."""
    library, project = _current_library()
    if not library.exists():
        return {"error": f"No hay biblioteca en {library.root}."}
    try:
        topics = _engine(library, project).topics(n_temas)
    except LibraryError as error:
        return _error(error)
    return {"temas": [asdict(topic) for topic in topics]}


@tool
def referencia(clave: str) -> dict:
    """Datos completos de una obra citable: título, autores, año, revista, DOI, entrada
    BibTeX, cuánta evidencia tiene y si está en las colecciones del documento."""
    library, project = _current_library()
    if project is not None and project.fuente == "zotero":
        from ai_writer.consulta import reference

        index, _, allowed = _zotero_document()
        found = reference(index, clave.lstrip("@"), allowed)
        return found or {"error": f"La clave «{clave}» no existe en Zotero."}
    reference = _engine(library, project).reference(clave.lstrip("@"))
    if reference is None:
        return {"error": f"La clave «{clave}» no existe en la biblioteca."}
    return reference


@tool
def validar_citas(texto: str) -> dict:
    """Comprueba las citas de un texto: que cada `[@clave]` exista en la biblioteca, que esté
    en las colecciones del documento y que haya salido en alguna búsqueda de evidencia.
    Úsala antes de dar por bueno cualquier texto con citas."""
    from ai_writer.citations import CitationIndex, check_citations
    from ai_writer.validation import check_text

    library, project = _current_library()
    if project is not None and project.fuente == "zotero":
        from ai_writer.verificacion import check_citations as check_zotero

        index, _, allowed = _zotero_document()
        report = check_zotero(texto, index, allowed)
        bad = report["desconocidas"] + report["fuera_de_las_colecciones"] + report["mal_formadas"]
        return {"correcto": not bad, **report}
    if project is not None:
        report = check_text(texto, _document_folder())
    else:
        report = check_citations(texto, CitationIndex.load(library))
    return {"correcto": report.ok, "informe": report.summary(), **asdict(report)}


@tool
def validar_documento() -> dict:
    """Valida el borrador `borrador/documento.md`: citas, huecos `[[PENDIENTE]]` y palabras
    por sección, y sugiere obras de las colecciones para cada `[@?]`. Escribe el informe
    en `revision/validacion.md`. Las sugerencias no se aplican solas: compruébalas antes."""
    from ai_writer.validation import DRAFT, REPORT, validate_document

    library, project = _current_library()
    folder = _document_folder()
    if project is None:
        return {"error": "La carpeta actual no es un documento de TheAIWriter."}
    if not (folder / DRAFT).exists():
        return {"error": f"Todavía no hay borrador en {DRAFT}."}
    report = validate_document(folder, suggest=True)
    return {
        "correcto": report.ok,
        "informe": report.citations.summary(),
        "huecos": report.gaps,
        "fuentes_posibles_para_huecos": [
            {"frase": gap["frase"], "claves": [source["cita"] for source in gap["fuentes"]]}
            for gap in report.gap_sources
        ],
        "palabras_por_seccion": report.words_per_section,
        "fichero": str(folder / REPORT),
    }


@tool
def verificar_documento(juez: bool = True) -> dict:
    """Verifica el borrador `borrador/documento.md` de un documento sobre Zotero. Al momento
    y sin gastar llamadas: que cada `[@clave]` exista y esté en las colecciones, y que cada
    cita literal entre comillas esté tal cual en el PDF; además escribe
    `borrador/referencias.bib`. Con `juez`, lanza en segundo plano el juez de apoyo, que
    compara cada frase citada con pasajes de la obra (una llamada a Claude por párrafo con
    citas; el resultado se consulta con `estado_verificacion`). El informe queda en
    `revision/verificacion.md`."""
    from ai_writer import verificacion

    folder = _document_folder()
    try:
        data = verificacion.check_document(folder)
        if juez and not verificacion.judge_running(data):
            data = verificacion.start_judge(folder)
    except LibraryError as error:
        return _error(error)
    return verificacion.overview(data)


@tool
def estado_verificacion() -> dict:
    """Resultado de la última verificación del borrador y cómo va el juez de apoyo: cuántas
    frases están apoyadas, parciales, tergiversadas o no apoyadas, y las que hay que
    revisar con el motivo."""
    from ai_writer import verificacion

    try:
        return verificacion.overview(verificacion.status(_document_folder()))
    except LibraryError as error:
        return _error(error)


@tool
def importar_zotero(ruta: str) -> dict:
    """Importa un `.bib` exportado de Zotero (mejor con Better BibTeX): los papers de la
    biblioteca que empareja, por DOI o por título, pasan a citarse con la clave y los datos
    de Zotero. Las entradas que no están en la biblioteca no se pueden citar y se listan."""
    from ai_writer.citations import CitationIndex

    library, _ = _current_library()
    path = Path(ruta).expanduser()
    if not path.is_file():
        return {"error": f"No existe el fichero {path}."}
    result = CitationIndex.load(library).import_zotero(path)
    shutil.copy2(path, library.root / "zotero.bib")
    return result


# Writing the document


def _document_project() -> tuple[Path, dict | None]:
    folder = _document_folder()
    if not (folder / PROJECT_FILE).exists():
        return folder, {"error": "La carpeta actual no es un documento: créalo con /theaiwriter:nuevo."}
    return folder, None


@tool
def escribir_documento(pausar_tras_plan: bool = False) -> dict:
    """Escribe el documento entero en segundo plano: temas de sus colecciones, plan,
    párrafo a párrafo con evidencia, revisión por sección, revisión global y validación de
    citas. Si se cortó o se detuvo, continúa donde se quedó. Responde al momento; el
    progreso se consulta con `estado_escritura`. Con `pausar_tras_plan` se detiene tras el
    plan (borrador/plan.md) hasta `aprobar_plan`. Necesita materiales/abstract.md."""
    from ai_writer.perspective_run import start_in_background

    folder, error = _document_project()
    if error:
        return error
    try:
        return start_in_background(folder, pause_after_plan=pausar_tras_plan)
    except (LibraryError, ValueError) as problem:
        return {"error": str(problem)}


@tool
def estado_escritura() -> dict:
    """Progreso de la escritura del documento: estado (en_curso, esperando_aprobacion,
    detenido, interrumpido, error, terminado), fase, párrafos escritos, secciones terminadas,
    llamadas al LLM, coste estimado y las últimas líneas del registro."""
    from ai_writer.perspective_run import LOG, PerspectiveRun

    folder, error = _document_project()
    if error:
        return error
    status = PerspectiveRun(folder).status()
    log = folder / LOG
    if log.exists():
        lines = [line for line in log.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
        status["registro"] = lines[-8:]
    return status


@tool
def aprobar_plan() -> dict:
    """Aprueba el plan (borrador/plan.json, con los cambios que se le hayan hecho) y sigue
    escribiendo en segundo plano."""
    from ai_writer.perspective_run import approve_plan

    folder, error = _document_project()
    if error:
        return error
    try:
        return approve_plan(folder)
    except (LibraryError, ValueError) as problem:
        return {"error": str(problem)}


@tool
def detener_escritura() -> dict:
    """Pide a la escritura en curso que se detenga al terminar el párrafo que está
    escribiendo. Se reanuda con `escribir_documento`."""
    from ai_writer.perspective_run import request_stop

    folder, error = _document_project()
    if error:
        return error
    request_stop(folder)
    return {"detener": "solicitado; se parará al terminar el párrafo en curso"}


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
