# Global Context

- **Obsidian vault**: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Notes/`
- **Personal website**: `~/code/personal/website/` — klee.page, hosted on Vercel

# Git Commits

- Do NOT include `Co-Authored-By` lines in commit messages
- Keep commit messages short and concise — one line, under 50 characters when possible
- No multi-line descriptions unless explicitly asked
- On commit or push, update the relevant Obsidian note to reflect what was done

<!-- include: .config/agents/writing.md -->

<!-- include: .config/agents/pr-descriptions.md -->

# AI CLI Tools

For personal projects (`~/code/personal/`), use the **AWS CLI** (e.g. `aws` commands).

# Codex/Agent Config Files

- Keep `.Codex/` and `.agents/` files minimal and concise
- Don't overcomplicate — short, clear directives only
- `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md` and `~/.cursor/skills/` are built from `~/code/personal/dotfiles` (`.config/`). Edit the repo copy, not the copy in `~`. Machine-only lines go in `~/.claude/CLAUDE.local.md` or `~/.codex/AGENTS.local.md`

# Execution, Style, and Verification

- Complete authorized implementation or fixes and relevant verification; do not stop at a proposed plan. Continue authorized read-only work, local worktrees, branch edits, and appropriate tests without repeated confirmation.
- Make reasonable assumptions for routine, reversible decisions. Ask focused questions when missing information materially affects correctness, scope, or authorization.
- Finish authorized preparation before requesting approval and present a concrete, reviewable result. Respect required approval gates; ask before destructive, irreversible, or otherwise unauthorized actions.
- Explicit user instructions override conflicting skill guidelines, subject to higher-priority instructions and actual permission boundaries.
- If a skill causes a pause or deviation, name and link its exact file, quote the rule, distinguish requirements from interpretation, and continue unaffected authorized work.
- Lead with the result. Use plain language, active voice, concise paragraphs, and lists when useful. Avoid repetitive transitions, boilerplate hypothetical warnings, and stock phrases such as "it's worth noting", "delve", "leverage", and "Bottom line". Explain concrete blockers or material risks.
- Match verification to scope and impact. Complete required checks; expand or repeat testing only for changes, failures, or concrete unresolved concerns. Report what changed, what was verified, and remaining uncertainty.

# OpenAI Model Migrations

- Use the OpenAI Docs skill and current official guidance for requested migrations (e.g. `$openai-docs migrate this project to GPT-6 Astra`). Preserve the requested model, inspect the project, apply relevant model and prompt changes, and flag broader API or architecture work.
- Astra migration reminders, verified 2026-09-27: tool calling requires Responses; remove unsupported `temperature`, `top_p`, and `top_logprobs`, plus endpoint-specific log-probability options. Recheck compatibility at migration time: https://developers.openai.com/api/docs/guides/latest-model .
