#!/usr/bin/env python3
"""Compare RAG exploration with and without the new improvements.

This script simulates Phase 3 retrievals using:
1. The OLD method (direct EmbeddingIndex search without exclusions)
2. The NEW method (EnhancedContextManager with exclusion, MMR, popularity penalty)

And compares the diversity metrics between both approaches.

Usage:
    python -m ai_writer.analytics.compare_exploration data/logs/run_MyPaper
"""

import argparse
import json
from pathlib import Path
from collections import Counter
from dataclasses import dataclass

import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich import box

console = Console()


@dataclass
class ExplorationMetrics:
    """Metrics for measuring exploration quality."""
    unique_ideas: int
    unique_claims: int
    total_idea_retrievals: int
    total_claim_retrievals: int
    ideas_retrieved_multiple: int
    claims_retrieved_multiple: int
    idea_coverage_pct: float
    claim_coverage_pct: float
    idea_reuse_ratio: float
    claim_reuse_ratio: float
    idea_gini: float
    exploration_score: float


def simulate_old_method(outline: dict, top_k: int = 10) -> ExplorationMetrics:
    """Simulate the OLD method: direct search without any exclusion or MMR.
    
    This mimics the original behavior where each paragraph search was independent
    and could retrieve the same items repeatedly.
    """
    from config.settings import settings
    from ai_writer.embeddings.embedding_index import EmbeddingIndex
    
    # Load indices directly (old method)
    ideas_index = EmbeddingIndex(
        name="ideas",
        cache_dir=settings.paths.embeddings_dir,
        text_field="idea",
    )
    ideas_index._load_from_cache()
    
    claims_index = EmbeddingIndex(
        name="claims",
        cache_dir=settings.paths.embeddings_dir,
        text_field="claim",
    )
    claims_index._load_from_cache()
    
    all_idea_fingerprints = []
    all_claim_fingerprints = []
    
    sections = outline.get("sections", [])
    
    for section in sections:
        paragraphs = section.get("paragraphs", [])
        
        for para in paragraphs:
            key_idea = para.get("key_idea", "")
            supporting_points = para.get("supporting_points", [])
            
            # Build query
            query_parts = [key_idea]
            if supporting_points:
                query_parts.extend(supporting_points[:2])
            query = " ".join(query_parts)
            
            # OLD: Direct search without exclusion
            idea_results = ideas_index.search(query=query, top_k=top_k)
            claim_results = claims_index.search(query=query, top_k=top_k)
            
            # Track fingerprints
            for item, score in idea_results:
                fp = f"idea:{item.get('paper_id', '')}:{hash(item.get('idea', '')[:100])}"
                all_idea_fingerprints.append(fp)
            
            for item, score in claim_results:
                fp = f"claim:{item.get('paper_id', '')}:{hash(item.get('claim', '')[:100])}"
                all_claim_fingerprints.append(fp)
    
    return _compute_metrics(
        all_idea_fingerprints,
        all_claim_fingerprints,
        len(ideas_index.items),
        len(claims_index.items),
    )


def simulate_new_method(outline: dict, top_k: int = 10) -> ExplorationMetrics:
    """Simulate the NEW method: EnhancedContextManager with all improvements.
    
    This uses:
    - Exclusion of already-used items
    - Popularity penalty
    - MMR diversification
    """
    from ai_writer.utils.enhanced_context_manager import EnhancedContextManager
    
    # Create context manager with a dummy abstract
    abstract = outline.get("thesis_statement", "Paper about AI and empathy")
    ctx_manager = EnhancedContextManager(abstract_context=abstract)
    
    # Reset exploration state
    ctx_manager.reset_exploration_state()
    
    all_idea_fingerprints = []
    all_claim_fingerprints = []
    
    sections = outline.get("sections", [])
    
    for section in sections:
        section_name = section.get("section_name", "Introducción")
        paragraphs = section.get("paragraphs", [])
        
        for para in paragraphs:
            key_idea = para.get("key_idea", "")
            supporting_points = para.get("supporting_points", [])
            suggested_sources = para.get("suggested_sources", [])
            
            # Build query like the real system
            query_parts = [key_idea]
            if supporting_points:
                query_parts.extend(supporting_points[:2])
            query = " ".join(query_parts)
            
            # NEW: Use context manager which applies exclusion, penalty, MMR
            # We need to simulate what get_context_for_idea does internally
            from ai_writer.utils.enhanced_context_manager import SECTION_CONFIGS
            config = SECTION_CONFIGS.get(section_name, SECTION_CONFIGS["Introducción"])
            
            if config.top_k == 0:
                continue
            
            # Get query embedding
            query_embedding = ctx_manager._get_cached_embedding(query)
            
            # Search with exclusion and penalty
            ideas_results = ctx_manager._search_ideas(query_embedding, config, exclude_used=True)
            claims_results = ctx_manager._search_claims(query_embedding, config, exclude_used=True)
            
            # Combine with MMR
            combined = ctx_manager._combine_and_diversify(ideas_results, claims_results, config)
            
            # Mark as used (this is the key difference!)
            ctx_manager._mark_items_as_used(combined)
            
            # Track fingerprints
            for item, score, item_type in combined:
                fp = ctx_manager._get_item_fingerprint(item, item_type)
                if item_type == "idea":
                    all_idea_fingerprints.append(fp)
                else:
                    all_claim_fingerprints.append(fp)
    
    return _compute_metrics(
        all_idea_fingerprints,
        all_claim_fingerprints,
        len(ctx_manager.ideas_index.items),
        len(ctx_manager.claims_index.items),
    )


def _compute_metrics(
    idea_fingerprints: list[str],
    claim_fingerprints: list[str],
    total_ideas: int,
    total_claims: int,
) -> ExplorationMetrics:
    """Compute exploration metrics from fingerprint lists."""
    
    unique_ideas = len(set(idea_fingerprints))
    unique_claims = len(set(claim_fingerprints))
    
    total_idea_retrievals = len(idea_fingerprints)
    total_claim_retrievals = len(claim_fingerprints)
    
    # Coverage
    idea_coverage = (unique_ideas / total_ideas * 100) if total_ideas > 0 else 0
    claim_coverage = (unique_claims / total_claims * 100) if total_claims > 0 else 0
    
    # Reuse ratio
    idea_reuse = total_idea_retrievals / unique_ideas if unique_ideas > 0 else 0
    claim_reuse = total_claim_retrievals / unique_claims if unique_claims > 0 else 0
    
    # Items retrieved multiple times
    idea_counts = Counter(idea_fingerprints)
    claim_counts = Counter(claim_fingerprints)
    
    ideas_multiple = sum(1 for c in idea_counts.values() if c > 1)
    claims_multiple = sum(1 for c in claim_counts.values() if c > 1)
    
    # Gini coefficient
    idea_values = np.array(list(idea_counts.values()), dtype=float)
    if len(idea_values) > 0:
        sorted_values = np.sort(idea_values)
        n = len(sorted_values)
        cumulative = np.cumsum(sorted_values)
        idea_gini = (n + 1 - 2 * np.sum(cumulative) / cumulative[-1]) / n
    else:
        idea_gini = 0
    
    # Exploration score (0-100)
    # Higher coverage = better
    # Lower reuse = better  
    # Lower gini = better (more uniform distribution)
    coverage_score = min(idea_coverage * 5, 40)  # Max 40 points for coverage
    reuse_penalty = max(0, 30 - (idea_reuse - 1) * 15)  # 30 points if no reuse
    gini_score = (1 - abs(idea_gini)) * 30  # 30 points for uniform distribution
    
    exploration_score = coverage_score + reuse_penalty + gini_score
    
    return ExplorationMetrics(
        unique_ideas=unique_ideas,
        unique_claims=unique_claims,
        total_idea_retrievals=total_idea_retrievals,
        total_claim_retrievals=total_claim_retrievals,
        ideas_retrieved_multiple=ideas_multiple,
        claims_retrieved_multiple=claims_multiple,
        idea_coverage_pct=idea_coverage,
        claim_coverage_pct=claim_coverage,
        idea_reuse_ratio=idea_reuse,
        claim_reuse_ratio=claim_reuse,
        idea_gini=idea_gini,
        exploration_score=exploration_score,
    )


def display_comparison(old_metrics: ExplorationMetrics, new_metrics: ExplorationMetrics):
    """Display comparison table between old and new methods."""
    
    console.print(Panel(
        "[bold]Comparación de Métodos de Exploración RAG[/bold]\n\n"
        "OLD: Búsqueda directa sin exclusión ni diversificación\n"
        "NEW: Con exclusión de ítems usados + MMR + penalización por popularidad",
        title="🔬 Exploration Comparison",
        border_style="cyan",
    ))
    
    # Main comparison table
    table = Table(title="📊 Métricas de Exploración", box=box.ROUNDED)
    table.add_column("Métrica", style="cyan")
    table.add_column("OLD", justify="right")
    table.add_column("NEW", justify="right")
    table.add_column("Δ Cambio", justify="right")
    
    def format_delta(old_val, new_val, higher_is_better=True):
        delta = new_val - old_val
        if higher_is_better:
            color = "green" if delta > 0 else ("red" if delta < 0 else "dim")
        else:
            color = "green" if delta < 0 else ("red" if delta > 0 else "dim")
        sign = "+" if delta > 0 else ""
        return f"[{color}]{sign}{delta:.1f}[/{color}]"
    
    def format_delta_int(old_val, new_val, higher_is_better=True):
        delta = new_val - old_val
        if higher_is_better:
            color = "green" if delta > 0 else ("red" if delta < 0 else "dim")
        else:
            color = "green" if delta < 0 else ("red" if delta > 0 else "dim")
        sign = "+" if delta > 0 else ""
        return f"[{color}]{sign}{delta}[/{color}]"
    
    # Ideas metrics
    table.add_row(
        "Ideas únicas recuperadas",
        str(old_metrics.unique_ideas),
        str(new_metrics.unique_ideas),
        format_delta_int(old_metrics.unique_ideas, new_metrics.unique_ideas, True),
    )
    table.add_row(
        "Cobertura de ideas (%)",
        f"{old_metrics.idea_coverage_pct:.1f}%",
        f"{new_metrics.idea_coverage_pct:.1f}%",
        format_delta(old_metrics.idea_coverage_pct, new_metrics.idea_coverage_pct, True),
    )
    table.add_row(
        "Ratio de reutilización",
        f"{old_metrics.idea_reuse_ratio:.2f}x",
        f"{new_metrics.idea_reuse_ratio:.2f}x",
        format_delta(old_metrics.idea_reuse_ratio, new_metrics.idea_reuse_ratio, False),
    )
    table.add_row(
        "Ideas repetidas (>1 vez)",
        str(old_metrics.ideas_retrieved_multiple),
        str(new_metrics.ideas_retrieved_multiple),
        format_delta_int(old_metrics.ideas_retrieved_multiple, new_metrics.ideas_retrieved_multiple, False),
    )
    
    table.add_section()
    
    # Claims metrics
    table.add_row(
        "Claims únicos recuperados",
        str(old_metrics.unique_claims),
        str(new_metrics.unique_claims),
        format_delta_int(old_metrics.unique_claims, new_metrics.unique_claims, True),
    )
    table.add_row(
        "Cobertura de claims (%)",
        f"{old_metrics.claim_coverage_pct:.1f}%",
        f"{new_metrics.claim_coverage_pct:.1f}%",
        format_delta(old_metrics.claim_coverage_pct, new_metrics.claim_coverage_pct, True),
    )
    table.add_row(
        "Claims repetidos (>1 vez)",
        str(old_metrics.claims_retrieved_multiple),
        str(new_metrics.claims_retrieved_multiple),
        format_delta_int(old_metrics.claims_retrieved_multiple, new_metrics.claims_retrieved_multiple, False),
    )
    
    table.add_section()
    
    # Overall scores
    table.add_row(
        "Coeficiente Gini (ideas)",
        f"{old_metrics.idea_gini:.3f}",
        f"{new_metrics.idea_gini:.3f}",
        format_delta(old_metrics.idea_gini, new_metrics.idea_gini, False),
    )
    table.add_row(
        "[bold]Exploration Score[/bold]",
        f"[bold]{old_metrics.exploration_score:.0f}/100[/bold]",
        f"[bold]{new_metrics.exploration_score:.0f}/100[/bold]",
        format_delta(old_metrics.exploration_score, new_metrics.exploration_score, True),
    )
    
    console.print(table)
    
    # Summary panel
    improvement = new_metrics.exploration_score - old_metrics.exploration_score
    if improvement > 10:
        emoji = "🚀"
        msg = "¡Mejora significativa en exploración!"
    elif improvement > 0:
        emoji = "✅"
        msg = "Mejora moderada en exploración"
    elif improvement == 0:
        emoji = "➡️"
        msg = "Sin cambios en exploración"
    else:
        emoji = "⚠️"
        msg = "La exploración empeoró - revisar configuración"
    
    console.print(Panel(
        f"{emoji} {msg}\n\n"
        f"Cambio en score: {'+' if improvement > 0 else ''}{improvement:.0f} puntos\n"
        f"Ideas únicas: {old_metrics.unique_ideas} → {new_metrics.unique_ideas}\n"
        f"Reutilización: {old_metrics.idea_reuse_ratio:.2f}x → {new_metrics.idea_reuse_ratio:.2f}x",
        title="📈 Resumen",
        border_style="green" if improvement > 0 else "yellow",
    ))


def main():
    parser = argparse.ArgumentParser(
        description="Compare RAG exploration with and without improvements"
    )
    parser.add_argument(
        "log_dir",
        type=Path,
        help="Directory containing the run logs (with phase2_outline.json)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of items to retrieve per paragraph (default: 10)",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export comparison results to JSON",
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
    
    n_sections = len(outline.get("sections", []))
    n_paragraphs = sum(
        len(s.get("paragraphs", []))
        for s in outline.get("sections", [])
    )
    
    console.print(Panel(
        f"[bold]Outline: {outline.get('title', 'Unknown')}[/bold]\n\n"
        f"Secciones: {n_sections}\n"
        f"Párrafos: {n_paragraphs}\n"
        f"Top-K por párrafo: {args.top_k}",
        title="📄 Configuración",
        border_style="blue",
    ))
    
    # Simulate OLD method
    console.print("\n[cyan]Simulando método OLD (sin mejoras)...[/cyan]")
    old_metrics = simulate_old_method(outline, args.top_k)
    
    # Simulate NEW method
    console.print("[cyan]Simulando método NEW (con mejoras)...[/cyan]")
    new_metrics = simulate_new_method(outline, args.top_k)
    
    # Display comparison
    console.print()
    display_comparison(old_metrics, new_metrics)
    
    # Export if requested
    if args.export:
        export_path = args.log_dir / "exploration_comparison.json"
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump({
                "old_method": {
                    "unique_ideas": old_metrics.unique_ideas,
                    "unique_claims": old_metrics.unique_claims,
                    "idea_coverage_pct": old_metrics.idea_coverage_pct,
                    "claim_coverage_pct": old_metrics.claim_coverage_pct,
                    "idea_reuse_ratio": old_metrics.idea_reuse_ratio,
                    "ideas_retrieved_multiple": old_metrics.ideas_retrieved_multiple,
                    "exploration_score": old_metrics.exploration_score,
                },
                "new_method": {
                    "unique_ideas": new_metrics.unique_ideas,
                    "unique_claims": new_metrics.unique_claims,
                    "idea_coverage_pct": new_metrics.idea_coverage_pct,
                    "claim_coverage_pct": new_metrics.claim_coverage_pct,
                    "idea_reuse_ratio": new_metrics.idea_reuse_ratio,
                    "ideas_retrieved_multiple": new_metrics.ideas_retrieved_multiple,
                    "exploration_score": new_metrics.exploration_score,
                },
                "improvement": new_metrics.exploration_score - old_metrics.exploration_score,
            }, f, indent=2)
        console.print(f"\n[dim]Exportado a {export_path}[/dim]")
    
    return 0


if __name__ == "__main__":
    exit(main())
