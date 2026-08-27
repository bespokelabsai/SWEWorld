---
title: "Weekly Notes \u2014 Week of Mar 3"
author: emil
created_at: 2025-03-05T09:28:00+00:00
---

# Weekly Notes, Week of Mar 3

## Milestone

Q2 plan milestone: Consolidation and Provider Breadth (Konrad Feltrin). Provider breadth is clearly the dominant theme this week across both Dario's and my tracks.

## In Progress

- PR 578 (Ref/update/ratelimits/gemini), rate limit handling for Gemini, ready for review and merge
- PR 571 (Feat/raft), my PR, still in flight
- PR 565 (add openai client backend), Dario, in review
- PR 566 (deepseek api), Dario, in review
- PR 575 (fix: use model name from config in cost processor), my PR, in review
- PR 468 (feat: add support for n samples in generation params), my PR, still in flight

Between PR 565, 566, and my raft work, there are a lot of open PRs right now. Worth keeping an eye on review queue.

## Open Questions

- PR 579 (Feat/openai/deepseek api): not clear to me whether this duplicates PR 565/566 or complements them. Need to loop in Dario and get clarity before anyone spends more time on it.
- Issue 207: implementing `has_capacity` using rate limit info from response headers. Not assigned yet as far as I can tell.
- Issue 233: auto-detecting rate limits. Related to 207 I think, but havent checked whether they are meant to be done together or sequentially. TBD.

## Notes

- PR 578 is the most actionable thing right now, just needs a review pass and it can merge
- openai, deepseek, and gemini coverage is what we are trying to close out this sprint, Dario has the client backends, I have raft and the cost processor fix
