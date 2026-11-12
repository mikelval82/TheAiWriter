# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic>=2", "python-dotenv>=1", "pyyaml>=6"]
# ///
"""Hook PostToolUse: tras editar borrador/documento.md, comprueba sus citas contra la biblioteca.

Usa el código del paquete (ai_writer.validation) sin el entorno completo del plugin:
la validación no carga embeddings, así que le bastan estas tres dependencias.
"""

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(PLUGIN_ROOT / "src"), str(PLUGIN_ROOT)]

from ai_writer.library import PROJECT_FILE, LibraryError  # noqa: E402
from ai_writer.validation import check_text  # noqa: E402

event = json.load(sys.stdin)
path = Path(event.get("tool_input", {}).get("file_path", ""))
folder = path.parent.parent
if path.name != "documento.md" or path.parent.name != "borrador" or not path.exists():
    sys.exit(0)
if not (folder / PROJECT_FILE).exists():
    sys.exit(0)

try:
    report = check_text(path.read_text(encoding="utf-8"), folder)
except LibraryError as error:
    print(f"TheAIWriter no pudo validar las citas: {error}", file=sys.stderr)
    sys.exit(0)

if not report.ok:
    output = {
        "decision": "block",
        "reason": (
            "TheAIWriter: el borrador tiene citas que no se pueden aceptar.\n"
            + report.summary()
            + "\nCorrígelas: cita solo claves devueltas por buscar_evidencia, o marca el "
            "hueco con [@?] si falta la fuente."
        ),
    }
elif report.not_retrieved or report.pending:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "TheAIWriter: " + report.summary(),
        }
    }
else:
    sys.exit(0)
json.dump(output, sys.stdout, ensure_ascii=False)
