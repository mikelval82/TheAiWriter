"""Script to test the RAG system with the processed papers."""

import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ai_writer.embeddings.rag_system import RAGSystem

console = Console()


def main() -> None:
    """Test the RAG system."""
    console.print("[bold blue]═══════════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]       TheAIWriter - RAG System Test           [/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════════[/bold blue]\n")

    # Initialize RAG system
    rag = RAGSystem()
    
    # Build indices
    rag.build_indices(force_rebuild=False)
    
    # Test queries
    test_queries = [
        "cognitive architectures for AI agents",
        "emotion recognition in conversational systems",
        "memory systems in language models",
        "empathy in human-computer interaction",
    ]
    
    console.print("\n[bold cyan]🔍 Testing Search Queries[/bold cyan]\n")
    
    for query in test_queries:
        console.print(Panel(f"[bold]Query:[/bold] {query}", border_style="blue"))
        
        # Search ideas
        ideas = rag.search_ideas(query, top_k=3, min_score=0.4)
        if ideas:
            console.print("\n[green]💡 Top Ideas:[/green]")
            for idea, score in ideas:
                console.print(f"  [{score:.3f}] {idea.get('idea', '')[:100]}...")
                console.print(f"         [dim]From: {idea.get('paper_title', 'Unknown')}[/dim]")
        
        # Search claims
        claims = rag.search_claims(query, top_k=2, min_score=0.4)
        if claims:
            console.print("\n[yellow]📌 Top Claims:[/yellow]")
            for claim, score in claims:
                console.print(f"  [{score:.3f}] {claim.get('claim', '')[:100]}...")
        
        # Search references
        refs = rag.search_references(query, top_k=3, min_score=0.3)
        if refs:
            console.print("\n[magenta]📚 Top References:[/magenta]")
            for ref, score in refs:
                console.print(f"  [{score:.3f}] {ref.get('citation_key', '')}: {ref.get('title', '')[:60]}...")
        
        console.print()
    
    # Test context retrieval for a section
    console.print("[bold cyan]📝 Testing Section Context Retrieval[/bold cyan]\n")
    
    section_name = "Introduction"
    section_desc = "Overview of cognitive architectures for empathic AI agents in the metaverse"
    
    context = rag.get_context_for_section(section_name, section_desc)
    
    console.print(f"[bold]Section:[/bold] {section_name}")
    console.print(f"[bold]Description:[/bold] {section_desc}\n")
    console.print(f"Retrieved: {len(context['ideas'])} ideas, {len(context['claims'])} claims, {len(context['references'])} references")
    
    console.print("\n[dim]Formatted context (first 1000 chars):[/dim]")
    console.print(context['formatted_context'][:1000])
    
    console.print("\n[bold green]═══════════════════════════════════════════════[/bold green]")
    console.print("[bold green]              Test Completed!                  [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════════[/bold green]")


if __name__ == "__main__":
    main()
