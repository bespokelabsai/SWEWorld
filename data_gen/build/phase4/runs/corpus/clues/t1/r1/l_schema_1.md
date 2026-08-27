# t1.r1.l_schema_1 — clue for t1.r1 (Prompt-level response cache keying)

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

This clue is one of several that build to: *The response_format schema has to take part in what identifies a stored response, so editing the schema resends only the affected rows.*

---

**Planted by phase 3 as**   emil, slack, 2025-02-24, #engineering
**Meant to settle**         the team agrees editing a response model currently yields stored objects shaped like the old schema
**So a reader concludes**   The response_format schema has to take part in what identifies a stored response, so editing the schema resends only the affected rows.
**Covers**                  rule
**Names that must appear**  confidence
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> Added a confidence field to the response model on the ungrounded QA example, reran, and got back last week's objects with no confidence on them. Then the downstream validator threw on every row and I spent an hour looking at the validator.

## Piece by piece

- [x] a confidence field was added to the response model on the ungrounded QA example
- [x] after rerunning, the stored objects returned were last week's objects with no confidence on them
- [x] the downstream validator threw on every row
- [x] he spent an hour looking at the validator

## What was actually said

**Emil Brandvold**, 2025-02-24, #engineering

> hit this exact thing this week, added a confidence field to the response model on the ungrounded QA example, reran, got stored objects with no confidence on them, and the downstream validator threw on every row

## In context

```
11:50  dario     is there a clean place in the dispatch flow to fingerprint the current response_format a
12:04  dermot    @Dario would you be up for writing down the cases you know trigger this, so we have some
12:41  emil      hit this exact thing this week, added a confidence field to the response model on the un   <-- the clue
12:41  emil      I spent an hour looking at the validator before I figured out where the actual problem w
12:41  emil      I think a pre-dispatch check is worth building but i'm not entirely sure who should own 
```
