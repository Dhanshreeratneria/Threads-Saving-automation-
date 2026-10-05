"""User model for thread ownership and identification."""

import re
from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    """Input model for creating a user."""

    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username for directory path")

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not v or len(v) < 3:
            raise ValueError("user_id must be at least 3 characters")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or len(v) < 3:
            raise ValueError("username must be at least 3 characters")
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("username must contain only alphanumeric, underscore, or hyphen")
        return v.lower()


class User(BaseModel):
    """User model with validated fields."""

    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Normalized username")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or len(v) < 3:
            raise ValueError("username must be at least 3 characters")
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("username must contain only alphanumeric, underscore, or hyphen")
        return v.lower()

    def get_user_path(self, base_path: str = "users") -> str:
        """Get the user's directory path."""
        return f"{base_path}/{self.username}"
