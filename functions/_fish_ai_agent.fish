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

    echo ""
    echo "🤖 Agent started with goal: $goal"

    set -l state_file (mktemp -t fish-ai-state.XXXXXX)
    set -l action_file (mktemp -t fish-ai-action.XXXXXX)
    set -l signal_file (mktemp -t fish-ai-signal.XXXXXX)
    
    if test $status -ne 0
        echo "❌ Failed to create temporary files."
        return 1
    end

    set -l last_output ""
    set -l last_status 0
    set -l rejected 0
    set -l confirm_mode "ask" # ask, always, deny

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

        # Run agent and process its stdout line by line
        set -l response_type ""
        echo -n "" > "$signal_file"

        "$_fish_ai_install_dir/bin/agent" $agent_args | while read -l line
            switch "$line"
                case THOUGHT
                    echo "---"
                    echo "💭 Agent Thought:"
                    set -l thought_content ""
                    while read -l thought_line
                        if test "$thought_line" = "END_THOUGHT"
                            break
                        end
                        set thought_content "$thought_content$thought_line\n"
                    end
                    echo -e "$thought_content" | "$_fish_ai_install_dir/bin/render"
                case 'TOOL_CALL:*'
                    set -l call (string replace "TOOL_CALL: " "" "$line")
                    echo "🛠️  Action: $call"
                case EXECUTE CONTINUE CHAT DONE ERROR
                    echo "$line" > "$signal_file"
                case '*'
                    # Ignore other output
            end
        end

        set -l response_type (cat "$signal_file" | string trim)
        set -l action_content (cat "$action_file")

        if test -z "$response_type"
            echo "❌ Agent failed to respond."
            if test -n "$action_content"
                echo "Error context: $action_content"
            end
            break
        end

        switch "$response_type"
            case EXECUTE
                echo "👉 Agent wants to execute: $action_content"
                if test "$confirm_mode" = "ask"
                    echo -n "Allow? [y]es / [a]lways / [n]o: "
                    read -l user_choice
                    switch "$user_choice"
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
                echo "💬 Agent Message:"
                cat "$action_file" | "$_fish_ai_install_dir/bin/render"
                # If it's a chat, the user might want to respond
                echo -n "Your response (leave empty to continue): "
                read -l user_response
                if test -n "$user_response"
                    set last_output "$user_response"
                else
                    set last_output "Continue"
                end
                set last_status 0

            case DONE
                echo "✅ Goal Achieved:"
                cat "$action_file" | "$_fish_ai_install_dir/bin/render"
                break
            
            case ERROR
                echo "❌ Agent error: $action_content"
                echo "Wait 5 seconds for debugging..."
                sleep 5
                break
            
            case '*'
                echo "❓ Unknown agent response: $response_type"
                if test -n "$action_content"
                    echo "Content: $action_content"
                end
                echo "Wait 5 seconds for debugging..."
                sleep 5
                break
        end
    end

    rm "$state_file" "$action_file" "$signal_file"
    commandline -f repaint
end
