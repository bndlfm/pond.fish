# Plan: Add Agentic Loop Mode with Tools to fish-ai

This plan outlines the implementation of an "agentic loop mode" in the `fish-ai` extension, incorporating structured tool use (including a shell execution tool) to achieve goals autonomously.

## Objective
Enable a multi-turn autonomous agent mode triggered by `Ctrl+A`. The agent will use tools (shell execution, file reading, etc.) to perform tasks, with shell commands requiring user confirmation.

## Implementation Details

### 1. Update Engine for Tool Support (`src/fish_ai/engine.py`)
- Modify `get_response(messages)` to accept an optional `tools` parameter.
- Implement tool-calling logic for supported providers (OpenAI, Anthropic, Gemini, Mistral).
- Update message formatting to handle `tool_calls` and `tool_outputs` in history.

### 2. Implement Agent Tools (`src/fish_ai/agent.py`)
Define the following tools in the new agent module:
- `shell_execute(command)`: Execute a command in the Fish shell (requires user confirmation).
- `read_file(path)`: Read the content of a file.
- `list_directory(path)`: List files in a directory.
- `write_file(path, content)`: Write content to a file.

The `agent.py` script will:
- Initialize the conversation with the goal.
- Process tool calls from the LLM.
- For `shell_execute`, return a special "PENDING_CONFIRMATION" status to the shell wrapper.
- For other tools, execute them immediately and feed the result back to the LLM.

### 3. Implement Fish Shell Wrapper (`functions/_fish_ai_agent.fish`)
The wrapper will:
- Set up the environment and state files.
- Loop until the agent returns `DONE`.
- If the agent requests `shell_execute`:
  - Display the command.
  - Wait for user confirmation (`Y/n`).
  - If confirmed: Execute using `eval` (to preserve state changes like `cd`), capture output, and pass back to `agent.py`.
  - If rejected: Inform the agent the command was rejected.
- If the agent requests other tools (read/list/write):
  - These can be executed directly by the Python script, but the shell wrapper should ideally show what's happening to keep the user informed.

### 4. Integration & Configuration
- **Entry Point**: `agent = 'fish_ai.agent:main'` in `pyproject.toml`.
- **Key Binding**: `Ctrl+A` (configurable via `keymap_3` in `config.ini`).
- **System Prompt**: Updated to guide the agent on tool usage and Fish shell specificities.

## Verification & Testing
- **Tool Execution**: Verify that `read_file` handles large files or missing files gracefully.
- **Confirmation Flow**: Ensure the agent cannot bypass the confirmation for `shell_execute`.
- **State Persistence**: Verify that `cd` in an agent-executed command actually changes the directory in the parent shell.
- **Multi-turn Logic**: Test a goal requiring multiple steps (e.g., "Find the largest Python file and summarize its first 10 lines").
