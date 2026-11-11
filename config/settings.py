"""Centralized configuration settings for TheAIWriter."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Base paths (define before load_dotenv to use in path)
BASE_DIR = Path(__file__).parent.parent

# Load environment variables from project root
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
REFERENCES_DIR = DATA_DIR / "references"
OUTPUT_DIR = DATA_DIR / "output"


# Default models per LLM backend: (default, reasoning, fast)
_DEFAULT_MODELS = {
    "claude-code": ("sonnet", "opus", "haiku"),
    "openai": ("gpt-5.2", "gpt-5.2", "gpt-5.2"),
}

# Default embedding model per embedding backend
_DEFAULT_EMBEDDING_MODELS = {
    "local": "intfloat/multilingual-e5-small",
    "openai": "text-embedding-3-small",
}


def _llm_backend() -> str:
    return os.getenv("LLM_BACKEND", "claude-code")


def _default_model(position: int) -> str:
    models = _DEFAULT_MODELS.get(_llm_backend(), _DEFAULT_MODELS["claude-code"])
    return models[position]


def _embedding_backend() -> str:
    return os.getenv("EMBEDDING_BACKEND", "local")


def _default_embedding_model() -> str:
    return _DEFAULT_EMBEDDING_MODELS.get(
        _embedding_backend(), _DEFAULT_EMBEDDING_MODELS["local"]
    )


class AISettings(BaseModel):
    """AI model configuration settings."""

    # Text generation: "claude-code" (the Claude Code CLI) or "openai"
    llm_backend: str = Field(default_factory=_llm_backend)
    claude_bin: str = Field(default_factory=lambda: os.getenv("CLAUDE_BIN", "claude"))
    llm_timeout: int = Field(default_factory=lambda: int(os.getenv("LLM_TIMEOUT", "600")))
    llm_max_retries: int = Field(default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "2")))

    # Embeddings: "local" (sentence-transformers) or "openai"
    embedding_backend: str = Field(default_factory=_embedding_backend)
    embedding_model: str = Field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", _default_embedding_model())
    )

    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    default_model: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_MODEL", _default_model(0))
    )
    reasoning_model: str = Field(
        default_factory=lambda: os.getenv("REASONING_MODEL", _default_model(1))
    )
    fast_model: str = Field(default_factory=lambda: os.getenv("FAST_MODEL", _default_model(2)))
    max_tokens: int = Field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "16384")))
    temperature: float = Field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0.0")))
    reasoning_effort: str = Field(default_factory=lambda: os.getenv("REASONING_EFFORT", "medium"))


class PathSettings(BaseModel):
    """Path configuration settings."""

    base_dir: Path = BASE_DIR
    data_dir: Path = DATA_DIR
    references_dir: Path = REFERENCES_DIR
    references_pdf_dir: Path = REFERENCES_DIR / "pdfs"
    references_markdown_dir: Path = REFERENCES_DIR / "markdown"
    output_dir: Path = OUTPUT_DIR
    drafts_dir: Path = OUTPUT_DIR / "drafts"
    final_dir: Path = OUTPUT_DIR / "final"
    processed_dir: Path = DATA_DIR / "processed"
    embeddings_dir: Path = DATA_DIR / "processed" / "embeddings"
    indices_dir: Path = DATA_DIR / "processed" / "indices"

    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        for field_name in self.model_fields:
            path = getattr(self, field_name)
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)


class Settings(BaseModel):
    """Main settings container."""

    ai: AISettings = Field(default_factory=AISettings)
    paths: PathSettings = Field(default_factory=PathSettings)


# Global settings instance
settings = Settings()
