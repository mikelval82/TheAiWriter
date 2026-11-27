"""Criteria reviews with checked sources and a fake model."""

import json
from pathlib import Path

import pytest
import yaml

from ai_writer import mcp_server, revisor, verificacion
from ai_writer.convocatoria import JournalFicha, check_journal_ficha
from ai_writer.library import LibraryError
from ai_writer.llm import LLMError, UsageLimitError
from tests.fake_zotero import make_pdf
from tests.test_convocatoria import QUOTE, SOURCE, ficha, save_ficha  # noqa: F401
from tests.test_passages import library  # noqa: F401
from tests.test_verificacion import Judge, draft  # noqa: F401
from tests.test_zotero_tools import document  # noqa: F401


def review_row(name, level="mejorable"):
    return {"nombre": name, "nivel": level, "fortalezas": ["Reconoce sus límites."],
            "carencias": [{"apartado": "Introducción", "problema": "Falta precisar la tesis."}],
            "trabajo": "Explicar la tesis y conseguir el dato pendiente del equipo."}


class Reviewer:
    """Return a scripted review and record every call."""

    def __init__(self, answer=..., error=None):
        self.answer, self.error, self.prompts = answer, error, []

    def complete_json(self, system, user):
        self.prompts.append((system, user))
        if self.error:
            raise self.error("límite o fallo de prueba")
        if self.answer is not ...:
            return self.answer
        criteria = json.loads(user.split("Criterios:\n")[1].split("\n\n")[0])
        return {"criterios": [review_row(c["nombre"]) for c in criteria],
                "prioridades": ["Precisar la tesis.", "Conseguir el dato.", "Revisar estructura."]}


def save_journal(folder, *, confirmed=True, quote=QUOTE):
    data = {"revista": "Revista de prueba", "confirmada": confirmed,
            "criterios": [{"nombre": "Impacto científico", "maximo": 10, "umbral": 5,
                           "descripcion": "Explicar el impacto de la propuesta.",
                           "fuente": {**SOURCE, "cita": quote}}]}
    path = folder / "revista/ficha.yaml"
    make_pdf(path.parent / "instrucciones.pdf", [("Instructions", QUOTE)])
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return data


def prompt_checks(reviewer):
    prompt = reviewer.prompts[0][1]
    return json.loads(prompt.split("Resumen de verificación:\n")[1].split("\n\n")[0])


def test_perspective_uses_generic_criteria_in_one_call(draft):  # noqa: F811
    origin, criteria = revisor.review_criteria(draft)
    assert origin == "genéricos (perspectiva)"
    assert [c["nombre"] for c in criteria] == [
        "Tesis clara y relevante", "Argumento sólido y apoyado en la literatura",
        "Objeciones y límites considerados", "Aportación respecto a lo publicado",
        "Estructura y claridad",
    ]
    reviewer = Reviewer()
    data = revisor.run_review(draft, reviewer)
    assert data["estado"] == "terminado" and data["origen"] == origin
    assert len(reviewer.prompts) == 1
    system, prompt = reviewer.prompts[0]
    assert system == revisor.REVIEW_SYSTEM
    assert origin in prompt
    assert all(c["nombre"] in prompt and c["descripcion"] in prompt for c in criteria)
    assert all(c["maximo"] is c["umbral"] is None for c in criteria)
    assert prompt.endswith((draft / verificacion.DRAFT).read_text(encoding="utf-8"))
    checks = prompt_checks(reviewer)
    assert checks["apoyo"]["juzgadas"] == checks["frases_a_revisar"] == 0
    assert checks["apoyo"]["total"] == checks["apoyo"]["sin_juzgar"] == 5
    assert not (draft / "borrador/referencias.bib").exists()


def test_results_have_their_own_generic_criteria(document):  # noqa: F811
    mcp_server.crear_documento("resultados", "T", colecciones=["Empatía"])
    (document / verificacion.DRAFT).write_text("## Resultados\nLa precisión fue 0,95.")
    origin, criteria = revisor.review_criteria(document)
    assert origin == "genéricos (resultados)"
    assert [c["nombre"] for c in criteria] == [
        "Pregunta y aportación", "Métodos reproducibles",
        "Resultados claros y con origen en los datos",
        "Discusión proporcionada a los datos, con limitaciones", "Relación con la literatura",
    ]
    reviewer = Reviewer()
    revisor.run_review(document, reviewer)
    assert prompt_checks(reviewer)["cifras"]["sin_origen"] == 1


@pytest.mark.parametrize("kind", ["perspectiva", "resultados"])
def test_confirmed_journal_supplies_checked_criteria(document, kind):  # noqa: F811
    mcp_server.crear_documento(kind, "T")
    journal = save_journal(document)
    (document / verificacion.DRAFT).write_text("## Introducción\nUna propuesta.")
    origin, criteria = revisor.review_criteria(document)
    assert origin == "revista: Revista de prueba"
    assert criteria == [{k: v for k, v in journal["criterios"][0].items() if k != "fuente"}]
    reviewer = Reviewer()
    data = revisor.run_review(document, reviewer)
    assert data["origen"] == origin and len(data["criterios"]) == 1
    assert '"maximo": 10.0' in reviewer.prompts[0][1]
    assert '"umbral": 5.0' in reviewer.prompts[0][1]
    assert mcp_server.comprobar_ficha() == {
        "requisitos": 1, "comprobados": 1, "fallidos": [], "avisos": [], "confirmada": True,
    }


@pytest.mark.parametrize("confirmed,quote,message", [
    (True, "An invented criterion absent from the official document", "citas fallidas"),
    (False, QUOTE, "Falta confirmar"),
    (True, "Too few words", "6 palabras"),
])
def test_unchecked_journal_is_rejected_before_spawning(
    draft, monkeypatch, confirmed, quote, message  # noqa: F811
):
    save_journal(draft, confirmed=confirmed, quote=quote)
    monkeypatch.setattr(revisor, "spawn_cli", lambda *args: pytest.fail("No debe lanzarse"))
    for operation in (revisor.review_criteria, revisor.start_review):
        with pytest.raises(LibraryError, match=message):
            operation(draft)
    assert message in mcp_server.revisar_documento()["error"]
    if confirmed:
        assert mcp_server.comprobar_ficha()["fallidos"]
    assert not (draft / revisor.REVIEW).exists()


def test_journal_model_and_checker_report_invalid_fichas(tmp_path):
    assert "falta revista/ficha.yaml" in check_journal_ficha(tmp_path)["error"]
    data = save_journal(tmp_path, confirmed=False)
    assert not JournalFicha.load(tmp_path).confirmada
    path = tmp_path / "revista/ficha.yaml"
    for content in ("[", "revista: Prueba", yaml.safe_dump({**data, "criterios": []})):
        path.write_text(content, encoding="utf-8")
        assert "no es válida" in check_journal_ficha(tmp_path)["error"]


@pytest.mark.parametrize("filename", ["../ajeno.pdf", "ausente.pdf", "instrucciones.txt"])
def test_journal_sources_stay_inside_journal_pdfs(draft, filename):  # noqa: F811
    data = save_journal(draft)
    data["criterios"][0]["fuente"]["fichero"] = filename
    (draft / "revista/ficha.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    assert "dentro de revista/" in check_journal_ficha(draft)["fallidos"][0]["motivo"]
    with pytest.raises(LibraryError, match="citas fallidas"):
        revisor.review_criteria(draft)


def test_call_uses_its_ficha_and_conformity_summary(document, ficha):  # noqa: F811
    mcp_server.crear_documento("convocatoria", "T")
    make_pdf(document / "convocatoria/instrucciones.pdf", [("Instructions", QUOTE)])
    ficha["confirmada"] = True
    save_ficha(document, ficha)
    save_journal(document, confirmed=False, quote="Invented words that are not in the PDF")
    (document / verificacion.DRAFT).write_text("## Motivación\n[PENDIENTE: equipo]")
    origin, criteria = revisor.review_criteria(document)
    assert origin == "convocatoria: Proyectos de prueba"
    assert criteria == [{"nombre": "Calidad", "maximo": 30, "umbral": 20,
                         "descripcion": "Calidad científica"}]
    reviewer = Reviewer()
    data = revisor.run_review(document, reviewer)
    assert data["criterios"][0]["nombre"] == "Calidad"
    call = prompt_checks(reviewer)["convocatoria"]
    assert call["faltan"] == ["Impacto esperado"]
    assert call["pendientes"] == 1 and call["extension"]["maximo"] == 2
    assert mcp_server.comprobar_ficha()["comprobados"] == 8


@pytest.mark.parametrize("state,message", [("absent", "falta"), ("unconfirmed", "Falta confirmar"),
                                          ("empty", "Falta al menos un criterio"),
                                          ("failed", "citas fallidas")])
def test_call_requires_a_confirmed_ficha_with_criteria(
    document, ficha, state, message  # noqa: F811
):
    mcp_server.crear_documento("convocatoria", "T")
    if state != "absent":
        make_pdf(document / "convocatoria/instrucciones.pdf", [("Instructions", QUOTE)])
        ficha["confirmada"] = state != "unconfirmed"
        if state == "empty":
            ficha["criterios"] = []
        if state == "failed":
            ficha["criterios"][0]["fuente"]["cita"] = "An invented criterion outside this PDF"
        save_ficha(document, ficha)
    with pytest.raises(LibraryError, match=message):
        revisor.review_criteria(document)


def test_review_preserves_every_draft_file_and_writes_reports(draft):  # noqa: F811
    (draft / "borrador/referencias.bib").write_bytes(b"bibliografia que debe conservarse\r\n")
    (draft / "borrador/plan.md").write_bytes(b"plan original\r\n")
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
              for p in (draft / "borrador").iterdir()}
    data = revisor.run_review(draft, Reviewer())
    after = {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
             for p in (draft / "borrador").iterdir()}
    assert before == after
    assert json.loads((draft / revisor.REVIEW).read_text(encoding="utf-8")) == data
    assert data["inicio"] and data["fin"] and data["error"] is None
    report = (draft / revisor.REVIEW_REPORT).read_text(encoding="utf-8")
    for text in ("# Revisión del borrador", "genéricos (perspectiva)", "automática y orientativa",
                 "no sustituye a la de la convocatoria o revista", "## Prioridades",
                 "Nivel: mejorable", "Reconoce sus límites", "Introducción: Falta precisar",
                 "### Trabajo", "Conseguir el dato"):
        assert text in report


def test_review_uses_previous_support_and_current_coverage(draft):  # noqa: F811
    verificacion.run_judge(draft, Judge("parcial"))
    reviewer = Reviewer()
    revisor.run_review(draft, reviewer)
    checks = prompt_checks(reviewer)
    assert checks["apoyo"]["parcial"] == 3 and checks["apoyo"]["apoyo"] == 0.0
    assert checks["frases_a_revisar"] == 3
    (draft / verificacion.DRAFT).write_text("## Introducción\nUna tesis sin citas.")
    reviewer = Reviewer()
    revisor.run_review(draft, reviewer)
    checks = prompt_checks(reviewer)
    assert checks["sin_citar"] == ["smith2020empathy"]
    assert checks["citas"]["en_coleccion"] == 1


def test_missing_invalid_and_reordered_criteria_stay_in_original_order(draft):  # noqa: F811
    _, criteria = revisor.review_criteria(draft)
    answer = {"criterios": [review_row(criteria[4]["nombre"], "bien"),
                           review_row(criteria[0]["nombre"], "flojo"),
                           review_row(criteria[2]["nombre"], "excelente"),
                           {"nombre": criteria[3]["nombre"], "nivel": "bien"},
                           review_row("Criterio inventado")],
              "prioridades": ["A", "B", "C", "D"]}
    data = revisor.run_review(draft, Reviewer(answer))
    assert [c["nombre"] for c in data["criterios"]] == [c["nombre"] for c in criteria]
    assert [c["nivel"] for c in data["criterios"]] == [
        "flojo", "sin_evaluar", "sin_evaluar", "sin_evaluar", "bien",
    ]
    assert data["prioridades"] == ["A", "B", "C"]
    assert "sin_evaluar" in (draft / revisor.REVIEW_REPORT).read_text(encoding="utf-8")


def test_usage_limit_is_saved(draft):  # noqa: F811
    data = revisor.run_review(draft, Reviewer(error=UsageLimitError))
    assert data["estado"] == "limite_de_uso" and data["error"] and data["fin"]
    assert revisor.review_status(draft) == data
    assert "limite_de_uso" in (draft / revisor.REVIEW_REPORT).read_text(encoding="utf-8")


@pytest.mark.parametrize("answer", [None, {"criterios": "ilegible"},
                                  {"criterios": [], "prioridades": [123]}])
def test_malformed_response_leaves_an_error_report(draft, answer):  # noqa: F811
    with pytest.raises(LLMError, match="no devolvió"):
        revisor.run_review(draft, Reviewer(answer))
    data = revisor.review_status(draft)
    assert data["estado"] == "error" and data["fin"] and data["error"]


def test_backend_errors_are_saved(draft):  # noqa: F811
    with pytest.raises(LLMError):
        revisor.run_review(draft, Reviewer(error=LLMError))
    assert revisor.review_status(draft)["estado"] == "error"


def test_background_review_tools_and_interrupted_state(draft, monkeypatch):  # noqa: F811
    calls = []

    def spawn(args, log):
        calls.append((args, log))
        return 12345

    monkeypatch.setattr(revisor, "spawn_cli", spawn)
    monkeypatch.setattr(revisor, "process_alive", lambda pid: pid == 12345)
    assert "todavía no se ha revisado" in mcp_server.estado_revision()["error"]
    started = mcp_server.revisar_documento()
    assert started["estado"] == "en_curso" and revisor.review_running(started)
    assert calls == [(["documento", "revisar", str(draft.resolve())], draft / revisor.REVIEW_LOG)]
    assert mcp_server.estado_revision() == started
    assert "ya está en marcha" in mcp_server.revisar_documento()["error"]
    assert len(calls) == 1
    monkeypatch.setattr(revisor, "process_alive", lambda pid: False)
    assert mcp_server.estado_revision()["estado"] == "interrumpido"
    with pytest.raises(LibraryError, match="todavía no se ha revisado"):
        revisor.review_status(draft.parent)


def test_missing_draft_fails_without_model_or_background_process(draft, monkeypatch):  # noqa: F811
    (draft / verificacion.DRAFT).unlink()
    reviewer = Reviewer()
    monkeypatch.setattr(revisor, "spawn_cli", lambda *args: pytest.fail("No debe lanzarse"))
    with pytest.raises(LibraryError, match="no hay borrador"):
        revisor.run_review(draft, reviewer)
    with pytest.raises(LibraryError, match="no hay borrador"):
        revisor.start_review(draft)
    assert not reviewer.prompts


@pytest.mark.parametrize("explicit_folder", [False, True])
def test_cli_dispatches_review(tmp_path, monkeypatch, capsys, explicit_folder):
    from ai_writer.main import main

    calls = []

    def review(folder):
        calls.append(folder)
        return {"estado": "terminado"}

    monkeypatch.setattr(revisor, "run_review", review)
    main(["documento", "revisar"] + ([str(tmp_path)] if explicit_folder else []))
    assert calls == [tmp_path if explicit_folder else Path(".")]
    assert capsys.readouterr().out.strip() == "terminado"


def test_review_is_stale_if_draft_changed_during_generation(draft):  # noqa: F811
    (draft / "materiales/abstract.md").write_text("Mi estudio.")
    path = draft / verificacion.DRAFT
    path.write_text("Versión anterior.")

    class EditingReviewer(Reviewer):
        def complete_json(self, system, user):
            path.write_text("Versión nueva.")
            return super().complete_json(system, user)

    assert revisor.run_review(draft, EditingReviewer())["estado"] == "terminado"
    assert mcp_server.estado_documento()["revision"]["estado"] == "desactualizada"
    verificacion.check_document(draft)
    assert mcp_server.estado_documento()["siguiente"] == "/theaiwriter:revisar"
