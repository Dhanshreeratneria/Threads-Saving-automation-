# Thread Saving MCP

A Model Context Protocol (MCP) server for saving Claude/Cruz Brain conversation threads as Markdown files in a GitHub repository.

## Quick Start

From PowerShell, in the project directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

In `.env`, set:

- `GITHUB_TOKEN`: a GitHub fine-grained personal access token with **Contents: Read and write** permission for the target repository.
- `GITHUB_OWNER`: the repository owner (user or organization).
- `GITHUB_REPOSITORY`: the target repository name. Create the repository and its configured branch first.

The server reads `.env` from the project directory regardless of the process working directory. Keep `.env` private; it is excluded from Git.

This is an MCP server using the stdio transport, so running it directly waits for an MCP client rather than opening a web page:

```powershell
.\.venv\Scripts\python.exe run.py
```

To connect it to an MCP client such as Claude Desktop, add an entry to that client's MCP server configuration and replace the paths with this project's absolute paths:

```json
{
  "mcpServers": {
    "thread-saving-mcp": {
      "command": "C:\\path\\to\\project\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\project\\run.py"]
    }
  }
}
```

Restart the MCP client after saving its configuration. Server logs are written to stderr so they do not interfere with the MCP protocol on stdout.

## Configuration

`.env.example` documents all supported settings, including the thread storage path, message/token/file-size limits, and logging level. The default storage path is `users`.

## MCP Tools

- **create_thread** - Create a new conversation thread
- **save_conversation** - Save user prompt + AI response
- **get_thread** - Retrieve thread metadata
- **list_threads** - List user's threads
- **search_threads** - Search within user's threads

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```

## Architecture

```
Claude/Cruz Brain
    ↓
ConversationCapture (integration layer)
    ↓
ThreadManager
    ↓
MarkdownGenerator
    ↓
GitHubStorage → Threads Repository
```

See full documentation in the project files.
"# Threads-Saving-automation-" 
