# t3.r2.l_model_gideon — clue for t3.r2 (Batch job status persistence across process restarts)

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

**Planted by phase 3 as**   gideon, slack, 2025-04-07, #pipeline
**Meant to settle**         gideon saw cost accounting go 10x wrong because a resumed job's model differed from the configured one
**So a reader concludes**   A persisted batch job may only be picked back up if the model name in the current config is the same one the job was submitted with, which means the model has to be recorded alongside the job id.
**Covers**                  rule
**Names that must appear**  —
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> the cost counter after a resume prices everything at whatever model the current config says, while the responses are coming back from whatever the job was actually submitted with. saw it come out about 10x off. we are going to get an issue filed about that number and I have nothing good to say.

## Piece by piece

- [x] the cost counter after a resume prices everything at whatever model the current config says
- [x] the responses are coming back from whatever model the job was actually submitted with
- [x] he saw it come out about 10x off
- [x] an issue is going to get filed about that reported cost number
- [x] he has nothing good to say about that reported number

## What was actually said

**Gideon Halloway**, 2025-04-07, #pipeline

> it did. The cost counter prices everything at whatever model the current config says at resume time, but the responses come back from whatever the job was originally submitted with. That's the 10x. It's not related to what the batch fixes touched, it's its own thing in the resume path.

## In context

```
12:28  emil      not convinced gideon's case is in scope for ws-050, honestly.
12:28  gideon    Ya
12:55  gideon    it did. The cost counter prices everything at whatever model the current config says at    <-- the clue
12:55  gideon    Someone is going to file an issue on that reported cost number and I have nothing good t
12:59  dario     - *ws-050*: gideon's case is confirmed as a resume path issue, the cost counter pricing 
```
