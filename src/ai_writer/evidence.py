"""Evidence from a library for a document: search, topics and the citable works behind them.

Every result carries the stable citation key of its paper, so whatever is written
from it can be checked against the library afterwards.
"""

import math
from collections import Counter
from dataclasses import dataclass

import numpy as np

from ai_writer.citations import CitationIndex
from ai_writer.embeddings.embedding_index import EmbeddingIndex
from ai_writer.library import Library

# Same text fields the indices were built with (see RAGSystem)
_IDEA_FIELDS = ["context", "keywords", "section", "paper_title"]
_CLAIM_FIELDS = ["evidence", "section", "paper_title"]


@dataclass
class Topic:
    """A group of related ideas in the document's papers."""

    id: int
    ideas: int
    papers: int
    keywords: list[str]
    examples: list[dict]


class EvidenceEngine:
    """Searches the ideas and claims of the papers a document may cite."""

    def __init__(self, library: Library, paper_ids: set[str] | None = None) -> None:
        self.library = library
        self.citations = CitationIndex.load(library)
        self.paper_ids = paper_ids
        self.ideas = self._load("ideas", "idea", _IDEA_FIELDS, "all_ideas.jsonl")
        self.claims = self._load("claims", "claim", _CLAIM_FIELDS, "all_claims.jsonl")
        self._topics: list[Topic] | None = None
        self._centroids: np.ndarray | None = None
        self._labels: dict[str, np.ndarray] = {}
        self._members: dict[int, list[int]] = {}

    def _load(self, name, text_field, fields, jsonl) -> EmbeddingIndex:
        index = EmbeddingIndex(
            name=name, cache_dir=self.library.embeddings_dir, text_field=text_field,
            context_fields=fields,
        )
        index.build_from_jsonl(self.library.indices_dir / jsonl)
        index.restrict_to_papers(self.paper_ids)
        return index

    def allowed_keys(self) -> set[str]:
        if self.paper_ids is None:
            return set(self.citations.citables())
        return self.citations.keys_for_papers(self.paper_ids)

    # Search

    def search(
        self,
        query: str,
        n: int = 8,
        kind: str = "todo",
        topic: int | None = None,
        exclude_keys: set[str] | None = None,
        max_per_paper: int = 2,
    ) -> list[dict]:
        """The ``n`` most relevant ideas and claims, at most ``max_per_paper`` per work.

        Args:
            kind: "ideas", "claims" or "todo".
            topic: Only items of this topic (see ``topics``).
            exclude_keys: Works not to return, for example those already cited.
        """
        embedding = self.ideas.get_embedding(query)
        pool = []
        if kind in ("ideas", "todo"):
            pool += [(item, s, "idea") for item, s in self._candidates(self.ideas, embedding, n, topic)]
        if kind in ("claims", "todo"):
            pool += [(item, s, "claim") for item, s in self._candidates(self.claims, embedding, n, topic)]
        pool.sort(key=lambda entry: entry[1], reverse=True)

        results, per_key, seen_texts = [], Counter(), set()
        for item, score, item_type in pool:
            key = self.citations.key_for(item.get("paper_id", ""))
            text = item.get(item_type, "")
            if not key or (exclude_keys and key in exclude_keys):
                continue
            if per_key[key] >= max_per_paper or text in seen_texts:
                continue
            per_key[key] += 1
            seen_texts.add(text)
            results.append(self._result(item, score, item_type, key))
            if len(results) >= n:
                break
        return results

    def _candidates(self, index: EmbeddingIndex, embedding, n, topic):
        if topic is None:
            return index.search_by_embedding(embedding, top_k=n * 8)
        self.topics()
        scores = index._cosine_similarity(embedding, index._embeddings_matrix)
        scores = np.where(self._topic_labels(index) == topic, scores, -np.inf)
        return index._top(scores, n * 8, min_score=-1.0)

    def _topic_labels(self, index: EmbeddingIndex) -> np.ndarray:
        """Nearest topic of every row of an index; claims get the topic of their nearest centroid."""
        cached = self._labels.get(index.name)
        if cached is None:
            matrix = index._embeddings_matrix
            distances = ((matrix[:, None, :] - self._centroids[None, :, :]) ** 2).sum(axis=2)
            cached = self._labels[index.name] = distances.argmin(axis=1)
        return cached

    def _result(self, item: dict, score: float, item_type: str, key: str) -> dict:
        citable = self.citations.citables()[key]
        result = {
            "clave": key,
            "cita": f"[@{key}]",
            "tipo": item_type,
            "texto": item.get(item_type, ""),
            "paper": citable.title,
            "año": citable.year,
            "seccion": item.get("section"),
            "relevancia": round(score, 3),
        }
        if item_type == "idea":
            result["contexto"] = item.get("context")
        else:
            result["evidencia"] = item.get("evidence")
            result["confianza"] = item.get("confidence")
        return result

    # Topics

    def topics(self, n_topics: int | None = None) -> list[Topic]:
        """Group the ideas of the document's papers into topics (k-means on their vectors)."""
        if self._topics is not None and n_topics is None:
            return self._topics
        from sklearn.cluster import KMeans

        rows = [i for i, item in enumerate(self.ideas.items) if self.ideas.allows(item)]
        if not rows:
            return []
        matrix = self.ideas._embeddings_matrix[rows]
        k = n_topics or max(4, min(12, round(math.sqrt(len(rows) / 2))))
        k = min(k, len(rows))
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(matrix)
        self._centroids = kmeans.cluster_centers_
        self._labels = {}
        self._members = {}

        topics = []
        for topic_id in range(k):
            members = [rows[i] for i in np.where(kmeans.labels_ == topic_id)[0]]
            items = [self.ideas.items[row] for row in members]
            keywords = Counter(
                word.lower() for item in items for word in item.get("keywords", [])
            )
            distances = np.linalg.norm(
                self.ideas._embeddings_matrix[members] - self._centroids[topic_id], axis=1
            )
            self._members[topic_id] = [int(row) for row in np.array(members)[np.argsort(distances)]]
            examples = []
            for row in self._members[topic_id]:
                item = self.ideas.items[row]
                key = self.citations.key_for(item.get("paper_id", ""))
                if key and all(example["clave"] != key for example in examples):
                    examples.append({"clave": key, "idea": item.get("idea", "")})
                if len(examples) == 3:
                    break
            topics.append(Topic(
                id=topic_id,
                ideas=len(items),
                papers=len({self.citations.key_for(item.get("paper_id", "")) for item in items}),
                keywords=[word for word, _ in keywords.most_common(6)],
                examples=examples,
            ))
        topics.sort(key=lambda topic: topic.ideas, reverse=True)
        self._topics = topics
        return topics

    def topic_ideas(self, topic_id: int, n: int, used_rows: set[int]) -> list[dict]:
        """Up to ``n`` ideas of a topic not in ``used_rows``, closest to its centre first.

        The rows taken are added to ``used_rows``, so successive calls never repeat an idea.
        """
        self.topics()
        topic = next(t for t in self._topics if t.id == topic_id)
        ideas = []
        for row in self._members.get(topic_id, []):
            if len(ideas) >= n:
                break
            if row in used_rows:
                continue
            used_rows.add(row)
            item = self.ideas.items[row]
            ideas.append({
                "idea": item.get("idea", ""),
                "cluster": ", ".join(topic.keywords[:3]),
                "clave": self.citations.key_for(item.get("paper_id", "")),
            })
        return ideas

    # Works

    def reference(self, key: str) -> dict | None:
        """Bibliographic data, BibTeX and amount of evidence of a citable work."""
        citable = self.citations.citables().get(key)
        if citable is None:
            return None
        ids = set(citable.paper_ids)
        return {
            "clave": key,
            "titulo": citable.title,
            "autores": list(citable.authors),
            "año": citable.year,
            "revista": citable.venue,
            "doi": citable.doi,
            "origen": citable.source,
            "en_colecciones_del_documento": key in self.allowed_keys(),
            "ideas": sum(1 for item in self.ideas.items if item.get("paper_id") in ids),
            "claims": sum(1 for item in self.claims.items if item.get("paper_id") in ids),
            "bibtex": self.citations.bibtex(key),
        }
