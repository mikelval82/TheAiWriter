"""Data models for paper outline structure."""

from pydantic import BaseModel, Field


class ParagraphOutline(BaseModel):
    """Outline for a single paragraph."""
    
    paragraph_number: int
    key_idea: str  # The main idea this paragraph should develop
    supporting_points: list[str] = Field(default_factory=list)  # Additional points to cover
    suggested_sources: list[str] = Field(default_factory=list)  # Paper titles to cite
    
    def to_query(self) -> str:
        """Convert to a search query for embeddings."""
        parts = [self.key_idea]
        if self.supporting_points:
            parts.extend(self.supporting_points[:2])
        return " ".join(parts)


class SectionOutline(BaseModel):
    """Outline for a paper section."""
    
    section_name: str
    section_purpose: str  # What this section should accomplish
    paragraphs: list[ParagraphOutline] = Field(default_factory=list)
    
    @property
    def total_paragraphs(self) -> int:
        return len(self.paragraphs)
    
    def get_all_key_ideas(self) -> list[str]:
        """Get all key ideas from paragraphs."""
        return [p.key_idea for p in self.paragraphs]


class PaperOutline(BaseModel):
    """Complete paper outline with sections and paragraph-level ideas."""
    
    title: str
    abstract: str
    thesis_statement: str  # Core argument of the paper
    sections: list[SectionOutline] = Field(default_factory=list)
    available_topics: list[str] = Field(default_factory=list)  # Topics from cluster analysis
    
    @property
    def total_sections(self) -> int:
        return len(self.sections)
    
    @property
    def total_paragraphs(self) -> int:
        return sum(s.total_paragraphs for s in self.sections)
    
    def get_section(self, section_name: str) -> SectionOutline | None:
        """Get a section by name."""
        for section in self.sections:
            if section.section_name == section_name:
                return section
        return None
    
    def to_markdown(self) -> str:
        """Convert outline to markdown for display."""
        lines = [
            f"# {self.title}",
            "",
            f"**Tesis:** {self.thesis_statement}",
            "",
            "---",
            "",
        ]
        
        for section in self.sections:
            lines.append(f"## {section.section_name}")
            lines.append(f"*{section.section_purpose}*")
            lines.append("")
            
            for para in section.paragraphs:
                lines.append(f"### Párrafo {para.paragraph_number}")
                lines.append(f"- **Idea clave:** {para.key_idea}")
                if para.supporting_points:
                    lines.append(f"- **Puntos de apoyo:** {', '.join(para.supporting_points)}")
                if para.suggested_sources:
                    lines.append(f"- **Fuentes sugeridas:** {', '.join(para.suggested_sources[:3])}")
                lines.append("")
        
        return "\n".join(lines)
