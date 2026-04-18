# Completions for the 'pond' command

# Disable file completions unless explicitly allowed
complete -c pond -f

# Options
complete -c pond -l json -d "Output raw JSON response"
complete -c pond -s q -d "Run a stateless AI query (supports piping)"
complete -c pond -s a -d "Trigger the autonomous agent"

# Main subcommands
complete -c pond -n "__fish_use_subcommand" -a skill -d "List or install skills"
complete -c pond -n "__fish_use_subcommand" -a forget -d "Clear agent memory"
complete -c pond -n "__fish_use_subcommand" -a compress -d "Summarize agent history"
complete -c pond -n "__fish_use_subcommand" -a status -d "Show session stats"
complete -c pond -n "__fish_use_subcommand" -a edit -d "Edit session history in editor"
complete -c pond -n "__fish_use_subcommand" -a version -d "Show version"
complete -c pond -n "__fish_use_subcommand" -a help -d "Show help"

# Subcommands for 'skill'
complete -c pond -n "__fish_seen_subcommand_from skill" -a list -d "List available skills"
complete -c pond -n "__fish_seen_subcommand_from skill" -a install -d "Install a skill from GitHub"
complete -c pond -n "__fish_seen_subcommand_from skill" -a remove -d "Remove an installed skill"
complete -c pond -n "__fish_seen_subcommand_from skill; and __fish_seen_subcommand_from remove" -a "(ls (test -z \"$XDG_CONFIG_HOME\"; and echo \"$HOME/.config/fish-ai/skills\"; or echo \"$XDG_CONFIG_HOME/fish-ai/skills\") 2>/dev/null)" -d "Installed skill"
