"""End-to-end run of the generation pipeline against the fake LLM.

Run from the repository root with ``python -m pytest`` so that ``config`` is importable.
"""

import pytest

from ai_writer.orchestrators.advanced_orchestrator import AdvancedPerspectiveOrchestrator
from tests.conftest import KNOWN_REFERENCE

TITLE = "Robots Sociales"


@pytest.fixture
def orchestrator(fake_llm, workspace):
    return AdvancedPerspectiveOrchestrator(n_clusters=3)


def test_run_writes_paper_and_review(orchestrator, workspace):
    paper_path, review_path = orchestrator.run(title=TITLE)

    assert paper_path.parent == workspace.final_dir
    paper = paper_path.read_text(encoding="utf-8")
    assert "## Introducción" in paper
    assert "## Conclusiones" in paper
    assert "Revisión Crítica" in review_path.read_text(encoding="utf-8")


def test_final_paper_has_resolved_citations_and_bibliography(orchestrator):
    paper_path, _ = orchestrator.run(title=TITLE)

    paper = paper_path.read_text(encoding="utf-8")
    assert "[@" not in paper
    assert "(Smith et al., 2020)" in paper
    assert "## Referencias" in paper
    assert KNOWN_REFERENCE in paper


def test_final_paper_is_the_globally_reviewed_version(orchestrator):
    paper_path, _ = orchestrator.run(title=TITLE)

    assert "Intro final" in paper_path.read_text(encoding="utf-8")


def test_run_honours_output_dir(orchestrator, tmp_path):
    out = tmp_path / "elsewhere"

    paper_path, review_path = orchestrator.run(title=TITLE, output_dir=out)

    assert paper_path.parent == out
    assert review_path.parent == out


def test_outline_refinement_is_logged(orchestrator, fake_llm, workspace):
    fake_llm.on("ESQUEMA A REVISAR", "Haz la tesis más específica.")

    orchestrator.run(title=TITLE)

    run_dir = workspace.data_dir / "logs" / "run_Robots_Sociales"
    assert (run_dir / "outline_feedback_1.json").exists()
    assert (run_dir / "outline_refined_1.json").exists()


def test_programming_errors_are_not_swallowed(orchestrator, monkeypatch):
    def boom(*args, **kwargs):
        raise TypeError("bug")

    monkeypatch.setattr(orchestrator.markdown_writer, "write", boom)

    with pytest.raises(TypeError):
        orchestrator.run(title=TITLE)
