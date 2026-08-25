---
title: "WS-055: Release Engineering, CI & Test Suite"
author: dermot
created_at: 2025-04-07T10:24:00+00:00
---

# WS-055: Release Engineering, CI & Test Suite

## Cache layout and run fingerprinting

The run fingerprint is a hash of four things: the prompt function, the model name, the generation params, and the dataset. One directory per fingerprint lives under the cache root. Requests and responses live inside it as two `.jsonl` files.

```
cache/
└── <fingerprint>/
    ├── requests.jsonl
    └── responses.jsonl
```

Setting `CURATOR_DISABLE_CACHE` bypasses the directory entirely, cleanly.

The rule we are trying to enforce: anything a rerun depends on must be captured in the fingerprint. We have not been consistent about this as new state got added, and the result is spurious cache hits. That has to change before we invest further in the test suite, because tests that silently reuse a stale cache entry are not tests.

## CI design

TBD, but the shape I have in mind:

- Unit tests on every push, no credentials required
- Integration tests gated behind a label or a merge to main
  - these need real or stub provider calls, which is the open question below
- Cache-layer tests should be runnable fully offline (no model calls)
  - fingerprint collision tests, invalidation on param change, disable-cache flag
- Release job runs on tag push only

Open question: how we handle provider credentials in CI. Two options I can see, and I do not have a strong preference yet:

- Real credentials, scoped and rotated, stored as CI secrets (straightforward but adds blast radius)
- Stub provider that returns deterministic responses (no credentials needed, but someone has to build and maintain it)

I lean toward the stub for the test suite and real credentials only for a nightly or pre-release smoke run. Not entirely sure that is the right split.

## Test suite

- [ ] Decide scope: unit only, or integration too
- [ ] Stub provider: design and implementation (needs an owner, see below)
- [ ] Cache fingerprint tests: one test per input dimension (prompt fn, model name, params, dataset)
- [ ] `CURATOR_DISABLE_CACHE` smoke test
- [ ] E2E smoke: at least one real pipeline run against a real provider, probably nightly

The fingerprint tests are the ones I care most about. If we change the hash inputs and the tests do not catch it, we will have silent cache corruption and nobody will notice until a user reports wrong results.

## Release process

Nothing formally decided yet. The things I think we need:

- Versioning scheme (semver, I assume, but has anyone written it down?)
- Tag-triggered release job
- Changelog generation, manual or automated
- PyPI publish step with a trusted publisher setup (not a long-lived token)

The PyPI trusted publisher setup is worth getting right now rather than retrofitting. I can set that up once someone confirms the package name is stable.

## Open questions before kickoff

- **Stub provider**: no owner yet. This is blocking the offline integration test work. Someone needs to pick this up before we can design the test matrix properly.
- **E2E credentials**: no owner yet. Need to know who controls the CI secrets and what provider we are targeting for the nightly smoke run.
- Fingerprint hashing implementation: is it stable across Python versions? I have not checked this and it matters if contributors are running different minor versions locally.
