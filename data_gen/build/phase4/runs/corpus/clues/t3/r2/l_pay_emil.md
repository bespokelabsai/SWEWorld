# t3.r2.l_pay_emil — clue for t3.r2 (Batch job status persistence across process restarts)

## The task it serves — t3

**The agent is told:** Ensure that if a Python process running a `batch=True` job is killed and restarted while a batch job is still pending on the provider's side, re-running the same script resumes polling the existing batch job instead of submitting a duplicate one.

### The hidden requirement — t3.r2

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | On restart, before resuming an existing batch job ID, the code must verify the persisted job's provider, model name, and request payload hash still match the current run's configuration; a mismatch must cause a fresh submission rather than resuming a stale/incompatible job. | **carries this** |
| scope | Resume-time validation. | — |
| failure_behavior | Mismatch causes a fresh submission with a logged reason for why the old job was not resumed, not a silent resume of incompatible results. | — |

This clue is one of several that build to: *A persisted batch job may only be picked back up if the requests the run would send now are the same as the ones the job was submitted with, compared as a hash of the request payloads rather than by run directory or row count.*

---

**Planted by phase 3 as**   emil, slack, 2025-03-26, #pipeline
**Meant to settle**         emil got results for old prompts after editing the prompt function and restarting
**So a reader concludes**   A persisted batch job may only be picked back up if the requests the run would send now are the same as the ones the job was submitted with, compared as a hash of the request payloads rather than by run directory or row count.
**Covers**                  rule
**Names that must appear**  —
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> this one is nastier. I rewrote the prompt function, ctrl-C'd, reran, and got completions for the old prompts back with zero complaint. the request jsonl sitting on disk was the new one, the job on the provider side was the old one, and nobody compared the two.

## Piece by piece

- [x] he rewrote the prompt function and then ctrl-C'd and reran
- [x] he got completions back for the old prompts
- [x] the system gave no complaint or warning about the mismatch
- [x] the request jsonl on disk already reflected the new version
- [x] the job on the provider side was still the old one
- [x] nobody compared the two to catch the mismatch

## What was actually said

**Emil Brandvold**, 2025-03-26, #pipeline

> Something nastier on the resume side: I rewrote the prompt function, ctrl-C'd, reran, and got completions for the old prompts back with zero complaint. The request jsonl on disk was already the new version, the job on the provider side was the old one, and nobody compared the two.

## In context

```
10:05  gideon    has anyone seen WS-047 actually written up somewhere? I can't find it in the issues
10:47  gideon    Is there a test for Mistral batch cost tracking anywhere, or is that still a gap?
11:10  emil      Something nastier on the resume side: I rewrote the prompt function, ctrl-C'd, reran, an   <-- the clue
11:38  dario     I'd lean toward calling that a correctness bug, not just a resume edge case. You're gett
11:56  emil      Has anyone done more than a quick pass on PR 604 to confirm it's not touching the cachin
```
