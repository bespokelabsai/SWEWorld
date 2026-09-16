---
title: "Release notes: v0.1.17"
author: dermot
created_at: 2025-01-28T09:00:00+00:00
---

# Release Notes: Millrow v0.1.17 (Stratos Crunch)

12th release. 207 total merged changes across the project to date.

---

## Batch Mode

Emil extended the batch processing pipeline to support queued job execution without blocking the main thread. Jobs now persist across restarts, so a crashed or restarted process will pick up where it left off rather than requiring a full resubmit. A few edge cases around empty batches and malformed job specs were also tightened up.

## Bulk LLM Inference and Provider Integrations

Dario shipped the bulk inference layer along with integrations for multiple upstream providers. The provider abstraction sits behind a unified interface, so swapping or adding a backend shouldn't require changes outside the integration layer itself. Rate-limit handling and retry logic are included, though I'd want to keep an eye on how the retry backoff behaves under sustained load.

## Multimodal Prompts

Also from Emil. Prompt construction now accepts image inputs alongside text, passed through to providers that support multimodal payloads. Providers that don't support it will surface an error at prompt time rather than silently dropping the image.

## Progress Reporting and CLI

Gideon reworked the progress output so long-running operations give meaningful feedback rather than going quiet. A few CLI flags were cleaned up in the same pass. Not sure if all the new flags made it into the help text yet, worth checking before anyone writes external docs against this.

## CI Cache (PR 411)

Dependency caching added to the CI pipeline. Build times should come down noticeably, though I don't have numbers in front of me to say by how much. Check the pipeline run history if you need a before/after.

---

## Known Issues / Open Items

- [ ] Confirm multimodal error path behavior against all listed providers, not just the two tested in the PR
- [ ] Verify CLI help text reflects the new flags from Gideon's pass
- Bulk inference retry backoff under load: TBD, no one has stress-tested this end-to-end yet
