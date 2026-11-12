"""Shared test harness: a scripted fake LLM and a synthetic corpus.

Nothing here touches the network. ``fake_llm`` replaces the shared LLM client
and embedder, and ``workspace`` points ``settings.paths`` at ``tmp_path``.
"""

import json
import zlib
from types import SimpleNamespace

import numpy as np
import pytest

from ai_writer.embeddings.embedder import set_embedder
from ai_writer.llm import LLMClient, LLMRequest, LLMResponse, set_llm_client
from config.settings import settings

EMBEDDING_DIMS = 64

PAPERS = [
    {
        "paper_id": "paper-emotion",
        "paper_title": "Emotion Models for Social Robots",
        "authors": ["Ana Smith", "Bo Jones", "Cy Lee"],
        "year": 2020,
        "word": "emotion",
    },
    {
        "paper_id": "paper-navigation",
        "paper_title": "Navigation in Crowded Spaces",
        "authors": ["Dana Brown", "Eli White"],
        "year": 2021,
        "word": "navigation",
    },
    {
        "paper_id": "paper-speech",
        "paper_title": "Speech Interfaces for Assistants",
        "authors": ["Fay Green"],
        "year": 2022,
        "word": "speech",
    },
]
IDEAS_PER_PAPER = 12

# Resolvable by ReferenceProcessor as "Smith et al., 2020".
KNOWN_CITATION = "[@Smith et al., 2020]"
KNOWN_REFERENCE = "Smith, A., Jones, B., Lee, C. Emotion models for social robots. HRI Journal, 2020."

DEFAULT_OUTLINE = {
    "thesis_statement": "Social robots need grounded emotion models.",
    "sections": [
        {
            "section_name": "Introducción",
            "section_purpose": "Presentar el tema",
            "paragraphs": [
                {
                    "paragraph_number": 1,
                    "key_idea": "emotion models matter for robots",
                    "supporting_points": ["emotion drives interaction"],
                    "suggested_sources": ["Emotion Models for Social Robots"],
                }
            ],
        },
        {
            "section_name": "Conclusiones",
            "section_purpose": "Sintetizar",
            "paragraphs": [
                {
                    "paragraph_number": 1,
                    "key_idea": "navigation and speech complete the picture",
                    "supporting_points": [],
                    "suggested_sources": [],
                }
            ],
        },
    ],
}


def fake_embedding(text: str) -> list[float]:
    """Deterministic bag-of-words embedding: shared words give close vectors."""
    vec = np.zeros(EMBEDDING_DIMS, dtype=np.float32)
    for word in text.lower().split():
        vec[zlib.crc32(word.encode("utf-8")) % EMBEDDING_DIMS] += 1.0
    norm = np.linalg.norm(vec)
    return (vec / norm if norm else vec).tolist()


class FakeEmbedder:
    """Embedder backed by ``fake_embedding``."""

    def __init__(self, model_name: str = "fake-embedder") -> None:
        self.model_name = model_name

    def embed(self, texts, kind="passage"):
        return np.array([fake_embedding(t) for t in texts], dtype=np.float32)


class FakeLLM:
    """LLM backend scripted by prompt substring.

    Rules are checked in order against the system and user prompts joined; the
    first match answers. An unmatched prompt fails the test, so a new LLM call
    in the pipeline cannot go unnoticed.
    """

    def __init__(self) -> None:
        self.rules: list[tuple[str, object]] = []
        self.calls: list[dict] = []

    def on(self, needle: str, response: object) -> None:
        """Answer prompts containing ``needle``. Newer rules take precedence.

        ``response`` is a string, or a callable taking the prompt text.
        """
        self.rules.insert(0, (needle, response))

    def prompts_containing(self, needle: str) -> list[str]:
        return [c["prompt"] for c in self.calls if needle in c["prompt"]]

    def complete(self, request: LLMRequest) -> LLMResponse:
        prompt = f"{request.system}\n{request.user}"
        self.calls.append({"prompt": prompt, "request": request})
        for needle, response in self.rules:
            if needle in prompt:
                text = response(prompt) if callable(response) else response
                return LLMResponse(text=text)
        raise AssertionError(f"FakeLLM has no rule for prompt:\n{prompt[:400]}")


def _script_default_pipeline(llm: FakeLLM) -> None:
    """Rules covering every call of AdvancedPerspectiveOrchestrator.run()."""
    llm.on("planificador de papers", json.dumps(DEFAULT_OUTLINE))
    llm.on("ESQUEMA A REVISAR", "Sin cambios necesarios")
    llm.on("Escribe UN SOLO PÁRRAFO", f"Párrafo escrito {KNOWN_CITATION}.")
    llm.on(
        "identifica 4 queries",
        json.dumps(
            {
                "support": "emotion robot",
                "counter": "navigation robot",
                "examples": "speech robot",
                "connections": "emotion speech",
            }
        ),
    )
    llm.on("Revisa y mejora la siguiente sección", f"Sección revisada {KNOWN_CITATION}.")
    llm.on("Genera un resumen conciso", "Resumen de la sección.")
    llm.on(
        "revisión final de coherencia",
        f"### Introducción\nIntro final {KNOWN_CITATION}.\n\n"
        f"### Conclusiones\nCierre final {KNOWN_CITATION}.",
    )
    llm.on("revisión crítica exhaustivo", "# Revisión Crítica\n\nTexto de la revisión.")


@pytest.fixture
def fake_llm() -> FakeLLM:
    """A FakeLLM and a FakeEmbedder installed as the shared client and embedder."""
    llm = FakeLLM()
    _script_default_pipeline(llm)
    set_llm_client(LLMClient(llm, max_retries=0))
    set_embedder(FakeEmbedder())
    yield llm
    set_llm_client(None)
    set_embedder(None)


def _write_jsonl(path, rows) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """A data directory under ``tmp_path`` holding a three-paper corpus."""
    data_dir = tmp_path / "data"
    paths = {
        "data_dir": data_dir,
        "references_dir": data_dir / "references",
        "references_pdf_dir": data_dir / "references" / "pdfs",
        "references_markdown_dir": data_dir / "references" / "markdown",
        "output_dir": data_dir / "output",
        "drafts_dir": data_dir / "output" / "drafts",
        "final_dir": data_dir / "output" / "final",
        "processed_dir": data_dir / "processed",
        "embeddings_dir": data_dir / "processed" / "embeddings",
        "indices_dir": data_dir / "processed" / "indices",
    }
    for name, path in paths.items():
        path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(settings.paths, name, path)
    monkeypatch.delenv("THEAIWRITER_BIBLIOTECA", raising=False)

    (paths["references_markdown_dir"] / "ABSTRACT.md").write_text(
        "Abstract de prueba sobre robots sociales.", encoding="utf-8"
    )

    ideas, claims = [], []
    for paper in PAPERS:
        common = {k: paper[k] for k in ("paper_id", "paper_title", "authors", "year")}
        for k in range(IDEAS_PER_PAPER):
            ideas.append(
                {
                    **common,
                    "id": f"{paper['paper_id']}-idea-{k}",
                    "section": "Introduction",
                    "idea": f"robot {paper['word']} idea{k} {paper['word']}{k}",
                    "context": f"context about {paper['word']}",
                    "importance": "high",
                    "keywords": [paper["word"], "robot"],
                }
            )
        for k in range(4):
            claims.append(
                {
                    **common,
                    "id": f"{paper['paper_id']}-claim-{k}",
                    "section": "Results",
                    "claim": f"robot {paper['word']} claim{k}",
                    "evidence": f"evidence about {paper['word']}",
                    "evidence_type": "citation",
                    "cited_references": [],
                    "confidence": "high",
                }
            )

    references = [
        {
            "id": "ref-smith",
            "source_paper_id": "paper-navigation",
            "citation_key": "Smith2020",
            "full_citation": KNOWN_REFERENCE,
            "authors": ["Smith, A.", "Jones, B.", "Lee, C."],
            "title": "Emotion models for social robots",
            "year": 2020,
            "venue": "HRI Journal",
        }
    ]

    _write_jsonl(paths["indices_dir"] / "all_ideas.jsonl", ideas)
    _write_jsonl(paths["indices_dir"] / "all_claims.jsonl", claims)
    _write_jsonl(paths["indices_dir"] / "all_references.jsonl", references)

    return SimpleNamespace(**paths, root=tmp_path)
