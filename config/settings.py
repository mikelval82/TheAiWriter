"""Centralized configuration settings for TheAIWriter."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Base paths (define before load_dotenv to use in path)
BASE_DIR = Path(__file__).parent.parent

# Load environment variables from project root
load_dotenv(BASE_DIR / ".env")


class AISettings(BaseModel):
    """AI model configuration settings."""

    # Text generation: "claude-code" (the Claude Code CLI) or "codex" (the Codex CLI)
    llm_backend: str = Field(default_factory=lambda: os.getenv("LLM_BACKEND", "claude-code"))
    claude_bin: str = Field(default_factory=lambda: os.getenv("CLAUDE_BIN", "claude"))
    codex_bin: str = Field(default_factory=lambda: os.getenv("CODEX_BIN", "codex"))
    codex_effort: str = Field(default_factory=lambda: os.getenv("CODEX_EFFORT", "low"))
    llm_timeout: int = Field(default_factory=lambda: int(os.getenv("LLM_TIMEOUT", "600")))
    llm_max_retries: int = Field(default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "2")))

    # Embeddings: "local" (fastembed, on this machine) is the only backend
    embedding_backend: str = Field(default_factory=lambda: os.getenv("EMBEDDING_BACKEND", "local"))
    embedding_model: str = Field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
    )
    # Persistent: fastembed's own default is a temporary folder
    embedding_cache_dir: Path = Field(
        default_factory=lambda: Path(
            os.getenv("EMBEDDING_CACHE_DIR", Path.home() / ".cache" / "theaiwriter" / "modelos")
        )
    )

    default_model: str = Field(default_factory=lambda: os.getenv("DEFAULT_MODEL", "sonnet"))
    max_tokens: int = Field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "16384")))
    temperature: float = Field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0.0")))


class Settings(BaseModel):
    """Main settings container."""

    ai: AISettings = Field(default_factory=AISettings)


# Global settings instance
settings = Settings()
