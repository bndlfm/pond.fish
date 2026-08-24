# Fish Capture Activation

Pond's local Fish capture patch is applied through the Nix overlay at:

```text
~/.nixcfg/overlays/default.nix
```

The capture path is configured in:

```text
~/.nixcfg/modules/home-manager/shell/fish.home.nix
```

```fish
set -gx FISH_COMMAND_CAPTURE_PATH $HOME/.local/share/pond/terminal-events.jsonl
```

## Activate

Build first without activation:

```fish
nix build ~/.nixcfg#homeConfigurations.'neko@meow'.activationPackage --no-link --no-write-lock-file
```

Activate through the existing Home Manager command:

```fish
hmrb
exec fish
```

Verify the active Fish and capture path:

```fish
readlink -f (command -v fish)
echo $FISH_COMMAND_CAPTURE_PATH
```

Smoke test separate streams and exit status:

```fish
rm -f /tmp/pond-capture.jsonl
printf 'stdout\n' >/tmp/pond-input
FISH_COMMAND_CAPTURE_PATH=/tmp/pond-capture.jsonl \
  script -qefc 'fish -i -c "cat /tmp/pond-input; cat /tmp/pond-missing; exit"' \
  /tmp/pond-typescript >/dev/null
jq -c . /tmp/pond-capture.jsonl
```

## Rollback

Home Manager keeps the previous generation. Use the normal generation switcher, or restore the prior overlay revision in `~/.nixcfg/overlays/default.nix`, then rebuild:

```fish
hmrb
exec fish
```

The patch is opt-in: removing `FISH_COMMAND_CAPTURE_PATH` disables capture without removing the patched Fish binary.

## Current boundaries

Capture applies only to the embedded allowlist and direct terminal stdout/stderr. Pipelines, explicit redirections, non-TTY execution, and unallowlisted/TTY-sensitive commands bypass capture.
