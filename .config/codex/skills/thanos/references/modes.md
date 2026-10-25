# Mode guidance

Use the relevant section to build a self-contained brief. Add secondary concerns when the user asks for them; do not run all modes by default.

## UI

Supply the user's task, intended audience, entry point, action sequence, screen copy and relevant states (loading, empty, success, error). Include actual DOM/accessibility excerpts or observations made by the coordinating assistant when available. Mark their source and distinguish measured facts from impressions.

The current runner does not transmit images. If a screenshot is supplied, the coordinating assistant can inspect it with an available permitted image tool and describe what it sees; label that as an intermediary observation. Reviewers must not claim they directly inspected the screenshot, tested keyboard access, measured contrast, or verified responsive layout. If direct visual comparison is essential, report that this transport does not support it.

Ask for prioritized improvements tied to task completion, with specific copy or interaction alternatives and the visual/interaction checks still required. Avoid presenting subjective taste as a defect. Verify proposals against the actual screen before recommending implementation.

## Planning

Supply the outcome, constraints, available resources, current state, dependencies and acceptance criteria. If no draft exists, ask both models to independently propose a plan. If one exists, include it as a candidate rather than a predetermined answer.

Ask for a preferred approach and a plausible alternative, ordered steps, decision points, uncertainties and inexpensive experiments that resolve them. Treat schedules and effort estimates as conditional on explicit assumptions. In the synthesis, produce an executable sequence and explain consequential disagreements. Do not claim any planned action was performed.

## Design

Supply the proposed architecture, data flow, trust boundaries, interfaces and invariants along with constraints and known alternatives. Include enough detail to evaluate concrete failure cases; identify missing contracts explicitly.

Ask which tradeoffs matter, which assumptions need evidence, and what would change the recommendation. Synthesize design decisions and validation experiments instead of accumulating every possible feature. Verify recommendations against the actual system's constraints.

## Adversarial

Supply the exact system or proposal being challenged, the allowed scope, expected invariants, and relevant boundaries such as concurrency, offline behavior, privacy or recovery. If an attack model matters, state actor capabilities rather than letting the reviewers invent unlimited access.

Ask for counterexamples: preconditions, a concrete sequence, the violated invariant, likely impact, a mitigation, and a discriminating test. Label hypothetical scenarios separately from reproduced defects. This mode is analytical and does not authorize exploitation, live probing, destructive testing or wider targets.

## Code

Supply a bounded diff or implementation excerpt with filenames, relevant surrounding code/contracts, expected behavior, and actual test results. Specify the base revision when available. Never imply reviewers can open omitted source files.

Ask for actionable correctness defects and regressions with evidence and focused tests. Verify findings against the real code before presenting them as bugs. Keep speculative improvements separate from demonstrated problems. A passing review is not a deployment approval or a substitute for tests.
