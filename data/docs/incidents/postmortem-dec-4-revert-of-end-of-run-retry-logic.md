---
title: "Postmortem: Dec 4 Revert of End-of-Run Retry Logic"
author: gideon
created_at: 2024-12-05T09:00:00+00:00
---

# Postmortem: Dec 4 Revert of End-of-Run Retry Logic

**Date of incident:** Dec 4, 2024
**Resolved:** same day, via revert
**Status:** open action items (see below)

---

## What happened

The end-of-run retry logic, which was meant to catch requests that stalled or timed out before a run completed, started re-queuing requests that had already finished successfully. On resume, any request that had not explicitly set itself to exhausted was treated as eligible for retry, regardless of whether a cache entry had already been written for it. So basically, completed requests got re-entered into the queue, ran again, and produced duplicate completions.

The immediate visible effect was inflated token counts in cost tracking. The retry logs themselves showed nothing obviously wrong because they were missing the fields that would have made the duplicates visible (more on that below).

We reverted on Dec 4 once the cost anomalies were traced back to the retry path.

---

## Impact

- Duplicate completions for an unknown number of requests during affected resume windows. I dont have a count yet, need whoever owns the cost dashboard to pull the exact figure for the impact window.
- Token counts in cost tracking were inflated. The magnitude depends on how many resumes happened between the deploy and the revert, which I'm also not certain of.
- No user-facing errors. Completions that were already cached were served correctly; the duplicates were happening behind the cache layer.

---

## Timeline

- Dec 3 or so: retry logic deployed (I'd want to confirm the exact deploy time from the deploy log)
- Dec 4: cost anomalies flagged, traced to retry path
- Dec 4: reverted

---

## Root cause

The retry eligibility check did not consult cache state. It was essentially: if this request is not marked exhausted, it can be retried. That logic is fine in the steady state where exhausted gets set reliably, but on resume the transition was not guaranteed, so requests that had completed and written a cache entry could still look eligible.

The fix gates retry eligibility on a cache lookup. If a cache entry exists for the request, it is skipped, regardless of the exhausted flag.

The reason this was not caught during review: retry events were logged without failure reason or outcome fields. There was also no request id or attempt number on these events. So when duplicates were happening, the retry log looked normal, and the signal only appeared in cost aggregates downstream. If the events had included outcome, the duplicate completions would have been visible directly in the logs rather than requiring a trace back from cost anomalies.

---

## What went well

- Cost tracking caught this. Honestly though, it was the right place to catch it given the logging gaps, but it's also the slowest possible detection path. Worth noting that without that anomaly surfacing when it did, this could have run longer.
- Revert was straightforward once the cause was identified. No complicated rollback, no schema migration, just reverting the retry path.

---

## Action items

- [ ] Add request id, attempt number, failure reason, and outcome to retry and timeout events. This is the main thing. Without these fields, this class of issue is invisible at the event level.
- [ ] Confirm exact impact window (deploys to revert) and get a count of affected requests from cost dashboard. TBD on who owns that, I'd check with whoever triaged the cost anomaly.
- [ ] Review whether the exhausted flag is being set reliably in all exit paths, or if there are other places where completed requests could look eligible under the current (post-fix) logic. I'm not fully confident the cache lookup covers every edge case here.

---

## Open questions

- Are there other places in the retry path that assume exhausted is a reliable signal, where a similar gap could exist?
- What is the right detection latency target for this kind of issue? Cost aggregates are slow. If retry logs had the fields they needed, we'd catch it faster, but I don't know if there's a monitoring expectation I should be writing against.
