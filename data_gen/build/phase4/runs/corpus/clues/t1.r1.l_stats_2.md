# t1.r1.l_stats_2 — clue for t1.r1 (Prompt-level response cache keying)

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

**Planted by phase 3 as**   emil, notion, 2025-05-02, page:handover-status-tracking-cost-reporting-and-the-v
**Had to be written into**  comment on Handover: Status Tracking, Cost Reporting & the Viewer Surface
**Meant to settle**         the team agrees an integer misses count is needed for cost estimation
**So a reader concludes**   The reported numbers have to be a fractional hit_rate plus an integer misses, and the two together have to account for every processed row.
**Covers**                  observability
**Names that must appear**  misses
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> For the cost estimate in the cookbook I do not want a percentage I have to invert. I want misses as a plain int so I can multiply it by price per row and put a dollar figure in front of someone before they hit go.

## What was actually said

**emil**, 2025-05-02, comment on Handover: Status Tracking, Cost Reporting & the Viewer Surface (written from #code-review)

> Concretely: add a `misses` field carrying the integer count of rows that missed, not a rate or percentage.

## What was actually written

> Nothing on disk matches this artifact — it was never written, which is why the clue could not land.
