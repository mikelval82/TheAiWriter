"""Reference index with cached embeddings for semantic search."""

import json
from pathlib import Path

import numpy as np
from openai import OpenAI
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ai_writer.models.reference import ParsedReference
from ai_writer.utils.reference_parser import ReferenceParser
from config.settings import settings

console = Console()


class ReferenceIndex:
    """Index of parsed references with cached embeddings for semantic search."""

    EMBEDDING_MODEL = "text-embedding-3-small"
    CACHE_FILENAME = "reference_index.json"

    def __init__(self, references_dir: Path | None = None) -> None:
        """Initialize the reference index.

        Args:
            references_dir: Directory containing markdown references.
                           Defaults to settings.paths.references_markdown_dir
        """
        self.references_dir = references_dir or settings.paths.references_markdown_dir
        self.cache_path = self.references_dir / self.CACHE_FILENAME
        self.client = OpenAI(api_key=settings.ai.openai_api_key)
        self.parser = ReferenceParser()
        
        self.references: list[ParsedReference] = []
        self._embeddings_matrix: np.ndarray | None = None

    def build(self, force_rebuild: bool = False) -> None:
        """Build or load the reference index.

        Args:
            force_rebuild: If True, rebuild even if cache exists.
        """
        if not force_rebuild and self._load_from_cache():
            console.print(f"[green]✓ Loaded {len(self.references)} references from cache[/green]")
            return

        console.print("[cyan]Building reference index...[/cyan]")
        
        # Parse all references
        self.references = self.parser.parse_directory(self.references_dir)
        console.print(f"[dim]  Parsed {len(self.references)} references[/dim]")

        # Generate embeddings
        self._generate_embeddings()

        # Save to cache
        self._save_to_cache()
        console.print(f"[green]✓ Index built and cached ({len(self.references)} references)[/green]")

    def _generate_embeddings(self) -> None:
        """Generate embeddings for all references."""
        texts_to_embed = []
        refs_needing_embedding = []

        for ref in self.references:
            if ref.embedding is None:
                texts_to_embed.append(ref.get_full_text())
                refs_needing_embedding.append(ref)

        if not texts_to_embed:
            console.print("[dim]  All embeddings already cached[/dim]")
            self._build_embeddings_matrix()
            return

        console.print(f"[dim]  Generating {len(texts_to_embed)} embeddings...[/dim]")

        # Batch embedding generation (OpenAI supports up to 2048 inputs)
        batch_size = 100
        for i in range(0, len(texts_to_embed), batch_size):
            batch_texts = texts_to_embed[i:i + batch_size]
            batch_refs = refs_needing_embedding[i:i + batch_size]

            response = self.client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=batch_texts,
            )

            for j, embedding_data in enumerate(response.data):
                batch_refs[j].embedding = embedding_data.embedding

        self._build_embeddings_matrix()

    def _build_embeddings_matrix(self) -> None:
        """Build numpy matrix from embeddings for fast similarity computation."""
        if not self.references:
            return
        
        embeddings = []
        for ref in self.references:
            if ref.embedding:
                embeddings.append(ref.embedding)
            else:
                # Placeholder zero vector if embedding is missing
                embeddings.append([0.0] * 1536)
        
        self._embeddings_matrix = np.array(embeddings)

    def _load_from_cache(self) -> bool:
        """Load index from cache file.

        Returns:
            True if cache was loaded successfully, False otherwise.
        """
        if not self.cache_path.exists():
            return False

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.references = [ParsedReference(**ref_data) for ref_data in data["references"]]
            self._build_embeddings_matrix()
            
            # Check if any new files were added
            current_files = set(f.name for f in self.references_dir.glob("*.md") if f.name.upper() != "ABSTRACT.MD")
            cached_files = set(ref.filename for ref in self.references)
            
            if current_files != cached_files:
                console.print("[yellow]  Cache outdated, rebuilding...[/yellow]")
                return False

            return True
        except Exception as e:
            console.print(f"[yellow]  Failed to load cache: {e}[/yellow]")
            return False

    def _save_to_cache(self) -> None:
        """Save index to cache file."""
        data = {
            "references": [ref.model_dump() for ref in self.references],
        }
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a text query.

        Args:
            text: The text to embed.

        Returns:
            The embedding vector as numpy array.
        """
        response = self.client.embeddings.create(
            model=self.EMBEDDING_MODEL,
            input=text,
        )
        return np.array(response.data[0].embedding)

    def search(
        self,
        query: str,
        top_k: int = 8,
        section_filter: list[str] | None = None,
    ) -> list[tuple[ParsedReference, float]]:
        """Search for references most similar to query.

        Args:
            query: The search query.
            top_k: Number of top results to return.
            section_filter: If provided, only return content from these sections.

        Returns:
            List of (reference, similarity_score) tuples, sorted by relevance.
        """
        if not self.references or self._embeddings_matrix is None:
            return []

        # Get query embedding
        query_embedding = self.get_embedding(query)

        # Compute cosine similarities
        similarities = self._cosine_similarity(query_embedding, self._embeddings_matrix)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            ref = self.references[idx]
            score = similarities[idx]
            results.append((ref, float(score)))

        return results

    def _cosine_similarity(self, query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between query and all references.

        Args:
            query: Query embedding vector.
            matrix: Matrix of reference embeddings.

        Returns:
            Array of similarity scores.
        """
        # Normalize query
        query_norm = query / np.linalg.norm(query)
        
        # Normalize matrix rows
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        matrix_norm = matrix / norms

        # Dot product gives cosine similarity
        return np.dot(matrix_norm, query_norm)

    def get_all_references(self) -> list[ParsedReference]:
        """Get all parsed references.

        Returns:
            List of all ParsedReference objects.
        """
        return self.references
