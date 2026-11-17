"""Check official call requirements and draft conformity, without any model."""

import re
import unicodedata
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

import fitz
import yaml
from pydantic import BaseModel, Field, model_validator

from ai_writer.library import LibraryError
from ai_writer.passages import page_texts

FICHA = Path("convocatoria") / "ficha.yaml"
JOURNAL_FICHA = Path("revista") / "ficha.yaml"
_HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)(?:\s+#+)?\s*$")


class Source(BaseModel):
    fichero: str = Field(min_length=1)
    pagina: int = Field(ge=1)
    cita: str = Field(min_length=1)


class CallSection(BaseModel):
    titulo: str = Field(min_length=1)
    nivel: Literal[2, 3]
    obligatorio: bool
    condicion: str | None = None
    pide: str
    criterios: list[str] = Field(default_factory=list)
    fuente: Source


class FieldLimit(BaseModel):
    nombre: str = Field(min_length=1)
    caracteres: int = Field(gt=0)
    apartado: str | None = None
    fuente: Source


class Limits(BaseModel):
    paginas: int | None = Field(default=None, gt=0)
    palabras_por_pagina: int = Field(default=500, gt=0)
    fuente: Source | None = None
    campos: list[FieldLimit] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_page_source(self):
        if self.paginas is not None and self.fuente is None:
            raise ValueError("limites.fuente es obligatoria si hay un límite de páginas")
        return self


class LanguageRule(BaseModel):
    regla: str
    fuente: Source


class Criterion(BaseModel):
    nombre: str = Field(min_length=1)
    maximo: float | None = Field(default=None, ge=0)
    umbral: float | None = Field(default=None, ge=0)
    descripcion: str
    fuente: Source


class CallFicha(BaseModel):
    convocatoria: str = Field(min_length=1)
    confirmada: bool = False
    plazo: str | None = None
    apartados: list[CallSection]
    limites: Limits
    idioma: LanguageRule | None = None
    criterios: list[Criterion] = Field(default_factory=list)

    @classmethod
    def load(cls, folder: Path) -> "CallFicha":
        path = Path(folder) / FICHA
        if not path.exists():
            raise LibraryError(f"No hay ficha de la convocatoria: falta {FICHA}.")
        try:
            return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
        except (OSError, ValueError, yaml.YAMLError) as error:
            raise LibraryError(f"La ficha {FICHA} no es válida: {error}") from error


class JournalFicha(BaseModel):
    revista: str = Field(min_length=1)
    confirmada: bool = False
    criterios: list[Criterion] = Field(min_length=1)

    @classmethod
    def load(cls, folder: Path) -> "JournalFicha":
        path = Path(folder) / JOURNAL_FICHA
        if not path.exists():
            raise LibraryError(f"No hay ficha de la revista: falta {JOURNAL_FICHA}.")
        try:
            return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
        except (OSError, ValueError, yaml.YAMLError) as error:
            raise LibraryError(f"La ficha {JOURNAL_FICHA} no es válida: {error}") from error


def _sources(ficha: CallFicha):
    for i, section in enumerate(ficha.apartados):
        yield f"apartados[{i}].fuente ({section.titulo})", section.fuente
    if ficha.limites.fuente is not None:
        yield "limites.fuente", ficha.limites.fuente
    for i, field in enumerate(ficha.limites.campos):
        yield f"limites.campos[{i}].fuente ({field.nombre})", field.fuente
    if ficha.idioma is not None:
        yield "idioma.fuente", ficha.idioma.fuente
    for i, criterion in enumerate(ficha.criterios):
        yield f"criterios[{i}].fuente ({criterion.nombre})", criterion.fuente


def check_ficha(folder: Path) -> dict:
    """Validate a ficha and locate each requirement's quotation in its official PDF."""
    try:
        ficha = CallFicha.load(folder)
    except LibraryError as error:
        return {"error": str(error)}
    return check_sources(folder, "convocatoria", _sources(ficha), ficha.confirmada)


def check_journal_ficha(folder: Path) -> dict:
    """Validate a journal ficha and locate its criteria's quotations in the PDFs."""
    try:
        ficha = JournalFicha.load(folder)
    except LibraryError as error:
        return {"error": str(error)}
    sources = ((f"criterios[{i}].fuente ({c.nombre})", c.fuente)
               for i, c in enumerate(ficha.criterios))
    return check_sources(folder, "revista", sources, ficha.confirmada)


def check_sources(
    folder: Path, subfolder: str, sources: Iterable[tuple[str, Source]], confirmada: bool
) -> dict:
    """Locate each source's literal quotation inside its PDF folder."""
    from ai_writer.verificacion import verbatim

    root = (Path(folder) / subfolder).resolve()
    report = {
        "requisitos": 0, "comprobados": 0, "fallidos": [], "avisos": [],
        "confirmada": confirmada,
    }
    texts = {}
    for location, source in sources:
        report["requisitos"] += 1
        entry = {"donde": location, **source.model_dump()}
        path = (root / source.fichero).resolve()
        failure = None
        if not path.is_relative_to(root) or path.suffix.lower() != ".pdf" or not path.is_file():
            failure = f"El fichero debe existir dentro de {subfolder}/ y ser PDF."
        elif len(source.cita.split()) < 6:
            failure = "La cita debe tener al menos 6 palabras."
        else:
            if path not in texts:
                try:
                    with fitz.open(path) as doc:
                        if not doc.is_pdf:
                            raise ValueError("El fichero no es un PDF")
                        texts[path] = page_texts(doc)
                except (OSError, ValueError, RuntimeError) as error:
                    texts[path] = f"No se pudo leer el PDF: {error}"
            pages = texts[path]
            if isinstance(pages, str):
                failure = pages
            elif not verbatim(source.cita, "\n\n".join(pages))[0]:
                failure = "La cita no aparece palabra por palabra en el PDF."
            else:
                report["comprobados"] += 1
                nearby = pages[max(0, source.pagina - 2):source.pagina + 1]
                if not verbatim(source.cita, "\n\n".join(nearby))[0]:
                    report["avisos"].append({
                        **entry,
                        "motivo": "La cita está en el PDF, pero no en la página indicada ±1.",
                    })
        if failure:
            report["fallidos"].append({**entry, "motivo": failure})
    return report


def _normalize(title: str) -> str:
    title = "".join(
        c for c in unicodedata.normalize("NFD", title.lower())
        if not unicodedata.combining(c)
    )
    title = re.sub(r"^\s*\d+(?:\.\d+)*(?:[.)]\s*|\s+)", "", title)
    title = " ".join(title.split())
    while title and unicodedata.category(title[-1]).startswith("P"):
        title = title[:-1].rstrip()
    return title


def _draft_lines(text: str) -> list[str]:
    lines, fence, width = [], "", 0
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if (marker and marker[1][0] == fence and len(marker[1]) >= width
                    and not marker[2].strip()):
                fence = ""
        elif marker:
            fence, width = marker[1][0], len(marker[1])
        elif not line.startswith(("    ", "\t")):
            lines.append(line)
    return lines


def check_call(text: str, ficha: CallFicha | dict) -> dict:
    """Compare headings, length, character limits and pending marks with a validated ficha."""
    if not isinstance(ficha, CallFicha):
        ficha = CallFicha.model_validate(ficha)
    lines = _draft_lines(text)
    headings, words, pending = [], [], []
    section = ""
    for i, line in enumerate(lines):
        heading = _HEADING.match(line)
        if heading:
            level, section = len(heading[1]), heading[2]
            headings.append({"titulo": section, "nivel": level, "line": i})
            if level != 1:
                words.extend(section.split())
        else:
            words.extend(line.split())
        for match in re.finditer(r"\[PENDIENTE:\s*([^\]]+)\]", line):
            pending.append({"marca": match.group(), "seccion": section})

    expected = {_normalize(s.titulo): i for i, s in enumerate(ficha.apartados)}
    present = [h for h in headings if h["nivel"] in (2, 3)]
    titles = {_normalize(h["titulo"]) for h in present}
    missing = [s.titulo for s in ficha.apartados
               if s.obligatorio and _normalize(s.titulo) not in titles]
    conditional = [{"titulo": s.titulo, "condicion": s.condicion} for s in ficha.apartados
                   if not s.obligatorio and _normalize(s.titulo) not in titles]
    extra = [h["titulo"] for h in present if _normalize(h["titulo"]) not in expected]
    order, last = True, -1
    for heading in present:
        position = expected.get(_normalize(heading["titulo"]))
        if position is not None:
            if position <= last:
                order = [heading["titulo"]]
                break
            last = position

    count = len(words)
    maximum = ficha.limites.paginas
    capacity = maximum * ficha.limites.palabras_por_pagina if maximum is not None else None
    state = ("sin_limite" if capacity is None else "excedido" if count > capacity
             else "aviso" if count >= capacity * 0.9 else "ok")
    fields, manual = [], []
    for field in ficha.limites.campos:
        if field.apartado is None:
            manual.append({"nombre": field.nombre, "maximo": field.caracteres})
            continue
        heading = next((h for h in present
                        if _normalize(h["titulo"]) == _normalize(field.apartado)), None)
        characters = None
        if heading is not None:
            end = next((h["line"] for h in headings
                        if h["line"] > heading["line"] and h["nivel"] <= heading["nivel"]),
                       len(lines))
            body = "\n".join(line for line in lines[heading["line"] + 1:end]
                             if not _HEADING.match(line)).strip()
            characters = len(body)
        fields.append({
            "nombre": field.nombre, "apartado": field.apartado,
            "caracteres": characters, "maximo": field.caracteres,
            "estado": ("ausente" if characters is None else
                       "excedido" if characters > field.caracteres else "ok"),
        })
    return {
        "faltan": missing, "condicionales_ausentes": conditional, "sobran": extra,
        "orden": order,
        "extension": {"palabras": count,
                      "paginas_estimadas": round(count / ficha.limites.palabras_por_pagina, 1),
                      "maximo": maximum, "estado": state},
        "campos": fields, "a_mano": manual, "pendientes": pending,
    }


def report_lines(ficha: dict, call: dict) -> list[str]:
    """The call section of the verification report, including manual checks."""
    lines = ["", "## Convocatoria", ""]
    if "error" in ficha:
        lines.append(ficha["error"])
    else:
        confirmed = "sí" if ficha["confirmada"] else "no; falta la confirmación del usuario"
        lines.append(
            f"Ficha: {ficha['comprobados']} de {ficha['requisitos']} requisitos comprobados; "
            f"{len(ficha['fallidos'])} fallidos. Confirmada: {confirmed}."
        )
        for name, label in (("fallidos", "Fallido"), ("avisos", "Aviso")):
            for entry in ficha[name]:
                lines.append(
                    f"- **{label}** en {entry['donde']} ({entry['fichero']}, "
                    f"p. {entry['pagina']}): {entry['motivo']} Cita: «{entry['cita']}»"
                )
    if "aviso" in call:
        lines.append(call["aviso"])
    else:
        lines.append(
            "Apartados obligatorios que faltan: " + (", ".join(call["faltan"]) or "ninguno")
        )
        for entry in call["condicionales_ausentes"]:
            lines.append(
                f"- Condicional ausente: {entry['titulo']}. "
                f"Condición: {entry['condicion'] or 'no indicada'}."
            )
        if call["sobran"]:
            lines.append("Encabezados que sobran: " + ", ".join(call["sobran"]))
        lines.append("Orden: " + ("correcto." if call["orden"] is True else
                                  "primer apartado fuera de sitio: " + ", ".join(call["orden"])))
        length = call["extension"]
        maximum = length["maximo"] if length["maximo"] is not None else "sin límite"
        lines.append(
            f"Extensión: {length['palabras']} palabras; {length['paginas_estimadas']:.1f} "
            f"páginas estimadas; máximo: {maximum}. Estado: {length['estado']}."
        )
        lines.append("Campos con límite de caracteres:")
        for entry in call["campos"]:
            characters = (
                entry["caracteres"] if entry["caracteres"] is not None else "apartado ausente"
            )
            lines.append(
                f"- {entry['nombre']} ({entry['apartado']}): {characters} / "
                f"{entry['maximo']} caracteres; {entry['estado']}."
            )
        for entry in call["a_mano"]:
            lines.append(f"- A mano: {entry['nombre']}, máximo {entry['maximo']} caracteres.")
        if not call["campos"] and not call["a_mano"]:
            lines.append("No hay campos con límite de caracteres.")
        lines.append(f"Pendientes: {len(call['pendientes'])}.")
        for entry in call["pendientes"]:
            lines.append(f"- {entry['seccion'] or 'sin sección'}: {entry['marca']}")
    lines += [
        "", "La extensión es una estimación por palabras: hay que comprobar las páginas reales "
        "en la plantilla oficial.",
    ]
    return lines
