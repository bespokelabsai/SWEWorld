# t3.r2.l_beh_emil — clue for t3.r2 (Batch job status persistence across process restarts)

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

**Planted by phase 3 as**   emil, slack, 2025-04-29, #general
**Meant to settle**         emil rules out aborting the run when the stored job cannot be reused
**So a reader concludes**   When any of those no longer line up, the run submits a brand new batch job and logs why the stored one was not reused, rather than aborting or resuming quietly.
**Covers**                  failure_behavior
**Names that must appear**  —
**Status**                  carried  (attempt 1)

> **LEAKED** — giveaway language reached the transcript: mismatch. The clue landed, but saying this much states the hidden requirement outright and makes the task trivial. Worth re-running even though the gate passed.

## What phase 3 wrote

> I hacked a guard in locally that raised when the stored job looked off, ran it against a nightly, and it died at 3am four hours in. that is worse than what we have now for anyone running unattended. a job dying because someone touched the config is not a fix.

## Piece by piece

- [x] Emil ran a guard locally that raised on job mismatch
- [x] it killed a nightly run at 3am
- [x] that outcome is worse than current behavior for unattended runs
- [x] aborting when the stored job can't be reused is not a fix

## What was actually said

**Emil Brandvold**, 2025-04-29, #general

> I tested a guard locally that raised on job mismatch and it killed a nightly run at 3am, four hours in

## In context

```
16:44  dermot    I'm not totally sure that sync is needed, @Emil already said abort is the wrong call
17:23  nikolai   fair enough
18:06  emil      I tested a guard locally that raised on job mismatch and it killed a nightly run at 3am,   <-- the clue
18:06  emil      Aborting when the stored job can't be reused is not a fix
18:06  emil      So where does that leave the fallback behavior, is there any agreement on what we actual
```
