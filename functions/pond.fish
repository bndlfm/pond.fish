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
                        commandline -r "$remaining_args"
                        _fish_ai_agent
                    else
                        _fish_ai_agent
                    end
            end
        case ai q query ask
            # General stateless query (pipeable)
            "$_fish_ai_install_dir/bin/ai" $remaining_args
        case forget
            pond agent forget
        case compress
            pond agent compress
        case help -h --help
            echo "Usage: pond <command> [args]"
            echo ""
            echo "Commands:"
            echo "  agent, -a    Run or manage the autonomous agent"
            echo "  ai, q, ask   Run a stateless query (supports piping)"
            echo "  forget       Clear the agent's session memory"
            echo "  compress     Summarize long agent history"
            echo ""
            echo "Examples:"
            echo "  pond agent \"fix the tests\""
            echo "  cat logs.txt | pond ai \"find errors\""
            echo "  pond \"how do I extract a tar file?\""
        case '*'
            if test -z "$subcommand"
                pond help
            else
                # Default to stateless query for anything else
                "$_fish_ai_install_dir/bin/ai" $argv
            end
    end
end
