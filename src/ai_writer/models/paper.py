"""Paper data model."""

from datetime import datetime

from pydantic import BaseModel, Field


class Section(BaseModel):
    """A section within a paper."""

    title: str = Field(..., description="The section title")
    content: str = Field(..., description="The section content")


class Paper(BaseModel):
    """An academic paper."""

    title: str = Field(..., description="The paper title")
    sections: list[Section] = Field(default_factory=list, description="Paper sections")
    authors: list[str] = Field(default_factory=list, description="List of authors")
    keywords: list[str] = Field(default_factory=list, description="Keywords/tags")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    def add_section(self, title: str, content: str) -> None:
        """Add a new section to the paper.

        Args:
            title: Section title.
            content: Section content.
        """
        self.sections.append(Section(title=title, content=content))
        self.updated_at = datetime.now()

    def get_section(self, title: str) -> Section | None:
        """Get a section by title.

        Args:
            title: The section title to search for.

        Returns:
            The section if found, None otherwise.
        """
        for section in self.sections:
            if section.title.lower() == title.lower():
                return section
        return None

    def update_section(self, title: str, content: str) -> bool:
        """Update a section's content.

        Args:
            title: The section title to update.
            content: The new content.

        Returns:
            True if section was found and updated, False otherwise.
        """
        for section in self.sections:
            if section.title.lower() == title.lower():
                section.content = content
                self.updated_at = datetime.now()
                return True
        return False

    def to_text(self) -> str:
        """Convert the paper to plain text format.

        Returns:
            Plain text representation of the paper.
        """
        lines = [self.title, "=" * len(self.title), ""]

        if self.authors:
            lines.append(f"Authors: {', '.join(self.authors)}")
            lines.append("")

        for section in self.sections:
            lines.append(section.title)
            lines.append("-" * len(section.title))
            lines.append(section.content)
            lines.append("")

        return "\n".join(lines)

    def word_count(self) -> int:
        """Calculate the total word count of the paper.

        Returns:
            Total number of words in all sections.
        """
        total = 0
        for section in self.sections:
            total += len(section.content.split())
        return total
