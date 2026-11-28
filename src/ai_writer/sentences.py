"""Cited sentences and paragraphs of a Markdown draft, without any model."""

import re
import unicodedata

from ai_writer.citations import find_citations

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
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
_LITERATURE_SECTION = re.compile(
    r"^(?:\d+(?:\.\d+)*[.)]?\s+)?(?:introduccion|introduction|discussion|discusion|background)\b"
)
_EMPIRICAL = re.compile(
    r"\b(?:ensayos|estudios|metaanalisis|revisiones|evidencia|literatura|trials|studies|"
    r"meta[- ]?analyses|reviews|evidence|literature)\b[^.!?]{0,100}\b"
    r"(?:demuestran?|muestran?|indican?|sugier(?:e|en)|senalan?|mostr(?:o|aron)|observaron|"
r"reportan?|documentan?|encontr(?:o|aron)|"
    r"show(?:s|ed)?|demonstrat(?:e|es|ed)|suggest(?:s|ed)?|indicat(?:e|es|ed)|report(?:s|ed)?|found)\b"
)
_OWN = re.compile(
    r"\b(?:nuestr[oa]s? (?:estudio|analisis|datos|resultados|hipotesis|muestra)|"
    r"en (?:este|el presente) (?:estudio|analisis)|observamos|encontramos|proponemos|"
    r"interpretamos|consideramos|planteamos|our (?:study|analysis|data|results|findings|"
    r"sample|hypothesis)|in this study|we (?:observed|found|hypothesize|interpret|propose))\b"
)
_PERCENT = re.compile(r"\d\s*%|\d\s+(?:por ciento|per cent|percent)\b")

MIN_SURNAME = 4  # shorter ones (Her, Li) are too easily ordinary words


def fold_text(text: str) -> str:
    """Compare section names and search words without case or accents."""
    return "".join(char for char in unicodedata.normalize("NFD", text.casefold())
                   if not unicodedata.combining(char))


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


def _blocks(text: str, *, literature_only: bool = False) -> list[tuple[str, str]]:
    """Paragraphs with their nearest heading and optional introduction/discussion scope."""
    blocks: list[tuple[str, str]] = []
    section, lines = "", []
    literature_level = None

    def flush() -> None:
        if lines and (not literature_only or literature_level is not None):
            blocks.append((section, " ".join(lines)))
        lines.clear()

    for line in text.splitlines():
        line = _FINDING_MARKER.sub("", line)
        heading = _HEADING.match(line)
        if heading:
            flush()
            section = heading[2]
            level = len(heading[1])
            if _LITERATURE_SECTION.match(fold_text(section).lstrip("*_")):
                literature_level = level
            elif literature_level is not None and level <= literature_level:
                literature_level = None
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


def literature_gaps(text: str, known: list[dict]) -> list[dict]:
    """Locate explicit placeholders and likely missing sources in introduction/discussion."""
    gaps = {
        (section, sentence): "fuente_pendiente"
        for section, paragraph in _blocks(text)
        for sentence in split_sentences(paragraph)
        if find_citations(sentence)[2]
    }
    already_reported = {(entry["seccion"], entry["frase"]) for entry in known}
    without_findings = "\n".join("" if _FINDING_MARKER.search(line) else line
                               for line in text.splitlines())
    for section, paragraph in _blocks(without_findings, literature_only=True):
        if paragraph.startswith(("|", "!", "#", "<!--")):
            continue
        for sentence in split_sentences(paragraph):
            position = section, sentence
            folded = fold_text(sentence)
            if position in gaps or position in already_reported or "[@" in sentence:
                continue
            if _EMPIRICAL.search(folded):
                gaps[position] = "afirmacion_empirica"
            elif _PERCENT.search(folded) and not _OWN.search(folded):
                gaps[position] = "porcentaje"
    return [{"seccion": section, "frase": sentence, "motivo": reason}
            for (section, sentence), reason in gaps.items()]


def sentence_query(sentence: str) -> str:
    """Remove citation and pending markers for passage retrieval."""
    return " ".join(_CITE_MARKUP.sub("", sentence).split()) or sentence
