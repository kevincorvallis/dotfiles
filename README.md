# dotfiles

Kevin's macOS dotfiles for Apple Silicon: zsh, Ghostty, AeroSpace, Starship, espanso, Sublime Text and Claude Code.
`bootstrap.sh` copies an explicit allowlist of files into `$HOME` and backs up anything it replaces, so it is safe to re-run.
Started from [Mathias Bynens' dotfiles](https://github.com/mathiasbynens/dotfiles); MIT licensed (`LICENSE-MIT.txt`).

## Quick start

On a new Mac, follow **[SETUP.md](SETUP.md)**. You do steps 1-4 by hand (Apple ID, hostname, Homebrew, Claude Code, the clone); then an agent can run the rest, stopping at each step that needs you (passwords, sign-ins, permission grants):

```sh
git clone https://github.com/kevincorvallis/dotfiles.git ~/code/personal/dotfiles
cd ~/code/personal/dotfiles && claude    # "Set up this Mac by following SETUP.md."
```

`bash scripts/doctor.sh` is the scorecard: it checks this Mac against SETUP.md, lists every gap as `TODO [you]` or `TODO [agent]` with the command that closes it, and exits 0 once the Mac is done. By hand, the core is `brew bundle --file=Brewfile`, then `bash bootstrap.sh -n` to preview and `bash bootstrap.sh` to deploy.

Keep the clone at `~/code/personal/dotfiles`: `$DOTFILES` and the `edit` alias default to it (override `DOTFILES` in `~/.extra`).

## Layout

| Repo path | Deployed to |
|---|---|
| `.zshrc` `.exports` `.aliases` `.functions` `.gitconfig` `.gitignore` `.vimrc` `.vim/` `.tmux.conf` `.curlrc` `.inputrc` `.hushlogin` | `~/` |
| `bin/` (cheatsheet, disk-clean, obsidian-sync) | `~/bin/` |
| `.config/ghostty/config`, plus `hosts/<LocalHostName>` if it exists | `~/Library/Application Support/com.mitchellh.ghostty/config` |
| `.config/aerospace/`, `.config/starship/`, `.config/atuin/` | `~/.config/…` |
| `.config/karabiner/karabiner.json` (only if absent: Karabiner rewrites it) | `~/.config/karabiner/` |
| `.config/espanso/config/*.yml`, `.config/espanso/match/*.yml` | `~/Library/Application Support/espanso/` |
| `.config/sublime/User/` | `~/Library/Application Support/Sublime Text/Packages/User/` |
| `.config/claude/` (settings, CLAUDE.md, agents, commands, rules, skills, output-styles, hooks, scripts) | `~/.claude/` |
| `.config/mcp/` (MCP server scripts and `requirements.txt`) | `~/.local/share/mcp/` |
| `launchagents/*.plist` (templates; `__HOME__` becomes `$HOME`) | `~/Library/LaunchAgents/`, only with `--launchagents` |
| `Brewfile`, `.macos`, `scripts/`, `*.example`, docs | not deployed; used in place |

## bootstrap.sh

```
bash bootstrap.sh [-f|--force] [-n|--dry-run] [--launchagents] [-h|--help]
  -f, --force      Do not ask for confirmation.
  -n, --dry-run    Show what would change (a drift report). Writes nothing.
  --launchagents   Also install launchagents/*.plist into ~/Library/LaunchAgents and load them.
```

Identical files are left alone. A file that differs is moved to `~/.dotfiles-backup/<timestamp>/` before the repo copy goes in. Files that are not in the repo are never deleted. On a Mac that already has config, run `-n` first and read the list. A Mac set up by the old rsync bootstrap needs a few steps before its first run; see [SETUP.md](SETUP.md#existing-mac-set-up-by-the-old-rsync-bootstrap).

## Machine-local overrides (untracked; bootstrap never writes them)

| File | Holds | Template |
|---|---|---|
| `~/.extra` | Per-machine exports and secrets read from the Keychain; sourced by `.zshrc` after the other dotfiles | `.extra.example` |
| `~/.gitconfig.local` | Another git identity, commit signing; included last by `.gitconfig` | SETUP.md step 6 |
| `~/Library/Application Support/espanso/match/private.yml` | Personal snippets (phone, address) | `.config/espanso/match/private.yml.example` |

## Checks

`bash scripts/check.sh` runs every repo check and exits 1 on any FAIL; `--offline` skips the network lookups. It covers shell syntax under `/bin/bash` 3.2, data-file parsing, a fresh-HOME bootstrap with idempotency and drift tests, a public-repo guard (secrets, `/Users/…` paths, work identifiers), the Brewfile and `.gitignore`. CI runs it on every push (`.github/workflows/check.yml`).
For a single machine, `bash bootstrap.sh -n` reports drift between the repo and `$HOME`.
