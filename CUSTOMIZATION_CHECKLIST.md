# Dotfiles Customization Checklist (File-by-File)

Use this checklist to review each file and decide which settings to keep, modify, or remove before applying the dotfiles. Mark off items as you handle them.

## `bootstrap.sh`
- [ ] Pull latest repo and rsync dotfiles into `$HOME`.
- [ ] Detect default shell; create and source `.zshrc` when using zsh.
- [ ] Prompt before overwriting files and optionally back up originals.
- [ ] Source the appropriate profile (`~/.zshrc` or `~/.bash_profile`) after syncing.

## `brew.sh` / `Brewfile`
- [ ] Prefer a `Brewfile` and run `brew bundle --file=Brewfile` for reproducible installs.
- [ ] Remove deprecated flags (`gnu-sed --with-default-names`, `wget --with-iri`, `bash-completion2`, `vim --with-override-system-vi`, `imagemagick --with-webp`).
- [ ] Add the `mas` CLI and script Mac App Store installs.
- [ ] Include desired taps, casks, fonts, and formulas; prune unused ones.
- [ ] Keep `brew.sh` minimal: `brew update`, `brew upgrade`, `brew cleanup`.

## `.macos`
### General UI/UX
- [ ] Restore default accent color or set your own.
- [ ] Show scrollbars automatically instead of always.
- [ ] Keep natural scrolling direction or remove override.
- [ ] Optionally enable Dark Mode by default.
- [ ] Disable transparency and focus ring animations if desired.
- [ ] Expand save and print panels by default.
- [ ] Save to disk instead of iCloud for new documents.
- [ ] Update Notification Center suppression for Big Sur and later.

### Input devices
- [ ] Enable tap-to-click and secondary click.
- [ ] Allow "natural" scrolling (`com.apple.swipescrolldirection -bool true`).
- [ ] Set fast keyboard repeat; disable press-and-hold.
- [ ] Boost Bluetooth audio quality (`Apple Bitpool Min`).

### Regional defaults
- [ ] Primary language and locale set to US (`AppleLanguages -array "en_US"`, `AppleLocale -string "en_US@currency=USD"`).
- [ ] Imperial measurement units (`AppleMeasurementUnits -string "Inches"`, `AppleMetricUnits -bool false`).
- [ ] Preferred US time zone (e.g., `America/New_York`).
- [ ] Show input menu on login screen.

### Energy & power
- [ ] Configure `pmset` options for sleep, standby delay, and hibernation.
- [ ] Decide on lid wakeup, restart after power loss, and restart on freeze.

### Screen & display
- [ ] Require password immediately after sleep or screensaver.
- [ ] Set screenshot location/format and disable shadow.
- [ ] Enable HiDPI display modes if needed.

### Finder
- [ ] Allow quitting Finder and disable window animations.
- [ ] Show hidden files, extensions, status bar, and path bar.
- [ ] Keep folders on top when sorting by name.
- [ ] Search current folder by default.
- [ ] Enable snap-to-grid, custom icon size, and item info on desktop.
- [ ] Avoid creating `.DS_Store` on network or USB volumes.
- [ ] Show `~/Library` and `/Volumes` folders.
- [ ] Use list view by default and disable trash empty warning.

### Dock & hot corners
- [ ] Relax auto-hide and animation tweaks.
- [ ] Configure or remove hot-corner actions.
- [ ] Add or remove persistent Dock apps.

### Menu bar & Spotlight
- [ ] Hide/show menu bar icons as desired.
- [ ] Reorder or disable Spotlight search categories and suggestions.

### Terminal & iTerm
- [ ] Install Solarized Dark theme and set as default.
- [ ] Enable Secure Keyboard Entry.
- [ ] Disable quit prompts for Terminal and iTerm.

### Miscellaneous
- [ ] Mute boot chime using modern key (`sudo nvram StartupMute=%01`).
- [ ] Prevent Music.app from capturing media keys (`com.apple.rcd.plist`).
- [ ] Consider adding a dark-mode toggle or variable.

## `.bash_profile` and `.bashrc`
- [ ] Ensure they source `.bash_prompt`, `.aliases`, `.exports`, `.functions`, and optional `~/.extra`.
- [ ] Add `PATH` entries or environment variables for tools.
- [ ] Customize shell options or prompt behavior.
- [ ] For zsh users, mirror logic in `.zshrc`.

## `.aliases`
- [ ] Review directory shortcuts (`dw`, `ic`, etc.) and update paths.
- [ ] Prune unused aliases; add personal commands.
- [ ] Verify macOS helpers (`cleanup`, `hidedesktop`, etc.) are still useful.
- [ ] Update application paths (Chrome, Sublime Text, etc.).

## `.exports`
- [ ] Confirm `LANG`/`LC_ALL` set to `en_US.UTF-8`.
- [ ] Set preferred `EDITOR` and adjust history sizes.
- [ ] Update or remove `ICLOUD` environment variable.
- [ ] Modify `NODE_REPL_*` and Python settings as needed.

## `.functions`
- [ ] Customize utility functions (`mkd`, `targz`, `server`, `tre`).
- [ ] Remove functions you don't use or add new ones.
- [ ] Verify compatibility with zsh if using.

## `.bash_prompt`
- [ ] Change prompt colors/theme or git status details.
- [ ] Port to zsh (`PROMPT`/`RPROMPT`) if desired.

## `.gitconfig`, `.gitignore`, `.gitattributes`
- [ ] Set `user.name` and `user.email`.
- [ ] Adjust aliases, difftool/mergetool, or signing preferences.
- [ ] Extend global ignore patterns and attributes.

## `.tmux.conf` / `.screenrc`
- [ ] Set preferred prefix keys and key bindings.
- [ ] Enable mouse support or customize status bar.
- [ ] Remove unused session manager configs.

## `.vimrc`, `.gvimrc`, and `.vim/`
- [ ] Choose color scheme and plugin manager.
- [ ] Configure clipboard, swap/backup/undo directories.
- [ ] Define indentation, mappings, and GUI-specific settings.

## `bin/`
- [ ] Review helper scripts for macOS version compatibility.
- [ ] Add personal scripts and ensure `bin` is on `$PATH`.

## Documentation (`README.md`, `COMMANDS_GUIDE.md`)
- [ ] Update docs when behavior changes or new tools are added.
- [ ] Provide usage examples for custom aliases and functions.

## After customization
1. Run `bash bootstrap.sh` to sync files into your home directory.
2. Execute `brew bundle --file=Brewfile` to install packages.
3. Apply system defaults with `./.macos`.
4. Reload your shell or log out/in to activate changes.
5. Keep machine-specific overrides in `~/.extra` to avoid merge conflicts.
