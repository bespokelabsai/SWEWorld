# t1.r1.l_scope_1 — clue for t1.r1 (Prompt-level response cache keying)

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
| observability | `cache_stats()` must expose a `hit_rate` float and a `misses` int that together account for 100% of processed rows. | — |

This clue is one of several that build to: *The change lands in the single shared lookup path, so it takes effect for batch submission and online requests alike rather than being special-cased per backend.*

---

**Planted by phase 3 as**   emil, slack, 2025-03-25, #engineering
**Meant to settle**         the team agrees batch submission and the online path go through the same reuse lookup
**So a reader concludes**   The change lands in the single shared lookup path, so it takes effect for batch submission and online requests alike rather than being special-cased per backend.
**Covers**                  scope
**Names that must appear**  jsonl
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> Reminder for whoever touches the reuse pass: batch submission builds its jsonl off the same lookup, that is why when the online path stopped re-sending duplicates last month the batch path quietly stopped too.

## Piece by piece

- [x] batch submission builds its jsonl off the same lookup used by the online path
- [x] the online path stopped re-sending duplicates last month
- [x] the batch path quietly stopped re-sending duplicates too, as a consequence of sharing that lookup

## What was actually said

**Emil Brandvold**, 2025-03-25, #engineering

> One thing for whoever touches the reuse pass: batch submission builds its jsonl off the same lookup as the online path. When the online path stopped re-sending duplicates last month, the batch path quietly stopped too. Is that already factored into Dario's sketch, or is it going to need explicit handling?

## In context

```
12:11  dermot    I'm not entirely sure that fingerprint is the right thing for reuse lookup
12:35  emil      Is the call to use the fingerprint as-is, or do we want a dedicated tracker for reuse?
12:36  emil      One thing for whoever touches the reuse pass: batch submission builds its jsonl off the    <-- the clue
12:39  dermot    yeah, batch and online go through the same reuse lookup, that's not changing. I'll read 
12:53  emil      When you've got the read on the fingerprint, are you dropping it here or in #pipeline?
```
