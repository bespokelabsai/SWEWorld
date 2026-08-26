---
title: "Weekly sync notes: week of Jan 13 \u2014 v0.1.15 and v0.1.15.post1 shipped"
author: dario
created_at: 2025-01-15T09:56:00+00:00
---

# Weekly sync notes: week of Jan 13 - v0.1.15 and v0.1.15.post1 shipped

**Date:** 2025-01-15

---

## Shipped

- v0.1.15 out earlier this week
- v0.1.15.post1 same-day hotfix, also out
    - cost calculation regression: was dividing by requests instead of minutes, so longer runs were coming out overcharged
    - typo in the first docs example
    - README updated to reflect the current LLM class interface (post-refactor)
- hotfix announcement sent to the team

## In review

- PR 133
- PR 161
- PR 362

no blockers on any of these as of sync time

## Still open

- example scripts against the current LLM interface: not yet confirmed clean, verification still in progress
    - need someone to sign off on these before we call the interface docs settled

## Notes

nothing else flagged as blocking. post1 was a quick turnaround and honestly went smoother than expected for a same-day fix.
