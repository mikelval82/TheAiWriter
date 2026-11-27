"""The saved literature review must point to a real, current PDF passage."""

import json
import os

from ai_writer import mcp_server, verificacion
from ai_writer.passages import PassageIndex
from ai_writer.zotero import Zotero
from tests.conftest import FakeEmbedder
from tests.fake_zotero import filler, make_pdf
from tests.test_passages import library  # noqa: F401
from tests.test_verificacion import Judge
from tests.test_zotero_tools import document  # noqa: F401


def test_supported_claim_exposes_a_verified_passage_and_fragment(document):  # noqa: F811
    mcp_server.crear_documento("perspectiva", "T", colecciones=["Empatía"])
    path = document / verificacion.DRAFT
    path.write_text("## Discusión\n\nLos chatbots dependen de sus condiciones [@smith2020empathy].")

    class QuotingJudge(Judge):
        def complete_json(self, system, user):
            answer = super().complete_json(system, user)
            row, = answer["veredictos"]
            snippet = user.split("Pasajes de la obra:\n  [")[1].split("\n")[0].split(") ", 1)[1]
            row["fragmento"] = " ".join(snippet.split()[:8])
            return answer

    data = verificacion.run_judge(document, QuotingJudge())
    passage = data["apoyo"][0]["pasaje"]
    assert passage["archivo"] == "smith.pdf"
    assert passage["fragmento"] in " ".join(passage["texto"].split())
    expected = f"zotero://open-pdf/library/items/PDF00001?page={passage['paginas'].split('-')[0]}"
    assert passage["zotero_url"] == expected
    markdown = (document / verificacion.REPORT).read_text(encoding="utf-8")
    assert "### Pasajes de las citas apoyadas" in markdown and expected in markdown
    assert "Fragmento señalado" in markdown

    found = mcp_server.evidencia_citas(frase="condiciones", seccion="Discusion")
    assert found["total"] == 1 and not found["desactualizado"]
    assert found["resultados"][0]["pasaje"] == passage

    path.write_text(path.read_text().replace("dependen", "son independientes"))
    changed = mcp_server.evidencia_citas(seccion="Discusion")
    assert changed["desactualizado"]
    assert changed["resultados"][0]["veredicto"] == "sin_juzgar"
    assert changed["resultados"][0]["pasaje"] is None


def test_a_positive_verdict_needs_a_passage_from_the_cited_work(document):  # noqa: F811
    mcp_server.crear_documento("perspectiva", "T", colecciones=["Empatía"])
    (document / verificacion.DRAFT).write_text("Los chatbots son útiles [@smith2020empathy].")

    class WrongPassage(Judge):
        def complete_json(self, system, user):
            answer = super().complete_json(system, user)
            answer["veredictos"][0]["pasaje"] = "lee2021robots#1"
            return answer

    data = verificacion.run_judge(document, WrongPassage())
    entry, = data["apoyo"]
    assert entry["veredicto"] == "sin_juzgar" and entry["pasaje"] is None
    assert "pasaje válido" in entry["motivo"]


def test_no_support_keeps_the_passages_consulted(document):  # noqa: F811
    mcp_server.crear_documento("perspectiva", "T", colecciones=["Empatía"])
    (document / verificacion.DRAFT).write_text("Los chatbots son útiles [@smith2020empathy].")

    class NoSupport(Judge):
        def complete_json(self, system, user):
            answer = super().complete_json(system, user)
            answer["veredictos"][0].update(pasaje=None, fragmento=None)
            return answer

    verificacion.run_judge(document, NoSupport("no_apoyada"))
    entry, = mcp_server.evidencia_citas()["resultados"]
    assert entry["veredicto"] == "no_apoyada" and entry["pasaje"] is None
    assert entry["pasajes_consultados"][0]["zotero_url"].startswith(
        "zotero://open-pdf/library/items/PDF00001?page="
    )


def test_a_pdf_change_only_invalidates_verdicts_using_that_pdf(document, library):  # noqa: F811
    mcp_server.crear_documento("perspectiva", "T")
    (document / verificacion.DRAFT).write_text(
        "## Introducción\n\nLos chatbots son útiles [@smith2020empathy].\n\n"
        "Los robots navegan [@lee2021robots]."
    )
    verificacion.run_judge(document, Judge())
    pdf = library.root / "storage/PDF00001/smith.pdf"
    stamp = pdf.stat().st_mtime_ns + 1_000_000
    os.utime(pdf, ns=(stamp, stamp))
    report = mcp_server.evidencia_citas()
    assert report["desactualizado"]
    assert [entry["veredicto"] for entry in report["resultados"]] == ["sin_juzgar", "apoyada"]
    assert report["resultados"][0]["pasaje"] is None
    checked = verificacion.check_document(document)
    assert checked["juez"]["estado"] == "desactualizado"
    judge = Judge()
    final = verificacion.run_judge(document, judge)
    assert len(judge.prompts) == 1 and verificacion.summary(final["apoyo"])["apoyada"] == 2


def test_two_attachments_with_same_name_keep_separate_zotero_links(library, tmp_path):  # noqa: F811
    linked = tmp_path / "otro" / "smith.pdf"
    make_pdf(library.add_pdf("PDF00009", "AAAA1111", linked=linked),
             [("Introduction", filler("linked", 180))])
    index = PassageIndex(Zotero(library.root), tmp_path / "pasajes", FakeEmbedder())
    index.update()
    passages = index.passages_of("smith2020empathy")
    assert {p["archivo"] for p in passages} == {"smith.pdf"}
    assert {p["zotero_url"].split("/")[-1].split("?")[0] for p in passages} == {"PDF00001", "PDF00009"}

    stored = index.root / "obras/AAAA1111.json"
    old = json.loads(stored.read_text())
    for passage in old["pasajes"]:
        passage.pop("adjunto")
    stored.write_text(json.dumps(old))
    assert all("zotero_url" not in p for p in index.passages_of("smith2020empathy"))


def test_sources_to_review_distinguish_literature_from_own_results(document):  # noqa: F811
    mcp_server.crear_documento("resultados", "T")
    (document / verificacion.DRAFT).write_text(
        "# T\n\n## 1. Introducción\n\nLos ensayos en humanos demuestran un efecto de dos años.\n\n"
        "La prevalencia fue del 38%.\n\nEste dato requiere otra fuente [@?].\n\n"
        "```text\nLos ensayos demuestran un 90%.\n```\n\n"
        "## Discusión\n\n### Alcance\n\nLa literatura indica que el efecto persiste.\n\n"
        "Nuestros resultados muestran un 19%.\n\n"
        "El porcentaje del control fue 42%. <!-- hallazgo:1 -->\n\n"
        "## Resultados\n\nLa prevalencia fue 20%.\n",
        encoding="utf-8",
    )
    report = mcp_server.comprobar_documento(juez=False)
    gaps = {row["frase"]: row["motivo"] for row in report["fuentes_por_revisar"]}
    assert gaps == {
        "Este dato requiere otra fuente [@?].": "fuente_pendiente",
        "Los ensayos en humanos demuestran un efecto de dos años.": "afirmacion_empirica",
        "La prevalencia fue del 38%.": "porcentaje",
        "La literatura indica que el efecto persiste.": "afirmacion_empirica",
    }
