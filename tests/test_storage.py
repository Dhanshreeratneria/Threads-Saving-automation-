"""Tests for storage backends."""

import pytest
import base64
from unittest.mock import AsyncMock, patch, MagicMock
from app.storage.base import ThreadStorage, StorageResult
from app.storage.github import GitHubStorage, GitHubNotFoundError


class TestStorageInterface:
    def test_storage_interface_abstract(self):
        with pytest.raises(TypeError):
            ThreadStorage()


@pytest.mark.asyncio
async def test_mock_github_create():
    with patch("app.storage.github.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            github_token="test-token", github_owner="test-owner", github_repository="test-repo"
        )
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"content": {"sha": "test-sha"}}
            mock_client = AsyncMock()
            mock_client.put = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client.is_closed = False
            mock_client_class.return_value = mock_client

            storage = GitHubStorage()
            result = await storage.create_file(filepath="users/test/test.md", content="test", commit_message="Test")
            assert result.success is True
            assert result.sha == "test-sha"
            payload = mock_client.put.await_args.kwargs["json"]
            assert payload["content"] == base64.b64encode(b"test").decode("ascii")
