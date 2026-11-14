"""PDF processing: one call per segment, verbatim quotes, no bibliography.

The synthetic paper has a tiny abstract (merged into its neighbour), an
acknowledgements section (skipped) and a section the model names but the text lacks,
so the expected calls are 2 (metadata, structure) plus one per remaining segment.
"""

import json

import pytest

from ai_writer.library import Library
from ai_writer.llm import UsageLimitError
from ai_writer.processors.batch_processor import BatchProcessor
from ai_writer.processors.extraction_agent import IDEA_KINDS, SECTION_ATTEMPTS, PDFExtractionAgent

STRUCTURE = [
    "Abstract",
    "Introduction",
    "Methods",
    "Discussion",  # named by the model, absent from the text
    "Acknowledgements",
    "Results",
    "References",
]
SEGMENTS = 3  # "Abstract / Introduction", "Methods", "Results"
INVENTED = "This sentence was invented by the model and it never appears in the paper at all."
PDF_NAME = "paper.pdf"


def _body(tag: str, n: int = 20) -> str:
    return " ".join(
        f"The {tag} study number {i} reports that measure {i} changes after training." for i in range(n)
    )


PAPER_TEXT = f"""Empathy Models in Robots
Ana Smith

Abstract
Short abstract of about twenty words that summarizes the paper in a very tiny section only.

1. Introduction
{_body("intro")}

2. Methods
{_body("method")}

Acknowledgements
We thank everyone who helped us with this work during the long project years.

3. Results
{_body("result")}

References
Smith, A. (2020). Something. Journal.
"""


class FakeReader:
    """Stands in for PDFReader: the text of each file comes from a dict."""

    def __init__(self, texts: dict[str, str]) -> None:
        self.texts = texts

    def read(self, path):
        return self.texts[path.name]

    def get_metadata(self, path):
        return {"page_count": 3}


def _content(prompt: str) -> str:
    return prompt.split("CONTENT:\n", 1)[1].split("\n\nReturn ONE JSON", 1)[0]


def _section(prompt: str) -> str:
    return prompt.split("SECTION: ", 1)[1].split("\n", 1)[0]


def _quote(prompt: str, words: int = 14) -> str:
    return " ".join(_content(prompt).split()[:words])


def _answer(prompt: str) -> str:
    """Two ideas and three claims: a verified pair, plus one invented idea."""
    quote = _quote(prompt)
    return json.dumps(
        {
            "ideas": [
                {"idea": f"Idea de {_section(prompt)}", "context": "c", "kind": " Method ", "quote": quote},
                {"idea": f"Idea inventada de {_section(prompt)}", "context": "c", "kind": "opinion",
                 "quote": INVENTED},
            ],
            "claims": [
                {"claim": "Hallazgo", "evidence": "e", "evidence_type": " Experiment ", "quote": quote},
                {"claim": "Recoge otra obra", "evidence": "e", "evidence_type": "citation", "quote": quote},
                {"claim": "Otra cosa", "evidence": "e", "evidence_type": "anecdote", "quote": quote},
            ],
        }
    )


@pytest.fixture
def batch(fake_llm, tmp_path):
    """A BatchProcessor over one fake PDF, with the model scripted for the synthetic paper."""
    root = tmp_path / "biblioteca"
    (root / "pdfs").mkdir(parents=True)
    (root / "pdfs" / PDF_NAME).write_bytes(b"")
    fake_llm.on("identify its section structure", json.dumps(
        [{"section_name": name, "section_number": i} for i, name in enumerate(STRUCTURE, 1)]
    ))
    fake_llm.on("MAIN IDEAS and its CLAIMS", _answer)
    processor = BatchProcessor(pdfs_folder=root / "pdfs", output_folder=root / "procesado")
    processor.pdf_processor.pdf_reader = FakeReader({PDF_NAME: PAPER_TEXT})
    processor.root = root
    return processor


def _run(batch: BatchProcessor) -> dict:
    return batch.process_all(build_embeddings=False)


def _paper_dir(batch: BatchProcessor):
    (folder,) = (batch.output_folder / "papers").iterdir()
    return folder


def _rows(path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_one_llm_call_per_segment(batch, fake_llm):
    _run(batch)

    segment_calls = fake_llm.prompts_containing("MAIN IDEAS and its CLAIMS")
    assert len(segment_calls) == SEGMENTS
    assert len(fake_llm.calls) == 2 + SEGMENTS
    assert [_section(p) for p in segment_calls] == ["Abstract / Introduction", "Methods", "Results"]
    # Each segment's text is sent once, with no overlap and without the acknowledgements
    texts = " ".join(_content(p) for p in segment_calls)
    assert "We thank everyone" not in texts
    assert texts.count("intro study number 7 ") == 1


def test_prompt_requires_a_verbatim_quote(batch, fake_llm):
    _run(batch)

    prompt = fake_llm.prompts_containing("MAIN IDEAS and its CLAIMS")[0]
    assert "between 8 and 40 words" in prompt
    assert "DISCARDED" in prompt
    assert fake_llm.calls[-1]["request"].max_tokens == 8000


def test_unverified_items_are_kept_in_the_paper_but_not_indexed(batch):
    _run(batch)

    folder = _paper_dir(batch)
    ideas = _rows(folder / "ideas.jsonl")
    assert len(ideas) == 2 * SEGMENTS
    assert [i["quote_verified"] for i in ideas].count(False) == SEGMENTS
    assert all(i["quote"] for i in ideas)

    indexed = _rows(batch.output_folder / "indices" / "all_ideas.jsonl")
    assert len(indexed) == SEGMENTS
    assert all(i["quote_verified"] for i in indexed)
    assert not any("inventada" in i["idea"] for i in indexed)
    assert len(_rows(batch.output_folder / "indices" / "all_claims.jsonl")) == 3 * SEGMENTS


def test_idea_kind_is_stored_and_unknown_values_become_none(batch, fake_llm):
    _run(batch)

    ideas = _rows(_paper_dir(batch) / "ideas.jsonl")
    assert [i["kind"] for i in ideas[:2]] == ["method", None]
    prompt = fake_llm.prompts_containing("MAIN IDEAS and its CLAIMS")[0]
    for kind in IDEA_KINDS:
        assert f"- {kind}:" in prompt


def test_claims_get_origin_and_normalised_evidence_type(batch):
    _run(batch)

    claims = _rows(_paper_dir(batch) / "claims.jsonl")[:3]
    assert [(c["evidence_type"], c["origin"]) for c in claims] == [
        ("experiment", "propio"),
        ("citation", "citado"),
        ("observation", "propio"),
    ]
    assert all(c["quote_verified"] for c in claims)


def test_metadata_records_the_processing(batch, fake_llm):
    _run(batch)

    procesado = json.loads((_paper_dir(batch) / "metadata.json").read_text(encoding="utf-8"))["procesado"]
    assert procesado["metodo"] == 2
    assert procesado["llamadas"] == len(fake_llm.calls) == 2 + SEGMENTS
    assert procesado["tramos"] == SEGMENTS
    assert procesado["segundos"] >= 0


def test_no_bibliography_is_extracted(batch, fake_llm):
    summary = _run(batch)

    assert not fake_llm.prompts_containing("bibliography")
    folder = _paper_dir(batch)
    assert not (folder / "references.jsonl").exists()
    assert not (batch.output_folder / "indices" / "all_references.jsonl").exists()
    assert "total_references" not in summary
    # Nothing downstream needs the file: the library lists the paper with 0 references
    (paper,) = Library(batch.root).papers()
    assert paper.references == 0
    assert paper.ideas == SEGMENTS  # only verified ideas are counted
    assert paper.claims == 3 * SEGMENTS


def test_unreadable_answer_is_asked_again(batch, fake_llm):
    answers = iter(["no es JSON"])
    fake_llm.on(
        "MAIN IDEAS and its CLAIMS",
        lambda prompt: next(answers, None) or _answer(prompt),
    )

    summary = _run(batch)

    assert summary["processed_successfully"] == 1
    assert len(fake_llm.calls) == 2 + SEGMENTS + 1


def test_unreadable_answer_after_retries_leaves_the_paper_pending(batch, fake_llm):
    fake_llm.on("MAIN IDEAS and its CLAIMS", "no es JSON")

    summary = _run(batch)

    assert summary["failed"] == 1
    assert len(fake_llm.prompts_containing("MAIN IDEAS and its CLAIMS")) == SECTION_ATTEMPTS
    assert not list((batch.output_folder / "papers").iterdir())
    assert not (batch.output_folder / "indices" / "all_ideas.jsonl").exists()
    assert [p.name for p in batch.get_pdfs_to_process()] == [PDF_NAME]


def test_paper_with_only_unverified_items_is_treated_as_failed(batch, fake_llm):
    fake_llm.on(
        "MAIN IDEAS and its CLAIMS",
        json.dumps(
            {
                "ideas": [{"idea": "i", "quote": INVENTED}],
                "claims": [{"claim": "c", "evidence_type": "data", "quote": INVENTED}],
            }
        ),
    )

    summary = _run(batch)

    assert summary["failed"] == 1
    assert not list((batch.output_folder / "papers").iterdir())
    assert [p.name for p in batch.get_pdfs_to_process()] == [PDF_NAME]
    status = batch.status["processed"][PDF_NAME]
    assert status["success"] is False
    assert "verificado" in status["error"]


def test_usage_limit_stops_the_batch_without_marking_the_paper(batch, fake_llm):
    def limit(prompt):
        raise UsageLimitError("You've hit your limit")

    fake_llm.on("MAIN IDEAS and its CLAIMS", limit)

    summary = _run(batch)

    assert PDF_NAME not in batch.status["processed"]
    assert summary["failed"] == 0
    assert [p.name for p in batch.get_pdfs_to_process()] == [PDF_NAME]


def test_sections_fall_back_to_size_based_segments_when_structure_is_unreadable(fake_llm):
    fake_llm.on("identify its section structure", "no es JSON")
    text = "Plain text without any heading. " + _body("flat", 40)

    sections = PDFExtractionAgent().extract_sections(text)

    assert len(fake_llm.prompts_containing("identify its section structure")) == 3
    assert [s["section_name"] for s in sections] == ["Texto"]
    assert [s["section_number"] for s in sections] == [1]
    assert "flat study number 39" in sections[0]["content"]
