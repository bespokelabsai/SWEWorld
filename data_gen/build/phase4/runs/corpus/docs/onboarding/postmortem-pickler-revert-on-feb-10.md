---
title: "Postmortem: pickler revert on Feb 10"
author: emil
created_at: 2025-02-11T09:14:00+00:00
---

# Postmortem: pickler revert on Feb 10

Merged change to the pickler introduced a cache-invalidation regression that caused silent data loss in resumed runs. Reverted Feb 10. Affected runs that were active across the change window need manual verification against output files.

## What happened

The pickler update was meant to make cache keys more stable. It had the opposite effect in one specific case: runs using resume where the generator function was touched between sessions.

Cache keys were derived from `inspect(func)` output, which includes comments and whitespace in the function source. Any cosmetic edit to a generator function, adding a comment, reformatting a line, produced a different hash. The cache entry from the previous session no longer matched, so rows that had already completed were treated as new and re-executed. In some runs this produced duplicates. In others, progress was dropped. Either way the run did not error, which is what made this hard to catch.

The failure mode only shows up in resume-across-code-change scenarios. Our test suite does not cover that boundary, so the regression passed review cleanly. Issue 124 on the repository documents the `inspect` sensitivity problem, but the pickler change was written without accounting for it.

## Timeline

```
~Feb 3-4  change merged; short test runs showed no issues
Feb 7     first report of unexpected re-execution on a longer batch run
Feb 9     root cause confirmed: inspect(func) sensitivity, traced to issue 124
Feb 10    revert merged; affected runs flagged for manual output check
```

## Impact

- Runs using resume that were active across the change window
    - some rows re-executed (duplicate output in some cases, lost progress in others)
    - no data corruption in the strict sense, but re-generation is not free
- Short runs and runs without any code changes between sessions: not affected
- The failure was silent, no error raised, which is the part i'm most concerned about going forward

I don't have a count of affected runs yet. Need to check with whoever is tracking active batch jobs for that window.

## Root cause

`inspect(func)` is whitespace- and comment-sensitive. The pickler change routed cache key generation through that output without stripping or normalizing it first. So a cache that should have survived a cosmetic code edit did not, and the run had no way to know it was starting over rather than continuing.

The sensitivity problem was already documented in issue 124. The connection between that issue and the pickler change was not made during review.

## What went well

- Issue 124 existed and gave us the root cause quickly once we knew where to look
- Revert was straightforward, no entanglement with other recent changes
- No data was corrupted, only re-generated (still a cost, but recoverable)

## Action items

- [ ] resume-across-code-change test case, before the pickler is touched again (this is the hard prerequisite)
- [ ] normalize function source before hashing: strip comments, collapse whitespace, then hash. issue 124 is the right place to track this
- [ ] manual output check for runs active Feb 3-10 that used resume
- [ ] decide whether the pickler work goes back into the queue once 124 is resolved, or waits for something else to force the issue

The normalization approach seems right to me but i'd want to see a proposal before we commit to it. If anyone has thoughts on what "strip and normalize" should look like in practice, lets circle back on that before the next attempt.

## Open questions

- How do we surface cache invalidation to the user? Right now a resumed run that starts over is indistinguishable from one that continues normally. That feels like a problem independent of this specific bug.
- Are there other places in the pickler that use `inspect` output? I haven't checked.
