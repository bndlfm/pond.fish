# Pond

Pond is a Fish-shell interface for a **stateful ACP agent**. It keeps the shell as a shell: terminal activity is recorded in order, but never wakes the agent until you explicitly start a Pond action.

Pond 3 uses a generic ACP subprocess. The default agent command is:

```text
hermes acp
```

`POND_HERMES_SERVER_URL` optionally selects the running Hermes backend (default `http://127.0.0.1:44437`). When a desktop-owned Hermes server is detected, Pond reuses its WebSocket session; otherwise it falls back to the configured ACP subprocess. `POND_HERMES_WS_TOKEN` can explicitly provide the server WebSocket token, but Pond also discovers a same-user desktop token automatically when possible.

Any compatible ACP agent can be configured with `POND_ACP_COMMAND_JSON`.

`POND_ICON_STYLE=emoji` opts into emoji icons if your terminal font does not include Nerd Font glyphs; the default style uses Nerd Font symbols for more stable alignment. Set `POND_FRAME_STYLE=plain` to disable the lightweight Powerline caps/gutter.
## What Pond does

- starts explicit stateful agent goals
- preserves workspace-scoped ACP sessions
- records assistant messages, executed commands, and terminal output chronologically
- renders Markdown and tool lifecycle events with Rich
- forwards agent permission requests through the terminal
- exposes harness-owned context status and manual compression

## What Pond intentionally does not do

- `pond -q` / stateless query mode
- fast agent-harness autocomplete or repair
- provider/API-key/model switching
- custom web search, skills, agent loop, or command whitelist
- automatic turns caused by terminal output

## Commands

```fish
pond -a "inspect this repository"
pond status
pond context
pond compress
pond forget
```

`pond status` reads only the local workspace-to-session pointer. `pond context` and `pond compress` explicitly send `/context` and `/compress` to the exact active ACP session. `pond forget` detaches the workspace pointer without deleting agent history.

## Configuring an ACP agent

The default is Hermes ACP. To select another compatible ACP agent, set an argv-only JSON command—Pond never shell-parses it:

```fish
set -gx POND_ACP_COMMAND_JSON '["/path/to/acp-agent", "--safe"]'
```

## Bindings

Pond defaults match the familiar Fish layout:

```text
Ctrl-X  ASK / xplain (no tools or reasoning)
Ctrl-A  agent mode (tools, skills, and reasoning)
```

Override them with `POND_KEYMAP_CODIFY` and `POND_KEYMAP_AGENT` if desired.

## Development

```fish
nix develop
.venv/bin/python -m pytest
```

See [DEVELOPMENT.md](DEVELOPMENT.md), [the stateful interaction design](docs/STATEFUL-ACP-INTERACTION-DESIGN.md), and [the rewrite contract](docs/HERMES-REWRITE-CONTRACT.md).
