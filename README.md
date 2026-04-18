![Badge with time spent](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FRealiserad%2Fd3ec7fdeecc35aeeb315b4efba493326%2Fraw%2Ffish-ai-git-estimate.json)
![Popularity badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FRealiserad%2Fd3ec7fdeecc35aeeb315b4efba493326%2Fraw%2Fpopularity.json)
[![Donate XMR](https://img.shields.io/badge/Donate_XMR-grey?style=for-the-badge&logo=monero)](https://github.com/user-attachments/assets/07a29402-4029-4ccb-86bc-539077977467)

# 🐟 pond: AI for Fish shell

`pond` is a powerful fork of `fish-ai` designed for developers who want a minimalist yet capable autonomous AI agent living directly in their Fish shell. It prioritizes **auditability**, **security**, and **seamless shell integration**.

## 🚀 Key Features

1.  **Autonomous AI Agent (`Ctrl+X`)**: A multi-turn expert that can read files, list directories, search the web, and execute shell commands to achieve complex goals.
2.  **Unified `pond` Command**: A master utility for piping data to an LLM, managing the agent, or asking quick questions.
3.  **SKILL.md Support**: Fully compatible with the `skills.sh` / `agentskills.io` standard. "Teach" the agent new expertise by dropping Markdown folders into `~/.config/fish-ai/skills/`.
4.  **Codify / Explain (`Ctrl+A`)**: Instantly turn natural language into shell commands or get clear explanations of what a command does.
5.  **Autocomplete / Fix (`Ctrl+Space`)**: Intelligent, context-aware command completions and instant fixes for your last failed command.
6.  **Brave Search Integration**: Real-time web access for troubleshooting, documentation, and research.
7.  **Advanced Audit UI**: Color-coded streaming of agent thoughts, tool calls, and truncated results directly in your terminal.
8.  **Surgical Permissions**: A 4-tier permission system (`[y/t/a/n]`) that puts you in full control of every system-modifying action.
9.  **Session Persistence**: Maintains conversation state between loops, allowing for long-running, multi-step collaborations.

## 📦 Installation

Install using [fisher](https://github.com/jorgebucaran/fisher):

```shell
fisher install bndlfm/pond
```

## 🤖 Usage Guide

### 🦾 The AI Agent

Type a goal in plain text or as a comment and press **Ctrl + X**:

```shell
# find all python files and search for TODOs
(press Ctrl+X)
```

The agent will work turn-by-turn. When it needs to execute a command, it will prompt you:
- **`[y]` Allow once**: Permit only this specific command.
- **`[t]` Allow for this task**: Grant temporary autonomy until the current goal is met or the agent asks a question.
- **`[a]` Always allow**: Grant full autonomy for the rest of the shell session.
- **`[n]` Deny**: Prevent the command from running and let the agent rethink.

**Manage Session State:**
- `pond agent forget`: Wipes the agent's memory to start a fresh session.
- `pond agent compress`: Manually trigger a summarization of long histories.
- `pond agent status`: View current session statistics.
- `pond skill list`: List all available specialized skills.

You can also trigger the agent directly from the CLI:
```shell
pond agent "find all large files"
```

### 🐚 Unified `pond` Command (Piping & Query)

The `pond` command provides a stateless interface for quick LLM queries, supporting piping:

```shell
# Pipe context in
cat README.md | pond "summarize this"

# Output raw JSON
pond "find python entrypoints" --json
```

It does not include shell history or previous agent state, making it ideal for scripting and data processing.

### 🛡️ Command Whitelist

`pond` can run safe commands automatically. Customize this list in your configuration:

```ini
[fish-ai]
whitelist = ls, grep, find, cat, pwd, date, eza, fd, rg
```

**Security Guard:** Any command containing redirections (`>`), pipes (`|`), or chaining (`;`, `&&`) is **never** whitelisted and will always require your manual approval.

### 🌐 Web Search

To enable web research, add your [Brave Search API key](https://api.search.brave.com/app/dashboard) to your config:

```ini
[fish-ai]
brave_search_api_key = <your_key>
```

### 🔌 Specialized Skills

`pond` supports the **agentskills.io** open standard. To add an expert, drop a skill folder from [skills.sh](https://skills.sh) into your skills directory:

```shell
# Location: ~/.config/fish-ai/skills/
pond skills list
```

### 📝 Codify & Explain

Press **Ctrl + A** to swap between natural language and shell commands:
- `list files larger than 1gb` &rarr; `find . -size +1G`
- `tar -xvzf archive.tar.gz` &rarr; Explains the command and flags.

### 🪄 Autocomplete & Fix

- Press **Ctrl + Space** while typing for intelligent completions.
- Press **Ctrl + Space** after a command fails to receive an immediate fix based on the error output.

## 🤸 Configuration

Edit `~/.config/fish-ai/config.ini` or use environment variables (ideal for **Nix/Home Manager**):

```ini
[fish-ai]
configuration = my-provider
whitelist = ls, rg, fd, cat

[my_provider]
provider = google
api_key = <your_key>
model = gemini-3.1-pro-preview
```

### Runtime Keybindings (Nix/Home Manager)
You can customize keybindings via environment variables in your shell config:
- `FISH_AI_KEYMAP_1`: Defaults to `ctrl-a` (Codify)
- `FISH_AI_KEYMAP_2`: Defaults to `ctrl-space` (Autocomplete)
- `FISH_AI_KEYMAP_3`: Defaults to `ctrl-x` (Agent)

## 🛠️ Development

`pond` includes a **Nix Flake** for a reproducible development environment.
Run `nix develop` to enter a shell with all dependencies configured.

See [DEVELOPMENT.md](DEVELOPMENT.md) for more details.

---
*Based on the original [fish-ai](https://github.com/Realiserad/fish-ai) by Bastian Fredriksson.*
