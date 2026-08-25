# t1.r1.l_unhash_3 — clue for t1.r1 (Prompt-level response cache keying)

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
| observability | `cache_stats()` must expose a `hit_rate` float and a `misses` int that together account for 100% of processed rows. | **carries this** |

This clue is one of several that build to: *When the response_format cannot be hashed, the row has to fall through as a plain miss and go to the backend instead of raising and killing the run.*

---

**Planted by phase 3 as**   gideon, slack, 2025-02-06, #pipeline
**Meant to settle**         the team agrees unhashable-schema rows should proceed to the backend and be reported as sends
**So a reader concludes**   When the response_format cannot be hashed, the row has to fall through as a plain miss and go to the backend instead of raising and killing the run.
**Covers**                  failure_behavior, observability
**Names that must appear**  —
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> Recipes that construct their schema on the fly are never going to be reusable and I am fine with that. What I am not fine with is being worse off than someone who never had a cache at all. Those rows should just go to the provider and show up in the sent column at the end.

## Piece by piece

- [x] a schema built on the fly is never going to be reusable, and that's fine
- [x] what's not fine is being worse off than someone who never had a cache at all
- [x] those rows should go to the provider
- [x] those rows should show up in the sent column / as sends

## What was actually said

**Gideon Halloway**, 2025-02-06, #pipeline

> And I get that a fly-built schema is never going to be reusable, that's fine, but being worse off than someone who never had a cache at all isn't / Those rows should just go to the provider and show up as sends

## In context

```
13:04  gideon    yeah, any unhashable type in the schema, lists are the most common. That bypass observab
13:34  dario     Completely silent, or does it at least show up somewhere in debug logs?
14:11  gideon    Completely silent. And I get that a fly-built schema is never going to be reusable, that   <-- the clue
14:11  gideon    Those rows should just go to the provider and show up as sends
```
