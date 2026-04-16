#!/usr/bin/env fish

function pond --description "The master command for the pond AI suite."
    set -l subcommand $argv[1]
    set -l remaining_args $argv[2..-1]

    # Helper for colored output
    set -l blue (set_color blue)
    set -l cyan (set_color cyan)
    set -l yellow (set_color yellow)
    set -l green (set_color green)
    set -l red (set_color red)
    set -l bold (set_color --bold)
    set -l normal (set_color normal)

    switch "$subcommand"
        case agent -a
            set -l action "$remaining_args[1]"
            set -l state_file "$_fish_ai_install_dir/agent_session.json"

            switch "$action"
                case forget clear
                    if test -f "$state_file"
                        rm "$state_file"
                        echo "🧹 "$green"Agent session cleared."$normal
                    else
                        echo "ℹ️  No active agent session found."
                    end

                case compress
                    if not test -f "$state_file"
                        echo "ℹ️  No active agent session to compress."
                        return
                    end
                    set -l action_file (mktemp -t fish-ai-action.XXXXXX)
                    echo "🗜️  "$cyan"Compressing session history..."$normal
                    "$_fish_ai_install_dir/bin/agent" --state "$state_file" --action-file "$action_file" --compress > /dev/null
                    rm "$action_file"
                    echo "✅ "$green"Compression complete."$normal

                case status
                    if not test -f "$state_file"
                        echo "ℹ️  "$yellow"No active agent session."$normal
                        return
                    end
                    set -l size (du -h "$state_file" | cut -f1)
                    set -l turns (grep -c '"role":' "$state_file")
                    echo "🤖 "$bold"Agent Session Status:"$normal
                    echo "  - File: $state_file"
                    echo "  - Size: $size"
                    echo "  - Message turns: $turns"

                case '*'
                    # If remaining_args is empty, just trigger agent (resumes)
                    # If not empty, it's a new goal
                    if test -n "$remaining_args"
                        commandline -r "$remaining_args"
                    end
                    _fish_ai_agent
            end

        case ai
            # General stateless query (supports piping)
            "$_fish_ai_install_dir/bin/ai" $remaining_args

        case forget
            pond agent forget
        case compress
            pond agent compress
        case status
            pond agent status

        case version -v --version
            set -l version "2.11.1" # Hardcoded for speed, matches pyproject.toml
            echo "🐟 "$bold"pond"$normal" v$version"

        case help -h --help
            echo "🐟 "$blue$bold"pond: AI-Powered Fish Shell Suite"$normal
            echo ""
            echo "Usage: pond <command> [arguments]"
            echo ""
            echo "$bold""Agent Commands:""$normal"
            echo "  agent, -a <goal>    Trigger the autonomous agent"
            echo "  agent forget        Clear the agent's session memory"
            echo "  agent compress      Summarize long conversation history"
            echo "  agent status        Show current session statistics"
            echo ""
            echo "$bold""Stateless Commands:""$normal"
            echo "  ai <prompt>         Run a one-off query (supports piping)"
            echo "  pond <prompt>       Shortcut for 'ai' query"
            echo ""
            echo "$bold""General Commands:""$normal"
            echo "  version, -v         Display version information"
            echo "  help, -h            Show this help message"
            echo ""
            echo "$bold""Examples:""$normal"
            echo "  cat logs.txt | pond ai \"find errors\""
            echo "  pond agent \"organize my downloads folder\""
            echo "  pond \"how do I use the 'find' command?\""

        case '*'
            if test -z "$subcommand"
                pond help
            else
                # Default to stateless query if subcommand is unknown
                "$_fish_ai_install_dir/bin/ai" $argv
            end
    end
end
