#!/usr/bin/env fish

function _fish_ai_autocomplete --description "Autocomplete a command using AI." --argument-names command cursor_position
    if test (_fish_ai_get_config debug) = True

        set -f selected_completion ("$_fish_ai_install_dir/bin/autocomplete" "$command" "$cursor_position" | \
            string collect)
    else
        set -f selected_completion ("$_fish_ai_install_dir/bin/autocomplete" "$command" "$cursor_position" | \
            string collect 2> /dev/null)
    end
    printf '%s' "$selected_completion"
end
