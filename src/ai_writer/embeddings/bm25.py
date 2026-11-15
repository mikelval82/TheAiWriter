"""Sparse lexical retrieval."""

import re
import unicodedata
from array import array
from collections import Counter

import numpy as np

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Return lowercase, accent-free tokens containing at least two characters."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return [word for word in _TOKEN.findall(plain) if len(word) > 1]


class BM25:
    """Score passages with BM25 using compact, per-term posting arrays."""

    def __init__(self, texts: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        lengths = np.zeros(len(texts), dtype=np.float32)
        postings: dict[str, tuple[array, array]] = {}
        for doc_id, text in enumerate(texts):
            counts = Counter(tokenize(text))
            lengths[doc_id] = sum(counts.values())
            for term, count in counts.items():
                posting = postings.get(term)
                if posting is None:
                    posting = postings[term] = (array("I"), array("f"))
                posting[0].append(doc_id)
                posting[1].append(count)

        average = float(lengths.mean()) if len(texts) else 0.0
        self._norm = k1 * (1.0 - b + b * lengths / average) if average else lengths
        self._postings = {
            term: (np.asarray(ids), np.asarray(frequencies))
            for term, (ids, frequencies) in postings.items()
        }

    def scores(self, query: str) -> np.ndarray:
        """Return one float32 score per passage, visiting only matching postings."""
        scores = np.zeros(len(self._norm), dtype=np.float32)
        for term in dict.fromkeys(tokenize(query)):
            posting = self._postings.get(term)
            if posting is None:
                continue
            ids, frequencies = posting
            idf = np.log1p((len(scores) - len(ids) + 0.5) / (len(ids) + 0.5))
            scores[ids] += idf * frequencies * (self.k1 + 1.0) / (frequencies + self._norm[ids])
        return scores
