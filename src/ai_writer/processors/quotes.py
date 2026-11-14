"""Checks, without any model, that a quote really appears in a paper's text.

The text comes from PyMuPDF (line breaks mid-sentence, hyphenation, ligatures, curly
quotes), so both sides are reduced to a stream of lowercase words before comparing.
"""

import re
import unicodedata
from bisect import bisect_left
from collections import defaultdict
from difflib import SequenceMatcher

MIN_FRAGMENT_WORDS = 4
MIN_TOTAL_WORDS = 6
MIN_SIMILARITY = 0.92
_MAX_BIGRAM_HITS = 50
_MAX_CANDIDATES = 10
_MAX_SKIPPED = 8

_DASHES = dict.fromkeys(map(ord, "‐‑‒–—―−"), "-")
_SOFT_HYPHEN = "­"
_LINE_HYPHEN = re.compile(r"(\w)-[ \t]*\n\s*(\w)")
_WORD = re.compile(r"\w+")
_ELLIPSIS = re.compile(r"\[\s*(?:…|\.{2,})\s*\]|\(\s*(?:…|\.{2,})\s*\)|…|\.{3,}")
_INSERTION = re.compile(r"\[[^\]]*\]")


def normalize(text: str) -> str:
    """Lowercase words separated by single spaces; punctuation, quotes and dashes vanish."""
    text = unicodedata.normalize("NFKC", text or "").replace(_SOFT_HYPHEN, "")
    text = _LINE_HYPHEN.sub(r"\1\2", text.translate(_DASHES).lower())
    return " ".join(_WORD.findall(text))


def fragments(quote: str) -> list[str]:
    """Normalised pieces of a quote, split on ellipses and bracketed insertions."""
    pieces = []
    for part in _ELLIPSIS.split(quote or ""):
        pieces += _INSERTION.split(part)
    return [piece for piece in map(normalize, pieces) if piece]


class QuoteChecker:
    """Normalises a paper's text once and answers `has(quote)` many times."""

    def __init__(self, text: str, normalized: bool = False):
        self.text = text if normalized else normalize(text)
        self._starts: list[int] = []
        self._bigrams: dict[tuple[str, str], list[int]] | None = None
        self._words: list[str] = []

    def has(self, quote: str) -> bool:
        pieces = [p for p in fragments(quote) if p.count(" ") + 1 >= MIN_FRAGMENT_WORDS]
        if not pieces or sum(p.count(" ") + 1 for p in pieces) < MIN_TOTAL_WORDS:
            return False
        pos = 0
        for piece in pieces:
            end = self._find(piece, pos)
            if end is None:
                return False
            pos = end
        return True

    def _find(self, piece: str, pos: int) -> int | None:
        """End offset of the first match of `piece` at or after `pos`, or None."""
        found = self.text.find(piece, pos)
        if found >= 0:
            return found + len(piece)
        return self._find_fuzzy(piece, pos)

    def _index(self) -> None:
        self._words = self.text.split()
        offset = 0
        for word in self._words:
            self._starts.append(offset)
            offset += len(word) + 1
        grams = defaultdict(list)
        for i in range(len(self._words) - 1):
            grams[(self._words[i], self._words[i + 1])].append(i)
        self._bigrams = grams

    def _end_of(self, lo: int, kept_words: int) -> int:
        """Char offset after the `kept_words`-th non-numeric word counted from word `lo`."""
        seen = 0
        for idx in range(lo, len(self._words)):
            if not self._words[idx].isdigit():
                seen += 1
                if seen == kept_words:
                    return self._starts[idx] + len(self._words[idx])
        return len(self.text)

    def _find_fuzzy(self, piece: str, pos: int) -> int | None:
        if self._bigrams is None:
            self._index()
        words = piece.split()
        votes: dict[int, int] = defaultdict(int)
        for i in range(len(words) - 1):
            hits = self._bigrams.get((words[i], words[i + 1]), ())
            if len(hits) <= _MAX_BIGRAM_HITS:
                for hit in hits:
                    votes[hit - i] += 1
        first_word = bisect_left(self._starts, pos)
        # Compare without bare numbers: footnote marks and "[7, 8]" citations in the text
        # are noise, and the same goes for the quote.
        words = [w for w in words if not w.isdigit()]
        target = " ".join(words)
        matcher = SequenceMatcher(None, autojunk=False)
        matcher.set_seq2(target)
        best = sorted(votes, key=lambda start: -votes[start])[:_MAX_CANDIDATES]
        for start in sorted(best):
            for shift in (0, -1, 1):
                lo = start + shift
                if lo < first_word or lo >= len(self._words):
                    continue
                kept, end_idx = [], lo
                for idx in range(lo, min(lo + len(words) + _MAX_SKIPPED + 2, len(self._words))):
                    if not self._words[idx].isdigit():
                        kept.append(self._words[idx])
                        end_idx = idx
                    if len(kept) >= len(words) + 2:
                        break
                for size in (0, -1, 1, 2, -2):
                    n = len(words) + size
                    if n < 1 or n > len(kept):
                        continue
                    matcher.set_seq1(" ".join(kept[:n]))
                    if (matcher.real_quick_ratio() >= MIN_SIMILARITY
                            and matcher.quick_ratio() >= MIN_SIMILARITY
                            and matcher.ratio() >= MIN_SIMILARITY):
                        return self._end_of(lo, n)
        return None


def find_quote(quote: str, text: str) -> bool:
    """True when every fragment of the quote appears, in order, in the paper's text."""
    if not quote or not text:
        return False
    return QuoteChecker(text).has(quote)
