# Stateful ACP Interaction Design

Status: approved design target for the post-legacy Pond interface.

## One interaction model

Pond 3 has one intelligence path: a stateful ACP session scoped to a workspace. There is no stateless query provider, no hidden second LLM client, and no automatic inference in response to terminal activity.

The user explicitly starts every turn through a Pond command or a configured binding. Pond then submits exactly one ACP `session/prompt` request to the workspace session.

## Workspace session ownership

- Pond resolves a workspace as the normalized Git root, falling back to normalized cwd.
- Pond stores the ACP session handle for that workspace/profile only in an atomic local pointer file (directory mode `0700`, file mode `0600`); ACP owns the actual transcript.
- ACP owns agent conversation state; Pond owns the chronological display/history timeline and its workspace-to-session mapping.
- A stale handle creates a new session only after an exact load attempt fails.
- Pond never selects a session by title or recency alone.

## Explicit turn envelope

Every user-started Pond action is encoded as ordinary text in a single ACP prompt. The `pond-action` CLI bridge resolves the workspace's exact session handle, submits the turn, then persists the returned handle for the next explicit action. The action is declared explicitly so the agent does not need to infer intent from a key sequence.

```text
[Pond action: command-draft]
User request: <user text>

Terminal activity observed since the prior user turn:
<ordered command/output entries, if any>

Return a proposed Fish command only. Do not execute it.
```

Other action names are `explain`, `complete`, `repair`, and `agent`. They are UI intents, not separate backend protocols. The agent receives no ambient terminal activity outside an explicit envelope.

## Terminal is passive

Terminal observer events append to the Pond timeline in real order, but do not:

- submit ACP prompts;
- interrupt or resume a session;
- cause a new assistant message;
- mutate the Fish command buffer.

On the next explicit user turn, Pond attaches the unread terminal command/output entries to that one request. The user message remains the event that wakes the agent.

If an ACP agent executes a tool during an already-active turn, ACP tool results may continue that same turn. They do not manufacture a new user message or a separate unsolicited assistant turn.

## Rendering and command buffers

- Assistant text streams to the Pond terminal UI through the Rich-backed `pond.render` module.
- Tool calls and results are rendered as timeline entries between messages.
- Final content is never executed automatically.
- Command-draft/complete/repair actions validate final output before replacing a Fish command buffer.
- Agent actions render the final report to stdout when piped and use stderr for progress/UI.
- Large tool output may be abbreviated in the terminal while the timeline retains full content or explicit truncation metadata.

## Permissions

Pond forwards standard ACP permission requests from the selected agent. It renders only options actually offered by that agent through `/dev/tty`, returns structured ACP outcomes, and fails closed on EOF, timeout, malformed input, cancellation, or bridge failure.

Pond's temporary “allow for this turn” choice is client-side bookkeeping: it responds with ACP `allow_once` only to matching later permission requests while the same explicit prompt remains active. It resets when that prompt ends.

## Migration sequence

1. Implement ACP session creation/load and the workspace mapping.
2. Submit a minimal explicit `agent` envelope and render final text.
3. Add timeline persistence/replay with terminal context batching.
4. Move command-draft, explain, completion, and repair one intent at a time.
5. Remove legacy Fish-AI dispatch only after each replacement has feature and safety tests.

## Acceptance criteria

- Running a terminal command without messaging Pond produces no ACP traffic and no assistant response.
- A subsequent explicit Pond message receives the prior terminal activity in the same chronological order users saw it.
- A fresh Pond process reloads the workspace session and timeline without losing command/output entries.
- Every final command proposal remains inert until the user runs it.
- Agent tool permissions remain interactive and fail closed.
