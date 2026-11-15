"""Tests for citation keys, Zotero import, citation checks and evidence search.

Run from the repository root with ``python -m pytest`` so that ``config`` is importable.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ai_writer.citations import CitationIndex, check_citations, find_citations, make_key
from ai_writer.evidence import EvidenceEngine
from ai_writer.library import Library, Project
from ai_writer.validation import record_retrieved, validate_document
from tests.conftest import PAPERS

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture
def library(tmp_path, fake_llm, workspace):
    """The synthetic corpus as a library, plus a duplicate of the emotion paper."""
    papers = [*PAPERS, {**PAPERS[0], "paper_id": "paper-emotion-copy"}]
    for paper in papers:
        folder = workspace.processed_dir / "papers" / paper["paper_id"]
        folder.mkdir(parents=True)
        metadata = {
            "paper_id": paper["paper_id"],
            "title": paper["paper_title"],
            "authors": paper["authors"],
            "year": paper["year"],
            "doi": "10.1/emotion" if paper["word"] == "emotion" else None,
            "source_file": f"/pdfs/{paper['paper_id']}.pdf",
        }
        (folder / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
        (folder / "ideas.jsonl").write_text(
            "\n".join('{"idea": "x"}' for _ in range(2 if paper["paper_id"] == "paper-emotion" else 1)),
            encoding="utf-8",
        )
    library = Library(tmp_path / "biblioteca")
    library.migrate_from(workspace.processed_dir)
    return library


def test_keys_are_bibtex_style_and_unique():
    taken = set()
    first = make_key(["Ana Smith"], 2020, "The Emotion Models", taken)
    taken.add(first)

    assert first == "smith2020emotion"
    assert make_key(["Smith, Ana"], 2020, "Emotion again", taken) == "smith2020emotionb"
    assert make_key([], None, "Á la carte", set()) == "anonimosfcarte"


def test_index_assigns_keys_merges_duplicates_and_writes_the_bibliography(library):
    index = CitationIndex.load(library)

    assert sorted(index.citables()) == [
        "brown2021navigation", "green2022speech", "smith2020emotion"
    ]
    assert index.key_for("paper-emotion-copy") == "smith2020emotion"
    assert index.citables()["smith2020emotion"].paper_ids == ("paper-emotion", "paper-emotion-copy")
    bib = library.bib_file.read_text(encoding="utf-8")
    assert "@article{smith2020emotion," in bib
    assert "author = {Ana Smith and Bo Jones and Cy Lee}" in bib


def test_keys_survive_new_papers(library):
    before = CitationIndex.load(library).citables()
    folder = library.processed_dir / "papers" / "paper-new"
    folder.mkdir()
    (folder / "metadata.json").write_text(json.dumps(
        {"paper_id": "paper-new", "title": "Emotion Models Revisited", "authors": ["Al Smith"],
         "year": 2020}
    ), encoding="utf-8")

    after = CitationIndex.load(library)

    assert set(before) <= set(after.citables())
    assert after.key_for("paper-new") == "smith2020emotionb"


def test_zotero_keys_and_data_win_for_matched_papers(library, tmp_path):
    bib = tmp_path / "zotero.bib"
    bib.write_text("""
@article{smithEmotionModels2020,
  title = {Emotion {Models} for Social Robots},
  author = {Smith, Ana and Jones, Bo and Lee, Cy},
  journal = {HRI Journal},
  year = {2020},
  doi = {10.1/EMOTION}
}
@article{otherPaper2019,
  title = {A Paper Not in the Library},
  year = {2019}
}
""", encoding="utf-8")

    result = CitationIndex.load(library).import_zotero(bib)

    assert result == {"emparejadas": ["smithEmotionModels2020"], "sin_paper": ["otherPaper2019"]}
    index = CitationIndex.load(library)
    citable = index.citables()["smithEmotionModels2020"]
    assert citable.source == "zotero" and citable.venue == "HRI Journal"
    assert index.key_for("paper-emotion-copy") == "smithEmotionModels2020"
    assert "smith2020emotion" not in index.citables()


def test_find_citations_accepts_pandoc_syntax_and_flags_the_old_format():
    keys, malformed, pending = find_citations(
        "A [@smith2020emotion]. B [@a2020x; @b2021y, p. 4]. C [@Brown et al., 2020]. D [@?]."
    )

    assert keys == ["smith2020emotion", "a2020x", "b2021y"]
    assert malformed == ["[@Brown et al., 2020]"]
    assert pending == 1


def test_check_citations_separates_unknown_outside_and_never_retrieved(library):
    index = CitationIndex.load(library)
    text = "[@smith2020emotion] [@brown2021navigation] [@green2022speech] [@made2020up]"

    report = check_citations(
        text, index, allowed_keys={"smith2020emotion", "brown2021navigation"},
        retrieved_keys={"smith2020emotion"},
    )

    assert not report.ok
    assert report.unknown == ["made2020up"]
    assert report.outside == ["green2022speech"]
    assert report.not_retrieved == ["brown2021navigation"]
    assert "No existen en la biblioteca: made2020up" in report.summary()


def test_evidence_search_stays_in_the_collections_and_cites_by_key(library):
    library.save_collection("Robots", library.find_papers(["emotion models", "crowded"]))
    engine = EvidenceEngine(library, library.paper_ids(["Robots"]))

    results = engine.search("robot speech idea", n=10)

    assert results
    assert {r["clave"] for r in results} <= {"smith2020emotion", "brown2021navigation"}
    assert all(r["cita"] == f"[@{r['clave']}]" for r in results)
    per_key = [r["clave"] for r in results]
    assert max(per_key.count(key) for key in set(per_key)) <= 2
    assert engine.reference("green2022speech")["en_colecciones_del_documento"] is False


def write_sections(library, paper_id, sections):
    """Processed sections of a paper, as ``{name: content}`` files like the PDF processor writes."""
    folder = library.processed_dir / "papers" / paper_id / "sections"
    folder.mkdir(parents=True, exist_ok=True)
    for number, (name, content) in enumerate(sections.items(), 1):
        data = {"section_name": name, "section_number": number, "content": content}
        (folder / f"{number:02d}_{name}.json").write_text(json.dumps(data), encoding="utf-8")


def test_passage_returns_the_full_section_of_a_work_within_the_documents_papers(library):
    write_sections(library, "paper-emotion", {"Introduction": "Texto completo de la introducción.", "Results": "Resultados."})
    write_sections(library, "paper-speech", {"Introduction": "Habla."})
    library.save_collection("Robots", library.find_papers(["emotion models", "crowded"]))
    engine = EvidenceEngine(library, library.paper_ids(["Robots"]))

    assert engine.passage("smith2020emotion", "Introduction") == "Texto completo de la introducción."
    assert engine.passage("smith2020emotion", "  introduction ") == "Texto completo de la introducción."
    assert engine.passage("smith2020emotion", "Discussion") is None
    assert engine.passage("smith2020emotion", "") is None
    assert engine.passage("made2020up", "Introduction") is None
    # green2022speech has the section but is not in the document's papers
    assert engine.passage("green2022speech", "Introduction") is None
    assert EvidenceEngine(library).passage("green2022speech", "Introduction") == "Habla."
    # the duplicate of a work counts only when it belongs to the document
    only_copy = EvidenceEngine(library, {"paper-emotion-copy"})
    assert only_copy.passage("smith2020emotion", "Introduction") is None


def test_topics_cover_only_the_documents_papers(library):
    library.save_collection("Robots", library.find_papers(["emotion models", "crowded"]))
    engine = EvidenceEngine(library, library.paper_ids(["Robots"]))

    topics = engine.topics(n_topics=2)

    assert sum(topic.ideas for topic in topics) == 24
    keys = {ex["clave"] for topic in topics for ex in topic.examples}
    assert keys <= {"smith2020emotion", "brown2021navigation"}
    topic_results = engine.search("robot", n=5, topic=topics[0].id)
    assert {r["clave"] for r in topic_results} <= keys | {"smith2020emotion", "brown2021navigation"}


def _document(library, tmp_path, text):
    library.save_collection("Robots", library.find_papers(["emotion models", "crowded"]))
    folder = tmp_path / "doc"
    Project.create(folder, tipo="perspectiva", titulo="T", colecciones=["Robots"],
                   biblioteca=library.root)
    (folder / "borrador" / "documento.md").write_text(text, encoding="utf-8")
    return folder


def test_validate_document_reports_citations_gaps_and_lengths(library, tmp_path):
    folder = _document(library, tmp_path, (
        "# Robots\n\n## Introducción\nRobots [@smith2020emotion] sienten [[PENDIENTE: dato]].\n\n"
        "## Conclusiones\nFin [@brown2021navigation].\n"
    ))
    record_retrieved(folder, "robots", ["smith2020emotion"])

    report = validate_document(folder)

    assert report.ok
    assert report.citations.not_retrieved == ["brown2021navigation"]
    assert report.gaps == ["[[PENDIENTE: dato]]"]
    assert report.words_per_section == {"Introducción": 2, "Conclusiones": 1}
    assert "## Huecos pendientes" in (folder / "revision" / "validacion.md").read_text(encoding="utf-8")


def _run_hook(folder, monkeypatch_env):
    event = {"tool_input": {"file_path": str(folder / "borrador" / "documento.md")}}
    completed = subprocess.run(
        [sys.executable, str(REPO / "hooks" / "validar.py")],
        input=json.dumps(event), capture_output=True, text=True, encoding="utf-8",
        env=monkeypatch_env, timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout) if completed.stdout.strip() else None


def test_hook_blocks_invented_citations_and_stays_quiet_when_all_is_well(library, tmp_path):
    import os

    env = os.environ | {"PYTHONPATH": ""}
    folder = _document(library, tmp_path, "Robots [@smith2020emotion] y [@made2020up].")

    blocked = _run_hook(folder, env)
    assert blocked["decision"] == "block"
    assert "made2020up" in blocked["reason"]

    (folder / "borrador" / "documento.md").write_text("Robots [@smith2020emotion].", encoding="utf-8")
    assert _run_hook(folder, env) is None


def test_gaps_get_suggested_sources_from_the_collections_only(library):
    library.save_collection("Robots", library.find_papers(["emotion models", "crowded"]))
    engine = EvidenceEngine(library, library.paper_ids(["Robots"]))

    gaps = engine.sources_for_gaps(
        "Los robots usan modelos de emoción [@?]. Esto está citado [@smith2020emotion].",
        min_relevance=-1,
    )

    assert [gap["frase"] for gap in gaps] == ["Los robots usan modelos de emoción [@?]."]
    keys = [source["clave"] for source in gaps[0]["fuentes"]]
    assert keys and len(keys) == len(set(keys))
    assert set(keys) <= {"smith2020emotion", "brown2021navigation"}


def _engine(library):
    library.save_collection("Robots", library.find_papers(["emotion models", "crowded", "speech"]))
    return EvidenceEngine(library, library.paper_ids(["Robots"]))


def test_idea_results_expose_the_kind(library):
    engine = _engine(library)
    engine.ideas.items[0]["kind"] = "limitation"
    results = engine.search("robot", n=50, kind="ideas", max_per_paper=12)
    by_text = {r["texto"]: r["clase"] for r in results}
    assert by_text[engine.ideas.items[0]["idea"]] == "limitation"
    assert None in by_text.values()


def test_search_ranks_cited_claims_below_own_findings_and_exposes_origin(library):
    engine = _engine(library)
    items = engine.claims.items
    own = next(i for i, c in enumerate(items) if c["paper_id"] == "paper-navigation")
    cited = next(i for i, c in enumerate(items) if c["paper_id"] == "paper-emotion")
    engine.claims._embeddings_matrix[own] = engine.claims._embeddings_matrix[cited]
    items[cited]["evidence_type"] = "citation"
    items[own]["evidence_type"] = "experiment"
    items[own].update(quote="Literal sentence.", quote_verified=True)

    results = engine.search("robot", n=20, kind="claims", max_per_paper=4)
    by_text = {r["texto"]: r for r in results}
    a, b = by_text[items[own]["claim"]], by_text[items[cited]["claim"]]
    assert (a["origen"], b["origen"]) == ("propio", "citado")
    assert results.index(a) < results.index(b)
    assert b["relevancia"] == pytest.approx(a["relevancia"] * 0.85, abs=2e-3)
    assert (a["cita_literal"], a["cita_verificada"]) == ("Literal sentence.", True)
    assert (b["cita_literal"], b["cita_verificada"]) == (None, None)


def test_search_origin_field_wins_and_ideas_expose_the_quote(library):
    engine = _engine(library)
    engine.claims.items[0].update(origin="propio", evidence_type="citation")
    engine.ideas.items[0].update(quote="Verbatim.", quote_verified=False)
    claim = engine.search("robot", n=50, kind="claims", max_per_paper=12)
    assert next(r for r in claim if r["texto"] == engine.claims.items[0]["claim"])["origen"] == "propio"
    idea = next(r for r in engine.search("robot", n=50, kind="ideas", max_per_paper=12)
                if r["texto"] == engine.ideas.items[0]["idea"])
    assert (idea["cita_literal"], idea["cita_verificada"]) == ("Verbatim.", False)
    assert "origen" not in idea
