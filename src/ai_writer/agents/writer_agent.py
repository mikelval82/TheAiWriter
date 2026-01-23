"""Writer agent for generating academic paper content."""

from ai_writer.agents.base_agent import BaseAgent
from ai_writer.models.paper import Paper, Section


class WriterAgent(BaseAgent):
    """Agent specialized in writing academic papers."""

    def __init__(
        self,
        model: str | None = None,
        abstract_context: str | None = None,
    ) -> None:
        """Initialize the writer agent.

        Args:
            model: The model to use. Defaults to settings default.
            abstract_context: The abstract that provides context for the paper.
        """
        super().__init__(model=model)
        self.abstract_context = abstract_context or ""

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for the writer agent."""
        base_prompt = """Eres un escritor académico experto con amplia experiencia en la redacción de 
artículos de investigación, disertaciones y artículos científicos. Tu escritura es:

- Clara, precisa y bien estructurada
- Académicamente rigurosa con citas apropiadas
- Atractiva manteniendo un tono académico formal
- Bien organizada con flujo lógico entre secciones

Al escribir:
1. Usas argumentos basados en evidencia
2. Citas fuentes apropiadamente
3. Sigues convenciones académicas estándar
4. Aseguras claridad y coherencia
5. Mantienes objetividad y análisis crítico
6. Escribes en ESPAÑOL de forma académica y profesional"""

        if self.abstract_context:
            base_prompt += f"""

CONTEXTO FUNDAMENTAL - ABSTRACT DEL PAPER:
El siguiente abstract define el tono, contexto y dirección del paper. 
Toda tu escritura debe mantener coherencia con este abstract:

---
{self.abstract_context}
---

Asegúrate de que cada sección que escribas:
- Sea coherente con los temas y argumentos del abstract
- Mantenga el mismo tono y nivel académico
- Contribuya a desarrollar las ideas centrales presentadas
- Use terminología consistente con el abstract"""

        return base_prompt

    def write(
        self,
        topic: str,
        sections: list[str],
        references: list[str] | None = None,
    ) -> Paper:
        """Write a complete paper on the given topic.

        Args:
            topic: The main topic/title of the paper.
            sections: List of section names to generate.
            references: Optional list of reference texts for context.

        Returns:
            A Paper object with generated content.
        """
        reference_context = ""
        if references:
            reference_context = "\n\nUse the following references as context:\n"
            for i, ref in enumerate(references, 1):
                # Truncate long references to avoid token limits
                truncated = ref[:2000] + "..." if len(ref) > 2000 else ref
                reference_context += f"\n--- Reference {i} ---\n{truncated}\n"

        generated_sections = []
        for section_name in sections:
            user_prompt = f"""Write the '{section_name}' section for an academic paper titled: "{topic}"

{reference_context}

Requirements:
- Write in formal academic style
- Be thorough but concise
- Include relevant details and analysis
- If this is the Abstract, keep it to 150-250 words
- If this is the Introduction, provide context and state the research objectives
- If this is Methodology, describe the approach clearly
- If this is Results, present findings objectively
- If this is Discussion, analyze and interpret the results
- If this is Conclusion, summarize key findings and implications

Write only the content for this section, without the section title."""

            content = self._call_api(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
            )

            generated_sections.append(Section(title=section_name, content=content.strip()))

        return Paper(
            title=topic,
            sections=generated_sections,
        )

    def write_section(
        self,
        section_name: str,
        previous_sections: list[Section] | None = None,
        reference_context: str = "",
    ) -> Section:
        """Write a single section with context from previous sections.

        Args:
            section_name: Name of the section to write.
            previous_sections: Already written sections for continuity.
            reference_context: Pre-formatted reference context from ReferenceContextManager.

        Returns:
            The generated Section object.
        """
        # Build context from previous sections
        previous_context = ""
        if previous_sections:
            previous_context = "\n\nSECCIONES ANTERIORES DEL PAPER (para mantener coherencia):\n"
            for sec in previous_sections:
                # Truncate long sections to avoid token limits
                content = sec.content[:1500] + "..." if len(sec.content) > 1500 else sec.content
                previous_context += f"\n### {sec.title}\n{content}\n"

        # Section-specific instructions
        section_instructions = self._get_section_instructions(section_name)

        user_prompt = f"""Escribe la sección '{section_name}' para un artículo de perspectivas académico.

{section_instructions}
{previous_context}
{reference_context}

REQUISITOS:
- Escribe en español académico formal
- Sé exhaustivo pero conciso
- Mantén coherencia con las secciones anteriores y el abstract
- Incluye análisis crítico y reflexivo apropiado para un paper de perspectivas
- Cita las referencias proporcionadas cuando sea relevante (usa el formato: Autor, Año)
- No incluyas el título de la sección, solo el contenido

Escribe únicamente el contenido de esta sección:"""

        content = self._call_api(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=4096,
        )

        return Section(title=section_name, content=content.strip())

    def _get_section_instructions(self, section_name: str) -> str:
        """Get specific writing instructions for each section type.

        Args:
            section_name: The name of the section.

        Returns:
            Specific instructions for that section type.
        """
        instructions = {
            "Introducción": """
INSTRUCCIONES PARA INTRODUCCIÓN:
- Presenta el contexto general del tema
- Establece la relevancia y actualidad del problema
- Enuncia claramente los objetivos del artículo
- Proporciona una visión general de la estructura del paper""",

            "Estado Actual del Arte": """
INSTRUCCIONES PARA ESTADO DEL ARTE:
- Revisa la literatura existente relevante
- Identifica las principales corrientes de investigación
- Sintetiza los avances más significativos
- Establece el marco teórico sobre el que se construye la perspectiva""",

            "Identificación del Problema o Brecha": """
INSTRUCCIONES PARA IDENTIFICACIÓN DEL PROBLEMA:
- Identifica claramente las limitaciones del conocimiento actual
- Señala las brechas en la investigación existente
- Argumenta por qué estas brechas son significativas
- Justifica la necesidad de una nueva perspectiva""",

            "La Nueva Perspectiva": """
INSTRUCCIONES PARA LA NUEVA PERSPECTIVA:
- Presenta la propuesta central del artículo
- Desarrolla los argumentos que sustentan esta perspectiva
- Diferencia esta visión de las aproximaciones existentes
- Proporciona evidencia o razonamiento que la respalde""",

            "Discusión": """
INSTRUCCIONES PARA DISCUSIÓN:
- Analiza las implicaciones de la perspectiva propuesta
- Contrasta con visiones alternativas
- Desarrolla argumentos a favor y posibles contraargumentos
- Conecta con el contexto más amplio del campo""",

            "Implicaciones Futuras": """
INSTRUCCIONES PARA IMPLICACIONES FUTURAS:
- Describe cómo esta perspectiva puede guiar investigación futura
- Propone direcciones concretas de desarrollo
- Establece una hoja de ruta para el campo
- Identifica oportunidades de innovación""",

            "Desafíos y Limitaciones": """
INSTRUCCIONES PARA DESAFÍOS Y LIMITACIONES:
- Reconoce honestamente las limitaciones de la perspectiva
- Identifica desafíos técnicos, metodológicos o conceptuales
- Discute posibles obstáculos para la implementación
- Sugiere formas de abordar estas limitaciones""",

            "Conclusiones": """
INSTRUCCIONES PARA CONCLUSIONES:
- Resume los puntos principales del artículo
- Reafirma la importancia de la perspectiva propuesta
- Proporciona un mensaje final memorable
- Conecta con las implicaciones más amplias""",

            "Declaración de Conflicto de Intereses": """
INSTRUCCIONES PARA CONFLICTO DE INTERESES:
- Incluye una declaración estándar de conflicto de intereses
- Mantén un tono formal y profesional""",

            "Agradecimientos": """
INSTRUCCIONES PARA AGRADECIMIENTOS:
- Genera un placeholder para agradecimientos
- Menciona fuentes de financiación típicas
- Incluye agradecimientos a colaboradores""",

            "Referencias Bibliográficas": """
INSTRUCCIONES PARA REFERENCIAS:
- Genera un placeholder indicando que las referencias se añadirán
- Sugiere el formato de citación apropiado (APA, IEEE, etc.)""",
        }

        return instructions.get(section_name, f"""
INSTRUCCIONES PARA {section_name.upper()}:
- Desarrolla el contenido de forma académica y rigurosa
- Mantén coherencia con el resto del documento
- Incluye análisis crítico apropiado""")

    def expand_section(self, paper: Paper, section_title: str) -> Paper:
        """Expand a specific section with more detail.

        Args:
            paper: The paper containing the section.
            section_title: The title of the section to expand.

        Returns:
            Updated paper with expanded section.
        """
        for section in paper.sections:
            if section.title.lower() == section_title.lower():
                user_prompt = f"""Expand the following section from an academic paper titled "{paper.title}".

Current content:
{section.content}

Requirements:
- Add more detail, examples, and analysis
- Maintain academic tone and style
- Ensure logical flow
- Approximately double the content length

Write only the expanded content."""

                expanded_content = self._call_api(
                    system_prompt=self.system_prompt,
                    user_prompt=user_prompt,
                )
                section.content = expanded_content.strip()
                break

        return paper

    def write_paragraph(
        self,
        key_idea: str,
        supporting_points: list[str],
        section_name: str,
        section_purpose: str,
        previous_paragraphs: list[str],
        reference_context: str,
        thesis: str,
        memory_context: str = "",
    ) -> str:
        """Write a single paragraph based on a specific key idea.
        
        This method is designed for the advanced orchestrator's
        paragraph-by-paragraph writing approach.
        
        Args:
            key_idea: The main idea this paragraph should develop.
            supporting_points: Additional points to cover.
            section_name: Name of the section.
            section_purpose: Purpose of the section.
            previous_paragraphs: Already written paragraphs in this section.
            reference_context: Context from embeddings search.
            thesis: Paper's thesis statement.
            memory_context: Summaries of previous sections for coherence.
            
        Returns:
            Written paragraph text.
        """
        previous_text = "\n\n".join(previous_paragraphs) if previous_paragraphs else ""
        
        supporting_text = ""
        if supporting_points:
            supporting_text = "\n".join(f"- {p}" for p in supporting_points)
        
        # Build memory section only if we have previous sections
        memory_section = ""
        if memory_context:
            memory_section = f"""
# CONTEXTO DE SECCIONES ANTERIORES
(Resúmenes para mantener coherencia con lo ya escrito)
{memory_context}
"""
        
        user_prompt = f"""Escribe UN SOLO PÁRRAFO académico para la sección "{section_name}".

# TESIS DEL PAPER
{thesis}

# PROPÓSITO DE LA SECCIÓN
{section_purpose}

# IDEA CLAVE A DESARROLLAR EN ESTE PÁRRAFO
{key_idea}

# PUNTOS DE APOYO A INCORPORAR
{supporting_text}
{memory_section}
# PÁRRAFOS ANTERIORES EN ESTA SECCIÓN
{previous_text if previous_text else "(Este es el primer párrafo de la sección)"}

# CONTEXTO DE LA LITERATURA
{reference_context if reference_context else "(Sin contexto adicional)"}

# INSTRUCCIONES
1. Escribe ÚNICAMENTE un párrafo coherente (4-8 oraciones)
2. Desarrolla la IDEA CLAVE como argumento central del párrafo
3. Incorpora los puntos de apoyo de forma natural
4. Cita la literatura proporcionada cuando sea relevante
5. Asegura transición fluida desde el párrafo anterior
6. Mantén consistencia con la tesis del paper y las secciones anteriores
7. Escribe en español académico formal

Escribe SOLO el párrafo, sin títulos ni comentarios adicionales."""

        paragraph = self._call_api(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
        )
        
        return paragraph.strip()
