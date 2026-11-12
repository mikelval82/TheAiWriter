# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=2.3,<3"]
# ///
"""Servidor MCP de prueba de la Fase A: comprueba los supuestos del plugin."""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from mcp.server.mcpserver import MCPServer

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TAREAS = Path(tempfile.gettempdir()) / "theaiwriter-fase-a"

mcp = MCPServer("theaiwriter")


@mcp.tool()
def diagnostico() -> dict:
    """Informa de dónde corre el servidor: sistema, Python y carpeta del plugin."""
    return {
        "sistema": platform.platform(),
        "python": sys.version.split()[0],
        "plugin_root": str(PLUGIN_ROOT),
        "claude_en_path": shutil.which("claude"),
    }


@mcp.tool()
def probar_claude() -> dict:
    """Lanza `claude -p` con haiku y devuelve si responde con la cuenta del usuario."""
    claude = shutil.which("claude")
    if claude is None:
        return {"ok": False, "error": "claude no está en el PATH del servidor"}
    inicio = time.monotonic()
    completado = subprocess.run(
        [claude, "-p", "Responde solo: ok", "--model", "haiku", "--output-format", "json",
         "--tools", "", "--no-session-persistence"],
        capture_output=True, text=True, encoding="utf-8", timeout=120,
        stdin=subprocess.DEVNULL,
    )
    try:
        salida = json.loads(completado.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "codigo": completado.returncode, "stderr": completado.stderr[-500:]}
    return {
        "ok": not salida.get("is_error", True),
        "respuesta": salida.get("result"),
        "segundos": round(time.monotonic() - inicio, 1),
    }


@mcp.tool()
def lanzar_tarea(segundos: int = 60) -> dict:
    """Lanza en segundo plano una tarea que escribe su progreso cada segundo."""
    TAREAS.mkdir(parents=True, exist_ok=True)
    progreso = TAREAS / f"tarea-{int(time.time())}.log"
    codigo = (
        "import sys, time\n"
        "ruta, n = sys.argv[1], int(sys.argv[2])\n"
        "for i in range(1, n + 1):\n"
        "    time.sleep(1)\n"
        "    open(ruta, 'w').write(f'{i}/{n}')\n"
    )
    opciones = {}
    if os.name == "nt":
        opciones["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        opciones["start_new_session"] = True
    subprocess.Popen(
        [sys.executable, "-c", codigo, str(progreso), str(segundos)],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        **opciones,
    )
    return {"tarea": progreso.name}


@mcp.tool()
def estado_tarea(tarea: str) -> dict:
    """Devuelve el progreso de una tarea lanzada con lanzar_tarea."""
    progreso = TAREAS / tarea
    return {"tarea": tarea, "progreso": progreso.read_text() if progreso.exists() else "sin empezar"}


if __name__ == "__main__":
    mcp.run()
