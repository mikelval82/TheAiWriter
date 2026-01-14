"""Tests for the Markdown reader."""

from pathlib import Path

import pytest

from ai_writer.readers.markdown_reader import MarkdownReader


class TestMarkdownReader:
    """Tests for MarkdownReader class."""

    def test_read_file(self, sample_markdown_file: Path) -> None:
        """Test reading a Markdown file."""
        reader = MarkdownReader()
        content = reader.read(sample_markdown_file)

        assert "# Sample Document" in content
        assert "## Introduction" in content

    def test_read_nonexistent_file(self, temp_directory: Path) -> None:
        """Test reading a file that doesn't exist."""
        reader = MarkdownReader()
        nonexistent = temp_directory / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            reader.read(nonexistent)

    def test_extract_sections(self, sample_markdown_file: Path) -> None:
        """Test extracting sections from Markdown."""
        reader = MarkdownReader()
        sections = reader.extract_sections(sample_markdown_file)

        assert "Introduction" in sections
        assert "Methods" in sections
        assert "Results" in sections
        assert "Conclusion" in sections

    def test_read_as_plain_text(self, sample_markdown_file: Path) -> None:
        """Test converting Markdown to plain text."""
        reader = MarkdownReader()
        plain_text = reader.read_as_plain_text(sample_markdown_file)

        # Should not contain Markdown syntax
        assert "##" not in plain_text
        assert "#" not in plain_text

    def test_read_as_html(self, sample_markdown_file: Path) -> None:
        """Test converting Markdown to HTML."""
        reader = MarkdownReader()
        html = reader.read_as_html(sample_markdown_file)

        assert "<h1>" in html or "<h2>" in html
        assert "<p>" in html
