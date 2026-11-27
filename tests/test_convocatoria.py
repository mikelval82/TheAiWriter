"""Official call requirements and draft conformity, without any model."""

import copy

import fitz
import pytest
import yaml

from ai_writer.convocatoria import CallFicha, check_call, check_ficha, confirm_ficha
from tests.fake_zotero import make_pdf
from tests.test_passages import library  # noqa: F401
from tests.test_zotero_tools import document  # noqa: F401

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


def test_official_limit_mismatch_reaches_the_document_report(document, ficha):  # noqa: F811
    from ai_writer import mcp_server, verificacion

    mcp_server.crear_documento("convocatoria", "T")
    quote = "La memoria admite un máximo de 20 páginas"
    make_pdf(document / "convocatoria/instrucciones.pdf", [("Instructions", QUOTE + "\n" + quote)])
    ficha["limites"].update(paginas=25, fuente={**SOURCE, "cita": quote})
    save_ficha(document, ficha)
    (document / verificacion.DRAFT).write_text("## Motivación\nTexto", encoding="utf-8")

    report = mcp_server.comprobar_documento(juez=False)
    failure, = report["ficha"]["fallidos"]
    assert failure["donde"] == "limites.fuente" and failure["cita"] == quote
    assert "25" in failure["motivo"] and "20" in failure["motivo"]
    assert "aviso" in report["convocatoria"]
    assert quote in (document / verificacion.REPORT).read_text(encoding="utf-8")
    assert mcp_server.confirmar_ficha()["confirmada"] is False


def test_only_changed_rule_requires_confirmation(official, ficha):
    from ai_writer.library import Project

    Project(tipo="convocatoria", titulo="T").save(official)
    assert confirm_ficha(official)["confirmada"] is True
    ficha["confirmada"] = True
    ficha["apartados"][1]["pide"] = "Describir el impacto científico esperado"
    save_ficha(official, ficha)

    data = check_ficha(official)
    assert data["confirmada"] is False
    assert data["fallidos"] == []
    pending = [rule for rule in data["reglas"] if rule["estado"] == "por_revisar"]
    assert [rule["donde"] for rule in pending] == ["apartados[1].fuente (Impacto esperado)"]
    assert sum(rule["estado"] == "aprobada" for rule in data["reglas"]) == 7
    assert confirm_ficha(official)["confirmada"] is True
    assert check_ficha(official)["confirmada"] is True


def test_confirm_ficha_rejects_a_revision_the_investigator_did_not_see(official, ficha):
    from ai_writer.library import Project

    Project(tipo="convocatoria", titulo="T").save(official)
    shown = check_ficha(official)["revision"]
    ficha["apartados"][1]["pide"] = "Explicar el impacto y cómo se medirá"
    save_ficha(official, ficha)

    assert "cambió" in confirm_ficha(official, revision=shown)["motivo"]
    current = check_ficha(official)
    assert current["confirmada"] is False
    assert confirm_ficha(official, revision=current["revision"]) == {"confirmada": True}


def test_change_on_a_cited_page_only_invalidates_rules_sourced_there(official, ficha):
    from ai_writer.library import Project

    Project(tipo="convocatoria", titulo="T").save(official)
    quote = "The team should document the expected impact of the project"
    pdf = official / "convocatoria/instrucciones.pdf"
    make_pdf(pdf, [("Instructions", QUOTE), ("Impact", quote)])
    ficha["apartados"][1]["fuente"] = {**SOURCE, "pagina": 2, "cita": quote}
    save_ficha(official, ficha)
    assert confirm_ficha(official)["confirmada"]
    make_pdf(pdf, [("Instructions", QUOTE), ("Impact", quote + "\nAlso include outreach plans.")])

    report = check_ficha(official)
    assert report["fallidos"] == [] and report["confirmada"] is False
    assert [rule["id"] for rule in report["reglas"] if rule["estado"] == "por_revisar"] == [
        "apartado:Impacto esperado",
    ]


@pytest.mark.parametrize("quote,declared,status", [
    ("The proposal must not exceed 20 pages in total", 20, "coincide"),
    ("La memoria tendrá 20 páginas como máximo", 25, "difiere"),
    ("La memoria individual admite hasta 20 páginas y la coordinada hasta 35 páginas",
     20, "revision_manual"),
    ("El apartado describe resultados de las últimas 20 páginas", 25, "revision_manual"),
])
def test_page_limits_only_check_an_unambiguous_maximum(official, ficha, quote, declared, status):
    make_pdf(official / "convocatoria/instrucciones.pdf", [("Instructions", QUOTE + "\n" + quote)])
    ficha["limites"].update(paginas=declared, fuente={**SOURCE, "cita": quote})
    save_ficha(official, ficha)

    report = check_ficha(official)
    limit = next(rule for rule in report["reglas"] if rule["id"] == "paginas")
    assert limit["valor"] == status
    assert bool(report["fallidos"]) == (status == "difiere")


def test_character_limit_compares_grouped_number_in_source(official, ficha):
    quote = "El resumen admite un máximo de 3.500 caracteres"
    make_pdf(official / "convocatoria/instrucciones.pdf", [("Instructions", QUOTE + "\n" + quote)])
    ficha["limites"]["campos"][1]["fuente"] = {**SOURCE, "cita": quote}
    ficha["limites"]["campos"][1]["caracteres"] = 3500
    save_ficha(official, ficha)
    assert check_ficha(official)["fallidos"] == []
    ficha["limites"]["campos"][1]["caracteres"] = 5000
    save_ficha(official, ficha)
    failure, = check_ficha(official)["fallidos"]
    assert "5000" in failure["motivo"] and "3500" in failure["motivo"]


def test_page_limit_does_not_trust_a_repunctuated_number(official, ficha):
    quote = "La memoria admite un máximo de 20,0 páginas"
    make_pdf(official / "convocatoria/instrucciones.pdf", [("Instructions", QUOTE + "\n" + quote)])
    ficha["limites"].update(paginas=200, fuente={**SOURCE, "cita": quote.replace(",", "")})
    save_ficha(official, ficha)

    limit = next(rule for rule in check_ficha(official)["reglas"] if rule["id"] == "paginas")
    assert limit["valor"] == "revision_manual"


def test_call_reports_empty_required_sections_separately(ficha):
    text = "## Motivación\n<!-- Completar -->\n### Impacto esperado\n\n"
    data = check_call(text, ficha)
    assert data["faltan"] == []
    assert data["vacios"] == ["Motivación", "Impacto esperado"]
    text += "#### Plan\nResultados que se usarán para definir el calendario.\n"
    assert check_call(text, ficha)["vacios"] == []


def test_estado_guides_to_ficha_and_then_to_a_fresh_check(document, ficha):  # noqa: F811
    from ai_writer import mcp_server, verificacion

    mcp_server.crear_documento("convocatoria", "T")
    make_pdf(document / "convocatoria/instrucciones.pdf", [("Instructions", QUOTE)])
    for name in ("abstract.md", "equipo.md"):
        (document / "materiales" / name).write_text("Datos de la propuesta.", encoding="utf-8")
    (document / verificacion.DRAFT).write_text("## Motivación\nTexto", encoding="utf-8")
    save_ficha(document, ficha)
    assert mcp_server.confirmar_ficha()["confirmada"]
    mcp_server.comprobar_documento(juez=False)

    ficha["confirmada"] = True
    ficha["apartados"][1]["pide"] = "Explicar el impacto y cómo se medirá"
    save_ficha(document, ficha)
    assert mcp_server.estado_documento()["siguiente"] == "/theaiwriter:escribir solo ficha"
    assert mcp_server.confirmar_ficha()["confirmada"]
    assert mcp_server.estado_documento()["siguiente"] == "/theaiwriter:comprobar"


MODALITY_QUOTE = (
    "Número máximo de páginas incluyendo la portada y el índice: "
    "20 para proyectos individuales y 35 para proyectos coordinados."
)


@pytest.fixture
def modal_call(document, ficha):  # noqa: F811
    from ai_writer import mcp_server, verificacion

    mcp_server.crear_documento("convocatoria", "T")
    make_pdf(document / "convocatoria/instrucciones.pdf",
             [("Instructions", QUOTE), ("Límites de la memoria", MODALITY_QUOTE)])
    fuente = {**SOURCE, "pagina": 2, "cita": MODALITY_QUOTE}
    ficha["limites"].update(paginas=None, fuente=None, paginas_por_modalidad=[
        {"modalidad": "individual", "paginas": 20, "fuente": fuente},
        {"modalidad": "coordinado", "paginas": 35, "fuente": fuente},
    ])
    save_ficha(document, ficha)
    for name in ("abstract.md", "equipo.md"):
        (document / "materiales" / name).write_text("Datos de la propuesta.", encoding="utf-8")
    (document / verificacion.DRAFT).write_text("## Motivación\n" + "dato " * 250, encoding="utf-8")
    return document


def test_call_asks_for_modality_and_recalculates_the_limit(modal_call):
    from ai_writer import mcp_server, verificacion

    initial = mcp_server.comprobar_ficha()
    assert mcp_server.confirmar_ficha(initial["revision"])["confirmada"]
    report = mcp_server.comprobar_documento(juez=False)
    assert report["ficha"]["modalidad"]["opciones"] == ["individual", "coordinado"]
    assert report["convocatoria"]["extension"]["estado"] == "modalidad_pendiente"
    assert report["convocatoria"]["extension"]["maximo"] is None
    assert "modalidad" in report["ficha"]["modalidad"]["pregunta"]
    assert mcp_server.estado_documento()["siguiente"] == "/theaiwriter:escribir modalidad"
    assert "¿Cuál es la modalidad" in (modal_call / verificacion.REPORT).read_text()

    assert mcp_server.fijar_modalidad_convocatoria(" individual ")["seleccion"] == "individual"
    individual = mcp_server.comprobar_documento(juez=False)
    first = individual["convocatoria"]["extension"]
    assert first["maximo"] == 20 and first["estado"] == "excedido"
    assert first["modalidad"] == "individual"
    assert first["fuente"]["pagina"] == 2 and first["fuente"]["cita"] == MODALITY_QUOTE
    assert "modalidad" in mcp_server.fijar_modalidad_convocatoria("externo")["error"].casefold()
    assert mcp_server.comprobar_ficha()["modalidad"]["seleccion"] == "individual"

    assert mcp_server.fijar_modalidad_convocatoria("coordinado")["seleccion"] == "coordinado"
    assert mcp_server.estado_documento()["comprobacion"]["estado"] == "desactualizada"
    coordinated = mcp_server.comprobar_documento(juez=False)
    second = coordinated["convocatoria"]["extension"]
    assert second["maximo"] == 35 and second["estado"] == "ok"
    assert coordinated["ficha"]["confirmada"]
    assert not coordinated["ficha"]["fallidos"]
    markdown = (modal_call / verificacion.REPORT).read_text()
    assert "coordinado" in markdown and "p. 2" in markdown and MODALITY_QUOTE in markdown


def write_final_pdf(folder, pages):
    path = folder / "exportacion/documento.pdf"
    with fitz.open() as pdf:
        for _ in range(pages):
            pdf.new_page()
        pdf.save(path)
    return path


def test_final_pdf_uses_actual_pages_and_selected_limit(modal_call):
    from ai_writer import mcp_server, verificacion

    assert mcp_server.confirmar_ficha()["confirmada"]
    path = write_final_pdf(modal_call, 35)
    pending = mcp_server.comprobar_documento(juez=False)["convocatoria"]
    assert pending["pdf_final"]["paginas"] == 35
    assert pending["pdf_final"]["estado"] == "modalidad_pendiente"

    for mode, maximum, state in (("individual", 20, "excedido"), ("coordinado", 35, "ok")):
        mcp_server.fijar_modalidad_convocatoria(mode)
        report = mcp_server.comprobar_documento(juez=False)["convocatoria"]
        assert report["extension"]["paginas_estimadas"] != 35
        final = report["pdf_final"]
        assert final["paginas"] == 35 and final["maximo"] == maximum and final["estado"] == state
        assert final["archivo"] == path.relative_to(modal_call).as_posix()
        assert final["fuente"]["pagina"] == 2 and final["fuente"]["cita"] == MODALITY_QUOTE
        markdown = (modal_call / verificacion.REPORT).read_text(encoding="utf-8")
        assert "35 páginas reales" in markdown and "páginas estimadas" in markdown


def test_missing_added_and_replaced_pdf_invalidate_the_previous_check(modal_call):
    from ai_writer import mcp_server

    assert mcp_server.confirmar_ficha()["confirmada"]
    mcp_server.fijar_modalidad_convocatoria("individual")
    assert mcp_server.comprobar_documento(juez=False)["convocatoria"]["pdf_final"]["estado"] == (
        "pendiente"
    )
    path = write_final_pdf(modal_call, 20)
    assert mcp_server.estado_comprobacion()["convocatoria"]["pdf_final"]["estado"] == (
        "desactualizado"
    )
    status = mcp_server.estado_documento()
    assert status["comprobacion"]["estado"] == "desactualizada"
    assert status["siguiente"] == "/theaiwriter:comprobar sin juez"
    assert mcp_server.comprobar_documento(juez=False)["convocatoria"]["pdf_final"]["estado"] == "ok"

    path.write_text("Este archivo no es un PDF.", encoding="utf-8")
    assert mcp_server.estado_documento()["comprobacion"]["estado"] == "desactualizada"
    final = mcp_server.comprobar_documento(juez=False)["convocatoria"]["pdf_final"]
    assert final["estado"] == "error" and final["paginas"] is None
    path.unlink()
    assert mcp_server.comprobar_documento(juez=False)["convocatoria"]["pdf_final"]["estado"] == (
        "pendiente"
    )


def test_pdf_with_a_fixed_limit_waits_for_ficha_confirmation(modal_call, ficha):
    from ai_writer import mcp_server

    ficha["limites"]["paginas_por_modalidad"] = []
    quote = "La memoria admitirá un máximo de 20 páginas"
    make_pdf(modal_call / "convocatoria/instrucciones.pdf",
             [("Instructions", QUOTE), ("Límites de la memoria", quote)])
    ficha["limites"].update(paginas=20, fuente={**SOURCE, "pagina": 2, "cita": quote})
    save_ficha(modal_call, ficha)
    write_final_pdf(modal_call, 20)
    pending = mcp_server.comprobar_documento(juez=False)["convocatoria"]["pdf_final"]
    assert pending["estado"] == "ficha_pendiente" and pending["paginas"] == 20
    assert mcp_server.confirmar_ficha()["confirmada"]
    final = mcp_server.comprobar_documento(juez=False)["convocatoria"]["pdf_final"]
    assert final["estado"] == "ok" and final["fuente"]["cita"] == quote


BUDGET_QUOTE = (
    "Si se solicitan al menos 100.000 euros en costes directos, "
    "la memoria debe redactarse en inglés."
)


@pytest.fixture
def budget_call(modal_call, ficha):
    pdf = modal_call / "convocatoria/instrucciones.pdf"
    make_pdf(pdf, [("Instructions", QUOTE), ("Límites", MODALITY_QUOTE),
                   ("Idioma", BUDGET_QUOTE)])
    ficha["idioma"] = {
        "regla": "Inglés desde el umbral de costes directos",
        "fuente": {**SOURCE, "pagina": 3, "cita": BUDGET_QUOTE},
        "costes_directos": {"desde_eur": "100000", "idioma": "en"},
    }
    save_ficha(modal_call, ficha)
    return modal_call


def test_budget_threshold_is_inclusive_and_keeps_the_modality(budget_call):
    from ai_writer import mcp_server, verificacion
    from ai_writer.library import Project

    assert mcp_server.confirmar_ficha()["confirmada"]
    assert mcp_server.fijar_modalidad_convocatoria("coordinado")["seleccion"] == "coordinado"
    initial = mcp_server.comprobar_documento(juez=False)["ficha"]["idioma_por_presupuesto"]
    assert initial["estado"] == "costes_pendientes" and "costes directos" in initial["pregunta"]
    assert mcp_server.estado_documento()["siguiente"] == "/theaiwriter:escribir presupuesto"

    assert mcp_server.fijar_costes_directos_convocatoria("99999.99")["estado"] == "no_aplica"
    before = mcp_server.comprobar_documento(juez=False)
    assert before["ficha"]["idioma_por_presupuesto"]["estado"] == "no_aplica"
    assert "error" in mcp_server.fijar_costes_directos_convocatoria("100000.001")
    assert mcp_server.comprobar_ficha()["idioma_por_presupuesto"]["importe_eur"] == "99999.99"

    active = mcp_server.fijar_costes_directos_convocatoria("100000")
    assert active["estado"] == "idioma_distinto" and active["idioma_requerido"] == "en"
    assert active["fuente"]["pagina"] == 3 and active["fuente"]["cita"] == BUDGET_QUOTE
    assert mcp_server.estado_documento()["comprobacion"]["estado"] == "desactualizada"
    previous = mcp_server.estado_comprobacion()["ficha"]["idioma_por_presupuesto"]
    assert previous["estado"] == "desactualizado"
    report = mcp_server.comprobar_documento(juez=False)
    assert report["ficha"]["confirmada"]
    assert report["ficha"]["modalidad"]["seleccion"] == "coordinado"
    assert report["ficha"]["idioma_por_presupuesto"]["estado"] == "idioma_distinto"
    markdown = (budget_call / verificacion.REPORT).read_text(encoding="utf-8")
    assert "inglés" in markdown and BUDGET_QUOTE in markdown
    assert Project.load(budget_call).idioma == "es"

    project = Project.load(budget_call)
    project.idioma = "en-GB"
    project.save(budget_call)
    assert mcp_server.comprobar_ficha()["idioma_por_presupuesto"]["estado"] == "ok"
    mcp_server.fijar_modalidad_convocatoria("individual")
    assert mcp_server.comprobar_ficha()["idioma_por_presupuesto"]["importe_eur"] == "100000.00"
    assert mcp_server.fijar_costes_directos_convocatoria(None)["estado"] == "costes_pendientes"


def test_budget_threshold_cannot_disagree_with_an_explicit_quote(budget_call, ficha):
    from ai_writer import mcp_server

    ficha["idioma"]["costes_directos"]["desde_eur"] = "90000"
    save_ficha(budget_call, ficha)
    failure, = mcp_server.comprobar_ficha()["fallidos"]
    assert failure["id"] == "idioma"
    assert failure["cita"] == BUDGET_QUOTE
    assert not mcp_server.confirmar_ficha()["confirmada"]


def test_budget_language_cannot_disagree_with_an_explicit_quote(budget_call, ficha):
    ficha["idioma"]["costes_directos"]["idioma"] = "fr"
    save_ficha(budget_call, ficha)
    failure, = check_ficha(budget_call)["fallidos"]
    assert failure["id"] == "idioma" and "inglés" in failure["motivo"]


def test_page_limits_match_the_number_for_each_modality(modal_call, ficha):
    report = check_ficha(modal_call)
    rules = [rule for rule in report["reglas"] if rule["id"].startswith("paginas:")]
    assert [rule["valor"] for rule in rules] == ["coincide", "coincide"]

    ficha["limites"]["paginas_por_modalidad"][0]["paginas"] = 35
    save_ficha(modal_call, ficha)
    failure, = check_ficha(modal_call)["fallidos"]
    assert failure["id"] == "paginas:individual"
    assert "35" in failure["motivo"] and "20" in failure["motivo"]


def test_page_limit_does_not_infer_modality_from_an_unrelated_sentence(modal_call, ficha):
    quote = (
        "Los proyectos individuales entregarán un resumen. "
        "Los anexos tienen un máximo de 20 páginas."
    )
    make_pdf(modal_call / "convocatoria/instrucciones.pdf",
             [("Instructions", QUOTE), ("Límites de la memoria", MODALITY_QUOTE + "\n" + quote)])
    ficha["limites"]["paginas_por_modalidad"][0]["fuente"]["cita"] = quote
    save_ficha(modal_call, ficha)
    rule = next(rule for rule in check_ficha(modal_call)["reglas"]
                if rule["id"] == "paginas:individual")
    assert rule["valor"] == "revision_manual"


def test_modality_is_pending_if_the_saved_option_disappears(modal_call, ficha):
    from ai_writer import mcp_server

    assert mcp_server.fijar_modalidad_convocatoria("coordinado")["seleccion"] == "coordinado"
    ficha["limites"]["paginas_por_modalidad"].pop()
    save_ficha(modal_call, ficha)
    report = mcp_server.comprobar_ficha()
    assert report["modalidad"]["seleccion"] is None
    assert report["modalidad"]["opciones"] == ["individual"]


def test_ficha_checks_every_source_and_keeps_confirmation(official, ficha):
    from ai_writer.library import Project

    Project(tipo="convocatoria", titulo="T").save(official)
    data = check_ficha(official)
    assert {key: data[key] for key in ("requisitos", "comprobados", "fallidos", "avisos",
                                      "confirmada")} == {
        "requisitos": 8, "comprobados": 8, "fallidos": [], "avisos": [], "confirmada": False,
    }
    assert all(rule["estado"] == "por_revisar" for rule in data["reglas"])
    # Old files are readable, but the flag alone cannot certify their current contents.
    ficha["confirmada"] = True
    save_ficha(official, ficha)
    assert check_ficha(official)["confirmada"] is False
    assert confirm_ficha(official)["confirmada"] is True
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


def test_readable_call_ficha_and_confirmation_preserve_yaml(official, monkeypatch):
    from ai_writer import mcp_server
    from ai_writer.convocatoria import ficha_text
    from ai_writer.library import Project

    Project(tipo="convocatoria", titulo="T").save(official)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(official))
    path = official / "convocatoria/ficha.yaml"
    before = path.read_text(encoding="utf-8").replace(
        "confirmada: false", "confirmada: false  # Esperar el sí del usuario"
    ) + "\n# Comentario final\n"
    path.write_text(before, encoding="utf-8")
    text = ficha_text(official)
    assert text == mcp_server.mostrar_ficha()
    for part in ("Convocatoria: Proyectos de prueba", "Plazo: no consta", "Límite de páginas: 2",
                 "Impacto: 12 caracteres", "Idioma: Inglés", "1. Motivación (obligatorio)",
                 "3. Formación (condicional: Si se solicita formación)", "Calidad científica",
                 "Máximo: 30", "umbral: 20", "instrucciones.pdf, página 1"):
        assert part in text
    assert mcp_server.confirmar_ficha() == {"confirmada": True}
    assert path.read_text(encoding="utf-8") == before.replace("confirmada: false", "confirmada: true")
    stamp = path.stat().st_mtime_ns
    assert confirm_ficha(official) == {"confirmada": True}
    assert path.stat().st_mtime_ns == stamp


@pytest.mark.parametrize("failure", ["missing", "invalid", "failed"])
def test_confirmation_refuses_bad_sources_without_touching_yaml(official, ficha, failure):
    from ai_writer.library import Project

    Project(tipo="convocatoria", titulo="T").save(official)
    path = official / "convocatoria/ficha.yaml"
    if failure == "missing":
        path.unlink()
    elif failure == "invalid":
        path.write_text("[", encoding="utf-8")
    else:
        ficha["criterios"][0]["fuente"]["cita"] = "Invented words absent from the official document"
        save_ficha(official, ficha)
    before = path.read_bytes() if path.exists() else None
    result = confirm_ficha(official)
    assert result["confirmada"] is False and result["motivo"]
    assert (path.read_bytes() if path.exists() else None) == before


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_confirmation_adds_missing_key_after_first_line(official, newline):
    from ai_writer.library import Project

    Project(tipo="convocatoria", titulo="T").save(official)
    path = official / "convocatoria/ficha.yaml"
    before = "# Conservar comentario\n" + path.read_text().replace("confirmada: false\n", "")
    before = before.replace("\n", newline)
    path.write_bytes(before.encode())
    assert confirm_ficha(official) == {"confirmada": True}
    first, rest = before.split(newline, 1)
    assert path.read_bytes() == (first + newline + "confirmada: true" + newline + rest).encode()


def test_journal_text_and_confirmation(document):  # noqa: F811
    from ai_writer import mcp_server
    from ai_writer.convocatoria import ficha_text
    from tests.test_revisor import save_journal

    mcp_server.crear_documento("perspectiva", "T")
    save_journal(document, confirmed=False)
    path = document / "revista/ficha.yaml"
    before = path.read_text(encoding="utf-8")
    text = ficha_text(document)
    assert "Revista: Revista de prueba" in text
    assert "Impacto científico" in text and "página 1" in text
    assert mcp_server.mostrar_ficha() == text
    assert confirm_ficha(document) == {"confirmada": True}
    assert path.read_text(encoding="utf-8") == before.replace("confirmada: false", "confirmada: true")
    before = path.read_text(encoding="utf-8").replace(QUOTE, "Invented words that are not in the PDF")
    path.write_text(before, encoding="utf-8")
    assert confirm_ficha(document)["confirmada"] is False
    assert path.read_text(encoding="utf-8") == before
