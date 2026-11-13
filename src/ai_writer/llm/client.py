"""Single entry point for text generation, independent of the provider."""

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError
from rich.console import Console

from config.settings import settings

console = Console()

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """A text generation call failed.

    Attributes:
        retryable: Whether trying the same call again can succeed.
    """

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class UsageLimitError(LLMError):
    """The account reached its usage limit: every call fails until it resets."""


@dataclass
class LLMRequest:
    """One generation call, as the backends receive it."""

    system: str
    user: str
    model: str
    max_tokens: int
    temperature: float
    json_mode: bool = False
    timeout: int = 600


@dataclass
class LLMResponse:
    """Text returned by a backend, with whatever usage it reports."""

    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class LLMBackend(Protocol):
    """A provider able to answer an LLMRequest."""

    def complete(self, request: LLMRequest) -> LLMResponse: ...


@dataclass
class LLMUsage:
    """Totals accumulated by an LLMClient."""

    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    calls_by_model: dict[str, int] = field(default_factory=dict)

    def add(self, model: str, response: LLMResponse) -> None:
        self.calls += 1
        self.input_tokens += response.input_tokens
        self.output_tokens += response.output_tokens
        self.cost_usd += response.cost_usd
        self.calls_by_model[model] = self.calls_by_model.get(model, 0) + 1


def extract_json(text: str) -> Any:
    """Parse the JSON value in a model response.

    Accepts bare JSON, JSON inside a markdown code fence, and JSON surrounded
    by prose.

    Raises:
        ValueError: If the text contains no parseable JSON.
    """
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    candidates = [text]
    if fenced:
        candidates.append(fenced.group(1))
    embedded = re.search(r"[\[{].*[}\]]", text, re.DOTALL)
    if embedded:
        candidates.append(embedded.group())

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"No JSON found in response: {text[:200]!r}")


class LLMClient:
    """Sends prompts to the configured backend, with retries and usage totals."""

    def __init__(
        self,
        backend: LLMBackend,
        max_retries: int | None = None,
        retry_delay: float = 2.0,
    ) -> None:
        """Initialize the client.

        Args:
            backend: Provider that answers the calls.
            max_retries: Extra attempts after a retryable failure. Defaults to settings.
            retry_delay: Seconds before the first retry; doubles on each attempt.
        """
        self.backend = backend
        self.max_retries = settings.ai.llm_max_retries if max_retries is None else max_retries
        self.retry_delay = retry_delay
        self.usage = LLMUsage()

    def complete(
        self,
        system: str,
        user: str,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        json_mode: bool = False,
        timeout: int | None = None,
    ) -> str:
        """Generate text for a system and user prompt.

        Args:
            system: The system prompt.
            user: The user prompt.
            model: Model to use. Defaults to the configured default model.
            max_tokens: Maximum tokens in the response, where the backend supports it.
            temperature: Sampling temperature, where the backend supports it.
            json_mode: Ask the backend for a JSON-only response.
            timeout: Seconds to wait for the response.

        Returns:
            The response text.

        Raises:
            LLMError: If the call fails and retrying does not help.
        """
        request = LLMRequest(
            system=system,
            user=user,
            model=model or settings.ai.default_model,
            max_tokens=max_tokens or settings.ai.max_tokens,
            temperature=settings.ai.temperature if temperature is None else temperature,
            json_mode=json_mode,
            timeout=timeout or settings.ai.llm_timeout,
        )

        attempt = 0
        while True:
            try:
                response = self.backend.complete(request)
            except LLMError as error:
                if not error.retryable or attempt >= self.max_retries:
                    raise
                delay = self.retry_delay * (2**attempt)
                attempt += 1
                console.print(
                    f"[yellow]⚠ LLM call failed ({error}); "
                    f"retry {attempt}/{self.max_retries} in {delay:.0f}s[/yellow]"
                )
                time.sleep(delay)
                continue
            self.usage.add(request.model, response)
            return response.text

    def complete_json(
        self,
        system: str,
        user: str,
        schema: type[T] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Generate a JSON response and parse it.

        Args:
            system: The system prompt.
            user: The user prompt.
            schema: Optional Pydantic model the response must validate against.
            **kwargs: Passed to :meth:`complete`.

        Returns:
            The parsed JSON, or an instance of ``schema`` when given.

        Raises:
            LLMError: If the call fails or the response is not valid for ``schema``.
        """
        text = self.complete(system, user, json_mode=True, **kwargs)
        try:
            data = extract_json(text)
            return schema.model_validate(data) if schema else data
        except (ValueError, ValidationError) as error:
            raise LLMError(f"Invalid JSON response: {error}") from error


def build_backend(name: str | None = None) -> LLMBackend:
    """Create the backend named in the settings.

    Raises:
        ValueError: If the backend name is unknown.
    """
    name = name or settings.ai.llm_backend
    if name == "claude-code":
        from ai_writer.llm.backends.claude_code import ClaudeCodeBackend

        return ClaudeCodeBackend()
    raise ValueError(
        f"Unknown LLM_BACKEND {name!r}; use 'claude-code' (OpenAI is no longer supported)"
    )


_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Return the client shared by every agent, creating it on first use."""
    global _client
    if _client is None:
        _client = LLMClient(build_backend())
    return _client


def set_llm_client(client: LLMClient | None) -> None:
    """Replace the shared client; ``None`` makes the next call rebuild it."""
    global _client
    _client = client
