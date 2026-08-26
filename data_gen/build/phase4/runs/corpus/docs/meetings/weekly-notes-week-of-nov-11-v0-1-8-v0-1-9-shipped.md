---
title: "Weekly notes: week of Nov 11 - v0.1.8 & v0.1.9 shipped"
author: dario
created_at: 2024-11-13T09:14:00+00:00
---

# Weekly notes: week of Nov 11 - v0.1.8 & v0.1.9 shipped

## Releases

- v0.1.8 shipped mid-week, v0.1.9 followed before end of week
- both are part of the Request Pipeline milestone
- 55 changes merged to date across the milestone (which is a lot for a single week stretch honestly)

## In flight

- PR 78: vLLM example for OpenAIOnlineParallelProcessor, bulk-llm-inference / provider-integrations, needs review
- PR 90: add argument to disable cache for Prompter, caching-and-resume, needs review
- PR 95: better no-data view and error handling in dataset viewer, ready, but may defer to next cycle
    - this is curator-viewer work, not on the critical path
- PR 44: starter example for running UI for the first time, still open
- PR 71: cleanup build script and .gitignore for build artifacts, still open

## 0.1.7 close-out

Emil cleared release-and-ci. PR 78, PR 90, and PR 95 still need eyes before 0.1.7 can formally close. PR 95 (viewer error handling) isnt critical path so deferring it to next cycle is on the table. The other two need actual review.

## Open questions carrying forward

- issue 33: check cache for batch=True completions, skip downloading if already cached
- issue 52: support multiple samples per request
- issue 55: complain louder when num generic requests != num generic responses

no movement on any of these this week as far as I can tell

## Process / other

- PR-only process is underway, Konrad Feltrin leading that
- agentic-curation, batch-mode, and related workstreams not yet started
