"""RAG (Retrieval-Augmented Generation) system for paper writing."""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from ai_writer.embeddings.embedding_index import EmbeddingIndex
from config.settings import settings

console = Console()


class RAGSystem:
    """RAG system with three separate indices for ideas, claims, and references."""

    def __init__(
        self,
        indices_dir: Path | None = None,
        embeddings_dir: Path | None = None,
    ) -> None:
        """Initialize the RAG system.

        Args:
            indices_dir: Directory containing JSONL index files.
            embeddings_dir: Directory for embedding cache files.
        """
        self.indices_dir = indices_dir or (settings.paths.data_dir / "processed" / "indices")
        self.embeddings_dir = embeddings_dir or (settings.paths.data_dir / "processed" / "embeddings")
        
        # Initialize the three indices with appropriate text fields
        self.ideas_index = EmbeddingIndex(
            name="ideas",
            cache_dir=self.embeddings_dir,
            text_field="idea",
            context_fields=["context", "keywords", "section", "paper_title"],
        )
        
        self.claims_index = EmbeddingIndex(
            name="claims",
            cache_dir=self.embeddings_dir,
            text_field="claim",
            context_fields=["evidence", "section", "paper_title"],
        )
        
        self.references_index = EmbeddingIndex(
            name="references",
            cache_dir=self.embeddings_dir,
            text_field="title",
            context_fields=["full_citation", "authors", "venue"],
        )

    def build_indices(self, force_rebuild: bool = False) -> None:
        """Build all three indices from JSONL files.

        Args:
            force_rebuild: If True, rebuild even if cache exists.
        """
        console.print("\n[bold blue]🔨 Building RAG Indices[/bold blue]\n")
        
        ideas_path = self.indices_dir / "all_ideas.jsonl"
        claims_path = self.indices_dir / "all_claims.jsonl"
        references_path = self.indices_dir / "all_references.jsonl"
        
        if ideas_path.exists():
            self.ideas_index.build_from_jsonl(ideas_path, force_rebuild)
        else:
            console.print(f"[yellow]⚠ Ideas index not found: {ideas_path}[/yellow]")
        
        if claims_path.exists():
            self.claims_index.build_from_jsonl(claims_path, force_rebuild)
        else:
            console.print(f"[yellow]⚠ Claims index not found: {claims_path}[/yellow]")
        
        if references_path.exists():
            self.references_index.build_from_jsonl(references_path, force_rebuild)
        else:
            console.print(f"[yellow]⚠ References index not found: {references_path}[/yellow]")
        
        console.print("\n[bold green]✓ RAG system ready![/bold green]")
        self._print_summary()

    def _print_summary(self) -> None:
        """Print summary of loaded indices."""
        table = Table(title="RAG Index Summary")
        table.add_column("Index", style="cyan")
        table.add_column("Items", justify="right")
        
        table.add_row("Ideas", str(len(self.ideas_index)))
        table.add_row("Claims", str(len(self.claims_index)))
        table.add_row("References", str(len(self.references_index)))
        
        console.print(table)

    def search_ideas(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.5,
    ) -> list[tuple[dict[str, Any], float]]:
        """Search for relevant ideas.

        Args:
            query: The search query.
            top_k: Number of results.
            min_score: Minimum similarity score.

        Returns:
            List of (idea, score) tuples.
        """
        return self.ideas_index.search(query, top_k, min_score)

    def search_claims(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.5,
    ) -> list[tuple[dict[str, Any], float]]:
        """Search for relevant claims with evidence.

        Args:
            query: The search query.
            top_k: Number of results.
            min_score: Minimum similarity score.

        Returns:
            List of (claim, score) tuples.
        """
        return self.claims_index.search(query, top_k, min_score)

    def search_references(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.5,
    ) -> list[tuple[dict[str, Any], float]]:
        """Search for relevant references.

        Args:
            query: The search query.
            top_k: Number of results.
            min_score: Minimum similarity score.

        Returns:
            List of (reference, score) tuples.
        """
        return self.references_index.search(query, top_k, min_score)

    def search_all(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.5,
    ) -> dict[str, list[tuple[dict[str, Any], float]]]:
        """Search across all indices.

        Args:
            query: The search query.
            top_k: Number of results per index.
            min_score: Minimum similarity score.

        Returns:
            Dictionary with results from each index.
        """
        return {
            "ideas": self.search_ideas(query, top_k, min_score),
            "claims": self.search_claims(query, top_k, min_score),
            "references": self.search_references(query, top_k, min_score),
        }

    def get_context_for_section(
        self,
        section_name: str,
        section_description: str,
        top_k_ideas: int = 8,
        top_k_claims: int = 5,
        top_k_refs: int = 10,
    ) -> dict[str, Any]:
        """Get relevant context for writing a paper section.

        Args:
            section_name: Name of the section being written.
            section_description: Description or outline of the section.
            top_k_ideas: Number of ideas to retrieve.
            top_k_claims: Number of claims to retrieve.
            top_k_refs: Number of references to retrieve.

        Returns:
            Dictionary with ideas, claims, and references for the section.
        """
        query = f"{section_name}: {section_description}"
        
        ideas = self.search_ideas(query, top_k_ideas, min_score=0.4)
        claims = self.search_claims(query, top_k_claims, min_score=0.4)
        references = self.search_references(query, top_k_refs, min_score=0.3)
        
        return {
            "ideas": ideas,
            "claims": claims,
            "references": references,
            "formatted_context": self._format_context(ideas, claims, references),
        }

    def _format_context(
        self,
        ideas: list[tuple[dict, float]],
        claims: list[tuple[dict, float]],
        references: list[tuple[dict, float]],
    ) -> str:
        """Format retrieved context for use in prompts.

        Args:
            ideas: List of (idea, score) tuples.
            claims: List of (claim, score) tuples.
            references: List of (reference, score) tuples.

        Returns:
            Formatted context string.
        """
        parts = []
        
        if ideas:
            parts.append("## Relevant Ideas from Literature\n")
            for idea, score in ideas:
                parts.append(f"- [{idea.get('paper_title', 'Unknown')}] {idea.get('idea', '')}")
                if idea.get('context'):
                    parts.append(f"  Context: {idea['context'][:200]}...")
            parts.append("")
        
        if claims:
            parts.append("## Claims with Evidence\n")
            for claim, score in claims:
                parts.append(f"- **Claim**: {claim.get('claim', '')}")
                parts.append(f"  **Evidence**: {claim.get('evidence', '')}")
                parts.append(f"  Source: {claim.get('paper_title', 'Unknown')}")
            parts.append("")
        
        if references:
            parts.append("## Relevant References\n")
            for ref, score in references:
                citation = ref.get('full_citation') or f"{ref.get('citation_key', '')}: {ref.get('title', '')}"
                parts.append(f"- {citation}")
        
        return "\n".join(parts)
