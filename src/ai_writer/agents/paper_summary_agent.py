"""Agent for summarizing academic papers using GPT-5.1/GPT-5."""

from ai_writer.agents.base_agent import BaseAgent
from config.settings import settings


class PaperSummaryAgent(BaseAgent):
    """Agent specialized in summarizing academic papers with deep reasoning."""

    SUMMARY_TEMPLATE = """# {title}

## Metadata
- **Autores**: {authors}
- **Año**: {year}
- **Keywords**: {keywords}

## Abstract
{abstract}

## Contribuciones Principales
{contributions}

## Metodología
{methodology}

## Resultados Clave
{results}

## Limitaciones
{limitations}

## Trabajo Futuro
{future_work}

## Citas Relevantes
{quotes}

## Notas Adicionales
{notes}
"""

    def __init__(self, use_reasoning: bool = True) -> None:
        """Initialize the agent with GPT-5.1 or GPT-5.

        Args:
            use_reasoning: If True, uses GPT-5 with reasoning for complex analysis.
                          If False, uses GPT-5.1 for standard summarization.
        """
        model = settings.ai.reasoning_model if use_reasoning else settings.ai.default_model
        super().__init__(model=model)
        self.use_reasoning = use_reasoning

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for paper summarization."""
        return """Eres un experto investigador académico especializado en analizar y resumir papers científicos.

Tu tarea es extraer la información más relevante de un paper académico y generar un resumen estructurado y completo.

INSTRUCCIONES:
1. Lee el paper completo cuidadosamente
2. Identifica las secciones clave: Abstract, Introducción, Metodología, Resultados, Discusión, Conclusiones
3. Extrae la información siguiendo el formato estructurado solicitado
4. Sé preciso y conciso, pero no omitas información importante
5. Usa bullet points para listas
6. Incluye citas textuales relevantes cuando sean significativas
7. Si alguna sección no está clara o no existe en el paper, indícalo explícitamente

FORMATO DE SALIDA:
Debes responder SIEMPRE en formato JSON con la siguiente estructura:
{
    "title": "Título completo del paper",
    "authors": "Lista de autores separados por coma",
    "year": "Año de publicación (si está disponible)",
    "keywords": "Keywords separadas por coma",
    "abstract": "Resumen del abstract en español",
    "contributions": "- Contribución 1\\n- Contribución 2\\n...",
    "methodology": "Descripción detallada de la metodología",
    "results": "- Resultado 1\\n- Resultado 2\\n...",
    "limitations": "- Limitación 1\\n- Limitación 2\\n...",
    "future_work": "- Trabajo futuro 1\\n- Trabajo futuro 2\\n...",
    "quotes": "- \\"Cita relevante 1\\"\\n- \\"Cita relevante 2\\"\\n...",
    "notes": "Observaciones adicionales sobre el paper"
}

IMPORTANTE:
- Responde SOLO con el JSON, sin texto adicional
- Asegúrate de que el JSON sea válido
- Escribe el resumen en ESPAÑOL
- Mantén las citas textuales en su idioma original (generalmente inglés)"""

    def summarize(self, paper_text: str) -> str:
        """Generate a structured summary of an academic paper.

        Args:
            paper_text: The full text content of the paper.

        Returns:
            Structured markdown summary of the paper.
        """
        import json

        user_prompt = f"""Analiza el siguiente paper académico y genera un resumen estructurado completo.

PAPER:
{paper_text}

Recuerda responder SOLO con el JSON estructurado."""

        # Use higher max_tokens for comprehensive summaries
        response = self._call_api(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=8192,
            temperature=0.0,
        )

        # Parse JSON response and format as markdown
        try:
            # Clean response if it has markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]

            data = json.loads(clean_response.strip())

            return self.SUMMARY_TEMPLATE.format(
                title=data.get("title", "Sin título"),
                authors=data.get("authors", "No especificados"),
                year=data.get("year", "No especificado"),
                keywords=data.get("keywords", "No especificadas"),
                abstract=data.get("abstract", "No disponible"),
                contributions=data.get("contributions", "No especificadas"),
                methodology=data.get("methodology", "No especificada"),
                results=data.get("results", "No especificados"),
                limitations=data.get("limitations", "No especificadas"),
                future_work=data.get("future_work", "No especificado"),
                quotes=data.get("quotes", "No hay citas destacadas"),
                notes=data.get("notes", "Sin notas adicionales"),
            )
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw response with basic formatting
            return f"# Resumen del Paper\n\n{response}"

    def summarize_with_context(self, paper_text: str, research_context: str) -> str:
        """Generate a summary with additional research context.

        Args:
            paper_text: The full text content of the paper.
            research_context: Context about the broader research project.

        Returns:
            Structured markdown summary with relevance analysis.
        """
        import json

        extended_prompt = f"""Analiza el siguiente paper académico y genera un resumen estructurado completo.

CONTEXTO DE INVESTIGACIÓN:
{research_context}

PAPER:
{paper_text}

Además de la estructura estándar, incluye en "notes" cómo este paper se relaciona con el contexto de investigación proporcionado.

Recuerda responder SOLO con el JSON estructurado."""

        response = self._call_api(
            system_prompt=self.system_prompt,
            user_prompt=extended_prompt,
            max_tokens=8192,
            temperature=0.0,
        )

        try:
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]

            data = json.loads(clean_response.strip())

            return self.SUMMARY_TEMPLATE.format(
                title=data.get("title", "Sin título"),
                authors=data.get("authors", "No especificados"),
                year=data.get("year", "No especificado"),
                keywords=data.get("keywords", "No especificadas"),
                abstract=data.get("abstract", "No disponible"),
                contributions=data.get("contributions", "No especificadas"),
                methodology=data.get("methodology", "No especificada"),
                results=data.get("results", "No especificados"),
                limitations=data.get("limitations", "No especificadas"),
                future_work=data.get("future_work", "No especificado"),
                quotes=data.get("quotes", "No hay citas destacadas"),
                notes=data.get("notes", "Sin notas adicionales"),
            )
        except json.JSONDecodeError:
            return f"# Resumen del Paper\n\n{response}"
