---
title: "Weekly notes: week of Dec 9 - two reverts"
author: dario
created_at: 2024-12-11T09:42:00+00:00
---

# Weekly notes: week of Dec 9 - two reverts

Rougher than usual. Two reverts, both now postmortem'd. Writing this up Wednesday so people have context before the end of week.

## The reverts

**Dec 4 - end-of-run retry logic**

Retry logic at end-of-run was interacting badly with how we close out a run. Reverted to stabilize. Gideon has the postmortem (ref: Postmortem: Dec 4 revert of end-of-run retry logic). The interaction wasnt obvious from the code, which is partly why it got through review.

**Dec 10 - batch auto-delete**

Auto-delete keyed on counters that were technically correct, but correct counters alone don't make auto-cleanup safe. Dermot has the postmortem (ref: Postmortem: Dec 10 revert of batch auto-delete).

The main thing to take out of this one: any cleanup has to be opt-in, not default. That's now written down. It should apply to anything we touch in the artifact lifecycle going forward, not just batch auto-delete specifically.

## What shipped

Still on v0.1.11. 111 changes merged to date. The reverts didn't push the release back, but they did add review load and opened some questions about what's in scope for 0.1.12 that we haven't answered yet.

## PRs in flight this week

- PR 78: vLLM example for OpenAIOnlineParallelProcessor (mine)
- PR 90: Add an argument to disable cache for Prompter (mine)
- PR 106: summarizing text messages between two people example (Konrad)
- PR 133: env example file (Otto)
- PR 161: Curator Usage Example, Prometheus LLM Judge evaluation (Gideon)
- PR 163: curator-viewer getCacheDir helper + cache dir param (Gideon)

## Carrying over

- issue 48: README docs on batch. Ownership still unclear. The postmortem flagged artifact lifecycle as in scope but nobody formally picked this up.
- issue 88: disabling caching for curator. Related to PR 90 above, probably.
- issue 86: retry on structured output failure. Feels more relevant now given the retry revert. Not sure if we deprioritize this or treat the revert as a reason to look at it more carefully before we bring retry logic back.

## Where things stand

The instability this week came from two independent areas, batch lifecycle and retry logic, not one systemic problem. That's actually somewhat reassuring. The pipeline isn't broken, we took the hits, documented them, and the counters are fine.

What's not settled going into next week:
- release scope for 0.1.12 (the reverts added open questions we haven't resolved)
- stale PR triage, backlog is accumulating
- issue 48 ownership
