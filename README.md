![MinCE logo](mince.png)

## What it does ✨

- Answers direct prompts or performs tasks using one or more local files as context
- Sends a single request to an OpenAI-compatible model endpoint
- Generates structured multi-file patches with diffs, optional review, and configurable output suffixes
- Supports text, JSON, JSON Schema Structured Outputs, and streamed text responses
- Supports configuration profiles, custom system prompts, reasoning controls, and model parameters
- Provides optional local session logging, API storage controls, usage statistics, and cost estimates
- Creates a context-controlled, continuously verified workflow and maximizes cost effectiveness

## Requirements 📦

- `python` 3.10 or newer and the `pip` package manager
- `make` from GNU Make or compatible for a managed installation
- Network access to your chosen OpenAI-compatible endpoint
- An API key for the endpoint
- Optional: a local OpenAI‑compatible server

## Install / Update 🛠️

```bash
git clone https://github.com/Southland-Systems/mince.git
cd mince
make install
```

Update

```bash
cd mince
make update
```

Uninstall

```bash
cd mince
make uninstall-user
```

Manual install

```bash
(cd mince && cp -a mince ~/.local/bin/ && chmod +x ~/.local/bin/mince \
  && pip install -U -r requirements.txt)
```

## First run 🚀

```bash
mince --init
```

This creates `~/.local/state/mince/config.json`.

## Basic usage 💡

Ask a direct question without file context:

```bash
mince -a "How are two strings concatenated?"
```

Run a task with local files as context:

```bash
mince -t "Summarize this project" -f README.md src/main.py
```

Read the task and context-file paths from files:

```bash
mince --task-file review-task.txt --files-list review-files.txt
```

Request JSON output:

```bash
mince --response-format json \
  --task "Extract the key settings" \
  --files config.yml
```

Write a response to a file:

```bash
mince -t "Add single-user locking to the provided script. Only output the whole script." \
  -f taskedit.py -o taskedit-new.py
```

Validate structured output against a JSON Schema:

```bash
mince --task "Provide the file name and line count as JSON" \
  --files README.md requirements.txt --response-format schema \
  --schema-file filemeta-schema.json
```

Generate a patch, review the diff, and write the approved result:

```bash
cp /etc/passwd .
mince -PR -f passwd -t "Remove lines 1-5 from 'passwd' \
and create a new file called 'passwd-new' with those lines."
```

Plan mode asks the model to create prompt for the next step using the supplied context:

```bash
mince --plan \
  --task "Review the error handling and propose the next implementation step" \
  --files src/main.py README.md
```

Create a dedicated 'ask' profile from the default profile:

```bash
mince --copy-profile a
mince --init-profile a

mince -p a -a 'How is a file read in Go lang?'
```

Run MinCE in a restricted systemd user unit for testing:

```bash
# systemd core container for restricted testing

systemd-run --user -qt -p ProtectSystem=strict \
  -p ProtectHome=read-only -p PrivateTmp=yes \
  mince --help

# -p RestrictAddressFamilies=AF_UNIX

# https://www.freedesktop.org/software/systemd/man/latest/systemd-run.html
# https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html
```

## Local model servers 🌐

Use any OpenAI‑compatible base URL, including Ollama:

```bash
mince --openai-base-url http://localhost:11434/v1 \
  --task "Summarize the project" \
  --files README.md
```

## Tested Providers ⚒️

| Provider | Model | Status |
|----------|-------|--------|
| OpenAI | GPT 5.6 | ✅ |
| Alibaba | Qwen 3.7 |  ✅ |
| Oracle | GPT-OSS-120b | ✅ |
| xAI | Grok 4.3 | ✅ |
| AWS | GPT-OSS-120b | ✅ |


## Notes 🗒️

- Large files are skipped automatically
- Binary files are not supported
- JSON Schema mode is best when you need machine‑readable output
- MinCE is tested on and assisted by `GPT 5.6 Luna`

## Command line arguments 📋

All the `mince` CLI arguments for reference.

| Argument | Description |
|----------|-------------|
| `-h`, `--help` | Show the help message and exit. |
| `-a TEXT`, `--ask TEXT` | Prompt without file context (use `-` to read from standard input). |
| `--ask-file FILE` | Read the ask prompt from the given file. |
| `-t TEXT`, `--task TEXT` | Task/prompt for the model with file context (use `-` to read from standard input). |
| `--task-file FILE` | Read the task/prompt from the given file. |
| `-f FILE...`, `--files FILE...` | Files to include as context. |
| `--files-list FILE` | Read context-file paths from a file, one per line. |
| `-p NAME`, `--profile NAME` | Select a configuration profile. |
| `-o FILE`, `--output-file FILE` | Write the response to the given file, overwriting it if it exists. |
| `-P`, `--patch` | Patch specified files and write changes to the filename plus the patch suffix. |
| `-R`, `--patch-review` | Confirm changes before writing to filenames without the suffix, unless a suffix is overridden. |
| `--patch-suffix SUFFIX` | Set the suffix for patched files (default: `.mcepatched`). |
| `--patch-save [BOOL]` | Save the patch file under `~/.local/state/mince/patches` (default: `on`). |
| `--plan` | Generate and review a prompt before using it as the task. |
| `--system-prompt TEXT` | Override the configured system prompt. |
| `--system-prompt-file FILE` | Read the system prompt from the given file. |
| `--patch-system-prompt TEXT` | Set the system prompt for patch mode. |
| `--plan-system-prompt TEXT` | Set the system prompt for plan mode. |
| `--model MODEL` | Override the configured model. |
| `--list-models` | List available models. |
| `--openai-base-url URL` | Set the OpenAI-compatible API base URL. |
| `--openai-proxy URL` | Set an HTTP(S) proxy URL. |
| `--openai-organization TEXT` | Set an optional organization ID. |
| `--openai-project TEXT` | Set an optional project name or ID. |
| `--openai-service-tier {off,auto,default,flex,scale,priority}` | Select the service tier. |
| `--response-format {text,json,schema}` | Select the LLM response format. |
| `--stream [BOOL]` | Stream text responses as they are generated. |
| `--schema-file FILE` | Load a JSON Schema; required with `--response-format schema`. |
| `--response-verbosity {low,medium,high,off}` | Set the verbosity level for text responses. |
| `--temperature FLOAT` | Set the sampling temperature from 0.0 to 2.0, or `off`. |
| `--top-p FLOAT` | Set top-p nucleus sampling from 0.0 to 1.0, or `off`. |
| `--openai-reasoning {none,minimal,low,medium,high,xhigh,max}` | Set the reasoning effort level. |
| `--reasoning-mode {standard,pro}` | Select standard or pro reasoning mode. |
| `--openai-extra-body KEY=VALUE[,KEY=VALUE,...]` | Add custom model parameters. |
| `--token-limit LIMIT` | Set the maximum allowed estimated input-token count. |
| `--token-cost INPUT:OUTPUT` | Set input and output costs per million tokens, or `off`. |
| `--estimate-only` | Print only the estimated input-token count and exit. |
| `--max-output-tokens LIMIT` | Set the maximum output tokens the LLM may use. |
| `--llm-timeout SECONDS` | Set the API request timeout. |
| `--linenum-system-prompt TEXT` | Set the system prompt for handling context-file line numbers. |
| `--no-line-numbers [BOOL]` | Do not prefix line numbers to context files. |
| `--print-reasoning` | Include reasoning output in `<think>` tags. |
| `--print-default-config` | Print the built-in default configuration as JSON. |
| `--print-current-config` | Print the stored configuration file, creating it if missing. |
| `--set-config NAME=VALUE` | Set a configuration value (may be repeated). |
| `--get-config [NAME]` | Get a configuration value, or all values if NAME is omitted. |
| `--log [BOOL]` | Enable or disable local session logging under `~/.local/state/mince/logs`. |
| `--no-api-log [BOOL]` | Do not store requests and responses in the OpenAI-compatible API. |
| `--quiet [BOOL]` | Suppress extra output such as statistics and information messages. |
| `--debug` | Output request and response objects within debug tags. |
| `--init` | Initialize and interactively change the default configuration file. |
| `--init-profile NAME` | Interactively initialize a configuration profile. |
| `--copy-profile NEW_NAME` | Copy the selected configuration profile to a new profile. |
| `--remove-profile NAME` | Remove a configuration profile. |
| `--list-profiles` | List available configuration profiles. |

Environment variable reference.

| Environment Variable | Description |
|----------------------|-------------|
| OPENAI_API_KEY       | OpenAI-compatible API key |


## Usage Notes 🪧

**Prevent incorrect cost calculation when specifying --model:**

If token costs are set in the configuration and `--model` is specified, `--token-cost` must also be specified, otherwise the cost calculation will be absent to prevent inaccuracies.


## Make targets 🚀

The project ships with a **Makefile** that handles both *user* and *system‑wide* installations.
All targets are **idempotent** – running them twice will simply refresh the existing install.

| Target | What it does |
|--------|--------------|
| `make install-user` | Creates a per‑user virtual‑env under `~/.local/share/mince`, installs the Python dependencies, copies the `mince` script, and drops a tiny launcher into `~/.local/bin/mince`. |
| `make uninstall-user` | Removes the user‑local install (launcher, virtual‑env and state directory). |
| `make update-user` | Re‑copies the script, upgrades the virtual‑env’s `pip` and the core packages (`openai`, `tiktoken`). |
| `make install-global` | Performs the same steps as *install‑user* but under `/opt/mince` (code) and `/usr/local/bin/mince` (launcher).  Uses `sudo` when needed. |
| `make uninstall-global` | Deletes the global install and the associated state directory. |
| `make update-global` | Refreshes a global install – identical to *update‑user* but with `sudo`. |
| `make update` | Auto‑detects whether a **user** or **global** install exists and runs the appropriate update target. |
| `make install` | Alias for `install-user` |
| `make shell` | Drops you into a Bash shell with the correct virtual‑env activated (`source …/bin/activate`). Handy for debugging or ad‑hoc runs. |
| `make help` | Prints this table and a short description of each target. |

## License and Copyright 📄

This project is licensed under the **Apache-2.0 License**

© 2026 Southland Systems, Ontario, Canada

