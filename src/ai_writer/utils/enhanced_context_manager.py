"""Enhanced context manager using ideas, claims, and references indices.

This module provides intelligent, multi-level context selection for paper sections
using semantic search across ideas, claims, and references with configurable
priorities, confidence filtering, and paper diversity constraints.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from rich.console import Console

from ai_writer.embeddings.embedding_index import EmbeddingIndex
from config.settings import settings

console = Console()


@dataclass
class SectionConfig:
    """Configuration for context selection per section type."""
    
    # Weight for ideas vs claims (0.0 = only claims, 1.0 = only ideas)
    ideas_weight: float
    
    # Minimum confidence level for claims ("high", "medium", "low")
    min_confidence: str
    
    # Preferred evidence types for claims (None = all)
    evidence_types: list[str] | None
    
    # Keywords to boost in search (section-specific focus)
    boost_keywords: list[str]
    
    # Maximum items per paper (for diversity)
    max_per_paper: int
    
    # Total items to retrieve
    top_k: int


# Section-specific configurations
# NOTE: top_k increased to ensure enough context per paragraph with exclusion enabled
SECTION_CONFIGS: dict[str, SectionConfig] = {
    "Introducción": SectionConfig(
        ideas_weight=0.7,  # Favor ideas for broad concepts
        min_confidence="medium",
        evidence_types=["citation"],
        boost_keywords=["introduction", "overview", "motivation", "background"],
        max_per_paper=6,  # Increased from 4
        top_k=28,  # Increased from 18
    ),
    "Estado Actual del Arte": SectionConfig(
        ideas_weight=0.8,  # Heavy on ideas - surveying concepts
        min_confidence="medium",
        evidence_types=None,  # All evidence types
        boost_keywords=["state of the art", "survey", "review", "prior work", "related work"],
        max_per_paper=6,  # Increased from 3
        top_k=36,  # Increased from 24
    ),
    "Identificación del Problema o Brecha": SectionConfig(
        ideas_weight=0.5,  # Balanced - need gaps and limitations
        min_confidence="medium",
        evidence_types=["observation", "citation"],
        boost_keywords=["limitation", "gap", "challenge", "problem", "missing", "lack"],
        max_per_paper=6,  # Increased from 4
        top_k=28,  # Increased from 18
    ),
    "La Nueva Perspectiva": SectionConfig(
        ideas_weight=0.6,  # Favor ideas for novel concepts
        min_confidence="high",  # Only high confidence for core contribution
        evidence_types=["experiment", "data"],
        boost_keywords=["novel", "contribution", "approach", "framework", "architecture"],
        max_per_paper=8,  # Increased from 5
        top_k=32,  # Increased from 20
    ),
    "Discusión": SectionConfig(
        ideas_weight=0.3,  # Favor claims with evidence for argumentation
        min_confidence="high",
        evidence_types=["experiment", "data", "citation"],
        boost_keywords=["results", "findings", "analysis", "comparison", "performance"],
        max_per_paper=6,  # Increased from 4
        top_k=32,  # Increased from 20
    ),
    "Implicaciones Futuras": SectionConfig(
        ideas_weight=0.6,
        min_confidence="medium",
        evidence_types=None,
        boost_keywords=["future", "direction", "opportunity", "potential", "emerging"],
        max_per_paper=6,  # Increased from 4
        top_k=28,  # Increased from 18
    ),
    "Desafíos y Limitaciones": SectionConfig(
        ideas_weight=0.4,  # Favor claims about limitations
        min_confidence="medium",
        evidence_types=["observation", "experiment"],
        boost_keywords=["limitation", "challenge", "risk", "difficulty", "constraint"],
        max_per_paper=6,  # Increased from 4
        top_k=24,  # Increased from 16
    ),
    "Conclusiones": SectionConfig(
        ideas_weight=0.5,  # Balanced for synthesis
        min_confidence="high",  # Only high confidence for conclusions
        evidence_types=None,
        boost_keywords=["conclusion", "summary", "key finding", "contribution"],
        max_per_paper=8,  # Increased from 5
        top_k=24,  # Increased from 16
    ),
    # Sections that don't need references
    "Declaración de Conflicto de Intereses": SectionConfig(
        ideas_weight=0.0, min_confidence="high", evidence_types=None,
        boost_keywords=[], max_per_paper=0, top_k=0,
    ),
    "Agradecimientos": SectionConfig(
        ideas_weight=0.0, min_confidence="high", evidence_types=None,
        boost_keywords=[], max_per_paper=0, top_k=0,
    ),
    "Referencias Bibliográficas": SectionConfig(
        ideas_weight=0.0, min_confidence="high", evidence_types=None,
        boost_keywords=[], max_per_paper=0, top_k=0,
    ),
}

# Confidence level ordering
CONFIDENCE_ORDER = {"high": 3, "medium": 2, "low": 1}


class EnhancedContextManager:
    """Manages intelligent, multi-level context selection for paper sections.
    
    Uses semantic search across:
    - Ideas: Key concepts and insights from papers
    - Claims: Statements with evidence and confidence levels
    - References: Paper metadata for citation
    
    Features:
    - Section-specific priorities (ideas vs claims)
    - Confidence filtering for claims
    - Paper diversity constraints
    - Token-efficient formatting
    """

    def __init__(
        self,
        abstract_context: str,
        indices_dir: Path | None = None,
        embeddings_dir: Path | None = None,
    ) -> None:
        """Initialize the enhanced context manager.

        Args:
            abstract_context: The paper's abstract for relevance ranking.
            indices_dir: Directory containing JSONL indices.
            embeddings_dir: Directory containing embedding caches.
        """
        self.abstract_context = abstract_context
        self.indices_dir = indices_dir or (settings.paths.data_dir / "processed" / "indices")
        self.embeddings_dir = embeddings_dir or (settings.paths.data_dir / "processed" / "embeddings")
        
        # Initialize indices
        self.ideas_index = self._load_ideas_index()
        self.claims_index = self._load_claims_index()
        
        # Cache for query embeddings (reuse across sections)
        self._embedding_cache: dict[str, np.ndarray] = {}
        
        # Track used citations for bibliography
        self._used_papers: dict[str, dict[str, Any]] = {}
        
        # ===== EXPLORATION TRACKING =====
        # Track used items to avoid repetition across paragraphs
        self._used_idea_fingerprints: set[str] = set()
        self._used_claim_fingerprints: set[str] = set()
        
        # Track retrieval frequency for popularity penalty
        self._idea_retrieval_counts: dict[str, int] = {}
        self._claim_retrieval_counts: dict[str, int] = {}
        
        # MMR diversity parameter (0=pure relevance, 1=pure diversity)
        self.mmr_lambda: float = 0.7  # 70% relevance, 30% diversity
        
        # ===== CLUSTER-AWARE EXPLORATION =====
        # Track which clusters have been explored
        self._explored_clusters: set[int] = set()
        self._cluster_labels: np.ndarray | None = None
        self._cluster_centroids: np.ndarray | None = None
        self._ideas_embeddings_cache: np.ndarray | None = None
        self._n_clusters: int = 25
        
        # Track positions within clusters for intra-cluster dispersion
        self._cluster_used_positions: dict[int, list[np.ndarray]] = {}
        
        # Fast lookup: idea text -> index (built lazily)
        self._idea_text_to_idx: dict[str, int] | None = None

    # =========================================================================
    # Exploration Helpers
    # =========================================================================
    
    def _build_idea_index_lookup(self) -> None:
        """Build a fast lookup table for idea text -> index."""
        if self._idea_text_to_idx is not None:
            return
        self._idea_text_to_idx = {}
        for idx, item in enumerate(self.ideas_index.items):
            text = item.get("idea", "")[:100]  # Use first 100 chars as key
            self._idea_text_to_idx[text] = idx
    
    def _get_idea_index(self, item: dict) -> int | None:
        """Get the index of an idea item (fast lookup)."""
        self._build_idea_index_lookup()
        if self._idea_text_to_idx is None:
            return None
        text = item.get("idea", "")[:100]
        return self._idea_text_to_idx.get(text)
    
    def _ensure_clusters_computed(self) -> None:
        """Compute clusters if not already done."""
        if self._cluster_labels is not None:
            return
        
        # Load embeddings
        embeddings_path = self.embeddings_dir / "ideas_index.npz"
        if not embeddings_path.exists():
            return
        
        data = np.load(embeddings_path)
        embeddings = data["embeddings"]
        self._ideas_embeddings_cache = embeddings
        
        # Cluster
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=self._n_clusters, random_state=42, n_init=10)
        self._cluster_labels = kmeans.fit_predict(embeddings)
        self._cluster_centroids = kmeans.cluster_centers_
    
    def _get_item_cluster(self, item: dict) -> int | None:
        """Get the cluster ID for an item."""
        if self._cluster_labels is None:
            return None
        
        # Find item index
        for idx, stored_item in enumerate(self.ideas_index.items):
            if stored_item.get("idea", "") == item.get("idea", ""):
                return int(self._cluster_labels[idx])
        return None
    
    def _get_underexplored_clusters(self, top_n: int = 5) -> list[int]:
        """Get clusters that haven't been explored yet."""
        self._ensure_clusters_computed()
        if self._cluster_labels is None:
            return []
        
        all_clusters = set(range(self._n_clusters))
        unexplored = all_clusters - self._explored_clusters
        return list(unexplored)[:top_n]
    
    def _get_item_fingerprint(self, item: dict, item_type: str) -> str:
        """Generate a unique fingerprint for an item to track usage.
        
        Args:
            item: The item dict (idea or claim).
            item_type: "idea" or "claim".
            
        Returns:
            A string fingerprint for deduplication.
        """
        if item_type == "idea":
            text = item.get("idea", "")[:100]
        else:
            text = item.get("claim", "")[:100]
        paper_id = item.get("paper_id", "")
        return f"{item_type}:{paper_id}:{hash(text)}"
    
    def _mark_items_as_used(self, items: list[tuple[dict, float, str]]) -> None:
        """Mark items as used after retrieval.
        
        Args:
            items: List of (item, score, type) tuples.
        """
        self._ensure_clusters_computed()
        
        for item, score, item_type in items:
            fp = self._get_item_fingerprint(item, item_type)
            
            if item_type == "idea":
                self._used_idea_fingerprints.add(fp)
                self._idea_retrieval_counts[fp] = self._idea_retrieval_counts.get(fp, 0) + 1
                
                # Track cluster exploration and position for dispersion (fast lookup)
                if self._cluster_labels is not None and self._ideas_embeddings_cache is not None:
                    idx = self._get_idea_index(item)
                    if idx is not None and idx < len(self._cluster_labels):
                        cluster_id = int(self._cluster_labels[idx])
                        self._explored_clusters.add(cluster_id)
                        
                        # Store normalized embedding for dispersion tracking
                        if idx < len(self._ideas_embeddings_cache):
                            emb = self._ideas_embeddings_cache[idx]
                            emb_norm = emb / (np.linalg.norm(emb) + 1e-10)
                            if cluster_id not in self._cluster_used_positions:
                                self._cluster_used_positions[cluster_id] = []
                            self._cluster_used_positions[cluster_id].append(emb_norm)
            else:
                self._used_claim_fingerprints.add(fp)
                self._claim_retrieval_counts[fp] = self._claim_retrieval_counts.get(fp, 0) + 1
    
    def _is_item_used(self, item: dict, item_type: str) -> bool:
        """Check if an item has already been used.
        
        Args:
            item: The item dict.
            item_type: "idea" or "claim".
            
        Returns:
            True if item was already used in a previous paragraph.
        """
        fp = self._get_item_fingerprint(item, item_type)
        if item_type == "idea":
            return fp in self._used_idea_fingerprints
        else:
            return fp in self._used_claim_fingerprints
    
    def _get_popularity_penalty(self, item: dict, item_type: str) -> float:
        """Get a penalty factor based on how often an item has been retrieved.
        
        Items that appear frequently get penalized to encourage exploration.
        
        Args:
            item: The item dict.
            item_type: "idea" or "claim".
            
        Returns:
            Penalty factor (0.0 to 1.0). Lower = more penalized.
        """
        fp = self._get_item_fingerprint(item, item_type)
        if item_type == "idea":
            count = self._idea_retrieval_counts.get(fp, 0)
        else:
            count = self._claim_retrieval_counts.get(fp, 0)
        
        # Exponential decay: 1.0 for first use, 0.5 for second, 0.25 for third, etc.
        return 1.0 / (2 ** count)
    
    def _get_intracluster_dispersion_penalty(self, item: dict, item_idx: int) -> float:
        """Get penalty based on proximity to already-used items in the same cluster.
        
        This encourages exploring different regions within the same cluster,
        not just picking items that are close together.
        
        Args:
            item: The item dict.
            item_idx: Index of the item in the ideas index.
            
        Returns:
            Penalty factor (0.0 to 1.0). Lower = too close to used items.
        """
        self._ensure_clusters_computed()
        if self._cluster_labels is None or self._ideas_embeddings_cache is None:
            return 1.0
        
        if item_idx >= len(self._cluster_labels):
            return 1.0
        
        cluster_id = int(self._cluster_labels[item_idx])
        used_positions = self._cluster_used_positions.get(cluster_id, [])
        
        if not used_positions:
            return 1.0  # First item in cluster, no penalty
        
        # Get item's embedding
        item_embedding = self._ideas_embeddings_cache[item_idx]
        item_embedding = item_embedding / (np.linalg.norm(item_embedding) + 1e-10)
        
        # Calculate max similarity to already-used items in this cluster
        max_sim = 0.0
        for used_emb in used_positions:
            sim = float(np.dot(item_embedding, used_emb))
            max_sim = max(max_sim, sim)
        
        # Penalize items that are very similar to already-used items
        # similarity 1.0 -> penalty 0.3 (heavily penalized)
        # similarity 0.5 -> penalty 0.7 (moderately penalized)
        # similarity 0.0 -> penalty 1.0 (no penalty)
        penalty = 1.0 - (max_sim * 0.7)
        return max(0.3, penalty)
    
    def _mark_item_position_in_cluster(self, item: dict, item_idx: int) -> None:
        """Track the position of a used item for intra-cluster dispersion."""
        self._ensure_clusters_computed()
        if self._cluster_labels is None or self._ideas_embeddings_cache is None:
            return
        
        if item_idx >= len(self._cluster_labels):
            return
        
        cluster_id = int(self._cluster_labels[item_idx])
        item_embedding = self._ideas_embeddings_cache[item_idx]
        item_embedding = item_embedding / (np.linalg.norm(item_embedding) + 1e-10)
        
        if cluster_id not in self._cluster_used_positions:
            self._cluster_used_positions[cluster_id] = []
        self._cluster_used_positions[cluster_id].append(item_embedding)
    
    def reset_exploration_state(self) -> None:
        """Reset exploration tracking for a new paper.
        
        Call this at the start of writing a new paper.
        """
        self._used_idea_fingerprints.clear()
        self._used_claim_fingerprints.clear()
        self._idea_retrieval_counts.clear()
        self._claim_retrieval_counts.clear()
        self._explored_clusters.clear()
        self._cluster_used_positions.clear()
    
    def get_exploration_stats(self) -> dict:
        """Get statistics about exploration of the embedding space.
        
        Returns:
            Dict with exploration metrics.
        """
        self._ensure_clusters_computed()
        return {
            "unique_ideas_used": len(self._used_idea_fingerprints),
            "unique_claims_used": len(self._used_claim_fingerprints),
            "total_ideas_available": len(self.ideas_index),
            "total_claims_available": len(self.claims_index),
            "ideas_coverage_percent": len(self._used_idea_fingerprints) / max(1, len(self.ideas_index)) * 100,
            "claims_coverage_percent": len(self._used_claim_fingerprints) / max(1, len(self.claims_index)) * 100,
            "clusters_explored": len(self._explored_clusters),
            "total_clusters": self._n_clusters,
            "clusters_coverage_percent": len(self._explored_clusters) / self._n_clusters * 100,
        }

    # =========================================================================
    # Index Loading
    # =========================================================================

    def _load_ideas_index(self) -> EmbeddingIndex:
        """Load the ideas embedding index."""
        index = EmbeddingIndex(
            name="ideas",
            cache_dir=self.embeddings_dir,
            text_field="idea",
            context_fields=["context", "keywords"],
        )
        jsonl_path = self.indices_dir / "all_ideas.jsonl"
        if jsonl_path.exists():
            index.build_from_jsonl(jsonl_path)
        else:
            console.print(f"[yellow]⚠️ Ideas index not found: {jsonl_path}[/yellow]")
        return index

    def _load_claims_index(self) -> EmbeddingIndex:
        """Load the claims embedding index."""
        index = EmbeddingIndex(
            name="claims",
            cache_dir=self.embeddings_dir,
            text_field="claim",
            context_fields=["evidence"],
        )
        jsonl_path = self.indices_dir / "all_claims.jsonl"
        if jsonl_path.exists():
            index.build_from_jsonl(jsonl_path)
        else:
            console.print(f"[yellow]⚠️ Claims index not found: {jsonl_path}[/yellow]")
        return index

    def get_context_for_section(
        self,
        section_name: str,
        previous_sections_text: str = "",
    ) -> str:
        """Get optimized, structured context for a specific section.

        This method:
        1. Gets section-specific configuration (ideas vs claims priority)
        2. Searches both indices with the query
        3. Filters claims by confidence level
        4. Limits items per paper for diversity
        5. Formats context efficiently for LLM consumption

        Args:
            section_name: Name of the paper section being written.
            previous_sections_text: Text from previously written sections.

        Returns:
            Formatted, token-efficient context string.
        """
        config = SECTION_CONFIGS.get(section_name, SECTION_CONFIGS["Introducción"])
        
        if config.top_k == 0:
            return ""  # No context needed for this section
        
        # Build search query
        query = self._build_query(section_name, previous_sections_text, config)
        
        # Get query embedding (cached)
        query_embedding = self._get_cached_embedding(query)
        
        # Search both indices
        ideas_results = self._search_ideas(query_embedding, config)
        claims_results = self._search_claims(query_embedding, config)
        
        # Combine and diversify by paper
        combined = self._combine_and_diversify(
            ideas_results, claims_results, config
        )
        
        if not combined:
            return ""
        
        # Mark items as used for exploration tracking
        self._mark_items_as_used(combined)
        
        # Track papers used
        self._track_used_papers(combined)
        
        # Format for LLM consumption
        return self._format_context(combined, section_name, config)

    def _build_query(
        self,
        section_name: str,
        previous_text: str,
        config: SectionConfig,
    ) -> str:
        """Build search query combining abstract, section, and boost keywords."""
        parts = [self.abstract_context]
        
        # Add section context
        parts.append(f"Sección: {section_name}")
        
        # Add boost keywords
        if config.boost_keywords:
            parts.append(f"Keywords: {', '.join(config.boost_keywords)}")
        
        # Add recent context (limited)
        if previous_text:
            recent = previous_text[-800:] if len(previous_text) > 800 else previous_text
            parts.append(recent)
        
        return " ".join(parts)

    def _get_cached_embedding(self, query: str) -> np.ndarray:
        """Get embedding for query, using cache if available."""
        cache_key = query[:200]  # Use prefix as cache key
        
        if cache_key not in self._embedding_cache:
            self._embedding_cache[cache_key] = self.ideas_index.get_embedding(query)
        
        return self._embedding_cache[cache_key]

    def _search_ideas(
        self,
        query_embedding: np.ndarray,
        config: SectionConfig,
        exclude_used: bool = True,
    ) -> list[tuple[dict[str, Any], float, str]]:
        """Search ideas index with configuration.
        
        Args:
            query_embedding: The query embedding vector.
            config: Section configuration.
            exclude_used: If True, exclude items already used in previous paragraphs.
        
        Returns:
            List of (item, score, type) tuples.
        """
        if config.ideas_weight == 0 or len(self.ideas_index) == 0:
            return []
        
        # Fetch more items to account for filtering
        # Use higher multiplier as pool depletes
        used_ratio = len(self._used_idea_fingerprints) / max(1, len(self.ideas_index))
        adaptive_multiplier = 3 + (used_ratio * 2)  # 3x to 5x as pool depletes
        fetch_multiplier = adaptive_multiplier if exclude_used else 1.5
        ideas_k = max(1, int(config.top_k * config.ideas_weight * fetch_multiplier))
        
        results = self.ideas_index.search_by_embedding(
            query_embedding, top_k=ideas_k, min_score=0.3
        )
        
        # Filter and adjust scores
        filtered_results = []
        fallback_results = []  # Items already used, kept for fallback
        target_count = int(config.top_k * config.ideas_weight)
        
        for item, score in results:
            # Check if already used
            if exclude_used and self._is_item_used(item, "idea"):
                # Keep for fallback with heavy penalty
                penalty = self._get_popularity_penalty(item, "idea") * 0.5
                fallback_results.append((item, score * penalty, "idea"))
                continue
            
            # Apply popularity penalty
            penalty = self._get_popularity_penalty(item, "idea")
            adjusted_score = score * penalty
            
            filtered_results.append((item, adjusted_score, "idea"))
        
        # If we don't have enough new items, add some from fallback
        if len(filtered_results) < target_count and fallback_results:
            needed = target_count - len(filtered_results)
            # Sort fallback by score and take top needed
            fallback_results.sort(key=lambda x: x[1], reverse=True)
            filtered_results.extend(fallback_results[:needed])
        
        # Add ideas from underexplored clusters for diversity (lightweight check)
        if exclude_used and len(self._explored_clusters) < self._n_clusters:
            underexplored_ideas = self._get_ideas_from_underexplored_clusters_fast(max_items=1)
            if underexplored_ideas:
                filtered_results.extend(underexplored_ideas)
        
        return filtered_results
    
    def _get_ideas_from_underexplored_clusters_fast(
        self,
        max_items: int = 1,
    ) -> list[tuple[dict, float, str]]:
        """Get ideas from clusters that haven't been explored yet (fast version).
        
        Uses precomputed embeddings instead of recalculating.
        
        Args:
            max_items: Maximum items to return from underexplored clusters.
            
        Returns:
            List of (item, score, type) tuples from underexplored clusters.
        """
        self._ensure_clusters_computed()
        if self._cluster_centroids is None or self._cluster_labels is None:
            return []
        
        if self._ideas_embeddings_cache is None:
            return []  # No cached embeddings available
        
        underexplored = self._get_underexplored_clusters(top_n=3)
        if not underexplored:
            return []
        
        results = []
        items = self.ideas_index.items
        
        for cluster_id in underexplored[:max_items]:
            # Find items in this cluster
            cluster_mask = self._cluster_labels == cluster_id
            cluster_indices = np.where(cluster_mask)[0]
            
            if len(cluster_indices) == 0:
                continue
            
            # Get random unused item from this cluster (fast, no embedding calc)
            np.random.shuffle(cluster_indices)
            for idx in cluster_indices[:10]:  # Check first 10 random items
                if idx >= len(items):
                    continue
                item = items[idx]
                if not self._is_item_used(item, "idea"):
                    # Use a fixed reasonable score
                    results.append((item, 0.5, "idea"))
                    break
            
            if len(results) >= max_items:
                break
        
        return results

    def _search_claims(
        self,
        query_embedding: np.ndarray,
        config: SectionConfig,
        exclude_used: bool = True,
    ) -> list[tuple[dict[str, Any], float, str]]:
        """Search claims index with configuration and filtering.
        
        Args:
            query_embedding: The query embedding vector.
            config: Section configuration.
            exclude_used: If True, exclude items already used in previous paragraphs.
        
        Returns:
            List of (item, score, type) tuples.
        """
        if config.ideas_weight == 1.0 or len(self.claims_index) == 0:
            return []
        
        # Fetch more items to account for filtering
        # Use higher multiplier as pool depletes
        used_ratio = len(self._used_claim_fingerprints) / max(1, len(self.claims_index))
        adaptive_multiplier = 3 + (used_ratio * 2)  # 3x to 5x as pool depletes
        fetch_multiplier = adaptive_multiplier if exclude_used else 2
        claims_k = max(1, int(config.top_k * (1 - config.ideas_weight) * fetch_multiplier))
        
        results = self.claims_index.search_by_embedding(
            query_embedding, top_k=claims_k, min_score=0.3
        )
        
        # Filter by confidence, evidence type, and usage
        filtered = []
        fallback_results = []  # Items already used, kept for fallback
        target_count = int(config.top_k * (1 - config.ideas_weight))
        min_conf_level = CONFIDENCE_ORDER.get(config.min_confidence, 1)
        
        for item, score in results:
            # Check confidence first
            item_conf = item.get("confidence", "medium")
            if CONFIDENCE_ORDER.get(item_conf, 1) < min_conf_level:
                continue
            
            # Check evidence type if specified
            if config.evidence_types:
                item_type = item.get("evidence_type", "")
                if item_type not in config.evidence_types:
                    continue
            
            # Check if already used
            if exclude_used and self._is_item_used(item, "claim"):
                # Keep for fallback with heavy penalty
                penalty = self._get_popularity_penalty(item, "claim") * 0.5
                fallback_results.append((item, score * penalty, "claim"))
                continue
            
            # Apply popularity penalty
            penalty = self._get_popularity_penalty(item, "claim")
            adjusted_score = score * penalty
            
            filtered.append((item, adjusted_score, "claim"))
        
        # If we don't have enough new items, add some from fallback
        if len(filtered) < target_count and fallback_results:
            needed = target_count - len(filtered)
            fallback_results.sort(key=lambda x: x[1], reverse=True)
            filtered.extend(fallback_results[:needed])
        
        return filtered

    def _combine_and_diversify(
        self,
        ideas: list[tuple[dict, float, str]],
        claims: list[tuple[dict, float, str]],
        config: SectionConfig,
    ) -> list[tuple[dict, float, str]]:
        """Combine results and enforce diversity using MMR.
        
        Uses Maximal Marginal Relevance (MMR) to balance relevance with diversity,
        avoiding retrieving semantically similar items repeatedly.
        
        Args:
            ideas: Ideas results with scores.
            claims: Claims results with scores.
            config: Section configuration.
            
        Returns:
            Combined, diversified list limited to top_k.
        """
        # Combine all results
        all_results = ideas + claims
        
        if not all_results:
            return []
        
        # Sort by score (descending) for initial ranking
        all_results.sort(key=lambda x: x[1], reverse=True)
        
        # Apply MMR for diversity
        selected = self._apply_mmr(all_results, config.top_k, config.max_per_paper)
        
        return selected
    
    def _apply_mmr(
        self,
        candidates: list[tuple[dict, float, str]],
        target_k: int,
        max_per_paper: int,
    ) -> list[tuple[dict, float, str]]:
        """Apply Maximal Marginal Relevance to select diverse items.
        
        MMR score = λ * relevance - (1-λ) * max_similarity_to_selected
        
        Also considers items used in previous paragraphs for better dispersion.
        
        Args:
            candidates: List of (item, score, type) sorted by score desc.
            target_k: Target number of items to select.
            max_per_paper: Maximum items from same paper.
            
        Returns:
            Selected diverse items.
        """
        if not candidates or target_k <= 0:
            return []
        
        # Get embeddings for all candidates using cached embeddings if available
        self._ensure_clusters_computed()
        embeddings = []
        
        for item, score, item_type in candidates:
            emb = None
            
            # Try to get from cached embeddings (fast lookup)
            if self._ideas_embeddings_cache is not None and item_type == "idea":
                idx = self._get_idea_index(item)
                if idx is not None and idx < len(self._ideas_embeddings_cache):
                    emb = self._ideas_embeddings_cache[idx]
            
            if emb is None:
                # Fallback: use a hash-based pseudo-embedding
                fingerprint = self._get_item_fingerprint(item, item_type)
                hash_val = hash(fingerprint)
                emb = np.array([((hash_val >> i) & 0xFF) / 255.0 for i in range(0, 128, 8)])
            
            embeddings.append(np.array(emb))
        
        # If we can't get embeddings, fall back to score-based selection
        if all(len(e) <= 16 for e in embeddings):
            return self._select_by_score_and_paper_diversity(candidates, target_k, max_per_paper)
        
        # Get the target embedding dimension (should be 1536)
        target_dim = max(len(e) for e in embeddings)
        
        # Filter out pseudo-embeddings and keep only real ones
        embeddings = [e if len(e) == target_dim else None for e in embeddings]
        
        # Normalize valid embeddings
        for i, e in enumerate(embeddings):
            if e is not None:
                embeddings[i] = e / (np.linalg.norm(e) + 1e-10)
        
        selected: list[tuple[dict, float, str]] = []
        selected_indices: list[int] = []
        selected_embeddings: list[np.ndarray] = []
        paper_counts: dict[str, int] = {}
        
        # Include previously used embeddings for dispersion (only matching dimensions)
        previously_used_embeddings: list[np.ndarray] = []
        for cluster_id, positions in self._cluster_used_positions.items():
            for pos in positions:
                if len(pos) == target_dim:
                    previously_used_embeddings.append(pos)
        
        # Select items using MMR
        remaining = list(range(len(candidates)))
        
        while len(selected) < target_k and remaining:
            best_idx = -1
            best_mmr_score = float('-inf')
            
            for idx in remaining:
                item, relevance_score, item_type = candidates[idx]
                paper_id = item.get("paper_id", "unknown")
                
                # Check paper limit
                if paper_counts.get(paper_id, 0) >= max_per_paper:
                    continue
                
                # Calculate MMR score
                candidate_emb = embeddings[idx]
                
                # Skip if no valid embedding for this candidate
                if candidate_emb is None:
                    # Use pure relevance score for items without embeddings
                    mmr_score = relevance_score * 0.5  # Slightly penalize
                elif not selected_embeddings and not previously_used_embeddings:
                    # First item ever: use pure relevance
                    mmr_score = relevance_score
                else:
                    # Calculate max similarity to already selected AND previously used
                    # Only compare with embeddings of same dimension
                    all_used_embs = [e for e in (selected_embeddings + previously_used_embeddings) if e is not None]
                    if all_used_embs:
                        max_sim = max(
                            (np.dot(candidate_emb, used_emb) for used_emb in all_used_embs),
                            default=0.0
                        )
                    else:
                        max_sim = 0.0
                    # MMR = λ * relevance - (1-λ) * max_similarity
                    mmr_score = (
                        self.mmr_lambda * relevance_score
                        - (1 - self.mmr_lambda) * max_sim
                    )
                
                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_idx = idx
            
            if best_idx == -1:
                # No valid candidates left (all hit paper limit)
                break
            
            # Add best item to selected
            item, score, item_type = candidates[best_idx]
            selected.append((item, score, item_type))
            selected_indices.append(best_idx)
            
            # Only add valid embeddings to the comparison list
            if embeddings[best_idx] is not None:
                selected_embeddings.append(embeddings[best_idx])
            
            # Update paper counts
            paper_id = item.get("paper_id", "unknown")
            paper_counts[paper_id] = paper_counts.get(paper_id, 0) + 1
            
            # Remove from remaining
            remaining.remove(best_idx)
        
        return selected
    
    def _select_by_score_and_paper_diversity(
        self,
        candidates: list[tuple[dict, float, str]],
        target_k: int,
        max_per_paper: int,
    ) -> list[tuple[dict, float, str]]:
        """Fallback: select by score with paper diversity constraint."""
        paper_counts: dict[str, int] = {}
        selected: list[tuple[dict, float, str]] = []
        
        for item, score, item_type in candidates:
            paper_id = item.get("paper_id", "unknown")
            
            if paper_counts.get(paper_id, 0) >= max_per_paper:
                continue
            
            paper_counts[paper_id] = paper_counts.get(paper_id, 0) + 1
            selected.append((item, score, item_type))
            
            if len(selected) >= target_k:
                break
        
        return selected

    def _track_used_papers(self, items: list[tuple[dict, float, str]]) -> None:
        """Track papers used for bibliography."""
        for item, _, _ in items:
            paper_id = item.get("paper_id", "")
            if paper_id and paper_id not in self._used_papers:
                self._used_papers[paper_id] = {
                    "title": item.get("paper_title", ""),
                    "authors": item.get("authors", []),
                    "year": item.get("year", ""),
                }

    def _format_context(
        self,
        items: list[tuple[dict, float, str]],
        section_name: str,
        config: SectionConfig,
    ) -> str:
        """Format context efficiently for LLM consumption.
        
        Uses a compact format that preserves essential information
        while minimizing token usage.
        """
        if not items:
            return ""
        
        lines = [
            f"\n📚 CONTEXTO PARA '{section_name}' ({len(items)} items):",
            "─" * 60,
        ]
        
        # Group by type for clarity
        ideas_items = [(i, s) for i, s, t in items if t == "idea"]
        claims_items = [(i, s) for i, s, t in items if t == "claim"]
        
        # Format ideas (compact)
        if ideas_items:
            lines.append("\n💡 IDEAS CLAVE:")
            for item, score in ideas_items:
                lines.append(self._format_idea_compact(item, score))
        
        # Format claims (compact)
        if claims_items:
            lines.append("\n📋 CLAIMS CON EVIDENCIA:")
            for item, score in claims_items:
                lines.append(self._format_claim_compact(item, score))
        
        lines.append("─" * 60)
        return "\n".join(lines)

    def _format_idea_compact(self, item: dict, score: float) -> str:
        """Format a single idea in compact form.
        
        Extracts only: idea text, paper title, importance, keywords (top 3)
        """
        idea = item.get("idea", "")
        paper = item.get("paper_title", "")[:50]  # Truncate long titles
        importance = item.get("importance", "")
        keywords = item.get("keywords", [])[:3]  # Top 3 keywords
        
        # Single line format
        kw_str = f" [{', '.join(keywords)}]" if keywords else ""
        imp_marker = "⭐" if importance == "high" else "•"
        
        return f"{imp_marker} [{paper}] {idea}{kw_str}"

    def _format_claim_compact(self, item: dict, score: float) -> str:
        """Format a single claim in compact form.
        
        Extracts: claim, evidence summary, confidence, paper
        """
        claim = item.get("claim", "")
        evidence = item.get("evidence", "")
        confidence = item.get("confidence", "")
        evidence_type = item.get("evidence_type", "")
        paper = item.get("paper_title", "")[:40]
        
        # Truncate evidence to key part
        if len(evidence) > 150:
            evidence = evidence[:150] + "..."
        
        # Confidence marker
        conf_marker = {"high": "✓", "medium": "○", "low": "?"}.get(confidence, "")
        type_marker = {"experiment": "🔬", "data": "📊", "citation": "📖", "observation": "👁️"}.get(evidence_type, "")
        
        lines = [
            f"{conf_marker}{type_marker} [{paper}]",
            f"   Claim: {claim}",
            f"   Evidence: {evidence}",
        ]
        return "\n".join(lines)

    def get_used_papers(self) -> list[dict[str, Any]]:
        """Get list of all papers referenced in context.
        
        Returns:
            List of paper metadata dicts for bibliography.
        """
        return list(self._used_papers.values())

    def get_citation_string(self, paper_id: str) -> str:
        """Get formatted citation string for a paper.
        
        Args:
            paper_id: The paper's unique ID.
            
        Returns:
            Formatted citation string.
        """
        if paper_id not in self._used_papers:
            return ""
        
        paper = self._used_papers[paper_id]
        authors = paper.get("authors", [])
        year = paper.get("year", "")
        title = paper.get("title", "")
        
        if authors:
            if len(authors) == 1:
                author_str = authors[0]
            elif len(authors) == 2:
                author_str = f"{authors[0]} & {authors[1]}"
            else:
                author_str = f"{authors[0]} et al."
        else:
            author_str = "Unknown"
        
        return f"{author_str} ({year}). {title}"

    def get_all_citations(self) -> list[str]:
        """Get all citations as formatted strings.
        
        Returns:
            List of formatted citation strings.
        """
        citations = []
        for paper_id, paper in self._used_papers.items():
            cite = self.get_citation_string(paper_id)
            if cite:
                citations.append(cite)
        return sorted(citations)

    def reset_usage_tracking(self) -> None:
        """Reset the paper usage tracking for a new paper generation."""
        self._used_papers.clear()
        self._embedding_cache.clear()

    # =========================================================================
    # Idea-Specific Context (for Advanced Orchestrator)
    # =========================================================================

    def get_context_for_idea(
        self,
        idea_query: str,
        section_name: str,
        suggested_topics: list[str] | None = None,
    ) -> str:
        """Get context for a specific idea query (paragraph-level).
        
        This method is designed for the advanced orchestrator where queries
        are built from paragraph-level key ideas rather than the abstract.
        
        Args:
            idea_query: The key idea and supporting points as a query string.
            section_name: Name of the section being written.
            suggested_topics: Optional topic suggestions from the planner.
            
        Returns:
            Formatted context string for the paragraph.
        """
        # Get section config, fallback to Introducción if not found
        config = SECTION_CONFIGS.get(section_name, SECTION_CONFIGS["Introducción"])
        
        if config.top_k == 0:
            return ""
        
        # Build query from the idea (NOT the abstract)
        query_parts = [idea_query]
        
        # Add suggested topics if available
        if suggested_topics:
            query_parts.append(f"Topics: {', '.join(suggested_topics[:3])}")
        
        # Add section keywords for fine-tuning
        if config.boost_keywords:
            query_parts.append(f"Keywords: {', '.join(config.boost_keywords[:3])}")
        
        query = " ".join(query_parts)
        
        # Get embedding for this specific query
        query_embedding = self._get_cached_embedding(query)
        
        # Search both indices
        ideas_results = self._search_ideas(query_embedding, config)
        claims_results = self._search_claims(query_embedding, config)
        
        # Combine and diversify
        combined = self._combine_and_diversify(
            ideas_results, claims_results, config
        )
        
        if not combined:
            return ""
        
        # Mark items as used for exploration tracking
        self._mark_items_as_used(combined)
        
        # Track papers used
        self._track_used_papers(combined)
        
        # Format for LLM consumption
        return self._format_context(combined, section_name, config)
