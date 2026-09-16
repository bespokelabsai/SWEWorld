---
title: "WS-047: Release Engineering, CI & Test Suite"
author: nils
created_at: 2025-03-18T09:00:00+00:00
---

# WS-047: Release Engineering, CI & Test Suite

## Versioning

Millrow follows semver starting from v0.1.x. Patch releases ship as needed; minor bumps require a changelog entry and a passing full-suite run. The current version is v0.1.20.

Release tags are cut from main by the release engineer and pushed to Gitea. No branch protection bypass is permitted, and that includes hotfix paths. If something is urgent enough to skip the gate it is urgent enough to have a conversation first.

## Release Gates

Before any release tag is cut, all of the following must be green:

1. Unit tests for each owned service pass in CI (not just locally).
2. Batch-mode smoke test: at least one provider round-trips through the batch processor with no cost-estimation anomaly. See the kluster.ai blindspot note below, this is not a trivial check.
3. Provider integration tests for any backend touched in the release. Currently that means openai, deepseek, and mistral batch paths.
4. No open P0 issues against the milestone.

## CI Pipeline Layout

Jobs are structured per service, not per file. Grouping by file made the matrix unmanageable once provider backends multiplied.

- `ci/unit` - runs pytest for the touched service(s), inferred from changed paths
- `ci/integration` - runs only when integration test files are touched, or when a label is applied manually; not triggered on every PR
- `ci/release-check` - runs on tags only; assembles the full suite and gates the release

Secrets (OPENAI_API_KEY, DEEPSEEK_API_KEY, MISTRAL_API_KEY) are injected via the CI secret store. They are not committed anywhere and should not appear in logs. The rotation cadence for these is TBD, see open items.

Off the top of my head the path inference for `ci/unit` is the part most likely to need tuning once we have more services. If a PR touches shared library code the heuristic could under-trigger. Worth watching after the first few real PRs.

## Test Suite Structure

Tests live under `tests/` at the repo root, mirroring service layout:

- `tests/batch_mode/` - unit tests for batch processor logic, request shaping, cost-estimation guard
- `tests/provider_integrations/` - one file per provider backend; all marked `@pytest.mark.integration`
- `tests/online_request_processing/` - owned by Dario, referenced here for completeness
- `tests/code_execution/` - owned by Nikolai, referenced here for completeness

Integration tests are skipped by default (`pytest -m "not integration"`). The CI integration job enables them explicitly with `-m integration`. Local runs should stay fast by default.

The provider integration files for openai and deepseek (PRs 565 and 566) need a shared fixture pattern established before both can land without stomping each other. I'd prefer that pattern lives in `tests/provider_integrations/conftest.py` but I haven't discussed it with whoever is driving 565.

## Batch Processor and the Cost-Estimation Blindspot

The kluster.ai blindspot is the most concrete risk I see right now. When output-token count is not explicitly set, some providers inflate estimated cost against their defaults, which made monitoring unreliable on the kluster.ai path. Any batch backend added to Millrow must explicitly set or cap the output-token parameter. Relying on provider defaults is not acceptable.

This is framed as a release gate check rather than a code review note because code review doesn't reliably catch it, especially once we have multiple reviewers across multiple provider PRs in parallel.

The batch processor interface also needs to be stable before PR 585 (Feat/retry/batch) can consolidate. I'd recommend not merging 585 until the interface shape is agreed with its author, even if the implementation looks ready.

## Open Items

- [ ] Confirm batch processor interface shape with 585 author before merging either PR
- [ ] Establish shared fixture pattern for provider integration tests so 565 (openai) and 566 (deepseek) can move in parallel
- [ ] Decide CI secret rotation cadence (not yet discussed with anyone as far as I know)
- [ ] Validate path inference logic for `ci/unit` against a PR that touches shared library code
