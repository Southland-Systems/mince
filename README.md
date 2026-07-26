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

## Basic Usage 💡

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

Validate structured output against the included example JSON Schema:

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

Preview the files selected by tree filters without making API requests:

```bash
mince --tree-files src tests --tree-include '*.py' --tree-exclude '*/.venv/*' --tree-show-only
```

Create and reuse a prompt-library entry:

```bash
mince --prompt-edit review 'Review the public API for compatibility risks.'
mince --prompt-expansion --task '^^review^^' --files src/api.py
```

Prepend the prompt-library entry to the default system prompt:

```bash
mince --prompt-assign review config system
mince --get-config system_prompt

Read an ask prompt from standard input:

```bash
mince --ask - <file
```

Compose an ask prompt in `$EDITOR`:

```bash
mince --ask e
```

Estimate input tokens without making an API request:

```bash
mince --estimate-only --task "Summarize the project" --files README.md mince
```

Stream a text response directly to the terminal:

```bash
mince --stream --task "Explain the project structure" --files README.md mince
```

Review saved session output using the printed session name:

```bash
mince --log-view SESSION
mince --patch-view SESSION
mince --tree-view SESSION
```

Copy a configuration option from another profile:

```bash
mince --profile aws_grok --set-config-from base_url aws
```

Run MinCE in a restricted systemd user unit for testing:

```bash
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
mince ---base-url http://localhost:11434/v1 \
  --task "Summarize the project" \
  --files README.md
```

## Core workflows: ask, task, patch, plan, and tree ⚡

MinCE centers on five complementary modes. Each mode provides a focused way to send instructions to an OpenAI-compatible model, from quick answers to repeatable, reviewable changes across a codebase.

### Ask mode — quick answers without file context

Use `--ask` (or `--ask-file`) when the model does not need local file context. The configured system prompt still applies. Pass `-` to read the prompt from standard input, or `e` to compose it in `$EDITOR`. Ask mode is mutually exclusive with contextual task and tree inputs.

### Task mode — turn context into action

Task mode is the primary context-aware workflow. Provide an objective with `--task` or `--task-file` and select files with `--files` or `--files-list`. MinCE assembles the files into bounded, line-numbered context by default, making code reviews, explanations, summaries, and implementation tasks concrete and easy to reference. Files larger than the configured limit are skipped.

### Patch mode — changes you can inspect and trust

Append `--patch` to turn a task into a structured, multi-file edit. The model returns a strict `line_replace_manifest`; MinCE validates the replacement ranges, generates a unified diff, and writes modified files alongside the originals using the `.mcepatched` suffix by default. When enabled, the diff is also saved under `~/.local/state/mince/patches`.

Enable `--patch-review` to inspect the diff and approve or cancel it. Approved changes go to the original files by default; explicitly providing `--patch-suffix` writes the approved result to separate suffixed files instead. Patch mode requires `--task` or `--task-file` together with the files to edit.

### Plan mode — think once, execute with intent

The `--plan` option asks the model to turn the supplied task and file context into a self-contained prompt for the next step. MinCE displays the proposed prompt and offers paging, editing, acceptance, or cancellation; only an accepted plan becomes the actual task. Plan mode works with contextual task inputs and can be combined with `--patch` for a planning phase before a controlled edit.

### Tree mode — scale the same judgement across a codebase

Tree mode makes one focused request per matched file. Start with `--tree-files` or `--tree-files-list`, then provide `--tree-task` or an extension-aware `--tree-task-file`. Directories are traversed recursively, `.git` directories are excluded by default, and `--tree-include` and `--tree-exclude` refine the scope. Requests run concurrently with up to 16 workers by default, adjustable with `--tree-parallel`; transient failures are retried with adaptive concurrency and backoff.

Use `.ext:task`, `*:task`, and unprefixed overall-task lines in `--tree-task-file`. `--tree-system-prompt-file` supports the same extension, wildcard, and overall-prompt selection for system instructions. Per-file results, resumable state, and a consolidated Markdown report are stored under `~/.local/state/mince/trees/SESSION_NAME`. Use `--tree-show-only` to preview the filtered files without API calls, or `--tree-reuse-session NAME` to continue unfinished work. Tree mode cannot be combined with regular ask/task inputs, plan mode, or patch mode.

### Profiles — save your best operating setup

Profiles capture reliable workflows behind a single flag. The default profile resides at `~/.local/state/mince/config.json`; additional named profiles are stored alongside it and can independently configure the model, endpoint, prompts, patch settings, limits, and logging options. Activate a profile with `-p NAME`, initialize or modify one with `--init-profile NAME`, and manage profiles with `--copy-profile`, `--list-profiles`, or `--remove-profile`.

```bash
mince --init-profile review
mince -p review --task "Review the public API" --files src/api.py README.md
```

### Prompt library — reusable instructions

Reusable prompts can be stored as Markdown files in `~/.local/state/mince/prompts/`. `NAME` is the prompt name in the library without the `.md` extension, `PROFILE` is a configuration profile name, and `TYPE` is one of `system`, `linenum`, `patch`, or `plan`.

Create or edit a prompt with `--prompt-edit NAME`, then assign it to a profile with `--prompt-assign NAME PROFILE TYPE`. Assignment prepends a file-backed prompt reference while retaining existing prompt text. Use `--prompt-assign-text` to store the prompt text directly, or `--prompt-assign-replace` to replace the target with only its file reference. `--prompt-unassign NAME PROFILE [TYPE]` removes one file-backed reference, or all prompt-type references when `TYPE` is omitted. Finally, `--prompt-remove NAME` removes references to the prompt from all profiles and deletes its file. Enable `--prompt-expansion` to expand `^^promptname^^` references in tasks and configured prompts.


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

All `mince` CLI arguments for reference. 

| Argument | Description |
|----------|-------------|
| `-h`, `--help` | Show the help message and exit. |
| `-a TEXT`, `--ask TEXT` | Prompt without file context; use `-` for standard input or `e` to edit with `$EDITOR`. |
| `--ask-file FILE` | Read the ask prompt from the given file. |
| `-t TEXT`, `--task TEXT` | Task or prompt for the model with file context; use `-` for standard input or `e` to edit. |
| `--task-file FILE` | Read the contextual task or prompt from the given file. |
| `--plan [BOOL]` | Generate and review an AI prompt from the task and context before using it as the task. |
| `-f FILE...`, `--files FILE...` | Include the specified files as context. |
| `--files-list FILE` | Read context-file paths from a file, one path per line; blank lines and lines beginning with `#` are ignored. |
| `--tree-files PATH...` | Recursively process the specified files or directories in tree mode. |
| `--tree-files-list FILE` | Read tree-mode file or directory roots from a file. |
| `--tree-task TEXT...` | Set the tree-mode task directly; use `-` for standard input or `e` to edit. |
| `--tree-task-file FILE` | Read extension-specific, wildcard, or overall tree tasks; use `.ext:task`, `*:task`, or an unprefixed overall task line. |
| `--tree-system-prompt-file FILE` | Read extension-specific, wildcard, or overall tree system prompts using the same line format. |
| `--tree-exclude PATTERN...` | Exclude tree files matching any supplied pattern. |
| `--tree-exclude-git [BOOL]` | Exclude `.git` directories from tree search; default is `on`. |
| `--tree-include PATTERN...` | Include only tree files matching at least one supplied pattern. |
| `--tree-show-only` | Print the filtered tree file list and exit without making API calls. |
| `--tree-parallel [N]` | Set the maximum number of concurrent tree requests; default is `16`, and `N` must be at least `1`. |
| `--tree-reuse-session NAME` | Use the named tree session output and state so unfinished work can be resumed. |
| `-p NAME`, `--profile NAME` | Select a configuration profile. |
| `--log-view SESSION` | Display a saved local log session. |
| `--patch-view SESSION` | Display a saved patch session. |
| `--tree-view SESSION` | Display a saved combined tree report. |
| `--remove-expired-data [KEEP_DAYS]` | Delete session data older than `KEEP_DAYS` days; defaults to `60` when omitted. |
| `-o FILE`, `--output-file FILE` | Write a regular-mode response to the given file, overwriting it if it exists. |
| `--patch [BOOL]` | Generate a structured multi-file patch and write changed files using the patch suffix; requires a task and context files. |
| `--patch-review [BOOL]` | Review the generated diff before writing; approved changes use original files by default, unless a patch suffix is explicitly provided. |
| `-S SUFFIX`, `--patch-suffix SUFFIX` | Set the suffix for patched files; default is `.mcepatched`. |
| `--patch-save [BOOL]` | Save the generated patch under `~/.local/state/mince/patches`; default is `on`. |
| `--prompt-expansion [BOOL]` | Expand `^^promptname^^` references using the prompt library; default is `off`. |
| `--system-prompt TEXT` | Override the configured system prompt. |
| `--system-prompt-file FILE` | Read the system prompt from the given file. |
| `--patch-system-prompt TEXT` | Set the system prompt used for patch mode. |
| `--plan-system-prompt TEXT` | Set the system prompt used for plan mode. |
| `--model MODEL` | Override the configured model. |
| `--list-models` | List models available from the configured endpoint. |
| `--base-url URL` | Set the OpenAI-compatible API base URL. |
| `--proxy-server URL` | Set an HTTP(S) proxy URL. |
| `--meta-organization TEXT` | Set an optional organization name or ID. |
| `--meta-project TEXT` | Set an optional project name or ID. |
| `--service-tier {off,auto,default,flex,scale,priority}` | Select the service tier. |
| `--response-format {text,json,schema}` | Select text, JSON object, or JSON Schema output. `schema` requires `--schema-file`. |
| `--stream [BOOL]` | Stream generated responses; streaming is supported only for text output. |
| `--schema-file FILE` | Load a JSON Schema for `--response-format schema`. |
| `--response-verbosity {low,medium,high,off}` | Set the verbosity level for text responses; default is `off`. |
| `--temperature FLOAT` | Set sampling temperature from `0.0` to `2.0`, or use `off` to disable it. |
| `--top-p FLOAT` | Set top-p nucleus sampling from `0.0` to `1.0`, or use `off` to disable it. |
| `--reasoning {off,none,minimal,low,medium,high,xhigh,max}` | Set reasoning effort, or use `off` to disable it. |
| `--reasoning-mode {standard,pro}` | Select standard or pro reasoning mode. |
| `--extra-body KEY=VALUE[,KEY=VALUE,...]` | Add custom model parameters. |
| `--token-limit LIMIT` | Set the maximum estimated input-token count; the built-in default is `65534`. |
| `--token-cost INPUT:OUTPUT` | Set input and output costs per million tokens, or use `off` to disable cost estimates. |
| `--estimate-only` | Print only the estimated input-token count and exit without making an API request. |
| `--max-output-tokens LIMIT` | Set the maximum output tokens the model may use; the built-in default is `65534`. |
| `--llm-timeout SECONDS` | Set the API request timeout in seconds; the built-in default is `300`. |
| `--linenum-system-prompt TEXT` | Set the system prompt used to explain or handle context-file line numbers. |
| `--no-line-numbers [BOOL]` | Control whether line-number prefixes are added to context files; `false` disables them. |
| `--print-reasoning [BOOL]` | Include reasoning output in `<think>` tags. |
| `--print-default-config` | Print the built-in default configuration as JSON. |
| `--print-current-config` | Print the stored configuration file, creating it if missing; the API key is masked. |
| `--set-config NAME=VALUE` | Set a configuration value; may be repeated, and `DEFAULT` resets a value. |
| `--set-config-from NAME PROFILE` | Set a configuration value in the selected profile from another profile. |
| `--get-config [NAME]` | Print one configuration value, or all values when `NAME` is omitted. |
| `--log [BOOL]` | Enable or disable local session logging under `~/.local/state/mince/logs`; the default is `on`, and tree mode always logs its work. |
| `--no-api-log [BOOL]` | Disable storing requests and responses in the OpenAI-compatible API. |
| `--quiet [BOOL]` | Suppress extra output such as statistics and informational messages. |
| `--debug` | Print request and response objects inside debug tags. |
| `--init` | Initialize and interactively change the default configuration file. |
| `--init-profile NAME` | Interactively initialize a new configuration profile. |
| `--copy-profile NEW_NAME` | Copy the selected configuration profile to a new profile. |
| `--remove-profile NAME` | Remove a configuration profile. |
| `--list-profiles` | List available configuration profiles. |
| `--show-profiles [NAME...]` | Display all configuration profiles, or only the named profiles, through the pager. |
| `--prompt-list` | List stored prompts and their profile assignments. |
| `--prompt-edit NAME [TEXT...]` | Edit or create a prompt-library entry; additional text forms its content, otherwise `$EDITOR` is opened. |
| `--prompt-assign NAME PROFILE TYPE` | Prepend a file-backed prompt reference to the selected profile prompt type, retaining existing text. |
| `--prompt-assign-text NAME PROFILE TYPE` | Replace the selected profile prompt type with the text stored in the named prompt. |
| `--prompt-assign-replace NAME PROFILE TYPE` | Replace the selected profile prompt type with only a file-backed reference to the named prompt. |
| `--prompt-unassign NAME PROFILE [TYPE]` | Remove the named prompt reference from one prompt type, or from all prompt types when `TYPE` is omitted. |
| `--prompt-remove NAME` | Remove references to the named prompt from all profiles and delete its library file. |
| `--prompt-print NAME` | Print the stored prompt-library entry. |

Environment variable reference.

| Environment variable | Description |
|----------------------|-------------|
| `OPENAI_API_KEY` | OpenAI-compatible API key; it overrides the key stored in the selected configuration profile. |
| `EDITOR` | Editor command used for `e` prompts and interactive plan, patch-review, and prompt editing. |

## Usage Notes 🪧

**Prevent incorrect cost calculation when specifying --model**

If token costs are set in the configuration and `--model` is specified, `--token-cost` must also be specified, otherwise the cost calculation will be absent to prevent inaccuracies.

**Patch is writing added lines and nothing else**

If the patch is writing a new file when it should be a diff, this may happen with large context (over 64k), first reset the patch system prompt to default, then try adding instructions like "prepare a text block based patch using the provided JSON schema" or re-word the current task to be more patch oriented.  Lastly try altering the patch system prompt to be more explicit.

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
