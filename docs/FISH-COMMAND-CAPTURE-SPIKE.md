# Fish Command Capture Spike

## Finding

Fish 4.8.1 emits `fish_preexec` before `reader_run_command()` and `fish_postexec` afterward. Those events provide the command line and status timing, but not stdout/stderr.

External commands are launched through `src/exec.rs` with their stdout/stderr resolved from the job `IoChain`. A plugin cannot retroactively capture those bytes after `fish_postexec`; they have already been written directly to the terminal or an explicit redirection.

## Safe partial implementation

Pond's `conf.d/pond.fish` records opt-in passive JSONL metadata at `fish_postexec`:

```json
{"time":"...","command":"git status","stdout":null,"stderr":null,"exit_status":0,"capture":"fish_event_hook"}
```

This is honest about unavailable streams and does not alter command behavior.

## Reliable stdout/stderr capture options

A complete implementation must choose one of:

1. Patch Fish's job I/O construction to tee non-interactive stdout/stderr while preserving the original terminal/redirect semantics.
2. Add an opt-in PTY wrapper mode that launches commands inside a managed pseudo-terminal and records the PTY stream.
3. Require commands to run through an explicit `pond run -- ...` wrapper.

A plain Fish plugin cannot provide transparent, reliable capture for arbitrary external commands without one of those mechanisms.

## Required regression coverage before a Fish patch

- ordinary stdout and stderr
- pipelines
- explicit redirections
- binary output
- interactive programs and job control
- Ctrl+C and signal status
- background jobs
- capture disabled path has no measurable output behavior change
