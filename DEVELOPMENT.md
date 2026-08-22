# Development

Pond is a Fish-shell interface for a stateful ACP agent. Read [the stateful interaction design](docs/STATEFUL-ACP-INTERACTION-DESIGN.md) and [the rewrite contract](docs/HERMES-REWRITE-CONTRACT.md) before changing runtime behavior.

## Local development

```fish
nix develop
.venv/bin/python -m pytest
fish -n conf.d/*.fish functions/*.fish completions/*.fish
```

The Nix shell creates a project-local virtual environment when needed and installs Pond in editable mode.

## Local Fisher smoke test

```fish
fisher install .
pond help
```

## Commit messages

Use conventional commits. Keep every completed sprint as one local commit with its tests and docs; do not push unless Neko explicitly asks.

## Release

A release tag is created only after the final acceptance evidence is reviewed. The current package version lives in `pyproject.toml`.
