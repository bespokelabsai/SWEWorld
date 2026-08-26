# t1.r1.l_prompt_3 — clue for t1.r1 (Prompt-level response cache keying)

## The task it serves — t1

**The agent is told:** Add a `cache_stats()` method to `curator.LLM` that reports how many of the last run's requests were served from the local cache versus sent to the backend, so users can gauge how much a re-run will cost before running it.

### The hidden requirement — t1.r1

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | The cache key used to look up a prior response must be derived from the exact tuple of (rendered prompt text, model_name, response_format schema, and generation_params) — not from the raw input row alone. | — |
| scope | Applies to every request path that already calls the existing cache-lookup helper, including batch and online modes. | — |
| exclusions_or_crossover | Two rows that render to an identical prompt string but differ only in fields unused by `prompt()` must be counted as the same cache entry, not treated as separate misses. | **carries this** |
| failure_behavior | If `response_format` cannot be hashed (e.g. a dynamically constructed Pydantic model), the row must be treated as a guaranteed cache miss rather than raising. | — |
| observability | `cache_stats()` must expose a `hit_rate` float and a `misses` int that together account for 100% of processed rows. | — |

This clue is one of several that build to: *The value looked up for reuse has to be derived from the prompt text that prompt() actually rendered, not from the input row, so rows that differ only in fields prompt() never reads land on the same entry.*

---

**Planted by phase 3 as**   emil, slack, 2025-01-29, #engineering
**Meant to settle**         the team agrees two rows rendering an identical prompt should resolve to one stored entry rather than two sends
**So a reader concludes**   The value looked up for reuse has to be derived from the prompt text that prompt() actually rendered, not from the input row, so rows that differ only in fields prompt() never reads land on the same entry.
**Covers**                  exclusions_or_crossover
**Names that must appear**  RAFT
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> RAFT emitted the same question against two chunk ids last night. Byte identical messages payload, I diffed them. Both went out as separate requests and both got billed. I would expect the second one to come straight back off disk since we already have that exact answer.

## Piece by piece

- [x] RAFT emitted the same question against two different chunk ids last night
- [x] the payload was byte identical
- [x] he diffed them himself
- [x] both went out as separate requests
- [x] both got billed
- [x] the second one should have come back off disk since they already had that exact answer

## What was actually said

**Emil Brandvold**, 2025-01-29, #engineering

> If the hash keys on prompt content alone then that tracks, but I saw RAFT last night emit the same byte-identical payload twice against two different chunk IDs, and both went out as separate requests and both got billed

## In context

```
11:29  dario     Makes sense
11:29  dario     that's consistent with how the cache layer handles it.
11:50  emil      If the hash keys on prompt content alone then that tracks, but I saw RAFT last night emi   <-- the clue
11:50  emil      Byte identical payload, I diffed them myself.
11:50  emil      Second one should've come straight back off disk since we already had that exact answer.
```
