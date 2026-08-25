# t3.r2.l_beh_gideon — clue for t3.r2 (Batch job status persistence across process restarts)

## The task it serves — t3

**The agent is told:** Ensure that if a Python process running a `batch=True` job is killed and restarted while a batch job is still pending on the provider's side, re-running the same script resumes polling the existing batch job instead of submitting a duplicate one.

### The hidden requirement — t3.r2

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | On restart, before resuming an existing batch job ID, the code must verify the persisted job's provider, model name, and request payload hash still match the current run's configuration; a mismatch must cause a fresh submission rather than resuming a stale/incompatible job. | — |
| scope | Resume-time validation. | — |
| failure_behavior | Mismatch causes a fresh submission with a logged reason for why the old job was not resumed, not a silent resume of incompatible results. | **carries this** |

This clue is one of several that build to: *When any of those no longer line up, the run submits a brand new batch job and logs why the stored one was not reused, rather than aborting or resuming quietly.*

---

**Planted by phase 3 as**   gideon, slack, 2025-02-14, #engineering
**Meant to settle**         gideon wants the reason for not reusing a stored job logged where the user sees it
**So a reader concludes**   When any of those no longer line up, the run submits a brand new batch job and logs why the stored one was not reused, rather than aborting or resuming quietly.
**Covers**                  failure_behavior
**Names that must appear**  —
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> whatever we do about reusing pending jobs, say why on the line where we skip one. today the only trace of a resume is the id at DEBUG level, and "resumed 1 pending batch job" with no reason attached is exactly how I burned an afternoon last month. one INFO line naming what didn't line up would have saved all of it.

## Piece by piece

- [x] the situation is reusing (or not reusing) a pending/stored batch job on resume
- [x] currently only the job id is logged, at DEBUG level
- [x] the message 'resumed 1 pending batch job' gives no reason for what didn't match
- [x] this caused Gideon to lose an afternoon last month
- [x] what should happen instead: log the reason at INFO level on the skip line

## What was actually said

**Gideon Halloway**, 2025-02-14, #engineering

> Separate thing I want to settle before end of day: when we skip a pending batch job on resume, can we log the reason at INFO, not just the id at DEBUG? "resumed 1 pending batch job" with nothing explaining what didn't match is how I lost an afternoon last month.

## In context

```
10:16  gideon    Is it all image inputs or specific formats?
10:50  dermot    I've been cross-referencing the anthropic vision docs on image content block types, ther
11:26  gideon    Separate thing I want to settle before end of day: when we skip a pending batch job on r   <-- the clue
11:34  emil      Fair point, that's a frustrating way to lose time.
11:35  emil      Are they failing outright or just behaving differently?
```
