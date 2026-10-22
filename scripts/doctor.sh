#!/usr/bin/env bash
# scripts/doctor.sh — is THIS Mac fully set up? (check.sh asks the same of the repo.)
# Read-only: never writes to the repo or $HOME. Each gap prints as TODO, tagged
# with who can close it, and the command that closes it:
#   [you]    needs a password, a GUI prompt, a sign-in or a personal value
#   [agent]  the printed command can run as-is, by an agent or by you
# OPT lines are opt-in steps; they never fail the run. Exits 1 while any TODO is left.
# Run it outside an agent sandbox: the gh, ssh and Keychain checks fail falsely inside one.
# Must stay compatible with macOS /bin/bash 3.2 (it runs before Homebrew).
# The "~/" in messages is display text, not a path to expand.
# shellcheck disable=SC2088

set -uo pipefail

usage() {
	printf '%s\n' \
		'Usage: bash scripts/doctor.sh [--offline] [-h|--help]' \
		'' \
		'Checks this Mac against SETUP.md and prints PASS / TODO / OPT, in SETUP order.' \
		'Exits 0 when nothing is left to do, 1 otherwise.' \
		'' \
		'  --offline   skip the network checks (ssh to GitHub, gh repo list)' \
		'  -h, --help  show this help'
}

OFFLINE=0
while [ $# -gt 0 ]; do
	case "$1" in
		--offline) OFFLINE=1 ;;
		-h | --help) usage; exit 0 ;;
		*) echo "doctor.sh: unknown option: $1" >&2; usage >&2; exit 2 ;;
	esac
	shift
done

cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1
ROOT="$(pwd -P)"
T="$(mktemp -d "${TMPDIR:-/tmp}/dotfiles-doctor.XXXXXX")" || exit 1
trap 'rm -rf "$T"' EXIT
PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
export HOMEBREW_NO_AUTO_UPDATE=1

# ---------- output ----------
NPASS=0 NYOU=0 NAGENT=0 NOPT=0
if [ -t 1 ]; then
	C_G=$'\033[32m' C_R=$'\033[31m' C_Y=$'\033[33m' C_D=$'\033[2m' C_B=$'\033[1m' C_0=$'\033[0m'
else
	C_G='' C_R='' C_Y='' C_D='' C_B='' C_0=''
fi
pass() { NPASS=$((NPASS + 1)); printf '%sPASS%s  %s\n' "$C_G" "$C_0" "$*"; }
# todo you|agent WHAT FIX
todo() {
	if [ "$1" = you ]; then NYOU=$((NYOU + 1)); else NAGENT=$((NAGENT + 1)); fi
	printf '%sTODO%s  [%s] %s\n        %s-> %s%s\n' "$C_R" "$C_0" "$1" "$2" "$C_D" "$3" "$C_0"
}
# opt WHAT FIX
opt() { NOPT=$((NOPT + 1)); printf '%sOPT%s   %s\n        %s-> %s%s\n' "$C_Y" "$C_0" "$1" "$C_D" "$2" "$C_0"; }
section() { printf '\n%s== %s ==%s\n' "$C_B" "$*" "$C_0"; }
# indent FILE — show (the start of) a tool's output under a TODO line
indent() { head -n "${2:-10}" "$1" | sed 's/^/        /'; }
have() { command -v "$1" > /dev/null 2>&1; }

KEY="$HOME/.ssh/id_ed25519_personal"
MCP="$HOME/.local/share/mcp"

printf '%s%s%s  macOS %s  %s\n' "$C_B" "$(scutil --get ComputerName 2> /dev/null || hostname)" "$C_0" \
	"$(sw_vers -productVersion 2> /dev/null)" "$(sysctl -n machdep.cpu.brand_string 2> /dev/null)"

# =====================================================================
section "Base system (SETUP 1-3)"
if scutil --get HostName > /dev/null 2>&1; then
	pass "hostname set (LocalHostName $(scutil --get LocalHostName 2> /dev/null))"
else
	todo you "HostName is unset, so the network names this Mac" 'sudo scutil --set ComputerName "<Name>"; sudo scutil --set HostName <name>; sudo scutil --set LocalHostName <name>'
fi
if xcode-select -p > /dev/null 2>&1; then
	pass "Command Line Tools installed"
else
	todo you "Command Line Tools missing" "xcode-select --install (a GUI prompt)"
fi
if [ -x /opt/homebrew/bin/brew ]; then
	pass "Homebrew installed"
else
	# The $(...) is the command to show, not to run here.
	# shellcheck disable=SC2016
	todo you "Homebrew missing" '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" (asks for your password)'
fi
if have claude; then pass "claude CLI installed"; else todo you "claude CLI missing" "curl -fsSL https://claude.ai/install.sh | bash, then claude auth login"; fi

# =====================================================================
section "GitHub access (SETUP 4-5)"
if [ -f "$KEY" ]; then
	pass "personal SSH key exists"
else
	todo you "no personal SSH key" "ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_personal (you choose the passphrase)"
fi
if grep -qs 'github-personal' "$HOME/.ssh/config"; then
	pass "~/.ssh/config has the github.com / github-personal host block"
else
	todo agent "~/.ssh/config lacks the github host block" "append the Host block from SETUP step 5, then chmod 600 ~/.ssh/config"
fi
GH_USER=""
if [ "$OFFLINE" = 1 ]; then
	:
elif have gh && gh auth status > /dev/null 2>&1; then
	GH_USER="$(gh api user -q .login 2> /dev/null)"
	pass "gh is logged in as ${GH_USER:-?}"
else
	todo you "gh is not logged in" "gh auth login -p ssh --web (upload ~/.ssh/id_ed25519_personal.pub when asked)"
fi
if [ "$OFFLINE" = 0 ]; then
	# ssh -T always exits 1 on GitHub, so judge by the greeting, not the status.
	hi="$(ssh -o BatchMode=yes -o ConnectTimeout=8 -T git@github.com 2>&1)" || true
	case "$hi" in
		*"successfully authenticated"*) pass "ssh -T git@github.com authenticates as $(printf '%s' "$hi" | sed -nE 's/^Hi ([^!]+)!.*/\1/p')" ;;
		*) todo you "SSH to GitHub fails (host key not accepted yet, or key not on GitHub)" "ssh -T git@github.com and accept the host key; brew bundle needs this for the private tap" ;;
	esac
fi
origin="$(git -C "$ROOT" remote get-url origin 2> /dev/null)" || origin=""
case "$origin" in
	git@*) pass "dotfiles remote uses SSH" ;;
	*) todo agent "dotfiles remote is '${origin:-none}', not SSH (pushes will ask for a password)" "git -C \"$ROOT\" remote set-url origin git@github.com:kevincorvallis/dotfiles.git (after SSH works)" ;;
esac

# =====================================================================
section "Packages (SETUP 6)"
if [ -x /opt/homebrew/bin/brew ]; then
	if brew bundle check --file="$ROOT/Brewfile" --verbose --no-upgrade > "$T/bundle" 2>&1; then
		pass "every Brewfile entry is installed"
	else
		grep 'needs to be' "$T/bundle" | sed -E 's/^[^A-Za-z]*//; s/ needs to be.*//' > "$T/missing"
		fix="in a terminal tab the user can type into: cd \"$ROOT\" && brew bundle --file=Brewfile (pkg casks ask for their password; App Store apps need the App Store signed in)"
		if [ -s "$T/missing" ]; then
			todo agent "$(wc -l < "$T/missing" | tr -d ' ') Brewfile entries not installed" "$fix"
			indent "$T/missing" 12
		else
			# No "needs to be" lines: brew itself failed, so show why.
			todo agent "brew bundle check failed" "$fix"
			grep -v '^Warning' "$T/bundle" > "$T/missing"
			indent "$T/missing" 6
		fi
	fi
else
	todo you "brew bundle can't run without Homebrew" "install Homebrew first"
fi

# =====================================================================
section "Machine-local files (SETUP 7)"
if [ -f "$HOME/.extra" ]; then
	if [ "$(stat -f %Lp "$HOME/.extra")" = 600 ]; then pass "~/.extra exists, mode 600"; else todo agent "~/.extra is readable by others" "chmod 600 ~/.extra"; fi
	if grep -qE '^[[:space:]]*git config' "$HOME/.extra"; then
		todo agent "~/.extra runs git config (rewrites ~/.gitconfig every shell start)" "delete those lines; identities go in ~/.gitconfig.local"
	fi
	if grep -qE '^[[:space:]]*export [A-Za-z_]*(TOKEN|SECRET|KEY|PASSWORD)[A-Za-z_]*=["'\'']?[A-Za-z0-9_/+-]{12,}' "$HOME/.extra"; then
		todo you "~/.extra holds a literal secret" "store it with: security add-generic-password -a \"\$USER\" -s <name> -w, then read it back (template in .extra.example)"
	fi
else
	todo agent "no ~/.extra" "cp \"$ROOT/.extra.example\" ~/.extra && chmod 600 ~/.extra"
fi

# =====================================================================
section "Deploy (SETUP 8)"
if bash "$ROOT/bootstrap.sh" -n > "$T/drift" 2> /dev/null; then
	n="$(sed -nE 's/^Dry run: ([0-9]+) would change.*/\1/p' "$T/drift")"
	if [ "${n:-x}" = 0 ]; then
		pass "bootstrap -n: every deployed file matches the repo"
	else
		todo agent "bootstrap -n: ${n:-?} files differ from the repo" "cd \"$ROOT\" && bash bootstrap.sh -f (replaced files are backed up)"
		grep 'would-change' "$T/drift" > "$T/drift.list"
		indent "$T/drift.list"
	fi
else
	todo agent "bootstrap.sh -n failed" "cd \"$ROOT\" && bash bootstrap.sh -n"
fi
if have zsh; then
	TERM=xterm-256color zsh -i -c 'echo ok' < /dev/null > "$T/zsh.out" 2> "$T/zsh.err"
	if [ "$(cat "$T/zsh.out")" = ok ] && [ ! -s "$T/zsh.err" ]; then
		pass "a new interactive zsh starts with no output"
	else
		todo agent "zsh -i is not clean (startup prints something)" "find the cause in ~/.zshrc, ~/.extra or a tool init"
		{ sed 's/^/stdout: /' "$T/zsh.out"; sed 's/^/stderr: /' "$T/zsh.err"; } > "$T/zsh.all"
		indent "$T/zsh.all" 6
	fi
fi
email="$(git -C "$ROOT" config user.email)"
if [ -n "$email" ]; then
	pass "git identity here: $(git -C "$ROOT" config user.name) <$email>"
else
	todo agent "git has no user.email" "deploy ~/.gitconfig (step 8), or set one in ~/.gitconfig.local"
fi

# =====================================================================
section "macOS settings (SETUP 10)"
if [ "$(defaults read com.apple.finder _FXShowPosixPathInTitle 2> /dev/null)" = 1 ]; then
	pass ".macos has been applied"
else
	todo you ".macos not applied yet" "give Ghostty Full Disk Access, then from Ghostty: cd \"$ROOT\" && ./.macos (asks for sudo); log out after"
fi

# =====================================================================
section "Claude Code MCP servers (SETUP 11)"
if [ -x "$MCP/.venv-mcp/bin/python" ]; then
	pass "MCP venv exists"
else
	todo agent "MCP venv missing" "uv venv --python 3.13 $MCP/.venv-mcp && uv pip install --python $MCP/.venv-mcp/bin/python -r $MCP/requirements.txt"
fi
if [ -f "$HOME/.mcp.json" ]; then
	pass "~/.mcp.json exists"
else
	todo agent "no ~/.mcp.json" "cp \"$ROOT/.config/mcp/mcp.json.example\" ~/.mcp.json && chmod 600 ~/.mcp.json"
fi
if security find-generic-password -s gemini-api-key > /dev/null 2>&1; then
	pass "gemini-api-key is in the Keychain"
else
	todo you "no gemini-api-key in the Keychain (the gemini MCP needs it)" "security add-generic-password -a \"\$USER\" -s gemini-api-key -w (prompts for the key)"
fi

# =====================================================================
section "Your values (SETUP 12)"
if [ -f "$HOME/Library/Application Support/espanso/match/private.yml" ]; then
	pass "espanso private.yml exists"
else
	todo you "no espanso private.yml (your phone/address snippets)" "copy .config/espanso/match/private.yml.example there and fill in real values"
fi

# =====================================================================
section "Your repos and builds (SETUP 14)"
if [ -n "$GH_USER" ]; then
	if gh repo list "$GH_USER" --source --no-archived --limit 500 --json name -q '.[].name' > "$T/repos" 2> /dev/null; then
		# Match names case-insensitively: GitHub has Emblem, the clone is emblem.
		for d in "$HOME"/code/*/*; do
			[ -d "$d" ] && basename "$d"
		done > "$T/local"
		grep -vixF -f "$T/local" "$T/repos" > "$T/notcloned"
		n="$(wc -l < "$T/notcloned" | tr -d ' ')"
		if [ "$n" = 0 ]; then
			pass "every non-archived GitHub repo of $GH_USER is cloned under ~/code"
		else
			opt "$n GitHub repos of $GH_USER are not cloned under ~/code: $(paste -sd' ' "$T/notcloned")" "clone the ones you want: gh repo clone <name> ~/code/personal/<name>"
		fi
	fi
fi
if [ -d /Applications/VoiceInk.app ] || [ -d "$HOME/Applications/VoiceInk.app" ]; then
	pass "VoiceInk (your build) is installed"
else
	todo agent "VoiceInk not installed (your own build, not a cask)" "gh repo clone kevincorvallis/VoiceInk ~/code/personal/VoiceInk, build it per its Makefile (needs Xcode), move the app to /Applications"
fi

# =====================================================================
section "Opt-in steps and sign-ins (SETUP 15-16)"
uid="$(id -u)"
for p in "$ROOT"/launchagents/*.plist; do
	[ -f "$p" ] || continue
	name="$(basename "$p")"
	label="${name%.plist}"
	if [ ! -f "$HOME/Library/LaunchAgents/$name" ]; then
		opt "LaunchAgent $label not installed" "read SETUP step 15 first, then: bash bootstrap.sh -f --launchagents"
	elif launchctl print "gui/$uid/$label" > /dev/null 2>&1; then
		pass "LaunchAgent $label loaded"
	else
		todo agent "LaunchAgent $label installed but not loaded" "launchctl bootstrap gui/$uid ~/Library/LaunchAgents/$name"
	fi
done
if have codex; then
	if codex login status > /dev/null 2>&1; then pass "codex is logged in"; else todo you "codex is not logged in" "codex login"; fi
fi
if [ ! -f "$HOME/.aws/credentials" ] && have aws; then
	opt "aws has no credentials" "aws configure with a new access key for this Mac"
fi

# ---------- summary ----------
todos=$((NYOU + NAGENT))
printf '\n%s%d passed, %d to do (%d for you, %d for an agent), %d optional%s\n' \
	"$C_B" "$NPASS" "$todos" "$NYOU" "$NAGENT" "$NOPT" "$C_0"
if [ "$todos" = 0 ]; then
	echo "This Mac is set up. Finish with the manual checks at the end of SETUP.md."
	exit 0
fi
exit 1
