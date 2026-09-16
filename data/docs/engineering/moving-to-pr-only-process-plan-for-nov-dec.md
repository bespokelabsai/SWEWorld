---
title: "Moving to PR-only: process plan for Nov/Dec"
author: konrad
created_at: 2024-11-07T14:23:37+00:00
---

# Moving to PR-only: process plan for Nov/Dec

## Why now

We have 3 changes merged and two workstreams (examples-cookbooks, release-and-ci) actively in flight. This is the right moment, because everything that comes after this point should be built under the policy from the start rather than retrofitted later. Waiting until the workstreams expand further just means more cleanup.

## What "PR-only" means here

No direct pushes to main. Every change, however small, goes through a pull request with at least one reviewer sign-off before merge. Maintainers are not exempt from this.

## Rollout

### November

- All in-flight PRs starting with PR 4 go through review under the new policy
- Any draft or exploratory branches that predate the policy either get converted to PRs or discarded, nothing lands from a branch that bypassed review
- CI checks from the release engineering plan get wired up and enforced on merge
- Each subsystem that ships a PR in November also ships a short "what to review" section in the PR description, so reviewers arent guessing at scope

### December

- Policy treated as stable; no exceptions without a recorded reason in the PR itself
- Turnaround expectation: one business day for non-blocking PRs; same day where possible for anything blocking another workstream
- End of December: brief retro in #engineering on what slowed reviews down, any tweaks needed going into the new year

## Reviewer expectations

What a review is expected to cover:

- Correctness relative to what the PR claims to do
- Whether the change introduces a pattern that needs to be documented or discussed before it spreads
- Whether tests cover the new behavior

What a review is NOT expected to be: exhaustive code archaeology. A review that asks one sharp question and gets a satisfying answer is a good review. We're not trying to make reviews a bottleneck.

## What counts as done

- [ ] PR 4 merges under the policy
- [ ] Every subsequent PR in the milestone has a reviewer listed before it merges
- [ ] CI enforcement is live (tracked in the release engineering plan, not here)

## Open items

- Reviewer assignment is currently informal, whoever is around. If turnaround starts slipping in December we revisit with a rotation, but I dont want to add process before theres a problem.
