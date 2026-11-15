"""Regression tests for CLI commands and PDF extraction.

Run from the repository root with ``python -m pytest`` so that ``config`` is importable.
"""

import numpy as np
from typer.testing import CliRunner

from ai_writer.main import app
from tests.conftest import IDEAS_PER_PAPER, PAPERS

runner = CliRunner()


def test_process_runs_without_input_option(fake_llm, workspace):
    result = runner.invoke(app, ["process"])

    assert result.exit_code == 0, result.output
    assert "Processed: 0 papers" in result.output


def test_stats_reports_missing_indices(workspace):
    result = runner.invoke(app, ["stats"])

    assert result.exit_code == 0, result.output
    assert result.output.count("Not found") == 3


def test_stats_reports_built_index(fake_llm, workspace):
    from ai_writer.embeddings.rag_system import RAGSystem

    RAGSystem().build_indices()
    with np.load(workspace.embeddings_dir / "ideas_index.npz") as data:
        dimensions = data["embeddings"].shape[1]

    result = runner.invoke(app, ["stats"])

    assert result.exit_code == 0, result.output
    ideas_row = next(line for line in result.output.splitlines() if "Ideas" in line)
    cells = ideas_row.replace("│", " ").split()
    assert cells == ["Ideas", str(len(PAPERS) * IDEAS_PER_PAPER), str(dimensions), str(len(PAPERS))]


def test_section_structure_is_asked_again_when_the_answer_is_unreadable(fake_llm):
    from ai_writer.processors.extraction_agent import PDFExtractionAgent

    answers = iter(["no es JSON", '[{"section_name": "Introduction", "section_number": 1}]'])
    fake_llm.on("identify its section structure", lambda prompt: next(answers))

    structure = PDFExtractionAgent()._identify_section_structure("Introduction\nSome text.")

    assert structure == [{"section_name": "Introduction", "section_number": 1}]
    assert len(fake_llm.prompts_containing("identify its section structure")) == 2
