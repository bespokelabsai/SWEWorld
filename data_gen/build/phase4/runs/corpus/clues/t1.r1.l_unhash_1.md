# t1.r1.l_unhash_1 — clue for t1.r1 (Prompt-level response cache keying)

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

**Planted by phase 3 as**   emil, slack, 2025-03-11, #cookbooks
**Meant to settle**         the team agrees a dynamically built response model currently aborts the run in the lookup pass
**So a reader concludes**   When the response_format cannot be hashed, the row has to fall through as a plain miss and go to the backend instead of raising and killing the run.
**Covers**                  failure_behavior
**Names that must appear**  create_model, TypeError: unhashable type
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> SimpleStrat builds its response model at runtime with pydantic create_model, and the lookup pass dies on it: TypeError: unhashable type. Run is dead at row zero, before a single request goes out. Traceback in thread.

## Piece by piece

- [x] SimpleStrat builds its response model at runtime using pydantic create_model
- [x] the lookup pass dies on it
- [x] the specific error is TypeError: unhashable type
- [x] the run is dead at row zero, before a single request goes out
- [x] the traceback appears in thread

## What was actually said

**Emil Brandvold**, 2025-03-11, #cookbooks

> SimpleStrat and RAFT both hit it, both build with create_model at runtime

## In context

```
11:39  dario     so do we need to decide today whether the check gets updated before PR 565 and 566 merge
11:46  emil      Went through the shipped blocks
11:47  emil      SimpleStrat and RAFT both hit it, both build with create_model at runtime   <-- the clue
11:47  emil      lookup pass dies on it with TypeError: unhashable type
11:47  emil      run is dead at row zero, before a single request goes out, traceback in thread
```
