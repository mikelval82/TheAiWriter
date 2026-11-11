"""Text generation through the OpenAI chat completions API."""

from ai_writer.llm.client import LLMError, LLMRequest, LLMResponse
from config.settings import settings


class OpenAIBackend:
    """Calls the OpenAI API with the key in ``OPENAI_API_KEY``."""

    def __init__(self) -> None:
        # Imported here so the default backend never needs an API key.
        from openai import OpenAI

        if not settings.ai.openai_api_key:
            raise LLMError("LLM_BACKEND=openai needs OPENAI_API_KEY to be set.")
        self.client = OpenAI(api_key=settings.ai.openai_api_key)

    def complete(self, request: LLMRequest) -> LLMResponse:
        import openai

        params = {
            "model": request.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
            "timeout": request.timeout,
        }
        # GPT-5 models use max_completion_tokens and don't support temperature
        if request.model.startswith("gpt-5"):
            params["max_completion_tokens"] = request.max_tokens
        else:
            params["max_tokens"] = request.max_tokens
            params["temperature"] = request.temperature
        if request.json_mode:
            params["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**params)
        except (
            openai.APIConnectionError,
            openai.RateLimitError,
            openai.InternalServerError,
        ) as error:
            raise LLMError(f"OpenAI API error: {error}", retryable=True) from error
        except openai.OpenAIError as error:
            raise LLMError(f"OpenAI API error: {error}") from error

        usage = response.usage
        return LLMResponse(
            text=response.choices[0].message.content or "",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
