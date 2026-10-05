"""Thread manager - high-level thread operations."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.config import get_settings
from app.logging_config import get_logger
from app.models.message import Message
from app.models.thread import Thread
from app.storage.base import ThreadStorage
from app.markdown.generator import MarkdownGenerator
from app.threads.rotation import ThreadRotation


logger = get_logger()


class ThreadNotFound(Exception):
    """Thread not found."""
    pass


class InvalidUser(Exception):
    """Invalid user."""
    pass


class ThreadManager:
    """High-level thread manager."""

    def __init__(self, storage: ThreadStorage):
        self.storage = storage
        self.rotation = ThreadRotation()
        self.markdown_generator = MarkdownGenerator()
        self.settings = get_settings()

    async def create_thread(
        self,
        user_id: str,
        username: str,
        thread_name: str,
        thread_id: Optional[str] = None,
        previous_thread_id: Optional[str] = None,
        continuation: bool = False,
    ) -> Thread:
        """Create a new thread."""
        if not user_id or len(user_id) < 3:
            raise InvalidUser("Invalid user_id")
        if not username or len(username) < 3:
            raise InvalidUser("Invalid username")

        thread = Thread.create(
            user_id=user_id,
            username=username,
            thread_name=thread_name,
            thread_id=thread_id,
            previous_thread_id=previous_thread_id,
            continuation=continuation,
        )
        logger.info(f"thread_created - {thread.thread_id} for user {username}")
        return thread

    async def get_thread(self, user_id: str, username: str, thread_id: str) -> Thread:
        """Retrieve a thread."""
        filepath = f"{self.settings.thread_base_path}/{username}/{thread_id}.md"
        try:
            result = await self.storage.get_file(filepath)
            if not result.success or not result.content:
                raise ThreadNotFound(f"Thread {thread_id} not found for user {username}")
            # Simplified - in production, parse Markdown to reconstruct thread
            thread = Thread.create(user_id=user_id, username=username, thread_name="Retrieved Thread", thread_id=thread_id)
            return thread
        except Exception as e:
            if isinstance(e, ThreadNotFound):
                raise
            logger.error(f"thread_get_error - {str(e)}")
            raise ThreadNotFound(f"Failed to get thread: {str(e)}")

    async def update_thread(self, thread: Thread) -> str:
        """Update a thread file."""
        filepath = thread.get_filepath(self.settings.thread_base_path)
        content = self.markdown_generator.generate(thread)
        thread.file_size = len(content.encode("utf-8"))
        thread.token_count = self.markdown_generator.estimate_tokens(content)

        try:
            try:
                existing = await self.storage.get_file(filepath)
                result = await self.storage.update_file(
                    filepath=filepath, content=content, sha=existing.sha,
                    commit_message=f"Update thread: {thread.thread_name}",
                )
                logger.info(f"thread_updated - {thread.thread_id}")
            except Exception:
                result = await self.storage.create_file(
                    filepath=filepath, content=content,
                    commit_message=f"Create thread: {thread.thread_name}",
                )
                logger.info(f"thread_created - {thread.thread_id}")

            if not result.success:
                raise Exception(f"Storage operation failed: {result.error}")
            return result.sha or ""
        except Exception as e:
            logger.error(f"thread_update_error - {str(e)}")
            raise

    async def close_thread(self, thread: Thread) -> None:
        """Close a thread."""
        thread.status = "closed"
        thread.updated_at = datetime.now(timezone.utc)
        await self.update_thread(thread)
        logger.info(f"thread_closed - {thread.thread_id}")

    async def add_message(self, thread: Thread, message: Message) -> Tuple[Thread, bool]:
        """Add a message to a thread."""
        if not message.content or len(message.content.strip()) == 0:
            raise ValueError("Message content cannot be empty")

        # Check for duplicate message_id
        existing_ids = {m.message_id for m in thread.messages}
        if message.message_id in existing_ids:
            logger.warning(f"duplicate_message - {message.message_id} in {thread.thread_id}")
            return thread, False

        thread.add_message(message)
        content = self.markdown_generator.generate(thread)
        needs_rotation, reason = self.rotation.check_limits(thread, content)

        if needs_rotation:
            logger.info(f"thread_rotation_needed - {reason}")

        return thread, needs_rotation

    async def save_conversation(self, thread: Thread, user_prompt: str, assistant_response: str,
                                user_message_id: Optional[str] = None,
                                assistant_message_id: Optional[str] = None) -> Tuple[Thread, bool]:
        """Save a conversation turn (user prompt + assistant response)."""
        user_msg = Message.create(role="user", content=user_prompt, message_id=user_message_id)
        assistant_msg = Message.create(role="assistant", content=assistant_response, message_id=assistant_message_id)

        thread, _ = await self.add_message(thread, user_msg)
        thread, needs_rotation = await self.add_message(thread, assistant_msg)
        await self.update_thread(thread)

        return thread, needs_rotation

    async def rotate_thread(self, current_thread: Thread, thread_name: Optional[str] = None) -> Thread:
        """Rotate to a new thread."""
        await self.close_thread(current_thread)
        new_thread = await self.create_thread(
            user_id=current_thread.user_id,
            username=current_thread.username,
            thread_name=thread_name or f"{current_thread.thread_name} (continued)",
            previous_thread_id=current_thread.thread_id,
            continuation=True,
        )
        logger.info(f"thread_rotated - {current_thread.thread_id} -> {new_thread.thread_id}")
        return new_thread

    async def list_threads(self, username: str) -> List[str]:
        """List all threads for a user."""
        path = f"{self.settings.thread_base_path}/{username}"
        try:
            result = await self.storage.list_files(path)
            if not result.success or not result.metadata:
                return []
            return result.metadata.get("files", [])
        except Exception as e:
            logger.error(f"list_threads_error - {str(e)}")
            return []

    async def search_threads(self, username: str, query: str) -> List[dict]:
        """Search threads for a user."""
        path = f"{self.settings.thread_base_path}/{username}"
        try:
            result = await self.storage.search_files(path, query)
            if not result.success or not result.metadata:
                return []
            return result.metadata.get("matches", [])
        except Exception as e:
            logger.error(f"search_threads_error - {str(e)}")
            return []
