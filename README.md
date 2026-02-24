# Kevin's dotfiles

Modern macOS dotfiles optimized for Apple Silicon, featuring a curated set of CLI tools and sensible defaults. Based on Mathias Bynens' dotfiles with significant modernization.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/kevincorvallis/dotfiles.git ~/dotfiles
cd ~/dotfiles

# Install dotfiles
bash bootstrap.sh

# Install Homebrew packages
brew bundle --file=Brewfile

# Apply macOS settings (optional)
./.macos

# Reload shell
source ~/.zshrc
```

## What's Included

### Modern CLI Tools

| Tool | Description | Alias |
|------|-------------|-------|
| `eza` | Modern `ls` replacement | `ls`, `l`, `la`, `ll`, `lt` |
| `bat` | Better `cat` with syntax highlighting | `cat`, `catp` |
| `ripgrep` | Fast grep alternative | `rg`, `rgi` |
| `fd` | Fast find alternative | `fd`, `fdi` |
| `fzf` | Fuzzy finder | - |
| `git-delta` | Beautiful git diffs | automatic |
| `gh` | GitHub CLI | - |
| `htop` | Interactive process viewer | - |
| `jq` | JSON processor | - |
| `tldr` | Simplified man pages | - |
| `zoxide` | Smarter `cd` that learns your habits | `z`, `zi` |
| `starship` | Cross-shell prompt with git/language context | automatic |
| `atuin` | Shell history search + sync | `ctrl-r` |
| `direnv` | Per-directory environment variables | automatic |

### Shell Plugins

- **zsh-autosuggestions** - Fish-like inline command suggestions as you type
- **zsh-syntax-highlighting** - Real-time command validation (green = valid, red = invalid)

### Terminal

- **Ghostty** - Fast, native terminal emulator with custom config (`.config/ghostty/config`)

### Window Management

- **Aerospace** - Tiling window manager with vim-style keybindings (`.config/aerospace/aerospace.toml`)

### Shell Features

- Apple Silicon Homebrew support (`/opt/homebrew`)
- Starship prompt with git/language context detection
- Atuin-powered shell history search (replaces ctrl-r)
- Zoxide smart directory navigation
- Extensive aliases for navigation and utilities
- Python 3 compatible functions
- iCloud directory shortcuts

## Installation

### Prerequisites

- macOS Sonoma/Sequoia (Apple Silicon)
- [Homebrew](https://brew.sh)
- zsh (default on modern macOS)

### Fresh Install

```bash
# 1. Clone repository
git clone https://github.com/kevincorvallis/dotfiles.git ~/dotfiles
cd ~/dotfiles

# 2. Review files before installing
cat .aliases      # Check aliases
cat .exports      # Check environment variables

# 3. Run bootstrap (copies files to ~/)
bash bootstrap.sh

# 4. Install packages
brew bundle --file=Brewfile

# 5. Apply macOS preferences (optional but recommended)
./.macos

# 6. Reload shell
source ~/.zshrc
```

### Updating Existing Installation

If you already have an older version installed:

```bash
cd ~/dotfiles

# Pull latest changes
git pull origin main

# Re-run bootstrap to copy updated files
bash bootstrap.sh --force

# Update/install new Homebrew packages
brew bundle --file=Brewfile

# Reload shell configuration
source ~/.zshrc

# Optional: Re-apply macOS settings
./.macos
```

## Aliases & Commands

### Navigation

| Command | Action |
|---------|--------|
| `..` | Go up one directory |
| `...` | Go up two directories |
| `....` | Go up three directories |
| `p` | `cd ~/projects` |
| `dl` | `cd ~/Downloads` |
| `dt` | `cd ~/Desktop` |
| `ic` | `cd` to iCloud Drive |

### File Listing (eza)

| Command | Action |
|---------|--------|
| `ls` | List files (eza) |
| `l` | Long listing |
| `la` | Long listing with hidden files |
| `ll` | Same as `la` |
| `lt` | Tree view (2 levels) |
| `lsd` | List directories only |

### System Utilities

| Command | Action |
|---------|--------|
| `update` | Update macOS, Homebrew, npm, gems |
| `cleanup` | Delete `.DS_Store` files recursively |
| `emptytrash` | Empty trash and clear system logs |
| `flush` | Flush DNS cache |
| `afk` | Lock screen |
| `reload` | Reload shell configuration |

### Network

| Command | Action |
|---------|--------|
| `ip` | External IP address |
| `localip` | Local IP address |
| `ips` | All IP addresses |

### Development

| Command | Action |
|---------|--------|
| `g` | Git |
| `s <file>` | Open in Sublime Text |
| `server` | Start Python HTTP server (port 8000) |
| `yt <url>` | Download YouTube video |

### Finder

| Command | Action |
|---------|--------|
| `show` | Show hidden files in Finder |
| `hide` | Hide hidden files in Finder |
| `hidedesktop` | Hide desktop icons |
| `showdesktop` | Show desktop icons |

## File Structure

```
~/dotfiles/
├── .aliases          # Command aliases (eza, bat, navigation)
├── .bash_profile     # Minimal bash config for script compatibility
├── .config/
│   ├── aerospace/
│   │   └── aerospace.toml  # Aerospace tiling WM config
│   ├── ghostty/
│   │   ├── config           # Ghostty terminal configuration
│   │   └── hosts/           # Per-host Ghostty overrides
│   └── starship/
│       └── starship.toml    # Starship prompt configuration
├── .exports          # Environment variables + Homebrew PATH
├── .functions        # Shell functions (server, mkd, etc.)
├── .gitconfig        # Git config with delta integration
├── .gitignore        # Global gitignore
├── .macos            # macOS system preferences
├── .vimrc            # Vim configuration (Solarized Dark)
├── .zshrc            # Zsh configuration (primary shell config)
├── Brewfile          # Homebrew packages + fonts
├── bootstrap.sh      # Installation script
└── init/
    └── Preferences.sublime-settings
```

## Customization

### Private Settings

Create `~/.extra` for settings you don't want to commit:

```bash
# Git credentials
GIT_AUTHOR_NAME="Your Name"
GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
git config --global user.name "$GIT_AUTHOR_NAME"
GIT_AUTHOR_EMAIL="your@email.com"
GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
git config --global user.email "$GIT_AUTHOR_EMAIL"

# Custom aliases
alias myproject="cd ~/projects/myproject"
```

### Adding Aliases

Edit `.aliases` directly or add to `~/.extra`:

```bash
alias myalias="my command here"
```

### macOS Settings

The `.macos` script configures system preferences. Key settings:

- Dark mode (pass `--no-dark-mode` to disable)
- Fast keyboard repeat
- Tap to click on trackpad
- Show file extensions
- Disable auto-correct
- Aerospace tiling window management

Review and customize before running:

```bash
# Review the script
less .macos

# Run with dark mode
./.macos

# Run without dark mode
./.macos --no-dark-mode
```

## Homebrew Packages

The `Brewfile` installs:

**Core Utilities**
- coreutils, findutils, gnu-sed, grep
- bash, bash-completion2
- vim, wget, openssh

**Modern CLI**
- gh, fzf, ripgrep, bat, eza
- git-delta, fd, tldr, htop, jq
- zoxide, starship, atuin, direnv
- zsh-autosuggestions, zsh-syntax-highlighting

**Development**
- git, git-lfs, php, lua

**Other**
- imagemagick, p7zip, pigz, tree, zopfli

**Fonts (Nerd Font variants)**
- JetBrains Mono, Fira Code, Monaspace, Cascadia Mono, Victor Mono, Geist Mono

**Apps**
- Ghostty (terminal emulator)
- Aerospace (tiling window manager)

## Troubleshooting

### Commands not found after install

```bash
# Reload shell
source ~/.zshrc

# Or restart terminal
```

### Homebrew not in PATH (Apple Silicon)

The `.exports` file should handle this, but if not:

```bash
# Add to ~/.zshrc or ~/.extra
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### eza/bat/etc not working

```bash
# Install the packages
brew bundle --file=Brewfile

# Verify installation
which eza bat rg fd
```

### Git delta not showing

Delta requires configuration in `.gitconfig`. If you had a previous `.gitconfig`, you may need to merge the delta settings:

```ini
[core]
    pager = delta

[interactive]
    diffFilter = delta --color-only

[delta]
    navigate = true
    line-numbers = true
    syntax-theme = Solarized (dark)
```

### macOS settings not applying

Some settings require:
- Logout/login
- Full restart
- Closing affected apps

## Requirements

- macOS 14+ (Sonoma) or macOS 15+ (Sequoia)
- Apple Silicon Mac (M1/M2/M3/M4)
- Homebrew
- Git

## Credits

Based on [Mathias Bynens' dotfiles](https://github.com/mathiasbynens/dotfiles) with modernization for:
- Apple Silicon compatibility
- Modern CLI tools (eza, bat, ripgrep, fd, delta)
- macOS Sonoma/Sequoia support
- Aerospace tiling window management
- Python 3 compatibility

## License

MIT

---

*Last updated: February 2026*
