---
title: "Release notes: v0.1.15"
author: emil
created_at: 2025-01-14T09:49:00+00:00
---

# Release notes: Millrow v0.1.15 (Stratos Crunch)

Released 2025-01-14.

## What changed

**LLM interface refactor**

The provider interface was refactored to unify how parameters get passed across processors. Caller API is backwards-compatible, so existing configs dont need changes.

**Token counting (PR 307)**

Token counting is now shared across online, batch, and local inference paths. Previously each processor had its own accounting, which meant discrepancies if you were mixing paths. Single implementation now.

**Config validation**

Startup validation now catches missing or mistyped fields and surfaces specific errors before any requests go out. Previously you could get a mid-run failure with a much less useful message.

**Bulk inference error handling (PR 248)**

Certain failure modes on the bulk inference path were surfacing as hard crashes. They are now caught and reported cleanly. Should make failures on large runs much easier to debug.

**Lazy provider imports**

Heavy provider dependencies are now imported on first use rather than at startup. If your workload only touches one provider, cold-start time is noticeably shorter. No behavior change otherwise.

**Cache and resume**

The cache hashing regression from Jan 13 was already reverted before this release and is not re-introduced here. Cache key function is unchanged.

One thing worth calling out explicitly: appending rows to your input dataset between a pause and a resume is not safe. A resumed job sizes its request set to the original run. If the dataset grew, reassembly by index will silently pair rows with the wrong results. No error, just wrong output. Don't do it.

## Not in this release

- PR 161 (Prometheus LLM Judge cookbook) - still open, will land in a follow-on
- PR 362 (fix_json curly-brace fix) - still in review
- PR 133 (env example file) - pending
