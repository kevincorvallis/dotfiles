# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

macOS dotfiles for Apple Silicon, based on Mathias Bynens' dotfiles. Shell config files are rsynced to `~/` via `bootstrap.sh`; app configs (Ghostty, Aerospace, Starship) are copied to their platform-specific locations.

## Key Commands

- **Install dotfiles**: `bash bootstrap.sh` (or `bootstrap.sh -f` to skip confirmation)
- **Install packages**: `brew bundle --file=Brewfile`
- **Apply macOS settings**: `./.macos` (or `./.macos --no-dark-mode`)
- **Reload shell**: `source ~/.zshrc`

## Architecture

Shell loads in this order: `.zshrc` → sources `.exports`, `.aliases`, `.functions`, `.extra` (from `~`) → then inits zsh plugins and modern tools

- `.zshrc` — Zsh options, completions, loads shared dotfiles, then inits plugins (autosuggestions, syntax-highlighting) and tools (starship, zoxide, atuin, direnv)
- `.exports` — PATH, editor, locale, tool configs (fzf, bat, starship)
- `.aliases` — All aliases; conditionally uses modern CLI tools (eza, bat, fd, rg, zoxide) with fallbacks
- `.functions` — Shell functions (server, mkd, targz, etc.)
- `.extra` — Private/untracked overrides (git credentials, personal aliases)

### bootstrap.sh

Rsyncs dotfiles to `~/` with explicit excludes (`.git/`, `.claude/`, `.config/`, `Brewfile`, docs). Then separately copies:
- Ghostty config → `~/Library/Application Support/com.mitchellh.ghostty/config` (base + host-specific overlay from `.config/ghostty/hosts/$(hostname -s)`)
- Aerospace config → `~/.config/aerospace/aerospace.toml`
- Starship config → `~/.config/starship/starship.toml`
- Claude Code config → `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, `~/.claude/agents/`
- Espanso config → `~/Library/Application Support/espanso/match/` and `~/Library/Application Support/espanso/config/`

### App Configs

- `.config/ghostty/config` — Base Ghostty terminal config
- `.config/ghostty/hosts/<hostname>` — Per-host Ghostty overrides (e.g., theme), appended to base config during bootstrap
- `.config/aerospace/aerospace.toml` — Aerospace tiling WM config (alt-hjkl nav, workspaces 1-6)
- `.config/starship/starship.toml` — Starship prompt config (green Matrix aesthetic)
- `.config/claude/settings.json` — Claude Code permissions, plugins, and allowed tools
- `.config/claude/CLAUDE.md` — Global Claude Code instructions
- `.config/claude/agents/librarian.md` — Custom "Librarian" research agent
- `.config/espanso/match/*.yml` — Text-expansion snippets (ai, base, comms, dev, git, markdown, symbols)
- `.config/espanso/config/default.yml` — Espanso global config (disables search bar to avoid Raycast collision)

### Other

- `.macos` — macOS `defaults write` commands (~33KB); requires sudo, some settings need logout/restart
- `.gitconfig` — Uses delta as pager; has URL shorthands (`gh:` → `git@github.com:`)
- `Brewfile` — Homebrew packages, cask apps (Ghostty, Aerospace, Sublime Text), Nerd Fonts
- `bin/subl` — Symlink to Sublime Text CLI
- `init/Preferences.sublime-settings` — Sublime Text preferences
