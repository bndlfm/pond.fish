# Pond 2.x Pre-Hermes Baseline

Captured on 2026-08-21 before the Hermes backend rewrite.

## Reproducibility boundary

- Rollback tag: `pre-hermes-rewrite`
- Rollback commit: `e396421eeceab808fcc806e32bc5a637db275f62`
- Environment-repair commit: `8a60066` (`fix: recreate stale Nix development venv`)
- Product version: `2.11.1`
- Branch at capture: `main`

The rollback tag intentionally predates the Nix development-shell repair. No provider credentials or user configuration are part of this baseline.

## Development environment

Entered with:

```sh
nix develop --no-write-lock-file
```

Resolved tools inside the shell:

| Tool | Version |
| --- | --- |
| Python | 3.11.15 |
| Fish | 4.6.0 |
| uv | 0.11.4 |
| Nix (host) | 2.34.8 |

The shell hook recreates `.venv` when `.venv/bin/python` is absent or not executable. This avoids retaining a venv whose interpreter was garbage-collected from the Nix store.

## Python tests

Command:

```sh
nix develop --no-write-lock-file -c bash -lc \
  '.venv/bin/python -m pytest'
```

Result:

```text
24 passed in 0.54s
```

Coverage command:

```sh
nix develop --no-write-lock-file -c bash -lc \
  '.venv/bin/python -m coverage erase; \
   .venv/bin/python -m coverage run --branch \
     --include="src/fish_ai/*.py" -m pytest; \
   .venv/bin/python -m coverage report'
```

Result:

```text
24 passed in 1.99s
TOTAL: 1068 statements, 546 missed, 400 branches, 40 partial, 43% coverage
```

Low-coverage migration hotspots:

| Module | Coverage |
| --- | ---: |
| `src/fish_ai/agent.py` | 8% |
| `src/fish_ai/engine.py` | 26% |
| `src/fish_ai/config.py` | 46% |
| `src/fish_ai/autocomplete.py` | 62% |

These numbers confirm that the custom agent loop, provider engine, and configuration paths require characterization before removal.

## Fish syntax

Command:

```sh
fish -n conf.d/*.fish functions/*.fish completions/*.fish
```

Result: pass.

This is syntax validation only. The pre-rewrite repository has no automated Fish behavioral suite for keybindings, command-buffer mutation, installation hooks, or the `pond` facade.

## Package build

Command:

```sh
nix develop --no-write-lock-file -c bash -lc \
  'uv build --out-dir /tmp/pond-baseline-dist'
```

Artifacts:

```text
fish_ai-2.11.1.tar.gz
fish_ai-2.11.1-py3-none-any.whl
```

Result: pass, with a pre-existing setuptools warning that the MIT license classifier is deprecated in favor of an SPDX license expression.

## Local process-overhead measurements

Ten warm filesystem-cache runs per command; these are local startup/import costs, not provider latency.

| Operation | Median | Min | Max |
| --- | ---: | ---: | ---: |
| `fish --no-config -c true` | 2.56 ms | 2.30 ms | 2.91 ms |
| `.venv/bin/python -c pass` | 11.55 ms | 10.81 ms | 12.00 ms |
| import `fish_ai.autocomplete` | 60.87 ms | 59.32 ms | 63.33 ms |
| import `fish_ai.agent` | 29.47 ms | 29.04 ms | 30.40 ms |

End-to-end codify/autocomplete/agent latency was not recorded because that would depend on live provider credentials, network state, and model choice. The Hermes transport spike must report its local overhead separately and must not regress interactive Ctrl+Space latency without an explicit product decision.

## Existing CI contract

- Python matrix: 3.10, 3.11, 3.12, 3.13, 3.14.
- Python CI command: coverage-wrapped pytest.
- Installation matrix: macOS 15 plus Arch Linux, Ubuntu, and Fedora containers.
- Installation tests exercise Fisher installation but do not currently test Fish widget behavior.

## Known pre-rewrite behavior and defects

- `fix` can replay the previous failed command to collect output, which may repeat side effects.
- `compress` reports success without a proven session-compression implementation.
- The Fish-side agent executes approved actions using `eval` in the active shell, allowing cwd, function, and variable mutation.
- Pond owns provider credentials/configuration, model SDKs, web search, skills, tools, approvals, and JSON session state.
- Stateless outputs are inserted into the command buffer; they must remain non-executing in the rewrite.
- Outbound secret redaction is a privacy invariant and must be characterized before provider dispatch is removed.

## Baseline gaps to close before backend replacement

1. Add Fish behavioral tests for Ctrl+Q, Ctrl+Space, Ctrl+A, and `pond` subcommands.
2. Characterize stdout, stderr, stdin, exit codes, and `--json` behavior.
3. Freeze secret-redaction behavior around actual request construction.
4. Freeze approval fail-closed behavior.
5. Record the intended 3.0 breaks, especially removal of active-shell arbitrary `eval` and legacy provider configuration.
