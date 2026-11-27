"""Document progress and available actions, read from local files without a model."""

import re
from pathlib import Path

from ai_writer import revisor, verificacion
from ai_writer.evidencia import has_results, inventory
from ai_writer.hallazgos import list_findings
from ai_writer.hallazgos_borrador import report_counts
from ai_writer.library import Project, is_template

ESCRIBIR = "/theaiwriter:escribir"
COMPROBAR = "/theaiwriter:comprobar"
REVISAR = "/theaiwriter:revisar"
CORREGIR = "/theaiwriter:corregir"
ESTADO = "/theaiwriter:estado"
HALLAZGOS = "/theaiwriter:hallazgos"
WORD = "pasar a Word: guía en docs/exportar.md"


def _material(path: Path) -> str:
    if not path.exists():
        return "falta"
    return "plantilla" if is_template(path) else "escrito"


def _file_material(folder: Path, suffix: str) -> str:
    return "escrito" if any(
        p.is_file() and p.suffix.lower() == suffix for p in folder.rglob("*")
    ) else "falta"


def _stale(data: dict, report: Path, draft: Path, fingerprint: str) -> bool:
    if saved := data.get("borrador_sha256"):
        return saved != fingerprint
    return draft.stat().st_mtime_ns > report.stat().st_mtime_ns


def _problems(checks: dict, text: str) -> bool:
    citations = checks.get("citas", {})
    call = checks.get("convocatoria", {})
    return bool(
        any(citations.get(key) for key in (
            "desconocidas", "fuera_de_las_colecciones", "mal_formadas", "sin_pdf", "pendientes"
        ))
        or any(not quote["encontrada_en"] for quote in checks.get("citas_literales", []))
        or checks.get("atribuciones_sin_cita")
        or any(e["veredicto"] in ("tergiversada", "no_apoyada", "parcial")
               for e in checks.get("apoyo", []))
        or checks.get("cifras", {}).get("sin_origen")
        or any(call.get(key) for key in ("faltan", "sobran", "pendientes"))
        or call.get("orden", True) is not True
        or call.get("extension", {}).get("estado") == "excedido"
        or any(field["estado"] == "excedido" for field in call.get("campos", []))
        or re.search(r"\[PENDIENTE(?::[^\]\n]+)?\]", text, flags=re.IGNORECASE)
    )


def _next_action(
    missing: list[str], text: str, check: dict, review: dict, problems: bool,
    findings: dict[str, int] | None,
) -> dict:
    def navigation(action: str, reason: str, *alternatives: tuple[str, str]) -> dict:
        return {
            "siguiente": action,
            "motivo_siguiente": reason,
            "alternativas": [{"accion": step, "motivo": why} for step, why in alternatives],
        }

    if missing:
        reason = {
            "materiales/abstract.md": "Responde a las preguntas sobre tu estudio o idea.",
            "materiales/equipo.md": "Describe el equipo y los recursos de la propuesta.",
            "convocatoria/*.pdf": "Añade los PDF oficiales en convocatoria/.",
            "salidas del análisis": "Añade una tabla, una salida de texto o un cuaderno con salidas guardadas.",
        }[missing[0]]
        return navigation(f"Completar {missing[0]}", reason,
                          ("/theaiwriter:ayuda materiales", "Ver qué materiales admite el proyecto."))
    if findings is not None and (
        findings["por_revisar"] or not text.strip() and not findings["aprobado"]
    ):
        reason = ("Cambió la evidencia de un hallazgo aprobado." if findings["por_revisar"]
                  else "Revisa los hallazgos que pueden entrar en Resultados.")
        return navigation(HALLAZGOS, reason,
                          (f"{ESCRIBIR} solo Métodos", "Avanzar con la descripción del estudio."))
    if not text.strip() and findings:
        return navigation(ESCRIBIR, "Ya hay hallazgos aprobados para el borrador.",
                          (f"{ESCRIBIR} con pausa", "Aprobar el plan antes de redactar."),
                          (f"{HALLAZGOS} ver", "Volver a los hallazgos y decidir qué incluir."))
    if not text.strip():
        return navigation(ESCRIBIR, "Los materiales básicos están listos.",
                          (f"{ESCRIBIR} con pausa", "Aprobar el plan antes de redactar."))
    if check["estado"] == "juez en curso" or review["estado"] == "en_curso":
        return navigation(ESTADO, "Hay un informe en preparación.",
                          ("Leer borrador/documento.md", "Revisar el texto mientras se prepara."))
    if check["estado"] in ("sin hacer", "desactualizada"):
        return navigation(COMPROBAR, "Hace falta una comprobación del borrador actual.",
                          (f"{COMPROBAR} sin juez", "Hacer solo las comprobaciones inmediatas."))
    links = check.get("hallazgos", {})
    if links.get("por_revisar") or links.get("sin_vinculo"):
        return navigation(CORREGIR, "Hay frases del estudio cuyo vínculo requiere revisión.",
                          (f"{HALLAZGOS} ver", "Consultar qué enunciados y fuentes están aprobados."),
                          ("Leer informes/comprobacion.md", "Localizar cada frase y su fuente."))
    if problems:
        return navigation(CORREGIR, "Hay citas, cifras o datos pendientes que requieren una decisión.",
                          ("Leer informes/comprobacion.md", "Consultar los avisos y sus fuentes."),
                          (REVISAR, "Revisar el argumento con los pendientes a la vista."))
    if check["recuento"]["sin_juzgar"] or check["estado"] in ("limite_de_uso", "interrumpido", "error"):
        reason = {
            "limite_de_uso": "El juez se detuvo por el límite de uso. Reanuda cuando se renueve.",
            "interrumpido": "El juez se interrumpió. Puedes reanudar la comprobación.",
            "error": "El juez falló. Consulta el informe o vuelve a intentarlo.",
        }.get(check["estado"], "Todavía hay pares de frase y obra pendientes de juicio.")
        return navigation(COMPROBAR, reason,
                          ("Leer informes/comprobacion.md", "Comprobar los pares a mano."),
                          (REVISAR, "Revisar por criterios aunque el juicio de citas esté incompleto."))
    if review["estado"] != "terminado":
        reason = {
            "sin hacer": "El borrador está listo para una revisión por criterios.",
            "desactualizada": "La revisión corresponde a una versión anterior del borrador.",
            "limite_de_uso": "La revisión se detuvo por el límite de uso. Reanuda cuando se renueve.",
            "error": "La revisión falló. Puedes volver a intentarlo.",
        }.get(review["estado"], "La revisión anterior quedó incompleta.")
        return navigation(REVISAR, reason,
                          ("Leer borrador/documento.md", "Hacer una revisión manual."))
    if review.get("prioridades") or any(
        item.get("nivel") in ("mejorable", "flojo") for item in review.get("criterios", [])
    ):
        return navigation(f"{CORREGIR} la revisión", "La revisión propone cambios para el borrador.",
                          ("Leer informes/revision.md", "Decidir qué cambios tienen sentido."),
                          (WORD, "Exportar si ya has valorado las sugerencias."))
    return navigation(WORD, "La comprobación y la revisión del borrador actual están completas.",
                      ("Leer borrador/documento.md", "Hacer una última lectura."))


def document_status(folder: Path) -> dict:
    """Summarize materials, provisional and complete reports, and available actions."""
    folder = Path(folder)
    project = Project.load(folder)
    materials = {"materiales/abstract.md": _material(folder / "materiales/abstract.md")}
    if project.tipo == "convocatoria":
        materials["materiales/equipo.md"] = _material(folder / "materiales/equipo.md")
        materials["convocatoria/*.pdf"] = _file_material(folder / "convocatoria", ".pdf")
    findings = entries = None
    if project.tipo == "resultados":
        materials["salidas del análisis"] = "escrito" if has_results(inventory(folder)) else "falta"
        entries = list_findings(folder)
        findings = {
            state: sum(entry["estado"] == state for entry in entries)
            for state in ("propuesto", "aprobado", "pendiente", "por_revisar")
        }

    draft = folder / verificacion.DRAFT
    text = draft.read_text(encoding="utf-8") if draft.exists() else ""
    fingerprint = verificacion.draft_fingerprint(text)
    result = folder / verificacion.RESULT
    checks = {}
    verification = {"estado": "sin hacer"}
    if result.exists():
        checks = verificacion.status(folder, findings=entries)
        judge = checks.get("juez", {})
        state = judge.get("estado", "sin_lanzar")
        stale = draft.exists() and _stale(checks, result, draft, fingerprint)
        if "total_pares_citados" not in checks and not stale:
            checks["total_pares_citados"] = verificacion.count_cited_pairs(text)
        stats = verificacion.support_summary(checks)
        if state == "en_curso":
            state = "juez en curso"
        elif stale or checks.get("hallazgos_desactualizados") or state == "desactualizado":
            state = "desactualizada"
        elif state in ("sin_lanzar", "terminado"):
            state = "parcial" if stats["sin_juzgar"] else "terminado"
        verification = {
            "estado": state, "juez": judge, "recuento": stats, "informe": verificacion.REPORT,
        }
        if "hallazgos_borrador" in checks:
            verification["hallazgos"] = report_counts(checks["hallazgos_borrador"])

    review_path = folder / revisor.REVIEW
    review = revisor.review_status(folder) if review_path.exists() else {"estado": "sin hacer"}
    if review["estado"] == "terminado" and draft.exists():
        if _stale(review, review_path, draft, fingerprint):
            review["estado"] = "desactualizada"
        elif any(item.get("nivel") == "sin_evaluar" for item in review.get("criterios", [])):
            review["estado"] = "parcial"

    missing = [name for name, state in materials.items() if state != "escrito"]
    return {
        "titulo": project.titulo, "tipo": project.tipo, "materiales": materials,
        "palabras": len(text.split()), "comprobacion": verification, "revision": review,
        **({"hallazgos": findings} if findings is not None else {}),
        **_next_action(missing, text, verification, review, _problems(checks, text), findings),
    }
