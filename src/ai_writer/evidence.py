"""Evidence from a library for a document: search, topics and the citable works behind them.

Every result carries the stable citation key of its paper, so whatever is written
from it can be checked against the library afterwards.
"""

import math
import re
from collections import Counter
from dataclasses import dataclass

import numpy as np

from ai_writer.citations import CitationIndex
from ai_writer.embeddings.embedding_index import EmbeddingIndex
from ai_writer.library import Library

# Same text fields the indices were built with (see RAGSystem)
_IDEA_FIELDS = ["context", "keywords", "section", "paper_title"]
# Below this relevance a work is too loosely related to suggest it for a gap
GAP_RELEVANCE = 0.85
_CLAIM_FIELDS = ["evidence", "section", "paper_title"]
# MMR weight of redundancy when picking the ideas of a topic (same as ClusterAnalyzer)
TOPIC_DIVERSITY = 0.3
# A statement the paper only supports by citing another work ranks below its own findings
CITED_CLAIM_WEIGHT = 0.85
# Ideas of these kinds do not feed the document plan while the topic has others
PLAN_EXCLUDED_KINDS = {"method"}


@dataclass
class Topic:
    """A group of related ideas in the document's papers."""

    id: int
    ideas: int
    papers: int
    keywords: list[str]
    examples: list[dict]


def _origin(claim: dict) -> str:
    """"citado" if the paper supports the claim only by citing another work, else "propio"."""
    origin = claim.get("origin") or ("citado" if claim.get("evidence_type") == "citation" else "propio")
    return "citado" if origin == "citado" else "propio"


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
        keys: set[str] | None = None,
    ) -> list[dict]:
        """The ``n`` most relevant ideas and claims, at most ``max_per_paper`` per work.

        Args:
            kind: "ideas", "claims" or "todo".
            topic: Only items of this topic (see ``topics``).
            exclude_keys: Works not to return, for example those already cited.
            keys: Only these works.
        """
        embedding = self.ideas.get_embedding(query)
        pool = []
        if kind in ("ideas", "todo"):
            pool += [(item, s, "idea") for item, s in self._candidates(self.ideas, embedding, n, topic, keys)]
        if kind in ("claims", "todo"):
            pool += [
                (item, s * (CITED_CLAIM_WEIGHT if _origin(item) == "citado" else 1), "claim")
                for item, s in self._candidates(self.claims, embedding, n, topic, keys)
            ]
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

    def sources_for_gaps(self, text: str, n: int = 2, min_relevance: float = GAP_RELEVANCE) -> list[dict]:
        """For each sentence of ``text`` with a ``[@?]``, the works that could back it.

        Only suggestions: whoever writes decides whether the work really says it.
        """
        gaps = []
        for sentence in re.findall(r"[^.!?\n]*\[@\?\][^.!?\n]*[.!?]?", text):
            query = re.sub(r"\[[^\]]*@[^\]]*\]", "", sentence).strip()
            if not query:
                continue
            found = [r for r in self.search(query, n=n, max_per_paper=1) if r["relevancia"] >= min_relevance]
            if found:
                gaps.append({"frase": sentence.strip(), "fuentes": found})
        return gaps

    def _candidates(self, index: EmbeddingIndex, embedding, n, topic, keys=None):
        if topic is None and keys is None:
            return index.search_by_embedding(embedding, top_k=n * 8)
        scores = index._cosine_similarity(embedding, index._embeddings_matrix)
        if topic is not None:
            self.topics()
            scores = np.where(self._topic_labels(index) == topic, scores, -np.inf)
        if keys is not None:
            in_keys = np.array([self.citations.key_for(item.get("paper_id", "")) in keys for item in index.items])
            scores = np.where(in_keys, scores, -np.inf)
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
            "cita_literal": item.get("quote"),
            "cita_verificada": item.get("quote_verified"),
        }
        if item_type == "idea":
            result["contexto"] = item.get("context")
            result["clase"] = item.get("kind")
        else:
            result["evidencia"] = item.get("evidence")
            result["confianza"] = item.get("confidence")
            result["origen"] = _origin(item)
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
        """Up to ``n`` ideas of a topic not in ``used_rows``, central yet spread out (MMR).

        Redundancy counts the ideas of this topic already in ``used_rows``, so successive
        calls keep spreading. Ideas of ``PLAN_EXCLUDED_KINDS`` come last. Two ideas of one work are avoided within a call while another
        work remains. The rows taken are added to ``used_rows``, so no idea is ever repeated.
        """
        self.topics()
        topic = next(t for t in self._topics if t.id == topic_id)
        members = self._members.get(topic_id, [])
        matrix = self.ideas._embeddings_matrix
        norms = np.linalg.norm(matrix[members], axis=1, keepdims=True) if members else None
        unit = matrix[members] / np.where(norms == 0, 1, norms) if members else None
        centre = self._centroids[topic_id] / (np.linalg.norm(self._centroids[topic_id]) or 1)
        keys = [self.citations.key_for(self.ideas.items[row].get("paper_id", "")) for row in members]
        relevance = unit @ centre if members else None
        taken = [i for i, row in enumerate(members) if row in used_rows]
        candidates = [i for i, row in enumerate(members) if row not in used_rows]
        # Method details only fill the plan when nothing else is left in the topic
        preferred = [
            i for i in candidates
            if self.ideas.items[members[i]].get("kind") not in PLAN_EXCLUDED_KINDS
        ]
        picked_keys, ideas = set(), []
        while candidates and len(ideas) < n:
            tier = [i for i in preferred if i in candidates] or candidates
            pool = [i for i in tier if keys[i] not in picked_keys] or tier
            redundancy = (unit[pool] @ unit[taken].T).max(axis=1) if taken else np.zeros(len(pool))
            score = (1 - TOPIC_DIVERSITY) * relevance[pool] - TOPIC_DIVERSITY * redundancy
            best = pool[int(np.argmax(score))]
            candidates.remove(best)
            taken.append(best)
            picked_keys.add(keys[best])
            used_rows.add(members[best])
            ideas.append({
                "idea": self.ideas.items[members[best]].get("idea", ""),
                "cluster": ", ".join(topic.keywords[:3]),
                "clave": keys[best],
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
