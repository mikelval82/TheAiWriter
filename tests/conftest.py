"""Deterministic embeddings for tests; no network or model downloads."""

import zlib

import numpy as np

EMBEDDING_DIMS = 64


def fake_embedding(text: str) -> list[float]:
    """Deterministic bag-of-words embedding: shared words give close vectors."""
    vec = np.zeros(EMBEDDING_DIMS, dtype=np.float32)
    for word in text.lower().split():
        vec[zlib.crc32(word.encode("utf-8")) % EMBEDDING_DIMS] += 1.0
    norm = np.linalg.norm(vec)
    return (vec / norm if norm else vec).tolist()


class FakeEmbedder:
    """Embedder backed by ``fake_embedding``."""

    def __init__(self, model_name: str = "fake-embedder") -> None:
        self.model_name = model_name

    def embed(self, texts, kind="passage"):
        return np.array([fake_embedding(t) for t in texts], dtype=np.float32)
