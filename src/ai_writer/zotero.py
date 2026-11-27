"""Read-only view of the student's local Zotero library.

Zotero keeps its data in a folder (``~/Zotero`` by default)::

    zotero.sqlite         items, collections and attachments
    zotero.sqlite-wal     recent changes not yet merged, while Zotero is open
    storage/<KEY>/        one folder per stored attachment, with the PDF inside

Nothing here writes to that folder: the database is copied to a temporary
folder and read from the copy, which also works while Zotero is open.
"""

import os
import re
import shutil
import sqlite3
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ai_writer.citations import make_key
from ai_writer.library import LibraryError, documents_dir

ZOTERO_ENV = "THEAIWRITER_ZOTERO"
INDEX_ENV = "THEAIWRITER_INDICE"
KEYS_FILE = "claves.json"
DATABASE = "zotero.sqlite"
PATH_SEPARATOR = " / "

_NOT_WORKS = ("attachment", "note", "annotation")
_FIELDS = (
    "title",
    "date",
    "DOI",
    "url",
    "publicationTitle",
    "proceedingsTitle",
    "bookTitle",
    "repository",
    "publisher",
    "volume",
    "issue",
    "pages",
    "citationKey",
    "extra",
)
_VENUE_FIELDS = ("publicationTitle", "proceedingsTitle", "bookTitle", "repository", "publisher")
_STORED, _LINKED_FILE = (0, 1), 2  # Zotero's linkMode values
_PREF = r'user_pref\("extensions\.zotero\.{name}",\s*"((?:[^"\\]|\\.)*)"\)'
_EXTRA_KEY = re.compile(r"^Citation Key:\s*(\S+)\s*$", re.M | re.I)


class ZoteroError(LibraryError):
    """Zotero's data cannot be found or read; the message is for the user."""


@dataclass(frozen=True)
class Work:
    """A citable item of the Zotero library and its PDFs on this computer."""

    item_key: str
    kind: str
    title: str
    authors: tuple[str, ...]  # "Surname, Name"
    year: int | None
    venue: str | None
    doi: str | None
    url: str | None
    volume: str | None
    issue: str | None
    pages: str | None
    zotero_cite_key: str | None  # set in Zotero or by Better BibTeX, if any
    pdfs: tuple[Path, ...]
    pdf_keys: tuple[str, ...] = ()  # attachment keys, in the same order


@dataclass(frozen=True)
class Collection:
    """A Zotero collection; ``path`` joins its ancestors' names (``Tesis / Capítulo 1``)."""

    key: str
    name: str
    path: str
    parent: str | None
    item_keys: tuple[str, ...]  # works directly in it, not in its subcollections


def _profile_dirs() -> list[Path]:
    home = Path.home()
    if sys.platform == "darwin":
        roots = [home / "Library" / "Application Support" / "Zotero" / "Profiles"]
    elif sys.platform.startswith("win"):
        roots = [
            Path(os.getenv("APPDATA", home / "AppData" / "Roaming"))
            / "Zotero"
            / "Zotero"
            / "Profiles"
        ]
    else:
        roots = [home / ".zotero" / "zotero"]
    return [p for root in roots if root.is_dir() for p in sorted(root.iterdir()) if p.is_dir()]


def _pref(name: str) -> str | None:
    """A string preference of the first Zotero profile that sets it."""
    pattern = re.compile(_PREF.format(name=re.escape(name)))
    for profile in _profile_dirs():
        prefs = profile / "prefs.js"
        if prefs.exists():
            match = pattern.search(prefs.read_text(encoding="utf-8", errors="ignore"))
            if match:
                return match.group(1).replace("\\\\", "\\")
    return None


def data_dir() -> Path:
    """Use ``THEAIWRITER_ZOTERO``, Zotero's configured folder, or ``~/Zotero``."""
    configured = os.getenv(ZOTERO_ENV) or _pref("dataDir")
    return Path(configured).expanduser() if configured else Path.home() / "Zotero"


def default_index_dir() -> Path:
    """``THEAIWRITER_INDICE`` if set, else ``<documents>/TheAIWriter/indice``."""
    configured = os.getenv(INDEX_ENV)
    return (
        Path(configured).expanduser() if configured else documents_dir() / "TheAIWriter" / "indice"
    )


class Zotero:
    """The works and collections of the user's own library, loaded once from a snapshot."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root else data_dir()
        if not (self.root / DATABASE).exists():
            raise ZoteroError(
                f"No encuentro la biblioteca de Zotero en {self.root}. "
                "Abre Zotero una vez para que "
                f"la cree o indica su carpeta en la variable {ZOTERO_ENV}."
            )
        self._works: dict[str, Work] = {}
        self._collections: dict[str, Collection] = {}
        self._load()

    # -- reading ---------------------------------------------------------

    def _load(self) -> None:
        with tempfile.TemporaryDirectory(prefix="theaiwriter-zotero-") as folder:
            copy = Path(folder) / DATABASE
            shutil.copy2(self.root / DATABASE, copy)
            wal = self.root / f"{DATABASE}-wal"
            if wal.exists() and wal.stat().st_size:
                shutil.copy2(wal, Path(folder) / wal.name)
            try:
                self._read(copy)
            except sqlite3.DatabaseError:
                # Zotero wrote while we copied: the main file alone is older but consistent
                (Path(folder) / wal.name).unlink(missing_ok=True)
                try:
                    self._read(copy)
                except sqlite3.DatabaseError as error:
                    raise ZoteroError(
                        f"No puedo leer la base de datos de Zotero ({error})."
                    ) from error

    def _read(self, path: Path) -> None:
        db = sqlite3.connect(path)
        try:
            library = db.execute("SELECT libraryID FROM libraries WHERE type = 'user'").fetchone()
            library_id = library[0] if library else 1
            tables = {
                row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            deleted = {row[0] for row in db.execute("SELECT itemID FROM deletedItems")}

            rows = db.execute(
                "SELECT i.itemID, i.key, t.typeName FROM items "
                "i JOIN itemTypes t USING (itemTypeID) "
                "WHERE i.libraryID = ?",
                (library_id,),
            ).fetchall()
            kinds = {item_id: (key, kind) for item_id, key, kind in rows if item_id not in deleted}

            fields: dict[int, dict[str, str]] = {}
            marks = ",".join("?" * len(_FIELDS))
            for item_id, name, value in db.execute(
                "SELECT d.itemID, f.fieldName, v.value FROM itemData "
                "d JOIN fields f USING (fieldID) "
                f"JOIN itemDataValues v USING (valueID) WHERE f.fieldName IN ({marks})",
                _FIELDS,
            ):
                fields.setdefault(item_id, {})[name] = str(value).strip()

            creators: dict[int, list[tuple[str, str]]] = {}
            for item_id, first, last, role in db.execute(
                "SELECT ic.itemID, c.firstName, c.lastName, ct.creatorType FROM itemCreators ic "
                "JOIN creators c USING (creatorID) JOIN creatorTypes ct USING (creatorTypeID) "
                "ORDER BY ic.itemID, ic.orderIndex"
            ):
                name = f"{last}, {first}" if first and last else (last or first or "")
                if name:
                    creators.setdefault(item_id, []).append((role, name))

            pdfs: dict[int, list[tuple[Path, str]]] = {}
            for item_id, parent_id, link_mode, stored in db.execute(
                "SELECT itemID, parentItemID, linkMode, path FROM itemAttachments "
                "WHERE contentType = 'application/pdf'"
            ):
                if item_id in deleted or item_id not in kinds:
                    continue
                file = self._attachment_file(kinds[item_id][0], link_mode, stored)
                if file and file.exists():
                    pdfs.setdefault(parent_id or item_id, []).append((file, kinds[item_id][0]))

            self._works = {}
            for item_id, (key, kind) in kinds.items():
                standalone_pdf = kind == "attachment" and item_id in pdfs
                if kind in _NOT_WORKS and not standalone_pdf:
                    continue
                self._works[key] = self._work(
                    key,
                    kind,
                    fields.get(item_id, {}),
                    creators.get(item_id, []),
                    pdfs.get(item_id, []),
                )

            gone = set()
            if "deletedCollections" in tables:
                gone = {row[0] for row in db.execute("SELECT collectionID FROM deletedCollections")}
            raw = {
                cid: (key, name, parent)
                for cid, key, name, parent in db.execute(
                    "SELECT collectionID, key, collectionName, parentCollectionID FROM collections "
                    "WHERE libraryID = ?",
                    (library_id,),
                )
                if cid not in gone
            }
            members: dict[int, list[str]] = {}
            for cid, item_id in db.execute(
                "SELECT collectionID, itemID FROM collectionItems ORDER BY collectionID, orderIndex"
            ):
                if item_id in kinds and kinds[item_id][0] in self._works:
                    members.setdefault(cid, []).append(kinds[item_id][0])

            def path_of(cid: int) -> str:
                names, seen = [], set()
                while cid in raw and cid not in seen:
                    seen.add(cid)
                    names.append(raw[cid][1])
                    cid = raw[cid][2]
                return PATH_SEPARATOR.join(reversed(names))

            self._collections = {
                key: Collection(
                    key,
                    name,
                    path_of(cid),
                    raw[parent][0] if parent in raw else None,
                    tuple(members.get(cid, [])),
                )
                for cid, (key, name, parent) in raw.items()
            }
        finally:
            db.close()

    def _attachment_file(
        self, attachment_key: str, link_mode: int, stored: str | None
    ) -> Path | None:
        if not stored:
            return None
        if link_mode in _STORED:
            return self.root / "storage" / attachment_key / stored.removeprefix("storage:")
        if link_mode == _LINKED_FILE:
            if stored.startswith("attachments:"):
                base = _pref("baseAttachmentPath")
                return Path(base) / stored.removeprefix("attachments:") if base else None
            return Path(stored)
        return None

    @staticmethod
    def _work(key: str, kind: str, fields: dict, creators: list, pdfs: list[tuple[Path, str]]) -> Work:
        authors = [name for role, name in creators if role == "author"] or [
            name for _, name in creators
        ]
        year = re.search(r"\d{4}", fields.get("date", ""))
        cite_key = fields.get("citationKey") or None
        if not cite_key:
            extra = _EXTRA_KEY.search(fields.get("extra", ""))  # where Better BibTeX pins its keys
            cite_key = extra.group(1) if extra else None
        title = fields.get("title") or (pdfs[0][0].stem if pdfs else "")
        return Work(
            item_key=key,
            kind=kind,
            title=title,
            authors=tuple(authors),
            year=int(year.group()) if year else None,
            venue=next((fields[f] for f in _VENUE_FIELDS if fields.get(f)), None),
            doi=fields.get("DOI") or None,
            url=fields.get("url") or None,
            volume=fields.get("volume") or None,
            issue=fields.get("issue") or None,
            pages=fields.get("pages") or None,
            zotero_cite_key=cite_key,
            pdfs=tuple(path for path, _ in pdfs),
            pdf_keys=tuple(key for _, key in pdfs),
        )

    # -- queries ---------------------------------------------------------

    def collections(self) -> list[Collection]:
        """Every collection, ordered by path."""
        return sorted(self._collections.values(), key=lambda c: c.path.lower())

    def collection(self, name: str) -> Collection:
        """The collection with this key, path or name (case-insensitive)."""
        if name in self._collections:
            return self._collections[name]
        wanted = name.strip().lower()
        found = [c for c in self._collections.values() if c.path.lower() == wanted]
        found = found or [c for c in self._collections.values() if c.name.lower() == wanted]
        if not found:
            raise ZoteroError(f"No hay ninguna colección de Zotero llamada «{name}».")
        if len(found) > 1:
            paths = "; ".join(sorted(c.path for c in found))
            raise ZoteroError(
                f"Hay varias colecciones llamadas «{name}»: {paths}. Indica la ruta completa."
            )
        return found[0]

    def item_keys(self, collections: list[str] | None = None) -> set[str]:
        """Works of these collections and descendants, or the whole library if none given."""
        if not collections:
            return set(self._works)
        children: dict[str, list[str]] = {}
        for c in self._collections.values():
            if c.parent:
                children.setdefault(c.parent, []).append(c.key)
        keys: set[str] = set()
        pending = [self.collection(name).key for name in collections]
        while pending:
            key = pending.pop()
            keys.update(self._collections[key].item_keys)
            pending.extend(children.get(key, []))
        return keys

    def works(self, collections: list[str] | None = None) -> list[Work]:
        """Works of these collections (see ``item_keys``), in a stable order."""
        return [self._works[key] for key in sorted(self.item_keys(collections))]

    def work(self, item_key: str) -> Work | None:
        return self._works.get(item_key)


def assign_keys(works: list[Work], stored: dict[str, str]) -> dict[str, str]:
    """Citation key of every work, by Zotero item key.

    A key never changes once assigned: ``stored`` wins, so drafts written before a
    work's data was corrected, or before Better BibTeX was installed, stay valid.
    A new work takes its Zotero citation key if it has one, else a generated one.
    """
    keys = {w.item_key: stored[w.item_key] for w in works if w.item_key in stored}
    taken = set(stored.values())
    for work in sorted(works, key=lambda w: w.item_key):
        if work.item_key in keys:
            continue
        key = work.zotero_cite_key
        if not key or key in taken:
            key = make_key(work.authors, work.year, work.title, taken)
        keys[work.item_key] = key
        taken.add(key)
    return keys


def citable_keys(
    collections: list[str], index_root: Path | None = None
) -> tuple[set[str], set[str]]:
    """(every citation key, those of ``collections``), without loading the passage index."""
    import json

    zotero = Zotero()
    stored_file = (index_root or default_index_dir()) / KEYS_FILE
    stored = json.loads(stored_file.read_text(encoding="utf-8")) if stored_file.exists() else {}
    keys = assign_keys(zotero.works(), stored)
    return set(keys.values()), {keys[item] for item in zotero.item_keys(collections)}
