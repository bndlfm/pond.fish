# Completions for the 'pond' command

# Disable file completions unless explicitly allowed
complete -c pond -f

# Main subcommands
complete -c pond -n "__fish_use_subcommand" -a agent -d "Autonomous AI Agent"
complete -c pond -n "__fish_use_subcommand" -a -a -d "Autonomous AI Agent"
complete -c pond -n "__fish_use_subcommand" -a ai -d "Stateless query (supports piping)"
complete -c pond -n "__fish_use_subcommand" -a forget -d "Clear agent memory"
complete -c pond -n "__fish_use_subcommand" -a clear -d "Clear agent memory"
complete -c pond -n "__fish_use_subcommand" -a compress -d "Summarize agent history"
complete -c pond -n "__fish_use_subcommand" -a status -d "Show session stats"
complete -c pond -n "__fish_use_subcommand" -a version -d "Show version"
complete -c pond -n "__fish_use_subcommand" -a help -d "Show help"

# Subcommands for 'agent'
complete -c pond -n "__fish_seen_subcommand_from agent -a" -a forget -d "Clear agent memory"
complete -c pond -n "__fish_seen_subcommand_from agent -a" -a clear -d "Clear agent memory"
complete -c pond -n "__fish_seen_subcommand_from agent -a" -a compress -d "Summarize agent history"
complete -c pond -n "__fish_seen_subcommand_from agent -a" -a status -d "Show session stats"

# Allow file completion for 'ai' type commands if needed, but usually prompts are plain text.
# For now, let's keep it clean.
