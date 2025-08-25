#!/usr/bin/env bash

# Install command-line tools using Homebrew.

# Make sure we’re using the latest Homebrew.
brew update

# Upgrade any already-installed formulae.
brew upgrade

# Install or update packages listed in the Brewfile.
brew bundle --file=Brewfile

# Remove outdated versions from the cellar.
brew cleanup
