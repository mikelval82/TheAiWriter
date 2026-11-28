"""Guided materials, report migration and deterministic document progress."""

import json
import os

import pytest

from ai_writer import mcp_server, revisor, verificacion
from ai_writer.avisos import NOTICES, pop_notices
from ai_writer.library import Project, is_template, migrate_reports
from tests.test_passages import library  # noqa: F401
from tests.test_zotero_tools import document  # noqa: F401


def test_load_migrates_old_reports_and_notifies_once(tmp_path):
    Project(tipo="perspectiva", titulo="Antiguo").save(tmp_path)
    old = tmp_path / "revision"
    old.mkdir()
    for name in ("verificacion.json", "verificacion.md", "verificacion.log",
                 "revision.json", "revision.md", "revision.log", "consultas.json"):
        (old / name).write_text(name, encoding="utf-8")
    Project.load(tmp_path)
    assert not old.exists()
    for name in ("comprobacion.json", "comprobacion.md", "comprobacion.log",
                 "revision.json", "revision.md", "revision.log", "consultas.json"):
        expected = name.replace("comprobacion", "verificacion")
        assert (tmp_path / "informes" / name).read_text() == expected
    Project.load(tmp_path)
    assert pop_notices(tmp_path) == [
        "La carpeta revision/ se ha renombrado a informes/ y verificacion.md a comprobacion.md."
    ]
    assert not migrate_reports(tmp_path)
    assert pop_notices(tmp_path) == []


def test_migration_does_not_merge_existing_folders(tmp_path):
    for name in ("revision", "informes"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "consultas.json").write_text(name)
    assert not migrate_reports(tmp_path)
    for name in ("revision", "informes"):
        assert (tmp_path / name / "consultas.json").read_text() == name
    assert not (tmp_path / NOTICES).exists()


@pytest.mark.parametrize("content,empty", [
    (None, True), ("", True), (" \n\t", True),
    ("# Título\n\n<!-- Pregunta\nmultilínea -->\n## Apartado\n", True),
    ("Título\n======\n\nApartado\n--------\n<!-- Pregunta -->", True),
    ("# Título\n<!-- pregunta -->\nMi respuesta.", False),
    ("<!-- pregunta -->\n0", False), ("#\nRespuesta", False),
])
def test_template_detection(tmp_path, content, empty):
    path = tmp_path / "material.md"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    assert is_template(path) is empty


@pytest.mark.parametrize("kind,question", [
    ("perspectiva", "¿Qué quieres defender (tu tesis, en una frase)?"),
    ("resultados", "¿Cuál es el resultado principal?"),
    ("convocatoria", "¿Cuál es la hipótesis?"),
])
def test_guided_materials_are_empty_until_answered(document, kind, question):  # noqa: F811
    Project.create(document, tipo=kind, titulo="T")
    abstract = document / "materiales/abstract.md"
    assert f"<!-- {question} -->" in abstract.read_text(encoding="utf-8")
    assert is_template(abstract)
    assert mcp_server.guia_escritura()["abstract_vacio"]
    status = mcp_server.estado_documento()
    assert status["tipo"] == kind
    assert status["titulo"] == "T"
    assert status["motivo_siguiente"]
    assert status["alternativas"][0]["accion"] == "/theaiwriter:ayuda materiales"
    assert status["materiales"]["materiales/abstract.md"] == "plantilla"
    assert status["siguiente"] == "Completar materiales/abstract.md"
    if kind == "convocatoria":
        assert is_template(document / "materiales/equipo.md")
        assert status["materiales"] == {"materiales/abstract.md": "plantilla",
                                       "materiales/equipo.md": "plantilla",
                                       "convocatoria/*.pdf": "falta"}
    if kind == "resultados":
        assert status["materiales"]["salidas del análisis"] == "falta"
    with abstract.open("a", encoding="utf-8") as stream:
        stream.write("Mi idea y objetivo.\n")
    assert not is_template(abstract)
    assert not mcp_server.guia_escritura()["abstract_vacio"]


def test_create_preserves_existing_abstract(document):  # noqa: F811
    path = document / "materiales/abstract.md"
    path.parent.mkdir()
    path.write_text("Mi idea", encoding="utf-8")
    Project.create(document, tipo="perspectiva", titulo="T")
    assert path.read_text() == "Mi idea"


@pytest.mark.parametrize("kind,extra", [
    ("resultados", "resultados/tablas/datos.CSV"),
    ("convocatoria", "convocatoria/oficiales/bases.PDF"),
])
def test_extra_materials_in_subfolders(document, kind, extra):  # noqa: F811
    Project.create(document, tipo=kind, titulo="T")
    (document / "materiales/abstract.md").write_text("Idea.")
    if kind == "convocatoria":
        assert mcp_server.estado_documento()["siguiente"] == "Completar materiales/equipo.md"
        (document / "materiales/equipo.md").write_text("Equipo conocido.")
    status = mcp_server.estado_documento()
    key = "salidas del análisis" if kind == "resultados" else "convocatoria/*.pdf"
    assert status["siguiente"] == f"Completar {key}"
    path = document / extra
    path.parent.mkdir()
    path.write_text("material")
    next_command = "hallazgos" if kind == "resultados" else "escribir"
    assert mcp_server.estado_documento()["siguiente"] == f"/theaiwriter:{next_command}"


def write_reports(
    folder, *, judge="terminado", verdict=None, figures=None, missing=None, review=False
):
    checks = {"juez": {"estado": judge}, "apoyo": []}
    if verdict:
        checks["apoyo"] = [{"veredicto": verdict}]
    if figures:
        checks["cifras"] = {"sin_origen": figures}
    if missing:
        checks["convocatoria"] = {"faltan": missing}
    (folder / verificacion.RESULT).write_text(json.dumps(checks))
    if review:
        (folder / revisor.REVIEW).write_text(json.dumps({"estado": "terminado", "criterios": []}))


@pytest.fixture
def ready(document):  # noqa: F811
    Project.create(document, tipo="perspectiva", titulo="T")
    (document / "materiales/abstract.md").write_text("Una idea.")
    return document


def test_next_step_without_draft_or_check_and_word_count(ready):
    assert mcp_server.estado_documento()["siguiente"] == "/theaiwriter:escribir"
    draft = ready / verificacion.DRAFT
    draft.write_text("  \n")
    assert mcp_server.estado_documento()["siguiente"] == "/theaiwriter:escribir"
    draft.write_text("# T\nUna idea.")
    status = mcp_server.estado_documento()
    assert status["palabras"] == 4
    assert status["comprobacion"] == {"estado": "sin hacer"}
    assert status["revision"] == {"estado": "sin hacer"}
    assert status["siguiente"] == "/theaiwriter:comprobar"


@pytest.mark.parametrize("verdict,figures,missing,review,expected", [
    ("apoyada", None, None, False, "/theaiwriter:revisar"),
    ("tergiversada", None, None, True, "/theaiwriter:corregir"),
    ("no_apoyada", None, None, False, "/theaiwriter:corregir"),
    (None, ["0,95"], None, True, "/theaiwriter:corregir"),
    (None, None, ["Impacto"], False, "/theaiwriter:corregir"),
    ("parcial", None, None, False, "/theaiwriter:corregir"),
    ("apoyada", None, None, True, "/theaiwriter:exportar"),
])
def test_next_step_follows_report_priority(ready, verdict, figures, missing, review, expected):
    (ready / verificacion.DRAFT).write_text("Borrador con texto.")
    write_reports(ready, verdict=verdict, figures=figures, missing=missing, review=review)
    status = mcp_server.estado_documento()
    assert status["siguiente"] == expected
    assert status["comprobacion"]["estado"] == "terminado"
    assert status["comprobacion"]["recuento"][verdict or "sin_juzgar"] == bool(verdict)
    result = ready / verificacion.RESULT
    stamp = result.stat().st_mtime_ns
    os.utime(ready / verificacion.DRAFT, ns=(stamp + 1_000_000, stamp + 1_000_000))
    assert mcp_server.estado_documento()["comprobacion"]["estado"] == "desactualizada"
    assert mcp_server.estado_documento()["siguiente"] == "/theaiwriter:comprobar"
    (ready / "materiales/abstract.md").unlink()
    assert mcp_server.estado_documento()["materiales"]["materiales/abstract.md"] == "falta"
    assert mcp_server.estado_documento()["siguiente"] == "Completar materiales/abstract.md"


def test_status_reports_running_and_interrupted_jobs(ready, monkeypatch):
    (ready / verificacion.DRAFT).write_text("Texto.")
    write_reports(ready, judge="en_curso")
    (ready / revisor.REVIEW).write_text('{"estado": "en_curso"}')
    monkeypatch.setattr(verificacion, "process_alive", lambda pid: True)
    monkeypatch.setattr(revisor, "process_alive", lambda pid: True)
    status = mcp_server.estado_documento()
    assert status["comprobacion"]["estado"] == "juez en curso"
    assert status["revision"]["estado"] == "en_curso"
    assert status["siguiente"] == "/theaiwriter:estado"
    monkeypatch.setattr(verificacion, "process_alive", lambda pid: False)
    monkeypatch.setattr(revisor, "process_alive", lambda pid: False)
    status = mcp_server.estado_documento()
    assert status["comprobacion"]["estado"] == status["revision"]["estado"] == "interrumpido"


def test_status_needs_a_document(document):  # noqa: F811
    assert "falta proyecto.yaml" in mcp_server.estado_documento()["error"]


def test_deterministic_check_has_new_names_and_finished_status(ready):
    (ready / verificacion.DRAFT).write_text("# T\nUna propuesta sin citas.")
    report = mcp_server.comprobar_documento(juez=False)
    assert report["informe"] == "informes/comprobacion.md"
    assert (ready / verificacion.REPORT).read_text().startswith("# Comprobación del borrador\n")
    status = mcp_server.estado_documento()
    assert status["comprobacion"]["estado"] == "terminado"
    assert status["comprobacion"]["juez"]["estado"] == "sin_lanzar"
    assert status["comprobacion"]["recuento"]["apoyada"] == 0
    assert status["siguiente"] == "/theaiwriter:revisar"


@pytest.mark.parametrize("state", ["error", "limite_de_uso", "interrumpido"])
def test_failed_reviews_offer_a_retry(ready, state):
    (ready / verificacion.DRAFT).write_text("Borrador con texto.")
    write_reports(ready, review=True)
    (ready / revisor.REVIEW).write_text(json.dumps({"estado": state}))
    status = mcp_server.estado_documento()
    assert status["revision"]["estado"] == state
    assert status["siguiente"] == "/theaiwriter:revisar"
    assert status["motivo_siguiente"]
    assert status["alternativas"][0]["accion"] == "Leer borrador/documento.md"


def test_citations_without_judgment_offer_next_steps(ready):
    (ready / verificacion.DRAFT).write_text(
        "El efecto depende de la condición [@smith2020empathy]."
    )
    report = mcp_server.comprobar_documento(juez=False)
    status = mcp_server.estado_documento()
    assert status["comprobacion"]["estado"] == "parcial"
    assert status["comprobacion"]["recuento"] == report["apoyo"]
    assert report["apoyo"]["total"] == report["apoyo"]["sin_juzgar"] == 1
    assert report["apoyo"]["juzgadas"] == 0
    assert status["siguiente"] == "/theaiwriter:comprobar"
    assert any(a["accion"] == "/theaiwriter:revisar" for a in status["alternativas"])


@pytest.mark.parametrize("pending", ["El alcance es [PENDIENTE: muestra].", "Falta una obra [@?]."])
def test_pending_items_offer_correction_before_export(ready, pending):
    (ready / verificacion.DRAFT).write_text(pending)
    mcp_server.comprobar_documento(juez=False)
    (ready / revisor.REVIEW).write_text('{"estado": "terminado"}')
    status = mcp_server.estado_documento()
    assert status["siguiente"] == "/theaiwriter:corregir"


def test_review_priorities_offer_correction_with_export_as_an_alternative(ready):
    (ready / verificacion.DRAFT).write_text("Borrador con texto.")
    write_reports(ready, review=True)
    (ready / revisor.REVIEW).write_text(
        '{"estado": "terminado", "prioridades": ["Aclarar las limitaciones."]}'
    )
    status = mcp_server.estado_documento()
    assert status["siguiente"] == "/theaiwriter:corregir la revisión"
    assert any(a["accion"] == "/theaiwriter:exportar" for a in status["alternativas"])


def test_export_next_step_after_review_and_after_a_draft_change(ready):
    draft = ready / verificacion.DRAFT
    draft.write_text("Borrador listo.")
    write_reports(ready, review=True)
    output = ready / "exportacion/documento.docx"
    assert mcp_server.estado_documento()["siguiente"] == "/theaiwriter:exportar"

    output.write_bytes(b"Copia de Word")
    status = mcp_server.estado_documento()
    assert status["exportacion"] == {"estado": "terminada", "documento": "exportacion/documento.docx"}
    assert status["siguiente"] == "Abrir exportacion/documento.docx"

    stamp = output.stat().st_mtime_ns
    os.utime(draft, ns=(stamp + 1_000_000, stamp + 1_000_000))
    write_reports(ready, review=True)
    fixed_stamp = stamp + 2_000_000
    for report in (verificacion.RESULT, revisor.REVIEW):
        os.utime(ready / report, ns=(fixed_stamp, fixed_stamp))
    status = mcp_server.estado_documento()
    assert status["exportacion"]["estado"] == "desactualizada"
    assert status["siguiente"] == "/theaiwriter:exportar reemplazar"
