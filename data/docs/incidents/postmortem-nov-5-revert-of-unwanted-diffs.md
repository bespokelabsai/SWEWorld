---
title: "Postmortem: Nov 5 revert of unwanted diffs"
author: dermot
created_at: 2024-11-06T10:29:32+00:00
---

# Postmortem: Nov 5 Revert of Unintended Examples Diffs

**Date of incident:** 2024-11-05
**Postmortem written:** 2024-11-12
**Status:** open, root cause not confirmed

---

## What happened

A merge to main was reverted on Nov 5 because it included unintended changes to examples/poem.py and examples/distill.py. Neither file was in scope for the authoring branch, and neither should have appeared in the diff. The revert was necessary to restore main to a clean state.

The files in question are owned by the examples-cookbooks subsystem. Nothing on the PR branch was intended to touch that layer.

## Impact

- main was in a bad state from the time of merge until the revert, roughly in the Nov 5 window (exact timestamps still needed from whoever owns the merge log)
- one merge reverted
- no downstream breakage confirmed as of writing

The blast radius was small. The revert was caught before anything downstream consumed the bad state, which is the main thing.

## Timeline

Exact timestamps still needed here. What I have:

- Nov 5: PR merged to main
- Nov 5: unexpected diffs in examples/poem.py and examples/distill.py noticed (not sure by whom or how, need to confirm)
- Nov 5: revert executed, main restored

If anyone has the actual commit times from the merge log, please add them.

## Root cause

Not confirmed yet. Two leading candidates:

- **Rebase artifact.** If the branch was rebased at some point before the PR opened, or during review, it is possible that a stale or conflicting version of the examples files was pulled in without being noticed in the diff review.
- **Untracked editor state.** Local changes to examples/poem.py or examples/distill.py that were not staged intentionally but were picked up during a commit.

I am not confident enough in either to call it. We need the branch history looked at, specifically the rebase points and any commit that touched examples/. I do not own that investigation myself and am not sure who the right person is to pull the git log apart, need team input here.

## What went well

The bad state on main was caught and reverted the same day. No downstream system consumed the broken state as far as we know. The revert itself was clean.

## Prevention options

Three options are on the table. The team needs to agree on one before this is closed.

- **Pre-merge review gate.** Any PR whose diff touches examples/ must get explicit sign-off from the examples-cookbooks owner before it can merge. No CI change required, just process.
- **CI check.** Add a check that fails the merge if a PR not scoped to the examples-cookbooks layer modifies any file under examples/. This is probably the most reliable option long term, but I am not entirely sure what the right way to scope "not scoped to that layer" is in CI terms, someone needs to look at what we have available.
- **Explicit sign-off requirement.** Similar to the first option but formalised, a required reviewer or approval step tied to the examples-cookbooks owner rather than a convention.

That said, these options are not mutually exclusive. The CI check catches accidents mechanically; the sign-off process handles cases where a PR legitimately needs to touch examples/ and just needs the right eyes on it. My instinct is we want both, but I am not pushing for that until the team has looked at the CI side.

## Open questions

- Exact timestamps for the merge and revert?
- Who noticed the bad diff and how? (matters for understanding whether the review process almost caught this)
- Which rebase points are in the branch history, and do any of them correlate with the examples/ changes appearing?
- Is the CI approach feasible with our current pipeline setup? Need someone who knows the pipeline config to answer this.

## Action items

- [ ] Confirm root cause by examining branch history, specifically rebase points and any commit touching examples/
- [ ] Team to agree on prevention approach before closing this incident
- [ ] Add exact timestamps to timeline once merge log is available
