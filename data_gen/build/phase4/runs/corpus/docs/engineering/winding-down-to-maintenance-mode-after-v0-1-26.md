---
title: "Winding down to maintenance mode after v0.1.26"
author: konrad
created_at: 2025-06-02T09:14:00+00:00
---

# Winding down to maintenance mode after v0.1.26

## What changes after the cutover

Team capacity drops sharply once v0.1.26 ships. Most contributors are moving onto other priorities and will not have regular bandwidth for Millrow. Reviews will be slower, expect days rather than hours for a response on a PR. That is the new normal, not a sign something went wrong.

Scope is narrowed to bug fixes and small maintenance changes only. New features are not being accepted in this period. If you open a feature PR it will sit, and I will eventually close it with a note.

## Work still in flight

These PRs are active and will be worked through before or shortly after the cutover:

- PR 653: Shreyas/finetuning client
- PR 663: fix error when torch isn't installed
- PR 675: add default app id parameter for curator llm
- PR 681: if the model is not known, let the cost be None

Open issues 52, 102, 121, 124, 207, 233, 290, and 293 remain unresolved. None of them are blocked on anyone in particular, they are simply deferred. I would not expect movement on them during dormancy unless a contributor picks one up on their own initiative.

## Expectations going forward

If you open a PR, assume the review cycle is slow. A PR sitting for a week with no comment is in the queue, not abandoned.

If you find a regression, file it. We will triage. Silence does not mean it is off our radar.

There will be periodic lightweight check-ins from maintainers, but no standing weekly cadence after v0.1.26 ships.
