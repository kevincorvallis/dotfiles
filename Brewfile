# Packages for a fresh Apple Silicon Mac: brew bundle --file=Brewfile
# Third-party tap items carry `trusted: true`; Homebrew 7 refuses untrusted taps.

# Taps
tap "nikitabobko/tap"
tap "supabase/tap"
# Not publicly reachable over HTTPS, so clone over SSH (personal key must be on GitHub first)
tap "kevincorvallis/tap", "git@github.com:kevincorvallis/homebrew-tap.git"

# Shell: prompt, history, navigation and plugins (wired up in .zshrc)
brew "starship"
brew "atuin"
brew "zoxide"
brew "direnv"
brew "fzf"
brew "zsh-autosuggestions"
brew "zsh-syntax-highlighting"

# Core CLI
brew "coreutils"    # unprefixed timeout, used by bin/disk-clean
brew "git"
brew "gh"
brew "git-delta"    # .gitconfig pager
brew "ripgrep"
brew "fd"
brew "bat"
brew "eza"
brew "jq"           # Claude hooks
brew "tree"
brew "tmux"         # .tmux.conf ships with the repo
brew "shellcheck"   # scripts/check.sh (CI runs it too)
brew "dockutil"     # sets the Dock layout on a new Mac

# Languages and dev tooling
brew "node"
brew "python@3.14"
brew "uv"
brew "cmake"        # VoiceInk whisper.xcframework build
brew "libomp"       # xgboost
brew "xcodegen"
brew "fastlane"
brew "awscli"
brew "supabase/tap/supabase", trusted: true
brew "ollama"

# Media and documents
brew "yt-dlp"
brew "ffmpeg"       # yt-dlp audio/video merges
brew "imagemagick"
brew "exiftool"
brew "poppler"      # pdftotext, pdfinfo

# Mac App Store CLI, used by the mas lines below
brew "mas"

# Fonts
cask "font-jetbrains-mono-nerd-font"

# Terminal, editor and desktop utilities
cask "ghostty"
cask "sublime-text"
cask "nikitabobko/tap/aerospace", trusted: true
cask "raycast"
cask "karabiner-elements"
cask "logi-options+"
cask "espanso"
cask "kevincorvallis/tap/emblem", trusted: true
cask "shottr"
cask "stats"
cask "soundsource"
cask "tailscale-app"
cask "jordanbaird-ice"   # menu bar manager
cask "finicky"           # routes links to a browser by rule
cask "jiggler"
# VoiceInk and Insang are not casks: they are built from their own repos (SETUP.md)

# Development
cask "visual-studio-code"
cask "cursor"
cask "docker-desktop"
cask "claude"
cask "chatgpt"
cask "figma"

# Browsers, notes, chat and media
cask "firefox"
cask "google-chrome"
cask "obsidian"
cask "anki"
cask "discord"
cask "slack"
cask "zoom"
cask "spotify"
cask "vlc"
cask "nvidia-geforce-now"

# Global npm CLIs
npm "@openai/codex"   # codex MCP expects /opt/homebrew/bin/codex
npm "vercel"

# Mac App Store (sign in to the App Store first)
mas "Xcode", id: 497799835
mas "Day One", id: 1055511498
mas "KakaoTalk", id: 869223134
mas "NordVPN", id: 905953485
mas "WhatsApp", id: 310633997
mas "Keynote", id: 409183694
mas "Numbers", id: 409203825
mas "Pages", id: 409201541
