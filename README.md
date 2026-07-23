![MinCE logo](mince.png)

## What it does ✨

- Answers direct prompts or performs tasks using one or more local files as context
- Sends requests to an OpenAI-compatible model endpoint
- Processes files recursively in tree mode, making one request per matched file
- Generates structured multi-file patches with diffs, optional review, and configurable output suffixes
- Supports text, JSON, JSON Schema Structured Outputs, and streamed text responses
- Supports configuration profiles, custom system prompts, reasoning controls, and model parameters
- Provides optional local session logging, API storage controls, usage statistics, and cost estimates
- Creates a context-controlled, continuously verified workflow and maximizes cost effectiveness

## Core workflows: four modes, one focused assistant ⚡

MinCE centers on four complementary modes. Each mode anchors the model to your selected files while offering varying degrees of control—from quick, precise answers to carefully verified, repeatable edits.

### Task mode — turn context into action

Task mode serves as the primary context-aware workflow. Provide a precise objective via `--task` (or `--task-file`) and specify files with `--files` (or `--files-list`). By default, MinCE assembles these files into a bounded, line-numbered context, which makes code reviews, explanations, and implementation tasks concrete and easy to reference.

### Patch mode — changes you can inspect and trust

Append `--patch` to convert a task into a structured, multi-file edit. The model produces a strict line-replacement manifest. MinCE validates the specified ranges, generates a unified diff, and writes modified files alongside the originals using the `.mcepatched` suffix by default. The diff is also saved to `~/.local/state/mince/patches` for later reference.

Enable `--patch-review` to introduce an approval step: review the diff, then approve or cancel. Approved changes apply to the original files by default. Use `--patch-suffix` if you prefer the result to be written as a separate file. Patch mode requires either `--task` or `--task-file` along with the files to edit.

### Plan mode — think once, execute with intent

The `--plan` flag instructs the model to convert the provided task and file context into a self-contained prompt for the subsequent step. MinCE displays this prompt and requests confirmation; only confirmed plans proceed as the actual task. Combine it with `--patch` to perform a thoughtful planning phase before executing a controlled edit.

### Tree mode — scale the same judgement across a codebase

Tree mode executes one focused request for each matched file. Begin with `--tree-files` (or `--tree-files-list`) and provide `--tree-task` or an extension-aware `--tree-task-file`. Directories are traversed recursively, with `.git` excluded by default. Use `--tree-include` and `--tree-exclude` to refine the scope. Requests execute concurrently, supporting up to 16 workers by default, adjustable with `--tree-parallel`.

Assign distinct instructions to different file types using entries like `.py:task`, `*:task`, and corresponding settings in `--tree-system-prompt-file`. Outputs are saved both per file and in a consolidated Markdown report under `~/.local/state/mince/trees/SESSION_NAME`. Use `--tree-show-only` to preview the filtered files without issuing API calls, or `--tree-reuse-session NAME` to continue an interrupted session.

### Profiles — save your best operating setup

Profiles allow you to capture reliable workflows behind a single flag. The default profile resides at `~/.local/state/mince/config.json`; additional named profiles are stored alongside it and can independently configure the model, endpoint, prompts, patch settings, limits, and logging options. Activate a profile with `-p NAME`, initialize or modify one using `--init-profile NAME`, and manage them via `--copy-profile`, `--list-profiles`, or `--remove-profile`.

```bash
mince --init-profile review
mince -p review --task "Review the public API" --files src/api.py README.md
```

### Prompt library — reusable instructions

Reusable prompts can be stored as Markdown files in `~/.local/state/mince/prompts/`. `NAME` is the prompt name in the library (without the .md extension), `PROFILE` is a configuration profile name, and `TYPE` is one of `system`, `linenum`, `patch`, or `plan`.

Create or edit a prompt with `--prompt-edit NAME`, then assign it to a profile with `--prompt-assign NAME PROFILE TYPE`. Assignment prepends a file-backed prompt reference while retaining existing prompt text. Use `--prompt-assign-text` to store the prompt's text directly, or `--prompt-assign-replace` to replace the target with only its file reference. `--prompt-unassign NAME PROFILE [TYPE]` removes one file-backed reference, or all prompt-type references when `TYPE` is omitted. Finally, `--prompt-remove NAME` removes references to the prompt from all profiles and deletes its file.

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

Run tree mode over files and directories:

```bash
mince --tree-files src tests --tree-task-file tree-task.txt \
  --tree-include '*.py' --tree-exclude '*/.venv/*' --tree-parallel 24
```

The `--tree-task-file` file contains a list of extensions and tasks. Lines may be `.ext:task`, `*:task` or an overall `task`, and they can be repeated.

```text
.py:Create python specific documentation for the provided script.
.py:Use Markdown to format the documentation.
*:Create best effort documentation for the provided file.
Ensure documentation is concise, complete and relevant to the content.
Keep the documentation technical and without conversation.
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

Generate a patch, review the diff, and write the approved result to the original and new file:

```bash
cp /etc/passwd .
mince --patch --patch-review -f passwd -t "Remove lines 1-5 from 'passwd' \
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
| xAI | Grok 4.5  | ✅ |
| AWS | GPT-OSS-120b | ✅ |


## Notes 🗒️

- Large files are skipped automatically
- Binary files are not supported
- JSON Schema mode is best when you need machine‑readable output
- Token estimation is provided by `tiktoken` which will download an encoder on first use
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
| `--tree-files PATH...` | Recursively process files or directories in tree mode. |
| `--tree-files-list FILE` | Read tree-mode file or directory roots from a file, one per line. |
| `--tree-task TEXT...` | Set the required tree-mode task directly (use `-` for standard input). |
| `--tree-task-file FILE` | Read tree-mode tasks from a file; use extension-specific, wildcard, or overall task lines. |
| `--tree-system-prompt-file FILE` | Select tree-mode system prompts by extension (`.ext:prompt`, `*:prompt`, and an overall `prompt`). |
| `--tree-include PATTERN...` | Include only tree files matching at least one pattern. |
| `--tree-exclude PATTERN...` | Exclude tree files matching any pattern. |
| `--tree-exclude-git [BOOL]` | Exclude `.git` directories (default: `on`). |
| `--tree-show-only` | Print only the filtered tree file list and exit without making requests. |
| `--tree-parallel [N]` | Set the maximum number of parallel tree-mode requests (default: `16`). |
| `--tree-reuse-session NAME` | Reuse a named tree session to resume unfinished work. |
| `-p NAME`, `--profile NAME` | Select a configuration profile. |
| `-o FILE`, `--output-file FILE` | Write the response to the given file, overwriting it if it exists. |
| `--patch` | Patch specified files and write changes to the filename plus the patch suffix. |
| `--patch-review` | Confirm changes before writing to filenames without the suffix, unless a suffix is overridden. |
| `-S`, `--patch-suffix SUFFIX` | Set the suffix for patched files (default: `.mcepatched`). |
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
| `--openai-reasoning {off,none,minimal,low,medium,high,xhigh,max}` | Set the reasoning effort level, or `off` to disable it. |
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
| `--prompt-list` | List stored prompts and the profiles to which they are assigned. |
| `--prompt-edit NAME` | Edit or create `NAME` in the prompt library. |
| `--prompt-assign NAME PROFILE TYPE` | Add a file-backed reference to `NAME` in `PROFILE` for `TYPE`, preserving existing prompt text. |
| `--prompt-assign-text NAME PROFILE TYPE` | Replace `PROFILE`'s prompt of `TYPE` with the text from `NAME`. |
| `--prompt-assign-replace NAME PROFILE TYPE` | Replace `PROFILE`'s prompt of `TYPE` with a reference to `NAME` only. |
| `--prompt-unassign NAME PROFILE [TYPE]` | Remove a reference to `NAME` from `PROFILE`'s prompt of `TYPE`; omit `TYPE` to check all prompt types. |
| `--prompt-remove NAME` | Remove references to `NAME` from all profiles and delete it from the prompt library. |

Environment variable reference.

| Environment Variable | Description |
|----------------------|-------------|
| OPENAI_API_KEY       | OpenAI-compatible API key |
| EDITOR | The text editor to use in plan mode |

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
| `make changelog` | Displays the changelog for the last two weeks or last 20 entries. |
| `make help` | Prints this table and a short description of each target. |

## Reporting Issues ⚠️

Create an Issue on GitHub or fill out the contact form on https://southlandsys.com or email contact@southlandsys.com (no reply will be given). Include as much detail as possible to ensure the issue is resolved.

Reporting an issue is much appreciated, reporting improves quality for everyone.

## Repository Locations 📍

https://github.com/Southland-Systems/mince

https://codeberg.org/Southland-Systems/mince

## License and Copyright 📄

This project is licensed under the **Apache-2.0 License**

© 2026 Southland Systems, Ontario, Canada
