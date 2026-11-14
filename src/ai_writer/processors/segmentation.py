"""Cut a paper's text into non-overlapping segments, one per LLM pass.

Pure and deterministic (no LLM): headings are located in order, administrative
sections and the bibliography are dropped (headings that follow it, such as appendices,
resume the body), small sections are merged into a neighbour and big ones are split at
paragraph boundaries.
"""

import re
from dataclasses import dataclass
from math import ceil

PREAMBLE = "Preámbulo"
FALLBACK = "Texto"

_NUM = r"(?:\d+(?:\.\d+)*\.?|[IVXLC]+\.|[A-Z]\.)"
_LEAD = rf"^[ \t]*(?:{_NUM}[ \t]*\n?[ \t]*)?"
_NUM_PREFIX = re.compile(rf"^\s*{_NUM}\s+")
_REFERENCES = re.compile(
    _LEAD + r"(?:references?|bibliography|referencias|bibliograf[ií]a|literature[ \t]+cited"
    r"|works[ \t]+cited)[ \t]*:?[ \t]*$",
    re.I | re.M,
)
_ADMIN = re.compile(
    r"acknowledg(?:e)?ments?"
    r"|funding(?: (?:sources?|information|statement|and acknowledg(?:e)?ments?))?"
    r"|(?:authors?['’]? )?contributions?(?: statement)?"
    r"|credit authorship contribution statement"
    r"|(?:declaration of )?(?:conflicts? of interests?|competing interests?|"
    r"conflicting interests?)(?: statement)?"
    r"|(?:data|code|software|materials?)(?: and (?:code|data|materials?))? availability"
    r"(?: statement)?"
    r"|availability of (?:data|code)(?: and (?:materials?|code))?"
    r"|ethics statement|ethics approval|ethical approval|statement of ethics"
    r"|ethics declarations?|ethical considerations statement"
    r"|ethics (?:and|&) consent.*"
    r"|declarations?"
    r"|supplementary (?:materials?|information|data)|supporting information"
    r"|(?:list of )?abbreviations",
    re.I,
)


# A heading line followed by a bare page number is a table-of-contents entry
_PAGE_NUMBER = re.compile(r"\s*(?:\d{1,4}|[ivxlc]{1,6})[ \t]*(?:\n|$)", re.I)


@dataclass
class Segment:
    name: str  # names of the merged sections joined with " / "
    number: int
    content: str
    start: int  # offset in the text
    end: int


@dataclass
class _Piece:
    """A segment under construction; `offset` is where `content` begins in the text."""

    name: str
    content: str
    start: int
    end: int
    offset: int


def _words(text: str) -> int:
    return len(text.split())


def _search(pattern: re.Pattern, text: str, pos: int) -> re.Match | None:
    """First match of a heading pattern from `pos` that is not a table-of-contents entry."""
    for match in pattern.finditer(text, pos):
        if not _PAGE_NUMBER.match(text, match.end()):
            return match
    return None


def _heading(name: str) -> re.Pattern | None:
    bare = _NUM_PREFIX.sub("", name).strip().rstrip(":.").strip()
    tokens = bare.split()
    if not tokens:
        return None
    body = r"[ \t]+".join(re.escape(token) for token in tokens)
    return re.compile(_LEAD + body + r"[ \t]*[:.]?[ \t]*$", re.I | re.M)


def _find_headings(text: str, names: list[str]) -> list[tuple[str, int, int]]:
    """(name, heading start, heading end) in order; names not found are dropped."""
    found: list[tuple[str, int, int]] = []
    pos = 0
    for name in names:
        pattern = _heading(name)
        match = _search(pattern, text, pos) if pattern else None
        if match:
            found.append((name.strip(), match.start(), match.end()))
            pos = match.end()
    return found


def _piece(text: str, name: str, start: int, end: int) -> _Piece:
    raw = text[start:end]
    return _Piece(name, raw.strip(), start, end, start + len(raw) - len(raw.lstrip()))


def _merge(a: _Piece, b: _Piece) -> _Piece:
    content = "\n\n".join(part for part in (a.content, b.content) if part)
    return _Piece(f"{a.name} / {b.name}", content, a.start, b.end, a.offset)


def _merge_small(pieces: list[_Piece], min_words: int) -> list[_Piece]:
    merged: list[_Piece] = []
    carry: _Piece | None = None
    for piece in pieces:
        if carry:
            piece, carry = _merge(carry, piece), None
        if _words(piece.content) < min_words:
            carry = piece
        else:
            merged.append(piece)
    if carry:
        if merged:
            merged[-1] = _merge(merged[-1], carry)
        else:
            merged.append(carry)
    return merged


def _units(content: str, max_words: int) -> list[tuple[int, int]]:
    """Offsets of paragraphs; oversized ones fall back to sentences, then to words."""
    units: list[tuple[int, int]] = []

    def spans(pattern: str, start: int, end: int) -> list[tuple[int, int]]:
        out, pos = [], start
        chunk = content[start:end]
        for sep in re.finditer(pattern, chunk):
            out.append((pos, start + sep.start()))
            pos = start + sep.end()
        out.append((pos, end))
        return [(a, b) for a, b in out if content[a:b].strip()]

    for p_start, p_end in spans(r"\n[ \t]*\n\s*", 0, len(content)):
        if _words(content[p_start:p_end]) <= max_words:
            units.append((p_start, p_end))
            continue
        for s_start, s_end in spans(r"(?<=[.!?])\s+", p_start, p_end):
            if _words(content[s_start:s_end]) <= max_words:
                units.append((s_start, s_end))
                continue
            words = list(re.finditer(r"\S+", content[s_start:s_end]))
            for i in range(0, len(words), max_words):
                chunk = words[i : i + max_words]
                units.append((s_start + chunk[0].start(), s_start + chunk[-1].end()))
    return units


def _pack(sizes: list[int], limit: int) -> list[int]:
    """Greedy grouping of consecutive units; returns the index where each part starts."""
    starts, current = [0], 0
    for i, size in enumerate(sizes):
        if current and current + size > limit:
            starts.append(i)
            current = 0
        current += size
    return starts


def _split(piece: _Piece, max_words: int) -> list[_Piece]:
    total = _words(piece.content)
    if total <= max_words:
        return [piece]
    units = _units(piece.content, max_words)
    sizes = [_words(piece.content[a:b]) for a, b in units]
    starts: list[int] = [0]
    for parts in range(ceil(total / max_words), len(units) + 1):
        limit = next(
            (lim for lim in range(ceil(total / parts), max_words + 1)
             if len(_pack(sizes, lim)) <= parts),
            None,
        )
        if limit:
            starts = _pack(sizes, limit)
            break
    else:
        starts = list(range(len(units)))
    bounds = starts + [len(units)]
    count = len(starts)
    out = []
    for i in range(count):
        first, last = units[bounds[i]], units[bounds[i + 1] - 1]
        out.append(
            _Piece(
                f"{piece.name} ({i + 1}/{count})",
                piece.content[first[0] : last[1]],
                max(piece.start, piece.offset + first[0]),
                min(piece.end, piece.offset + last[1]),
                piece.offset + first[0],
            )
        )
    return out


def segment(
    text: str, section_names: list[str], min_words: int = 150, max_words: int = 2500
) -> list[Segment]:
    """Cut `text` into ordered, non-overlapping segments of `min_words`..`max_words`."""
    if not text.strip():
        return []
    headings = _find_headings(text, section_names)
    refs = _search(_REFERENCES, text, headings[0][2] if headings else 0)
    body_end = refs.start() if refs else len(text)
    # Headings after the bibliography (appendices) resume the body; the references name
    # itself never does
    late = [h for h in headings if h[1] >= body_end and not _REFERENCES.match(text, h[1])]
    headings = [h for h in headings if h[1] < body_end]
    if len(headings) < 2:
        refs = _search(_REFERENCES, text, 0)
        body_end = refs.start() if refs else len(text)
        pieces = [_piece(text, FALLBACK, 0, body_end)]
    else:
        pieces = []
        if _words(text[: headings[0][1]]) >= min_words:
            pieces.append(_piece(text, PREAMBLE, 0, headings[0][1]))
        ends = [h[1] for h in headings[1:]] + [body_end]
        if late:
            ends += [h[1] for h in late[1:]] + [len(text)]
            headings = headings + late
        for (name, _, heading_end), end in zip(headings, ends):
            bare = _NUM_PREFIX.sub("", name).strip().rstrip(":.")
            if not _ADMIN.fullmatch(bare):
                pieces.append(_piece(text, name, heading_end, end))
        pieces = _merge_small(pieces, min_words)
    pieces = [part for piece in pieces for part in _split(piece, max_words)]
    return [
        Segment(p.name, number, p.content, p.start, p.end)
        for number, p in enumerate((p for p in pieces if p.content), start=1)
    ]
