# Pond Architecture

Pond is a Fish-shell client for a **stateful ACP agent**.

## Boundaries

- `functions/pond.fish` exposes stateful user actions: agent goal, status, context, compression, and session detach.
- `functions/_pond_codify_or_explain.fish` submits explicit command-draft actions; it does not provide legacy query/explain mode.
- `functions/_pond_agent.fish` submits explicit stateful agent goals.
- `conf.d/pond.fish` sets XDG paths and only registers user-configured bindings. It performs no installation, network work, or default binding setup.
- `src/pond/backend/` contains the generic ACP protocol client, session pointers, permissions, context pressure, and chronological history.
- `src/pond/render.py` uses Rich for Markdown and tool lifecycle rendering.

## Session and terminal model

One normalized workspace maps to one exact ACP session handle per profile. Pond stores only that local pointer; the ACP agent owns transcript persistence and compaction.

Terminal activity is passive. Command/output events are preserved in the timeline, but Pond sends them to the agent only when the user starts a later explicit action.

## Safety

- Pond never auto-executes returned commands.
- ACP permission requests are rendered through `/dev/tty` and fail closed.
- `pond compress` and `pond context` are explicit wrappers around the active ACP session’s `/compress` and `/context` commands.
- Pond does not contain a provider engine, API-key storage, custom tool loop, stateless query mode, or agent-harness autocomplete/repair mode.

See [the interaction design](docs/STATEFUL-ACP-INTERACTION-DESIGN.md) and [the rewrite contract](docs/HERMES-REWRITE-CONTRACT.md).
