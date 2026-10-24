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
| `bin/` (cheatsheet, disk-clean, finder-favorites, obsidian-sync) | `~/bin/` |
| `.config/ghostty/config`, plus `hosts/<LocalHostName>` if it exists | `~/Library/Application Support/com.mitchellh.ghostty/config` |
| `.config/aerospace/`, `.config/starship/`, `.config/atuin/` | `~/.config/…` |
| `.config/karabiner/karabiner.json` (only if absent: Karabiner rewrites it) | `~/.config/karabiner/` |
| `.config/finder/favorites.txt` (personal sidebar folder list) | `~/.config/finder/`; import explicitly with `finder-favorites` |
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

## Finder Favorites

The personal folder list is saved in `.config/finder/favorites.txt`. After bootstrap,
preview and import it from a normal terminal:

```sh
finder-favorites import ~/.config/finder/favorites.txt --dry-run
finder-favorites import ~/.config/finder/favorites.txt
```

Import skips existing Favorites and missing folders, then appends new folders in
file order. It leaves existing sidebar order and built-in items alone; drag items
in Finder if you want an exact visual match. Bootstrap only copies the list and tool.

To capture the current sidebar, run this from the repo:

```sh
bin/finder-favorites export .config/finder/favorites.local.txt
```

The complete export is ignored by Git and is never deployed. Copy it privately to
the new Mac to import work or other private folders too. Review paths before
copying personal entries into the tracked `favorites.txt`; `~` adapts to the new
account name. The tool requires Apple's Command Line Tools (installed in SETUP step 2)
and uses the deprecated macOS shared-file-list API. If access fails, try a normal
terminal; the GUI fallback is to select each folder in Finder and press **Control–Command–T**.

### Custom sidebar icons (Emblem)

The Favorites export saves folder paths only. Restore the icons separately with
Emblem (already in the Brewfile). The saved personal mapping is **`~/code` →
`hammer.fill`**. Keep **Match folder icons** enabled to match the folder icon too.

After the folders and Favorites exist on the new Mac, open Emblem, add the folder
with its symbol, then use the row menu → **Regenerate Icon App** → **Setup Steps…**.
Enable its **<favorite name> Sync** extension in System Settings → General →
Login Items & Extensions → Finder, then use **Restart Finder** in Emblem's
checklist and check the sidebar visually.

The complete old-Mac config is saved privately as `.config/finder/emblem.local.json`
(ignored by Git, not deployed). Keep it with `favorites.local.txt` when transferring
private settings. The private **Mac Studio GUI Setup** note contains all saved
folder-to-symbol assignments and restoration steps. Regenerate icon apps on the
new Mac; their generated bundles contain old absolute folder paths. The other
personal Favorites have no custom mapping in the saved Emblem config; preserve
their normal icons unless another source supplies a mapping.

## Machine-local overrides (untracked; bootstrap never writes them)

| File | Holds | Template |
|---|---|---|
| `~/.extra` | Per-machine exports and secrets read from the Keychain; sourced by `.zshrc` after the other dotfiles | `.extra.example` |
| `~/.gitconfig.local` | Another git identity, commit signing; included last by `.gitconfig` | SETUP.md step 6 |
| `~/Library/Application Support/espanso/match/private.yml` | Personal snippets (phone, address) | `.config/espanso/match/private.yml.example` |

## Checks

`bash scripts/check.sh` runs every repo check and exits 1 on any FAIL; `--offline` skips the network lookups. It covers shell syntax under `/bin/bash` 3.2, data-file parsing, a fresh-HOME bootstrap with idempotency and drift tests, a public-repo guard (secrets, `/Users/…` paths, work identifiers), the Brewfile and `.gitignore`. CI runs it on every push (`.github/workflows/check.yml`).
For a single machine, `bash bootstrap.sh -n` reports drift between the repo and `$HOME`.
