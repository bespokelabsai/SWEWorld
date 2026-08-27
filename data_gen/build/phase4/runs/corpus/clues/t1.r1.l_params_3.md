# t1.r1.l_params_3 — clue for t1.r1 (Prompt-level response cache keying)

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

**Planted by phase 3 as**   dario, notion, 2025-01-28, page:design-t1-plant
**Had to be written into**  Prompt-level response cache keying
**Meant to settle**         the team agrees differing generation_params should force a resend of just those rows
**So a reader concludes**   generation_params has to take part in what identifies a stored response, so changing temperature or max_tokens resends those rows.
**Covers**                  rule
**Names that must appear**  generation_params
**Status**                  carried  (attempt 1)

> **LEAKED** — giveaway language reached the transcript: cache key, hash. The clue landed, but saying this much states the hidden requirement outright and makes the task trivial. Worth re-running even though the gate passed.

## What phase 3 wrote

> Writing down what I think the sane behaviour is, because right now everyone's answer is rm -rf on the cache dir: if generation_params differ from the stored run, those rows should be going out to the provider again, and only those rows.

## What was actually said

**dario**, 2025-01-28, Prompt-level response cache keying (written from #releases)

> rows whose key has changed -> sent to provider, response written back into cache on success

## What was actually written

`docs/design/prompt-level-response-cache-keying.md`

```
# Prompt-level response cache keying

## The problem

Right now the operational answer whenever generation_params change between runs is to blow away the whole cache dir and start fresh. That is wrong, and I want to write down what the right behaviour is before we keep building on top of the wrong one.

## What the cache key should be

Hash of (prompt text, generation_params), at the row level. Not at the run level.

A row is valid if and only if both of those things match what was stored. A row whose prompt text and generation_params are identical to the stored row is still good, regardless of what other rows in the same run are doing.

This matters because a 50k-row run where someone tweaks temperature does not suddenly have 50k invalid rows. It has however many rows used the old value, and only those need to go back to the provider.

## Resume behaviour

- rows with a matching cache key -> served from cache, no provider call
- rows whose key has changed -> sent to provider, response written back into cache on success
- rows with no cached entry at all -> same as above, treated as a miss

This is just a per-row cache lookup. The run-level invalidation the current code does is not a simplification, its a bug.

## Cache write failures

A write failure on the cache is not a reason to abort the run. The write is an optimisation for the next run, not a correctness requirement for this one. If we cant write a row to disk, the correct behaviour is to log it, carry on, and accept that the next run will have to re-fetch that row. We do not abort work the user has already paid for because we could not put a file on disk.

The distinction that matters here: losing a cached row makes the next run more expensive. Aborting the current run makes this run invalid. Those are not the same failure mode and should not be handled the same way.

## What prompted this

The current practice is full cache invalidation any time generation_params differ from the stored run. I think this grew out of not having per-row keying at all, so the only options were "use the whole cache" or "throw it away". Once the key includes generation_params at the row level, that tradeoff disappears and there is no reason to keep the rm -rf behaviour.

## Open questions

- Who owns the cache write path right now? I need to know before I can put a PR number against this.
- Is generation_params serialisation stable enough to hash? If the same params can produce different byte representations depending on insertion order or library version, the key is unreliable. I honestly don't know the answer here and it should be checked before implementation, not assumed.
- Are there row types where generation_params are intentionally absent or variable? If so, the key degenerates to just the prompt hash for those rows and we should say that explicitly rather than let it be implicit.
```
