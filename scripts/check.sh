#!/usr/bin/env bash
# scripts/check.sh — is this dotfiles repo production-ready?
# Read-only for the repo and the real HOME: bootstrap.sh only ever runs against
# throwaway HOME directories under $TMPDIR. Must stay compatible with /bin/bash 3.2.

set -uo pipefail

# (printf, not a heredoc: bash 3.2 always writes heredocs to /tmp, which sandboxes deny)
usage() {
	printf '%s\n' \
		'Usage: bash scripts/check.sh [--offline] [-h|--help]' \
		'' \
		'Runs every production-readiness check and prints PASS / FAIL / WARN / SKIP.' \
		'Exits 1 if anything FAILs.' \
		'' \
		'  1. script syntax     bash -n (/bin/bash 3.2), bash-4 scan, zsh -n, python, swift, shellcheck' \
		'  2. data files        json, toml, yaml, plist, ghostty config, .gitconfig' \
		'  3. bootstrap         fresh-HOME deploy, idempotency, dry-run, drift/backup, zsh -i' \
		'  4. public-repo guard work identifiers, secret shapes, hard-coded /Users paths' \
		'  5. Brewfile          parse, duplicates, tap trust, names vs formulae.brew.sh' \
		'  6. repo files & git  SETUP-referenced files exist, nothing untracked, overlays ignored' \
		'' \
		'  --offline   skip network checks (formulae.brew.sh, api.github.com)' \
		'  -h, --help  show this help' \
		'' \
		'Environment:' \
		'  DOTFILES_DENYLIST  extended regex (case-insensitive) of work identifiers that must' \
		'                     never appear in the repo, e.g. word1|word2. Kept out of the repo:' \
		'                     export it from ~/.extra; CI reads the DOTFILES_DENYLIST secret.' \
		'                     Unset = work-identifier scan skipped (WARN).' \
		'  CI                 when set (GitHub Actions sets it), untracked files FAIL, not WARN.'
}

OFFLINE=0
while [ $# -gt 0 ]; do
	case "$1" in
		--offline) OFFLINE=1 ;;
		-h | --help) usage; exit 0 ;;
		*) echo "check.sh: unknown option: $1" >&2; usage >&2; exit 2 ;;
	esac
	shift
done

cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1
ROOT="$(pwd -P)"
T="$(mktemp -d "${TMPDIR:-/tmp}/dotfiles-check.XXXXXX")" || exit 1
trap 'rm -rf "$T"' EXIT

BASH32=/bin/bash
[ -x "$BASH32" ] || BASH32=bash

# ---------- output ----------
NPASS=0 NFAIL=0 NWARN=0 NSKIP=0
if [ -t 1 ]; then
	C_G=$'\033[32m' C_R=$'\033[31m' C_Y=$'\033[33m' C_D=$'\033[2m' C_B=$'\033[1m' C_0=$'\033[0m'
else
	C_G='' C_R='' C_Y='' C_D='' C_B='' C_0=''
fi
pass() { NPASS=$((NPASS + 1)); printf '%sPASS%s  %s\n' "$C_G" "$C_0" "$*"; }
fail() { NFAIL=$((NFAIL + 1)); printf '%sFAIL%s  %s\n' "$C_R" "$C_0" "$*"; }
warn() { NWARN=$((NWARN + 1)); printf '%sWARN%s  %s\n' "$C_Y" "$C_0" "$*"; }
skip() { NSKIP=$((NSKIP + 1)); printf '%sSKIP%s  %s\n' "$C_D" "$C_0" "$*"; }
section() { printf '\n%s== %s ==%s\n' "$C_B" "$*" "$C_0"; }
# indent FILE — show (the start of) a tool's output under a FAIL line
indent() { head -n 15 "$1" | sed 's/^/        /'; }
have() { command -v "$1" > /dev/null 2>&1; }

# ---------- file list: tracked + untracked-not-ignored, existing regular files ----------
IS_GIT=0
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
	IS_GIT=1
	git -c core.quotePath=false ls-files -co --exclude-standard > "$T/ls"
else
	find . -type f ! -path './.git/*' | sed 's|^\./||' > "$T/ls"
fi
while IFS= read -r f; do
	if [ -f "$f" ] && [ ! -L "$f" ]; then
		printf '%s\n' "$f"
	fi
done < "$T/ls" | LC_ALL=C sort -u > "$T/files"
pick() { grep -E "$1" "$T/files"; }

# python3 with tomllib (3.11+); macOS /usr/bin/python3 is 3.9
PY=''
for p in python3 /opt/homebrew/bin/python3 /usr/local/bin/python3; do
	if "$p" -I -c 'import tomllib' > /dev/null 2>&1; then
		PY=$p
		break
	fi
done

# =====================================================================
section "1. Shell syntax"
# =====================================================================
: > "$T/bash.lst"
: > "$T/zsh.lst"
: > "$T/py.lst"
: > "$T/swift.lst"
for f in .zshrc .exports .aliases .functions .extra.example; do
	if [ -f "$f" ]; then echo "$f" >> "$T/zsh.lst"; fi
done
pick '^(bootstrap\.sh|\.macos|bin/.+|scripts/.+|\.config/claude/hooks/.+)$|\.(sh|zsh|py)$' > "$T/cand"
while IFS= read -r f; do
	first="$(head -n 1 "$f")"
	case "$first" in
		'#!'*zsh*) kind=zsh ;;
		'#!'*bash* | '#!/bin/sh'* | '#!/usr/bin/env sh'*) kind=bash ;;
		'#!'*python*) kind=python ;;
		'#!'*swift*) kind=swift ;;
		*)
			case "$f" in
				*.sh) kind=bash ;;
				*.zsh) kind=zsh ;;
				*.py) kind=python ;;
				*) kind=other ;;
			esac
			;;
	esac
	case "$kind" in
		bash) echo "$f" >> "$T/bash.lst" ;;
		zsh) echo "$f" >> "$T/zsh.lst" ;;
		python) echo "$f" >> "$T/py.lst" ;;
		swift) echo "$f" >> "$T/swift.lst" ;;
		*)
			case "$f" in
				bin/* | scripts/*) warn "$f: no recognised shebang (bash/sh/zsh/python/swift)" ;;
			esac
			;;
	esac
	case "$f" in
		bin/* | scripts/*.sh | .macos)
			if [ "$kind" != other ] && [ ! -x "$f" ]; then
				warn "$f is not executable (chmod +x $f)"
			fi
			;;
	esac
done < "$T/cand"

# bash -n with macOS /bin/bash 3.2: bootstrap, bin/ and .macos run before Homebrew's bash exists
n=0 bad=0
while IFS= read -r f; do
	n=$((n + 1))
	if ! "$BASH32" -n "$f" 2> "$T/err"; then
		bad=$((bad + 1))
		fail "bash -n $f"
		indent "$T/err"
	fi
done < "$T/bash.lst"
if [ "$bad" = 0 ]; then pass "bash -n with $BASH32 ($n files)"; fi

# Syntax /bin/bash 3.2 rejects at runtime but bash -n can't see (comment lines ignored)
BASH4_RE='(^|[;&|[:space:]])(declare|local|typeset)[[:space:]]+-[aAfFgilnprtux]*[Anlu]([[:space:]]|$)'
BASH4_RE="$BASH4_RE"'|(^|[;&|[:space:]])(mapfile|readarray|coproc)([[:space:]]|$)'
BASH4_RE="$BASH4_RE"'|\$\{[A-Za-z_][A-Za-z0-9_]*(\[[^]]*\])?(,,?|\^\^?)\}'
BASH4_RE="$BASH4_RE"'|\$\{[A-Za-z_][A-Za-z0-9_]*@[QEPAaKkUuL]\}'
BASH4_RE="$BASH4_RE"'|\$\{[A-Za-z_][A-Za-z0-9_]*\[-[0-9]+\]\}'
BASH4_RE="$BASH4_RE"'|\$\{[A-Za-z_][A-Za-z0-9_]*:[^}:]*:-[0-9]+\}'
BASH4_RE="$BASH4_RE"'|\|&|&>>|;;&|wait[[:space:]]+-n|shopt[[:space:]]+-s[[:space:]]+(globstar|lastpipe)|EPOCH(SECONDS|REALTIME)'
bad=0
grep -vxF scripts/check.sh "$T/bash.lst" > "$T/bash4.lst" # its own patterns would match; CI runs it under /bin/bash
while IFS= read -r f; do
	grep -nE "$BASH4_RE" "$f" | grep -vE '^[0-9]+:[[:space:]]*#' > "$T/b4"
	if [ -s "$T/b4" ]; then
		bad=$((bad + 1))
		fail "$f uses bash 4+ syntax (must run on macOS /bin/bash 3.2)"
		indent "$T/b4"
	fi
done < "$T/bash4.lst"
if [ "$bad" = 0 ]; then pass "no bash 4+ syntax ($(wc -l < "$T/bash4.lst" | tr -d ' ') files)"; fi

if have zsh; then
	n=0 bad=0
	while IFS= read -r f; do
		n=$((n + 1))
		if ! zsh -n "$f" 2> "$T/err"; then
			bad=$((bad + 1))
			fail "zsh -n $f"
			indent "$T/err"
		fi
	done < "$T/zsh.lst"
	if [ "$bad" = 0 ]; then pass "zsh -n ($n files)"; fi
else
	skip "zsh -n: zsh not installed"
fi

if [ -s "$T/py.lst" ]; then
	py="${PY:-python3}"
	if have "$py"; then
		n=0 bad=0
		while IFS= read -r f; do
			n=$((n + 1))
			if ! "$py" -I -c '
import ast, sys
try:
    ast.parse(open(sys.argv[1], "rb").read(), sys.argv[1])
except SyntaxError as e:
    sys.exit("%s:%s: %s" % (e.filename, e.lineno, e.msg))
' "$f" 2> "$T/err"; then
				bad=$((bad + 1))
				fail "python syntax $f"
				indent "$T/err"
			fi
		done < "$T/py.lst"
		if [ "$bad" = 0 ]; then pass "python syntax ($n files)"; fi
	else
		skip "python syntax: python3 not installed"
	fi
fi

if [ -s "$T/swift.lst" ]; then
	if have swiftc; then
		n=0 bad=0
		while IFS= read -r f; do
			n=$((n + 1))
			cp "$f" "$T/check.swift"
			if ! swiftc -typecheck -module-cache-path "${SWIFT_MODULECACHE_PATH:-$T/swift-modules}" "$T/check.swift" 2> "$T/err"; then
				bad=$((bad + 1))
				fail "swift typecheck $f"
				indent "$T/err"
			fi
		done < "$T/swift.lst"
		if [ "$bad" = 0 ]; then pass "swift typecheck ($n files)"; fi
	else
		skip "swift syntax: install Apple's Command Line Tools"
	fi
fi

if have shellcheck; then
	n=0 bad=0
	while IFS= read -r f; do
		n=$((n + 1))
		if head -n 1 "$f" | grep -q '^#!'; then
			shellcheck -S warning -e SC1090,SC1091 "$f" > "$T/err" 2>&1
		else
			shellcheck -S warning -e SC1090,SC1091 -s bash "$f" > "$T/err" 2>&1
		fi
		if [ -s "$T/err" ]; then
			bad=$((bad + 1))
			fail "shellcheck $f"
			indent "$T/err"
		fi
	done < "$T/bash.lst"
	if [ "$bad" = 0 ]; then pass "shellcheck -S warning ($n files)"; fi
else
	skip "shellcheck: not installed (brew install shellcheck; CI runs it)"
fi

# The reviewer suite uses a fake Cursor CLI; it must never require network or login.
py="${PY:-python3}"
if [ ! -f tests/test_cross_review.py ]; then
	fail "cross-review: offline behavioral test suite missing"
elif ! have "$py"; then
	skip "cross-review tests: python3 not installed"
elif "$py" -B -I -m unittest discover -s tests -p 'test_cross_review.py' > "$T/err" 2>&1; then
	pass "cross-review offline behavioral tests"
else
	fail "cross-review offline behavioral tests"
	indent "$T/err"
fi

# =====================================================================
section "2. Data files"
# =====================================================================
pick '\.json(\.example)?$' > "$T/list"
if have jq; then
	n=0 bad=0
	while IFS= read -r f; do
		n=$((n + 1))
		if ! jq empty "$f" 2> "$T/err"; then
			bad=$((bad + 1))
			fail "json $f"
			indent "$T/err"
		fi
	done < "$T/list"
	if [ "$bad" = 0 ]; then pass "json valid ($n files)"; fi
else
	skip "json: jq not installed"
fi

pick '\.toml$' > "$T/list"
if [ -n "$PY" ]; then
	n=0 bad=0
	while IFS= read -r f; do
		n=$((n + 1))
		if ! "$PY" -I -c 'import sys, tomllib; tomllib.load(open(sys.argv[1], "rb"))' "$f" 2> "$T/err"; then
			bad=$((bad + 1))
			fail "toml $f"
			tail -n 1 "$T/err" | sed 's/^/        /'
		fi
	done < "$T/list"
	if [ "$bad" = 0 ]; then pass "toml valid ($n files)"; fi
else
	skip "toml: needs python3 >= 3.11 (tomllib)"
fi

# YAML: syntax only (no object construction), and the top level must be a mapping
pick '\.ya?ml(\.example)?$' > "$T/list"
if have ruby; then
	n=0 bad=0
	while IFS= read -r f; do
		n=$((n + 1))
		if ! ruby -ryaml -e '
			f = ARGV[0]
			begin
				d = Psych.parse(File.read(f), filename: f)
			rescue Psych::SyntaxError => e
				abort e.message
			end
			abort "#{f}: empty document" unless d
			abort "#{f}: top level is not a mapping" unless d.root.is_a?(Psych::Nodes::Mapping)
		' "$f" 2> "$T/err"; then
			bad=$((bad + 1))
			fail "yaml $f"
			indent "$T/err"
		fi
	done < "$T/list"
	if [ "$bad" = 0 ]; then pass "yaml valid ($n files)"; fi
else
	skip "yaml: ruby not installed"
fi

# plist templates: render __HOME__, lint, and reject ~ (launchd doesn't expand it)
pick '\.plist$' > "$T/list"
if [ ! -s "$T/list" ]; then
	skip "plist: none in repo"
elif have plutil; then
	n=0 bad=0
	while IFS= read -r f; do
		n=$((n + 1))
		sed "s|__HOME__|$T/home|g" "$f" > "$T/render.plist"
		if ! plutil -lint "$T/render.plist" > "$T/err" 2>&1; then
			bad=$((bad + 1))
			fail "plist $f"
			indent "$T/err"
		elif grep -n '<string>~' "$f" > "$T/err"; then
			bad=$((bad + 1))
			fail "plist $f uses ~ (launchd doesn't expand it; use __HOME__)"
			indent "$T/err"
		fi
	done < "$T/list"
	if [ "$bad" = 0 ]; then pass "plist templates lint clean ($n files)"; fi
else
	skip "plist: plutil not available (not macOS)"
fi

GHOSTTY=''
if have ghostty; then
	GHOSTTY="$(command -v ghostty)"
elif [ -x /Applications/Ghostty.app/Contents/MacOS/ghostty ]; then
	GHOSTTY=/Applications/Ghostty.app/Contents/MacOS/ghostty
fi
if [ ! -f .config/ghostty/config ]; then
	fail "ghostty: .config/ghostty/config missing"
elif [ -z "$GHOSTTY" ]; then
	skip "ghostty +validate-config: Ghostty not installed"
else
	mkdir -p "$T/ghome"
	n=0 bad=0
	cp .config/ghostty/config "$T/ghostty.conf"
	for h in "" .config/ghostty/hosts/*; do
		if [ -n "$h" ]; then
			[ -f "$h" ] || continue
			{ cat .config/ghostty/config; printf '\n'; cat "$h"; } > "$T/ghostty.conf"
		fi
		n=$((n + 1))
		if ! HOME="$T/ghome" "$GHOSTTY" +validate-config --config-file="$T/ghostty.conf" > "$T/err" 2>&1; then
			bad=$((bad + 1))
			fail "ghostty config${h:+ + $h}"
			indent "$T/err"
		fi
	done
	if [ "$bad" = 0 ]; then pass "ghostty +validate-config (base + $((n - 1)) host overlays)"; fi
fi

if [ ! -f .gitconfig ]; then
	fail ".gitconfig missing"
elif ! git config --file .gitconfig --list > "$T/gc" 2> "$T/err"; then
	fail ".gitconfig does not parse"
	indent "$T/err"
else
	bad=0
	if grep -iE '^(commit|tag)\.gpgsign=|^user\.signingkey=' "$T/gc" > "$T/err"; then
		bad=1
		fail ".gitconfig: signing settings belong in ~/.gitconfig.local, not the public repo"
		indent "$T/err"
	fi
	if grep -i '^includeif\.' "$T/gc" > "$T/err"; then
		bad=1
		fail ".gitconfig: includeIf blocks belong in ~/.gitconfig.local"
		indent "$T/err"
	fi
	if ! tail -n 1 "$T/gc" | grep -q '^include\.path=~/\.gitconfig\.local$'; then
		bad=1
		fail ".gitconfig must end with: [include] path = ~/.gitconfig.local"
	fi
	if [ "$bad" = 0 ]; then pass ".gitconfig parses; no signing/includeIf; ends with ~/.gitconfig.local include"; fi
fi

# =====================================================================
section "3. Fresh-HOME bootstrap"
# =====================================================================
# run_bootstrap HOME LOG ARGS... — clean environment, macOS /bin/bash, no stdin
run_bootstrap() {
	local home=$1 log=$2
	shift 2
	env -i HOME="$home" PATH="$PATH" TERM="${TERM:-dumb}" TMPDIR="${TMPDIR:-/tmp}" \
		USER="${USER:-$(id -un)}" LOGNAME="${LOGNAME:-$(id -un)}" SHELL="${SHELL:-/bin/zsh}" \
		"$BASH32" "$ROOT/bootstrap.sh" "$@" < /dev/null > "$log" 2>&1
}

# snapshot DIR OUT — dirs, files+symlinks with mode/mtime, and file checksums
snapshot() {
	(
		cd "$1" || exit 1
		find . -type d | LC_ALL=C sort
		find . \( -type f -o -type l \) -exec stat -f '%Sp %m %N' {} + | LC_ALL=C sort
		find . -type f -exec shasum -a 256 {} + | LC_ALL=C sort
	) > "$2"
}

# deploy_map — "repo-path<TAB>path-under-HOME" for every file bootstrap.sh must
# deploy (D1 contract). Ghostty is concatenated, so it is checked separately.
deploy_map() {
	local f d
	while IFS= read -r f; do
		case "$f" in
			*.example | *.pyc | */__pycache__/* | */.DS_Store) continue ;;
			.zshrc | .exports | .aliases | .functions | .gitconfig | .gitignore | .vimrc | .tmux.conf | .curlrc | .hushlogin | .inputrc) d=$f ;;
			.vim/* | bin/*) d=$f ;;
			.config/aerospace/aerospace.toml | .config/starship/starship.toml | .config/atuin/config.toml | .config/karabiner/karabiner.json | .config/finder/favorites.txt) d=$f ;;
			.config/espanso/config/*/* | .config/espanso/match/*/*) continue ;;
			.config/espanso/config/*.yml | .config/espanso/match/*.yml) d="Library/Application Support/espanso/${f#.config/espanso/}" ;;
			.config/sublime/User/*) d="Library/Application Support/Sublime Text/Packages/User/${f#.config/sublime/User/}" ;;
			.config/claude/settings.json | .config/claude/CLAUDE.md | .config/claude/AGENT-GRAPH.md) d=".claude/${f#.config/claude/}" ;;
			.config/claude/agents/* | .config/claude/commands/* | .config/claude/rules/* | .config/claude/skills/* | .config/claude/hooks/* | .config/claude/scripts/* | .config/claude/output-styles/*) d=".claude/${f#.config/claude/}" ;;
			.config/codex/skills/*) d=".codex/skills/${f#.config/codex/skills/}" ;;
			.config/mcp/*) d=".local/share/mcp/${f#.config/mcp/}" ;;
			*) continue ;;
		esac
		printf '%s\t%s\n' "$f" "$d"
	done < "$T/files"
}

REQUIRED='.zshrc
.exports
.aliases
.functions
.gitconfig
.gitignore
.vimrc
.tmux.conf
.curlrc
.hushlogin
.inputrc
bin/disk-clean
bin/finder-favorites
bin/cross-review
.config/finder/favorites.txt
.config/starship/starship.toml
.config/aerospace/aerospace.toml
.config/atuin/config.toml
.config/karabiner/karabiner.json
.claude/settings.json
.claude/CLAUDE.md
.claude/hooks/pre-bash-guard.sh
.codex/skills/cross-model-review/SKILL.md
Library/Application Support/com.mitchellh.ghostty/config
Library/Application Support/espanso/match'

FORBIDDEN='CLAUDE.md
README.md
SETUP.md
LICENSE-MIT.txt
Brewfile
.macos
bootstrap.sh
init
scripts
.github
launchagents
.git
.extra
.extra.example
.claude/settings.local.json
Library/LaunchAgents'

GHOSTTY_DST='Library/Application Support/com.mitchellh.ghostty/config'

bootstrap_checks() {
	local H1="$T/home1" H2="$T/home2" p f d rc n bad host
	mkdir -p "$H1" "$H2"

	# --- run 1 on an empty HOME ---
	if ! run_bootstrap "$H1" "$T/run1.log" -f; then
		fail "bootstrap.sh -f on an empty HOME exited non-zero (remaining bootstrap checks skipped)"
		tail -n 15 "$T/run1.log" | sed 's/^/        /'
		return
	fi
	pass "bootstrap.sh -f on an empty HOME exits 0"

	bad=0
	printf '%s\n' "$REQUIRED" > "$T/required"
	while IFS= read -r p; do
		if [ ! -e "$H1/$p" ]; then
			bad=$((bad + 1))
			fail "not deployed: ~/$p"
		fi
	done < "$T/required"
	for p in .claude/hooks/pre-bash-guard.sh bin/disk-clean; do
		if [ -e "$H1/$p" ] && [ ! -x "$H1/$p" ]; then
			bad=$((bad + 1))
			fail "deployed but not executable: ~/$p"
		fi
	done
	if [ "$bad" = 0 ]; then pass "all required files deployed"; fi

	bad=0
	printf '%s\n' "$FORBIDDEN" > "$T/forbidden"
	while IFS= read -r p; do
		if [ -e "$H1/$p" ] || [ -L "$H1/$p" ]; then
			bad=$((bad + 1))
			fail "must never be deployed: ~/$p"
		fi
	done < "$T/forbidden"
	(cd "$H1" && find . -name '*.example') > "$T/err"
	if [ -s "$T/err" ]; then
		bad=$((bad + 1))
		fail "templates (*.example) deployed:"
		indent "$T/err"
	fi
	if [ "$bad" = 0 ]; then pass "nothing from the never-deploy list reached HOME"; fi

	# --- every mapped file deployed byte-identical; nothing outside the map ---
	deploy_map > "$T/map"
	n=0 bad=0
	while IFS="$(printf '\t')" read -r f d; do
		n=$((n + 1))
		if [ ! -e "$H1/$d" ]; then
			bad=$((bad + 1))
			fail "not deployed: $f -> ~/$d"
		elif ! cmp -s "$f" "$H1/$d"; then
			bad=$((bad + 1))
			fail "deployed copy differs from repo: $f -> ~/$d"
		else
			case "$d" in
				bin/* | .claude/hooks/*.sh)
					if [ ! -x "$H1/$d" ]; then
						bad=$((bad + 1))
						fail "deployed but not executable: ~/$d"
					fi
					;;
			esac
		fi
	done < "$T/map"
	if [ "$bad" = 0 ]; then pass "deploy map: $n files byte-identical (bin/ and hooks executable)"; fi

	host="$(scutil --get LocalHostName 2> /dev/null)" || host="$(hostname -s 2> /dev/null)" || host=""
	if [ -f "$H1/$GHOSTTY_DST" ] && [ -f .config/ghostty/config ]; then
		cp .config/ghostty/config "$T/ghostty.want"
		if [ -n "$host" ] && [ -f ".config/ghostty/hosts/$host" ]; then
			{ printf '\n'; cat ".config/ghostty/hosts/$host"; } >> "$T/ghostty.want"
		fi
		grep -vxF -f "$H1/$GHOSTTY_DST" "$T/ghostty.want" | grep -v '^[[:space:]]*$' > "$T/err"
		if [ -s "$T/err" ]; then
			fail "ghostty config is missing lines from the repo config:"
			indent "$T/err"
		elif [ -n "$host" ] && [ -f ".config/ghostty/hosts/$host" ]; then
			pass "ghostty config = base + hosts/$host"
		else
			pass "ghostty config = base (no overlay for host '$host')"
		fi
	fi

	{ cut -f 2 "$T/map"; echo "$GHOSTTY_DST"; } | LC_ALL=C sort -u > "$T/expected"
	(cd "$H1" && find . \( -type f -o -type l \) ! -name .DS_Store | sed 's|^\./||' | LC_ALL=C sort) > "$T/actual"
	LC_ALL=C comm -23 "$T/actual" "$T/expected" > "$T/err"
	if [ -s "$T/err" ]; then
		fail "files deployed that are not in the deploy map:"
		indent "$T/err"
	else
		pass "no files deployed outside the deploy map"
	fi

	# --- hooks/commands referenced by settings.json exist ---
	if [ -f "$H1/.claude/settings.json" ] && have jq; then
		jq -r '[.. | objects | .command? | strings] | .[]' "$H1/.claude/settings.json" |
			grep -oE '(\$HOME|\$\{HOME\}|~)/[^[:space:]"]+' | LC_ALL=C sort -u > "$T/hookrefs"
		n=0 bad=0
		while IFS= read -r p; do
			n=$((n + 1))
			f="$H1/${p#*/}"
			if [ ! -f "$f" ]; then
				bad=$((bad + 1))
				fail "settings.json references a missing file: $p"
			fi
		done < "$T/hookrefs"
		if [ "$bad" = 0 ]; then pass "settings.json: all $n referenced hook/command paths exist"; fi
	fi

	# --- run 2: idempotent, no backups ---
	if [ -e "$H1/.dotfiles-backup" ]; then
		fail "first run on an empty HOME created ~/.dotfiles-backup (nothing should need backing up)"
	fi
	# Codex owns other skills and settings; bootstrap must leave them in place.
	mkdir -p "$H1/.codex/skills/local-only"
	printf '%s\n' 'local-only skill fixture' > "$H1/.codex/skills/local-only/SKILL.md"
	printf '%s\n' '# local-only settings fixture' > "$H1/.codex/config.toml"
	snapshot "$H1" "$T/snap1"
	sleep 1 # make any rewrite visible as an mtime change
	if ! run_bootstrap "$H1" "$T/run2.log" -f; then
		fail "second bootstrap.sh -f exited non-zero"
		tail -n 15 "$T/run2.log" | sed 's/^/        /'
	else
		snapshot "$H1" "$T/snap2"
		if [ -e "$H1/.dotfiles-backup" ]; then
			fail "second run created a backup dir (it should find every file unchanged)"
		elif ! cmp -s "$T/snap1" "$T/snap2"; then
			fail "second run changed HOME (not idempotent):"
			/usr/bin/diff "$T/snap1" "$T/snap2" > "$T/err"
			indent "$T/err"
		else
			pass "second run is a no-op (no file, mode, mtime or backup changes)"
			pass "existing local Codex skills and settings preserved"
		fi
	fi

	# --- dry run on an empty HOME, unknown flag ---
	run_bootstrap "$H2" "$T/dry.log" -n
	rc=$?
	if [ "$rc" != 0 ]; then
		fail "bootstrap.sh -n exited $rc"
		indent "$T/dry.log"
	elif [ -n "$(ls -A "$H2")" ]; then
		fail "bootstrap.sh -n wrote to an empty HOME:"
		ls -A "$H2" | sed 's/^/        /'
	elif ! grep -q 'zshrc' "$T/dry.log"; then
		fail "bootstrap.sh -n on an empty HOME did not report what it would install"
	else
		pass "bootstrap.sh -n reports changes and writes nothing"
	fi
	run_bootstrap "$H2" "$T/bogus.log" --bogus-flag
	rc=$?
	if [ "$rc" != 2 ]; then
		fail "bootstrap.sh --bogus-flag exited $rc (want usage + exit 2)"
	elif [ -n "$(ls -A "$H2")" ]; then
		fail "HOME not empty after -n / --bogus-flag (see dry-run result above)"
	else
		pass "unknown flag -> exit 2, nothing written"
	fi

	# --- drift: dry-run reports it untouched; real run backs it up; karabiner left alone ---
	printf '\n# drift\n' >> "$H1/.zshrc"
	if [ -f "$H1/.config/karabiner/karabiner.json" ]; then
		printf '\n' >> "$H1/.config/karabiner/karabiner.json"
	fi
	cp "$H1/.config/karabiner/karabiner.json" "$T/karabiner.drift" 2> /dev/null
	snapshot "$H1" "$T/snap3"
	if ! run_bootstrap "$H1" "$T/drift-dry.log" -n; then
		fail "bootstrap.sh -n with drift exited non-zero"
		indent "$T/drift-dry.log"
	else
		snapshot "$H1" "$T/snap4"
		if ! cmp -s "$T/snap3" "$T/snap4"; then
			fail "bootstrap.sh -n modified a populated HOME"
		elif ! grep 'zshrc' "$T/drift-dry.log" | grep -v unchanged > /dev/null; then
			fail "bootstrap.sh -n did not report the drifted ~/.zshrc"
		else
			pass "dry run on a drifted HOME reports drift and writes nothing"
		fi
	fi
	if ! run_bootstrap "$H1" "$T/drift.log" -f; then
		fail "bootstrap.sh -f with drift exited non-zero"
		indent "$T/drift.log"
	else
		find "$H1/.dotfiles-backup" -type f -name .zshrc -exec grep -l '^# drift$' {} + > "$T/bak" 2> /dev/null
		if ! cmp -s .zshrc "$H1/.zshrc"; then
			fail "drifted ~/.zshrc was not restored from the repo"
		elif [ ! -s "$T/bak" ]; then
			fail "drifted ~/.zshrc was replaced without a copy in ~/.dotfiles-backup/<timestamp>/.zshrc"
		else
			pass "drifted file restored; old copy kept in ~/.dotfiles-backup/<timestamp>/"
		fi
		if [ -f "$T/karabiner.drift" ]; then
			if cmp -s "$T/karabiner.drift" "$H1/.config/karabiner/karabiner.json"; then
				pass "existing karabiner.json left alone (copy only if absent)"
			else
				fail "bootstrap overwrote an existing karabiner.json (must copy only if absent)"
			fi
		fi
	fi

	# --- a fresh interactive zsh starts clean (fixed TERM: the caller's may be dumb or unset) ---
	if have zsh; then
		env -i HOME="$H1" PATH="$PATH" TERM=xterm-256color \
			zsh -i -c 'echo ok' < /dev/null > "$T/zsh.out" 2> "$T/zsh.err"
		if [ "$(cat "$T/zsh.out")" = ok ] && [ ! -s "$T/zsh.err" ]; then
			pass "zsh -i in the fresh HOME prints only 'ok', stderr empty"
		else
			fail "zsh -i in the fresh HOME is not clean (expected stdout 'ok' and empty stderr)"
			{ sed 's/^/stdout: /' "$T/zsh.out"; sed 's/^/stderr: /' "$T/zsh.err"; } > "$T/err"
			indent "$T/err"
		fi
	else
		skip "zsh -i: zsh not installed"
	fi
}

if [ "$(uname -s)" != Darwin ]; then
	skip "bootstrap: not macOS"
elif [ ! -f bootstrap.sh ]; then
	fail "bootstrap.sh missing"
else
	bootstrap_checks
fi

# =====================================================================
section "4. Public-repo guard"
# =====================================================================
# The work-identifier list lives outside this public repo (see --help); never print it.
WORK_RE="${DOTFILES_DENYLIST:-}"
SECRET_RE='AKIA[0-9A-Z]{16}|(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}'
SECRET_RE="$SECRET_RE"'|(^|[^A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35}'
SECRET_RE="$SECRET_RE"'|-----BEGIN [A-Z ]*PRIVATE KEY-----'
USERS_RE='/Users/[a-z][A-Za-z0-9._-]*'

tr '\n' '\0' < "$T/files" > "$T/scan0"

# report HITS LABEL MASK — one FAIL per file:line from `grep -Hno` output
# MASK: "" shows the match, 1 its first 4 chars, hide only its length
report() {
	awk -v mask="$3" '{
		i = index($0, ":"); f = substr($0, 1, i - 1); r = substr($0, i + 1)
		j = index(r, ":"); l = substr(r, 1, j - 1); m = substr(r, j + 1)
		if (mask == "hide") m = "(" length(m) " chars)"
		else if (mask) m = substr(m, 1, 4) "...(" length(m) " chars)"
		k = f ":" l
		if (!(k in seen)) { order[++n] = k; seen[k] = m }
		else if (index(seen[k], m) == 0) seen[k] = seen[k] ", " m
	} END { for (x = 1; x <= n; x++) print order[x] "  [" seen[order[x]] "]" }' "$1" > "$T/report"
	while IFS= read -r line; do
		fail "$2: $line"
	done < "$T/report"
}

nhits=0
scanned='secret shapes or /Users paths'
if [ -z "$WORK_RE" ]; then
	warn "work-identifier scan skipped (DOTFILES_DENYLIST unset; export it from ~/.extra)"
else
	# against one empty line: 1 = valid, 0 = matches everything (e.g. a stray |), 2 = invalid
	printf '\n' > "$T/empty"
	rc=0
	grep -qE -e "$WORK_RE" "$T/empty" > /dev/null 2>&1 || rc=$?
	if [ "$rc" != 1 ]; then
		fail "DOTFILES_DENYLIST is not a usable extended regex (invalid, or matches the empty string); work-identifier scan not run"
	else
		scanned="work identifiers, $scanned"
		grep -iE -e "$WORK_RE" "$T/files" > "$T/hits"
		while IFS= read -r p; do fail "work identifier in a path: $p"; done < "$T/hits"
		nhits=$(wc -l < "$T/hits")
		xargs -0 grep -HInoiE -e "$WORK_RE" < "$T/scan0" > "$T/hits" 2> /dev/null
		report "$T/hits" "work identifier" hide
		nhits=$((nhits + $(wc -l < "$T/hits")))
	fi
fi
xargs -0 grep -HInoE -e "$SECRET_RE" < "$T/scan0" > "$T/hits" 2> /dev/null
report "$T/hits" "secret-shaped string" 1
nhits=$((nhits + $(wc -l < "$T/hits")))
xargs -0 grep -HInoE -e "$USERS_RE" < "$T/scan0" > "$T/hits" 2> /dev/null
report "$T/hits" "hard-coded /Users path (use \$HOME)" ""
nhits=$((nhits + $(wc -l < "$T/hits")))
if [ "$nhits" = 0 ]; then
	pass "no $scanned in $(wc -l < "$T/files" | tr -d ' ') files"
fi

# =====================================================================
section "5. Brewfile"
# =====================================================================
# gh_api URL — HTTP status of a GitHub API GET (uses GITHUB_TOKEN when set, e.g. in CI)
gh_api() {
	if [ -n "${GITHUB_TOKEN:-}" ]; then
		curl -sS -o /dev/null -w '%{http_code}' --max-time 10 -H "Authorization: Bearer $GITHUB_TOKEN" "$1" 2> /dev/null
	else
		curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2> /dev/null
	fi
}

brew_checks() {
	local type name rest tap n bad unk code user repo id

	if have brew; then
		if HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_ANALYTICS=1 HOMEBREW_NO_ENV_HINTS=1 \
			brew bundle list --all --file="$ROOT/Brewfile" > /dev/null 2> "$T/err"; then
			pass "brew bundle parses the Brewfile"
		else
			fail "brew bundle cannot parse the Brewfile"
			indent "$T/err"
		fi
	elif have ruby; then
		if ruby -c Brewfile > /dev/null 2> "$T/err"; then
			pass "Brewfile is valid Ruby (brew not installed for a full parse)"
		else
			fail "Brewfile is not valid Ruby"
			indent "$T/err"
		fi
	else
		skip "Brewfile parse: neither brew nor ruby installed"
	fi

	sed -e 's/#.*$//' Brewfile |
		sed -nE 's/^[[:space:]]*(tap|brew|cask|mas|npm|vscode|uv|go|cargo)[[:space:]]+"([^"]+)"(.*)$/\1|\2|\3/p' > "$T/items"

	cut -d '|' -f 1,2 "$T/items" | LC_ALL=C sort | uniq -d > "$T/err"
	if [ -s "$T/err" ]; then
		fail "Brewfile has duplicate entries:"
		indent "$T/err"
	else
		pass "Brewfile: no duplicate entries ($(wc -l < "$T/items" | tr -d ' ') entries)"
	fi

	# Homebrew 7 refuses formulae/casks from non-official taps unless trusted
	grep '^tap|' "$T/items" | grep -E 'trusted:[[:space:]]*true' | cut -d '|' -f 2 |
		tr '[:upper:]' '[:lower:]' > "$T/trusted_taps"
	# taps with an explicit clone URL (e.g. SSH to a private repo) aren't looked up on GitHub
	grep '^tap|' "$T/items" | grep -E '^tap\|[^|]*\|[[:space:]]*,[[:space:]]*"' | cut -d '|' -f 2 |
		tr '[:upper:]' '[:lower:]' > "$T/url_taps"
	: > "$T/core"
	: > "$T/taps"
	n=0 bad=0
	while IFS='|' read -r type name rest; do
		case "$type" in
			tap)
				[ "${name%%/*}" = homebrew ] || echo "$name" >> "$T/taps"
				;;
			brew | cask)
				case "$name" in
					*/*/*)
						tap="$(printf '%s' "${name%/*}" | tr '[:upper:]' '[:lower:]')"
						if [ "${tap%%/*}" = homebrew ]; then
							echo "$type|${name##*/}" >> "$T/core"
						else
							n=$((n + 1))
							echo "${name%/*}" >> "$T/taps"
							case "$rest" in
								*trusted:*true*) ;;
								*)
									if ! grep -qxF "$tap" "$T/trusted_taps"; then
										bad=$((bad + 1))
										fail "$type \"$name\" needs trusted: true (Homebrew 7 refuses untrusted taps)"
									fi
									;;
							esac
						fi
						;;
					*) echo "$type|$name" >> "$T/core" ;;
				esac
				;;
			mas)
				id="$(printf '%s' "$rest" | sed -nE 's/.*id:[[:space:]]*([0-9]+).*/\1/p')"
				if [ -z "$id" ]; then
					bad=$((bad + 1))
					fail "mas \"$name\" has no numeric id:"
				fi
				;;
		esac
	done < "$T/items"
	if [ "$bad" = 0 ]; then pass "Brewfile: $n third-party tap items trusted; mas ids numeric"; fi

	if [ "$OFFLINE" = 1 ]; then
		skip "Brewfile names vs formulae.brew.sh / GitHub: --offline"
		return
	fi
	if ! have curl; then
		skip "Brewfile names: curl not installed"
		return
	fi
	code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 https://formulae.brew.sh/api/formula/git.json 2> /dev/null)"
	if [ "$code" != 200 ]; then
		skip "Brewfile names: formulae.brew.sh unreachable (HTTP ${code:-000})"
		return
	fi

	n=0 bad=0 unk=0
	while IFS='|' read -r type name; do
		kind=formula
		[ "$type" = cask ] && kind=cask
		code="$(curl -sS -o "$T/api.json" -w '%{http_code}' --max-time 10 "https://formulae.brew.sh/api/$kind/$name.json" 2> /dev/null)"
		case "$code" in
			200)
				n=$((n + 1))
				if ! have jq; then
					:
				elif jq -e '.disabled == true' "$T/api.json" > /dev/null; then
					bad=$((bad + 1))
					fail "$type \"$name\" is disabled upstream ($(jq -r '.disable_reason // "no reason given"' "$T/api.json"))"
				elif jq -e '.deprecated == true' "$T/api.json" > /dev/null; then
					warn "$type \"$name\" is deprecated ($(jq -r '[.deprecation_reason, .deprecation_date] | map(select(. != null)) | join(", ")' "$T/api.json"))"
				fi
				;;
			404)
				bad=$((bad + 1))
				fail "$type \"$name\" not found on formulae.brew.sh (typo, alias or renamed?)"
				;;
			*) unk=$((unk + 1)) ;;
		esac
	done < "$T/core"
	if [ "$unk" != 0 ]; then skip "Brewfile names: $unk lookups failed (network), not verified"; fi
	if [ "$bad" = 0 ]; then pass "Brewfile: $n core formulae/casks exist and are not disabled"; fi

	n=0 bad=0 unk=0
	tr '[:upper:]' '[:lower:]' < "$T/taps" | LC_ALL=C sort -u > "$T/taps.u"
	while IFS= read -r tap; do
		user="${tap%%/*}"
		repo="${tap#*/}"
		repo="${repo#homebrew-}"
		if grep -qxF "$tap" "$T/url_taps"; then
			skip "tap \"$tap\": explicit clone URL in Brewfile, GitHub lookup not applicable"
			continue
		fi
		code="$(gh_api "https://api.github.com/repos/$user/homebrew-$repo")"
		case "$code" in
			200) n=$((n + 1)) ;;
			404)
				# brew clones a URL-less tap over anonymous HTTPS, so missing and private both break it
				bad=$((bad + 1))
				fail "tap \"$tap\": github.com/$user/homebrew-$repo not publicly reachable (missing or private; give it an explicit clone URL if private)"
				;;
			*) unk=$((unk + 1)) ;;
		esac
	done < "$T/taps.u"
	if [ "$unk" != 0 ]; then skip "tap repos: $unk GitHub lookups failed (network or rate limit), not verified"; fi
	if [ "$bad" = 0 ] && [ "$n" != 0 ]; then pass "tap repos exist on GitHub ($n)"; fi
}

if [ -f Brewfile ]; then
	brew_checks
else
	fail "Brewfile missing"
fi

# =====================================================================
section "6. Repo files & git"
# =====================================================================
# Repo files SETUP.md tells you to copy or use; REQUIRED above only covers deployed paths
SETUP_FILES='.extra.example
.config/mcp/mcp.json.example
.config/mcp/requirements.txt
.config/espanso/match/private.yml.example
launchagents/com.kevincorvallis.disk-clean.plist
launchagents/com.kevincorvallis.obsidian-sync.plist'
printf '%s\n' "$SETUP_FILES" > "$T/setup_files"
n=0 bad=0
while IFS= read -r p; do
	n=$((n + 1))
	if [ ! -f "$p" ]; then
		bad=$((bad + 1))
		fail "SETUP.md refers to a repo file that is missing: $p"
	fi
done < "$T/setup_files"
if [ "$bad" = 0 ]; then pass "SETUP-referenced repo files exist ($n)"; fi

if [ "$IS_GIT" = 0 ]; then
	skip "git checks: not a git checkout"
else
	# A fresh clone only gets what is committed; CI checks out commits, so anything untracked fails there
	git -c core.quotePath=false ls-files -o --exclude-standard --directory --no-empty-directory > "$T/untracked"
	while IFS= read -r p; do
		if [ -n "${CI:-}" ]; then
			fail "untracked (a fresh clone won't have it): $p"
		else
			warn "untracked (a fresh clone won't have it; commit it or gitignore it): $p"
		fi
	done < "$T/untracked"
	if [ ! -s "$T/untracked" ]; then pass "no untracked, un-ignored files"; fi

	if git ls-files --error-unmatch .claude/settings.local.json > /dev/null 2>&1; then
		warn ".claude/settings.local.json is tracked; from a terminal run: git rm --cached .claude/settings.local.json"
	else
		pass ".claude/settings.local.json is not tracked"
	fi
	bad=0
	for p in .claude/settings.local.json .extra .gitconfig.local; do
		if ! git check-ignore -q --no-index "$p"; then
			bad=1
			warn "$p is not gitignored (a local overlay could be committed by accident)"
		fi
	done
	if [ "$bad" = 0 ]; then pass "local overlays (.extra, .gitconfig.local, settings.local.json) are gitignored"; fi
fi

# =====================================================================
printf '\n%s%d passed, %d failed, %d warnings, %d skipped%s\n' "$C_B" "$NPASS" "$NFAIL" "$NWARN" "$NSKIP" "$C_0"
[ "$NFAIL" = 0 ]
