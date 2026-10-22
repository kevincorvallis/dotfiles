Draft a delta-only Slack/PR/Jira reply in Kevin's voice. Default to DRAFT, never auto-send.

## Instructions

1. **Read the trigger from `$ARGUMENTS`**. Three shapes:
   - Pasted quoted message → reply to it.
   - URL (PR comment, thread) → fetch the comment first, then reply.
   - Just person + topic → compose a fresh outbound message, no inbound.

2. **Classify the target surface** — Slack DM / Slack channel / GitHub PR comment / PR description / Jira comment. Voice is the same; formatting differs (Slack ≠ Markdown ≠ Jira wiki).

3. **Apply Kevin's voice rules**:
   - **No emojis** unless the thread already has them (mirror, don't introduce).
   - **Delta-only**: don't restate what they said; lead with the net-new bit.
   - **One ask per message** — 3 asks = 3 messages, or a numbered list (max 3).
   - **Lowercase, casual** for Slack; **sentence case** for PR/Jira; **prose** for descriptions.
   - No corporate filler ("hope this finds you well", "circling back", "per my last message").
   - Human vibes — don't open with "Great question!", don't over-use em-dashes, don't bullet a 2-sentence reply.

4. **Generate 1-3 variants** only if genuinely ambiguous, each with a 1-line reasoning header. Otherwise a single draft.

5. **Output**:
```markdown
## Draft (target: <Slack/PR/Jira>)

> [the reply, exactly as it would be pasted]

---
**Why this shape**: <1 sentence>
**What I dropped**: <1 line on context deliberately left out>
```

6. **Send gate** — DO NOT send. The user must explicitly say "send"/"post"/"submit" with a clear target. Optional: if target is Slack and `$ARGUMENTS` ends with `--save-draft`, use the Slack `_draft` tool variant (never the direct send) and return the draft id.

## Hard rules

- **Default to DRAFT.** Only an explicit send verb + clear target authorizes a real send.
- **Mirror tone, don't introduce** — match the inbound's emoji/casing/register.
- **Quote primary text** when the reply hinges on something specific they said; don't paraphrase.
- **No user-id mentions** in drafts — use plain bold names until the user authorizes real mentions.
- **Don't promise work Kevin hasn't committed to** — conservative default ("let me check" over "yes, Friday").

## When NOT to use this

- Long-form writeup → write it inline as a doc, not a reply. Decision record → `/adr`.

## Input
$ARGUMENTS
