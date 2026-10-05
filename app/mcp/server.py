"""MCP Server implementation."""

import asyncio
from typing import Any, Dict, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from app.config import get_settings
from app.logging_config import get_logger, setup_logging
from app.storage.github import GitHubStorage
from app.threads.manager import ThreadManager
from app.integration.conversation import ConversationCapture
from app.services.search import SearchService


logger = get_logger()


def create_mcp_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("thread-saving-mcp")
    storage: Optional[GitHubStorage] = None
    thread_manager: Optional[ThreadManager] = None
    conversation_capture: Optional[ConversationCapture] = None
    search_service: Optional[SearchService] = None

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available MCP tools."""
        return [
            Tool(
                name="create_thread",
                description="Create a new conversation thread for a user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "Unique user identifier"},
                        "username": {"type": "string", "description": "Username for directory path"},
                        "thread_name": {"type": "string", "description": "Display name for the thread"},
                    },
                    "required": ["user_id", "username", "thread_name"],
                },
            ),
            Tool(
                name="save_conversation",
                description="Save a user prompt and AI response to a thread",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "thread_id": {"type": "string", "description": "Thread identifier"},
                        "user_prompt": {"type": "string", "description": "User's prompt (preserved exactly)"},
                        "assistant_response": {"type": "string", "description": "Assistant's response (preserved exactly)"},
                        "username": {"type": "string", "description": "Username (defaults to user_id)"},
                        "user_message_id": {"type": "string", "description": "Optional idempotency key"},
                        "assistant_message_id": {"type": "string", "description": "Optional idempotency key"},
                    },
                    "required": ["user_id", "thread_id", "user_prompt", "assistant_response"],
                },
            ),
            Tool(
                name="get_thread",
                description="Retrieve a thread by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "thread_id": {"type": "string", "description": "Thread identifier"},
                        "username": {"type": "string", "description": "Username (defaults to user_id)"},
                    },
                    "required": ["user_id", "thread_id"],
                },
            ),
            Tool(
                name="list_threads",
                description="List all threads for a user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "username": {"type": "string", "description": "Username (defaults to user_id)"},
                    },
                    "required": ["user_id"],
                },
            ),
            Tool(
                name="search_threads",
                description="Search threads for a user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "query": {"type": "string", "description": "Search query"},
                        "username": {"type": "string", "description": "Username (defaults to user_id)"},
                    },
                    "required": ["user_id", "query"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        try:
            nonlocal storage, thread_manager, conversation_capture, search_service

            if storage is None:
                storage = GitHubStorage()
                thread_manager = ThreadManager(storage)
                conversation_capture = ConversationCapture(thread_manager)
                search_service = SearchService(storage)

            username = arguments.get("username") or arguments.get("user_id")

            if name == "create_thread":
                result = await thread_manager.create_thread(
                    user_id=arguments["user_id"], username=username, thread_name=arguments["thread_name"],
                )
                await thread_manager.update_thread(result)
                return [TextContent(type="text", text=f"Thread created: {result.thread_id}\nPath: {result.get_filepath(thread_manager.settings.thread_base_path)}")]

            elif name == "save_conversation":
                try:
                    thread = await thread_manager.get_thread(
                        user_id=arguments["user_id"], username=username, thread_id=arguments["thread_id"],
                    )
                except Exception:
                    thread = await thread_manager.create_thread(
                        user_id=arguments["user_id"], username=username,
                        thread_name=f"Thread {arguments['thread_id']}", thread_id=arguments["thread_id"],
                    )

                updated_thread, needs_rotation = await thread_manager.save_conversation(
                    thread=thread, user_prompt=arguments["user_prompt"],
                    assistant_response=arguments["assistant_response"],
                    user_message_id=arguments.get("user_message_id"),
                    assistant_message_id=arguments.get("assistant_message_id"),
                )

                if needs_rotation:
                    new_thread = await thread_manager.rotate_thread(updated_thread)
                    return [TextContent(type="text", text=f"Conversation saved and thread rotated: {new_thread.thread_id}")]

                return [TextContent(type="text", text=f"Conversation saved to thread: {updated_thread.thread_id}\nMessages: {updated_thread.message_count}")]

            elif name == "get_thread":
                thread = await thread_manager.get_thread(
                    user_id=arguments["user_id"], username=username, thread_id=arguments["thread_id"],
                )
                return [TextContent(type="text", text=f"Thread: {thread.thread_id}\nName: {thread.thread_name}\nStatus: {thread.status}\nMessages: {thread.message_count}")]

            elif name == "list_threads":
                threads = await thread_manager.list_threads(username)
                if not threads:
                    return [TextContent(type="text", text=f"No threads found for user: {username}")]
                return [TextContent(type="text", text=f"Threads for {username}:\n" + "\n".join(threads))]

            elif name == "search_threads":
                results = await search_service.search_threads(
                    user_id=arguments["user_id"], username=username, query=arguments["query"],
                )
                if not results:
                    return [TextContent(type="text", text=f"No matching threads found for query: {arguments['query']}")]
                result_text = f"Found {len(results)} matching threads:\n"
                for match in results:
                    result_text += f"- {match.get('filepath', 'unknown')}\n"
                return [TextContent(type="text", text=result_text)]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            logger.error(f"tool_error - {name}: {str(e)}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    return server


async def run_server():
    """Run the MCP server."""
    setup_logging()
    logger.info("Starting Thread Saving MCP server...")
    server = create_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
