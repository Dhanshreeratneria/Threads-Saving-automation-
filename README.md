# Thread Saving MCP

A Model Context Protocol (MCP) server for saving Claude/Cruz Brain conversation threads as Markdown files in a GitHub repository.

## Quick Start

```bash
cd thread-saving-mcp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GitHub credentials
python run.py
```

## Configuration

Edit `.env` with your GitHub details:

```env
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_OWNER=your_github_username
GITHUB_REPOSITORY=your-threads-repository
GITHUB_BRANCH=main
MAX_MESSAGES=100
MAX_TOKENS=50000
MAX_FILE_SIZE_MB=5
```

## MCP Tools

- **create_thread** - Create a new conversation thread
- **save_conversation** - Save user prompt + AI response
- **get_thread** - Retrieve thread metadata
- **list_threads** - List user's threads
- **search_threads** - Search within user's threads

## Testing

```bash
pytest tests/ -v
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
