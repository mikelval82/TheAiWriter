"""Parser for structured markdown references."""

import re
from pathlib import Path

from ai_writer.models.reference import ParsedReference


class ReferenceParser:
    """Parser for structured markdown reference files."""

    # Section headers to look for (in Spanish and English)
    SECTION_PATTERNS = {
        "title": r"^#\s+(.+)$",
        "authors": r"\*\*Autores?\*\*:\s*(.+)",
        "year": r"\*\*Año\*\*:\s*(.+)",
        "keywords": r"\*\*Keywords?\*\*:\s*(.+)",
        "abstract": r"^##\s*Abstract\s*$",
        "contributions": r"^##\s*Contribuciones?\s*Principales?\s*$",
        "methodology": r"^##\s*Metodolog[íi]a\s*$",
        "results": r"^##\s*Resultados?\s*Claves?\s*$",
        "limitations": r"^##\s*Limitaciones?\s*$",
        "future_work": r"^##\s*Trabajo\s*Futuro\s*$",
        "quotes": r"^##\s*Citas?\s*Relevantes?\s*$",
        "notes": r"^##\s*Notas?\s*Adicionales?\s*$",
    }

    def parse(self, content: str, filename: str) -> ParsedReference:
        """Parse a structured markdown file into a ParsedReference.

        Args:
            content: The markdown content to parse.
            filename: The original filename.

        Returns:
            A ParsedReference object with extracted sections.
        """
        lines = content.split("\n")
        
        # Extract title from first H1
        title = ""
        for line in lines:
            match = re.match(self.SECTION_PATTERNS["title"], line)
            if match:
                title = match.group(1).strip()
                break

        # Extract metadata
        authors = self._extract_metadata(content, "authors")
        year = self._extract_metadata(content, "year")
        keywords = self._extract_metadata(content, "keywords")

        # Extract sections
        sections = self._extract_all_sections(content)

        return ParsedReference(
            filename=filename,
            title=title,
            authors=authors,
            year=year,
            keywords=keywords,
            abstract=sections.get("abstract", ""),
            contributions=sections.get("contributions", ""),
            methodology=sections.get("methodology", ""),
            results=sections.get("results", ""),
            limitations=sections.get("limitations", ""),
            future_work=sections.get("future_work", ""),
            quotes=sections.get("quotes", ""),
            notes=sections.get("notes", ""),
        )

    def _extract_metadata(self, content: str, field: str) -> str:
        """Extract a metadata field from content.

        Args:
            content: The full content.
            field: The field name to extract.

        Returns:
            The extracted value or empty string.
        """
        pattern = self.SECTION_PATTERNS.get(field, "")
        if not pattern:
            return ""
        
        match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_all_sections(self, content: str) -> dict[str, str]:
        """Extract all content sections from the markdown.

        Args:
            content: The full markdown content.

        Returns:
            Dictionary mapping section names to their content.
        """
        sections = {}
        lines = content.split("\n")
        
        current_section = None
        current_content = []
        
        section_headers = [
            ("abstract", r"^##\s*Abstract"),
            ("contributions", r"^##\s*Contribuciones?\s*Principales?"),
            ("methodology", r"^##\s*Metodolog[íi]a"),
            ("results", r"^##\s*Resultados?\s*Claves?"),
            ("limitations", r"^##\s*Limitaciones?"),
            ("future_work", r"^##\s*Trabajo\s*Futuro"),
            ("quotes", r"^##\s*Citas?\s*Relevantes?"),
            ("notes", r"^##\s*Notas?\s*Adicionales?"),
        ]

        for line in lines:
            # Check if this line starts a new section
            new_section = None
            for section_name, pattern in section_headers:
                if re.match(pattern, line, re.IGNORECASE):
                    new_section = section_name
                    break

            if new_section:
                # Save previous section if exists
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = new_section
                current_content = []
            elif current_section:
                # Skip if it's another H2 header (end of section)
                if re.match(r"^##\s+", line):
                    if current_content:
                        sections[current_section] = "\n".join(current_content).strip()
                    current_section = None
                    current_content = []
                else:
                    current_content.append(line)

        # Don't forget the last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def parse_file(self, file_path: Path) -> ParsedReference:
        """Parse a markdown file into a ParsedReference.

        Args:
            file_path: Path to the markdown file.

        Returns:
            A ParsedReference object.
        """
        content = file_path.read_text(encoding="utf-8")
        return self.parse(content, file_path.name)

    def parse_directory(self, directory: Path) -> list[ParsedReference]:
        """Parse all markdown files in a directory.

        Args:
            directory: Path to the directory containing markdown files.

        Returns:
            List of ParsedReference objects.
        """
        references = []
        for file_path in directory.glob("*.md"):
            # Skip ABSTRACT.md as it's the paper's own abstract
            if file_path.name.upper() == "ABSTRACT.MD":
                continue
            try:
                ref = self.parse_file(file_path)
                references.append(ref)
            except Exception as e:
                print(f"Warning: Failed to parse {file_path.name}: {e}")
        return references
