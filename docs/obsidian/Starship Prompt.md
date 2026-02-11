# Starship Prompt

> [Starship](https://starship.rs/) is a fast, cross-shell prompt that replaces the custom `.bash_prompt`. It works in both bash and zsh and auto-detects context.

## What It Shows

Starship automatically detects what you're working on and shows relevant info:

- **Git branch + status** - current branch, modified/staged/untracked counts
- **Language versions** - Python, Node.js, Rust, Go, etc. (only when relevant files exist)
- **Cloud context** - AWS profile, Kubernetes context
- **Command duration** - shows time for commands > 2 seconds
- **Exit code** - red prompt on failed commands

## Setup

Already configured in your dotfiles. Starship is initialized in:
- `.exports` (for bash)
- `.zshrc` (for zsh)

The old `.bash_prompt` is kept as a fallback but only loads if starship is not installed.

## Configuration

Starship is configured via `~/.config/starship.toml`. To get started with a preset:

```bash
# List available presets
starship preset --list

# Apply a preset
starship preset pure-preset -o ~/.config/starship.toml
starship preset tokyo-night -o ~/.config/starship.toml

# Or use the default (no config file needed)
```

### Popular Presets
| Preset | Style |
|--------|-------|
| `pure-preset` | Minimal, clean (like Pure prompt) |
| `tokyo-night` | Tokyo Night color scheme |
| `nerd-font-symbols` | Uses Nerd Font icons |
| `gruvbox-rainbow` | Gruvbox colors with rainbow modules |

### Custom Configuration Example
```toml
# ~/.config/starship.toml

[character]
success_symbol = "[>](bold green)"
error_symbol = "[>](bold red)"

[git_branch]
symbol = " "

[directory]
truncation_length = 3
```

## How It Replaces .bash_prompt

Your old prompt showed: `username@hostname in ~/path (git-branch [+!?$])`

Starship shows similar info but with:
- Automatic language version detection
- Command execution time
- Configurable modules
- Same prompt in bash AND zsh
- 10-100x faster rendering

## Tags
#dotfiles #starship #prompt #shell
