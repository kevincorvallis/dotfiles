# Personal MacBook Dotfiles

These dotfiles keep my development environment consistent across all of my MacBooks. They start from [Mathias Bynens](https://github.com/mathiasbynens/dotfiles) and include my own aliases, functions, and iCloud shortcuts.

## Quick Start
```bash
# clone and set up
git clone https://github.com/kevinlee/dotfiles.git ~/dotfiles
cd ~/dotfiles
bash bootstrap.sh

# reload shell (zsh)
source ~/.zshrc
```

## Installation

### Requirements
- macOS (tested on macOS 15+)
- Git
- zsh (default on modern macOS)
- [Homebrew](https://brew.sh/) for additional packages (optional)

### Steps
1. **Clone the repo**
   ```bash
   git clone https://github.com/kevinlee/dotfiles.git ~/dotfiles
   cd ~/dotfiles
   ```
2. **Review the files before running anything**
   ```bash
   ls -la
   cat .aliases    # command shortcuts
   cat .exports    # environment variables
   cat .functions  # custom functions
   ```
3. **Run the installer**
   ```bash
   bash bootstrap.sh
   ```
4. **Reload your shell**
   ```bash
   source ~/.zshrc
   ```

## Features

### iCloud Shortcuts
These aliases help me jump directly into frequently used iCloud folders:
- `ic` – open iCloud Drive (`~/Library/Mobile\ Documents/com~apple~CloudDocs`)
- `college` – open `$ICLOUD/School/College`
- `sc` – open `$ICLOUD/School/College/USC/super_senior`
- `film` – open `$ICLOUD/Personal/photos/film_photography`

### Development Tools
- `edit` – open `~/.zshrc` in your editor
- `s [path]` – open a file or folder in Sublime Text
- `yt [url]` – download a YouTube video (requires `yt-dlp`)

### Navigation
- `dw` – go to Downloads
- `..`, `...`, `....` – move up directories quickly
- `p` – go to `~/projects`
- `dt` – Desktop shortcut

### System Utilities
- `update` – update macOS, Homebrew, npm, and gems
- `cleanup` – remove `.DS_Store` files recursively
- `emptytrash` – empty the Trash and clear system logs
- `flush` – flush DNS cache
- `ip` – show external IP address
- `localip` – show local IP address

## Directory Layout
```
~/dotfiles/
├── .aliases          # alias definitions
├── .exports          # environment variables (includes $ICLOUD)
├── .functions        # custom shell functions
├── .bash_profile     # bash setup
├── .bash_prompt      # custom shell prompt
├── .zshrc            # zsh configuration
├── .vimrc            # Vim configuration
├── .gitconfig        # Git aliases and settings
├── bootstrap.sh      # installation script
├── brew.sh           # Homebrew packages
└── init/             # misc. app configs (Sublime Text, iTerm2, etc.)
```

## Customisation
- Create `~/.extra` for machine–specific settings. It will be sourced automatically if present.
- Edit any of the dotfiles to suit your workflow. Re-run `bash bootstrap.sh` to reapply them.
- For Terminal themes and Spectacle settings, check the files under `init/`.

## Homebrew Packages
If you use Homebrew, run `./brew.sh` after installing the dotfiles to grab the extra packages used by my setup.

## Resetting
If you ever need to start over, backup your config and run the installer again:
```bash
cp ~/.zshrc ~/.zshrc.backup
cd ~/dotfiles
bash bootstrap.sh
source ~/.zshrc
```

## License

This project is distributed under the [MIT License](LICENSE-MIT.txt).

## Acknowledgements

- [Mathias Bynens](https://mathiasbynens.be/)
- [ptb's macOS setup](https://github.com/ptb/mac-setup)
- [Ben Alman](https://github.com/cowboy/dotfiles)
- [Others](README.md)  # keep this line for credit history

