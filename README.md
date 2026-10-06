![mce logo](mce.webp)

## What it does ✨

mce is a command-line assistant for engineering workflows that use local files as model context. It connects to OpenAI-compatible Responses API endpoints and supports focused analysis, precise edits, and reviewable automation.

- **Targeted file changes:** supports precise, single-change editing through line-based, multi-file UTF-8 patch manifests. Patch application checks ranges and LF/CRLF line endings, produces unified diffs, and supports review and iterative revisions.
- **Flexible patch workflows:** writes suffixed copies by default, supports approved in-place changes, and optionally commits changes on dedicated Git branches that can later be squash-merged or removed.
- **Lightweight agent interface:** provides reviewed or automatic multi-turn tool calls for patches, shell commands, file reads, schema-based workers, persistent task lists, and context retention. The compact controller targets baseline context overhead below 5,000 tokens; files, history, and profile schemas increase total request size.
- **Reviewed shell execution:** attaches a reason to every command, supports revisions and follow-up turns, and enforces per-command timeouts.  Shell processes are restricted to `AF_UNIX` socket creation unless networking is explicitly enabled.
- **Filesystem containment with `mcec`:** runs the assistant or `$SHELL` in a transient systemd user service on Linux. The host filesystem is read-only by default, with writable private temporary directories, `~/.local/state/mince`, and explicitly granted paths. Host networking is enabled by default, and most of the invoking environment is forwarded.
- **Cost-conscious operation:** supports provider service tiers such as `flex`, input-token limits, token and cost estimates, and configurable retries. Explicit prompt caching is disabled by default; this does not disable provider-managed automatic caching.
- **Provider customization:** configures API endpoints, credentials, proxies, organization and project metadata, sampling, and reasoning. The `safety_identifier` configuration setting and `extra_body` request parameters support additional provider-specific controls.
- **Structured response contracts:** generates text, streamed text, JSON objects, or JSON Schema-based Structured Outputs. Optional JSON repair handles malformed responses, and response output can be written directly to a file.
- **Composable prompts and profiles:** accepts prompts and context from files, file lists, standard input, or `$EDITOR`; supports reusable prompt-library entries, nested expansion, mode-specific instructions, and configuration-profile inheritance.
- **Planning before execution:** generates a next-step prompt from the task and context for review or editing before submitting the primary request.
- **Recursive batch processing:** processes filtered file trees with extension-specific tasks and system prompts, bounded parallelism, adaptive retry/backoff, persistent progress, and combined Markdown reports.
- **Traceable task sessions:** retains request state, file checksums, responses, available reasoning, and patch or shell artifacts for inspection and reuse. Saved logs, patches, and tree reports can be viewed, exported, or removed by age.
- **Operational diagnostics:** exposes API usage, response statistics, model discovery, local logging, API-side storage controls, and debug request output.

## Requirements 📦

- `python` 3.10 or newer and the `pip` package manager
- `systemd-run` for `mcec`
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

Run offline tests (mce must be installed)

```bash
cd mince
python mince-test
```

## First run 🚀

```bash
mce --init
```

This creates `~/.local/state/mince/config.json`.

## Basic Usage 💡

Ask a direct question without file context:

```bash
mce -a "How are two strings concatenated?"
```

Run a task with local files as context:

```bash
mce -t "Summarize this project" -f README.md src/main.py
```

Read the task and context-file paths from files:

```bash
mce --task-file review-task.txt --files-list review-files.txt
```

Run tree mode over files and directories:

```bash
mce --tree-files src tests --tree-task-file tree-task.txt \
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
mce --response-format json \
  --task "Extract the key settings" \
  --files config.yml
```

Write a response to a file:

```bash
mce -t "Add single-user locking to the provided script. Only output the whole script." \
  -f taskedit.py -o taskedit-new.py
```

Validate structured output against the included example JSON Schema:

```bash
mce --task "Provide the file name and line count as JSON" \
  --files README.md requirements.txt --response-format schema \
  --schema-file filemeta-schema.json
```

Generate a patch, review the diff, and write approved existing-file changes in place (the manifest may also create new files):

```bash
cp /etc/passwd .
mce --patch --patch-review -f passwd -t "Remove lines 1-5 from 'passwd' \
and create a new file called 'passwd-new' with those lines."
```

Manage patch changes using a git branch named `mcebranch`:

```bash
mce --patch --patch-review --patch-branch -f mince README.md \
  -t 'Refresh the command line arguments in `README.md` from `mince`.'

mce --patch --patch-review --patch-branch -f README.md \
  -t 'Rewrite the language to be professional.'

# revert last commit
git reset --hard HEAD~1
git diff HEAD~1

mce --patch --patch-review --patch-branch -f README.md \
  -t 'Rewrite the language to use a professional tone.'

mce -M Updated README with improved language.
```

Apply a suffixed patch from a --patch-review declined session at turn two:

```bash
mce -S .patched --patch-file-apply mince-1785553265-lfaUfaDq 1
```

Plan mode asks the model to create prompt for the next step using the supplied context:

```bash
mce --plan \
  --task "Review the error handling and propose the next implementation step" \
  --files src/main.py README.md
```

Generate, review, and execute shell commands:

```bash
mce -p task --shell \
  --task 'List the current directory, write the listing to "listing.txt", and then read "/etc/passwd".'
```

Run a task in automatic agent mode with `mcec`:

```bash
mcec --contain-write-path . -p task --agent  --agent-auto \
  --task 'Determine the globally installed software development tools and write using "patch" as Markdown format to filename `sdk.md`.'
```

Create or extend a text-based chess game:

```bash
mcec --contain-write-path . -p ollama --agent --agent-auto --shell-networking \
  --task 'Create or continue a text-based chess game using the python.chess module in .venv. Create or update support scripts as needed.'
```

Create a dedicated 'ask' profile from the default profile:

```bash
mce --copy-profile a
mce --init-profile a

mce -p a -a 'How is a file read in Go lang?'
```

Preview the files selected by tree filters without making API requests:

```bash
mce --tree-files src tests --tree-include '*.py' --tree-exclude '*/.venv/*' --tree-show-only
```

Create and reuse a prompt-library entry:

```bash
mce --prompt-edit review 'Review the public API for compatibility risks.'
mce --prompt-expansion --task '^^review^^' --files src/api.py
```

Prepend the prompt-library entry to the default system prompt:

```bash
mce --profile config --prompt-assign review system
mce --get-config system_prompt
```

Read an ask prompt from standard input:

```bash
mce --ask - <file
```

Compose an ask prompt in `$EDITOR`:

```bash
mce --ask e
```

Estimate input tokens without making an API request:

```bash
mce --estimate-only --task "Summarize the project" --files README.md mince
```

Stream a text response directly to the terminal:

```bash
mce --stream --task "Explain the project structure" --files README.md mince
```

Review saved session output using the printed session name:

```bash
mce --log-view SESSION
mce --patch-view SESSION
mce --tree-view SESSION
```

Copy a configuration option from another profile:

```bash
mce --profile aws_grok --set-config-from base_url aws
```

Use a `flex` service tier, omit explicit prompt caching, and allow three additional transient-failure retries:

```bash
mce --service-tier flex --explicit-prompt-cache off --retry 3 \
  --task "Identify one actionable reliability issue" --files src/main.py
```

Service-tier and caching support depend on the endpoint. Explicit caching is already `off` by default.

Configure an API safety identifier in the selected configuration profile:

```bash
mce --set-config safety_identifier=engineering-cli
```

Attempt JSON repair before parsing structured output:

```bash
mce --response-format json --response-json-repair \
  --task "Extract the key settings as JSON" --files config.yml
```

Run a reviewed agent session with a named patch worker and configurable context expiry:

```bash
mce --agent-profile-type code_patch patch
mce --agent-profile-description code_patch 'Generate minimal, focused patches.'
mce --agent-tool-list --agent-profile code_patch
mce --agent --agent-profile code_patch --agent-context-expires 12 6 24 \
  --task "Review the module and fix one clearly identified defect" --files src/main.py
```

`--agent-context-expires` sets `DEFAULT [MIN] [MAX]` in controller turns. Files supplied through `--files` are pinned rather than expired.

Provide fresh context from an existing, trusted executable before each agent controller request:

```bash
mce --agent --agent-hook-context ./project-status.sh \
  --task "Assess the project's current status" --files README.md
```

Hook scripts run directly, without tool-call review. Only standard output from successful executions is included, in `<additional_context>` blocks.

Inspect the expanded agent system prompt or restore its built-in library entry:

```bash
mce --get-config-detail agent_system_prompt
mce --prompt-reset-default agent
```

Inspect artifacts from the first saved session turn, replacing `SESSION` with the printed session name:

```bash
mce --state-print-json SESSION 0 request_task response
```

## Local model servers 🌐

Use any OpenAI‑compatible base URL, including Ollama:

```bash
mce --base-url http://localhost:11434/v1 \
  --task "Summarize the project" \
  --files README.md
```

## Security and Containment 🔐

- Use `mcec` as a drop-in replacement for `mce` to restrict filesystem writes through a systemd sandbox; state and private temporary directories remain writable by default
- Supply `--shell-networking` to enable network access during agent and shell operations
- `mcec --contain-help` provides extensive options to customize the sandbox environment


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
- `mce` is tested on and assisted by `GPT 6.1 Sol` and locally tested on `Ollama` with `Ornith 1.5 9b`

## Command line arguments for `mce` 📋

Public arguments implemented by `mce`. Select a stored configuration profile with `-p` or `--profile`; the default is `config`. Most runtime settings fall back to that profile when not overridden on the command line.

Options shown with `[BOOL]` accept `on`/`off`, `true`/`false`, `yes`/`no`, or `1`/`0`. Session `TURN` values are zero-based, non-negative integers.

| Argument | Description |
|----------|-------------|
| `-h`, `--help` | Show the help message and exit. |
| `-a TEXT`, `--ask TEXT` | Prompt without file context; use `-` for standard input or `e` to edit with `$EDITOR`. |
| `--ask-file FILE...` | Read and combine ask prompts from one or more files; may be repeated. |
| `-t TEXT`, `--task TEXT` | Supply a contextual task as one argument; use `-` for standard input or `e` to edit. Shell and agent tasks may omit file context. |
| `--task-file FILE...` | Read and combine task prompts from one or more files; may be repeated. |
| `--plan [BOOL]` | Generate a next-step prompt from the task and context for review or editing before using it as the task. |
| `--agent` | Run a reviewed, multi-turn agent session using controller tool calls. |
| `--agent-auto` | Automatically confirm agent tool calls and display each before execution. Agent patches overwrite source files unless `--patch-suffix` is supplied. Requires `--agent`. |
| `--agent-context-expires DEFAULT [MIN] [MAX]` | Set agent context expiry in controller turns; defaults to `12 6 24`. Values must satisfy `MIN <= DEFAULT <= MAX`. Requires `--agent`. |
| `--agent-hook-context SCRIPT...` | Execute scripts before each controller request and include successful stdout in `<additional_context>` blocks. Scripts run directly without tool-call review. Requires `--agent`. |
| `--agent-profile NAME[,NAME...]` | Load stored profiles as `agent_NAME` controller tools; accepts comma-separated names and may be repeated. Use with `--agent` or `--agent-tool-list`. |
| `--agent-tool-list` | List built-in tool names and descriptions, plus any selected `--agent-profile` tools, without running a session. |
| `-f FILE...`, `--files FILE...` | Include files as context; use `-` for standard input. In agent mode, context supplied here is pinned. |
| `--files-list FILE...` | Read context paths from one or more list files; blank lines and lines beginning with `#` are ignored. May be repeated. |
| `-p NAME`, `--profile NAME` | Select an existing configuration profile. |
| `-o FILE`, `--output-file FILE` | Write response output to the given file, overwriting it if it exists. |
| `--shell [BOOL]` | Generate, review, and execute shell-command manifests for the task, with follow-up turns as needed. |
| `--shell-networking [BOOL]` | Allow shell commands, including agent shell tools, to create sockets using address families other than `AF_UNIX`. Defaults to `off`; requires shell or agent mode. |
| `--patch [BOOL]` | Generate a line-based, multi-file patch. Changed files use suffixed output unless review or branch settings select in-place writes. Requires readable context files; standard input is not supported. |
| `--patch-branch [BOOL\|NAME]` | Use an `mce`-prefixed Git branch and commit patch changes; defaults to `mcebranch` and overrides suffix settings. Also selects the branch for `--patch-merge` or `--patch-file-apply`. |
| `-D [NAME]`, `--patch-branch-remove [NAME]` | Delete a patch branch, including unmerged commits; defaults to `mcebranch`. |
| `-M TEXT...`, `--patch-merge TEXT...` | Squash-merge the selected patch branch, commit with the supplied message, and delete the branch after success. Select a custom branch with `--patch-branch`. |
| `--patch-review [BOOL]` | Review diffs before writing. Approved changes use original paths unless a suffix override is active; patch generation supports revisions and navigation between patch turns. |
| `-S SUFFIX`, `--patch-suffix SUFFIX` | Override the suffix for patched files; the built-in default is `.mcepatched`. |
| `--patch-save [BOOL]` | Save generated unified diffs and JSON patch manifests under `~/.local/state/mince/patches`; defaults to `on`. |
| `--patch-file-apply SESSION_OR_PATH [TURN]` | Apply a saved session patch, optionally from a specific turn, or a JSON patch manifest file. Honors review, suffix, and branch settings; makes no API request. `TURN` requires a session name. |
| `--patch-file-print SESSION_OR_PATH [TURN]` | Print a unified diff against current files from a saved session patch or JSON manifest, without an API request. `TURN` requires a session name. |
| `--noninteractive` | Disable prompts and force quiet mode and local logging. Task results, generated patches, and fresh shell/agent proposals are saved without review. `--agent-auto`, resumed shell sessions, and `--patch-file-apply` can still execute commands or modify files. |
| `--reuse-session SESSION_NAME [TURN]` | Reuse context paths and task state from a completed turn, latest by default. Supports shell, patch, agent, and tree workflows; agents restore tool history and task lists, and tree mode resumes unfinished work. Patch revision requires `--task`. |
| `--reuse-session-skip-verify` | Skip SHA-256 verification of reused context files; use when file changes are intentional. |
| `--tree-files PATH...` | Recursively process the specified files or directories in tree mode. |
| `--tree-files-list FILE...` | Read tree-mode file or directory roots from one or more list files; may be repeated. |
| `--tree-task TEXT...` | Set the tree-mode task directly; use `-` for standard input or `e` to edit. |
| `--tree-task-file FILE...` | Combine extension-specific, wildcard, and overall tasks from files. Lines use `.ext:task`, `*:task`, or an unprefixed overall task; may be repeated. |
| `--tree-system-prompt-file FILE` | Read extension-specific, wildcard, and overall system prompts using the same line format as `--tree-task-file`. |
| `--tree-exclude PATTERN...` | Exclude tree files matching any supplied pattern. |
| `--tree-exclude-git [BOOL]` | Exclude `.git` directories from tree search; defaults to `on`. |
| `--tree-include PATTERN...` | Include only tree files matching at least one supplied pattern. |
| `--tree-show-only` | Print the filtered tree file list and exit without making API requests. |
| `--tree-parallel [N]` | Set the maximum number of concurrent tree requests; defaults to `16`. `N` must be at least `1`. |
| `--system-prompt TEXT` | Override the configured system prompt. |
| `--system-prompt-file FILE` | Read the system prompt from the given file. |
| `--system-prompt-with-task [BOOL]` | Prepend the task to the system prompt instead of including it in the user prompt. |
| `--linenum-system-prompt TEXT` | Override instructions for handling context-file line numbers. |
| `--patch-system-prompt TEXT` | Override the patch-mode system prompt. |
| `--shell-system-prompt TEXT` | Override the shell-mode system prompt. |
| `--agent-system-prompt TEXT` | Override the agent-mode system prompt. |
| `--plan-system-prompt TEXT` | Override the plan-mode system prompt. |
| `--prompt-expansion [BOOL]` | Expand `^^promptname^^` references using the prompt library, including nested references; defaults to `off`. |
| `--model MODEL` | Override the configured model. |
| `--list-models` | List models available from the configured endpoint. |
| `--base-url URL` | Set the OpenAI-compatible API base URL. |
| `--proxy-server URL` | Set an HTTP(S) proxy URL. |
| `--meta-organization TEXT` | Set an optional organization ID. |
| `--meta-project TEXT` | Set an optional project name or ID. |
| `--service-tier {off,auto,default,flex,scale,priority}` | Select a provider service tier; `off` omits the request parameter. |
| `--response-format {text,json,schema}` | Select text, JSON objects, or a JSON Schema response contract. Custom schema output requires `--schema-file`; patch and shell modes supply built-in schemas. |
| `--response-json-repair [BOOL]` | Attempt to repair malformed JSON before parsing responses or tool arguments; defaults to `off`. |
| `--stream [BOOL]` | Stream text responses. Streaming is disabled for JSON/schema and noninteractive task output; tree and agent modes do not stream. |
| `--explicit-prompt-cache [BOOL]` | Request explicit prompt caching with `prompt_cache_options.mode=explicit`; defaults to `off`. Endpoint support is required. |
| `--schema-file FILE` | Load a JSON Schema response-format document for `--response-format schema`. |
| `--response-verbosity {low,medium,high,off}` | Set verbosity for text responses; defaults to `off`, which omits the setting. |
| `--temperature FLOAT` | Set sampling temperature from `0.0` to `2.0`, or use `off` to omit it. |
| `--top-p FLOAT` | Set top-p nucleus sampling from `0.0` to `1.0`, or use `off` to omit it. |
| `--reasoning {off,none,minimal,low,medium,high,xhigh,max}` | Set reasoning effort; `off` omits reasoning parameters and disables reasoning output. |
| `--reasoning-mode {standard,pro}` | Select the reasoning mode; the built-in default is `standard`. |
| `--extra-body KEY=VALUE[,KEY=VALUE,...]` | Add provider-specific request parameters; boolean and numeric values are converted to their corresponding types. |
| `--token-limit LIMIT` | Set the maximum estimated input-token count; the built-in default is `65534`. |
| `--token-cost INPUT:OUTPUT` | Set input and output costs per million tokens, or use `off` to disable estimates. A model override disables configured costs unless this option is also supplied. |
| `--estimate-only` | Print the estimated input-token count for a regular request or plan without making an API request. Not supported for tree or direct agent sessions. |
| `--max-output-tokens LIMIT` | Set the maximum output tokens the model may use; the built-in default is `65534`. |
| `--llm-timeout SECONDS` | Set the API request and per-shell-command timeout in seconds; the built-in default is `300`. |
| `--retry COUNT` | Set additional retries for transient API failures and invalid agent responses; defaults to `2`. Must be a non-negative integer. |
| `--no-line-numbers [BOOL]` | Omit line-number prefixes when enabled. Patch and agent modes always number file context. |
| `--print-reasoning [BOOL]` | Include available reasoning output in `<think>` tags. |
| `--print-default-config` | Print the built-in default configuration as JSON. |
| `--print-current-config` | Print the stored profile configuration as JSON, rather than a merged inheritance view; masks the API key. |
| `--set-config NAME=VALUE` | Set a value in the selected profile; may be repeated. `DEFAULT` restores the built-in default, or removes the override in an inherited profile. |
| `--set-config-from NAME PROFILE` | Copy a stored configuration value from another profile into the selected profile. |
| `--get-config [NAME]` | Print one effective configuration value, or all values when omitted. `^` marks inherited values; API keys are masked. |
| `--get-config-detail [NAME]` | Print effective settings with resolved system prompts in square brackets, or one setting when named. Includes prompt-file resolution and enabled library expansion; `^` marks inherited values. |
| `--log [BOOL]` | Control local logging under `~/.local/state/mince/logs`; defaults to `on`. Tree mode and `--noninteractive` force logging. |
| `--no-api-log [BOOL]` | Control API-side storage: bare `--no-api-log` or explicit `off` disables storage; explicit `on` enables it. |
| `--quiet [BOOL]` | Suppress extra output such as statistics and informational messages. |
| `--debug` | Print request and response objects inside debug tags. |
| `--init` | Initialize and interactively edit the default configuration file; unavailable with `--noninteractive`. |
| `--init-profile NAME` | Interactively initialize or edit the named configuration profile; unavailable with `--noninteractive`. |
| `--copy-profile NEW_NAME` | Copy the selected profile's stored configuration to a new profile. |
| `--remove-profile NAME` | Remove a configuration profile; the default `config` profile cannot be removed. |
| `--list-profiles` | List available configuration profiles. |
| `--inherit-profile NEW_NAME` | Create a new profile that inherits the selected profile. |
| `--print-profiles [NAME...]` | Display merged configuration profiles, all or only those named, through the pager; API keys are masked. |
| `--print-profiles-json [NAME...]` | Print merged configuration profiles as a JSON object keyed by name; API keys are masked. |
| `--prompt-list` | List stored prompts and their profile assignments. |
| `--prompt-reset-default [TYPE,...]` | Restore selected built-in prompt-library files, or all when omitted. Types are `system`, `linenum`, `patch`, `plan`, `shell`, and `agent`. |
| `--prompt-edit NAME [TEXT...]` | Edit or create a prompt-library entry; additional text forms its content, otherwise `$EDITOR` is opened. |
| `--prompt-assign NAME TYPE` | Prepend a file-backed prompt reference to the selected profile's prompt type. Types are `system`, `linenum`, `patch`, `plan`, `shell`, and `agent`. |
| `--prompt-assign-text NAME TYPE` | Replace the selected profile's prompt type with the named entry's text content. |
| `--prompt-assign-replace NAME TYPE` | Replace the selected profile's prompt type with only a file-backed reference to the named entry. |
| `--prompt-unassign NAME [TYPE]` | Remove a prompt reference from one selected-profile prompt type, or all types when omitted. |
| `--prompt-remove NAME` | Remove references from profiles and delete a custom library entry. Built-in `mce_*` entries are reset instead of deleted. |
| `--prompt-print [NAME...]` | Print all stored prompts or the named entries. |
| `--prompt-print-json [NAME...]` | Print all stored prompts or the named entries as a JSON object keyed by name. |
| `--agent-profile-edit NAME [TEXT...]` | Edit or create an agent profile's schema content using additional text or `$EDITOR`. |
| `--agent-profile-description NAME [TEXT...]` | Set an agent profile's description and instructions using optional text or `$EDITOR`. |
| `--agent-profile-type NAME [TYPE]` | Set the profile type; omit `TYPE` for `custom`. Supported types are `custom`, `patch`, and `shell`; the latter two use built-in response schemas. |
| `--agent-profile-copy NAME NEW_NAME` | Copy an agent profile to a new name. |
| `--agent-profile-rename NAME NEW_NAME` | Rename an agent profile. |
| `--agent-profile-remove NAME` | Remove an agent profile. |
| `--agent-profile-print-json [NAME...]` | Print stored agent-profile documents as JSON keyed by name; prints all when names are omitted. |
| `--agent-profile-list` | List stored agent profile names and descriptions. |
| `--log-view SESSION` | Display a saved local log session. |
| `--patch-view SESSION` | Display a saved unified-diff patch session. |
| `--tree-view SESSION` | Display a saved combined Markdown tree report. |
| `--state-print-json [SESSION [TURN] [TYPE...]]` | Print selected saved artifacts as a JSON object. With no arguments, list artifact types; with a session, default to its latest completed turn. |
| `--shell-session-print-json SESSION [TURN]` | Print a saved shell-session response as JSON, optionally for a specific turn. |
| `--remove-expired-data [KEEP_DAYS]` | Delete logs, patches, tree output, and state data older than `KEEP_DAYS`; defaults to `60`. |

Environment variable reference.

| Environment variable | Description |
|----------------------|-------------|
| `OPENAI_API_KEY` | OpenAI-compatible API key; overrides the key stored in the selected configuration profile. |
| `EDITOR` | Editor command for `e` prompts, plan editing, patch/shell/agent revisions, and prompt or agent-profile editors; defaults to `vi`. |

## Command line arguments for `mcec` 📋

`mcec` runs the assistant in a transient systemd user service. It requires Linux, `systemd-run`, and a running systemd user manager that supports the wrapper's sandbox properties.

```text
mcec [CONTAINMENT_OPTIONS...] [--] [MCE_ARGS...]
```

Containment options are consumed by the wrapper; other arguments are passed unchanged to the assistant. Use `--` to stop wrapper option parsing, `mcec --contain-help` for containment help, or `mce --help` for assistant help. With `--contain-use-shell`, assistant arguments are ignored. Invoking `mcec` without arguments prints help guidance without starting a service.

Options taking one value accept `--option VALUE` or `--option=VALUE`. Bind options require separate `SOURCE DESTINATION` arguments. Read/write grants and bind sources must be existing regular files or directories. Relative grant and bind paths are resolved against the contained working directory; grant an existing parent directory when the assistant needs to create a new file.

| Argument | Description |
|----------|-------------|
| `--contain-write-path PATH`, `-W PATH` | Allow writes to an existing file or directory. May be repeated. |
| `--contain-read-path PATH`, `--contain-read-only-path PATH` | Expose an existing path read-only, including paths otherwise hidden by a private home or private temporary directory. May be repeated. |
| `--contain-bind-read-only SOURCE DESTINATION` | Bind an existing source at a destination and keep it read-only. May be repeated. |
| `--contain-bind-write SOURCE DESTINATION` | Bind an existing source at a writable destination. May be repeated. |
| `--contain-working-directory PATH` | Use an existing directory instead of the current directory. This option's relative path is resolved against the invoking directory. |
| `--contain-home MODE` | Set home visibility to `read-only` (default), `tmpfs`, `inaccessible`, or `off`. Working-directory, runtime, state, and explicit-grant paths are re-exposed as needed. |
| `--contain-state MODE` | Use `persistent` (default), `ephemeral`, or `read-only` state at `~/.local/state/mince`. Ephemeral state is a writable tmpfs without saved configuration or sessions; read-only mode requires an existing state directory. |
| `--contain-private-tmp MODE` | Enable (`on`, default) or disable (`off`) private writable `/tmp` and `/var/tmp`. |
| `--contain-no-private-tmp` | Disable private temporary directories; equivalent to `--contain-private-tmp off`. |
| `--contain-network MODE` | Use `host` networking (default) or `none`. The latter uses a private network namespace and restricts socket creation to `AF_UNIX`. API calls normally require host networking. |
| `--contain-timeout SECONDS` | Stop the transient service after a positive integer number of seconds. |
| `--contain-allow-namespaces` | Allow the contained process to create namespaces. Disabled by default because this may weaken filesystem containment. |
| `--contain-use-shell` | Run `$SHELL` instead of the assistant for sandbox testing. `SHELL` must identify an executable; assistant arguments are ignored. |
| `--contain-dry-run` | Print the `systemd-run` command instead of executing the service. Path validation and state-directory setup still occur. |
| `--contain-help` | Show containment help and exit. |
| `--` | Stop wrapper option parsing and pass all remaining arguments to the assistant unchanged. |

Containment primarily limits filesystem writes; it is not complete isolation. Host networking and most environment variables, including API credentials, remain available by default. `--shell-networking` controls the assistant's shell socket restriction and cannot override `--contain-network none`.

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


## Tests passed 🧪

Last tested: `2026-10-06`

```text

TAP version 13
1..55
ok 1 - prints the built-in configuration offline
ok 2 - supports inherited profile overrides
ok 3 - filters tree inputs without an API
ok 4 - processes tree files through a local API
ok 5 - selects extension-specific tree prompts
ok 6 - creates, assigns, and removes prompt-library entries
ok 7 - expands prompt-library references
ok 8 - loads prompt and context files
ok 9 - lists state artifact types offline
ok 10 - applies patches to multiple files and creates files
ok 11 - inserts patches into empty files
ok 12 - validates patches and preserves line endings
ok 13 - reviews patches interactively without a suffix
ok 14 - handles text and JSON responses from a local API
ok 15 - handles streamed text responses
ok 16 - streams text responses to an output file
ok 17 - enables text streaming from configuration
ok 18 - preserves prompt placement and line-number overrides
ok 19 - handles custom JSON-schema responses
ok 20 - validates and writes an API patch response
ok 21 - records patch artifacts and reapplies saved JSON
ok 22 - applies deletion and replacement patch ranges
ok 23 - rejects reused sessions with changed files
ok 24 - executes shell scripts and saves state offline
ok 25 - handles shell follow-up commands and failures
ok 26 - reports shell command timeouts
ok 27 - reuses completed shell sessions without an extra request
ok 28 - writes and commits patch changes on a git branch
ok 29 - merges and removes patch branches
ok 30 - rejects invalid patch ranges, content, endings, and duplicate paths
ok 31 - applies a saved session patch only once
ok 32 - repairs JSON and controls explicit prompt caching
ok 33 - retries transient but not permanent API failures
ok 34 - disables conflicting task modes for ask requests
ok 35 - revises the last shell command turn after session completion
ok 36 - restricts shell network address families unless enabled
ok 37 - applies native agent patches and refreshes companion file context
ok 38 - updates persistent agent tasks atomically at capacity
ok 39 - retries invalid agent responses and rejects invalid call batches
ok 40 - manages agent profiles and delegates schema-constrained worker requests
ok 41 - reviews plans and preserves accepted, rejected, and saved state
ok 42 - navigates patch revisions and applies the selected state turn
ok 43 - reuses saved shell output without executing commands again
ok 44 - pins agent file context and extends unpinned context expiry
ok 45 - restores selected agent history, tasks, and persisted file context
ok 46 - redacts API keys in configuration output and session logs
ok 47 - writes text and JSON output files without duplicating stdout
ok 48 - estimates tokens and rejects oversized requests before API calls
ok 49 - rejects invalid shell manifests before executing commands
ok 50 - runs agent hooks per turn and omits failed output and stdin
ok 51 - refreshes readfile context without retaining stale files or overwriting snapshots
ok 52 - preserves rejected tool proposals without applying patches or executing commands
ok 53 - revises saved patches with checksum verification explicitly skipped
ok 54 - honors explicit automatic-agent patch suffixes without modifying source files
ok 55 - rejects task-list overflow atomically and renumbers removal batches
```


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
