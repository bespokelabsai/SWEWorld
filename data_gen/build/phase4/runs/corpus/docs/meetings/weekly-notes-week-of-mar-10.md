---
title: "Weekly Notes \u2014 Week of Mar 10"
author: nils
created_at: 2025-03-12T09:14:00+00:00
---

# Weekly Notes, Week of Mar 10

**Attendees:** Nils Brandt, Emil Brandvold, Dario Kestrel, Nikolai Berresford, Gideon Halloway

**Milestone:** Consolidation and Provider Breadth, Pruning After the Sprint

---

## Status

- PR 565 (openai client backend, Dario) and PR 566 (deepseek api, Dario) both in review
  - PR 579 (Emil) covers overlapping ground from the batch side
  - team agreed: coordinate the three before any of them merges, otherwise we risk conflicts that are painful to untangle
- PR 468 (n samples support in generation params, Emil) still open, blocked on issue 52
- PR 581 (env var to disable rich, Gideon), straightforward change, just needs a reviewer pass this week
- PR 583 (param to disable metadata db, Nikolai), in review, no blockers reported
- Batch upload refactor and Pydantic model work (Nils), landed. Upload path is clean now, models no longer carry raw dicts through the pipeline. happy with how that came out
- Blocks and Recipes RAFT work (WS-044, Emil), in flight. RAFT and SimpleStrat strategies being wired in this week

## Open Questions

These are all carried forward, none resolved this meeting.

- issue 52: multiple samples per request, no decision yet; PR 468 cant move until this is settled
- issue 102: returning plain dicts vs Pydantic objects per row, still open
- issue 121: should we handle pydantic-to-dict and back for the user automatically when adding to a row, still open (related to 102 but not the same question)
- issue 124: `inspect(func)` cache invalidation is sensitive to comments and whitespace changes, no fix yet, off the top of my head this one is trickier than it looks
- issue 207 / issue 233: has_capacity implementation and auto-detecting rate limits, both open, need actual provider header data before we can do anything concrete here

## Provider Backends

OpenAI and DeepSeek are the immediate priority for provider breadth, that is what PR 565, 566 and 579 are all pointed at.

Mistral batch processor design is not aligned yet. We agreed it needs a dedicated discussion before anyone starts implementation, otherwise we will end up refactoring it again. TBD when that gets scheduled.

## Next Steps

- [ ] Coordinate PR 565 / PR 566 / PR 579 before any of the three merges
- [ ] Get reviewer eyes on PR 581 and PR 583 this week
- [ ] Schedule Mistral batch processor design discussion
- [ ] Keep issue 52 and issue 121 visible going into next planning cycle
