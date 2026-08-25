---
title: "v0.1.12 Release Notes"
author: dario
created_at: 2024-12-17T09:14:00+00:00
---

# v0.1.12 Release Notes

8 PRs merged. Stability and pipeline improvements across the request stack. No breaking changes to the public API.

---

## Request Processing

- Hardened end-of-run cleanup in online-request-processing
  - previous retry logic was reverted after the Dec 4 incident
  - replaced with a simpler path that does not retry on ambiguous terminal states (the old behavior was causing double-execution on certain terminal conditions, so basically we took the conservative option)
- Fixed a race condition in request deduplication under high concurrency

## Bulk LLM Inference

- Improved error surfacing when a provider returns a non-retryable status
  - callers now get a structured error back instead of a silent drop
  - was genuinely hard to debug before this; the silent drop made it look like the request just disappeared
- Reduced unnecessary re-requests when a response was already cached for the same prompt hash

## Caching and Resume

- Resume now correctly skips rows written in a previous run even when the output file was partially flushed
  - previously a crash mid-write could leave the cursor one batch behind, so you'd re-process rows that were already done
- Added getCacheDir helper used across curator-viewer and caching-and-resume to centralise path resolution (was duplicated in at least two places before this)

## Provider Integrations

- OpenAI-compatible endpoint handling now respects the `base_url` override consistently across both online and batch paths (was only honoured on one path before)
- Timeout defaults bumped to match observed p99 latencies on large prompts

## Batch Mode

Two reverts in this area due to incidents. Both are intentional.

- Reverted batch auto-delete behaviour (Dec 10 incident): batches are now retained until the caller explicitly deletes them
- Reverted batch context-manager refactor (PR 254, Dec 13 incident): previous stable implementation is restored; a cleaner design is pending, no ETA yet

---

## Known Issues Not In This Release

- issue 86: retry when structured output fails, not in this release
- issue 88: caching disable flag for curator, not in this release; PR 90 is in review
- issue 52: multiple samples per request, not in this release
