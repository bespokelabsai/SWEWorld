---
title: "Weekly notes: week of Nov 25 - v0.1.10 out"
author: gideon
created_at: 2024-11-27T08:50:00+00:00
---

# Weekly notes: week of Nov 25 - v0.1.10 out

## Shipped

- v0.1.10 is out

## In flight

- PR 141: LiteLLM + instructor backend, still open
- PR 161: Prometheus LLM Judge example
- PR 78: vLLM example
- PR 90: disable cache for Prompter
- PR 106: text messages summarization example
- PR 133: env example file

## Commits landed this week (targeting v0.1.11)

Six commits since Monday, rough breakdown:

- instructor + liteLLM coverage checks
- model init logging
- formatting cleanup

Nothing dramatic, mostly tidying up the surface area around the LiteLLM integration before we cut 0.1.11.

## Postmortem: Nov 23 LiteLLM revert

Still in progress. I dont have a finalized write-up yet. Will link here once its on the wiki.

## Open questions

These are all tracked in issues and none of them are resolved as of today. Listing here because they keep coming up in conversation and I want one place to point people.

- issue 33: cache behavior for batch completions
- issue 47: batch cancellation
- issue 48: batch README docs
- issue 50: varying batch size
- issue 52: multiple samples per request
- issue 55: louder error on response count mismatch
- issue 62: generation config support
- issue 74: broader model support via LiteLLM

Honestly the cache question (issue 33) feels like it should be settled before we go much further with PR 90, since those two are probably touching the same behavior. Not sure if that dependency is explicit anywhere yet.
