"""Application configuration using pydantic-settings."""

from typing import Optional
from pathlib import Path
import re
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    github_token: str = Field(..., description="GitHub personal access token")
    github_owner: str = Field(..., description="GitHub username or organization")
    github_repository: str = Field(..., description="GitHub repository name")
    github_branch: str = Field(default="main", description="GitHub branch name")
    thread_base_path: str = Field(default="users", description="Base path for thread storage")
    max_messages: int = Field(default=100, description="Maximum messages per thread")
    max_tokens: int = Field(default=50000, description="Maximum tokens per thread")
    max_file_size_mb: int = Field(default=5, description="Maximum file size in MB")
    log_level: str = Field(default="INFO", description="Logging level")

    @field_validator("github_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v or len(v) < 10:
            raise ValueError("GitHub token must be a valid personal access token")
        return v

    @field_validator("github_owner", "github_repository")
    @classmethod
    def validate_alphanumeric(cls, v: str, info) -> str:
        pattern = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?" if info.field_name == "github_owner" else r"[A-Za-z0-9._-]+"
        if not v or not re.fullmatch(pattern, v) or v in {".", ".."}:
            raise ValueError(f"{info.field_name} contains unsupported characters")
        return v

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
