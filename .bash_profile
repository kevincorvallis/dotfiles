# ~/.bash_profile - Minimal bash config for script compatibility
# Main shell config is in ~/.zshrc

# PATH
export PATH="$HOME/bin:$HOME/.local/bin:$PATH"

# Homebrew (Apple Silicon)
if [[ -d "/opt/homebrew" ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Load shared dotfiles
for file in ~/.{exports,aliases,functions,extra}; do
    [[ -r "$file" ]] && [[ -f "$file" ]] && source "$file"
done
unset file
