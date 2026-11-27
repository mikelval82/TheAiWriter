"""MCP tools for Claude to write with Zotero PDF passages and verify citations.

Exposes diagnostics, document setup, Zotero collections and passage consultation,
references, citation checks and document verification.

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
from pathlib import Path
from typing import Literal

from mcp.server.mcpserver import MCPServer

from ai_writer.evidencia import Fuente
from ai_writer.hallazgos import Propuesta, Seleccion
from ai_writer.library import PROJECT_FILE, LibraryError, Project

server = MCPServer("theaiwriter")


def tool(function):
    """Register a tool, routing its prints to stderr to preserve the MCP protocol."""

    @functools.wraps(function)
    def quiet(*args, **kwargs):
        with contextlib.redirect_stdout(sys.stderr):
            return function(*args, **kwargs)

    server.tool()(quiet)
    return quiet


def _document_folder() -> Path:
    return Path(os.getenv("CLAUDE_PROJECT_DIR") or os.getcwd())


def _error(error: LibraryError) -> dict:
    return {"error": str(error)}


@tool
def diagnostico() -> dict:
    """Informa de dónde corre el plugin: sistema, Python, carpetas y si `claude` está disponible."""
    from ai_writer.exportacion import pandoc_executable
    from ai_writer.zotero import Zotero, default_index_dir

    is_document = (_document_folder() / PROJECT_FILE).exists()
    try:
        zotero = Zotero()
        found = {
            "carpeta": str(zotero.root),
            "obras": len(zotero.works()),
            "con_pdf": sum(bool(w.pdfs) for w in zotero.works()),
        }
    except LibraryError as error:
        found = {"error": str(error)}
    return {
        "sistema": platform.platform(),
        "python": sys.version.split()[0],
        "carpeta_del_documento": str(_document_folder()),
        "es_un_documento": is_document,
        "zotero": found,
        "indice_de_pasajes": str(default_index_dir()),
        "claude_en_path": shutil.which("claude"),
        "pandoc": pandoc_executable(),
    }


@tool
def probar_claude() -> dict:
    """Lanza `claude -p` con haiku y devuelve si responde con la cuenta del usuario."""
    claude = shutil.which("claude")
    if claude is None:
        return {"ok": False, "error": "claude no está en el PATH del servidor"}
    start = time.monotonic()
    completed = subprocess.run(
        [
            claude,
            "-p",
            "Responde solo: ok",
            "--model",
            "haiku",
            "--output-format",
            "json",
            "--tools",
            "",
            "--no-session-persistence",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
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
def crear_documento(
    tipo: str,
    titulo: str,
    idioma: str = "es",
    colecciones: list[str] | None = None,
) -> dict:
    """Crea `proyecto.yaml` y las carpetas materiales/, borrador/, informes/ y exportacion/.
    `tipo` acepta «perspectiva», «resultados» o «convocatoria». Resultados añade resultados/
    y analisis/; convocatoria añade convocatoria/ y materiales/equipo.md.
    Las colecciones se validan contra Zotero;
    sin colecciones, el documento usa todas las obras."""
    from ai_writer.consulta import open_index, scope

    folder = _document_folder()
    try:
        project = Project.create(
            folder,
            tipo=tipo,
            titulo=titulo,
            idioma=idioma,
            colecciones=colecciones or [],
        )
        index = open_index()
        return {"documento": str(folder / PROJECT_FILE), **index.status(scope(project, index))}
    except LibraryError as error:
        return _error(error)
    except ValueError as error:
        return {"error": f"Datos no válidos: {error}"}


@tool
def guia_escritura() -> dict:
    """Lee proyecto.yaml y devuelve la guía de escritura obligatoria para su tipo."""
    from importlib.resources import files

    from ai_writer.library import is_template

    try:
        project = Project.load(_document_folder())
    except LibraryError as error:
        return _error(error)
    except ValueError as error:
        return {"error": f"Datos no válidos en proyecto.yaml: {error}"}
    guide = files("ai_writer").joinpath("guias", f"{project.tipo}.md")
    return {
        "tipo": project.tipo, "guia": guide.read_text(encoding="utf-8"),
        "abstract_vacio": is_template(_document_folder() / "materiales/abstract.md"),
    }


@tool
def estado_documento() -> dict:
    """Resume materiales, borrador, comprobación, revisión y siguiente paso, sin modelo."""
    from ai_writer.estado import document_status

    try:
        return document_status(_document_folder())
    except LibraryError as error:
        return _error(error)
    except ValueError as error:
        return {"error": f"Datos no válidos en el documento: {error}"}


def _results_folder() -> Path:
    folder = _document_folder()
    if Project.load(folder).tipo != "resultados":
        raise LibraryError("El registro de hallazgos está disponible en documentos de tipo resultados.")
    return folder


@tool
def estado_hallazgos(incluir_materiales: bool = True) -> dict:
    """Lista los hallazgos con su evidencia y versión. Puede incluir los archivos del estudio."""
    from ai_writer.evidencia import inventory
    from ai_writer.hallazgos import list_findings

    try:
        folder = _results_folder()
        report = {"hallazgos": list_findings(folder)}
        if incluir_materiales:
            report["materiales"] = inventory(folder)
        return report
    except (LibraryError, ValueError) as error:
        return {"error": str(error)}


@tool
def leer_evidencia_resultados(fuente: Fuente) -> dict:
    """Lee una celda CSV, un fragmento literal de una salida de Jupyter o una línea de resultados."""
    from ai_writer.evidencia import read_source

    try:
        evidence = read_source(_results_folder(), fuente)
        evidence.pop("codigo", None)
        return evidence
    except (LibraryError, ValueError) as error:
        return {"error": str(error)}


@tool
def guardar_hallazgos(propuestas: list[Propuesta]) -> dict:
    """Registra propuestas sin aprobar. Para editar, usa el id y la versión en sustituye."""
    from ai_writer.hallazgos import save_findings

    try:
        return {"hallazgos": save_findings(_results_folder(), propuestas)}
    except (LibraryError, ValueError) as error:
        return {"error": str(error)}


@tool
def decidir_hallazgos(seleccion: list[Seleccion], decision: Literal["aprobado", "pendiente"]) -> dict:
    """Guarda una decisión explícita del investigador usando el id y versión de cada hallazgo mostrado."""
    from ai_writer.hallazgos import decide_findings

    try:
        return {"hallazgos": decide_findings(_results_folder(), seleccion, decision)}
    except (LibraryError, ValueError) as error:
        return {"error": str(error)}


@tool
def mostrar_ficha() -> str:
    """Muestra la ficha de convocatoria o revista como texto legible, sin modelo."""
    from ai_writer.convocatoria import ficha_text

    try:
        return ficha_text(_document_folder())
    except (LibraryError, ValueError) as error:
        return str(error)


@tool
def confirmar_ficha(revision: str | None = None) -> dict:
    """Confirma tras el sí. En convocatoria pasa la revisión devuelta por comprobar_ficha."""
    from ai_writer.convocatoria import confirm_ficha

    return confirm_ficha(_document_folder(), revision)


@tool
def comprobar_ficha() -> dict:
    """Comprueba la ficha contra sus PDF, sin modelo. En convocatoria devuelve revisión y reglas."""
    from ai_writer.convocatoria import JOURNAL_FICHA, check_ficha, check_journal_ficha

    folder = _document_folder()
    try:
        project = Project.load(folder)
    except LibraryError as error:
        return _error(error)
    except ValueError as error:
        return {"error": f"Datos no válidos en proyecto.yaml: {error}"}
    if project.tipo != "convocatoria" and (folder / JOURNAL_FICHA).exists():
        return check_journal_ficha(folder)
    return check_ficha(folder)


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
            {
                "ruta": c.path,
                "obras": len(keys := zotero.item_keys([c.key])),
                "con_pdf": sum(bool(zotero.work(key).pdfs) for key in keys),
            }
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


# References and citation checks


@tool
def referencia(clave: str) -> dict:
    """Datos de una obra de Zotero: título, autores, año, revista, DOI, BibTeX,
    pasajes disponibles y si está en las colecciones del documento."""
    from ai_writer.consulta import reference

    try:
        index, _, allowed = _zotero_document()
        found = reference(index, clave.lstrip("@"), allowed)
    except LibraryError as error:
        return _error(error)
    return found or {"error": f"La clave «{clave}» no existe en Zotero."}


@tool
def exportar_documento(
    estilo_csl: str | None = None, plantilla_docx: str | None = None, reemplazar: bool = False,
) -> dict:
    """Genera exportacion/documento.docx desde el borrador con Pandoc, sin modelo.
    El estilo y la plantilla son archivos del proyecto. Reemplaza solo cuando se indica."""
    from ai_writer.exportacion import export_document

    try:
        return export_document(
            _document_folder(), style=estilo_csl, template=plantilla_docx,
            replace_existing=reemplazar,
        )
    except (LibraryError, OSError, ValueError) as error:
        return {"error": str(error)}


@tool
def preparar_citas_vivas() -> dict:
    """Escribe `exportacion/documento-zotero.md`, una copia del borrador con las claves que cada
    obra tiene guardadas en Zotero (las de Better BibTeX), para pasarla a Word con citas vivas
    según `docs/exportar.md`. No cambia el borrador ni Zotero. `sin_clave_en_zotero` son las
    obras citadas que aún no tienen clave allí: el filtro no las convertirá."""
    from ai_writer.consulta import live_citations_draft

    try:
        index, _, _ = _zotero_document()
        return live_citations_draft(_document_folder(), index)
    except LibraryError as error:
        return _error(error)


@tool
def comprobar_citas(texto: str) -> dict:
    """Comprueba que cada `[@clave]` exista en Zotero y esté en las colecciones del
    documento. Úsala antes de dar por bueno cualquier texto con citas."""
    from ai_writer.verificacion import check_citations

    try:
        index, _, allowed = _zotero_document()
        report = check_citations(texto, index, allowed)
    except LibraryError as error:
        return _error(error)
    bad = report["desconocidas"] + report["fuera_de_las_colecciones"] + report["mal_formadas"]
    return {"correcto": not bad, **report}


@tool
def comprobar_documento(juez: bool = True) -> dict:
    """Verifica el borrador `borrador/documento.md` de un documento sobre Zotero. Al momento
    y sin gastar llamadas: que cada `[@clave]` exista y esté en las colecciones, y que cada
    cita literal entre comillas esté tal cual en el PDF; en documentos de tipo resultados,
    coteja las frases enlazadas con los hallazgos aprobados o busca las cifras de borradores
    anteriores en resultados/. En convocatorias,
    comprueba la ficha contra los PDF oficiales y la conformidad del borrador. Además escribe
    `borrador/referencias.bib`. Con `juez`, lanza en segundo plano el juez de apoyo, que
    compara cada frase citada con pasajes de la obra (una llamada a Claude por párrafo con
    citas; el resultado se consulta con `estado_comprobacion`). El informe queda en
    `informes/comprobacion.md`."""
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
def estado_comprobacion() -> dict:
    """Resultado de la última verificación del borrador y cómo va el juez de apoyo: cuántas
    frases están apoyadas, parciales, tergiversadas o no apoyadas, y las que hay que
    revisar con el motivo."""
    from ai_writer import verificacion

    try:
        Project.load(_document_folder())
        return verificacion.overview(verificacion.status(_document_folder()))
    except LibraryError as error:
        return _error(error)


@tool
def evidencia_citas(frase: str = "", seccion: str = "", desde: int = 0, limite: int = 12) -> dict:
    """Muestra los veredictos guardados y sus pasajes de Zotero, incluidas las citas apoyadas.
    Filtra por un fragmento de la frase o por el nombre del apartado. No lanza el juez."""
    from ai_writer.verificacion import citation_evidence

    try:
        return citation_evidence(
            _document_folder(), phrase=frase, section=seccion, offset=desde, limit=limite
        )
    except (LibraryError, ValueError, OSError) as error:
        return {"error": str(error)}


@tool
def revisar_documento() -> dict:
    """Evalúa el borrador por criterios en segundo plano con una llamada a Claude.
    No cambia el borrador. El resultado se consulta con `estado_revision` y queda en
    `informes/revision.md`. Usa la ficha confirmada de convocatoria o revista, o los
    criterios genéricos del tipo si no hay revista."""
    from ai_writer import revisor

    try:
        return revisor.start_review(_document_folder())
    except LibraryError as error:
        return _error(error)


@tool
def estado_revision() -> dict:
    """Devuelve el estado, las prioridades y la evaluación por criterios de la revisión."""
    from ai_writer import revisor

    try:
        Project.load(_document_folder())
        return revisor.review_status(_document_folder())
    except LibraryError as error:
        return _error(error)


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
