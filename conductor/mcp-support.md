# Plan: Add Model Context Protocol (MCP) Support

This plan outlines the integration of MCP into the `pond` agent, allowing it to use standardized external tools.

## Objective
Enable the agent to act as an MCP Client, connecting to MCP Servers to expand its toolset beyond local file reading and shell execution.

## Implementation Details

### 1. Dependencies
Update `pyproject.toml` to include:
- `mcp`: The official Model Context Protocol Python SDK.

### 2. Configuration (`fish-ai.ini`)
Add support for configuring MCP servers:
```ini
[mcp]
# Format: <name> = <command to start server>
google-drive = npx -y @modelcontextprotocol/server-google-drive
local-db = python /path/to/my_db_server.py
```

### 3. Agent Integration (`src/fish_ai/agent.py`)
- **Discovery**: At startup, the agent iterates through the `[mcp]` config and starts the server processes.
- **Tool Mapping**: It queries each server for its tools and converts them into the OpenAI/Gemini tool calling format.
- **Execution**:
  - Native tools (`read_path`, `shell_execute`) remain handled locally.
  - MCP tools are routed to the corresponding server process.
- **Lifecycle**: Ensure all MCP server processes are cleanly terminated when the agent loop finishes.

### 4. UI & Auditing
- MCP tool calls should be logged just like native tools: `🛠️ Action: <server>:<tool>(...)`.
- Results should be displayed in the truncated 4-line format.

## Verification
- Connect a simple MCP server (e.g., a "hello world" or "echo" server).
- Verify the agent can list and call the tools from that server.
- Verify that `Ctrl+C` correctly kills both the agent and all background MCP servers.
