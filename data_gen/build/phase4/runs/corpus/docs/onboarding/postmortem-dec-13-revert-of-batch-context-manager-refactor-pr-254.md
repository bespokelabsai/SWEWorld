---
title: "Postmortem: Dec 13 revert of batch context-manager refactor (PR #254)"
author: konrad
created_at: 2024-12-16T09:14:00+00:00
---

# Postmortem: Dec 13 revert of batch context-manager refactor (PR #254)

Dec 16, 2024

## What happened

PR #254 refactored the batch-mode context manager to consolidate resource setup and teardown, previously spread across several call sites, into a single managed block. The goal was cleaner resource lifecycle management and less duplication. Reasonable intent.

During multi-request batch runs after the merge, the consolidated block failed to restore batch parameters correctly when an inner operation raised an exception mid-flight. Parameters set on entry were not reset on exit through the failure path. Subsequent requests in the same batch then inherited stale configuration from the failed request, silently.

The failure path in question only triggers when a request errors out inside an already-running batch. The existing test fixtures did not cover that combination, so the problem did not surface in review.

Revert merged Dec 13.

## Timeline

- Dec 12: PR #254 merged
- Dec 13 morning: reports of inconsistent batch behavior on multi-request runs
- Dec 13 afternoon: root cause identified, stale parameter leak confirmed
- Dec 13: revert merged

## Root cause

The context manager's exit path did not unconditionally reset batch parameters. In the success path, teardown ran correctly. In the exception path, teardown was skipped or partially skipped depending on where the exception originated. Whatever state the failed request had written to shared parameters was left in place for the next request to read.

This is a known hazard with context managers that touch shared mutable state. The consolidated block introduced a single exit path without ensuring that path was truly unconditional.

## Impact

- Batch runs containing any failing request mid-sequence could silently pick up wrong parameters for all subsequent requests
- No data loss; affected runs produced outputs with incorrect configuration rather than crashing or erroring visibly
- Scope limited to multi-request batch runs with at least one mid-sequence failure

The silent nature of this is the part I find most uncomfortable. A run completing with wrong configuration is harder to catch than one that fails loudly.

## What went well

- Root cause identified within hours of the first reports
- Revert was straightforward, no secondary breakage
- The discussion in the issue thread was quick and stayed focused on the mechanism rather than anything else

## Action items

- [ ] Any context manager touching shared mutable state must reset that state unconditionally in its exit path, exception case included. This should become a review checklist item for batch-mode changes, not just an informal expectation.
- [ ] Tests for batch-mode changes must cover the mid-batch failure path before merge. Need to decide where that fixture lives and who owns keeping it current.
- [ ] Review other context managers in batch-mode for the same exit-path pattern. I do not know how many there are off the top of my head, need someone to do a sweep.
- [ ] Confirm the replacement approach for the context-manager consolidation is safe before re-attempting the refactor. The underlying goal of PR #254 was valid, the implementation just needs the failure path closed.

## Open questions

- Who is taking the sweep of other batch-mode context managers? I would like that done before end of week if possible.
- The replacement approach for the consolidation: is there a proposal yet, or is that still open? I have not seen anything in the issue tracker as of today.
