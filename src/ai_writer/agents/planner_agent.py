"""Planner agent for generating paper outlines."""

import json
from rich.console import Console
from rich.panel import Panel

from openai import OpenAI

from ai_writer.models.outline import PaperOutline, SectionOutline, ParagraphOutline
from config.settings import settings

console = Console()


# Modelo por defecto para el planificador
PLANNER_MODEL = "gpt-5.2"

# Standard perspective paper sections con número de párrafos recomendados
# Formato: (nombre, propósito, num_parrafos_min, num_parrafos_max)
PERSPECTIVE_SECTIONS = [
    ("Introducción", "Presentar el tema, su relevancia y la tesis central del paper", 2, 3),
    ("Estado Actual del Arte", "Revisar los avances recientes y el conocimiento establecido", 3, 5),
    ("Identificación del Problema o Brecha", "Identificar limitaciones, contradicciones o áreas no exploradas", 2, 3),
    ("La Nueva Perspectiva", "Proponer la visión o enfoque novedoso del autor", 3, 4),
    ("Discusión", "Analizar implicaciones, comparar con enfoques existentes", 3, 5),
    ("Implicaciones Futuras", "Proyectar el impacto potencial y direcciones de investigación", 2, 3),
    ("Desafíos y Limitaciones", "Reconocer obstáculos y limitaciones de la perspectiva", 2, 3),
    ("Conclusiones", "Sintetizar los puntos clave y el mensaje final", 1, 2),
]

PLANNER_SYSTEM_PROMPT = """Eres un experto planificador de papers académicos. Tu tarea es generar 
un esquema detallado (outline) para un paper de perspectivas, basándote en:

1. El abstract proporcionado
2. Los temas principales identificados en la literatura relevante
3. Las IDEAS CONCRETAS extraídas de la literatura para cada sección

Para cada sección del paper, debes:
- Definir N párrafos (respetando el rango especificado)
- Asignar una idea clave ESPECÍFICA a cada párrafo (inspirada en las ideas de la literatura)
- Identificar puntos de apoyo concretos (basados en las ideas proporcionadas)
- Indicar qué temas de la literatura fundamentan cada párrafo

IMPORTANTE:
- UTILIZA las ideas de la literatura proporcionadas como base para el contenido
- Las ideas clave deben ser ESPECÍFICAS y ARGUMENTATIVAS, no descriptivas
- Cada párrafo debe contribuir al argumento general del paper
- El esquema debe fluir lógicamente entre secciones

Responde SOLO con un JSON válido siguiendo el schema proporcionado."""


class PlannerAgent:
    """Agent for planning paper structure and generating outlines."""
    
    def __init__(
        self,
        model: str | None = None,
    ) -> None:
        """Initialize the planner agent.
        
        Args:
            model: OpenAI model to use. Defaults to gpt-5.1 for better reasoning.
        """
        self.client = OpenAI(api_key=settings.ai.openai_api_key)
        self.model = model or PLANNER_MODEL
    
    def _extract_json(self, content: str) -> str | None:
        """Extract JSON from a response that may contain other text.
        
        Args:
            content: Raw response content.
            
        Returns:
            Extracted JSON string or None if not found.
        """
        import re
        
        # First try: content is already valid JSON
        content = content.strip()
        if content.startswith("{") and content.endswith("}"):
            return content
        
        # Second try: find JSON block in markdown code fence
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            return match.group(1)
        
        # Third try: find first { to last }
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return content[start:end + 1]
        
        return None
    
    def _validate_outline_data(self, data: dict) -> bool:
        """Validate that the outline data has actual content.
        
        Args:
            data: Parsed JSON data.
            
        Returns:
            True if data is valid and has content, False otherwise.
        """
        # Check for thesis statement
        if not data.get("thesis_statement"):
            console.print("[dim]    - thesis_statement vacío[/dim]")
            return False
        
        # Check sections
        sections = data.get("sections", [])
        if not sections:
            console.print("[dim]    - No hay secciones[/dim]")
            return False
        
        # Check at least first section has content
        for section in sections[:2]:  # Check first 2 sections
            section_name = section.get("section_name", "")
            if not section_name:
                console.print("[dim]    - section_name vacío[/dim]")
                return False
            
            paragraphs = section.get("paragraphs", [])
            if not paragraphs:
                console.print(f"[dim]    - {section_name}: sin párrafos[/dim]")
                return False
            
            for para in paragraphs:
                key_idea = para.get("key_idea", "")
                if not key_idea:
                    console.print(f"[dim]    - {section_name}: key_idea vacío[/dim]")
                    return False
        
        return True
    
    def _build_planning_prompt(
        self,
        abstract: str,
        topics_summary: str,
        sections: list[tuple[str, str, int, int]],
        section_ideas: dict[str, list[dict]] | None = None,
    ) -> str:
        """Build the prompt for outline generation.
        
        Args:
            abstract: Paper abstract.
            topics_summary: Summary of available topics from cluster analysis.
            sections: List of (section_name, section_purpose, min_paragraphs, max_paragraphs) tuples.
            section_ideas: Dict mapping section names to lists of relevant ideas from literature.
            
        Returns:
            Complete prompt string.
        """
        # Build sections with paragraph counts and ideas inline
        sections_with_ideas = []
        for name, purpose, min_p, max_p in sections:
            section_block = f"## {name}\n**Propósito:** {purpose}\n**Párrafos:** {min_p}-{max_p}\n"
            
            # Add ideas for this section if available
            if section_ideas and name in section_ideas:
                ideas = section_ideas[name]
                if ideas:
                    section_block += "**Ideas de la literatura:**\n"
                    for i, idea in enumerate(ideas, 1):
                        text = idea.get("idea") or idea.get("statement") or idea.get("text", "")
                        cluster = idea.get("cluster", "")
                        if text:
                            # Truncate cleanly at sentence boundary if possible
                            text = text[:250].rsplit('.', 1)[0] + '.' if len(text) > 250 else text
                            cluster_tag = f" [{cluster}]" if cluster else ""
                            section_block += f"  {i}. {text}{cluster_tag}\n"
            
            sections_with_ideas.append(section_block)
        
        sections_text = "\n".join(sections_with_ideas)
        
        return f"""# TAREA: Generar esquema detallado para paper de perspectivas

## Abstract
{abstract}

## Secciones (genera el JSON para TODAS)

{sections_text}

## Formato de Salida (JSON)

```json
{{
  "thesis_statement": "Tesis central en una oración",
  "sections": [
    {{
      "section_name": "Nombre de la sección",
      "section_purpose": "Propósito breve",
      "paragraphs": [
        {{
          "paragraph_number": 1,
          "key_idea": "Idea específica y argumentativa (NO genérica)",
          "supporting_points": ["Punto de apoyo 1", "Punto de apoyo 2"],
          "suggested_sources": ["Topic1", "Topic2"]
        }}
      ]
    }}
  ]
}}
```

## Instrucciones
1. Genera exactamente el número de párrafos indicado por sección
2. Basa cada key_idea en las ideas de literatura proporcionadas
3. Usa suggested_sources para indicar qué topics fundamentan cada párrafo
4. Todos los campos deben tener contenido"""

    def generate_outline(
        self,
        abstract: str,
        topics_summary: str,
        title: str = "Paper de Perspectivas",
        sections: list[tuple[str, str, int, int]] | None = None,
        section_ideas: dict[str, list[dict]] | None = None,
        logger = None,
    ) -> PaperOutline:
        """Generate a detailed paper outline.
        
        Args:
            abstract: Paper abstract.
            topics_summary: Summary of available topics from cluster analysis.
            title: Paper title.
            sections: Optional custom sections (name, purpose, min_paragraphs, max_paragraphs).
            section_ideas: Dict mapping section names to lists of relevant ideas from literature.
            logger: Optional PipelineLogger for saving prompts and responses.
            
        Returns:
            Complete PaperOutline object.
        """
        console.print("\n[bold cyan]📋 Generando esquema del paper...[/bold cyan]")
        
        if section_ideas:
            total_ideas = sum(len(ideas) for ideas in section_ideas.values())
            console.print(f"[dim]  Ideas de literatura: {total_ideas} ideas para {len(section_ideas)} secciones[/dim]")
        
        sections = sections or PERSPECTIVE_SECTIONS
        
        prompt = self._build_planning_prompt(abstract, topics_summary, sections, section_ideas)
        
        # Log prompt length for debugging
        console.print(f"[dim]  Prompt: {len(prompt)} chars[/dim]")
        
        # Save prompt to logs if logger is provided
        if logger:
            full_prompt = f"""# System Prompt

{PLANNER_SYSTEM_PROMPT}

IMPORTANTE: Responde ÚNICAMENTE con JSON válido, sin texto adicional.

---

# User Prompt

{prompt}
"""
            logger.log_prompt(full_prompt, "planner_prompt")
        
        # Try up to 3 times: 2 with primary model, 1 with fallback
        models_to_try = [self.model, self.model, "gpt-4o"]
        
        for attempt, model in enumerate(models_to_try):
            try:
                console.print(f"[dim]  Llamando a {model} (intento {attempt + 1}/{len(models_to_try)})...[/dim]")
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": PLANNER_SYSTEM_PROMPT + "\n\nIMPORTANTE: Responde ÚNICAMENTE con JSON válido, sin texto adicional."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_completion_tokens=8000,
                    response_format={"type": "json_object"},
                    timeout=180,
                )
                
                content = response.choices[0].message.content
                console.print(f"[dim]  Respuesta recibida: {len(content) if content else 0} chars[/dim]")
                
                # Log the raw response
                if logger and content:
                    logger.log_llm_response(content, model, f"planner_response_attempt_{attempt + 1}")
                
                if not content or content.strip() == "":
                    console.print(f"[yellow]⚠ Respuesta vacía (intento {attempt + 1}/{len(models_to_try)})[/yellow]")
                    continue
                
                # Try to extract JSON from the response
                json_content = self._extract_json(content)
                if not json_content:
                    console.print(f"[yellow]⚠ No se encontró JSON (intento {attempt + 1}/{len(models_to_try)})[/yellow]")
                    continue
                    
                data = json.loads(json_content)
                
                # Validate that we have actual content
                if not self._validate_outline_data(data):
                    console.print(f"[yellow]⚠ JSON con campos vacíos (intento {attempt + 1}/{len(models_to_try)})[/yellow]")
                    continue
                
                # Parse response into outline
                outline = self._parse_outline_response(data, abstract, title)
                
                console.print(f"[green]✓ Esquema generado: {outline.total_sections} secciones, "
                             f"{outline.total_paragraphs} párrafos[/green]")
                
                return outline
                
            except json.JSONDecodeError as e:
                console.print(f"[yellow]⚠ Error JSON (intento {attempt + 1}/{len(models_to_try)}): {e}[/yellow]")
                continue
            except Exception as e:
                console.print(f"[red]Error generando esquema: {e}[/red]")
                continue  # Try next model instead of breaking
        
        # Return a basic outline as fallback
        console.print("[yellow]Usando esquema básico como fallback[/yellow]")
        return self._create_basic_outline(abstract, title, sections)
    
    def _parse_outline_response(
        self,
        data: dict,
        abstract: str,
        title: str,
    ) -> PaperOutline:
        """Parse LLM response into PaperOutline object.
        
        Args:
            data: Parsed JSON response.
            abstract: Paper abstract.
            title: Paper title.
            
        Returns:
            PaperOutline object.
        """
        sections = []
        
        for section_data in data.get("sections", []):
            paragraphs = []
            
            for para_data in section_data.get("paragraphs", []):
                paragraph = ParagraphOutline(
                    paragraph_number=para_data.get("paragraph_number", len(paragraphs) + 1),
                    key_idea=para_data.get("key_idea", ""),
                    supporting_points=para_data.get("supporting_points", []),
                    suggested_sources=para_data.get("suggested_sources", []),
                )
                paragraphs.append(paragraph)
            
            section = SectionOutline(
                section_name=section_data.get("section_name", ""),
                section_purpose=section_data.get("section_purpose", ""),
                paragraphs=paragraphs,
            )
            sections.append(section)
        
        return PaperOutline(
            title=title,
            abstract=abstract,
            thesis_statement=data.get("thesis_statement", ""),
            sections=sections,
        )
    
    def _create_basic_outline(
        self,
        abstract: str,
        title: str,
        sections: list[tuple[str, str, int, int]],
    ) -> PaperOutline:
        """Create a basic fallback outline.
        
        Args:
            abstract: Paper abstract.
            title: Paper title.
            sections: List of (section_name, section_purpose, min_paragraphs, max_paragraphs) tuples.
            
        Returns:
            Basic PaperOutline object.
        """
        outline_sections = []
        
        for section_name, section_purpose, min_p, max_p in sections:
            # Create min_p paragraphs per section as fallback
            paragraphs = []
            for i in range(min_p):
                if i == 0:
                    paragraphs.append(ParagraphOutline(
                        paragraph_number=1,
                        key_idea=f"Introducir {section_name.lower()}",
                        supporting_points=["Contexto", "Definiciones"],
                    ))
                else:
                    paragraphs.append(ParagraphOutline(
                        paragraph_number=i + 1,
                        key_idea=f"Desarrollar argumentos de {section_name.lower()}",
                        supporting_points=["Evidencia", "Ejemplos"],
                    ))
            
            section = SectionOutline(
                section_name=section_name,
                section_purpose=section_purpose,
                paragraphs=paragraphs,
            )
            outline_sections.append(section)
        
        return PaperOutline(
            title=title,
            abstract=abstract,
            thesis_statement="Por definir",
            sections=outline_sections,
        )
    
    def refine_outline(
        self,
        outline: PaperOutline,
        feedback: str,
    ) -> PaperOutline:
        """Refine an outline based on feedback.
        
        Args:
            outline: Current outline.
            feedback: Feedback to incorporate.
            
        Returns:
            Refined PaperOutline object.
        """
        console.print("[cyan]🔄 Refinando esquema basado en feedback...[/cyan]")
        
        refine_prompt = f"""# Esquema Actual

{outline.to_markdown()}

# Feedback para Mejorar

{feedback}

# Instrucciones

Refina el esquema incorporando el feedback. Mantén la estructura JSON:
{{
  "thesis_statement": "...",
  "sections": [...]
}}

Asegúrate de:
1. Abordar específicamente cada punto del feedback
2. Mantener coherencia entre secciones
3. Mejorar las ideas clave para que sean más específicas y argumentables"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PLANNER_SYSTEM_PROMPT + "\n\nIMPORTANTE: Responde ÚNICAMENTE con JSON válido y COMPLETO."},
                    {"role": "user", "content": refine_prompt},
                ],
                temperature=0.7,
                max_completion_tokens=8000,  # Increased from 4000
                response_format={"type": "json_object"},
                timeout=180,
            )
            
            content = response.choices[0].message.content
            
            if not content or content.strip() == "":
                console.print("[yellow]Respuesta vacía en refinamiento. Manteniendo esquema original.[/yellow]")
                return outline
                
            data = json.loads(content)
            
            # Validate refined data has actual content
            if not self._validate_outline_data(data):
                console.print("[yellow]Esquema refinado tiene campos vacíos. Manteniendo esquema original.[/yellow]")
                return outline
            
            refined = self._parse_outline_response(data, outline.abstract, outline.title)
            refined.available_topics = outline.available_topics
            
            console.print("[green]✓ Esquema refinado[/green]")
            return refined
            
        except Exception as e:
            console.print(f"[yellow]Error refinando: {e}. Manteniendo esquema original.[/yellow]")
            return outline
    
    def display_outline(self, outline: PaperOutline) -> None:
        """Display the outline in a formatted panel.
        
        Args:
            outline: Outline to display.
        """
        console.print(Panel(
            outline.to_markdown(),
            title=f"📝 Esquema: {outline.title}",
            border_style="cyan",
        ))
