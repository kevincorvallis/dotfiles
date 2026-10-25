#!/usr/bin/env bash
# bootstrap.sh — copy this repo's dotfiles into $HOME using an explicit allowlist.
# Files that already match are left alone; files that differ are backed up to
# ~/.dotfiles-backup/<timestamp>/ before they are replaced. Safe to re-run.
# Must stay compatible with macOS /bin/bash 3.2 (it runs before Homebrew).

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1
REPO="$(pwd -P)"

usage() {
	printf '%s\n' \
		'Usage: bash bootstrap.sh [-f|--force] [-n|--dry-run] [--launchagents] [-h|--help]' \
		'' \
		'  -f, --force      Do not ask for confirmation.' \
		'  -n, --dry-run    Show what would change (a drift report). Writes nothing.' \
		'  --launchagents   Also install launchagents/*.plist into ~/Library/LaunchAgents and load them.' \
		'  -h, --help       Show this help.'
}

FORCE=0 DRY=0 AGENTS=0
for arg in "$@"; do
	case "$arg" in
		-f | --force) FORCE=1 ;;
		-n | --dry-run) DRY=1 ;;
		--launchagents) AGENTS=1 ;;
		-h | --help) usage; exit 0 ;;
		*) echo "bootstrap.sh: unknown option: $arg" >&2; usage >&2; exit 2 ;;
	esac
done

# ---------- preflight (warn only) ----------
if [ "$(uname -s)" != "Darwin" ]; then
	echo "warning: not macOS — the app config paths below assume macOS." >&2
fi
if ! command -v brew > /dev/null 2>&1 && [ ! -x /opt/homebrew/bin/brew ]; then
	echo "warning: Homebrew not found. Install it and run 'brew bundle' first; git's pager (delta) and the shell tools come from the Brewfile." >&2
fi

if [ "$FORCE" = 0 ] && [ "$DRY" = 0 ]; then
	printf 'Copy dotfiles into %s? Files that differ are backed up first. (y/n) ' "$HOME"
	reply=""
	read -r -n 1 reply || true
	echo
	case "$reply" in
		y | Y) ;;
		*) echo "Aborted; nothing changed."; exit 1 ;;
	esac
fi

# ---------- helpers ----------
BACKUP_DIR="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"
BACKED_UP=0 CHANGED=0 FAILED=0
N_NEW=0 N_UPD=0 N_SAME=0 N_DRIFT=0 N_SKIP=0
TMP="$(mktemp -d "${TMPDIR:-/tmp}/dotfiles.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

# The "~/" printed below is display text, not a path to expand.
# shellcheck disable=SC2088
pretty() {
	case "$1" in
		"$HOME"/*) printf '~/%s' "${1#"$HOME"/}" ;;
		*) printf '%s' "$1" ;;
	esac
}
say() { printf '  %-13s %s\n' "$1" "$2"; }
section() { printf '\n%s\n' "$1"; }
skip() {
	say "skipped" "$1 (not in repo)"
	N_SKIP=$((N_SKIP + 1))
}

# install_file SRC DST [x]
# Copy SRC to DST unless identical. An existing DST that differs (file, symlink or
# directory) is moved into BACKUP_DIR first, so nothing is lost and no symlink is
# written through. "x" makes DST executable. Sets CHANGED=1 when DST was written.
install_file() {
	local src=$1 dst=$2 exe=${3:-} bak
	CHANGED=0
	if [ -f "$dst" ] && cmp -s "$src" "$dst"; then
		say "unchanged" "$(pretty "$dst")"
		N_SAME=$((N_SAME + 1))
	elif [ -e "$dst" ] || [ -L "$dst" ]; then
		if [ "$DRY" = 1 ]; then
			say "would-change" "$(pretty "$dst") (differs)"
		else
			bak="$BACKUP_DIR/${dst#"$HOME"/}"
			mkdir -p "$(dirname "$bak")"
			mv "$dst" "$bak"
			cp "$src" "$dst"
			BACKED_UP=1 CHANGED=1
			say "backed-up" "$(pretty "$dst") (old copy in backup dir)"
		fi
		N_UPD=$((N_UPD + 1))
	else
		if [ "$DRY" = 1 ]; then
			say "would-change" "$(pretty "$dst") (new)"
		else
			mkdir -p "$(dirname "$dst")"
			cp "$src" "$dst"
			CHANGED=1
			say "installed" "$(pretty "$dst")"
		fi
		N_NEW=$((N_NEW + 1))
	fi
	if [ "$exe" = x ] && [ "$DRY" = 0 ]; then
		chmod +x "$dst"
	fi
}

# deploy SRC DST [x] — install_file for a source that may not exist.
deploy() {
	if [ -f "$1" ]; then
		install_file "$@"
	else
		skip "$1"
	fi
}

# install_tree SRCDIR DSTDIR [GLOB] — every file under SRCDIR, recursively; files
# matching GLOB become executable. Extra files already in DSTDIR are never touched.
install_tree() {
	local src=$1 dst=$2 glob=${3:-} f exe
	if [ ! -d "$src" ]; then
		skip "$src/"
		return 0
	fi
	find "$src" -type f ! -name .DS_Store ! -name '*.example' ! -name '*.pyc' ! -path '*/__pycache__/*' |
		LC_ALL=C sort > "$TMP/tree"
	while IFS= read -r f <&3; do
		exe=""
		if [ -n "$glob" ]; then
			# $glob is meant to match as a pattern, so it stays unquoted.
			# shellcheck disable=SC2254
			case "$(basename "$f")" in
				$glob) exe=x ;;
			esac
		fi
		install_file "$f" "$dst/${f#"$src"/}" "$exe"
	done 3< "$TMP/tree"
}

# ---------- deploy ----------
if [ "$DRY" = 1 ]; then
	echo "Dry run: nothing will be written."
fi

section "Shell and CLI (~/)"
for f in .zshrc .exports .aliases .functions .gitconfig .gitignore .vimrc .tmux.conf .curlrc .hushlogin .inputrc; do
	deploy "$f" "$HOME/$f"
done
install_tree .vim "$HOME/.vim"

section "Scripts (~/bin)"
install_tree bin "$HOME/bin" '*'

section "Ghostty"
if [ -f .config/ghostty/config ]; then
	host="$(scutil --get LocalHostName 2> /dev/null)" || host="$(hostname -s 2> /dev/null)" || host=""
	cp .config/ghostty/config "$TMP/ghostty"
	if [ -n "$host" ] && [ -f ".config/ghostty/hosts/$host" ]; then
		printf '\n' >> "$TMP/ghostty"
		cat ".config/ghostty/hosts/$host" >> "$TMP/ghostty"
		say "overlay" ".config/ghostty/hosts/$host"
	fi
	install_file "$TMP/ghostty" "$HOME/Library/Application Support/com.mitchellh.ghostty/config"
else
	skip .config/ghostty/config
fi

section "App configs (~/.config)"
deploy .config/aerospace/aerospace.toml "$HOME/.config/aerospace/aerospace.toml"
deploy .config/starship/starship.toml "$HOME/.config/starship/starship.toml"
deploy .config/atuin/config.toml "$HOME/.config/atuin/config.toml"
deploy .config/finder/favorites.txt "$HOME/.config/finder/favorites.txt"

# Karabiner rewrites karabiner.json from its own UI, so only seed it on a fresh machine.
k_src=.config/karabiner/karabiner.json
k_dst="$HOME/.config/karabiner/karabiner.json"
if [ ! -f "$k_src" ]; then
	skip "$k_src"
elif [ -e "$k_dst" ] && ! cmp -s "$k_src" "$k_dst"; then
	say "drift" "$(pretty "$k_dst") differs from the repo; left alone (Karabiner owns it)."
	say "" "To take the repo copy: cp '$REPO/$k_src' ~/.config/karabiner/"
	N_DRIFT=$((N_DRIFT + 1))
else
	install_file "$k_src" "$k_dst"
fi

section "Espanso"
esp="$HOME/Library/Application Support/espanso"
for d in config match; do
	if [ ! -d ".config/espanso/$d" ]; then
		skip ".config/espanso/$d/"
		continue
	fi
	# *.yml only: private.yml.example is a template, and local files such as
	# private.yml are never touched because they are not in the repo.
	for f in .config/espanso/"$d"/*.yml; do
		if [ -f "$f" ]; then
			install_file "$f" "$esp/$d/$(basename "$f")"
		fi
	done
done

section "Sublime Text"
install_tree .config/sublime/User "$HOME/Library/Application Support/Sublime Text/Packages/User"

section "Claude Code (~/.claude)"
for f in settings.json CLAUDE.md AGENT-GRAPH.md; do
	deploy ".config/claude/$f" "$HOME/.claude/$f"
done
for d in agents commands rules skills scripts output-styles; do
	install_tree ".config/claude/$d" "$HOME/.claude/$d"
done
install_tree .config/claude/hooks "$HOME/.claude/hooks" '*.sh'

section "Codex skills (~/.codex/skills)"
install_tree .config/codex/skills "$HOME/.codex/skills"

section "MCP server scripts (~/.local/share/mcp)"
install_tree .config/mcp "$HOME/.local/share/mcp"

section "LaunchAgents"
if [ "$AGENTS" = 0 ]; then
	say "not loaded" "pass --launchagents to install launchagents/*.plist"
elif [ ! -d launchagents ]; then
	skip "launchagents/"
else
	uid="$(id -u)"
	for p in launchagents/*.plist; do
		if [ ! -f "$p" ]; then
			continue
		fi
		name="$(basename "$p")"
		label="${name%.plist}"
		dst="$HOME/Library/LaunchAgents/$name"
		sed "s|__HOME__|$HOME|g" "$p" > "$TMP/$name"
		install_file "$TMP/$name" "$dst"
		if [ "$DRY" = 1 ]; then
			continue
		fi
		if [ "$CHANGED" = 1 ] || ! launchctl print "gui/$uid/$label" > /dev/null 2>&1; then
			launchctl bootout "gui/$uid" "$dst" 2> /dev/null || true
			if launchctl bootstrap "gui/$uid" "$dst"; then
				say "loaded" "$label"
			else
				say "FAILED" "launchctl bootstrap gui/$uid $(pretty "$dst")"
				FAILED=1
			fi
		fi
	done
fi

# ---------- summary ----------
echo
if [ "$DRY" = 1 ]; then
	echo "Dry run: $((N_NEW + N_UPD)) would change ($N_NEW new, $N_UPD differ), $N_SAME unchanged, $N_DRIFT drift, $N_SKIP skipped. Nothing was written."
	exit 0
fi
echo "Done: $N_NEW installed, $N_UPD replaced, $N_SAME unchanged, $N_DRIFT drift, $N_SKIP skipped."
if [ "$BACKED_UP" = 1 ]; then
	echo "Previous versions of replaced files: $(pretty "$BACKUP_DIR")"
fi
if [ ! -f "$HOME/.extra" ] && [ -f .extra.example ]; then
	echo "No ~/.extra yet: machine-local settings go there (template: $REPO/.extra.example)."
fi
echo "Open a new shell: exec zsh -l"
exit "$FAILED"
