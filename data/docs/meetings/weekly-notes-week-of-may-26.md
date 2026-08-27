---
title: "Weekly Notes \u2014 Week of May 26"
author: emil
created_at: 2025-05-28T09:28:00+00:00
---

# Weekly Notes, Week of May 26

## In-flight PRs

- PR 652 (viewer dataset download), open 33 days, no reviewer assigned
  - blocking curator-viewer integration work
  - needs eyes before anything else can happen here
- PR 653 (finetuning client), open 32 days, awaiting review
- PR 663 (torch import fix), open 21 days, contained change, still waiting
- PR 675 (default app id param for curator llm), in review, seems closest to landing

PR 652 and 653 being open this long is starting to be a real problem. 33 days is too long for something that's actively blocking integration work.

## Release

Currently at v0.1.24. Release criteria for v0.1.25 are not confirmed yet, which is the blocker before we can properly plan the next push.

Open question: does PR 663 need to land before v0.1.25 cuts? Same question for PR 653. If i had to guess, 663 probably does (it's a fix, not a feature), but I haven't confirmed that with anyone. Let's circle back on that once we know which PRs gate the release.

## Services (Emil)

All four active this week:

- agentic-curation
- batch-mode
- blocks-and-recipes
- local-offline-inference

Nothing resolved, nothing closed. Will carry forward next week unless something changes.

## Blockers

- PR 652 has no reviewer, this is the immediate thing to fix, curator-viewer integration doesnt move until this merges
- v0.1.25 release criteria still undefined, which makes it hard to prioritize anything

## Open Questions

- Issue 290 (`ModuleNotFoundError: No module named 'resource'`), unclear whether PR 663 actually addresses this. Needs someone to confirm before we close it.
- Issues 52, 102, 121, 124, 207, 233, 293, all still open, no movement this week. Not tracking them individually here until something changes.
