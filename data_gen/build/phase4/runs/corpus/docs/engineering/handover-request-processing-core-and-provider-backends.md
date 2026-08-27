---
title: "Handover: Request-Processing Core and Provider Backends"
author: dario
created_at: 2025-02-04T09:14:00+00:00
---

# Handover: Request-Processing Core and Provider Backends

For: Emil Brandvold
From: Dario Kestrel
Date: 2025-02-04

This covers the four components I've been owning: online-request-processing, bulk-llm-inference, caching-and-resume, and provider-integrations. I'll be available for questions through end of week but after that Emil should treat this doc as the primary reference.

---

## online-request-processing

Handles concurrent online requests. The flow is: request comes in, gets resolved against the active provider config, gets dispatched to bulk-llm-inference, result flows back to the caller.

Key things to know:

- **Retries live here, not in the provider layer.** The provider layer only ever sees one attempt. If you're debugging a retry loop or adjusting backoff behavior, this is where to look.
- Rate-limit backoff is also here. The provider layer does not know or care about rate limits, it just returns a response or an error.
- This separation is intentional. Mixing retry logic into the provider backends made earlier iterations hard to reason about, so we pulled it up. Worth keeping that boundary clean.

I think the retry config could use another look at some point, particularly the backoff ceilings, but it is not urgent and I haven't had time to revisit it.

---

## bulk-llm-inference

Takes a dataset, fans requests out across the provider. Core invariant: **a row does not get written until the response is confirmed good.** Partial results from a failed batch do not land on disk. This is load-bearing, not just a nicety.

- Concurrency is controlled by a semaphore, limit set per-provider in the config
- If you need to tune throughput for a given provider, the semaphore limit is the knob
- Do not add intermediate writes without thinking through what a mid-batch failure does to the resume logic (see caching-and-resume below)

The fan-out itself is straightforward. The part that catches people is the write-only-on-confirmed-good invariant and how it interacts with partial batches. If a batch partially succeeds and then fails, nothing from that batch is on disk, and the whole thing reruns on resume.

---

## caching-and-resume

Cache keys are built from the full prompt plus all generation params: model, temperature, and anything else that affects the output. A cache hit skips the provider entirely.

- Resume works by checking the cache before dispatch. If the key is already present, the row is considered done.
- **Changing any generation param invalidates the cache for that row.** This is correct behavior but it surprises people occasionally, so worth knowing going in.
- There is no separate "resume state" file or checkpoint. The cache IS the resume mechanism.

If someone reports that a rerun is redoing work it shouldn't be, the first thing to check is whether the generation params changed between runs (even something like temperature going from 0.7 to 0.70 might or might not matter depending on how the key serialization handles it, I actually haven't verified the exact normalization there).

---

## provider-integrations

**Draft section, some edge cases still being worked through.**

Each provider backend implements the same interface:
- resolve model name
- validate cost map entry exists
- send request
- return normalized response

The cost map check happens at init time, not per-request. If a model isn't in the cost map, you'll get a failure at startup, not mid-run. That's intentional.

### Batch providers

Providers that return a batch object rather than an inline response have an additional constraint:

- **The batch id is only written to disk after the batch completes successfully.**
- An id written before completion creates a dead polling reference on any rerun. The rerun will try to poll an id that may be stale or gone.
- This should not change. If someone proposes writing the id earlier "for observability" or similar, the answer is no.

### Known gap

The config validator does not currently cover all non-standard provider backends. This is the thing I am most concerned about leaving open. It needs a follow-up pass before the provider list grows any further. I'd make this a near-term priority Emil, because adding a backend before that pass is done means we're flying without validation on whatever that backend's config looks like.

I don't know enough about the full set of non-standard backends to say how much work the validator pass is. Whoever added the most recent non-standard backend would know better than me.

---

## Open questions / things to watch

- [ ] Config validator gap (see above), needs scoping and a ticket before next provider is added
- [ ] Retry backoff ceiling in online-request-processing, I think its probably fine for current load but haven't verified
- Cache key serialization and whether param normalization is exact, I genuinely don't know if `0.7` and `0.70` produce the same key. Probably worth a quick test before anyone relies on resume across runs where params may have drifted slightly.
- TBD: who is taking over the cost map? I've been the one updating it when new models come in but it probably needs a clear owner
