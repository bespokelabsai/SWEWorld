# t1.r1.l_schema_3 — clue for t1.r1 (Prompt-level response cache keying)

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

**Planted by phase 3 as**   gideon, slack, 2025-03-12, #incidents
**Meant to settle**         the team agrees a schema change should resend only the affected rows rather than discard everything
**So a reader concludes**   The response_format schema has to take part in what identifies a stored response, so editing the schema resends only the affected rows.
**Covers**                  rule
**Names that must appear**  —
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> Nuking the whole cache dir every time I tweak one field is the main reason people here do not trust reruns. On a 200k set that is real money to get one extra field.

## Piece by piece

- [x] nuking the whole cache dir on any field tweak is the main reason reruns aren't trusted here
- [x] on a 200k set that's real money to reprocess for one extra field

## What was actually said

**Gideon Halloway**, 2025-03-12, #incidents

> and that cost is for re-processing one extra field, not the real work

## In context

```
15:32  gideon    Nuking the whole cache dir on any field tweak is why reruns aren't trusted here
15:32  gideon    this is the whole reason nobody trusts reruns here
15:32  gideon    and that cost is for re-processing one extra field, not the real work   <-- the clue
15:32  gideon    On a 200k set that's real money
```
