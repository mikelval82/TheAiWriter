"""Tests for the on-demand writing mode: consult the library, read passages, then write a section.

Run from the repository root with ``python -m pytest`` so that ``config`` is importable.
"""

import json
import re

import pytest

from ai_writer.demand_run import MAX_ROUNDS, RESULTS_PER_QUERY, SYSTEM, DemandRun
from ai_writer.library import Project
from ai_writer.llm import LLMError
from ai_writer.perspective_run import STATE, STOP
from tests.test_citations import library, write_sections  # noqa: F401  (fixture)
from tests.test_perspective_run import _support_all

SECTION_PROMPT = "redacta UNA sección de un documento científico"
INTRO_TEXT = "Texto completo de la introducción de emotion con cifras 42%."


def consult(*queries, read=()):
    return json.dumps({"accion": "consultar", "buscar": list(queries), "leer": list(read)})


def write(text):
    return json.dumps({"accion": "escribir", "texto": text})


def first_key(prompt: str) -> str:
    return re.search(r"^E1 · \[@([^\]]+)\]", prompt, re.M).group(1)


def script(fake_llm, *replies):
    """Answer the section prompts in order with these replies (strings or callables of the prompt)."""
    queue = iter(replies)
    fake_llm.on(SECTION_PROMPT, lambda prompt: (lambda r: r(prompt) if callable(r) else r)(next(queue)))


def section_prompts(fake_llm) -> list[str]:
    return fake_llm.prompts_containing(SECTION_PROMPT)


@pytest.fixture
def document(library, tmp_path, fake_llm):  # noqa: F811
    write_sections(library, "paper-emotion", {"Introduction": INTRO_TEXT})
    write_sections(library, "paper-navigation", {"Introduction": "Navegación en espacios llenos."})
    library.save_collection("Robots", library.find_papers(["emotion models", "crowded"]))
    folder = tmp_path / "doc"
    Project.create(folder, tipo="perspectiva", titulo="Robots sociales", colecciones=["Robots"],
                   biblioteca=library.root)
    (folder / "materiales" / "abstract.md").write_text(
        "Los robots sociales necesitan modelos de emoción.", encoding="utf-8"
    )
    fake_llm.on("revisor estricto de citas", _support_all)
    return folder


def finish(fake_llm):
    """Every section is written at once with the first work offered."""
    script(fake_llm, *[lambda p: write(f"Párrafo uno [@{first_key(p)}].\n\nPárrafo dos.")] * 2)


def test_the_model_consults_reads_a_passage_and_writes_a_document_whose_citations_validate(document, fake_llm):
    script(
        fake_llm,
        consult("robot emotion idea", read=["E1"]),
        lambda p: write(f"Los modelos de emoción mejoran la interacción [@{first_key(p)}]."),
        lambda p: write(f"Cierre [@{first_key(p)}]."),
    )

    status = DemandRun(document).run()

    assert status["estado"] == "terminado"
    assert status["parrafos"] == "2/2"
    assert status["secciones_terminadas"] == ["Introducción", "Conclusiones"]
    first, second, _third = section_prompts(fake_llm)
    assert "TEXTOS COMPLETOS LEÍDOS" not in first
    passages = {"smith2020emotion": INTRO_TEXT, "brown2021navigation": "Navegación en espacios llenos."}
    assert "TEXTOS COMPLETOS LEÍDOS" in second and passages[first_key(first)] in second
    state = json.loads((document / STATE).read_text(encoding="utf-8"))
    assert state["citas_validas"] is True
    assert "Los modelos de emoción mejoran la interacción [@" in (document / "borrador" / "documento.md").read_text(encoding="utf-8")


def test_evidence_ids_are_stable_and_the_passage_comes_with_its_work_and_section(document, fake_llm):
    script(
        fake_llm,
        consult("robot speech idea", read=["E1"]),
        lambda p: write(f"Texto [@{first_key(p)}]."),
        lambda p: write(f"Cierre [@{first_key(p)}]."),
    )

    DemandRun(document).run()

    first, second, _third = section_prompts(fake_llm)
    lines = lambda prompt: re.findall(r"^E\d+ · .*$", prompt, re.M)  # noqa: E731
    assert lines(first) and lines(second)[: len(lines(first))] == lines(first)
    assert 0 < len(lines(second)) - len(lines(first)) <= RESULTS_PER_QUERY
    assert len(lines(first)) <= 2 * 4 * 2  # seeds: a query per paragraph, plus the plan's works
    key = first_key(first)
    section = re.search(r"^E1 · \[@[^\]]+\] · apartado «([^»]+)»", first, re.M).group(1)
    header = f"## [@{key}], apartado «{section}»"
    assert header in second
    assert header not in first
    # the model sees one line per item: id, citation, section name, type and text
    assert re.search(r"^E1 · \[@\S+\] · apartado «\w+» · (idea|hallazgo propio|afirmación citada) · .+", first, re.M)


def test_unknown_ids_and_missing_passages_are_reported_not_fatal(document, fake_llm):
    def read_a_claim(prompt):
        claim = re.search(r"^(E\d+) · .* · afirmación citada · ", prompt, re.M).group(1)
        return consult(read=["E99", claim, "E1"])

    script(
        fake_llm,
        consult("robot emotion claim0"),
        read_a_claim,
        lambda p: write(f"Texto [@{first_key(p)}]."),
        lambda p: write(f"Cierre [@{first_key(p)}]."),
    )

    assert DemandRun(document).run()["estado"] == "terminado"

    third = section_prompts(fake_llm)[2]
    notes = third.split("AVISOS DE LA ÚLTIMA CONSULTA")[1]
    assert "No existe la evidencia E99" in notes
    assert "No hay texto completo de E" in notes and "apartado «Results»" in notes
    assert "apartado «Introduction»" in third.split("TEXTOS COMPLETOS LEÍDOS")[1]


def test_a_passage_is_shown_once_even_if_asked_again(document, fake_llm):
    script(
        fake_llm,
        consult(read=["E1"]),
        consult(read=["E1"]),
        lambda p: write(f"Texto [@{first_key(p)}]."),
        lambda p: write(f"Cierre [@{first_key(p)}]."),
    )

    DemandRun(document).run()

    third = section_prompts(fake_llm)[2]
    assert third.count("TEXTOS COMPLETOS LEÍDOS") == 1
    assert len(re.findall(r"^## \[@\S+\], apartado", third, re.M)) == 1


def test_the_last_round_only_accepts_writing_and_a_stubborn_model_gets_one_more_call(document, fake_llm):
    script(
        fake_llm,
        *[consult("robot idea")] * MAX_ROUNDS,
        lambda p: write(f"Texto [@{first_key(p)}]."),
        lambda p: write(f"Cierre [@{first_key(p)}]."),
    )

    assert DemandRun(document).run()["estado"] == "terminado"

    prompts = section_prompts(fake_llm)
    first_section = prompts[: MAX_ROUNDS + 1]
    assert len(prompts) == MAX_ROUNDS + 1 + 1
    assert "YA NO SE PUEDE CONSULTAR" not in first_section[MAX_ROUNDS - 2]
    assert "YA NO SE PUEDE CONSULTAR" in first_section[MAX_ROUNDS - 1]
    assert "pero ya no se puede consultar" in first_section[MAX_ROUNDS]


def test_a_model_that_never_writes_fails_after_the_round_cap(document, fake_llm):
    fake_llm.on(SECTION_PROMPT, consult("robot idea"))

    with pytest.raises(LLMError, match="no escribió"):
        DemandRun(document).run()

    assert len(section_prompts(fake_llm)) == MAX_ROUNDS + 1
    assert DemandRun(document).status()["estado"] == "error"


def test_an_unreadable_answer_is_asked_again(document, fake_llm):
    script(fake_llm, "esto no es JSON", '{"accion": "otra"}', lambda p: write(f"Texto [@{first_key(p)}]."),
           lambda p: write(f"Cierre [@{first_key(p)}]."))
    assert DemandRun(document).run()["estado"] == "terminado"
    assert len(section_prompts(fake_llm)) == 4  # two bad answers retried, then one per section


def test_an_answer_that_stays_unreadable_fails_after_two_retries(document, fake_llm):
    fake_llm.on(SECTION_PROMPT, "siempre ilegible")

    with pytest.raises(LLMError, match="ilegible"):
        DemandRun(document).run()

    assert len(section_prompts(fake_llm)) == 3


def test_the_prompt_carries_the_context_the_writing_rules_and_the_target_length(document, fake_llm):
    finish(fake_llm)

    DemandRun(document).run()

    intro, closing = section_prompts(fake_llm)
    low, high = 184, 276  # perspectiva, two planned paragraphs: 5000 words / 2 each, within the range
    assert "Los robots sociales necesitan modelos de emoción." in intro
    assert "Social robots need grounded emotion models." in intro
    assert "emotion models matter for robots" in intro and "navigation and speech complete the picture" in intro
    assert "emotion drives interaction" in intro
    assert "SECCIÓN QUE TOCA ESCRIBIR: Introducción" in intro
    assert "TEXTO YA ESCRITO" not in intro
    assert f"entre {low} y {high} palabras (1 párrafos)" in intro
    assert "### Introducción\nPárrafo uno [@" in closing.split("# SECCIÓN QUE TOCA")[0]
    assert "SECCIÓN QUE TOCA ESCRIBIR: Conclusiones" in closing
    for rule in ("Nunca escribas [@?]", "SIN cita", "«afirmación citada»", "sin encabezado",
                 "No repitas lo que ya dicen", "Respeta la extensión objetivo", "Varía las obras citadas",
                 "Antes de citar un resultado, un método o una cifra concretos, lee el texto completo"):
        assert rule in SYSTEM
        assert rule in fake_llm.calls[[c["prompt"] for c in fake_llm.calls].index(intro)]["request"].system


def test_sections_are_stored_with_their_paragraphs_and_no_review_runs(document, fake_llm):
    finish(fake_llm)

    DemandRun(document).run()

    state = json.loads((document / STATE).read_text(encoding="utf-8"))
    assert [len(s["parrafos"]) for s in state["secciones"]] == [2, 2]
    assert state["secciones"][0]["contenido"].count("\n\n") == 1
    assert state["revision_global_hecha"]
    assert fake_llm.prompts_containing("Revisa y mejora la siguiente sección") == []
    assert fake_llm.prompts_containing("revisión final de coherencia") == []
    draft = (document / "borrador" / "documento.md").read_text(encoding="utf-8")
    assert "## Introducción\n\nPárrafo uno [@" in draft and "## Conclusiones" in draft


def test_what_the_model_saw_and_the_searches_are_recorded_for_the_validator(document, fake_llm):
    script(
        fake_llm,
        consult("robot emotion idea"),
        lambda p: write(f"Texto [@{first_key(p)}]."),
        lambda p: write(f"Cierre [@{first_key(p)}]."),
    )

    DemandRun(document).run()

    seen = json.loads((document / "revision" / "evidencia_vista.json").read_text(encoding="utf-8"))
    retrieved = json.loads((document / "revision" / "evidencia.json").read_text(encoding="utf-8"))
    assert set(seen) == {"Introducción", "Conclusiones"}
    items = [item for by_key in seen.values() for stored in by_key.values() for item in stored]
    assert items and all(set(item) == {"clave", "tipo", "texto", "cita_literal", "origen"} for item in items)
    assert all((item["origen"] in ("citado", "propio")) == (item["tipo"] == "claim") for item in items)
    assert any("robot emotion idea" in queries for queries in retrieved.values())
    assert any("emotion models matter for robots" in " ".join(q) for q in retrieved.values())


def test_a_stopped_run_resumes_without_rewriting_finished_sections(document, fake_llm):
    def stop_after_writing(prompt):
        (document / STOP).touch()
        return write(f"Introducción única [@{first_key(prompt)}].")

    script(fake_llm, stop_after_writing)

    status = DemandRun(document).run()

    assert status["estado"] == "detenido"
    assert status["secciones_terminadas"] == ["Introducción"]
    assert status["parrafos"] == "1/2"
    script(fake_llm, lambda p: write(f"Cierre [@{first_key(p)}]."))
    before = len(section_prompts(fake_llm))

    assert DemandRun(document).run()["estado"] == "terminado"

    resumed = section_prompts(fake_llm)[before:]
    assert len(resumed) == 1
    assert "Introducción única" in resumed[0] and "SECCIÓN QUE TOCA ESCRIBIR: Conclusiones" in resumed[0]
    assert len(fake_llm.prompts_containing("planificador de papers")) == 1
    assert "Introducción única" in (document / "borrador" / "documento.md").read_text(encoding="utf-8")
