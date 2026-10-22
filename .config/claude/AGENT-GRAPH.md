# Agent Graph — canonical topology (v3, 2026-10-12)

Five curated global agents. Edges are **advisory**: subagents cannot spawn subagents, so the main loop executes
handoffs. Every agent's final message ends with a strict-grammar line — `next: <agent-name> — <one-line reason>`
or `next: none`.

## Main-loop protocol (the part that makes edges real)

1. When a subagent report ends with `next: <agent> — <reason>`, treat it as a first-class routing suggestion:
   follow it, or say in one line why not.
2. Never re-dispatch the agent that just reported.
3. Pass forward only the context the next agent needs — never the full transcript (hop bloat).

## Nodes

| Agent | Scope | Role |
|---|---|---|
| librarian | global | open-source code evidence with GitHub permalinks |
| researcher | global | academic papers, citations, literature synthesis |
| Code Reviewer | global | defect-focused diff/PR review |
| Accessibility Auditor | global | WCAG/keyboard/screen-reader audits |
| Reality Checker | global | adversarial verification of claims; VERIFIED/REFUTED/UNPROVEN |

## Edges

```mermaid
graph LR
  CR[Code Reviewer] -->|verify-claim| RC[Reality Checker]
  CR -->|a11y-pass| AA[Accessibility Auditor]
  AA -->|verify-claim| RC
  LB[librarian] -->|academic-depth| RS[researcher]
  RS -->|code-depth| LB
  RS -->|cite-check| RC
```

| Edge | Type | Trigger |
|---|---|---|
| Code Reviewer → Reality Checker | verify-claim | review findings rest on unverified claims |
| Code Reviewer → Accessibility Auditor | a11y-pass | the diff touches UI surfaces |
| Accessibility Auditor → Reality Checker | verify-claim | a claimed a11y fix needs independent evidence |
| librarian ↔ researcher | academic-depth / code-depth | question crosses the paper↔code boundary |
| researcher → Reality Checker | cite-check | key claims need adversarial evidence-checking |

## Maintenance

- This file is the single source of truth; each agent's "Report contract (Agent Graph)" section must agree with it.
- The three reviewers kept their original `name:` values ("Code Reviewer", "Accessibility Auditor",
  "Reality Checker"); nothing was renamed.
