---
title: "Handover: Status Tracking, Cost Reporting & the Viewer Surface"
author: gideon
created_at: 2025-05-01T08:56:12+00:00
---

# Handover: Status Tracking, Cost Reporting & the Viewer Surface

My direct ownership is progress-and-cli and online-request-processing. The viewer surface section below is from the integration side only, not ownership.

---

## Status Tracking (progress-and-cli)

The CLI progress bar updates on a timer. PR 632 (Fix/curator-cli-batch-update-freq-increase) increases the batch update frequency because the old cadence was leaving the display visibly stale on fast runs.

- the change is straightforward: update interval is configurable, new default is more aggressive
- no behavioral change to the underlying request logic
- needs to merge before the next release

One thing to know going in: progress tracking relies on counts coming back from bulk-llm-inference. If the inference layer is slow to report, the CLI lags. That is expected, not a bug.

## Cost Reporting (online-request-processing)

Cost and usage data is attached to responses in online-request-processing. We do not compute the numbers ourselves, they come from provider response headers and bodies.

What is reported today:
- token counts
- dollar cost, where the provider returns it

What is NOT guaranteed:
- per-request cost breakdown for every provider
- normalized usage shape across providers

Issue 293 (OpenAI Usage and Costs via API) is still open. The short version is that not every provider returns usage in the same shape and we havent normalized across all of them yet. No owner on that one right now.

Issue 207 (has_capacity via rate limit headers) is related and also open. I think those two are connected enough that whoever picks up 293 should read 207 first, but i havent confirmed that with anyone.

## Caching and the Viewer Surface

One thing anyone picking this up needs to have straight: cache hit/miss stats reflect what is actually on disk at the time of the run. On a machine with no history, nothing is on disk and every request goes to the provider. That is a correct number, not a broken one. Zero hit rate on a cold-start run is expected.

The viewer (curator-viewer, Dario's) surfaces these numbers. The integration point on my side is that online-request-processing attaches cache metadata to the response object, which PR 643 is formalizing. Until 643 lands, the viewer is reading fields that are present but not yet part of the stable response contract. So the viewer works right now, but on an informal contract.

PR 643 needs to land to firm up that boundary. Once it merges, Dario has a stable contract to read from.

## Open Items

- [ ] PR 632 merge (batch update freq), needed before next release
- [ ] PR 643 merge (response object contract), needed to stabilize the viewer integration
- [ ] Issue 293: cost reporting across providers, no owner yet
- [ ] Issue 207: has_capacity via rate limit headers, open and probably related to 293

## Ownership notes

The caching-and-resume service is Dario's. I can speak to what online-request-processing hands off but not to what caching-and-resume does with it internally. Questions about what gets cached, when, and why should go to him.
