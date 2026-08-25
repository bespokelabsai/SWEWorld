---
title: "Postmortem: Nov 23 revert to old LiteLLM backend"
author: gideon
created_at: 2024-11-25T09:28:00+00:00
---

# Postmortem: Nov 23 Revert to Previous LiteLLM Backend

**Date of incident:** Nov 23, 2024
**Hotfix release:** v0.1.9.post1
**Status:** Resolved. Follow-up tracked in PR 141.

---

## What Happened

A new LiteLLM backend landed with the intent of adding structured output support via instructor. Shortly after, structured output requests began failing in a way that had not surfaced during pre-merge review. The decision was made to revert to the prior stable backend rather than attempt a patch on something we did not yet fully understand.

The revert went into v0.1.9.post1. Because structured output via instructor was a new capability rather than an existing one, the revert did not take anything away from users that had been working before.

## Impact

- Structured output via instructor: unavailable from the time the new backend landed until v0.1.9.post1 shipped
- All other curator functionality: unaffected
- No data loss, no corruption of existing outputs

The window was short and the capability was new, so actual user impact was low. That said, anyone who had already started integrating the instructor path would have hit failures without a clear error message explaining why. I dont have a count of how many users were in that state.

## Timeline

- Nov 23: new LiteLLM backend merges
- Nov 23: structured output failures reported
- Nov 23: decision made to revert rather than hot-patch
- Nov 23: revert lands, v0.1.9.post1 released

I dont have the exact times for each of these. If we need them for a more detailed record, they should be in the git log and release notes.

## Root Cause

The new backend changed how responses were parsed when using instructor. The prior backend had an implicit contract about response shape, and the integration between LiteLLM and instructor had edge cases that were not covered in review.

Honestly, this is the kind of thing thats easy to miss in review because the failure mode only shows up with certain request shapes. A unit test against the happy path would not have caught it. What would have caught it is a broader set of structured output request shapes exercised before merge, or a smoke test that specifically targets the instructor integration path. Neither of those existed.

## What Went Well

- The decision to revert rather than patch was made quickly, which kept the unstable surface from sitting in production while we debugged
- Because the capability was new, the revert was clean and did not remove anything users depended on
- v0.1.9.post1 shipped the same day

## Action Items

- [ ] Add a smoke test for the instructor integration path so this class of regression is caught in CI (needs an owner, I'd suggest whoever is driving PR 141)
- [ ] Run a broader set of structured output request shapes against the new backend before PR 141 merges, not just the happy path
- [ ] PR 141 review criteria should explicitly include: does this pass against malformed or edge-case response shapes?

PR 141 is the corrected implementation and is a blocker for v0.1.11. The lessons here are meant to feed directly into the review criteria for that PR before it merges.

## Open Questions

- Do we know which request shapes specifically triggered the failure? If someone captured the failing payloads, that should go into PR 141 as a test case.
- Is there a way to gate structured output capability behind a feature flag so a future regression here is isolated more easily? I dont know enough about the current architecture to say whether thats realistic, but its worth asking.
