"""Checks of a document's draft: citations, pending gaps and length per section.

Imports nothing heavy (no embeddings), so the plugin's hook can run it after every edit.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from ai_writer.citations import CitationIndex, CitationReport, check_citations
from ai_writer.library import Project

DRAFT = Path("borrador") / "documento.md"
RETRIEVED = Path("revision") / "evidencia.json"
REPORT = Path("revision") / "validacion.md"
PENDING_GAP = re.compile(r"\[\[PENDIENTE[^\]]*\]\]")
_HEADING = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.M)


@dataclass
class DocumentReport:
    citations: CitationReport
    gaps: list[str] = field(default_factory=list)
    words_per_section: dict[str, int] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.citations.ok

    def markdown(self) -> str:
        lines = ["# Validación del borrador", "", "## Citas", "", self.citations.summary(), ""]
        lines += ["## Huecos pendientes", ""]
        lines += [f"- {gap}" for gap in self.gaps] or ["Ninguno."]
        lines += ["", "## Extensión por sección", "", "| Sección | Palabras |", "|---|---|"]
        lines += [f"| {name} | {words} |" for name, words in self.words_per_section.items()]
        return "\n".join(lines) + "\n"


def retrieved_keys(folder: Path) -> set[str] | None:
    """Keys returned by evidence searches for this document; ``None`` if none were made."""
    path = Path(folder) / RETRIEVED
    if not path.exists():
        return None
    return set(json.loads(path.read_text(encoding="utf-8")))


def record_retrieved(folder: Path, query: str, keys: list[str]) -> None:
    """Remember which works a search returned, to warn about citations never retrieved."""
    path = Path(folder) / RETRIEVED
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for key in keys:
        queries = data.setdefault(key, [])
        if query not in queries:
            queries.append(query)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check_text(text: str, folder: Path) -> CitationReport:
    """Check the citations of a text written for the document in ``folder``."""
    project = Project.load(folder)
    library = project.library()
    index = CitationIndex.load(library)
    allowed = index.keys_for_papers(project.paper_ids())
    return check_citations(text, index, allowed, retrieved_keys(folder))


def validate_document(folder: Path, write_report: bool = True) -> DocumentReport:
    """Validate ``borrador/documento.md`` and write ``revision/validacion.md``."""
    folder = Path(folder)
    text = (folder / DRAFT).read_text(encoding="utf-8")
    report = DocumentReport(
        citations=check_text(text, folder),
        gaps=PENDING_GAP.findall(text),
        words_per_section=_words_per_section(text),
    )
    if write_report:
        (folder / REPORT).parent.mkdir(parents=True, exist_ok=True)
        (folder / REPORT).write_text(report.markdown(), encoding="utf-8")
    return report


def _words_per_section(text: str) -> dict[str, int]:
    headings = list(_HEADING.finditer(text))
    # A level-1 heading opening the text is the document's title, not a section
    if headings and headings[0].start() == 0 and headings[0].group(1) == "#" and len(headings) > 1:
        text = text[headings[0].end():]
        headings = list(_HEADING.finditer(text))
    sections = {}
    if headings and _words(text[: headings[0].start()]):
        sections["(antes del primer título)"] = _words(text[: headings[0].start()])
    for i, heading in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        sections[heading.group(2)] = _words(text[heading.end():end])
    if not headings:
        sections["(documento)"] = _words(text)
    return sections


def _words(text: str) -> int:
    text = PENDING_GAP.sub("", re.sub(r"\[[^\]]*@[^\]]*\]", "", text))
    return len(re.findall(r"\w+", text))
