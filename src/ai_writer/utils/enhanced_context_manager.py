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
SECTION_CONFIGS: dict[str, SectionConfig] = {
    "Introducción": SectionConfig(
        ideas_weight=0.7,  # Favor ideas for broad concepts
        min_confidence="medium",
        evidence_types=["citation"],
        boost_keywords=["introduction", "overview", "motivation", "background"],
        max_per_paper=4,
        top_k=12,
    ),
    "Estado Actual del Arte": SectionConfig(
        ideas_weight=0.8,  # Heavy on ideas - surveying concepts
        min_confidence="medium",
        evidence_types=None,  # All evidence types
        boost_keywords=["state of the art", "survey", "review", "prior work", "related work"],
        max_per_paper=3,  # More diversity for survey
        top_k=18,
    ),
    "Identificación del Problema o Brecha": SectionConfig(
        ideas_weight=0.5,  # Balanced - need gaps and limitations
        min_confidence="medium",
        evidence_types=["observation", "citation"],
        boost_keywords=["limitation", "gap", "challenge", "problem", "missing", "lack"],
        max_per_paper=4,
        top_k=12,
    ),
    "La Nueva Perspectiva": SectionConfig(
        ideas_weight=0.6,  # Favor ideas for novel concepts
        min_confidence="high",  # Only high confidence for core contribution
        evidence_types=["experiment", "data"],
        boost_keywords=["novel", "contribution", "approach", "framework", "architecture"],
        max_per_paper=5,
        top_k=15,
    ),
    "Discusión": SectionConfig(
        ideas_weight=0.3,  # Favor claims with evidence for argumentation
        min_confidence="high",
        evidence_types=["experiment", "data", "citation"],
        boost_keywords=["results", "findings", "analysis", "comparison", "performance"],
        max_per_paper=4,
        top_k=14,
    ),
    "Implicaciones Futuras": SectionConfig(
        ideas_weight=0.6,
        min_confidence="medium",
        evidence_types=None,
        boost_keywords=["future", "direction", "opportunity", "potential", "emerging"],
        max_per_paper=4,
        top_k=12,
    ),
    "Desafíos y Limitaciones": SectionConfig(
        ideas_weight=0.4,  # Favor claims about limitations
        min_confidence="medium",
        evidence_types=["observation", "experiment"],
        boost_keywords=["limitation", "challenge", "risk", "difficulty", "constraint"],
        max_per_paper=4,
        top_k=10,
    ),
    "Conclusiones": SectionConfig(
        ideas_weight=0.5,  # Balanced for synthesis
        min_confidence="high",  # Only high confidence for conclusions
        evidence_types=None,
        boost_keywords=["conclusion", "summary", "key finding", "contribution"],
        max_per_paper=5,
        top_k=10,
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
    ) -> list[tuple[dict[str, Any], float, str]]:
        """Search ideas index with configuration.
        
        Returns:
            List of (item, score, type) tuples.
        """
        if config.ideas_weight == 0 or len(self.ideas_index) == 0:
            return []
        
        # Calculate how many ideas to fetch based on weight
        ideas_k = max(1, int(config.top_k * config.ideas_weight * 1.5))
        
        results = self.ideas_index.search_by_embedding(
            query_embedding, top_k=ideas_k, min_score=0.3
        )
        
        # Tag as ideas
        return [(item, score, "idea") for item, score in results]

    def _search_claims(
        self,
        query_embedding: np.ndarray,
        config: SectionConfig,
    ) -> list[tuple[dict[str, Any], float, str]]:
        """Search claims index with configuration and filtering.
        
        Returns:
            List of (item, score, type) tuples.
        """
        if config.ideas_weight == 1.0 or len(self.claims_index) == 0:
            return []
        
        # Calculate how many claims to fetch
        claims_k = max(1, int(config.top_k * (1 - config.ideas_weight) * 2))
        
        results = self.claims_index.search_by_embedding(
            query_embedding, top_k=claims_k, min_score=0.3
        )
        
        # Filter by confidence and evidence type
        filtered = []
        min_conf_level = CONFIDENCE_ORDER.get(config.min_confidence, 1)
        
        for item, score in results:
            # Check confidence
            item_conf = item.get("confidence", "medium")
            if CONFIDENCE_ORDER.get(item_conf, 1) < min_conf_level:
                continue
            
            # Check evidence type if specified
            if config.evidence_types:
                item_type = item.get("evidence_type", "")
                if item_type not in config.evidence_types:
                    continue
            
            filtered.append((item, score, "claim"))
        
        return filtered

    def _combine_and_diversify(
        self,
        ideas: list[tuple[dict, float, str]],
        claims: list[tuple[dict, float, str]],
        config: SectionConfig,
    ) -> list[tuple[dict, float, str]]:
        """Combine results and enforce paper diversity.
        
        Args:
            ideas: Ideas results with scores.
            claims: Claims results with scores.
            config: Section configuration.
            
        Returns:
            Combined, diversified list limited to top_k.
        """
        # Combine all results
        all_results = ideas + claims
        
        # Sort by score (descending)
        all_results.sort(key=lambda x: x[1], reverse=True)
        
        # Apply paper diversity constraint
        paper_counts: dict[str, int] = {}
        diversified = []
        
        for item, score, item_type in all_results:
            paper_id = item.get("paper_id", "unknown")
            
            # Check paper limit
            current_count = paper_counts.get(paper_id, 0)
            if current_count >= config.max_per_paper:
                continue
            
            paper_counts[paper_id] = current_count + 1
            diversified.append((item, score, item_type))
            
            # Stop when we have enough
            if len(diversified) >= config.top_k:
                break
        
        return diversified

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
