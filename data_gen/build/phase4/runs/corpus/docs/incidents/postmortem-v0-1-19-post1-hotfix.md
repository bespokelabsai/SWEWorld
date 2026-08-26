---
title: "Postmortem: v0.1.19.post1 hotfix"
author: konrad
created_at: 2025-02-27T09:14:00+00:00
---

# Postmortem: v0.1.19.post1 Hotfix

v0.1.19 shipped a regression in the Anthropic backend that caused generation requests to fail under certain parameter configurations. We caught it via user reports the same day, identified the root cause, and shipped v0.1.19.post1 as a fix within the same day. This doc covers what broke, how we found it, and what we are changing.

## Impact

Users on v0.1.19 who hit the affected model/mode combination got API errors and could not complete generation runs. The only workaround was pinning back to v0.1.18. We do not have exact numbers on how many users were affected, since we dont currently track that. Anyone who upgraded on release day and used Anthropic was likely to hit it depending on their config.

## Timeline

- v0.1.19 cut and published to PyPI
- First failure reports came in from users shortly after release
- Root cause identified: a generation parameter was being passed to the Anthropic client that the API rejects in certain model/mode combinations
- Fix implemented, reviewed, and merged
- v0.1.19.post1 published; verified against the reported failure cases

I dont have exact timestamps for these steps. Worth capturing that in future incidents.

## Root Cause

A change to how generation parameters were passed to the Anthropic client introduced a parameter that the API accepts in some model contexts but rejects in others. The problem is that it fails silently in the cases we were testing and only raises an error in specific combinations we didnt have in our test matrix. So our local smoke tests passed, and the regression shipped.

This is a tricky class of bug because the API itself is inconsistent about it. A parameter that works fine with one model raises an error with another, with no obvious signal during development that you are on a boundary.

## What Went Well

- Turnaround was fast. Report to hotfix published, same day.
- The fix was narrow and well-scoped, no other surface area touched.
- No data loss or corruption, the failures were clean errors not silent bad output.

## What Could Be Better

- The affected parameter combination was not in our test matrix. We had coverage for the happy path but not for the edge cases across model/mode combinations. The Anthropic API has enough variation here that we probably need to be more deliberate about it.
- We had no pre-publish smoke test that actually exercises the Anthropic backend against real API calls. Our pre-release checks were all local and did not catch this.

## Action Items

- [ ] Expand generation-param test coverage to include edge-case model/mode combinations for the Anthropic backend (at minimum the combinations that surfaced in this incident)
- [ ] Evaluate adding a lightweight pre-publish integration check against the Anthropic API before cutting a release tag. Not sure what the right shape is here (cost, secrets in CI, etc.), needs a conversation before we commit to an approach.

## Open Questions

- Do we want a way to track affected-user counts for incidents like this? Right now we are guessing. Not sure who owns that or what it would take.
- Is there a way to validate Anthropic parameter combinations without making real API calls, or do we just have to test against the live API? I dont know enough about their client internals to say.
