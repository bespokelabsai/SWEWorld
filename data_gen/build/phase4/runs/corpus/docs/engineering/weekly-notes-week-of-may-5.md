---
title: "Weekly Notes \u2014 Week of May 5"
author: dermot
created_at: 2025-05-07T09:14:00+00:00
---

# Weekly Notes, Week of May 5

## Shipped

- v0.1.24 is out

## In Progress

- **bulk-llm-inference**: PR 654 open, gemini processor download batch is now lazy, meaning it defers the download until actually needed rather than on import. still under review
- **multimodal-prompts**: PR 658 open for review, covers agentic/multiturn prompting
- **finetuning**: PR 653 (client-side work) is with nikolai for review
- **code-execution**: torch import error is fixed, PR 663 merged this week
- **curator-viewer** and **caching-and-resume**: both sitting in dario's queue, work continuing
- **batch-mode**, **blocks-and-recipes**, **local-offline-inference**: ongoing with emil, nothing mergeable yet as far as i know

## Examples and Cookbooks

The prescription example has been drafted and is under review for inclusion in the main suite. That part feels close.

The stalled items are the problem. Three cookbook PRs (multimodal and structured-output related) are blocked waiting on a review decision. I dont have visibility into whether that decision is close or whether nobody has picked it up. Look, we need to either make the call on those PRs or formally defer them so they stop sitting there looking like active work.

- [ ] unblock or formally defer the three stalled cookbook PRs
- [ ] confirm prescription example is actually integrated into the suite once review completes

## Open Questions (unresolved)

These were open coming in to this week and nothing closed on any of them.

- issue 52, multiple samples per request
- issue 124, inspect cache invalidation on whitespace
- issue 207, rate limit detection
- issue 233, has_capacity behavior

Not entirely sure who is actively looking at 207 and 233. They feel related (both touch rate limiting logic) but i havent confirmed that with whoever owns that area.

## Carry Forward

- unblock or formally defer the stalled cookbook PRs (see above)
- confirm prescription example lands in the suite
- continue provider breadth work under bulk-llm-inference
