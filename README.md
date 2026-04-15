![Badge with time spent](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FRealiserad%2Fd3ec7fdeecc35aeeb315b4efba493326%2Fraw%2Ffish-ai-git-estimate.json)
![Popularity badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FRealiserad%2Fd3ec7fdeecc35aeeb315b4efba493326%2Fraw%2Fpopularity.json)
[![Donate XMR](https://img.shields.io/badge/Donate_XMR-grey?style=for-the-badge&logo=monero)](https://github.com/user-attachments/assets/07a29402-4029-4ccb-86bc-539077977467)

# 🐟 pond: AI for Fish shell

`pond` is a fork of `fish-ai` that provides autonomous agentic capabilities and integrated AI assistance for the Fish shell.

## 🚀 Features

1.  **AI Agent (`Ctrl+X`)**: An autonomous agent that can execute shell commands, read/write files, and list directories.
2.  **Codify / Explain (`Ctrl+A`)**: Turn natural language into commands or explain what a command does.
3.  **Autocomplete / Fix (`Ctrl+Space`)**: Intelligent completions and instant fixes for failed commands.
4.  **Markdown Support**: Agent responses are beautifully rendered with Markdown in your terminal.
5.  **Auditability**: Real-time streaming of agent thoughts, tool calls, and results.
6.  **Session Persistence**: The agent maintains state between invocations.

## 📦 Installation

Install using [fisher](https://github.com/jorgebucaran/fisher):

```shell
fisher install bndlfm/pond
```

## 🙉 How to use

### 🤖 AI Agent

Press **Ctrl + X** to trigger the agent. You can type a goal in plain text or as a comment:

```shell
find all large files and compress them
# (then press Ctrl+X)
```

The agent will propose commands and ask for permission:
- **y**: Allow once.
- **a**: Always allow for this session.
- **n**: Deny this command.

To clear the agent's memory, run `fish_ai_agent_forget`.
To compress long sessions, run `fish_ai_agent_compress`.

### 📝 Codify / Explain

Type a goal and press **Ctrl + A** to get a shell command:

```shell
# list all files larger than 1MB
# (then press Ctrl+A)
```

Or type a command and press **Ctrl + A** to get an explanation.

### 🪄 Autocomplete / Fix

Start typing and press **Ctrl + Space** for completions. If a command fails, press **Ctrl + Space** to get a fix.

## 🤸 Configuration

Edit `~/.config/fish-ai.ini` to configure your provider.

```ini
[fish-ai]
configuration = my-provider

[my_provider]
provider = google
api_key = <your key>
model = gemini-3.1-pro-preview
```

## 🐾 Data privacy

Content is sent to your configured LLM provider. Sensitive information (keys, tokens) is redacted before sending.

## 🛠️ Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for instructions on setting up a development environment with **Nix**.
