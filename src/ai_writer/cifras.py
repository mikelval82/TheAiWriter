"""Check a draft's own figures against CSV and Markdown results, without any model."""

import csv
import io
import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext
from pathlib import Path

from ai_writer.sentences import split_sentences

_NUMBER = re.compile(r"(?<![\w.,])[+-]?\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?(?![\w]|[.,]\d)")
_FIGURE = re.compile(
    r"(?<![\w.,])[+-]?\d+(?:[.,]\d+)?(?:\s*%)?(?![\w]|[.,]\d)"
)
_HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)(?:\s+#+)?\s*$")
_CITATION = re.compile(r"\[@[^\]]*\]")
_TOLERANCE = Decimal("1e-9")


def _number(text: str) -> Decimal:
    return Decimal(text.strip().rstrip("%").strip().replace(",", "."))


def _sources(results_dir: Path) -> tuple[list[Decimal], list[str]]:
    values, files = [], []
    for path in sorted(results_dir.rglob("*")):
        if not path.is_file() or path.suffix not in (".csv", ".md"):
            continue
        text = path.read_text(encoding="utf-8-sig")
        files.append(path.relative_to(results_dir).as_posix())
        if path.suffix == ".md":
            values.extend(_number(m.group()) for m in _NUMBER.finditer(text))
            continue
        try:
            dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;")
        except csv.Error:
            dialect = csv.excel
        for row in csv.reader(io.StringIO(text), dialect):
            for cell in row:
                try:
                    value = _number(cell)
                except InvalidOperation:
                    continue
                if value.is_finite():
                    values.append(value)
    return values, files


def _prose(text: str) -> tuple[str, list[str]]:
    """Hide code and link destinations before sentence splitting; retain them for reports."""
    lines, fence, width = [], "", 0
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if (marker and marker[1][0] == fence and len(marker[1]) >= width
                    and not marker[2].strip()):
                fence = ""
            lines.append("")
        elif marker:
            fence, width = marker[1][0], len(marker[1])
            lines.append("")
        elif line.startswith(("    ", "\t")):
            lines.append("")
        else:
            lines.append(line)
    text = "\n".join(lines)
    hidden = []

    def hide(match: re.Match) -> str:
        hidden.append(match.group())
        return f"HIDDENFIGURETOKEN{len(hidden) - 1}END"

    text = re.sub(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)", hide, text, flags=re.S)
    # Destinations may have a title and balanced parentheses (as in Wikipedia URLs).
    text = re.sub(r"(?<=\]\()(?:[^()\n]|\([^()\n]*\))*(?=\))", hide, text)
    text = re.sub(r"(?m)^ {0,3}\[[^\]\n]+\]:[^\n]*", hide, text)
    text = re.sub(r"(?<=\])\[[^\]\n]*\]", hide, text)
    text = re.sub(r"<[^<>\s]+>|(?:https?://|www\.)[^\s<>]+", hide, text)
    return text, hidden


def _sentences(text: str):
    text, hidden = _prose(text)
    section, excluded, lines = "", False, []

    def sentences():
        if not excluded:
            for sentence in split_sentences(" ".join(lines)):
                if not _CITATION.search(sentence):
                    original = re.sub(
                        r"HIDDENFIGURETOKEN(\d+)END", lambda m: hidden[int(m[1])], sentence
                    )
                    yield section, sentence, original
        lines.clear()

    for line in text.splitlines():
        heading = _HEADING.match(line)
        if heading:
            yield from sentences()
            level, title = len(heading[1]), heading[2]
            if level <= 2:
                section = title if level == 2 else ""
                normalized = "".join(
                    c for c in unicodedata.normalize("NFD", section.lower())
                    if not unicodedata.combining(c)
                )
                excluded = normalized.startswith(("introduc", "metod", "method"))
            lines.append(title)
            yield from sentences()
        elif not line.strip():
            yield from sentences()
        else:
            lines.append(line.strip())
    yield from sentences()


def _matches(value: Decimal, target: Decimal, places: int) -> bool:
    with localcontext() as context:
        context.prec = max(28, len(value.as_tuple().digits) + abs(value.adjusted()) + places + 2)
        half_up = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
        if abs(half_up - target) <= _TOLERANCE:
            return True
        rounded = Decimal(str(round(float(value), places)))
        return rounded.is_finite() and abs(rounded - target) <= _TOLERANCE


def check_figures(text: str, results_dir: Path) -> dict:
    """Check decimals and percentages outside cited sentences, introduction and methods.

    Sources are numeric CSV cells and numbers in Markdown files, searched recursively.
    A match accepts Python rounding or decimal half-up rounding, also scaling fractions
    by 100 for percentages. It establishes presence, not the meaning of the sentence.
    """
    results_dir = Path(results_dir)
    values, files = _sources(results_dir)
    report = {"comprobadas": 0, "con_origen": 0, "sin_origen": [], "ficheros": files}
    if not values:
        report["aviso"] = "No hay tablas CSV ni resultados Markdown con cifras en resultados/."
    for section, sentence, original in _sentences(text):
        for match in _FIGURE.finditer(sentence):
            figure = match.group()
            percentage = figure.endswith("%")
            if not percentage and not any(c in figure for c in ",."):
                continue
            target = _number(figure)
            places = max(0, -target.as_tuple().exponent)
            report["comprobadas"] += 1
            if any(
                _matches(value, target, places)
                or (percentage and _matches(value * 100, target, places))
                for value in values
            ):
                report["con_origen"] += 1
            else:
                report["sin_origen"].append(
                    {"cifra": figure, "seccion": section, "frase": original}
                )
    return report
