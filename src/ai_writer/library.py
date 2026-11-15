"""Document configuration and the user's documents folder."""

import os
import re
import sys
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

PROJECT_FILE = "proyecto.yaml"
DocumentKind = Literal["perspectiva"]


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
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})

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
        for sub in ("materiales", "borrador", "revision", "exportacion"):
            (folder / sub).mkdir(parents=True, exist_ok=True)
        project.save(folder)
        return project
