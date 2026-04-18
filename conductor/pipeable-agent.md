# Plan: Make Agentic Loop Pipeable

This plan outlines the changes needed to make `pond agent` pipeable by separating progress (audit trail) from the final result.

## Objective
Enable users to pipe the output of an autonomous agent task into other shell tools (e.g., `pond agent "..." | jq`) without intermediate noise like thoughts or tool calls.

## Implementation Steps

### 1. Update `_fish_ai_agent.fish`
- Route all progress indicators (⏳ STATUS, 💭 Thought, 🛠️ Action, 🔌 Skill, 📋 Result) to **`stderr`** (using `>&2`).
- Route all interactive prompts and permission warnings to **`stderr`**.
- Route the final `CHAT` or `DONE` output to **`stdout`**.
- Add `isatty stdout` check:
    - If `stdout` is a TTY: Use the rich Markdown renderer for the final result.
    - If `stdout` is a pipe: Output the raw content directly to preserve formatting/data structure for the next tool.

### 2. Update `pond.fish`
- Ensure that when `pond agent` is called from the CLI, it inherits the new stderr/stdout routing correctly.

## Verification
- Run `pond agent "echo hello" | cat`.
- Verify that thoughts and actions appear in the terminal.
- Verify that ONLY "hello" (or the final report) is captured by `cat`.
- Run `pond agent "get status as json" | jq .` and verify it parses correctly.
