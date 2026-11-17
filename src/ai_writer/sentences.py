"""Cited sentences and paragraphs of a Markdown draft, without any model."""

import re

from ai_writer.citations import find_citations

_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")
_CITE_MARKUP = re.compile(r"\[[^\[\]]*@[^\[\]]*\]|\[\[PENDIENTE[^\]]*\]\]")
_ABBREVIATION = re.compile(r"\b(?:e\.g|i\.e|et al|cf|vs|pp?|fig|figs|no|dr|dra|sr|sra)\.", re.I)
_GENUS = re.compile(r"\b[A-Z]\.(?=\*?\s+\*?[a-z])")  # *E. coli*, S. aureus
_DECIMAL = re.compile(r"(?<=\d)\.(?=\d)")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_DOT = "\x01"


def split_sentences(paragraph: str) -> list[str]:
    """Sentences of a paragraph; never splits inside ``[...]`` or on common abbreviations."""
    groups: list[str] = []

    def hide(match: re.Match) -> str:
        groups.append(match.group(0))
        return f"\x00{len(groups) - 1}\x00"

    masked = re.sub(r"\[[^\[\]]*\]", hide, " ".join(paragraph.split()))
    masked = _ABBREVIATION.sub(lambda m: m.group(0).replace(".", _DOT), masked)
    masked = _GENUS.sub(lambda m: m.group(0).replace(".", _DOT), masked)
    masked = _DECIMAL.sub(_DOT, masked)
    pieces = [p for p in _SENTENCE_END.split(masked) if p.strip()]
    merged: list[str] = []
    for piece in pieces:  # citation markup right after a full stop belongs to the previous sentence
        lead = re.match(r"((?:\x00\d+\x00[\s.,;]*)+)(.*)", piece)
        if merged and lead:
            merged[-1] += " " + lead.group(1).strip()
            piece = lead.group(2)
        if piece.strip():
            merged.append(piece)

    def restore(text: str) -> str:
        return re.sub(r"\x00(\d+)\x00", lambda m: groups[int(m.group(1))], text).replace(_DOT, ".")

    return [restore(p).strip() for p in merged]


def cited_paragraphs(text: str) -> list[dict]:
    """Paragraphs with cited sentences: ``{"seccion", "frases": [(sentence, [keys])]}``."""
    blocks: list[tuple[str, str]] = []
    section, lines = "", []

    def flush() -> None:
        if lines:
            blocks.append((section, " ".join(lines)))
            lines.clear()

    for line in text.splitlines():
        heading = _HEADING.match(line)
        if heading:
            flush()
            section = heading.group(1)
        elif not line.strip():
            flush()
        else:
            lines.append(line.strip())
    flush()

    paragraphs = []
    for section, block in blocks:
        cited = []
        for sentence in split_sentences(block):
            keys = list(dict.fromkeys(find_citations(sentence)[0]))
            if keys:
                cited.append((sentence, keys))
        if cited:
            paragraphs.append({"seccion": section, "frases": cited})
    return paragraphs


def sentence_query(sentence: str) -> str:
    """Remove citation and pending markers for passage retrieval."""
    return " ".join(_CITE_MARKUP.sub("", sentence).split()) or sentence
