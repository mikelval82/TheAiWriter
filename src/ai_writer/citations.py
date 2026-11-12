"""Stable citation keys for the papers of a library, and checks of the citations in a text.

Every paper gets a BibTeX key (``sumers2024cognitive``) that never changes once
assigned. Keys live in ``claves.json`` in the library and the bibliography in
``referencias.bib``. A Zotero export, when imported, replaces the key and the
bibliographic data of the papers it matches.

Texts cite with Pandoc syntax: ``[@key]``, ``[@key1; @key2]`` or ``[@key, p. 4]``.
``[@?]`` marks a citation still to be found.
"""

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from ai_writer.library import Library, PaperEntry

PENDING_MARKER = "[@?]"

_STOPWORDS = {
    "a", "an", "the", "of", "on", "in", "for", "and", "to", "with", "from", "toward",
    "towards", "using", "via", "is", "are", "can", "do", "does", "how", "what", "why",
    "el", "la", "los", "las", "de", "del", "en", "y", "un", "una", "para", "por", "con",
}
_GROUP = re.compile(r"\[([^\[\]]*@[^\[\]]*)\]")
_CITE = re.compile(r"^\s*-?@([\w:.\-]+)\s*(,[^;]*)?$")


def _ascii(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", text.lower())


def normalize_title(title: str) -> str:
    """Lowercase ASCII words, for matching the same paper across sources."""
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    return " ".join(re.findall(r"[a-z0-9]+", text))


def _last_name(author: str) -> str:
    author = author.strip()
    if "," in author:
        return author.split(",")[0]
    return author.split()[-1] if author.split() else ""


def make_key(authors: tuple[str, ...] | list[str], year, title: str, taken: set[str]) -> str:
    """``<first author's surname><year><first meaningful title word>``, unique in ``taken``."""
    surname = _ascii(_last_name(authors[0])) if authors else ""
    word = next(
        (w for w in normalize_title(title).split() if w not in _STOPWORDS and len(w) > 2), ""
    )
    base = f"{surname or 'anonimo'}{year or 'sf'}{word}"
    key, suffix = base, ord("b")
    while key in taken:
        key, suffix = f"{base}{chr(suffix)}", suffix + 1
    return key


@dataclass(frozen=True)
class Citable:
    """A citable work: one key for one paper and its duplicates in the library."""

    key: str
    paper_ids: tuple[str, ...]
    title: str
    authors: tuple[str, ...]
    year: int | None
    venue: str | None
    doi: str | None
    source: str  # "generada" or "zotero"


class CitationIndex:
    """The citation keys of a library, kept in ``claves.json`` and ``referencias.bib``."""

    def __init__(self, library: Library) -> None:
        self.library = library
        self.keys_file = library.root / "claves.json"
        data = {}
        if self.keys_file.exists():
            data = json.loads(self.keys_file.read_text(encoding="utf-8"))
        self._keys: dict[str, str] = data.get("claves", {})
        self._zotero: dict[str, dict] = data.get("zotero", {})
        self._duplicates: dict[str, str] = {}
        self._citables: dict[str, Citable] = {}

    @classmethod
    def load(cls, library: Library) -> "CitationIndex":
        """Load the keys, assign keys to new papers and rewrite the files if anything changed."""
        return cls(library).refresh()

    def refresh(self) -> "CitationIndex":
        papers = {paper.id: paper for paper in self.library.papers()}
        metadata = {pid: _metadata(self.library, pid) for pid in papers}
        self._duplicates = _find_duplicates(papers, metadata)
        before = dict(self._keys)

        # A key given to a paper later found to be a duplicate passes to its canonical paper
        for duplicate, canonical in self._duplicates.items():
            if canonical not in self._keys and duplicate in self._keys:
                self._keys[canonical] = self._keys[duplicate]
        taken = {key for pid, key in self._keys.items() if pid in papers}
        for pid in sorted(papers):
            if pid in self._duplicates or pid in self._keys:
                continue
            paper = papers[pid]
            key = make_key(paper.authors, paper.year, paper.title, taken)
            self._keys[pid] = key
            taken.add(key)

        self._citables = {}
        for pid, paper in papers.items():
            if pid in self._duplicates:
                continue
            key = self._keys[pid]
            ids = (pid, *sorted(d for d, canonical in self._duplicates.items() if canonical == pid))
            zotero = self._zotero.get(pid)
            if zotero:
                self._citables[key] = Citable(
                    key=key, paper_ids=ids, title=zotero.get("title", paper.title),
                    authors=tuple(_split_bib_authors(zotero.get("author", ""))) or paper.authors,
                    year=_int(zotero.get("year")) or paper.year,
                    venue=zotero.get("journal") or zotero.get("booktitle"),
                    doi=zotero.get("doi"), source="zotero",
                )
            else:
                self._citables[key] = Citable(
                    key=key, paper_ids=ids, title=paper.title, authors=paper.authors,
                    year=paper.year, venue=metadata[pid].get("venue"),
                    doi=metadata[pid].get("doi"), source="generada",
                )

        bibliography = self.bibtex_all()
        bib_changed = (
            not self.library.bib_file.exists()
            or self.library.bib_file.read_text(encoding="utf-8") != bibliography
        )
        if self._keys != before or not self.keys_file.exists():
            self._save()
        if bib_changed and self._citables:
            self.library.bib_file.write_text(bibliography, encoding="utf-8")
        return self

    def _save(self) -> None:
        data = {"claves": dict(sorted(self._keys.items())), "zotero": self._zotero}
        self.keys_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Lookups

    def citables(self) -> dict[str, Citable]:
        return dict(self._citables)

    def key_for(self, paper_id: str) -> str | None:
        """The key a paper is cited by; a duplicate gets its canonical paper's key."""
        return self._keys.get(self._duplicates.get(paper_id, paper_id))

    def keys_for_papers(self, paper_ids: set[str]) -> set[str]:
        return {key for pid in paper_ids if (key := self.key_for(pid))}

    def duplicates(self) -> dict[str, str]:
        """Duplicate paper id → the paper id whose key it shares."""
        return dict(self._duplicates)

    def bibtex(self, key: str) -> str:
        citable = self._citables[key]
        fields = {
            "title": citable.title,
            "author": " and ".join(citable.authors),
            "year": citable.year,
            "journal": citable.venue,
            "doi": citable.doi,
        }
        body = ",\n".join(
            f"  {name} = {{{_bib_escape(str(value))}}}" for name, value in fields.items() if value
        )
        return f"@article{{{key},\n{body}\n}}\n"

    def bibtex_all(self) -> str:
        header = "% Generado por TheAIWriter a partir de la biblioteca. No lo edites a mano.\n\n"
        return header + "\n".join(self.bibtex(key) for key in sorted(self._citables))

    # Zotero

    def import_zotero(self, bib_path: Path) -> dict:
        """Take keys and data from a Zotero (or Better BibTeX) export for the papers it matches.

        Papers are matched by DOI, then by title. Entries that match no paper are
        reported and ignored: only papers in the library can be cited.
        """
        import bibtexparser

        parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        parser.ignore_nonstandard_types = False
        with open(bib_path, encoding="utf-8") as f:
            entries = bibtexparser.load(f, parser=parser).entries

        by_doi, by_title = {}, {}
        for citable in self._citables.values():
            if citable.doi:
                by_doi[citable.doi.lower()] = citable.paper_ids[0]
            by_title[normalize_title(citable.title)] = citable.paper_ids[0]

        matched, unmatched = [], []
        other_keys = set(self._keys.values())
        for entry in entries:
            entry = {k.lower(): v for k, v in entry.items()}
            doi = (entry.get("doi") or "").lower()
            pid = by_doi.get(doi) if doi else None
            pid = pid or by_title.get(normalize_title(_strip_braces(entry.get("title", ""))))
            if pid is None:
                unmatched.append(entry.get("id", "?"))
                continue
            key = entry["id"]
            if key in other_keys and self._keys.get(pid) != key:
                unmatched.append(f"{key} (clave ya usada por otro paper)")
                continue
            other_keys.discard(self._keys.get(pid))
            self._keys[pid] = key
            other_keys.add(key)
            self._zotero[pid] = {
                name: _strip_braces(entry[name])
                for name in ("title", "author", "year", "journal", "booktitle", "doi")
                if entry.get(name)
            }
            matched.append(key)

        self._save()
        self.refresh()
        return {"emparejadas": matched, "sin_paper": unmatched}


def _metadata(library: Library, paper_id: str) -> dict:
    path = library.processed_dir / "papers" / paper_id / "metadata.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _find_duplicates(papers: dict[str, PaperEntry], metadata: dict[str, dict]) -> dict[str, str]:
    """Group papers with the same DOI or title; keep the one with a DOI, then the richest."""
    groups: dict[str, list[str]] = {}
    for pid, paper in papers.items():
        doi = (metadata[pid].get("doi") or "").lower()
        title = normalize_title(paper.title)
        group_key = next((k for k in (f"doi:{doi}", f"t:{title}") if k in groups), None)
        if group_key is None:
            group_key = f"t:{title}"
            groups[group_key] = []
            if doi:
                groups[f"doi:{doi}"] = groups[group_key]
        groups[group_key].append(pid)

    duplicates = {}
    seen = set()
    for members in groups.values():
        if id(members) in seen or len(members) < 2:
            continue
        seen.add(id(members))
        canonical = max(
            members,
            key=lambda pid: (bool(metadata[pid].get("doi")), papers[pid].ideas, pid),
        )
        duplicates.update({pid: canonical for pid in members if pid != canonical})
    return duplicates


def _split_bib_authors(authors: str) -> list[str]:
    return [a.strip() for a in authors.replace("\n", " ").split(" and ") if a.strip()]


def _strip_braces(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("{", "").replace("}", "")).strip()


def _bib_escape(text: str) -> str:
    return text.replace("&", r"\&").replace("%", r"\%")


def _int(value) -> int | None:
    try:
        return int(str(value)[:4])
    except (TypeError, ValueError):
        return None


# Checking the citations of a text


@dataclass
class CitationReport:
    """What a text cites, compared with what it may cite."""

    valid: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)  # not in the library
    outside: list[str] = field(default_factory=list)  # in the library, not in the document's collections
    not_retrieved: list[str] = field(default_factory=list)  # never returned by a search
    malformed: list[str] = field(default_factory=list)
    pending: int = 0

    @property
    def ok(self) -> bool:
        return not (self.unknown or self.outside or self.malformed)

    def summary(self) -> str:
        """A short report in Spanish, for Claude and the student."""
        lines = [
            f"{len(set(self.valid))} citas válidas ({len(self.valid)} usos), "
            f"{self.pending} pendientes {PENDING_MARKER}."
        ]
        if self.unknown:
            lines.append("No existen en la biblioteca: " + ", ".join(sorted(set(self.unknown))))
        if self.outside:
            lines.append(
                "Están en la biblioteca pero fuera de las colecciones del documento: "
                + ", ".join(sorted(set(self.outside)))
            )
        if self.malformed:
            lines.append(
                "Con formato no válido (usa [@clave] o [@clave1; @clave2]): "
                + ", ".join(self.malformed)
            )
        if self.not_retrieved:
            lines.append(
                "Aviso: citadas sin haber salido en ninguna búsqueda de evidencia: "
                + ", ".join(sorted(set(self.not_retrieved)))
            )
        return "\n".join(lines)


def find_citations(text: str) -> tuple[list[str], list[str], int]:
    """Return (keys cited, malformed citation groups, pending markers) in reading order."""
    keys, malformed, pending = [], [], 0
    for match in _GROUP.finditer(text):
        group = match.group(1)
        if group.strip() == "@?":
            pending += 1
            continue
        parts = [_CITE.match(part) for part in group.split(";")]
        if all(parts):
            keys.extend(part.group(1).rstrip(".") for part in parts)
        else:
            malformed.append(match.group(0))
    return keys, malformed, pending


def check_citations(
    text: str,
    index: CitationIndex,
    allowed_keys: set[str] | None = None,
    retrieved_keys: set[str] | None = None,
) -> CitationReport:
    """Check every citation of ``text`` against the library and the document's collections."""
    keys, malformed, pending = find_citations(text)
    library_keys = set(index.citables())
    report = CitationReport(malformed=malformed, pending=pending)
    for key in keys:
        if key not in library_keys:
            report.unknown.append(key)
        elif allowed_keys is not None and key not in allowed_keys:
            report.outside.append(key)
        else:
            report.valid.append(key)
            if retrieved_keys is not None and key not in retrieved_keys:
                report.not_retrieved.append(key)
    return report
