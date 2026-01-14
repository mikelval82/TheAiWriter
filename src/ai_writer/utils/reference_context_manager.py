"""Reference context manager for intelligent reference selection per section."""

from ai_writer.models.reference import ParsedReference
from ai_writer.utils.reference_index import ReferenceIndex
from rich.console import Console

console = Console()


# Mapping from paper sections to reference sections to extract
SECTION_MAPPING: dict[str, list[str]] = {
    "Introducción": ["abstract", "contributions"],
    "Estado Actual del Arte": ["abstract", "contributions", "methodology", "results"],
    "Identificación del Problema o Brecha": ["limitations", "future_work", "contributions"],
    "La Nueva Perspectiva": ["contributions", "methodology", "results", "notes"],
    "Discusión": ["results", "notes", "limitations", "quotes"],
    "Implicaciones Futuras": ["future_work", "results", "contributions"],
    "Desafíos y Limitaciones": ["limitations", "future_work"],
    "Conclusiones": ["abstract", "results", "quotes", "contributions"],
    "Declaración de Conflicto de Intereses": [],  # No references needed
    "Agradecimientos": [],  # No references needed
    "Referencias Bibliográficas": ["abstract"],  # Just for citation info
}


class ReferenceContextManager:
    """Manages intelligent selection and filtering of references for each paper section."""

    def __init__(
        self,
        reference_index: ReferenceIndex,
        abstract_context: str,
        top_k: int = 8,
    ) -> None:
        """Initialize the context manager.

        Args:
            reference_index: The pre-built reference index.
            abstract_context: The paper's abstract for relevance ranking.
            top_k: Number of top references to select per section.
        """
        self.index = reference_index
        self.abstract_context = abstract_context
        self.top_k = top_k
        
        # Cache for already computed relevance rankings
        self._relevance_cache: dict[str, list[tuple[ParsedReference, float]]] = {}

    def get_context_for_section(
        self,
        section_name: str,
        previous_sections_text: str = "",
    ) -> str:
        """Get optimized reference context for a specific section.

        This method:
        1. Determines which reference sections are relevant for this paper section
        2. Ranks references by semantic similarity to (abstract + section_name + previous_content)
        3. Extracts only the relevant sections from top-k references
        4. Returns formatted context without truncation

        Args:
            section_name: Name of the paper section being written.
            previous_sections_text: Text from previously written sections for context.

        Returns:
            Formatted reference context string.
        """
        # Get the reference sections to extract for this paper section
        relevant_ref_sections = SECTION_MAPPING.get(section_name, ["abstract", "contributions"])
        
        if not relevant_ref_sections:
            return ""  # No references needed for this section

        # Build query for semantic search
        query = self._build_search_query(section_name, previous_sections_text)

        # Get top-k most relevant references
        top_references = self._get_ranked_references(query, section_name)

        if not top_references:
            return ""

        # Extract only relevant sections from each reference
        context_parts = []
        for ref, score in top_references:
            ref_context = self._extract_reference_context(ref, relevant_ref_sections, score)
            if ref_context:
                context_parts.append(ref_context)

        if not context_parts:
            return ""

        header = f"\n\n📚 REFERENCIAS RELEVANTES PARA '{section_name}' ({len(context_parts)} referencias seleccionadas):\n"
        header += "=" * 80 + "\n"
        
        return header + "\n\n".join(context_parts)

    def _build_search_query(self, section_name: str, previous_text: str) -> str:
        """Build search query combining abstract, section name, and previous content.

        Args:
            section_name: Current section being written.
            previous_text: Text from previous sections.

        Returns:
            Combined query string for semantic search.
        """
        # Combine abstract (most important), section name, and recent context
        query_parts = [
            self.abstract_context,
            f"Sección: {section_name}",
        ]
        
        # Add last part of previous text for continuity (limit to avoid too long queries)
        if previous_text:
            # Take last ~1000 chars of previous text
            recent_context = previous_text[-1000:] if len(previous_text) > 1000 else previous_text
            query_parts.append(recent_context)

        return " ".join(query_parts)

    def _get_ranked_references(
        self,
        query: str,
        section_name: str,
    ) -> list[tuple[ParsedReference, float]]:
        """Get references ranked by relevance to query.

        Uses caching to avoid repeated API calls for same section.

        Args:
            query: The search query.
            section_name: Section name for caching.

        Returns:
            List of (reference, score) tuples.
        """
        # Check cache first
        cache_key = section_name
        if cache_key in self._relevance_cache:
            return self._relevance_cache[cache_key]

        # Search using the index
        results = self.index.search(query=query, top_k=self.top_k)
        
        # Cache results
        self._relevance_cache[cache_key] = results
        
        # Log selected references
        if results:
            console.print(f"  [dim]📎 Referencias seleccionadas para '{section_name}':[/dim]")
            for ref, score in results[:3]:  # Show top 3
                console.print(f"     [dim]• {ref.title[:60]}... (score: {score:.3f})[/dim]")

        return results

    def _extract_reference_context(
        self,
        ref: ParsedReference,
        sections_to_extract: list[str],
        relevance_score: float,
    ) -> str:
        """Extract and format relevant sections from a reference.

        Args:
            ref: The parsed reference.
            sections_to_extract: List of section names to extract.
            relevance_score: The relevance score for this reference.

        Returns:
            Formatted reference context string.
        """
        # Get combined content of requested sections (no truncation)
        content = ref.get_sections(sections_to_extract)
        
        if not content.strip():
            return ""

        # Format with citation info
        header = f"--- [{ref.to_citation_str()}] (relevancia: {relevance_score:.2f}) ---\n"
        return header + content

    def get_all_citations(self) -> list[str]:
        """Get all citations from references used.

        Returns:
            List of formatted citations.
        """
        citations = []
        seen = set()
        
        for results in self._relevance_cache.values():
            for ref, _ in results:
                if ref.filename not in seen:
                    citations.append(ref.to_citation_str())
                    seen.add(ref.filename)
        
        return sorted(citations)

    def clear_cache(self) -> None:
        """Clear the relevance cache."""
        self._relevance_cache.clear()
