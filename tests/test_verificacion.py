"""Tests for the checks of a draft written from Zotero."""

import json

import pytest

from ai_writer import mcp_server, verificacion
from ai_writer.consulta import open_index
from ai_writer.library import LibraryError
from ai_writer.llm import LLMError, UsageLimitError
from ai_writer.sentences import cited_paragraphs, split_sentences
from ai_writer.verificacion import DRAFT
from tests.test_passages import library  # noqa: F401  (fixture)
from tests.test_zotero_tools import document  # noqa: F401  (fixture)

QUOTE = "The chatbot study reports that chatbot outcomes depend on chatbot conditions"
DRAFT_TEXT = f"""# T

## Introducción

Los resultados dependen de las condiciones [@smith2020empathy]. Como dice el artículo, \
«{QUOTE}» [@smith2020empathy]. Una frase sin cita.

Otra obra dice que «The chatbot study reports that chatbot outcomes ignore chatbot conditions» \
[@smith2020empathy; @nadie2000]. Los robots navegan [@lee2021robots] y falta una [@?].
"""


class Judge:
    """Answers every pair with the scripted verdict; records the prompts."""

    def __init__(self, verdict="apoyada", fail_after=None, error=UsageLimitError):
        self.verdict, self.fail_after, self.error, self.prompts = verdict, fail_after, error, []

    def complete_json(self, system, user):
        if self.fail_after is not None and len(self.prompts) >= self.fail_after:
            raise self.error("límite")
        self.prompts.append(user)
        numbers = [int(line[1:line.index("]")]) for line in user.splitlines()
                   if line.startswith("[") and "] Frase:" in line]
        first_id = user.split("Pasajes de la obra:\n  [")[1].split("]")[0]
        return {"veredictos": [{"n": n, "veredicto": self.verdict, "motivo": "porque sí",
                                "pasaje": first_id} for n in numbers]}


@pytest.fixture
def draft(document):  # noqa: F811
    mcp_server.crear_documento("perspectiva", "T", colecciones=["Empatía"])
    (document / DRAFT).write_text(DRAFT_TEXT, encoding="utf-8")
    return document


def test_citations_quotes_and_bibliography_without_llm(draft):
    data = verificacion.check_document(draft)
    assert data["citas"] == {
        "validas": ["smith2020empathy"], "desconocidas": ["nadie2000"],
        "fuera_de_las_colecciones": ["lee2021robots"], "sin_pdf": [], "mal_formadas": [], "pendientes": 1,
    }
    found, altered = data["citas_literales"]
    assert found["encontrada_en"] == "smith2020empathy"
    assert altered["encontrada_en"] is None
    assert altered["mas_parecido"]["clave"] == "smith2020empathy"
    assert altered["mas_parecido"]["diferencias"] == [{"cita": "ignore", "texto": "depend on"}]
    assert (draft / "borrador/referencias.bib").read_text(encoding="utf-8").startswith("@article{smith2020empathy,")
    report = (draft / verificacion.REPORT).read_text(encoding="utf-8")
    assert "No existen en Zotero:** nadie2000" in report
    assert "El borrador dice «ignore» y el PDF dice «depend on»" in report
    assert "El juez de apoyo no se ha lanzado" in report


def test_perspective_has_no_figure_check(draft, monkeypatch):
    def unexpected(*args):
        pytest.fail("Las perspectivas no comprueban cifras propias")

    monkeypatch.setattr(verificacion, "check_figures", unexpected)
    data = verificacion.check_document(draft)
    saved = json.loads((draft / verificacion.RESULT).read_text(encoding="utf-8"))
    assert "cifras" not in data and "cifras" not in saved
    assert "cifras" not in verificacion.overview(data)
    assert "## Cifras propias" not in verificacion.markdown(data)


@pytest.mark.parametrize("figure", ["0,943", "0,953"])
def test_results_document_checks_and_reports_own_figures(document, figure):  # noqa: F811
    mcp_server.crear_documento("resultados", "T", colecciones=["Empatía"])
    (document / DRAFT).write_text(f"## Resultados\nLa precisión fue {figure}.", encoding="utf-8")
    (document / "resultados/metricas.csv").write_text("modelo,valor\nA,0.943\n", encoding="utf-8")
    data = verificacion.check_document(document)
    figures = data["cifras"]
    assert figures["comprobadas"] == 1
    assert figures["con_origen"] == (figure == "0,943")
    saved = json.loads((document / verificacion.RESULT).read_text(encoding="utf-8"))
    assert saved["cifras"] == verificacion.overview(data)["cifras"] == figures
    report = (document / verificacion.REPORT).read_text(encoding="utf-8")
    assert "## Cifras propias" in report and "1 cifras comprobadas" in report
    assert "no que la frase la describa bien" in report
    if figure == "0,953":
        assert "Sin origen: 0,953" in report
        assert "(Resultados): «La precisión fue 0,953.»" in report
    else:
        assert "Todas las cifras comprobadas tienen origen" in report


def test_a_single_changed_word_is_not_verbatim():
    text = ("But empathy is a broad concept that refers to the cognitive and emotional reactions of an "
            "individual to the observed experiences of another [3]. It involves co-\nregulation too.")
    assert verificacion._verbatim("empathy is a broad concept that refers to the cognitive", text) == (True, None)
    assert verificacion._verbatim("experiences of another. It involves co-regulation too", text)[0]  # footnote, hyphen
    assert verificacion._verbatim("empathy is a broad concept … reactions of an individual", text)[0]
    verbatim, closest = verificacion._verbatim(
        "empathy is a narrow concept that refers to the cognitive and emotional reactions of an individual", text)
    assert not verbatim and closest["diferencias"] == [{"cita": "narrow", "texto": "broad"}]
    assert verificacion._verbatim("nothing here resembles the paper in any way at all", text) == (False, None)


def test_judge_sees_passages_of_the_cited_work(draft):
    mcp_server.buscar_pasajes("survey conditions", claves=["smith2020empathy"], n=1)
    judge = Judge("tergiversada")
    data = verificacion.run_judge(draft, judge)
    assert data["juez"]["estado"] == "terminado"
    assert len(judge.prompts) == 2  # one call per paragraph with cited sentences
    assert "smith2020empathy#" in judge.prompts[0] and "lee2021robots#" not in judge.prompts[1]
    consulted = json.loads((draft / "revision/consultas.json").read_text(encoding="utf-8"))["pasajes"][0]
    assert f"[{consulted}]" in judge.prompts[0]  # what the writer read is before the judge too

    stats = verificacion.summary(data["apoyo"])
    assert (stats["tergiversada"], stats["sin_juzgar"], stats["apoyo"]) == (3, 2, 0.0)
    outside = next(e for e in data["apoyo"] if e["clave"] == "lee2021robots")
    assert "no se puede comprobar" in outside["motivo"]  # not in the document's collections
    unknown = next(e for e in data["apoyo"] if e["clave"] == "nadie2000")
    assert unknown["veredicto"] == "sin_juzgar" and "no existe" in unknown["motivo"]
    judged = data["apoyo"][0]
    assert judged["pasaje"]["id"].startswith("smith2020empathy#") and judged["motivo"] == "porque sí"
    assert "**Tergiversada** [@smith2020empathy]" in (draft / verificacion.REPORT).read_text(encoding="utf-8")


def test_judge_resumes_after_the_usage_limit(draft):
    data = verificacion.run_judge(draft, Judge(fail_after=1))
    assert data["juez"]["estado"] == "limite_de_uso" and data["juez"]["hechos"] == 1
    assert verificacion.summary(data["apoyo"])["apoyada"] == 2

    second = Judge()
    data = verificacion.run_judge(draft, second)
    assert data["juez"]["estado"] == "terminado" and len(second.prompts) == 1
    assert verificacion.summary(data["apoyo"])["apoyada"] == 3


def test_unreadable_judge_answers_are_not_support(draft):
    data = verificacion.run_judge(draft, Judge(fail_after=0, error=LLMError))
    stats = verificacion.summary(data["apoyo"])
    assert stats["sin_juzgar"] == 5 and stats["apoyo"] is None


def test_tools_report_and_refuse_other_documents(draft, monkeypatch):
    monkeypatch.setattr(verificacion, "spawn_cli", lambda args, log: 0)
    answer = mcp_server.verificar_documento()
    assert answer["citas"]["validas"] == 1 and answer["claves_con_problemas"]["desconocidas"] == ["nadie2000"]
    assert len(answer["citas_literales"]["no_encontradas"]) == 1
    assert answer["juez"]["estado"] == "en_curso"
    assert mcp_server.estado_verificacion()["juez"]["estado"] == "interrumpido"  # pid 0 is not alive

    (draft / DRAFT).unlink()
    assert "no hay borrador" in mcp_server.verificar_documento(juez=False)["error"]
    with pytest.raises(LibraryError):
        verificacion.status(draft.parent)


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


def test_background_judge_keeps_the_cli_invocation(draft, monkeypatch):
    calls = []

    def spawn(args, log):
        calls.append((args, log))
        return 12345

    monkeypatch.setattr(verificacion, "spawn_cli", spawn)
    verificacion.start_judge(draft)
    assert calls == [
        (["documento", "verificar", str(draft.resolve())], draft / verificacion.LOG)
    ]


def test_cli_dispatches_document_verification(tmp_path, monkeypatch, capsys):
    from ai_writer.main import main

    calls = []

    def judge(folder):
        calls.append(folder)
        return {"apoyo": []}

    monkeypatch.setattr(verificacion, "run_judge", judge)
    main(["documento", "verificar", str(tmp_path)])
    assert calls == [tmp_path]
    assert "'apoyo': None" in capsys.readouterr().out
