"""Main application entry point."""

import asyncio
from app.mcp.server import run_server
from app.logging_config import setup_logging


def main():
    """Run the MCP server."""
    setup_logging()
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
