---
title: "Weekly sync notes: week of Jun 9 (bulk LLM inference)"
author: emil
created_at: 2025-06-11T09:28:00+00:00
---

# Weekly sync notes: week of Jun 9 (bulk LLM inference)

Note-taker: Emil. Led by Dario.

---

## Status

Dario walked through current state of bulk-llm-inference. Overall: on track for the milestone, no blockers.

## Rate limit handling

- Issues 207 and 233 both still open
- Auto-detect rate limits work: team agreed to defer this to post-dormancy
  - not blocking v0.1.26, and dormancy window is close enough that it doesnt make sense to rush it in now

## Cost / usage tracking

- Issue 293: unblocked but not prioritized for v0.1.26
  - Dario confirmed it's unblocked (the API surface is there to do it)
  - just not in scope for this milestone, comes after

## Open

- [ ] 207 - rate limit handling
- [ ] 233 - rate limit handling (related, separate issue)
- [ ] 293 - cost/usage tracking via API, punted past v0.1.26
