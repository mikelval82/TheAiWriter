"""Processes that outlive the tool call that starts them (PDF processing, writing a document)."""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def spawn_cli(args: list[str], log_file: Path) -> int:
    """Run ``python -m ai_writer <args>`` detached, with its output in ``log_file``; return its pid."""
    options = {}
    if os.name == "nt":
        options["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "ai_writer", *args],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            env=os.environ | {"PYTHONIOENCODING": "utf-8"}, **options,
        )
    return process.pid


def process_alive(pid: int | None) -> bool:
    if not pid:
        return False
    if os.name == "nt":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
