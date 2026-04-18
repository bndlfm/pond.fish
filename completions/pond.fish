# Completions for the 'pond' command

# Disable file completions unless explicitly allowed
complete -c pond -f

# Options
complete -c pond -l json -d "Output raw JSON response"
complete -c pond -s q -d "Run a stateless AI query (supports piping)"
complete -c pond -s a -d "Trigger the autonomous agent"

# Main subcommands
complete -c pond -n "__fish_use_subcommand" -a "skill skills" -d "List or install skills"
complete -c pond -n "__fish_use_subcommand" -a forget -d "Clear agent memory"
complete -c pond -n "__fish_use_subcommand" -a compress -d "Summarize agent history"
complete -c pond -n "__fish_use_subcommand" -a status -d "Show session stats"
complete -c pond -n "__fish_use_subcommand" -a edit -d "Edit session history in editor"
complete -c pond -n "__fish_use_subcommand" -a version -d "Show version"
complete -c pond -n "__fish_use_subcommand" -a help -d "Show help"

# Subcommands for 'skill'
complete -c pond -n "__fish_seen_subcommand_from skill skills" -a list -d "List available skills"
complete -c pond -n "__fish_seen_subcommand_from skill skills" -a install -d "Install a skill from GitHub"
