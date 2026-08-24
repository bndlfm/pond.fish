# Pond 3 shell initialization and Fisher lifecycle.

if not set -q _pond_install_dir
    set -g _pond_install_dir (test -n "$XDG_DATA_HOME"; and echo "$XDG_DATA_HOME/pond"; or echo "$HOME/.local/share/pond")
end
if not set -q _pond_data_dir
    set -g _pond_data_dir $_pond_install_dir
end
if not set -q _pond_config_path
    set -g _pond_config_path (test -n "$XDG_CONFIG_HOME"; and echo "$XDG_CONFIG_HOME/pond/config.ini"; or echo "$HOME/.config/pond/config.ini")
end

function _pond_bind --description "Register Pond bindings, with Fish-compatible defaults."
    set -l ask_key ctrl-x
    set -l agent_key ctrl-a
    if set -q POND_KEYMAP_CODIFY
        set ask_key "$POND_KEYMAP_CODIFY"
    end
    if set -q POND_KEYMAP_AGENT
        set agent_key "$POND_KEYMAP_AGENT"
    end
    bind -M insert "$ask_key" _pond_codify_or_explain
    bind -M insert "$agent_key" _pond_agent
end

function _pond_record_postexec --on-event fish_postexec --description "Record passive terminal events as JSONL."
    set -l exit_status $status
    if test (count $argv) -eq 0; or not type -q jq
        return
    end
    mkdir -p "$_pond_install_dir"
    set -l command_text (string join ' ' -- $argv)
    set -l timestamp (date -u +%Y-%m-%dT%H:%M:%SZ)
    jq -cn \
        --arg time "$timestamp" \
        --arg command "$command_text" \
        --argjson status $exit_status \
        '{time: $time, command: $command, stdout: null, stderr: null, exit_status: $status, capture: "fish_event_hook"}' \
        >> "$_pond_install_dir/terminal-events.jsonl"
end


function _pond_install --on-event pond_install
    set -l source (set -q POND_PYTHON_SOURCE; and echo "$POND_PYTHON_SOURCE"; or echo "git+https://github.com/bndlfm/pond.fish@feat/pond-3-acp-rewrite")
    mkdir -p "$_pond_install_dir"

    if type -q uv
        uv venv --quiet --clear --python python "$_pond_install_dir"
        or return 1
        uv pip install --quiet --python "$_pond_install_dir/bin/python" "$source"
    else if type -q nix
        nix run nixpkgs#uv -- venv --quiet --clear --python python "$_pond_install_dir"
        or return 1
        nix run nixpkgs#uv -- pip install --quiet --python "$_pond_install_dir/bin/python" "$source"
    else
        echo "Pond requires uv or Nix to install its Python ACP bridge." >&2
        return 1
    end

    fish_add_path --path "$_pond_install_dir/bin"
end

if test -d "$_pond_install_dir/bin"
    fish_add_path --path "$_pond_install_dir/bin"
end

if status is-interactive
    _pond_bind
end
