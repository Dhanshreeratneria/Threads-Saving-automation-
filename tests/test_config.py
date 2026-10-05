"""Tests for application configuration."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_accept_github_names_with_hyphens():
    settings = Settings(
        _env_file=None,
        github_token="test-token-123456",
        github_owner="test-owner",
        github_repository="thread_saving.test",
    )

    assert settings.github_owner == "test-owner"
    assert settings.github_repository == "thread_saving.test"


def test_settings_reject_invalid_github_owner():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            github_token="test-token-123456",
            github_owner="not/an-owner",
            github_repository="threads",
        )
