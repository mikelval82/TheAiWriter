#!/usr/bin/env python3
"""Visualize the embedding space showing explored vs unexplored ideas.

This script creates a 2D visualization of the embedding space using t-SNE or UMAP,
highlighting which ideas were retrieved during paper writing (red) vs not (blue).

Usage:
    python -m ai_writer.analytics.visualize_embedding_space data/logs/run_MyPaper
    python -m ai_writer.analytics.visualize_embedding_space data/logs/run_MyPaper --method umap
    python -m ai_writer.analytics.visualize_embedding_space data/logs/run_MyPaper --save plot.png
"""

import argparse
import json
from pathlib import Path
from collections import Counter

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from rich.console import Console
from rich.progress import track, Progress

console = Console()


def load_ideas_embeddings():
    """Load ideas index with embeddings."""
    from config.settings import settings
    from ai_writer.embeddings.embedding_index import EmbeddingIndex
    
    ideas_index = EmbeddingIndex(
        name="ideas",
        cache_dir=settings.paths.embeddings_dir,
        text_field="idea",
    )
    ideas_index._load_from_cache()
    
    return ideas_index


def simulate_retrievals_and_get_fingerprints(outline: dict) -> set[str]:
    """Simulate retrievals using the new method and return fingerprints of retrieved ideas."""
    from ai_writer.utils.enhanced_context_manager import EnhancedContextManager, SECTION_CONFIGS
    
    abstract = outline.get("thesis_statement", "Paper about AI and empathy")
    ctx_manager = EnhancedContextManager(abstract_context=abstract)
    ctx_manager.reset_exploration_state()
    
    retrieved_fingerprints = set()
    sections = outline.get("sections", [])
    
    for section in sections:
        section_name = section.get("section_name", "Introducción")
        paragraphs = section.get("paragraphs", [])
        
        for para in paragraphs:
            key_idea = para.get("key_idea", "")
            supporting_points = para.get("supporting_points", [])
            
            query_parts = [key_idea]
            if supporting_points:
                query_parts.extend(supporting_points[:2])
            query = " ".join(query_parts)
            
            config = SECTION_CONFIGS.get(section_name, SECTION_CONFIGS["Introducción"])
            
            if config.top_k == 0:
                continue
            
            query_embedding = ctx_manager._get_cached_embedding(query)
            ideas_results = ctx_manager._search_ideas(query_embedding, config, exclude_used=True)
            claims_results = ctx_manager._search_claims(query_embedding, config, exclude_used=True)
            combined = ctx_manager._combine_and_diversify(ideas_results, claims_results, config)
            ctx_manager._mark_items_as_used(combined)
            
            # Track fingerprints of retrieved ideas
            for item, score, item_type in combined:
                if item_type == "idea":
                    fp = ctx_manager._get_item_fingerprint(item, item_type)
                    retrieved_fingerprints.add(fp)
    
    return retrieved_fingerprints


def reduce_dimensions(embeddings: np.ndarray, method: str = "tsne", n_components: int = 2):
    """Reduce embeddings to 2D using t-SNE or UMAP."""
    console.print(f"[cyan]Reduciendo dimensionalidad con {method.upper()}...[/cyan]")
    
    if method == "tsne":
        from sklearn.manifold import TSNE
        reducer = TSNE(
            n_components=n_components,
            perplexity=min(30, len(embeddings) - 1),
            random_state=42,
            max_iter=1000,
            verbose=0,
        )
        reduced = reducer.fit_transform(embeddings)
    elif method == "umap":
        try:
            import umap
            reducer = umap.UMAP(
                n_components=n_components,
                n_neighbors=15,
                min_dist=0.1,
                random_state=42,
            )
            reduced = reducer.fit_transform(embeddings)
        except ImportError:
            console.print("[yellow]UMAP no instalado, usando t-SNE...[/yellow]")
            return reduce_dimensions(embeddings, method="tsne", n_components=n_components)
    elif method == "pca":
        from sklearn.decomposition import PCA
        reducer = PCA(n_components=n_components, random_state=42)
        reduced = reducer.fit_transform(embeddings)
    else:
        raise ValueError(f"Método desconocido: {method}")
    
    return reduced


def create_visualization(
    reduced_embeddings: np.ndarray,
    retrieved_mask: np.ndarray,
    cluster_labels: np.ndarray | None = None,
    title: str = "Embedding Space Exploration",
    save_path: Path | None = None,
    figsize: tuple = (14, 10),
):
    """Create the visualization plot."""
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Split into retrieved and not retrieved
    not_retrieved = ~retrieved_mask
    
    # Plot not retrieved (blue, smaller, more transparent)
    ax.scatter(
        reduced_embeddings[not_retrieved, 0],
        reduced_embeddings[not_retrieved, 1],
        c='#3498db',
        s=15,
        alpha=0.4,
        label=f'No exploradas ({np.sum(not_retrieved):,})',
        edgecolors='none',
    )
    
    # Plot retrieved (red, larger, more opaque)
    ax.scatter(
        reduced_embeddings[retrieved_mask, 0],
        reduced_embeddings[retrieved_mask, 1],
        c='#e74c3c',
        s=50,
        alpha=0.8,
        label=f'Exploradas ({np.sum(retrieved_mask):,})',
        edgecolors='white',
        linewidths=0.5,
    )
    
    # Add cluster boundaries if available
    if cluster_labels is not None:
        unique_labels = np.unique(cluster_labels)
        
        # Calculate exploration per cluster
        cluster_stats = {}
        for label in unique_labels:
            mask = cluster_labels == label
            cluster_size = np.sum(mask)
            explored_in_cluster = np.sum(retrieved_mask & mask)
            cluster_stats[label] = {
                'size': cluster_size,
                'explored': explored_in_cluster,
                'pct': (explored_in_cluster / cluster_size * 100) if cluster_size > 0 else 0
            }
        
        # Draw cluster labels with exploration info
        for label in unique_labels:
            mask = cluster_labels == label
            if np.sum(mask) > 5:
                centroid_x = np.mean(reduced_embeddings[mask, 0])
                centroid_y = np.mean(reduced_embeddings[mask, 1])
                stats = cluster_stats[label]
                
                # Color based on exploration percentage
                if stats['pct'] > 10:
                    color = '#27ae60'  # Green - well explored
                elif stats['pct'] > 0:
                    color = '#f39c12'  # Orange - partially explored  
                else:
                    color = '#c0392b'  # Red - not explored
                
                ax.annotate(
                    f'C{label}\n({stats["explored"]}/{stats["size"]})',
                    (centroid_x, centroid_y),
                    fontsize=7,
                    alpha=0.8,
                    ha='center',
                    va='center',
                    color=color,
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7, edgecolor=color),
                )
    
    # Styling
    ax.set_xlabel('Dimensión 1', fontsize=12)
    ax.set_ylabel('Dimensión 2', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add stats annotation
    total = len(retrieved_mask)
    explored = np.sum(retrieved_mask)
    coverage = explored / total * 100
    
    stats_text = (
        f"Total ideas: {total:,}\n"
        f"Exploradas: {explored:,}\n"
        f"Cobertura: {coverage:.1f}%"
    )
    ax.annotate(
        stats_text,
        xy=(0.02, 0.98),
        xycoords='axes fraction',
        verticalalignment='top',
        fontsize=10,
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
    )
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        console.print(f"[green]✓ Plot guardado en {save_path}[/green]")
    
    return fig, ax


def create_heatmap_visualization(
    reduced_embeddings: np.ndarray,
    retrieved_mask: np.ndarray,
    title: str = "Density of Explored Ideas",
    save_path: Path | None = None,
    figsize: tuple = (14, 10),
):
    """Create a heatmap showing density of exploration."""
    
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # Left: All ideas density
    ax1 = axes[0]
    h1 = ax1.hist2d(
        reduced_embeddings[:, 0],
        reduced_embeddings[:, 1],
        bins=50,
        cmap='Blues',
    )
    ax1.set_title('Densidad de Todas las Ideas', fontsize=12)
    ax1.set_xlabel('Dimensión 1')
    ax1.set_ylabel('Dimensión 2')
    plt.colorbar(h1[3], ax=ax1, label='Conteo')
    
    # Right: Explored ideas density
    ax2 = axes[1]
    explored_emb = reduced_embeddings[retrieved_mask]
    if len(explored_emb) > 0:
        h2 = ax2.hist2d(
            explored_emb[:, 0],
            explored_emb[:, 1],
            bins=50,
            cmap='Reds',
            range=[
                [reduced_embeddings[:, 0].min(), reduced_embeddings[:, 0].max()],
                [reduced_embeddings[:, 1].min(), reduced_embeddings[:, 1].max()],
            ],
        )
        plt.colorbar(h2[3], ax=ax2, label='Conteo')
    ax2.set_title('Densidad de Ideas Exploradas', fontsize=12)
    ax2.set_xlabel('Dimensión 1')
    ax2.set_ylabel('Dimensión 2')
    
    plt.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if save_path:
        heatmap_path = save_path.parent / f"{save_path.stem}_heatmap{save_path.suffix}"
        plt.savefig(heatmap_path, dpi=150, bbox_inches='tight')
        console.print(f"[green]✓ Heatmap guardado en {heatmap_path}[/green]")
    
    return fig, axes


def main():
    parser = argparse.ArgumentParser(
        description="Visualize embedding space exploration"
    )
    parser.add_argument(
        "log_dir",
        type=Path,
        help="Directory containing the run logs (with phase2_outline.json)",
    )
    parser.add_argument(
        "--method",
        choices=["tsne", "umap", "pca"],
        default="tsne",
        help="Dimensionality reduction method (default: tsne)",
    )
    parser.add_argument(
        "--save",
        type=Path,
        default=None,
        help="Path to save the plot (e.g., plot.png)",
    )
    parser.add_argument(
        "--heatmap",
        action="store_true",
        help="Also generate a density heatmap",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Sample N ideas for faster visualization (default: all)",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Don't display the plot (useful for headless environments)",
    )
    parser.add_argument(
        "--show-clusters",
        action="store_true",
        help="Show cluster boundaries and labels",
    )
    parser.add_argument(
        "--n-clusters",
        type=int,
        default=25,
        help="Number of clusters to visualize (default: 25)",
    )
    
    args = parser.parse_args()
    
    # Find outline file
    outline_path = args.log_dir / "phase2_outline.json"
    if not outline_path.exists():
        console.print(f"[red]Error: No se encontró {outline_path}[/red]")
        return 1
    
    # Load outline
    with open(outline_path, encoding="utf-8") as f:
        outline = json.load(f)
    
    title = outline.get("title", "Paper")
    console.print(f"[bold cyan]Visualizando espacio de embeddings para:[/bold cyan] {title}")
    
    # Load ideas index
    console.print("[cyan]Cargando índice de ideas...[/cyan]")
    ideas_index = load_ideas_embeddings()
    
    # Get embeddings matrix
    console.print("[cyan]Extrayendo embeddings...[/cyan]")
    items = ideas_index.items
    
    # Check if embeddings are stored
    embeddings_path = ideas_index.cache_dir / "ideas_index.npz"
    if embeddings_path.exists():
        data = np.load(embeddings_path)
        embeddings = data["embeddings"]
    else:
        console.print("[red]Error: No se encontraron embeddings en caché[/red]")
        return 1
    
    console.print(f"[dim]Embeddings shape: {embeddings.shape}[/dim]")
    
    # Sample if requested
    if args.sample and args.sample < len(embeddings):
        console.print(f"[yellow]Muestreando {args.sample} de {len(embeddings)} ideas[/yellow]")
        indices = np.random.choice(len(embeddings), args.sample, replace=False)
        embeddings_sample = embeddings[indices]
        items_sample = [items[i] for i in indices]
    else:
        embeddings_sample = embeddings
        items_sample = items
        indices = np.arange(len(embeddings))
    
    # Simulate retrievals
    console.print("[cyan]Simulando recuperaciones...[/cyan]")
    retrieved_fingerprints = simulate_retrievals_and_get_fingerprints(outline)
    console.print(f"[dim]Ideas recuperadas: {len(retrieved_fingerprints)}[/dim]")
    
    # Create fingerprints for all items and check which were retrieved
    from ai_writer.utils.enhanced_context_manager import EnhancedContextManager
    ctx = EnhancedContextManager(abstract_context="dummy")
    
    retrieved_mask = np.zeros(len(items_sample), dtype=bool)
    for i, item in enumerate(items_sample):
        fp = ctx._get_item_fingerprint(item, "idea")
        if fp in retrieved_fingerprints:
            retrieved_mask[i] = True
    
    console.print(f"[dim]Ideas exploradas en muestra: {np.sum(retrieved_mask)}[/dim]")
    
    # Compute clusters if requested
    cluster_labels = None
    if args.show_clusters:
        console.print(f"[cyan]Calculando {args.n_clusters} clusters...[/cyan]")
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=args.n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings_sample)
    
    # Reduce dimensions
    reduced = reduce_dimensions(embeddings_sample, method=args.method)
    
    # Determine save path
    if args.save:
        save_path = args.save
    else:
        save_path = args.log_dir / f"embedding_space_{args.method}.png"
    
    # Create main visualization
    console.print("[cyan]Generando visualización...[/cyan]")
    fig, ax = create_visualization(
        reduced,
        retrieved_mask,
        cluster_labels=cluster_labels,
        title=f"Exploración del Espacio de Embeddings\n{title}",
        save_path=save_path,
    )
    
    # Create heatmap if requested
    if args.heatmap:
        create_heatmap_visualization(
            reduced,
            retrieved_mask,
            title=f"Densidad de Exploración - {title}",
            save_path=save_path,
        )
    
    if not args.no_show:
        plt.show()
    
    console.print("[green]✓ Visualización completada[/green]")
    return 0


if __name__ == "__main__":
    exit(main())
