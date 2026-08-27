---
title: "Weekly update: week of Apr 7"
author: dermot
created_at: 2025-04-14T09:42:00+00:00
---

# Weekly update: week of Apr 7

## What shipped

- v0.1.23 released, then v0.1.23.post1 hotfix cut shortly after
  - postmortem is in the postmortems collection if you need the detail
- PR 631 in review: projected-total and projected-remaining readout improvements
- PR 632 up: batch update frequency fix in the curator CLI
- PR 626 in progress: metadata schema update, adding cost fields
- PR 634 in progress: OpenAI and DeepSeek provider support

## In flight

- Batch statistics account checkpointed, but not yet validated, needs someone to run a pass on it
- Provider cost metadata consistency across backends is still an open question (see issue 293)
- Merge ordering matters here: PR 632 should land before PR 626 or we will have conflicts

## Open question

Look we need to settle this before PR 626 gets any further: is cost metadata coming back consistently across provider backends, or are there gaps depending on which provider you hit?

I dont have a clear picture of this yet. If the gaps are real, it affects how the schema in PR 626 needs to be structured, so i would rather know now than after the PR lands. If anyone has run requests against multiple backends recently, say so. Issue 293 has some of the thread but i am not sure it is current.
