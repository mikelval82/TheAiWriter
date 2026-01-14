"""Centralized configuration settings for TheAIWriter."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
REFERENCES_DIR = DATA_DIR / "references"
OUTPUT_DIR = DATA_DIR / "output"


class AISettings(BaseModel):
    """AI model configuration settings."""

    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    default_model: str = Field(default_factory=lambda: os.getenv("DEFAULT_MODEL", "gpt-5.1"))
    reasoning_model: str = Field(default_factory=lambda: os.getenv("REASONING_MODEL", "gpt-5-2025-08-07"))
    fast_model: str = Field(default_factory=lambda: os.getenv("FAST_MODEL", "gpt-5-mini-2025-08-07"))
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
