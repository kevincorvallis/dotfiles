# Atuin - Shell History

> [Atuin](https://atuin.sh/) replaces your shell history with a SQLite database, providing full-text search, context tracking, and optional cross-machine sync.

## What It Does

Standard shell history is a flat text file with limited search. Atuin stores each command with:
- **Timestamp** - when you ran it
- **Duration** - how long it took
- **Exit code** - whether it succeeded
- **Directory** - where you ran it
- **Session** - which terminal session
- **Hostname** - which machine

## Key Bindings

| Key | What It Does |
|-----|-------------|
| `Ctrl+R` | Open full-screen history search UI |
| `Up Arrow` | Search history (same as before, but enhanced) |
| `Ctrl+R` again | Cycle through filter modes: global / session / directory |

## Filter Modes

Press `Ctrl+R` repeatedly to cycle through:
1. **Global** - search all history
2. **Host** - only commands from this machine
3. **Session** - only commands from this terminal session
4. **Directory** - only commands run in the current directory

## Setup

Already configured in your dotfiles. Atuin is initialized in:
- `.exports` (for bash)
- `.zshrc` (for zsh)

### Optional: Cross-Machine Sync

Atuin can sync your shell history across machines with end-to-end encryption:

```bash
# Register an account
atuin register -u <username> -e <email>

# Or login on another machine
atuin login -u <username>

# Sync manually
atuin sync

# Check sync status
atuin status
```

All data is encrypted client-side. Atuin's servers never see your commands.

### Configuration

Atuin config lives at `~/.config/atuin/config.toml`:

```toml
# Common settings
[settings]
# Search mode: prefix, fulltext, fuzzy, skim
search_mode = "fuzzy"

# Filter mode when pressing up arrow
filter_mode = "global"

# Style: compact, full
style = "compact"

# Don't sync sensitive commands
secrets_filter = true
```

## Tips

- Type part of a command and press `Up` to search just that prefix
- Use `atuin stats` to see your most-used commands
- `atuin history list` shows recent history with metadata
- Commands starting with a space are still hidden (respects `HISTCONTROL`)

## Tags
#dotfiles #atuin #history #shell #tools
