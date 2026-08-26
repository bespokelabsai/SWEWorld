# t3.r2.l_model_emil — clue for t3.r2 (Batch job status persistence across process restarts)

## The task it serves — t3

**The agent is told:** Ensure that if a Python process running a `batch=True` job is killed and restarted while a batch job is still pending on the provider's side, re-running the same script resumes polling the existing batch job instead of submitting a duplicate one.

### The hidden requirement — t3.r2

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | On restart, before resuming an existing batch job ID, the code must verify the persisted job's provider, model name, and request payload hash still match the current run's configuration; a mismatch must cause a fresh submission rather than resuming a stale/incompatible job. | **carries this** |
| scope | Resume-time validation. | **carries this** |
| failure_behavior | Mismatch causes a fresh submission with a logged reason for why the old job was not resumed, not a silent resume of incompatible results. | — |

This clue is one of several that build to: *A persisted batch job may only be picked back up if the model name in the current config is the same one the job was submitted with, which means the model has to be recorded alongside the job id.*

---

**Planted by phase 3 as**   emil, slack, 2025-04-23, #pipeline
**Meant to settle**         emil notes the persisted job record does not include the model it was submitted with
**So a reader concludes**   A persisted batch job may only be picked back up if the model name in the current config is the same one the job was submitted with, which means the model has to be recorded alongside the job id.
**Covers**                  rule, scope
**Names that must appear**  —
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> the record we keep for a pending job is the id, the request file path and a timestamp. that is it. nothing on disk tells me which model it went out with, so when someone pastes me a run dir I genuinely cannot say whether picking it back up is safe or not. that has bitten me twice this week.

## Piece by piece

- [x] the pending job record stores only the id, the request file path, and a timestamp
- [x] that is the entire record, nothing else on it
- [x] the model the job was submitted with is not recorded anywhere on disk
- [x] when handed a run dir, Emil cannot tell what model it went out with
- [x] as a result, Emil cannot tell whether picking the job back up is safe
- [x] this gap has caused Emil concrete trouble twice this week

## What was actually said

**Emil Brandvold**, 2025-04-23, #pipeline

> Related: the persisted job record doesn't store the model either, just the id, the request file path, and a timestamp

## In context

```
13:16  dario     Honestly I don't have that count, and I'd lean toward not moving on this until we do.
14:33  gideon    Is there a way to pull that count from the cache store, or does it need instrumentation 
15:09  emil      Related: the persisted job record doesn't store the model either, just the id, the reque   <-- the clue
15:09  emil      and this isn't the first time either, it's bitten me twice this week
15:09  emil      that's the whole record, nothing else on it
```
