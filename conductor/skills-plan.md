# Plan: Implement Script-Based Skills

This plan replaces MCP with a minimalist "Skills" system based on self-documenting scripts.

## Objective
Enable users to extend the agent's capabilities by simply dropping scripts into a designated "skills" directory.

## Implementation Details

### 1. Skill Specification
A "Skill" is an executable file that:
-   Returns its OpenAI-compatible tool definition (JSON) when called with `--info`.
-   Performs its action and returns text output when called with arguments.

Example (`skills/get_weather`):
```bash
#!/bin/bash
if [ "$1" == "--info" ]; then
  echo '{"name": "get_weather", "description": "Get weather for a city", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}}}'
  exit 0
fi
curl -s "wttr.in/$location?format=3"
```

### 2. Agent Integration (`src/fish_ai/agent.py`)
-   **Discovery**: Define `SKILLS_DIR` (default: `~/.config/fish-ai/skills`).
-   **Registration**: Loop through files in `SKILLS_DIR`. For each executable, run `./script --info` and add the result to the agent's tool list.
-   **Execution**: If a tool call matches a discovered skill, execute the script. Pass arguments as environment variables or CLI flags (e.g., `--key value`).

### 3. Folder Setup
Ensure the `skills` directory is created automatically if it doesn't exist.

## Verification
-   Create a dummy "hello" skill.
-   Verify the agent "learns" the tool at startup.
-   Verify the agent can successfully call the skill and receive the output.
