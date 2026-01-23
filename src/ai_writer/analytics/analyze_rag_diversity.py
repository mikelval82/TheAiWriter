#!/usr/bin/env python3
"""Script to analyze RAG exploration vs exploitation.

This script can:
1. Analyze existing logs from a run
2. Simulate Phase 3 retrievals using an existing outline to predict diversity
3. Generate recommendations for improving RAG exploration

Usage:
    python -m src.ai_writer.analytics.analyze_rag_diversity data/logs/run_MyPaper
    python -m src.ai_writer.analytics.analyze_rag_diversity data/logs/run_MyPaper --simulate
"""

import argparse
import json
from pathlib import Path
from collections import Counter

import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

console = Console()


def load_embeddings():
    """Load the ideas and claims embedding indices."""
    from config.settings import settings
    from ai_writer.embeddings.embedding_index import EmbeddingIndex
    
    ideas_index = EmbeddingIndex(
        name="ideas",
        cache_dir=settings.paths.embeddings_dir,
        text_field="idea",
    )
    # Load from cache
    ideas_index._load_from_cache()
    
    claims_index = EmbeddingIndex(
        name="claims",
        cache_dir=settings.paths.embeddings_dir,
        text_field="claim",
    )
    claims_index._load_from_cache()
    
    return ideas_index, claims_index


def simulate_paragraph_retrievals(outline_path: Path, top_k: int = 10):
    """Simulate what the RAG would retrieve for each paragraph.
    
    Args:
        outline_path: Path to outline JSON.
        top_k: Number of results to retrieve per paragraph.
        
    Returns:
        Dict with simulation results.
    """
    # Load outline
    with open(outline_path, encoding="utf-8") as f:
        outline = json.load(f)
    
    # Load indices
    ideas_index, claims_index = load_embeddings()
    
    console.print(f"[cyan]🔬 Simulating retrievals for {outline_path.name}[/cyan]")
    console.print(f"[dim]Ideas index: {len(ideas_index.items)} items[/dim]")
    console.print(f"[dim]Claims index: {len(claims_index.items)} items[/dim]")
    
    # Track all retrievals
    all_idea_indices = []
    all_claim_indices = []
    paragraph_retrievals = []
    
    sections = outline.get("sections", [])
    
    for section in track(sections, description="Simulating retrievals..."):
        section_name = section.get("section_name", "Unknown")
        paragraphs = section.get("paragraphs", [])
        
        for para in paragraphs:
            para_num = para.get("paragraph_number", 0)
            key_idea = para.get("key_idea", "")
            supporting_points = para.get("supporting_points", [])
            
            # Build query like the real system does
            query_parts = [key_idea]
            if supporting_points:
                query_parts.extend(supporting_points[:2])
            query = " ".join(query_parts)
            
            # Search ideas (search method handles embedding internally)
            idea_results = ideas_index.search(
                query=query,
                top_k=top_k,
            )
            
            # Search claims
            claim_results = claims_index.search(
                query=query,
                top_k=top_k,
            )
            
            # Use text fingerprint as unique ID
            idea_fingerprints = [hash(item.get("idea", "")[:50]) for item, score in idea_results]
            claim_fingerprints = [hash(item.get("claim", "")[:50]) for item, score in claim_results]
            
            all_idea_indices.extend(idea_fingerprints)
            all_claim_indices.extend(claim_fingerprints)
            
            paragraph_retrievals.append({
                "section": section_name,
                "paragraph": para_num,
                "query": query[:100],
                "idea_fingerprints": idea_fingerprints,
                "claim_fingerprints": claim_fingerprints,
                "idea_similarities": [score for item, score in idea_results],
                "claim_similarities": [score for item, score in claim_results],
            })
    
    return {
        "n_paragraphs": len(paragraph_retrievals),
        "all_idea_indices": all_idea_indices,
        "all_claim_indices": all_claim_indices,
        "paragraph_retrievals": paragraph_retrievals,
        "ideas_total": len(ideas_index.items),
        "claims_total": len(claims_index.items),
    }


def analyze_retrieval_diversity(sim_results: dict) -> dict:
    """Analyze diversity of simulated retrievals.
    
    Args:
        sim_results: Results from simulate_paragraph_retrievals.
        
    Returns:
        Dict with diversity metrics.
    """
    idea_indices = sim_results["all_idea_indices"]
    claim_indices = sim_results["all_claim_indices"]
    ideas_total = sim_results["ideas_total"]
    claims_total = sim_results["claims_total"]
    
    # Unique items
    unique_ideas = len(set(idea_indices))
    unique_claims = len(set(claim_indices))
    
    # Coverage
    idea_coverage = unique_ideas / ideas_total * 100 if ideas_total > 0 else 0
    claim_coverage = unique_claims / claims_total * 100 if claims_total > 0 else 0
    
    # Reuse ratio
    idea_reuse = len(idea_indices) / unique_ideas if unique_ideas > 0 else 0
    claim_reuse = len(claim_indices) / unique_claims if unique_claims > 0 else 0
    
    # Most retrieved items (hot spots)
    idea_counts = Counter(idea_indices)
    claim_counts = Counter(claim_indices)
    
    top_ideas = idea_counts.most_common(10)
    top_claims = claim_counts.most_common(10)
    
    # Gini coefficient for idea distribution
    idea_values = np.array(list(idea_counts.values()), dtype=float)
    if len(idea_values) > 0:
        sorted_values = np.sort(idea_values)
        n = len(sorted_values)
        cumulative = np.cumsum(sorted_values)
        idea_gini = (n + 1 - 2 * np.sum(cumulative) / cumulative[-1]) / n
    else:
        idea_gini = 0
    
    # Inter-paragraph overlap (how many items appear in multiple paragraphs)
    n_paragraphs = sim_results["n_paragraphs"]
    ideas_in_multiple = sum(1 for c in idea_counts.values() if c > 1)
    claims_in_multiple = sum(1 for c in claim_counts.values() if c > 1)
    
    return {
        "total_retrievals": len(idea_indices) + len(claim_indices),
        "unique_ideas": unique_ideas,
        "unique_claims": unique_claims,
        "idea_coverage_percent": idea_coverage,
        "claim_coverage_percent": claim_coverage,
        "idea_reuse_ratio": idea_reuse,
        "claim_reuse_ratio": claim_reuse,
        "idea_gini": max(0, idea_gini),
        "ideas_retrieved_multiple_times": ideas_in_multiple,
        "claims_retrieved_multiple_times": claims_in_multiple,
        "ideas_retrieved_multiple_percent": ideas_in_multiple / unique_ideas * 100 if unique_ideas > 0 else 0,
        "top_10_ideas": top_ideas,
        "top_10_claims": top_claims,
    }


def print_simulation_report(sim_results: dict, diversity: dict):
    """Print formatted simulation report."""
    
    console.print(Panel(
        "[bold]Simulación de Recuperación RAG[/bold]\n\n"
        f"Párrafos analizados: {sim_results['n_paragraphs']}\n"
        f"Ideas disponibles: {sim_results['ideas_total']:,}\n"
        f"Claims disponibles: {sim_results['claims_total']:,}",
        title="🔬 Phase 3 Simulation",
        border_style="cyan",
    ))
    
    # Coverage table
    table = Table(title="📊 Cobertura del Espacio de Embeddings", show_header=True)
    table.add_column("Métrica", style="cyan")
    table.add_column("Ideas", justify="right")
    table.add_column("Claims", justify="right")
    
    table.add_row(
        "Únicos recuperados",
        str(diversity["unique_ideas"]),
        str(diversity["unique_claims"]),
    )
    
    idea_cov = diversity["idea_coverage_percent"]
    claim_cov = diversity["claim_coverage_percent"]
    
    idea_color = "green" if idea_cov > 10 else "yellow" if idea_cov > 5 else "red"
    claim_color = "green" if claim_cov > 10 else "yellow" if claim_cov > 5 else "red"
    
    table.add_row(
        "Cobertura %",
        f"[{idea_color}]{idea_cov:.1f}%[/{idea_color}]",
        f"[{claim_color}]{claim_cov:.1f}%[/{claim_color}]",
    )
    
    idea_reuse = diversity["idea_reuse_ratio"]
    claim_reuse = diversity["claim_reuse_ratio"]
    
    reuse_color = lambda r: "green" if r < 1.5 else "yellow" if r < 2.5 else "red"
    
    table.add_row(
        "Ratio de reutilización",
        f"[{reuse_color(idea_reuse)}]{idea_reuse:.2f}x[/{reuse_color(idea_reuse)}]",
        f"[{reuse_color(claim_reuse)}]{claim_reuse:.2f}x[/{reuse_color(claim_reuse)}]",
    )
    
    table.add_row(
        "Recuperados >1 vez",
        f"[red]{diversity['ideas_retrieved_multiple_times']}[/red] ({diversity['ideas_retrieved_multiple_percent']:.0f}%)",
        f"[red]{diversity['claims_retrieved_multiple_times']}[/red]",
    )
    
    console.print(table)
    
    # Hot spots
    if diversity["top_10_ideas"]:
        table = Table(title="🔥 Ideas más recuperadas (Hot Spots)", show_header=True)
        table.add_column("Índice", style="cyan")
        table.add_column("Veces", justify="right")
        table.add_column("% Total", justify="right")
        
        total_retrievals = len(sim_results["all_idea_indices"])
        
        for idx, count in diversity["top_10_ideas"][:5]:
            pct = count / total_retrievals * 100 if total_retrievals > 0 else 0
            color = "red" if count > 3 else "yellow" if count > 2 else "white"
            table.add_row(str(idx), f"[{color}]{count}[/{color}]", f"{pct:.1f}%")
        
        console.print(table)
    
    # Exploration score
    score = calculate_exploration_score(diversity)
    
    if score >= 70:
        score_color = "green"
        interpretation = "Buena exploración"
    elif score >= 40:
        score_color = "yellow"
        interpretation = "Exploración moderada - hay margen de mejora"
    else:
        score_color = "red"
        interpretation = "⚠️ Explotación excesiva - el RAG está estancado en pocas ideas"
    
    console.print(Panel(
        f"[bold {score_color}]{score:.0f} / 100[/bold {score_color}]\n\n"
        f"{interpretation}",
        title="🎯 Exploration Score (Phase 3)",
        border_style=score_color,
    ))
    
    # Recommendations
    print_recommendations(diversity)


def calculate_exploration_score(diversity: dict) -> float:
    """Calculate exploration score from diversity metrics."""
    scores = []
    
    # Coverage (weight: 30%)
    coverage = (diversity["idea_coverage_percent"] + diversity["claim_coverage_percent"]) / 2
    coverage_score = min(100, coverage * 10)  # Scale up since coverage is typically low
    scores.append(coverage_score * 0.30)
    
    # Low reuse (weight: 30%)
    avg_reuse = (diversity["idea_reuse_ratio"] + diversity["claim_reuse_ratio"]) / 2
    reuse_score = max(0, 100 - (avg_reuse - 1) * 50)  # Penalize reuse > 1
    scores.append(reuse_score * 0.30)
    
    # Low Gini (weight: 20%)
    gini_score = (1 - diversity["idea_gini"]) * 100
    scores.append(gini_score * 0.20)
    
    # Low overlap (weight: 20%)
    overlap_pct = diversity["ideas_retrieved_multiple_percent"]
    overlap_score = max(0, 100 - overlap_pct * 2)
    scores.append(overlap_score * 0.20)
    
    return sum(scores)


def print_recommendations(diversity: dict):
    """Print recommendations based on metrics."""
    recommendations = []
    
    if diversity["idea_reuse_ratio"] > 2.0:
        recommendations.append(
            "🔄 **Alta reutilización de ideas**: Cada idea se usa ~{:.1f} veces. "
            "Implementar exclusión de ítems ya recuperados.".format(diversity["idea_reuse_ratio"])
        )
    
    if diversity["idea_coverage_percent"] < 5:
        recommendations.append(
            "📍 **Baja cobertura**: Solo se explora {:.1f}% del espacio de ideas. "
            "Considerar aumentar diversidad con MMR o sampling aleatorio.".format(
                diversity["idea_coverage_percent"]
            )
        )
    
    if diversity["ideas_retrieved_multiple_percent"] > 30:
        recommendations.append(
            "🔁 **{:.0f}% de ideas repetidas**: Implementar un mecanismo de "
            "\"used_items\" para excluir ítems ya usados en párrafos previos.".format(
                diversity["ideas_retrieved_multiple_percent"]
            )
        )
    
    if diversity["idea_gini"] > 0.5:
        recommendations.append(
            "⚖️ **Distribución desigual** (Gini={:.2f}): Pocas ideas dominan. "
            "Implementar balanceo o penalización por popularidad.".format(diversity["idea_gini"])
        )
    
    if recommendations:
        console.print(Panel(
            "\n\n".join(recommendations),
            title="💡 Recomendaciones para mejorar exploración",
            border_style="yellow",
        ))
    else:
        console.print("[green]✓ Métricas de exploración aceptables[/green]")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze RAG exploration vs exploitation"
    )
    parser.add_argument(
        "log_dir",
        type=str,
        help="Path to run log directory",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Simulate Phase 3 retrievals using outline",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of results per retrieval (default: 10)",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export results to JSON",
    )
    
    args = parser.parse_args()
    log_dir = Path(args.log_dir)
    
    if not log_dir.exists():
        console.print(f"[red]Error: {log_dir} no existe[/red]")
        return
    
    # First run Phase 2 diversity analysis
    from ai_writer.analytics.embedding_diversity import EmbeddingDiversityAnalyzer
    
    console.print("[bold]═══ Análisis de Diversidad del Espacio de Embeddings ═══[/bold]\n")
    
    analyzer = EmbeddingDiversityAnalyzer(log_dir)
    analyzer.analyze()
    analyzer.print_report()
    
    # If --simulate, also run Phase 3 simulation
    if args.simulate:
        console.print("\n[bold]═══ Simulación de Fase 3 (Escritura) ═══[/bold]\n")
        
        outline_path = log_dir / "phase2_outline.json"
        if not outline_path.exists():
            console.print(f"[red]No se encontró outline en {outline_path}[/red]")
            return
        
        sim_results = simulate_paragraph_retrievals(outline_path, top_k=args.top_k)
        diversity = analyze_retrieval_diversity(sim_results)
        print_simulation_report(sim_results, diversity)
        
        if args.export:
            export_path = log_dir / "phase3_simulation.json"
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump({
                    "simulation": {
                        "n_paragraphs": sim_results["n_paragraphs"],
                        "ideas_total": sim_results["ideas_total"],
                        "claims_total": sim_results["claims_total"],
                    },
                    "diversity_metrics": diversity,
                    "paragraph_details": sim_results["paragraph_retrievals"],
                }, f, indent=2, ensure_ascii=False, default=str)
            console.print(f"[dim]📊 Exported to: {export_path}[/dim]")


if __name__ == "__main__":
    main()
