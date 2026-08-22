# Plan: Add Stateless `ai` Command for Piping

This plan outlines the implementation of a new `ai` command that serves as a general-purpose, stateless interface for LLM queries via the command line.

## Objective
Enable a unix-style interface for the LLM backend that supports piping input and output without including shell history or previous agent state.

## Implementation Details

### 1. Register CLI Entry Point (`pyproject.toml`)
Add a new script entry:
- `ai = "fish_ai.ai:main"`

### 2. Create Python Module (`src/fish_ai/ai.py`)
Implement the `main` function to:
- **Read Stdin**: Capture data if it's being piped in (`not sys.stdin.isatty()`).
- **Parse Arguments**: Combine all CLI arguments into a single prompt string.
- **Stateless Context**:
  - Do NOT include `get_commandline_history`.
  - Do NOT include `get_file_info` automatically.
  - Use a clean system prompt focused on direct technical assistance.
- **Engine Integration**: Call `engine.get_chat_response` with the isolated message list.
- **Raw Output**: Print only the LLM's content to `stdout` to ensure compatibility with further piping or redirection.

### 3. Documentation (`README.md`)
Add a section for the `ai` command with examples:
- `cat log.txt | ai "find the errors"`
- `ai "generate a regex for email validation" > regex.txt`

## Verification & Testing
- **Piping In**: `echo "foo" | ai "uppercase this"` -> output: `FOO`
- **Piping Out**: `ai "list 5 fruits" | grep "Apple"` -> output should contain `Apple`.
- **Statelessness**: Verify that the command does not know about previous `ai` calls or shell history.
