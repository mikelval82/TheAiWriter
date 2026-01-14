"""Agent for extracting structured data from PDF text using LLM."""

import json
import re
from typing import Any

from ai_writer.agents.base_agent import BaseAgent
from ai_writer.processors.models import (
    Claim,
    Idea,
    PaperMetadata,
    Reference,
    SectionData,
)
from config.settings import settings


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
        """Identify and segment the paper into sections.
        
        Args:
            text: Full paper text.
            
        Returns:
            List of sections with name and content.
        """
        prompt = f"""Analyze this academic paper and identify its sections.

TEXT:
{text[:50000]}

Identify the main sections (Abstract, Introduction, Related Work, Methodology, 
Results, Discussion, Conclusion, References, etc.) and return as JSON array:

[
    {{
        "section_name": "Abstract",
        "section_number": 1,
        "content": "The full text content of this section..."
    }},
    ...
]

Important:
- Include the full content of each section
- Preserve paragraph structure
- Do not include References section content (just mark it exists)
- Section names should be standardized (e.g., "Related Work" not "2.1 Previous Studies")

Return ONLY the JSON array, no other text."""

        response = self._call_api(self.system_prompt, prompt, max_tokens=16000)
        return self._parse_json_response(response, default=[])

    def extract_ideas_from_section(
        self,
        section_name: str,
        section_content: str,
        paper_title: str,
        authors: list[str],
        year: int | None,
        paper_id: str,
    ) -> list[Idea]:
        """Extract main ideas from a section.
        
        Args:
            section_name: Name of the section.
            section_content: Text content of the section.
            paper_title: Title of the paper.
            authors: List of authors.
            year: Publication year.
            paper_id: Unique paper identifier.
            
        Returns:
            List of Idea objects.
        """
        prompt = f"""Analyze this section from an academic paper and extract the MAIN IDEAS.

PAPER: {paper_title}
SECTION: {section_name}

CONTENT:
{section_content[:12000]}

Extract 3-7 main ideas from this section. For each idea, provide:

[
    {{
        "idea": "Clear, concise statement of the main idea (1-2 sentences)",
        "context": "Brief quote or paraphrase providing context",
        "importance": "high|medium|low",
        "keywords": ["keyword1", "keyword2", ...],
        "related_references": ["Author2024", "Smith2023", ...] (if mentioned)
    }},
    ...
]

Focus on:
- Novel contributions and claims
- Key arguments and findings
- Important definitions or frameworks
- Significant conclusions

Return ONLY the JSON array, no other text."""

        response = self._call_api(self.system_prompt, prompt, max_tokens=4000)
        ideas_data = self._parse_json_response(response, default=[])
        
        ideas = []
        for data in ideas_data:
            ideas.append(Idea(
                paper_id=paper_id,
                paper_title=paper_title,
                authors=authors,
                year=year,
                section=section_name,
                idea=data.get("idea", ""),
                context=data.get("context", ""),
                importance=data.get("importance", "medium"),
                keywords=data.get("keywords", []),
                related_references=data.get("related_references", []),
            ))
        
        return ideas

    def extract_claims_from_section(
        self,
        section_name: str,
        section_content: str,
        paper_title: str,
        paper_id: str,
    ) -> list[Claim]:
        """Extract claims with evidence from a section.
        
        Args:
            section_name: Name of the section.
            section_content: Text content of the section.
            paper_title: Title of the paper.
            paper_id: Unique paper identifier.
            
        Returns:
            List of Claim objects.
        """
        prompt = f"""Analyze this section and extract CLAIMS WITH EVIDENCE.

PAPER: {paper_title}
SECTION: {section_name}

CONTENT:
{section_content[:12000]}

Extract claims that are supported by evidence (citations, data, experiments).

[
    {{
        "claim": "The specific assertion being made",
        "evidence": "The supporting evidence or citation",
        "evidence_type": "citation|data|experiment|observation",
        "cited_references": ["Author2024", ...],
        "confidence": "high|medium|low"
    }},
    ...
]

Focus on:
- Claims backed by citations
- Statistical findings
- Experimental results
- Comparative analyses

Return ONLY the JSON array, no other text."""

        response = self._call_api(self.system_prompt, prompt, max_tokens=4000)
        claims_data = self._parse_json_response(response, default=[])
        
        claims = []
        for data in claims_data:
            claims.append(Claim(
                paper_id=paper_id,
                paper_title=paper_title,
                section=section_name,
                claim=data.get("claim", ""),
                evidence=data.get("evidence", ""),
                evidence_type=data.get("evidence_type", "citation"),
                cited_references=data.get("cited_references", []),
                confidence=data.get("confidence", "medium"),
            ))
        
        return claims

    def extract_references(
        self,
        references_text: str,
        paper_id: str,
    ) -> list[Reference]:
        """Extract structured references from the references section.
        
        Args:
            references_text: Text of the references section.
            paper_id: Unique paper identifier.
            
        Returns:
            List of Reference objects.
        """
        # Clean up the text - rejoin lines that were split
        cleaned_text = references_text.replace("\n", " ").replace("  ", " ")
        
        prompt = f"""Parse this bibliography/references section from an academic paper.
The text may have formatting issues from PDF extraction - please parse it carefully.

REFERENCES TEXT:
{cleaned_text[:18000]}

For each reference, extract:

[
    {{
        "citation_key": "[1] or Author2024 format",
        "full_citation": "Complete citation as written",
        "authors": ["Last, First", ...],
        "title": "Paper/book title",
        "year": 2024,
        "doi": "10.xxxx/xxxxx or null",
        "venue": "Journal/Conference name or null"
    }},
    ...
]

Parse as many references as possible. Use null for fields you cannot determine.

Return ONLY the JSON array, no other text."""

        response = self._call_api(self.system_prompt, prompt, max_tokens=8000)
        refs_data = self._parse_json_response(response, default=[])
        
        references = []
        for data in refs_data:
            references.append(Reference(
                source_paper_id=paper_id,
                citation_key=data.get("citation_key", ""),
                full_citation=data.get("full_citation", ""),
                authors=data.get("authors", []),
                title=data.get("title", ""),
                year=data.get("year"),
                doi=data.get("doi"),
                venue=data.get("venue"),
            ))
        
        return references

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
