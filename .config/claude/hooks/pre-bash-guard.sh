#!/bin/bash
# Claude Code PreToolUse hook — block destructive Bash command shapes.
# Reads PreToolUse(Bash) event JSON on stdin; exits 2 (with reason on stderr)
# to block the tool call. Exit 0 = allow.
#
# A tripwire for accidental destructive commands, not a sandbox. The command is
# split on ; & | ( ) ` and newlines, and each piece is judged by its first word
# (after VAR=x prefixes and sudo/env/command/exec/nohup/time). Quotes are not
# parsed: a separator inside a quoted string splits there too, which can block
# a commit message that quotes a destructive command. Commands hidden in
# variables, scripts or aliases are not seen. permissions.ask in settings.json
# prompts on similar patterns; this blocks them outright.
#
# Wired in ~/.claude/settings.json under "hooks.PreToolUse", matcher Bash.
# Source of truth: the dotfiles repo (.config/claude/hooks/); bootstrap.sh deploys it to ~/.claude/hooks/.
# Must run on macOS /bin/bash 3.2.
set -u

INPUT=$(cat)

# Extract the command. jq ships with macOS 15+; the grep fallback is best-effort.
if command -v jq >/dev/null; then
  CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)
else
  CMD=$(printf '%s' "$INPUT" | grep -oE '"command"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed -E 's/^"command"[[:space:]]*:[[:space:]]*"//; s/"$//')
fi

# Allow empty / unparseable commands to fall through; harness handles them.
[ -z "$CMD" ] && exit 0

block() {
  echo "BLOCKED by pre-bash-guard.sh: $1" >&2
  echo "To override: stop and ask the user for explicit confirmation, then have them run the command directly." >&2
  exit 2
}

# short_opt WORD LETTERS — WORD is a short-option cluster (-f, -xdf) holding any of LETTERS.
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

# 1. Destructive git operations. Arguments: the words after "git".
check_git() {
  local verb w del=0 force=0
  while [ $# -gt 0 ]; do # global options before the verb
    case "$1" in
      -C | -c | --git-dir | --work-tree | --namespace)
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
    push)
      for w in "$@"; do
        case "$w" in --force* | +*) block "git force-push requires explicit user authorization" ;; esac
        short_opt "$w" f && block "git force-push requires explicit user authorization"
      done
      ;;
    reset)
      for w in "$@"; do
        [ "$w" = --hard ] && block "git reset --hard is destructive without confirmation"
      done
      ;;
    clean)
      for w in "$@"; do
        if [ "$w" = --force ] || short_opt "$w" f; then
          block "git clean -f loses uncommitted work"
        fi
      done
      ;;
    branch)
      for w in "$@"; do
        case "$w" in
          --delete) del=1 ;;
          --force) force=1 ;;
        esac
        short_opt "$w" D && del=1 force=1
        short_opt "$w" d && del=1
        short_opt "$w" f && force=1
      done
      if [ "$del" = 1 ] && [ "$force" = 1 ]; then
        block "force-delete branch loses unmerged commits"
      fi
      ;;
  esac
}

# 2. rm -rf on absolute or home paths (relative paths like ./build are allowed).
check_rm() {
  local w r=0 f=0 abs=0 opts=1
  for w in "$@"; do
    if [ "$opts" = 1 ]; then
      case "$w" in
        --) opts=0; continue ;;
        --recursive) r=1; continue ;;
        --force) f=1; continue ;;
        --*) continue ;;
        -?*)
          short_opt "$w" rR && r=1
          short_opt "$w" f && f=1
          continue
          ;;
      esac
    fi
    # Quotes were stripped from the segment, so "$HOME/x" arrives as $HOME/x.
    # shellcheck disable=SC2016
    case "$w" in /* | '~'* | '$HOME'* | '${HOME}'*) abs=1 ;; esac
  done
  if [ "$r" = 1 ] && [ "$f" = 1 ] && [ "$abs" = 1 ]; then
    block "rm -rf on an absolute or home path requires explicit confirmation"
  fi
}

# 3. Shell-expansion bypass: `bash -c "..."`, `sh -c "..."` and `eval "..."`
#    evade the per-command allowlist.
check_shell() {
  local w
  for w in "$@"; do
    case "$w" in
      --*) ;;
      -*) short_opt "$w" c && block "bash -c / sh -c / eval bypasses the per-command allowlist" ;;
      *) return 0 ;;
    esac
  done
}

SEGS=$(printf '%s\n' "$CMD" | awk '
  { line = line $0 }
  /\\$/ { sub(/\\$/, "", line); next }
  { gsub(/[;&|()`]/, "\n", line); print line; line = "" }
  END { if (line != "") { gsub(/[;&|()`]/, "\n", line); print line } }')

# One segment per line. A for loop, not `while read <<EOF`: bash 3.2 writes here-docs to a
# temp file, and if that fails the loop would silently allow everything.
# Word splitting is on purpose below; noglob keeps `rm -rf /x*` from expanding here.
set -f
IFS='
'
for seg in $SEGS; do
  IFS=$' \t\n'
  seg=${seg//[\"\']/}
  # shellcheck disable=SC2086
  set -- $seg
  ex=0
  while [ $# -gt 0 ]; do # skip VAR=x prefixes and wrapper commands
    case "$1" in
      exec) ex=1; shift ;;
      [A-Za-z_]*=* | sudo | command | builtin | env | nohup | time | '{' | '!' | -*) shift ;;
      *) break ;;
    esac
  done
  [ $# -gt 0 ] || continue
  cmd=${1##*/}
  cmd=${cmd#\\}
  shift
  case "$cmd" in
    git) check_git "$@" ;;
    rm) check_rm "$@" ;;
    eval) block "bash -c / sh -c / eval bypasses the per-command allowlist" ;;
    sh | bash | zsh | dash | ksh)
      [ "$ex" = 1 ] && block "exec into a new shell bypasses the per-command allowlist"
      check_shell "$@"
      ;;
  esac
done

exit 0
