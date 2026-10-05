"""Message model for conversation messages."""

import uuid
from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


MessageRole = Literal["user", "assistant", "system", "tool"]


class MessageCreate(BaseModel):
    """Input model for creating a message."""

    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    message_id: Optional[str] = Field(default=None, description="Optional idempotency key")
    timestamp: Optional[datetime] = Field(default=None, description="Message timestamp")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Message content cannot be empty")
        return v


class Message(BaseModel):
    """Message model with all fields."""

    message_id: str = Field(..., description="Unique message identifier")
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content (preserved exactly)")
    timestamp: datetime = Field(..., description="Message timestamp")

    @classmethod
    def create(
        cls,
        role: MessageRole,
        content: str,
        message_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> "Message":
        """Create a new message with auto-generated ID and timestamp."""
        return cls(
            message_id=message_id or str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=timestamp or datetime.now(timezone.utc),
        )
