---
title: "Weekly notes: week of Dec 9 - two reverts"
author: dario
created_at: 2024-12-11T09:42:00+00:00
---

# Weekly notes: week of Dec 9 - two reverts

An unusual week. We shipped and then had to walk back two separate changes. Both are now documented separately as postmortems; this is just the weekly summary layer.

## The two reverts

**Dec 4 - end-of-run retry logic**

- Reverted after it introduced regressions at the tail of runs
- Root cause: the retry path fired after the run's counters were already settled, producing duplicate or orphaned records
- No data loss confirmed, behavior was wrong, not destructive
- Gideon's postmortem is not yet published as of today (Dec 11), that's still outstanding, noted below

**Dec 10 - batch auto-delete**

- Reverted the same day it landed
- The auto-delete logic bypassed the per-run counters entirely, which are the canonical source of truth for batch lifecycle
    - any future implementation has to gate on the counters first, before any delete logic runs
- Dermot's postmortem is on the wiki: Postmortem: Dec 10 revert of batch auto-delete (incidents collection)

Worth saying clearly: these two incidents are related only in that both touched batch lifecycle code. They were independent changes and independent failures. I don't think there's a common root cause to chase here, though I'd want Gideon's postmortem published before I close that question entirely.

## What else moved this week

- PR 244 (error-handling across core pipeline) - main thing blocking the 0.1.12 release cut, needs review
- PR 90 (disable cache for Prompter) - still open, waiting on review cycles
- PR 78 (vLLM example) - still open, same situation
- PR 163 (getCacheDir helper, curator-viewer) - Gideon's, also open

v0.1.11 shipped earlier in the week and is stable. 0.1.12 scope is being finalized now.

## Stability read

Both reverts were caught quickly, hours not days, which is the best we can do given that neither regression was detectable before it ran against real data. The counter-gating lesson from the Dec 10 incident is the clearest actionable thing to come out of this week. Once that's encoded as a hard gate, the batch auto-delete feature can be re-approached without the same risk.

No ongoing instability in the services I own (bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations). Pipeline is stable at v0.1.11.

## Open items into next week

- [ ] PR 244 review and merge (blocking 0.1.12)
- [ ] 0.1.12 scope decision: which of the stale PRs land, which defer to a later cut
- [ ] Gideon's postmortem for the Dec 4 retry revert - not published yet, need to follow up with him on timing
- [ ] counter-gating design for batch auto-delete re-implementation (TBD who owns this, not me)
