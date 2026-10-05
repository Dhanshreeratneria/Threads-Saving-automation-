"""Thread model for conversation threads."""

import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from app.models.message import Message


ThreadStatus = Literal["active", "closed"]


class ThreadCreate(BaseModel):
    """Input model for creating a thread."""

    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username for path")
    thread_name: str = Field(..., description="Thread display name")


class Thread(BaseModel):
    """Thread model with all fields."""

    thread_id: str = Field(..., description="Unique thread identifier")
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username for path")
    thread_name: str = Field(..., description="Thread display name")
    created_at: datetime = Field(..., description="Thread creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    status: ThreadStatus = Field(default="active", description="Thread status")
    message_count: int = Field(default=0, description="Number of messages")
    token_count: int = Field(default=0, description="Estimated token count")
    file_size: int = Field(default=0, description="File size in bytes")
    previous_thread_id: Optional[str] = Field(default=None, description="Previous thread ID")
    continuation: bool = Field(default=False, description="Whether this is a continuation")
    messages: List[Message] = Field(default_factory=list, description="Thread messages")

    @classmethod
    def create(
        cls,
        user_id: str,
        username: str,
        thread_name: str,
        thread_id: Optional[str] = None,
        previous_thread_id: Optional[str] = None,
        continuation: bool = False,
    ) -> "Thread":
        """Create a new thread with auto-generated ID and timestamps."""
        now = datetime.now(timezone.utc)
        return cls(
            thread_id=thread_id or f"thread-{now.strftime('%Y-%m-%d-%H%M%S')}-{str(uuid.uuid4())[:8]}",
            user_id=user_id,
            username=username,
            thread_name=thread_name,
            created_at=now,
            updated_at=now,
            status="active",
            message_count=0,
            token_count=0,
            file_size=0,
            previous_thread_id=previous_thread_id,
            continuation=continuation,
            messages=[],
        )

    def add_message(self, message: Message) -> None:
        """Add a message to the thread."""
        self.messages.append(message)
        self.message_count = len(self.messages)
        self.updated_at = datetime.now(timezone.utc)

    def get_filename(self) -> str:
        """Get the Markdown filename for this thread."""
        return f"{self.thread_id}.md"

    def get_filepath(self, base_path: str = "users") -> str:
        """Get the full filepath for this thread."""
        return f"{base_path}/{self.username}/{self.get_filename()}"
