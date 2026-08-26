---
title: "Postmortem: Dec 10 revert of batch auto-delete"
author: dermot
created_at: 2024-12-11T09:14:00+00:00
---

# Postmortem: Dec 10 revert of batch auto-delete

**Date:** Dec 10 2024
**Status:** Reverted same day

---

## What happened

The batch auto-delete feature was meant to clean up completed batch job files after a run finished. It ran too early: it deleted the on-disk response cache before the end-of-run summary had read from it. Users saw a summary table with zeroed-out counts. In cases where the run had not fully written responses before the batch status flipped to complete, those responses are gone permanently, and resume is broken for those runs.

We reverted the same day.

## Impact

- Any run that completed while the feature was live may have a summary table showing incorrect (low or zero) hit and request counts.
- Runs that had not finished writing all responses before the batch status flipped lost those responses. Not recoverable.
- Resume is broken for affected runs because the request files were also removed.

I dont have a precise count of affected runs yet. Need to check with whoever owns the run logs to scope that.

## Root cause

The counters the summary table prints are computed lazily from disk, hits against the on-disk responses and requests that went out to the provider. When auto-delete removed those files before the summary ran, the counters read zero because the backing files were gone, not because no work had been done. The deletion was real; the reported counts were not.

The underlying problem is that auto-delete gated on completed batch status only, with no check that the summary had already consumed the files. The ordering dependency was implicit and nothing enforced it.

## Contributing factors

- No gate on summary completion before deletion ran, only on batch status.
- The lazy counter reads surface a missing file as zero rather than an error, so the failure mode was silent.
- No test covered the ordering between deletion and summary output.

## Timeline

- Dec 10, sometime in the morning: feature goes live (exact deploy time TBD, need to check deployment logs)
- Dec 10: user reports zeroed summary counts and broken resume
- Dec 10: reverted to prior behavior

## What went well

We caught it and reverted the same day. The revert path was clean, no secondary issues from rolling back.

## Action items

- [ ] Before re-introducing auto-delete: gate it explicitly on summary completion, not batch status alone
- [ ] Add a test that confirms summary counters match on-disk file counts before any cleanup runs
- [ ] Make a missing file surface as a warning or error rather than a silent zero (the lazy read behavior is a latent problem regardless of this feature)
- [ ] Scope the number of affected runs with whoever owns the run logs

The third item is worth doing independently of auto-delete. A counter reading zero because a file is absent is a bad failure mode to have sitting in the codebase.
