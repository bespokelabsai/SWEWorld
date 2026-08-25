---
title: "Release notes: 0.1.19"
author: gideon
created_at: 2025-02-17T10:31:00+00:00
---

# Release notes: 0.1.19

258 changes merged across 16 releases.

---

## Highlights

### Progress bar revamp

Full rework of the progress display. ETA tracking is more stable (less jitter on runs with uneven work distribution), and cache hit rate now shows alongside throughput while a run is active. So you can see at a glance how much is being pulled from cache vs. done fresh, which matters a lot on incremental runs.

Also cleaned up a few rough edges around wide terminals and slow TTYs that were producing garbled output.

### Online request handling fixes

Around a dozen fixes to concurrent request handling:

- edge cases in cost accounting under concurrent requests
- per-provider token attribution getting misassigned when requests overlapped
- a couple of race conditions, hard to repro but confirmed real

If you were seeing inconsistent cost totals on parallel runs, this should clear that up.

### Function-calling example fix

A bug in the function-calling example was tripping up users on first run. Fixed.

---

## Upgrade

```
pip install --upgrade millrow
```

No breaking changes.
