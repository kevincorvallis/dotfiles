# New Machine Setup

Step-by-step guide for setting up a fresh macOS (Apple Silicon) machine with these dotfiles.

## 1. Prerequisites

```bash
xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"
```

## 2. SSH Key + GitHub Auth

```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
eval "$(ssh-agent -s)"

mkdir -p ~/.ssh
cat >> ~/.ssh/config << 'EOF'
Host github.com
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
EOF

ssh-add --apple-use-keychain ~/.ssh/id_ed25519
pbcopy < ~/.ssh/id_ed25519.pub

# Add key to GitHub (easiest via gh CLI)
brew install gh
gh auth login  # Select: GitHub.com → SSH → paste key

ssh -T git@github.com  # Verify
```

## 3. Clone + Install

```bash
git clone git@github.com:kevincorvallis/dotfiles.git ~/dotfiles
cd ~/dotfiles
brew bundle --file=Brewfile
```

## 4. Work/Machine-Specific Overrides

Create `~/.extra` **before** bootstrapping to override personal defaults (e.g. git email):

```bash
cat > ~/.extra << 'EOF'
git config --global user.name "Your Name"
git config --global user.email "your-work-email@company.com"
EOF
```

## 5. Host-Specific Ghostty Config (Optional)

```bash
# Create overlay for this machine's hostname
vim ~/dotfiles/.config/ghostty/hosts/$(hostname -s)
```

## 6. Bootstrap

```bash
cd ~/dotfiles
bash bootstrap.sh
```

Deploys: shell configs → `~/`, Ghostty → App Support, Aerospace → `~/.config/`, Starship → `~/.config/`, Claude Code → `~/.claude/`

## 7. Extra Apps (Not in Brewfile)

```bash
brew install --cask obsidian
brew install node python
```

## 8. macOS Preferences (Optional)

Review before running — some settings may conflict with IT/MDM policies.

```bash
./.macos
```

Requires sudo. Some settings need logout/restart.

## Things to Watch Out For

- **Git email**: `.gitconfig` has personal email — override via `.extra` before committing
- **Atuin sync**: keep work/personal shell history separate if using sync
- **`.macos`**: review section by section on managed machines
- **Ghostty hosts**: only `brock` exists — create one for new hostname if needed
