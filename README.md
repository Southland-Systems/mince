![MinCE logo](mince.png)

## What it does ✨

- Reads one or more local files as context
- Can optionally patch files
- Prefixes line numbers to content for improved LLM understanding
- Sends a single request to an OpenAI‑compatible model endpoint
- Supports text, JSON, and JSON Schema Structured Outputs
- Works with hosted APIs and local OpenAI‑compatible servers
- Creates a context controlled, continuously verified workflow

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

# Update
cd mince
make update

# Uninstall
cd mince
make uninstall-user

# Manual install
(cd mince && cp -a mince ~/.local/bin/ && chmod +x ~/.local/bin/mince \
  && pip install -U -r requirements.txt)
```

## First run 🚀

```bash
mince --init
```

This creates `~/.local/state/mince/config.json`.

## Basic usage 💡

```bash
mince --task "Summarize this project" --files README.md src/main.py
```

```bash
mince --ask "You are an expert programmer specializing in Python. \
How are two strings concatenated?"
```

```bash
mince --system-prompt "You are a senior engineering reviewer." \
  --task "Review the deployment flow" \
  --files docker-compose.yml deploy.py
```

```bash
mince --response-format json \
  --task "Extract the key settings" \
  --files config.yml
```

```bash
mince --task "Add single-user locking to the provided script. \
Only output the whole script with any changes. \
Add commented notes at the end." \
  --files taskedit.py --output-file taskedit-new.py
```

```bash
mince --task "Provide the file name and line count as JSON" \
  --files README.md requirements.txt --response-format schema \
  --schema-file filemeta-schema.json
```

```bash
mince --files passwd --task 'The provided `passwd` file is a \
UNIX account file in "passwd" format. Remove lines 1-5 from `passwd` \
and create a new file called `passwd-new` with those lines.' \
  --patch --patch-review --patch-suffix .patched
```

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
| OpenAI | GPT 5.5 | ✅ |
| Alibaba | Qwen 3.7 |  ✅ |
| Oracle | GPT-OSS-120b | ✅ |
| xAI | Grok 4.3 | ✅ |
| AWS | GPT-OSS-120b | ✅ |


## Notes 🗒️

- Large files are skipped automatically
- Binary files are not supported
- JSON Schema mode is best when you need machine‑readable output
- MinCE is tested on and assisted by `gpt-oss-120b`

## Command line arguments 📋

All the `mince` CLI arguments for reference.

| Argument               | Description |
|------------------------|-------------|
| `--task`               | Task/prompt for the model with file context. |
| `--task-file`          | Read the task/prompt from the given file. |
| `--files`              | Files to include as context. |
| `--ask`                | Prompt without file context or the configured system prompt. |
| `--ask-file`           | Read the ask prompt from the given file. |
| `--output-file`        | Write the response to the given file (overwrites if it exists). |
| `--patch`              | Patch specified files and write changes to the filename + patch suffix. |
| `--patch-review`       | Confirm the changes before writing to filenames *without* the suffix (override with --patch-suffix). |
| `--patch-suffix`       | Suffix for patched files. |
| `--system-prompt`      | System prompt override. |
| `--system-prompt-file` | Read the system prompt from the given file. |
| `--model`              | Override configured model. |
| `--list-models`        | List available models. |
| `--openai-base-url`    | OpenAI-compatible API base URL. |
| `--openai-proxy`       | HTTP(S) proxy URL (eg: http://user:pass@proxy:8080). |
| `--openai-organization`| Optional OpenAI organization ID. |
| `--openai-project`     | Optional project name or ID. |
| `--openai-service-tier`| OpenAI service tier. |
| `--response-format`    | LLM response format in text, JSON or JSON‑Schema. |
| `--schema-file`        | Path to a JSON Schema file (required for --response-format schema). |
| `--response-verbosity` | Verbosity level for text responses (off, low, medium, high). |
| `--temperature`        | Sampling temperature (off, 0.0‑2.0). |
| `--top-p`              | Top‑p nucleus sampling (off, 0.0‑1.0). |
| `--openai-reasoning`   | Reasoning effort level (none, minimal, low, medium, high, xhigh). |
| `--openai-extra-body`  | Custom model parameters (key=value pairs separated by commas). |
| `--token-limit`        | Maximum allowed input token count (65534). |
| `--max-output-tokens`  | Maximum output tokens the LLM will use (65534). |
| `--llm-timeout`        | Timeout in seconds for the API call (300). |
| `--linenum-system-prompt` | System prompt for handling context file line numbers. |
| `--no-line-numbers`    | Do not prefix line numbers to context files. |
| `--print-reasoning`    | Output the reasoning monolog in <reasoning> tags with the content in <response> tags. |
| `--print-default-config` | Print the built‑in default configuration as JSON. |
| `--print-current-config` | Print the stored configuration file (creates it if missing). |
| `--quiet`              | Suppress printing of extra output (stats, information). |
| `--init`               | Initialize and interactively change the configuration file. |
| `--profile`            | Select configuration profile. |
| `--init-profile`       | Interactively initialize a new configuration profile. |
| `--list-profiles`      | List available configuration profiles. |
| `--copy-profile`       | Copy the current configuration profile to a new profile. |
| `--remove-profile`     | Remove a configuration profile. |

Environment variable reference.

| Environment Variable | Description |
|----------------------|-------------|
| OPENAI_API_KEY       | OpenAI-compatible API key |

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

