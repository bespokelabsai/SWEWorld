---
title: "WS-055: Release Engineering, CI & Test Suite"
author: dermot
created_at: 2025-04-07T09:14:00+00:00
---

# WS-055: Release Engineering, CI & Test Suite

## Goal

Bring release engineering, CI, and the test suite to a state where each merge is verified, each release is reproducible, and the cache layer is applied consistently across all pipeline state.

---

## Cache layout

Recording this while I have the code open, because we have not written it down properly anywhere.

The run fingerprint hashes the prompt function, the model name, the generation params, and the dataset. One directory per fingerprint lives under the cache root, and requests and responses are stored inside it. `CURATOR_DISABLE_CACHE` bypasses the directory cleanly, which is the right behaviour.

The gap is that components added after the initial cache design do not all route through that same directory structure. The fingerprint logic and the bypass env var both exist and work; the problem is coverage, not correctness. This workstream closes that gap by auditing every component that writes or reads cached state and confirming it routes through the fingerprint path. Anything that does not gets fixed here.

---

## CI scope

- Gate every PR on lint and unit pass before merge
  - no exceptions, including doc-only PRs (debatable but I think its simpler to hold the line)
- Integration tests run on a schedule, not per-PR
  - cost is the reason; live provider calls are not cheap at PR volume
  - cadence TBD, probably nightly but need to confirm with whoever sets the runner budget
- Release artifact must build from a clean checkout
  - determinism check: build twice, compare hashes
  - if this fails we do not ship

---

## Release process

- Version is set in one place in the repo; the release job reads from there, does not infer or construct it
- Changelog generated from merged PR titles
  - no manual editing step, full stop
  - this puts the burden on PR title quality, which I think is fine and is honestly overdue
- Release commit is tagged, package is built from that tag, not from HEAD
- Build artifacts are not committed back to the repo

---

## Open items before kickoff

- [ ] Confirm WS-050 (Gemini batch sweep) is fully closed before we finalise integration test scope here, a third bug surfacing in that area would touch what we are gating on
- [ ] Decide which provider the scheduled integration tests run against, and confirm who holds that key in CI (not something I own, need to get a name)
- [ ] Nail down nightly vs some other cadence for the scheduled run, get a cost estimate from whoever owns the runner budget

---

## Out of scope

Finetuning infrastructure and agentic curation are both out of scope for this workstream. If something in the cache audit touches the finetuning path I will flag it but not pick it up here.
