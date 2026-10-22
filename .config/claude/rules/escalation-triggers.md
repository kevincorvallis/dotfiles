# Escalation Triggers

For cheap/mechanical stages: subagent seats, Workflow `effort: low` stages, downshifted-model agents. Referenced by fan-out templates and gauntlet seats — don't paste, link.

## The rule

Punt upward — don't guess — when the stage is **about to take an action** that:

- has irreversible side effects (prod writes, deletes, sends, transitions)
- introduces a new abstraction the task didn't ask for
- sits on conflicting requirements
- can't name its own verification method
- touches security, billing, auth, or migrations
- hand-rolls polling, regex parsing of structured data, timers, or a state machine a platform primitive already provides

Triggers are **action-scoped, not topic-scoped**: *mentioning* prod data doesn't fire; *about to write to it* does.

## Punt mechanics

- **Flag-and-continue** where safe: tag the finding/step `escalate: true` in the report and keep working. The orchestrator decides what goes up a tier.
- **Hard-stop** only before irreversible actions.

## Downshift policy (from the 2026-07-08 gauntlet — all 4 seats)

Do NOT downshift a stage's model just because this trigger list exists — trigger *recognition* is a judgment skill cheap tiers lack. Downshift only stages whose triggers proved **syntactic** (keyword-matchable) after a measurement period at full tier. Track punt-rate; zero firings after two weeks means this file is decoration.
