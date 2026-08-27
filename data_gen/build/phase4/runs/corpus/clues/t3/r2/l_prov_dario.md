# t3.r2.l_prov_dario — clue for t3.r2 (Batch job status persistence across process restarts)

## The task it serves — t3

**The agent is told:** Ensure that if a Python process running a `batch=True` job is killed and restarted while a batch job is still pending on the provider's side, re-running the same script resumes polling the existing batch job instead of submitting a duplicate one.

### The hidden requirement — t3.r2

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | On restart, before resuming an existing batch job ID, the code must verify the persisted job's provider, model name, and request payload hash still match the current run's configuration; a mismatch must cause a fresh submission rather than resuming a stale/incompatible job. | **carries this** |
| scope | Resume-time validation. | — |
| failure_behavior | Mismatch causes a fresh submission with a logged reason for why the old job was not resumed, not a silent resume of incompatible results. | — |

This clue is one of several that build to: *A persisted batch job may only be picked back up if the provider/backend it was submitted against is the same one the current run is configured for.*

---

**Planted by phase 3 as**   dario, slack, 2025-04-18, #incidents
**Meant to settle**         dario saw a restarted run resume a job submitted under a different provider
**So a reader concludes**   A persisted batch job may only be picked back up if the provider/backend it was submitted against is the same one the current run is configured for.
**Covers**                  rule
**Names that must appear**  —
**Status**                  carried  (attempt 1)

> **LEAKED** — giveaway language reached the transcript: fingerprint. The clue landed, but saying this much states the hidden requirement outright and makes the task trivial. Worth re-running even though the gate passed.

## What phase 3 wrote

> heads up, I killed a run mid-batch, flipped the backend from openai to anthropic in the same script and reran, and it went straight back to polling the openai batch id from the first attempt. only spotted it because the id in the log still had the openai shape on it.

## Piece by piece

- [x] killed a run mid-batch
- [x] switched backend from openai to anthropic in the same script
- [x] reran it
- [x] it resumed polling the openai batch id from the first attempt
- [x] he only noticed because the id in the log still had the openai shape

## What was actually said

**Dario Kestrel**, 2025-04-18, #incidents

> Actually I hit something related - killed a run mid-batch, switched the backend from openai to anthropic in the same script, reran, and it went straight back to polling the openai batch id from the first attempt.

## In context

```
10:58  dario     Do you know if Konrad had the same provider set both times, or did anything change betwe
11:10  nikolai   dunno, I'd have to check with Konrad
11:24  dario     Actually I hit something related - killed a run mid-batch, switched the backend from ope   <-- the clue
11:24  dario     only spotted it because the id in the log still had the openai shape on it
12:03  nikolai   So the provider name is in the fingerprint but it's not actually being used to key the c
```
