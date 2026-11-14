"""The student's library of papers and the documents written from it.

A library is a visible folder shared by every document::

    biblioteca/
        pdfs/                 original PDFs
        procesado/            what PDF processing extracts: papers/<id>/, indices/*.jsonl,
                              processing_status.json
        vectores/             embedding indices, tagged with their model
        colecciones.yaml      named groups of papers
        referencias.bib       bibliography with stable keys (phase C)

A document is the folder where the student opens Claude; ``proyecto.yaml``
names its kind, language and the collections it draws evidence from.
"""

import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from ai_writer.background import now, process_alive, spawn_cli
from config.settings import settings

LIBRARY_ENV = "THEAIWRITER_BIBLIOTECA"
PROJECT_FILE = "proyecto.yaml"


def documents_dir() -> Path:
    """The user's documents folder, localized on Linux (``~/Documentos``)."""
    home = Path.home()
    if sys.platform.startswith("linux"):
        config_home = Path(os.getenv("XDG_CONFIG_HOME", home / ".config"))
        user_dirs = config_home / "user-dirs.dirs"
        if user_dirs.exists():
            match = re.search(
                r'^XDG_DOCUMENTS_DIR="([^"]+)"', user_dirs.read_text(encoding="utf-8"), re.M
            )
            if match:
                return Path(match.group(1).replace("$HOME", str(home)))
    return home / "Documents"


def default_library_dir() -> Path:
    """``THEAIWRITER_BIBLIOTECA`` if set, else ``<documents>/TheAIWriter/biblioteca``."""
    configured = os.getenv(LIBRARY_ENV)
    if configured:
        return Path(configured).expanduser()
    return documents_dir() / "TheAIWriter" / "biblioteca"


class LibraryError(Exception):
    """A library or project request that cannot be satisfied; the message is for the user."""


@dataclass(frozen=True)
class PaperEntry:
    """One processed paper, read from its ``procesado/papers/<id>/`` folder."""

    id: str
    title: str
    file: str
    authors: tuple[str, ...]
    year: int | None
    ideas: int
    claims: int
    references: int


class Library:
    """A library folder: its layout, its papers and its collections."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root else default_library_dir()
        self.pdfs_dir = self.root / "pdfs"
        self.processed_dir = self.root / "procesado"
        self.indices_dir = self.processed_dir / "indices"
        self.embeddings_dir = self.root / "vectores"
        self.collections_file = self.root / "colecciones.yaml"
        self.bib_file = self.root / "referencias.bib"

    def exists(self) -> bool:
        return self.processed_dir.is_dir()

    def create(self) -> "Library":
        """Create the folders; existing content is kept."""
        for path in (self.pdfs_dir, self.indices_dir, self.embeddings_dir):
            path.mkdir(parents=True, exist_ok=True)
        if not self.collections_file.exists():
            self._save_collections({})
        return self

    def activate(self) -> None:
        """Point the pipeline's configured paths at this library."""
        settings.paths.references_pdf_dir = self.pdfs_dir
        settings.paths.processed_dir = self.processed_dir
        settings.paths.indices_dir = self.indices_dir
        settings.paths.embeddings_dir = self.embeddings_dir

    # Papers

    def papers(self) -> list[PaperEntry]:
        """Processed papers, sorted by title.

        Read from each paper's folder rather than ``processing_status.json``, which
        can miss papers (two PDFs with the same file name share one entry).
        """
        papers_dir = self.processed_dir / "papers"
        if not papers_dir.is_dir():
            return []
        papers = []
        for folder in papers_dir.iterdir():
            metadata_file = folder / "metadata.json"
            if not metadata_file.is_file():
                continue
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            papers.append(
                PaperEntry(
                    id=metadata.get("paper_id", folder.name),
                    title=metadata.get("title") or folder.name,
                    file=Path(metadata.get("source_file", "")).name,
                    authors=tuple(metadata.get("authors") or ()),
                    year=metadata.get("year"),
                    ideas=count_usable_items(folder / "ideas.jsonl"),
                    claims=count_usable_items(folder / "claims.jsonl"),
                    references=_count_lines(folder / "references.jsonl"),
                )
            )
        return sorted(papers, key=lambda paper: paper.title.lower())

    def find_papers(self, queries: list[str]) -> list[PaperEntry]:
        """Resolve each query to exactly one paper by id, file name or title fragment.

        Raises:
            LibraryError: If a query matches no paper or more than one.
        """
        papers = self.papers()
        found = []
        for query in queries:
            needle = query.strip().lower()
            matches = [p for p in papers if needle == p.id]
            if not matches:
                matches = [
                    p for p in papers if needle in p.title.lower() or needle in p.file.lower()
                ]
            if not matches:
                raise LibraryError(f"Ningún paper de la biblioteca coincide con «{query}».")
            # Copies of one work (same title) count as one match
            if len({" ".join(p.title.lower().split()) for p in matches}) > 1:
                titles = "; ".join(p.title for p in matches[:5])
                raise LibraryError(f"«{query}» coincide con varios papers: {titles}.")
            found.extend(p for p in matches if p not in found)
        return found

    # PDFs and their processing

    @property
    def job_file(self) -> Path:
        return self.processed_dir / "proceso.json"

    @property
    def log_file(self) -> Path:
        return self.processed_dir / "registro.log"

    def pending_pdfs(self) -> list[Path]:
        """PDFs in ``pdfs/`` not yet processed successfully (same rule as BatchProcessor)."""
        status_file = self.processed_dir / "processing_status.json"
        processed = {}
        if status_file.exists():
            processed = json.loads(status_file.read_text(encoding="utf-8")).get("processed", {})
        return sorted(
            pdf for pdf in self.pdfs_dir.glob("*.pdf")
            if not processed.get(pdf.name, {}).get("success")
        )

    def add_pdfs(self, paths: list[Path]) -> list[Path]:
        """Copy PDFs, or every PDF in the given folders, into ``pdfs/``.

        Raises:
            LibraryError: If a path does not exist or is not a PDF.
        """
        sources = []
        for path in map(Path, paths):
            path = path.expanduser()
            if path.is_dir():
                sources.extend(sorted(path.glob("*.pdf")))
            elif path.is_file() and path.suffix.lower() == ".pdf":
                sources.append(path)
            else:
                raise LibraryError(f"«{path}» no es un PDF ni una carpeta con PDFs.")
        self.create()
        added = []
        for source in sources:
            target = self.pdfs_dir / source.name
            if target.exists():
                continue
            shutil.copy2(source, target)
            added.append(target)
        return added

    def job(self) -> dict | None:
        """The last background processing run: estado, inicio, fin, pid."""
        if not self.job_file.exists():
            return None
        job = json.loads(self.job_file.read_text(encoding="utf-8"))
        if job.get("estado") == "en_curso" and not process_alive(job.get("pid")):
            job["estado"] = "interrumpido"
        return job

    def write_job(self, **fields) -> None:
        job = (self.job() or {}) | fields
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.job_file.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")

    def start_processing(self) -> dict:
        """Process the pending PDFs in a separate process that outlives the caller.

        Raises:
            LibraryError: If a run is already in progress or nothing is pending.
        """
        job = self.job()
        if job and job.get("estado") == "en_curso":
            raise LibraryError("Ya hay un procesado en curso.")
        pending = self.pending_pdfs()
        if not pending:
            raise LibraryError("No hay PDFs pendientes de procesar.")

        pid = spawn_cli(["--biblioteca", str(self.root), "biblioteca", "procesar"], self.log_file)
        self.write_job(estado="en_curso", pid=pid, pendientes=len(pending), inicio=now(), fin=None)
        return self.job()

    # Collections

    def collections(self) -> dict[str, list[str]]:
        """Collection name → paper ids."""
        if not self.collections_file.exists():
            return {}
        data = yaml.safe_load(self.collections_file.read_text(encoding="utf-8")) or {}
        return {
            name: [paper["id"] for paper in (entry or {}).get("papers", [])]
            for name, entry in data.items()
        }

    def save_collection(self, name: str, papers: list[PaperEntry]) -> None:
        """Create or replace a collection."""
        name = name.strip()
        if not name:
            raise LibraryError("La colección necesita un nombre.")
        data = self._load_collections_raw()
        data[name] = {"papers": [{"id": p.id, "titulo": p.title} for p in papers]}
        self._save_collections(data)

    def delete_collection(self, name: str) -> None:
        data = self._load_collections_raw()
        if name not in data:
            raise LibraryError(f"No existe la colección «{name}».")
        del data[name]
        self._save_collections(data)

    def paper_ids(self, collections: list[str] | None = None) -> set[str]:
        """Ids of the papers in these collections; every paper when none are named.

        Raises:
            LibraryError: If a collection does not exist.
        """
        if not collections:
            return {paper.id for paper in self.papers()}
        known = self.collections()
        missing = [name for name in collections if name not in known]
        if missing:
            raise LibraryError(
                f"No existen las colecciones: {', '.join(missing)}. "
                f"Disponibles: {', '.join(known) or 'ninguna'}."
            )
        return {paper_id for name in collections for paper_id in known[name]}

    def _load_collections_raw(self) -> dict:
        if not self.collections_file.exists():
            return {}
        return yaml.safe_load(self.collections_file.read_text(encoding="utf-8")) or {}

    def _save_collections(self, data: dict) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        header = "# Colecciones de papers. Cada documento elige cuáles usa en proyecto.yaml.\n"
        body = yaml.safe_dump(data, allow_unicode=True, sort_keys=True) if data else ""
        self.collections_file.write_text(header + body, encoding="utf-8")

    # Migration

    def migrate_from(self, processed_dir: Path, pdfs_dir: Path | None = None) -> dict[str, int]:
        """Copy an existing ``data/processed`` (and its PDFs) into this library.

        Nothing is reprocessed or re-embedded: papers, indices and vectors are copied
        as they are. Vectors of earlier models (``previous_*``) are left behind.

        Raises:
            LibraryError: If the library already has papers, or the source has none.
        """
        processed_dir = Path(processed_dir)
        if not (processed_dir / "papers").is_dir():
            raise LibraryError(f"{processed_dir} no contiene papers procesados.")
        if self.papers():
            raise LibraryError(f"La biblioteca {self.root} ya tiene papers; no se sobrescribe.")
        self.create()

        shutil.copytree(processed_dir / "papers", self.processed_dir / "papers", dirs_exist_ok=True)
        status_file = processed_dir / "processing_status.json"
        if status_file.exists():
            shutil.copy2(status_file, self.processed_dir)
        for jsonl in (processed_dir / "indices").glob("*.jsonl"):
            shutil.copy2(jsonl, self.indices_dir)
        vectors = 0
        for path in (processed_dir / "embeddings").glob("*_*.*"):
            if path.is_file():
                shutil.copy2(path, self.embeddings_dir)
                vectors += 1
        pdfs = 0
        if pdfs_dir and Path(pdfs_dir).is_dir():
            for pdf in Path(pdfs_dir).glob("*.pdf"):
                shutil.copy2(pdf, self.pdfs_dir)
                pdfs += 1
        return {"papers": len(self.papers()), "vector_files": vectors, "pdfs": pdfs}


def count_usable_items(path: Path) -> int:
    """Items of a paper's ideas or claims file that reach the indices.

    Items whose quote was not found in the paper (``quote_verified`` false) are kept in
    the file for auditing but do not count; items without the field are counted.
    """
    if not path.is_file():
        return 0
    with open(path, encoding="utf-8") as f:
        return sum(
            1 for line in f if line.strip() and json.loads(line).get("quote_verified") is not False
        )


def _count_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    with open(path, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


DocumentKind = Literal["perspectiva", "resultados", "convocatoria"]


class Project(BaseModel):
    """``proyecto.yaml``: what a document folder writes and from which evidence."""

    tipo: DocumentKind
    titulo: str
    idioma: str = "es"
    perfil: str | None = Field(
        default=None, description="Estructura de secciones; vacío: la del tipo de documento"
    )
    colecciones: list[str] = Field(
        default_factory=list, description="Vacío: toda la biblioteca"
    )
    biblioteca: Path | None = Field(
        default=None, description="Vacío: la biblioteca por defecto"
    )
    materiales: dict[str, str] = Field(
        default_factory=dict, description="Nombre → ruta relativa dentro de materiales/"
    )
    plantilla_docx: str | None = None

    @classmethod
    def load(cls, folder: Path) -> "Project":
        path = Path(folder) / PROJECT_FILE
        if not path.exists():
            raise LibraryError(f"{folder} no es un documento de TheAIWriter: falta {PROJECT_FILE}.")
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})

    def save(self, folder: Path) -> None:
        data = self.model_dump(mode="json", exclude_none=True)
        (Path(folder) / PROJECT_FILE).write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

    @classmethod
    def create(cls, folder: Path, **fields) -> "Project":
        """Create a document folder; its collections must exist in its library.

        Raises:
            LibraryError: If the folder already holds a project or a collection is unknown.
        """
        folder = Path(folder)
        if (folder / PROJECT_FILE).exists():
            raise LibraryError(f"{folder} ya tiene un {PROJECT_FILE}.")
        project = cls(**fields)
        project.paper_ids()
        for sub in ("materiales", "borrador", "revision", "exportacion"):
            (folder / sub).mkdir(parents=True, exist_ok=True)
        project.save(folder)
        return project

    def library(self) -> Library:
        return Library(self.biblioteca)

    def paper_ids(self) -> set[str]:
        """Papers this document may draw evidence from."""
        return self.library().paper_ids(self.colecciones)
