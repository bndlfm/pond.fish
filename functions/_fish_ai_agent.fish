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
    
    echo "🗜️  Compressing session history..."
    "$_fish_ai_install_dir/bin/agent" --state "$state_file" --action-file "$action_file" --compress > /dev/null
    
    rm "$action_file"
    echo "✅ Compression complete."
end

function _fish_ai_agent --description "Run an autonomous agent to achieve a goal."
    function __fish_ai_agent_cleanup --on-event fish_cancel
        # This function is triggered when ctrl-c is pressed in fish
        set -g _fish_ai_agent_interrupted 1
    end
    set -g _fish_ai_agent_interrupted 0

    set -l start_time (date +%s%3N)
    set -l goal (commandline --current-buffer | string collect | string trim)
    set goal (string replace -r '^#\s*' '' "$goal")
    
    set -l state_file "$_fish_ai_install_dir/agent_session.json"
    set -l action_file (mktemp -t fish-ai-action.XXXXXX)
    set -l signal_file (mktemp -t fish-ai-signal.XXXXXX)
    set -l history_file (mktemp -t fish-ai-history.XXXXXX)
    
    if test -z "$goal"; and not test -f "$state_file"
        echo "No goal provided and no active session to resume." >&2
        rm "$action_file" "$signal_file" "$history_file"
        return
    end

    # Clear current commandline but don't repaint yet
    commandline --replace ""

    set -l cyan (set_color cyan)
    set -l yellow (set_color yellow)
    set -l green (set_color green)
    set -l red (set_color red)
    set -l blue (set_color blue)
    set -l magenta (set_color magenta)
    set -l normal (set_color normal)
    set -l bold (set_color --bold)

    set -l end_time (date +%s%3N)
    set -l duration (math "($end_time - $start_time) / 1000.0")
    if test -n "$goal"
        echo "" >&2
        echo "🤖 "$bold"Agent received goal ($duration""s):"$normal" $goal" >&2
    else
        echo "" >&2
        echo "🤖 Resuming agent session ($duration""s)..." >&2
    end

    set -l last_output ""
    set -l last_status 0
    set -l rejected 0
    set -l confirm_mode "ask" # ask, always, turn, deny

    # Pre-cache configuration
    set -l config_whitelist (_fish_ai_get_config whitelist "ls,grep,find,cat,pwd,date,eza,fd,rg,ripgrep")
    set -l whitelist (string split "," "$config_whitelist")
    set -l trimmed_whitelist
    for cmd in $whitelist
        set trimmed_whitelist $trimmed_whitelist (string trim $cmd)
    end

    while true
        if test $_fish_ai_agent_interrupted -eq 1
            echo "👋 "$red"Agent session interrupted."$normal >&2
            break
        end

        set -l agent_args --state "$state_file" --action-file "$action_file"
        if test -n "$goal"
            set agent_args $agent_args --goal "$goal"
            set goal ""
            set agent_args $agent_args --cwd (pwd)
            history | head -n 20 > "$history_file"
            if test -s "$history_file"
                set agent_args $agent_args --history-file "$history_file"
            end
        else
            set agent_args $agent_args --last-output "$last_output" --last-status "$last_status"
        end

        if test $rejected -eq 1
            set agent_args $agent_args --rejected
            set rejected 0
        end

        set -l response_type ""
        echo -n "" > "$signal_file"

        # Execute agent and capture its output reliably
        set -l agent_out (mktemp -t fish-ai-agent-out.XXXXXX)
        "$_fish_ai_install_dir/bin/agent" $agent_args > "$agent_out" 2>&1
        
        # Check if the agent crashed or was interrupted
        set -l agent_status $status
        if test $agent_status -ne 0
            if test $agent_status -eq 130
                echo "👋 "$red"Agent session interrupted."$normal >&2
            else
                echo "❌ "$red"Agent crashed with status $agent_status."$normal >&2
                echo "Error details:" >&2
                cat "$agent_out" >&2
                echo "" >&2
                echo "Press any key to return to shell..." >&2
                read -n 1
            end
            rm "$agent_out" "$action_file" "$signal_file"
            commandline -f repaint
            return
        end

        # Process the captured output
        cat "$agent_out" | while read -l line
            switch "$line"
                case 'STATUS:*'
                    set -l status_msg (string replace "STATUS: " "" "$line")
                    echo "⏳ $status_msg" >&2
                case THOUGHT
                    echo "$blue---$normal" >&2
                    echo "💭 "$blue$bold"Thought:"$normal >&2
                    set -l thought_content ""
                    while read -l thought_line
                        if test "$thought_line" = "END_THOUGHT"
                            break
                        end
                        set thought_content "$thought_content$thought_line\n"
                    end
                    echo -e "$thought_content" | "$_fish_ai_install_dir/bin/render" >&2
                case 'TOOL_CALL:*'
                    set -l call (string replace "TOOL_CALL: " "" "$line")
                    echo "🛠️  "$yellow$bold"Action: $call"$normal >&2
                case 'SKILL_ACTIVATE:*'
                    set -l skill (string replace "SKILL_ACTIVATE: " "" "$line")
                    echo "🔌 "$magenta$bold"Activating Skill: $skill"$normal >&2
                case TOOL_RESULT
                    echo "📋 "$cyan$bold"Result:"$normal" " >&2
                    set -l result_content ""
                    while read -l result_line
                        if test "$result_line" = "END_RESULT"
                            break
                        end
                        set result_content "$result_content$result_line\n"
                    end
                    if test (string length "$result_content") -gt 0
                        echo -e "$result_content" | head -n 4 >&2
                        if test (echo -e "$result_content" | wc -l) -gt 4
                            echo "$cyan... [Output Truncated]$normal" >&2
                        end
                    end
                    echo "" >&2
                case EXECUTE CONTINUE CHAT DONE ERROR
                    echo "$line" > "$signal_file"
                case 'DEBUG:*' 'USAGE:*'
                    # Silence but potentially log if needed
            end
        end
        rm "$agent_out"

        set -l response_type (cat "$signal_file" | string trim)
        set -l action_content (cat "$action_file")

        if test -z "$response_type"
            echo "❌ "$red"Agent failed to respond."$normal >&2
            break
        end

        switch "$response_type"
            case EXECUTE
                set -l first_word (string split -m 1 " " -- "$action_content")[1]
                set -l is_whitelisted 0
                if not string match -rq '[>|;&]' "$action_content"
                    if contains "$first_word" $trimmed_whitelist
                        set is_whitelisted 1
                    end
                end

                if test "$confirm_mode" = "ask" -a $is_whitelisted -eq 0
                    echo "👉 "$yellow$bold"Agent wants to execute:"$normal" "$bold"$action_content"$normal >&2
                    echo "   ["$green$bold"y"$normal"] Allow once" >&2
                    echo "   ["$blue$bold"t"$normal"] Allow for this task (automatic until goal/chat)" >&2
                    echo "   ["$cyan$bold"a"$normal"] Always allow for this session" >&2
                    echo "   ["$red$bold"n"$normal"] Deny this command" >&2
                    
                    if not read -l -P (set_color green)"Allow? [y/t/a/n]: "(set_color normal) user_choice </dev/tty
                        rm "$action_file" "$signal_file"
                        echo "👋 "$red"Agent session interrupted."$normal >&2
                        commandline -f repaint
                        return
                    end
                    
                    # Clear the prompt from stderr
                    printf "\033[1A\033[2K\033[1A\033[2K\033[1A\033[2K\033[1A\033[2K\033[1A\033[2K\033[1A\033[2K" >&2
                    
                    switch "$user_choice"
                        case t Turn turn
                            set confirm_mode "turn"
                        case a Always always
                            set confirm_mode "always"
                        case n No no
                            set rejected 1
                            echo "❌ "$red"Command denied."$normal >&2
                            continue
                        case y Yes yes ""
                            # Proceed
                        case '*'
                            set rejected 1
                            echo "❌ "$red"Invalid choice."$normal >&2
                            continue
                    end
                end
                
                if test $is_whitelisted -eq 1
                    echo "🛠️  "$yellow$bold"Agent executed (whitelisted):"$normal" "$bold"$action_content"$normal >&2
                else if test "$confirm_mode" = "turn"; or test "$confirm_mode" = "always"
                    echo "🛠️  "$yellow$bold"Agent executed (authorized):"$normal" "$bold"$action_content"$normal >&2
                else
                    echo "🛠️  "$yellow$bold"Agent executed:"$normal" "$bold"$action_content"$normal >&2
                end
                
                set -l out_file (mktemp -t fish-ai-eval-out.XXXXXX)
                begin
                    eval $action_content
                end > "$out_file" 2>&1
                set last_status $status
                set last_output (cat "$out_file" | string collect)
                rm "$out_file"
                
                if test $last_status -eq 130
                    rm "$action_file" "$signal_file"
                    echo "👋 "$red"Agent session interrupted."$normal >&2
                    commandline -f repaint
                    return
                end

                if test -n "$last_output"
                    echo "✅ "$green$bold"Output:"$normal >&2
                    echo "$last_output" | head -n 4 >&2
                    if test (echo "$last_output" | wc -l) -gt 4
                        echo "$green... [Output Truncated]$normal" >&2
                    end
                end
                echo "" >&2
            
            case CONTINUE
                continue

            case CHAT
                if test "$confirm_mode" = "turn"
                    set confirm_mode "ask"
                end
                if isatty stdout
                    echo "💬 "$blue$bold"Agent Report:"$normal
                    cat "$action_file" | "$_fish_ai_install_dir/bin/render"
                else
                    cat "$action_file"
                end
                break

            case DONE
                if test "$confirm_mode" = "turn"
                    set confirm_mode "ask"
                end
                if isatty stdout
                    echo "✅ "$green$bold"Final Achievement:"$normal" "
                    cat "$action_file" | "$_fish_ai_install_dir/bin/render"
                else
                    cat "$action_file"
                end
                break
            
            case ERROR
                echo "❌ "$red$bold"Agent error:"$normal" $action_content" >&2
                break
            
            case '*'
                echo "❓ "$red"Unknown response:"$normal" $response_type" >&2
                break
        end
    end

    functions -e __fish_ai_agent_cleanup
    set -e _fish_ai_agent_interrupted
    rm "$action_file" "$signal_file" "$history_file"
    commandline -f repaint
end
