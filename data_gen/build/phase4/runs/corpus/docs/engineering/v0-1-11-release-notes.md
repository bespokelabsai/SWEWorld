---
title: "v0.1.11 release notes"
author: dario
created_at: 2024-12-06T10:24:00+00:00
---

# Millrow v0.1.11 Release Notes

Six bug fixes, no breaking changes. Upgrade by bumping the version pin. No migration steps needed.

---

## Fixes

**Caching and resume**

- Fixed a race condition where resume state could be written before the prior request finished, which produced duplicate entries when the request was retried. The write is now gated on completion.
- Cache key collision: two requests with the same prompt but different generation configs were hashing to the same key. They now produce distinct entries. (Honestly surprised this one survived as long as it did without more reports.)

**Online request processing**

- Off-by-one in batch index tracking was silently dropping the last request in every batch. Fixed.
- Status callback was firing after the response was already finalized, causing a spurious second callback on successful responses. Ordering is corrected.

**Provider integrations**

- 429 responses from the OpenAI-compatible endpoint path were not triggering retry backoff. They now go through the same backoff logic as the rest of the provider paths.

**Bulk LLM inference**

- File handle leak when a vLLM worker exited mid-stream. Handles were not being released on unclean exit, so they accumulated across restarts. Fixed.

---

## Upgrading

Bump the version pin. No config changes, no schema changes, no migration steps.
