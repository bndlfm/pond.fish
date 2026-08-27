# Pond 3 shell initialization and Fisher lifecycle.

# Remove the pre-unified legacy writer if this shell was started before Pond was updated.
functions --erase _pond_record_postexec 2>/dev/null

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
    # Bind raw control sequences in both maps; this avoids key-name fallthrough in vi mode.
    bind -M insert \ca _pond_agent
    bind -M default \ca _pond_agent
    bind -M insert \cx _pond_codify_or_explain
    bind -M default \cx _pond_codify_or_explain
end

function _pond_setup_python --description "Install or refresh Pond's private Python backend."
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

function _pond_install --on-event pond_install
    _pond_setup_python
end

function _pond_update --on-event pond_update
    _pond_setup_python
end

if test -d "$_pond_install_dir/bin"
    fish_add_path --path "$_pond_install_dir/bin"
end

if status is-interactive
    _pond_bind
end
