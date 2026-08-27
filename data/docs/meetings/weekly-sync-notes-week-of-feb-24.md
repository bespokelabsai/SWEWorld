---
title: "Weekly sync notes: week of Feb 24"
author: gideon
created_at: 2025-03-04T09:14:00+00:00
---

# Weekly sync notes: week of Feb 24

## Shipped

- v0.1.20 - includes the online processor cost revamp (PR 546)
- v0.1.19.post1 - patch release

## Milestone: Consolidation and Provider Breadth

Post-sprint pruning done. Team is spread across a lot of areas right now:

- batch-mode
- blocks-and-recipes
- bulk-llm-inference
- caching-and-resume
- code-execution
- curator-viewer
- examples-cookbooks
- local-offline-inference
- multimodal-prompts
- online-request-processing

Not going to list every thread per area here, most of it is in the individual PRs.

## Carrying into next week

- token-field fixes - need these to close the cost estimation loop properly, still open
- PR 565, PR 566 - provider backend PRs, both pending review
- Gemini rate limit handling - path not decided yet, needs a decision before anyone picks it up
    - I dont think we agreed on who owns this call, somebody needs to

## Questions

- Who is picking up the Gemini rate limit question? I want to make sure its not just sitting there next sync.
