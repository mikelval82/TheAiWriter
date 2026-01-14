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
        # First, identify section structure
        structure = self._identify_section_structure(text)
        
        # Then extract content for each section
        sections = self._extract_section_contents(text, structure)
        
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

        response = self._call_api(self.system_prompt, prompt, max_tokens=2000)
        return self._parse_json_response(response, default=[])

    def _extract_section_contents(
        self,
        text: str,
        structure: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Extract content for each identified section.
        
        Args:
            text: Full paper text.
            structure: List of section names and numbers.
            
        Returns:
            List of sections with full content.
        """
        import re
        
        sections = []
        section_names = [s.get("section_name", "") for s in structure]
        
        for i, sec_info in enumerate(structure):
            section_name = sec_info.get("section_name", f"Section {i+1}")
            section_num = sec_info.get("section_number", i + 1)
            
            # Try to find section boundaries using regex
            # Build pattern for current section
            escaped_name = re.escape(section_name)
            pattern = rf'(?:^|\n)\s*(?:\d+\.?\s*)?{escaped_name}\s*\n'
            
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start_pos = match.end()
                
                # Find next section start
                end_pos = len(text)
                next_section_name = section_names[i + 1] if i + 1 < len(section_names) else "References"
                escaped_next = re.escape(next_section_name)
                next_pattern = rf'(?:^|\n)\s*(?:\d+\.?\s*)?{escaped_next}\s*\n'
                next_match = re.search(next_pattern, text[start_pos:], re.IGNORECASE)
                
                if next_match:
                    end_pos = start_pos + next_match.start()
                else:
                    # Try to find References as end boundary
                    ref_match = re.search(r'\n\s*References\s*\n', text[start_pos:], re.IGNORECASE)
                    if ref_match:
                        end_pos = start_pos + ref_match.start()
                
                content = text[start_pos:end_pos].strip()
                
                # Clean up content
                content = self._clean_section_content(content)
            else:
                # Fallback: use LLM to extract
                content = self._extract_section_with_llm(text, section_name)
            
            sections.append({
                "section_name": section_name,
                "section_number": section_num,
                "content": content,
            })
        
        return sections

    def _clean_section_content(self, content: str) -> str:
        """Clean section content from PDF artifacts.
        
        Args:
            content: Raw section content.
            
        Returns:
            Cleaned content.
        """
        import re
        
        # Remove page markers
        content = re.sub(r'---\s*Page\s*\d+\s*---', '', content)
        # Remove repeated header/footer lines
        content = re.sub(r'Published in [^\n]+\n', '', content)
        # Normalize whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()

    def _extract_section_with_llm(self, text: str, section_name: str) -> str:
        """Use LLM to extract a specific section when regex fails.
        
        Args:
            text: Full paper text.
            section_name: Name of section to extract.
            
        Returns:
            Section content.
        """
        prompt = f"""Find and extract the "{section_name}" section from this academic paper.

TEXT:
{text[:60000]}

Return ONLY the content of the "{section_name}" section, nothing else.
If the section doesn't exist in the paper, return "SECTION_NOT_FOUND"."""

        response = self._call_api(self.system_prompt, prompt, max_tokens=8000)
        
        if "SECTION_NOT_FOUND" in response:
            return ""
        
        return response.strip()
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
        # Clean up the text - rejoin lines that were split by PDF extraction
        cleaned_text = self._clean_references_text(references_text)
        
        # Split into logical chunks by finding reference boundaries
        # Each chunk should contain complete references
        chunks = self._split_references_into_chunks(cleaned_text, max_chunk_size=8000)
        
        all_references = []
        for chunk in chunks:
            if not chunk.strip():
                continue
            refs = self._extract_references_chunk(chunk, paper_id)
            all_references.extend(refs)
        
        return all_references

    def _split_references_into_chunks(self, text: str, max_chunk_size: int = 8000) -> list[str]:
        """Split references text into chunks at reference boundaries.
        
        Args:
            text: Cleaned references text.
            max_chunk_size: Maximum size of each chunk.
            
        Returns:
            List of text chunks, each containing complete references.
        """
        import re
        
        # Split by lines that look like reference starts
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            
            # Check if this is a new reference start and we're near the limit
            is_ref_start = bool(re.match(
                r'^[A-Z][a-z]+,?\s+[A-Z]\.?|^\[[0-9]+\]|^[A-Z]\.\s+[A-Z]',
                line.strip()
            ))
            
            if current_size + line_size > max_chunk_size and current_chunk and is_ref_start:
                # Save current chunk and start new one
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks

    def _clean_references_text(self, text: str) -> str:
        """Clean up references text from PDF extraction artifacts.
        
        Args:
            text: Raw text from PDF.
            
        Returns:
            Cleaned text with references properly formatted.
        """
        import re
        
        # Remove page markers
        text = re.sub(r'---\s*Page\s*\d+\s*---', '\n', text)
        
        # Remove header/footer artifacts (journal info repeated)
        text = re.sub(r'Published in [^\n]+\n', '\n', text)
        
        # Normalize whitespace but preserve paragraph breaks
        lines = text.split('\n')
        cleaned_lines = []
        current_ref = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_ref:
                    cleaned_lines.append(' '.join(current_ref))
                    current_ref = []
                continue
            
            # Check if this looks like a new reference start
            # (starts with author name pattern, number, or bracket)
            is_new_ref = bool(re.match(
                r'^(\[[0-9]+\]|[A-Z][a-z]+,?\s+[A-Z]\.?|[A-Z]\.\s+[A-Z])',
                line
            ))
            
            if is_new_ref and current_ref:
                cleaned_lines.append(' '.join(current_ref))
                current_ref = [line]
            else:
                current_ref.append(line)
        
        if current_ref:
            cleaned_lines.append(' '.join(current_ref))
        
        return '\n'.join(cleaned_lines)

    def _extract_references_chunk(
        self,
        chunk: str,
        paper_id: str,
    ) -> list[Reference]:
        """Extract references from a chunk of text.
        
        Args:
            chunk: Cleaned text chunk containing references.
            paper_id: Unique paper identifier.
            
        Returns:
            List of Reference objects.
        """
        prompt = f"""You are parsing a bibliography section from an academic paper.
Extract ALL references you can find in this text.

TEXT:
{chunk}

For EACH reference found, extract:
{{
    "citation_key": "AuthorYear format (e.g., 'Smith2024') or number '[1]'",
    "full_citation": "The complete citation text as it appears",
    "authors": ["Surname, FirstName", ...],
    "title": "Title of the paper/book",
    "year": 2024,
    "doi": "DOI if present, null otherwise",
    "venue": "Journal, Conference, or arXiv"
}}

IMPORTANT:
- Extract EVERY reference, even if some fields are unclear
- For arXiv papers, use "arXiv" as venue
- Generate citation_key from first author surname + year
- Return a JSON array with all references

Return ONLY a valid JSON array, no explanation."""

        response = self._call_api(self.system_prompt, prompt, max_tokens=8000)
        refs_data = self._parse_json_response(response, default=[])
        
        references = []
        for data in refs_data:
            if not data.get("full_citation") and not data.get("title"):
                continue  # Skip empty entries
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
