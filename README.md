![mce logo](mce.webp)

## What it does ✨

mce is a command-line assistant for engineering workflows that use local files as model context. It connects to OpenAI-compatible Responses API endpoints and supports focused analysis, precise edits, and reviewable automation.

- **Targeted file changes:** proposes edits to existing or new text files, shows unified diffs, and supports review and iterative revisions.
- **Flexible patch workflows:** standalone patch mode writes suffixed copies by default, supports approved in-place changes, and can commit changes on dedicated Git branches.
- **Multi-turn agents:** combines file reads, patches, shell commands, worker delegation, and task tracking. Tools execute automatically by default; use `--agent-review` for confirmation.
- **Reviewed shell execution:** explains each proposed command and supports revisions, follow-up turns, and per-command timeouts. Network socket creation is restricted unless explicitly enabled.
- **Filesystem containment with `mcec`:** limits filesystem writes on Linux. Private temporary directories, assistant state, and explicitly granted paths remain writable by default; containment does not hide all host files or credentials.
- **Cost controls:** provides input-token limits, usage and cost estimates, service-tier selection, configurable retries, and optional explicit prompt caching.
- **Provider customization:** supports OpenAI-compatible endpoints, credentials, proxies, organization and project settings, sampling, and reasoning options.
- **Flexible output:** returns text, streamed text, JSON, or schema-constrained responses, with optional JSON repair and output files.
- **Reusable prompts and profiles:** reads prompts and context from files, file lists, standard input, or `$EDITOR`, and supports prompt-library entries and inherited configuration profiles.
- **Planning before execution:** prepares a next-step prompt for review or editing before the main request.
- **Recursive batch processing:** applies tasks across filtered file trees, with parallel requests, saved progress, and combined Markdown reports.
- **Saved sessions:** retains task context, responses, patches, and shell output for inspection and resumption. Optional tracing helps diagnose command execution.
- **Operational diagnostics:** includes model discovery, request statistics, local logging, API-side storage controls, and debug output.

## Requirements 📦

- Python 3.10 or newer and the `pip` package manager
- Linux and `pyseccomp` for uncontained shell commands with the default socket restrictions
- Linux, `systemd-run`, and a running systemd user manager for `mcec` and contained shell commands
- `make` from GNU Make or compatible for a managed installation
- Network access to your chosen OpenAI-compatible endpoint
- An API key for the endpoint
- Optional: `strace` for system call logging
- Optional: a local OpenAI-compatible server

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

Using a proxy

```bash
export HTTP_PROXY="http://localhost:8888"
export HTTPS_PROXY="http://localhost:8888"
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

This creates `~/.local/state/mince/config.json` and any missing built-in prompt-library files under `~/.local/state/mince/prompts`.

Inspect the selected profile's effective settings, including expanded prompts, or print the built-in defaults:

```bash
mce --get-config-detail
mce --print-default-config
```

### Configuration presets

Select a built-in preset with `-p`: `ask`, `task`, `tree`, `patch`, `planpatch`, `shell`, `plantask`, or `agent`. These inherit shared settings from `config`, so you can configure your endpoint and credentials once.

Internal `mce_*` profiles are read-only. Customize the corresponding preset name or create an inherited profile for your own workflow. Configuration profiles are separate from agent worker profiles.

## Basic Usage 💡

Ask a direct question without file context:

```bash
mce -p ask -a "How are two strings concatenated?"
```

Draft deployment files in a contained, writable workspace reading the API key at runtime so it does not need to be stored locally:

```bash
mkdir -p ~/workspace
cd ~/workspace
mcec -W . -p agent --apikey --reasoning max --response-verbosity high \
  --task 'Draft an Apache HTTPD deployment and hardening script to be run as root, ' \
  'plus a short README. Write files only in this workspace; the system is read-only, ' \
  'do not install services or change system configuration.'
```

Run a task with local files as context:

```bash
mce -p task -t "Summarize this project" -f README.md src/main.py
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

Request structured output using the included example JSON Schema:

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

Manage patch changes using a Git branch named `mcebranch`:

```bash
mce --patch --patch-review --patch-branch -f mince README.md \
  -t 'Update README.md to match the command-line options in mince. Leave mince unchanged.'

mce --patch --patch-review --patch-branch -f README.md \
  -t 'Make the usage examples concise and consistent.'

mce -M "Refresh README usage documentation"
```

Accepted changes are committed on the patch branch. `-M` squash-merges that branch and deletes it after a successful commit.

Apply a suffixed copy of a saved patch after declining review (turn `1` is the second saved turn):

```bash
mce -S .patched --patch-file-apply SESSION 1
```

Plan mode asks the model to create a prompt for the next step using the supplied context:

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

Add `--shell-trace` to retain traces of executed commands in session state. Tracing requires Linux and `strace`; trace files may contain sensitive data.

Run a task in automatic agent mode with `mcec`:

```bash
mcec --contain-write-path . -p task --agent \
  --task 'Determine the globally installed software development tools and write using "patch" as Markdown format to filename `sdk.md`.'
```

Create or extend a text-based chess game:

```bash
mcec --contain-write-path . -p ollama --agent --shell-networking \
  --task 'Create or continue a text-based chess game using the python.chess module in .venv. Create or update support scripts as needed.'
```

Agent tool calls execute without confirmation by default. Add `--agent-review` to review calls and changes. Automatic agent patches overwrite source paths unless `--patch-suffix` is explicitly supplied; a configured suffix alone is ignored. Reviewed agent patches follow the usual `--patch-review` and suffix settings.

Create a custom profile that inherits the `task` preset:

```bash
mce -p task --inherit-profile review
mce -p review --set-config response_verbosity=low
mce -p review -t 'Review the public API for compatibility risks.' -f src/api.py
```

Only your overrides are stored in the child profile; shared settings continue to come from its parent.

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

Request the `flex` service tier and explicit prompt caching when the endpoint supports them:

```bash
mce --service-tier flex --explicit-prompt-cache on \
  --task "Identify one actionable reliability issue" --files src/main.py
```

Service-tier availability, caching behavior, and pricing depend on the provider. Explicit caching is off in the base configuration and on in the built-in presets. Disabling it does not disable the provider's automatic caching.

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
mce --agent --agent-review --patch-review --agent-profile code_patch \
  --agent-context-expires 24 12 48 \
  --task "Review the module and fix one clearly identified defect" --files src/main.py
```

Selected profiles expose `agent_NAME` worker tools. Even `patch` and `shell` workers return structured proposals only; the controller must submit them through `patch` or `shell` to apply edits or execute commands.

Use a stored worker profile for the generic `agent` tool instead of controller continuation:

```bash
mce --agent --agent-profile-default code_patch \
  --task "Fix one clearly identified defect" --files src/main.py
```

`--agent-profile-default` changes only the generic `agent` tool; it does not replace the controller. Additional named worker tools can still be selected with `--agent-profile`.

`--agent-context-expires` sets `DEFAULT [MIN] [MAX]` in controller turns; the built-in values are `24 12 48`. Omitted bounds use their built-in values, and `MIN <= DEFAULT <= MAX` is required. Initial context supplied through `--files` is pinned against expiry; `--files-list` and configured files are not automatically pinned. Pins do not prevent removal under token pressure.


Provide fresh context from an existing, trusted executable before each agent controller request:

```bash
mce --agent --agent-hook-context ./project-status.sh \
  --task "Assess the project's current status" --files README.md
```

Hook scripts run directly, without tool-call review or the shell tool's timeout and socket restrictions. Only standard output from successful executions is included, in `<hook_context>` blocks. Use trusted executables; when invoked through `mcec`, hooks still run inside the wrapper's sandbox.

Inspect the expanded agent system prompt or restore its built-in library entry:

```bash
mce --get-config-detail agent_system_prompt
mce --prompt-reset-default agent
```

### Saved state and resumption

Inspect artifacts from the first saved session turn, replacing `SESSION` with the printed session name:

```bash
mce --state-print-json SESSION 0 request_task response
```

Validated patch manifests and diffs are saved per turn as `response_schema_patch` and `response_diff_patch` under `~/.local/state/mince/state/SESSION/TURN/`, even when logging is off. Successful writes also record `response_schema_patch_applied`.

Shell output and optional traces use indexed files named `response_shell_output_*` and `response_shell_trace_*`. Older sessions may use the unindexed `response_shell_output` filename.

For a turn that executed commands with tracing enabled, export all its shell output and trace files:

```bash
mce --state-print-json SESSION 0 response_shell_output response_shell_trace
```

Replace `0` with the saved turn you want to inspect. You can also request an exact indexed filename.

Resume a saved task or agent session in a new session:

```bash
mce --resume-session SESSION
mce --agent --resume-session SESSION
mce --patch --resume-session SESSION 1 \
  --task "Revise the previous patch without changing the public API"
```

Resumption creates a new session linked to the selected completed turn (latest by default), follows earlier resume links, and continues inherited turn numbering. Context paths and SHA-256 checksums come from saved state; verification is enabled unless `--resume-session-skip-verify` is supplied. Use that override only when file changes are intentional. Patch resumption requires a new `--task`; agent resumption restores saved history, tasks, summaries, and retention metadata. Keep referenced source sessions when cleaning up state.

With `--shell --resume-session SESSION --noninteractive`, saved command turns can execute automatically. Previously recorded shell output is reused instead of rerunning those commands, and a saved `session_end` response exits without execution. Supply a new `--task` to request a revision of the latest reusable command turn within the selected history.

## Local model servers 🌐

Use any OpenAI‑compatible base URL, including Ollama:

```bash
mce --base-url http://localhost:11434/v1 \
  --task "Summarize the project" \
  --files README.md
```

## Security and Containment 🔐

- Agent mode executes tools without confirmation by default. Use `--agent-review` for approval, avoid running as root, and grant only the paths needed for the task.
- Use `mcec` as a drop-in replacement for `mce` to limit filesystem writes. State and private temporary directories remain writable by default; the working directory is not automatically writable.  Use `-W .` to grant it writes.
- By default, shell commands can create only Unix sockets; `--shell-networking` permits other socket families. This setting does not govern API calls or hook scripts. `--shell-timeout SECONDS` limits each command; `0` disables that limit.
- Containment is not complete isolation or a guarantee against data leaks. Host files and credentials can remain accessible, and Unix sockets can provide access to host services. Only send context you are authorized to share with the configured provider.
- Logs, saved state, and traces can contain sensitive content. Review them before sharing. Use `mcec --contain-help` and the argument reference below to check sandbox options and their scope.


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
- `mce` is tested with and assisted by `GPT 6.1 Sol` and locally tested with `Ollama` running `Ornith 1.5 9b`

## Command line arguments for `mce` 📋

Public arguments implemented by `mce`. Select a stored configuration profile with `-p` or `--profile`; the default is `config`. Most runtime settings fall back to that profile when not overridden on the command line.

Options shown with `[BOOL]` accept `on`/`off`, `true`/`false`, `yes`/`no`, or `1`/`0`. Session `TURN` values are zero-based, non-negative integers.

| Argument | Description |
|----------|-------------|
| `-h`, `--help` | Show the help message and exit. |
| `-a TEXT...`, `--ask TEXT...` | Prompt without file context; use `-` for standard input or `e` to edit with `$EDITOR`. |
| `--ask-file FILE...` | Read and combine ask prompts from one or more files; may be repeated. |
| `-t TEXT...`, `--task TEXT...` | Supply a task using one or more text arguments; use `-` for standard input or `e` to edit. Patch, shell, and agent tasks may omit file context. |
| `--task-file FILE...` | Read and combine task prompts from one or more files; may be repeated. |
| `--plan [BOOL]` | Generate a next-step prompt from the task and context for review or editing before using it as the task. With `--noninteractive`, save the plan and stop. |
| `--agent [BOOL]` | Run a multi-turn agent session. Calls execute automatically and are displayed before execution; patches overwrite source paths unless `--patch-suffix` is explicitly supplied. Conflicting standalone patch and shell options are ignored. |
| `--agent-review` | Review agent tool calls and changes before execution. Requires agent mode; accepted patches follow the usual patch-review and suffix settings. |
| `--agent-context-expires DEFAULT [MIN] [MAX]` | Set agent context expiry in controller turns; built-in defaults are `24 12 48`. Omitted bounds retain their built-in values. Values must satisfy `MIN <= DEFAULT <= MAX`. Requires agent mode. |
| `--agent-hook-context SCRIPT...` | Execute trusted scripts before each controller turn and include successful stdout in `<hook_context>` blocks. Scripts run directly without tool-call review. Requires agent mode. |
| `--agent-profile NAME[,NAME...]` | Load stored profiles as `agent_NAME` controller tools; accepts comma-separated names and may be repeated. Use with `--agent` or `--agent-tool-list`. |
| `--agent-profile-default NAME` | Replace the generic `agent` continuation tool with the selected schema-constrained worker profile. Use with `--agent` or `--agent-tool-list`. |
| `--agent-tool-list` | List built-in and selected profile tool names and descriptions, including any `--agent-profile-default` replacement, without running a session. |
| `-f FILE...`, `--files FILE...` | Include files as context; use `-` for standard input. In agent mode, context supplied here is pinned. |
| `--files-list FILE...` | Read context paths from one or more list files; blank lines and lines beginning with `#` are ignored. May be repeated. |
| `-p NAME`, `--profile NAME` | Select an existing configuration profile. |
| `-o FILE`, `--output-file FILE` | Write response output to the given file, overwriting it if it exists. |
| `--shell [BOOL]` | Generate, review, and execute shell-command manifests for the task, with follow-up turns as needed. |
| `--shell-trace [BOOL]` | Trace executed shell commands with `strace` and save traces in session state. Defaults to `off`; requires Linux, `strace`, and shell or agent mode. |
| `--shell-timeout SECONDS` | Set the per-command timeout for standalone and agent shell execution. The base default is `0` (disabled); the `shell` and `agent` presets use `300`. Must be non-negative and is independent of `--llm-timeout`. |
| `--shell-networking [BOOL]` | Permit non-`AF_UNIX` socket creation for shell commands, including agent shell tools. Defaults to `off`; requires shell or agent mode. Does not control API requests or hook scripts. |
| `--patch [BOOL]` | Generate a line-based, multi-file patch for existing or new files, with optional context. Include existing files to edit as context; standard input is not supported. Changed files use suffixed output unless review or branch settings select in-place writes. |
| `--patch-branch [BOOL\|NAME]` | Use an `mce`-prefixed Git branch and commit patch changes; defaults to `mcebranch` and overrides suffix settings. Also selects the branch for `--patch-merge` or `--patch-file-apply`. |
| `-D [NAME]`, `--patch-branch-remove [NAME]` | Delete a patch branch, including unmerged commits; defaults to `mcebranch`. |
| `-M TEXT...`, `--patch-merge TEXT...` | Squash-merge the selected patch branch, commit with the supplied message, and delete the branch after success. Select a custom branch with `--patch-branch`. |
| `--patch-review [BOOL]` | Review diffs before writing. Approved changes use original paths unless a suffix override is active; patch generation supports revisions and navigation between patch turns. |
| `-S SUFFIX`, `--patch-suffix SUFFIX` | Override the suffix for patched files; the built-in default is `.mcepatched`. |
| `--patch-file-apply SESSION_OR_PATH [TURN]` | Apply a saved session patch, optionally from a specific turn, or a JSON patch manifest file. Honors review, suffix, and branch settings; makes no API request. `TURN` requires a session name. |
| `--patch-file-print SESSION_OR_PATH [TURN]` | Print a unified diff against current files from a saved session patch or JSON manifest, without an API request. `TURN` requires a session name. |
| `--noninteractive` | Disable prompts, force quiet mode and local logging, and print the session name. Task/plan output, generated patches, and fresh shell proposals are saved. `--agent` still executes tools unless `--agent-review` is set; resumed shell sessions and `--patch-file-apply` can also execute commands or write files. |
| `--resume-session SESSION_NAME [TURN]` | Start a new, linked session from a completed turn, latest by default; restore context paths and task state, following earlier resume links. Supports shell, patch, agent, and tree workflows. Patch revision requires `--task`; agents restore saved history, task lists, and context metadata. |
| `--resume-session-skip-verify` | Skip SHA-256 verification of resumed context files; use when file changes are intentional. |
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
| `--system-prompt-with-task [BOOL]` | Place the task and generated instructions before the configured system prompt instead of in the user prompt. Defaults to `on` in the base configuration. |
| `--linenum-system-prompt TEXT` | Override instructions for handling context-file line numbers. |
| `--patch-system-prompt TEXT` | Override the patch-mode system prompt. |
| `--shell-system-prompt TEXT` | Override the shell-mode system prompt. |
| `--agent-system-prompt TEXT` | Override the agent-mode system prompt. |
| `--plan-system-prompt TEXT` | Override the plan-mode system prompt. |
| `--prompt-expansion [BOOL]` | Expand `^^promptname^^` references using the prompt library, including nested references; defaults to `off`. |
| `--model MODEL` | Override the configured model. |
| `--list-models` | List models available from the configured endpoint. |
| `--apikey` | Prompt for an API key without echoing it; overrides `OPENAI_API_KEY` and the selected profile's key. |
| `--apikey-from-fd FD` | Read the API key from an already-open, non-negative file descriptor; overrides `OPENAI_API_KEY` and the selected profile's key. Cannot be combined with `--apikey`. |
| `--base-url URL` | Set the OpenAI-compatible API base URL. |
| `--proxy-server URL` | Set an HTTP(S) proxy URL. |
| `--meta-organization TEXT` | Set an optional organization ID. |
| `--meta-project TEXT` | Set an optional project name or ID. |
| `--service-tier {off,auto,default,flex,scale,priority}` | Select a provider service tier; `off` omits the request parameter. |
| `--response-format {text,json,schema}` | Select text, JSON objects, or a JSON Schema response contract. Custom schema output requires `--schema-file`; patch and shell modes supply built-in schemas. |
| `--response-json-repair [BOOL]` | Attempt to repair malformed JSON before parsing responses or tool arguments; defaults to `off`. |
| `--stream [BOOL]` | Stream text responses. Streaming is disabled for JSON/schema and noninteractive task output; tree and agent modes do not stream. |
| `--explicit-prompt-cache [BOOL]` | Request explicit prompt caching when supported by the endpoint. Off in the base configuration; enabled by the built-in presets. |
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
| `--llm-timeout SECONDS` | Set the API request timeout in seconds; the built-in default is `300`. Shell command timeouts are configured separately with `--shell-timeout`. |
| `--retry COUNT` | Set additional retries for transient API failures and invalid agent responses. Defaults to `3`; must be a non-negative integer. |
| `--no-line-numbers [BOOL]` | Omit line-number prefixes when enabled. Patch and agent modes always number file context. |
| `--print-reasoning [BOOL]` | Include available reasoning output in `<think>` tags. |
| `--print-default-config` | Print the built-in default configuration as JSON. |
| `--print-current-config` | Print the selected profile document as JSON rather than a merged inheritance view; masks the API key. |
| `--set-config NAME=VALUE...` | Set one or more values in the selected profile; may be repeated. `DEFAULT` restores the built-in default, or removes the override in an inherited profile. |
| `--set-config-from NAME PROFILE` | Copy an effective configuration value from another profile into the selected profile. |
| `--get-config [NAME]` | Print one effective configuration value, or all values when omitted. `^` marks inherited values; API keys are masked. |
| `--get-config-detail [NAME]` | Print effective settings with resolved system prompts in square brackets, or one setting when named. Includes prompt-file resolution and enabled library expansion; `^` marks inherited values. |
| `--log [BOOL]` | Control local logging under `~/.local/state/mince/logs`; defaults to `on`. Tree mode and `--noninteractive` force logging. |
| `--no-api-log [BOOL]` | Control API-side storage: bare `--no-api-log` or explicit `off` disables storage; explicit `on` enables it. |
| `--quiet [BOOL]` | Suppress extra output such as statistics and informational messages. |
| `--debug` | Print request and response objects inside debug tags. |
| `--init` | Initialize and interactively edit the selected configuration profile, `config` by default; unavailable with `--noninteractive`. |
| `--init-profile NAME` | Interactively initialize or edit the named configuration profile; unavailable with `--noninteractive`. |
| `--copy-profile NEW_NAME` | Copy the selected profile document to a new profile. Use `config` as the destination to replace the default configuration with the selected profile's effective settings. |
| `--remove-profile NAME` | Remove a user profile. Removing a built-in preset's override restores its built-in behavior; `config` and internal `mce_*` profiles cannot be removed. |
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
| `--patch-view SESSION` | Display the latest saved unified diff in session state, or a legacy patch file when no state session exists. |
| `--tree-view SESSION` | Display a saved combined Markdown tree report. |
| `--state-print-json [SESSION [TURN] [TYPE...]]` | Print selected saved artifacts as JSON. With no arguments, list artifact types; with a session, default to its latest completed turn. Shell output and trace types select all matching indexed files; exact indexed filenames are also accepted. |
| `--shell-session-print-json SESSION [TURN]` | Print a saved shell-session response as JSON, optionally for a specific turn. |
| `--remove-expired-data [KEEP_DAYS]` | Delete logs, patches, tree output, and state data older than `KEEP_DAYS`; defaults to `60`. |

Compatibility options:

- `--agent-auto` is deprecated and still requires `--agent`; automatic execution is now the default. Use `--agent-review` to request confirmation.
- `--reuse-session` and `--tree-reuse-session` are deprecated aliases for `--resume-session`; `--reuse-session-skip-verify` is a deprecated alias for `--resume-session-skip-verify`.
- `--patch-save` is deprecated and has no effect. Validated patch manifests and diffs are saved in session state; no `patch_save` setting is needed.

Environment variable reference.

| Environment variable | Description |
|----------------------|-------------|
| `OPENAI_API_KEY` | OpenAI-compatible API key; overrides the selected profile's stored key. `--apikey` and `--apikey-from-fd` take precedence over this variable. |
| `EDITOR` | Editor command for `e` prompts, plan editing, patch/shell/agent revisions, and prompt or agent-profile editors; defaults to `vi`. |
| `SHELL` | Executable shell used by `mcec --contain-use-shell` for sandbox testing. |

## Command line arguments for `mcec` 📋

`mcec` runs the assistant in a transient systemd user service. It requires Linux, `systemd-run`, and a running systemd user manager that supports the wrapper's sandbox properties.

```text
mcec [CONTAINMENT_OPTIONS...] [--] [MCE_ARGS...]
```

Containment options are consumed by the wrapper; other arguments are forwarded to the assistant. Explicit `--agent` or enabled `--shell` flags also trigger the inner shell-containment setup described below. Use `--` to stop wrapper option parsing, `mcec --contain-help` for containment help, or `mce --help` for assistant help. With `--contain-use-shell`, assistant arguments are ignored. Invoking `mcec` without arguments prints help guidance without starting a service.

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
| `--contain-network MODE` | Set networking for the outer service to `host` (default) or `none`. The latter uses a private network namespace and restricts socket creation to `AF_UNIX`; API calls normally require host networking. Separately launched shell services have their own networking settings. |
| `--contain-timeout SECONDS` | Stop the transient service after a positive integer number of seconds. |
| `--contain-trace FILE` | Trace the contained command and its children with `strace`. Relative paths use the contained working directory; the parent directory must exist. Existing trace files are overwritten. Requires `strace`. |
| `--contain-allow-namespaces` | Allow the contained process to create namespaces. Disabled by default because this may weaken filesystem containment. |
| `--contain-use-shell` | Run `$SHELL` instead of the assistant for sandbox testing. `SHELL` must identify an executable; assistant arguments are ignored. |
| `--contain-dry-run` | Print the `systemd-run` command instead of executing the service. Path validation and state-directory setup still occur. |
| `--contain-help` | Show containment help and exit. |
| `--` | Stop wrapper option parsing and pass all remaining arguments to the assistant unchanged. |

`mcec` primarily restricts filesystem writes; it is not complete isolation or a guarantee against data leaks. It does not hide all host files, remove credentials from the environment, or block access to host services through Unix sockets. Host networking is available by default.

With default settings, the outer process has writable private temporary directories and persistent assistant state, plus any explicit write grants. The working directory is not automatically writable. Home-visibility settings can hide paths, but working-directory, runtime, state, and explicitly granted paths are re-exposed as needed; `--contain-home off` does not by itself make the home directory writable.

`--contain-state ephemeral` starts without saved configuration or sessions, so supply credentials and endpoint settings separately. Read-only state prevents operations that need to create or update configuration, sessions, or logs.

An explicit `--agent` or enabled `--shell` flag on the forwarded command line requests separate sandboxed services for shell commands. Modes enabled only through a configuration profile do not trigger this extra setup; their child commands still run inside the outer sandbox. Pass the mode flag explicitly to request the separate shell sandbox.

The separate shell services use their own filesystem settings and private temporary directories. The wrapper forwards only `--contain-write-path`/`-W` grants as their writable-path exceptions, not writable bind destinations or its automatic state-directory grant. Outer bind mappings and home/state visibility settings are not inherited. Do not assume that files visible in the outer sandbox are visible in these services.

`--contain-network` controls the outer service, not the separate shell services. Shell commands can create only Unix sockets by default; `--shell-networking` permits other socket families. Thus `--contain-network none` alone does not restrict the separate shell services. API calls and hook scripts follow the outer sandbox's restrictions, not the shell tool's socket or per-command timeout settings.

Use `--contain-dry-run` to inspect the generated command without starting the service. `--contain-use-shell` tests the outer sandbox only.

`--contain-trace FILE` traces the contained assistant or test shell and its children, but not separately launched shell services. Use `--shell-trace` for those commands. Traces may include credentials or file contents; review them before sharing.

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

Last tested: `2026-10-29`

```text
TAP version 13
1..86
ok 1 - prints the built-in configuration offline
ok 2 - resolves virtual built-in profiles and protects internal profiles
ok 3 - repairs invalid configuration and rejects assignment batches atomically
ok 4 - supports inherited profile overrides
ok 5 - filters tree inputs without an API
ok 6 - processes tree files through a local API
ok 7 - combines shared tree prompts with wildcard, case-insensitive, and compound suffix selection
ok 8 - retries transient tree failures and resumes completed or partially failed results without duplicate work
ok 9 - creates, assigns, and removes prompt-library entries
ok 10 - expands prompt-library references
ok 11 - loads prompt and context files
ok 12 - lists state artifact types offline
ok 13 - applies patches to multiple files and creates files
ok 14 - inserts patches into empty files
ok 15 - validates patches and preserves line endings
ok 16 - reviews patches interactively without a suffix
ok 17 - handles text and JSON responses from a local API
ok 18 - handles streamed text and buffered reasoning responses
ok 19 - streams text responses to an output file
ok 20 - reconstructs streamed reasoning, replays cached context, and rejects incomplete streams
ok 21 - enables text streaming from configuration
ok 22 - preserves prompt placement and line-number overrides
ok 23 - reports relative file paths without inventing them for external files or stdin
ok 24 - separates schema instructions from literal schema data in either instruction role
ok 25 - handles custom JSON-schema responses
ok 26 - validates and writes an API patch response
ok 27 - creates API patch files without initial context
ok 28 - records session patch artifacts and reapplies exported JSON
ok 29 - applies deletion and replacement patch ranges
ok 30 - rejects resumed sessions with changed files
ok 31 - executes shell scripts and saves state offline
ok 32 - handles shell follow-up commands and failures
ok 33 - rejects invalid shell follow-ups while preserving accepted output and recording response errors
ok 34 - separates shell execution timeouts from API timeouts
ok 35 - totals shell and agent usage and costs once in stderr and session logs
ok 36 - traces shell and agent commands into distinct indexed state artifacts
ok 37 - resumes completed shell sessions without an extra request
ok 38 - writes and commits patch changes on a git branch
ok 39 - merges and removes patch branches
ok 40 - rejects invalid patch ranges, content, endings, and duplicate paths
ok 41 - applies a saved session patch only once
ok 42 - repairs JSON and controls explicit prompt caching
ok 43 - validates response completion, refusals, and retryable response errors
ok 44 - records failed requests without completing turns and resumes only completed work
ok 45 - selects API keys securely from configuration, environment, and file descriptors
ok 46 - retries transient but not permanent API failures
ok 47 - disables conflicting task modes for ask requests
ok 48 - ignores standalone patch and shell options in agent mode
ok 49 - revises the last shell command turn after session completion
ok 50 - restricts shell network address families unless enabled
ok 51 - applies native agent patches and refreshes companion file context
ok 52 - bounds readfile content and expires missing files independently
ok 53 - updates persistent agent tasks atomically at capacity
ok 54 - retries invalid agent requests and rejects invalid call batches
ok 55 - manages agent profiles and replays reasoning across worker delegation
ok 56 - delegates named and default built-in worker profiles without executing their proposals
ok 57 - reviews plans and preserves accepted, rejected, and saved state
ok 58 - navigates patch revisions and applies the selected state turn
ok 59 - resumes indexed and legacy shell output without executing commands again
ok 60 - pins agent file context and extends unpinned context expiry
ok 61 - restores selected agent history, tasks, file context, and remaining expiry
ok 62 - redacts API keys in configuration output and session logs
ok 63 - writes text and JSON output files without duplicating stdout
ok 64 - estimates tokens and rejects oversized requests before API calls
ok 65 - rejects invalid shell manifests before executing commands
ok 66 - runs agent hooks per turn and omits failed output and stdin
ok 67 - refreshes readfile context without retaining stale files or overwriting snapshots
ok 68 - preserves rejected tool proposals without applying patches or executing commands
ok 69 - revises resumed patches with checksum verification explicitly skipped
ok 70 - honors explicit automatic-agent patch suffixes without modifying source files
ok 71 - rejects task-list overflow atomically and renumbers removal batches
ok 72 - persists encrypted reasoning and replays it when resuming a task
ok 73 - forks resumed session chains and respects inherited turn cutoffs
ok 74 - distinguishes automatic, reviewed, rejected, and saved agent execution
ok 75 - compacts agent context into persisted Markdown summaries
ok 76 - automatically compacts pinned context and resumes summary-only turns
ok 77 - refreshes expired summaries without compacting or double-aging live context
ok 78 - retains deprecated option compatibility with explicit warnings
ok 79 - builds default containment commands and preserves argument boundaries
ok 80 - selects containment state, visibility, network, runtime, and shell modes
ok 81 - resolves, quotes, deduplicates, and orders containment grants and bindings
ok 82 - preserves mapped working directories and exposes explicit grant overrides
ok 83 - forwards nested shell containment grants and respects argument separators
ok 84 - grants and executes containment tracing without modifying dry-run destinations
ok 85 - rejects invalid containment options and paths before execution
ok 86 - imports containment environment by name and executes commands through PATH
```


## Usage Notes 🪧

**Adjust agent context expiration depending on context window size**

Adjusting `--agent-context-expires` may be required when using long context windows over many turns.  This setting and its default are still experimental and may change.

**Prevent incorrect cost calculation when specifying --model**

Specifying `--model` without `--token-cost` will disable token cost calculation.  Models will have unique pricing making the configured token pricing incorrect.

**Token estimation influences token limits**

Token estimation and actual input token usage may vary greatly model depending, adjust the token limit with the difference included for ideal results.

## Known Issues and Reporting ⚠️

**Command line arguments may clash**

Mixing combinations of command line arguments may lead to untested behaviour.

**Reporting Issues**

Create an Issue on GitHub or fill out the contact form on https://southlandsys.com or email contact@southlandsys.com (no reply will be given). Include as much detail as possible to ensure the issue is resolved.

Reporting an issue is much appreciated, reporting improves quality for everyone.

## Repository Locations 📍

https://github.com/Southland-Systems/mince

https://codeberg.org/Southland-Systems/mince

## License and Copyright 📄

This project is licensed under the **Apache-2.0 License**

Copyright 2023-2026 Southland Systems, Ontario, Canada
