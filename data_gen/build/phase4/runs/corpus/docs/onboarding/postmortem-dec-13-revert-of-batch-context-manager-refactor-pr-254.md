---
title: "Postmortem: Dec 13 revert of batch context-manager refactor (PR #254)"
author: konrad
created_at: 2024-12-16T09:14:00+00:00
---

# Postmortem: Dec 13 revert of batch context-manager refactor (PR #254)

**Date:** Dec 13, 2024
**Status:** revert complete, runs stable as of Dec 13 afternoon

---

## What happened

PR #254 refactored the batch subsystem to use a context manager for lifecycle management, wrapping the previous explicit open/submit/wait/close calls in a `with` block. The goal was cleaner teardown and more predictable resource cleanup.

Within hours of merging, batch runs started failing intermittently. The failure pattern: parameters configured on a batch object before entering the `with` block were silently dropped inside it. The context manager's `__enter__` was re-initializing state on entry rather than carrying forward the existing instance configuration. Callers that set up the batch object and then immediately opened the context assumed they were handing control of the same object. They were not.

A second failure mode appeared under concurrent load. Two runs sharing a processor could each acquire the context manager on their own copy of state, then race on the underlying batch queue at teardown. Neither `__exit__` yielded the queue gracefully because each run believed it had sole ownership.

The revert was cut the same day. Runs stabilized.

## Timeline

```
Dec 13 AM    PR #254 merged
Dec 13       intermittent batch failures reported
Dec 13       root cause identified (re-init on __enter__)
Dec 13 PM    revert merged, runs confirmed stable
```

Three days since then, no further instability.

## Impact

Batch runs were unreliable for a window of a few hours on Dec 13. I dont have an exact count of failed runs from that window, need to check with whoever owns the batch run logs or dashboard. No data was corrupted as far as we can tell, the failures were execution failures not silent bad output.

## Root cause

The context manager's `__enter__` returned `self` but had already reset `self` before returning. This is a subtle Python footgun: the returned object looks like the configured instance but has lost all pre-entry state. Callers had no way to see this at the call site.

The concurrent teardown problem was a secondary consequence of the same design: because each worker believed it held independent state, the shared queue was not released cleanly on exit.

The original code had no tests asserting that pre-configured state survived context entry. That gap meant the re-init behavior went undetected in review.

The two issues, the state re-init and the concurrent teardown race, were both products of a refactor that changed how state was held AND changed the lifecycle pattern in the same PR. Those were bundled together, which made it harder to reason about either in isolation.

## What to avoid in SimpleLLM folding

The batch revert is directly relevant to the planned SimpleLLM folding work. A few specific things:

- **Re-initializing state on entry.** Any wrapper or lifecycle object that takes ownership of a configured instance must carry that configuration forward. This needs an explicit test, not a code review eyeball.
- **Bundling lifecycle and state changes in one PR.** Separate the state refactor from the lifecycle wrapper. Each should be reviewable and revertable on its own.
- **No before/after behavioral assertion.** Any folding PR should include a test that asserts a caller-configured object produces the same behavior after the wrapper is applied. Not just that it runs, that it produces the same result with the same configuration.
- **Concurrent teardown assumptions.** If SimpleLLM folding touches anything shared across parallel workers, teardown ordering must be explicit and tested under load. Dont rely on GC or `__exit__` order under concurrency.

I'm not deep enough into the SimpleLLM internals to say exactly which pieces are shared across workers right now. That's worth mapping before the folding work starts.

## Action items

- [ ] SimpleLLM folding PRs should be one behavioral change at a time, small enough to revert cleanly
- [ ] Any lifecycle wrapper touching batch-mode or shared processor state needs a concurrent teardown test before merge
- [ ] Pre-context configuration survival should be a standing test case in batch-mode going forward
- [ ] Get a count of failed runs from Dec 13 impact window (need whoever owns the batch dashboard)
- [ ] Map which SimpleLLM state is shared across parallel workers before folding work begins

## Open questions

- Do we have a count of affected runs from the Dec 13 window? I don't have visibility into that directly.
- Is there existing test infrastructure for concurrent batch scenarios, or would that need to be built? I'm assuming we'd need to build it but not sure.
- Who's taking the SimpleLLM folding work? The action items above should probably be assigned before that PR is opened, not after.
