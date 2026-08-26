# t3.r2.l_beh_dermot — clue for t3.r2 (Batch job status persistence across process restarts)

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

**Planted by phase 3 as**   dermot, slack, 2025-04-21, #pipeline
**Meant to settle**         dermot wants a fresh submission rather than reuse when the stored job does not match the current run
**So a reader concludes**   When any of those no longer line up, the run submits a brand new batch job and logs why the stored one was not reused, rather than aborting or resuming quietly.
**Covers**                  failure_behavior
**Names that must appear**  —
**Status**                  carried  (attempt 1)

> **LEAKED** — giveaway language reached the transcript: mismatch. The clue landed, but saying this much states the hidden requirement outright and makes the task trivial. Worth re-running even though the gate passed.

## What phase 3 wrote

> my take after this week: if the job sitting on the provider isn't the job we would send today, just send a new one and eat the 24h and the money. a duplicate batch costs us a few dollars, handing someone a dataset that quietly blends two configs costs us their trust.

## Piece by piece

- [x] if the stored job doesn't match what we'd send today, we submit a new one
- [x] we accept the 24h wait
- [x] we accept the extra money cost
- [x] a duplicate batch costs only a few dollars
- [x] handing someone a dataset that blends two configs costs trust

## What was actually said

**Dermot Callaghan**, 2025-04-21, #pipeline

> if the stored job doesn't match what we'd send today, I think we just submit a new one and eat the 24h and the cost

## In context

```
09:00  dermot    been thinking about the job-reuse question this week
09:00  dermot    if the stored job doesn't match what we'd send today, I think we just submit a new one a   <-- the clue
09:00  dermot    a duplicate batch is a few dollars; a dataset that quietly blends two configs is a trust
09:43  gideon    i think that's right for a full mismatch, but do we have a clear definition of what "doe
```
