# t3.r2.l_pay_dario — clue for t3.r2 (Batch job status persistence across process restarts)

## The task it serves — t3

**The agent is told:** Ensure that if a Python process running a `batch=True` job is killed and restarted while a batch job is still pending on the provider's side, re-running the same script resumes polling the existing batch job instead of submitting a duplicate one.

### The hidden requirement — t3.r2

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | On restart, before resuming an existing batch job ID, the code must verify the persisted job's provider, model name, and request payload hash still match the current run's configuration; a mismatch must cause a fresh submission rather than resuming a stale/incompatible job. | **carries this** |
| scope | Resume-time validation. | **carries this** |
| failure_behavior | Mismatch causes a fresh submission with a logged reason for why the old job was not resumed, not a silent resume of incompatible results. | — |

This clue is one of several that build to: *A persisted batch job may only be picked back up if the requests the run would send now are the same as the ones the job was submitted with, compared as a hash of the request payloads rather than by run directory or row count.*

---

**Planted by phase 3 as**   dario, slack, 2025-02-05, #help
**Meant to settle**         dario had sampling-parameter changes ignored on resume, and notes the batch path never digests request bodies
**So a reader concludes**   A persisted batch job may only be picked back up if the requests the run would send now are the same as the ones the job was submitted with, compared as a hash of the request payloads rather than by run directory or row count.
**Covers**                  rule, scope
**Names that must appear**  max_tokens
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> and it is not just the prompt text. same prompts, I bumped temperature and max_tokens for an ablation, restarted, and it happily resumed the earlier job, so my two arms of the ablation were the identical settings twice.

## Piece by piece

- [x] changes were sampling parameters (temperature and max_tokens), not the prompt text
- [x] he restarted the run
- [x] it resumed the earlier job instead of applying the new settings
- [x] as a result both arms of his ablation ended up with identical settings
- [x] the batch path never even parses the request body

## What was actually said

**Dario Kestrel**, 2025-02-05, #help

> mine was resume specifically - same prompts, I bumped temperature and max_tokens for an ablation, restarted, and it just picked up the old run with the original settings

## In context

```
13:52  dermot    does anyone know if the seed is factored into the cache key at all?
14:18  dario     nice call on landing it as a genuine bug
14:18  dario     mine was resume specifically - same prompts, I bumped temperature and max_tokens for an    <-- the clue
14:18  dario     and both arms ended up on identical settings since it just resumed the old ones
14:26  dario     also wondering if the batch path is even part of this, i don't think it reads the reques
```
