---
description: Dispatch 15 parallel investigation agents on a topic — wraps superpowers:dispatching-parallel-agents with a standard fan-out.
argument-hint: "<topic or question to investigate from many angles>"
---

# /fan15 — 15-Agent Parallel Fan-Out

Kevin's most-common pattern: "kick off 15 parallel agents to investigate X."
Documented 99× across recent sessions with various typos ("parlalel", "paralel").
This command standardizes the workflow and saves the prose.

## What this command does

Invoke the `superpowers:dispatching-parallel-agents` skill with the user's topic ($ARGUMENTS), then:

1. **Decompose** the topic into 15 independent sub-questions — different angles, different evidence sources, different falsification targets. Each sub-question must be:
   - Answerable without context from the other 14
   - Bounded (a single subsystem, a single file path, a single dataset, a single question)
   - Hypothesis-laden (predicts what the answer might be, so the agent can falsify)

2. **Dispatch** all 15 via parallel `Agent` calls in a single message. Use `subagent_type: general-purpose` unless a more specialized agent matches.

3. **Each agent prompt** includes:
   - The narrow sub-question
   - Where to look (specific file paths, tables, dashboards — not "the codebase")
   - Expected output: ≤500 words, evidence-first, falsification check at the end
   - "Quote primary sources. Do not synthesize across sources you didn't read."
   - The punt rule from `~/.claude/rules/escalation-triggers.md`: flag `escalate: true` (and stop before anything irreversible) rather than guessing past a trigger.

4. **Synthesize** when all 15 return:
   - Group by agreement / disagreement / unique signal
   - Flag any agent that hedged (low confidence, "could not find") — these are the gaps
   - Apply the **convergence rule**: 3+ agents agreeing on a prediction is NOT independent verification — verify against primary sources before treating as fact
   - Produce a single synthesized answer with explicit confidence levels per claim

## When NOT to use this

- **Single-source questions** — "what does file X say?" is one Read, not 15 agents.
- **Sequential dependencies** — if step 2 needs step 1's output, fan-out wastes work.
- **Prediction tasks on unverified data** — parallel agents predicting model behavior produce fiction. Use real data first.
- **Tasks under 30 min of manual work** — fan-out overhead > savings.

## After dispatch

While the 15 agents run, this command should:
- Update the TaskList with one task per sub-question
- Tell the user the breakdown so they can redirect if a sub-question is misframed
- Wait for all 15 to land before synthesizing — do not pre-commit to a narrative

## Related

- `superpowers:dispatching-parallel-agents` (canonical skill)
