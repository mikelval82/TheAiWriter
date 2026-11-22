"""Pending notices for the next user prompt, without models or embeddings."""

import json
from pathlib import Path

from ai_writer.background import now

NOTICES = "informes/avisos.json"


def add_notice(folder: Path, text: str) -> None:
    """Append a dated notice to the document's queue."""
    path = Path(folder) / NOTICES
    notices = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    notices.append({"texto": text, "fecha": now()})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notices, ensure_ascii=False, indent=1), encoding="utf-8")


def pop_notices(folder: Path) -> list[str]:
    """Return pending notices and empty the queue."""
    path = Path(folder) / NOTICES
    if not path.exists():
        return []
    notices = json.loads(path.read_text(encoding="utf-8"))
    texts = [notice["texto"] for notice in notices]
    path.write_text("[]\n", encoding="utf-8")
    return texts
