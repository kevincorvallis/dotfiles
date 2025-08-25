#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")";

git pull origin main;

doIt() {
	current_shell="$(echo "$SHELL")"
	rsync --exclude ".git/" \
		--exclude ".DS_Store" \
		--exclude ".osx" \
		--exclude "bootstrap.sh" \
		--exclude "README.md" \
		--exclude "LICENSE-MIT.txt" \
		-avh --no-perms . ~;
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
