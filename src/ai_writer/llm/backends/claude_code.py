"""Text generation through the Claude Code CLI in print mode."""

import json
import os
import subprocess
import tempfile

from ai_writer.llm.client import LLMError, LLMRequest, LLMResponse, UsageLimitError
from config.settings import settings

JSON_ONLY_INSTRUCTION = (
    "\n\nRespond with a single valid JSON value and nothing else: "
    "no prose, no markdown code fences."
)


class ClaudeCodeBackend:
    """Runs ``claude -p`` once per call.

    The CLI uses the login of the installed Claude Code, so no API key is
    needed. Tools and MCP servers are disabled: the model only answers the
    prompt. ``max_tokens`` and ``temperature`` have no CLI equivalent and are
    ignored.
    """

    def __init__(self, executable: str | None = None) -> None:
        """Initialize the backend.

        Args:
            executable: Name or path of the CLI. Defaults to settings.
        """
        self.executable = executable or settings.ai.claude_bin

    def complete(self, request: LLMRequest) -> LLMResponse:
        system = request.system + (JSON_ONLY_INSTRUCTION if request.json_mode else "")

        # The CLI runs in an empty directory so that no project CLAUDE.md or
        # settings leak into the prompt. The system prompt goes through a file
        # and the user prompt through stdin: both can exceed argument limits.
        with tempfile.TemporaryDirectory(prefix="ai-writer-") as workdir:
            system_path = os.path.join(workdir, "system.txt")
            with open(system_path, "w", encoding="utf-8") as f:
                f.write(system)

            command = [
                self.executable,
                "-p",
                "--output-format",
                "json",
                "--model",
                request.model,
                "--system-prompt-file",
                system_path,
                "--tools",
                "",
                "--strict-mcp-config",
                "--no-session-persistence",
            ]
            try:
                completed = subprocess.run(
                    command,
                    input=request.user,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=request.timeout,
                    cwd=workdir,
                )
            except FileNotFoundError as error:
                raise LLMError(
                    f"Claude Code CLI not found ({self.executable!r}). Install it, set "
                    "CLAUDE_BIN to its path."
                ) from error
            except subprocess.TimeoutExpired as error:
                raise LLMError(
                    f"Claude Code CLI timed out after {request.timeout}s", retryable=True
                ) from error

        return self._parse(completed)

    def _parse(self, completed: subprocess.CompletedProcess) -> LLMResponse:
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            detail = (completed.stderr or completed.stdout).strip()[:500]
            raise LLMError(
                f"Claude Code CLI exited with code {completed.returncode}: {detail}",
                retryable=True,
            ) from error

        result = payload.get("result") or ""
        if payload.get("is_error"):
            if "not logged in" in result.lower():
                raise LLMError("Claude Code CLI is not logged in. Run `claude` and use /login.")
            if "hit your" in result.lower() and "limit" in result.lower():
                raise UsageLimitError(
                    f"Límite de uso de la cuenta de Claude alcanzado: {result[:300]}"
                )
            raise LLMError(f"Claude Code CLI error: {result[:500]}", retryable=True)

        usage = payload.get("usage") or {}
        return LLMResponse(
            text=result,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            cost_usd=payload.get("total_cost_usd") or 0.0,
        )
