# Global Context

- **Obsidian vault**: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Notes/`
- **Personal website**: `~/Downloads/Projects/website/` — klee.page, hosted on AWS Amplify

# Git Commits

- Do NOT include `Co-Authored-By` lines in commit messages
- Keep commit messages short and concise — one line, under 50 characters when possible
- No multi-line descriptions unless explicitly asked
- On commit or push, update the relevant Obsidian note to reflect what was done

# AI CLI Tools

- **Personal projects** (`~/code/personal/`): Use **AWS CLI** (e.g. `aws` commands)
- **Work projects** (`~/code/paramount/`): Use **Gemini CLI** (e.g. `gemini` commands)

# Claude/Agent Config Files

- Keep `.claude/` and `.agents/` files minimal and concise
- Don't overcomplicate — short, clear directives only

# Agent Graph

Custom agents form a small typed graph — canonical topology in `~/.claude/AGENT-GRAPH.md` (7 nodes: vault-navigator, shortform-infra, librarian, researcher, Code Reviewer, Accessibility Auditor, Reality Checker; old pack archived at `~/.claude/agents-archive-2026-07-03/`).

- When a subagent's report ends with `next: <agent> — <reason>`, treat it as a routing suggestion: follow it or say in one line why not.
- Max one utility hop (→ vault-navigator) per task; never re-dispatch the agent that just reported.
- Pass the next agent only the context it needs, never the full transcript.
