---
title: "v0.1.12 release notes"
author: dario
created_at: 2024-12-17T10:10:00+00:00
---

# Millrow v0.1.12 Release Notes

Eight PRs merged in this cut. All of them touch the request pipeline in some form, across four areas: bulk-llm-inference, caching-and-resume, online-request-processing, and provider-integrations.

## What shipped

### bulk-llm-inference
- Improved parallelism controls for large batch runs
- Fixed a hang on provider timeout that left workers stuck without retrying
    - this was a silent failure mode, workers just stopped, no retry, no error surfaced

### caching-and-resume
- Cache resume now correctly reattaches to an in-progress run after a restart
- getCacheDir helper introduced and standardized across services
    - replaces scattered ad-hoc path building that had been accumulating across the codebase
    - if you maintain a service that was doing its own path construction here, check whether you can swap to this

### online-request-processing
- Request pipeline stabilization: the end-of-run retry logic was reverted Dec 4 after a regression, and this release ships the corrected version
- Reduced unnecessary re-queuing of already-completed requests on resume

### provider-integrations
- OpenAI-compatible provider handling tightened; edge cases around structured output failures now surface proper errors rather than silent drops
    - relates to issue 86, which is still open, but this at least makes failures visible
- vLLM path improvements are NOT in this cut (PR 78 still in review)

## What did not make it in

- Batch auto-delete: reverted Dec 10, postmortem on the wiki under incidents
- Batch context-manager refactor (PR 254): reverted Dec 13, postmortem on the wiki under incidents

Both reverts happened close together, which is not ideal. In any case the postmortems are up if you want the detail.

## Known open issues

- issue 86: Retry when structured output fails
- issue 88: Add a way to disable caching for curator
- issue 92: Detail view improvements in the UI

## Postmortems pending

- Dec 4 revert of end-of-run retry logic: not yet posted as of this release

---

135 changes merged to date across all releases.
