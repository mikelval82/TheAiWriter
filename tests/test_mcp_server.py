"""Tests for the plugin's MCP tools, called as plain functions.

Run from the repository root with ``python -m pytest`` so that ``config`` is importable.
"""

import yaml

from ai_writer import mcp_server
from ai_writer.library import LIBRARY_ENV
from tests.test_library import library, processed  # noqa: F401  (fixtures)


def test_document_tools_follow_the_folder_claude_was_opened_in(library, tmp_path, monkeypatch):  # noqa: F811
    folder = tmp_path / "doc"
    folder.mkdir()
    monkeypatch.setenv(LIBRARY_ENV, str(library.root))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(folder))

    assert mcp_server.guardar_coleccion("Robots", ["emotion", "crowded"])["papers"] == [
        "Emotion Models for Social Robots",
        "Navigation in Crowded Spaces",
    ]
    assert "error" in mcp_server.crear_documento("perspectiva", "T", colecciones=["Voz"])

    created = mcp_server.crear_documento("perspectiva", "T", colecciones=["Robots"])

    assert created["papers_disponibles"] == 2
    assert yaml.safe_load((folder / "proyecto.yaml").read_text(encoding="utf-8"))["colecciones"] == [
        "Robots"
    ]
    status = mcp_server.estado_biblioteca()
    assert status["papers"] == 3
    assert status["documento"]["papers_disponibles"] == 2
    assert [p["id"] for p in mcp_server.listar_papers("Robots")["papers"]] == [
        "paper-emotion",
        "paper-navigation",
    ]


def test_tools_report_errors_instead_of_raising(library, monkeypatch):  # noqa: F811
    monkeypatch.setenv(LIBRARY_ENV, str(library.root))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(library.root))

    assert "No existe" in mcp_server.borrar_coleccion("Voz")["error"]
    assert "No hay PDFs" in mcp_server.procesar_pdfs()["error"]
