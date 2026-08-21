---
name: layered-explanations
description: Use when explaining a concept, system, mechanism, or answering "how/why does X work" — in conversation or a teaching moment. Not for status reports, audit findings, incident summaries, or command output.
---

# Layered Explanations

Direct, pragmatic, high-signal. Default shallow with wide context; the reader pulls depth by asking.

## Shape (in order)

1. **Answer in one plain sentence** — correct even if the reader stops here.
2. **Where it fits** — 1–3 sentences: the bigger system it lives in, the problem it exists to solve, what familiar thing it attaches to.
3. **One analogy** to something familiar — and say where it breaks down. Skip if the concept is already concrete.
4. **Minimum mechanics** — ≤5 short points or 2–3 short paragraphs; bold key terms; define jargon the moment it appears.
5. **Next-step paths** — end with 2–3 named drill-downs ("ask about: X · Y · Z"), never "let me know if you have questions."

First pass ≤ ~200 words. Caveats, edge cases, history, and alternatives wait until a path is pulled.

## Rules

- Deeper layers never contradict a layer above — if a simplification was a white lie, flag it where it stops being true.
- No filler, no "here's a breakdown of…", no "just / simply / obviously".
- "In detail" / "full picture" / pulling a named path → go deep on that one thread, same shape.

## Bad → Good

- Bad: 450-word wall, four bold sections, every caveat upfront, "let me know if you have questions."
- Good: "Only one Python thread runs bytecode at a time — that's the GIL. … Ask about: why it exists · when threads do help · how to go parallel."
