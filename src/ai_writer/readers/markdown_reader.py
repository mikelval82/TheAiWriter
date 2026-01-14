"""Markdown document reader."""

import re
from pathlib import Path

import markdown


class MarkdownReader:
    """Reader for Markdown documents."""

    def read(self, path: Path | str) -> str:
        """Read content from a Markdown file.

        Args:
            path: Path to the Markdown file.

        Returns:
            The raw Markdown content.

        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Markdown file not found: {path}")

        return path.read_text(encoding="utf-8")

    def read_as_plain_text(self, path: Path | str) -> str:
        """Read Markdown file and convert to plain text (strip formatting).

        Args:
            path: Path to the Markdown file.

        Returns:
            Plain text content without Markdown formatting.
        """
        content = self.read(path)
        return self._strip_markdown(content)

    def read_as_html(self, path: Path | str) -> str:
        """Read Markdown file and convert to HTML.

        Args:
            path: Path to the Markdown file.

        Returns:
            HTML content converted from Markdown.
        """
        content = self.read(path)
        md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])
        return md.convert(content)

    def extract_sections(self, path: Path | str) -> dict[str, str]:
        """Extract sections from a Markdown file based on headings.

        Args:
            path: Path to the Markdown file.

        Returns:
            Dictionary mapping section titles to their content.
        """
        content = self.read(path)
        sections: dict[str, str] = {}

        # Split by headings (# to ######)
        pattern = r"^(#{1,6})\s+(.+)$"
        lines = content.split("\n")
        current_section = "Introduction"
        current_content: list[str] = []

        for line in lines:
            match = re.match(pattern, line)
            if match:
                # Save previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                # Start new section
                current_section = match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _strip_markdown(self, content: str) -> str:
        """Remove Markdown formatting from text.

        Args:
            content: Markdown content.

        Returns:
            Plain text without formatting.
        """
        # Remove headers
        content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)

        # Remove bold/italic
        content = re.sub(r"\*\*(.+?)\*\*", r"\1", content)
        content = re.sub(r"\*(.+?)\*", r"\1", content)
        content = re.sub(r"__(.+?)__", r"\1", content)
        content = re.sub(r"_(.+?)_", r"\1", content)

        # Remove links but keep text
        content = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", content)

        # Remove images
        content = re.sub(r"!\[.*?\]\(.+?\)", "", content)

        # Remove code blocks
        content = re.sub(r"```[\s\S]*?```", "", content)
        content = re.sub(r"`(.+?)`", r"\1", content)

        # Remove horizontal rules
        content = re.sub(r"^[-*_]{3,}$", "", content, flags=re.MULTILINE)

        return content.strip()
