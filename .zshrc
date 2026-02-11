# ~/.zshrc - Main zsh configuration

# =============================================================================
# PATH
# =============================================================================
export PATH="$HOME/bin:$HOME/.local/bin:$PATH"

# =============================================================================
# Homebrew (Apple Silicon)
# =============================================================================
if [[ -d "/opt/homebrew" ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# =============================================================================
# Zsh Options
# =============================================================================
# History
HISTFILE=~/.zsh_history
HISTSIZE=32768
SAVEHIST=32768
setopt HIST_IGNORE_DUPS      # Don't record duplicates
setopt HIST_IGNORE_SPACE     # Don't record commands starting with space
setopt SHARE_HISTORY         # Share history between sessions
setopt APPEND_HISTORY        # Append to history file
# Don't record commands that look like they contain sensitive data
HISTORY_IGNORE='(*password*|*secret*|*token*|*API_KEY*|export *TOKEN*|export *SECRET*)'

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
# Completion (compinit loaded after Homebrew FPATH is set, see below)
# =============================================================================

# Case-insensitive completion
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'

# Menu selection
zstyle ':completion:*' menu select

# Colors in completion
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"

# =============================================================================
# Prompt (Matrix style)
# =============================================================================
autoload -Uz vcs_info
precmd() { vcs_info }

setopt PROMPT_SUBST

# Git branch in prompt
zstyle ':vcs_info:git:*' formats ' %F{green}[%b]%f'
zstyle ':vcs_info:*' enable git

# Matrix prompt
PROMPT='%F{green}%~%f${vcs_info_msg_0_} %F{green}>>%f '

# =============================================================================
# Key Bindings
# =============================================================================
bindkey -e                           # Emacs key bindings
bindkey '^[[A' history-search-backward   # Up arrow searches history
bindkey '^[[B' history-search-forward    # Down arrow searches history

# =============================================================================
# Load shared dotfiles
# =============================================================================
for file in ~/.{exports,aliases,functions,extra}; do
    [[ -r "$file" ]] && [[ -f "$file" ]] && source "$file"
done
unset file

# =============================================================================
# Homebrew completions
# =============================================================================
if type brew &>/dev/null; then
    FPATH="$(brew --prefix)/share/zsh/site-functions:${FPATH}"
    autoload -Uz compinit && compinit
fi
