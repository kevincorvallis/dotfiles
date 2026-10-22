#!/bin/bash
# Claude Code PreToolUse hook — block `git add` / `git commit` of secrets-prone files.
# Wired in ~/.claude/settings.json under "hooks.PreToolUse", matcher Bash.
# Source of truth: the dotfiles repo (.config/claude/hooks/); bootstrap.sh deploys it to ~/.claude/hooks/.
#
# Reads the PreToolUse event JSON on stdin (https://code.claude.com/docs/en/hooks) and exits 2
# with a reason on stderr if any disallowed file path is in the stage operation.
#
# Specifically blocks:
#   - **/.claude/settings.local.json (personal local overrides; should never be committed)
#   - **/.env, **/.env.* (env files with credentials; .env.example/.sample/.template are allowed)
#   - **/.obsidian/workspace.json (Obsidian per-machine UI state — agents sometimes stage it accidentally)
#   - **/*credentials.json, **/service-account*.json (cloud service-account keys)
#   - **/*token*.txt, **/*secret*.txt (catch-all for adhoc credential dumps)
#   - **/*.pem, **/*.p8, **/*.p12, **/id_rsa, **/id_ecdsa, **/id_ed25519 (private keys)
#
# Files are resolved through git, so `git add .`, `git add -A`, directories and `-C <dir>` are
# covered: for `git add` it checks the literal arguments plus what `git ls-files` says the
# pathspecs would stage; for `git commit` it checks the index (plus modified files with -a).
# The command is split on ; & | ( ) ` and newlines, and `cd <dir>` pieces are followed.
# Quotes are not parsed. If git or the directory is unavailable it falls back to the literal
# arguments. Must run on macOS /bin/bash 3.2.
#
# pre-bash-guard.sh handles destructive command shapes; this complements it by inspecting the
# file paths being staged.
#
# Exit codes:
#   0 = allow
#   2 = block (the message on stderr is shown to Claude per docs)

set -u

# Read the JSON-encoded tool input from stdin
INPUT=$(cat)

# Extract the bash command and the session cwd. jq ships with macOS 15+; the grep fallback is best-effort.
if command -v jq >/dev/null; then
  COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)
  DIR=$(printf '%s' "$INPUT" | jq -r '.cwd // ""' 2>/dev/null)
else
  COMMAND=$(printf '%s' "$INPUT" | grep -oE '"command"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed -E 's/^"command"[[:space:]]*:[[:space:]]*"//; s/"$//')
  DIR=""
fi

# Only inspect commands that could be a git add / git commit
case "$COMMAND" in
  *git*) ;;
  *) exit 0 ;;
esac
case "$COMMAND" in
  *add* | *stage* | *commit*) ;;
  *) exit 0 ;;
esac
if [ -z "$DIR" ] || [ ! -d "$DIR" ]; then
  DIR=$PWD
fi

# Patterns that should never be staged, matched against one repo path per line
BLOCKED_PATTERNS=(
  '(^|/)\.claude/settings\.local\.json$'
  '(^|/)\.env(\.[^/]*)?$'
  '(^|/)\.obsidian/workspace\.json$'
  'credentials\.json$'
  'service-account[^/]*\.json$'
  'token[^/]*\.txt$'
  'secret[^/]*\.txt$'
  '\.(pem|p8|p12)$'
  '(^|/)id_(rsa|ecdsa|ed25519)$'
)
ALLOWED_TEMPLATES='(^|/)\.env\.(example|sample|template)$'

# short_opt WORD LETTERS — WORD is a short-option cluster (-A, -Av) holding any of LETTERS.
short_opt() {
  case "$1" in
    -- | --* | -) return 1 ;;
    -*)
      # $2 is a set of letters for the bracket expression, so it stays unquoted.
      # shellcheck disable=SC2254
      case "${1#-}" in *[$2]*) return 0 ;; esac
      ;;
  esac
  return 1
}

# in_dir BASE PATH — PATH resolved against BASE (absolute, ~ and relative)
in_dir() {
  # '~/' matches a literal "~/" from the command line, expanded by hand.
  # shellcheck disable=SC2088
  case "$2" in
    /*) printf '%s' "$2" ;;
    '~') printf '%s' "$HOME" ;;
    '~/'*) printf '%s/%s' "$HOME" "${2#'~/'}" ;;
    *) printf '%s/%s' "$1" "$2" ;;
  esac
}

STAGED_FILES=""
add_files() { STAGED_FILES=$(printf '%s\n%s' "$STAGED_FILES" "$1"); }

# check_git WORDS... — the words after "git"; adds the files it would stage to STAGED_FILES.
check_git() {
  local gdir=$DIR verb w paths="" all=0 upd=0 force=0 commit_all=0 opts=1 mode ex
  while [ $# -gt 0 ]; do # global options before the verb
    case "$1" in
      -C)
        [ $# -ge 2 ] || return 0
        gdir=$(in_dir "$gdir" "$2")
        shift 2
        ;;
      -c | --git-dir | --work-tree | --namespace)
        [ $# -ge 2 ] || return 0
        shift 2
        ;;
      -*) shift ;;
      *) break ;;
    esac
  done
  [ $# -gt 0 ] || return 0
  verb=$1
  shift
  case "$verb" in
    add | stage)
      for w in "$@"; do
        if [ "$opts" = 1 ]; then
          case "$w" in
            --) opts=0; continue ;;
            --all) all=1; continue ;;
            --update) upd=1; continue ;;
            --force) force=1; continue ;;
            -?*)
              short_opt "$w" A && all=1
              short_opt "$w" u && upd=1
              short_opt "$w" f && force=1
              continue
              ;;
          esac
        fi
        paths="$paths $w"
      done
      # Literal arguments first: they still count when git can't resolve them.
      set -f
      # shellcheck disable=SC2086
      add_files "$(printf '%s\n' $paths)"
      set +f
      if [ -z "$paths" ]; then
        # -A / -u with no pathspec cover the whole tree; a bare `git add` stages nothing.
        { [ "$all" = 1 ] || [ "$upd" = 1 ]; } || return 0
        paths=":/"
      fi
      mode=-mo # modified + untracked; -u alone means tracked files only
      if [ "$upd" = 1 ] && [ "$all" = 0 ]; then mode=-m; fi
      ex=--exclude-standard # -f stages ignored files too
      if [ "$force" = 1 ]; then ex=""; fi
      set -f
      # shellcheck disable=SC2086
      add_files "$(git -C "$gdir" ls-files $mode $ex --full-name -- $paths 2>/dev/null)"
      set +f
      ;;
    commit)
      for w in "$@"; do
        case "$w" in
          --all) commit_all=1 ;;
          -?*) short_opt "$w" a && commit_all=1 ;;
        esac
      done
      add_files "$(git -C "$gdir" diff --cached --name-only 2>/dev/null)"
      if [ "$commit_all" = 1 ]; then
        add_files "$(git -C "$gdir" ls-files -m --full-name 2>/dev/null)"
      fi
      ;;
  esac
}

SEGS=$(printf '%s\n' "$COMMAND" | awk '
  { line = line $0 }
  /\\$/ { sub(/\\$/, "", line); next }
  { gsub(/[;&|()`]/, "\n", line); print line; line = "" }
  END { if (line != "") { gsub(/[;&|()`]/, "\n", line); print line } }')

# One segment per line. A for loop, not `while read <<EOF`: bash 3.2 writes here-docs to a
# temp file, and if that fails the loop would silently allow everything.
IFS='
'
set -f
for seg in $SEGS; do
  IFS=$' \t\n'
  set -f # check_git turns noglob off again
  seg=${seg//[\"\']/}
  # shellcheck disable=SC2086
  set -- $seg
  while [ $# -gt 0 ]; do # skip VAR=x prefixes and wrapper commands
    case "$1" in
      [A-Za-z_]*=* | sudo | command | builtin | env | nohup | time | exec | '{' | '!' | -*) shift ;;
      *) break ;;
    esac
  done
  [ $# -gt 0 ] || continue
  cmd=${1##*/}
  cmd=${cmd#\\}
  shift
  case "$cmd" in
    cd) DIR=$(in_dir "$DIR" "${1:-$HOME}") ;;
    git) check_git "$@" ;;
  esac
done
IFS=$' \t\n'
set +f

STAGED_FILES=$(printf '%s\n' "$STAGED_FILES" | grep -vE "$ALLOWED_TEMPLATES" | grep -v '^$' | LC_ALL=C sort -u)

# Match patterns
VIOLATIONS=""
for pat in "${BLOCKED_PATTERNS[@]}"; do
  hit=$(printf '%s\n' "$STAGED_FILES" | grep -E "$pat" | tr '\n' ' ' || true)
  if [ -n "$hit" ]; then
    VIOLATIONS="$VIOLATIONS\n  - pattern '$pat' matched: $hit"
  fi
done

if [ -n "$VIOLATIONS" ]; then
  printf 'BLOCKED: about to stage / commit a secret-prone file.\n' >&2
  printf 'Violations:%b\n' "$VIOLATIONS" >&2
  printf 'If this is intentional (e.g., a redacted example), surface it to the user and let them stage it manually.\n' >&2
  exit 2
fi

exit 0
