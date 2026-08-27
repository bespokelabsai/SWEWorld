---
title: "Dec 4 Revert: End-of-Run Retry Logic"
author: gideon
created_at: 2024-12-16T10:17:00+00:00
---

# Dec 4 Revert: End-of-Run Retry Logic

Postmortem for the revert of end-of-run retry logic merged to the request pipeline on December 3. The change was reverted on December 4 after it produced unexpected behavior in production. This document covers what happened, why we reverted, and what has to be true before we try again.

## Impact

- Affected: request pipeline in production, specifically the retry pass that runs after a batch exhausts its primary processing loop
- Duration: approximately 14 hours between deploy (Dec 3, ~6pm) and revert (Dec 4, ~8am)
- Observed symptoms:
  - Requests that had already succeeded were re-entering the retry queue and being processed a second time (not all of them, but enough to be visible)
  - Some downstream consumers received duplicate events during that window
  - No data loss detected, but duplicate delivery is a contract violation for at least two consumers (need to confirm which ones with whoever owns the consumer registry)
- User-facing impact: honestly unclear. The duplicates were caught by monitoring before any escalation came in, so I do not have a clean count of how many actually reached end users vs. were absorbed somewhere downstream.

## Timeline

```
Dec 3, ~6:00pm  - end-of-run retry logic merged and deployed to production
Dec 3, ~9:30pm  - first alert fires: anomalous retry queue depth
Dec 3, ~9:45pm  - on-call investigates, initially attributed to a spike in upstream volume
Dec 4, ~7:15am  - duplicate events confirmed by downstream consumer team
Dec 4, ~7:50am  - decision made to revert
Dec 4, ~8:10am  - revert deployed, queue depth returns to baseline within ~20 minutes
```

Gaps I could not reconstruct: I do not know exactly when the retry queue alert was acknowledged or whether any action was taken overnight between ~10pm and 7am. The on-call log from that window would clarify this.

## Root Cause

The retry logic was designed to trigger at end-of-run for any request that had not reached a terminal state. The problem is that "not terminal" was evaluated against a status field that is written asynchronously. There is a window, sometimes several seconds wide, between when a request completes successfully and when that status is flushed to the store the retry pass reads from.

During that window, a completed request looks like a candidate for retry. Under normal conditions this window is narrow enough that the retry pass would not catch many of these. Under the load profile on Dec 3 evening, the flush lag widened and the retry pass picked up a significant number of already-complete requests.

This is a pre-existing gap in the design, not something introduced by the retry logic itself. The retry logic made the gap consequential for the first time.

## What Went Well

- The retry queue depth alert fired within a few hours, and the signal was real (not noise)
- Reverting was straightforward. The change was self-contained enough that the revert did not pull in anything unrelated, and deploy time was short
- No data corruption, only duplicates

## What Did Not Go Well

- The async flush lag was not identified during review. Honestly, I think this is partly because the status write path is not well documented and the latency characteristics under load are not visible anywhere obvious.
- The initial overnight investigation did not reach a conclusion. We lost several hours that way.
- We do not have a good way right now to distinguish "request that has not yet completed" from "request that completed but has not yet been written as complete." The retry logic could not have made the right call even with more careful implementation, because the information it needed was not reliably available.

## Open Questions

- Which downstream consumers were affected by duplicate delivery, and do any of them have non-idempotent processing? (I would ask whoever maintains the consumer registry, I do not know who that is right now)
- What is the actual p99 flush lag under production load? I do not have this number. It needs to come from whoever owns the status write pipeline metrics.
- Was anything done during the overnight window between the first alert and the morning escalation? The on-call log should say.

## Action Items

- [ ] Add observability for status flush lag, specifically a metric that makes the window between completion and status write visible at scale. Without this we cannot safely reintroduce any retry logic that depends on terminal-state detection. (who owns the status write pipeline? need to find out before assigning this)
- [ ] Document the re-introduction conditions for end-of-run retry before any re-implementation work starts. My current thinking is that the retry pass needs to read from a source that is either synchronously consistent or includes a "written-at" timestamp we can use to exclude recently-completed records, but I want to discuss this with the pipeline team before committing to an approach.
- [ ] Clarify on-call handoff expectations for anomalous-but-not-critical alerts overnight. The gap between 10pm and 7am suggests the process either did not escalate when it should have, or escalated and got no response, and I do not know which.
- [ ] Confirm whether duplicate events from the impact window need any remediation with affected consumers, or whether idempotency downstream absorbed them.

## Re-Introduction Conditions

This section is a placeholder. I want to write this out properly once I have the flush lag data and have talked through the design with the pipeline team. Right now I would not reintroduce end-of-run retry in any form until at least the observability item above is done. The gap between completion and status write has to be measurable before we can make any sensible claim about whether a retry candidate is actually incomplete.

TBD, targeting a follow-up discussion before end of December.
