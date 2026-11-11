"""Tests for the configurable embedder and the indices built on it.

Run from the repository root with ``python -m pytest`` so that ``config`` is importable.
No embedding model is loaded: indices get a fake embedder.
"""

import json

import numpy as np
import pytest
from typer.testing import CliRunner

from ai_writer.embeddings.embedder import (
    LEGACY_EMBEDDING_MODEL,
    LocalEmbedder,
    build_embedder,
    set_embedder,
)
from ai_writer.embeddings.embedding_index import EmbeddingIndex, EmbeddingModelMismatch
from ai_writer.main import app
from tests.conftest import EMBEDDING_DIMS, FakeEmbedder

runner = CliRunner()


def _ideas_index(workspace, embedder) -> EmbeddingIndex:
    return EmbeddingIndex(
        name="ideas",
        cache_dir=workspace.embeddings_dir,
        text_field="idea",
        embedder=embedder,
    )


def _build(workspace, embedder) -> EmbeddingIndex:
    index = _ideas_index(workspace, embedder)
    index.build_from_jsonl(workspace.indices_dir / "all_ideas.jsonl")
    return index


def test_index_records_the_embedding_model(workspace):
    _build(workspace, FakeEmbedder("model-a"))

    with open(workspace.embeddings_dir / "ideas_metadata.json", encoding="utf-8") as f:
        assert json.load(f)["embedding_model"] == "model-a"


def test_index_reloads_cache_built_with_the_same_model(workspace):
    built = _build(workspace, FakeEmbedder("model-a"))

    reloaded = _build(workspace, FakeEmbedder("model-a"))

    assert len(reloaded) == len(built)


def test_index_refuses_cache_built_with_another_model(workspace):
    _build(workspace, FakeEmbedder("model-a"))

    with pytest.raises(EmbeddingModelMismatch, match="ai-writer reindex"):
        _build(workspace, FakeEmbedder("model-b"))


def test_cache_without_model_name_counts_as_the_legacy_model(workspace):
    _build(workspace, FakeEmbedder(LEGACY_EMBEDDING_MODEL))
    metadata_path = workspace.embeddings_dir / "ideas_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    del metadata["embedding_model"]
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    assert len(_build(workspace, FakeEmbedder(LEGACY_EMBEDDING_MODEL))) > 0
    with pytest.raises(EmbeddingModelMismatch):
        _build(workspace, FakeEmbedder("model-b"))


def test_search_embeds_the_query_as_a_query(workspace):
    kinds = []

    class RecordingEmbedder(FakeEmbedder):
        def embed(self, texts, kind="passage"):
            kinds.append(kind)
            return super().embed(texts, kind)

    index = _build(workspace, RecordingEmbedder())
    results = index.search("robot emotion", top_k=3)

    assert kinds == ["passage", "query"]
    assert len(results) == 3
    assert "emotion" in results[0][0]["idea"]


def test_reindex_rebuilds_and_keeps_previous_vectors(workspace):
    _build(workspace, FakeEmbedder("model-a"))
    old_vectors = np.load(workspace.embeddings_dir / "ideas_index.npz")["embeddings"]
    set_embedder(FakeEmbedder("model-b"))
    try:
        result = runner.invoke(app, ["reindex"])
    finally:
        set_embedder(None)

    assert result.exit_code == 0, result.output
    backup = workspace.embeddings_dir / "previous_model-a"
    assert np.array_equal(np.load(backup / "ideas_index.npz")["embeddings"], old_vectors)
    for name in ("ideas", "claims", "references"):
        metadata = json.loads(
            (workspace.embeddings_dir / f"{name}_metadata.json").read_text(encoding="utf-8")
        )
        assert metadata["embedding_model"] == "model-b"
    assert np.load(workspace.embeddings_dir / "ideas_index.npz")["embeddings"].shape[1] == EMBEDDING_DIMS


def test_e5_models_get_query_and_passage_prefixes():
    assert LocalEmbedder("intfloat/multilingual-e5-small")._prefix("query") == "query: "
    assert LocalEmbedder("intfloat/multilingual-e5-small")._prefix("passage") == "passage: "
    assert LocalEmbedder("BAAI/bge-m3")._prefix("query") == ""


def test_unknown_embedding_backend_is_rejected():
    with pytest.raises(ValueError, match="EMBEDDING_BACKEND"):
        build_embedder("cohere")
