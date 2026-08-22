# Stateless Provider Evaluation — Hermes 0.20.4

Evaluated 2026-08-22 00:13 CDT against the local Hermes Agent `0.20.4` installation.

## Decision

**Do not make Hermes the default Pond stateless provider yet.**

Pond remains opt-in for stateless generation through `POND_STATELESS_COMMAND_JSON` until Hermes exposes a stable, public no-tools stdin-to-stdout interface that satisfies Pond's contract.

## Candidate A: `hermes chat -Q --query-file -`

Command evaluated:

```sh
printf '%s' 'Reply with exactly POND_OK. Do not use tools.' |
  hermes chat -Q --query-file - --source tool --ignore-rules \
    -t context_engine --max-turns 1 --in /home/neko/Projects/pond
```

Observed:

| Property | Result |
| --- | --- |
| Final response on stdout | Yes: `POND_OK` |
| Diagnostics/session ID on stderr | Yes |
| Arbitrary input through stdin | Yes |
| Durable session row | Yes (`session_id` emitted) |
| Tool safety | `context_engine` currently resolves without active tools, but this is not a dedicated public no-tools guarantee |
| Configuration isolation | `--ignore-rules` works, but startup still reported deprecated user `.env` settings on stderr |

This candidate is good for arbitrary text transport, but its persistent-session side effect and reliance on a toolset configuration are wrong for a fast, stateless command-buffer feature.

## Candidate B: `hermes -z`

Command evaluated:

```sh
hermes --ignore-rules -t context_engine -z 'Reply with exactly POND_OK. Do not use tools.'
```

Observed:

| Property | Result |
| --- | --- |
| Final response on stdout | Yes: `POND_OK` |
| stderr chatter | None in this run |
| Input transport | Prompt is argv, not stdin |
| Tool safety | Same non-contractual `context_engine` assumption |
| Approval model | One-shot mode automatically enables YOLO/approval bypass behavior |

This candidate has clean output, but the argv input transport and approval semantics make it unsuitable as Pond's default while no-tools isolation depends on an implementation detail.

## Required upstream/public contract before enabling a default

Pond needs all of the following:

1. A documented public no-tools mode, not merely a currently empty toolset.
2. Arbitrary prompt input via stdin or another non-argv channel.
3. Clean final stdout, with diagnostics only on stderr.
4. No durable session creation for stateless work.
5. No automatic approval/hook bypass that could become unsafe if tools are later exposed.

Until then, users may provide an explicitly trusted `POND_STATELESS_COMMAND_JSON` provider. Pond will not silently substitute Hermes or grant it tools.
