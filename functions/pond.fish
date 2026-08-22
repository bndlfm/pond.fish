#!/usr/bin/env fish

function pond --description "Stateful ACP shell interface for Pond."
    set -l action $argv[1]
    set -l remaining $argv[2..-1]

    if contains -- -q $argv
        echo "pond -q was removed; use an explicit stateful Pond action instead." >&2
        return 2
    end

    if contains -- -a $argv
        set -l goal (string join ' ' $remaining)
        if test -n "$goal"
            commandline --replace "$goal"
        end
        _pond_agent
        return
    end

    switch "$action"
        case forget
            pond-forget --cwd (pwd)
        case status
            pond-status --cwd (pwd)
        case context
            pond-context --cwd (pwd)
        case compress
            pond-compress --cwd (pwd)
        case version -v --version
            echo "pond v3.0.0.dev0"
        case help -h --help ''
            echo "Pond — stateful ACP shell interface"
            echo ""
            echo "Usage: pond -a <goal> | pond <command>"
            echo ""
            echo "Commands:"
            echo "  status     Show the local workspace ACP session"
            echo "  context    Show harness context usage and compression status"
            echo "  compress   Explicitly request harness context compression"
            echo "  forget     Detach this workspace from its ACP session"
            echo "  version    Show Pond version"
        case '*'
            echo "Unknown Pond command: $action" >&2
            echo "Use 'pond help' to see supported stateful actions." >&2
            return 2
    end
end
