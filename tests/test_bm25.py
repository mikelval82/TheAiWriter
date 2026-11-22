"""Tests for sparse lexical retrieval and rank fusion."""

import numpy as np

from ai_writer.embeddings.bm25 import BM25, tokenize


def test_exact_term_outranks_unrelated_text() -> None:
    scores = BM25(["Empathy predicts helping", "Clouds bring rain", ""]).scores("empathy")
    assert scores.dtype == np.float32
    assert scores.shape == (3,)
    assert scores[0] > 0
    np.testing.assert_array_equal(scores[1:], [0.0, 0.0])


def test_rare_terms_weigh_more() -> None:
    index = BM25(["rare common", "common other", "common third"])
    assert index.scores("rare")[0] > index.scores("common")[0]


def test_accents_case_and_token_boundaries() -> None:
    assert tokenize("¡ÉMPATÍA! acción, A y 7 42 foo_bar") == [
        "empatia", "accion", "42", "foo", "bar"
    ]
    index = BM25(["La empatía ayuda", "LA EMPATIA AYUDA"])
    np.testing.assert_array_equal(index.scores("EMPATÍA"), index.scores("empatia"))
    assert index.scores("EMPATÍA")[0] == index.scores("EMPATÍA")[1]


def test_empty_corpus_query_and_texts() -> None:
    empty = BM25([]).scores("words")
    assert empty.shape == (0,)
    assert empty.dtype == np.float32
    np.testing.assert_array_equal(BM25(["", ""]).scores("words"), [0.0, 0.0])
    index = BM25(["some words", ""])
    for query in ("", "a !", "absent"):
        np.testing.assert_array_equal(index.scores(query), [0.0, 0.0])


def test_scores_follow_bm25_formula() -> None:
    index = BM25(["term term", "other words"])
    expected = np.log(2.0) * 2 * 2.5 / (2 + 1.5)
    np.testing.assert_allclose(index.scores("term"), [expected, 0.0])

