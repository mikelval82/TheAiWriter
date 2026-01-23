"""Test script for the planner agent with gpt-5.2."""

import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from ai_writer.agents.planner_agent import PlannerAgent, PLANNER_MODEL

console = Console()


def test_planner_with_prompt():
    """Test the planner agent using the saved planner_prompt.md file."""
    
    # Show which model we're using
    console.print(Panel(
        f"[bold cyan]Testing PlannerAgent with model: {PLANNER_MODEL}[/bold cyan]",
        title="🧪 Planner Test"
    ))
    
    # Read the planner_prompt.md file
    prompt_path = Path("/home/mikel/TheAIWriter/data/logs/run_Agentes_Empáticos_Fundamentales/planner_prompt.md")
    
    if not prompt_path.exists():
        console.print(f"[red]Error: No se encuentra {prompt_path}[/red]")
        return
    
    content = prompt_path.read_text(encoding="utf-8")
    console.print(f"[dim]Prompt cargado: {len(content)} chars[/dim]")
    
    # Extract abstract from the prompt
    abstract_start = content.find("## Abstract")
    abstract_end = content.find("## Secciones")
    
    if abstract_start == -1 or abstract_end == -1:
        console.print("[red]Error: No se pudo extraer el abstract[/red]")
        return
    
    abstract_section = content[abstract_start:abstract_end]
    # Extract just the abstract text after "Abstract:" 
    abstract_text_start = abstract_section.find("Abstract:")
    if abstract_text_start != -1:
        abstract = abstract_section[abstract_text_start + len("Abstract:"):].strip()
    else:
        abstract = abstract_section.replace("## Abstract", "").strip()
    
    console.print(f"\n[bold]Abstract extraído:[/bold]")
    console.print(f"[dim]{abstract[:300]}...[/dim]\n")
    
    # Extract section ideas from the prompt
    section_ideas = extract_section_ideas(content)
    console.print(f"[dim]Secciones encontradas: {list(section_ideas.keys())}[/dim]")
    for name, ideas in section_ideas.items():
        console.print(f"[dim]  - {name}: {len(ideas)} ideas[/dim]")
    
    # Create planner agent
    planner = PlannerAgent()
    console.print(f"\n[bold]Modelo configurado: {planner.model}[/bold]\n")
    
    # Generate outline
    try:
        outline = planner.generate_outline(
            abstract=abstract,
            topics_summary="Topics from literature review",
            title="Hacia Agentes Empáticos Fundamentales",
            section_ideas=section_ideas,
        )
        
        # Show results
        console.print(Panel(
            f"[bold green]✓ Outline generado exitosamente[/bold green]\n\n"
            f"Tesis: {outline.thesis_statement[:200]}...\n\n"
            f"Secciones: {outline.total_sections}\n"
            f"Párrafos: {outline.total_paragraphs}",
            title="📋 Resultado"
        ))
        
        # Show outline details
        console.print("\n[bold cyan]Estructura del outline:[/bold cyan]")
        for section in outline.sections:
            console.print(f"\n[bold]{section.section_name}[/bold] ({len(section.paragraphs)} párrafos)")
            for i, para in enumerate(section.paragraphs, 1):
                console.print(f"  {i}. [dim]{para.key_idea[:100]}...[/dim]")
        
        # Save output for inspection
        output_path = Path("/home/mikel/TheAIWriter/data/logs/test_planner_output.json")
        output_data = {
            "model": planner.model,
            "thesis_statement": outline.thesis_statement,
            "total_sections": outline.total_sections,
            "total_paragraphs": outline.total_paragraphs,
            "sections": [
                {
                    "name": s.section_name,
                    "purpose": s.section_purpose,
                    "paragraphs": [
                        {
                            "number": p.paragraph_number,
                            "key_idea": p.key_idea,
                            "supporting_points": p.supporting_points,
                            "suggested_sources": p.suggested_sources,
                        }
                        for p in s.paragraphs
                    ]
                }
                for s in outline.sections
            ]
        }
        output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
        console.print(f"\n[dim]Output guardado en: {output_path}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


def extract_section_ideas(content: str) -> dict[str, list[dict]]:
    """Extract section ideas from the planner prompt."""
    import re
    
    section_ideas = {}
    
    # Find each section block
    section_pattern = r"## ([\w\s]+)\n\*\*Propósito:\*\*[^\n]+\n\*\*Párrafos:\*\*[^\n]+\n(?:\*\*Ideas de la literatura:\*\*\n((?:  \d+\.[^\n]+\n)+))?"
    
    matches = re.findall(section_pattern, content)
    
    for match in matches:
        section_name = match[0].strip()
        ideas_text = match[1] if len(match) > 1 else ""
        
        ideas = []
        if ideas_text:
            # Parse each idea line
            idea_lines = re.findall(r"  \d+\. ([^\[]+)\[([^\]]+)\]", ideas_text)
            for idea_text, cluster in idea_lines:
                ideas.append({
                    "idea": idea_text.strip(),
                    "cluster": cluster.strip(),
                })
        
        section_ideas[section_name] = ideas
    
    return section_ideas


if __name__ == "__main__":
    test_planner_with_prompt()
