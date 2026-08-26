---
title: "Weekly notes: week of Dec 9 - two reverts"
author: dario
created_at: 2024-12-11T09:35:00+00:00
---

# Weekly notes: week of Dec 9 - two reverts

## Reverts

Two reverts landed this week, both in the pipeline layer. Neither caused data loss, which is fortunate, but both affected correctness of output in ways that would have been hard to debug downstream.

**End-of-run retry logic** (reverted Dec 4, postmortem by Gideon Halloway)
- retry logic was firing after a run completed and re-sending requests that had already been counted
- result: inflated output numbers
- caught quickly because the summary looked wrong at the terminal

**Batch auto-delete** (reverted Dec 10, postmortem by Dermot Callaghan)
- auto-delete was wiping per-run response and request files before the end-of-run summary had a chance to read them
- result: all counts printed as zero
- again, obvious immediately from the terminal

## What these two have in common

Both failures come down to ordering. In the first case, an end-of-run hook ran before summary completion when it should have run after. In the second, file cleanup ran before summary read when it should have been gated on summary completion. I think the general lesson is that anything touching files the summary depends on, or anything that fires "at end of run", needs an explicit dependency on summary completion rather than relying on timing or assumed order.

The other thing worth noting: we caught both of these from the terminal output alone. No additional instrumentation was needed. The current observability surface is sufficient for this class of bug.

## Open follow-ups

Re-introducing batch auto-delete is still open. Tracking in Dermot's postmortem, not here.

## PRs in flight this week

- PR 78: vLLM example
- PR 90: disable cache for Prompter
- PR 106: text messages summarization example
- PR 133: env example file
- PR 161: Prometheus LLM judge example
- PR 163: curator-viewer cache dir

Haven't looked closely at most of these this week, the revert work took priority.

## Release

No release this week. v0.1.11 holds.
