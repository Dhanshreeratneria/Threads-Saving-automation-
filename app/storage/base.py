"""Abstract storage interface for thread files."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class StorageResult:
    """Result of a storage operation."""

    success: bool
    content: Optional[str] = None
    sha: Optional[str] = None
    filepath: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None


class ThreadStorage(ABC):
    """Abstract base class for thread storage backends."""

    @abstractmethod
    async def create_file(self, filepath: str, content: str, commit_message: str) -> StorageResult:
        """Create a new file."""
        pass

    @abstractmethod
    async def get_file(self, filepath: str) -> StorageResult:
        """Read a file."""
        pass

    @abstractmethod
    async def update_file(self, filepath: str, content: str, sha: str, commit_message: str) -> StorageResult:
        """Update an existing file."""
        pass

    @abstractmethod
    async def list_files(self, path: str) -> StorageResult:
        """List files in a directory."""
        pass

    @abstractmethod
    async def search_files(self, path: str, query: str) -> StorageResult:
        """Search files in a directory."""
        pass
