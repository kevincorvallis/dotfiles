Summon both external vendors on a **question**: send the prompt to Gemini and GPT in parallel (one round, inline, no subagents), then synthesize with Claude's own take. Depends only on the global `gemini` + `codex` MCP servers.

**Boundary vs `/gauntlet`**: `/thanos` is for questions where a wrong answer is recoverable — second opinions, tradeoffs, "am I missing anything?", naming, library/strategy choices, small snippets (≲500 tokens of context). It NEVER escalates: no crossfire, no subagents, no follow-up rounds. If there's a concrete artifact whose defects are costly (diff, design, migration, prod change), stop and suggest `/gauntlet` instead.

## Panel

Gemini via `mcp__gemini__ask_gemini` (`latest` = `gemini-3.8-flash` default, `smartest` = `gemini-3.8-flash` + "reason exhaustively", `fast` = `gemini-2.5-flash`), GPT via `mcp__codex__ask_gpt` (`latest`/`smartest` = `gpt-6-astra` wrapper default — omit `model`; it auto-falls back to `gpt-5.6-sol` with a `[fallback: ...]` prefix until this ChatGPT account is enabled for Astra; `fast` = `gpt-5.5` explicit). Tier from first argument (`/thanos smartest <prompt>`).

`/thanos wide <prompt>`: still ONE round, but four parallel calls — each vendor asked twice with **different framings** (e.g. "strongest answer" vs "steelman the opposite / what everyone gets wrong about this"; never two identical prompts). Use for genuinely open questions where the first framing might tunnel. In synthesis, the two responses from one vendor are NOT independent votes — group by framing, not by count. Degradation is per-call: one failed framing means partial coverage noted, not a discarded vendor.

## Rules

- Both tools are stateless — embed FULL context in each prompt (paste file contents/error text, never a bare path or PR number).
- Send both calls in ONE message so they run in parallel.
- Ask each vendor for a **direct answer in ≤10 bullets/short paragraphs, uncertainty flagged** — no essays. Verbosity is the main token leak here.
- Never send secrets/tokens or internal diagram source to external models.
- If one vendor errors (after one retry), continue with the other, mark **DEGRADED**.
- Either tool may return a `[fallback: ...]` prefix (Gemini tier fallback; GPT while `gpt-6-astra` is still gated) — note which model actually answered.

## Context pass (cheap, conditional)

If the question touches ongoing work and the cwd has notes or agent memory (e.g. design docs, gotchas notes, the memory index), do ONE quick lookup and fold the relevant facts into the vendor prompt — a sentence or two of real context beats a confidently wrong consensus. Skip entirely for general/tech questions with no local angle. Scrub credentials, IDs, and internal URLs before sending externally.

## Round 0 — sealed take

Write your OWN answer (2-5 bullets) in your reasoning before dispatching. Prevents anchoring.

## Round 1 — parallel ask

Same prompt to both vendors, straight framing (not adversarial): best direct answer with brief reasoning. If the question presents options ("A or B?"), instruct both vendors to first say whether the option set is right — missing option D, false separation, negotiable requirement, faulty premise — before choosing.

## Round 2 — synthesis (Claude)

- **Consensus** — state it once as the answer. But treat 3-way agreement as ~2 independent votes, not 3: same training data, correlated blind spots. If the consensus rests on a checkable fact that would be costly if stale (an API still exists, a config option, a version behavior), spend one quick doc/file check on it before presenting — correlated staleness is the known failure mode of agreement.
- **Divergence** — verify checkable claims against actual files/docs before ruling; then rule with one line per point.
- **Unique** — one source only: keep if verified, else mark unverified. Novel points deserve attention, not discounting.

Output: consensus answer first, then a short divergence table (`Point | Gemini | GPT | Claude ruling`) only if there were disagreements. Inline only — no files, no Slack/Jira posts unless explicitly asked.
