---
title: "Weekly notes: week of Dec 2 - v0.1.11 out"
author: dario
created_at: 2024-12-04T09:14:00+00:00
---

# Weekly notes: week of Dec 2 - v0.1.11 out

## Shipped

- v0.1.11 out
  - batch file cleanup
  - additional retry coverage
  - progress bar fix on resume
- PR 202 merged: retry-once fix
  - the bug: a failed request could re-enter the queue more than once under concurrent batch conditions
  - was a real correctness issue, not just a nuisance, glad thats in

## In flight

- PR 78: vLLM example for OpenAIOnlineParallelProcessor, review welcome, nobody has picked it up yet as far as I can tell
- PR 90: argument to disable cache for Prompter, nearly ready per last update
- PR 161, PR 163: curator viewer and usage example work (Gideon)
- PR 106, PR 133: example and env file additions (Konrad, Otto)

## Open / carry-forward

- Rate limit edge cases and some auth error retry gaps turned up during 0.1.11 work
  - filed as follow-on issues
  - triage still ongoing: what actually blocks 0.1.12 vs. what can defer
- issue 86: retry on structured output fail, open
- issue 88: disable caching for curator, open (overlaps with PR 90 somewhat? need to check)
- issue 52: multiple samples per request, open, no movement this week
- Async retry parallelism under batch load: needs a call on production-readiness before 0.1.12 cuts
  - I dont think we can just let this slip in without a decision, it has load implications

## Next

- [ ] Agree which PRs land before 0.1.12 release cut
- [ ] Triage rate limit / capacity / token estimation work, what ships with 0.1.12, what defers post-ship

TBD on timing for 0.1.12 cut. Nothing agreed yet as of Dec 4.
