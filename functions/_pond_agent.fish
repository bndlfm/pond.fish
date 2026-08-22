# Statefully submit the current command buffer as a Pond agent goal.
function _pond_agent --description "Pond stateful agent launcher."
    set -l goal (commandline --current-buffer | string collect | string trim)
    if test -z "$goal"
        return
    end

    pond-action agent "$goal" --cwd (pwd)
    commandline --replace ""
    commandline -f repaint
end
