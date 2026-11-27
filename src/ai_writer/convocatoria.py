"""Check official call requirements and draft conformity, without any model."""

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path
from stat import S_ISREG
from tempfile import NamedTemporaryFile
from typing import Literal, NamedTuple

import fitz
import yaml
from pydantic import BaseModel, Field, model_validator

from ai_writer.library import LibraryError, Project
from ai_writer.passages import page_texts
from ai_writer.presupuesto_convocatoria import (
    BudgetLanguage,
    budget_language_status,
    language_name,
    quoted_budget_language,
    read_amount,
)
from ai_writer.reglas_convocatoria import (
    ApplicableRule,
    Key,
    ProposalField,
    Source,
    Value,
    evaluate_rules,
    proposal_value,
    validate_rules,
)

FICHA = Path("convocatoria") / "ficha.yaml"
APPROVALS = FICHA.with_name("aprobaciones.json")
PROPOSAL = FICHA.with_name("propuesta.json")
COSTS = FICHA.with_name("costes-directos.json")
JOURNAL_FICHA = Path("revista") / "ficha.yaml"
FINAL_PDF = Path("exportacion") / "documento.pdf"
_HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)(?:\s+#+)?\s*$")
_NUMBER = re.compile(r"(?<!\w)[0-9]+(?:[., \u00a0\u202f][0-9]+)*(?!\w)")
_INTEGER = re.compile(r"(?:[0-9]+|[0-9]{1,3}(?:[., \u00a0\u202f][0-9]{3})+)")
_MAXIMUM = re.compile(
    r"\b(?:m[aá]xim[oa](?:\s+de)?|hasta|no\s+(?:m[aá]s\s+de|"
    r"(?:(?:podr[aá]|deber[aá])\s+)?(?:exceder|superar)(?:\s+de)?)|"
    r"maximum(?:\s+of)?|up\s+to|at\s+most|no\s+more\s+than|not\s+exceed)\s+$",
    re.I,
)
_PAGE_UNITS = r"p[aá]ginas?|pages?"
_PAGE_LIMIT_CUE = re.compile(r"\b(?:m[aá]xim[oa]|l[ií]mite)\s+de\s+p[aá]ginas\b", re.I)
_COMMENT = re.compile(r"<!--.*?(?:-->|$)", re.S)
_PENDING = re.compile(r"\[PENDIENTE(?::[^\]\n]+)?\]", re.I)
_FICHA_CHANGED = "La ficha cambió. Muéstrala y revísala otra vez."


class CallSection(BaseModel):
    titulo: str = Field(min_length=1)
    nivel: Literal[2, 3]
    obligatorio: bool
    condicion: str | None = None
    pide: str
    criterios: list[str] = Field(default_factory=list)
    fuente: Source


class FieldLimit(BaseModel):
    nombre: str = Field(min_length=1)
    caracteres: int = Field(gt=0)
    apartado: str | None = None
    fuente: Source


def _modality_key(label: str) -> str:
    return " ".join(label.casefold().split())


class ModalPageLimit(BaseModel):
    modalidad: str = Field(min_length=1)
    paginas: int = Field(gt=0)
    fuente: Source


class Limits(BaseModel):
    paginas: int | None = Field(default=None, gt=0)
    palabras_por_pagina: int = Field(default=500, gt=0)
    fuente: Source | None = None
    campos: list[FieldLimit] = Field(default_factory=list)
    paginas_por_modalidad: list[ModalPageLimit] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_page_source(self):
        if self.paginas is not None and self.fuente is None:
            raise ValueError("limites.fuente es obligatoria si hay un límite de páginas")
        choices = [_modality_key(limit.modalidad) for limit in self.paginas_por_modalidad]
        if choices and self.paginas is not None:
            raise ValueError("Usa un límite general o límites por modalidad.")
        if "" in choices or len(set(choices)) != len(choices):
            raise ValueError("Cada límite por modalidad debe tener un nombre distinto y no vacío.")
        return self


class LanguageRule(BaseModel):
    regla: str
    fuente: Source
    costes_directos: BudgetLanguage | None = None


class Criterion(BaseModel):
    nombre: str = Field(min_length=1)
    maximo: float | None = Field(default=None, ge=0)
    umbral: float | None = Field(default=None, ge=0)
    descripcion: str
    fuente: Source


class CallFicha(BaseModel):
    convocatoria: str = Field(min_length=1)
    confirmada: bool = False
    plazo: str | None = None
    apartados: list[CallSection]
    limites: Limits
    idioma: LanguageRule | None = None
    criterios: list[Criterion] = Field(default_factory=list)
    datos_propuesta: dict[Key, ProposalField] = Field(default_factory=dict)
    reglas_aplicables: list[ApplicableRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_applicable_rules(self):
        validate_rules(self.datos_propuesta, self.reglas_aplicables)
        return self

    @classmethod
    def load(cls, folder: Path) -> "CallFicha":
        path = Path(folder) / FICHA
        if not path.exists():
            raise LibraryError(f"No hay ficha de la convocatoria: falta {FICHA}.")
        try:
            return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
        except (OSError, ValueError, yaml.YAMLError) as error:
            raise LibraryError(f"La ficha {FICHA} no es válida: {error}") from error


class JournalFicha(BaseModel):
    revista: str = Field(min_length=1)
    confirmada: bool = False
    criterios: list[Criterion] = Field(min_length=1)

    @classmethod
    def load(cls, folder: Path) -> "JournalFicha":
        path = Path(folder) / JOURNAL_FICHA
        if not path.exists():
            raise LibraryError(f"No hay ficha de la revista: falta {JOURNAL_FICHA}.")
        try:
            return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
        except (OSError, ValueError, yaml.YAMLError) as error:
            raise LibraryError(f"La ficha {JOURNAL_FICHA} no es válida: {error}") from error


class CallRule(NamedTuple):
    id: str
    location: str
    source: Source
    contents: dict
    limit: tuple[int, str, str] | None = None
    modality: str | None = None


def _call_rules(ficha: CallFicha) -> Iterable[CallRule]:
    for i, section in enumerate(ficha.apartados):
        yield CallRule(f"apartado:{section.titulo}", f"apartados[{i}].fuente ({section.titulo})",
                       section.fuente, section.model_dump())
    if ficha.limites.fuente is not None:
        limit = None
        if ficha.limites.paginas is not None:
            limit = (ficha.limites.paginas, "páginas", _PAGE_UNITS)
        yield CallRule("paginas", "limites.fuente", ficha.limites.fuente,
                       {"paginas": ficha.limites.paginas}, limit)
    for index, option in enumerate(ficha.limites.paginas_por_modalidad):
        yield CallRule(
            f"paginas:{_modality_key(option.modalidad)}",
            f"limites.paginas_por_modalidad[{index}].fuente ({option.modalidad})",
            option.fuente, option.model_dump(), (option.paginas, "páginas", _PAGE_UNITS),
            option.modalidad,
        )
    for i, field in enumerate(ficha.limites.campos):
        yield CallRule(f"campo:{field.nombre}", f"limites.campos[{i}].fuente ({field.nombre})",
                       field.fuente, field.model_dump(),
                       (field.caracteres, "caracteres", r"caracteres?|characters?"))
    if ficha.idioma is not None:
        yield CallRule(
            "idioma", "idioma.fuente", ficha.idioma.fuente,
            ficha.idioma.model_dump(mode="json", exclude_none=True),
        )
    for i, criterion in enumerate(ficha.criterios):
        yield CallRule(
            f"criterio:{criterion.nombre}", f"criterios[{i}].fuente ({criterion.nombre})",
            criterion.fuente, criterion.model_dump(),
        )
    for rule in ficha.reglas_aplicables:
        yield CallRule(
            f"regla:{rule.id}", f"{rule.requisito} ({rule.id})",
            rule.fuente, rule.model_dump(mode="json"),
        )


def _fingerprint(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_approvals(folder: Path) -> dict:
    try:
        saved = json.loads((folder / APPROVALS).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(saved, dict) or saved.get("version") != 1:
        return {}
    keys = saved.get("reglas")
    return saved if isinstance(keys, list) and all(isinstance(key, str) for key in keys) else {}


def _write_json(path: Path, data: dict) -> None:
    temp = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False,
        ) as stream:
            temp = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        temp.replace(path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def _proposal_data_path(folder: Path, key: str) -> Path:
    path = folder / FICHA.parent / f"dato-{key}.json"
    if not path.resolve().is_relative_to(folder.resolve()):
        raise LibraryError("El dato de la propuesta debe guardarse dentro del proyecto.")
    return path


def _proposal_values(folder: Path, ficha: CallFicha) -> dict:
    values = {}
    for name, field in ficha.datos_propuesta.items():
        try:
            saved = json.loads(_proposal_data_path(folder, name).read_text(encoding="utf-8"))
            value = proposal_value(field, saved["valor"])
            values[name] = str(value) if isinstance(value, Decimal) else value
        except (LibraryError, KeyError, TypeError, OSError, ValueError):
            continue
    return values


def set_proposal_value(folder: Path, key: str, value: Value | None) -> dict:
    folder = Path(folder)
    if Project.load(folder).tipo != "convocatoria":
        raise LibraryError("Los datos de la propuesta pertenecen a una convocatoria.")
    ficha = CallFicha.load(folder)
    if (field := ficha.datos_propuesta.get(key)) is None:
        raise LibraryError(f"La ficha no define el dato {key}.")
    normalized = proposal_value(field, value) if value is not None else None
    if isinstance(normalized, Decimal):
        normalized = str(normalized)
    _write_json(_proposal_data_path(folder, key), {"valor": normalized})
    return {"dato": key, "valor": normalized}


def _saved_modality(folder: Path) -> str | None:
    try:
        saved = json.loads((folder / PROPOSAL).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    choice = saved.get("modalidad") if isinstance(saved, dict) else None
    return choice if isinstance(choice, str) else None


def _saved_costs(folder: Path) -> Decimal | None:
    try:
        saved = json.loads((folder / COSTS).read_text(encoding="utf-8"))
        amount = saved.get("importe_eur") if isinstance(saved, dict) else None
        return read_amount(amount) if isinstance(amount, str) else None
    except (OSError, ValueError):
        return None


def budget_inputs_changed(folder: Path, budget: dict) -> bool:
    """Check whether the recorded budget verdict describes the current project inputs."""
    folder = Path(folder)
    amount = _saved_costs(folder)
    recorded = budget.get("importe_eur")
    try:
        return ((read_amount(recorded) if recorded is not None else None) != amount
                or Project.load(folder).idioma != budget.get("idioma_declarado"))
    except (LibraryError, OSError, ValueError, yaml.YAMLError):
        return True


def set_direct_costs(folder: Path, amount: str | None) -> dict:
    """Save the researcher's amount without changing the modality or the approved rules."""
    folder = Path(folder)
    if Project.load(folder).tipo != "convocatoria":
        raise LibraryError("Solo se pueden indicar costes directos en una convocatoria.")
    ficha = CallFicha.load(folder)
    if ficha.idioma is None or ficha.idioma.costes_directos is None:
        raise LibraryError("La ficha no contiene una regla de idioma vinculada al presupuesto.")
    costs = read_amount(amount) if amount is not None else None
    if _saved_costs(folder) != costs:
        _write_json(folder / COSTS, {"importe_eur": f"{costs:.2f}" if costs is not None else None})
    return _check_call_ficha(folder, ficha)[0]["idioma_por_presupuesto"]


def _modal_page_limit(limits: Limits, modality: str | None) -> ModalPageLimit | None:
    if modality is None:
        return None
    key = _modality_key(modality)
    return next((rule for rule in limits.paginas_por_modalidad
                 if _modality_key(rule.modalidad) == key), None)


def _modality_status(limits: Limits, modality: str | None) -> dict:
    options = [limit.modalidad for limit in limits.paginas_por_modalidad]
    selected = _modal_page_limit(limits, modality)
    return {
        "estado": "seleccionada" if selected is not None else "pendiente",
        "seleccion": selected.modalidad if selected is not None else None,
        "opciones": options,
        "limite": selected.model_dump() if selected is not None else None,
        "pregunta": None if selected is not None else
        f"¿Cuál es la modalidad de la propuesta? Opciones: {', '.join(options)}.",
    }


def set_call_modality(folder: Path, modality: str) -> dict:
    """Record the investigator's choice independently of rule approval."""
    folder = Path(folder)
    if Project.load(folder).tipo != "convocatoria":
        raise LibraryError("Solo se puede fijar la modalidad en un proyecto de convocatoria.")
    limits = CallFicha.load(folder).limites
    if not limits.paginas_por_modalidad:
        raise LibraryError("La ficha no contiene límites por modalidad.")
    status = _modality_status(limits, modality)
    selected = status["seleccion"]
    if selected is None:
        raise LibraryError(f"Modalidad no disponible. {status['pregunta']}")
    if _saved_modality(folder) != selected:
        _write_json(folder / PROPOSAL, {"modalidad": selected})
    return status


def ficha_text(folder: Path) -> str:
    """Render the call or journal ficha in Spanish, without a model."""
    kind = Project.load(folder).tipo
    ficha = CallFicha.load(folder) if kind == "convocatoria" else JournalFicha.load(folder)
    label = "Convocatoria" if kind == "convocatoria" else "Revista"
    name = ficha.convocatoria if kind == "convocatoria" else ficha.revista
    lines = [f"{label}: {name}"]
    if isinstance(ficha, CallFicha):
        lines.append(f"Plazo: {ficha.plazo or 'no consta'}")
        if ficha.limites.paginas_por_modalidad:
            lines.append("Límites de páginas por modalidad:")
            for limit in ficha.limites.paginas_por_modalidad:
                source = limit.fuente
                lines.append(
                    f"- {limit.modalidad}: {limit.paginas} páginas "
                    f"({source.fichero}, p. {source.pagina}). «{source.cita}»"
                )
        else:
            lines.append(f"Límite de páginas: {ficha.limites.paginas or 'no consta'}")
        for field in ficha.limites.campos:
            lines.append(f"- {field.nombre}: {field.caracteres} caracteres "
                         f"({field.apartado or 'a mano'}).")
        lines += [f"Idioma: {ficha.idioma.regla if ficha.idioma else 'no consta'}",
                  "", "Apartados:"]
        for number, section in enumerate(ficha.apartados, 1):
            requirement = ("obligatorio" if section.obligatorio else
                           f"condicional: {section.condicion or 'no indicada'}")
            lines.append(f"{number}. {section.titulo} ({requirement}). {section.pide}")
    lines += ["", "Criterios:"]
    for criterion in ficha.criterios:
        maximum = criterion.maximo if criterion.maximo is not None else "no consta"
        threshold = criterion.umbral if criterion.umbral is not None else "no consta"
        lines.append(f"- {criterion.nombre}: {criterion.descripcion} "
                     f"Máximo: {maximum}; umbral: {threshold}. "
                     f"Fuente: {criterion.fuente.fichero}, página {criterion.fuente.pagina}.")
    if not ficha.criterios:
        lines.append("No constan criterios de evaluación.")
    if isinstance(ficha, CallFicha):
        report, _ = _check_call_ficha(Path(folder), ficha)
        for rule in ficha.reglas_aplicables:
            conditions = ", ".join(f"{c.dato} {c.operador} {c.valor}" for c in rule.cuando)
            check = rule.comprobar.model_dump() if rule.comprobar else "revisión manual"
            lines.append(
                f"- {rule.requisito}. Aplica: {conditions or 'siempre'}. Comprobar: {check}."
            )
        if modality := report.get("modalidad"):
            lines.append(
                modality["pregunta"] or f"Modalidad de la propuesta: {modality['seleccion']}."
            )
        if budget := report.get("idioma_por_presupuesto"):
            lines.extend(_budget_report_lines(budget))
        if not report["confirmada"]:
            lines += ["", "Ficha por confirmar. Reglas por revisar:"]
            for rule in report["reglas"]:
                if rule["estado"] != "aprobada":
                    lines.append(
                        f"- {rule['donde']}, {rule['fichero']}, p. {rule['pagina']}. "
                        f"«{rule['cita']}»"
                    )
            if report["cambio_estructura"]:
                lines.append("Cambió el orden, se retiró una regla o cambiaron datos de la ficha.")
        for rule in report["reglas"]:
            if rule.get("valor") == "revision_manual":
                lines.append(f"- Cotejo manual de la regla: {rule['donde']}.")
    return "\n".join(lines)


def confirm_ficha(folder: Path, revision: str | None = None) -> dict:
    """Confirm checked sources while preserving the YAML layout and comments."""
    try:
        call = Project.load(folder).tipo == "convocatoria"
        path = Path(folder) / (FICHA if call else JOURNAL_FICHA)
        if not path.exists():
            return {"confirmada": False, "motivo": f"No hay ficha: falta {path.name}."}
        with path.open(encoding="utf-8", newline="") as stream:
            text = stream.read()
        snapshot = None
        if call:
            ficha = CallFicha.load(folder)
            report, snapshot = _check_call_ficha(Path(folder), ficha)
            if revision is not None and revision != report["revision"]:
                return {"confirmada": False, "motivo": _FICHA_CHANGED}
            set_flag = not ficha.confirmada
        else:
            report = check_journal_ficha(folder)
            set_flag = not report.get("confirmada")
        if report.get("error") or report.get("fallidos"):
            return {"confirmada": False, "motivo": report.get("error") or report["fallidos"]}
        if report["confirmada"]:
            return {"confirmada": True}
        if path.read_bytes() != text.encode("utf-8"):
            return {"confirmada": False, "motivo": _FICHA_CHANGED}
        updated = text
        if set_flag:
            updated, count = re.subn(
                r"^(confirmada:[ \t]*)false(?=[ \t]*(?:#|\r?$))", r"\g<1>true", text,
                flags=re.M,
            )
            if not count:
                if re.search(r"^confirmada[ \t]*:", text, re.M):
                    return {"confirmada": False,
                            "motivo": "Usa confirmada: false en una línea de primer nivel."}
                lines = text.splitlines(keepends=True)
                newline = "\r\n" if "\r\n" in text else "\n"
                lines[0] = lines[0].rstrip("\r\n") + newline
                lines.insert(1, "confirmada: true" + newline)
                updated = "".join(lines)
        if snapshot is not None:
            _write_json(Path(folder) / APPROVALS, snapshot)
        if updated != text:
            with path.open("w", encoding="utf-8", newline="") as stream:
                stream.write(updated)
        return {"confirmada": True}
    except (LibraryError, OSError) as error:
        return {"confirmada": False, "motivo": str(error)}


def _quoted_limit(quote: str, unit: str) -> int | None:
    """Extract a single explicitly stated maximum, leaving ambiguous quotes for review."""
    numbers = list(_NUMBER.finditer(quote))
    if len(numbers) != 1:
        return None
    number, = numbers
    suffix = re.match(rf"\s+(?:{unit})\b", quote[number.end():], re.I)
    if suffix is None or not _INTEGER.fullmatch(number[0]):
        return None
    before, after = quote[:number.start()], quote[number.end() + suffix.end():]
    if _MAXIMUM.search(before) or re.match(r"\s+(?:como\s+m[aá]ximo|max(?:imum)?)\b", after, re.I):
        return int(re.sub(r"[^0-9]", "", number[0]))
    return None


def _modality_pattern(label: str) -> str:
    words = [re.escape(word) + r"(?:es|s)?" for word in _modality_key(label).split()]
    return r"\b" + r"\s+".join(words) + r"\b"


def _quoted_modal_limit(quote: str, modality: str, options: list[ModalPageLimit]) -> int | None:
    """Read a maximum tied to the named modality when the wording makes the pair explicit."""
    quote = _normalize_pdf_spacing(quote)
    label = _modality_pattern(modality)
    values = set()
    for clause in re.split(r"(?<=[.!?])\s+|;\s*", quote):
        if cue := _PAGE_LIMIT_CUE.search(clause):
            pattern = (rf"(?<![\w.,-])([0-9]+)\s+(?:(?:{_PAGE_UNITS})\s+)?"
                       rf"para\s+(?:(?:los|las)\s+)?(?:proyectos?\s+)?{label}")
            values.update(int(number) for number in re.findall(pattern, clause[cue.end():]))
        mentioned = [option.modalidad for option in options
                     if re.search(_modality_pattern(option.modalidad), clause)]
        if mentioned == [modality]:
            if (limit := _quoted_limit(clause, _PAGE_UNITS)) is not None:
                values.add(limit)
    return next(iter(values)) if len(values) == 1 else None


def _normalize_pdf_spacing(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _budget_rule_value(rule: BudgetLanguage, source: Source, exact: bool) -> tuple[str, str | None]:
    amount, language = quoted_budget_language(source.cita) if exact else (None, None)
    if amount is not None and amount != rule.desde_eur:
        return "difiere", (
            f"La ficha indica un umbral de {rule.desde_eur:.2f} EUR. "
            f"La cita indica {amount:.2f} EUR."
        )
    if language is not None and language != rule.idioma.split("-", 1)[0]:
        return "difiere", (
            f"La ficha indica {language_name(rule.idioma)}. "
            f"La cita exige {language_name(language)}."
        )
    return ("coincide" if amount is not None and language is not None else "revision_manual"), None


def _check_call_ficha(folder: Path, ficha: CallFicha) -> tuple[dict, dict]:
    rules = list(_call_rules(ficha))
    evidence = {}
    report = check_sources(folder, "convocatoria",
                           ((rule.location, rule.source) for rule in rules),
                           False, evidence=evidence)
    saved = _read_approvals(folder) if ficha.confirmada else {}
    approved_keys = set(saved.get("reglas", []))
    current_keys = []
    summaries = []
    options = ficha.limites.paginas_por_modalidad
    budget_rule = ficha.idioma.costes_directos if ficha.idioma is not None else None
    for rule in rules:
        item = {"id": rule.id, "donde": rule.location, **rule.source.model_dump()}
        if rule.modality is not None:
            item["modalidad"] = rule.modality
        matched = evidence.get(rule.location)
        mismatch = None
        if rule.limit and matched is not None:
            declared, units, pattern = rule.limit
            quoted = None
            if matched[1] and rule.modality is not None:
                quoted = _quoted_modal_limit(rule.source.cita, rule.modality, options)
            elif matched[1]:
                quoted = _quoted_limit(rule.source.cita, pattern)
            item["valor"] = "revision_manual" if quoted is None else "coincide"
            if quoted is not None and quoted != declared:
                item["valor"] = "difiere"
                mismatch = (f"La ficha indica {declared} {units}. "
                            f"La cita indica un máximo de {quoted}.")
        if rule.id == "idioma" and budget_rule is not None and matched is not None:
            item["valor"], mismatch = _budget_rule_value(budget_rule, rule.source, matched[1])
        if rule.id.startswith("regla:") and matched is not None:
            item["valor"] = "revision_manual"
        if mismatch is not None:
            report["fallidos"].append({**item, "motivo": mismatch})
            report["comprobados"] -= 1
            matched = None
        if matched is not None:
            key = _fingerprint((rule.id, rule.source.model_dump(), rule.contents,
                                matched[0]))
            current_keys.append(key)
            item["estado"] = "aprobada" if key in approved_keys else "por_revisar"
        else:
            item["estado"] = "por_revisar"
        summaries.append(item)

    structure = _fingerprint((ficha.convocatoria, ficha.plazo, ficha.limites.palabras_por_pagina,
                              [rule.id for rule in rules]))
    snapshot = {"version": 1, "estructura": structure, "reglas": current_keys}
    report["reglas"] = summaries
    report["confirmada"] = not report["fallidos"] and saved == snapshot
    report["cambio_estructura"] = bool(saved and saved.get("estructura") != structure)
    ficha_data = ficha.model_dump(mode="json", exclude={"confirmada"})
    revision = (snapshot, ficha_data)
    if options:
        modality = report["modalidad"] = _modality_status(ficha.limites, _saved_modality(folder))
        revision += (modality["seleccion"],)
    else:
        # Keep the existing revision for calls with a single unconditional limit.
        del ficha_data["limites"]["paginas_por_modalidad"]
    if budget_rule is not None:
        budget = budget_language_status(
            budget_rule, _saved_costs(folder), Project.load(folder).idioma, report["confirmada"],
        )
        budget["fuente"] = ficha.idioma.fuente.model_dump()
        report["idioma_por_presupuesto"] = budget
        revision += (budget["importe_eur"], budget["idioma_declarado"])
    elif ficha_data["idioma"] is not None:
        del ficha_data["idioma"]["costes_directos"]
    if ficha.reglas_aplicables or ficha.datos_propuesta:
        values = _proposal_values(folder, ficha)
        language = Project.load(folder).idioma
        preview = evaluate_rules(
            folder, ficha.reglas_aplicables, ficha.datos_propuesta, values,
            {"idioma_proyecto": language or None}, approved=report["confirmada"],
        )
        report["reglas_aplicables"] = preview
        needed = {name for row in preview for name in row.get("datos_pendientes", [])}
        report["datos_propuesta"] = {
            name: {**field.model_dump(), "valor": values.get(name), "solicitar": name in needed}
            for name, field in ficha.datos_propuesta.items()
        }
        report["idioma_proyecto"] = language
        revision += (values, language)
    else:
        del ficha_data["datos_propuesta"], ficha_data["reglas_aplicables"]
    report["revision"] = _fingerprint(revision)
    return report, snapshot


def check_ficha(folder: Path, ficha: CallFicha | None = None) -> dict:
    """Validate a ficha and locate each requirement's quotation in its official PDF."""
    try:
        if ficha is None:
            ficha = CallFicha.load(folder)
        return _check_call_ficha(Path(folder), ficha)[0]
    except LibraryError as error:
        return {"error": str(error)}


def check_journal_ficha(folder: Path) -> dict:
    """Validate a journal ficha and locate its criteria's quotations in the PDFs."""
    try:
        ficha = JournalFicha.load(folder)
    except LibraryError as error:
        return {"error": str(error)}
    sources = ((f"criterios[{i}].fuente ({c.nombre})", c.fuente)
               for i, c in enumerate(ficha.criterios))
    return check_sources(folder, "revista", sources, ficha.confirmada)


def check_sources(
    folder: Path, subfolder: str, sources: Iterable[tuple[str, Source]], confirmada: bool,
    *, evidence: dict[str, tuple[str, bool]] | None = None,
) -> dict:
    """Locate each source's literal quotation inside its PDF folder."""
    from ai_writer.verificacion import verbatim

    root = (Path(folder) / subfolder).resolve()
    report = {
        "requisitos": 0, "comprobados": 0, "fallidos": [], "avisos": [],
        "confirmada": confirmada,
    }
    texts = {}
    for location, source in sources:
        report["requisitos"] += 1
        entry = {"donde": location, **source.model_dump()}
        path = (root / source.fichero).resolve()
        failure = None
        if not path.is_relative_to(root) or path.suffix.lower() != ".pdf" or not path.is_file():
            failure = f"El fichero debe existir dentro de {subfolder}/ y ser PDF."
        elif len(source.cita.split()) < 6:
            failure = "La cita debe tener al menos 6 palabras."
        else:
            if path not in texts:
                try:
                    with fitz.open(path) as doc:
                        if not doc.is_pdf:
                            raise ValueError("El fichero no es un PDF")
                        texts[path] = page_texts(doc)
                except (OSError, ValueError, RuntimeError) as error:
                    texts[path] = f"No se pudo leer el PDF: {error}"
            pages = texts[path]
            if isinstance(pages, str):
                failure = pages
            elif not verbatim(source.cita, "\n\n".join(pages), explain=False)[0]:
                failure = "La cita no aparece palabra por palabra en el PDF."
            else:
                report["comprobados"] += 1
                nearby = range(max(0, source.pagina - 2), min(len(pages), source.pagina + 1))
                near_text = "\n\n".join(pages[i] for i in nearby)
                in_nearby = verbatim(source.cita, near_text, explain=False)[0]
                if not in_nearby:
                    report["avisos"].append({
                        **entry,
                        "motivo": "La cita está en el PDF, pero no en la página indicada ±1.",
                    })
                if evidence is not None:
                    candidates = (sorted(nearby, key=lambda i: abs(i + 1 - source.pagina))
                                  if in_nearby else range(len(pages)))
                    found = next(
                        (i for i in candidates
                         if verbatim(source.cita, pages[i], explain=False)[0]),
                        None,
                    )
                    scope = nearby if in_nearby else range(len(pages))
                    if found is not None:
                        scope = [found]
                    page_context = [(i, _normalize_pdf_spacing(pages[i])) for i in scope]
                    strict_quote = _normalize_pdf_spacing(source.cita)
                    combined = " ".join(text for _, text in page_context)
                    exact = re.search(rf"(?<!\w){re.escape(strict_quote)}(?!\w)", combined)
                    evidence[location] = (_fingerprint(page_context), exact is not None)
        if failure:
            report["fallidos"].append({**entry, "motivo": failure})
    return report


def _normalize(title: str) -> str:
    title = "".join(
        c for c in unicodedata.normalize("NFD", title.lower())
        if not unicodedata.combining(c)
    )
    title = re.sub(r"^\s*\d+(?:\.\d+)*(?:[.)]\s*|\s+)", "", title)
    title = " ".join(title.split())
    while title and unicodedata.category(title[-1]).startswith("P"):
        title = title[:-1].rstrip()
    return title


def _draft_lines(text: str) -> list[str]:
    lines, fence, width = [], "", 0
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if (marker and marker[1][0] == fence and len(marker[1]) >= width
                    and not marker[2].strip()):
                fence = ""
        elif marker:
            fence, width = marker[1][0], len(marker[1])
        elif not line.startswith(("    ", "\t")):
            lines.append(line)
    return lines


def _section_body(lines: list[str], headings: list[dict], heading: dict) -> str:
    end = next((h["line"] for h in headings
                if h["line"] > heading["line"] and h["nivel"] <= heading["nivel"]), len(lines))
    return "\n".join(line for line in lines[heading["line"] + 1:end]
                     if not _HEADING.match(line)).strip()


def check_call(text: str, ficha: CallFicha | dict, *, modalidad: str | None = None) -> dict:
    """Compare headings, length, character limits and pending marks with a validated ficha."""
    if not isinstance(ficha, CallFicha):
        ficha = CallFicha.model_validate(ficha)
    lines = _COMMENT.sub("", "\n".join(_draft_lines(text))).splitlines()
    headings, words, pending = [], [], []
    section = ""
    for i, line in enumerate(lines):
        heading = _HEADING.match(line)
        if heading:
            level, section = len(heading[1]), heading[2]
            headings.append({"titulo": section, "nivel": level, "line": i})
            if level != 1:
                words.extend(section.split())
        else:
            words.extend(line.split())
        for match in re.finditer(r"\[PENDIENTE:\s*([^\]]+)\]", line):
            pending.append({"marca": match.group(), "seccion": section})

    expected = {_normalize(s.titulo): i for i, s in enumerate(ficha.apartados)}
    present = [h for h in headings if h["nivel"] in (2, 3)]
    by_title = {}
    for heading in present:
        by_title.setdefault(_normalize(heading["titulo"]), heading)
    titles = by_title.keys()
    missing = [s.titulo for s in ficha.apartados
               if s.obligatorio and _normalize(s.titulo) not in titles]
    empty = []
    for section in ficha.apartados:
        heading = by_title.get(_normalize(section.titulo))
        if section.obligatorio and heading is not None:
            content = _PENDING.sub("", _section_body(lines, headings, heading))
            if not content.strip():
                empty.append(section.titulo)
    conditional = [{"titulo": s.titulo, "condicion": s.condicion} for s in ficha.apartados
                   if not s.obligatorio and _normalize(s.titulo) not in titles]
    extra = [h["titulo"] for h in present if _normalize(h["titulo"]) not in expected]
    order, last = True, -1
    for heading in present:
        position = expected.get(_normalize(heading["titulo"]))
        if position is not None:
            if position <= last:
                order = [heading["titulo"]]
                break
            last = position

    count = len(words)
    limit = _modal_page_limit(ficha.limites, modalidad)
    maximum = limit.paginas if limit is not None else ficha.limites.paginas
    capacity = maximum * ficha.limites.palabras_por_pagina if maximum is not None else None
    state = ("sin_limite" if capacity is None else "excedido" if count > capacity
             else "aviso" if count >= capacity * 0.9 else "ok")
    if ficha.limites.paginas_por_modalidad and limit is None:
        state = "modalidad_pendiente"
    extension = {
        "palabras": count, "paginas_estimadas": round(count / ficha.limites.palabras_por_pagina, 1),
        "maximo": maximum, "estado": state,
    }
    if limit is not None:
        extension.update(modalidad=limit.modalidad, fuente=limit.fuente.model_dump())
    fields, manual = [], []
    for field in ficha.limites.campos:
        if field.apartado is None:
            manual.append({"nombre": field.nombre, "maximo": field.caracteres})
            continue
        heading = by_title.get(_normalize(field.apartado))
        characters = len(_section_body(lines, headings, heading)) if heading is not None else None
        fields.append({
            "nombre": field.nombre, "apartado": field.apartado,
            "caracteres": characters, "maximo": field.caracteres,
            "estado": ("ausente" if characters is None else
                       "excedido" if characters > field.caracteres else "ok"),
        })
    return {
        "faltan": missing, "vacios": empty, "condicionales_ausentes": conditional, "sobran": extra,
        "orden": order,
        "extension": extension,
        "campos": fields, "a_mano": manual, "pendientes": pending,
    }


def _final_pdf_file(folder: Path) -> tuple[Path | None, list[int] | str | None]:
    """Locate the final PDF within the project and identify its current file version."""
    root = folder.resolve()
    try:
        path = (root / FINAL_PDF).resolve()
        if not path.is_relative_to(root) or path.suffix.lower() != ".pdf":
            return None, "El PDF final debe estar dentro del proyecto y tener extensión .pdf."
        info = path.stat()
        if not S_ISREG(info.st_mode):
            return None, "La ruta del PDF final debe corresponder a un archivo."
    except FileNotFoundError:
        return None, None
    except (OSError, RuntimeError, ValueError):
        return None, "No se puede acceder al PDF final."
    return path, [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns]


def check_final_pdf(folder: Path, ficha: CallFicha, rules: dict, extension: dict) -> dict:
    """Count real PDF pages and compare them with the applicable confirmed maximum."""
    path, version = _final_pdf_file(Path(folder))
    report = {
        "archivo": FINAL_PDF.as_posix(), "paginas": None, "maximo": extension["maximo"],
        "version_archivo": version,
    }
    if source := extension.get("fuente"):
        report.update(modalidad=extension["modalidad"], fuente=source)
    elif ficha.limites.fuente is not None and extension["maximo"] is not None:
        report["fuente"] = ficha.limites.fuente.model_dump()
    if isinstance(version, str):
        return {**report, "estado": "error", "motivo": version}
    if path is None:
        return {**report, "estado": "pendiente"}

    try:
        with fitz.open(path) as pdf:
            if not pdf.is_pdf or pdf.needs_pass or not pdf.page_count:
                raise ValueError("PDF ilegible, vacío o protegido por contraseña")
            pages = pdf.page_count
    except (OSError, RuntimeError, ValueError):
        return {**report, "estado": "error", "motivo": "No se puede leer el PDF final."}
    if _final_pdf_file(Path(folder))[1] != version:
        return {**report, "estado": "desactualizado", "motivo": "El PDF cambió durante la lectura."}
    report["paginas"] = pages
    if not rules["confirmada"]:
        state = "ficha_pendiente"
    elif extension["estado"] == "modalidad_pendiente":
        state = "modalidad_pendiente"
    elif report["maximo"] is None:
        state = "sin_limite"
    else:
        state = "excedido" if pages > report["maximo"] else "ok"
    return {**report, "estado": state}


def final_pdf_is_stale(folder: Path, report: dict) -> bool:
    """Detect when the saved count belongs to a previous file or a missing one."""
    return report.get("estado") == "desactualizado" or (
        _final_pdf_file(Path(folder))[1] != report.get("version_archivo")
    )


def _budget_report_lines(budget: dict) -> list[str]:
    source = budget["fuente"]
    required = language_name(budget["idioma_requerido"])
    declared = language_name(budget["idioma_declarado"])
    lines = [
        "", "### Idioma según los costes directos", "",
        f"Desde {budget['desde_eur']} EUR, la memoria debe redactarse en {required}.",
        f"Fuente: {source['fichero']}, p. {source['pagina']}. «{source['cita']}»",
    ]
    if budget["importe_eur"] is not None:
        lines.append(f"Costes directos declarados: {budget['importe_eur']} EUR.")
    messages = {
        "ficha_pendiente": "Confirma la ficha para aplicar la condición.",
        "costes_pendientes": budget["pregunta"],
        "no_aplica": "El importe queda por debajo del umbral de esta regla.",
        "idioma_distinto": f"El proyecto indica {declared} y esta regla exige {required}.",
        "ok": f"El idioma declarado del proyecto coincide con el exigido ({required}).",
        "desactualizado": "Los costes directos o el idioma cambiaron. Vuelve a comprobarlos.",
    }
    lines.append(messages[budget["estado"]])
    return lines


def report_lines(ficha: dict, call: dict) -> list[str]:
    """The call section of the verification report, including manual checks."""
    lines = ["", "## Convocatoria", ""]
    if "error" in ficha:
        lines.append(ficha["error"])
    else:
        confirmed = "sí" if ficha["confirmada"] else "no; falta la confirmación del usuario"
        lines.append(
            f"Ficha: {ficha['comprobados']} de {ficha['requisitos']} requisitos comprobados; "
            f"{len(ficha['fallidos'])} fallidos. Confirmada: {confirmed}."
        )
        for name, label in (("fallidos", "Fallido"), ("avisos", "Aviso")):
            for entry in ficha[name]:
                lines.append(
                    f"- **{label}** en {entry['donde']} ({entry['fichero']}, "
                    f"p. {entry['pagina']}): {entry['motivo']} Cita: «{entry['cita']}»"
                )
        if ficha.get("cambio_estructura"):
            lines.append("Cambió el orden, se retiró una regla o cambiaron los datos de la ficha.")
        for rule in ficha.get("reglas", []):
            if rule["estado"] == "por_revisar":
                lines.append(
                    f"- Por aprobar: {rule['donde']} ({rule['fichero']}, p. {rule['pagina']})."
                )
            if rule.get("valor") == "revision_manual":
                lines.append(f"- Cotejo manual de la regla: {rule['donde']}.")
        if question := ficha.get("modalidad", {}).get("pregunta"):
            lines.append(question)
    if "aviso" in call:
        lines.append(call["aviso"])
    else:
        lines.append(
            "Apartados obligatorios que faltan: " + (", ".join(call["faltan"]) or "ninguno")
        )
        if call.get("vacios"):
            lines.append(
                "Apartados obligatorios pendientes de contenido: " + ", ".join(call["vacios"])
            )
        for entry in call["condicionales_ausentes"]:
            lines.append(
                f"- Condicional ausente: {entry['titulo']}. "
                f"Condición: {entry['condicion'] or 'no indicada'}."
            )
        if call["sobran"]:
            lines.append("Encabezados que sobran: " + ", ".join(call["sobran"]))
        lines.append("Orden: " + ("correcto." if call["orden"] is True else
                                  "primer apartado fuera de sitio: " + ", ".join(call["orden"])))
        length = call["extension"]
        maximum = length["maximo"] if length["maximo"] is not None else "sin límite"
        if length["estado"] == "modalidad_pendiente":
            maximum = "por determinar según la modalidad"
        if source := length.get("fuente"):
            lines.append(
                f"Modalidad: {length['modalidad']}. "
                f"Límite de {maximum} páginas ({source['fichero']}, p. {source['pagina']}). "
                f"«{source['cita']}»"
            )
        lines.append(
            f"Extensión: {length['palabras']} palabras; {length['paginas_estimadas']:.1f} "
            f"páginas estimadas; máximo: {maximum}. Estado: {length['estado']}."
        )
        lines.append("Campos con límite de caracteres:")
        for entry in call["campos"]:
            characters = (
                entry["caracteres"] if entry["caracteres"] is not None else "apartado ausente"
            )
            lines.append(
                f"- {entry['nombre']} ({entry['apartado']}): {characters} / "
                f"{entry['maximo']} caracteres; {entry['estado']}."
            )
        for entry in call["a_mano"]:
            lines.append(f"- A mano: {entry['nombre']}, máximo {entry['maximo']} caracteres.")
        if not call["campos"] and not call["a_mano"]:
            lines.append("No hay campos con límite de caracteres.")
        lines.append(f"Pendientes: {len(call['pendientes'])}.")
        for entry in call["pendientes"]:
            lines.append(f"- {entry['seccion'] or 'sin sección'}: {entry['marca']}")
    lines += ["", "La extensión del borrador se estima por palabras. "
              "El recuento real usa el PDF preparado con la plantilla oficial."]
    if final := call.get("pdf_final"):
        lines += ["", "### PDF final", "", f"Archivo: `{final['archivo']}`."]
        if final["paginas"] is not None:
            lines.append(f"Recuento: {final['paginas']} páginas reales.")
        if final["maximo"] is not None:
            lines.append(f"Máximo aplicable: {final['maximo']} páginas.")
        if (source := final.get("fuente")) and not final.get("modalidad"):
            lines.append(f"Fuente: {source['fichero']}, p. {source['pagina']}. «{source['cita']}»")
        messages = {
            "pendiente": "Guarda aquí el PDF de la memoria con la plantilla oficial.",
            "error": final.get("motivo", ""),
            "desactualizado": "El PDF cambió. Vuelve a ejecutar /theaiwriter:comprobar sin juez.",
            "ficha_pendiente": "Confirma la ficha para contrastar el recuento con el límite.",
            "modalidad_pendiente": "Elige la modalidad para determinar el límite.",
            "sin_limite": "La ficha carece de un máximo general de páginas.",
            "excedido": "El PDF final supera el máximo de páginas.",
            "ok": "El PDF final está dentro del límite de páginas.",
        }
        lines.append(messages[final["estado"]])
    if budget := ficha.get("idioma_por_presupuesto"):
        lines.extend(_budget_report_lines(budget))
    if applicable := call.get("reglas_aplicables"):
        lines += ["", "### Reglas de la convocatoria", ""]
        for rule in applicable:
            source = rule["fuente"]
            lines.append(
                f"- {rule['requisito']} ({rule['estado'].replace('_', ' ')}). "
                f"{source['fichero']}, p. {source['pagina']}. «{source['cita']}»"
            )
            if relative := rule.get("archivo"):
                lines.append(f"  Archivo esperado: `{relative}`.")
            if comparison := rule.get("comparacion"):
                operator = comparison["operador"].replace("_", " ")
                observed = rule["observado"] if rule["observado"] is not None else "pendiente"
                lines.append(
                    f"  Esperado: {comparison['dato']} {operator} {comparison['valor']}. "
                    f"Observado: {observed}."
                )
    return lines
