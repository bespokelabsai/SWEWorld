# t1.r1.l_unhash_2 — clue for t1.r1 (Prompt-level response cache keying)

## The task it serves — t1

**The agent is told:** Add a `cache_stats()` method to `curator.LLM` that reports how many of the last run's requests were served from the local cache versus sent to the backend, so users can gauge how much a re-run will cost before running it.

### The hidden requirement — t1.r1

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | The cache key used to look up a prior response must be derived from the exact tuple of (rendered prompt text, model_name, response_format schema, and generation_params) — not from the raw input row alone. | — |
| scope | Applies to every request path that already calls the existing cache-lookup helper, including batch and online modes. | — |
| exclusions_or_crossover | Two rows that render to an identical prompt string but differ only in fields unused by `prompt()` must be counted as the same cache entry, not treated as separate misses. | — |
| failure_behavior | If `response_format` cannot be hashed (e.g. a dynamically constructed Pydantic model), the row must be treated as a guaranteed cache miss rather than raising. | **carries this** |
| observability | `cache_stats()` must expose a `hit_rate` float and a `misses` int that together account for 100% of processed rows. | — |

This clue is one of several that build to: *When the response_format cannot be hashed, the row has to fall through as a plain miss and go to the backend instead of raising and killing the run.*

---

**Planted by phase 3 as**   dermot, slack, 2025-03-26, #help
**Meant to settle**         the team agrees people are already patching around the exception to get runs through
**So a reader concludes**   When the response_format cannot be hashed, the row has to fall through as a plain miss and go to the backend instead of raising and killing the run.
**Covers**                  failure_behavior
**Names that must appear**  try/except
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> I wrapped that call in a try/except locally to get the demo dataset out for the Friday cut and I have been carrying the patch since. Not shipping it, but I am also not deleting it, which tells you something.

## Piece by piece

- [x] the call was wrapped in a try/except
- [x] the wrapping was done locally
- [x] the purpose was to get the demo dataset through
- [x] this was for the Friday cut
- [x] he has been carrying the patch since then
- [x] he has not shipped it
- [x] he has also not deleted it
- [x] that fact (not shipped, not deleted) says something about the state of things

## What was actually said

**Dermot Callaghan**, 2025-03-26, #help

> for what it's worth, I've had a try/except wrapped around that call since the friday cut, just to get the demo dataset through

## In context

```
09:36  dermot    that's the unknown-capability case biting us already. if we don't know what the server s
09:36  gideon    so the check is hard-blocking even when it just can't tell?
10:08  dermot    for what it's worth, I've had a try/except wrapped around that call since the friday cut   <-- the clue
10:08  dermot    done locally, on my own branch, not shipped anywhere
10:08  dermot    I haven't shipped it and I haven't deleted it either, which tells you something about wh
```
