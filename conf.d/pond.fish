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
