"""GitHub storage backend implementation."""

import base64
from typing import Optional
import httpx

from app.config import get_settings
from app.logging_config import get_logger
from app.storage.base import ThreadStorage, StorageResult


logger = get_logger()


class GitHubError(Exception):
    """Base exception for GitHub errors."""
    pass


class GitHubAuthenticationError(GitHubError):
    """GitHub authentication failed."""
    pass


class GitHubNotFoundError(GitHubError):
    """Resource not found."""
    pass


class GitHubConflictError(GitHubError):
    """Conflict (e.g., SHA mismatch)."""
    pass


class StorageError(GitHubError):
    """General storage error."""
    pass


class GitHubStorage(ThreadStorage):
    """GitHub REST API storage backend."""

    def __init__(self, token: Optional[str] = None, owner: Optional[str] = None,
                 repo: Optional[str] = None, branch: Optional[str] = None):
        settings = get_settings()
        self.token = token or settings.github_token
        self.owner = owner or settings.github_owner
        self.repo = repo or settings.github_repository
        self.branch = branch or settings.github_branch
        self.base_url = "https://api.github.com"
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "thread-saving-mcp/0.1.0",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _validate_path(self, filepath: str) -> None:
        """Validate filepath to prevent path traversal."""
        if not filepath or ".." in filepath or filepath.startswith("/"):
            raise ValueError("Invalid filepath")

    async def create_file(self, filepath: str, content: str, commit_message: str) -> StorageResult:
        """Create a new file in GitHub."""
        self._validate_path(filepath)
        try:
            client = await self._get_client()
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{filepath}"
            encoded_content = base64.b64encode(content.encode("utf-8")).decode("ascii")
            data = {"message": commit_message, "content": encoded_content, "branch": self.branch}
            response = await client.put(url, json=data)

            if response.status_code == 401:
                raise GitHubAuthenticationError("GitHub authentication failed")
            elif response.status_code == 404:
                raise GitHubNotFoundError("Repository or branch not found")
            elif response.status_code == 422:
                raise GitHubConflictError(f"File already exists: {filepath}")
            elif response.status_code not in (200, 201):
                raise StorageError(f"Failed to create file: {response.status_code}")

            result_data = response.json()
            logger.info(f"github_create - Created file: {filepath}")
            return StorageResult(
                success=True,
                sha=result_data.get("content", {}).get("sha"),
                filepath=filepath,
            )
        except httpx.HTTPError as e:
            logger.error(f"github_error - HTTP error: {str(e)}")
            raise StorageError(f"HTTP error: {str(e)}")

    async def get_file(self, filepath: str) -> StorageResult:
        """Get a file from GitHub."""
        self._validate_path(filepath)
        try:
            client = await self._get_client()
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{filepath}"
            response = await client.get(url, params={"ref": self.branch})

            if response.status_code == 401:
                raise GitHubAuthenticationError("GitHub authentication failed")
            elif response.status_code == 404:
                raise GitHubNotFoundError(f"File not found: {filepath}")
            elif response.status_code != 200:
                raise StorageError(f"Failed to get file: {response.status_code}")

            result_data = response.json()
            content_bytes = base64.b64decode(result_data["content"])
            content = content_bytes.decode("utf-8")
            logger.info(f"github_get - Retrieved file: {filepath}")
            return StorageResult(success=True, content=content, sha=result_data.get("sha"), filepath=filepath)
        except httpx.HTTPError as e:
            logger.error(f"github_error - HTTP error: {str(e)}")
            raise StorageError(f"HTTP error: {str(e)}")

    async def update_file(self, filepath: str, content: str, sha: str, commit_message: str) -> StorageResult:
        """Update an existing file in GitHub."""
        self._validate_path(filepath)
        try:
            client = await self._get_client()
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{filepath}"
            encoded_content = base64.b64encode(content.encode("utf-8")).decode("ascii")
            data = {"message": commit_message, "content": encoded_content, "sha": sha, "branch": self.branch}
            response = await client.put(url, json=data)

            if response.status_code == 401:
                raise GitHubAuthenticationError("GitHub authentication failed")
            elif response.status_code == 404:
                raise GitHubNotFoundError(f"File not found: {filepath}")
            elif response.status_code == 409:
                raise GitHubConflictError("Conflict: file was modified by another process")
            elif response.status_code not in (200, 201):
                raise StorageError(f"Failed to update file: {response.status_code}")

            result_data = response.json()
            logger.info(f"github_update - Updated file: {filepath}")
            return StorageResult(success=True, sha=result_data.get("content", {}).get("sha"), filepath=filepath)
        except httpx.HTTPError as e:
            logger.error(f"github_error - HTTP error: {str(e)}")
            raise StorageError(f"HTTP error: {str(e)}")

    async def list_files(self, path: str) -> StorageResult:
        """List files in a directory."""
        self._validate_path(path)
        try:
            client = await self._get_client()
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{path}"
            response = await client.get(url, params={"ref": self.branch})

            if response.status_code == 401:
                raise GitHubAuthenticationError("GitHub authentication failed")
            elif response.status_code == 404:
                raise GitHubNotFoundError(f"Path not found: {path}")
            elif response.status_code != 200:
                raise StorageError(f"Failed to list files: {response.status_code}")

            result_data = response.json()
            files = [item["path"] for item in result_data if item.get("type") == "file" and item.get("name", "").endswith(".md")]
            logger.info(f"github_list - Listed {len(files)} files in {path}")
            return StorageResult(success=True, metadata={"files": files, "count": len(files)})
        except httpx.HTTPError as e:
            logger.error(f"github_error - HTTP error: {str(e)}")
            raise StorageError(f"HTTP error: {str(e)}")

    async def search_files(self, path: str, query: str) -> StorageResult:
        """Search files in a directory."""
        self._validate_path(path)
        try:
            list_result = await self.list_files(path)
            if not list_result.success or not list_result.metadata:
                return StorageResult(success=False, error="Failed to list files")

            files = list_result.metadata.get("files", [])
            matching_files = []
            client = await self._get_client()

            for filepath in files:
                try:
                    file_result = await self.get_file(filepath)
                    if file_result.success and file_result.content:
                        if query.lower() in file_result.content.lower():
                            idx = file_result.content.lower().find(query.lower())
                            start = max(0, idx - 50)
                            end = min(len(file_result.content), idx + len(query) + 50)
                            snippet = file_result.content[start:end]
                            matching_files.append({"filepath": filepath, "snippet": snippet, "sha": file_result.sha})
                except (GitHubNotFoundError, Exception):
                    continue

            logger.info(f"github_search - Found {len(matching_files)} matching files")
            return StorageResult(success=True, metadata={"matches": matching_files, "count": len(matching_files)})
        except Exception as e:
            logger.error(f"github_error - Search error: {str(e)}")
            return StorageResult(success=False, error=str(e))
