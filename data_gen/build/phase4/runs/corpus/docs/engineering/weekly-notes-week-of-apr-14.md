---
title: "Weekly Notes \u2014 Week of Apr 14"
author: gideon
created_at: 2025-04-16T09:14:00+00:00
---

# Weekly Notes, Week of Apr 14

## In flight

- WS-050 (Emil): batch mode work ongoing
  - async batch API support at ~50% cost reduction
  - PR 468 (n samples in generation params) still open, not merged yet
- PR 632 (me): CLI batch update frequency fix
  - blocking CLI observability finalization, needs review before that work can close out
  - if youre waiting on something here, please prioritize it
- PR 640 (Tomas): OpenAI + DeepSeek API support, in review
- PR 642 (Devraj): GPT-4.1 structured output support, open for review
- PR 643 (Emil): Response object in curator, open
  - potential overlap with PR 642 on the structured output mapping side, need to confirm before either merges

## Decisions / notes

Milestone focus stays on provider breadth and consolidation. We're not expanding scope this sprint.

The GPT-4.1 structured output path needs a call or at least an async thread before PR 642 and the batch work (mine) both land. I dont think they diverge badly but i haven't looked closely enough at Devraj's mapping layer to be sure. Someone needs to own that check and it probably shouldn't be me, since im too close to the batch side.

Cost streaming pattern, we agreed this needs to be documented for future provider integrations. Nobody wrote that doc yet. TBD on who picks it up.

## Open issues (no resolution this week)

- issue 52: multiple samples per request
- issue 207: `has_capacity` via rate limit headers
- issue 233: auto-detect rate limits
- issue 102, 121, 124, 290, 293: (haven't pulled these up, carrying them forward from last week)

## Questions

- PR 643 vs PR 642 overlap: confirmed or not? who's checking?
- cost streaming doc: who owns this?
