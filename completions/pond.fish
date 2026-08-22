# Completions for the stateful Pond ACP interface.
complete -c pond -f
complete -c pond -s a -d "Start an explicit stateful agent goal"
complete -c pond -n "__fish_use_subcommand" -a status -d "Show this workspace ACP session"
complete -c pond -n "__fish_use_subcommand" -a context -d "Show harness context pressure"
complete -c pond -n "__fish_use_subcommand" -a compress -d "Request harness context compression"
complete -c pond -n "__fish_use_subcommand" -a forget -d "Detach this workspace ACP session"
complete -c pond -n "__fish_use_subcommand" -a version -d "Show version"
complete -c pond -n "__fish_use_subcommand" -a help -d "Show help"
