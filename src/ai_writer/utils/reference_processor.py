"""Reference processor for parsing citation markers and generating bibliography.

This module handles:
1. Parsing [@Author et al., Year] markers in text
2. Building a lookup dictionary from references index
3. Generating the final References section with full citations

Citation format: [@Author et al., 2020] or [@Smith & Jones, 2019]
This format is similar to Pandoc/BibTeX and easy for LLMs to generate.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()


@dataclass
class CitationMatch:
    """A matched citation in the text."""
    marker: str  # Full marker including \ref{...}
    key: str  # Citation key inside the marker
    start: int  # Start position in text
    end: int  # End position in text
    full_citation: str | None = None  # Full citation from references
    reference_number: int | None = None  # Assigned reference number


@dataclass
class ReferenceProcessor:
    """Processes citation markers and generates bibliography.
    
    Usage:
        processor = ReferenceProcessor(references_index_path)
        processor.load_references()
        
        # After paper is written:
        final_text = processor.process_paper(paper_text)
    """
    
    references_index_path: Path | None = None
    
    # Loaded reference data: citation_key -> full_citation
    # Keys are normalized to "Author et al., Year" format
    _references_dict: dict[str, dict[str, Any]] = field(default_factory=dict)
    
    # Track used references in order of appearance
    _used_references: list[dict[str, Any]] = field(default_factory=list)
    _used_keys: set[str] = field(default_factory=set)
    
    # Pattern to match [@...] markers (Pandoc-style citations)
    # Examples: [@Brown et al., 2020], [@Smith & Jones, 2019]
    REF_PATTERN = re.compile(r'\[@([^\]]+)\]')
    
    def __post_init__(self) -> None:
        """Initialize the reference dictionaries."""
        if not hasattr(self, '_references_dict') or self._references_dict is None:
            self._references_dict = {}
        if not hasattr(self, '_used_references') or self._used_references is None:
            self._used_references = []
        if not hasattr(self, '_used_keys') or self._used_keys is None:
            self._used_keys = set()
    
    def load_references(self, references_path: Path | None = None) -> int:
        """Load references from JSONL index file.
        
        Args:
            references_path: Path to all_references.jsonl or processed papers dir.
            
        Returns:
            Number of references loaded.
        """
        import json
        from config.settings import settings
        
        # Try to find references
        path = references_path or self.references_index_path
        
        if path is None:
            # Default paths
            jsonl_path = settings.paths.data_dir / "processed" / "indices" / "all_references.jsonl"
            if jsonl_path.exists():
                path = jsonl_path
        
        if path is None or not path.exists():
            console.print("[yellow]⚠ No references index found[/yellow]")
            return 0
        
        # Load JSONL file
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    ref_data = json.loads(line)
                    # Create multiple lookup keys for the same reference
                    keys = self._generate_lookup_keys(ref_data)
                    for key in keys:
                        self._references_dict[key] = ref_data
                    count += 1
        
        console.print(f"[green]✓ Cargadas {count} referencias[/green]")
        return count
    
    def _generate_lookup_keys(self, ref_data: dict) -> list[str]:
        """Generate multiple lookup keys for a reference.
        
        This helps match different citation formats:
        - "Brown et al., 2020"
        - "Brown, 2020"
        - "Brown et al. (2020)"
        - "Brown2020"
        
        Args:
            ref_data: Reference data from JSONL.
            
        Returns:
            List of normalized lookup keys.
        """
        keys = []
        
        authors = ref_data.get("authors", [])
        year = str(ref_data.get("year", ""))
        citation_key = ref_data.get("citation_key", "")
        
        if not authors or not year:
            # Fallback to citation_key
            if citation_key:
                keys.append(self._normalize_key(citation_key))
            return keys
        
        # Get first author's last name
        first_author = authors[0] if authors else ""
        # Handle formats like "Brown, T." or "T. Brown"
        if "," in first_author:
            last_name = first_author.split(",")[0].strip()
        elif " " in first_author:
            parts = first_author.split()
            # Assume last word is last name
            last_name = parts[-1].strip()
        else:
            last_name = first_author
        
        # Generate various formats
        if len(authors) > 2:
            keys.append(self._normalize_key(f"{last_name} et al., {year}"))
            keys.append(self._normalize_key(f"{last_name} et al. {year}"))
            keys.append(self._normalize_key(f"{last_name} et al.({year})"))
            keys.append(self._normalize_key(f"{last_name} et al. ({year})"))
        elif len(authors) == 2:
            second_author = authors[1]
            if "," in second_author:
                second_last = second_author.split(",")[0].strip()
            elif " " in second_author:
                second_last = second_author.split()[-1].strip()
            else:
                second_last = second_author
            keys.append(self._normalize_key(f"{last_name} & {second_last}, {year}"))
            keys.append(self._normalize_key(f"{last_name} and {second_last}, {year}"))
            keys.append(self._normalize_key(f"{last_name} y {second_last}, {year}"))
        
        keys.append(self._normalize_key(f"{last_name}, {year}"))
        keys.append(self._normalize_key(f"{last_name} {year}"))
        keys.append(self._normalize_key(f"{last_name}({year})"))
        keys.append(self._normalize_key(f"{last_name} ({year})"))
        
        # Also add citation key (e.g., "Brown2020")
        if citation_key:
            keys.append(self._normalize_key(citation_key))
        
        return keys
    
    def _normalize_key(self, key: str) -> str:
        """Normalize a citation key for lookup.
        
        Removes extra whitespace, lowercases, removes punctuation variations.
        """
        # Lowercase
        key = key.lower().strip()
        # Normalize whitespace
        key = re.sub(r'\s+', ' ', key)
        # Remove extra punctuation but keep essential structure
        key = key.replace("(", "").replace(")", "")
        key = key.replace(".", "")
        return key
    
    def find_citations(self, text: str) -> list[CitationMatch]:
        """Find all [@Author, Year] citation markers in text.
        
        Args:
            text: The paper text to search.
            
        Returns:
            List of CitationMatch objects.
        """
        matches = []
        
        for match in self.REF_PATTERN.finditer(text):
            citation_key = match.group(1).strip()
            matches.append(CitationMatch(
                marker=match.group(0),
                key=citation_key,
                start=match.start(),
                end=match.end(),
            ))
        
        return matches
    
    def resolve_citation(self, citation_key: str) -> dict[str, Any] | None:
        """Look up a citation key in the references dictionary.
        
        Args:
            citation_key: The citation key to look up (e.g., "Brown et al., 2020").
            
        Returns:
            Reference data dict if found, None otherwise.
        """
        normalized = self._normalize_key(citation_key)
        return self._references_dict.get(normalized)
    
    def process_paper(
        self,
        text: str,
        citation_style: str = "inline",
        generate_references_section: bool = True,
    ) -> str:
        """Process a complete paper, resolving citations and generating bibliography.
        
        Args:
            text: The paper text with [@Author, Year] markers.
            citation_style: How to format inline citations:
                - "inline": (Author et al., Year)
                - "numbered": [1], [2], etc.
            generate_references_section: Whether to append References section.
            
        Returns:
            Processed paper text with resolved citations and References section.
        """
        # Reset tracking
        self._used_references = []
        self._used_keys = set()
        
        # Find all citations
        citations = self.find_citations(text)
        
        if not citations:
            console.print("[dim]No se encontraron marcadores [@...] en el texto[/dim]")
            return text
        
        console.print(f"[cyan]📚 Procesando {len(citations)} citas...[/cyan]")
        
        # Process citations in reverse order to maintain positions
        processed_text = text
        unresolved = []
        
        # First pass: collect all unique citations and assign numbers
        citation_numbers: dict[str, int] = {}
        
        for citation in citations:
            ref_data = self.resolve_citation(citation.key)
            if ref_data:
                # Add to used references if new
                ref_key = ref_data.get("id") or ref_data.get("citation_key", citation.key)
                if ref_key not in self._used_keys:
                    self._used_keys.add(ref_key)
                    self._used_references.append(ref_data)
                    citation_numbers[self._normalize_key(citation.key)] = len(self._used_references)
                else:
                    # Find existing number
                    for i, used_ref in enumerate(self._used_references, 1):
                        if (used_ref.get("id") or used_ref.get("citation_key")) == ref_key:
                            citation_numbers[self._normalize_key(citation.key)] = i
                            break
            else:
                unresolved.append(citation.key)
        
        # Second pass: replace markers (reverse order to maintain positions)
        for citation in reversed(citations):
            normalized = self._normalize_key(citation.key)
            ref_data = self.resolve_citation(citation.key)
            
            if ref_data:
                if citation_style == "numbered":
                    num = citation_numbers.get(normalized, "?")
                    replacement = f"[{num}]"
                else:
                    # Inline: (Author et al., Year)
                    replacement = f"({citation.key})"
            else:
                # Keep original key for unresolved citations
                replacement = f"({citation.key})"
            
            processed_text = (
                processed_text[:citation.start] + 
                replacement + 
                processed_text[citation.end:]
            )
        
        # Report unresolved citations
        if unresolved:
            console.print(f"[yellow]⚠ {len(set(unresolved))} citas no resueltas:[/yellow]")
            for key in set(unresolved):
                console.print(f"  [dim]• {key}[/dim]")
        
        # Generate References section
        if generate_references_section and self._used_references:
            references_section = self._generate_references_section(citation_style)
            processed_text += references_section
        
        console.print(f"[green]✓ {len(self._used_references)} referencias resueltas[/green]")
        
        return processed_text
    
    def _generate_references_section(self, citation_style: str = "inline") -> str:
        """Generate the References section.
        
        Args:
            citation_style: Citation style used in the paper.
            
        Returns:
            Formatted References section as markdown.
        """
        if not self._used_references:
            return ""
        
        lines = [
            "\n\n## Referencias\n",
        ]
        
        for i, ref in enumerate(self._used_references, 1):
            full_citation = ref.get("full_citation", "")
            
            if not full_citation:
                # Build citation from components
                authors = ref.get("authors", [])
                year = ref.get("year", "")
                title = ref.get("title", "")
                venue = ref.get("venue", "")
                
                if isinstance(authors, list):
                    authors_str = ", ".join(authors)
                else:
                    authors_str = str(authors)
                
                full_citation = f"{authors_str} ({year}). {title}"
                if venue:
                    full_citation += f". {venue}"
                full_citation += "."
            
            if citation_style == "numbered":
                lines.append(f"[{i}] {full_citation}\n")
            else:
                lines.append(f"- {full_citation}\n")
        
        return "\n".join(lines)
    
    def get_used_references(self) -> list[dict[str, Any]]:
        """Get list of references used in the paper.
        
        Returns:
            List of reference data dicts in order of first appearance.
        """
        return self._used_references.copy()
    
    def get_citation_context(self) -> str:
        """Generate citation context for the writer agent.
        
        This creates a summary of available citations that can be
        injected into the writer's prompt.
        
        Returns:
            Formatted string with available citation keys.
        """
        if not self._references_dict:
            return ""
        
        # Get unique references (by citation_key)
        unique_refs: dict[str, dict] = {}
        for ref in self._references_dict.values():
            key = ref.get("citation_key", "")
            if key and key not in unique_refs:
                unique_refs[key] = ref
        
        lines = [
            "\n📖 CITAS DISPONIBLES (usa el formato [@Autor et al., Año]):\n",
        ]
        
        # Show first ~50 unique references
        for i, (key, ref) in enumerate(list(unique_refs.items())[:50]):
            authors = ref.get("authors", [])
            year = ref.get("year", "")
            title = ref.get("title", "")[:60]
            
            if isinstance(authors, list) and len(authors) > 0:
                first_author = authors[0].split(",")[0] if "," in authors[0] else authors[0]
                if len(authors) > 2:
                    author_str = f"{first_author} et al."
                elif len(authors) == 2:
                    second = authors[1].split(",")[0] if "," in authors[1] else authors[1]
                    author_str = f"{first_author} & {second}"
                else:
                    author_str = first_author
            else:
                author_str = str(authors) if authors else "Unknown"
            
            lines.append(f"  • [@{author_str}, {year}] - {title}...")
        
        if len(unique_refs) > 50:
            lines.append(f"\n  [... y {len(unique_refs) - 50} referencias más]")
        
        return "\n".join(lines)
    
    def clear(self) -> None:
        """Clear used references tracking."""
        self._used_references = []
        self._used_keys = set()


# Convenience function for processing
def process_paper_references(
    paper_text: str,
    references_path: Path | None = None,
    citation_style: str = "inline",
) -> str:
    """Process a paper's citation markers and generate bibliography.
    
    Args:
        paper_text: The paper text with [@Author, Year] markers.
        references_path: Path to references JSONL (optional).
        citation_style: "inline" or "numbered".
        
    Returns:
        Processed paper with resolved citations and References section.
    """
    processor = ReferenceProcessor(references_index_path=references_path)
    processor.load_references()
    return processor.process_paper(paper_text, citation_style=citation_style)
