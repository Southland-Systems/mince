![MinCE logo](mince.png)

## What it does ✨

- MinCE ensures minimal context by giving you full control for maximum result
- Reads one or more local files as context
- Sends a single request to an OpenAI‑compatible model endpoint
- Supports plain text, JSON, and JSON Schema outputs
- Stores your settings in a local config file
- Works with hosted APIs and local OpenAI‑compatible servers
- Keeps the setup lightweight and repeatable

## Requirements 📦

- `python` 3.11 or newer and the `pip` package manager
- `make` from GNU Make or compatible
- Network access to your chosen OpenAI-compatible endpoint
- An API key for the endpoint
- Optional: a local OpenAI‑compatible server

## Install / Update 🛠️


```bash
git clone https://github.com/Southland-Systems/mince.git
cd mince
make install
#make update
```

## First run 🚀

```bash
make init
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

## Local model servers 🌐

Use any OpenAI‑compatible base URL, including Ollama:

```bash
mince --openai-base-url http://address:11434/v1 \
  --task "Summarize the project" \
  --files README.md
```

## Use cases 🎯

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
- Binary or unreadable files are handled as safely as possible.
- JSON Schema mode is best when you need machine‑readable output.

## Make targets 🚀

The project ships with a tiny **Makefile** that handles both *user* and *system‑wide* installations.
All targets are **idempotent** – running them twice will simply refresh the existing install.

| Target | What it does | Where it puts the files |
|--------|--------------|------------------------|
| `make install-user` | Creates a per‑user virtual‑env under `~/.local/share/mince`, installs the Python dependencies, copies the `mince` script, and drops a tiny launcher into `~/.local/bin/mince`. | `~/.local/share/mince/.venv` + `~/.local/bin/mince` |
| `make uninstall-user` | Removes the user‑local install (launcher, virtual‑env and state directory). | — |
| `make update-user` | Re‑copies the script, upgrades the virtual‑env’s `pip` and the core packages (`openai`, `tiktoken`). | Same as *install‑user* |
| `make install-global` | Performs the same steps as *install‑user* but under `/opt/mince` (code) and `/usr/local/bin/mince` (launcher).  Uses `sudo` when needed. | `/opt/mince/.venv` + `/usr/local/bin/mince` |
| `make uninstall-global` | Deletes the global install and the associated state directory. | — |
| `make update-global` | Refreshes a global install – identical to *update‑user* but with `sudo`. | Same as *install‑global* |
| `make update` | Auto‑detects whether a **user** or **global** install exists and runs the appropriate update target. | — |
| `make install` | Alias for `install-user` | — |
| `make shell` | Drops you into a Bash shell with the correct virtual‑env activated (`source …/bin/activate`). Handy for debugging or ad‑hoc runs. | — |
| `make help` | Prints this table and a short description of each target. | — |

