# t3.r2.l_pay_dermot — clue for t3.r2 (Batch job status persistence across process restarts)

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

**Planted by phase 3 as**   dermot, slack, 2025-01-14, #releases
**Meant to settle**         dermot got rows paired with the wrong answers because a resumed job's request set was smaller than the current one
**So a reader concludes**   A persisted batch job may only be picked back up if the requests the run would send now are the same as the ones the job was submitted with, compared as a hash of the request payloads rather than by run directory or row count.
**Covers**                  rule
**Names that must appear**  —
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> appending to the input dataset between restarts is a trap too. I added 200 rows to a 800 row set, restarted, resumed job came back with 800 results for 1000 requests and reassembly slotted them in by index. half the rows carried an answer to somebody else's question and it looked completely fine on inspection.

## Piece by piece

- [x] appending to the input dataset between restarts is a trap
- [x] 200 rows were added to an 800-row set
- [x] the job was restarted
- [x] the resumed job came back with 800 results for 1000 requests
- [x] reassembly slotted the results in by index
- [x] half the rows carried an answer to somebody else's question
- [x] it looked completely fine on inspection

## What was actually said

**Dermot Callaghan**, 2025-01-14, #releases

> "v0.1.15 is out" just went to the team. I also flagged in it that appending to the input dataset between restarts is a trap, I had 200 rows added to an 800-row set and the resumed job came back with 800 results for 1000 requests, reassembly slotted by index, and half the rows had somebody else's answer without any sign of it on inspection.

## In context

```
09:00  dermot    "v0.1.15 is out" just went to the team. I also flagged in it that appending to the input   <-- the clue
09:03  dermot    @emil where are the release notes for 0.1.15 at, and do they cover the caching-and-resum
09:16  nikolai   I'm around all day if you need me for anything on the release.
```
