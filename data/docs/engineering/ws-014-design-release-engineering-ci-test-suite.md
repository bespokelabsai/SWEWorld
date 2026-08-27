---
title: "WS-014 design: Release Engineering, CI & Test Suite"
author: dermot
created_at: 2025-01-06T09:14:00+00:00
---

# WS-014 Design: Release Engineering, CI & Test Suite (Millrow / Stratos Crunch)

## Scope

Covers how releases are cut, what CI must pass before a merge lands, and the structure of the test suite. Does not cover provider-specific integration testing (that is WS-016) or example/cookbook validation, which is owned separately under examples-cookbooks.

## Release Process

Releases follow a linear version scheme: `0.1.x` for the current milestone. A release is cut from main when all of the following are true:

- All in-flight PRs targeting the release are merged or explicitly deferred
- CI passes clean on main, meaning no skipped checks and no suppressed failures
- The changelog entry is written and reviewed
- The release owner (currently me, Dermot Callaghan, for Stratos Crunch) has signed off

Patch releases (`0.1.x+1`) are reserved for regressions found after a minor ships. No feature work in a patch, full stop.

## CI Pipeline

Runs on every PR and on every push to main. Stages are sequential; a failure blocks everything downstream.

### Stage 1 - Lint and format

- `ruff check` for style and import hygiene
- `ruff format --check` to catch unformatted diffs
- Failures here are almost always under a minute to fix; contributors are expected to run this locally before pushing

### Stage 2 - Unit tests

- No network, no provider credentials
- Must complete under 3 minutes wall-clock (currently well inside that, but I want it on record)
- Coverage threshold: 80% line coverage on changed files
    - Soft gate for now (warning only) until the threshold is met consistently for two consecutive releases, then it hardens
    - not entirely sure when we cross that line; I'd say after 0.1.14 is realistic

### Stage 3 - Integration smoke

- Requires provider credentials injected as CI secrets
- Runs a minimal end-to-end path: one online request, one batch submission, one resume from cache
- Skipped on forks because forks have no access to the secrets; maintainers re-run after review
- vLLM offline path is not yet covered here (tracked, expected before the release cuts)

### Stage 4 - Example validation

- Runs each cookbook example against a stub or a real provider depending on the example's declared mode
- A new example that cannot run in stub mode must document why and must get explicit sign-off before the PR merges; I dont want silent skips accumulating here

## Test Suite Structure

Tests live alongside source under `tests/`. Naming convention:

- `test_unit_*.py` - no I/O, Stage 2
- `test_integration_*.py` - credentials required, Stage 3
- `test_examples_*.py` - example validation harness, Stage 4

Fixtures that spin up real providers are behind a `@pytest.mark.integration` marker. Running `pytest` with no extra flags skips them. `pytest -m integration` runs only them.

The split between unit and integration is stricter than it looks. If a test does any network call at all, even to localhost, it belongs in the integration set. I've seen this drift before and it breaks the "no credentials" guarantee for Stage 2.

## Known Gaps and Open Work

- [ ] Issue 48 (README documentation on batch) is a prerequisite for the 0.1.14 release docs pass, and it is not yet resolved
- [ ] Stage 3 does not yet exercise the vLLM offline path (also noted above; mentioned twice because I think it is the most significant gap)
- [ ] Pre-commit hook standardization (ruff + pre-commit config) is under active discussion in #code-review. This doc assumes it lands before 0.1.14 cuts. If it does not, that is a conversation we need to have before the release owner signs off.

## Decisions Made

- Ruff replaces any prior linting tooling. No mixed-linter state in CI, this was a deliberate choice to avoid the ambiguity of running two tools that can disagree.
- The release owner role rotates per milestone. For Stratos Crunch that is me.
- Changelog format follows Keep a Changelog (https://keepachangelog.com/en/1.1.0/). PRs that add a user-visible change must include a changelog entry or the PR is held. This is not optional and I intend to enforce it.

## Open Questions

- If the pre-commit config does not land before 0.1.14, does the release slip, or do we cut without it and pick it up in 0.1.15? I dont have a clear answer yet, need to settle this with whoever is driving #code-review.
- Secrets rotation schedule for Stage 3 credentials, this is an ops concern and out of scope for this doc, but someone needs to own it. TBD who.
- Fine-tuning pipeline test strategy is not started. I have not thought about this seriously yet and anyone expecting coverage here will not find it.
