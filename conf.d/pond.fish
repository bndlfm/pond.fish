# Pond shell initialization. Safe to source repeatedly: no network access,
# environment creation, backend discovery, or default key sequences.

if not set -q _pond_data_dir
    set -g _pond_data_dir (test -n "$XDG_DATA_HOME"; and echo "$XDG_DATA_HOME/pond"; or echo "$HOME/.local/share/pond")
end

if not set -q _pond_config_path
    set -g _pond_config_path (test -n "$XDG_CONFIG_HOME"; and echo "$XDG_CONFIG_HOME/pond/config.ini"; or echo "$HOME/.config/pond/config.ini")
end

function _pond_bind --description "Register explicitly configured Pond bindings."
    if set -q POND_KEYMAP_CODIFY
        bind "$POND_KEYMAP_CODIFY" _pond_codify_or_explain
    end
    if set -q POND_KEYMAP_AGENT
        bind "$POND_KEYMAP_AGENT" _pond_agent
    end
end

if status is-interactive
    _pond_bind
end
