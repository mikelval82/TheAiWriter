"""Document progress and next step, read from local files without a model."""

from pathlib import Path

from ai_writer import revisor, verificacion
from ai_writer.library import Project, is_template


def _material(path: Path) -> str:
    if not path.exists():
        return "falta"
    return "plantilla" if is_template(path) else "escrito"


def document_status(folder: Path) -> dict:
    """Summarize materials, reports and the next task in their working order."""
    folder = Path(folder)
    project = Project.load(folder)
    materials = {"materiales/abstract.md": _material(folder / "materiales/abstract.md")}
    if project.tipo == "convocatoria":
        materials["materiales/equipo.md"] = _material(folder / "materiales/equipo.md")
        materials["convocatoria/*.pdf"] = (
            "escrito" if any(
                p.suffix.lower() == ".pdf"
                for p in (folder / "convocatoria").rglob("*") if p.is_file()
            ) else "falta"
        )
    if project.tipo == "resultados":
        materials["resultados/*.csv"] = (
            "escrito" if any(
                p.suffix.lower() == ".csv"
                for p in (folder / "resultados").rglob("*") if p.is_file()
            ) else "falta"
        )
    draft = folder / verificacion.DRAFT
    text = draft.read_text(encoding="utf-8") if draft.exists() else ""
    has_draft = bool(text.strip())
    result = folder / verificacion.RESULT
    checks = {}
    verification = {"estado": "sin hacer"}
    if result.exists():
        checks = verificacion.status(folder)
        judge = checks.get("juez", {})
        state = judge.get("estado", "sin_lanzar")
        verification = {
            "estado": {
                "en_curso": "juez en curso", "sin_lanzar": "terminado",
                "desactualizado": "desactualizada",
            }.get(state, state),
            "juez": judge, "recuento": verificacion.summary(checks.get("apoyo", [])),
            "informe": verificacion.REPORT,
        }
        if draft.exists() and draft.stat().st_mtime_ns > result.stat().st_mtime_ns:
            verification["estado"] = "desactualizada"
    review_path = folder / revisor.REVIEW
    review = revisor.review_status(folder) if review_path.exists() else {"estado": "sin hacer"}
    missing = [name for name, state in materials.items() if state != "escrito"]
    problems = (
        any(e["veredicto"] in ("tergiversada", "no_apoyada") for e in checks.get("apoyo", []))
        or checks.get("cifras", {}).get("sin_origen")
        or checks.get("convocatoria", {}).get("faltan")
    )
    if missing:
        next_step = f"Completar {missing[0]}"
    elif not has_draft:
        next_step = "/theaiwriter:escribir"
    elif verification["estado"] == "juez en curso" or review["estado"] == "en_curso":
        next_step = "/theaiwriter:estado"
    elif verification["estado"] in ("sin hacer", "desactualizada"):
        next_step = "/theaiwriter:comprobar"
    elif problems:
        next_step = "/theaiwriter:corregir"
    elif not review_path.exists():
        next_step = "/theaiwriter:revisar"
    else:
        next_step = "pasar a Word: guía en docs/exportar.md"
    return {
        "tipo": project.tipo, "materiales": materials,
        "palabras": len(text.split()), "comprobacion": verification,
        "revision": review, "siguiente": next_step,
    }
