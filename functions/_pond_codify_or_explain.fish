# Statefully submit a configured Pond command-draft or explanation action.
function _pond_codify_or_explain --description "Pond command draft and explanation launcher."
    set -l input (commandline --current-buffer | string collect)
    if test -z "$input"
        return
    end

    set -l trimmed_input (string trim "$input")
    set -l first_word (string split -m 1 " " -- "$trimmed_input")[1]
    if not string match -q "# *" "$trimmed_input"; and type -q "$first_word"
        return
    end

    set -l action_command pond-action
    if not type -q $action_command
        set action_command "$_pond_install_dir/bin/pond-action"
    end
    set -l terminal_context (history --max=20 | string collect)
    set -l output ($action_command command-draft "$input" --cwd (pwd) --terminal-context "$terminal_context" | string collect)
    commandline --replace "$output"
    commandline -f repaint
end
