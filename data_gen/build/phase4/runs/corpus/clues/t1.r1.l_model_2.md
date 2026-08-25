# t1.r1.l_model_2 — clue for t1.r1 (Prompt-level response cache keying)

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

**Planted by phase 3 as**   dermot, slack, 2025-01-30, #incidents
**Meant to settle**         the team agrees reuse must be scoped per model rather than switched off wholesale
**So a reader concludes**   model_name has to take part in what identifies a stored response, so the same prompt against a different model is not reused.
**Covers**                  rule
**Names that must appear**  CURATOR_DISABLE_CACHE=1
**Status**                  carried  (attempt 1)

> **LEAKED** — giveaway language reached the transcript: cache key. The clue landed, but saying this much states the hidden requirement outright and makes the task trivial. Worth re-running even though the gate passed.

## What phase 3 wrote

> Every time I run a model sweep I end up exporting CURATOR_DISABLE_CACHE=1 for the whole thing, which then means the second and third models pay full price for the prompts I already have at that model.

## Piece by piece

- [x] when running a model sweep, they export CURATOR_DISABLE_CACHE=1 for the whole thing
- [x] as a result, the second and third models pay full price for prompts already cached at the first model

## What was actually said

**Dermot Callaghan**, 2025-01-30, #incidents

> every time I run model sweep I end up exporting `CURATOR_DISABLE_CACHE=1` for the whole thing, which means the second and third models pay full price for prompts we already cached at the first. the flag is too blunt, reuse needs to be scoped per model, not switched off wholesale.

## In context

```
09:00  dermot    every time I run model sweep I end up exporting `CURATOR_DISABLE_CACHE=1` for the whole    <-- the clue
09:16  dermot    is the cache key scoped per model at all right now, or is it purely content-based?
10:17  dermot    @Dario, you own caching-and-resume, do you know offhand whether there's any existing mec
```
