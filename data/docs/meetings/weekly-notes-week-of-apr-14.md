---
title: "Weekly Notes \u2014 Week of Apr 14"
author: gideon
created_at: 2025-04-16T10:03:00+00:00
---

# Weekly Notes, Week of Apr 14

## Merged

- PR 632, CLI batch update frequency fix, merged earlier this week
  - was blocking some local testing so glad thats out

## In Flight

- PR 640, OpenAI and DeepSeek API support
  - still open, needs review
- PR 642, GPT-4.1 structured output
  - tied somewhat to 640 in terms of ordering, not a hard dependency but makes sense to sequence them
- PR 643, CuratorResponse object
  - early but moving

## WS-050 Batch Mode (with Emil)

Ongoing work here. Emil is taking the lead on some of the infrastructure side, I'm handling the API layer and how cost gets surfaced. Not blocked but there are open questions I havent pinned down yet (see below).

## Gemini 2.0 / 2.5 API Incompatibility

Triaged this. The short version is that there's a breaking difference in how the Gemini 2.0 and 2.5 APIs behave compared to what we currently expect, but it doesnt block anything in the current sprint. Moved to backlog as non-blocking. We'll need to come back to it before doing a serious Gemini push.

## Cost-Streaming Pattern, Needs Docs Before Next Sprint

I want to flag this before we get into next sprint's provider work. The cost-streaming pattern we're using is not documented anywhere and it will matter the moment someone else tries to add a provider. I think we should write it down this week or early next, before the PRs in flight land and the pattern starts spreading. I can draft it but want to check if Emil has context I'm missing first.

## Open Questions

- Projected-remaining readout: what should the UI show when cost-streaming is delayed or incomplete? Does it show last known? Does it block? I dont have a clear answer here and I'm not sure who owns that decision.
- Batch vs online cost representation: how do we align the cost number the user sees in batch mode with what they'd see in online mode? They probably should not be directly comparable but I dont know if thats documented as intentional anywhere.

These two are related and probably need a short sync before PR 640 goes much further.
