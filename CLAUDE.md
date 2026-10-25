# CLAUDE.md

Guidance for Claude Code in this repo: Kevin's macOS (Apple Silicon) dotfiles. The repo is public. Files are deployed by copying, not symlinking. README.md has the layout and SETUP.md the new-Mac runbook.

## Commands

- `bash scripts/check.sh [--offline]` runs every repo check (CI runs it too). Run it after any change.
- `bash scripts/doctor.sh` checks this Mac against SETUP.md and lists each gap as `TODO [you]` or `[agent]`. It is read-only; run it outside the sandbox. To set up a new Mac, follow SETUP.md's "For the agent" section.
- `bash bootstrap.sh -n` is a drift report and writes nothing. `bash bootstrap.sh [-f] [--launchagents]` deploys.
- Test bootstrap only against a throwaway HOME: `HOME=$(mktemp -d) bash bootstrap.sh -f`. Don't run bootstrap, `--launchagents` or `.macos` against the real HOME unless asked.
- `brew bundle --file=Brewfile` installs packages. `./.macos` applies system settings; it needs Full Disk Access and asks for sudo itself.

## Deploy (bootstrap.sh)

An explicit allowlist. Identical files are left alone. A file that differs is moved to `~/.dotfiles-backup/<timestamp>/` and then replaced. Extra files in a destination are never deleted.

- `.zshrc .exports .aliases .functions .gitconfig .gitignore .vimrc .vim/ .tmux.conf .curlrc .hushlogin .inputrc` go to `~/`.
- `bin/*` goes to `~/bin/` and is made executable.
- `.config/ghostty/config`, plus `hosts/<scutil --get LocalHostName>` appended when that file exists, goes to `~/Library/Application Support/com.mitchellh.ghostty/config`.
- `.config/{aerospace,starship,atuin}/` go to `~/.config/`. `.config/karabiner/karabiner.json` is copied only if absent.
- `.config/espanso/{config,match}/*.yml` go to `~/Library/Application Support/espanso/`.
- `.config/sublime/User/*` goes to Sublime Text's `Packages/User/`.
- `.config/claude/` goes to `~/.claude/`: settings.json, CLAUDE.md, AGENT-GRAPH.md, and the agents, commands, rules, skills, output-styles, scripts and hooks dirs (`hooks/*.sh` made executable).
- `.config/codex/skills/` goes to `~/.codex/skills/`; other Codex files and local skills are preserved. Cross-model review also needs Cursor CLI installed and signed in on each Mac (SETUP.md step 8).
- `.config/mcp/*` goes to `~/.local/share/mcp/`.
- `launchagents/*.plist` go to `~/Library/LaunchAgents/` only with `--launchagents`. `__HOME__` becomes `$HOME`, and launchctl reloads any agent that changed or isn't loaded.
- Never deployed: this file, README.md, SETUP.md, LICENSE-MIT.txt, Brewfile, .macos, scripts/, .github/, `*.example` and .claude/.

This `CLAUDE.md` is repo guidance. `.config/claude/CLAUDE.md` is the global file that becomes `~/.claude/CLAUDE.md`.

To add a deployed path, update `bootstrap.sh`, `deploy_map()` in `scripts/check.sh`, and the README layout table.

## Shell

- `.zshrc`, in order: PATH and Homebrew; history, including `HISTORY_IGNORE` for secret-looking lines; completion; the paste-oneline widget. It then sources `~/.exports`, `~/.aliases`, `~/.functions` and `~/.extra`. Last come the guarded tool inits: autosuggestions, fzf, starship, zoxide, atuin, direnv and the gh token, with syntax-highlighting at the very end.
- `.exports`: env vars, and `DOTFILES` (the repo path, default `~/code/personal/dotfiles`).
- `.aliases`: `cd`→z, `ls`→eza and `cat`→bat only in an interactive terminal outside Claude Code (`CLAUDECODE` unset). `edit` opens `$DOTFILES`.
- `.functions`: `update()` only.

## Machine-local overlays (untracked; bootstrap never writes them)

- `~/.extra` (template `.extra.example`): per-machine exports and secrets read from the Keychain. No `git config` calls.
- `~/.gitconfig.local`, included last by `.gitconfig`: other identities and commit signing. Tracked files carry no signing config.
- espanso `match/private.yml` (template `match/private.yml.example`): identity snippets, and any machine-only triggers.
- `~/.mcp.json` (from `.config/mcp/mcp.json.example`) and `~/.claude/settings.local.json`.

## Rules

- Edit the repo copy, never the deployed copy in `~`.
- `bootstrap.sh`, `.macos`, `scripts/check.sh` and the bash scripts in `bin/` must run on macOS `/bin/bash` 3.2. That rules out associative arrays, `mapfile`, `${x,,}` and `|&`.
- Public repo: no secrets, no `/Users/<name>` paths (use `$HOME`), no employer or work identifiers, no real personal details. check.sh fails on these.
- Every hook referenced in `.config/claude/settings.json` must exist in the repo.
