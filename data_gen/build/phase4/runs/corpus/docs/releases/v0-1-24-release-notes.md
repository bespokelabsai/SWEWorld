---
title: "v0.1.24 Release Notes"
author: emil
created_at: 2025-05-06T09:35:00+00:00
---

# Millrow v0.1.24 Release Notes

Milestone: Consolidation and Provider Breadth, Pruning After the Sprint.

Three changes in this release.

---

## feat: n samples in generation params (PR 468)

Generation params now accept an `n` field, letting you request multiple samples per call. This is groundwork toward issue 52 (full multi-sample support); the round-trip handling downstream of the `n` field is still an open question and not finalized in this release.

## perf: lazy batch download in Gemini processor (PR 654)

The Gemini processor was downloading the full batch upfront before processing anything. Downloads are now deferred until items are actually consumed. On large runs this meaningfully reduces peak memory and improves throughput. No API change.

## feat: dataset download from viewer (PR 652)

The curator viewer now has a download action. Users can pull a dataset directly from the UI without making a separate API call. Should reduce some of the friction we kept hearing about.

---

## Open / still outstanding

- Full multi-sample round-trip (issue 52), `n` param lands here but the rest is TBD
- No other known blockers at cut time
