---
title: "Weekly sync notes: week of Jun 16"
author: nikolai
created_at: 2025-06-18T09:14:00+00:00
---

# Weekly sync notes: week of Jun 16

## PRs in flight

- **PR 690** - Fix Multimodal Gemini Batch Request Creation (Emil)
  - needs review, currently blocked waiting on someone to pick it up
  - should be straightforward but havent looked at it myself yet
- **PR 691** - feat: auto batch mode (Emil)
  - open question: does this block the next release? not settled as of today
  - need to decide before we cut anything
- **PR 653** - finetuning client, Shreyas + me
  - in review, my part is done, waiting on feedback
- **PR 675** - add default app id param for curator llm (Nolan)
  - in review

## Release status

Currently at v0.1.25. Nothing cut this week yet.

Milestone coming up: **Lights Left On** (Dormancy After v0.1.26). That's the next meaningful target. The auto batch mode question (PR 691) is the one i'd want resolved before we think about v0.1.26 seriously.

## code-execution service

Still in flight, mine. No blocker right now but not done.

## Open questions (carried over)

Most of these are just sitting there. Listing them so they dont fall off the radar.

- issue 52 - multiple samples per request
- issue 102 - return dict without Pydantic objects
- issue 121 - pydantic to dict handling
  - 121 and 102 feel related, if i had to guess resolving one probably touches the other
- issue 124 - inspect cache invalidation on whitespace
- issue 207 - has_capacity via rate limit headers
- issue 233 - auto-detect rate limits
  - 207 and 233 are also clearly in the same area, should probably be looked at together
- issue 290 - ModuleNotFoundError resource
- issue 293 - OpenAI usage and costs via API

Nobody has picked up owners for most of these. TBD on who takes what before v0.1.26.
