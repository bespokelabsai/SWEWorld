---
title: "Postmortem: Dec 10 revert of batch auto-delete"
author: dermot
created_at: 2024-12-11T09:00:00+00:00
---

# Postmortem: Dec 10 revert of batch auto-delete

**Date:** Dec 10 2024
**Status:** resolved, revert clean

---

## What happened

The batch auto-delete feature shipped in the prior release. During internal testing it became clear the delete logic could remove on-disk response files that a resumed run would still need. The commit was reverted the same day.

No external users were affected. No data was permanently lost.

## Root cause

The auto-delete was keyed on a per-request completion flag rather than on the per-run counters that drive the summary table. Those counters track two things: on-disk responses received, and requests actually sent out to the provider. Those two numbers are what the summary table prints at the end of a run, and they are the canonical measure of whether a run is complete.

The problem is that the completion flag and those counters are not kept in sync. A request that had gone out to the provider but whose response had not yet been written back to disk could have its flag set in a state the delete logic read as "done." So the delete could run, remove the file, and leave a resume with nothing to read.

In a clean, uninterrupted run this probably would not have triggered. In a partially completed or interrupted run it was a real data hazard.

## What went well

Caught in internal testing before it reached any external users. The revert was clean and straightforward. No recovery work was needed.

## Action items

- [ ] Any future batch auto-delete implementation must gate deletion on the existing per-run hit counters (on-disk responses + requests sent), not on a separate completion flag.
- [ ] Add a note to the batch-mode design doc flagging this constraint before the feature is re-attempted. I'll do this today.
- [ ] The summary table counters are now explicitly the canonical source of truth for run completeness. Anything acting on completion state reads from those, full stop.

## Open questions

The feature itself is not ruled out, just reverted. I don't have a timeline for when it gets re-attempted or who picks it up. That needs a decision, but not urgently.
