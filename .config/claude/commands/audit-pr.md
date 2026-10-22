Multi-agent convention audit on a PR. Dispatches parallel agents against named patterns (conventions, security/correctness, per-author style) and synthesizes findings into an action list. Optional follow-up commit + PR description fix, gated by user confirmation. Repo-agnostic.

## When to use

Before marking a non-trivial PR ready-for-review. Especially valuable for:
- Auth / security changes (no precedent → easy to drift from conventions that don't yet exist)
- Infra / IaC changes (claims about deployment patterns that need verifying against the actual config)
- First-of-its-kind PRs in a service (establishing the pattern future PRs will follow)
- PRs where the description and the shipped diff may have drifted apart

Skip for: typo fixes, single-line config changes, obvious refactors with full test coverage.

## Input

`$ARGUMENTS` — PR number, or empty to audit the current branch's open PR.

## Phase 1: Classify the change shape

1. Fetch the diff: `gh pr diff <num>` or `git diff <base>...HEAD`.
2. Classify into one or more categories (bias toward narrowing): **auth-security**, **infra-iac**, **data-pipeline**, **frontend**, **refactor**, **endpoint-add**, **bugfix**.
3. Estimate blast radius: lines changed, modules touched, user-facing vs internal.
4. Pick agent count: **5** for typo/bugfix, **8-10** for endpoint-add or refactor, **12-15** for auth-security / infra / data-pipeline, **15-18** for first-of-its-kind.

## Phase 2: Resolve relevant people

Build a 2-3 person list whose patterns matter for this PR:
- **PR author** — pull their last ~5 substantive PRs in the same repo for self-consistency.
- **CODEOWNERS** for the touched paths, and recent contributors to the touched files (`git log --format="%an <%ae>" -- <file> | sort -u`).
- If the user named specific people, those override automatic resolution.

## Phase 3: Pick lenses from the menu

Always include (adapt prompts to the category):
- **Changelog/commit-message conformance** — match the repo's recent entries' length, tense, prefix, link format.
- **Build/package config** — does the new file need an explicit dep entry, or is the glob sufficient?
- **Test conventions** — fixtures, naming, mock style, negative-path density.
- **Per-author pattern audit** — one agent per resolved person from Phase 2.

Add for **auth-security**: HTTP auth precedent across the repo; constant-time comparison usage; secret-handling pattern; fail-mode semantics (fail-closed vs lazy-fail); error-response shape; logging (don't log secrets/401 reasons); relevant RFC compliance.

Add for **infra-iac**: secret-management precedent; env-var naming convention; resource/scaling config vs sibling components; image/version pinning shape.

Add for **data-pipeline**: schema migration safety (back-compat, NULL handling, defaults); write idempotency; dead-letter wiring; consumer audit (who reads the data, do they handle the new shape?).

Always add (scope-correctness):
- **PR description vs diff** — does the description accurately describe what shipped?
- **Cross-system impact claims** — for any "this also fixes/touches X" claim, grep across the repos you work in for the symbol and verify.

## Phase 4: Dispatch agents in parallel

Single message, multiple `Agent` calls. Each agent gets: a self-contained context block, ONE investigation lane, a strict output format (`VERDICT: [ALIGNED | DRIFT | NO PRECEDENT FOUND | BLOCKER]` + 3-5 evidence bullets with `file:line` citations + a ≤2-sentence recommendation), and a read-only mandate. Prefer `run_in_background: true`.

## Phase 5: Synthesize into a verdict

Bucket findings into **Aligned** (no action), **Real drift** (recommend addressing — multiple agents converge or one high-confidence finding), and **Skip** (single-agent stylistic preference, no convergence).

Calibration: 1 agent = surface but don't auto-fix; 2+ converging = high confidence; scope-correctness findings are highest priority.

```
## Verdict: [healthy / needs alignment / blocker]
### Aligned (no action)   | Lane | Finding |
### Real drift — recommend addressing   1. <change, file, why> ...
### Skip (defensible either way)   - <bullet>
```

## Phase 6: Confirm before applying

Never auto-edit or push. Present the proposed follow-up commit, any PR-description rewrite, and wait for an explicit "go" before any `git add`/`commit`/`push`/`gh pr edit`.

## Phase 7: Apply (after confirmation)

1. Edit files on the branch. 2. Run the repo's fmt+lint+test. 3. Verify green before committing. 4. Commit with a conventional message. 5. Push to the existing branch. 6. `gh pr edit --body` only if the description drifted — **never `--title`** (the author owns the title; teammates find PRs by it). 

## Reasoning discipline

Parsimony (one lens explaining a finding is enough), surface enumeration (confirm "no precedent" agents checked all relevant dirs), evidence over authority (if the description claims "matches pattern X" but X doesn't exist, the description is wrong), convergence as confidence.

## Anti-patterns

Hardcoded "always 15 agents" (calibrate to blast radius); lens-menu sprawl (5-8 per category); auto-fix without confirmation; ignoring scope-correctness lanes.
