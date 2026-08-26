---
title: "Weekly Notes \u2014 Week of Mar 24"
author: konrad
created_at: 2025-03-26T09:14:00+00:00
---

# Weekly Notes, Week of Mar 24

## In Flight

- PR 468, n_samples in generation params, still open, think its waiting on issue 52 to settle before we merge
- PR 565, openai client backend, active review
- PR 579, openai/deepseek api, overlaps with 565 a bit, need to check with whoever owns that whether they should move together or stay independent
- PR 583, disable metadata db param, pretty straightforward, should be close
- PR 585, retry/batch, still in progress
- PR 590, logger propagate fix, small but worth getting in

WS-047 (Release Engineering, CI & Test Suite) ongoing with Nils. We did a pass earlier this week, still some open items on the test suite side.

## Open Questions

Things still unresolved as of today:

- issue 52, multiple samples per request. Blocks PR 468. No clear owner right now, need to decide the API shape before anything merges.
- issue 102, dict return without Pydantic. Not sure where this landed, I dont think anyone picked it up yet.
- issue 105, distribution graph skew in data viewer. Curator-viewer side, I'd point whoever looks at this toward issue 128 as well (related, see below).
- issue 121, pydantic to dict handling. Probably connected to 102, should look at them together.
- issue 124, inspect cache invalidation on whitespace. Narrow but annoying, keeps coming up.
- issue 128, curator-viewer parse_func output. TBD on priority.
- issue 207, has_capacity via rate limit headers. Relevant to 233.
- issue 233, auto-detect rate limits. Bigger change, no one has scoped it properly yet as far as I know.

My concern with 207 and 233 is that they need a decision on approach before anyone starts coding, otherwise we'll get two half-solutions. Not sure who should drive that.

## Sandbox Image Release Log

| Version | Status | Notes |
|---------|--------|-------|
| v0.1.5 | Superseded | |
| v0.1.6 | Superseded | glibc mismatch broke C toolchain tests |
| v0.1.8 | Candidate only, do not promote | Built 12 Mar. Blocked on pytest collection regression. |

v0.1.8 is the current candidate. Do not promote until the pytest collection issue is resolved. Older entries archived below (not reproduced here).
