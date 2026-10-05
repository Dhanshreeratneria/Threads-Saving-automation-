"""
Conversation capture interface - decoupled from specific AI platforms.
"""

from typing import Optional
from app.logging_config import get_logger
from app.models.thread import Thread
from app.threads.manager import ThreadManager


logger = get_logger()


class ConversationCapture:
    """Interface for capturing and saving conversations."""

    def __init__(self, thread_manager: ThreadManager):
        self.thread_manager = thread_manager

    async def capture_conversation(
        self, user_id: str, thread_id: str, user_prompt: str, assistant_response: str,
        username: Optional[str] = None, user_message_id: Optional[str] = None,
        assistant_message_id: Optional[str] = None,
    ) -> Thread:
        """Capture and save a conversation turn."""
        username = username or user_id
        thread = await self.thread_manager.get_thread(user_id=user_id, username=username, thread_id=thread_id)
        updated_thread, needs_rotation = await self.thread_manager.save_conversation(
            thread=thread, user_prompt=user_prompt, assistant_response=assistant_response,
            user_message_id=user_message_id, assistant_message_id=assistant_message_id,
        )

        if needs_rotation:
            new_thread = await self.thread_manager.rotate_thread(updated_thread)
            logger.info(f"conversation_rotated - {thread_id} -> {new_thread.thread_id}")
            return new_thread

        logger.info(f"conversation_saved - {thread_id} for user {user_id}")
        return updated_thread

    async def capture_and_create_thread(
        self, user_id: str, username: str, thread_name: str, user_prompt: str, assistant_response: str,
        user_message_id: Optional[str] = None, assistant_message_id: Optional[str] = None,
    ) -> Thread:
        """Create a new thread and save the first conversation."""
        thread = await self.thread_manager.create_thread(user_id=user_id, username=username, thread_name=thread_name)
        updated_thread, needs_rotation = await self.thread_manager.save_conversation(
            thread=thread, user_prompt=user_prompt, assistant_response=assistant_response,
            user_message_id=user_message_id, assistant_message_id=assistant_message_id,
        )
        logger.info(f"conversation_created - {thread.thread_id} for user {username}")
        return updated_thread
