---
title: "Postmortem: v0.1.15.post1 hotfix"
author: emil
created_at: 2025-01-16T09:21:00+00:00
---

# Postmortem: v0.1.15.post1 Hotfix

Release date: 2025-01-16. Same-day patch for a cache hashing regression introduced in v0.1.15.

## Impact

- Incorrect cache invalidation under certain provider configurations
- Affected: any deployment where the backend selection fell through to a non-default path
- No data loss
- Duration: from v0.1.15 going out to v0.1.15.post1 confirming clean on CI, same day

I don't have exact numbers on how many environments were actively affected before the patch shipped. If anyone saw this in prod and has specifics, worth adding here.

## Timeline

```
v0.1.15 ships
  -> hashing regression present but not immediately visible in standard CI paths
  -> regression surfaces under specific provider configurations
  -> identified and root cause confirmed
  -> fix committed: hashing logic pinned to stable path, offending change reverted
  -> v0.1.15.post1 ships
  -> CI run confirms clean
```

All of this happened on 2025-01-16. I dont have exact timestamps for each step.

## Root Cause

The hashing logic in v0.1.15 was changed in a way that produced different hash outputs depending on which backend was selected. Under the default configuration this wasn't visible because the path through the code was consistent. Under certain provider configurations, the backend selection fell through to a different path, and the resulting hashes didn't match what was previously cached, causing unnecessary invalidation.

The silent fallthrough is the real problem here. The regression existed in v0.1.15 but there was no signal that the non-default backend path was being exercised differently. Standard CI didn't catch it because it runs against the default configuration.

The fix pinned the hashing logic to a stable path regardless of which backend is selected, and reverted the change that introduced the divergence.

## What Went Well

- Same-day turnaround once the regression was identified
- No data loss, cache invalidation is recoverable by definition
- CI confirmed clean before we called it done

## Action Items

- [ ] Document the config defaults for backend selection before the next rollout, specifically which backend is selected under which conditions and what the fallthrough behavior is. This is the thing most likely to mask a similar regression again: if we dont know which path a given environment is on, we cant write a test that covers it.
- [ ] Check whether CI can be extended to cover at least one non-default backend configuration. Even a smoke test would have caught this.

The documentation item is the higher priority. The CI gap is real but the documentation gap is what made the CI gap dangerous.

## Open Questions

- Which environments actually hit this before the patch? I'd want to know if anyone saw visible failures vs. just silent invalidation churn.
- Who owns the backend selection config? Needs to be whoever writes the documentation above, or at minimum reviews it.
