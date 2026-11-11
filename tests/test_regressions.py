"""Regression tests for the CLI commands and agent defaults fixed in phase 0.

Run from the repository root with ``python -m pytest`` so that ``config`` is importable.
"""

import numpy as np
from typer.testing import CliRunner

from ai_writer.agents.translator_agent import TranslatorAgent
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
    from ai_writer.utils.enhanced_context_manager import EnhancedContextManager

    EnhancedContextManager(abstract_context="")  # builds the ideas and claims caches
    with np.load(workspace.embeddings_dir / "ideas_index.npz") as data:
        dimensions = data["embeddings"].shape[1]

    result = runner.invoke(app, ["stats"])

    assert result.exit_code == 0, result.output
    ideas_row = next(line for line in result.output.splitlines() if "Ideas" in line)
    cells = ideas_row.replace("│", " ").split()
    assert cells == ["Ideas", str(len(PAPERS) * IDEAS_PER_PAPER), str(dimensions), str(len(PAPERS))]


def test_translator_default_style_guide_exists(fake_llm):
    translator = TranslatorAgent()

    assert translator.style_guide_path.exists()
    assert translator.style_guide


def test_outline_refinement_prompt_names_the_parsed_keys(fake_llm):
    from ai_writer.agents.planner_agent import PlannerAgent
    from ai_writer.models.outline import PaperOutline
    from tests.conftest import DEFAULT_OUTLINE

    outline = PaperOutline(title="T", abstract="A", **DEFAULT_OUTLINE)

    refined = PlannerAgent().refine_outline(outline, "Haz la tesis más específica.")

    prompt = fake_llm.prompts_containing("Feedback para Mejorar")[0]
    for key in ("section_name", "section_purpose", "key_idea", "supporting_points"):
        assert f'"{key}"' in prompt
    assert [s.section_name for s in refined.sections] == ["Introducción", "Conclusiones"]
