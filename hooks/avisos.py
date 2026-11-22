# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic>=2", "pyyaml>=6"]
# ///
"""Deliver pending document notices without blocking the user's prompt."""

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(PLUGIN_ROOT / "src"), str(PLUGIN_ROOT)]

from ai_writer.avisos import pop_notices  # noqa: E402


def main(event: dict) -> dict | None:
    """Return extra context when the working document has pending notices."""
    try:
        cwd = event.get("cwd")
        if not cwd:
            return None
        folder = Path(cwd)
        if not (folder / "proyecto.yaml").is_file():
            return None
        notices = pop_notices(folder)
        if notices:
            return {"hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "TheAIWriter: " + "\n".join(notices)
                + " Menciónalo al usuario al principio de tu respuesta.",
            }}
    except Exception:
        return None
    return None


if __name__ == "__main__":
    try:
        output = main(json.load(sys.stdin))
        if output:
            print(json.dumps(output, ensure_ascii=False))
    except Exception:
        pass
