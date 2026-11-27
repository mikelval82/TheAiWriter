"""Audit manuscript statements against the wording and evidence approved by the researcher."""

import re

from ai_writer.cifras import _CITATION, _HEADING, _NUMBER, _prose, lines_without_code, restore_prose
from ai_writer.hallazgos import normalize_statement
from ai_writer.sentences import split_sentences

_TOKEN = re.compile(
    r"(?P<ticks>`+)(?!`).+?(?<!`)(?P=ticks)(?!`)|(?P<comment><!--.*?(?:-->|$))"
)
_MARKER_PREFIX = re.compile(r"<!--\s*hallazgo\s*:", re.IGNORECASE)
_MARKER = re.compile(r"<!--\s*hallazgo\s*:\s*([1-9][0-9]{0,17})\s*-->\s*$", re.IGNORECASE)
_RESULT_SECTION = re.compile(r"^(?:\d+(?:\.\d+)*[.)]?\s+)?(?:resultados|results)\b", re.I)
_REFERENCE = re.compile(
    r"\b(?:fig(?:ura|ure)?\.?|tabla|table|anexo|appendix|ecuación|equation)\s+s?\d+(?:\.\d+)*\b",
    re.I,
)


def _markdown_lines(text: str):
    """Yield line number, visible text and finding comments outside code or block comments."""
    in_comment = False
    for number, source in enumerate(lines_without_code(text), 1):
        if in_comment:
            end = source.find("-->")
            if end == -1:
                continue
            source = source[end + 3:]
            in_comment = False
        markers = []

        def remove_comment(match: re.Match) -> str:
            nonlocal in_comment
            comment = match["comment"]
            if comment is None:
                return match.group()
            in_comment = not comment.endswith("-->")
            if _MARKER_PREFIX.match(comment):
                markers.append((comment, source[match.end():].strip()))
            return " "

        content = _TOKEN.sub(remove_comment, source).strip()
        if content or markers:
            yield number, content, markers


def _link(line: int, section: str, text: str, markers: list, registry: dict) -> dict:
    entry = {"linea": line, "seccion": section, "frase": text}
    match = _MARKER.fullmatch(markers[0][0])
    if len(markers) != 1 or match is None or markers[0][1] or not text:
        return {
            **entry, "estado": "marca_invalida",
            "motivo": "Pon una frase y un solo vínculo al final de la línea.",
        }
    finding_id = int(match[1])
    entry["id"] = finding_id
    finding = registry.get(finding_id)
    if finding is None:
        return {**entry, "estado": "desconocido", "motivo": "El hallazgo no existe en el registro."}
    entry.update(fuente=finding["fuente"], enunciado=finding["enunciado"],
                 valor=finding["valor"], grupo=finding.get("grupo"), unidad=finding.get("unidad"))
    if finding["estado"] != "aprobado":
        return {
            **entry, "estado": finding["estado"],
            "motivo": finding.get("aviso") or "La evidencia requiere una decisión en /theaiwriter:hallazgos.",
        }
    if normalize_statement(text) != normalize_statement(finding["enunciado"]):
        return {
            **entry, "estado": "frase_cambiada",
            "motivo": "La frase difiere de la aprobada. Restaura el enunciado o aprueba su nueva formulación.",
        }
    return {**entry, "estado": "coincide"}


def check_findings(text: str, findings: list[dict]) -> dict | None:
    """Compare each linked line with the approved statement. Flag unlinked result numbers."""
    if not findings and not _MARKER_PREFIX.search(text):
        return None
    registry = {finding["id"]: finding for finding in findings}
    approved = {normalize_statement(finding["enunciado"]) for finding in findings
                if finding["estado"] == "aprobado"}
    section, in_results = "", False
    links, unlinked = [], []
    for number, source, markers in _markdown_lines(text):
        if heading := _HEADING.fullmatch(source):
            level, title = len(heading[1]), heading[2]
            section = title
            if level <= 2 or _RESULT_SECTION.match(title):
                in_results = bool(_RESULT_SECTION.match(title))
            if not markers:
                continue
        if markers:
            links.append(_link(number, section, source, markers, registry))
        elif in_results and not source.startswith(("|", "![")):
            prose, hidden = _prose(source)
            for sentence in split_sentences(prose):
                numeric = _NUMBER.search(_REFERENCE.sub("", _CITATION.sub("", sentence)))
                restored = restore_prose(sentence, hidden)
                if numeric or normalize_statement(restored) in approved:
                    unlinked.append({"linea": number, "seccion": section, "frase": restored})

    if not registry and not links:
        return None  # preserve the legacy number check for projects without finding links
    versions = {
        str(link["id"]): registry.get(link["id"], {}).get("version")
        for link in links if "id" in link
    }
    matched = sum(link["estado"] == "coincide" for link in links)
    return {
        "coinciden": matched,
        "por_revisar": len(links) - matched,
        "vinculos": links,
        "sin_vinculo": unlinked,
        "versiones": versions,
    }


def findings_changed(report: dict | None, findings: list[dict]) -> bool:
    """Check the current versions of the findings referenced by a saved report."""
    if report is None:
        return bool(findings)
    versions = {str(finding["id"]): finding["version"] for finding in findings}
    return any(versions.get(key) != old for key, old in report["versiones"].items())


def report_counts(report: dict) -> dict:
    return {
        "coinciden": report["coinciden"],
        "por_revisar": report["por_revisar"],
        "sin_vinculo": len(report["sin_vinculo"]),
    }


def _source_label(source: dict) -> str:
    file = source["archivo"]
    if source["tipo"] == "csv":
        return f"{file} · fila {source['fila']}, columna «{source['columna']}»"
    if source["tipo"] == "cuaderno":
        return f"{file} · celda {source['celda']}, salida {source['salida']}"
    return f"{file} · línea {source['linea']}"


def report_lines(report: dict) -> list[str]:
    lines = [
        "", "## Hallazgos del estudio", "",
        f"{report['coinciden']} frases coinciden con el texto y la evidencia aprobados. "
        f"{report['por_revisar']} vínculos por revisar y "
        f"{len(report['sin_vinculo'])} frases de Resultados por vincular.",
        "",
    ]
    for entry in report["vinculos"]:
        label = "Coincide" if entry["estado"] == "coincide" else "Revisar vínculo"
        finding = f", hallazgo {entry['id']}" if "id" in entry else ""
        lines.append(f"- **{label}** (línea {entry['linea']}{finding}) «{entry['frase']}»")
        if "fuente" in entry:
            lines.append(f"  - Fuente · {_source_label(entry['fuente'])}")
            if entry.get("grupo"):
                lines.append(f"  - Grupo registrado · {entry['grupo']}")
        if "motivo" in entry:
            lines.append(f"  - {entry['motivo']}")
        if entry["estado"] == "frase_cambiada":
            lines.append(f"  - Frase aprobada · «{entry['enunciado']}»")
    for entry in report["sin_vinculo"]:
        lines.append(f"- **Por vincular** (línea {entry['linea']}) «{entry['frase']}»")
    return lines
