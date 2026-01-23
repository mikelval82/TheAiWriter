#!/usr/bin/env python3
"""Visualize embedding spaces with clustering and topic extraction."""

import json
import sys
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Check dependencies
try:
    import umap
    import matplotlib.pyplot as plt
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans, DBSCAN
    from collections import Counter
except ImportError as e:
    console.print(f"[red]Missing dependency: {e}[/red]")
    console.print("Install with: pip install umap-learn matplotlib scikit-learn")
    sys.exit(1)


def load_embeddings(embeddings_dir: Path, index_type: str = "ideas"):
    """Load embeddings and metadata from disk.
    
    Args:
        embeddings_dir: Path to embeddings directory.
        index_type: Type of index (ideas, claims, references).
        
    Returns:
        Tuple of (embeddings array, metadata list).
    """
    npz_path = embeddings_dir / f"{index_type}_index.npz"
    meta_path = embeddings_dir / f"{index_type}_metadata.json"
    
    if not npz_path.exists():
        raise FileNotFoundError(f"Embeddings not found: {npz_path}")
    
    # Load embeddings
    data = np.load(npz_path)
    embeddings = data["embeddings"]
    
    # Load metadata
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    return embeddings, metadata


def load_items_from_jsonl(jsonl_path: Path) -> list[dict]:
    """Load items from JSONL file."""
    items = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items


def reduce_dimensions(embeddings: np.ndarray, n_components: int = 2) -> np.ndarray:
    """Reduce embedding dimensions using UMAP.
    
    Args:
        embeddings: High-dimensional embeddings.
        n_components: Target dimensions (2 for visualization).
        
    Returns:
        Reduced embeddings.
    """
    console.print("[cyan]📉 Reducing dimensions with UMAP...[/cyan]")
    
    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=15,
        min_dist=0.1,
        metric="cosine",
        random_state=42,
    )
    
    reduced = reducer.fit_transform(embeddings)
    return reduced


def cluster_embeddings(
    embeddings: np.ndarray,
    n_clusters: int = 10,
    method: str = "kmeans",
) -> np.ndarray:
    """Cluster embeddings using KMeans or DBSCAN.
    
    Args:
        embeddings: Embeddings to cluster (can be high or low dimensional).
        n_clusters: Number of clusters for KMeans.
        method: Clustering method ("kmeans" or "dbscan").
        
    Returns:
        Cluster labels (-1 for noise in DBSCAN).
    """
    console.print(f"[cyan]🔮 Clustering with {method.upper()}...[/cyan]")
    
    if method == "dbscan":
        clusterer = DBSCAN(eps=0.5, min_samples=3, metric="euclidean")
        labels = clusterer.fit_predict(embeddings)
    else:
        # Use KMeans - more reliable
        clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = clusterer.fit_predict(embeddings)
    
    n_clusters_found = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    
    console.print(f"  [dim]Found {n_clusters_found} clusters, {n_noise} noise points[/dim]")
    
    return labels


def extract_cluster_topics(
    items: list[dict],
    labels: np.ndarray,
    text_field: str = "idea",
    top_n_words: int = 5,
) -> dict[int, dict]:
    """Extract main topics for each cluster using TF-IDF.
    
    Args:
        items: List of item dictionaries.
        labels: Cluster labels for each item.
        text_field: Field containing the text to analyze.
        top_n_words: Number of top words per cluster.
        
    Returns:
        Dictionary mapping cluster_id to topic info.
    """
    console.print("[cyan]🏷️  Extracting cluster topics...[/cyan]")
    
    cluster_ids = sorted(set(labels))
    cluster_topics = {}
    
    for cluster_id in cluster_ids:
        if cluster_id == -1:
            continue  # Skip noise
        
        # Get items in this cluster
        cluster_indices = np.where(labels == cluster_id)[0]
        cluster_texts = [items[i].get(text_field, "") for i in cluster_indices]
        
        # Get paper titles in cluster
        paper_titles = [items[i].get("paper_title", "Unknown") for i in cluster_indices]
        paper_counts = Counter(paper_titles)
        
        # TF-IDF for topic extraction
        if len(cluster_texts) > 1:
            try:
                vectorizer = TfidfVectorizer(
                    max_features=100,
                    stop_words="english",
                    ngram_range=(1, 2),
                )
                tfidf_matrix = vectorizer.fit_transform(cluster_texts)
                
                # Get top words by mean TF-IDF score
                mean_tfidf = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
                top_indices = mean_tfidf.argsort()[-top_n_words:][::-1]
                feature_names = vectorizer.get_feature_names_out()
                top_words = [feature_names[i] for i in top_indices]
            except Exception:
                top_words = ["(unable to extract)"]
        else:
            # Single item cluster
            words = cluster_texts[0].split()[:top_n_words]
            top_words = words
        
        # Representative item (closest to cluster centroid would be better, but this is simpler)
        representative = cluster_texts[0][:200] + "..." if len(cluster_texts[0]) > 200 else cluster_texts[0]
        
        cluster_topics[cluster_id] = {
            "size": len(cluster_indices),
            "top_words": top_words,
            "representative": representative,
            "top_papers": paper_counts.most_common(3),
        }
    
    return cluster_topics


def visualize_clusters(
    reduced_embeddings: np.ndarray,
    labels: np.ndarray,
    cluster_topics: dict[int, dict],
    title: str = "Embedding Space",
    output_path: Path | None = None,
):
    """Create visualization of clustered embeddings.
    
    Args:
        reduced_embeddings: 2D embeddings from UMAP.
        labels: Cluster labels.
        cluster_topics: Topic info per cluster.
        title: Plot title.
        output_path: Path to save the figure.
    """
    console.print("[cyan]📊 Creating visualization...[/cyan]")
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Color palette
    unique_labels = sorted(set(labels))
    n_clusters = len([l for l in unique_labels if l != -1])
    colors = plt.cm.tab20(np.linspace(0, 1, max(n_clusters, 1)))
    
    # Plot noise points first (gray)
    noise_mask = labels == -1
    if noise_mask.any():
        ax.scatter(
            reduced_embeddings[noise_mask, 0],
            reduced_embeddings[noise_mask, 1],
            c="lightgray",
            s=10,
            alpha=0.5,
            label="Noise",
        )
    
    # Plot each cluster
    color_idx = 0
    for cluster_id in unique_labels:
        if cluster_id == -1:
            continue
        
        mask = labels == cluster_id
        topic_info = cluster_topics.get(cluster_id, {})
        topic_label = ", ".join(topic_info.get("top_words", [])[:3])
        size = topic_info.get("size", 0)
        
        ax.scatter(
            reduced_embeddings[mask, 0],
            reduced_embeddings[mask, 1],
            c=[colors[color_idx % len(colors)]],
            s=30,
            alpha=0.7,
            label=f"C{cluster_id}: {topic_label} ({size})",
        )
        
        # Add cluster center annotation
        center_x = reduced_embeddings[mask, 0].mean()
        center_y = reduced_embeddings[mask, 1].mean()
        ax.annotate(
            f"C{cluster_id}",
            (center_x, center_y),
            fontsize=9,
            fontweight="bold",
            ha="center",
        )
        
        color_idx += 1
    
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("UMAP Dimension 1")
    ax.set_ylabel("UMAP Dimension 2")
    
    # Legend outside plot
    ax.legend(
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=8,
        framealpha=0.9,
    )
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        console.print(f"  [green]✓ Saved to {output_path}[/green]")
    
    plt.show()


def print_cluster_summary(cluster_topics: dict[int, dict], index_type: str):
    """Print a summary table of clusters."""
    
    table = Table(title=f"Cluster Topics - {index_type.upper()}")
    table.add_column("Cluster", style="cyan", justify="center")
    table.add_column("Size", justify="right")
    table.add_column("Top Keywords", style="green")
    table.add_column("Top Papers", style="dim")
    
    for cluster_id in sorted(cluster_topics.keys()):
        info = cluster_topics[cluster_id]
        keywords = ", ".join(info["top_words"][:5])
        papers = ", ".join([p[0][:30] + "..." for p, _ in info["top_papers"][:2]])
        
        table.add_row(
            str(cluster_id),
            str(info["size"]),
            keywords,
            papers,
        )
    
    console.print(table)
    
    # Print representative examples
    console.print("\n[bold]Representative Examples:[/bold]")
    for cluster_id in sorted(cluster_topics.keys())[:5]:  # Top 5 clusters
        info = cluster_topics[cluster_id]
        console.print(Panel(
            info["representative"],
            title=f"Cluster {cluster_id} ({info['size']} items)",
            border_style="dim",
        ))


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Visualize embedding spaces")
    parser.add_argument(
        "--type",
        choices=["ideas", "claims", "references"],
        default="ideas",
        help="Type of embeddings to visualize",
    )
    parser.add_argument(
        "--n-clusters",
        type=int,
        default=10,
        help="Number of clusters for KMeans",
    )
    parser.add_argument(
        "--method",
        choices=["kmeans", "dbscan"],
        default="kmeans",
        help="Clustering method",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild embeddings before visualization",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output path for the visualization image",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip interactive plot, only print summary",
    )
    
    args = parser.parse_args()
    
    # Paths
    base_path = Path(__file__).parent.parent.parent.parent
    embeddings_dir = base_path / "data" / "processed" / "embeddings"
    indices_dir = base_path / "data" / "processed" / "indices"
    
    console.print(Panel(
        f"[bold]Embedding Space Visualization[/bold]\n"
        f"Type: {args.type}\n"
        f"Clusters: {args.n_clusters} ({args.method})",
        title="🔬 TheAIWriter",
    ))
    
    # Check if we need to use JSONL directly (when embeddings are outdated)
    jsonl_path = indices_dir / f"all_{args.type}.jsonl"
    npz_path = embeddings_dir / f"{args.type}_index.npz"
    
    if not npz_path.exists() or args.rebuild:
        console.print("[yellow]⚠ Embeddings not found or rebuild requested[/yellow]")
        console.print("[yellow]  Run: python -m ai_writer.scripts.build_embeddings[/yellow]")
        return
    
    # Load embeddings
    embeddings, _ = load_embeddings(embeddings_dir, args.type)
    console.print(f"[green]✓ Loaded {len(embeddings)} embeddings[/green]")
    
    # Load items for text analysis
    items = load_items_from_jsonl(jsonl_path)
    
    # Check if counts match
    if len(embeddings) != len(items):
        console.print(f"[yellow]⚠ Mismatch: {len(embeddings)} embeddings vs {len(items)} items[/yellow]")
        console.print("[yellow]  Embeddings may be outdated. Rebuild with --rebuild[/yellow]")
        # Use minimum
        min_count = min(len(embeddings), len(items))
        embeddings = embeddings[:min_count]
        items = items[:min_count]
    
    # Determine text field
    text_field = {
        "ideas": "idea",
        "claims": "claim", 
        "references": "full_citation",
    }.get(args.type, "idea")
    
    # Reduce dimensions
    reduced = reduce_dimensions(embeddings)
    
    # Cluster
    labels = cluster_embeddings(reduced, n_clusters=args.n_clusters, method=args.method)
    
    # Extract topics
    cluster_topics = extract_cluster_topics(items, labels, text_field=text_field)
    
    # Print summary
    print_cluster_summary(cluster_topics, args.type)
    
    # Visualize
    if not args.no_plot:
        output_path = Path(args.output) if args.output else None
        visualize_clusters(
            reduced,
            labels,
            cluster_topics,
            title=f"{args.type.capitalize()} Embedding Space",
            output_path=output_path,
        )


if __name__ == "__main__":
    main()
