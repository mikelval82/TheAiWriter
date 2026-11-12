# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Hook de prueba: tras editar un borrador/documento.md, avisa de las citas sin clave."""

import json
import re
import sys
from pathlib import Path

entrada = json.load(sys.stdin)
ruta = Path(entrada.get("tool_input", {}).get("file_path", ""))
if ruta.name != "documento.md" or ruta.parent.name != "borrador" or not ruta.exists():
    sys.exit(0)

texto = ruta.read_text(encoding="utf-8")
citas = re.findall(r"\[@([^\]\s;?][^\]\s;]*)", texto)
pendientes = texto.count("[@?]")
json.dump(
    {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                f"TheAIWriter validó {ruta}: {len(citas)} citas, {pendientes} sin clave ([@?])."
            ),
        }
    },
    sys.stdout,
    ensure_ascii=False,
)
