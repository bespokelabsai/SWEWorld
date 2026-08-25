---
title: "Postmortem: Dec 4 revert of end-of-run retry logic"
author: gideon
created_at: 2024-12-05T09:14:00+00:00
---

# Postmortem: Dec 4 Revert of End-of-Run Retry Logic

Dec 5 2024. Written by Gideon Halloway.

---

## What Happened

On Dec 4 we reverted a change to the retry logic in online-request-processing. The retry block was re-entering the asyncio event loop after a run had already finished, causing the processor to take a second pass over completed requests. That second pass occasionally re-submitted requests that had already settled, producing duplicate cost entries downstream.

The revert was clean and is confirmed stable as of this morning.

## Impact

- Duplicate cost entries created during the window the bad logic was live
- Affected only runs that hit the retry path at or near completion (not every run)
- Exact count of affected runs and duplicate entries: I do not have this yet, need whoever owns the billing/cost dashboard to pull the numbers for the window the bad code was deployed
- No data loss, no requests dropped, no auth or session impact that I am aware of

## Timeline

The exact deploy and revert timestamps are approximate here, I am reconstructing from memory and should verify against deploy logs.

- Dec 3, sometime in the afternoon: retry logic merged into online-request-processing
- Dec 4, morning: first reports of duplicate cost entries
- Dec 4, mid-morning: root cause identified as double-spin in the asyncio event loop
- Dec 4, afternoon: revert merged and deployed
- Dec 4, end of day: duplicate entries confirmed stopped; no new incidents reported overnight

TBD: actual timestamps from CI/CD logs. Someone on the infra side would have those.

## Root Cause

The retry block was keying its scheduling decision off the raw response error code, not the run's completion state. So when a run finished but the final response carried a retriable error code (which is a legitimate combination), the retry logic would schedule another attempt. That attempt re-entered the asyncio event loop after the run's completion flag had already been set.

The problem is that nothing gated the retry on whether the run was actually done. The completion flag existed and was being set correctly; the retry path simply was not consulting it.

PR 202 is the fix. It adds an explicit check against run state before scheduling any retry, so a completed run cannot be re-queued regardless of the error code on the last response.

A secondary issue that contributed: the asyncio loop lifecycle was not confirmed closed before cleanup callbacks fired. I want to be careful here because honestly this is the part I am less certain about mechanically. My understanding is that the cleanup callbacks ran while the loop was still technically schedulable, which is what made the re-entry possible in the first place. Need to confirm this with whoever owns the asyncio plumbing in this service before we write it into guidance.

## What Went Well

- Revert was straightforward, no partial state to unwind
- Root cause was identified the same day without a lot of back-and-forth
- PR 202 addresses the direct cause and is already in

## What Changes

**Immediate rule for retry paths:** any retry logic that touches end-of-run state must gate on the completion flag explicitly, not on the response error code alone. The error code is not a reliable proxy for run state.

**asyncio loop lifecycle:** before any cleanup callbacks fire, the loop should be confirmed closed. I am not confident I know exactly what that enforcement looks like in practice, this needs a short design note from whoever owns that layer.

## Action Items

- [ ] Pull duplicate cost entry count for Dec 3-4 from the billing dashboard (need someone with access, not me)
- [ ] Verify timeline timestamps against deploy logs
- [ ] Write short guidance note on retry path requirements (completion flag gate) to live somewhere in the engineering wiki under online-request-processing
- [ ] Follow up on asyncio loop lifecycle enforcement, needs input from whoever owns that part of the service
- [ ] Audit other retry paths in online-request-processing for the same pattern (I can do this pass but it will take a day or two)

## Open Questions

- How many runs were actually affected? And of those, how many produced duplicates vs. how many hit the retry path but did not re-submit? The distinction matters for assessing blast radius.
- Are duplicate cost entries being corrected, and if so, how? That is outside what I own.
- Is there a test we could have written that would have caught this before merge? My instinct is yes, something that exercises the retry path with the completion flag already set. Worth discussing before PR 202 closes if it hasnt already.
