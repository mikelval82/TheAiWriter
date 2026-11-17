"""Official call requirements and draft conformity, without any model."""

import copy

import pytest
import yaml

from ai_writer.convocatoria import CallFicha, check_call, check_ficha
from tests.fake_zotero import make_pdf

QUOTE = "The proposal must explain its motivation and expected scientific impact"
SOURCE = {"fichero": "instrucciones.pdf", "pagina": 1, "cita": QUOTE}


@pytest.fixture
def ficha():
    return {
        "convocatoria": "Proyectos de prueba", "confirmada": False, "plazo": None,
        "apartados": [
            {"titulo": title, "nivel": level, "obligatorio": required,
             "condicion": None if required else "Si se solicita formación",
             "pide": "Explicar la propuesta", "criterios": ["Calidad"],
             "fuente": copy.deepcopy(SOURCE)}
            for title, level, required in (
                ("Motivación", 2, True), ("Impacto esperado", 3, True), ("Formación", 2, False)
            )
        ],
        "limites": {
            "paginas": 2, "palabras_por_pagina": 10, "fuente": copy.deepcopy(SOURCE),
            "campos": [
                {"nombre": "Impacto", "caracteres": 12, "apartado": "Impacto esperado",
                 "fuente": copy.deepcopy(SOURCE)},
                {"nombre": "Resumen web", "caracteres": 200, "apartado": None,
                 "fuente": copy.deepcopy(SOURCE)},
            ],
        },
        "idioma": {"regla": "Inglés", "fuente": copy.deepcopy(SOURCE)},
        "criterios": [{"nombre": "Calidad", "maximo": 30, "umbral": 20,
                       "descripcion": "Calidad científica", "fuente": copy.deepcopy(SOURCE)}],
    }


def save_ficha(folder, ficha):
    path = folder / "convocatoria/ficha.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(ficha, allow_unicode=True), encoding="utf-8")


@pytest.fixture
def official(tmp_path, ficha):
    make_pdf(tmp_path / "convocatoria/instrucciones.pdf", [("Instructions", QUOTE)])
    save_ficha(tmp_path, ficha)
    return tmp_path


def test_ficha_checks_every_source_and_keeps_confirmation(official, ficha):
    data = check_ficha(official)
    assert data == {"requisitos": 8, "comprobados": 8, "fallidos": [], "avisos": [],
                    "confirmada": False}
    ficha["confirmada"] = True
    save_ficha(official, ficha)
    assert check_ficha(official)["confirmada"] is True


@pytest.mark.parametrize("quote", ["Invented words about a different official requirement",
                                   "Too few words"])
def test_ficha_rejects_invented_or_short_quotes(official, ficha, quote):
    ficha["apartados"][0]["fuente"]["cita"] = quote
    save_ficha(official, ficha)
    data = check_ficha(official)
    assert data["requisitos"] == 8 and data["comprobados"] == 7
    assert len(data["fallidos"]) == 1
    entry = data["fallidos"][0]
    assert entry["donde"].startswith("apartados[0]") and entry["cita"] == quote
    assert entry["fichero"] == "instrucciones.pdf" and entry["pagina"] == 1
    assert entry["motivo"]


@pytest.mark.parametrize("page,warning", [(2, False), (4, True)])
def test_wrong_page_warns_only_outside_the_one_page_margin(tmp_path, ficha, page, warning):
    sections = [("Other", "Other instructions apply here.")] * (page - 1) + [("Rule", QUOTE)]
    make_pdf(tmp_path / "convocatoria/instrucciones.pdf", sections)
    save_ficha(tmp_path, ficha)
    data = check_ficha(tmp_path)
    assert data["comprobados"] == 8 and data["fallidos"] == []
    assert bool(data["avisos"]) == warning
    if warning:
        assert data["avisos"][0]["pagina"] == 1
        assert "±1" in data["avisos"][0]["motivo"]


@pytest.mark.parametrize("location", ["section", "pages", "field", "language", "criterion"])
def test_ficha_requires_sources(official, ficha, location):
    target = {
        "section": ficha["apartados"][0], "pages": ficha["limites"],
        "field": ficha["limites"]["campos"][0], "language": ficha["idioma"],
        "criterion": ficha["criterios"][0],
    }[location]
    del target["fuente"]
    save_ficha(official, ficha)
    data = check_ficha(official)
    assert "no es válida" in data["error"] and "fuente" in data["error"]


@pytest.mark.parametrize("filename", ["ausente.pdf", "instrucciones.txt", "../ajeno.pdf",
                                     "/ajeno.pdf", "falso.pdf"])
def test_ficha_only_reads_pdfs_inside_its_folder(official, ficha, filename):
    (official / "convocatoria/falso.pdf").write_text("No es PDF", encoding="utf-8")
    ficha["apartados"][0]["fuente"]["fichero"] = filename
    save_ficha(official, ficha)
    data = check_ficha(official)
    assert data["comprobados"] == 7 and len(data["fallidos"]) == 1


def test_absent_malformed_and_invalid_fichas_return_errors(tmp_path):
    assert "falta" in check_ficha(tmp_path)["error"]
    path = tmp_path / "convocatoria/ficha.yaml"
    path.parent.mkdir()
    for content in ("[", "convocatoria: Prueba\n", "[]"):
        path.write_text(content, encoding="utf-8")
        assert "no es válida" in check_ficha(tmp_path)["error"]


def test_defaults_and_optional_sources(official, ficha):
    ficha["limites"] = {"paginas": None, "campos": []}
    ficha["idioma"] = None
    ficha["criterios"] = []
    save_ficha(official, ficha)
    assert CallFicha.load(official).limites.palabras_por_pagina == 500
    assert check_ficha(official)["requisitos"] == 3
    assert check_call("", ficha)["extension"]["estado"] == "sin_limite"


def test_call_reports_missing_conditional_and_extra_headings(ficha):
    data = check_call("## Motivación\nTexto\n### Otra cosa\nTexto", ficha)
    assert data["faltan"] == ["Impacto esperado"]
    assert data["condicionales_ausentes"] == [
        {"titulo": "Formación", "condicion": "Si se solicita formación"}
    ]
    assert data["sobran"] == ["Otra cosa"] and data["orden"] is True


def test_call_accepts_numbered_normalized_headings_and_reports_first_inversion(ficha):
    data = check_call("## 2.1. MOTIVACION: ##\n### 3) Impacto   esperado.\n", ficha)
    assert data["faltan"] == data["sobran"] == [] and data["orden"] is True
    data = check_call("### Impacto esperado\n## Motivación\n## Formación", ficha)
    assert data["orden"] == ["Motivación"]


@pytest.mark.parametrize("words,state", [(17, "ok"), (18, "aviso"), (20, "aviso"),
                                        (21, "excedido")])
def test_call_word_budget_excludes_title_and_code(ficha, words, state):
    text = ("# Título que no debe contarse\n" + "palabra " * words +
            "\n```md\n## Motivación\n[PENDIENTE: código]\n```\n"
            "~~~\ntexto de código\n~~~\n    más código\n")
    length = check_call(text, ficha)["extension"]
    assert length == {"palabras": words, "paginas_estimadas": round(words / 10, 1),
                      "maximo": 2, "estado": state}
    assert check_call(text, ficha)["faltan"] == ["Motivación", "Impacto esperado"]


def test_field_character_limit_includes_subsection_text_and_excludes_headings(ficha):
    text = ("## Motivación\nContexto\n### Impacto esperado\n1234567\n"
            "#### Detalle\nabcdef\n## Formación\nOtra")
    data = check_call(text, ficha)
    assert data["campos"] == [{"nombre": "Impacto", "apartado": "Impacto esperado",
                               "caracteres": 14, "maximo": 12, "estado": "excedido"}]
    assert data["a_mano"] == [{"nombre": "Resumen web", "maximo": 200}]
    assert check_call("### Impacto esperado\n123", ficha)["campos"][0]["estado"] == "ok"
    absent = check_call("", ficha)["campos"][0]
    assert absent["caracteres"] is None and absent["estado"] == "ausente"


def test_pending_marks_retain_their_section(ficha):
    text = ("[PENDIENTE: idea]\n## Motivación\n[PENDIENTE: nombre] y [PENDIENTE: fecha]\n"
            "### Impacto esperado\n[PENDIENTE: recursos]")
    assert check_call(text, ficha)["pendientes"] == [
        {"marca": "[PENDIENTE: idea]", "seccion": ""},
        {"marca": "[PENDIENTE: nombre]", "seccion": "Motivación"},
        {"marca": "[PENDIENTE: fecha]", "seccion": "Motivación"},
        {"marca": "[PENDIENTE: recursos]", "seccion": "Impacto esperado"},
    ]
