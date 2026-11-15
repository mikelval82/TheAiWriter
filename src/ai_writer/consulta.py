"""A document's view of Zotero: the works it may cite, what it has consulted, its bibliography."""

import json
from pathlib import Path

from ai_writer.library import Project
from ai_writer.passages import ID_SEPARATOR, PassageIndex
from ai_writer.zotero import DATABASE, Work, Zotero

CONSULTED = "revision/consultas.json"
BIBLIOGRAPHY = "borrador/referencias.bib"
_ENTRY_TYPES = {
    "journalArticle": "article",
    "conferencePaper": "inproceedings",
    "book": "book",
    "bookSection": "incollection",
    "thesis": "phdthesis",
}

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
    for char in "&%$#_":
        text = text.replace(char, "\\" + char)
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
