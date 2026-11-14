"""Tests for writing a document in its folder: phases, checkpoints, pause, stop and language.

Run from the repository root with ``python -m pytest`` so that ``config`` is importable.
"""

import json
import re

import pytest

from ai_writer.library import LibraryError, Project
from ai_writer.llm import LLMError
from ai_writer.models.outline import PaperOutline, ParagraphOutline, SectionOutline
from ai_writer.perspective_run import (
    PLAN,
    STATE,
    STOP,
    PerspectiveRun,
    fit_plan,
    replace_invalid_citations,
    revision_is_safe,
)
from ai_writer.profiles import PROFILES
from ai_writer.utils.enhanced_context_manager import (
    CITED_CLAIM_WEIGHT,
    DEFAULT_SECTION_CONFIG,
    SECTION_CONFIGS,
    EnhancedContextManager,
)
from ai_writer.citations import CitationIndex
from tests.conftest import DEFAULT_OUTLINE
from tests.test_citations import library  # noqa: F401  (fixture)


def _cite_first_key(prompt: str) -> str:
    keys = re.findall(r"Citar: \[@([^\]]+)\]", prompt)
    return f"Párrafo escrito [@{keys[0]}]." if keys else "Párrafo sin fuentes [@?]."


def _support_all(prompt):
    """The support judge finds every cited sentence backed by its source."""
    numbers = re.findall(r"^\[(\d+)\] Frase:", prompt, re.M)
    return json.dumps({"veredictos": [{"n": int(n), "veredicto": "apoyada", "motivo": "ok"} for n in numbers]})


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
    fake_llm.on("revisión final de coherencia de UNA sección",
                lambda prompt: "Revisado: " + re.search(r"CONTENIDO ACTUAL:\n\S+ (.*?)\n", prompt, re.S).group(1))
    fake_llm.on("revisor estricto de citas", _support_all)
    return folder


def _writer_calls(fake_llm) -> int:
    return len(fake_llm.prompts_containing("Escribe UN SOLO PÁRRAFO"))


def test_full_run_writes_a_document_whose_citations_all_pass(document, fake_llm):
    replies = iter([
        "Intro [@smith2020emotion] y [@made2020up].",
        # green2022speech is in the library but not in the document's collections
        "Cierre [@smith2020emotion; @green2022speech].",
    ])
    fake_llm.on("Escribe UN SOLO PÁRRAFO", lambda prompt: next(replies))

    status = PerspectiveRun(document).run()

    assert status["estado"] == "terminado"
    assert status["parrafos"] == "2/2"
    text = (document / "borrador" / "documento.md").read_text(encoding="utf-8")
    assert text.startswith("# Robots sociales")
    assert "Revisado: [@smith2020emotion] y [@?]." in text
    assert "Revisado: [@smith2020emotion]." in text
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


def test_paragraphs_are_asked_for_their_share_of_the_target_length(document, fake_llm):
    PerspectiveRun(document).run()

    low, high = PROFILES["perspectiva"].paragraph_words(2)
    assert (low, high) == (184, 276)
    prompts = fake_llm.prompts_containing("Escribe UN SOLO PÁRRAFO")
    assert all(f"entre {low} y {high} palabras" in prompt for prompt in prompts)


def test_the_plan_is_cut_to_the_profiles_paragraph_limits():
    paragraphs = [ParagraphOutline(paragraph_number=i, key_idea=f"idea {i}") for i in range(1, 6)]
    outline = PaperOutline(title="T", abstract="A", thesis_statement="T", sections=[
        SectionOutline(section_name="Introducción", section_purpose="p", paragraphs=paragraphs),
    ])

    fit_plan(outline, PROFILES["perspectiva"])

    intro = outline.sections[0].paragraphs
    assert [p.key_idea for p in intro] == ["idea 1", "idea 2", "idea 3"]
    assert intro[-1].supporting_points == ["idea 4", "idea 5"]


def test_works_already_cited_often_are_pointed_out_to_the_writer(document, fake_llm):
    fake_llm.on("Escribe UN SOLO PÁRRAFO", lambda prompt: " ".join(["[@smith2020emotion]"] * 7))

    PerspectiveRun(document).run()

    first, second = fake_llm.prompts_containing("Escribe UN SOLO PÁRRAFO")
    assert "OBRAS YA MUY CITADAS" not in first
    assert "OBRAS YA MUY CITADAS EN EL DOCUMENTO: [@smith2020emotion] (7 veces)" in second


def test_a_coherence_revision_that_adds_citations_or_changes_length_is_discarded(document, fake_llm):
    fake_llm.on("revisión final de coherencia de UNA sección", "Otro texto [@brown2021navigation].")

    PerspectiveRun(document).run()

    state = json.loads((document / STATE).read_text(encoding="utf-8"))
    assert state["revision_global_descartada"] == ["Introducción", "Conclusiones"]
    text = (document / "borrador" / "documento.md").read_text(encoding="utf-8")
    assert "Otro texto" not in text


def test_revision_is_safe_checks_citations_and_length():
    original = "Uno dos tres cuatro [@a] cinco seis siete ocho [@b]."
    assert revision_is_safe(original, "Uno dos tres cuatro cinco seis siete ocho nueve [@b].")
    assert not revision_is_safe(original, "Uno dos tres cuatro cinco seis siete ocho [@c].")
    assert not revision_is_safe(original, "Uno [@a].")
    assert not revision_is_safe(original, "")


def test_each_paragraph_is_offered_the_works_its_plan_ideas_come_from(document, fake_llm):
    outline = json.loads(json.dumps(DEFAULT_OUTLINE))
    outline["sections"][1]["paragraphs"][0]["source_keys"] = [
        "brown2021navigation", "green2022speech", "made2020up",
    ]
    fake_llm.on("planificador de papers", json.dumps(outline))

    PerspectiveRun(document).run()

    assert "(fuente: smith2020emotion)" in fake_llm.prompts_containing("planificador de papers")[0]
    intro, closing = fake_llm.prompts_containing("Escribe UN SOLO PÁRRAFO")
    assert "FUENTES DE LAS IDEAS DEL PLAN" not in intro
    plan_sources = closing.split("FUENTES DE LAS IDEAS DEL PLAN")[1].split("CONTEXTO PARA")[0]
    # only works of the document's collections, whatever the planner wrote
    assert set(re.findall(r"Citar: \[@([^\]]+)\]", plan_sources)) == {"brown2021navigation"}


@pytest.fixture
def revision_document(document, fake_llm):
    project = Project.load(document)
    project.perfil = "revision"
    project.save(document)
    outline = json.loads(json.dumps(DEFAULT_OUTLINE))
    outline["sections"][1]["section_name"] = "Síntesis Temática"
    fake_llm.on("planificador de papers", json.dumps(outline))
    return document


def test_each_profile_section_searches_with_its_own_config(revision_document, monkeypatch):
    seen = {}
    original = EnhancedContextManager.get_context_for_idea

    def spy(self, idea_query, section_name, suggested_topics=None, config=None):
        seen[section_name] = config
        return original(self, idea_query, section_name, suggested_topics, config)

    monkeypatch.setattr(EnhancedContextManager, "get_context_for_idea", spy)

    PerspectiveRun(revision_document).run()

    synthesis = PROFILES["revision"].section("Síntesis Temática").search
    assert synthesis is not None and synthesis.evidence_types is None
    assert seen["Síntesis Temática"] is synthesis
    # Introducción has no config of its own: the manager takes SECTION_CONFIGS' entry
    assert seen["Introducción"] is None


def test_every_section_of_every_profile_has_a_usable_search_config():
    for profile in PROFILES.values():
        for spec in profile.sections:
            assert (spec.search or SECTION_CONFIGS.get(spec.name)) is not None, (profile.name, spec.name)


def test_a_section_without_config_gets_the_neutral_default_not_introduccion(document, fake_llm, monkeypatch):
    run = PerspectiveRun(document)
    manager = run.context_manager("abstract")
    used = []
    original = manager._search_claims

    def spy(embedding, config, *args, **kwargs):
        used.append(config)
        return original(embedding, config, *args, **kwargs)

    monkeypatch.setattr(manager, "_search_claims", spy)

    manager.get_context_for_idea("emotion robots", "Sección inventada")
    manager.get_context_for_idea("emotion robots", "Sección inventada", config=PROFILES["ensayo"].sections[1].search)

    assert used[0] is DEFAULT_SECTION_CONFIG
    assert used[0] is not SECTION_CONFIGS["Introducción"]
    assert used[0].evidence_types is None
    assert used[1].evidence_types == ["experiment", "data"]


def test_later_sections_get_the_full_text_written_and_the_plan_ahead_not_summaries(document, fake_llm):
    replies = iter(["Texto único de la introducción [@smith2020emotion].", "Cierre [@smith2020emotion]."])
    fake_llm.on("Escribe UN SOLO PÁRRAFO", lambda prompt: next(replies))

    PerspectiveRun(document).run()

    intro, closing = fake_llm.prompts_containing("Escribe UN SOLO PÁRRAFO")
    assert "TEXTO YA ESCRITO" not in intro
    ahead = intro.split("PLAN DE LAS SECCIONES QUE FALTAN POR ESCRIBIR")[1].split("# PÁRRAFOS ANTERIORES")[0]
    assert "### Conclusiones" in ahead and "navigation and speech complete the picture" in ahead
    written = closing.split("TEXTO YA ESCRITO")[1].split("# PÁRRAFOS ANTERIORES")[0]
    assert "### Introducción\nTexto único de la introducción [@smith2020emotion]." in written
    assert "PLAN DE LAS SECCIONES" not in closing
    assert "no repitas" in closing
    # the section review and the global review see the other sections in full, never summaries
    reviews = fake_llm.prompts_containing("Revisa y mejora la siguiente sección")
    assert "Texto único de la introducción" in reviews[1]
    coherence = fake_llm.prompts_containing("revisión final de coherencia de UNA sección")
    assert "Cierre [@smith2020emotion]." in coherence[0]
    assert "Texto único de la introducción" in coherence[1]
    assert fake_llm.prompts_containing("Genera un resumen conciso") == []
    state = json.loads((document / STATE).read_text(encoding="utf-8"))
    assert all("resumen" not in section for section in state["secciones"])


def test_cited_claims_are_labelled_and_rank_below_own_findings(document, fake_llm):
    manager = PerspectiveRun(document).context_manager("abstract")
    base = {"paper_id": "p1", "paper_title": "Obra", "claim": "x", "evidence": "y", "confidence": "high"}
    own = {**base, "evidence_type": "experiment", "quote": "frase literal", "quote_verified": True}
    cited = {**base, "evidence_type": "citation", "origin": "citado"}
    same_origin = {**base, "evidence_type": "data", "origin": "citado"}

    assert "afirmación citada" not in manager._format_claim_compact(own, 1.0)
    assert "Cita literal: «frase literal»" in manager._format_claim_compact(own, 1.0)
    assert "(afirmación citada: el paper la apoya en otra obra)" in manager._format_claim_compact(cited, 1.0)
    assert "afirmación citada" in manager._format_claim_compact(same_origin, 1.0)
    idea = {"idea": "i", "paper_title": "Obra", "quote": "otra frase", "quote_verified": False}
    assert "Cita literal" not in manager._format_idea_compact(idea, 1.0)
    assert "Cita literal: «otra frase»" in manager._format_idea_compact({**idea, "quote_verified": True}, 1.0)

    config = SECTION_CONFIGS["Introducción"]
    ranked = manager._combine_and_diversify([], [(cited, 0.9, "claim"), (own, 0.9, "claim")], config)
    assert [item["evidence_type"] for item, _, _ in ranked] == ["experiment", "citation"]
    assert ranked[1][1] == pytest.approx(0.9 * CITED_CLAIM_WEIGHT)
    assert ranked[0][1] == pytest.approx(0.9)


def test_a_document_saved_with_old_summaries_resumes(document, fake_llm):
    assert PerspectiveRun(document).run()["estado"] == "terminado"
    state = json.loads((document / STATE).read_text(encoding="utf-8"))
    state["secciones"] = state["secciones"][:1]  # only the first section was written
    state["secciones"][0]["resumen"] = "Resumen antiguo."
    state.pop("revision_global_hecha")
    (document / STATE).write_text(json.dumps(state), encoding="utf-8")
    before = _writer_calls(fake_llm)

    status = PerspectiveRun(document).run()

    assert status["estado"] == "terminado"
    assert status["parrafos"] == "2/2"
    assert status["secciones_terminadas"] == ["Introducción", "Conclusiones"]
    assert _writer_calls(fake_llm) - before == 1
    assert fake_llm.prompts_containing("Genera un resumen conciso") == []


def test_closing_judges_the_support_of_every_citation(document, fake_llm):
    fake_llm.on("Escribe UN SOLO PÁRRAFO", "Los robots usan modelos de emoción [@smith2020emotion].")
    status = PerspectiveRun(document).run()

    assert status["estado"] == "terminado"
    support = json.loads((document / "revision" / "apoyo.json").read_text(encoding="utf-8"))
    assert support["resumen"]["apoyo"] == 1.0
    assert support["resumen"]["apoyada"] == len(support["entradas"]) > 0
    assert "## Apoyo de las citas" in (document / "revision" / "validacion.md").read_text(encoding="utf-8")


def test_the_run_records_what_the_writer_saw_under_the_drafts_section_titles(document, fake_llm):
    outline = json.loads(json.dumps(DEFAULT_OUTLINE))
    outline["sections"][1]["paragraphs"][0]["source_keys"] = ["brown2021navigation"]
    fake_llm.on("planificador de papers", json.dumps(outline))

    PerspectiveRun(document).run()

    seen = json.loads((document / "revision" / "evidencia_vista.json").read_text(encoding="utf-8"))
    draft = (document / "borrador" / "documento.md").read_text(encoding="utf-8")
    assert set(seen) == {"Introducción", "Conclusiones"}
    assert all(f"## {title}" in draft for title in seen)
    items = [item for by_key in seen.values() for stored in by_key.values() for item in stored]
    assert items and all(set(item) == {"clave", "tipo", "texto", "cita_literal", "origen"} for item in items)
    assert all(item["tipo"] in ("idea", "claim") for item in items)
    assert all((item["origen"] in ("citado", "propio")) == (item["tipo"] == "claim") for item in items)
    assert "brown2021navigation" in seen["Conclusiones"]


def test_resuming_does_not_duplicate_seen_items(document, fake_llm):
    PerspectiveRun(document).run()
    path = document / "revision" / "evidencia_vista.json"
    before = json.loads(path.read_text(encoding="utf-8"))

    from ai_writer.validation import record_seen
    for title, by_key in before.items():
        for stored in by_key.values():
            record_seen(document, title, stored)

    assert json.loads(path.read_text(encoding="utf-8")) == before
