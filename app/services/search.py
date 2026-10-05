"""Search service for threads."""

from typing import List, Optional
from app.config import get_settings
from app.logging_config import get_logger
from app.storage.base import ThreadStorage


logger = get_logger()


class SearchService:
    """Search service for user threads."""

    def __init__(self, storage: ThreadStorage):
        self.storage = storage
        self.base_path = get_settings().thread_base_path

    async def search_threads(self, user_id: str, username: str, query: str) -> List[dict]:
        """Search threads for a user."""
        if not user_id or not username:
            return []
        path = f"{self.base_path}/{username}"
        try:
            result = await self.storage.search_files(path, query)
            if not result.success or not result.metadata:
                return []
            return result.metadata.get("matches", [])
        except Exception as e:
            logger.error(f"search_error - {str(e)}")
            return []

    async def search_by_thread_id(self, user_id: str, username: str, thread_id: str) -> Optional[dict]:
        """Search for a specific thread by ID."""
        if not user_id or not username or not thread_id:
            return None
        path = f"{self.base_path}/{username}"
        try:
            result = await self.storage.search_files(path, thread_id)
            if not result.success or not result.metadata:
                return None
            matches = result.metadata.get("matches", [])
            for match in matches:
                if match.get("filepath", "").endswith(f"/{thread_id}.md"):
                    return match
            return None
        except Exception as e:
            logger.error(f"search_by_id_error - {str(e)}")
            return None
