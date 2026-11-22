"""Tests for the MCP tools that consult Zotero, called as plain functions."""

import json
from dataclasses import replace

import pytest

from ai_writer import consulta, mcp_server
from ai_writer.embeddings.embedder import set_embedder
from ai_writer.passages import INDEX_ENV
from ai_writer.zotero import ZOTERO_ENV
from tests.conftest import FakeEmbedder
from tests.test_passages import library  # noqa: F401  (fixture)


@pytest.fixture
def document(library, tmp_path, monkeypatch):  # noqa: F811
    folder = tmp_path / "doc"
    folder.mkdir()
    monkeypatch.setenv(ZOTERO_ENV, str(library.root))
    monkeypatch.setenv(INDEX_ENV, str(tmp_path / "indice"))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(folder))
    set_embedder(FakeEmbedder())
    consulta._indexes.clear()
    yield folder
    set_embedder(None)
    consulta._indexes.clear()


def test_collections_and_document_on_zotero(document):
    listed = mcp_server.colecciones_zotero()
    assert listed["obras"] == 3
    assert listed["colecciones"] == [{"ruta": "Empatía", "obras": 1, "con_pdf": 1}]

    assert "No hay ninguna" in mcp_server.crear_documento(
        "perspectiva", "T", colecciones=["Nada"])["error"]
    created = mcp_server.crear_documento("perspectiva", "T", colecciones=["Empatía"])
    assert (created["obras"], created["con_pdf"], created["pendientes"]) == (1, 1, 1)


def test_search_indexes_on_first_use_and_stays_in_the_collections(document):
    mcp_server.crear_documento("perspectiva", "T", colecciones=["Empatía"])
    found = mcp_server.buscar_pasajes("lidar robot outcomes")
    assert found["indexadas_ahora"] == 1
    assert {r["clave"] for r in found["resultados"]} == {"smith2020empathy"}
    assert "indexadas_ahora" not in mcp_server.buscar_pasajes("chatbot")
    assert mcp_server.buscar_pasajes("chatbot", claves=["@lee2021robots"])["resultados"] == []

    status = mcp_server.estado_indice()
    assert (status["indexadas"], status["pendientes"], status["obras_sin_pdf"]) == (1, 0, [])


def test_reading_is_recorded_for_the_judge(document):
    mcp_server.crear_documento("perspectiva", "T")
    first = mcp_server.buscar_pasajes("survey conditions", n=1)["resultados"][0]
    around = mcp_server.leer_pasaje(first["id"])
    assert first["id"] in [p["id"] for p in around["pasajes"]]
    section = mcp_server.leer_pasaje(first["id"], "seccion")["pasajes"]
    assert {p["seccion"] for p in section} == {first["seccion"]}
    pages = mcp_server.leer_paginas("lee2021robots", 3)
    assert [p["seccion"] for p in pages["pasajes"]] == ["Results"]
    assert "error" in mcp_server.leer_pasaje("nadie#3")
    assert "error" in mcp_server.leer_paginas("lee2021robots", 40)

    log = json.loads((document / consulta.CONSULTED).read_text(encoding="utf-8"))
    assert log["consultas"] == [{"consulta": "survey conditions", "pasajes": [first["id"]]}]
    seen = consulta.consulted(document)
    assert set(seen) == {first["clave"], "lee2021robots"}
    assert int(first["id"].split("#")[1]) in seen[first["clave"]]


def test_markup_of_zotero_titles_becomes_latex():
    escape = consulta._escape
    assert escape("Strains of <i>E. coli</i> &amp; more_x") == r"Strains of \textit{E. coli} \& more\_x"
    assert escape("CO<sub>2</sub>") == r"CO\textsubscript{2}"
    assert escape('<span style="font-variant:small-caps;">ResFinder</span> 4') == r"\textsc{ResFinder} 4"
    assert escape("p < 0.05 and x > 1") == "p < 0.05 and x > 1"


def test_live_citations_use_the_keys_zotero_has(document, monkeypatch):
    mcp_server.crear_documento("perspectiva", "T", colecciones=["Empatía"])
    draft = document / consulta.DRAFT
    text = "Una [@smith2020empathy, p. 4; @lee2021robots]. Otra [-@smith2020empathy.] y a@smith2020empathy.org [@?].\n"
    draft.write_text(text, encoding="utf-8")
    index = consulta.open_index()
    work = index.work_of("smith2020empathy")
    item = replace(work, zotero_cite_key="smithEmpathyAgents2020")
    monkeypatch.setitem(index.zotero._works, work.item_key, item)

    answer = mcp_server.preparar_citas_vivas()

    assert answer["cambiadas"] == {"smith2020empathy": "smithEmpathyAgents2020"}
    assert answer["sin_clave_en_zotero"] == ["lee2021robots"]
    assert (document / consulta.LIVE_DRAFT).read_text(encoding="utf-8") == (
        "Una [@smithEmpathyAgents2020, p. 4; @lee2021robots]. Otra [-@smithEmpathyAgents2020.] "
        "y a@smith2020empathy.org [@?].\n"
    )
    assert draft.read_text(encoding="utf-8") == text
    draft.unlink()
    assert "no hay borrador" in mcp_server.preparar_citas_vivas()["error"]


def test_reference_and_bibliography_come_from_zotero(document):
    mcp_server.crear_documento("perspectiva", "T", colecciones=["Empatía"])
    reference = mcp_server.referencia("@smith2020empathy")
    assert reference["titulo"] == "Empathy in chatbots" and reference["en_el_documento"]
    assert reference["bibtex"].startswith("@article{smith2020empathy,")
    assert "author = {Smith, Ana}" in reference["bibtex"]
    assert mcp_server.referencia("lee2021robots")["en_el_documento"] is False
    assert "error" in mcp_server.referencia("nadie2000")

    index = consulta.open_index()
    path = consulta.write_bibliography(document, index, ["lee2021robots", "smith2020empathy", "nadie"])
    assert path.read_text(encoding="utf-8").count("@article{") == 2


def test_hook_blocks_citations_that_are_not_in_the_collections(document):
    import os
    import subprocess
    import sys
    from pathlib import Path

    mcp_server.crear_documento("perspectiva", "T", colecciones=["Empatía"])
    draft = document / "borrador" / "documento.md"

    def run_hook():
        event = json.dumps({"tool_input": {"file_path": str(draft)}})
        hook = Path(__file__).resolve().parent.parent / "hooks" / "validar.py"
        done = subprocess.run([sys.executable, str(hook)], input=event, capture_output=True,
                              text=True, env=os.environ.copy(), check=True)
        return json.loads(done.stdout) if done.stdout.strip() else None

    draft.write_text("Bien citado [@smith2020empathy] y un hueco [@?].", encoding="utf-8")
    assert run_hook() is None
    draft.write_text("Mal [@lee2021robots] y peor [@inventado2020].", encoding="utf-8")
    blocked = run_hook()
    assert blocked["decision"] == "block"
    assert "No existen en Zotero: inventado2020" in blocked["reason"]
    assert "Fuera de las colecciones del documento: lee2021robots" in blocked["reason"]
    assert mcp_server.comprobar_citas("x [@inventado2020]")["correcto"] is False
    assert mcp_server.comprobar_citas("x [@smith2020empathy]")["correcto"] is True
    assert mcp_server.diagnostico()["zotero"]["obras"] == 3


def test_project_round_trip_and_document_folders(document):
    from ai_writer.library import Project

    Project.create(
        document, tipo="perspectiva", titulo="Robots sociales", colecciones=["Empatía"]
    )
    project = Project.load(document)
    assert project.model_dump() == {
        "tipo": "perspectiva", "titulo": "Robots sociales", "idioma": "es",
        "colecciones": ["Empatía"],
    }
    for sub in ("materiales", "borrador", "informes", "exportacion"):
        assert (document / sub).is_dir()


def test_project_refuses_unknown_collections_and_existing_projects(document):
    from ai_writer.library import LibraryError, Project

    with pytest.raises(LibraryError, match="No hay ninguna colección"):
        Project.create(document, tipo="perspectiva", titulo="T", colecciones=["Nada"])
    assert not (document / "proyecto.yaml").exists()

    Project.create(document, tipo="perspectiva", titulo="T")
    with pytest.raises(LibraryError, match="ya tiene"):
        Project.create(document, tipo="perspectiva", titulo="T")


def test_project_load_ignores_legacy_extra_keys(document):
    from ai_writer.library import Project

    (document / "proyecto.yaml").write_text(
        'tipo: perspectiva\ntitulo: T\nfuente: zotero\nbiblioteca: /old/path\n'
        'perfil: antiguo\nmateriales: {abstract: abstract.md}\nplantilla_docx: old.docx\n',
        encoding="utf-8",
    )
    project = Project.load(document)
    assert project.model_dump() == {
        "tipo": "perspectiva", "titulo": "T", "idioma": "es", "colecciones": [],
    }
    project.save(document)
    assert "fuente" not in (document / "proyecto.yaml").read_text(encoding="utf-8")


def test_project_load_requires_a_project_file(document):
    from ai_writer.library import LibraryError, Project

    with pytest.raises(LibraryError, match="falta proyecto.yaml"):
        Project.load(document)


def test_create_results_document_and_its_folders(document):
    from ai_writer.library import Project

    created = mcp_server.crear_documento(
        "resultados", "Resultados propios", colecciones=["Empatía"]
    )
    assert "error" not in created
    assert Project.load(document).tipo == "resultados"
    for sub in ("materiales", "borrador", "informes", "exportacion", "resultados", "analisis"):
        assert (document / sub).is_dir()


@pytest.mark.parametrize("kind", ["desconocido"])
def test_document_tools_reject_unsupported_kinds(document, kind):
    assert "Datos no válidos" in mcp_server.crear_documento(kind, "T")["error"]
    assert not (document / "proyecto.yaml").exists()


def test_tools_work_outside_a_document(document):
    assert mcp_server.diagnostico()["es_un_documento"] is False
    assert "biblioteca" not in mcp_server.diagnostico()
    assert mcp_server.referencia("smith2020empathy")["en_el_documento"] is True
    assert mcp_server.comprobar_citas("x [@smith2020empathy]")["correcto"] is True
    unknown = mcp_server.comprobar_citas("x [@nadie2000]")
    assert unknown["correcto"] is False
    assert unknown["desconocidas"] == ["nadie2000"]


def test_create_call_document_and_team_template(document):
    from ai_writer.library import Project

    created = mcp_server.crear_documento("convocatoria", "Memoria", colecciones=["Empatía"])
    assert "error" not in created
    assert Project.load(document).tipo == "convocatoria"
    assert (document / "convocatoria").is_dir()
    template = (document / "materiales/equipo.md").read_text(encoding="utf-8")
    for label in ("Personas", "Resultados previos", "Recursos", "Presupuesto", "Duración",
                  "Solo se usará lo que esté escrito aquí"):
        assert label in template


def test_create_call_preserves_existing_team_notes(document):
    path = document / "materiales/equipo.md"
    path.parent.mkdir()
    path.write_text("Datos del usuario", encoding="utf-8")
    mcp_server.crear_documento("convocatoria", "Memoria")
    assert path.read_text(encoding="utf-8") == "Datos del usuario"


@pytest.mark.parametrize("kind", ["perspectiva", "resultados", "convocatoria"])
def test_writing_guide_matches_document_kind(document, kind):
    from importlib.resources import files

    mcp_server.crear_documento(kind, "T")
    guide = mcp_server.guia_escritura()
    resource = files("ai_writer").joinpath("guias", f"{kind}.md")
    assert resource.is_file()
    assert guide == {"tipo": kind, "guia": resource.read_text(encoding="utf-8"),
                     "abstract_vacio": True}
    assert guide["guia"].strip() and f"# Guía de escritura: {kind}" in guide["guia"]


def test_guide_and_call_check_require_a_document(document):
    assert "falta proyecto.yaml" in mcp_server.guia_escritura()["error"]
    assert "falta proyecto.yaml" in mcp_server.comprobar_ficha()["error"]
