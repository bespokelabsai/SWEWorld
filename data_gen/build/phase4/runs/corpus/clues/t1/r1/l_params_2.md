# t1.r1.l_params_2 — clue for t1.r1 (Prompt-level response cache keying)

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

This clue is one of several that build to: *generation_params has to take part in what identifies a stored response, so changing temperature or max_tokens resends those rows.*

---

**Planted by phase 3 as**   emil, slack, 2025-04-18, #engineering
**Meant to settle**         the team agrees changing max_tokens currently returns the previous truncated output
**So a reader concludes**   generation_params has to take part in what identifies a stored response, so changing temperature or max_tokens resends those rows.
**Covers**                  rule
**Names that must appear**  max_tokens
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> Same shape of thing with max_tokens for me. Response came back truncated mid sentence, I raised max_tokens, reran, got handed the truncated text again. Deleted the cache directory in the end, which also threw away four thousand rows that were perfectly fine.

## Piece by piece

- [x] response came back truncated mid-sentence
- [x] raised max_tokens
- [x] reran
- [x] got handed the same truncated text again
- [x] deleted the cache directory
- [x] that took out four thousand rows that were perfectly fine

## What was actually said

**Emil Brandvold**, 2025-04-18, #engineering

> Same shape of thing with max_tokens for me - response came back truncated mid-sentence, I raised max_tokens, reran, and got handed the same truncated text again. Ended up deleting the whole cache directory, which took out four thousand rows that were perfectly fine.

## In context

```
13:39  dario     @Emil Brandvold when you hit this, is it local or also in CI, and do you know if the var
14:09  gideon    so waiting on Dario to check what CI sets, then we can figure out reuse vs. new var
14:51  emil      Same shape of thing with max_tokens for me - response came back truncated mid-sentence,    <-- the clue
14:51  emil      This was local - is the expectation that people bust the whole cache when generation par
14:51  emil      To be clear on the sequence: truncated mid-sentence with max_tokens, raised max_tokens, 
```
