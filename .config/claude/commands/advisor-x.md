---
description: Cross-vendor advisor — forwards THIS session's transcript to Gemini + GPT (gpt-6-astra, auto-fallback gpt-5.6-sol) for a second opinion, then rules on the divergence
---

Cross-vendor sibling of the built-in `advisor` tool. Where `advisor` forwards the transcript to a stronger *Anthropic* model (`advisorModel` in `~/.claude/settings.json` — Anthropic-only, no vendor hook), this forwards the same transcript to **Gemini** and **GPT (`gpt-6-astra`, wrapper default; falls back to `gpt-5.6-sol` with a `[fallback: ...]` prefix while this ChatGPT account is gated)** in parallel.

**Boundary vs `/thanos`**: `/thanos` sends a prompt *you write*. `/advisor-x` sends the *whole session* — use it when the useful context is what already happened (the tool calls, the dead ends, the numbers you measured), not something you can restate in a paragraph. If you can state the question standalone in ≲500 tokens, use `/thanos` — it's much cheaper.

## Arguments

`$ARGUMENTS` is the optional focus question ("am I about to ship a bug?", "is my read on the tradeoff right?"). If empty, default the question to: *"Review this session. What is the biggest error, unverified assumption, or missed alternative? Be specific and cite the turn."*

Optional first-word flags:
- `full` — raise `--turns` to 200 and `--max-chars` to 250000 (long sessions; costs more).
- `gemini` / `gpt` — single vendor only.

## Step 1 — build the digest

```bash
python3 ~/.claude/scripts/session-digest.py --cwd "$PWD" > "${TMPDIR:-/tmp}/advisor-x-digest.txt"
wc -c "${TMPDIR:-/tmp}/advisor-x-digest.txt"
```

The script reads this session's `.jsonl` from `~/.claude/projects/<slugified-cwd>/`, located via `CLAUDE_CODE_SESSION_ID` (it refuses to guess by mtime unless given `--allow-guess`). It drops thinking blocks, clips each tool call/result to 1500 chars, keeps the last 80 messages, and scrubs known secret patterns (GitHub/Slack/Google/OpenAI tokens, private keys, `key=`/`password=` assignments).

**Read the digest before sending it.** The scrubber is pattern-based, not exhaustive. This session's contents are about to leave the machine to two third-party APIs.

## Step 2 — sealed take (before dispatch)

Write your own answer to the focus question in 2-5 bullets in your reasoning, *before* reading any vendor response. Prevents anchoring — the whole value of a second opinion is that it's independent of yours.

## Step 3 — parallel ask

Send **both calls in one message** so they run concurrently. Same prompt to each:

- `mcp__gemini__ask_gemini` — `model: "gemini-3.8-flash"` (newest tier; this is a long prompt), `max_output_tokens: 8192`
- `mcp__codex__ask_gpt` — omit `model` (defaults to `gpt-6-astra`, auto-fallback `gpt-5.6-sol`; note the answering model if a `[fallback: ...]` prefix appears)

Prompt shape:

```
You are reviewing another AI agent's working session. Below is the full
transcript: the user's requests, the agent's tool calls, and the results.

<FOCUS QUESTION>

Answer in <=10 bullets. Be concrete — cite the specific turn, command, or
number you're reacting to. Flag uncertainty explicitly rather than hedging
everything. Priority order:
1. Factual errors or claims the transcript does not actually support.
2. Unverified assumptions the agent is building on.
3. Alternatives the agent never considered.
Do not summarize the session back to me. Do not praise it.

--- TRANSCRIPT ---
<contents of ${TMPDIR:-/tmp}/advisor-x-digest.txt>
```

Paste the digest **inline** — both MCP tools are stateless and cannot read files.

## Step 4 — rule

- **Consensus**: state it once. Treat 3-way agreement as ~2 independent votes, not 3 — correlated training data means correlated blind spots. If the consensus rests on a checkable fact about *this* repo/session, check the file before presenting it.
- **Divergence**: verify against actual files/output before ruling. One line per point.
- **Unique to one vendor**: keep if you can verify it; else mark unverified. A point only one model raised is often the valuable one.
- If a vendor errors after one retry, continue with the other and mark the result **DEGRADED**.

Output: the ruling first, then a `Point | Gemini | GPT | Claude ruling` table only if they disagreed. Inline only — no files written, nothing posted to Slack/Jira.

## Cleanup

```bash
rm -f "${TMPDIR:-/tmp}/advisor-x-digest.txt"
```
