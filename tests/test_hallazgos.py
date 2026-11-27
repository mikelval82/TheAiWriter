"""Exercise the results workflow with local evidence and persisted decisions."""

import json

import pytest

from ai_writer import mcp_server
from ai_writer.hallazgos import REGISTRY, Hallazgo, Propuesta, Seleccion
from ai_writer.library import Project


def write_notebook(path, *, code="print('media del control 17.5')", output=True):
    path.write_text(json.dumps({"cells": [
        {"cell_type": "markdown", "source": ["# Resultados"]},
        {"cell_type": "code", "source": [code], "outputs": [
            {"output_type": "stream", "text": ["media del control 17.5\n"]},
            {"output_type": "display_data", "data": {"image/png": "elided"}},
        ] if output else []},
    ]}), encoding="utf-8")


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    Project(tipo="resultados", titulo="Comparación de grupos").save(tmp_path)
    for name in ("materiales", "resultados", "analisis"):
        (tmp_path / name).mkdir()
    (tmp_path / "materiales/abstract.md").write_text("Comparar dos grupos.", encoding="utf-8")
    return tmp_path


def proposal(*, row=1, group="control", value="42%", edit=None):
    return Propuesta(hallazgo=Hallazgo(
        enunciado=f"La tasa de {group} fue del {value}.",
        metrica="tasa",
        grupo=group,
        valor=value,
        unidad="%",
        fuente={"tipo": "csv", "archivo": "resultados/tasas.csv",
                "fila": row, "columna": "tasa", "columna_grupo": "grupo"},
    ), sustituye=edit)


def notebook_proposal(value="17.5"):
    return Propuesta(hallazgo=Hallazgo(
        enunciado=f"La media del control fue {value}.",
        metrica="media",
        grupo="control",
        valor=value,
        fuente={"tipo": "cuaderno", "archivo": "analisis/estudio.ipynb", "celda": 2,
                "salida": 1, "fragmento": "media del control 17.5"},
    ))


def selection(entry):
    return Seleccion(id=entry["id"], version=entry["version"])


def test_inventory_guides_to_results_without_requiring_csv(project):
    (project / "analisis/estudio.R").write_text("# cálculo")
    (project / "resultados/figura.svg").write_text("<svg/>")
    notebook = project / "analisis/estudio.ipynb"
    write_notebook(notebook, output=False)

    materials = {item["archivo"]: item for item in mcp_server.estado_hallazgos()["materiales"]}
    assert materials["materiales/abstract.md"]["tipo"] == "nota"
    assert materials["analisis/estudio.R"]["tipo"] == "script"
    assert materials["resultados/figura.svg"]["tipo"] == "figura"
    assert materials["analisis/estudio.ipynb"]["salidas_texto"] == 0
    status = mcp_server.estado_documento()
    assert status["materiales"]["salidas del análisis"] == "falta"
    assert not (project / REGISTRY).exists()

    write_notebook(notebook)
    assert mcp_server.estado_documento()["siguiente"] == "/theaiwriter:hallazgos"
    entry, = mcp_server.guardar_hallazgos([notebook_proposal()])["hallazgos"]
    assert entry["evidencia"] == {"fragmento": "media del control 17.5"}
    approved, = mcp_server.decidir_hallazgos([selection(entry)], "aprobado")["hallazgos"]
    assert approved["estado"] == "aprobado"
    assert mcp_server.estado_documento()["siguiente"] == "/theaiwriter:escribir"

    write_notebook(notebook, code="print('media del control 17.5')  # cambió el cálculo")
    assert mcp_server.estado_documento()["hallazgos"]["por_revisar"] == 1
    stale, = mcp_server.estado_hallazgos(incluir_materiales=False)["hallazgos"]
    assert stale["estado"] == "por_revisar"
    assert "cambió" in mcp_server.decidir_hallazgos([selection(approved)], "aprobado")["error"]
    assert mcp_server.decidir_hallazgos([selection(stale)], "aprobado")["hallazgos"][0]["estado"] == "aprobado"


def test_csv_group_mismatch_rolls_back_whole_batch(project):
    table = project / "resultados/tasas.csv"
    table.write_text("grupo;tasa\ncontrol;42%\ntratamiento;18%\n", encoding="utf-8-sig")
    result = mcp_server.guardar_hallazgos([proposal(), proposal(group="tratamiento")])
    assert "grupo de la fila es «control»" in result["error"]
    assert mcp_server.estado_hallazgos()["hallazgos"] == []

    proposals = [proposal(), proposal(row=2, group="tratamiento", value="18%")]
    entries = mcp_server.guardar_hallazgos(proposals)["hallazgos"]
    assert mcp_server.guardar_hallazgos(proposals)["hallazgos"] == entries
    approved = mcp_server.decidir_hallazgos([selection(e) for e in entries], "aprobado")["hallazgos"]
    assert [e["estado"] for e in approved] == ["aprobado", "aprobado"]
    assert mcp_server.estado_hallazgos()["hallazgos"] == approved

    updated = "grupo;tasa\ncontrol;43%\ntratamiento;18%\n"
    table.write_text(updated, encoding="utf-8")
    first, second = mcp_server.estado_hallazgos()["hallazgos"]
    assert first["estado"] == "por_revisar" and second == approved[1]
    assert "43%" in first["aviso"]
    assert "cambió" in mcp_server.decidir_hallazgos([selection(approved[0])], "aprobado")["error"]

    updated_first, unchanged = mcp_server.guardar_hallazgos(
        [proposal(value="43%", edit=selection(first))]
    )["hallazgos"]
    assert updated_first["id"] == first["id"] and updated_first["estado"] == "propuesto"
    pending, approved_second = mcp_server.decidir_hallazgos([selection(updated_first)], "pendiente")[
        "hallazgos"
    ]
    assert pending["estado"] == "pendiente" and approved_second == second
    assert table.read_text(encoding="utf-8") == updated


def test_text_requires_exact_value_and_keeps_precise_location(project):
    path = project / "resultados/medias.md"
    path.write_text("# Media\nLa media del control fue -17.5 unidades.\n", encoding="utf-8")
    item = Hallazgo(
        enunciado="La media del control fue 17.5 unidades.",
        metrica="media", valor="17.5", grupo="control", unidad="unidades",
        fuente={"tipo": "texto", "archivo": "resultados/medias.md", "linea": 2,
                "fragmento": "media del control fue -17.5 unidades"},
    )
    assert "no aparece" in mcp_server.guardar_hallazgos([Propuesta(hallazgo=item)])["error"]
    corrected = item.model_copy(update={"valor": "-17.5", "enunciado": "La media fue -17.5."})
    entry, = mcp_server.guardar_hallazgos([Propuesta(hallazgo=corrected)])["hallazgos"]
    assert entry["fuente"]["linea"] == 2
    assert mcp_server.decidir_hallazgos([selection(entry)], "aprobado")["hallazgos"][0][
        "estado"
    ] == "aprobado"
    path.unlink()
    assert mcp_server.estado_hallazgos()["hallazgos"][0]["estado"] == "por_revisar"


def test_existing_project_and_unusable_sources(project):
    write_notebook(project / "analisis/estudio.ipynb", output=False)
    error = mcp_server.guardar_hallazgos([notebook_proposal()])["error"]
    assert "carece de esa salida guardada" in error
    proposal_outside = proposal()
    proposal_outside.hallazgo.fuente.archivo = "resultados/../tasas.csv"
    assert "Ruta de evidencia" in mcp_server.guardar_hallazgos([proposal_outside])["error"]
    assert mcp_server.estado_hallazgos()["hallazgos"] == []
    Project(tipo="perspectiva", titulo="Otro proyecto").save(project)
    assert "tipo resultados" in mcp_server.estado_hallazgos()["error"]
