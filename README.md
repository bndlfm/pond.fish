# About

`fish-ai` adds AI functionality to [Fish](https://fishshell.com).
It's awesome! I built it to make my life easier, and I hope it will make
yours easier too. Here is the complete sales pitch:

- It can turn a comment into a shell command and vice versa, which means
less time spent
reading manpages, googling and copy-pasting from Stack Overflow. Great
when working with `git`, `kubectl`, `curl` and other tools with loads
of parameters and switches.
- Did you make a typo? It can also fix a broken command (similarly to
[`thefuck`](https://github.com/nvbn/thefuck)).
- Not sure what to type next or just lazy? Let the LLM autocomplete
your commands with a built in fuzzy finder.
- Everything is done using two (configurable) keyboard shortcuts, no mouse needed!
- It can be hooked up to the LLM of your choice (even a self-hosted one!).
- The whole thing is open source, hopefully somewhat easy to read and
around 2000 lines of code, which means that you can audit the code
yourself in an afternoon.
- Install and update with ease using [`fisher`](https://github.com/jorgebucaran/fisher).
- Tested on both macOS and the most common Linux distributions.
- Does not interfere with [`fzf.fish`](https://github.com/PatrickF1/fzf.fish),
[`tide`](https://github.com/IlanCosman/tide) or any of the other plugins
you're already using!
- Does not wrap your shell, install telemetry or force you to switch
to a proprietary terminal emulator.

This plugin was originally based on [Tom Dörr's `fish.codex` repository](https://github.com/tom-doerr/codex.fish).
Without Tom, this repository would not exist!

If you like it, please add a ⭐.

Bug fixes are welcome! I consider this project largely feature complete.
Before opening a PR for a feature request, consider opening an issue where
you explain what you want to add and why, and we can talk about it first.

## 🎥 Demo

![Demo](https://github.com/user-attachments/assets/86b61223-e568-4152-9e5e-d572b2b1385b)

## 👨‍🔧 How to install

### Install `fish-ai`

Make sure `git` and either [`uv`](https://github.com/astral-sh/uv), or
[a supported version of Python](https://github.com/bndlfm/pond/blob/main/.github/workflows/python-tests.yaml)
along with `pip` and `venv` is installed. Then grab the plugin using
[`fisher`](https://github.com/jorgebucaran/fisher):

```shell
fisher install bndlfm/pond
```

### Create a configuration

Create a configuration file `$XDG_CONFIG_HOME/fish-ai.ini` (use
`~/.config/fish-ai.ini` if `$XDG_CONFIG_HOME` is not set) where
you specify which LLM `fish-ai` should talk to. If you're not sure,
use GitHub Models.

#### Anthropic

To use [Anthropic](https://www.anthropic.com):

```ini
[anthropic]
provider = anthropic
api_key = <your API key>
model = claude-sonnet-4-6
```

#### Azure OpenAI

To use [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service):

```ini
[fish-ai]
configuration = azure

[azure]
provider = azure
server = https://<your instance>.openai.azure.com
model = <your deployment name>
api_key = <your API key>
```

#### Bedrock

To use models on [AWS Bedrock](https://aws.amazon.com/bedrock/) via the
[OpenAI-compatible API](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-mantle.html):

```ini
[fish-ai]
configuration = bedrock

[bedrock]
provider = bedrock
aws_region = us-east-1
```

If no `api_key` is configured, a short-term token is automatically
generated from your
[AWS credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-authentication.html)
(SSO, IAM roles, environment variables, etc.). You can also specify
an `api_key` directly if you prefer to use a
[Bedrock API key](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html).

This uses the Bedrock Mantle gateway which supports all models available
on Bedrock. See the
[supported regions](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-mantle.html)
for available regions.

#### Cohere

To use [Cohere](https://cohere.com):

```ini
[cohere]
provider = cohere
api_key = <your API key>
model = command-a-03-2025
```

#### DeepSeek

To use [DeepSeek](https://www.deepseek.com):

```ini
[deepseek]
provider = deepseek
api_key = <your API key>
```

#### GitHub Models

To use [GitHub Models](https://github.com/marketplace/models):

```ini
[github]
provider = github
api_key = <your personal access token>
model = gpt-4o
```

#### Google

To use [Google Gemini](https://ai.google.dev):

```ini
[google]
provider = google
api_key = <your API key>
model = gemini-1.5-flash
```

#### Groq

To use [Groq](https://groq.com):

```ini
[groq]
provider = groq
api_key = <your API key>
model = llama3-70b-8192
```

#### Mistral

To use [Mistral](https://mistral.ai):

```ini
[mistral]
provider = mistral
api_key = <your API key>
model = mistral-large-latest
```

#### OpenAI

To use [OpenAI](https://openai.com):

```ini
[openai]
provider = openai
api_key = <your API key>
model = gpt-4o
```

#### OpenRouter

To use [OpenRouter](https://openrouter.ai):

```ini
[openrouter]
provider = openrouter
api_key = <your API key>
model = anthropic/claude-3.5-sonnet
```

#### Self-hosted

To use a self-hosted LLM (e.g. [Ollama](https://ollama.com),
[LocalAI](https://localai.io) or [vLLM](https://github.com/vllm-project/vllm)):

```ini
[fish-ai]
configuration = self-hosted

[self-hosted]
provider = openai
server = http://localhost:11434/v1
model = llama3
api_key = ollama
```

### Put the API key on your keyring

Instead of storing the API key in the configuration file, you can
store it in your system keyring. This is more secure as the key is
encrypted and not stored in plaintext.

To store the API key in the keyring, run the following command:

```shell
fish_ai_put_api_key
```

The plugin will then automatically retrieve the key from the keyring.

## 🙉 How to use

### Transform comments into commands and vice versa

Type a comment and press `Ctrl+A` to turn it into a command.

```shell
# list all files in the current directory
```

Press `Ctrl+A` again to turn the command back into a comment.

### Autocomplete commands

Type a partial command and press `Ctrl+Space` to autocomplete it.

```shell
git comm
```

### Suggest fixes

If a command fails, press `Ctrl+Space` to suggest a fix.

```shell
git commit -m "Initial commit"
# error: pathspec 'commit' did not match any file(s) known to git
```

### Agentic loop

Press `Ctrl+X` to start an agentic loop. The agent can execute
commands, read and write files and list directories.

```shell
# find all python files and count the number of lines
```

## 🏗️ Architecture & Codepaths

The `fish-ai` plugin integrates AI capabilities into the Fish shell through several distinct codepaths:

### 1. Initialization and Configuration (`conf.d/fish_ai.fish`)
*   **Startup**: Sets up environment variables and maps keyboard shortcuts (defaulting to `Ctrl+A`, `Ctrl+Space`, and `Ctrl+X`).
*   **Lifecycle**: Handles virtual environment creation and dependency installation via `pip`.

### 2. Core Engine (`src/fish_ai/engine.py`)
*   **Backend Communication**: Central hub for interacting with various AI providers (OpenAI, Anthropic, Google, etc.).
*   **Context Gathering**: Fetches OS info, manpages, file snippets, and shell history to provide the LLM with relevant context.
*   **Redaction**: Automatically removes sensitive information (API keys, tokens) before sending data to the AI.

### 3. Codify / Explain (`src/fish_ai/codify.py` & `src/fish_ai/explain.py`)
*   **Trigger**: `Ctrl+A`.
*   **Logic**: Translates natural language comments into shell commands or explains existing commands.

### 4. Autocomplete / Fix (`src/fish_ai/autocomplete.py` & `src/fish_ai/fix.py`)
*   **Trigger**: `Ctrl+Space`.
*   **Logic**: Provides intelligent command completions or suggests fixes for failed commands.

### 5. AI Agent (`src/fish_ai/agent.py`)
*   **Trigger**: `Ctrl+X`.
*   **Capabilities**: An autonomous agent that can execute shell commands, read/write files, and list directories using tool calling.
*   **State Management**: Maintains session state and uses recursive summarization to manage long conversation histories.

## 🤸 Additional options

### Change the default key bindings

If you want to use different key bindings, you can set the
`fish_ai_codify_bind` and `fish_ai_autocomplete_bind` variables in
your `config.fish` file.

```shell
set -g fish_ai_codify_bind \ca
set -g fish_ai_autocomplete_bind \cspace
set -g fish_ai_agent_bind \cx
```

### Explain in a different language

By default, the plugin explains commands in English. You can change
this by setting the `language` option in the configuration file.

```ini
[fish-ai]
language = German
```

### Number of completions

By default, the plugin suggests 5 completions. You can change this
by setting the `completions` option in the configuration file.

```ini
[fish-ai]
completions = 3
```

### Personalise completions using commandline history

The plugin can use your commandline history to personalise completions.
This is disabled by default. To enable it, set the `history` option
in the configuration file.

```ini
[fish-ai]
history = True
```

### Preview pipes

When autocompleting a command that contains a pipe, the plugin can
preview the output of the command before the pipe. This is enabled
by default. To disable it, set the `piping` option in the configuration
file.

```ini
[fish-ai]
piping = False
```

### Configure the progress indicator

The plugin shows a progress indicator while waiting for the LLM.
You can change the character used for the progress indicator by
setting the `indicator` option in the configuration file.

```ini
[fish-ai]
indicator = 🤖
```

### Use custom headers

If you need to send custom headers to the LLM provider, you can
specify them in the configuration file.

```ini
[openai]
headers = {"X-My-Header": "my-value"}
```

## 🎭 Switch between contexts

If you are working on multiple projects, you can switch between
different configurations using the `fish_ai_switch_context` command.

```shell
fish_ai_switch_context
```

This will open a fuzzy finder where you can select the configuration
you want to use.

## 🐾 Data privacy

When you use `fish-ai`, the content of your commandline is sent to
the LLM provider you have configured. If you have enabled history,
your commandline history is also sent. If you use the agentic loop,
the output of the commands you execute is also sent.

### Redaction of sensitive information

The plugin attempts to redact sensitive information from the prompt
before submitting it to the LLM. Sensitive information is replaced by
the `<REDACTED>` placeholder.

The following information is redacted:

- Passwords and API keys supplied as commandline arguments
- PEM-encoded private keys stored in files
- Bearer tokens, provided to e.g. cURL

If you trust the LLM provider (e.g. because you are hosting locally)
you can disable redaction using the `redact = False` option.
