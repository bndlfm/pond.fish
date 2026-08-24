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

## Verified first Fish patch

`patches/fish-command-capture.patch` applies to Fish 4.8.1 and has been independently verified with 3 focused capture tests, the Fish library suite, and a Fish binary build. A PTY check confirmed separate stdout/stderr JSONL records and exit status.

## Current boundary

The patch captures only eligible direct-terminal commands. Pipelines, explicit redirections, non-TTY execution, and unallowlisted/TTY-sensitive commands bypass capture by design. The 129-command policy is embedded directly in the local patch.

## Remaining regression coverage

- pipelines remain unchanged
- explicit redirections remain unchanged
- binary output
- interactive programs and job control
- Ctrl+C and signal status
- background jobs
- capture-disabled path has no output behavior change
