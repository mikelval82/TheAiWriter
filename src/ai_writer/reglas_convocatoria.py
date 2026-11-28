"""Declarative requirements whose data and conditions come from the call sheet."""

import operator
import re
from decimal import Decimal
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Key = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")]
Value = str | int | float | bool
DataType = Literal["texto", "numero", "booleano"]
BUILTINS: dict[str, DataType] = {
    "idioma_proyecto": "texto",
    "paginas_pdf": "numero",
    "palabras_borrador": "numero",
}
_OPERATORS = {
    "igual": operator.eq,
    "distinto": operator.ne,
    "mayor": operator.gt,
    "mayor_o_igual": operator.ge,
    "menor": operator.lt,
    "menor_o_igual": operator.le,
}


class Source(BaseModel):
    fichero: str = Field(min_length=1)
    pagina: int = Field(ge=1)
    cita: str = Field(min_length=1)


class ProposalField(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: DataType
    pregunta: str = Field(min_length=1)
    opciones: list[str] = Field(default_factory=list)


class Comparison(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dato: Key
    operador: Literal["igual", "distinto", "mayor", "mayor_o_igual", "menor", "menor_o_igual"]
    valor: Value


class RequiredFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    archivo: str = Field(min_length=1)


class ApplicableRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Key
    requisito: str = Field(min_length=1)
    cuando: list[Comparison] = Field(default_factory=list)
    comprobar: Comparison | RequiredFile | None = None
    fuente: Source


def normalize_value(kind: DataType, value: Value) -> str | Decimal | bool:
    if kind == "texto" and isinstance(value, str) and value.strip():
        return value.strip().casefold()
    if kind == "booleano" and isinstance(value, bool):
        return value
    if kind == "numero" and re.fullmatch(r"-?[0-9]{1,20}(?:\.[0-9]{1,10})?", str(value)):
        return Decimal(str(value))
    raise ValueError(f"El valor de tipo {kind} no es válido.")


def proposal_value(field: ProposalField, value: Value) -> str | Decimal | bool:
    normalized = normalize_value(field.tipo, value)
    options = {option.strip().casefold() for option in field.opciones}
    if options and normalized not in options:
        raise ValueError(f"Elige una de estas opciones: {', '.join(field.opciones)}.")
    return normalized


def validate_rules(fields: dict[str, ProposalField], rules: list[ApplicableRule]) -> None:
    names = [rule.id for rule in rules]
    if len(set(names)) != len(names):
        raise ValueError("Cada regla debe tener un identificador distinto.")
    for name, field in fields.items():
        if name in BUILTINS:
            raise ValueError(f"{name} es un dato calculado por el programa.")
        if field.opciones:
            options = {option.strip().casefold() for option in field.opciones}
            if field.tipo != "texto" or "" in options or len(options) != len(field.opciones):
                raise ValueError(f"Las opciones de {name} deben ser textos distintos y no vacíos.")

    def validate(comparison: Comparison, types: dict[str, DataType]) -> None:
        kind = types.get(comparison.dato)
        if kind is None:
            raise ValueError(f"Dato desconocido en la regla: {comparison.dato}.")
        if kind != "numero" and comparison.operador not in ("igual", "distinto"):
            raise ValueError(f"{comparison.dato} solo admite igualdad o diferencia.")
        normalize_value(kind, comparison.valor)

    declared = {name: field.tipo for name, field in fields.items()}
    for rule in rules:
        for condition in rule.cuando:
            validate(condition, declared)
        check = rule.comprobar
        if isinstance(check, Comparison):
            validate(check, declared | BUILTINS)
        if isinstance(check, RequiredFile):
            path = PurePosixPath(check.archivo)
            if path.is_absolute() or len(path.parts) == 0 or ".." in path.parts or (
                PureWindowsPath(check.archivo).drive or "\\" in check.archivo
            ):
                raise ValueError("El archivo de una regla debe ser una ruta relativa del proyecto.")


def file_present(folder: Path, relative: str) -> bool:
    try:
        root = folder.resolve()
        resolved = (root / relative).resolve()
        return resolved.is_relative_to(root) and resolved.is_file()
    except (OSError, RuntimeError, ValueError):
        return False


def evaluate_rules(
    folder: Path, rules: list[ApplicableRule], fields: dict[str, ProposalField],
    values: dict, calculated: dict, *, approved: bool,
) -> list[dict]:
    types = {name: field.tipo for name, field in fields.items()} | BUILTINS
    actual = values | calculated

    def compare(check: Comparison) -> bool | None:
        value = actual.get(check.dato)
        if value is None:
            return None
        kind = types[check.dato]
        return _OPERATORS[check.operador](
            normalize_value(kind, value), normalize_value(kind, check.valor),
        )

    results = []
    for rule in rules:
        row = {"id": rule.id, "requisito": rule.requisito, "fuente": rule.fuente.model_dump(),
               "aplica": None}
        results.append(row)
        if not approved:
            row["estado"] = "ficha_pendiente"
            continue
        conditions = [(condition.dato, compare(condition)) for condition in rule.cuando]
        missing = list(dict.fromkeys(key for key, outcome in conditions if outcome is None))
        if any(outcome is False for _, outcome in conditions):
            row.update(estado="no_aplica", aplica=False)
            continue
        if missing:
            row.update(estado="datos_pendientes", datos_pendientes=missing)
            continue
        row["aplica"] = True
        check = rule.comprobar
        if isinstance(check, RequiredFile):
            present = file_present(folder, check.archivo)
            row.update(archivo=check.archivo, presente=present,
                       estado="cumple" if present else "no_cumple")
        elif isinstance(check, Comparison):
            outcome = compare(check)
            row.update(comparacion=check.model_dump(), observado=actual.get(check.dato))
            if outcome is None:
                row.update(estado="datos_pendientes", datos_pendientes=[check.dato])
            else:
                row["estado"] = "cumple" if outcome else "no_cumple"
        else:
            row["estado"] = "revision_manual"
    return results
