Create a new Architecture Decision Record. Portable across repos — detects the decisions folder or falls back sensibly.

## Instructions

1. Find the ADR folder: check for `Decisions/`, `docs/decisions/`, `docs/adr/`, or `adr/` (in that order). If none exists, ask the user where ADRs should live before creating one — don't create a folder unprompted.
2. List existing ADRs there to determine the next number.
3. Create `ADR-NNN [Title].md` in that folder. Match the repo's existing ADR frontmatter/format if there are prior ADRs; otherwise use the structure below.
4. If `$ARGUMENTS` contains context, fill in the Context section. Set status to `proposed`.

## Default structure (when the repo has no prior ADR to match)

```markdown
---
title: "ADR-NNN: [Title]"
date: YYYY-MM-DD
status: proposed
tags: [adr, decision]
---

# ADR-NNN: [Title]

## Status

Proposed

## Context

[From arguments or leave for user to fill]

## Options Considered

### Option A: [Name]
- **Pros:**
- **Cons:**

### Option B: [Name]
- **Pros:**
- **Cons:**

## Decision

[Leave for user to fill]

## Consequences

[Leave for user to fill]
```

## Input
$ARGUMENTS
