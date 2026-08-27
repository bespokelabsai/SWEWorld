---
title: "Weekly sync notes: week of Jan 20 \u2014 v0.1.16 shipped"
author: nikolai
created_at: 2025-01-22T09:14:00+00:00
---

# Weekly sync notes: week of Jan 20, v0.1.16 shipped

**Date:** 2025-01-22
**Attendees:** TBD (need to add before sharing)

---

## Release

v0.1.16 shipped. 198 changes merged across 11 releases total, feels like good momentum, actually.

## PRs in flight

- PR 133: env example file (Otto Brennan), pending review
- PR 161: Prometheus LLM Judge evaluation example (Gideon Halloway), pending review
- PR 362: Fix_json curly braces fix (Ilse Vandekerckhove), pending review
- PR 372: Gemini batch request processor (Millrow Refactor Bot), pending review
- PR 378: max parallel request processor support (Emil Brandvold), needs at least one review
- PR 387: block capacity by max_tokens for Anthropic online (Emil Brandvold), needs at least one review

PR 378 and 387 are both Emil's and both are sitting without review. I want to make sure we get eyes on those before they start drifting. They're independent PRs so either can land first, but both need at least one reviewer before they can move.

No decisions made on the stale PR queue more broadly, that conversation is still open.

## Open questions

These are all still open, no resolution this week.

- issue 52: support multiple samples per request
- issue 92: [UI] better JSON / markdown / file extension views in detail view
- issue 93: [UI] display run status
- issue 94: metadata.db run status (enum), run progress (percentage), etc
- issue 102: clarify that return value must be a plain dict, not Pydantic objects
- issue 105: distribution graph skewed in data viewer
- issue 121: should we handle pydantic -> dict and back automatically when adding to a row?
- issue 124: `inspect(func)` sensitive to comments and whitespace, cache invalidates unexpectedly

I'm a bit concenred that 92/93/94 are all UI-adjacent and all open at the same time, not sure if those are being tracked together or if they're truly independent. Would be good to clarify who owns that cluster.

Issue 124 i find particularly tricky, cache invalidation due to whitespace is the kind of thing that bites users silently and they may not realise why their results look stale.

## Questions I don't have answers to

- who is reviewing 133 and 161? they've been pending a while, i don't know if anyone picked them up
- is the stale PR queue discussion happening async somewhere, or do we want to put time on the calendar?
- PR 372 is attributed to Millrow Refactor Bot, i assume that's an automated PR but i'm not sure who to ping if review comments need a human response
