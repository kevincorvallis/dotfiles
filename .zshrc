# ~/.zshrc - Main zsh configuration

# =============================================================================
# PATH
# =============================================================================
typeset -U path fpath                # Drop duplicate entries (nested shells, tmux)
export PATH="$HOME/bin:$HOME/.local/bin:$PATH"

# =============================================================================
# Homebrew (Apple Silicon) - sets HOMEBREW_PREFIX, PATH and fpath
# =============================================================================
if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# =============================================================================
# Zsh Options
# =============================================================================
# History
HISTFILE="$HOME/.zsh_history"
HISTSIZE=32768
SAVEHIST=32768
setopt HIST_IGNORE_DUPS      # Don't record duplicates
setopt HIST_IGNORE_SPACE     # Don't record commands starting with space
setopt SHARE_HISTORY         # Share history between sessions
setopt APPEND_HISTORY        # Append to history file
# Keep lines that look like they carry credentials out of the history file.
# (#i) = case-insensitive; needs EXTENDED_GLOB (set below). Atuin has its own filter.
HISTORY_IGNORE='(#i)(*password*|*secret*|*token*|*api_key*|*apikey*|*bearer*)'

# Directory navigation
setopt AUTO_CD               # cd by typing directory name
setopt AUTO_PUSHD            # Push directories onto stack
setopt PUSHD_IGNORE_DUPS     # Don't push duplicates
setopt CDABLE_VARS           # cd to named directories

# Globbing and matching
setopt EXTENDED_GLOB         # Extended globbing
setopt NO_CASE_GLOB          # Case-insensitive globbing

# Correction
setopt CORRECT               # Command correction

# =============================================================================
# Completion (fpath already includes Homebrew's site-functions)
# =============================================================================
autoload -Uz compinit && compinit

# Case-insensitive completion
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'

# Menu selection
zstyle ':completion:*' menu select

# =============================================================================
# Key Bindings
# =============================================================================
bindkey -e                           # Emacs key bindings

# Paste the clipboard as a single line (newlines -> spaces).
# Ghostty sends ^V for cmd+shift+v; plain cmd+v still pastes normally.
paste-oneline() {
    local clip
    clip=$(pbpaste | tr '\n' ' ')
    LBUFFER+="$clip"
}
zle -N paste-oneline
bindkey '^V' paste-oneline

# =============================================================================
# Load shared dotfiles (~/.extra = untracked machine-local overrides)
# =============================================================================
for file in ~/.{exports,aliases,functions,extra}; do
    [[ -r "$file" ]] && [[ -f "$file" ]] && source "$file"
done
unset file

# =============================================================================
# Plugins and tool integrations (each skipped when not installed)
# =============================================================================
if [[ -r "${HOMEBREW_PREFIX:-}/share/zsh-autosuggestions/zsh-autosuggestions.zsh" ]]; then
    source "$HOMEBREW_PREFIX/share/zsh-autosuggestions/zsh-autosuggestions.zsh"
fi

# fzf key bindings (Ctrl-T files, Alt-C dirs). Loaded before atuin so atuin keeps Ctrl-R.
# Only with a terminal ($TTY set): without one, its option save/restore errors on `zle`.
if [[ -n "$TTY" ]] && command -v fzf &>/dev/null; then
    eval "$(fzf --zsh)"
fi

# Starship prompt
if command -v starship &>/dev/null; then
    eval "$(starship init zsh)"
fi

# Zoxide (smarter cd)
if command -v zoxide &>/dev/null; then
    eval "$(zoxide init zsh)"
fi

# Atuin (shell history search; binds Ctrl-R and Up)
if command -v atuin &>/dev/null; then
    eval "$(atuin init zsh)"
fi

# Direnv (per-directory env vars)
if command -v direnv &>/dev/null; then
    eval "$(direnv hook zsh)"
fi

# GitHub MCP (Claude Code github plugin): reuse gh's Keychain credential.
# Exported only when gh is logged in, so a fresh machine doesn't get an empty token.
if [[ -z "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ]] && command -v gh &>/dev/null; then
    _gh_token="$(gh auth token 2>/dev/null)"
    if [[ -n "$_gh_token" ]]; then
        export GITHUB_PERSONAL_ACCESS_TOKEN="$_gh_token"
    fi
    unset _gh_token
fi

# Syntax highlighting must load last, after every widget above is defined
if [[ -r "${HOMEBREW_PREFIX:-}/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]]; then
    source "$HOMEBREW_PREFIX/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
fi
