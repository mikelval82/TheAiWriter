"""Tests for writing a document in its folder: phases, checkpoints, pause, stop and language.

Run from the repository root with ``python -m pytest`` so that ``config`` is importable.
"""

import json
import re

import pytest

from ai_writer.library import LibraryError, Project
from ai_writer.llm import LLMError
from ai_writer.perspective_run import (
    PLAN,
    STATE,
    STOP,
    PerspectiveRun,
    replace_invalid_citations,
)
from ai_writer.citations import CitationIndex
from tests.test_citations import library  # noqa: F401  (fixture)


def _cite_first_key(prompt: str) -> str:
    keys = re.findall(r"Citar: \[@([^\]]+)\]", prompt)
    return f"Párrafo escrito [@{keys[0]}]." if keys else "Párrafo sin fuentes [@?]."


@pytest.fixture
def document(library, tmp_path, fake_llm):  # noqa: F811
    library.save_collection("Robots", library.find_papers(["emotion models", "crowded"]))
    folder = tmp_path / "doc"
    Project.create(folder, tipo="perspectiva", titulo="Robots sociales", colecciones=["Robots"],
                   biblioteca=library.root)
    (folder / "materiales" / "abstract.md").write_text(
        "Los robots sociales necesitan modelos de emoción.", encoding="utf-8"
    )
    fake_llm.on("Escribe UN SOLO PÁRRAFO", _cite_first_key)
    fake_llm.on("Revisa y mejora la siguiente sección",
                lambda prompt: re.search(r"CONTENIDO ACTUAL:\n(.*?)\n", prompt, re.S).group(1))
    fake_llm.on("revisión final de coherencia", (
        "### Introducción\nIntro final [@smith2020emotion] y [@made2020up].\n\n"
        "### Conclusiones\nCierre final [@smith2020emotion; @green2022speech]."
    ))
    return folder


def _writer_calls(fake_llm) -> int:
    return len(fake_llm.prompts_containing("Escribe UN SOLO PÁRRAFO"))


def test_full_run_writes_a_document_whose_citations_all_pass(document, fake_llm):
    status = PerspectiveRun(document).run()

    assert status["estado"] == "terminado"
    assert status["parrafos"] == "2/2"
    text = (document / "borrador" / "documento.md").read_text(encoding="utf-8")
    assert text.startswith("# Robots sociales")
    assert "## Introducción\n\nIntro final [@smith2020emotion] y [@?]." in text
    # green2022speech is in the library but not in the document's collections
    assert "Cierre final [@smith2020emotion]." in text
    corrections = (document / "revision" / "citas_corregidas.md").read_text(encoding="utf-8")
    assert "made2020up" in corrections and "green2022speech" in corrections
    state = json.loads((document / STATE).read_text(encoding="utf-8"))
    assert state["citas_validas"] is True
    assert (document / "revision" / "validacion.md").exists()
    assert (document / "revision" / "revision_critica.md").exists()


def test_writer_is_offered_only_the_collections_keys(document, fake_llm):
    PerspectiveRun(document).run()

    offered = set()
    for prompt in fake_llm.prompts_containing("Escribe UN SOLO PÁRRAFO"):
        offered |= set(re.findall(r"Citar: \[@([^\].]+)\]", prompt))
    assert offered and offered <= {"smith2020emotion", "brown2021navigation"}


def test_a_failed_run_resumes_from_the_last_paragraph(document, fake_llm):
    calls = []

    def fail_second(prompt):
        calls.append(prompt)
        if len(calls) == 2:
            raise LLMError("se cortó la conexión", retryable=False)
        return _cite_first_key(prompt)

    fake_llm.on("Escribe UN SOLO PÁRRAFO", fail_second)
    with pytest.raises(LLMError):
        PerspectiveRun(document).run()

    status = PerspectiveRun(document).status()
    assert status["estado"] == "error" and "conexión" in status["error"]
    assert status["parrafos"] == "1/2"

    fake_llm.on("Escribe UN SOLO PÁRRAFO", _cite_first_key)
    before = _writer_calls(fake_llm)
    assert PerspectiveRun(document).run()["estado"] == "terminado"
    assert _writer_calls(fake_llm) - before == 1
    assert len(fake_llm.prompts_containing("planificador de papers")) == 1


def test_pause_after_plan_waits_and_writes_the_edited_plan(document, fake_llm):
    status = PerspectiveRun(document).run(pause_after_plan=True)

    assert status["estado"] == "esperando_aprobacion"
    assert _writer_calls(fake_llm) == 0
    plan = json.loads((document / PLAN).read_text(encoding="utf-8"))
    plan["sections"][0]["paragraphs"][0]["key_idea"] = "idea editada por la alumna"
    (document / PLAN).write_text(json.dumps(plan), encoding="utf-8")

    run = PerspectiveRun(document)
    assert run.run()["estado"] == "esperando_aprobacion"  # still not approved
    run.save(plan_aprobado="sí")
    assert PerspectiveRun(document).run()["estado"] == "terminado"
    assert fake_llm.prompts_containing("idea editada por la alumna")


def test_stop_request_ends_after_the_paragraph_in_progress(document, fake_llm):
    def stop_after_first(prompt):
        (document / STOP).touch()
        return _cite_first_key(prompt)

    fake_llm.on("Escribe UN SOLO PÁRRAFO", stop_after_first)

    status = PerspectiveRun(document).run()

    assert status["estado"] == "detenido"
    assert status["parrafos"] == "1/2"
    fake_llm.on("Escribe UN SOLO PÁRRAFO", _cite_first_key)
    assert PerspectiveRun(document).run()["estado"] == "terminado"


def test_other_languages_are_requested_in_every_prompt(document, fake_llm):
    project = Project.load(document)
    project.idioma = "inglés"
    project.save(document)

    PerspectiveRun(document).run()

    note = "IDIOMA DE SALIDA: redacta todo el texto que produzcas en inglés"
    assert all(note in call["prompt"] for call in fake_llm.calls)


def test_missing_abstract_is_reported_before_any_call(document, fake_llm):
    (document / "materiales" / "abstract.md").unlink()

    with pytest.raises(LibraryError, match="abstract"):
        PerspectiveRun(document).run()
    assert fake_llm.calls == []


def test_replace_invalid_citations_keeps_valid_parts(library):  # noqa: F811
    index = CitationIndex.load(library)
    text, replaced = replace_invalid_citations(
        "A [@smith2020emotion; @made2020up, p. 3]. B [@Brown et al., 2020]. C [@?].",
        index, {"smith2020emotion"},
    )

    assert text == "A [@smith2020emotion]. B [@?]. C [@?]."
    assert replaced == ["made2020up", "[@Brown et al., 2020]"]
