# Global Context

- **Obsidian vault**: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Notes/`
- **Personal website**: `~/code/personal/website/` — klee.page, hosted on Vercel

# Git Commits

- Do NOT include `Co-Authored-By` lines in commit messages
- Keep commit messages short and concise — one line, under 50 characters when possible
- No multi-line descriptions unless explicitly asked
- On commit or push, update the relevant Obsidian note to reflect what was done

# PR Descriptions

- Open with one plain paragraph on the intended behavior, covering the 5Ws (what changes, who it affects, where in the system, when it applies, why) — a reviewer should get the intent in ~60 seconds
- Close with a prose paragraph on how the change was validated — only claims backed by evidence; say plainly what is red or unverified
- Plain prose, ≤4 short paragraphs, ~150–200 words (intent ≤80, validation ≤60): no headers, bold labels, checklists, or file paths; tickets as links; no AI-attribution footer

# AI CLI Tools

For personal projects (`~/code/personal/`), use the **AWS CLI** (e.g. `aws` commands).

# Trivial Transforms

- For quick text transformations (unwrap/reflow pasted terminal output, reformat, convert, extract), skip skill invocation and announcements entirely — reply with ONLY the transformed result, no preamble.

# Explaining Things

Two request shapes, two response shapes:

**Explaining a concept, system, or mechanism ("how/why does X work"):** layer it.

- One plain-sentence answer first, then where it fits / why it matters, then minimum mechanics — bold key terms, define jargon inline, one analogy if it earns its place (say where it breaks down)
- First pass ≤ ~200 words; hold edge cases, caveats, and alternatives until asked
- End with 2–3 named drill-down paths ("ask about: X · Y · Z") — never "let me know if you have questions"
- "In detail" or pulling a path unlocks full depth on that thread; deeper layers must never contradict the simple version

**Reporting status, audits, or known facts:** use that artifact's own shape and end at the bottom line or next action — the drill-down closer belongs to explanations only.

Full recipe: `~/.claude/skills/layered-explanations/SKILL.md`

# Claude/Agent Config Files

- Keep `.claude/` and `.agents/` files minimal and concise
- Don't overcomplicate — short, clear directives only

# Agent Graph

Custom agents form a small typed graph — canonical topology in `~/.claude/AGENT-GRAPH.md` (5 nodes: librarian, researcher, Code Reviewer, Accessibility Auditor, Reality Checker).

- When a subagent's report ends with `next: <agent> — <reason>`, treat it as a routing suggestion: follow it or say in one line why not.
- Never re-dispatch the agent that just reported.
- Pass the next agent only the context it needs, never the full transcript.
