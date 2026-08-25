# t1.r1.l_scope_2 — clue for t1.r1 (Prompt-level response cache keying)

## The task it serves — t1

**The agent is told:** Add a `cache_stats()` method to `curator.LLM` that reports how many of the last run's requests were served from the local cache versus sent to the backend, so users can gauge how much a re-run will cost before running it.

### The hidden requirement — t1.r1

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | The cache key used to look up a prior response must be derived from the exact tuple of (rendered prompt text, model_name, response_format schema, and generation_params) — not from the raw input row alone. | — |
| scope | Applies to every request path that already calls the existing cache-lookup helper, including batch and online modes. | **carries this** |
| exclusions_or_crossover | Two rows that render to an identical prompt string but differ only in fields unused by `prompt()` must be counted as the same cache entry, not treated as separate misses. | — |
| failure_behavior | If `response_format` cannot be hashed (e.g. a dynamically constructed Pydantic model), the row must be treated as a guaranteed cache miss rather than raising. | — |
| observability | `cache_stats()` must expose a `hit_rate` float and a `misses` int that together account for 100% of processed rows. | **carries this** |

This clue is one of several that build to: *The change lands in the single shared lookup path, so it takes effect for batch submission and online requests alike rather than being special-cased per backend.*

---

**Planted by phase 3 as**   gideon, slack, 2025-02-21, #pipeline
**Meant to settle**         the team agrees batch-mode reuse behaviour is currently unverified and has regressed before
**So a reader concludes**   The change lands in the single shared lookup path, so it takes effect for batch submission and online requests alike rather than being special-cased per backend.
**Covers**                  scope, observability
**Names that must appear**  e2e
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> We only ever assert on reuse counts in the online tests. The batch e2e checks the reassembled output and nothing else, which is exactly how the last regression rode out to a release. It bit me on the Azure batch run too.

## Piece by piece

- [x] reuse counts are only asserted in the online tests
- [x] the batch e2e checks only the reassembled output and nothing else
- [x] this gap is exactly how the last regression rode out to a release
- [x] it bit Gideon on the Azure batch run

## What was actually said

**Gideon Halloway**, 2025-02-21, #pipeline

> We only ever assert on reuse counts in the online tests, the batch e2e checks the reassembled output and nothing else

## In context

```
15:32  emil      Actually, I flagged the resume offset as the thing to check, not reuse counts generally
15:32  emil      Those are related but not the same concern
16:03  gideon    We only ever assert on reuse counts in the online tests, the batch e2e checks the reasse   <-- the clue
16:04  gideon    That's exactly how the last regression rode out to a release, and it's the same gap that
16:10  dario     So the async batch refactor sits until someone adds a reuse count assertion to the batch
```
