# Load bash profile configurations (shared aliases, exports, functions)
if [ -f ~/.bash_profile ]; then
  source ~/.bash_profile
fi

# Zsh-specific tool initialization (overrides bash init from .exports)
# starship - cross-shell prompt
if command -v starship &> /dev/null; then
  eval "$(starship init zsh)"
fi

# zoxide - smarter cd
if command -v zoxide &> /dev/null; then
  eval "$(zoxide init zsh)"
fi

# atuin - shell history
if command -v atuin &> /dev/null; then
  eval "$(atuin init zsh)"
fi
