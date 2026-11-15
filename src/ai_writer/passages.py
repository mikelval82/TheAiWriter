"""Passages of the PDFs in Zotero, searchable by meaning and by words.

Every PDF is cut, without any LLM, into passages that stay inside one section and
carry their pages. The index lives outside Zotero::

    indice/
        claves.json            citation key of every work, by Zotero item key
        modelo.json            embedding model and cut version of the stored data
        obras/<ITEM>.json      passages of a work and the fingerprint of its PDFs
        vectores/<ITEM>.npy    one embedding row per passage

Only new or changed PDFs are read again.
"""

import json
import re
from bisect import bisect_right
from collections import Counter
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np

from ai_writer.embeddings.bm25 import BM25
from ai_writer.embeddings.embedder import Embedder, get_embedder
from ai_writer.segmentation import _find_headings, segment
from ai_writer.zotero import (  # noqa: F401
    INDEX_ENV,
    KEYS_FILE,
    Work,
    Zotero,
    assign_keys,
    default_index_dir,
)

CUT_VERSION = 1  # bump when the cutting changes, so every work is cut again
MIN_WORDS, MAX_WORDS = 150, 300  # 300 words fit the embedding model's window
MIN_PASSAGE_WORDS = 80  # shorter pieces of a section are joined to a neighbour
MIN_HEADINGS = 3  # fewer headings found in the text: that source of names is not trusted
ID_SEPARATOR = "#"
LEXICAL_WEIGHT = 0.5  # share of the word match in the blended score

_PART = re.compile(r" \(\d+/\d+\)$")
_CAPTION = re.compile(r"^(?:fig(?:ure|\.)?|table|tabla|algorithm|listing|box)\b", re.I)
_KNOWN = re.compile(
    r"^(?:(?:\d+|[IVX]+)\.?\s*)?(?:abstract|resumen|introduction|background|related works?|methods?"
    r"|methodology|materials and methods|results|findings|discussion|general discussion"
    r"|conclusions?|limitations|future work|implications|appendix(?: [a-z])?)$",
    re.I,
)
_GLUED_NUMBER = re.compile(r"^((?:\d+(?:\.\d+)*|[IVX]+)\.)(?=[^\s\d])")
_BOLD = 16  # PyMuPDF span flag


# -- cutting a PDF ----------------------------------------------------------


def _page_texts(doc) -> list[str]:
    """Text of each page, blocks separated by a blank line so paragraphs can be told apart."""
    pages = []
    for page in doc:
        blocks = [b[4].strip() for b in page.get_text("blocks") if b[6] == 0 and b[4].strip()]
        pages.append("\n\n".join(blocks))
    return pages


def _outline_names(doc) -> list[str]:
    return [title.strip() for level, title, _ in doc.get_toc() if level <= 2 and title.strip()]


def _font_names(doc) -> list[str]:
    """Lines that look like headings: larger or bolder than the body, short, not a caption."""
    lines = []  # (page, text, size, bold)
    sizes: Counter = Counter()
    for number, page in enumerate(doc):
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                text = " ".join("".join(s["text"] for s in spans).split())
                text = _GLUED_NUMBER.sub(r"\1 ", text)  # "II.RELATED WORK"
                size = round(max(s["size"] for s in spans) * 2) / 2
                bold = all(s["flags"] & _BOLD or "bold" in s["font"].lower() for s in spans)
                sizes[size] += len(text)
                lines.append((number, text, size, bold))
    if not sizes:
        return []
    body = sizes.most_common(1)[0][0]
    title_size = max((size for page, _, size, _ in lines if page == 0), default=body)
    pages_with = Counter()
    for page, text in {(page, text) for page, text, _, _ in lines}:
        pages_with[text] += 1

    # Title, authors and affiliations come before the first standard heading of page 1
    first_known = next(
        (i for i, (page, text, _, _) in enumerate(lines) if page == 0 and _KNOWN.match(text)), 0
    )
    names = []
    for page, text, size, bold in lines[first_known:]:
        words = text.split()
        if not 1 <= len(words) <= 12 or sum(c.isalpha() for c in text) < 3 or len(text) > 90:
            continue
        if _CAPTION.match(text) or pages_with[text] >= 3:  # captions and running headers
            continue
        known = bool(_KNOWN.match(text))
        if page == 0 and size == title_size and size > body and not known:  # the paper's title
            continue
        if "@" in text or text.count(",") >= 2:  # authors, affiliations, keyword lists
            continue
        if text.endswith((".", ",", ";", ":")) or not (text[0].isupper() or text[0].isdigit()):
            continue
        stands_out = size >= body + 0.8 or (bold and size >= body - 0.2)
        capitals = text.isupper() and len(words) <= 8 and size >= body
        if known or capitals or stands_out:
            names.append(text)
    return list(dict.fromkeys(names))


def section_names(doc, text: str) -> tuple[list[str], str]:
    """Section titles of a PDF and where they come from: its outline, its fonts, or nowhere."""
    for source, names in (("indice", _outline_names(doc)), ("letra", _font_names(doc))):
        if len(_find_headings(text, names)) >= MIN_HEADINGS:
            return names, source
    return [], "tamaño"


def _tidy(content: str) -> str:
    """Join the lines of each paragraph, undoing end-of-line hyphenation."""
    paragraphs = []
    for paragraph in re.split(r"\n[ \t]*\n\s*", content):
        joined = re.sub(r"(?<=[a-záéíóúñ])-\n(?=[a-záéíóúñ])", "", paragraph)
        joined = " ".join(joined.split())
        if joined:
            paragraphs.append(joined)
    return "\n\n".join(paragraphs)


def cut_pdf(path: Path) -> dict:
    """PDF pages, section source and passages with section names, pages and text."""
    with fitz.open(path) as doc:
        pages = _page_texts(doc)
        text = "\n\n".join(pages)
        names, source = section_names(doc, text) if text.strip() else ([], "tamaño")
    starts, offset = [], 0
    for page in pages:
        starts.append(offset)
        offset += len(page) + 2

    def page_of(position: int) -> int:
        return max(1, bisect_right(starts, position))

    passages = []
    for piece in segment(text, names, MIN_WORDS, MAX_WORDS):
        content = _tidy(piece.content)
        if not content:
            continue
        section = _PART.sub("", piece.name)
        pages_span = [page_of(piece.start), page_of(max(piece.start, piece.end - 1))]
        last = passages[-1] if passages else None
        # A stray short paragraph joins the passage before it rather than standing alone
        if last and last["seccion"] == section and len(content.split()) < MIN_PASSAGE_WORDS:
            last["texto"] += "\n\n" + content
            last["paginas"][1] = pages_span[1]
            continue
        passages.append({"seccion": section, "paginas": pages_span, "texto": content})
    for i, passage in enumerate(passages[:-1]):  # ... or the one after it, when it opens a section
        after = passages[i + 1]
        if (
            len(passage["texto"].split()) < MIN_PASSAGE_WORDS
            and after["seccion"] == passage["seccion"]
        ):
            after["texto"] = passage["texto"] + "\n\n" + after["texto"]
            after["paginas"][0] = passage["paginas"][0]
            passage["texto"] = ""
    passages = [p for p in passages if p["texto"]]
    return {"paginas": len(pages), "secciones_por": source, "pasajes": passages}


# -- the index -------------------------------------------------------------


def _fingerprint(work: Work) -> list:
    return [[str(p), p.stat().st_size, p.stat().st_mtime_ns] for p in work.pdfs]


class PassageIndex:
    """Passages of the works in a Zotero library, kept up to date and searchable."""

    def __init__(
        self, zotero: Zotero, root: Path | None = None, embedder: Embedder | None = None
    ) -> None:
        self.zotero = zotero
        self.root = Path(root) if root else default_index_dir()
        self.embedder = embedder or get_embedder()
        (self.root / "obras").mkdir(parents=True, exist_ok=True)
        (self.root / "vectores").mkdir(parents=True, exist_ok=True)
        self._keys_file = self.root / KEYS_FILE
        stored = (
            json.loads(self._keys_file.read_text(encoding="utf-8"))
            if self._keys_file.exists()
            else {}
        )
        self.keys = assign_keys(zotero.works(), stored)  # item key -> citation key
        if self.keys != stored:
            self._write(self._keys_file, {**stored, **self.keys})
        self._items = {cite: item for item, cite in self.keys.items()}
        self._loaded: tuple | None = None  # (rows, matrix, bm25) of everything indexed

    @staticmethod
    def _write(path: Path, data) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    def _stored(self, item_key: str) -> dict | None:
        path = self.root / "obras" / f"{item_key}.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def _same_model(self) -> bool:
        path = self.root / "modelo.json"
        if not path.exists():
            return False
        return json.loads(path.read_text(encoding="utf-8")) == self._model_tag()

    def _model_tag(self) -> dict:
        return {"modelo": self.embedder.model_name, "corte": CUT_VERSION}

    # -- building --------------------------------------------------------

    def pending(self, item_keys: set[str] | None = None) -> list[Work]:
        """Works with PDFs that are not indexed yet or whose PDFs changed."""
        fresh = self._same_model()
        out = []
        for work in self.zotero.works():
            if not work.pdfs or (item_keys is not None and work.item_key not in item_keys):
                continue
            stored = self._stored(work.item_key) if fresh else None
            if not stored or stored["huella"] != _fingerprint(work):
                out.append(work)
        return out

    def update(self, item_keys: set[str] | None = None) -> dict:
        """Index what ``pending`` lists. Returns what was done, with the PDFs that gave no text."""
        if not self._same_model():  # another model or cut: nothing stored is comparable
            for folder in ("obras", "vectores"):
                for file in (self.root / folder).iterdir():
                    file.unlink()
            self._write(self.root / "modelo.json", self._model_tag())
        done, empty, failed = [], [], []
        for work in self.pending(item_keys):
            passages, pages = [], 0
            try:
                for pdf in work.pdfs:
                    cut = cut_pdf(pdf)
                    pages += cut["paginas"]
                    for passage in cut["pasajes"]:
                        passages.append(
                            {**passage, "archivo": pdf.name, "secciones_por": cut["secciones_por"]}
                        )
            except Exception as error:  # a damaged PDF must not stop the rest
                failed.append(
                    {"clave": self.keys[work.item_key], "titulo": work.title, "error": str(error)}
                )
                continue
            for number, passage in enumerate(passages, 1):
                passage["n"] = number
            vectors = np.zeros((0, 0), dtype=np.float32)
            if passages:
                texts = [f"{work.title}. {p['seccion']}. {p['texto']}" for p in passages]
                vectors = _normalize(self.embedder.embed(texts, kind="passage"))
            np.save(self.root / "vectores" / f"{work.item_key}.npy", vectors)
            self._write(
                self.root / "obras" / f"{work.item_key}.json",
                {"huella": _fingerprint(work), "paginas": pages, "pasajes": passages},
            )
            (done if passages else empty).append(self.keys[work.item_key])
        self._loaded = None
        return {"indexadas": done, "sin_texto": empty, "fallidas": failed}

    # -- reading ---------------------------------------------------------

    def _load(self) -> tuple:
        if self._loaded is None:
            rows, blocks = [], []
            for work in self.zotero.works():
                stored = self._stored(work.item_key) if work.pdfs else None
                if not stored or not stored["pasajes"]:
                    continue
                vectors = np.load(self.root / "vectores" / f"{work.item_key}.npy")
                if len(vectors) != len(stored["pasajes"]):
                    continue
                blocks.append(vectors)
                rows.extend((work, passage) for passage in stored["pasajes"])
            matrix = np.vstack(blocks) if blocks else np.zeros((0, 1), dtype=np.float32)
            self._loaded = (rows, matrix, BM25([p["texto"] for _, p in rows]))
        return self._loaded

    def _result(self, work: Work, passage: dict, score: float | None = None) -> dict:
        first, last = passage["paginas"]
        result = {
            "id": f"{self.keys[work.item_key]}{ID_SEPARATOR}{passage['n']}",
            "clave": self.keys[work.item_key],
            "titulo": work.title,
            "año": work.year,
            "seccion": passage["seccion"],
            "paginas": str(first) if first == last else f"{first}-{last}",
            "texto": passage["texto"],
        }
        if score is not None:
            result["relevancia"] = round(float(score), 4)
        return result

    def search(
        self,
        query: str,
        n: int = 8,
        item_keys: set[str] | None = None,
        max_per_work: int = 3,
        lexical: bool = True,
    ) -> list[dict]:
        """Rank passages by meaning, blended with word matches if ``lexical``."""
        rows, matrix, bm25 = self._load()
        if not rows or not query.strip():
            return []
        vector = _normalize(self.embedder.embed([query], kind="query"))[0]
        semantic = matrix @ vector
        scores = _blend(semantic, bm25.scores(query)) if lexical else semantic
        results, per_work = [], Counter()
        for row in np.argsort(-scores):
            work, passage = rows[row]
            if item_keys is not None and work.item_key not in item_keys:
                continue
            if per_work[work.item_key] >= max_per_work:
                continue
            per_work[work.item_key] += 1
            results.append(self._result(work, passage, scores[row]))
            if len(results) >= n:
                break
        return results

    def work_of(self, cite_key: str) -> Work | None:
        item = self._items.get(cite_key)
        return self.zotero.work(item) if item else None

    def passages_of(self, cite_key: str) -> list[dict]:
        """Every passage of a work, in reading order; empty if it is not indexed."""
        work = self.work_of(cite_key)
        stored = self._stored(work.item_key) if work else None
        return [self._result(work, p) for p in stored["pasajes"]] if stored else []

    def read(self, passage_id: str, scope: str = "vecinos") -> list[dict]:
        """Around a passage: itself and its neighbours (``vecinos``) or its whole ``seccion``."""
        cite_key, _, number = passage_id.rpartition(ID_SEPARATOR)
        passages = self.passages_of(cite_key)
        if not number.isdigit() or not 1 <= int(number) <= len(passages):
            return []
        position = int(number) - 1
        if scope == "seccion":
            section = passages[position]["seccion"]
            first = last = position
            while first > 0 and passages[first - 1]["seccion"] == section:
                first -= 1
            while last + 1 < len(passages) and passages[last + 1]["seccion"] == section:
                last += 1
            return passages[first : last + 1]
        return passages[max(0, position - 1) : position + 2]

    def pages(self, cite_key: str, first: int, last: int) -> list[dict]:
        """The passages of a work that touch pages ``first``..``last``."""
        out = []
        for passage in self.passages_of(cite_key):
            a, _, b = passage["paginas"].partition("-")
            if int(a) <= last and int(b or a) >= first:
                out.append(passage)
        return out

    def status(self, item_keys: set[str] | None = None) -> dict:
        """How much of the library (or of ``item_keys``) is indexed."""
        works = [w for w in self.zotero.works() if item_keys is None or w.item_key in item_keys]
        with_pdf = [w for w in works if w.pdfs]
        pending = {w.item_key for w in self.pending(item_keys)}
        indexed = [self._stored(w.item_key) for w in with_pdf if w.item_key not in pending]
        return {
            "obras": len(works),
            "con_pdf": len(with_pdf),
            "sin_pdf": len(works) - len(with_pdf),
            "indexadas": len(indexed),
            "pendientes": len(pending),
            "pasajes": sum(len(s["pasajes"]) for s in indexed if s),
            "sin_texto": sum(1 for s in indexed if s and not s["pasajes"]),
        }


def _normalize(vectors: np.ndarray) -> np.ndarray:
    vectors = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.where(norms == 0, 1, norms)


def _blend(semantic: np.ndarray, lexical: np.ndarray) -> np.ndarray:
    """Weighted sum of both scores, each standardized; meaning alone when no word matches."""
    if not lexical.any():  # e.g. a query in Spanish over papers in English
        return semantic

    def standard(x: np.ndarray) -> np.ndarray:
        return (x - x.mean()) / (x.std() + 1e-9)

    return (1 - LEXICAL_WEIGHT) * standard(semantic) + LEXICAL_WEIGHT * standard(lexical)
