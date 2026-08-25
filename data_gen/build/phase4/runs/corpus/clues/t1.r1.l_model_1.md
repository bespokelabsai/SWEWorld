# t1.r1.l_model_1 — clue for t1.r1 (Prompt-level response cache keying)

## The task it serves — t1

**The agent is told:** Add a `cache_stats()` method to `curator.LLM` that reports how many of the last run's requests were served from the local cache versus sent to the backend, so users can gauge how much a re-run will cost before running it.

### The hidden requirement — t1.r1

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | The cache key used to look up a prior response must be derived from the exact tuple of (rendered prompt text, model_name, response_format schema, and generation_params) — not from the raw input row alone. | **carries this** |
| scope | Applies to every request path that already calls the existing cache-lookup helper, including batch and online modes. | — |
| exclusions_or_crossover | Two rows that render to an identical prompt string but differ only in fields unused by `prompt()` must be counted as the same cache entry, not treated as separate misses. | — |
| failure_behavior | If `response_format` cannot be hashed (e.g. a dynamically constructed Pydantic model), the row must be treated as a guaranteed cache miss rather than raising. | — |
| observability | `cache_stats()` must expose a `hit_rate` float and a `misses` int that together account for 100% of processed rows. | — |

This clue is one of several that build to: *model_name has to take part in what identifies a stored response, so the same prompt against a different model is not reused.*

---

**Planted by phase 3 as**   gideon, slack, 2025-03-18, #random
**Meant to settle**         the team agrees changing the model currently returns the previous model's stored answers
**So a reader concludes**   model_name has to take part in what identifies a stored response, so the same prompt against a different model is not reused.
**Covers**                  rule
**Names that must appear**  gpt-4o-mini, gpt-4o
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> Lost most of yesterday to this. Swapped gpt-4o-mini for gpt-4o on the reannotation set, run finished in nine seconds, summary said everything came off disk. The outputs were the mini ones. I only noticed because the formatting was too sloppy for 4o.

## Piece by piece

- [x] Lost most of yesterday to this
- [x] Swapped gpt-4o-mini for gpt-4o on the reannotation set
- [x] Run finished in nine seconds
- [x] Summary said everything came off disk
- [x] The outputs were the mini ones
- [x] Only noticed because the formatting was too sloppy for 4o

## What was actually said

**Gideon Halloway**, 2025-03-18, #random

> Swapped gpt-4o-mini for gpt-4o on the reannotation set, run finished in nine seconds, summary said everything came off disk

## In context

```
11:25  emil      That whole failure mode applies to the postmortem I've been writing up too, we had the k
11:29  gideon    same pattern, silent is the worst kind of wrong
11:29  gideon    Swapped gpt-4o-mini for gpt-4o on the reannotation set yesterday and lost most of the da   <-- the clue
11:29  gideon    Run finished in nine seconds, summary said everything came off disk, outputs were the mi
11:29  gideon    Only notcied because the formatting was too sloppy for 4o
```
