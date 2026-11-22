"""Document configuration and the user's documents folder."""

import os
import re
import sys
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

PROJECT_FILE = "proyecto.yaml"
DocumentKind = Literal["perspectiva", "resultados", "convocatoria"]

ABSTRACT_QUESTIONS = {
    "perspectiva": [
        "¿Qué quieres defender (tu tesis, en una frase)?", "¿Por qué importa ahora?",
        "¿Qué argumentos la sostienen?", "¿Qué objeción esperas?",
    ],
    "resultados": [
        "¿Qué pregunta responde el trabajo?", "¿Qué datos y métodos usaste?",
        "¿Cuál es el resultado principal?", "¿Qué aporta respecto a lo publicado?",
    ],
    "convocatoria": [
        "¿Qué problema aborda el proyecto?", "¿Cuál es la hipótesis?",
        "¿Qué objetivos tiene?", "¿Qué se espera conseguir?",
    ],
}


def is_template(path: Path) -> bool:
    """Whether a file contains only headings, HTML comments and whitespace."""
    path = Path(path)
    if not path.exists():
        return True
    text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
    text = re.sub(r"^ {0,3}\S[^\n]*\n {0,3}(?:=+|-+)[ \t]*$", "", text, flags=re.M)
    text = re.sub(r"^ {0,3}#{1,6}(?:[ \t]+.*)?$", "", text, flags=re.M)
    return not text.strip()


def migrate_reports(folder: Path) -> bool:
    """Move an old report folder without merging existing folders."""
    folder = Path(folder)
    old, new = folder / "revision", folder / "informes"
    if not old.is_dir() or new.exists():
        return False
    old.rename(new)
    for suffix in ("json", "md", "log"):
        source = new / f"verificacion.{suffix}"
        if source.exists():
            source.rename(new / f"comprobacion.{suffix}")
    return True


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


class LibraryError(Exception):
    """A library or project request that cannot be satisfied; the message is for the user."""


class Project(BaseModel):
    """Document kind, title, language and Zotero collections in ``proyecto.yaml``.

    Unknown fields from older project files are ignored by Pydantic.
    """

    tipo: DocumentKind
    titulo: str
    idioma: str = "es"
    colecciones: list[str] = Field(default_factory=list, description="Vacío: todo Zotero")

    @classmethod
    def load(cls, folder: Path) -> "Project":
        path = Path(folder) / PROJECT_FILE
        if not path.exists():
            raise LibraryError(f"{folder} no es un documento de TheAIWriter: falta {PROJECT_FILE}.")
        project = cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
        if migrate_reports(folder):
            from ai_writer.avisos import add_notice

            add_notice(folder, "La carpeta revision/ se ha renombrado a informes/ y "
                       "verificacion.md a comprobacion.md.")
        return project

    def save(self, folder: Path) -> None:
        data = self.model_dump(mode="json", exclude_none=True)
        (Path(folder) / PROJECT_FILE).write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

    @classmethod
    def create(cls, folder: Path, **fields) -> "Project":
        """Create a document folder; its collections must exist in Zotero.

        Raises:
            LibraryError: If the folder already holds a project or a collection is unknown.
        """
        folder = Path(folder)
        if (folder / PROJECT_FILE).exists():
            raise LibraryError(f"{folder} ya tiene un {PROJECT_FILE}.")
        project = cls(**fields)
        from ai_writer.zotero import Zotero

        Zotero().item_keys(project.colecciones)
        for sub in ("materiales", "borrador", "informes", "exportacion"):
            (folder / sub).mkdir(parents=True, exist_ok=True)
        abstract = folder / "materiales" / "abstract.md"
        if not abstract.exists():
            abstract.write_text(
                "# Abstract\n\n" + "".join(
                    f"<!-- {q} -->\n\n\n" for q in ABSTRACT_QUESTIONS[project.tipo]
                ),
                encoding="utf-8",
            )
        if project.tipo == "resultados":
            for sub in ("resultados", "analisis"):
                (folder / sub).mkdir(parents=True, exist_ok=True)
        if project.tipo == "convocatoria":
            (folder / "convocatoria").mkdir(parents=True, exist_ok=True)
            team = folder / "materiales" / "equipo.md"
            if not team.exists():
                team.write_text(
                    "# Datos del equipo\n\n"
                    "<!-- Solo se usará lo que esté escrito aquí. Completa los datos que conozcas; "
                    "lo que falte se marcará como pendiente en el borrador. -->\n\n"
                    "## Personas del equipo y su papel\n\n"
                    "<!-- ¿Quiénes participan? Indica nombre, papel y dedicación "
                    "de cada persona. -->\n\n\n"
                    "## Resultados previos\n\n"
                    "<!-- ¿Qué publicaciones, proyectos y datos propios aporta el equipo? -->\n\n\n"
                    "## Recursos disponibles\n\n"
                    "<!-- ¿Qué instalaciones, equipos y otros recursos están disponibles? -->\n\n\n"
                    "## Presupuesto previsto\n\n"
                    "<!-- ¿Qué presupuesto se necesita por partidas? -->\n\n\n"
                    "## Duración y cronograma previstos\n\n"
                    "<!-- ¿Cuánto durará el proyecto? "
                    "¿Qué tareas e hitos incluye el calendario? -->\n\n\n",
                    encoding="utf-8",
                )
        project.save(folder)
        return project
