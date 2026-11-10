# PR Descriptions

Shape: a short visible opener a human can skim, then the full agent write-up collapsed in `<details>` (Simon Willison's "details-summary" pattern).

- Opener: one plain paragraph on the intended behavior, covering the 5Ws (what changes, who it affects, where in the system, when it applies, why) — a reviewer should get the intent in ~60 seconds; then a prose paragraph on how the change was validated — only claims backed by evidence; say plainly what is red or unverified. Add a screenshot if the change is visual
- Opener limits: plain prose, ≤4 short paragraphs, ~150–200 words (intent ≤80, validation ≤60): no headers, bold labels, checklists, or file paths; tickets as links; no AI-attribution footer
- Collapsed block: everything else (design notes, file-by-file changes, commands run, follow-ups) goes below the opener in `<details>`; the opener limits don't apply inside. `<summary>` is the plain label `Full write-up` — no model or tool name. Skip the block if there's nothing beyond the opener. Same pattern for long agent-written comments
- Keep the blank line after `</summary>` — without it GitHub shows the inside as raw Markdown:

```html
<details>
<summary>Full write-up</summary>

…full agent write-up…

</details>
```
