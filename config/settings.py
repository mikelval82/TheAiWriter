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
    reasoning_model: str = Field(default_factory=lambda: os.getenv("REASONING_MODEL", "opus"))
    fast_model: str = Field(default_factory=lambda: os.getenv("FAST_MODEL", "haiku"))
    max_tokens: int = Field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "16384")))
    temperature: float = Field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0.0")))


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
