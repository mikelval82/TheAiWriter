"""Reviewer agent for reviewing and improving academic papers."""

import json
from typing import TYPE_CHECKING

from ai_writer.agents.base_agent import BaseAgent
from ai_writer.models.paper import Paper, Section

if TYPE_CHECKING:
    from ai_writer.utils.enhanced_context_manager import EnhancedContextManager


class ReviewerAgent(BaseAgent):
    """Agent specialized in reviewing and improving academic papers."""

    def __init__(
        self,
        model: str | None = None,
        abstract_context: str | None = None,
        context_manager: "EnhancedContextManager | None" = None,
    ) -> None:
        """Initialize the reviewer agent.

        Args:
            model: The model to use. Defaults to settings default.
            abstract_context: The abstract that provides context for the paper.
            context_manager: Optional context manager for RAG-enhanced review.
        """
        super().__init__(model=model)
        self.abstract_context = abstract_context or ""
        self.context_manager = context_manager
        # Short-term memory: resúmenes de secciones revisadas
        self.section_summaries: dict[str, str] = {}
    
    def set_context_manager(self, context_manager: "EnhancedContextManager") -> None:
        """Set the context manager for RAG-enhanced review.
        
        Args:
            context_manager: The enhanced context manager to use.
        """
        self.context_manager = context_manager
    
    def reset_memory(self) -> None:
        """Reset the short-term memory (section summaries)."""
        self.section_summaries = {}
    
    def _generate_section_summary(self, section: Section) -> str:
        """Generate a concise summary of a section for context memory.
        
        Args:
            section: The section to summarize.
            
        Returns:
            A concise summary capturing key points and arguments.
        """
        user_prompt = f"""Genera un resumen conciso de la siguiente sección de un paper académico.

SECCIÓN: {section.title}

CONTENIDO:
{section.content}

INSTRUCCIONES:
- Resume en 3-5 oraciones los puntos clave y argumentos principales
- Incluye la tesis o idea central de la sección
- Menciona conceptos o términos importantes introducidos
- Sé preciso y conciso (máximo 150 palabras)
- Este resumen se usará para dar contexto al revisar secciones posteriores

RESUMEN:"""

        summary = self._call_api(
            system_prompt="Eres un asistente experto en síntesis de textos académicos. Generas resúmenes precisos y concisos.",
            user_prompt=user_prompt,
            max_tokens=300,
            temperature=0.3,
        )
        
        return summary.strip()
    
    def update_section_memory(self, section: Section) -> str:
        """Update the short-term memory with a new or revised section.
        
        Args:
            section: The section to add/update in memory.
            
        Returns:
            The generated summary.
        """
        summary = self._generate_section_summary(section)
        self.section_summaries[section.title] = summary
        return summary
    
    def get_context_from_memory(self) -> str:
        """Build context string from accumulated section summaries.
        
        Returns:
            Formatted context string with all section summaries.
        """
        if not self.section_summaries:
            return ""
        
        context = "\n\nMEMORIA DE SECCIONES ANTERIORES:\n"
        context += "(Resúmenes de las secciones ya revisadas para mantener coherencia)\n"
        
        for title, summary in self.section_summaries.items():
            context += f"\n### {title}\n{summary}\n"
        
        return context

    # =========================================================================
    # RAG-Enhanced Review Methods
    # =========================================================================
    
    def _generate_strengthening_queries(self, section: Section) -> dict[str, str]:
        """Generate 4 specific queries to strengthen the section's arguments.
        
        Generates one query of each type:
        - support: Evidence that confirms claims in the section
        - counter: Limitations or criticisms to address
        - examples: Concrete implementations or case studies
        - connections: Relationships with other concepts
        
        Args:
            section: The section to analyze.
            
        Returns:
            Dict with query types as keys and query strings as values.
        """
        user_prompt = f"""Analiza la siguiente sección académica e identifica 4 queries específicas para buscar 
en la literatura y fortalecer los argumentos.

SECCIÓN: {section.title}

CONTENIDO:
{section.content}

Genera exactamente 4 queries, una de cada tipo:

1. SOPORTE: Una query para buscar estudios o evidencia que confirmen el argumento principal
2. CONTRARIA: Una query para buscar limitaciones, críticas o evidencia contraria que debería abordarse
3. EJEMPLO: Una query para buscar implementaciones concretas, casos de estudio o ejemplos prácticos
4. CONEXION: Una query para buscar relaciones con otros conceptos o campos que enriquezcan el argumento

IMPORTANTE:
- Las queries deben ser específicas y basadas en el contenido real de la sección
- Deben ser útiles para búsqueda semántica en un corpus académico
- No uses términos genéricos, sé concreto

Responde SOLO en formato JSON:
{{
    "support": "query para buscar evidencia de soporte...",
    "counter": "query para buscar limitaciones o críticas...",
    "examples": "query para buscar implementaciones o ejemplos...",
    "connections": "query para buscar relaciones con otros conceptos..."
}}"""

        response = self._call_api(
            system_prompt="Eres un experto en investigación académica. Generas queries precisas para búsqueda en literatura científica.",
            user_prompt=user_prompt,
            max_tokens=500,
            temperature=0.5,
        )
        
        # Parse JSON response
        try:
            # Clean response if wrapped in markdown
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            queries = json.loads(response)
            return {
                "support": queries.get("support", ""),
                "counter": queries.get("counter", ""),
                "examples": queries.get("examples", ""),
                "connections": queries.get("connections", ""),
            }
        except json.JSONDecodeError:
            # Fallback: return empty queries
            return {"support": "", "counter": "", "examples": "", "connections": ""}
    
    def _search_for_strengthening_evidence(
        self,
        queries: dict[str, str],
        top_k_per_query: int = 2,
    ) -> str:
        """Search the embedding space for evidence to strengthen arguments.
        
        Args:
            queries: Dict with query types and query strings.
            top_k_per_query: Number of results per query type.
            
        Returns:
            Formatted context string with found evidence.
        """
        if not self.context_manager:
            return ""
        
        evidence_sections = []
        
        query_type_labels = {
            "support": "📗 EVIDENCIA DE SOPORTE",
            "counter": "📙 LIMITACIONES/CRÍTICAS A CONSIDERAR",
            "examples": "📘 EJEMPLOS E IMPLEMENTACIONES",
            "connections": "📕 CONEXIONES CON OTROS CONCEPTOS",
        }
        
        for query_type, query in queries.items():
            if not query:
                continue
            
            label = query_type_labels.get(query_type, query_type.upper())
            
            # Search in ideas index
            results = self.context_manager.ideas_index.search(query, top_k=top_k_per_query)
            
            if results:
                section_text = f"\n{label}:\n"
                section_text += f"(Query: {query[:80]}...)\n" if len(query) > 80 else f"(Query: {query})\n"
                
                for item, score in results:
                    idea = item.get("idea", "")
                    paper = item.get("paper_title", "Unknown")[:50]
                    section_text += f"- [{paper}] {idea}\n"
                
                evidence_sections.append(section_text)
        
        if not evidence_sections:
            return ""
        
        context = "\n\n" + "=" * 50 + "\n"
        context += "EVIDENCIA ADICIONAL DE LA LITERATURA\n"
        context += "(Resultados de búsqueda para fortalecer argumentos)\n"
        context += "=" * 50
        context += "".join(evidence_sections)
        
        return context
    @property
    def system_prompt(self) -> str:
        """Return the system prompt for the reviewer agent."""
        base_prompt = """Eres un revisor y editor académico experto con amplia experiencia 
en revisión por pares para revistas de primer nivel. Tu enfoque de revisión es:

- Constructivo y exhaustivo
- Enfocado en mejorar claridad y rigor
- Atento al flujo lógico y la argumentación
- Sensible a las convenciones y estándares académicos

Al revisar:
1. Identificas áreas que necesitan mejora
2. Sugieres mejoras específicas
3. Corriges inconsistencias y errores
4. Fortaleces argumentos y evidencia
5. Mejoras legibilidad y flujo
6. Trabajas en ESPAÑOL manteniendo un tono académico profesional"""

        if self.abstract_context:
            base_prompt += f"""

CONTEXTO FUNDAMENTAL - ABSTRACT DEL PAPER:
El siguiente abstract define el tono, contexto y dirección del paper.
Todas tus revisiones deben asegurar coherencia con este abstract:

---
{self.abstract_context}
---

Al revisar, verifica que:
- El contenido sea coherente con los temas del abstract
- Se mantenga el mismo tono y nivel académico
- La terminología sea consistente
- Los argumentos apoyen la tesis central del abstract"""

        return base_prompt

    def review(self, paper: Paper) -> Paper:
        """Review and improve a paper.

        Args:
            paper: The paper to review.

        Returns:
            An improved version of the paper.
        """
        improved_sections = []

        for section in paper.sections:
            user_prompt = f"""Review and improve the following section from an academic paper titled "{paper.title}".

Section: {section.title}

Current content:
{section.content}

Requirements:
- Improve clarity and precision
- Strengthen arguments
- Fix any grammatical or stylistic issues
- Enhance academic rigor
- Maintain the core ideas but express them better
- Ensure proper academic tone

Write only the improved content, not commentary about changes."""

            improved_content = self._call_api(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
            )

            improved_sections.append(
                Section(title=section.title, content=improved_content.strip())
            )

        return Paper(
            title=paper.title,
            sections=improved_sections,
            authors=paper.authors,
            keywords=paper.keywords,
        )

    def get_feedback(self, paper: Paper) -> str:
        """Get detailed feedback on a paper without modifying it.

        Args:
            paper: The paper to get feedback on.

        Returns:
            Detailed feedback and suggestions.
        """
        paper_text = paper.to_text()

        user_prompt = f"""Provide detailed feedback on the following academic paper:

{paper_text}

Provide feedback in the following format:
1. Overall Assessment
2. Strengths
3. Areas for Improvement
4. Specific Suggestions for Each Section
5. Grammar and Style Notes
6. Recommendations for Next Steps"""

        feedback = self._call_api(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=2000,
        )

        return feedback

    def check_consistency(self, paper: Paper) -> str:
        """Check the paper for internal consistency.

        Args:
            paper: The paper to check.

        Returns:
            Report on any inconsistencies found.
        """
        paper_text = paper.to_text()

        user_prompt = f"""Analyze the following academic paper for internal consistency:

{paper_text}

Check for:
1. Logical flow between sections
2. Consistent terminology usage
3. Claims made in one section that contradict another
4. References to content that doesn't exist
5. Gaps in argumentation

Provide a consistency report with specific issues and locations."""

        report = self._call_api(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
        )

        return report
    
    def review_section(
        self,
        section: Section,
        previous_sections: list[Section] | None = None,
        update_memory: bool = True,
        use_rag_enhancement: bool = True,
    ) -> Section:
        """Review and improve a single section with context from memory.

        Args:
            section: The section to review.
            previous_sections: Already written sections (used to sync memory if empty).
            update_memory: Whether to update memory after review (default True).
            use_rag_enhancement: Whether to search for additional evidence (default True).

        Returns:
            The improved section.
        """
        # Sync memory with previous sections if memory is empty
        # (This handles the case where we're starting fresh or sections were written without review)
        if previous_sections and not self.section_summaries:
            for sec in previous_sections:
                if sec.title not in self.section_summaries:
                    self.update_section_memory(sec)
        
        # Build context from memory (summaries) instead of truncated text
        previous_context = self.get_context_from_memory()
        
        # RAG Enhancement: Search for additional evidence to strengthen arguments
        rag_context = ""
        if use_rag_enhancement and self.context_manager:
            # Generate targeted queries based on section content
            queries = self._generate_strengthening_queries(section)
            # Search embedding space for evidence
            rag_context = self._search_for_strengthening_evidence(queries)

        user_prompt = f"""Revisa y mejora la siguiente sección de un artículo de perspectivas académico.

SECCIÓN A REVISAR: {section.title}

CONTENIDO ACTUAL:
{section.content}
{previous_context}{rag_context}

CRITERIOS DE REVISIÓN:
1. Claridad y precisión del lenguaje
2. Fortaleza de los argumentos
3. Coherencia con el abstract y secciones anteriores
4. Rigor académico
5. Flujo lógico y transiciones
6. Corrección gramatical y estilística

INSTRUCCIONES:
- Mejora el contenido manteniendo las ideas centrales
- Asegura coherencia con el contexto del paper (resúmenes de secciones anteriores)
- Si se proporciona EVIDENCIA ADICIONAL DE LA LITERATURA, considera incorporar 
  insights relevantes para fortalecer los argumentos (cita las fuentes si las usas)
- Escribe en español académico formal
- NO incluyas comentarios sobre los cambios, solo el contenido mejorado

Escribe únicamente el contenido mejorado de la sección:"""

        improved_content = self._call_api(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=4096,
        )

        improved_section = Section(title=section.title, content=improved_content.strip())
        
        # Update memory with the improved section
        if update_memory:
            self.update_section_memory(improved_section)
        
        return improved_section

    def review_full_paper(self, paper: Paper) -> Paper:
        """Perform a final coherence review of the complete paper.

        Args:
            paper: The complete paper to review.

        Returns:
            The paper with improved coherence.
        """
        paper_text = paper.to_text()

        user_prompt = f"""Realiza una revisión final de coherencia del siguiente artículo de perspectivas.

PAPER COMPLETO:
{paper_text}

OBJETIVOS DE LA REVISIÓN FINAL:
1. Asegurar coherencia global entre todas las secciones
2. Verificar que el flujo narrativo sea lógico
3. Confirmar que los argumentos se desarrollan progresivamente
4. Asegurar consistencia terminológica
5. Verificar que las conclusiones derivan de los argumentos presentados

Para cada sección, proporciona una versión mejorada que maximice la coherencia global.
Responde en formato estructurado con cada sección claramente delimitada:

### [Nombre de Sección]
[Contenido mejorado]

NO incluyas el Abstract (ya está definido). Comienza desde la Introducción."""

        response = self._call_api(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=16000,
        )

        # Parse the response and update sections
        # Keep the abstract as-is, update other sections
        improved_sections = [paper.sections[0]]  # Keep abstract

        # Simple parsing of markdown sections
        current_section = None
        current_content = []

        for line in response.split("\n"):
            if line.startswith("### "):
                if current_section and current_content:
                    improved_sections.append(
                        Section(title=current_section, content="\n".join(current_content).strip())
                    )
                current_section = line[4:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        # Add last section
        if current_section and current_content:
            improved_sections.append(
                Section(title=current_section, content="\n".join(current_content).strip())
            )

        # If parsing failed, return original paper
        if len(improved_sections) <= 1:
            return paper

        return Paper(
            title=paper.title,
            sections=improved_sections,
            authors=paper.authors,
            keywords=paper.keywords,
        )

    def generate_critical_review(self, paper: Paper) -> str:
        """Generate a comprehensive critical review document.

        Args:
            paper: The complete paper to review critically.

        Returns:
            A markdown document with the critical review.
        """
        paper_text = paper.to_text()

        user_prompt = f"""Genera un documento de revisión crítica exhaustivo del siguiente artículo de perspectivas.

PAPER A REVISAR:
{paper_text}

ESTRUCTURA DEL DOCUMENTO CRÍTICO:

# Revisión Crítica: [Título del Paper]

## 1. Resumen Ejecutivo
- Evaluación general (1-10)
- Fortalezas principales
- Debilidades principales

## 2. Análisis de Coherencia
- Coherencia con el abstract
- Flujo lógico entre secciones
- Consistencia argumentativa

## 3. Evaluación por Sección
Para cada sección:
- Puntos fuertes
- Áreas de mejora
- Sugerencias específicas

## 4. Rigor Académico
- Calidad de la argumentación
- Uso de evidencia
- Originalidad de la perspectiva

## 5. Aspectos Formales
- Claridad del lenguaje
- Estructura del documento
- Estilo académico

## 6. Recomendaciones Prioritarias
Lista numerada de las mejoras más importantes

## 7. Conclusión de la Revisión
Valoración final y recomendación de publicación

---

Sé constructivo pero riguroso. Este documento servirá para mejorar futuras versiones del paper."""

        critical_review = self._call_api(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=8000,
        )

        return critical_review

    def review_outline(self, outline) -> str:
        """Review a paper outline and provide improvement feedback.
        
        Args:
            outline: PaperOutline object to review.
            
        Returns:
            Feedback string for improving the outline.
        """
        outline_text = outline.to_markdown()
        
        user_prompt = f"""Revisa el siguiente esquema de paper académico y proporciona feedback para mejorarlo.

ESQUEMA A REVISAR:
{outline_text}

CRITERIOS DE EVALUACIÓN:
1. ¿Las ideas clave son específicas y argumentables, o demasiado genéricas?
2. ¿Hay coherencia lógica entre secciones y párrafos?
3. ¿Los puntos de apoyo son relevantes para cada idea clave?
4. ¿El esquema cubre todos los aspectos necesarios del tema?
5. ¿Hay redundancia EVIDENTE entre secciones? (solo si dos párrafos dicen esencialmente lo mismo)
6. ¿Las transiciones entre secciones serán naturales?

INSTRUCCIONES:
- Si el esquema es bueno, responde "Sin cambios necesarios"
- Si hay mejoras, proporciona feedback específico y accionable
- Sé conciso y directo
- Enfócate en las mejoras más importantes
- IMPORTANTE: Valora la profundidad y exhaustividad del contenido
- NO sugieras eliminar o fusionar párrafos a menos que haya redundancia clara y evidente
- Prefiere sugerir mejoras de contenido sobre reducciones de estructura

FEEDBACK:"""

        feedback = self._call_api(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=1500,
        )
        
        return feedback.strip()