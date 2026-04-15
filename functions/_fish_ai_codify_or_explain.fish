#!/usr/bin/env fish

function _fish_ai_codify_or_explain --description "Transform a command into a comment and vice versa using AI."
    set -f input (commandline --current-buffer | string collect)

    if test -z "$input"
        return
    end

    _fish_ai_show_progress_indicator

    set -l trimmed_input (string trim "$input")
    set -l first_word (string split -m 1 " " -- "$trimmed_input")[1]

    # If it starts with a hash, it's definitely natural language
    if string match -q "# *" "$trimmed_input"
        set -f output (_fish_ai_codify "$input" | string collect)
    # If the first word is a known command, assume it's a command to be explained
    else if type -q "$first_word"
        set -f output (_fish_ai_explain "$input" | string collect)
    # Otherwise, treat it as natural language to be codified
    else
        set -f output (_fish_ai_codify "$input" | string collect)
    end

    commandline --replace "$output"

    commandline -f repaint
end
