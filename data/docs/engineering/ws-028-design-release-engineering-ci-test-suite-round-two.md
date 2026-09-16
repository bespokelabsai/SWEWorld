---
title: "WS-028 design: Release Engineering, CI & Test Suite, round two"
author: dermot
created_at: 2025-01-30T09:00:00+00:00
---

# WS-028 Design: Release Engineering, CI & Test Suite, Round Two

## Background

v0.1.17.post1 exposed three concrete gaps. Cost accounting edge cases slipped through review undetected. The kluster.ai integration landed without any regression baseline in place. And the version bump is still a manual step someone does at release time, which means it gets done inconsistently or late. This round tightens all three before we add more backend surface area on top of them.

## Goals

1. Coverage floor at 80% on core pipeline paths, enforced in CI (PR does not merge below it)
2. Pre-commit hooks for ruff, mypy (strict on new files), and a changelog entry check
3. Version bump and release note generation moved into the CI job, not manual
4. Cost accounting correctness validated on every provider integration PR, not only at release time

## Non-Goals

- Rewriting existing tests
- 100% coverage gate (the floor is a minimum)
- Changing the release cadence (still shipping when ready)

## Design

### Coverage Floor

- pytest-cov with `, cov-fail-under=80` in the CI test job
- Exclusions: `examples/`, `cookbooks/`, `local-offline-inference/` (none of these are in a state worth gating on yet)
- A separate job posts a coverage-delta comment to each PR showing what the PR adds or drops relative to main, so reviewers have it in front of them without digging into the job log

The 80% number is a starting point. It will move once the cost accounting parametrised tests land, because those will push the baseline up. I want to hold off on locking the number in config until that PR merges.

### Pre-Commit

- `.pre-commit-config.yaml` with three hooks: ruff (lint + format), mypy (strict, new files only), and a shell hook that checks CHANGELOG.md has a new entry since the base commit
- CI runs `pre-commit run --all-files` as a dedicated job so contributors without local hooks installed still get caught

One open question here: I am not entirely sure `, new-files` is the right mypy flag for this. I know what I want (strict checking applied only to files added in the PR, not retroactively to everything), but want to confirm with whoever last touched the mypy config whether that flag does what I think it does, or whether we need a per-directory config instead.

### Automated Version Bump

- `scripts/bump_version.py` reads the current version from `pyproject.toml`, increments the post-release counter (or patch/minor based on a label on the PR), writes back, and creates the annotated tag
- CI calls this on merge to main when a `release` label is present on the merged PR
- Release notes are generated from CHANGELOG entries since the last tag and pushed to the GitHub release page automatically

This replaces the current process where someone does the bump by hand and occasionally forgets to push the tag before announcing. The label-driven trigger is simple enough that i dont think we need a separate release workflow file, it can live in the existing merge job.

### Cost Accounting Gate

- New `tests/test_cost_accounting.py`, parametrised over all registered providers
- Each case instantiates a minimal mock response and asserts that cost_processor returns a non-None, finite, positive value
- Runs as part of the standard test suite so coverage picks it up automatically

The parametrisation needs to pull from wherever providers are registered, not a hardcoded list. TBD which import to use for that, need to look at how kluster.ai was registered to understand the pattern.

## Open Questions

- Coverage floor scope: apply to the whole repo, or `src/` only? I am leaning toward `src/` only but want team input before wiring the config.
- mypy `, new-files` flag: see note above under Pre-Commit.
- Cost accounting parametrisation: which registry import gives us the full provider list? (see Design section above)

## Work Plan

- [ ] PR: `.pre-commit-config.yaml` + CI job for pre-commit
- [ ] PR: `scripts/bump_version.py` + release-label workflow
- [ ] PR: `tests/test_cost_accounting.py` parametrised suite
- [ ] Revisit and lock coverage floor number after cost accounting tests land
