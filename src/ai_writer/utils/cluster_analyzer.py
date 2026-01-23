"""Cluster analyzer for extracting topics from embedding space."""

from pathlib import Path
from dataclasses import dataclass, field

import numpy as np
from rich.console import Console
from rich.table import Table

from config.settings import settings

console = Console()


@dataclass
class ClusterTopic:
    """A topic extracted from a cluster of embeddings."""
    
    cluster_id: int
    label: str  # Human-readable topic name
    keywords: list[str]  # Top keywords from TF-IDF
    representative_ideas: list[str]  # Ideas closest to centroid
    size: int  # Number of items in cluster
    centroid: np.ndarray = field(repr=False)  # Cluster centroid for queries
    
    def to_query(self) -> str:
        """Convert topic to a search query."""
        parts = [self.label] + self.keywords[:3]
        return " ".join(parts)


class ClusterAnalyzer:
    """Analyzes embedding space to extract main topics."""
    
    def __init__(
        self,
        embeddings_dir: Path | None = None,
        n_clusters: int = 25,  # Increased from 10 for better exploration
    ) -> None:
        """Initialize the cluster analyzer.
        
        Args:
            embeddings_dir: Directory containing embedding files.
            n_clusters: Number of clusters to create.
        """
        self.embeddings_dir = embeddings_dir or settings.paths.embeddings_dir
        self.n_clusters = n_clusters
        
        # Will be loaded on demand
        self._ideas_embeddings: np.ndarray | None = None
        self._ideas_metadata: list[dict] | None = None
        self._claims_embeddings: np.ndarray | None = None
        self._claims_metadata: list[dict] | None = None
        
        # Cluster results
        self._topics: list[ClusterTopic] | None = None
    
    def _load_embeddings(self, embed_type: str = "ideas") -> tuple[np.ndarray, list[dict]]:
        """Load embeddings and metadata from disk.
        
        Args:
            embed_type: Type of embeddings ("ideas" or "claims").
            
        Returns:
            Tuple of (embeddings array, metadata list).
        """
        import json
        
        index_path = self.embeddings_dir / f"{embed_type}_index.npz"
        metadata_path = self.embeddings_dir / f"{embed_type}_metadata.json"
        
        if not index_path.exists():
            raise FileNotFoundError(f"Index not found: {index_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found: {metadata_path}")
        
        data = np.load(index_path)
        embeddings = data["embeddings"]
        
        with open(metadata_path, encoding="utf-8") as f:
            metadata_raw = json.load(f)
        
        # Handle both list and dict formats
        if isinstance(metadata_raw, dict) and "items" in metadata_raw:
            metadata = metadata_raw["items"]
        elif isinstance(metadata_raw, list):
            metadata = metadata_raw
        else:
            raise ValueError(f"Unexpected metadata format: {type(metadata_raw)}")
        
        return embeddings, metadata
    
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
        labels = kmeans.fit_predict(embeddings)
        centroids = kmeans.cluster_centers_
        
        return labels, centroids
    
    def _extract_keywords(
        self,
        texts: list[str],
        n_keywords: int = 5,
    ) -> list[str]:
        """Extract top keywords from texts using TF-IDF.
        
        Args:
            texts: List of text documents.
            n_keywords: Number of top keywords to extract.
            
        Returns:
            List of top keywords.
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        if not texts:
            return []
        
        # Spanish stop words
        stop_words = [
            "de", "la", "el", "en", "y", "a", "los", "que", "del", "las", 
            "un", "por", "con", "para", "una", "su", "es", "se", "como",
            "más", "al", "lo", "le", "ya", "o", "fue", "ha", "son", "pero",
            "sus", "the", "and", "of", "to", "in", "for", "is", "on", "that",
            "with", "as", "are", "this", "be", "from", "or", "an", "by", "we",
            "can", "also", "these", "which", "our", "their", "has", "have",
        ]
        
        try:
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words=stop_words,
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.9,
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get average TF-IDF scores across all documents
            avg_scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
            top_indices = avg_scores.argsort()[-n_keywords:][::-1]
            
            return [feature_names[i] for i in top_indices]
        except ValueError:
            # Not enough documents or vocabulary
            return []
    
    def _generate_topic_label(
        self,
        keywords: list[str],
        representative_ideas: list[str],
    ) -> str:
        """Generate a human-readable topic label.
        
        Args:
            keywords: Top keywords for the cluster.
            representative_ideas: Representative ideas from the cluster.
            
        Returns:
            Topic label string.
        """
        if keywords:
            # Use top 2 keywords as label
            return " + ".join(keywords[:2]).title()
        elif representative_ideas:
            # Fallback: truncate first idea
            return representative_ideas[0][:50] + "..."
        else:
            return "Unknown Topic"
    
    def analyze(self, embed_type: str = "ideas") -> list[ClusterTopic]:
        """Analyze embedding space and extract topics.
        
        Args:
            embed_type: Type of embeddings to analyze ("ideas" or "claims").
            
        Returns:
            List of ClusterTopic objects.
        """
        console.print(f"[cyan]🔬 Analyzing {embed_type} embedding space...[/cyan]")
        
        # Load embeddings
        embeddings, metadata = self._load_embeddings(embed_type)
        console.print(f"  Loaded {len(embeddings)} embeddings")
        
        # Cluster
        labels, centroids = self._cluster_embeddings(embeddings)
        console.print(f"  Created {len(centroids)} clusters")
        
        # Extract topics from each cluster
        topics = []
        for cluster_id in range(len(centroids)):
            # Get indices of items in this cluster
            cluster_mask = labels == cluster_id
            cluster_indices = np.where(cluster_mask)[0]
            
            if len(cluster_indices) == 0:
                continue
            
            # Get texts for this cluster
            # Try different field names depending on embed_type
            cluster_texts = []
            for i in cluster_indices:
                item = metadata[i]
                # ideas have 'idea' field, claims have 'statement' field
                text = item.get("idea") or item.get("statement") or item.get("text") or item.get("content", "")
                cluster_texts.append(text)
            
            # Extract keywords
            keywords = self._extract_keywords(cluster_texts)
            
            # Find representative ideas (closest to centroid)
            cluster_embeddings = embeddings[cluster_mask]
            centroid = centroids[cluster_id]
            
            # Compute distances to centroid
            distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
            closest_indices = distances.argsort()[:3]  # Top 3 closest
            
            representative_ideas = [cluster_texts[i] for i in closest_indices]
            
            # Generate label
            label = self._generate_topic_label(keywords, representative_ideas)
            
            topic = ClusterTopic(
                cluster_id=cluster_id,
                label=label,
                keywords=keywords,
                representative_ideas=representative_ideas,
                size=len(cluster_indices),
                centroid=centroid,
            )
            topics.append(topic)
        
        # Sort by cluster size (descending)
        topics.sort(key=lambda t: t.size, reverse=True)
        
        self._topics = topics
        return topics
    
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
        
        lines = ["# Temas Principales Identificados en la Literatura\n"]
        
        for i, topic in enumerate(topics, 1):
            lines.append(f"## {i}. {topic.label}")
            lines.append(f"- **Palabras clave:** {', '.join(topic.keywords[:5])}")
            lines.append(f"- **Cantidad de ideas:** {topic.size}")
            lines.append(f"- **Idea representativa:** \"{topic.representative_ideas[0][:200]}...\"")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_topic_centroids(self, topics: list[ClusterTopic] | None = None) -> dict[str, np.ndarray]:
        """Get centroids for each topic for targeted searches.
        
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
        embeddings, metadata = self._load_embeddings(embed_type)
        
        # Compute cosine similarity (embeddings are normalized)
        # For L2-normalized vectors, cosine similarity = dot product
        similarities = np.dot(embeddings, centroid)
        
        # Get top-k indices
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
        section_topic_mapping: dict[str, list[str]],
        ideas_per_section: int = 8,
    ) -> dict[str, list[dict]]:
        """Get relevant ideas for each paper section based on topic mapping.
        
        Uses exclusive assignment: each idea can only be assigned to one section.
        Prioritizes ideas that are both close to centroid AND belong to the cluster.
        
        Args:
            topics: List of ClusterTopic objects.
            section_topic_mapping: Dict mapping section names to relevant topic labels.
            ideas_per_section: Number of ideas to retrieve per section.
            
        Returns:
            Dict mapping section names to lists of relevant ideas.
        """
        # Load embeddings once
        embeddings, metadata = self._load_embeddings("ideas")
        
        # Get cluster assignments for each embedding
        from sklearn.cluster import KMeans
        n_clusters = min(self.n_clusters, len(embeddings))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Create mapping from topic label to cluster_id
        topic_to_cluster = {t.label: t.cluster_id for t in topics}
        
        # Track which ideas have been used (exclusive assignment)
        used_indices = set()
        section_ideas = {}
        
        for section_name, topic_labels in section_topic_mapping.items():
            section_results = []
            ideas_needed = ideas_per_section
            
            for label in topic_labels:
                if label not in topic_to_cluster:
                    continue
                
                cluster_id = topic_to_cluster[label]
                centroid = topics[next(i for i, t in enumerate(topics) if t.label == label)].centroid
                
                # Find ideas that BELONG to this cluster (not just close to centroid)
                cluster_mask = cluster_labels == cluster_id
                cluster_indices = np.where(cluster_mask)[0]
                
                # Filter out already used indices
                available_indices = [i for i in cluster_indices if i not in used_indices]
                
                if not available_indices:
                    continue
                
                # Compute similarity to centroid for available ideas
                available_embeddings = embeddings[available_indices]
                similarities = np.dot(available_embeddings, centroid)
                
                # Get top ideas from THIS cluster
                n_to_take = min(2, ideas_needed, len(available_indices))
                top_local_indices = similarities.argsort()[-n_to_take:][::-1]
                
                for local_idx in top_local_indices:
                    global_idx = available_indices[local_idx]
                    used_indices.add(global_idx)
                    
                    item = metadata[global_idx].copy()
                    item["similarity"] = float(similarities[local_idx])
                    item["cluster"] = label
                    section_results.append(item)
                    ideas_needed -= 1
                    
                    if ideas_needed <= 0:
                        break
                
                if ideas_needed <= 0:
                    break
            
            section_ideas[section_name] = section_results
        
        return section_ideas
        
        return section_ideas
