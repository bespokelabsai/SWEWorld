---
title: "Postmortem: cache hashing regression revert on Jan 13"
author: dermot
created_at: 2025-01-14T08:51:00+00:00
---

# Postmortem: cache hashing regression revert on Jan 13

**Date:** 2025-01-14
**Author:** Dermot Callaghan
**Status:** draft, actions in progress

---

## What happened

A refactor to the cache key construction logic was merged to main on Jan 13. The intent was to normalize certain fields before hashing, so that semantically equivalent requests would resolve to the same cache entry regardless of minor surface differences. The implementation changed how the hash was computed for requests that had already been written to cache under the old scheme.

On a resumed batch job, those existing rows no longer matched. They were treated as new requests and re-sent to the LLM.

The practical result: a resumed job re-sent a large share of rows that had already been answered. Tokens and time burned, and the duplicate output had to be reconciled manually before that job's results could be used.

The change was reverted the same day.

---

## Timeline

- Jan 13, morning: refactor merged to main
- Jan 13, midday: first report of unexpected re-inference on a resumed batch job
- Jan 13, early afternoon: root cause confirmed as the hashing change
- Jan 13, mid-afternoon: revert merged and deployed

---

## Root cause

The hash function for cache lookup is the single decision point for whether a row is reused or sent to the LLM. All three processors, online, batch, and the local vLLM one, call the same function. A change to it is effectively a breaking change to every cache that is already on disk or in-flight, not just new runs.

The refactor was reviewed as a correctness improvement. The backwards-compatibility impact on existing cache entries was not flagged during review, and there was nothing in the review checklist or the code itself that would have prompted someone to think about it.

That is the root cause: the function carries a contract that is not written down anywhere near the function, and the review did not surface it.

---

## What was missed

There was no test that resumed a job against a cache written by a previous version of the hash function. A fresh run would not expose this, because on first write the old and new schemes agree. The mismatch only appears on read, when the key computed at lookup time does not match the key that was written. So CI passed cleanly.

---

## Actions

- [ ] Treat any change to the cache hash function as a breaking change requiring either a cache-format version bump or an explicit migration. Need to agree on what that process actually looks like, i dont think we have one written down yet.
- [ ] Add a resume test: write a cache under a known hash scheme, then read it back after a code change and assert that no already-answered rows are re-sent. The "known hash scheme" part needs some thought, not entirely sure how to pin that without it becoming brittle.
- [ ] Add a code comment at the hash function noting that all three processors call it and that a change here affects every persisted cache. This one is done as of this morning.

---

## Open questions

- How long was the affected job running before the report came in? I dont have that number. Whoever ran the job would know.
- What is the total token cost of the duplicate re-inference? Need this for the incident record. Check with whoever owns the billing dashboard.
- Should we version the cache format now, proactively, before the next change to the hash function? My instinct is yes but that is an engineering decision not just mine to make.
