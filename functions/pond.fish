#!/usr/bin/env fish

function pond --description "The master command for the pond AI suite."
    set -l subcommand $argv[1]
    set -l remaining_args $argv[2..-1]
    set -l json_flag 0
    set -l query_flag 0
    set -l agent_flag 0
    
    # 1. Flag Detection
    if contains -- --json $argv
        set json_flag 1
    end
    if contains -- -q $argv
        set query_flag 1
    end
    if contains -- -a $argv
        set agent_flag 1
    end

    # 2. Argument Cleaning
    set -l clean_args
    for arg in $argv
        if test "$arg" != "--json" -a "$arg" != "-q" -a "$arg" != "-a"
            set clean_args $clean_args "$arg"
        end
    end
    
    # 3. Subcommand/Goal Extraction
    if test (count $clean_args) -gt 0
        set subcommand "$clean_args[1]"
        set remaining_args $clean_args[2..-1]
    end

    # Helper for colored output
    set -l blue (set_color blue)
    set -l cyan (set_color cyan)
    set -l yellow (set_color yellow)
    set -l green (set_color green)
    set -l red (set_color red)
    set -l bold (set_color --bold)
    set -l normal (set_color normal)

    # 4. Handle Inference via -q
    if test $query_flag -eq 1
        if test -z "$subcommand"
            echo "❌ "$red"Error: No prompt provided for -q."$normal
            return 1
        end
        
        set -l full_prompt "$clean_args"
        if test $json_flag -eq 1
            "$_fish_ai_install_dir/bin/ai" $full_prompt --json
        else
            "$_fish_ai_install_dir/bin/ai" $full_prompt
        end
        return
    end

    # 5. Handle Agent via -a
    if test $agent_flag -eq 1
        set -l state_file "$_fish_ai_install_dir/agent_session.json"
        
        if test -n "$clean_args"
            commandline -r "$clean_args"
        end
        
        if test $json_flag -eq 1
            set -l action_file (mktemp -t fish-ai-action.XXXXXX)
            "$_fish_ai_install_dir/bin/agent" --state "$state_file" --action-file "$action_file" --goal "$clean_args" --json
            rm "$action_file"
        else
            _fish_ai_agent
        end
        return
    end

    # 6. Handle Subcommands
    switch "$subcommand"
        case skill
            set -l action "$remaining_args[1]"
            if test "$action" = "list" -o -z "$action"
                set -l state_file "$_fish_ai_install_dir/agent_session.json"
                set -l action_file (mktemp -t fish-ai-action.XXXXXX)
                "$_fish_ai_install_dir/bin/agent" --state "$state_file" --action-file "$action_file" --list-skills
                rm "$action_file"
            else if test "$action" = "install"
                set -l skill_id "$remaining_args[2]"
                if test -z "$skill_id"
                    echo "❌ "$red"Error: No skill ID provided."$normal
                    echo "Usage: pond skill install <owner>/<repo>/skills/<name>"
                    return 1
                end
                
                # Expected format: owner/repo/path/to/skill
                # Example: anthropics/skills/skills/pdf
                set -l parts (string split "/" "$skill_id")
                if test (count $parts) -lt 3
                    echo "❌ "$red"Error: Invalid skill ID format."$normal
                    echo "Usage: pond skill install <owner>/<repo>/[path/to/skill]"
                    return 1
                end

                set -l owner $parts[1]
                set -l repo $parts[2]
                set -l skill_path (string join "/" $parts[3..-1])
                set -l skill_name $parts[-1]

                set -l skills_dir (dirname "$_fish_ai_config_path")/skills
                mkdir -p "$skills_dir"
                
                echo "📥 "$cyan"Installing skill '$skill_name' from github.com/$owner/$repo..."$normal
                
                # Check for git
                if not type -q git
                    echo "❌ "$red"Error: 'git' is required to install skills."$normal
                    return 1
                end

                # Use a temporary directory for sparse clone
                set -l tmp_clone_dir (mktemp -d -t skill-clone.XXXXXX)
                
                if git clone --depth 1 --filter=blob:none --sparse "https://github.com/$owner/$repo.git" "$tmp_clone_dir" >/dev/null 2>&1
                    pushd "$tmp_clone_dir"
                    if git sparse-checkout set "$skill_path" >/dev/null 2>&1
                        if test -d "$skill_path"
                            cp -R "$skill_path" "$skills_dir/"
                            echo "✅ "$green"Skill '$skill_name' installed successfully."$normal
                            echo "   Location: $skills_dir/$skill_name"
                        else
                            echo "❌ "$red"Error: Skill path '$skill_path' not found in repository."$normal
                        end
                    else
                        echo "❌ "$red"Failed to perform sparse checkout for '$skill_path'."$normal
                    end
                    popd
                else
                    echo "❌ "$red"Error: Failed to clone repository 'https://github.com/$owner/$repo.git'."$normal
                end
                rm -rf "$tmp_clone_dir"
            else if test "$action" = "remove"
                set -l skill_name "$remaining_args[2]"
                if test -z "$skill_name"
                    echo "❌ "$red"Error: No skill name provided."$normal
                    echo "Usage: pond skill remove <skill-name>"
                    return 1
                end

                set -l skills_dir (dirname "$_fish_ai_config_path")/skills
                set -l target_dir "$skills_dir/$skill_name"

                if test -d "$target_dir"
                    rm -rf "$target_dir"
                    echo "🗑️  "$green"Skill '$skill_name' removed successfully."$normal
                else
                    echo "❌ "$red"Error: Skill '$skill_name' not found in $skills_dir."$normal
                    return 1
                end
            else
                echo "❓ Unknown skill action: $action"
                echo "Try 'pond skill list', 'pond skill install <owner/repo/path>' or 'pond skill remove <name>'."
            end

        case forget
            set -l state_file "$_fish_ai_install_dir/agent_session.json"
            if test -f "$state_file"
                rm "$state_file"
                echo "🧹 "$green"Agent session cleared."$normal
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
            echo "🗜️  "$cyan"Compressing session history..."$normal
            "$_fish_ai_install_dir/bin/agent" --state "$state_file" --action-file "$action_file" --compress > /dev/null
            rm "$action_file"
            echo "✅ "$green"Compression complete."$normal

        case status
            set -l state_file "$_fish_ai_install_dir/agent_session.json"
            if test -f "$state_file"
                set -l size (du -h "$state_file" | cut -f1)
                set -l turns (grep -c '"role":' "$state_file")
                echo "🤖 "$bold"Agent Session Status:"$normal
                echo "  - File: $state_file"
                echo "  - Size: $size"
                echo "  - Message turns: $turns"
            else
                echo "ℹ️  "$yellow"No active agent session."$normal
            end

        case edit
            set -l state_file "$_fish_ai_install_dir/agent_session.json"
            if not test -f "$state_file"
                echo "ℹ️  "$yellow"No active agent session to edit."$normal
                return
            end
            if set -q VISUAL
                $VISUAL "$state_file"
            else if set -q EDITOR
                $EDITOR "$state_file"
            else
                vi "$state_file"
            end

        case version -v --version
            set -l version "2.11.1" 
            echo "🐟 "$bold"pond"$normal" v$version"

        case help -h --help
            echo "🐟 "$blue$bold"pond: AI-Powered Fish Shell Suite"$normal
            echo ""
            echo "Usage: pond [options] <command> [arguments]"
            echo ""
            echo "$bold""Options:""$normal"
            echo "  -q <prompt>         Run a stateless AI query (supports piping)"
            echo "  -a <goal>           Trigger the autonomous agent"
            echo "  --json              Output raw JSON response"
            echo ""
            echo "$bold""Session Commands:""$normal"
            echo "  forget              Clear the agent's session memory"
            echo "  compress            Summarize long conversation history"
            echo "  status              Show current session statistics"
            echo "  edit                Open session history in your editor"
            echo ""
            echo "$bold""General Commands:""$normal"
            echo "  skill list          List all available specialized skills"
            echo "  skill install <id>  Install a skill from GitHub (e.g., anthropics/skills/skills/pdf)"
            echo "  skill remove <name> Remove an installed skill"
            echo "  version, -v         Display version information"
            echo "  help, -h            Show this help message"
            echo ""
            echo "$bold""Examples:""$normal"
            echo "  cat logs.txt | pond -q \"find errors\""
            echo "  pond -a \"fix the tests\""

        case '*'
            if test -z "$subcommand"
                pond help
            else
                echo "❌ "$red"Unknown subcommand: $subcommand"$normal
                echo "To run a query, use: pond -q \"$argv\""
            end
    end
end
