"""Text generation through the Codex CLI in non-interactive mode."""

import os
import subprocess
import tempfile

from ai_writer.llm.backends.claude_code import JSON_ONLY_INSTRUCTION
from ai_writer.llm.client import LLMError, LLMRequest, LLMResponse, UsageLimitError
from config.settings import settings

_LIMIT_MARKS = ("usage limit", "rate limit", "quota")


class CodexBackend:
    """Runs ``codex exec`` once per call, with the login of the installed Codex CLI.

    The agent runs in an empty directory with a read-only sandbox, so it can only
    answer the prompt. Codex has no separate system prompt: it goes first in the
    prompt. ``max_tokens`` and ``temperature`` have no CLI equivalent and are ignored.
    """

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or settings.ai.codex_bin

    def complete(self, request: LLMRequest) -> LLMResponse:
        system = request.system + (JSON_ONLY_INSTRUCTION if request.json_mode else "")
        with tempfile.TemporaryDirectory(prefix="ai-writer-") as workdir:
            answer = os.path.join(workdir, "answer.txt")
            command = [
                self.executable, "exec",
                "--skip-git-repo-check", "--ephemeral",
                "--sandbox", "read-only",
                "--model", request.model,
                "-c", f'model_reasoning_effort="{settings.ai.codex_effort}"',
                "--output-last-message", answer,
                "-",
            ]
            try:
                completed = subprocess.run(
                    command, input=f"{system}\n\n{request.user}", capture_output=True, text=True,
                    encoding="utf-8", timeout=request.timeout, cwd=workdir,
                )
            except FileNotFoundError as error:
                raise LLMError(
                    f"Codex CLI not found ({self.executable!r}). Install it or set CODEX_BIN to its path."
                ) from error
            except subprocess.TimeoutExpired as error:
                raise LLMError(f"Codex CLI timed out after {request.timeout}s", retryable=True) from error
            text = ""
            if os.path.exists(answer):
                with open(answer, encoding="utf-8") as f:
                    text = f.read().strip()

        if completed.returncode != 0 or not text:
            detail = (completed.stderr or completed.stdout).strip()[-500:]
            if any(mark in detail.lower() for mark in _LIMIT_MARKS):
                raise UsageLimitError(f"Límite de uso de la cuenta de Codex alcanzado: {detail[-300:]}")
            raise LLMError(f"Codex CLI exited with code {completed.returncode}: {detail}", retryable=True)
        return LLMResponse(text=text)
