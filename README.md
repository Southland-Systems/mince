![MinCE logo](mince.png)

## What it does ✨

- **Context-aware assistance:** answers direct questions or performs tasks using local files, file lists, standard input, editor-authored prompts, and reusable session context.
- **OpenAI-compatible by design:** connects to hosted providers or local model servers through configurable API URLs, keys, proxies, organizations, projects, service tiers, sampling controls, reasoning settings, and custom request parameters.
- **Flexible output contracts:** generates plain text, streamed text, JSON objects, or JSON Schema-validated Structured Outputs; responses can also be written directly to files.
- **Composable prompting:** supports system-prompt files, task files, a reusable prompt library with nested expansion, mode-specific prompts, and configuration profiles with inheritance.
- **Planning before execution:** turns a task and its context into a reviewable next-step prompt before making the primary request.
- **Structured code changes:** produces line-aware, multi-file patch manifests that preserve declared encodings and line endings, show unified diffs, support iterative revisions and review, save artifacts, and can be applied or printed later.
- **Git-aware patch workflows:** writes suffixed patch files by default, can update approved files in place, and optionally creates, commits, merges, or removes isolated patch branches.
- **Reviewed shell automation:** generates shell-command manifests with reasons, supports multi-turn command workflows and revisions, enforces per-command timeouts, and restricts network address families on Linux unless networking is explicitly enabled.
- **Tool-calling agents:** runs confirmed or automatic multi-turn controller sessions that can patch files, run shell commands, delegate through named agent profiles, retain pinned context, and end with an auditable tool history.
- **Scalable tree processing:** recursively processes filtered file trees with extension-specific tasks and system prompts, bounded parallelism, adaptive retry/backoff, persistent progress, resumable work, and combined Markdown reports.
- **Session traceability:** stores request state, checksums, responses, reasoning, diffs, shell output, and applied-patch records; sessions can be reused, inspected as JSON, viewed through a pager, or expired automatically.
- **Operational visibility:** provides input-token estimates, API usage and cost estimates, response statistics, local logging, API-side storage controls, debug request output, and model discovery.

## Requirements 📦

- `python` 3.10 or newer and the `pip` package manager
- `systemd-run` for `mince-contain`
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

Run offline tests (mince must be installed)

```bash
cd mince
python mince-test
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

Generate a patch, review the diff, and write approved existing-file changes in place (the manifest may also create new files):

```bash
cp /etc/passwd .
mince --patch --patch-review -f passwd -t "Remove lines 1-5 from 'passwd' \
and create a new file called 'passwd-new' with those lines."
```

Manage patch changes using a git branch named `mcebranch`:

```bash
mince --patch --patch-review --patch-branch -f mince README.md \
  -t 'Refresh the command line arguments in `README.md` from `mince`.'

mince --patch --patch-review --patch-branch -f README.md \
  -t 'Rewrite the language to be professional.'

# revert last commit
git reset --hard HEAD~1
git diff HEAD~1

mince --patch --patch-review --patch-branch -f README.md \
  -t 'Rewrite the language to use a professional tone.'

mince -M Updated README with improved language.
```

Apply a suffixed patch from a --patch-review declined session at turn two:

```bash
mince -S .patched --patch-file-apply mince-1785553265-lfaUfaDq 1
```

Plan mode asks the model to create prompt for the next step using the supplied context:

```bash
mince --plan \
  --task "Review the error handling and propose the next implementation step" \
  --files src/main.py README.md
```

Perform shell tasks:

```bash
mince -p task --shell -t 'List the content of the current directory, ' \
  'and then write that listing to a file called "listing.txt" in the next turn. Then get the content of the file "/etc/passwd".'
```

Run a task in automatic agent mode with `mince-contain`:

```bash
mince-contain --contain-write-path . -p task --agent  --agent-auto \
  --task 'Determine the globally installed software development tools and write using "patch" as Markdown format to filename `sdk.md`.'
```

Create a chess game with python:

```bash
mince-contain --contain-write-path . -p ollama --agent --agent-auto --shell-networking \
  --task 'Create or continue the text based chess game using `python.chess` module in the `.venv` environment. ' \
  'Create or change any support scripts as required.'
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
```

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

## Local model servers 🌐

Use any OpenAI‑compatible base URL, including Ollama:

```bash
mince --base-url http://localhost:11434/v1 \
  --task "Summarize the project" \
  --files README.md
```

## Security and Containment 🔐

- Use `mince-contain` as a drop-in replacement for `mince` to run inside a read-only container
- Supply `--shell-networking` to enable network access during agent and shell operations
- `mince-contain --contain-help` provides extensive options to customize the container environment


## Tested Providers ⚒️

| Provider | Model | Status |
|----------|-------|--------|
| OpenAI | GPT 6 Astra | ✅ |
| Alibaba | Qwen 3.8 |  ✅ |
| Oracle | GPT-OSS-120b | ✅ |
| xAI | Grok 4.5  | ✅ |
| AWS | GPT-OSS-120b | ✅ |
| Ollama | Ornith 1.5 9b | ✅ |


## Notes 🗒️

- Large files are skipped automatically
- Binary files are not supported
- JSON Schema mode is best when you need machine‑readable output
- Token estimation is provided by `tiktoken` which will download an encoder on first use
- MinCE is tested on and assisted by `GPT 5.6 Terra` and locally tested on `Ollama` with `Ornith 1.5 9b`

## Command line arguments 📋

All public `mince` CLI arguments for reference. Options that modify a configuration profile use the profile selected with `-p` or `--profile`.

| Argument | Description |
|----------|-------------|
| `-h`, `--help` | Show the help message and exit. |
| `-a TEXT`, `--ask TEXT` | Prompt without file context; use `-` for standard input or `e` to edit with `$EDITOR`. |
| `--ask-file FILE...` | Read and combine an ask prompt from one or more files. |
| `-t TEXT`, `--task TEXT` | Task or prompt for the model with file context; use `-` for standard input or `e` to edit. |
| `--task-file FILE...` | Read and combine a contextual task or prompt from one or more files. |
| `--plan [BOOL]` | Generate and review an AI prompt from the task and context before using it as the task. |
| `--agent` | Run a confirmed multi-turn agent session that uses controller tool calls. |
| `--agent-auto` | Automatically confirm agent tool calls and display each call before execution; agent patches overwrite source files unless `--patch-suffix` is supplied. Requires `--agent`. |
| `--agent-profile NAME[,NAME...]` | Load stored agent profiles as individually named agent controller tools. Requires `--agent`. |
| `-f FILE...`, `--files FILE...` | Include the specified files as context; use `-` for standard input. |
| `--files-list FILE...` | Read context-file paths from one or more files; blank lines and lines beginning with `#` are ignored. |
| `-p NAME`, `--profile NAME` | Select a configuration profile. |
| `-o FILE`, `--output-file FILE` | Write response output to the given file, overwriting it if it exists. |
| `--shell [BOOL]` | Generate, review, and run shell commands for the task. |
| `--shell-networking` | Allow shell commands, including agent shell tools, to use network address families other than `AF_UNIX`. |
| `--patch [BOOL]` | Generate a structured multi-file patch and write changed files using the patch suffix; requires a task and context files. |
| `--patch-branch [BOOL\|NAME]` | Use a git branch for patch changes; the default branch is `mcebranch`, and custom names receive an `mce` prefix when needed. |
| `-D [NAME]`, `--patch-branch-remove [NAME]` | Delete a patch branch; defaults to `mcebranch`. |
| `-M TEXT...`, `--patch-merge TEXT...` | Squash-merge the selected patch branch and commit the result with `TEXT`; the default branch is `mcebranch`. |
| `--patch-review [BOOL]` | Review the generated diff before writing; approved changes use original files by default unless a patch suffix is explicitly supplied. |
| `-S SUFFIX`, `--patch-suffix SUFFIX` | Set the suffix for patched files; the default is `.mcepatched`. |
| `--patch-save [BOOL]` | Save generated patch files under `~/.local/state/mince/patches`; the default is `on`. |
| `--patch-file-apply SESSION_OR_PATH [TURN]` | Apply a saved session patch, optionally from a specific turn, or apply a JSON patch manifest file. |
| `--patch-file-print SESSION_OR_PATH [TURN]` | Print the diff from a saved session patch, optionally from a specific turn, or from a JSON patch manifest file. |
| `--noninteractive` | Disable review prompts, save the response or patch artifacts, and exit. |
| `--reuse-session SESSION_NAME [TURN]` | Reuse saved context and task state from a session; optionally select a completed turn. Tree mode resumes unfinished work. |
| `--reuse-session-skip-verify` | Skip checksum verification of reused session context files. |
| `--tree-files PATH...` | Recursively process the specified files or directories in tree mode. |
| `--tree-files-list FILE...` | Read tree-mode file or directory roots from one or more files. |
| `--tree-task TEXT...` | Set the tree-mode task directly; use `-` for standard input or `e` to edit. |
| `--tree-task-file FILE...` | Read extension-specific, wildcard, or overall tree tasks; use `.ext:task`, `*:task`, or an unprefixed overall task line. |
| `--tree-system-prompt-file FILE` | Read extension-specific, wildcard, or overall tree system prompts using the same line format as `--tree-task-file`. |
| `--tree-exclude PATTERN...` | Exclude tree files matching any supplied pattern. |
| `--tree-exclude-git [BOOL]` | Exclude `.git` directories from tree search; the default is `on`. |
| `--tree-include PATTERN...` | Include only tree files matching at least one supplied pattern. |
| `--tree-show-only` | Print the filtered tree file list and exit without making API calls. |
| `--tree-parallel [N]` | Set the maximum number of concurrent tree requests; the default is `16`, and `N` must be at least `1`. |
| `--system-prompt TEXT` | Override the configured system prompt. |
| `--system-prompt-file FILE` | Read the system prompt from the given file. |
| `--system-prompt-with-task [BOOL]` | Append the task to the system prompt instead of including it in the user prompt. |
| `--linenum-system-prompt TEXT` | Set the system prompt used to explain or handle context-file line numbers. |
| `--patch-system-prompt TEXT` | Set the system prompt used for patch mode. |
| `--shell-system-prompt TEXT` | Set the system prompt used for shell-command mode. |
| `--plan-system-prompt TEXT` | Set the system prompt used for plan mode. |
| `--prompt-expansion [BOOL]` | Expand `^^promptname^^` references using the prompt library; the default is `off`. |
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
| `--response-verbosity {low,medium,high,off}` | Set the verbosity level for text responses; the default is `off`. |
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
| `--no-line-numbers [BOOL]` | When true, omit line-number prefixes from context files. |
| `--print-reasoning [BOOL]` | Include reasoning output in `<think>` tags. |
| `--print-default-config` | Print the built-in default configuration as JSON. |
| `--print-current-config` | Print the stored configuration file, creating it if missing; the API key is masked. |
| `--set-config NAME=VALUE` | Set a configuration value; may be repeated, and `DEFAULT` resets a value. |
| `--set-config-from NAME PROFILE` | Set a configuration value in the selected profile from another profile. |
| `--get-config [NAME]` | Print one configuration value, or all values when `NAME` is omitted. |
| `--log [BOOL]` | Enable or disable local session logging under `~/.local/state/mince/logs`; the default is `on`, and tree mode always logs its work. |
| `--no-api-log [BOOL]` | Control API-side request and response storage; the bare option disables storage. |
| `--quiet [BOOL]` | Suppress extra output such as statistics and informational messages. |
| `--debug` | Print request and response objects inside debug tags. |
| `--init` | Initialize and interactively change the default configuration file. |
| `--init-profile NAME` | Interactively initialize a new configuration profile. |
| `--copy-profile NEW_NAME` | Copy the selected configuration profile to a new profile. |
| `--remove-profile NAME` | Remove a configuration profile. |
| `--list-profiles` | List available configuration profiles. |
| `--inherit-profile NEW_NAME` | Create a profile that inherits the selected profile. |
| `--print-profiles [NAME...]` | Display all configuration profiles, or only the named profiles, through the pager. |
| `--print-profiles-json [NAME...]` | Display all configuration profiles, or only the named profiles, as a JSON object keyed by name. |
| `--prompt-list` | List stored prompts and their profile assignments. |
| `--prompt-edit NAME [TEXT...]` | Edit or create a prompt-library entry; additional text forms its content, otherwise `$EDITOR` is opened. |
| `--prompt-assign NAME TYPE` | Prepend a file-backed prompt reference to the selected profile prompt type. Types are `system`, `linenum`, `patch`, `plan`, and `shell`. |
| `--prompt-assign-text NAME TYPE` | Replace the selected profile prompt type with the text stored in the named prompt. |
| `--prompt-assign-replace NAME TYPE` | Replace the selected profile prompt type with only a file-backed reference to the named prompt. |
| `--prompt-unassign NAME [TYPE]` | Remove the named prompt reference from one prompt type, or from all prompt types when `TYPE` is omitted. |
| `--prompt-remove NAME` | Remove references to the named prompt from all profiles and delete its library file. |
| `--prompt-print [NAME...]` | Print all stored prompts or the specified prompt-library entries. |
| `--prompt-print-json [NAME...]` | Print all stored prompts or the specified entries as a JSON object keyed by name. |
| `--agent-profile-edit NAME [TEXT...]` | Edit or create an agent profile; additional text forms its content, otherwise `$EDITOR` is opened. |
| `--agent-profile-description NAME [TEXT...]` | Set an agent profile description from optional text or an editor. |
| `--agent-profile-type NAME [TYPE]` | Set an agent profile type, or omit `TYPE` for `custom`. Types are `custom`, `patch`, `shell`, and `text`. |
| `--agent-profile-copy NAME NEW_NAME` | Copy an agent profile. |
| `--agent-profile-rename NAME NEW_NAME` | Rename an agent profile. |
| `--agent-profile-remove NAME` | Remove an agent profile. |
| `--agent-profile-print-json [NAME...]` | Print stored agent profiles as a JSON object keyed by name. |
| `--agent-profile-list` | List stored agent profile names and descriptions. |
| `--log-view SESSION` | Display a saved local log session. |
| `--patch-view SESSION` | Display a saved patch session. |
| `--tree-view SESSION` | Display a saved combined tree report. |
| `--state-print-json [SESSION [TURN] [TYPE...]]` | Print saved state artifacts as JSON; with no arguments, list available artifact types. |
| `--shell-session-print-json SESSION [TURN]` | Print a saved shell-session response as JSON, optionally for a specific turn. |
| `--remove-expired-data [KEEP_DAYS]` | Delete logs, patches, tree output, and state data older than `KEEP_DAYS`; the default is `60`. |

Environment variable reference.

| Environment variable | Description |
|----------------------|-------------|
| `OPENAI_API_KEY` | OpenAI-compatible API key; it overrides the key stored in the selected configuration profile. |
| `EDITOR` | Editor command used for `e` prompts and interactive plan, patch-review, and prompt editing. |

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

## Usage Notes 🪧

**Prevent incorrect cost calculation when specifying --model**

If token costs are set in the configuration and `--model` is specified, `--token-cost` must also be specified, otherwise the cost calculation will be absent to prevent inaccuracies.


## Known Issues and Reporting ⚠️

**Agent using incorrect tool calls**

Ensure the default agent system prompt does not contain tool call instructions, use `--prompt-reset-default agent` to reset the agent system prompt.

**Command line arguments may clash**

Mixing combinations of command line arguments may lead to unexpected behaviour.

**Reporting Issues**

Create an Issue on GitHub or fill out the contact form on https://southlandsys.com or email contact@southlandsys.com (no reply will be given). Include as much detail as possible to ensure the issue is resolved.

Reporting an issue is much appreciated, reporting improves quality for everyone.

## Repository Locations 📍

https://github.com/Southland-Systems/mince

https://codeberg.org/Southland-Systems/mince

## License and Copyright 📄

This project is licensed under the **Apache-2.0 License**

© 2026 Southland Systems, Ontario, Canada
