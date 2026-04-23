##
## Supported major.minor versions of Python.
## Unit tests are run in CI against these versions.
##
set -g _fish_ai_supported_versions 3.10 3.11 3.12 3.13 3.14

set -g _fish_ai_install_dir (test -n "$FISH_AI_INSTALL_DIR"; and echo "$FISH_AI_INSTALL_DIR"; or test -z "$XDG_DATA_HOME"; and echo "$HOME/.local/share/fish-ai"; or echo "$XDG_DATA_HOME/fish-ai")
set -g _fish_ai_config_path (test -n "$FISH_AI_CONFIG_PATH"; and echo "$FISH_AI_CONFIG_PATH"; or test -z "$XDG_CONFIG_HOME"; and echo "$HOME/.config/fish-ai/config.ini"; or echo "$XDG_CONFIG_HOME/fish-ai/config.ini")

##
## This section creates the keybindings for fish-ai. Modify your `config.ini`
## and restart the terminal emulator to change the keybindings from their defaults.
##
function _fish_ai_get_config --description "Get a configuration value quickly using Fish."
    set -l key $argv[1]
    set -l default $argv[2]

    # 1. Environment variables (highest priority)
    set -l env_key "FISH_AI_"(string upper "$key")
    if set -q $env_key
        echo $$env_key
        return 0
    end

    # 2. Config file
    if test -f "$_fish_ai_config_path"
        # Find active configuration section
        set -l active_section (grep -m 1 "^configuration\s*=" "$_fish_ai_config_path" | cut -d'=' -f2 | string trim)
        
        if test -n "$active_section"
            # Try to find key in the active section
            set -l value (sed -n "/^\[$active_section\]/,/^\[/p" "$_fish_ai_config_path" | grep -m 1 "^$key\s*=" | cut -d'=' -f2 | string trim)
            if test -n "$value"
                echo $value
                return 0
            end
        end

        # Fallback to [fish-ai] section or global
        set -l value (grep -m 1 "^$key\s*=" "$_fish_ai_config_path" | cut -d'=' -f2 | string trim)
        if test -n "$value"
            echo $value
            return 0
        end
    end

    # 3. Default value
    if test -n "$default"
        echo "$default"
        return 0
    end

    return 1
end

function _fish_ai_unbind --description "Remove keybindings for fish-ai."
    if test -n "$_fish_ai_keymap_1"
        bind -e -- $_fish_ai_keymap_1
        bind -M insert -e -- $_fish_ai_keymap_1 2>/dev/null
    end
    if test -n "$_fish_ai_keymap_2"
        bind -e -- $_fish_ai_keymap_2
        bind -M insert -e -- $_fish_ai_keymap_2 2>/dev/null
    end
    if test -n "$_fish_ai_keymap_3"
        bind -e -- $_fish_ai_keymap_3
        bind -M insert -e -- $_fish_ai_keymap_3 2>/dev/null
    end
    # Also explicitly unbind the old default Ctrl+P just in case
    bind -e -- \cp 2>/dev/null
    bind -M insert -e -- \cp 2>/dev/null
end

function _fish_ai_bind --description "Create keybindings for fish-ai."
    # Support environment variables for keybindings (useful for Nix/Home Manager)
    set -l key1 (_fish_ai_get_config keymap_1 \ca | string unescape)
    set -l key2 (_fish_ai_get_config keymap_2 ctrl-space | string unescape)
    set -l key3 (_fish_ai_get_config keymap_3 ctrl-x | string unescape)

    # Special handling for ctrl-space which might be NULL or nul
    if test "$key2" = "ctrl-space"
        set key2 nul
    end

    # Always unbind old keys if they were tracked
    _fish_ai_unbind

    # Update global tracking variables for unbind to use next time
    set -g _fish_ai_keymap_1 $key1
    set -g _fish_ai_keymap_2 $key2
    set -g _fish_ai_keymap_3 $key3

    if test "$fish_key_bindings" = fish_vi_key_bindings
        set -g _fish_ai_bind_command bind -M insert
    else
        set -g _fish_ai_bind_command bind
    end

    # Apply bindings to the primary mode (insert in VI, default in Emacs)
    if test -n "$_fish_ai_keymap_1"
        $_fish_ai_bind_command -- $_fish_ai_keymap_1 _fish_ai_codify_or_explain
    end
    if test -n "$_fish_ai_keymap_2"
        $_fish_ai_bind_command -- $_fish_ai_keymap_2 _fish_ai_autocomplete_or_fix
    end
    if test -n "$_fish_ai_keymap_3"
        $_fish_ai_bind_command -- $_fish_ai_keymap_3 _fish_ai_agent
    end

    # For VI users, also bind in default mode for convenience
    if test "$fish_key_bindings" = fish_vi_key_bindings
        if test -n "$_fish_ai_keymap_1"
            bind -M default -- $_fish_ai_keymap_1 _fish_ai_codify_or_explain
        end
        if test -n "$_fish_ai_keymap_2"
            bind -M default -- $_fish_ai_keymap_2 _fish_ai_autocomplete_or_fix
        end
        if test -n "$_fish_ai_keymap_3"
            bind -M default -- $_fish_ai_keymap_3 _fish_ai_agent
        end
    end
end

if status is-interactive
    # If the install dir doesn't exist, try to find it relative to the script
    if not test -d "$_fish_ai_install_dir"
        set -l script_dir (dirname (status filename))
        # If we are in the source tree, the install dir might be .venv
        if test -d "$script_dir/../.venv"
            set -g _fish_ai_install_dir "$script_dir/../.venv"
        end
    end

    # Bind if the install dir exists or if we have the binaries in PATH
    if test -d "$_fish_ai_install_dir"; or type -q pond
        _fish_ai_bind
    end
end

##
## This section contains the plugin lifecycle hooks invoked by the fisher package
## manager.
##
function _fish_ai_install --on-event fish_ai_install
    _fish_ai_set_python_version
    if type -q uv
        echo "🥡 Setting up a virtual environment using uv..."
        uv venv --quiet --seed --python $_fish_ai_python_version "$_fish_ai_install_dir"
    else
        echo "🥡 Setting up a virtual environment using venv..."
        python$_fish_ai_python_version -m venv "$_fish_ai_install_dir"
    end
    if test $status -ne 0
        echo "💔 Installation failed. Check previous terminal output for details."
        return 1
    end

    echo "🍬 Installing dependencies. This may take a few seconds..."
    "$_fish_ai_install_dir/bin/pip" -qq install "$(_fish_ai_get_installation_url)"
    if test $status -ne 0
        echo "💔 Installation from '$(_fish_ai_get_installation_url)' failed. Check previous terminal output for details."
        return 2
    end
    _fish_ai_python_version_check
    _fish_ai_symlink_truststore
    _fish_ai_autoconfig_gh_models
    _fish_ai_bind
    if ! test -f "$_fish_ai_config_path"
        echo "🤗 You must create a configuration file before the plugin can be used!"
    end
end

function _fish_ai_update --on-event fish_ai_update
    # Upgrade to fish-ai 1.9.0
    if test -d "$HOME/.fish-ai"
        echo "👷 Moving installation directory to '$_fish_ai_install_dir'."
        mv "$HOME/.fish-ai" "$_fish_ai_install_dir"
    end
    if test -f "$HOME/.config/fish-ai.ini"
        if test "$_fish_ai_config_path" != "$HOME/.config/fish-ai.ini"
            echo "👷 Moving configuration file to '$_fish_ai_config_path'."
            mkdir -p (dirname "$_fish_ai_config_path")
            mv "$HOME/.config/fish-ai.ini" "$_fish_ai_config_path"
        end
    end
    # Upgrade to fish-ai 2.0.0
    set -l provider (_fish_ai_get_config provider)
    if test "$provider" = huggingface
        echo "🌇 The provider for Hugging Face has been removed. Switch to a different provider."
    end
    # Upgrade to fish-ai 2.8.0
    if test -f "$_fish_ai_config_path"
        if grep -q '^temperature\s*=' "$_fish_ai_config_path"
            sed -i '/^temperature\s*=/d' "$_fish_ai_config_path"
            echo "🌇 The 'temperature' parameter is no longer supported and has been removed from your configuration."
        end
    end
    # Upgrade to fish-ai 2.10.6
    if test "$provider" = cohere
        set -l model (_fish_ai_get_config model)
        if test -z "$model"
            echo "👋 Please specify the Cohere model you want to use in '$_fish_ai_config_path'."
        end
    end

    _fish_ai_set_python_version
    if type -q uv
        uv venv --quiet --clear --seed --python $_fish_ai_python_version "$_fish_ai_install_dir"
    else
        python$_fish_ai_python_version -m venv --upgrade "$_fish_ai_install_dir"
    end
    if test $status -ne 0
        echo "💔 Installation failed. Check previous terminal output for details."
        return 1
    end

    echo "🐍 Now using $($_fish_ai_install_dir/bin/python3 --version)."
    echo "🍬 Upgrading dependencies. This may take a few seconds..."
    $_fish_ai_install_dir/bin/pip install -qq --upgrade "$(_fish_ai_get_installation_url)"
    if test $status -ne 0
        echo "💔 Installation failed. Check previous terminal output for details."
        return 2
    end
    _fish_ai_python_version_check
    _fish_ai_symlink_truststore
    _fish_ai_warn_plaintext_api_keys
end

function _fish_ai_uninstall --on-event fish_ai_uninstall
    _fish_ai_unbind
    if test -d "$_fish_ai_install_dir"
        echo "💣 Nuking the virtual environment..."
        rm -r "$_fish_ai_install_dir"
    end
end

function _fish_ai_set_python_version
    if test -n "$FISH_AI_PYTHON_VERSION"
        echo "🐍 Using Python $FISH_AI_PYTHON_VERSION as specified by the environment variable 'FISH_AI_PYTHON_VERSION'."
        set -g _fish_ai_python_version $FISH_AI_PYTHON_VERSION
    else if type -q uv
        # Use the last supported version of Python
        set -g _fish_ai_python_version $_fish_ai_supported_versions[-1]
    else
        # Use the Python version provided by the system
        set -g _fish_ai_python_version 3
    end
end

function _fish_ai_get_installation_url
    # Try to find the plugin in fisher's list (matches 'fish-ai' or 'pond')
    set -f plugin (fisher list | grep -E 'fish-ai|pond' | head -1)
    if test "$plugin" = ""
        # If we can't find it in the list, check if we're currently in the source directory
        if test -f pyproject.toml; and grep -q 'name = "fish_ai"' pyproject.toml
            echo -n (pwd)
        else
            # Fallback to the original repository as a last resort
            echo -n "fish-ai@git+https://github.com/bndlfm/pond"
        end
    else if test (string sub --start 1 --length 1 "$plugin") = /
        # Install from a local folder
        echo -n "$plugin"
    else
        # Install from GitHub
        echo -n "fish-ai@git+https://github.com/$plugin"
    end
end

function _fish_ai_python_version_check
    set -f current_python_version ("$_fish_ai_install_dir/bin/python3" -c 'import platform; major, minor, _ = platform.python_version_tuple(); print(major, end="."); print(minor, end="")')
    if ! contains $current_python_version $_fish_ai_supported_versions
        echo "🔔 This plugin has not been tested with Python $_fish_ai_python_version and may not function correctly."
        echo "The following versions are supported: $_fish_ai_supported_versions"
        echo "Consider setting the environment variable 'FISH_AI_PYTHON_VERSION' to a supported version and reinstalling the plugin. For example:"
        set_color --italics blue
        echo ""
        echo "  fisher remove bndlfm/pond"
        echo "  set -U FISH_AI_PYTHON_VERSION $_fish_ai_supported_versions[-1]"
        echo "  fisher install bndlfm/pond"
        echo ""
        set_color normal
    end
end

function _fish_ai_symlink_truststore --description "Use the bundle with CA certificates trusted by the OS."
    if test -f /etc/ssl/certs/ca-certificates.crt
        echo "🔑 Symlinking to certificates stored in /etc/ssl/certs/ca-certificates.crt."
        ln -snf /etc/ssl/certs/ca-certificates.crt ("$_fish_ai_install_dir/bin/python3" -c 'import certifi; print(certifi.where())')
    else if test -f /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
        echo "🔑 Symlinking to certificates stored in /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem."
        ln -snf /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem ("$_fish_ai_install_dir/bin/python3" -c 'import certifi; print(certifi.where())')
    else if test -f /etc/ssl/cert.pem
        echo "🔑 Symlinking to certificates stored in /etc/ssl/cert.pem."
        ln -snf /etc/ssl/cert.pem ("$_fish_ai_install_dir/bin/python3" -c 'import certifi; print(certifi.where())')
    end
end

function _fish_ai_warn_plaintext_api_keys --description "Warn about plaintext API keys."
    if ! test -f "$_fish_ai_config_path"
        return
    end
    if grep -q "^api_key" "$_fish_ai_config_path"
        echo -n "🚨 One or more plaintext API keys are stored in "
        set_color --bold red
        echo -n "$_fish_ai_config_path"
        set_color normal
        echo -n ". Consider moving them to your keyring using "
        set_color --italics blue
        echo -n fish_ai_put_api_key
        set_color normal
        echo "."
    end
end

function _fish_ai_autoconfig_gh_models --description "Deploy configuration for GitHub Models."
    if test -f "$_fish_ai_config_path"
        return
    end
    if ! type -q gh
        return
    end
    if test -z (gh auth token 2>/dev/null)
        return
    end
    if test -z (gh ext ls | grep "gh models" 2>/dev/null)
        return
    end
    mkdir -p (dirname "$_fish_ai_config_path")
    echo "[fish-ai]" >>"$_fish_ai_config_path"
    echo "configuration = github" >>"$_fish_ai_config_path"
    echo "" >>"$_fish_ai_config_path"
    echo "[github]" >>"$_fish_ai_config_path"
    echo "provider = self-hosted" >>"$_fish_ai_config_path"
    echo "server = https://models.inference.ai.azure.com" >>"$_fish_ai_config_path"
    echo "api_key = $(gh auth token)" >>"$_fish_ai_config_path"
    echo "model = gpt-4o-mini" >>"$_fish_ai_config_path"

    echo "😺 Access to GitHub Models has been automatically configured for you!"
end

function _fish_ai_show_progress_indicator --description "Show a progress indicator."
    if type -q fish_right_prompt
        set -f rplen (string length -v (fish_right_prompt)[-1])
    else
        set -f rplen 0
    end
    # Get the progress indicator from the configuration, use hourglass emoji if not set
    set -f progress_indicator (_fish_ai_get_config progress_indicator '⏳')
    set -f pilen (string length "$progress_indicator")
    # Move the cursor to the end of the line and insert progress indicator
    tput hpa (math $COLUMNS - $rplen - 1 - $pilen)
    echo -n "$progress_indicator"
end
