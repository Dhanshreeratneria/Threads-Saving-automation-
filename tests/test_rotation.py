"""Tests for thread rotation."""

import pytest
from unittest.mock import patch
from app.models.thread import Thread
from app.threads.rotation import ThreadRotation


@pytest.fixture
def rotation():
    return ThreadRotation()


@patch("app.threads.rotation.get_settings")
def test_check_limits_under_limit(mock_settings, rotation):
    mock_settings.return_value.max_messages = 100
    mock_settings.return_value.max_tokens = 50000
    mock_settings.return_value.max_file_size_bytes = 5 * 1024 * 1024

    thread = Thread.create(user_id="user1", username="user1", thread_name="Test")
    thread.message_count = 5
    needs_rotation, reason = rotation.check_limits(thread, "test content")
    assert needs_rotation is False


@patch("app.threads.rotation.get_settings")
def test_check_limits_message_limit(mock_settings, rotation):
    mock_settings.return_value.max_messages = 5
    mock_settings.return_value.max_tokens = 50000
    mock_settings.return_value.max_file_size_bytes = 5 * 1024 * 1024

    thread = Thread.create(user_id="user1", username="user1", thread_name="Test")
    thread.message_count = 5
    needs_rotation, reason = rotation.check_limits(thread, "test")
    assert needs_rotation is True
    assert "Message limit" in reason
