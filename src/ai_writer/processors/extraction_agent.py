"""Agent for extracting structured data from PDF text using LLM."""

import json
import re
from typing import Any

from ai_writer.agents.base_agent import BaseAgent
from ai_writer.processors.models import Claim, Idea
from ai_writer.processors.segmentation import segment
from config.settings import settings


STRUCTURE_ATTEMPTS = 3  # tries at finding the sections before giving up
SECTION_ATTEMPTS = 3  # tries at getting a readable answer for one segment
IDEA_KINDS = ("finding", "concept", "method", "limitation", "proposal", "background")


class ExtractionError(RuntimeError):
    """The model never returned a readable answer for a segment."""


def _idea_kind(value: Any) -> str | None:
    """The idea's kind if it is one of IDEA_KINDS, else None."""
    kind = str(value or "").strip().lower()
    return kind if kind in IDEA_KINDS else None


def _safe_get(data: dict, key: str, default: Any = "") -> Any:
    """Get value from dict, treating None as missing.
    
    Unlike dict.get(), this returns the default if the value is None.
    This handles LLM responses that explicitly return null for fields.
    """
    value = data.get(key)
    if value is None:
        return default
    return value


def _safe_get_list(data: dict, key: str) -> list:
    """Get list from dict, treating None as empty list."""
    value = data.get(key)
    if value is None or not isinstance(value, list):
        return []
    return value


class PDFExtractionAgent(BaseAgent):
    """Agent for extracting structured information from paper text."""

    def __init__(self) -> None:
        """Initialize with the default model."""
        super().__init__(model=settings.ai.default_model)

    @property
    def system_prompt(self) -> str:
        """System prompt for extraction tasks."""
        return """You are an expert academic paper analyzer. Your task is to extract 
structured information from academic papers with high precision and accuracy.

You must always respond with valid JSON that matches the requested schema exactly.
Be thorough but concise. Extract only what is explicitly stated or strongly implied."""

    def extract_metadata(self, text: str, filename: str) -> dict[str, Any]:
        """Extract paper metadata from the first pages.
        
        Args:
            text: Text from the first few pages of the paper.
            filename: Original filename for fallback title.
            
        Returns:
            Dictionary with metadata fields.
        """
        prompt = f"""Analyze this academic paper text and extract metadata.

TEXT:
{text[:8000]}

FILENAME: {filename}

Extract and return as JSON:
{{
    "title": "Full paper title",
    "authors": ["Author 1", "Author 2", ...],
    "year": 2024,
    "doi": "10.xxxx/xxxxx or null if not found",
    "venue": "Journal or Conference name or null"
}}

If you cannot find a field, use null. For authors, extract full names when possible.
Return ONLY the JSON, no other text."""

        response = self._call_api(self.system_prompt, prompt, max_tokens=1000)
        return self._parse_json_response(response)

    def extract_sections(self, text: str) -> list[dict[str, Any]]:
        """Cut the paper into non-overlapping segments, one per extraction pass.

        The model only names the sections; the cutting is done by ``segment``, which
        falls back to size-based pieces when the model finds no usable structure.

        Args:
            text: Full paper text.

        Returns:
            List of sections with name, number and content.
        """
        structure = self._identify_section_structure(text)
        names = [
            str(item["section_name"])
            for item in structure
            if isinstance(item, dict) and item.get("section_name")
        ]

        sections = []
        for piece in segment(text, names):
            content = self.clean_text(piece.content)
            if content:
                sections.append({
                    "section_name": piece.name,
                    "section_number": piece.number,
                    "content": content,
                })
        return sections

    def _identify_section_structure(self, text: str) -> list[dict[str, Any]]:
        """Identify the section structure of the paper.
        
        Args:
            text: Full paper text.
            
        Returns:
            List of section names and approximate positions.
        """
        prompt = f"""Analyze this academic paper and identify its section structure.

TEXT (first 40000 chars):
{text[:40000]}

... (paper continues) ...

TEXT (last 15000 chars):
{text[-15000:]}

List ALL sections found in the paper with their names. Return as JSON:

[
    {{"section_name": "Abstract", "section_number": 1}},
    {{"section_name": "Introduction", "section_number": 2}},
    ...
]

Important:
- Use the ACTUAL section names from the paper
- Include all sections except References
- Preserve the original numbering if present
- Common sections: Abstract, Introduction, Background, Related Work, Methodology, Framework, Case Studies, Experiments, Results, Discussion, Conclusion

Return ONLY the JSON array."""

        # An unreadable answer comes back now and then; without sections the paper
        # yields no ideas, so ask again before giving up
        for _ in range(STRUCTURE_ATTEMPTS):
            response = self._call_api(self.system_prompt, prompt, max_tokens=2000)
            structure = self._parse_json_response(response, default=[])
            if isinstance(structure, list) and structure:
                return structure
        return []

    def clean_text(self, content: str) -> str:
        """Clean paper text from PDF artifacts.
        
        Args:
            content: Raw text.
            
        Returns:
            Cleaned text.
        """
        # Remove page markers
        content = re.sub(r'---\s*Page\s*\d+\s*---', '', content)
        # Remove repeated header/footer lines
        content = re.sub(r'Published in [^\n]+\n', '', content)
        # Normalize whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()

    def extract_from_section(
        self,
        section_name: str,
        section_content: str,
        paper_title: str,
        authors: list[str],
        year: int | None,
        paper_id: str,
    ) -> tuple[list[Idea], list[Claim]]:
        """Extract the ideas and the claims of a segment in one call.

        Every item carries a ``quote``; checking it against the paper is up to the caller.

        Args:
            section_name: Name of the segment.
            section_content: Text content of the segment.
            paper_title: Title of the paper.
            authors: List of authors.
            year: Publication year.
            paper_id: Unique paper identifier.

        Returns:
            The Idea and the Claim objects.

        Raises:
            ExtractionError: If no attempt returned readable JSON.
        """
        prompt = f"""Analyze this section from an academic paper and extract its MAIN IDEAS and its CLAIMS WITH EVIDENCE.

PAPER: {paper_title}
SECTION: {section_name}

CONTENT:
{section_content}

Return ONE JSON object with two lists:

{{
    "ideas": [
        {{
            "idea": "Clear, concise statement of the main idea (1-2 sentences)",
            "context": "Short explanation that situates the idea",
            "quote": "Sentence copied verbatim from the CONTENT that states the idea",
            "kind": "finding|concept|method|limitation|proposal|background",
            "importance": "high|medium|low",
            "keywords": ["keyword1", "keyword2", ...],
            "related_references": ["Author2024", "Smith2023", ...] (if mentioned)
        }}
    ],
    "claims": [
        {{
            "claim": "The specific assertion being made",
            "evidence": "The supporting evidence or citation",
            "evidence_type": "experiment|data|observation|citation",
            "quote": "Sentence copied verbatim from the CONTENT that states the claim",
            "cited_references": ["Author2024", ...],
            "confidence": "high|medium|low"
        }}
    ]
}}

IDEAS: extract up to 7 main ideas (fewer when the section is short, none when it has no substance). Focus on:
- Novel contributions and claims
- Key arguments and findings
- Important definitions or frameworks
- Significant conclusions

Set "kind" of each idea to exactly one of:
- finding: a result or conclusion of the paper
- concept: a definition, framework, model or theoretical position
- method: how the study was done (procedure, materials, datasets, apparatus, features, metrics, implementation details)
- limitation: a limitation, gap, risk or open problem
- proposal: something the paper proposes or recommends
- background: context from prior work

CLAIMS: extract up to 10 claims that are supported by evidence. Focus on:
- Claims backed by citations
- Statistical findings
- Experimental results
- Comparative analyses
Set evidence_type to "experiment" for the paper's own experiments or studies, "data" for its own quantitative or statistical findings, "observation" for its own qualitative observations or arguments, and "citation" when the support is another work that the paper cites.

QUOTES (required for every idea and every claim):
- Copy ONE sentence, or one contiguous passage, from the CONTENT that states the idea or the claim, character by character, between 8 and 40 words.
- Do not paraphrase, translate, add words or edit with brackets. Keep the language of the paper.
- The ellipsis "…" is allowed only to drop the middle of a long sentence.
- Items whose quote is not found verbatim in the text are DISCARDED, so copy exactly. If you cannot back an item with a quote, leave that item out.

Return ONLY the JSON object, no other text."""

        for _ in range(SECTION_ATTEMPTS):
            response = self._call_api(self.system_prompt, prompt, max_tokens=8000)
            data = self._parse_json_response(response)
            if isinstance(data, dict) and ("ideas" in data or "claims" in data):
                break
        else:
            raise ExtractionError(
                f"Respuesta ilegible del modelo para el tramo «{section_name}» "
                f"tras {SECTION_ATTEMPTS} intentos"
            )

        ideas = []
        for item in _safe_get_list(data, "ideas"):
            if not isinstance(item, dict) or not _safe_get(item, "idea"):
                continue
            ideas.append(Idea(
                paper_id=paper_id,
                paper_title=paper_title,
                authors=authors,
                year=year,
                section=section_name,
                idea=item["idea"],
                context=_safe_get(item, "context"),
                kind=_idea_kind(item.get("kind")),
                importance=_safe_get(item, "importance", "medium"),
                keywords=_safe_get_list(item, "keywords"),
                related_references=_safe_get_list(item, "related_references"),
                quote=str(_safe_get(item, "quote")),
            ))

        claims = []
        for item in _safe_get_list(data, "claims"):
            if not isinstance(item, dict) or not _safe_get(item, "claim"):
                continue
            claims.append(Claim(
                paper_id=paper_id,
                paper_title=paper_title,
                section=section_name,
                claim=item["claim"],
                evidence=str(_safe_get(item, "evidence")),
                evidence_type=str(_safe_get(item, "evidence_type", "observation")),
                cited_references=_safe_get_list(item, "cited_references"),
                confidence=_safe_get(item, "confidence", "medium"),
                quote=str(_safe_get(item, "quote")),
            ))

        return ideas, claims

    def _parse_json_response(
        self,
        response: str,
        default: Any = None,
    ) -> Any:
        """Parse JSON from LLM response, handling common issues.
        
        Args:
            response: Raw LLM response.
            default: Default value if parsing fails.
            
        Returns:
            Parsed JSON or default value.
        """
        if default is None:
            default = {}
            
        # Clean up response
        text = response.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        
        # Try to find JSON in the response
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from the text
            json_match = re.search(r"[\[{].*[}\]]", text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
        
        return default
