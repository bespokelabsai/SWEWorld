# t1.r1.l_schema_2 — clue for t1.r1 (Prompt-level response cache keying)

## The task it serves — t1

**The agent is told:** Add a `cache_stats()` method to `curator.LLM` that reports how many of the last run's requests were served from the local cache versus sent to the backend, so users can gauge how much a re-run will cost before running it.

### The hidden requirement — t1.r1

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | The cache key used to look up a prior response must be derived from the exact tuple of (rendered prompt text, model_name, response_format schema, and generation_params) — not from the raw input row alone. | **carries this** |
| scope | Applies to every request path that already calls the existing cache-lookup helper, including batch and online modes. | — |
| exclusions_or_crossover | Two rows that render to an identical prompt string but differ only in fields unused by `prompt()` must be counted as the same cache entry, not treated as separate misses. | — |
| failure_behavior | If `response_format` cannot be hashed (e.g. a dynamically constructed Pydantic model), the row must be treated as a guaranteed cache miss rather than raising. | **carries this** |
| observability | `cache_stats()` must expose a `hit_rate` float and a `misses` int that together account for 100% of processed rows. | — |

This clue is one of several that build to: *The response_format schema has to take part in what identifies a stored response, so editing the schema resends only the affected rows.*

---

**Planted by phase 3 as**   dario, notion, 2025-02-24, page:design-t2-plant
**Had to be written into**  Structured output schema validation before dispatch
**Meant to settle**         the team agrees a schema edit today requires manually discarding stored responses
**So a reader concludes**   The response_format schema has to take part in what identifies a stored response, so editing the schema resends only the affected rows.
**Covers**                  rule, failure_behavior
**Names that must appear**  response_format, CURATOR_DISABLE_CACHE=1
**Status**                  carried  (attempt 1)

## What phase 3 wrote

> Adding this to the troubleshooting page since it is the third report: if you edit your response_format between runs, either wipe the cache directory or set CURATOR_DISABLE_CACHE=1 first, otherwise you will get objects built to the previous schema.

## What was actually said

**dario**, 2025-02-24, Structured output schema validation before dispatch (written from #code-review)

> If yes: either remove the cache directory for that run, or set `CURATOR_DISABLE_CACHE=1` before restarting. Do not just restart, the mismatch will persist for every row with a cache hit.

## What was actually written

`docs/engineering/structured-output-schema-validation-before-dispatch.md`

```
# Structured output schema validation before dispatch

## What this covers

How bulk-llm-inference validates response_format schemas before dispatching to a provider, and what to do when a schema-mismatch causes 400s on resume. Adding the troubleshooting section explicitly because this is the third time its come up.

## Validation behavior

Before the first request in each batch is sent, the schema in response_format is checked for JSON Schema draft compatibility. This happens inside bulk-llm-inference, upstream of the provider integration layer, so a structurally broken schema surfaces before anything is dispatched rather than mid-run with partial results in an unknown state.

On resume, the pipeline compares a fingerprint of the cached schema against the current response_format:

- Match: proceeds normally, cache hits are served from cache
- Mismatch: logs a warning and continues (does not hard-stop)
    - rows with a cache hit are still served from cache as-is, built to the old schema
    - the provider is given the new schema
    - provider returns 400s because the cached objects dont conform

The warning-only behavior is intentional, on the assumption that some schema changes are additive and backward-compatible. I think this assumption is too generous in practice but thats the current design.

## Why mismatch errors look the way they do

Schema mismatches are the most common cause of silent 400s on a resume run. The requests look structurally valid from the providers perspective, which is why the rejections come back as 400s rather than a more descriptive error. The cache-built objects conform to the old schema; the provider was told to expect the new one. There is nothing wrong with either side individually, the disagreement is between them.

Worth being explicit: the provider does not know you resumed a run or that a cache is involved. It just sees objects that dont match the schema it was given.

## Troubleshooting

Steps for any 400 on resume:

1. Check whether response_format was edited since the last run.
2. If yes: either remove the cache directory for that run, or set `CURATOR_DISABLE_CACHE=1` before restarting. Do not just restart, the mismatch will persist for every row with a cache hit.
3. If no: the 400 is a genuine provider-side rejection, not a cache issue. Check the schema for constructs the provider doesnt support.
    - common offenders: nested `$defs`, `unevaluatedProperties`, anything that isnt in the subset the provider actually accepts (varies by provider, havent documented that per-provider yet)

## Open questions

- Should the fingerprint mismatch be a hard stop instead of a warning? The warning-only path exists for additive changes but I'm not sure how often that case actually occurs vs. how often people are just editing their schema between runs and then confused by the 400s. Worth raising if this keeps coming up.
- Per-provider list of unsupported constructs: TBD, needs someone who has actually hit the edge cases with each provider to document them. I dont own that.
```
