"""Embedding index for semantic search over processed paper data."""

import json
from pathlib import Path
from typing import Any, TypeVar, Generic

import numpy as np
from openai import OpenAI
from pydantic import BaseModel
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from config.settings import settings

console = Console()

T = TypeVar("T", bound=BaseModel)


class EmbeddingIndex(Generic[T]):
    """Generic embedding index for semantic search.
    
    Can be used with any Pydantic model that has text content to embed.
    """

    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS = 1536

    def __init__(
        self,
        name: str,
        cache_dir: Path | None = None,
        text_field: str = "idea",
        context_fields: list[str] | None = None,
    ) -> None:
        """Initialize the embedding index.

        Args:
            name: Name of the index (e.g., "ideas", "claims", "references").
            cache_dir: Directory for cache files. Defaults to data/processed/embeddings.
            text_field: Primary field to embed from each item.
            context_fields: Additional fields to include in embedding text.
        """
        self.name = name
        self.cache_dir = cache_dir or (settings.paths.data_dir / "processed" / "embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_path = self.cache_dir / f"{name}_index.npz"
        self.metadata_path = self.cache_dir / f"{name}_metadata.json"
        
        self.text_field = text_field
        self.context_fields = context_fields or []
        
        self.client = OpenAI(api_key=settings.ai.openai_api_key)
        
        self.items: list[dict[str, Any]] = []
        self._embeddings_matrix: np.ndarray | None = None
        self._id_to_index: dict[str, int] = {}

    def build_from_jsonl(self, jsonl_path: Path, force_rebuild: bool = False) -> None:
        """Build index from a JSONL file.

        Args:
            jsonl_path: Path to the JSONL file with items to index.
            force_rebuild: If True, rebuild even if cache exists.
        """
        if not force_rebuild and self._load_from_cache():
            console.print(f"[green]✓ Loaded {self.name} index: {len(self.items)} items[/green]")
            return

        console.print(f"[cyan]📚 Building {self.name} index...[/cyan]")
        
        # Load items from JSONL
        self.items = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.items.append(json.loads(line))
        
        console.print(f"  [dim]Loaded {len(self.items)} items from {jsonl_path.name}[/dim]")

        # Generate embeddings
        self._generate_embeddings()

        # Save to cache
        self._save_to_cache()
        console.print(f"[green]✓ {self.name} index built: {len(self.items)} items[/green]")

    def _get_text_for_embedding(self, item: dict[str, Any]) -> str:
        """Extract text to embed from an item.

        Args:
            item: The item dictionary.

        Returns:
            Combined text for embedding.
        """
        parts = []
        
        # Primary text field
        if self.text_field in item:
            parts.append(str(item[self.text_field]))
        
        # Context fields
        for field in self.context_fields:
            if field in item and item[field]:
                value = item[field]
                if isinstance(value, list):
                    parts.append(" ".join(str(v) for v in value))
                else:
                    parts.append(str(value))
        
        return " ".join(parts)

    def _generate_embeddings(self) -> None:
        """Generate embeddings for all items."""
        if not self.items:
            return

        texts_to_embed = [self._get_text_for_embedding(item) for item in self.items]
        
        console.print(f"  [dim]Generating {len(texts_to_embed)} embeddings...[/dim]")

        embeddings = []
        batch_size = 100
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"[cyan]Embedding {self.name}...", total=len(texts_to_embed))
            
            for i in range(0, len(texts_to_embed), batch_size):
                batch = texts_to_embed[i:i + batch_size]
                
                response = self.client.embeddings.create(
                    model=self.EMBEDDING_MODEL,
                    input=batch,
                )
                
                for embedding_data in response.data:
                    embeddings.append(embedding_data.embedding)
                
                progress.update(task, advance=len(batch))
        
        self._embeddings_matrix = np.array(embeddings, dtype=np.float32)
        self._build_id_index()

    def _build_id_index(self) -> None:
        """Build mapping from item IDs to matrix indices."""
        self._id_to_index = {}
        for i, item in enumerate(self.items):
            item_id = item.get("id", str(i))
            self._id_to_index[item_id] = i

    def _load_from_cache(self) -> bool:
        """Load index from cache files.

        Returns:
            True if cache was loaded successfully.
        """
        if not self.cache_path.exists() or not self.metadata_path.exists():
            return False

        try:
            # Load embeddings
            data = np.load(self.cache_path)
            self._embeddings_matrix = data["embeddings"]
            
            # Load metadata
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            self.items = metadata["items"]
            self._build_id_index()
            
            return True
        except Exception as e:
            console.print(f"[yellow]  Failed to load {self.name} cache: {e}[/yellow]")
            return False

    def _save_to_cache(self) -> None:
        """Save index to cache files."""
        # Save embeddings as compressed numpy
        np.savez_compressed(self.cache_path, embeddings=self._embeddings_matrix)
        
        # Save metadata as JSON
        metadata = {"items": self.items}
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False)

    def get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a query text.

        Args:
            text: The text to embed.

        Returns:
            The embedding vector.
        """
        response = self.client.embeddings.create(
            model=self.EMBEDDING_MODEL,
            input=text,
        )
        return np.array(response.data[0].embedding, dtype=np.float32)

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> list[tuple[dict[str, Any], float]]:
        """Search for similar items.

        Args:
            query: The search query.
            top_k: Number of results to return.
            min_score: Minimum similarity score (0-1).

        Returns:
            List of (item, score) tuples, sorted by score descending.
        """
        if self._embeddings_matrix is None or len(self.items) == 0:
            return []

        # Get query embedding
        query_embedding = self.get_embedding(query)
        
        # Compute cosine similarities
        scores = self._cosine_similarity(query_embedding, self._embeddings_matrix)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score >= min_score:
                results.append((self.items[idx], score))
        
        return results

    def search_by_embedding(
        self,
        embedding: np.ndarray,
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> list[tuple[dict[str, Any], float]]:
        """Search using a pre-computed embedding.

        Args:
            embedding: The query embedding vector.
            top_k: Number of results to return.
            min_score: Minimum similarity score.

        Returns:
            List of (item, score) tuples.
        """
        if self._embeddings_matrix is None or len(self.items) == 0:
            return []

        scores = self._cosine_similarity(embedding, self._embeddings_matrix)
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score >= min_score:
                results.append((self.items[idx], score))
        
        return results

    @staticmethod
    def _cosine_similarity(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between query and all items.

        Args:
            query: Query embedding vector.
            matrix: Matrix of item embeddings.

        Returns:
            Array of similarity scores.
        """
        # Normalize query
        query_norm = query / (np.linalg.norm(query) + 1e-10)
        
        # Normalize matrix rows
        matrix_norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
        matrix_normalized = matrix / matrix_norms
        
        # Dot product gives cosine similarity
        return np.dot(matrix_normalized, query_norm)

    def __len__(self) -> int:
        """Return number of items in the index."""
        return len(self.items)
