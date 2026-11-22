"""Pending notices and the nonblocking prompt hook, with fake background models."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ai_writer import revisor, verificacion
from ai_writer.avisos import NOTICES, add_notice, pop_notices
from ai_writer.llm import LLMError, UsageLimitError
from tests.test_passages import library  # noqa: F401
from tests.test_revisor import Reviewer
from tests.test_verificacion import Judge, draft  # noqa: F401
from tests.test_zotero_tools import document  # noqa: F401

HOOK = Path(__file__).resolve().parent.parent / "hooks/avisos.py"


def run_hook(event):
    return subprocess.run([sys.executable, str(HOOK)], input=event, text=True,
                          capture_output=True, check=True)


def test_notices_are_dated_and_consumed_once(tmp_path):
    assert pop_notices(tmp_path) == []
    add_notice(tmp_path, "Primero.")
    add_notice(tmp_path, "Segundo.")
    data = json.loads((tmp_path / NOTICES).read_text(encoding="utf-8"))
    assert len(data) == 2 and all(n["fecha"] for n in data)
    assert pop_notices(tmp_path) == ["Primero.", "Segundo."]
    assert json.loads((tmp_path / NOTICES).read_text()) == []
    assert pop_notices(tmp_path) == []


def test_hook_delivers_context_and_empties_notices(tmp_path):
    (tmp_path / "proyecto.yaml").write_text("tipo: perspectiva\ntitulo: T\n")
    add_notice(tmp_path, "Ha terminado el juez.")
    add_notice(tmp_path, "Ha terminado la revisión.")
    event = json.dumps({"cwd": str(tmp_path)})
    result = run_hook(event)
    assert not result.stderr
    output = json.loads(result.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "UserPromptSubmit"
    assert output["additionalContext"] == (
        "TheAIWriter: Ha terminado el juez.\nHa terminado la revisión. "
        "Menciónalo al usuario al principio de tu respuesta."
    )
    assert run_hook(event).stdout == ""


@pytest.mark.parametrize("event", ["", "[", "null", "[]", "{}", '{"cwd": 15}'])
def test_hook_ignores_invalid_input(event):
    done = run_hook(event)
    assert done.stdout == done.stderr == ""


def test_hook_ignores_non_documents_and_preserves_queue(tmp_path):
    add_notice(tmp_path, "Pendiente.")
    assert not run_hook(json.dumps({"cwd": str(tmp_path)})).stdout
    assert pop_notices(tmp_path) == ["Pendiente."]


def test_hook_ignores_unreadable_notice_data(tmp_path):
    (tmp_path / "proyecto.yaml").touch()
    (tmp_path / "informes").mkdir()
    (tmp_path / NOTICES).write_text("mal JSON")
    done = run_hook(json.dumps({"cwd": str(tmp_path)}))
    assert done.stdout == done.stderr == ""


@pytest.mark.parametrize("state", ["terminado", "limite_de_uso", "error"])
def test_judge_notices_every_terminal_state(draft, monkeypatch, state):  # noqa: F811
    if state == "error":
        monkeypatch.setattr(verificacion, "judge_support", lambda *args: (_ for _ in ()).throw(
            RuntimeError("Fallo de prueba")))
        with pytest.raises(RuntimeError):
            verificacion.run_judge(draft, Judge())
    else:
        verificacion.run_judge(draft, Judge(fail_after=1 if state == "limite_de_uso" else None))
    assert verificacion.status(draft)["juez"]["estado"] == state
    notices = pop_notices(draft)
    assert len(notices) == 1 and "informes/comprobacion.md" in notices[0]
    if state == "terminado":
        assert "3 de 5 frases apoyadas, 2 por revisar" in notices[0]
    else:
        assert state in notices[0] and "/theaiwriter:comprobar" in notices[0]


@pytest.mark.parametrize("state,error", [
    ("terminado", None), ("limite_de_uso", UsageLimitError), ("error", LLMError),
])
def test_reviewer_notices_every_terminal_state(draft, state, error):  # noqa: F811
    if state == "error":
        with pytest.raises(LLMError):
            revisor.run_review(draft, Reviewer(error=error))
    else:
        revisor.run_review(draft, Reviewer(error=error))
    assert revisor.review_status(draft)["estado"] == state
    notices = pop_notices(draft)
    assert len(notices) == 1 and "informes/revision.md" in notices[0]
    if state == "terminado":
        assert "0 criterios flojos, 5 mejorables" in notices[0]
    else:
        assert state in notices[0] and "/theaiwriter:revisar" in notices[0]
