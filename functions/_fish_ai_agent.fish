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

function fish_ai_agent_compress --description "Compress the current agentic loop session history."
    set -l state_file "$_fish_ai_install_dir/agent_session.json"
    if not test -f "$state_file"
        echo "ℹ️  No active agent session to compress."
        return
    end
    
    set -l action_file (mktemp -t fish-ai-action.XXXXXX)
    set -l signal_file (mktemp -t fish-ai-signal.XXXXXX)
    
    echo "🗜️  Compressing session history..."
    "$_fish_ai_install_dir/bin/agent" --state "$state_file" --action-file "$action_file" --compress > /dev/null
    
    rm "$action_file" "$signal_file"
    echo "✅ Compression complete."
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

    set -l cyan (set_color cyan)
    set -l yellow (set_color yellow)
    set -l green (set_color green)
    set -l red (set_color red)
    set -l blue (set_color blue)
    set -l normal (set_color normal)
    set -l bold (set_color --bold)

    if test -n "$goal"
        echo ""
        echo "🤖 "$bold"Agent received goal:"$normal" $goal"
    else
        echo ""
        echo "🤖 "$bold"Resuming agent session..."$normal
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
            
            # On first call, also pass the external history and CWD
            set agent_args $agent_args --cwd (pwd)
            set -l ext_history (history | head -n 20 | string collect)
            if test -n "$ext_history"
                set agent_args $agent_args --external-history "$ext_history"
            end
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

        set -l agent_out (mktemp -t fish-ai-agent-out.XXXXXX)
        "$_fish_ai_install_dir/bin/agent" $agent_args > "$agent_out"
        
        if test $status -ne 0
            rm "$agent_out"
            echo "👋 "$red"Agent session interrupted."$normal
            break
        end

        cat "$agent_out" | while read -l line
            switch "$line"
                case 'STATUS:*'
                    set -l status_msg (string replace "STATUS: " "" "$line")
                    echo "⏳ $status_msg"
                case THOUGHT
                    echo "$blue---$normal"
                    echo "💭 "$blue$bold"Thought:"$normal
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
                    echo "🛠️  "$yellow$bold"Action:"$normal" "$yellow"$call"$normal
                case TOOL_RESULT
                    echo "📋 "$cyan$bold"Result:"$normal
                    set -l result_content ""
                    while read -l result_line
                        if test "$result_line" = "END_RESULT"
                            break
                        end
                        set result_content "$result_content$result_line\n"
                    end
                    if test (string length "$result_content") -gt 500
                        echo (string sub --length 500 "$result_content")
                        echo "$cyan... [Output Truncated]$normal"
                    else
                        echo "$result_content"
                    end
                case EXECUTE CONTINUE CHAT DONE ERROR
                    echo "$line" > "$signal_file"
            end
        end
        rm "$agent_out"

        set -l response_type (cat "$signal_file" | string trim)
        set -l action_content (cat "$action_file")

        if test -z "$response_type"
            echo "❌ "$red"Agent failed to respond."$normal
            break
        end

        switch "$response_type"
            case EXECUTE
                if test "$confirm_mode" = "ask"
                    echo "👉 "$yellow$bold"Agent wants to execute:"$normal" "$bold"$action_content"$normal
                    echo "   ["$green$bold"y"$normal"] Allow once"
                    echo "   ["$cyan$bold"a"$normal"] Always allow for this session"
                    echo "   ["$red$bold"n"$normal"] Deny this command"
                    read -l -P (set_color green)"Allow? [y/a/n]: "(set_color normal) user_choice
                    
                    printf "\033[1A\033[2K\033[1A\033[2K\033[1A\033[2K\033[1A\033[2K\033[1A\033[2K"
                    
                    switch "$user_choice"
                        case a Always always
                            set confirm_mode "always"
                        case n No no
                            set rejected 1
                            echo "❌ "$red"Command denied."$normal
                            continue
                        case y Yes yes ""
                            # Proceed
                        case '*'
                            set rejected 1
                            echo "❌ "$red"Invalid choice."$normal
                            continue
                    end
                end
                
                echo "🛠️  "$yellow$bold"Agent executed:"$normal" "$bold"$action_content"$normal
                set last_output (eval $action_content 2>&1 | string collect)
                set last_status $status
            
            case CONTINUE
                continue

            case CHAT
                echo "💬 "$blue$bold"Agent Message:"$normal
                cat "$action_file" | "$_fish_ai_install_dir/bin/render"
                read -l -P (set_color blue)"Your response (leave empty to continue): "(set_color normal) user_response
                if test -n "$user_response"
                    set last_output "$user_response"
                else
                    set last_output "Continue"
                end
                set last_status 0

            case DONE
                echo "✅ "$green$bold"Goal Achieved:"$normal" "
                cat "$action_file" | "$_fish_ai_install_dir/bin/render"
                break
            
            case ERROR
                echo "❌ "$red$bold"Agent error:"$normal" $action_content"
                sleep 5
                break
            
            case '*'
                echo "❓ "$red"Unknown response:"$normal" $response_type"
                sleep 5
                break
        end
    end

    rm "$action_file" "$signal_file"
    commandline -f repaint
end
