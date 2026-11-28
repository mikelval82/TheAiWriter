"""Convert the Markdown manuscript to a final DOCX using local Pandoc."""

import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

from ai_writer.citations import find_citations
from ai_writer.consulta import BIBLIOGRAPHY, DRAFT
from ai_writer.library import LibraryError, Project

WORD_DOCUMENT = Path("exportacion") / "documento.docx"
PANDOC_GUIDE = "https://pandoc.org/installing.html"


def pandoc_executable() -> str | None:
    return shutil.which(os.environ.get("THEAIWRITER_PANDOC") or "pandoc")


def _project_file(folder: Path, name: str, suffix: str, label: str) -> Path:
    path = (folder / name).resolve()
    if not path.is_relative_to(folder) or path.suffix.lower() != suffix or not path.is_file():
        raise LibraryError(f"Indica {label} con extensión {suffix} dentro de la carpeta del proyecto.")
    return path


def _check_docx(path: Path) -> None:
    try:
        with ZipFile(path) as docx:
            if {"[Content_Types].xml", "word/document.xml"}.issubset(docx.namelist()):
                return
    except (BadZipFile, OSError):
        pass
    raise LibraryError("Pandoc no produjo un DOCX válido.")


def export_status(folder: Path, draft: Path) -> dict:
    """Report the local Word copy and whether its Markdown or bibliography changed."""
    output = folder / WORD_DOCUMENT
    state = "sin hacer"
    if output.is_file():
        exported = output.stat().st_mtime_ns
        sources = (draft, folder / BIBLIOGRAPHY)
        state = "desactualizada" if any(
            source.is_file() and source.stat().st_mtime_ns > exported for source in sources
        ) else "terminada"
    return {"estado": state, "documento": WORD_DOCUMENT.as_posix()}


def export_document(
    folder: Path, *, style: str | None = None, template: str | None = None,
    replace_existing: bool = False,
) -> dict:
    """Export a snapshot of the manuscript. Keep previous outputs on errors."""
    folder = folder.resolve()
    project = Project.load(folder)
    draft = folder / DRAFT
    if not draft.is_file() or not (text := draft.read_text(encoding="utf-8")).strip():
        raise LibraryError("Falta el borrador. Usa /theaiwriter:escribir antes de exportar.")

    output = folder / WORD_DOCUMENT
    if not output.parent.resolve().is_relative_to(folder):
        raise LibraryError("La carpeta exportacion/ debe estar dentro del proyecto.")
    existing = f"Ya existe {WORD_DOCUMENT.as_posix()}. Usa /theaiwriter:exportar reemplazar si quieres actualizarlo."
    if not replace_existing and (output.exists() or output.is_symlink()):
        raise LibraryError(existing)

    executable = pandoc_executable()
    if not executable:
        raise LibraryError(
            "Pandoc no está disponible. Instálalo o indica su ruta con THEAIWRITER_PANDOC "
            f"y vuelve a abrir Claude Code. {PANDOC_GUIDE}"
        )

    bibliography = folder / BIBLIOGRAPHY
    references = bibliography.read_bytes() if bibliography.is_file() else None
    if find_citations(text)[0] and references is None:
        raise LibraryError(
            f"Falta {BIBLIOGRAPHY}. Usa /theaiwriter:comprobar sin juez para generar la bibliografía."
        )

    options = [
        "--from=markdown", "--to=docx", "--standalone", "--citeproc", "--strip-comments",
        "--resource-path=" + os.pathsep.join(("borrador", ".", "resultados")),
        "--metadata", f"lang={project.idioma}",
        "--metadata", "reference-section-title=" + (
            "Referencias" if project.idioma.lower().split("-", 1)[0] == "es" else "References"
        ),
    ]
    if style is not None:
        options.extend(("--csl", str(_project_file(folder, style, ".csl", "un estilo CSL"))))
    if template is not None:
        options.extend(("--reference-doc", str(_project_file(folder, template, ".docx", "una plantilla"))))

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=".theaiwriter-", dir=output.parent) as tmp:
            pending = Path(tmp) / output.name
            if references is not None:
                snapshot = Path(tmp) / bibliography.name
                snapshot.write_bytes(references)
                options.extend(("--bibliography", str(snapshot)))
            result = subprocess.run(
                [executable, *options, "--output", str(pending)], cwd=folder, input=text,
                capture_output=True, encoding="utf-8", errors="replace", timeout=120, check=False,
            )
            if result.returncode:
                detail = result.stderr.strip()[:2000]
                raise LibraryError(f"Pandoc no pudo convertir el borrador. {detail}".strip())
            _check_docx(pending)
            current_references = bibliography.read_bytes() if bibliography.is_file() else None
            if not draft.is_file() or draft.read_text(encoding="utf-8") != text or current_references != references:
                raise LibraryError("El borrador o la bibliografía cambiaron durante la exportación. Vuelve a exportar.")
            if replace_existing:
                pending.replace(output)
            else:
                os.link(pending, output)
    except FileExistsError as error:
        raise LibraryError(existing) from error
    except subprocess.TimeoutExpired as error:
        raise LibraryError("Pandoc tardó más de dos minutos. Revisa las figuras y vuelve a intentarlo.") from error
    except OSError as error:
        raise LibraryError(f"No se pudo guardar el DOCX. Comprueba que puedas escribir en exportacion/. {error}") from error
    return {"documento": WORD_DOCUMENT.as_posix(), "avisos": result.stderr.strip()[:4000]}
