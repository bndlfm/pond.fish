# Legacy Runtime Removal Map

This map is the deletion order for the remaining Fish-AI runtime. Pond 3 keeps only the ACP stateful path, Rich rendering, session mapping, and the small Pond action CLIs.

## Keep

- `src/pond/backend/` — generic ACP transport, session mapping, permission policy, timeline, context-pressure display.
- `src/pond/action_cli.py` — stateful Pond action/session commands.
- `src/pond/render.py` — Rich Markdown and tool lifecycle rendering.
- `functions/pond.fish`, `functions/_pond_*.fish`, `conf.d/pond.fish` — Pond shell UI.
- `agent-client-protocol` and `rich` dependencies.

## Delete as one dependency-checked removal sequence

### 1. Provider and stateless task modules

Delete the source modules and their tests:

- `src/pond/engine.py`
- `src/pond/config.py`
- `src/pond/codify.py`
- `src/pond/explain.py`
- `src/pond/autocomplete.py`
- `src/pond/fix.py`
- `src/pond/redact.py`
- `src/pond/put_api_key.py`
- `src/pond/switch_context.py`
- corresponding tests: `engine_test.py`, `codify_test.py`, `explain_test.py`, `autocomplete_test.py`, `fix_test.py`, `redact_test.py`

Do not delete the current `fix_test.py` safety assertion until its replacement removal test proves there is no longer a provider repair entrypoint.

### 2. Legacy custom agent

Delete:

- `src/pond/agent.py`
- `src/pond/tests/agent_test.py`
- legacy script entries (`agent`, `render`) once all Fish callers point at `pond-action`/`pond.render`.

### 3. Legacy Fish wrappers and startup

Delete only after the prior two groups are gone:

- `conf.d/fish_ai.fish`
- every `functions/_fish_ai_*.fish`
- `functions/fish_ai_*.fish`
- legacy `pond.fish` branches used when `POND_REWRITE` is unset

Then remove `POND_REWRITE`: Pond 3 becomes the single runtime path.

### 4. Dependencies and CI

Remove from `pyproject.toml` and `.devcontainer/requirements-dev.txt` once no source import remains:

- `openai`, `mistralai`, `anthropic`, `groq`, `google-genai`
- `aws-bedrock-token-generator`, `httpx[socks]`
- `keyring`, `simple-term-menu`, `binaryornot`, `iterfzf`

Keep `agent-client-protocol` and `rich`.

Update installation containers, CI coverage paths, README, architecture docs, and migration notes in the same final cleanup sequence.

## Verification gates

Before each deletion commit:

1. `search_files` finds no live import/caller outside the deletion set.
2. Write a failing regression test proving the Pond ACP replacement path remains intact.
3. Run the full Python suite, Fish syntax checks, package build, and relevant installation smoke test.
4. Commit locally only; do not push unless Neko explicitly asks.
