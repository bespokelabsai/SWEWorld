---
title: "Postmortem: Examples/Cookbooks Lint & Structured-Output Revert"
author: dermot
created_at: 2025-05-07T09:35:00+00:00
---

# Postmortem: Examples/Cookbooks Lint and Structured-Output Revert

**Date:** 2025-05-07
**Status:** Revert landed, corrected re-implementation in progress

---

## What Happened

A branch adding structured-output patterns to the cookbook examples made a capability assumption, specifically that all targeted models support structured output in the form the examples used. That assumption was not checked against the central model support table before the branch merged.

The lint step caught a formatting issue in the examples, which delayed the merge and caused some noise, but it did not catch the capability mismatch. Once the change landed, runs against models that do not support that form of structured output failed. The fix was a revert of the structured-output changes, followed by work on a corrected re-implementation that is not yet merged as of this writing.

## Impact

- CI pipeline blocked on the lint failure until the formatting issue was corrected
- Structured-output cookbook examples broken against a subset of targeted models post-merge
- Revert required, adding churn to the branch history and delaying the feature

I do not have a count of which specific models were affected or for how long before the revert landed. That detail should come from whoever owns the model compatibility test results.

## Timeline

```
~May 5  - branch opens, lint failure surfaces in CI (formatting)
        - formatting corrected, branch re-submitted
May 6   - branch merges
        - failures appear against models not supporting assumed structured-output form
May 7   - revert lands
        - re-implementation work begins (ongoing)
```

Exact times are TBD, I am working from memory of the review thread.

## Root Cause

The codebase already had at least three places tracking per-model capability information. The branch introduced a fourth dict rather than extending the existing support table. Because the central table was not updated, nothing else in the codebase could benefit from the correction, and more importantly the gate that should have caught the incompatibility was effectively bypassed.

The lint step was checking formatting, not capability correctness. There was no automated check that would have caught a branch referencing model capability outside the canonical table.

## What Went Well

- The lint step did catch a real issue (the formatting problem), even though it was not the one that mattered most
- The revert was straightforward, no data loss, no downstream service impact

## Action Items

- [ ] Extend the model support table to cover the structured-output capability constraint introduced by this branch. Do not leave the fourth dict in place.
- [ ] Add a lint or test step that catches capability references made outside the canonical support table. Not entirely sure what the right shape for that check is, need to look at what the table's access pattern actually looks like before writing the rule.
- [ ] Validate the prescription example and any new structured-output patterns against the support table before the re-implementation merges.
- [ ] Confirm with whoever owns the support table whether there is a documented process for extending it, or whether that process needs to be written down.

## Open Questions

- Which models were affected and is that list now fully captured in the support table?
- Is the re-implementation being reviewed against the support table in the current PR, or is that being left to a follow-up?
- The three pre-existing capability dicts: are any of them now redundant? That would be worth cleaning up while attention is on this surface, but I have not looked at them in detail.

---

*Look, we need to stop growing parallel capability structures every time someone adds a new model constraint. The support table is cheap to extend and everything reading it improves immediately. If your branch depends on what a model can do, the right move is to look it up in the table and add the pattern there if it is missing.*
