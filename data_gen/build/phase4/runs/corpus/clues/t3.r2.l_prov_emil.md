# t3.r2.l_prov_emil — clue for t3.r2 (Batch job status persistence across process restarts)

## The task it serves — t3

**The agent is told:** Ensure that if a Python process running a `batch=True` job is killed and restarted while a batch job is still pending on the provider's side, re-running the same script resumes polling the existing batch job instead of submitting a duplicate one.

### The hidden requirement — t3.r2

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | On restart, before resuming an existing batch job ID, the code must verify the persisted job's provider, model name, and request payload hash still match the current run's configuration; a mismatch must cause a fresh submission rather than resuming a stale/incompatible job. | **carries this** |
| scope | Resume-time validation. | **carries this** |
| failure_behavior | Mismatch causes a fresh submission with a logged reason for why the old job was not resumed, not a silent resume of incompatible results. | — |

This clue is one of several that build to: *A persisted batch job may only be picked back up if the provider/backend it was submitted against is the same one the current run is configured for.*

---

**Planted by phase 3 as**   emil, slack, 2025-04-02, #code-review
**Meant to settle**         emil hit a 404 polling loop because the stored job id was reused across two backends
**So a reader concludes**   A persisted batch job may only be picked back up if the provider/backend it was submitted against is the same one the current run is configured for.
**Covers**                  rule, scope
**Names that must appear**  —
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> related annoyance: the pending job id gets parked in the run dir keyed off the dataset only, so the plain openai path and the azure deployment of the same model land in the same slot. moved a cookbook over to azure last week, the restart polled a job that endpoint doesn't own and I sat in a 404 retry loop for twenty minutes before giving up and wiping the dir by hand.

## Piece by piece

- [x] The pending job ID is stored in the run dir keyed only off the dataset, with no backend distinction
- [x] As a result the plain openai path and an azure deployment of the same model share the same slot
- [x] He moved a cookbook to azure last week
- [x] On restart it polled a job the openai endpoint doesn't own
- [x] It sat in a 404 retry loop for twenty minutes
- [x] He had to wipe the run dir by hand to recover

## What was actually said

**Emil Brandvold**, 2025-04-02, #code-review

> moved a cookbook to azure last week, the restart polled a job the openai endpoint doesn't own, sat in a 404 retry loop for twenty minutes before giving up and wiping the dir by hand

## In context

```
11:57  emil      Moved a cookbook to azure last week and the restart polled a job the openai endpoint doe
11:58  emil      related annoyance: the pending job id gets parked in the run dir keyed off the dataset o
11:58  emil      moved a cookbook to azure last week, the restart polled a job the openai endpoint doesn'   <-- the clue
12:11  emil      Does the job ID scoping fix belong in PR 615 or should it go in its own PR?
15:11  dermot    sorry, been in a call - so the 404 loop was the job id not scoped per backend, that's se
```
