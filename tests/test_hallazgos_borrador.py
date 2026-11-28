"""Verify the trail from approved evidence to statements in the manuscript."""


import pytest

from ai_writer import mcp_server, verificacion
from ai_writer.hallazgos_borrador import check_findings
from ai_writer.sentences import cited_paragraphs
from tests.test_hallazgos import notebook_proposal, proposal, selection, write_notebook
from tests.test_passages import library  # noqa: F401
from tests.test_zotero_tools import document  # noqa: F401


@pytest.fixture
def study(document):  # noqa: F811
    mcp_server.crear_documento("resultados", "T", colecciones=["Empatía"])
    (document / "materiales/abstract.md").write_text("Comparamos dos grupos.")
    (document / "resultados/tasas.csv").write_text("grupo,tasa\ncontrol,42%\ntratamiento,18%\n")
    write_notebook(document / "analisis/estudio.ipynb")
    items = mcp_server.guardar_hallazgos([
        proposal(), proposal(row=2, group="tratamiento", value="18%"), notebook_proposal(),
    ])["hallazgos"]
    approved = mcp_server.decidir_hallazgos([selection(entry) for entry in items], "aprobado")
    return document, approved["hallazgos"]


def test_study_checks_csv_and_notebook_and_reports_changed_group(study):
    folder, (control, treatment, notebook) = study
    correct = "\n".join(["## Resultados", "", *[
        entry["linea_borrador"] for entry in (control, treatment, notebook)
    ]])
    draft = folder / verificacion.DRAFT
    draft.write_text(correct, encoding="utf-8")
    report = mcp_server.comprobar_documento(juez=False)
    results = report["hallazgos_borrador"]
    assert (results["coinciden"], results["por_revisar"], results["sin_vinculo"]) == (3, 0, [])
    assert "cifras" not in report
    assert [entry["estado"] for entry in results["vinculos"]] == ["coincide"] * 3
    assert mcp_server.estado_documento()["siguiente"] == "/theaiwriter:revisar"

    wrong = correct.replace("de control fue del 42%", "de tratamiento fue del 42%")
    draft.write_text(wrong, encoding="utf-8")
    checked = mcp_server.comprobar_documento(juez=False)["hallazgos_borrador"]
    assert (checked["coinciden"], checked["por_revisar"]) == (2, 1)
    entry = checked["vinculos"][0]
    assert entry["estado"] == "frase_cambiada"
    assert entry["frase"] == "La tasa de tratamiento fue del 42%."
    assert entry["enunciado"] == "La tasa de control fue del 42%."
    assert entry["fuente"]["fila"] == 1 and entry["grupo"] == "control"
    status = mcp_server.estado_documento()
    assert status["siguiente"] == "/theaiwriter:corregir"
    assert status["comprobacion"]["hallazgos"] == {"coinciden": 2, "por_revisar": 1, "sin_vinculo": 0}
    markdown = (folder / verificacion.REPORT).read_text(encoding="utf-8")
    assert "resultados/tasas.csv · fila 1" in markdown
    assert "analisis/estudio.ipynb · celda 2, salida 1" in markdown


def test_source_changes_invalidate_saved_report_without_draft_edit(study):
    folder, (control, treatment, _) = study
    (folder / verificacion.DRAFT).write_text(
        "## Resultados\n" + control["linea_borrador"] + "\n" + treatment["linea_borrador"]
    )
    assert mcp_server.comprobar_documento(juez=False)["hallazgos_borrador"]["coinciden"] == 2

    table = folder / "resultados/tasas.csv"
    table.write_text("grupo,tasa\ncontrol,43%\ntratamiento,18%\n")
    assert mcp_server.estado_comprobacion()["hallazgos_desactualizados"] is True
    status = mcp_server.estado_documento()
    assert status["comprobacion"]["estado"] == "desactualizada"
    assert status["siguiente"] == "/theaiwriter:hallazgos"

    new = mcp_server.comprobar_documento(juez=False)
    assert not new.get("hallazgos_desactualizados")
    assert [e["estado"] for e in new["hallazgos_borrador"]["vinculos"]] == ["por_revisar", "coincide"]


def test_report_detects_bad_missing_and_unapproved_links(study):
    _, (control, treatment, notebook) = study
    pending = {**notebook, "estado": "pendiente"}
    text = """## Métodos
La muestra incluyó 23 personas.

## 3. Results
### Cohorts
La tasa de control fue del 42%. <!-- hallazgo:1 -->
    Ignora 900. <!-- hallazgo:91 -->
```text
Ignora 901. <!-- hallazgo:92 -->
```
<!-- Nota
Ignora 902. <!-- hallazgo:93 -->
La figura 3 muestra los grupos.
Véase `<!-- hallazgo:94 -->`.
Participaron 12 personas. Se registraron 3 eventos.
La media del control fue 17.5. <!-- hallazgo:3 -->
Una frase desconocida. <!-- hallazgo:77 -->
Una frase mal vinculada. <!-- hallazgo:1 --> Texto detrás.
Otra frase mal vinculada. <!-- hallazgo:1 --> <!-- hallazgo:2 -->
<!-- hallazgo:1 -->

## Discusión
Un hallazgo reutilizado. <!-- hallazgo:2 -->
"""
    report = check_findings(text, [control, treatment, pending])
    assert [entry["estado"] for entry in report["vinculos"]] == [
        "coincide", "pendiente", "desconocido", "marca_invalida", "marca_invalida",
        "marca_invalida", "frase_cambiada",
    ]
    assert [entry["frase"] for entry in report["sin_vinculo"]] == [
        "Participaron 12 personas.", "Se registraron 3 eventos.",
    ]
    assert report["coinciden"] == 1 and report["por_revisar"] == 6


def test_number_check_still_reads_legacy_results_until_register_is_used(document):  # noqa: F811
    mcp_server.crear_documento("resultados", "T", colecciones=["Empatía"])
    (document / "materiales/abstract.md").write_text("Comparamos dos grupos.")
    (document / "resultados/tasas.csv").write_text("grupo,tasa\ncontrol,42%\n")
    (document / verificacion.DRAFT).write_text("## Resultados\nLa tasa fue del 42%.")
    first = mcp_server.comprobar_documento(juez=False)
    assert first["cifras"]["con_origen"] == 1
    assert "hallazgos_borrador" not in first
    assert mcp_server.guardar_hallazgos([proposal()])["hallazgos"]
    assert mcp_server.estado_documento()["comprobacion"]["estado"] == "desactualizada"
    second = mcp_server.comprobar_documento(juez=False)
    assert "cifras" not in second
    assert second["hallazgos_borrador"]["sin_vinculo"][0]["frase"] == "La tasa fue del 42%."


def test_finding_marker_is_hidden_from_literature_citation_parser():
    report, = cited_paragraphs(
        "La tasa del control fue 42%. <!-- hallazgo:1 -->\n"
        "Smith atribuye el efecto al contexto [@smith2020empathy]."
    )
    assert report["frases"][0][0] == "Smith atribuye el efecto al contexto [@smith2020empathy]."
    assert report["previas"] == ["La tasa del control fue 42%."]
