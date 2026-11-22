"""A document's view of Zotero: the works it may cite, what it has consulted, its bibliography."""

import html
import json
import re
from pathlib import Path

from ai_writer.citations import find_citations, replace_keys
from ai_writer.library import LibraryError, Project
from ai_writer.passages import ID_SEPARATOR, PassageIndex
from ai_writer.zotero import DATABASE, Work, Zotero

CONSULTED = "informes/consultas.json"
BIBLIOGRAPHY = "borrador/referencias.bib"
DRAFT = "borrador/documento.md"
LIVE_DRAFT = "exportacion/documento-zotero.md"
_ENTRY_TYPES = {
    "journalArticle": "article",
    "conferencePaper": "inproceedings",
    "book": "book",
    "bookSection": "incollection",
    "thesis": "phdthesis",
}
_MARKUP = {
    "i": "textit",
    "b": "textbf",
    "sub": "textsubscript",
    "sup": "textsuperscript",
    "scp": "textsc",
}
_SMALL_CAPS = re.compile(r'<span style="font-variant:\s*small-caps;?">(.*?)</span>', re.S)

_indexes: dict[tuple, PassageIndex] = {}


def open_index(root: Path | None = None) -> PassageIndex:
    """The passage index of the local Zotero, reloaded when Zotero's database changes."""
    from ai_writer.zotero import data_dir

    zotero_root = data_dir()
    stamps = tuple(
        file.stat().st_mtime_ns if file.exists() else 0
        for file in (zotero_root / DATABASE, zotero_root / f"{DATABASE}-wal")
    )
    cache_key = (str(zotero_root), str(root), stamps)
    if cache_key not in _indexes:
        _indexes.clear()
        _indexes[cache_key] = PassageIndex(Zotero(zotero_root), root)
    return _indexes[cache_key]


def scope(project: Project | None, index: PassageIndex) -> set[str] | None:
    """Zotero item keys the document may cite; ``None`` outside a document: everything."""
    if project is None or not project.colecciones:
        return None
    return index.zotero.item_keys(project.colecciones)


def record(folder: Path, query: str | None, ids: list[str]) -> None:
    """Remember the passages a search (or a read, ``query`` None) put before the writer."""
    path = Path(folder) / CONSULTED
    data = (
        json.loads(path.read_text(encoding="utf-8"))
        if path.exists()
        else {"consultas": [], "pasajes": []}
    )
    if query:
        data["consultas"].append({"consulta": query, "pasajes": ids})
    data["pasajes"] = list(dict.fromkeys(data["pasajes"] + ids))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def consulted(folder: Path) -> dict[str, list[int]]:
    """Passage numbers seen while writing, by citation key."""
    path = Path(folder) / CONSULTED
    if not path.exists():
        return {}
    seen: dict[str, list[int]] = {}
    for passage_id in json.loads(path.read_text(encoding="utf-8")).get("pasajes", []):
        key, _, number = passage_id.rpartition(ID_SEPARATOR)
        if key and number.isdigit():
            seen.setdefault(key, []).append(int(number))
    return seen


def _escape(text: str) -> str:
    """Zotero text for a BibTeX field, with its HTML markup as LaTeX commands."""
    text = html.unescape(_SMALL_CAPS.sub(r"<scp>\1</scp>", text))
    for char in "&%$#_":
        text = text.replace(char, "\\" + char)
    for tag, command in _MARKUP.items():
        text = re.sub(f"<{tag}>(.*?)</{tag}>", rf"\\{command}{{\1}}", text, flags=re.S)
    return text


def bibtex(work: Work, key: str) -> str:
    """BibTeX entry of a Zotero work under our citation key."""
    venue_field = {"article": "journal", "inproceedings": "booktitle", "incollection": "booktitle"}
    kind = _ENTRY_TYPES.get(work.kind, "misc")
    fields = {
        "title": f"{{{_escape(work.title)}}}",
        "author": _escape(" and ".join(work.authors)),
        "year": str(work.year) if work.year else None,
        venue_field.get(kind, "howpublished"): _escape(work.venue) if work.venue else None,
        "volume": work.volume,
        "number": work.issue,
        "pages": work.pages,
        "doi": work.doi,
        "url": None if work.doi else work.url,
    }
    lines = [f"  {name} = {{{value}}}" for name, value in fields.items() if value]
    return f"@{kind}{{{key},\n" + ",\n".join(lines) + "\n}"


def reference(index: PassageIndex, key: str, allowed: set[str] | None) -> dict | None:
    """Full data of a citable work, or ``None`` if the key is unknown."""
    work = index.work_of(key)
    if work is None:
        return None
    return {
        "clave": key,
        "cita": f"[@{key}]",
        "titulo": work.title,
        "autores": list(work.authors),
        "año": work.year,
        "revista": work.venue,
        "doi": work.doi,
        "url": work.url,
        "bibtex": bibtex(work, key),
        "tiene_pdf": bool(work.pdfs),
        "pasajes": len(index.passages_of(key)),
        "en_el_documento": allowed is None or work.item_key in allowed,
    }


def write_bibliography(folder: Path, index: PassageIndex, keys: list[str]) -> Path:
    """Write ``borrador/referencias.bib`` with the entries of ``keys`` that exist."""
    entries = [bibtex(index.work_of(key), key) for key in sorted(set(keys)) if index.work_of(key)]
    path = Path(folder) / BIBLIOGRAPHY
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n\n".join(entries) + ("\n" if entries else ""), encoding="utf-8")
    return path


def live_citations_draft(folder: Path, index: PassageIndex) -> dict:
    """Write a copy of the draft with the citation keys Zotero has (Better BibTeX keeps its own
    there) instead of ours, for Pandoc's ``zotero.lua``. The draft itself does not change."""
    draft = Path(folder) / DRAFT
    if not draft.exists():
        raise LibraryError(f"Todavía no hay borrador en {DRAFT}.")
    text = draft.read_text(encoding="utf-8")
    renamed, missing = {}, []
    for key in dict.fromkeys(find_citations(text)[0]):
        work = index.work_of(key)
        if work and work.zotero_cite_key:
            renamed[key] = work.zotero_cite_key
        else:
            missing.append(key)
    path = Path(folder) / LIVE_DRAFT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(replace_keys(text, renamed), encoding="utf-8")
    changed = {ours: theirs for ours, theirs in renamed.items() if ours != theirs}
    return {"fichero": LIVE_DRAFT, "cambiadas": changed, "sin_clave_en_zotero": missing}
