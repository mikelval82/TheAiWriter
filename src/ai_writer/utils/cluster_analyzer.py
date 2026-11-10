"""Cluster analyzer for extracting topics from embedding space.

Phase 1 builds a single :class:`TopicSpace` (one load from disk, one KMeans run)
that phase 2 reuses to select ideas per section by ``cluster_id``.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table

from config.settings import settings

console = Console()

# Spanish + English stop words used for keyword extraction
STOP_WORDS = [
    "de", "la", "el", "en", "y", "a", "los", "que", "del", "las",
    "un", "por", "con", "para", "una", "su", "es", "se", "como",
    "más", "al", "lo", "le", "ya", "o", "fue", "ha", "son", "pero",
    "sus", "the", "and", "of", "to", "in", "for", "is", "on", "that",
    "with", "as", "are", "this", "be", "from", "or", "an", "by", "we",
    "can", "also", "these", "which", "our", "their", "has", "have",
]


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    """Return a row-wise L2-normalized copy of ``matrix``."""
    matrix = np.asarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=-1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def _item_text(item: dict) -> str:
    """Extract the text of an ideas/claims metadata item."""
    return item.get("idea") or item.get("statement") or item.get("text") or item.get("content", "")


@dataclass
class ClusterTopic:
    """A topic extracted from a cluster of embeddings."""

    cluster_id: int
    label: str  # Human-readable topic name (unique within a TopicSpace)
    keywords: list[str]  # Top discriminative keywords (class-based TF-IDF)
    representative_ideas: list[str]  # Central and mutually diverse ideas (MMR)
    size: int  # Number of items in cluster
    centroid: np.ndarray = field(repr=False)  # L2-normalized cluster centroid

    def to_query(self) -> str:
        """Convert topic to a search query."""
        parts = [self.label] + self.keywords[:3]
        return " ".join(parts)


@dataclass(frozen=True, eq=False)
class TopicSpace:
    """Single result of phase 1, consumed by phase 2.

    Attributes:
        embeddings: (n, d) L2-normalized embedding matrix.
        metadata: Metadata items aligned with ``embeddings`` rows.
        assignments: (n,) cluster_id of each item.
        topics: ClusterTopic per cluster_id.
    """

    embeddings: np.ndarray
    metadata: list[dict]
    assignments: np.ndarray
    topics: dict[int, ClusterTopic]

    def ideas_of(self, cluster_id: int) -> np.ndarray:
        """Return the row indices of the items assigned to ``cluster_id``."""
        return np.where(self.assignments == cluster_id)[0]

    def cluster_id_for_label(self, label: str) -> int | None:
        """Return the cluster_id of a (unique) topic label, if any."""
        for cluster_id, topic in self.topics.items():
            if topic.label == label:
                return cluster_id
        return None


class ClusterAnalyzer:
    """Analyzes embedding space to extract main topics."""

    def __init__(
        self,
        embeddings_dir: Path | None = None,
        n_clusters: int = 25,  # Increased from 10 for better exploration
        n_representatives: int = 3,
        mmr_diversity: float = 0.3,
    ) -> None:
        """Initialize the cluster analyzer.

        Args:
            embeddings_dir: Directory containing embedding files.
            n_clusters: Number of clusters to create.
            n_representatives: Representative ideas kept per topic.
            mmr_diversity: Weight of diversity (0-1) when choosing representatives.

        Raises:
            ValueError: If ``n_clusters`` is not an integer >= 2 (bools rejected).
        """
        if (
            isinstance(n_clusters, bool)
            or not isinstance(n_clusters, int)
            or n_clusters < 2
        ):
            raise ValueError(
                f"n_clusters must be an integer >= 2, got {n_clusters!r}"
            )

        self.embeddings_dir = embeddings_dir or settings.paths.embeddings_dir
        self.n_clusters = n_clusters
        self.n_representatives = n_representatives
        self.mmr_diversity = mmr_diversity

        # Loaded once per embed_type
        self._embeddings_cache: dict[str, tuple[np.ndarray, list[dict]]] = {}

        # Cluster results
        self._topic_spaces: dict[str, TopicSpace] = {}
        self._topics: list[ClusterTopic] | None = None

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_embeddings(self, embed_type: str = "ideas") -> tuple[np.ndarray, list[dict]]:
        """Load embeddings and metadata from disk (cached per embed_type).

        Args:
            embed_type: Type of embeddings ("ideas" or "claims").

        Returns:
            Tuple of (embeddings array, metadata list).

        Raises:
            FileNotFoundError: If index or metadata files are missing.
            ValueError: If metadata format is unknown or its length does not
                match the number of embeddings.
        """
        if embed_type in self._embeddings_cache:
            return self._embeddings_cache[embed_type]

        index_path = self.embeddings_dir / f"{embed_type}_index.npz"
        metadata_path = self.embeddings_dir / f"{embed_type}_metadata.json"

        if not index_path.exists():
            raise FileNotFoundError(f"Index not found: {index_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found: {metadata_path}")

        with np.load(index_path) as data:
            embeddings = np.asarray(data["embeddings"])

        with open(metadata_path, encoding="utf-8") as f:
            metadata_raw = json.load(f)

        # Handle both list and dict formats
        if isinstance(metadata_raw, dict) and "items" in metadata_raw:
            metadata = metadata_raw["items"]
        elif isinstance(metadata_raw, list):
            metadata = metadata_raw
        else:
            raise ValueError(f"Unexpected metadata format: {type(metadata_raw)}")

        if embeddings.ndim != 2:
            raise ValueError(
                f"{embed_type} embeddings must be a 2D matrix, got shape {embeddings.shape}"
            )
        if embeddings.shape[0] != len(metadata):
            raise ValueError(
                f"{embed_type} index is inconsistent: {embeddings.shape[0]} embeddings "
                f"but {len(metadata)} metadata items ({index_path.name} / "
                f"{metadata_path.name}). Rebuild the index."
            )

        self._embeddings_cache[embed_type] = (embeddings, metadata)
        return embeddings, metadata

    # ------------------------------------------------------------------
    # Clustering and labelling
    # ------------------------------------------------------------------

    def _cluster_embeddings(self, embeddings: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Perform KMeans clustering on embeddings.

        Args:
            embeddings: Embedding matrix (n_samples, n_dims).

        Returns:
            Tuple of (cluster labels, cluster centroids).
        """
        from sklearn.cluster import KMeans

        # Adjust n_clusters if we have fewer samples
        n_clusters = min(self.n_clusters, len(embeddings))

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(embeddings)

        return kmeans.labels_, kmeans.cluster_centers_

    def _extract_keywords(
        self,
        texts_by_cluster: dict[int, list[str]],
        n_keywords: int = 5,
    ) -> dict[int, list[str]]:
        """Extract discriminative keywords per cluster with class-based TF-IDF.

        A single vocabulary is fitted on the whole corpus; each cluster is treated
        as one document. Terms present in every cluster are not discriminative and
        are only used when a cluster has no other terms.

        Args:
            texts_by_cluster: Texts of each cluster, keyed by cluster_id.
            n_keywords: Number of top keywords to extract per cluster.

        Returns:
            Dict mapping cluster_id to its top keywords.
        """
        from sklearn.feature_extraction.text import CountVectorizer

        cluster_ids = sorted(texts_by_cluster)
        empty: dict[int, list[str]] = {cid: [] for cid in cluster_ids}
        if not cluster_ids:
            return empty

        class_docs = [" ".join(texts_by_cluster[cid]) for cid in cluster_ids]
        try:
            vectorizer = CountVectorizer(stop_words=STOP_WORDS, ngram_range=(1, 2))
            counts = vectorizer.fit_transform(class_docs).toarray().astype(np.float64)
        except ValueError:
            # Empty vocabulary
            return empty

        terms = vectorizer.get_feature_names_out()

        row_totals = counts.sum(axis=1, keepdims=True)
        row_totals[row_totals == 0] = 1.0
        tf = counts / row_totals

        term_totals = counts.sum(axis=0)
        avg_words_per_class = counts.sum() / len(cluster_ids)
        idf = np.log1p(avg_words_per_class / np.maximum(term_totals, 1e-12))
        scores = tf * idf

        if len(cluster_ids) > 1:
            in_every_cluster = (counts > 0).all(axis=0)
        else:
            in_every_cluster = np.zeros(len(terms), dtype=bool)

        result: dict[int, list[str]] = {}
        for row, cid in enumerate(cluster_ids):
            order = np.argsort(-scores[row], kind="stable")
            present = [j for j in order if counts[row, j] > 0]
            discriminative = [j for j in present if not in_every_cluster[j]]
            chosen = discriminative or present
            result[cid] = [str(terms[j]) for j in chosen[:n_keywords]]

        return result

    def _select_representatives(
        self,
        member_embeddings: np.ndarray,
        centroid: np.ndarray,
        k: int,
    ) -> list[int]:
        """Pick up to ``k`` central yet diverse members (Maximal Marginal Relevance).

        Args:
            member_embeddings: L2-normalized embeddings of the cluster members.
            centroid: L2-normalized cluster centroid.
            k: Number of representatives.

        Returns:
            Local indices (into ``member_embeddings``) of the representatives.
        """
        relevance = member_embeddings @ centroid
        candidates = list(range(len(relevance)))
        selected: list[int] = []
        diversity = self.mmr_diversity

        while candidates and len(selected) < k:
            if not selected:
                best = max(candidates, key=lambda i: relevance[i])
            else:
                redundancy = (
                    member_embeddings[candidates] @ member_embeddings[selected].T
                ).max(axis=1)
                mmr = (1 - diversity) * relevance[candidates] - diversity * redundancy
                best = candidates[int(np.argmax(mmr))]
            selected.append(best)
            candidates.remove(best)

        return selected

    def _generate_topic_label(
        self,
        keywords: list[str],
        representative_ideas: list[str],
        existing_labels: set[str] | None = None,
        cluster_id: int | None = None,
    ) -> str:
        """Generate a human-readable topic label, unique among ``existing_labels``.

        Args:
            keywords: Top keywords for the cluster.
            representative_ideas: Representative ideas from the cluster.
            existing_labels: Labels already in use; the result is added to it.
            cluster_id: Used to disambiguate colliding labels.

        Returns:
            Topic label string.
        """
        if keywords:
            # Use top 2 keywords as label
            label = " + ".join(keywords[:2]).title()
        elif representative_ideas:
            # Fallback: truncate first idea
            label = representative_ideas[0][:50] + "..."
        else:
            label = "Unknown Topic"

        if existing_labels is None:
            return label

        if label in existing_labels:
            suffix = f"#{cluster_id}" if cluster_id is not None else "#"
            candidate = f"{label} ({suffix})"
            counter = 2
            while candidate in existing_labels:
                candidate = f"{label} ({suffix}-{counter})"
                counter += 1
            label = candidate

        existing_labels.add(label)
        return label

    def build_topic_space(self, embed_type: str = "ideas") -> TopicSpace:
        """Build the TopicSpace: one load, one KMeans, labelled topics.

        Args:
            embed_type: Type of embeddings to analyze ("ideas" or "claims").

        Returns:
            The TopicSpace (also cached for later phases).
        """
        embeddings, metadata = self._load_embeddings(embed_type)
        normalized = _l2_normalize(embeddings)

        assignments, centroids = self._cluster_embeddings(normalized)
        assignments = np.asarray(assignments)

        members_by_cluster: dict[int, np.ndarray] = {}
        texts_by_cluster: dict[int, list[str]] = {}
        for cluster_id in range(len(centroids)):
            indices = np.where(assignments == cluster_id)[0]
            if len(indices) == 0:
                continue
            members_by_cluster[cluster_id] = indices
            texts_by_cluster[cluster_id] = [_item_text(metadata[i]) for i in indices]

        keywords_by_cluster = self._extract_keywords(texts_by_cluster)

        topics: dict[int, ClusterTopic] = {}
        used_labels: set[str] = set()
        for cluster_id, indices in members_by_cluster.items():
            texts = texts_by_cluster[cluster_id]
            centroid = _l2_normalize(centroids[cluster_id])

            local = self._select_representatives(
                normalized[indices], centroid, self.n_representatives
            )
            representative_ideas = [texts[i] for i in local]

            keywords = keywords_by_cluster.get(cluster_id, [])
            label = self._generate_topic_label(
                keywords, representative_ideas, used_labels, cluster_id
            )

            topics[cluster_id] = ClusterTopic(
                cluster_id=cluster_id,
                label=label,
                keywords=keywords,
                representative_ideas=representative_ideas,
                size=len(indices),
                centroid=centroid,
            )

        space = TopicSpace(
            embeddings=normalized,
            metadata=metadata,
            assignments=assignments,
            topics=topics,
        )
        self._topic_spaces[embed_type] = space
        return space

    def get_topic_space(self, embed_type: str = "ideas") -> TopicSpace:
        """Return the cached TopicSpace, building it on first use."""
        if embed_type not in self._topic_spaces:
            self.build_topic_space(embed_type)
        return self._topic_spaces[embed_type]

    def analyze(self, embed_type: str = "ideas") -> list[ClusterTopic]:
        """Analyze embedding space and extract topics.

        Args:
            embed_type: Type of embeddings to analyze ("ideas" or "claims").

        Returns:
            List of ClusterTopic objects sorted by size (descending).
        """
        console.print(f"[cyan]🔬 Analyzing {embed_type} embedding space...[/cyan]")

        space = self.build_topic_space(embed_type)
        console.print(f"  Loaded {len(space.metadata)} embeddings")
        console.print(f"  Created {len(space.topics)} clusters")

        topics = sorted(space.topics.values(), key=lambda t: t.size, reverse=True)

        self._topics = topics
        return topics

    # ------------------------------------------------------------------
    # Presentation
    # ------------------------------------------------------------------

    def display_topics(self, topics: list[ClusterTopic] | None = None) -> None:
        """Display topics in a rich table.

        Args:
            topics: Topics to display. Uses cached topics if None.
        """
        topics = topics or self._topics
        if not topics:
            console.print("[yellow]No topics to display. Run analyze() first.[/yellow]")
            return

        table = Table(title="📊 Extracted Topics from Embedding Space")
        table.add_column("ID", style="dim", width=4)
        table.add_column("Topic", style="cyan", width=30)
        table.add_column("Size", justify="right", width=6)
        table.add_column("Keywords", style="green", width=40)

        for topic in topics:
            table.add_row(
                str(topic.cluster_id),
                topic.label,
                str(topic.size),
                ", ".join(topic.keywords[:4]),
            )

        console.print(table)

    def get_topics_summary(self, topics: list[ClusterTopic] | None = None) -> str:
        """Get a text summary of topics for the planner agent.

        Args:
            topics: Topics to summarize. Uses cached topics if None.

        Returns:
            Markdown-formatted summary of topics.
        """
        topics = topics or self._topics
        if not topics:
            return "No topics available."

        def _clip(text: str, limit: int = 200) -> str:
            return text if len(text) <= limit else text[:limit].rstrip() + "..."

        lines = ["# Temas Principales Identificados en la Literatura\n"]

        for i, topic in enumerate(topics, 1):
            lines.append(f"## {i}. {topic.label}")
            lines.append(f"- **Palabras clave:** {', '.join(topic.keywords[:5])}")
            lines.append(f"- **Cantidad de ideas:** {topic.size}")
            for idea in topic.representative_ideas[:2]:
                lines.append(f"- **Idea representativa:** \"{_clip(idea)}\"")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_topic_centroids(self, topics: list[ClusterTopic] | None = None) -> dict[str, np.ndarray]:
        """Get centroids for each topic for targeted searches.

        Labels are unique within a TopicSpace, so no topic is lost.

        Args:
            topics: Topics to get centroids from. Uses cached topics if None.

        Returns:
            Dictionary mapping topic labels to their centroids.
        """
        topics = topics or self._topics
        if not topics:
            return {}

        return {topic.label: topic.centroid for topic in topics}

    def search_by_centroid(
        self,
        centroid: np.ndarray,
        top_k: int = 5,
        embed_type: str = "ideas",
    ) -> list[dict]:
        """Search for items closest to a centroid in embedding space.

        Args:
            centroid: The centroid vector to search around.
            top_k: Number of results to return.
            embed_type: Type of embeddings to search ("ideas" or "claims").

        Returns:
            List of metadata dicts for closest items.
        """
        if embed_type in self._topic_spaces:
            space = self._topic_spaces[embed_type]
            embeddings, metadata = space.embeddings, space.metadata
        else:
            raw, metadata = self._load_embeddings(embed_type)
            embeddings = _l2_normalize(raw)

        similarities = embeddings @ _l2_normalize(centroid)

        top_indices = similarities.argsort()[-top_k:][::-1]

        results = []
        for idx in top_indices:
            item = metadata[idx].copy()
            item["similarity"] = float(similarities[idx])
            results.append(item)

        return results

    def search_by_topic(
        self,
        topic_label: str,
        top_k: int = 5,
        embed_type: str = "ideas",
    ) -> list[dict]:
        """Search for items closest to a topic's centroid.

        Args:
            topic_label: The topic label to search for.
            top_k: Number of results to return.
            embed_type: Type of embeddings to search.

        Returns:
            List of metadata dicts for closest items.
        """
        centroids = self.get_topic_centroids()

        if topic_label not in centroids:
            console.print(f"[yellow]Topic '{topic_label}' not found[/yellow]")
            return []

        return self.search_by_centroid(centroids[topic_label], top_k, embed_type)

    def get_ideas_for_sections(
        self,
        topics: list[ClusterTopic],
        section_topic_mapping: dict[str, list[int | str]],
        ideas_per_section: int = 8,
        topic_space: TopicSpace | None = None,
    ) -> dict[str, list[dict]]:
        """Get relevant ideas for each paper section based on topic mapping.

        Reuses the TopicSpace built in phase 1 (no re-clustering). Uses exclusive
        assignment: each idea can only be assigned to one section. Within each
        cluster, ideas closest to its centroid are preferred.

        Args:
            topics: Topics from phase 1 (used to resolve legacy label keys).
            section_topic_mapping: Section name -> list of cluster_ids (labels
                are accepted for backwards compatibility).
            ideas_per_section: Number of ideas to retrieve per section.
            topic_space: TopicSpace to use. Defaults to the cached ideas space.

        Returns:
            Dict mapping section names to lists of idea dicts, each including
            ``cluster_id`` and ``cluster`` (topic label).
        """
        space = topic_space or self.get_topic_space("ideas")
        label_to_id = {t.label: t.cluster_id for t in topics} if topics else {}

        used_indices: set[int] = set()
        section_ideas: dict[str, list[dict]] = {}

        for section_name, topic_refs in section_topic_mapping.items():
            section_results: list[dict] = []
            ideas_needed = ideas_per_section

            for ref in topic_refs:
                if ideas_needed <= 0:
                    break

                if isinstance(ref, str):
                    cluster_id = label_to_id.get(ref)
                    if cluster_id is None:
                        cluster_id = space.cluster_id_for_label(ref)
                else:
                    cluster_id = int(ref)

                topic = space.topics.get(cluster_id) if cluster_id is not None else None
                if topic is None:
                    continue

                available = [int(i) for i in space.ideas_of(cluster_id) if int(i) not in used_indices]
                if not available:
                    continue

                similarities = space.embeddings[available] @ topic.centroid

                n_to_take = min(2, ideas_needed, len(available))
                top_local = similarities.argsort()[-n_to_take:][::-1]

                for local_idx in top_local:
                    global_idx = available[local_idx]
                    used_indices.add(global_idx)

                    item = space.metadata[global_idx].copy()
                    item["similarity"] = float(similarities[local_idx])
                    item["cluster"] = topic.label
                    item["cluster_id"] = cluster_id
                    section_results.append(item)
                    ideas_needed -= 1

            section_ideas[section_name] = section_results

        return section_ideas
