# Pond 3.x shell initialization.
#
# This file intentionally performs no installation, network access, or backend
# discovery. It is safe to source repeatedly from an interactive Fish session.

if not set -q _pond_data_dir
    set -g _pond_data_dir (test -n "$XDG_DATA_HOME"; and echo "$XDG_DATA_HOME/pond"; or echo "$HOME/.local/share/pond")
end

if not set -q _pond_config_path
    set -g _pond_config_path (test -n "$XDG_CONFIG_HOME"; and echo "$XDG_CONFIG_HOME/pond/config.ini"; or echo "$HOME/.config/pond/config.ini")
end

# The rewrite bindings are opt-in and intentionally have no default key names.
# Users choose all three key sequences through their environment/configuration.
function _pond_bind --description "Register explicitly configured Pond bindings."
    if not set -q POND_REWRITE; or test "$POND_REWRITE" != 1
        return
    end

    if set -q POND_KEYMAP_CODIFY
        bind "$POND_KEYMAP_CODIFY" _pond_codify_or_explain
    end
    if set -q POND_KEYMAP_COMPLETE
        bind "$POND_KEYMAP_COMPLETE" _pond_autocomplete_or_fix
    end
    if set -q POND_KEYMAP_AGENT
        bind "$POND_KEYMAP_AGENT" _pond_agent
    end
end

if status is-interactive
    _pond_bind
end
