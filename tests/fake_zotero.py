"""Builds a minimal Zotero data folder (database and storage) for tests."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE libraries (libraryID INTEGER PRIMARY KEY, type TEXT);
CREATE TABLE itemTypes (itemTypeID INTEGER PRIMARY KEY, typeName TEXT);
CREATE TABLE items (itemID INTEGER PRIMARY KEY, itemTypeID INT, libraryID INT, key TEXT);
CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT);
CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value);
CREATE TABLE itemData (itemID INT, fieldID INT, valueID INT);
CREATE TABLE creators (creatorID INTEGER PRIMARY KEY, firstName TEXT, lastName TEXT);
CREATE TABLE creatorTypes (creatorTypeID INTEGER PRIMARY KEY, creatorType TEXT);
CREATE TABLE itemCreators (itemID INT, creatorID INT, creatorTypeID INT, orderIndex INT);
CREATE TABLE itemAttachments (itemID INTEGER PRIMARY KEY, parentItemID INT, linkMode INT,
                              contentType TEXT, path TEXT);
CREATE TABLE deletedItems (itemID INTEGER PRIMARY KEY);
CREATE TABLE collections (collectionID INTEGER PRIMARY KEY, collectionName TEXT,
                          parentCollectionID INT, libraryID INT, key TEXT);
CREATE TABLE collectionItems (collectionID INT, itemID INT, orderIndex INT);
CREATE TABLE deletedCollections (collectionID INTEGER PRIMARY KEY);
"""
TYPES = ["journalArticle", "preprint", "attachment", "note"]


class FakeZotero:
    """Adds works, PDFs and collections to a Zotero folder under ``root``."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        (self.root / "storage").mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "zotero.sqlite")
        self.db.executescript(SCHEMA)
        self.db.execute("INSERT INTO libraries VALUES (1, 'user')")
        self.db.executemany("INSERT INTO itemTypes VALUES (?, ?)", list(enumerate(TYPES, 1)))
        self.db.executemany("INSERT INTO creatorTypes VALUES (?, ?)", [(1, "author"), (2, "editor")])
        self._ids: dict[str, int] = {}
        self._collections: dict[str, int] = {}

    def _item(self, key: str, kind: str) -> int:
        cursor = self.db.execute(
            "INSERT INTO items (itemTypeID, libraryID, key) VALUES (?, 1, ?)", (TYPES.index(kind) + 1, key)
        )
        self._ids[key] = cursor.lastrowid
        return cursor.lastrowid

    def _set(self, item_id: int, name: str, value) -> None:
        self.db.execute("INSERT OR IGNORE INTO fields (fieldName) SELECT ? WHERE NOT EXISTS "
                        "(SELECT 1 FROM fields WHERE fieldName = ?)", (name, name))
        field_id = self.db.execute("SELECT fieldID FROM fields WHERE fieldName = ?", (name,)).fetchone()[0]
        value_id = self.db.execute("INSERT INTO itemDataValues (value) VALUES (?)", (value,)).lastrowid
        self.db.execute("INSERT INTO itemData VALUES (?, ?, ?)", (item_id, field_id, value_id))

    def add_work(self, key: str, title: str, authors=(), kind: str = "journalArticle", **fields) -> str:
        """``authors`` are ``(first, last)`` or ``(first, last, role)`` tuples."""
        item_id = self._item(key, kind)
        self._set(item_id, "title", title)
        for name, value in fields.items():
            self._set(item_id, name, value)
        for order, author in enumerate(authors):
            first, last, role = (*author, "author")[:3]
            creator = self.db.execute("INSERT INTO creators (firstName, lastName) VALUES (?, ?)",
                                      (first, last)).lastrowid
            self.db.execute("INSERT INTO itemCreators VALUES (?, ?, ?, ?)",
                            (item_id, creator, 1 if role == "author" else 2, order))
        self.db.commit()
        return key

    def add_pdf(self, key: str, parent: str | None, filename: str = "paper.pdf",
                content: bytes = b"%PDF-1.4\n", linked: Path | None = None, on_disk: bool = True) -> Path:
        """A stored PDF (``storage/<key>/<filename>``) or one linked at ``linked``."""
        item_id = self._item(key, "attachment")
        file = linked or self.root / "storage" / key / filename
        if on_disk:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(content)
        self.db.execute(
            "INSERT INTO itemAttachments VALUES (?, ?, ?, 'application/pdf', ?)",
            (item_id, self._ids.get(parent), 2 if linked else 1, str(linked) if linked else f"storage:{filename}"),
        )
        self.db.commit()
        return file

    def add_collection(self, key: str, name: str, items=(), parent: str | None = None) -> str:
        cursor = self.db.execute(
            "INSERT INTO collections (collectionName, parentCollectionID, libraryID, key) VALUES (?, ?, 1, ?)",
            (name, self._collections.get(parent), key),
        )
        self._collections[key] = cursor.lastrowid
        self.db.executemany("INSERT INTO collectionItems VALUES (?, ?, ?)",
                            [(cursor.lastrowid, self._ids[item], n) for n, item in enumerate(items)])
        self.db.commit()
        return key

    def delete_item(self, key: str) -> None:
        self.db.execute("INSERT INTO deletedItems VALUES (?)", (self._ids[key],))
        self.db.commit()

    def delete_collection(self, key: str) -> None:
        self.db.execute("INSERT INTO deletedCollections VALUES (?)", (self._collections[key],))
        self.db.commit()
