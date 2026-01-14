"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest

from ai_writer.models.paper import Paper, Section
from ai_writer.models.reference import Reference, ReferenceType


@pytest.fixture
def sample_paper() -> Paper:
    """Create a sample paper for testing."""
    return Paper(
        title="Sample Research Paper",
        authors=["John Doe", "Jane Smith"],
        keywords=["AI", "Machine Learning", "Research"],
        sections=[
            Section(
                title="Abstract",
                content="This is a sample abstract for testing purposes.",
            ),
            Section(
                title="Introduction",
                content="This is a sample introduction section.",
            ),
            Section(
                title="Conclusion",
                content="This is a sample conclusion section.",
            ),
        ],
    )


@pytest.fixture
def sample_reference() -> Reference:
    """Create a sample reference for testing."""
    return Reference(
        title="Sample Reference Document",
        reference_type=ReferenceType.PDF,
        authors=["Alice Johnson"],
        year=2024,
        content="This is sample reference content for testing.",
    )


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    """Create a temporary directory for file operations."""
    test_dir = tmp_path / "ai_writer_tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture
def sample_markdown_content() -> str:
    """Sample Markdown content for testing."""
    return """# Sample Document

## Introduction

This is the introduction section.

## Methods

This describes the methodology used.

## Results

Here are the results.

## Conclusion

This is the conclusion.
"""


@pytest.fixture
def sample_markdown_file(temp_directory: Path, sample_markdown_content: str) -> Path:
    """Create a sample Markdown file."""
    file_path = temp_directory / "sample.md"
    file_path.write_text(sample_markdown_content, encoding="utf-8")
    return file_path
