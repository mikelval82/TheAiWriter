"""Analyzer for RAG exploration vs exploitation in the embedding space.

This module provides metrics to quantify how well the RAG system
explores the full embedding space vs exploiting a narrow subset.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from difflib import SequenceMatcher

console = Console()


@dataclass
class DiversityMetrics:
    """Metrics for embedding space exploration."""
    
    # Basic counts
    total_ideas_retrieved: int = 0
    unique_ideas: int = 0
    duplicate_ideas: int = 0
    
    # Coverage metrics
    clusters_available: int = 0
    clusters_used: int = 0
    cluster_coverage: float = 0.0  # % of available clusters used
    
    # Similarity metrics
    avg_inter_section_similarity: float = 0.0  # Similarity between sections
    avg_intra_section_similarity: float = 0.0  # Similarity within sections
    
    # Distribution metrics
    cluster_entropy: float = 0.0  # Higher = more uniform distribution
    cluster_gini: float = 0.0  # Lower = more equal distribution
    
    # Overlap metrics
    section_overlap_matrix: dict = field(default_factory=dict)
    ideas_per_cluster: dict = field(default_factory=dict)
    
    # Exploration score (0-100)
    exploration_score: float = 0.0


class EmbeddingDiversityAnalyzer:
    """Analyze diversity and exploration of the embedding space."""
    
    def __init__(self, log_dir: Path | str):
        """Initialize analyzer with a run log directory.
        
        Args:
            log_dir: Path to the run log directory containing JSON files.
        """
        self.log_dir = Path(log_dir)
        self.section_ideas: dict = {}
        self.topics: list = []
        self.metrics = DiversityMetrics()
        
    def load_logs(self) -> bool:
        """Load log files from the directory.
        
        Returns:
            True if logs loaded successfully.
        """
        # Load topics
        topics_file = self.log_dir / "phase1_topics.json"
        if topics_file.exists():
            with open(topics_file, encoding="utf-8") as f:
                data = json.load(f)
                self.topics = data.get("topics", [])
                console.print(f"[dim]Loaded {len(self.topics)} topics[/dim]")
        
        # Load section ideas
        ideas_file = self.log_dir / "phase2_section_ideas.json"
        if ideas_file.exists():
            with open(ideas_file, encoding="utf-8") as f:
                data = json.load(f)
                self.section_ideas = data.get("sections", {})
                console.print(f"[dim]Loaded ideas for {len(self.section_ideas)} sections[/dim]")
        
        return bool(self.topics and self.section_ideas)
    
    def analyze(self) -> DiversityMetrics:
        """Run full diversity analysis.
        
        Returns:
            DiversityMetrics with all computed metrics.
        """
        if not self.section_ideas:
            if not self.load_logs():
                console.print("[red]Failed to load logs[/red]")
                return self.metrics
        
        # Compute all metrics
        self._compute_basic_counts()
        self._compute_cluster_coverage()
        self._compute_similarity_metrics()
        self._compute_distribution_metrics()
        self._compute_overlap_matrix()
        self._compute_exploration_score()
        
        return self.metrics
    
    def _compute_basic_counts(self) -> None:
        """Compute basic idea counts."""
        all_ideas = []
        for section_data in self.section_ideas.values():
            ideas = section_data.get("ideas", [])
            all_ideas.extend([idea["text"] for idea in ideas])
        
        self.metrics.total_ideas_retrieved = len(all_ideas)
        
        # Find duplicates using fuzzy matching
        unique_texts = set()
        duplicates = 0
        for idea in all_ideas:
            is_duplicate = False
            for existing in unique_texts:
                similarity = SequenceMatcher(None, idea, existing).ratio()
                if similarity > 0.85:  # 85% similar = duplicate
                    is_duplicate = True
                    duplicates += 1
                    break
            if not is_duplicate:
                unique_texts.add(idea)
        
        self.metrics.unique_ideas = len(unique_texts)
        self.metrics.duplicate_ideas = duplicates
    
    def _compute_cluster_coverage(self) -> None:
        """Compute cluster coverage metrics."""
        self.metrics.clusters_available = len(self.topics)
        
        # Collect all clusters used across sections
        all_clusters_used = set()
        for section_data in self.section_ideas.values():
            topics_used = section_data.get("topics_used", [])
            all_clusters_used.update(topics_used)
        
        self.metrics.clusters_used = len(all_clusters_used)
        
        if self.metrics.clusters_available > 0:
            self.metrics.cluster_coverage = (
                self.metrics.clusters_used / self.metrics.clusters_available * 100
            )
    
    def _compute_similarity_metrics(self) -> None:
        """Compute intra and inter section similarity."""
        section_names = list(self.section_ideas.keys())
        
        # Build list of ideas per section
        section_idea_texts = {}
        for section_name, section_data in self.section_ideas.items():
            section_idea_texts[section_name] = [
                idea["text"] for idea in section_data.get("ideas", [])
            ]
        
        # Intra-section similarity (average similarity within each section)
        intra_similarities = []
        for section_name, ideas in section_idea_texts.items():
            if len(ideas) < 2:
                continue
            section_sims = []
            for i in range(len(ideas)):
                for j in range(i + 1, len(ideas)):
                    sim = SequenceMatcher(None, ideas[i], ideas[j]).ratio()
                    section_sims.append(sim)
            if section_sims:
                intra_similarities.append(np.mean(section_sims))
        
        if intra_similarities:
            self.metrics.avg_intra_section_similarity = np.mean(intra_similarities)
        
        # Inter-section similarity (similarity between different sections)
        inter_similarities = []
        for i, sec1 in enumerate(section_names):
            for j, sec2 in enumerate(section_names):
                if i >= j:
                    continue
                ideas1 = section_idea_texts[sec1]
                ideas2 = section_idea_texts[sec2]
                
                # Average pairwise similarity between sections
                pairwise_sims = []
                for idea1 in ideas1:
                    for idea2 in ideas2:
                        sim = SequenceMatcher(None, idea1, idea2).ratio()
                        pairwise_sims.append(sim)
                
                if pairwise_sims:
                    inter_similarities.append(np.mean(pairwise_sims))
        
        if inter_similarities:
            self.metrics.avg_inter_section_similarity = np.mean(inter_similarities)
    
    def _compute_distribution_metrics(self) -> None:
        """Compute entropy and Gini coefficient for cluster distribution."""
        # Count ideas per cluster
        cluster_counts = Counter()
        for section_data in self.section_ideas.values():
            topics_used = section_data.get("topics_used", [])
            for topic in topics_used:
                cluster_counts[topic] += 1
        
        self.metrics.ideas_per_cluster = dict(cluster_counts)
        
        if not cluster_counts:
            return
        
        counts = np.array(list(cluster_counts.values()), dtype=float)
        total = counts.sum()
        
        if total == 0:
            return
        
        # Normalize to probabilities
        probs = counts / total
        
        # Entropy (higher = more uniform distribution)
        # Max entropy = log2(n_clusters) for uniform distribution
        entropy = -np.sum(probs * np.log2(probs + 1e-10))
        max_entropy = np.log2(len(counts))
        self.metrics.cluster_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        # Gini coefficient (lower = more equal distribution)
        # 0 = perfect equality, 1 = perfect inequality
        sorted_counts = np.sort(counts)
        n = len(sorted_counts)
        cumulative = np.cumsum(sorted_counts)
        gini = (n + 1 - 2 * np.sum(cumulative) / cumulative[-1]) / n
        self.metrics.cluster_gini = max(0, gini)
    
    def _compute_overlap_matrix(self) -> None:
        """Compute overlap between sections (Jaccard similarity)."""
        section_names = list(self.section_ideas.keys())
        
        # Get idea sets per section
        section_idea_sets = {}
        for section_name, section_data in self.section_ideas.items():
            # Use first 50 chars as fingerprint for matching
            ideas = section_data.get("ideas", [])
            section_idea_sets[section_name] = set(
                idea["text"][:50] for idea in ideas
            )
        
        # Compute Jaccard overlap matrix
        overlap = {}
        for sec1 in section_names:
            overlap[sec1] = {}
            for sec2 in section_names:
                if sec1 == sec2:
                    overlap[sec1][sec2] = 1.0
                else:
                    set1 = section_idea_sets[sec1]
                    set2 = section_idea_sets[sec2]
                    if set1 or set2:
                        jaccard = len(set1 & set2) / len(set1 | set2)
                    else:
                        jaccard = 0.0
                    overlap[sec1][sec2] = jaccard
        
        self.metrics.section_overlap_matrix = overlap
    
    def _compute_exploration_score(self) -> None:
        """Compute overall exploration score (0-100).
        
        Higher score = better exploration of the embedding space.
        """
        scores = []
        
        # 1. Cluster coverage (weight: 25%)
        coverage_score = self.metrics.cluster_coverage
        scores.append(coverage_score * 0.25)
        
        # 2. Uniqueness ratio (weight: 25%)
        if self.metrics.total_ideas_retrieved > 0:
            uniqueness = self.metrics.unique_ideas / self.metrics.total_ideas_retrieved * 100
        else:
            uniqueness = 0
        scores.append(uniqueness * 0.25)
        
        # 3. Distribution uniformity via entropy (weight: 25%)
        entropy_score = self.metrics.cluster_entropy * 100
        scores.append(entropy_score * 0.25)
        
        # 4. Low inter-section overlap (weight: 25%)
        # Lower overlap = better exploration
        overlap_penalty = self.metrics.avg_inter_section_similarity * 100
        overlap_score = max(0, 100 - overlap_penalty * 2)  # Penalize high overlap
        scores.append(overlap_score * 0.25)
        
        self.metrics.exploration_score = sum(scores)
    
    def print_report(self) -> None:
        """Print a formatted analysis report."""
        m = self.metrics
        
        # Header
        console.print(Panel(
            f"[bold]Análisis de Exploración del Espacio de Embeddings[/bold]\n\n"
            f"📁 Run: {self.log_dir.name}",
            title="📊 RAG Diversity Analytics",
            border_style="cyan",
        ))
        
        # Basic counts table
        table = Table(title="📈 Conteo de Ideas", show_header=True)
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right")
        table.add_row("Total ideas recuperadas", str(m.total_ideas_retrieved))
        table.add_row("Ideas únicas", str(m.unique_ideas))
        table.add_row("Ideas duplicadas/similares", f"[red]{m.duplicate_ideas}[/red]" if m.duplicate_ideas > 5 else str(m.duplicate_ideas))
        table.add_row("Ratio de unicidad", f"{m.unique_ideas/m.total_ideas_retrieved*100:.1f}%" if m.total_ideas_retrieved > 0 else "N/A")
        console.print(table)
        
        # Cluster coverage table
        table = Table(title="🎯 Cobertura de Clusters", show_header=True)
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right")
        table.add_row("Clusters disponibles", str(m.clusters_available))
        table.add_row("Clusters utilizados", str(m.clusters_used))
        color = "green" if m.cluster_coverage > 80 else "yellow" if m.cluster_coverage > 50 else "red"
        table.add_row("Cobertura", f"[{color}]{m.cluster_coverage:.1f}%[/{color}]")
        console.print(table)
        
        # Distribution metrics
        table = Table(title="📊 Distribución de Uso", show_header=True)
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right")
        table.add_column("Interpretación")
        
        entropy_color = "green" if m.cluster_entropy > 0.8 else "yellow" if m.cluster_entropy > 0.5 else "red"
        table.add_row(
            "Entropía normalizada",
            f"[{entropy_color}]{m.cluster_entropy:.3f}[/{entropy_color}]",
            "1.0 = uniforme, 0 = concentrado"
        )
        
        gini_color = "green" if m.cluster_gini < 0.3 else "yellow" if m.cluster_gini < 0.5 else "red"
        table.add_row(
            "Coeficiente Gini",
            f"[{gini_color}]{m.cluster_gini:.3f}[/{gini_color}]",
            "0 = igual, 1 = desigual"
        )
        console.print(table)
        
        # Similarity metrics
        table = Table(title="🔍 Análisis de Similaridad", show_header=True)
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right")
        table.add_column("Interpretación")
        
        intra_color = "green" if m.avg_intra_section_similarity < 0.3 else "yellow" if m.avg_intra_section_similarity < 0.5 else "red"
        table.add_row(
            "Similaridad intra-sección",
            f"[{intra_color}]{m.avg_intra_section_similarity:.3f}[/{intra_color}]",
            "Menor = ideas más diversas en cada sección"
        )
        
        inter_color = "green" if m.avg_inter_section_similarity < 0.2 else "yellow" if m.avg_inter_section_similarity < 0.4 else "red"
        table.add_row(
            "Similaridad inter-sección",
            f"[{inter_color}]{m.avg_inter_section_similarity:.3f}[/{inter_color}]",
            "Menor = secciones más diferenciadas"
        )
        console.print(table)
        
        # Cluster usage distribution
        if m.ideas_per_cluster:
            table = Table(title="📦 Ideas por Cluster", show_header=True)
            table.add_column("Cluster", style="cyan")
            table.add_column("Uso", justify="right")
            table.add_column("Barra")
            
            max_count = max(m.ideas_per_cluster.values())
            for cluster, count in sorted(m.ideas_per_cluster.items(), key=lambda x: -x[1]):
                bar_len = int(count / max_count * 20)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                table.add_row(cluster[:25], str(count), bar)
            console.print(table)
        
        # Exploration Score
        score = m.exploration_score
        if score >= 75:
            score_color = "green"
            interpretation = "Excelente exploración del espacio"
        elif score >= 50:
            score_color = "yellow"
            interpretation = "Exploración moderada, hay margen de mejora"
        else:
            score_color = "red"
            interpretation = "Explotación excesiva, poca diversidad"
        
        console.print(Panel(
            f"[bold {score_color}]{score:.1f} / 100[/bold {score_color}]\n\n"
            f"{interpretation}",
            title="🎯 Exploration Score",
            border_style=score_color,
        ))
        
        # Recommendations
        self._print_recommendations()
    
    def _print_recommendations(self) -> None:
        """Print recommendations based on metrics."""
        m = self.metrics
        recommendations = []
        
        if m.duplicate_ideas > 5:
            recommendations.append(
                "🔄 **Alta duplicación**: Implementar un filtro de deduplicación "
                "más agresivo usando embeddings en lugar de texto."
            )
        
        if m.cluster_coverage < 70:
            recommendations.append(
                f"📍 **Baja cobertura**: Solo se usan {m.clusters_used}/{m.clusters_available} clusters. "
                "Considerar forzar representación de clusters menos usados."
            )
        
        if m.cluster_entropy < 0.7:
            recommendations.append(
                "⚖️ **Distribución desigual**: Algunos clusters dominan. "
                "Implementar un balanceo de muestreo entre clusters."
            )
        
        if m.avg_inter_section_similarity > 0.3:
            recommendations.append(
                "🔁 **Alta similaridad entre secciones**: Las ideas se repiten. "
                "Implementar exclusión de ideas ya usadas en secciones previas."
            )
        
        if m.avg_intra_section_similarity > 0.4:
            recommendations.append(
                "📝 **Ideas similares en misma sección**: Falta diversidad interna. "
                "Aplicar MMR (Maximal Marginal Relevance) para selección."
            )
        
        if recommendations:
            console.print(Panel(
                "\n".join(recommendations),
                title="💡 Recomendaciones",
                border_style="yellow",
            ))
        else:
            console.print("[green]✓ No hay recomendaciones críticas[/green]")
    
    def export_report(self, output_path: Path | str | None = None) -> Path:
        """Export metrics to JSON file.
        
        Args:
            output_path: Optional output path. Defaults to log_dir/diversity_analysis.json
            
        Returns:
            Path to exported file.
        """
        if output_path is None:
            output_path = self.log_dir / "diversity_analysis.json"
        else:
            output_path = Path(output_path)
        
        m = self.metrics
        report = {
            "run_name": self.log_dir.name,
            "basic_counts": {
                "total_ideas_retrieved": m.total_ideas_retrieved,
                "unique_ideas": m.unique_ideas,
                "duplicate_ideas": m.duplicate_ideas,
                "uniqueness_ratio": m.unique_ideas / m.total_ideas_retrieved if m.total_ideas_retrieved > 0 else 0,
            },
            "cluster_coverage": {
                "clusters_available": m.clusters_available,
                "clusters_used": m.clusters_used,
                "coverage_percent": m.cluster_coverage,
            },
            "distribution": {
                "cluster_entropy": m.cluster_entropy,
                "cluster_gini": m.cluster_gini,
                "ideas_per_cluster": m.ideas_per_cluster,
            },
            "similarity": {
                "avg_intra_section_similarity": m.avg_intra_section_similarity,
                "avg_inter_section_similarity": m.avg_inter_section_similarity,
            },
            "section_overlap_matrix": m.section_overlap_matrix,
            "exploration_score": m.exploration_score,
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        console.print(f"[dim]📊 Report exported to: {output_path}[/dim]")
        return output_path


def main():
    """CLI entry point for diversity analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze RAG exploration vs exploitation in embedding space"
    )
    parser.add_argument(
        "log_dir",
        type=str,
        help="Path to run log directory (e.g., data/logs/run_MyPaper)",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export report to JSON file",
    )
    
    args = parser.parse_args()
    
    analyzer = EmbeddingDiversityAnalyzer(args.log_dir)
    analyzer.analyze()
    analyzer.print_report()
    
    if args.export:
        analyzer.export_report()


if __name__ == "__main__":
    main()
