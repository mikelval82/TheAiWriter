"""Acceptance tests for proposal A: single TopicSpace (criteria A.c1-A.c5).

Run from the repository root with ``python -m pytest`` so that ``config`` is importable.
All indices are synthetic and written to ``tmp_path``: no network or API key needed.
"""

import json

import numpy as np
import pytest
import sklearn.cluster

from ai_writer.utils.cluster_analyzer import ClusterAnalyzer

# Three well-separated groups; "robot" appears in every idea of every group.
GROUP_WORDS = ["emotion", "navigation", "speech"]
IDEAS_PER_GROUP = 6
DIMS = 12


def _write_index(directory, embeddings, items, embed_type="ideas"):
    np.savez_compressed(directory / f"{embed_type}_index.npz", embeddings=embeddings)
    with open(directory / f"{embed_type}_metadata.json", "w", encoding="utf-8") as f:
        json.dump({"items": items}, f)


def _synthetic_corpus(seed=0):
    rng = np.random.default_rng(seed)
    embeddings, items = [], []
    for group, word in enumerate(GROUP_WORDS):
        base = np.zeros(DIMS, dtype=np.float32)
        base[group * 4] = 1.0
        for k in range(IDEAS_PER_GROUP):
            vec = base + rng.normal(scale=0.05, size=DIMS).astype(np.float32)
            embeddings.append(vec / np.linalg.norm(vec))
            idx = len(items)
            items.append(
                {
                    "id": idx,
                    "group": group,
                    "idea": f"robot {word} study variant{group}x{k}",
                }
            )
    return np.stack(embeddings).astype(np.float32), items


@pytest.fixture
def corpus_dir(tmp_path):
    embeddings, items = _synthetic_corpus()
    _write_index(tmp_path, embeddings, items)
    return tmp_path


def _analyzer(directory):
    return ClusterAnalyzer(embeddings_dir=directory, n_clusters=len(GROUP_WORDS))


def test_kmeans_fit_and_disk_load_once(corpus_dir, monkeypatch):
    """A.c1: phase 1 + phase 2 run KMeans.fit once and read the index once."""
    fit_calls = {"n": 0}
    load_calls = {"n": 0}

    original_kmeans = sklearn.cluster.KMeans

    class CountingKMeans(original_kmeans):
        def fit(self, X, y=None, sample_weight=None):
            fit_calls["n"] += 1
            return super().fit(X, y=y, sample_weight=sample_weight)

    original_load = np.load

    def counting_load(path, *args, **kwargs):
        if str(path).endswith("ideas_index.npz"):
            load_calls["n"] += 1
        return original_load(path, *args, **kwargs)

    monkeypatch.setattr(sklearn.cluster, "KMeans", CountingKMeans)
    monkeypatch.setattr(np, "load", counting_load)

    analyzer = _analyzer(corpus_dir)
    topics = analyzer.analyze(embed_type="ideas")
    mapping = {"Intro": [t.cluster_id for t in topics]}
    analyzer.get_ideas_for_sections(topics, mapping, ideas_per_section=4)
    analyzer.search_by_topic(topics[0].label, top_k=2)

    assert fit_calls["n"] == 1
    assert load_calls["n"] == 1


def test_length_mismatch_raises(tmp_path):
    """A.c2: inconsistent embeddings/metadata fail explicitly."""
    embeddings, items = _synthetic_corpus()
    _write_index(tmp_path, embeddings, items[:-1])

    analyzer = _analyzer(tmp_path)
    with pytest.raises(ValueError, match="inconsistent"):
        analyzer.analyze(embed_type="ideas")


def test_labels_unique_on_keyword_collision(corpus_dir, monkeypatch):
    """A.c3: labels stay unique when clusters share their top keywords."""

    def same_keywords(self, texts_by_cluster, n_keywords=5):
        return {cid: ["shared", "topic", "extra"] for cid in texts_by_cluster}

    monkeypatch.setattr(ClusterAnalyzer, "_extract_keywords", same_keywords)

    analyzer = _analyzer(corpus_dir)
    topics = analyzer.analyze(embed_type="ideas")

    labels = [t.label for t in topics]
    assert len(topics) == len(GROUP_WORDS)
    assert len(set(labels)) == len(labels)
    # Every topic is still reachable by label (none silently lost)
    assert set(analyzer.get_topic_centroids(topics)) == set(labels)


def test_ubiquitous_term_not_top_keyword(corpus_dir):
    """A.c4: a term present in every cluster is never a cluster's top keyword."""
    analyzer = _analyzer(corpus_dir)
    topics = analyzer.analyze(embed_type="ideas")

    assert len(topics) == len(GROUP_WORDS)
    for topic in topics:
        assert topic.keywords, f"cluster {topic.cluster_id} has no keywords"
        assert topic.keywords[0] != "robot"
        assert "robot" not in topic.keywords


def test_section_ideas_belong_to_cluster_and_are_exclusive(corpus_dir):
    """A.c5: returned ideas belong to their cluster_id and are not repeated."""
    analyzer = _analyzer(corpus_dir)
    topics = analyzer.analyze(embed_type="ideas")
    space = analyzer.get_topic_space("ideas")

    all_ids = [t.cluster_id for t in topics]
    mapping = {
        "Introducción": all_ids,
        "Estado del arte": all_ids,
        "Conclusiones": list(reversed(all_ids)),
    }
    section_ideas = analyzer.get_ideas_for_sections(topics, mapping, ideas_per_section=4)

    seen: list[int] = []
    for ideas in section_ideas.values():
        for item in ideas:
            idx = item["id"]
            assert int(space.assignments[idx]) == item["cluster_id"]
            assert item["cluster"] == space.topics[item["cluster_id"]].label
            seen.append(idx)

    assert seen, "no ideas were selected"
    assert len(seen) == len(set(seen))


@pytest.mark.parametrize("bad", [0, 1, -3, 2.5, True, "5"])
def test_init_rejects_invalid_n_clusters(bad, tmp_path) -> None:
    """V.c1: invalid n_clusters is rejected at construction; 2 and 25 are accepted."""
    with pytest.raises(ValueError, match="n_clusters"):
        ClusterAnalyzer(embeddings_dir=tmp_path, n_clusters=bad)

    for good in (2, 25):
        analyzer = ClusterAnalyzer(embeddings_dir=tmp_path, n_clusters=good)
        assert analyzer.n_clusters == good
