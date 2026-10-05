"""Thread rotation logic based on limits."""

from typing import Tuple
from app.config import get_settings
from app.logging_config import get_logger
from app.models.thread import Thread


logger = get_logger()


class ThreadRotation:
    """Handle thread rotation based on configured limits."""

    def __init__(self):
        self.settings = get_settings()

    def check_limits(self, thread: Thread, new_content: str) -> Tuple[bool, str]:
        """Check if thread has reached any limit."""
        if thread.message_count >= self.settings.max_messages:
            return True, f"Message limit reached ({thread.message_count}/{self.settings.max_messages})"

        if thread.token_count >= self.settings.max_tokens:
            return True, f"Token limit reached ({thread.token_count}/{self.settings.max_tokens})"

        new_size = len(new_content.encode("utf-8"))
        if new_size >= self.settings.max_file_size_bytes:
            return True, f"File size limit reached ({new_size}/{self.settings.max_file_size_bytes} bytes)"

        return False, ""
