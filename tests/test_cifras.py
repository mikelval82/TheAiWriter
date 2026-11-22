"""Tests for own figures checked against result files, without a model."""

import pytest

from ai_writer.cifras import check_figures


@pytest.fixture
def results(tmp_path):
    folder = tmp_path / "resultados"
    folder.mkdir()
    (folder / "metricas.csv").write_text("modelo,valor\nA,0.94326\n", encoding="utf-8")
    return folder


@pytest.mark.parametrize("figure", ["0,94", "0.94", "0,943", "0.943"])
def test_figures_match_at_two_or_three_decimal_places(results, figure):
    data = check_figures(f"## Resultados\nLa precisión fue {figure}.", results)
    assert (data["comprobadas"], data["con_origen"], data["sin_origen"]) == (1, 1, [])
    assert data["ficheros"] == ["metricas.csv"]


def test_altered_figure_reports_its_sentence_and_section(results):
    data = check_figures("## Resultados\nLa precisión fue 0,953. Otro resultado.", results)
    assert data["sin_origen"] == [
        {"cifra": "0,953", "seccion": "Resultados", "frase": "La precisión fue 0,953."}
    ]


@pytest.mark.parametrize("figure", ["94,3 %", "94.3%", "94%"])
def test_percentages_match_fractions(results, figure):
    data = check_figures(f"La precisión fue {figure}.", results)
    assert (data["comprobadas"], data["con_origen"]) == (1, 1)


def test_percentage_can_match_an_unscaled_value(results):
    (results / "porcentajes.csv").write_text("porcentaje\n95\n", encoding="utf-8")
    assert check_figures("Se obtuvo un 95%.", results)["con_origen"] == 1


@pytest.mark.parametrize("citation", [" [@obra2020]", ". [@obra2020]", " [@?]"])
def test_a_sentence_with_a_citation_is_ignored(results, citation):
    data = check_figures(f"Otros obtuvieron 0,953{citation}. Aquí fue 0,943.", results)
    assert (data["comprobadas"], data["con_origen"]) == (1, 1)


@pytest.mark.parametrize(
    "heading", ["Métodos", "METODOS", "Methods", "Introducción", "Introduction"]
)
def test_introduction_and_methods_include_their_subsections(results, heading):
    text = f"## {heading}\nFue 0,953.\n\n### Datos\nFue 0,954.\n\n## Resultados\nFue 0,943."
    data = check_figures(text, results)
    assert (data["comprobadas"], data["con_origen"]) == (1, 1)


def test_integers_without_a_percentage_are_ignored(results):
    assert check_figures("Se usaron 150 muestras en 2026.", results)["comprobadas"] == 0


def test_markdown_results_and_recursive_paths(results):
    folder = results / "resumen"
    folder.mkdir()
    (folder / "calculos.md").write_text(
        "La diferencia fue -0,0123 y el recuento 47.", encoding="utf-8"
    )
    data = check_figures("La diferencia fue -0,012. Se alcanzó el 47%.", results)
    assert (data["comprobadas"], data["con_origen"]) == (2, 2)
    assert data["ficheros"] == ["metricas.csv", "resumen/calculos.md"]


@pytest.mark.parametrize("exists", [True, False])
def test_no_tables_warns_and_marks_all_figures(tmp_path, exists):
    folder = tmp_path / "resultados"
    if exists:
        folder.mkdir()
        (folder / "figura.svg").write_text("0.943", encoding="utf-8")
    data = check_figures("Fue 0,943 y un 95%.", folder)
    assert data["comprobadas"] == len(data["sin_origen"]) == 2
    assert data["con_origen"] == 0 and data["ficheros"] == [] and data["aviso"]


def test_empty_tables_warn(results):
    (results / "metricas.csv").write_text("modelo,valor\n", encoding="utf-8")
    data = check_figures("Fue 0,943.", results)
    assert data["aviso"] and len(data["sin_origen"]) == 1
    assert data["ficheros"] == ["metricas.csv"]


@pytest.mark.parametrize("source,figure", [("0.945", "0,95"), ("0.945", "0,94"),
                                          ("-1.225", "-1,23"), ("2.675", "2,67")])
def test_python_and_half_up_rounding_are_both_accepted(results, source, figure):
    (results / "metricas.csv").write_text(f"valor\n{source}\n", encoding="utf-8")
    assert check_figures(f"Fue {figure}.", results)["con_origen"] == 1


def test_semicolon_csv_with_decimal_commas_and_scientific_notation(results):
    (results / "metricas.csv").write_text(
        'modelo;valor;error\nA;0,94326;1.23e-2\nB;"0,823";NaN\n', encoding="utf-8"
    )
    data = check_figures("Fue 0,943, con error 0,012 y otro valor 0,823.", results)
    assert (data["comprobadas"], data["con_origen"]) == (3, 3)


def test_code_and_link_destinations_are_ignored_but_labels_are_checked(results):
    text = """## Resultados
La precisión fue 0,943 con `umbral = 0.953`.

```python
## Métodos
valor = 0.953
```

~~~
valor = 0.953
~~~

    valor = 0.953

La [precisión 0,943](https://ejemplo.test/0.953/figura_(0.954).png) fue estable.
![Figura](figuras/curva-0.953.png "Título 0.953")
[Informe][ref0.953]

[ref0.953]: resultados/0.953.md
<https://ejemplo.test/0.953>
"""
    data = check_figures(text, results)
    assert (data["comprobadas"], data["con_origen"]) == (2, 2)


def test_inline_code_is_preserved_in_the_reported_sentence(results):
    data = check_figures("Fue 0,953 con `umbral = 0.999`.", results)
    assert data["sin_origen"][0]["frase"] == "Fue 0,953 con `umbral = 0.999`."
