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

    set -l output (pond-action command-draft "$input" --cwd (pwd) | string collect)
    commandline --replace "$output"
    commandline -f repaint
end
