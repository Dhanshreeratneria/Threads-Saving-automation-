"""Tests for Markdown generator."""

import pytest
from app.models.thread import Thread
from app.models.message import Message
from app.markdown.generator import MarkdownGenerator


@pytest.fixture
def sample_thread():
    thread = Thread.create(user_id="testuser", username="testuser", thread_name="Test Thread")
    thread.add_message(Message.create(role="user", content="How are you?"))
    thread.add_message(Message.create(role="assistant", content="I'm doing well!"))
    return thread


def test_generate_basic(sample_thread):
    generator = MarkdownGenerator()
    markdown = generator.generate(sample_thread)
    assert "# Claude Conversation" in markdown
    assert "### User" in markdown
    assert "### Claude" in markdown
    assert "How are you?" in markdown


def test_estimate_tokens():
    text = "This is a test message."
    tokens = MarkdownGenerator.estimate_tokens(text)
    assert tokens > 0
