"""Cited sentences and paragraphs of a Markdown draft, without any model."""

import re

from ai_writer.citations import find_citations

_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")
_FINDING_MARKER = re.compile(r"<!--\s*hallazgo\s*:\s*\d+\s*-->", re.IGNORECASE)
_CITE_MARKUP = re.compile(r"\[[^\[\]]*@[^\[\]]*\]|\[\[PENDIENTE[^\]]*\]\]")
_ABBREVIATION = re.compile(r"\b(?:e\.g|i\.e|et al|cf|vs|pp?|fig|figs|no|dr|dra|sr|sra)\.", re.I)
_GENUS = re.compile(r"\b[A-Z]\.(?=\*?\s+\*?[a-z])")  # *E. coli*, S. aureus
_DECIMAL = re.compile(r"(?<=\d)\.(?=\d)")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_DOT = "\x01"
_OTHERS_WORK = re.compile(  # a sentence that tells what somebody else's work says
    r"\bet al\b|\by colaboradores\b|\band colleagues\b"
    r"|\b(?:los|las|estos|estas|esos|esas|dichos|sus)\s+autor[ae]s\b|\b(?:the|these|those)\s+authors\b"
    r"|\b(?:trabajos?|estudios?|artículos?)\s+(?:original(?:es)?|previos?|anterior(?:es)?)\b"
    r"|\b(?:ese|esos|aquel|aquellos|dicho|dichos|otro|otros)\s+(?:trabajos?|estudios?|artículos?)\b"
    r"|\b(?:original|previous|prior|earlier|other|that)\s+(?:stud(?:y|ies)|works?|papers?)\b"
    r"|\b(?:the|el)\s+tutorial\b|\bse ha (?:demostrado|descrito|observado|propuesto|mostrado)\b"
    r"|\b(?:has|have) been (?:shown|reported|described|proposed)\b",
    re.I,
)
MIN_SURNAME = 4  # shorter ones (Her, Li) are too easily ordinary words


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


def _blocks(text: str) -> list[tuple[str, str]]:
    """Paragraphs as ``(section, text)``; headings only set the section."""
    blocks: list[tuple[str, str]] = []
    section, lines = "", []

    def flush() -> None:
        if lines:
            blocks.append((section, " ".join(lines)))
            lines.clear()

    for line in text.splitlines():
        line = _FINDING_MARKER.sub("", line)
        heading = _HEADING.match(line)
        if heading:
            flush()
            section = heading.group(1)
        elif not line.strip():
            flush()
        else:
            lines.append(line.strip())
    flush()
    return blocks


def cited_paragraphs(text: str) -> list[dict]:
    """Paragraphs with cited sentences: ``{"seccion", "texto", "frases": [(sentence, [keys])],
    "previas": [preceding sentence]}``, ``previas`` in step with ``frases``."""
    paragraphs = []
    for section, block in _blocks(text):
        cited, previous = [], []
        before = ""
        for sentence in split_sentences(block):
            keys = list(dict.fromkeys(find_citations(sentence)[0]))
            if keys:
                cited.append((sentence, keys))
                previous.append(before)
            before = sentence
        if cited:
            paragraphs.append(
                {"seccion": section, "texto": block, "frases": cited, "previas": previous}
            )
    return paragraphs


def uncited_attributions(text: str, surnames: set[str]) -> list[dict]:
    """Sentences without citation that seem to tell what a work says: they name its authors
    (``surnames``, lowercase) or speak of other people's work. Nothing checks them."""
    entries = []
    for section, block in _blocks(text):
        if block.startswith(("|", "```", "!", "#")):
            continue
        for sentence in split_sentences(block):
            if "[@" in sentence:
                continue
            names = {w.lower() for w in re.findall(r"\b[A-ZÁÉÍÓÚÑ][\wáéíóúüñ]+", sentence)}
            named = {n for n in names & surnames if len(n) >= MIN_SURNAME}
            if named or _OTHERS_WORK.search(sentence):
                entries.append({"seccion": section, "frase": sentence})
    return entries


def sentence_query(sentence: str) -> str:
    """Remove citation and pending markers for passage retrieval."""
    return " ".join(_CITE_MARKUP.sub("", sentence).split()) or sentence
