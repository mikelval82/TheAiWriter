"""Read saved analysis materials and resolve precise, project-relative sources."""

import csv
import json
from itertools import islice
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from ai_writer.library import LibraryError

TEXT = (".md", ".txt")
FIGURES = (".png", ".jpg", ".jpeg", ".svg", ".pdf", ".tif", ".tiff")
SCRIPTS = (".py", ".r", ".rmd", ".sh", ".m", ".jl", ".qmd")


class CeldaCSV(BaseModel, extra="forbid"):
    tipo: Literal["csv"]
    archivo: str
    fila: int = Field(gt=0, description="Registro de datos desde 1, sin contar la cabecera.")
    columna: str = Field(min_length=1)
    columna_grupo: str | None = Field(default=None, min_length=1)


class SalidaCuaderno(BaseModel, extra="forbid"):
    tipo: Literal["cuaderno"]
    archivo: str
    celda: int = Field(gt=0, description="Posición de la celda desde 1, contando todos los tipos.")
    salida: int = Field(gt=0, description="Posición de la salida guardada desde 1.")
    fragmento: str = Field(min_length=1, max_length=500)


class LineaTexto(BaseModel, extra="forbid"):
    tipo: Literal["texto"]
    archivo: str
    linea: int = Field(gt=0)
    fragmento: str = Field(min_length=1, max_length=500)


Fuente = Annotated[CeldaCSV | SalidaCuaderno | LineaTexto, Field(discriminator="tipo")]


def _source_path(folder: Path, name: str, roots: tuple[str, ...], suffixes: tuple[str, ...]) -> Path:
    relative = PurePosixPath(name)
    if (
        len(relative.parts) < 2
        or relative.parts[0] not in roots
        or "\\" in name
        or any(part == ".." or part.startswith(".") for part in relative.parts)
        or relative.suffix.lower() not in suffixes
    ):
        raise LibraryError(f"Ruta de evidencia no admitida en el proyecto: {name}")
    path = folder.joinpath(*relative.parts).resolve()
    if not path.is_relative_to(folder.resolve()) or not path.is_file():
        raise LibraryError(f"No encuentro el archivo de evidencia en el proyecto: {name}")
    return path


def _notebook(path: Path) -> list[dict]:
    try:
        cells = json.loads(path.read_text(encoding="utf-8-sig"))["cells"]
        if not isinstance(cells, list) or any(not isinstance(cell, dict) for cell in cells):
            raise ValueError
        return cells
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise LibraryError(f"No puedo leer las celdas de {path.name}.") from error


def _output_text(output: object) -> str:
    if not isinstance(output, dict):
        return ""
    if output.get("output_type") == "stream":
        value = output.get("text")
    elif output.get("output_type") in ("display_data", "execute_result"):
        data = output.get("data")
        value = (data.get("text/plain") or data.get("text/markdown")) if isinstance(data, dict) else None
    else:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(line, str) for line in value):
        return "".join(value)
    return ""


def _outputs(cell: dict) -> list:
    outputs = cell.get("outputs")
    return outputs if cell.get("cell_type") == "code" and isinstance(outputs, list) else []


def inventory(folder: Path) -> list[dict]:
    """List supported materials and notebooks with saved text output."""
    items = []
    project = folder.resolve()
    for root in ("materiales", "resultados", "analisis"):
        directory = folder / root
        if not directory.resolve().is_relative_to(project):
            continue
        for path in sorted(directory.rglob("*")):
            relative = path.relative_to(folder)
            if (
                not path.is_file()
                or not path.resolve().is_relative_to(project)
                or any(part.startswith(".") for part in relative.parts)
            ):
                continue
            suffix = path.suffix.lower()
            item = {"archivo": relative.as_posix()}
            if root == "resultados" and suffix == ".csv":
                item["tipo"] = "tabla"
            elif root == "resultados" and suffix in FIGURES:
                item["tipo"] = "figura"
            elif root == "analisis" and suffix == ".ipynb":
                item["tipo"] = "cuaderno"
                try:
                    cells = _notebook(path)
                    item["salidas_texto"] = sum(
                        bool(_output_text(out).strip()) for cell in cells for out in _outputs(cell)
                    )
                except LibraryError as error:
                    item["error"] = str(error)
            elif root == "analisis" and suffix in SCRIPTS:
                item["tipo"] = "script"
            elif suffix in TEXT:
                item["tipo"] = "salida de texto" if root == "resultados" else "nota"
            else:
                continue
            items.append(item)
    return items


def has_results(items: list[dict]) -> bool:
    return any(
        item["tipo"] in ("tabla", "salida de texto") or item.get("salidas_texto", 0)
        for item in items
    )


def _csv_source(folder: Path, source: CeldaCSV) -> dict:
    path = _source_path(folder, source.archivo, ("resultados",), (".csv",))
    with path.open(encoding="utf-8-sig", newline="") as stream:
        sample = stream.read(8192)
        stream.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        except csv.Error:
            dialect = csv.excel
        rows = (row for row in csv.reader(stream, dialect, strict=True) if row)
        headers = [header.strip() for header in next(rows, [])]
        row = next(islice(rows, source.fila - 1, None), None)
    if row is None or len(row) != len(headers):
        raise LibraryError(f"No hay un registro de datos válido en la fila {source.fila}.")
    columns = [source.columna]
    if source.columna_grupo is not None:
        columns.append(source.columna_grupo)
    for column in columns:
        if headers.count(column) != 1:
            raise LibraryError(f"La columna «{column}» falta o se repite en la cabecera.")
    if source.columna == source.columna_grupo:
        raise LibraryError("La columna del grupo debe ser distinta de la columna del valor.")
    value = row[headers.index(source.columna)].strip()
    if not value:
        raise LibraryError("La celda indicada está vacía.")
    result = {"valor": value}
    if source.columna_grupo is not None:
        group = row[headers.index(source.columna_grupo)].strip()
        if not group:
            raise LibraryError("La celda del grupo está vacía.")
        result["grupo"] = group
    return result


def _notebook_source(folder: Path, source: SalidaCuaderno) -> dict:
    path = _source_path(folder, source.archivo, ("analisis",), (".ipynb",))
    cells = _notebook(path)
    outputs = _outputs(cells[source.celda - 1]) if source.celda <= len(cells) else []
    if source.salida > len(outputs):
        raise LibraryError("La celda indicada carece de esa salida guardada.")
    output = _output_text(outputs[source.salida - 1])
    if source.fragmento not in output:
        raise LibraryError("El fragmento literal no aparece en la salida de texto indicada.")
    code = cells[source.celda - 1].get("source", "")
    if isinstance(code, list) and all(isinstance(line, str) for line in code):
        code = "".join(code)
    return {"fragmento": source.fragmento, "codigo": code}


def read_source(folder: Path, source: Fuente) -> dict:
    """Resolve selected evidence. Code is read as text and never executed."""
    try:
        if isinstance(source, CeldaCSV):
            return _csv_source(folder, source)
        if isinstance(source, SalidaCuaderno):
            return _notebook_source(folder, source)
        path = _source_path(folder, source.archivo, ("resultados",), TEXT)
        with path.open(encoding="utf-8-sig") as stream:
            line = next(islice(stream, source.linea - 1, None), "")
        if source.fragmento not in line:
            raise LibraryError("El fragmento literal no aparece en esa línea.")
        return {"fragmento": source.fragmento}
    except (OSError, UnicodeError, csv.Error, RuntimeError) as error:
        raise LibraryError(f"No puedo leer la evidencia de {source.archivo}: {error}") from error
