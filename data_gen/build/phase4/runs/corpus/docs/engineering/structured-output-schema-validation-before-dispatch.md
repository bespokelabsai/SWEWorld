---
title: "Structured output schema validation before dispatch"
author: dario
created_at: 2025-02-24T09:28:00+00:00
---

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
