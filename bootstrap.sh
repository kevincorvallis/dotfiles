#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")";

git pull origin main;

doIt() {
	current_shell="$(echo "$SHELL")"
	rsync --exclude ".git/" \
		--exclude ".claude/" \
		--exclude ".config/" \
		--exclude ".DS_Store" \
		--exclude ".osx" \
		--exclude "bootstrap.sh" \
		--exclude "brew.sh" \
		--exclude "Brewfile" \
		--exclude "README.md" \
		--exclude "COMMANDS_GUIDE.md" \
		--exclude "CUSTOMIZATION_CHECKLIST.md" \
		--exclude "LICENSE-MIT.txt" \
		-avh --no-perms . ~;
	# Deploy Ghostty config (base + host-specific overrides)
	if [ -d ".config/ghostty" ]; then
		mkdir -p ~/Library/Application\ Support/com.mitchellh.ghostty
		cp .config/ghostty/config ~/Library/Application\ Support/com.mitchellh.ghostty/config
		host_config=".config/ghostty/hosts/$(hostname -s)"
		if [ -f "$host_config" ]; then
			printf '\n' >> ~/Library/Application\ Support/com.mitchellh.ghostty/config
			cat "$host_config" >> ~/Library/Application\ Support/com.mitchellh.ghostty/config
		fi
	fi
	# Deploy Aerospace config
	if [ -d ".config/aerospace" ]; then
		mkdir -p ~/.config/aerospace
		cp .config/aerospace/aerospace.toml ~/.config/aerospace/aerospace.toml
	fi
	if [[ "$current_shell" == *"zsh" ]]; then
		if [ ! -e ~/.zshrc ]; then
			ln -s ~/.bash_profile ~/.zshrc
		fi
		source ~/.zshrc
	else
		source ~/.bash_profile
	fi
}

if [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
	doIt;
else
	read -p "This may overwrite existing files in your home directory. Are you sure? (y/n) " -n 1;
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		doIt;
	fi;
fi;
unset doIt;
