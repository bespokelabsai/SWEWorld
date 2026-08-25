---
title: "v0.1.21 Release Notes"
author: dermot
created_at: 2025-03-19T09:14:00+00:00
---

# v0.1.21 Release Notes

**Millrow/curator** - released 2025-03-19

## Bugfixes

- **Gemini unicode output fix**
  - Malformed unicode characters in batch responses were being silently dropped or corrupted before the row was written. No error was raised, so affected rows looked complete but contained bad data.
  - Fix validates and repairs unicode at the point the Gemini response is decoded, before it touches output. If you have been running batch jobs against the Gemini backend and are not entirely sure your output was clean, it is worth re-running those jobs on v0.1.21.

- **Token count wrap fix**
  - Output-token estimates were stored in a field that overflowed for long responses, causing the running total to wrap to a very small or negative number. Cost accounting downstream of that figure was therefore wrong.
  - Fix widens the field. Existing cost records that were produced by an overflowed count are not corrected automatically, i mean there is no migration, so if you need accurate cost history for long-response runs you will need to re-derive those figures from raw logs.

## Upgrade

No breaking changes. Drop-in replacement for v0.1.20. Standard upgrade path applies.

## What is not changed

Nothing else. No new features, no config changes, no deprecations.
