# Completions for the 'pond' command

# Disable file completions unless explicitly allowed
complete -c pond -f

# Main subcommands
complete -c pond -n "__fish_use_subcommand" -a agent -d "Autonomous AI Agent"
complete -c pond -n "__fish_use_subcommand" -a ai -d "Stateless query (supports piping)"
complete -c pond -n "__fish_use_subcommand" -a skills -d "List available skills"
complete -c pond -n "__fish_use_subcommand" -a skill -d "List available skills"
complete -c pond -n "__fish_use_subcommand" -a forget -d "Clear agent memory"
complete -c pond -n "__fish_use_subcommand" -a compress -d "Summarize agent history"
complete -c pond -n "__fish_use_subcommand" -a status -d "Show session stats"
complete -c pond -n "__fish_use_subcommand" -a edit -d "Edit session history in editor"
complete -c pond -n "__fish_use_subcommand" -a version -d "Show version"
complete -c pond -n "__fish_use_subcommand" -a help -d "Show help"

# Options
complete -c pond -l json -d "Output raw JSON response"

# Subcommands for 'agent'
complete -c pond -n "__fish_seen_subcommand_from agent" -a forget -d "Clear agent memory"
complete -c pond -n "__fish_seen_subcommand_from agent" -a compress -d "Summarize agent history"
complete -c pond -n "__fish_seen_subcommand_from agent" -a status -d "Show session stats"

# Subcommands for 'skills'
complete -c pond -n "__fish_seen_subcommand_from skills skill" -a list -d "List available skills"
