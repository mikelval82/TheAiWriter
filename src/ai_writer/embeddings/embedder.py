"""Text embedding, independent of where the vectors come from."""

from typing import Literal, Protocol

import numpy as np

from config.settings import settings

# Model that built the indices created before the model name was recorded
# (OpenAI's, no longer supported: such indices need `ai-writer reindex`).
LEGACY_EMBEDDING_MODEL = "text-embedding-3-small"

TextKind = Literal["passage", "query"]


class Embedder(Protocol):
    """Turns texts into vectors.

    ``model_name`` identifies the vector space: vectors from different models
    are not comparable, so indices record it and refuse to mix.
    """

    model_name: str

    def embed(self, texts: list[str], kind: TextKind = "passage") -> np.ndarray:
        """Return one float32 row per text."""
        ...


class LocalEmbedder:
    """Embeds on this machine with a sentence-transformers model.

    The model is downloaded on first use and loaded lazily, so importing this
    module stays cheap.
    """

    def __init__(self, model_name: str | None = None, batch_size: int = 32) -> None:
        """Initialize the embedder.

        Args:
            model_name: Hugging Face model id. Defaults to settings.
            batch_size: Texts encoded per batch.
        """
        self.model_name = model_name or settings.ai.embedding_model
        self.batch_size = batch_size
        self._model = None

    def _prefix(self, kind: TextKind) -> str:
        # E5 models are trained with these prefixes and search worse without them.
        if "e5" in self.model_name.lower():
            return f"{kind}: "
        return ""

    def embed(self, texts: list[str], kind: TextKind = "passage") -> np.ndarray:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as error:
                raise RuntimeError(
                    "EMBEDDING_BACKEND=local needs the sentence-transformers package "
                    "(pip install sentence-transformers)."
                ) from error
            self._model = SentenceTransformer(self.model_name)

        prefix = self._prefix(kind)
        vectors = self._model.encode(
            [prefix + text for text in texts],
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > self.batch_size,
        )
        return np.asarray(vectors, dtype=np.float32)


def build_embedder(backend: str | None = None) -> Embedder:
    """Create the embedder named in the settings.

    Raises:
        ValueError: If the backend name is unknown.
    """
    backend = backend or settings.ai.embedding_backend
    if backend == "local":
        return LocalEmbedder()
    raise ValueError(
        f"Unknown EMBEDDING_BACKEND {backend!r}; use 'local' (OpenAI is no longer supported)"
    )


_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    """Return the embedder shared by every index, creating it on first use."""
    global _embedder
    if _embedder is None:
        _embedder = build_embedder()
    return _embedder


def set_embedder(embedder: Embedder | None) -> None:
    """Replace the shared embedder; ``None`` makes the next call rebuild it."""
    global _embedder
    _embedder = embedder
