---
title: "Postmortem: Dec 13 revert of batch context-manager refactor (PR #254)"
author: konrad
created_at: 2024-12-16T08:51:00+00:00
---

# Postmortem: Dec 13 revert of batch context-manager refactor (PR #254)

Dec 16, 2024

---

## What happened

PR #254 refactored context-manager handling in batch mode. It merged on Dec 13 and was reverted the same day after it introduced instability in batch parameter management.

This was the third batch-mode revert in roughly ten days:

- Dec 4: end-of-run retry logic
- Dec 10: batch auto-delete
- Dec 13: context-manager refactor (PR #254)

Three reverts in ten days in the same area is not a coincidence. It points to something systemic about how batch parameter and lifecycle interactions are understood, or not understood, in this codebase right now.

## Timeline

- Dec 13, sometime after merge: instability observed in batch parameter management
- Dec 13, same day: revert issued
- Dec 16: this postmortem written

I do not have the exact merge and revert timestamps. Emil would have those from the commit log.

## Root cause

The refactor changed how batch state was scoped and torn down. The core problem was scope: the PR bundled a structural change (context-manager shape and lifetime) together with behavioral changes (parameter passing and cleanup sequencing). When one interaction misfired, there was no surgical rollback available. The only options were "all in" or full revert, and we reverted.

The specific interaction that misfired in the teardown sequence is not yet confirmed. That detail needs to come from Emil before any follow-on work starts.

## Contributing factors

- Structural and behavioral changes in one PR, so fault isolation was impossible
- No intermediate shippable state existed, which is what forced the binary choice
- The batch-mode area had already shown two fragile points in the preceding ten days, signaling that parameter and lifecycle interactions here are not yet well understood

## Impact

- No user-facing data loss
- Refactoring work lost, will need to be re-approached from scratch
- Adds weight to the pattern of batch-mode instability, which should increase caution on any upcoming work in this area

## What to change going forward

These apply especially to the planned SimpleLLM folding work, which will need to pass through batch parameter territory.

- Do not bundle structural refactors with parameter or lifecycle changes in the same PR. Separate them even if it feels slower.
- Any change that touches batch parameter sequencing should land in the smallest independent step that is both correct and revertable on its own.
- Before merging a refactor that changes context-manager scope, confirm the teardown sequence under both normal and error paths explicitly, not just the happy path.
- Treat the batch parameter surface as fragile until there is a clean, tested abstraction in place. We have now seen three data points that say it is.

## Open questions

- What specifically misfired in the teardown sequence? Need Emil to confirm before any follow-on PR is drafted.
- Do the three December reverts share a common root? My guess is yes, something about parameter state under certain batch configurations, but that is not confirmed.
- Is there a way to add test coverage over the context-manager teardown path so a future refactor has a signal before it merges? Not sure who owns that work or how hard it is to add.

## Status

Revert is complete. No follow-on PR is in flight as of Dec 16. The area is a known risk for SimpleLLM folding work and should be treated as such until the open questions above are answered.
