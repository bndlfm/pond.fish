#!/usr/bin/env fish

function fish_ai_agent_forget --description "Clear the current agentic loop session state."
    set -l state_file "$_fish_ai_install_dir/agent_session.json"
    if test -f "$state_file"
        rm "$state_file"
        echo "🧹 Agent session cleared."
    else
        echo "ℹ️  No active agent session found."
    end
end

function _fish_ai_agent --description "Run an autonomous agent to achieve a goal."
    set -l goal (commandline --current-buffer | string collect)
    
    set -l state_file "$_fish_ai_install_dir/agent_session.json"
    set -l action_file (mktemp -t fish-ai-action.XXXXXX)
    set -l signal_file (mktemp -t fish-ai-signal.XXXXXX)
    
    if test -z "$goal"; and not test -f "$state_file"
        echo "No goal provided and no active session to resume."
        rm "$action_file" "$signal_file"
        return
    end

    commandline --replace ""
    commandline -f repaint

    if test -n "$goal"
        echo ""
        echo "🤖 Agent received goal: $goal"
    else
        echo ""
        echo "🤖 Resuming agent session..."
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

        # Run agent and process its signals
        set -l response_type ""
        echo -n "" > "$signal_file"

        "$_fish_ai_install_dir/bin/agent" $agent_args | while read -l line
            switch "$line"
                case THOUGHT
                    echo "---"
                    echo "💭 Thought:"
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
                case TOOL_RESULT
                    echo "✅ Result:"
                    set -l result_content ""
                    while read -l result_line
                        if test "$result_line" = "END_RESULT"
                            break
                        end
                        set result_content "$result_content$result_line\n"
                    end
                    # Truncate large tool results for the UI
                    if test (string length "$result_content") -gt 500
                        echo (string sub --length 500 "$result_content")
                        echo "... [Output Truncated]"
                    else
                        echo "$result_content"
                    end
                case EXECUTE CONTINUE CHAT DONE ERROR
                    echo "$line" > "$signal_file"
            end
        end

        set -l response_type (cat "$signal_file" | string trim)
        set -l action_content (cat "$action_file")

        if test -z "$response_type"
            echo "❌ Agent failed to respond."
            break
        end

        switch "$response_type"
            case EXECUTE
                echo "👉 Agent wants to execute: $action_content"
                if test "$confirm_mode" = "ask"
                    read -l -P "Allow? [y]es / [a]lways / [n]o [y/a/n]: " user_choice
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
                
                echo "Executing..."
                set last_output (eval $action_content 2>&1 | string collect)
                set last_status $status
                
                # Show execution output for audit
                echo "✅ Output:"
                if test (string length "$last_output") -gt 500
                    echo (string sub --length 500 "$last_output")
                    echo "... [Output Truncated]"
                else
                    echo "$last_output"
                end
            
            case CONTINUE
                continue

            case CHAT
                echo "💬 Agent Message:"
                cat "$action_file" | "$_fish_ai_install_dir/bin/render"
                read -l -P "Your response (leave empty to continue): " user_response
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
                sleep 5
                break
            
            case '*'
                echo "❓ Unknown response: $response_type"
                sleep 5
                break
        end
    end

    rm "$action_file" "$signal_file"
    commandline -f repaint
end
