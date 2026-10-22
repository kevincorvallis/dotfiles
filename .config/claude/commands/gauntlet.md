Adversarial cross-vendor review of a concrete **artifact** (diff, design, plan, claim, ticket) with staged escalation: blind structured attacks → quote-gate → delta-only crossfire (only if warranted) → Claude verifies and judges. Requires the global `gemini` + `codex` MCP servers; everything else (local notes/memory context, subagents) is used when available, skipped when not.

**Boundary vs `/thanos`**: `/gauntlet` is for artifacts where missing a defect is materially costly (prod behavior, money, auth, data integrity, irreversible changes, public APIs) and findings must be verified against source. No artifact, or a recoverable question → use `/thanos`. Style-only, docs-only, or boilerplate reviews → don't use either at heavy tier. Calibration (benchmarked 2026-07-07 on 2 real PRs vs runtime-verified ground truth): a solo Claude review + runtime verification matches the panel's recall at ~1/4 the tokens — the panel buys tail coverage and hallucination-gating, so reserve it for genuine blast radius, and never treat any mode as a substitute for the empirical check.

## Panel

| Tier | Gemini (`mcp__gemini__ask_gemini`) | GPT (`mcp__codex__ask_gpt`) |
|---|---|---|
| `latest` (default) | `gemini-3.8-flash`, all rounds | `gpt-6-astra` (wrapper default — omit `model`; auto-falls back to `gpt-5.6-sol` with a `[fallback: ...]` prefix until this ChatGPT account is enabled for Astra) |
| `smartest` | `gemini-3.8-flash` + "reason exhaustively" (watch for `[fallback: ...]` — the answering model is what counts) | `gpt-6-astra` + "reason exhaustively" (same fallback rule) |
| `fast` | `gemini-2.5-flash`, no crossfire ever | `gpt-5.5` (explicit — cheaper/faster tier) + "top-3 issues only" |

Tier from first argument (`/gauntlet smartest <topic>`). Crossfire uses the same model as Round 1 — its replies are ≤30 words; don't spend the expensive tier there.

## Rules

- Both tools are stateless — each call must embed the full text it needs. Structured-output calls set `max_output_tokens` ≥ 8192 (truncated JSON = lost findings, observed live 2026-07-07).
- If one vendor errors after one retry, continue single-opponent, mark report **DEGRADED**. If BOTH vendors fail, ABORT: report INCOMPLETE with the errors — never emit a verdict from an empty panel.
- Vendor findings are **structured JSON only**, no prose: `{severity, quote (verbatim from artifact), location, failure_scenario (concrete), confidence}`. A clean review returns exactly `{"clean": true}` — so empty output is distinguishable from a parse failure. Max 8 findings per call; max 2 BLOCKERs, and a third BLOCKER must name the exact check the judge can run to confirm it. Rubric hardcoded in the prompt: BLOCKER = crash/data-loss/security/ship-stopping; MAJOR = wrong behavior or state; MINOR = everything else. Each panel seat wraps its return with `{vendor, lens, model_answered}` so the scoreboard and fallback attribution survive. Either wrapper may prefix its reply with `[fallback: <model> answered ...]` (Gemini tier fallback; GPT while `gpt-6-astra` is still gated on this account) — strip that line before JSON-parsing and record the model it names as `model_answered`.

## Pre-send gate (mechanical, before ANYTHING leaves)

Scan the artifact itself before any external call: grep for credential patterns (`api[_-]?key`, `secret`, `token`, `password`, `BEGIN .* PRIVATE KEY`, `.env` content, high-entropy strings in assignments). Hit → stop and show the user the offending lines; do not send. Also check size: over ~50k tokens, don't silently truncate — tell the user and review the riskiest subset explicitly. The Rules-level "never send secrets" is intent; this gate is enforcement.

## Context pass (before Round 0)

External models are context-blind — an artifact reviewed without local knowledge produces generic findings. If the working directory has notes or agent memory (design docs, gotchas notes, prior audits on the same component, the memory index), pull what's relevant via direct reads. Distill into a **context brief, ≤300 words**: conventions, constraints, known traps, prior findings on this component. Nothing that doesn't change the review. Scrub the brief before it goes external: no credentials, project/bucket IDs, internal URLs, or people's names.

## Round 0 — Claude's sealed take

Before dispatching, write your OWN top findings (3-7 bullets, severity-ranked) in your reasoning. Prevents anchoring, and doubles as the single-strong-model baseline the panel must beat.

## Round 1 — Blind takes (parallel subagent panel, artifact by reference)

Default: write the artifact ONCE to a scratchpad file, then dispatch **four parallel `general-purpose` subagents in one message** — one per (vendor × lens):

- **Lens A — correctness**: bugs, logic errors, data-flow, state, concurrency.
- **Lens B — assumptions**: unstated assumptions, missing edge cases, security, failure modes under load/partial failure.

Each subagent: reads the file + context brief, sends artifact + its lens's adversarial prompt to its vendor, quote-gates the response (below), and returns ONLY the surviving JSON findings in the seat wrapper. Seats follow the punt rule in `~/.claude/rules/escalation-triggers.md` — flag, don't guess, never act irreversibly. The main context never holds the artifact more than once. Tiny artifacts (≲60 lines) or `fast` tier: two direct inline calls, one per vendor, both lenses merged into one prompt.

**Cluster/dedupe** the finding sets before anything escalates — key on `(location, failure mode)`, never on quote alone: two findings quoting the same region for different failure modes (e.g. missing transaction vs missing authz) are DISTINCT and both survive.

Adversarial prompt core: "Find what is WRONG under your lens — no praise, no summary. Every finding needs a verbatim quote and a concrete failure scenario. If nothing above MINOR, return {\"clean\": true}."

## Quote-gate (mechanical, before any escalation)

Match each finding's `quote` against the artifact after **normalizing both sides**: strip markdown emphasis/backticks, smart quotes → straight, collapse whitespace runs. Models quote rendered text, not raw markup — exact byte-matching false-drops real findings (observed live: `**bold**` vs `bold`, twice). After normalization: clear no-match → drop as **HALLUCINATED** (logged, counted in scoreboard); near-miss (quote is plainly of a real passage but trivially mangled, e.g. ellipsized) → keep, tagged NEAR-MISS, for Round 3 verification.

Exception: findings whose *claim* is whitespace-dependent (IndentationError, YAML nesting, tab/space mix) can't be gated on normalized text — normalization erases the very evidence in question. Check those against the raw artifact bytes instead (observed live: both Gemini seats fabricated the identical IndentationError; raw-byte check killed it).

## Round 2 — Delta-only crossfire (conditional, ONE round max)

**Disputed, operationally**: two seats flag the same `(location, topic)` with conflicting severity or validity, or one seat returns `{"clean": true}` for territory where another seat found a BLOCKER/MAJOR. Skip crossfire entirely when Round 1 (post-gate) has no BLOCKER/MAJOR findings and no disputes — go straight to verdict. Debate past one round adds noise, not signal.

When it runs: for each disputed or BLOCKER/MAJOR finding, send the opposing vendor the finding + minimal relevant snippet — never the full artifact, never the source's identity ("A reviewer flagged: ..."), which kills sycophancy and self-preference. Response format: `{valid: bool, reason: ≤30 words}`. A crossfire rejection is **advisory, not a kill**: the responder saw only a snippet and may lack the cross-cutting context — Claude rules in Round 3. (Same for blanket approvals: 8-for-8 "valid" is agreement bias, not confirmation.)

## Round 3 — Verdict (Claude judges)

1. **Verify** every surviving BLOCKER/MAJOR against the evidence the artifact type affords — code: run a test, type-check, read the code path; plans/designs/claims: check against source documents, data, or the artifact's own internal consistency. A finding that CANNOT be verified with available evidence is capped at **PLAUSIBLE** — reported, never silently dropped, never CONFIRMED. When more than two findings need verification, spawn parallel verification subagents (Reality Checker pattern: default verdict NEEDS EVIDENCE) rather than verifying serially inline. Adversarial output is hypothesis generation, not truth; only verification promotes a finding.
2. Classify: **CONFIRMED** (verified), **PLAUSIBLE** (unverifiable with available evidence), **DISPUTED** (seats disagree — Claude rules, one-line reasoning), **UNIQUE** (one source only — weight HIGHER, not lower: vendor agreement is largely correlated error, novelty is the real signal), **SEALED-ONLY** (Claude's Round 0 caught it, panel missed).
3. Emit: verdict line (PASS / PASS-WITH-FIXES / FAIL + one sentence), findings table (`# | Severity | Class | Finding | Caught by | Ruling`), scoreboard (findings + hallucinated + near-miss counts per seat, which model actually answered, whether crossfire ran and what it changed).
4. If the repo has an audits folder (e.g. `docs/audits/`), write the verdict there as `YYYY-MM-DD Gauntlet — <slug>.md` matching repo conventions; else report inline. Never post to Slack/Jira/GitHub unless explicitly asked.
