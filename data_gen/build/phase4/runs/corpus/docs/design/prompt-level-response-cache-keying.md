---
title: "Prompt-level response cache keying"
author: dario
created_at: 2025-01-28T09:56:00+00:00
---

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
