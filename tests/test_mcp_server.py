"""Tests for the plugin's MCP tools, called as plain functions.

Run from the repository root with ``python -m pytest`` so that ``config`` is importable.
"""

import yaml

from ai_writer import mcp_server
from ai_writer.library import LIBRARY_ENV
from tests.test_citations import library  # noqa: F401  (fixture)


def test_document_tools_follow_the_folder_claude_was_opened_in(library, tmp_path, monkeypatch):  # noqa: F811
    folder = tmp_path / "doc"
    folder.mkdir()
    monkeypatch.setenv(LIBRARY_ENV, str(library.root))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(folder))

    library.save_collection("Robots", library.find_papers(["paper-emotion", "crowded"]))
    assert "error" in mcp_server.crear_documento(
        "perspectiva", "T", colecciones=["Voz"], fuente="biblioteca"
    )

    created = mcp_server.crear_documento(
        "perspectiva", "T", colecciones=["Robots"], fuente="biblioteca"
    )

    assert created["papers_disponibles"] == 2
    assert yaml.safe_load((folder / "proyecto.yaml").read_text(encoding="utf-8"))["colecciones"] == [
        "Robots"
    ]
    reference = mcp_server.referencia("@smith2020emotion")
    assert reference["titulo"] == "Emotion Models for Social Robots"
    assert reference["en_colecciones_del_documento"] is True
    assert reference["bibtex"].startswith("@article{smith2020emotion,")
    assert mcp_server.referencia("green2022speech")["en_colecciones_del_documento"] is False
    assert mcp_server.validar_citas("Robots [@smith2020emotion].")["correcto"] is True
    outside = mcp_server.validar_citas("Voz [@green2022speech].")
    assert outside["correcto"] is False
    assert outside["outside"] == ["green2022speech"]


def test_tools_report_errors_instead_of_raising(library, monkeypatch):  # noqa: F811
    monkeypatch.setenv(LIBRARY_ENV, str(library.root))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(library.root))

    assert "no existe" in mcp_server.referencia("nadie2020")["error"]
    unknown = mcp_server.validar_citas("Texto [@nadie2020].")
    assert unknown["correcto"] is False
    assert unknown["unknown"] == ["nadie2020"]
    assert mcp_server.referencia("smith2020emotion")["en_colecciones_del_documento"] is True
    assert mcp_server.validar_citas("Robots [@smith2020emotion].")["correcto"] is True
    assert "Datos no válidos" in mcp_server.crear_documento(
        "desconocido", "T", fuente="biblioteca"
    )["error"]
