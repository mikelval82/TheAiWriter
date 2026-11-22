"""Citation key generation and Pandoc citation parsing."""

import re
import unicodedata

_STOPWORDS = {
    "a",
    "an",
    "the",
    "of",
    "on",
    "in",
    "for",
    "and",
    "to",
    "with",
    "from",
    "toward",
    "towards",
    "using",
    "via",
    "is",
    "are",
    "can",
    "do",
    "does",
    "how",
    "what",
    "why",
    "el",
    "la",
    "los",
    "las",
    "de",
    "del",
    "en",
    "y",
    "un",
    "una",
    "para",
    "por",
    "con",
}
_GROUP = re.compile(r"\[([^\[\]]*@[^\[\]]*)\]")
_CITE = re.compile(r"^\s*-?@([\w:.\-]+)\s*(,[^;]*)?$")
_KEY = re.compile(r"@([\w:.\-]*\w)")


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


def replace_keys(text: str, keys: dict[str, str]) -> str:
    """``text`` with the keys of its citation groups renamed; nothing else changes."""

    def rename(match: re.Match) -> str:
        return _KEY.sub(lambda m: "@" + keys.get(m.group(1), m.group(1)), match.group(0))

    return _GROUP.sub(rename, text)


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
