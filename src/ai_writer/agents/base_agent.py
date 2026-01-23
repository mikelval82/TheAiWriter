"""Base agent class for AI interactions."""

from abc import ABC, abstractmethod

from openai import OpenAI

from config.settings import settings


# Models that require max_completion_tokens instead of max_tokens
GPT5_MODELS = ["gpt-5", "gpt-5.1", "gpt-5.2", "gpt-5-mini", "gpt-5-2025-08-07", "gpt-5-mini-2025-08-07"]


class BaseAgent(ABC):
    """Abstract base class for AI agents."""

    def __init__(self, model: str | None = None) -> None:
        """Initialize the agent with an AI client.

        Args:
            model: The model to use. Defaults to settings default.
        """
        self.client = OpenAI(api_key=settings.ai.openai_api_key)
        self.model = model or settings.ai.default_model

    def _is_gpt5_model(self) -> bool:
        """Check if the current model is a GPT-5 variant."""
        return any(gpt5 in self.model for gpt5 in GPT5_MODELS)

    def _call_api(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Make an API call to the AI model.

        Args:
            system_prompt: The system prompt defining agent behavior.
            user_prompt: The user's input/request.
            max_tokens: Maximum tokens in response.
            temperature: Creativity parameter (0-1).

        Returns:
            The model's response text.
        """
        tokens = max_tokens or settings.ai.max_tokens
        temp = temperature if temperature is not None else settings.ai.temperature

        # Build request parameters based on model type
        request_params = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        # GPT-5 models use max_completion_tokens and don't support temperature
        if self._is_gpt5_model():
            request_params["max_completion_tokens"] = tokens
        else:
            request_params["max_tokens"] = tokens
            request_params["temperature"] = temp

        response = self.client.chat.completions.create(**request_params)
        return response.choices[0].message.content or ""

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass
