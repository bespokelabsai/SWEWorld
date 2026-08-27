---
title: "Release engineering & CI/test-suite plan"
author: konrad
created_at: 2024-11-01T09:14:00+00:00
---

# Release engineering & CI/test-suite plan (Millrow)

## Goals

All changes to Millrow reach main through a reviewed PR. No direct pushes. CI must pass before merge is allowed, enforced at the branch protection level.

## CI pipeline shape

Checks run in this order on every PR:

1. Lint and type-check
2. Unit tests for the subsystem touched by the PR
3. Integration smoke test (online-request-processing path, stubbed provider, no real API calls)
4. Verifier self-test for any code-execution verifier touched by the PR

1 and 2 run in parallel. 3 only starts if both 1 and 2 pass. 4 runs in parallel with 3.

The logic here is that lint/unit failures are cheap to catch and there's no point spending time on the integration run if the basics are broken. Makes sense to keep it that way even if the ordering adds a little latency.

## Test coverage expectations

No numeric coverage threshold is enforced. What IS expected: any PR that changes runtime behavior includes or updates tests for that behavior. A PR with no test changes that touches the runtime path should be flagged in review, not merged silently.

- reasoning-dataset pipelines (examples-cookbooks) tested by running example notebooks in headless mode and asserting output schema matches expected shape
  - these are slow, so they're gated behind the `run-notebook-tests` CI label
  - not triggered on every push, only when label is applied or on release runs

## Release process

Tag-and-publish. No manual steps in the middle.

- tag main with a semver tag (v0.4.0 style)
- release-and-ci picks up the tag, runs the full suite including notebook tests
- on success, publishes the release artifact and generates changelog from merged PR titles since the last tag
- PR titles must be descriptive, thats where the changelog comes from, no manual editing

One thing to flag here: if PR titles are vague ("fix bug", "wip", etc.) the generated changelog is useless. This is a review hygiene thing, not something we can automate around. Worth calling out in the contributing guide.

## Rollback

If a release introduces a regression, rollback is: revert the offending PR on main, cut a patch release. Hotfixes do not bypass the PR process, same pipeline applies.

## Open items

- [ ] Stub provider for the integration smoke test is not implemented yet. Until it is, the integration check (step 3) is skipped and CI output notes why. Someone needs to scope and build this before we can rely on the smoke test for anything.
- [ ] Notebook test infrastructure (headless run + schema assertion) scoped to a future PR, not yet started
- [ ] Contributing guide needs a section on PR title expectations given the changelog generation dependency

TBD: who owns the release-and-ci service configuration, I need to check with whoever set that up originally.
