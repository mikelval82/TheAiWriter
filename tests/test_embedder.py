"""Tests for embedding model prefixes and backend selection."""

import pytest

from ai_writer.embeddings.embedder import LocalEmbedder, build_embedder


def test_e5_models_get_query_and_passage_prefixes():
    assert LocalEmbedder("intfloat/multilingual-e5-small")._prefix("query") == "query: "
    assert LocalEmbedder("intfloat/multilingual-e5-small")._prefix("passage") == "passage: "
    assert LocalEmbedder("BAAI/bge-m3")._prefix("query") == ""


def test_unknown_embedding_backend_is_rejected():
    with pytest.raises(ValueError, match="EMBEDDING_BACKEND"):
        build_embedder("cohere")
