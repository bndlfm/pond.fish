#!/usr/bin/env fish

function pond --description "Main control command for the pond AI plugin."
    set -l subcommand $argv[1]
    set -l remaining_args $argv[2..-1]

    switch "$subcommand"
        case agent -a
            set -l action $remaining_args[1]
            switch "$action"
                case forget
                    set -l state_file "$_fish_ai_install_dir/agent_session.json"
                    if test -f "$state_file"
                        rm "$state_file"
                        echo "🧹 Agent session cleared."
                    else
                        echo "ℹ️  No active agent session found."
                    end
                case compress
                    set -l state_file "$_fish_ai_install_dir/agent_session.json"
                    if not test -f "$state_file"
                        echo "ℹ️  No active agent session to compress."
                        return
                    end
                    set -l action_file (mktemp -t fish-ai-action.XXXXXX)
                    echo "🗜️  Compressing session history..."
                    "$_fish_ai_install_dir/bin/agent" --state "$state_file" --action-file "$action_file" --compress > /dev/null
                    rm "$action_file"
                    echo "✅ Compression complete."
                case '*'
                    # If no action or unrecognized action, trigger the agent loop with the remaining args as goal
                    if test -n "$remaining_args"
                        # Set the commandline and call the agent function
                        commandline -r "$remaining_args"
                        _fish_ai_agent
                    else
                        # Just trigger agent (resumes session)
                        _fish_ai_agent
                    end
            end
        case forget
            # Shortcut for agent forget
            pond agent forget
        case compress
            # Shortcut for agent compress
            pond agent compress
        case help -h --help
            echo "Usage: pond agent [forget|compress|<goal>]"
            echo "       pond forget"
            echo "       pond compress"
        case '*'
            echo "❓ Unknown subcommand: $subcommand"
            echo "Try 'pond help' for usage."
            return 1
    end
end
