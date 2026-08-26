# t1.r1.l_stats_1 — clue for t1.r1 (Prompt-level response cache keying)

## The task it serves — t1

**The agent is told:** Add a `cache_stats()` method to `curator.LLM` that reports how many of the last run's requests were served from the local cache versus sent to the backend, so users can gauge how much a re-run will cost before running it.

### The hidden requirement — t1.r1

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | The cache key used to look up a prior response must be derived from the exact tuple of (rendered prompt text, model_name, response_format schema, and generation_params) — not from the raw input row alone. | — |
| scope | Applies to every request path that already calls the existing cache-lookup helper, including batch and online modes. | — |
| exclusions_or_crossover | Two rows that render to an identical prompt string but differ only in fields unused by `prompt()` must be counted as the same cache entry, not treated as separate misses. | — |
| failure_behavior | If `response_format` cannot be hashed (e.g. a dynamically constructed Pydantic model), the row must be treated as a guaranteed cache miss rather than raising. | — |
| observability | `cache_stats()` must expose a `hit_rate` float and a `misses` int that together account for 100% of processed rows. | **carries this** |

This clue is one of several that build to: *The reported numbers have to be a fractional hit_rate plus an integer misses, and the two together have to account for every processed row.*

---

**Planted by phase 3 as**   gideon, slack, 2025-02-20, #viewer
**Meant to settle**         the team agrees a fractional hit_rate is needed alongside raw counts
**So a reader concludes**   The reported numbers have to be a fractional hit_rate plus an integer misses, and the two together have to account for every processed row.
**Covers**                  observability
**Names that must appear**  hit_rate
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> The end of run table says cached: 12,403 and the first thing every single user asks is out of what. A bare count tells nobody whether their rerun is cheap. Give me a hit_rate I can print as a percentage next to it.

## Piece by piece

- [x] the end-of-run table currently shows a bare count like cached: 12,403
- [x] the first thing every user asks is 'out of what'
- [x] a bare count doesn't tell you whether a rerun is cheap
- [x] he wants hit_rate printed as a percentage next to the count

## What was actually said

**Gideon Halloway**, 2025-02-20, #viewer

> End-of-run summary table is mostly wired up, but I keep hitting the same thing, we show `cached: 12,403` and the first question anyone's going to ask is "out of what." We have hit_rate already so I think we should just print it as a percentage right next to the count.

## In context

```
09:00  gideon    End-of-run summary table is mostly wired up, but I keep hitting the same thing, we show    <-- the clue
09:00  gideon    a bare count doesn't tell you if a rerun is cheap, that's the whole reason I want it.
09:34  gideon    What does hit_rate actually return right now, a float between 0 and 1 or something else?
```
