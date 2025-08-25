# Kevin's dotfiles

My customized macOS dotfiles for development and productivity, based on Mathias Bynens' excellent dotfiles with personal customizations for zsh and iCloud workflows.

## Quick Start (TL;DR)

```bash
# Clone and install
git clone https://github.com/kevinlee/dotfiles.git ~/dotfiles
cd ~/dotfiles
bash bootstrap.sh

# Install Homebrew packages
brew bundle --file=Brewfile

# Load configuration (for zsh users)
source ~/.zshrc
```

## Installation

### Prerequisites
- macOS (tested on macOS 15+)
- Git
- zsh (default shell on modern macOS)

### Full Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kevinlee/dotfiles.git ~/dotfiles
   cd ~/dotfiles
   ```

2. **Review the files** (IMPORTANT - don't skip this step):
   ```bash
   # Check what will be installed
   ls -la
   cat .aliases    # See all aliases
   cat .exports    # See environment variables
   cat .functions  # See custom functions
   ```

3. **Install the dotfiles:**
   ```bash
   bash bootstrap.sh
   ```
   This will:
   - Pull latest changes from GitHub
   - Copy all dotfiles to your home directory
   - Ask for confirmation before overwriting existing files

4. **Set up zsh configuration:**
   ```bash
   source ~/.zshrc
   ```

### Verification

Test that everything is working:
```bash
# Test custom aliases
ic          # Should navigate to iCloud Drive
college     # Should navigate to School/College folder
edit        # Should open ~/.zshrc in vi
s .         # Should open current directory in Sublime Text

# Test environment variables
echo $ICLOUD    # Should show your iCloud path

# Test other aliases
l           # Enhanced ls with colors
ip          # Show external IP
update      # Update all system packages
```

## Custom Features

### iCloud Integration
Quick navigation to iCloud directories:
- `ic` - Jump to iCloud Drive root (`~/Library/Mobile Documents/com~apple~CloudDocs`)
- `college` - Navigate to `$ICLOUD/School/College`
- `sc` - Navigate to `$ICLOUD/School/College/USC/super_senior`
- `film` - Navigate to `$ICLOUD/Personal/photos/film_photography`

### Development Tools
- `edit` - Quick edit of zsh configuration (`vi ~/.zshrc`)
- `s [file/directory]` - Open files/directories in Sublime Text
- `yt [url]` - Download YouTube videos with optimized settings (requires `yt-dlp`)

### Directory Navigation
- `dw` - Navigate to Downloads folder
- `..`, `...`, `....` - Navigate up 1, 2, 3 directories
- `p` - Navigate to ~/projects
- `dt` - Navigate to Desktop
- `dl` - Navigate to Downloads

### System Utilities
- `update` - Update macOS, Homebrew, npm, gems all at once
- `cleanup` - Remove .DS_Store files recursively
- `emptytrash` - Empty trash + clear system logs
- `flush` - Clear DNS cache
- `ip` - Show external IP address
- `localip` - Show local IP address

## File Structure

```
~/dotfiles/
├── .aliases          # All command aliases (including custom ones)
├── .exports          # Environment variables (including $ICLOUD)
├── .functions        # Custom shell functions
├── .bash_profile     # Main bash configuration
├── .bash_prompt      # Custom prompt (works in zsh too)
├── .zshrc           # zsh configuration (created during setup)
├── .vimrc           # Vim configuration
├── .gitconfig       # Git configuration
├── bootstrap.sh     # Installation script
├── Brewfile         # Homebrew formulae and taps
├── brew.sh          # Homebrew installer (uses Brewfile)
└── README.md        # This file
```

## Configuration Files Explained

### `.zshrc` (Main zsh config)
- Loads all dotfiles components
- Sets up zsh-specific features (history, completion, etc.)
- Compatible with the bash-based dotfiles

### `.aliases` (Command shortcuts)
- Custom iCloud navigation aliases
- System utilities
- Development tools
- All standard Unix/macOS aliases

### `.exports` (Environment variables)
- `$ICLOUD` - Path to iCloud Drive
- `$EDITOR` - Default editor (vim)
- History settings
- Language settings

## Updating

To update your dotfiles:
```bash
cd ~/dotfiles
bash bootstrap.sh
source ~/.zshrc  # Reload configuration
```

## Customization

### Adding Your Own Aliases
1. Edit `~/.aliases` to add permanent aliases
2. Or create `~/.extra` for private/temporary customizations

### Adding New iCloud Shortcuts
Add to `.aliases`:
```bash
alias myproject="cd \"$ICLOUD/Projects/MyProject\""
```

### Override Settings
Create `~/.extra` file:
```bash
# Private settings not committed to repo
export CUSTOM_VAR="value"
alias secret="echo 'private command'"
```

## Troubleshooting

### Common Issues

**"Command not found" errors:**
```bash
# Reload configuration
source ~/.zshrc
# Or restart terminal
```

**iCloud aliases not working:**
```bash
# Check if ICLOUD variable is set
echo $ICLOUD
# Should show: /Users/[username]/Library/Mobile Documents/com~apple~CloudDocs
```

**Sublime Text alias not working:**
```bash
# Check if Sublime Text is installed in Applications
ls -la "/Applications/Sublime Text.app/Contents/SharedSupport/bin/subl"
```

**Bootstrap script errors:**
```bash
# Use bash explicitly (not zsh)
bash bootstrap.sh
# Not: source bootstrap.sh
```

### Resetting Everything
If something goes wrong:
```bash
# Backup your current config
cp ~/.zshrc ~/.zshrc.backup

# Re-run bootstrap
cd ~/dotfiles
bash bootstrap.sh

# Reload
source ~/.zshrc
```

## What This Setup Gives You

1. **Efficient Navigation**: Jump to common directories instantly
2. **Development Workflow**: Quick file editing, git shortcuts
3. **System Maintenance**: One-command updates and cleanup
4. **iCloud Integration**: Seamless access to cloud-synced files
5. **Zsh Optimization**: Modern shell with intelligent completion
6. **Consistent Environment**: Same setup across multiple machines

## Dependencies

These tools enhance the experience but aren't required:
- `yt-dlp` - For YouTube downloading (`brew install yt-dlp`)
- `Sublime Text` - For the `s` alias
- `Homebrew` - For package management (`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`)

## Future Setup Notes

When setting up on a new machine:
1. Install Homebrew first
2. Install Git and configure GitHub access
3. Clone this repo and run bootstrap
4. Install additional tools (yt-dlp, Sublime Text, etc.)
5. Create ~/.extra for machine-specific settings

## Add custom commands without creating a new fork

If `~/.extra` exists, it will be sourced along with the other files. You can use this to add a few custom commands without the need to fork this entire repository, or to add commands you don't want to commit to a public repository.

Example `~/.extra` file:

```bash
# Git credentials
# Not in the repository, to prevent people from accidentally committing under my name
GIT_AUTHOR_NAME="Your Name"
GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
git config --global user.name "$GIT_AUTHOR_NAME"
GIT_AUTHOR_EMAIL="your.email@example.com"
GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
git config --global user.email "$GIT_AUTHOR_EMAIL"
```

You could also use `~/.extra` to override settings, functions and aliases from this dotfiles repository.

### Sensible macOS defaults

When setting up a new Mac, you may want to set some sensible macOS defaults:

```bash
./.macos
```

### Install Homebrew formulae

When setting up a new Mac, you may want to install some common [Homebrew](https://brew.sh/) formulae (after installing Homebrew, of course):

```bash
brew bundle --file=Brewfile
# or
./brew.sh
```

Some of the functionality of these dotfiles depends on formulae listed in the `Brewfile`. If you don't plan to use `brew bundle`, you should look carefully through the file and manually install any particularly important ones. A good example is Bash/Git completion: the dotfiles use a special version from Homebrew.

## Feedback

Suggestions/improvements welcome!

## Author

Kevin Lee

## Thanks to…

* [Mathias Bynens](https://mathiasbynens.be/) for the original dotfiles this is based on
* @ptb and [his _macOS Setup_ repository](https://github.com/ptb/mac-setup)
* [Ben Alman](http://benalman.com/) and his [dotfiles repository](https://github.com/cowboy/dotfiles)
* [Cătălin Mariș](https://github.com/alrra) and his [dotfiles repository](https://github.com/alrra/dotfiles)
* [Gianni Chiappetta](https://butt.zone/) for sharing his [amazing collection of dotfiles](https://github.com/gf3/dotfiles)
* [Jan Moesen](http://jan.moesen.nu/) and his [ancient `.bash_profile`](https://gist.github.com/1156154) + [shiny _tilde_ repository](https://github.com/janmoesen/tilde)
* Lauri 'Lri' Ranta for sharing [loads of hidden preferences](https://web.archive.org/web/20161104144204/http://osxnotes.net/defaults.html)
* [Matijs Brinkhuis](https://matijs.brinkhu.is/) and his [dotfiles repository](https://github.com/matijs/dotfiles)
* [Nicolas Gallagher](http://nicolasgallagher.com/) and his [dotfiles repository](https://github.com/necolas/dotfiles)
* [Sindre Sorhus](https://sindresorhus.com/)
* [Tom Ryder](https://sanctum.geek.nz/) and his [dotfiles repository](https://sanctum.geek.nz/cgit/dotfiles.git/about)
* [Kevin Suttle](http://kevinsuttle.com/) and his [dotfiles repository](https://github.com/kevinSuttle/dotfiles) and [macOS-Defaults project](https://github.com/kevinSuttle/macOS-Defaults), which aims to provide better documentation for [`~/.macos`](https://mths.be/macos)
* [Haralan Dobrev](https://hkdobrev.com/)
* Anyone who [contributed a patch](https://github.com/mathiasbynens/dotfiles/contributors) or [made a helpful suggestion](https://github.com/mathiasbynens/dotfiles/issues)

---

*Last updated: July 2025*
