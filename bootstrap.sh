#!/usr/bin/env bash
# bootstrap.sh — copy this repo's dotfiles into $HOME using an explicit allowlist.
# Files that already match are left alone; files that differ are backed up to
# ~/.dotfiles-backup/<timestamp>/ before they are replaced. Safe to re-run.
# Files named in ~/.config/dotfiles/skip are kept as they are on this Mac.
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
		'  -h, --help       Show this help.' \
		'' \
		'To keep a file as it is on this Mac, list it in ~/.config/dotfiles/skip: one path' \
		'under ~ per line ("~/path" or "path"); lines that start with "#" are comments.' \
		'An entry that matches no file bootstrap deploys stops the run.'
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

# Per-Mac skip list (untracked; bootstrap only reads it). It names files under ~
# that this Mac keeps as they are: one per line, written as "~/path", "$HOME/path"
# or "path". Lines that start with "#" are comments.
SKIP_FILE="$HOME/.config/dotfiles/skip"
KEPT=0 N_KEPT=0 N_MISS=0
: > "$TMP/skip"
: > "$TMP/skip.hit"
if [ -f "$SKIP_FILE" ]; then
	while IFS= read -r line || [ -n "$line" ]; do
		line="${line#"${line%%[![:space:]]*}"}"
		line="${line%"${line##*[![:space:]]}"}"
		case "$line" in
			'' | '#'*) continue ;;
		esac
		line="${line#\~/}"
		line="${line#\$HOME/}"
		line="${line#"$HOME"/}"
		printf '%s\n' "$line" >> "$TMP/skip"
	done < "$SKIP_FILE"
fi

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

# kept DST — true when DST is in the skip list. Reports it and records the match.
kept() {
	local rel=${1#"$HOME"/}
	if [ -s "$TMP/skip" ] && grep -qxF -- "$rel" "$TMP/skip"; then
		printf '%s\n' "$rel" >> "$TMP/skip.hit"
		say "kept" "$(pretty "$1") (in the skip list)"
		N_KEPT=$((N_KEPT + 1))
		return 0
	fi
	return 1
}

# install_file SRC DST [x]
# Copy SRC to DST unless identical. An existing DST that differs (file, symlink or
# directory) is moved into BACKUP_DIR first, so nothing is lost and no symlink is
# written through. "x" makes DST executable. Sets CHANGED=1 when DST was written.
# A DST named in the skip list is left alone, whatever it holds; that sets KEPT=1.
install_file() {
	local src=$1 dst=$2 exe=${3:-} bak
	CHANGED=0 KEPT=0
	if kept "$dst"; then
		KEPT=1
		return 0
	fi
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

# build SRC OUT [OVERLAY] — write SRC to OUT with every line of the form
# "<!-- include: REPO/PATH -->" replaced by that repo file's contents. When
# OVERLAY exists (an untracked machine-local file), append it after a blank line.
build() {
	local src=$1 out=$2 overlay=${3:-} line inc
	: > "$out"
	while IFS= read -r line || [ -n "$line" ]; do
		case "$line" in
			'<!-- include: '*' -->')
				inc=${line#'<!-- include: '}
				inc=${inc%' -->'}
				cat "$inc" >> "$out"
				;;
			*) printf '%s\n' "$line" >> "$out" ;;
		esac
	done < "$src"
	if [ -n "$overlay" ] && [ -f "$overlay" ]; then
		printf '\n' >> "$out"
		cat "$overlay" >> "$out"
		say "overlay" "$(pretty "$overlay")"
	fi
}

# deploy_built SRC DST [OVERLAY] — deploy for a file that is built first (see build).
deploy_built() {
	if [ ! -f "$1" ]; then
		skip "$1"
		return 0
	fi
	build "$1" "$TMP/built" "${3:-}"
	install_file "$TMP/built" "$2"
}

# ---------- skip list guard ----------
# An entry that matches no file bootstrap deploys (a typo, a folder, the wrong
# case) would leave that file unprotected. So a real run first does a dry run of
# itself, and stops before it writes anything if any entry matched nothing.
if [ "$DRY" = 0 ] && [ -s "$TMP/skip" ]; then
	set -- -n
	if [ "$AGENTS" = 1 ]; then
		set -- -n --launchagents
	fi
	if ! "$BASH" "$REPO/bootstrap.sh" "$@" > "$TMP/guard" 2>&1; then
		if grep 'no match' "$TMP/guard"; then
			echo "Stopped: fix $(pretty "$SKIP_FILE") first. Nothing was written."
		else
			cat "$TMP/guard"
			echo "Stopped: the dry run that checks the skip list failed. Nothing was written."
		fi
		exit 1
	fi
fi

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
elif kept "$k_dst"; then
	:
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
for f in settings.json AGENT-GRAPH.md; do
	deploy ".config/claude/$f" "$HOME/.claude/$f"
done
# CLAUDE.md, AGENTS.md and the Cursor skills are built: the shared rules in
# .config/agents/ are included, then this Mac's own *.local.md is appended.
deploy_built .config/claude/CLAUDE.md "$HOME/.claude/CLAUDE.md" "$HOME/.claude/CLAUDE.local.md"
for d in agents commands rules skills scripts output-styles; do
	install_tree ".config/claude/$d" "$HOME/.claude/$d"
done
install_tree .config/claude/hooks "$HOME/.claude/hooks" '*.sh'

section "Codex (~/.codex)"
deploy_built .config/codex/AGENTS.md "$HOME/.codex/AGENTS.md" "$HOME/.codex/AGENTS.local.md"
install_tree .config/codex/skills "$HOME/.codex/skills"

section "Cursor skills (~/.cursor/skills)"
if [ -d .config/cursor/skills ]; then
	find .config/cursor/skills -type f ! -name .DS_Store | LC_ALL=C sort > "$TMP/tree"
	while IFS= read -r f <&3; do
		deploy_built "$f" "$HOME/.cursor/skills/${f#.config/cursor/skills/}"
	done 3< "$TMP/tree"
else
	skip .config/cursor/skills/
fi

section "MCP server scripts (~/.local/share/mcp)"
install_tree .config/mcp "$HOME/.local/share/mcp"

section "LaunchAgents"
if [ "$AGENTS" = 0 ]; then
	say "not loaded" "pass --launchagents to install launchagents/*.plist"
	# This run deploys no launch agent, but a skip list entry for one is still valid.
	for p in launchagents/*.plist; do
		if [ -f "$p" ]; then
			printf 'Library/LaunchAgents/%s\n' "$(basename "$p")" >> "$TMP/skip.hit"
		fi
	done
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
		if [ "$DRY" = 1 ] || [ "$KEPT" = 1 ]; then
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
# Skip list entries that matched no file bootstrap deploys.
if [ -s "$TMP/skip" ]; then
	while IFS= read -r p; do
		if ! grep -qxF -- "$p" "$TMP/skip.hit"; then
			say "no match" "$(pretty "$HOME/$p") is in the skip list, but bootstrap deploys no such file"
			N_MISS=$((N_MISS + 1))
		fi
	done < "$TMP/skip"
fi
KEPT_NOTE=""
if [ "$N_KEPT" -gt 0 ]; then
	KEPT_NOTE=", $N_KEPT kept (skip list)"
fi
echo
if [ "$DRY" = 1 ]; then
	echo "Dry run: $((N_NEW + N_UPD)) would change ($N_NEW new, $N_UPD differ), $N_SAME unchanged, $N_DRIFT drift, $N_SKIP skipped$KEPT_NOTE. Nothing was written."
	if [ "$N_MISS" -gt 0 ]; then
		echo "$N_MISS skip list entries match nothing. Fix $(pretty "$SKIP_FILE"); a real run stops until they match."
		exit 1
	fi
	exit 0
fi
if [ "$N_MISS" -gt 0 ]; then
	FAILED=1
fi
echo "Done: $N_NEW installed, $N_UPD replaced, $N_SAME unchanged, $N_DRIFT drift, $N_SKIP skipped$KEPT_NOTE."
if [ "$BACKED_UP" = 1 ]; then
	echo "Previous versions of replaced files: $(pretty "$BACKUP_DIR")"
fi
if [ ! -f "$HOME/.extra" ] && [ -f .extra.example ]; then
	echo "No ~/.extra yet: machine-local settings go there (template: $REPO/.extra.example)."
fi
echo "Open a new shell: exec zsh -l"
exit "$FAILED"
