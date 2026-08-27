# Statefully submit the current command buffer as a Pond agent goal.
function _pond_agent --description "Pond stateful agent launcher."
    set -l goal (commandline --current-buffer | string collect | string trim)
    if test -z "$goal"
        return
    end

    set -l action_command pond-action
    if not type -q $action_command
        set action_command "$_pond_install_dir/bin/pond-action"
    end
    set -l terminal_context (history --max=20 | string collect)
    $action_command agent "$goal" --cwd (pwd) --terminal-context "$terminal_context"
    set -l action_status $status
    if test $action_status -ne 0
        printf "Pond agent failed (exit %s); prompt preserved.\n" $action_status >&2
        commandline -f repaint
        return $action_status
    end
    commandline --replace ""
    commandline -f repaint
end
