"""Text embedding, independent of where the vectors come from."""

from typing import Literal, Protocol

import numpy as np

from config.settings import settings

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


# Models fastembed does not ship but can load from their official ONNX export:
# (pooling, dimensions). Their vectors match sentence-transformers' (cosine 1.000).
_CUSTOM_ONNX_MODELS = {
    "intfloat/multilingual-e5-small": ("MEAN", 384),
}


class LocalEmbedder:
    """Embeds on this machine with fastembed (ONNX, no PyTorch).

    The model is downloaded on first use into ``settings.ai.embedding_cache_dir``
    and loaded lazily, so importing this module stays cheap.
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

    def _load(self):
        from fastembed import TextEmbedding

        supported = {m["model"] for m in TextEmbedding.list_supported_models()}
        if self.model_name not in supported:
            if self.model_name not in _CUSTOM_ONNX_MODELS:
                raise RuntimeError(
                    f"EMBEDDING_MODEL {self.model_name!r} is not available in fastembed."
                )
            from fastembed.common.model_description import ModelSource, PoolingType

            pooling, dim = _CUSTOM_ONNX_MODELS[self.model_name]
            TextEmbedding.add_custom_model(
                model=self.model_name,
                pooling=PoolingType[pooling],
                normalization=True,
                sources=ModelSource(hf=self.model_name),
                dim=dim,
                model_file="onnx/model.onnx",
            )
        return TextEmbedding(self.model_name, cache_dir=str(settings.ai.embedding_cache_dir))

    def embed(self, texts: list[str], kind: TextKind = "passage") -> np.ndarray:
        if self._model is None:
            self._model = self._load()

        prefix = self._prefix(kind)
        vectors = self._model.embed([prefix + text for text in texts], batch_size=self.batch_size)
        return np.asarray(list(vectors), dtype=np.float32)


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
