# t3.r2.l_prov_gideon — clue for t3.r2 (Batch job status persistence across process restarts)

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

**Planted by phase 3 as**   gideon, slack, 2025-04-14, #viewer
**Meant to settle**         gideon saw a resumed job whose provider disagreed with the configured one, breaking the cost table
**So a reader concludes**   A persisted batch job may only be picked back up if the provider/backend it was submitted against is the same one the current run is configured for.
**Covers**                  rule
**Names that must appear**  —
**Status**                  carried  (attempt 1)

> **LEAKED** — giveaway language reached the transcript: mismatch. The clue landed, but saying this much states the hidden requirement outright and makes the task trivial. Worth re-running even though the gate passed.

## What phase 3 wrote

> got a weird one in the summary table after a restart: header said the run was on gemini, the batch object we were tracking was clearly a mistral one, and the cost column came out as gibberish because the token fields didn't line up. I can make the table defensive but the thing feeding it is wrong.

## Piece by piece

- [x] header said the run was on gemini
- [x] the batch object being tracked was clearly mistral
- [x] the cost column came out as gibberish
- [x] the token fields didn't line up, causing that
- [x] this happened after a restart
- [x] he could make the table defensive
- [x] but the thing feeding it the wrong info is the real problem

## What was actually said

**Gideon Halloway**, 2025-04-14, #viewer

> Also ran into something weird after a restart: the summary table header said the run was on gemini but the batch object we were tracking was clearly mistral, so the cost column came out as gibberish because the token fields didn't line up

## In context

```
09:00  gideon    PR 631 is in for review, it's the projected total and remaining work, and I think it's c
09:00  gideon    Also ran into something weird after a restart: the summary table header said the run was   <-- the clue
09:00  gideon    I can make the table defensive but whatever is feeding it the wrong provider info is the
09:41  dermot    I can take PR 631, does anyone have eyes on PR 632 from the viewer side yet?
```
