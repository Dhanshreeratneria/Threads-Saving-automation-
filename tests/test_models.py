"""Tests for data models."""

import pytest
from app.models.user import UserCreate
from app.models.message import Message, MessageRole
from app.models.thread import Thread


class TestUser:
    def test_create_user_valid(self):
        user = UserCreate(user_id="user123", username="testuser")
        assert user.user_id == "user123"
        assert user.username == "testuser"

    def test_user_invalid_username(self):
        with pytest.raises(ValueError):
            UserCreate(user_id="user123", username="test@user")


class TestMessage:
    def test_create_message_valid(self):
        msg = Message.create(role="user", content="Test message")
        assert msg.role == "user"
        assert msg.content == "Test message"
        assert msg.message_id is not None

    def test_message_empty_content(self):
        with pytest.raises(ValueError):
            Message.create(role="user", content="")


class TestThread:
    def test_create_thread_valid(self):
        thread = Thread.create(user_id="user123", username="testuser", thread_name="Test Thread")
        assert thread.user_id == "user123"
        assert thread.status == "active"
        assert thread.message_count == 0

    def test_thread_add_message(self):
        thread = Thread.create(user_id="user123", username="testuser", thread_name="Test")
        msg = Message.create(role="user", content="Test message")
        thread.add_message(msg)
        assert thread.message_count == 1
