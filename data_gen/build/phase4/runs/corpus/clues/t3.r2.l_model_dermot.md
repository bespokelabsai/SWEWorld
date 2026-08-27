# t3.r2.l_model_dermot — clue for t3.r2 (Batch job status persistence across process restarts)

## The task it serves — t3

**The agent is told:** Ensure that if a Python process running a `batch=True` job is killed and restarted while a batch job is still pending on the provider's side, re-running the same script resumes polling the existing batch job instead of submitting a duplicate one.

### The hidden requirement — t3.r2

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | On restart, before resuming an existing batch job ID, the code must verify the persisted job's provider, model name, and request payload hash still match the current run's configuration; a mismatch must cause a fresh submission rather than resuming a stale/incompatible job. | **carries this** |
| scope | Resume-time validation. | — |
| failure_behavior | Mismatch causes a fresh submission with a logged reason for why the old job was not resumed, not a silent resume of incompatible results. | — |

This clue is one of several that build to: *A persisted batch job may only be picked back up if the model name in the current config is the same one the job was submitted with, which means the model has to be recorded alongside the job id.*

---

**Planted by phase 3 as**   dermot, slack, 2025-04-16, #cookbooks
**Meant to settle**         dermot got outputs from the old model after editing the model name and restarting
**So a reader concludes**   A persisted batch job may only be picked back up if the model name in the current config is the same one the job was submitted with, which means the model has to be recorded alongside the job id.
**Covers**                  rule
**Names that must appear**  gpt-4o-mini, gpt-4o
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> lost most of an afternoon on this. bumped the example from gpt-4o-mini to gpt-4o, killed the run because I fat-fingered the output path, reran, and the dataset that came out was plainly mini text. the batch id it resumed was the one from before the edit.

## Piece by piece

- [x] Dermot lost most of an afternoon on this
- [x] he bumped the example from gpt-4o-mini to gpt-4o
- [x] he killed the run because he fat-fingered the output path
- [x] he reran it
- [x] the dataset that came out was plainly mini text
- [x] the batch id it resumed was the one from before the edit

## What was actually said

**Dermot Callaghan**, 2025-04-16, #cookbooks

> sorry, I wasn't clear enough on this earlier - I had the example on gpt-4o-mini, edited it to gpt-4o, killed the run when I fat-fingered the output path, restarted, and the dataset that came back was plainly mini. resume picked up the batch id from before the edit.

## In context

```
14:48  nikolai   sent Re: Docker code executor image pinning to Emil, Dario, and Dermot, flagged the back
14:48  nikolai   will look at what the sandbox repo actually publishes this afternoon
14:51  dermot    sorry, I wasn't clear enough on this earlier - I had the example on gpt-4o-mini, edited    <-- the clue
14:51  dermot    lost most of an afternoon on this
```
