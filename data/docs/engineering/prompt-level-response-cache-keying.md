---
title: "Prompt-level response cache keying"
author: dario
created_at: 2025-01-28T09:49:00+00:00
---

# Prompt-level response cache keying

The current assumption baked into the resume logic is that generation_params are run-scoped: if they differ from what produced the cache, the cache is worthless. That is wrong, and the fix is to move keying down to the prompt level.

## The problem

When a run resumes, we compare the current generation_params against whatever was used in the stored run. If they differ at all, the practical path today is to wipe the cache directory and regenerate everything. This throws away rows that are perfectly valid, because their prompt and params are unchanged. The only rows that actually need to go back to the provider are the ones whose params differ from what produced them.

The blast radius of the current approach is the whole run. It should be individual rows.

## Proposed keying scheme

Each cached row gets a key that incorporates:

- the prompt content (exact text, not an index or sequence number)
- the generation_params that were used to produce that row's response

On resume, we compute the key for each row in the current run and look it up. Match -> return from cache. No match -> provider call for that row only.

The cache directory stops being a monolithic "this run used these params" artifact and becomes a lookup table keyed per prompt.

I think this is the right shape. The main thing I am not sure about is what "prompt content" means precisely if there is any templating or injection happening before the call goes out. We would need to key on the final resolved prompt, not the template. Worth confirming with whoever owns the prompt assembly step.

## What changes

- **Nothing changes** for runs where params are consistent across the whole run. The behaviour is identical, just implemented differently under the hood.
- **Partial reruns become possible.** If you change temperature on half the rows (or the params are updated between a crash and a resume), only the affected rows go back out. Valid cache hits are reused.
- **The rm -rf path goes away** as the routine answer to a params mismatch. It was always a blunt instrument.

The downside is that the cache directory grows more complex to inspect manually, because the key is no longer just "run id" or "run id + params hash". That is an acceptable tradeoff.

## Open questions

- **Partial writes mid-run.** A row that was in-flight when the process died may have been written partially, or the write may not have been flushed at all. We need to either detect and discard those rows on resume, or make the write atomic (write to a temp file, rename on completion). I dont know what the current write path looks like here, need to check.
- **Scope of generation_params for keying.** Full dict equality is the obvious choice but it is brittle if params gain new optional keys with defaults. I think we want a stable canonical subset, but I am not sure what belongs in it vs. what is noise. Some params probably dont affect the response content (things like timeout or retry config) and shouldnt be part of the key. Need to pin this down before implementing.
- **Key format.** Hash of (prompt, params subset), or something human-readable? Hash is safer for collisions and path length. TBD.

## Out of scope (for now)

- TTL or expiry on cache entries. Not changing that here.
- Cache eviction policy when the directory gets large.
