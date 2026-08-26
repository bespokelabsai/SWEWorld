---
title: "Weekly Notes \u2014 Week of May 19"
author: emil
created_at: 2025-05-21T09:14:00+00:00
---

# Weekly Notes, Week of May 19

Millrow / Consolidation and Provider Breadth milestone.

---

## Status by service

- **batch-mode** (Emil), in flight, no blockers
- **blocks-and-recipes** (Emil), in flight
- **local-offline-inference** (Emil), in flight
- **multimodal-prompts** (Emil), in flight
- **bulk-llm-inference** (Dario), in flight
- **caching-and-resume** (Dario), in flight
- **curator-viewer** (Dario), in flight
- **examples-cookbooks** (Dario), in flight
- **code-execution** (Nikolai), in flight
- **finetuning** (Konrad), in flight, edge cases still being worked through

## Active PRs

- PR 652: add support to download dataset from viewer (Emil)
- PR 653: finetuning client (Nikolai)
- PR 663: fix error when torch isn't installed (Nikolai)

## Release

v0.1.24. 348 changes merged to date.

## Open questions

- issue 52: support multiple samples per request
- issue 102: clarify that we must return a dict without Pydantic objects per row
- issue 121: should we handle pydantic-to-dict and back for the user when adding to a row?
- issue 124: `inspect(func)` is sensitive to comments and whitespace, cache invalidates unexpectedly
- issue 207: implementing has_capacity using rate limit info from response headers
- issue 233: automatically detect rate limits
- issue 290: `ModuleNotFoundError: No module named 'resource'`
- issue 293: OpenAI usage and costs via API

## Notes

Response object shape for agent outputs came up this week. We're leaning toward plain dict, which stays consistent with the direction in issue 102. Not fully settled yet though, and it matters, because examples-cookbooks will need updating once the shape is locked, and both PR 653 and the code-execution work are downstream of that decision. Would be good to get issue 102 closed out sooner rather than later so those dont stall.
