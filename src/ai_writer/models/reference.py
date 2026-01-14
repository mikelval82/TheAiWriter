"""Reference data model for source documents."""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class ReferenceType(str, Enum):
    """Type of reference document."""

    PDF = "pdf"
    MARKDOWN = "markdown"
    ARTICLE = "article"
    BOOK = "book"
    WEBSITE = "website"


class Reference(BaseModel):
    """A reference document used as source material."""

    title: str = Field(..., description="Reference title")
    source_path: Path | None = Field(None, description="Path to source file")
    content: str = Field("", description="Extracted text content")
    reference_type: ReferenceType = Field(ReferenceType.PDF, description="Type of reference")
    authors: list[str] = Field(default_factory=list, description="List of authors")
    year: int | None = Field(None, description="Publication year")
    url: str | None = Field(None, description="URL if applicable")
    notes: str = Field("", description="User notes about this reference")
    added_at: datetime = Field(default_factory=datetime.now, description="When added")

    def to_citation(self, style: str = "apa") -> str:
        """Generate a citation string.

        Args:
            style: Citation style (apa, mla, chicago).

        Returns:
            Formatted citation string.
        """
        authors_str = ", ".join(self.authors) if self.authors else "Unknown"
        year_str = str(self.year) if self.year else "n.d."

        if style.lower() == "apa":
            return f"{authors_str} ({year_str}). {self.title}."
        elif style.lower() == "mla":
            return f'{authors_str}. "{self.title}." {year_str}.'
        elif style.lower() == "chicago":
            return f'{authors_str}. "{self.title}," {year_str}.'
        else:
            return f"{authors_str} ({year_str}). {self.title}."

    def get_summary(self, max_length: int = 500) -> str:
        """Get a truncated summary of the content.

        Args:
            max_length: Maximum length of the summary.

        Returns:
            Truncated content.
        """
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."


class ReferenceCollection(BaseModel):
    """A collection of references."""

    name: str = Field(..., description="Collection name")
    references: list[Reference] = Field(default_factory=list, description="References in collection")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    def add(self, reference: Reference) -> None:
        """Add a reference to the collection.

        Args:
            reference: The reference to add.
        """
        self.references.append(reference)

    def find_by_title(self, title: str) -> Reference | None:
        """Find a reference by title.

        Args:
            title: The title to search for.

        Returns:
            The reference if found, None otherwise.
        """
        for ref in self.references:
            if ref.title.lower() == title.lower():
                return ref
        return None

    def generate_bibliography(self, style: str = "apa") -> str:
        """Generate a bibliography from all references.

        Args:
            style: Citation style to use.

        Returns:
            Formatted bibliography.
        """
        citations = [ref.to_citation(style) for ref in self.references]
        return "\n".join(sorted(citations))

class ParsedReference(BaseModel):
    """A parsed academic reference with structured sections for intelligent retrieval."""

    filename: str = Field(..., description="Original filename")
    title: str = Field(default="", description="Paper title")
    
    # Metadata
    authors: str = Field(default="", description="Authors list")
    year: str = Field(default="", description="Publication year")
    keywords: str = Field(default="", description="Keywords")
    
    # Content sections
    abstract: str = Field(default="", description="Abstract section")
    contributions: str = Field(default="", description="Main contributions")
    methodology: str = Field(default="", description="Methodology section")
    results: str = Field(default="", description="Key results")
    limitations: str = Field(default="", description="Limitations")
    future_work: str = Field(default="", description="Future work")
    quotes: str = Field(default="", description="Relevant quotes")
    notes: str = Field(default="", description="Additional notes")
    
    # Embedding (cached)
    embedding: list[float] | None = Field(default=None, description="Cached embedding vector")

    def get_section(self, section_name: str) -> str:
        """Get content of a specific section.
        
        Args:
            section_name: Name of the section to retrieve.
            
        Returns:
            The section content or empty string if not found.
        """
        section_map = {
            "abstract": self.abstract,
            "contributions": self.contributions,
            "methodology": self.methodology,
            "results": self.results,
            "limitations": self.limitations,
            "future_work": self.future_work,
            "quotes": self.quotes,
            "notes": self.notes,
        }
        return section_map.get(section_name.lower(), "")

    def get_sections(self, section_names: list[str]) -> str:
        """Get combined content of multiple sections.
        
        Args:
            section_names: List of section names to retrieve.
            
        Returns:
            Combined content of all requested sections.
        """
        contents = []
        for name in section_names:
            content = self.get_section(name)
            if content:
                contents.append(f"### {name.replace('_', ' ').title()}\n{content}")
        return "\n\n".join(contents)

    def get_full_text(self) -> str:
        """Get full text of the reference for embedding generation."""
        parts = [
            self.title,
            self.abstract,
            self.contributions,
            self.methodology,
            self.results,
        ]
        return " ".join(p for p in parts if p)

    def to_citation_str(self) -> str:
        """Generate a simple citation string."""
        return f"{self.authors} ({self.year}). {self.title}"