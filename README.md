![MinCE logo](mince.png)

## What it does ✨

- Reads one or more local files as context
- Prefix line numbers to content for improved LLM understanding
- Sends a single request to an OpenAI‑compatible model endpoint
- Supports plain text, JSON, and JSON Schema outputs
- Works with hosted APIs and local OpenAI‑compatible servers

## Requirements 📦

- `python` 3.9 or newer and the `pip` package manager
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
mince --response-format schema \
  --schema-file schema.json \
  --task "Turn the notes into structured output" \
  --files notes.md
```

```bash
mince --task "Add single-user locking to the provided script. \
Only output the whole script with any changes. \
Add commented notes at the end." \
  --files taskedit.py >taskedit-new.py
```

## Local model servers 🌐

Use any OpenAI‑compatible base URL, including Ollama:

```bash
mince --openai-base-url http://localhost:11434/v1 \
  --task "Summarize the project" \
  --files README.md
```

## Use cases 🎯

- Generate source code patches and whole re-writes
- Summarize a repository from a handful of files
- Explain what a legacy script is doing
- Turn meeting notes into a clean recap
- Draft release notes from changelog fragments
- Convert rough notes into polished prose
- Extract key fields from YAML, JSON, or text files
- Review deployment files for clarity
- Compare two versions of a document
- Generate a checklist from a plan
- Create a migration summary
- Rewrite content for a different audience
- Produce a concise executive summary
- Pull action items from a meeting transcript
- Convert incident notes into a postmortem draft
- Turn a spec into a customer-friendly overview
- Extract risks and assumptions from project notes
- Create FAQ-style answers from documentation
- Summarize pull-request context before review
- Describe configuration files in plain English
- Clean up rough draft text
- Turn brainstorming notes into a structured outline
- Identify missing pieces in a draft
- Create a “what changed” summary from file diffs or notes
- Rephrase technical language for non-technical readers
- Produce structured output for downstream automation
- Extract deadlines, owners, and next steps
- Transform scattered notes into a decision log
- Draft handoff notes for another teammate
- Build a compact briefing from several source files
- Create training material from internal notes
- Shape product notes into a feature description
- Turn dense documentation into a friendlier version
- Summarize a design document before a meeting
- Review a roadmap note and highlight priorities
- Convert an outline into a polished article draft
- Generate a quick answer from a bundle of reference files

## Notes 🗒️

- Large files are skipped automatically.
- Binary files are not supported.
- JSON Schema mode is best when you need machine‑readable output.

## Command line arguments 📋

All the `mince` CLI arguments for reference.

| Argument                | Description |
|-------------------------|-------------|
| `--task`                | Task/prompt for the model. |
| `--files`               | Files to include as context. |
| `--init`                | Initialize and interactively change the configuration file. |
| `--system-prompt`       | System prompt override. |
| `--model`               | Override configured model. |
| `--openai-base-url`     | OpenAI‑compatible API base URL. |
| `--openai-organization` | Optional OpenAI organization ID. |
| `--openai-project`      | Optional project name or ID. |
| `--openai-service-tier` | OpenAI service tier (`auto`, `default`, `flex`, `scale`, `priority`). |
| `--response-format`     | Output format: `text` (default), `json`, or `schema`. |
| `--schema-file`         | Path to a JSON Schema file (required for `--response-format schema`). |
| `--temperature`         | Sampling temperature (0.0‑2.0). |
| `--top-p`               | Top‑p nucleus sampling (0.0‑1.0). |
| `--openai-reasoning`    | Reasoning effort level (`none`, `minimal`, `low`, `medium`, `high`, `xhigh`). |
| `--token-limit`         | Maximum allowed input token count. |
| `--max-output-tokens`   | Maximum output tokens the LLM will use. |
| `--llm-timeout`         | Timeout in seconds for the API call. |
| `--print-reasoning`     | Output the reasoning monolog in `<reasoning>` tags with the content in `<response>` tags. |
| `--quiet`               | Suppress printing of extra output (stats, information). |

## Make targets 🚀

The project ships with a tiny **Makefile** that handles both *user* and *system‑wide* installations.
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

This project is licensed under the **Apache-2.0 License**.

© 2026 Southland Systems, Ontario, Canada.

