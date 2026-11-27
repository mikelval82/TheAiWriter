"""Persist human decisions on findings bound to the evidence reviewed."""

import json
import re
import sqlite3
from contextlib import closing, contextmanager
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from ai_writer.evidencia import CeldaCSV, Fuente, read_source
from ai_writer.library import LibraryError

REGISTRY = Path("informes") / "hallazgos.sqlite"
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class Hallazgo(BaseModel, extra="forbid"):
    enunciado: ShortText
    metrica: ShortText
    valor: ShortText
    grupo: ShortText | None = None
    unidad: ShortText | None = None
    fuente: Fuente


class Seleccion(BaseModel, extra="forbid"):
    id: int = Field(gt=0)
    version: str = Field(pattern=r"^[a-f0-9]{64}$")


class Propuesta(BaseModel, extra="forbid"):
    hallazgo: Hallazgo
    sustituye: Seleccion | None = None


def _signature(*parts: object) -> str:
    return sha256(json.dumps(parts, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _checked_source(folder: Path, finding: Hallazgo) -> tuple[dict, str]:
    evidence = read_source(folder, finding.fuente)
    if isinstance(finding.fuente, CeldaCSV):
        if finding.valor != evidence["valor"]:
            raise LibraryError(f"La celda indica «{evidence['valor']}» y la propuesta indica «{finding.valor}».")
        if finding.grupo != evidence.get("grupo"):
            raise LibraryError(
                f"El grupo de la fila es «{evidence.get('grupo') or 'sin columna de grupo'}». "
                "Indica el grupo tal como aparece en la columna correspondiente."
            )
        version = _signature(evidence)
    else:
        excerpt = evidence["fragmento"]
        value = re.escape(finding.valor)
        if not re.search(rf"(?<![\w+−-])(?<!\d[.,]){value}(?!\w|[.,]\d)", excerpt):
            raise LibraryError(f"El valor «{finding.valor}» no aparece en el fragmento literal.")
        if finding.grupo and not re.search(rf"(?<!\w){re.escape(finding.grupo)}(?!\w)", excerpt):
            raise LibraryError(f"El grupo «{finding.grupo}» no aparece en el fragmento literal.")
        version = _signature(evidence)
    return {key: value for key, value in evidence.items() if key != "codigo"}, version


@contextmanager
def _registry(folder: Path, *, write: bool = False):
    path = folder / REGISTRY
    if not path.resolve().is_relative_to(folder.resolve()):
        raise LibraryError("El registro de hallazgos debe estar dentro del proyecto.")
    if not write and not path.is_file():
        yield None
        return
    try:
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
        target = path.resolve().as_uri() + ("?mode=rwc" if write else "?mode=ro")
        with closing(sqlite3.connect(target, uri=True)) as db, db:
            db.row_factory = sqlite3.Row
            if write:
                db.execute(
                    "CREATE TABLE IF NOT EXISTS hallazgos (id INTEGER PRIMARY KEY, "
                    "propuesta TEXT NOT NULL, decision TEXT NOT NULL, evidencia_aprobada TEXT)"
                )
                db.execute("BEGIN IMMEDIATE")
            yield db
    except (OSError, sqlite3.Error) as error:
        raise LibraryError(f"No puedo acceder al registro de hallazgos: {error}") from error


def _entries(db: sqlite3.Connection | None) -> list[sqlite3.Row]:
    if db is None or db.execute(
        "SELECT 1 FROM sqlite_master WHERE name = 'hallazgos' AND type = 'table'"
    ).fetchone() is None:
        return []
    return list(db.execute("SELECT * FROM hallazgos ORDER BY id"))


def _view(folder: Path, row: sqlite3.Row) -> tuple[dict, str | None]:
    finding = Hallazgo.model_validate_json(row["propuesta"])
    error = None
    try:
        evidence, proof = _checked_source(folder, finding)
    except LibraryError as exc:
        evidence, proof, error = {}, None, str(exc)

    state = row["decision"]
    if state == "aprobado" and (proof is None or proof != row["evidencia_aprobada"]):
        state = "por_revisar"
    return {
        "id": row["id"], "estado": state, **finding.model_dump(),
        "evidencia": evidence, "aviso": error,
        "version": _signature(
            row["id"], row["propuesta"], row["decision"], row["evidencia_aprobada"], proof, error
        ),
    }, proof


def list_findings(folder: Path) -> list[dict]:
    with _registry(folder) as db:
        return [_view(folder, row)[0] for row in _entries(db)]


def _selected(folder: Path, db: sqlite3.Connection, selection: Seleccion) -> tuple[dict, str | None]:
    row = db.execute("SELECT * FROM hallazgos WHERE id = ?", (selection.id,)).fetchone()
    if row is None:
        raise LibraryError(f"No existe el hallazgo {selection.id}.")
    view, proof = _view(folder, row)
    if view["version"] != selection.version:
        raise LibraryError(f"El hallazgo {selection.id} o su fuente cambió. Vuelve a mostrarlo antes de decidir.")
    return view, proof


def _check_selection(ids: list[int]) -> None:
    if len(ids) != len(set(ids)):
        raise LibraryError("Cada hallazgo debe aparecer una sola vez en la selección.")


def save_findings(folder: Path, proposals: list[Propuesta]) -> list[dict]:
    """Add proposals or edit selected findings without granting approval."""
    if not proposals:
        return list_findings(folder)
    _check_selection([p.sustituye.id for p in proposals if p.sustituye])
    with _registry(folder, write=True) as db:
        for proposal in proposals:
            finding = proposal.hallazgo
            _checked_source(folder, finding)
            encoded = finding.model_dump_json()
            if proposal.sustituye:
                _selected(folder, db, proposal.sustituye)
                db.execute(
                    "UPDATE hallazgos SET propuesta = ?, decision = 'propuesto', evidencia_aprobada = NULL "
                    "WHERE id = ? AND propuesta != ?",
                    (encoded, proposal.sustituye.id, encoded),
                )
            elif db.execute("SELECT 1 FROM hallazgos WHERE propuesta = ?", (encoded,)).fetchone() is None:
                db.execute(
                    "INSERT INTO hallazgos (propuesta, decision) VALUES (?, 'propuesto')", (encoded,)
                )
        return [_view(folder, row)[0] for row in _entries(db)]


def decide_findings(
    folder: Path, choices: list[Seleccion], decision: Literal["aprobado", "pendiente"]
) -> list[dict]:
    """Apply a batch of decisions to the versions shown to the researcher."""
    if not choices:
        return list_findings(folder)
    _check_selection([choice.id for choice in choices])
    with _registry(folder, write=True) as db:
        for choice in choices:
            view, proof = _selected(folder, db, choice)
            if decision == "aprobado" and proof is None:
                raise LibraryError(f"Revisa la evidencia del hallazgo {choice.id}. {view['aviso']}")
            db.execute(
                "UPDATE hallazgos SET decision = ?, evidencia_aprobada = ? WHERE id = ?",
                (decision, proof if decision == "aprobado" else None, choice.id),
            )
        return [_view(folder, row)[0] for row in _entries(db)]
