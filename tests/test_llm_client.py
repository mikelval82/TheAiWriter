"""Tests for the LLM client and its Claude Code backend.

Run from the repository root with ``python -m pytest`` so that ``config`` is importable.
The CLI is never executed: ``subprocess.run`` is replaced.
"""

import json
import subprocess

import pytest
from pydantic import BaseModel

from ai_writer.llm import LLMClient, LLMError, LLMRequest, LLMResponse
from ai_writer.llm.backends import claude_code
from ai_writer.llm.backends.claude_code import ClaudeCodeBackend
from ai_writer.llm.client import build_backend, extract_json


def _request(**overrides) -> LLMRequest:
    values = {
        "system": "SYSTEM",
        "user": "USER",
        "model": "sonnet",
        "max_tokens": 100,
        "temperature": 0.0,
    }
    return LLMRequest(**{**values, **overrides})


class FakeCLI:
    """Replacement for ``subprocess.run`` that records how the CLI was called."""

    def __init__(self, stdout="", returncode=0, stderr="", error=None) -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr
        self.error = error
        self.command: list[str] = []
        self.kwargs: dict = {}
        self.system_prompt = ""

    def __call__(self, command, **kwargs):
        self.command = command
        self.kwargs = kwargs
        if self.error:
            raise self.error
        system_path = command[command.index("--system-prompt-file") + 1]
        with open(system_path, encoding="utf-8") as f:
            self.system_prompt = f.read()
        return subprocess.CompletedProcess(command, self.returncode, self.stdout, self.stderr)


@pytest.fixture
def cli(monkeypatch):
    def install(**kwargs) -> FakeCLI:
        fake = FakeCLI(**kwargs)
        monkeypatch.setattr(claude_code.subprocess, "run", fake)
        return fake

    return install


def _result(text, **extra) -> str:
    return json.dumps({"result": text, "is_error": False, **extra})


# ---------------------------------------------------------------- Claude Code backend


def test_claude_backend_returns_result_and_usage(cli):
    cli(
        stdout=_result(
            "hola",
            total_cost_usd=0.01,
            usage={"input_tokens": 7, "output_tokens": 3},
        )
    )

    response = ClaudeCodeBackend("claude").complete(_request())

    assert response == LLMResponse(text="hola", input_tokens=7, output_tokens=3, cost_usd=0.01)


def test_claude_backend_passes_prompts_without_tools(cli):
    fake = cli(stdout=_result("ok"))

    ClaudeCodeBackend("claude").complete(_request(model="haiku", timeout=42))

    command = fake.command
    assert command[:2] == ["claude", "-p"]
    assert command[command.index("--model") + 1] == "haiku"
    assert command[command.index("--tools") + 1] == ""
    assert "--strict-mcp-config" in command
    assert fake.system_prompt == "SYSTEM"
    assert fake.kwargs["input"] == "USER"
    assert fake.kwargs["timeout"] == 42


def test_claude_backend_json_mode_asks_for_json_only(cli):
    fake = cli(stdout=_result("{}"))

    ClaudeCodeBackend("claude").complete(_request(json_mode=True))

    assert fake.system_prompt.startswith("SYSTEM")
    assert "JSON" in fake.system_prompt


def test_claude_backend_not_installed_is_a_clear_error(cli):
    cli(error=FileNotFoundError())

    with pytest.raises(LLMError, match="not found") as raised:
        ClaudeCodeBackend("claude").complete(_request())

    assert not raised.value.retryable


def test_claude_backend_not_logged_in_is_not_retried(cli):
    cli(stdout=json.dumps({"result": "Not logged in · Please run /login", "is_error": True}))

    with pytest.raises(LLMError, match="not logged in") as raised:
        ClaudeCodeBackend("claude").complete(_request())

    assert not raised.value.retryable


@pytest.mark.parametrize(
    "kwargs",
    [
        {"error": subprocess.TimeoutExpired("claude", 5)},
        {"stdout": "", "returncode": 1, "stderr": "boom"},
        {"stdout": json.dumps({"result": "overloaded", "is_error": True})},
    ],
    ids=["timeout", "crash", "api-error"],
)
def test_claude_backend_transient_failures_are_retryable(cli, kwargs):
    cli(**kwargs)

    with pytest.raises(LLMError) as raised:
        ClaudeCodeBackend("claude").complete(_request())

    assert raised.value.retryable


# ---------------------------------------------------------------- LLMClient


class ScriptedBackend:
    """Backend that plays a list of responses or errors in order."""

    def __init__(self, *outcomes) -> None:
        self.outcomes = list(outcomes)
        self.requests: list[LLMRequest] = []

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return LLMResponse(text=outcome, input_tokens=2, output_tokens=1, cost_usd=0.5)


def test_client_retries_retryable_errors():
    backend = ScriptedBackend(LLMError("busy", retryable=True), "ok")
    client = LLMClient(backend, max_retries=2, retry_delay=0)

    assert client.complete("s", "u") == "ok"
    assert len(backend.requests) == 2


def test_client_gives_up_after_max_retries():
    backend = ScriptedBackend(*[LLMError("busy", retryable=True)] * 3)
    client = LLMClient(backend, max_retries=2, retry_delay=0)

    with pytest.raises(LLMError, match="busy"):
        client.complete("s", "u")
    assert len(backend.requests) == 3


def test_client_does_not_retry_permanent_errors():
    backend = ScriptedBackend(LLMError("not logged in"), "never reached")
    client = LLMClient(backend, max_retries=2, retry_delay=0)

    with pytest.raises(LLMError, match="not logged in"):
        client.complete("s", "u")
    assert len(backend.requests) == 1


def test_client_accumulates_usage():
    client = LLMClient(ScriptedBackend("a", "b"), max_retries=0)

    client.complete("s", "u", model="haiku")
    client.complete("s", "u", model="sonnet")

    assert client.usage.calls == 2
    assert client.usage.input_tokens == 4
    assert client.usage.cost_usd == 1.0
    assert client.usage.calls_by_model == {"haiku": 1, "sonnet": 1}


class Capital(BaseModel):
    capital: str


def test_complete_json_validates_against_schema():
    client = LLMClient(ScriptedBackend('```json\n{"capital": "París"}\n```'), max_retries=0)

    assert client.complete_json("s", "u", schema=Capital) == Capital(capital="París")


@pytest.mark.parametrize("text", ["no json here", '{"city": "París"}'], ids=["no-json", "wrong-shape"])
def test_complete_json_rejects_invalid_responses(text):
    client = LLMClient(ScriptedBackend(text), max_retries=0)

    with pytest.raises(LLMError, match="Invalid JSON"):
        client.complete_json("s", "u", schema=Capital)


@pytest.mark.parametrize(
    "text",
    ['{"a": 1}', '```json\n{"a": 1}\n```', 'Aquí está:\n{"a": 1}\nFin.'],
    ids=["bare", "fenced", "embedded"],
)
def test_extract_json_accepts_common_shapes(text):
    assert extract_json(text) == {"a": 1}


def test_unknown_backend_is_rejected():
    with pytest.raises(ValueError, match="LLM_BACKEND"):
        build_backend("gemini")
