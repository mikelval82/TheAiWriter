"""Base agent class for AI interactions."""

from abc import ABC, abstractmethod

from ai_writer.llm import LLMClient, get_llm_client
from config.settings import settings


class BaseAgent(ABC):
    """Abstract base class for AI agents."""

    def __init__(self, model: str | None = None, llm: LLMClient | None = None) -> None:
        """Initialize the agent.

        Args:
            model: The model to use. Defaults to settings default.
            llm: Client used for generation. Defaults to the shared client.
        """
        self.llm = llm or get_llm_client()
        self.model = model or settings.ai.default_model

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
        return self.llm.complete(
            system_prompt,
            user_prompt,
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass
