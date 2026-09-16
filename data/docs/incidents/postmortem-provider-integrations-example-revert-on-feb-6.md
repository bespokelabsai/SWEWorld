---
title: "Postmortem: provider-integrations example revert on Feb 6"
author: nikolai
created_at: 2025-02-07T09:12:00+00:00
---

# Postmortem: provider-integrations example revert, Feb 6 2025

## What happened

A provider-integrations example was merged that introduced a reference cycle inside the inference client. Under sustained load, the Python garbage collector could not collect those cycles promptly, so memory grew without bound until the process was killed or restarted. That is the GC leak.

Separately, a code path added alongside the example could return an empty response to callers without raising an exception. Rows in generation runs silently dropped, no error surfaced, no retry triggered.

The two problems were coupled to the same change. Once both were confirmed under load, we reverted on Feb 6 rather than try to isolate a minimal fix under time pressure. Fixes shipped in v0.1.18.post4.

## Impact

- Memory grew until process death or restart on any long-running generation job
- Some rows received empty responses with no exception, causing silent data loss (no retry, no signal to the caller)
- inference.net users were hit harder than others because their request volume exposed the GC pressure faster than lower-traffic integrations

I dont have exact numbers yet on how many rows were silently dropped across affected runs. That needs to come from whoever owns the generation job logs.

## Timeline

```
Feb 6 (morning)   provider-integrations example merged
Feb 6 (afternoon) memory growth flagged under sustained load
Feb 6 (afternoon) empty-response path identified, rows confirmed dropped silently
Feb 6 (evening)   decision made to revert the full change
Feb 6 (evening)   revert landed
```

Exact commit timestamps I'd need to pull from the repo, i'm reconstructing this from memory and slack. Someone should verify these against the merge log before we finalize.

## Root cause

The inference client ended up holding a reference cycle: object A -> object B -> object A, approximately. Python's cyclic GC can collect these eventually, but under sustained load the collector couldn't keep up, so the cycles accumulated. This is a known failure mode with Python reference counting and it needs explicit care around any long-lived client objects.

The empty-response path was a separate issue: a branch that was reachable under certain response shapes returned without checking whether the response body was actually populated. No exception, no signal. The caller had no way to know.

Neither of these would have been caught by the existing code-execution checklist, because we didn't have an explicit check for either reference cycles or empty-response handling. That's on the checklist gap, not on any specific review.

## What went well

- The decision to revert rather than patch under pressure was right. Both problems were coupled to the same change and the blast radius of a bad in-place fix would have been worse.
- The revert itself was clean and landed quickly.

## Fixes in v0.1.18.post4

- GC leak: broke the reference cycle in the inference client so the collector can reclaim objects promptly. I want to make sure we have a test that exercises this under load before the example re-lands, not just a unit test for the cycle.
- Empty response: added an explicit check that raises rather than returning silently. Callers now see an exception and the row can be retried.
- inference.net integration path: confirmed both fixes apply there. This was verified specifically because inference.net traffic was the first to surface the pressure.

## Action items

- [ ] Re-land the provider-integrations example with a review checkpoint specifically for reference cycles (owner TBD, i'd expect whoever originally wrote the example)
- [ ] Add empty-response handling to the code-execution checklist before merge
- [ ] Get row-drop counts from generation job logs to understand actual data loss scope (needs whoever owns those logs)
- [ ] Consider whether we want a longer-running memory test in CI for client objects, not sure what that looks like on our infra (need to ask whoever owns the pipeline config)

## Open questions

- How many rows were actually dropped silently? I don't have this yet.
- Were any downstream consumers affected by the dropped rows, or did they all land in jobs that can be re-run?
- The CI memory test question above, I genuinely don't know what's feasible there without asking someone who knows the deployment setup.
