#!/usr/bin/env fish

function _fish_ai_agent --description "Run an autonomous agent to achieve a goal."
    set -l goal (commandline --current-buffer | string collect)
    if test -z "$goal"
        echo "No goal provided. Please type a goal and press the agent shortcut."
        return
    end

    # Clear commandline
    commandline --replace ""
    commandline -f repaint

    set -l state_file (mktemp)
    set -l action_file (mktemp)
    set -l last_output ""
    set -l last_status 0
    set -l rejected 0
    set -l confirm_mode "ask" # ask, always, deny

    echo "🤖 Agent started with goal: $goal"

    while true
        set -l agent_args --state "$state_file" --action-file "$action_file"
        if test -n "$goal"
            set agent_args $agent_args --goal "$goal"
            set goal ""
        else
            set agent_args $agent_args --last-output "$last_output" --last-status "$last_status"
        end

        if test $rejected -eq 1
            set agent_args $agent_args --rejected
            set rejected 0
        end

        set -l response_type ("$_fish_ai_install_dir/bin/agent" $agent_args)
        set -l action_content (cat "$action_file")

        switch $response_type
            case EXECUTE
                echo "👉 Agent wants to execute: $action_content"
                if test "$confirm_mode" = "ask"
                    read -l -P "Allow? [y]es / [a]lways / [n]o: " user_choice
                    switch $user_choice
                        case a Always always
                            set confirm_mode "always"
                        case n No no
                            set rejected 1
                            continue
                        case y Yes yes ""
                            # Proceed
                        case '*'
                            set rejected 1
                            continue
                    end
                end
                
                # Execute the command
                echo "Executing..."
                set last_output (eval $action_content 2>&1 | string collect)
                set last_status $status
                echo "Output: $last_output"
            
            case CONTINUE
                # Agent executed an internal tool and wants to continue immediately
                continue

            case CHAT
                echo "💬 Agent: $action_content"
                # If it's a chat, the user might want to respond
                read -l -P "Your response (leave empty to continue): " user_response
                if test -n "$user_response"
                    set last_output "$user_response"
                else
                    set last_output "Continue"
                end
                set last_status 0

            case DONE
                echo "✅ Agent finished: $action_content"
                break
            
            case ERROR
                echo "❌ Agent error: $action_content"
                break
            
            case '*'
                echo "❓ Unknown agent response: $response_type"
                if test -n "$action_content"
                    echo "Content: $action_content"
                end
                break
        end
    end

    rm "$state_file" "$action_file"
    commandline -f repaint
end
