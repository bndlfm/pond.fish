# FUTURE IDEAS

## Lightweight inline collapsible transcript

Build a persistent, Fish-native Pond transcript renderer without modifying Fish source code or requiring a full-screen TUI.

### Desired behavior

- Keep completed tool/skill calls in a structured transcript.
- Collapse older turns after a quiet period into compact summaries such as:
  ```text
  … 7 tools · 2 skills · 1m 42s
  ```
- Keep the active response expanded.
- Re-expand a collapsed turn with a Fish keybinding, for example:
  ```text
  Ctrl-O        expand/collapse previous turn
  Ctrl-Shift-O  expand/collapse all tool detail
  ```
- Preserve Pond 2’s compact visual language and Rich rendering.

### Nix override and non-Nix Fish patch for stdout/stderr capture

Investigate an opt-in Fish runtime patch that writes complete command records as JSONL, including command text, timestamps, exit status, stdout, and stderr.

- **Nix users:** provide a declarative Fish overlay/override applying `patches/fish-command-capture.patch`.
- **Non-Nix users:** provide the same source patch plus standard Fish build instructions, and eventually a portable patched Fish release if the patch proves stable.
- **Default behavior:** capture disabled unless `FISH_COMMAND_CAPTURE_PATH` is set.
- **Compatibility requirements:** preserve pipelines, binary output, interactive programs, redirections, job control, TTY behavior, and normal performance when disabled.

This would provide reliable stdout/stderr capture without forcing Pond to own the entire shell PTY.

### Proposed architecture

```text
Fish keybindings
    ↓
Pond inline transcript helper
    ↓
Hermes persistent backend
```

The helper would communicate with Fish through a local pipe or socket, retain structured turns, and redraw only Pond-owned output. Fish itself would not need modification.

### Scope estimates

- Minimal version: approximately 1 sprint and 300–600 lines of Python/Fish integration. Collapse/expand occurs after an agent turn returns to the prompt.
- Full live version: approximately 2–4 sprints and 600–1,000+ lines. This would support live streaming, terminal resize, ANSI cursor management, background lifecycle, reconnects, and hotkeys while an agent is active.

### Recommended starting point

Implement the minimal post-turn version first. It preserves the Fish-native feel without turning Pond into a full-screen TUI and leaves room for live collapse/expand later.
