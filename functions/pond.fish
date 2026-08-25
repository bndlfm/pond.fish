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

    set -l forget_command pond-forget
    set -l status_command pond-status
    set -l context_command pond-context
    set -l compress_command pond-compress
    if not type -q $forget_command
        set forget_command "$_pond_install_dir/bin/pond-forget"
        set status_command "$_pond_install_dir/bin/pond-status"
        set context_command "$_pond_install_dir/bin/pond-context"
        set compress_command "$_pond_install_dir/bin/pond-compress"
    end

    switch "$action"
        case forget
            $forget_command --cwd (pwd)
            if status is-interactive
                commandline --replace ""
                commandline -f repaint
            end
        case status
            $status_command --cwd (pwd)
        case context
            $context_command --cwd (pwd)
        case compress
            $compress_command --cwd (pwd)
        case version -v --version
            echo "pond v3.0.0.dev2"
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
