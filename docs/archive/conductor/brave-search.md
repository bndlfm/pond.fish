# Plan: Add Brave Search Tool to Agentic Loop

This plan outlines the integration of the Brave Search API into the autonomous agent, providing real-time web research capabilities.

## Objective
Enable the agent to search the web using `web_search(query)` when it needs documentation, latest versions, or troubleshooting help that isn't available in the local environment.

## Implementation Details

### 1. Configuration
-   **Setting**: Add `brave_search_api_key` to the `[fish-ai]` section in `~/.config/config.ini`.
-   **Keyring Support**: Update `fish_ai_put_api_key` to support saving the Brave key to the system keyring.

### 2. Python Agent Tool (`src/fish_ai/agent.py`)
-   **Implementation**: Create a `web_search(query)` function using `httpx`.
-   **Parsing**: Extract `title`, `url`, and `description` from the top 5 results in the `web.results` payload.
-   **Safety**: Return a clear error if the API key is missing.
-   **Tool Registration**: Add `web_search` to the `TOOLS` list with clear parameter descriptions.
-   **Prompting**: Update `SYSTEM_PROMPT` to guide the agent on when to use web search vs. local tools.

### 3. Verification & Testing
-   **Config check**: Verify the agent reports a missing API key gracefully.
-   **Live Search**: Test with a real query (e.g., "latest stable version of fish shell") and verify the agent can read and summarize the results.
-   **Audit UI**: Confirm the search action and results are correctly displayed in the terminal audit trail.
