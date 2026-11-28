"""Exercise DOCX export, including Pandoc itself when the executable is available."""

import base64
from pathlib import Path
from subprocess import CompletedProcess
from zipfile import ZipFile

import pytest

from ai_writer import exportacion, mcp_server
from ai_writer.consulta import BIBLIOGRAPHY, DRAFT
from ai_writer.library import Project


@pytest.fixture
def folder(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    Project(tipo="resultados", titulo="T").save(tmp_path)
    (tmp_path / "borrador").mkdir()
    (tmp_path / DRAFT).write_text("## Resultados\n\nSe registraron 42 casos. <!-- hallazgo:1 -->\n")
    return tmp_path


def mock_converter(monkeypatch, *, stderr="", failure=0, during=None):
    calls = []

    def run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        if "--bibliography" in arguments:
            bib = Path(arguments[arguments.index("--bibliography") + 1])
            assert bib.read_text(encoding="utf-8") == "@article{a, title={Un estudio}}\n"
        output = Path(arguments[arguments.index("--output") + 1])
        if not failure:
            with ZipFile(output, "w") as archive:
                archive.writestr("[Content_Types].xml", "<Types/>")
                archive.writestr("word/document.xml", "<document>Texto nuevo</document>")
        if during:
            during()
        return CompletedProcess(arguments, failure, stdout="", stderr=stderr)

    monkeypatch.setattr(exportacion, "pandoc_executable", lambda: "pandoc")
    monkeypatch.setattr(exportacion.subprocess, "run", run)
    return calls


def test_export_provides_figure_paths_bibliography_and_style(folder, monkeypatch):
    draft = folder / DRAFT
    original = draft.read_text(encoding="utf-8") + "\nUn estudio anterior [@a].\n"
    draft.write_text(original, encoding="utf-8")
    bibliography = folder / BIBLIOGRAPHY
    bibliography.write_text("@article{a, title={Un estudio}}\n", encoding="utf-8")
    style, template = folder / "revista con espacios.csl", folder / "plantilla.docx"
    style.write_text("csl")
    template.write_text("docx")
    calls = mock_converter(monkeypatch, stderr="[WARNING] Comprueba la figura")
    result = mcp_server.exportar_documento(estilo_csl=style.name, plantilla_docx=template.name)
    assert result == {"documento": "exportacion/documento.docx", "avisos": "[WARNING] Comprueba la figura"}
    (arguments, supplied), = calls
    assert supplied["cwd"] == folder
    assert supplied["input"] == original
    assert "--strip-comments" in arguments and "--citeproc" in arguments
    assert "--resource-path=" + exportacion.os.pathsep.join(("borrador", ".", "resultados")) in arguments
    assert arguments[arguments.index("--csl") + 1] == str(style)
    assert arguments[arguments.index("--reference-doc") + 1] == str(template)
    assert draft.read_text(encoding="utf-8") == original
    assert exportacion.export_status(folder, draft)["estado"] == "terminada"


def test_export_requires_pandoc_and_bibliography_when_citing(folder, monkeypatch):
    monkeypatch.setattr(exportacion, "pandoc_executable", lambda: None)
    assert "pandoc.org/installing.html" in mcp_server.exportar_documento()["error"]
    (folder / DRAFT).write_text("Cita de un trabajo previo [@a].")
    calls = mock_converter(monkeypatch)
    error = mcp_server.exportar_documento()["error"]
    assert "/theaiwriter:comprobar sin juez" in error
    assert not calls and not (folder / exportacion.WORD_DOCUMENT).exists()


def test_existing_docx_survives_a_failed_or_outdated_export(folder, monkeypatch):
    output = folder / exportacion.WORD_DOCUMENT
    output.parent.mkdir()
    output.write_bytes(b"Word anterior")
    failing = mock_converter(monkeypatch, failure=1, stderr="plantilla no válida")
    assert "reemplazar" in mcp_server.exportar_documento()["error"]
    assert not failing
    assert "plantilla no válida" in mcp_server.exportar_documento(reemplazar=True)["error"]
    assert output.read_bytes() == b"Word anterior"

    draft = folder / DRAFT
    mock_converter(monkeypatch, during=lambda: draft.write_text("Borrador cambiado."))
    assert "cambiaron durante" in mcp_server.exportar_documento(reemplazar=True)["error"]
    assert output.read_bytes() == b"Word anterior"

    mock_converter(monkeypatch)
    assert "documento" in mcp_server.exportar_documento(reemplazar=True)
    with ZipFile(output) as archive:
        assert b"Texto nuevo" in archive.read("word/document.xml")
    assert list(output.parent.iterdir()) == [output]


def test_style_and_template_paths_are_local(folder, monkeypatch):
    calls = mock_converter(monkeypatch)
    assert "dentro de la carpeta" in mcp_server.exportar_documento(estilo_csl="../prueba.csl")["error"]
    assert "extensión .docx" in mcp_server.exportar_documento(plantilla_docx="plantilla.odt")["error"]
    assert not calls


@pytest.mark.skipif(not exportacion.pandoc_executable(), reason="Pandoc requiere instalación local")
def test_real_docx_contains_figure_and_citation_without_finding_comment(folder):
    figures = folder / "resultados"
    figures.mkdir()
    image = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jQbcAAAAASUVORK5CYII="
    )
    (figures / "figura.png").write_bytes(image)
    (folder / DRAFT).write_text(
        "## Resultados\n\nLa tasa del control fue del 42%. <!-- hallazgo:1 -->\n\n"
        "Compárese con el estudio anterior [@smith2020].\n\n"
        "![Figura del estudio](../resultados/figura.png)\n",
        encoding="utf-8",
    )
    (folder / BIBLIOGRAPHY).write_text(
        "@article{smith2020, author={Smith, Jane}, title={Tasas comparadas}, year={2020}, "
        "journal={Revista de Prueba}}\n",
        encoding="utf-8",
    )
    result = exportacion.export_document(folder)
    assert not result["avisos"]
    with ZipFile(folder / exportacion.WORD_DOCUMENT) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
        assert "Tasas comparadas" in document and "Smith" in document and "Referencias" in document
        assert "hallazgo:1" not in document and "[@smith2020]" not in document
        assert any(name.startswith("word/media/") for name in archive.namelist())
