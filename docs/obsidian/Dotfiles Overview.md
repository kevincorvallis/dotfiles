# Dotfiles Overview

> Personal macOS development environment configuration for Apple Silicon Macs running macOS Tahoe 26+. Based on [Mathias Bynens' dotfiles](https://github.com/mathiasbynens/dotfiles) with significant modernization.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/kevincorvallis/dotfiles.git ~/dotfiles

# Run the bootstrap to symlink dotfiles to $HOME
cd ~/dotfiles && source bootstrap.sh

# Install Homebrew packages
brew bundle --file=Brewfile

# Apply macOS system settings (requires sudo)
./.macos

# Restart your terminal
```

## File Map

| File | Purpose | See Also |
|------|---------|----------|
| `.macos` | macOS system defaults (Finder, Dock, Safari, etc.) | [[macOS System Settings]] |
| `Brewfile` | Homebrew package manifest | [[Brewfile - Package Management]] |
| `.bash_profile` | Shell initialization (loads all other dotfiles) | [[Shell Configuration]] |
| `.zshrc` | Zsh-specific initialization | [[Shell Configuration]] |
| `.exports` | Environment variables + tool init | [[Shell Configuration]] |
| `.aliases` | Command shortcuts | [[Aliases Reference]] |
| `.functions` | Reusable shell functions | [[Shell Functions]] |
| `.bash_prompt` | Legacy bash prompt (replaced by Starship) | [[Starship Prompt]] |
| `.gitconfig` | Git configuration + aliases | [[Git Configuration]] |
| `.vimrc` | Vim editor settings | [[Vim Configuration]] |
| `.curlrc` / `.wgetrc` | HTTP client defaults | [[HTTP Client Configs]] |
| `.inputrc` | Readline (tab completion, history search) | [[Shell Configuration]] |
| `.tmux.conf` | tmux terminal multiplexer | [[tmux Configuration]] |
| `.editorconfig` | Cross-editor formatting rules | [[Editor Settings]] |
| `bootstrap.sh` | Installation/sync script | This file |
| `brew.sh` | Legacy Homebrew update script | Use `brew bundle` instead |

## Architecture

```
~/.bash_profile loads files in this order:
  1. ~/.path         (custom PATH extensions)
  2. ~/.exports      (env vars + tool init: starship, zoxide, atuin)
  3. ~/.aliases      (command shortcuts)
  4. ~/.functions    (shell functions)
  5. ~/.extra        (private settings, not committed)
  6. ~/.bash_prompt  (only if starship is NOT installed)
```

## Tags
#dotfiles #macos #development #setup
