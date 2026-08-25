---
title: "Postmortem: Dec 10 revert of batch auto-delete"
author: dermot
created_at: 2024-12-11T09:14:00+00:00
---

# Postmortem: Dec 10 Revert of Batch Auto-Delete

**Date:** Dec 10 2024
**Status:** Resolved (reverted same day)

---

## What happened

On Dec 10 we merged a change to batch-mode that automatically deleted on-disk request and response files at the end of a run, once the summary table had printed. The logic keyed on the per-run counters: if the run completed and the counters were non-zero, the files were removed.

The change was reverted the same day. The assumption underneath it was wrong. Those files are not intermediary scratch that can be discarded once the run is done. Users read them after a run to audit what was sent and what came back from the provider. Deleting at end of run destroyed data that had not yet been consumed.

## Timeline

```
Dec 10 AM   change merged to batch-mode
Dec 10      issue identified: post-run files gone, users cannot audit
Dec 10      change reverted
Dec 11      this postmortem written
```

## Root cause

The counters batch-mode keeps per run track requests that went out to the provider and responses that came back on disk. Those are exactly the two numbers the summary table prints. A counter reaching its expected value tells us the run completed cleanly. It says nothing about whether anyone has read the output files since.

Auto-delete keyed on those counters was keyed on the wrong signal entirely. A completed run is not the same as a consumed run. No explicit contract existed for the lifecycle of on-disk run artifacts, so the delete logic filled a gap that was never formally scoped. That absence of a defined lifecycle is the real root cause. The counter logic was correct for what counters are supposed to measure.

## Impact

Users who ran batch-mode on Dec 10 after the merge lost access to their on-disk request and response files immediately on run completion. I do not have a count of how many runs were affected between merge and revert. Whoever can pull that from the logs should add it here.

The data loss was silent: the run appeared to complete normally, and the summary table printed as expected. There was no error, no warning.

## Contributing factors

- No lifecycle policy for run artifacts. The files existence post-run was implicit, never documented.
- The change passed review without a case being raised for post-run file access patterns.
- batch-mode has no integration tests that verify file presence after a completed run. A test covering that would have caught this.

## What we are doing

- Auto-delete is reverted and will not come back without a documented artifact lifecycle policy first.
- Any future cleanup feature must be opt-in, a flag or a separate sweep command. Not default behavior.
- Issue 48 (README documentation on batch) should pick up artifact lifecycle as part of its scope. Not entirely sure who is driving 48 right now, so someone needs to make sure this gets added to it explicitly.

- [ ] Confirm scope of issue 48 includes artifact lifecycle
- [ ] Establish written lifecycle policy for on-disk run artifacts before any cleanup feature is reopened
- [ ] Add integration test: file presence after completed run

## What we are not changing

The counters are correct and useful. They measure exactly what the summary table reports, requests out to the provider and responses back on disk. That is the right thing to count. The mistake was using them to gate a delete, not the counting itself.

## What went well

The issue was caught and reverted the same day. The revert was straightforward, no secondary failures.

## Open questions

- How many runs were affected between merge and revert? Needs someone with access to run logs.
- Should we define a default retention period for run artifacts, or leave that entirely to the user? That decision should happen before issue 48 closes.
