"""Tests for the citation support judge."""

import json
import re

import pytest

from ai_writer.library import Library, Project
from ai_writer.llm import UsageLimitError
from ai_writer.support import (
    MAX_EVIDENCE, cited_paragraphs, judge_document, markdown, save, split_sentences, summary,
)
from tests.conftest import PAPERS


@pytest.fixture
def library(tmp_path, fake_llm, workspace):
    import json as _json

    for paper in PAPERS:
        folder = workspace.processed_dir / "papers" / paper["paper_id"]
        folder.mkdir(parents=True)
        metadata = {"paper_id": paper["paper_id"], "title": paper["paper_title"],
                    "authors": paper["authors"], "year": paper["year"],
                    "source_file": f"/pdfs/{paper['paper_id']}.pdf"}
        (folder / "metadata.json").write_text(_json.dumps(metadata), encoding="utf-8")
        (folder / "ideas.jsonl").write_text('{"idea": "x"}', encoding="utf-8")
    library = Library(tmp_path / "biblioteca")
    library.migrate_from(workspace.processed_dir)
    return library


def _document(library, tmp_path, text):
    library.save_collection("Robots", library.find_papers(["emotion models", "crowded"]))
    folder = tmp_path / "doc"
    Project.create(folder, tipo="perspectiva", titulo="T", colecciones=["Robots"],
                   biblioteca=library.root)
    (folder / "borrador" / "documento.md").write_text(text, encoding="utf-8")
    return folder


def _verdicts(*verdicts):
    return json.dumps({"veredictos": [
        {"n": i, "veredicto": v, "motivo": f"motivo {i}"} for i, v in enumerate(verdicts, 1)
    ]})


def _judge_calls(fake_llm):
    return fake_llm.prompts_containing("revisor estricto de citas")


def test_sentences_are_not_split_inside_citations_or_on_abbreviations():
    text = ("Smith et al. mostraron un 3.5 % más [@a2020x; @b2021y, p. 4]. "
            "Otros, e.g. Lee, lo niegan [@c2022z]. Es decir, i.e. así. Fin!")

    assert split_sentences(text) == [
        "Smith et al. mostraron un 3.5 % más [@a2020x; @b2021y, p. 4].",
        "Otros, e.g. Lee, lo niegan [@c2022z].",
        "Es decir, i.e. así.",
        "Fin!",
    ]


def test_a_citation_after_the_full_stop_stays_with_its_sentence():
    assert split_sentences("Sienten. [@a2020x] Otra cosa.") == ["Sienten. [@a2020x]", "Otra cosa."]


def test_one_entry_per_sentence_and_key_and_gaps_are_ignored():
    text = ("# T\n\n## Intro\nUna [@smith2020emotion; @brown2021navigation]. Hueco [@?]. "
            "Sin cita.\n\nOtra más [@smith2020emotion].\n\n## Fin\nNada.\n")

    paragraphs = cited_paragraphs(text)

    assert [(p["seccion"], [(s, k) for s, k in p["frases"]]) for p in paragraphs] == [
        ("Intro", [("Una [@smith2020emotion; @brown2021navigation].",
                    ["smith2020emotion", "brown2021navigation"])]),
        ("Intro", [("Otra más [@smith2020emotion].", ["smith2020emotion"])]),
    ]


def test_one_call_per_cited_paragraph_and_none_without_citations(library, tmp_path, fake_llm):
    folder = _document(library, tmp_path, (
        "## Intro\nPárrafo sin citas. Otra frase.\n\n"
        "Robot emotion [@smith2020emotion]. Navigation [@brown2021navigation].\n\n"
        "## Fin\nRobot emotion otra vez [@smith2020emotion].\n"
    ))
    fake_llm.on("revisor estricto de citas", lambda prompt: _verdicts(
        *(["apoyada", "parcial"] if "Navigation" in prompt else ["no_apoyada"])))

    entries = judge_document(folder)

    assert len(_judge_calls(fake_llm)) == 2
    assert [(e["seccion"], e["clave"], e["veredicto"]) for e in entries] == [
        ("Intro", "smith2020emotion", "apoyada"),
        ("Intro", "brown2021navigation", "parcial"),
        ("Fin", "smith2020emotion", "no_apoyada"),
    ]
    assert entries[1]["motivo"] == "motivo 2"
    assert set(entries[0]) == {"seccion", "frase", "clave", "veredicto", "motivo", "cita_literal"}


def test_a_work_without_evidence_is_not_supported_and_costs_no_call(library, tmp_path, fake_llm):
    folder = _document(library, tmp_path, "Robot emotion [@made2020up].\n")

    entries = judge_document(folder)

    assert [(e["veredicto"], e["cita_literal"]) for e in entries] == [("no_apoyada", None)]
    assert entries[0]["motivo"].startswith("La biblioteca no tiene evidencia")
    assert _judge_calls(fake_llm) == []


def test_evidence_is_shown_to_the_judge_and_literal_quote_is_returned(library, tmp_path, fake_llm, monkeypatch):
    from ai_writer.evidence import EvidenceEngine

    item = {"clave": "smith2020emotion", "tipo": "claim", "texto": "robots sienten",
            "evidencia": "dato", "relevancia": 0.9, "origen": "citado",
            "cita_literal": "Robots do feel.", "cita_verificada": True}
    monkeypatch.setattr(EvidenceEngine, "search", lambda self, *a, **k: [item])
    folder = _document(library, tmp_path, "Los robots sienten [@smith2020emotion].\n")
    fake_llm.on("revisor estricto de citas", _verdicts("parcial"))

    entries = judge_document(folder)

    prompt = _judge_calls(fake_llm)[0]
    assert "CITA LITERAL: «Robots do feel.»" in prompt and "CITADO" in prompt
    assert entries[0]["cita_literal"] == "Robots do feel."


def _found(text, key="smith2020emotion"):
    return {"clave": key, "tipo": "idea", "texto": text, "contexto": "", "cita_literal": None}


def _stored(text, key="smith2020emotion", quote=None):
    return {"clave": key, "tipo": "idea", "texto": text, "cita_literal": quote, "origen": None}


def test_items_the_writer_saw_in_the_section_join_the_sentence_search(library, tmp_path, fake_llm, monkeypatch):
    from ai_writer.evidence import EvidenceEngine
    from ai_writer.validation import record_seen

    monkeypatch.setattr(EvidenceEngine, "search", lambda self, *a, **k: [_found("cercano"), _found("repetido")])
    folder = _document(library, tmp_path, "## Intro\n\nLos robots sienten [@smith2020emotion].\n")
    record_seen(folder, "Intro", [_stored("repetido"), _stored("visto", quote="Literal vista.")])
    record_seen(folder, "Otra", [_stored("de otra sección")])
    fake_llm.on("revisor estricto de citas", _verdicts("apoyada"))

    entries = judge_document(folder)

    prompt = _judge_calls(fake_llm)[0]
    assert prompt.count("repetido") == 1 and "visto" in prompt and "otra sección" not in prompt
    assert prompt.index("cercano") < prompt.index("visto")
    assert entries[0]["cita_literal"] == "Literal vista."


def test_evidence_shown_is_capped(library, tmp_path, fake_llm, monkeypatch):
    from ai_writer.evidence import EvidenceEngine
    from ai_writer.validation import record_seen

    monkeypatch.setattr(EvidenceEngine, "search", lambda self, *a, **k: [_found(f"cerca{i}") for i in range(5)])
    folder = _document(library, tmp_path, "## Intro\n\nLos robots sienten [@smith2020emotion].\n")
    record_seen(folder, "Intro", [_stored(f"visto{i}") for i in range(20)])
    fake_llm.on("revisor estricto de citas", _verdicts("apoyada"))

    judge_document(folder)

    prompt = _judge_calls(fake_llm)[0]
    assert len(re.findall(r"^  \d+\. ", prompt, re.M)) == MAX_EVIDENCE
    assert "cerca4" in prompt and "visto6" in prompt and "visto7" not in prompt


def test_without_a_seen_record_the_paragraph_queries_of_the_work_are_searched(library, tmp_path, fake_llm, monkeypatch):
    from ai_writer.evidence import EvidenceEngine
    from ai_writer.validation import record_retrieved

    def search(self, query, n=8, **kwargs):
        return [_found(f"resultado de {query}")]

    monkeypatch.setattr(EvidenceEngine, "search", search)
    folder = _document(library, tmp_path, "## Intro\n\nLos robots sienten [@smith2020emotion].\n")
    record_retrieved(folder, "consulta uno", ["smith2020emotion"])
    record_retrieved(folder, "consulta dos", ["smith2020emotion", "brown2021navigation"])
    fake_llm.on("revisor estricto de citas", _verdicts("apoyada"))

    judge_document(folder)

    prompt = _judge_calls(fake_llm)[0]
    assert "resultado de consulta uno" in prompt and "resultado de consulta dos" in prompt


def test_the_no_evidence_shortcut_needs_every_source_empty(library, tmp_path, fake_llm, monkeypatch):
    from ai_writer.evidence import EvidenceEngine
    from ai_writer.validation import record_seen

    monkeypatch.setattr(EvidenceEngine, "search", lambda self, *a, **k: [])
    folder = _document(library, tmp_path, "## Intro\n\nLos robots sienten [@smith2020emotion].\n")
    fake_llm.on("revisor estricto de citas", _verdicts("apoyada"))
    assert judge_document(folder)[0]["veredicto"] == "no_apoyada" and _judge_calls(fake_llm) == []

    record_seen(folder, "Intro", [_stored("visto")])
    assert judge_document(folder)[0]["veredicto"] == "apoyada"


@pytest.mark.parametrize("answer", ["no es json", '{"otra": 1}', '[{"n": 1, "veredicto": "quizá"}]'])
def test_an_unreadable_answer_is_unjudged_never_support(library, tmp_path, fake_llm, answer):
    folder = _document(library, tmp_path, "Robot emotion [@smith2020emotion].\n")
    fake_llm.on("revisor estricto de citas", answer)

    entries = judge_document(folder)

    assert entries[0]["veredicto"] == "sin_juzgar"
    assert entries[0]["motivo"]
    assert summary(entries)["apoyo"] is None


def test_usage_limit_propagates(library, tmp_path, fake_llm):
    folder = _document(library, tmp_path, "Robot emotion [@smith2020emotion].\n")

    def limit(prompt):
        raise UsageLimitError("límite")

    class Limited:
        def complete_json(self, system, user, **kwargs):
            raise UsageLimitError("límite")

    with pytest.raises(UsageLimitError):
        judge_document(folder, llm=Limited())


def _entry(verdict, key="a2020x"):
    return {"seccion": "S", "frase": f"frase {verdict}", "clave": key, "veredicto": verdict,
            "motivo": f"porque {verdict}", "cita_literal": "texto literal" if verdict == "parcial" else None}


def test_summary_counts_and_support_share():
    entries = [_entry("apoyada"), _entry("apoyada"), _entry("parcial"), _entry("no_apoyada"),
               _entry("sin_juzgar")]

    assert summary(entries) == {"apoyada": 2, "parcial": 1, "no_apoyada": 1, "sin_juzgar": 1,
                                "apoyo": 0.5}
    assert summary([_entry("sin_juzgar")])["apoyo"] is None
    assert summary([])["apoyo"] is None
    assert summary([_entry("apoyada")] * 2 + [_entry("parcial")])["apoyo"] == 0.667


def test_markdown_lists_worst_first_and_collapses_the_supported(tmp_path):
    entries = [_entry("apoyada"), _entry("sin_juzgar"), _entry("parcial"), _entry("no_apoyada")]

    text = markdown(entries)

    assert text.startswith("## Apoyo de las citas")
    order = [text.index(f"frase {v}") for v in ("no_apoyada", "parcial", "sin_juzgar")]
    assert order == sorted(order)
    assert "frase apoyada" not in text and "1 citas están apoyadas" in text
    assert "Cita literal de la obra: «texto literal»" in text
    assert "Motivo: porque parcial" in text


def test_save_writes_entries_and_summary(tmp_path):
    entries = [_entry("apoyada")]

    path = save(tmp_path, entries)

    assert path == tmp_path / "revision" / "apoyo.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["entradas"] == entries and data["resumen"]["apoyo"] == 1.0
