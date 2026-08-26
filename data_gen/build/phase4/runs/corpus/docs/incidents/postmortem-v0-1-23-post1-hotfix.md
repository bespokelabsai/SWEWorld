---
title: "Postmortem: v0.1.23.post1 Hotfix"
author: dermot
created_at: 2025-04-14T09:14:00+00:00
---

# Postmortem: v0.1.23.post1 Hotfix

**Date:** 2025-04-14
**Release affected:** v0.1.23
**Hotfix release:** v0.1.23.post1
**Status:** Hotfix shipped. Follow-up items open.

---

## What Happened

v0.1.23 shipped and a behavioral regression was identified shortly after. The regression was in a code path that existing pre-release checks did not exercise, so it was not caught before the release went out. We scoped a minimal fix, reviewed it, and cut v0.1.23.post1. No full release cycle was run for the hotfix.

The regression was behavioral, not data-related. No records were corrupted or lost.

## Impact

- Users on v0.1.23 between the initial release and the hotfix deployment were affected.
- Exact number of affected users and duration of the window: I do not have this. Whoever owns the deployment telemetry would have it.
- No data loss.

## Timeline

I do not have the precise timestamps for these. Need to pull them from the release log before this postmortem is considered closed.

- v0.1.23 shipped
- Regression identified (post-release, exact report time unknown)
- Fix scoped and reviewed
- v0.1.23.post1 released

## Root Cause

The regression was introduced by a change included in v0.1.23. The affected code path was not exercised by the checks running at the time of pre-release review, so the failure mode was invisible until users hit it in production.

That said, this is not simply a gap in test coverage in the narrow sense. The pre-release verification gate itself did not require that this class of change demonstrate coverage of the affected path before merging. The coverage gap and the gate gap are two separate things and both need addressing.

## What Went Well

- The fix was scoped tightly. We did not expand scope under pressure, which kept the hotfix review fast and low-risk.
- The decision to cut a post release rather than hold and do a full v0.1.24 cycle was correct given the nature of the regression.

## Action Items

- [ ] Add coverage for the affected code path so this regression class is caught pre-release (owner TBD, needs to be picked up this sprint)
- [ ] Review the pre-release verification gate for changes touching this area of the codebase, specifically whether there should be a required check before such changes can merge
- [ ] Reconstruct the full timeline with actual timestamps and update this document

The second item is the one I am less sure how to scope. Not entirely sure whether that is a policy change to the merge process, a CI gate change, or both. Need to get the right people in a room before writing that up as a concrete task.
