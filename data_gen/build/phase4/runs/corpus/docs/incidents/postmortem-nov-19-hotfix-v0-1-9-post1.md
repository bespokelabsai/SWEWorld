---
title: "Postmortem: Nov 19 hotfix (v0.1.9.post1)"
author: gideon
created_at: 2024-11-20T09:35:00+00:00
---

# Postmortem: Nov 19 hotfix (v0.1.9.post1)

Released Nov 19, 2024. Written Nov 20.

---

## What happened

v0.1.9 shipped with a behavior regression in the request pipeline. The regression was caught after the release was out, a fix was scoped and prepared, and v0.1.9.post1 went out the same day. No data loss, no API contract changes.

The incident was low severity in terms of impact, but the hotfix added unplanned release work and surfaced a gap in pre-release coverage for that code path.

## Timeline

Exact times not recorded here, will update if someone has them logged.

- v0.1.9 ships
- Regression identified in the request pipeline post-release
- Fix scoped, patch prepared
- v0.1.9.post1 cut and released, Nov 19

## Root cause

A change introduced in v0.1.9 altered behavior in the request layer in a way that was not intended. The specific code path affected did not have sufficient test coverage to catch this before the release went out, so the failure mode surfaced in the pipeline after the fact rather than in CI.

The gap is in coverage, not in the change itself. The change appears to have been reasonable in isolation; the problem is that the affected path had no test asserting the old behavior, so nothing caught that the behavior had changed.

## What went well

- Regression caught and reported quickly after the release
- Fix was self-contained, low risk, and easy to reason about
- Emil turned the CI and release around without blocking the team for long

## What could be better

The request layer coverage for this path was thin. There is no clean way to say that differently. Whether that is because the path is hard to test, or just because coverage grew unevenly over time, I am not sure, and honestly that distinction matters for what we do next.

The window between v0.1.9 shipping and the hotfix was longer than it needed to be, though I do not have the exact gap to put a number on it. If anyone has that in the CI logs it would be worth recording.

## Action items

No action items formally assigned as of this writing.

The related issues 33, 55, and 57 all touch the request layer and are worth keeping in mind when we do address coverage there. None of them are blocked on this postmortem, they were already on the backlog.

## Open questions

- Do we want a coverage requirement or a targeted test added for the affected path before v0.1.10 goes out, or is this a one-off?
- Who is the right person to own a coverage audit of the request layer more broadly? (I would not assume that falls to me without a conversation.)
