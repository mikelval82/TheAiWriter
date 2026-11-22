# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic>=2", "pyyaml>=6"]
# ///
"""Block unknown or out-of-collection Zotero citations after a draft edit.

The hook imports only project configuration and Zotero metadata, without embeddings.
"""

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(PLUGIN_ROOT / "src"), str(PLUGIN_ROOT)]

from ai_writer.library import PROJECT_FILE, LibraryError, Project  # noqa: E402

event = json.load(sys.stdin)
path = Path(event.get("tool_input", {}).get("file_path", ""))
folder = path.parent.parent
if path.name != "documento.md" or path.parent.name != "borrador" or not path.exists():
    sys.exit(0)
if not (folder / PROJECT_FILE).exists():
    sys.exit(0)


def check_zotero(text: str, collections: list[str]) -> None:
    """Block unknown Zotero citations and works outside the document's collections."""
    from ai_writer.citations import find_citations
    from ai_writer.zotero import citable_keys

    every, allowed = citable_keys(collections)
    cited, malformed, _ = find_citations(text)
    cited = list(dict.fromkeys(cited))
    unknown = [key for key in cited if key not in every]
    outside = [key for key in cited if key in every and key not in allowed]
    if not (unknown or outside or malformed):
        return
    lines = ["TheAIWriter: el borrador tiene citas que no se pueden aceptar."]
    if unknown:
        lines.append("No existen en Zotero: " + ", ".join(unknown))
    if outside:
        lines.append("Fuera de las colecciones del documento: " + ", ".join(outside))
    if malformed:
        lines.append("Mal escritas: " + ", ".join(malformed))
    lines.append(
        "Corrígelas: cita solo claves devueltas por buscar_pasajes, o marca el hueco "
        "con [@?] si falta la fuente."
    )
    json.dump({"decision": "block", "reason": "\n".join(lines)}, sys.stdout, ensure_ascii=False)


try:
    project = Project.load(folder)
    check_zotero(path.read_text(encoding="utf-8"), project.colecciones)
except LibraryError as error:
    print(f"TheAIWriter no pudo validar las citas: {error}", file=sys.stderr)
    sys.exit(0)
