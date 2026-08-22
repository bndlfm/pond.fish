# Pond 3.0 ACP Rewrite Contract

Status: approved pre-implementation boundary for the Pond 3.0 rewrite.

This document separates behavior Pond must preserve from behavior deliberately transferred to Hermes or removed. It is the acceptance contract for implementation after S00–S05.

## Architecture boundary

Pond remains a Fish-native frontend. A compatible ACP agent becomes the stateful agent runtime. Hermes is Pond's shipped default command and reference-tested developer integration, not a required protocol specialization.

### Pond owns

- Fish keybindings and command-buffer manipulation.
- Ctrl+Q codify/explain routing.
- Ctrl+Space autocomplete/fix routing and FZF selection.
- Ctrl+A agent launch and terminal presentation.
- Shell-specific prompt/context collection.
- ACP client rendering and permission interaction.
- A minimal mapping from workspace to Hermes ACP session ID.
- Stable Pond CLI output and exit-code contracts.

### The selected ACP agent owns

- Provider/model selection and credentials.
- Inference, reasoning configuration, retries, and usage accounting.
- Stateful agent loop and tool execution.
- Tool policy and dangerous-command classification.
- Skills, MCP servers, search, delegation, and project rules.
- Session history, compression, branching, and cancellation.

Pond's core must not import Hermes internal Python modules. The stateful boundary is standard ACP over stdio. The default command is `hermes acp`; other ACP agent commands are supported when they negotiate the required capabilities.

## Preserved user behavior

### Ctrl+Q

- Empty command buffer: no action.
- Hash-prefixed or unknown natural language: generate a Fish command.
- Known command: return a concise explanation/comment.
- Output replaces the command buffer and is never automatically executed.

### Ctrl+Space

- Non-empty command buffer: request completion, preserve the logical cursor, and allow FZF refinement.
- Empty buffer after a failed command: offer a repaired command.
- A repaired or completed command is inserted, never automatically executed.
- Pond 3.0 must not rerun the failed command merely to recover stderr.

### Ctrl+A / agent

- The current command buffer becomes the initial goal.
- Agent tools run relative to the intended workspace.
- Assistant text and tool lifecycle are streamed to the terminal.
- Ctrl+C cooperatively cancels the active ACP turn and does not leave child processes.
- Final textual output remains pipeable separately from progress rendering.

### `pond -q`

- Accept prompt arguments and optional stdin context.
- Plain mode emits final content to stdout.
- Diagnostics go to stderr.
- Failure returns nonzero.
- `--json` uses a Pond-owned, versioned envelope rather than exposing a provider SDK object.
- Missing prompt and missing stdin must return nonzero; the Pond 2.x behavior is a known defect.

## Permission contract

The selected ACP agent classifies commands and issues ACP permission requests. Pond renders available server options and returns structured responses; it does not maintain a competing command whitelist.

Pond presents:

- Allow once.
- Allow until the current agent turn ends.
- Allow for the Hermes session, when offered.
- Allow always, when offered.
- Deny once.
- Deny always, when offered.

“Allow until end of turn” is a Pond client convenience because ACP/Hermes does not currently expose that exact scope. Pond implements it by answering subsequent matching requests with `allow_once` only until the current `session/prompt` completes, fails, times out, or is cancelled. It must not send an unknown permission option ID to Hermes.

The temporary match scope is the same executable or normalized command pattern, not every later command in the turn.

Permissions fail closed on:

- EOF or unavailable `/dev/tty`.
- Timeout.
- Unknown or malformed option.
- ACP bridge failure.
- Child-process death.
- Cancellation.

## Privacy contract

- Existing outbound prompt redaction remains in place for quick transformations until tests demonstrate an equivalent pre-provider Hermes guarantee.
- No migration copies provider keys from Pond configuration into Hermes.
- No credential, token, or secret appears in logs, migration reports, JSON output, session-pointer files, or test fixtures.
- Stateless transformations ignore personal memory, SOUL, skills, project rules, and ambient MCP servers unless explicitly enabled.
- Stateful Ctrl+A agent sessions intentionally use the selected Hermes profile and workspace context.

## Naming and startup boundary

Pond 3.0 removes the legacy startup implementation:

- Delete `conf.d/fish_ai.fish` after the replacement is installed and tested.
- Add a minimal, network-free `conf.d/pond.fish`.
- Rename private `_fish_ai_*` functions and globals to `_pond_*`.
- Keep only documented public compatibility shims that have an explicit removal date.

The new startup file may:

- Resolve Pond helpers.
- Verify that `hermes` is present.
- Register Fish keybindings.
- Define Pond-specific XDG paths and UI settings.

It must not:

- Create or update Python environments during ordinary shell startup.
- Install packages over the network during shell startup.
- Read, copy, or mutate Hermes credentials/configuration.
- Start an ACP child until a Pond feature is invoked.

## Deliberate 3.0 breaks

- Pond no longer owns provider/model/API-key configuration.
- `fish_ai_put_api_key` and `fish_ai_switch_context` are removed.
- Pond's custom Brave search, tool schemas, skill manager, and agent loop are removed.
- `pond skill` delegates to documented Hermes skill commands or is removed.
- Raw JSON `agent_session.json` is not imported into Hermes automatically.
- `pond edit` no longer edits raw agent history.
- `pond compress` must invoke real Hermes compression or fail honestly.
- Arbitrary agent commands no longer execute through `eval` in the active Fish process. Consequently, an agent cannot silently persist Fish-local cwd, variable, alias, or function mutations.
- The Pond 2.x `$version` collision and missing `-q` prompt handling are fixed rather than preserved.

## Session contract

- Hermes owns conversation messages and compression.
- Pond stores only an atomic, mode-`0600` workspace/profile-to-ACP-session mapping.
- Workspace identity is the normalized Git root when available, otherwise normalized cwd.
- Missing/stale Hermes session IDs create a new explicit session; Pond never resumes a different session by fuzzy title.
- `pond forget` detaches the workspace mapping.
- `pond forget --purge` additionally deletes the exact selected-agent session only when the negotiated ACP capability supports deletion; otherwise it fails clearly without touching local mapping state.
- Legacy Pond config and `agent_session.json` remain untouched so the final 2.x rollback ref remains usable.

## Transport gates

Before production migration:

1. Verify the generic ACP SDK handshake and negotiated capabilities.
2. Verify new/load/resume/cancel, cwd binding, streaming, permissions, and stderr/stdout framing against a protocol fixture.
3. Measure cold and warm latency.
4. Verify a public and genuinely zero-tool stateless path.
5. Compare stdin-safe `hermes chat -Q --query-file -` against any one-shot alternative.
6. Run a dedicated Hermes compatibility suite against `hermes acp`; that preset may set `HERMES_ACP_SKIP_CONFIGURED_MCP=1` unless the user explicitly opts into ambient MCP servers. Generic ACP commands receive no Hermes-specific environment variables.
7. If per-keypress startup misses the Ctrl+Space latency budget, use a persistent per-shell ACP process or a lazy user service.

No provider backend is deleted before these gates pass and the corresponding Pond path is covered by tests.

## Rollback

- Untouched 2.x rollback tag: `pre-hermes-rewrite` at `e396421eeceab808fcc806e32bc5a637db275f62`.
- Environment repair is isolated in commit `8a60066`.
- Baseline evidence is in `docs/BASELINE-2.x.md`.
- Legacy configuration/session files are never rewritten or deleted automatically during the opt-in milestones.
- The dual-backend flag is a temporary migration scaffold and is removed for the final 3.0 release.

## Acceptance gates

Pond 3.0 cannot release until:

- Python 3.10–3.14 tests pass.
- Fish syntax and behavioral tests pass.
- macOS, Ubuntu, Fedora, and Arch installation tests pass.
- ACP integration tests cover permission, cancel, resume, workspace isolation, and child cleanup.
- Stateless generation is proven tool-free.
- Ctrl+Space latency is measured and accepted.
- No test or log leaks fixture secrets.
- Every deliberate break above is documented in migration instructions.
