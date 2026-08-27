---
title: "Weekly Notes \u2014 Week of Apr 7"
author: dermot
created_at: 2025-04-09T09:14:00+00:00
---

# Weekly Notes, Week of Apr 7

**Milestone:** Consolidation and Provider Breadth
**Release:** v0.1.22 | 318 changes merged to date

---

## PRs this week

- PR 614, batch cancellation fixes, merged
- PR 621, gemini batch finish reason, merged
- PR 583, metadata db param
    - still waiting on review, day 33 now
    - look we need to get eyes on this, i'll chase again tomorrow
- PR 468, n-samples support, merged

## Work streams

- WS-050 batch mode, Emil, in flight
    - no blocker raised this week, checking in with Emil Friday
- WS-055 release engineering and CI, mine
    - v0.1.22 cut, 318 merged to date
    - TBD: confirm CI pipeline health post-release (need to check the run logs from this morning)

## Open questions carried forward

These have not moved this week.

- Issue 52, multiple samples, still open
- Issue 207, has_capacity detection via rate limit headers, no progress
- Issue 233, auto-detect rate limits, no progress
- Issue 290, ModuleNotFoundError on resource, not entirely sure who is looking at this currently
- Issue 293, OpenAI usage and cost reporting, open

## Notes / things to follow up

- [ ] Chase PR 583 reviewer, 33 days is too long
- [ ] Confirm WS-055 CI run status post v0.1.22
- [ ] Check with Emil on WS-050 expected merge window
- [ ] Issue 290, find out who owns the resource path and whether they have looked at the error
