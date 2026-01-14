"""Tests for the Markdown writer."""

from pathlib import Path

from ai_writer.models.paper import Paper
from ai_writer.writers.markdown_writer import MarkdownWriter


class TestMarkdownWriter:
    """Tests for MarkdownWriter class."""

    def test_write_paper(self, sample_paper: Paper, temp_directory: Path) -> None:
        """Test writing a paper to Markdown."""
        writer = MarkdownWriter()
        output_path = temp_directory / "test_paper.md"

        result = writer.write(sample_paper, output_path)

        assert result == output_path
        assert output_path.exists()

        content = output_path.read_text(encoding="utf-8")
        assert sample_paper.title in content
        assert "Abstract" in content
        assert "Introduction" in content

    def test_to_string(self, sample_paper: Paper) -> None:
        """Test converting paper to Markdown string."""
        writer = MarkdownWriter()
        content = writer.to_string(sample_paper)

        assert f"# {sample_paper.title}" in content
        assert "## Abstract" in content
        assert "## Introduction" in content
        assert "## Conclusion" in content

    def test_includes_authors(self, sample_paper: Paper) -> None:
        """Test that authors are included in output."""
        writer = MarkdownWriter()
        content = writer.to_string(sample_paper)

        assert "**Authors:**" in content
        assert "John Doe" in content
        assert "Jane Smith" in content

    def test_includes_table_of_contents(self, sample_paper: Paper) -> None:
        """Test that table of contents is included."""
        writer = MarkdownWriter()
        content = writer.to_string(sample_paper)

        assert "## Table of Contents" in content
        assert "[Abstract]" in content
