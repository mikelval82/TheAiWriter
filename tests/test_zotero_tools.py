"""Tests for the MCP tools that consult Zotero, called as plain functions."""

import json

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
        "perspectiva", "T", colecciones=["Nada"], fuente="zotero")["error"]
    created = mcp_server.crear_documento("perspectiva", "T", colecciones=["Empatía"], fuente="zotero")
    assert (created["obras"], created["con_pdf"], created["pendientes"]) == (1, 1, 1)


def test_search_indexes_on_first_use_and_stays_in_the_collections(document):
    mcp_server.crear_documento("perspectiva", "T", colecciones=["Empatía"], fuente="zotero")
    found = mcp_server.buscar_pasajes("lidar robot outcomes")
    assert found["indexadas_ahora"] == 1
    assert {r["clave"] for r in found["resultados"]} == {"smith2020empathy"}
    assert "indexadas_ahora" not in mcp_server.buscar_pasajes("chatbot")
    assert mcp_server.buscar_pasajes("chatbot", claves=["@lee2021robots"])["resultados"] == []

    status = mcp_server.estado_indice()
    assert (status["indexadas"], status["pendientes"], status["obras_sin_pdf"]) == (1, 0, [])


def test_reading_is_recorded_for_the_judge(document):
    mcp_server.crear_documento("perspectiva", "T", fuente="zotero")
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


def test_reference_and_bibliography_come_from_zotero(document):
    mcp_server.crear_documento("perspectiva", "T", colecciones=["Empatía"], fuente="zotero")
    reference = mcp_server.referencia("@smith2020empathy")
    assert reference["titulo"] == "Empathy in chatbots" and reference["en_el_documento"]
    assert reference["bibtex"].startswith("@article{smith2020empathy,")
    assert "author = {Smith, Ana}" in reference["bibtex"]
    assert mcp_server.referencia("lee2021robots")["en_el_documento"] is False
    assert "error" in mcp_server.referencia("nadie2000")

    index = consulta.open_index()
    path = consulta.write_bibliography(document, index, ["lee2021robots", "smith2020empathy", "nadie"])
    assert path.read_text(encoding="utf-8").count("@article{") == 2
