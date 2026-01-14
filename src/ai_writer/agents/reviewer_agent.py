"""Reviewer agent for reviewing and improving academic papers."""

from ai_writer.agents.base_agent import BaseAgent
from ai_writer.models.paper import Paper, Section


class ReviewerAgent(BaseAgent):
    """Agent specialized in reviewing and improving academic papers."""

    def __init__(
        self,
        model: str | None = None,
        abstract_context: str | None = None,
    ) -> None:
        """Initialize the reviewer agent.

        Args:
            model: The model to use. Defaults to settings default.
            abstract_context: The abstract that provides context for the paper.
        """
        super().__init__(model=model)
        self.abstract_context = abstract_context or ""

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
    ) -> Section:
        """Review and improve a single section with context.

        Args:
            section: The section to review.
            previous_sections: Already written sections for context.

        Returns:
            The improved section.
        """
        # Build context from previous sections
        previous_context = ""
        if previous_sections:
            previous_context = "\n\nCONTEXTO - SECCIONES ANTERIORES:\n"
            for sec in previous_sections:
                content = sec.content[:1000] + "..." if len(sec.content) > 1000 else sec.content
                previous_context += f"\n### {sec.title}\n{content}\n"

        user_prompt = f"""Revisa y mejora la siguiente sección de un artículo de perspectivas académico.

SECCIÓN A REVISAR: {section.title}

CONTENIDO ACTUAL:
{section.content}
{previous_context}

CRITERIOS DE REVISIÓN:
1. Claridad y precisión del lenguaje
2. Fortaleza de los argumentos
3. Coherencia con el abstract y secciones anteriores
4. Rigor académico
5. Flujo lógico y transiciones
6. Corrección gramatical y estilística

INSTRUCCIONES:
- Mejora el contenido manteniendo las ideas centrales
- Asegura coherencia con el contexto del paper
- Escribe en español académico formal
- NO incluyas comentarios sobre los cambios, solo el contenido mejorado

Escribe únicamente el contenido mejorado de la sección:"""

        improved_content = self._call_api(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=4096,
        )

        return Section(title=section.title, content=improved_content.strip())

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