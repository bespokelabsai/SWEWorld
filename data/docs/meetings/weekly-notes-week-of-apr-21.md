---
title: "Weekly Notes \u2014 Week of Apr 21"
author: gideon
created_at: 2025-04-23T09:00:00+00:00
---

# Weekly Notes, Week of Apr 21

current version: v0.1.23, no release this week

## In Flight

- PR 632, batch CLI update frequency
  - pending review/merge, i think this one is close
- PR 643, response object in curator
  - blocked on routing decision, need to nail down where this lives before it can merge
  - TBD who's making the call on that
- PR 468, n-samples support
  - stalled, ~75 days now, needs someone to look at it
  - this is the one i'm most worried about, 75 days is a long time for something that sounds scoped
- PR 640, OpenAI/DeepSeek API
  - in review
- PR 651, multimodal model updates
  - in review

## Open Questions

these have been sitting for a while and none of them resolved this week

- issue 52: multiple samples, still open
- issue 207: has_capacity via rate-limit headers, still open
- issue 233: auto-detect rate limits, still open

207 and 233 feel related to me, not sure if they're being tracked together or separately.

## Things That Need Attention

PR 468 is the one i'd flag. 75 days stalled is past the point where you can assume someone is quietly working it, somebody should either pick it up or explicitly close it out. same with the routing decision on PR 643, that one's blocked on a decision not on code.

## Questions

- who owns the routing decision for PR 643?
- is anyone actively on PR 468 or do we need to reassign?
- are issues 207 and 233 being tracked together anywhere?
