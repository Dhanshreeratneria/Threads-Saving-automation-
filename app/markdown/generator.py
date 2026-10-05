"""Markdown generator for conversation threads."""

from typing import Optional
from app.models.thread import Thread


class MarkdownGenerator:
    """Generate Markdown content from Thread objects."""

    @staticmethod
    def generate(thread: Thread, include_metadata: bool = True) -> str:
        """Generate Markdown content from a Thread object."""
        lines = []

        # Header
        lines.append("# Claude Conversation")
        lines.append("")
        lines.append(f"**User:** {thread.username}")
        lines.append(f"**Thread ID:** {thread.thread_id}")
        lines.append(f"**Thread Name:** {thread.thread_name}")
        lines.append(f"**Created:** {thread.created_at.isoformat()}")
        lines.append(f"**Updated:** {thread.updated_at.isoformat()}")
        lines.append(f"**Status:** {thread.status}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Conversation section
        lines.append("## Conversation")
        lines.append("")

        for message in thread.messages:
            role_display = MarkdownGenerator._get_role_display(message.role)
            lines.append(f"### {role_display}")
            lines.append("")
            lines.append(message.content)
            lines.append("")

        lines.append("---")
        lines.append("")

        # Metadata section
        if include_metadata:
            lines.append("## Thread Metadata")
            lines.append("")
            lines.append(f"- User ID: {thread.user_id}")
            lines.append(f"- Thread ID: {thread.thread_id}")
            lines.append(f"- Message Count: {thread.message_count}")
            lines.append(f"- Token Count: {thread.token_count}")
            lines.append(f"- File Size: {thread.file_size} bytes")
            lines.append(f"- Previous Thread: {thread.previous_thread_id or 'None'}")
            lines.append(f"- Continuation: {'Yes' if thread.continuation else 'No'}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _get_role_display(role: str) -> str:
        """Get display name for message role."""
        role_map = {
            "user": "User",
            "assistant": "Claude",
            "system": "System",
            "tool": "Tool",
        }
        return role_map.get(role, role.capitalize())

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough estimate of token count (~4 characters per token)."""
        return len(text) // 4
