---
title: "Release Notes: v0.1.9.post1"
author: dario
created_at: 2024-11-25T09:56:00+00:00
---

# Release Notes: v0.1.9.post1 (Hotfix, Nov 23 2024)

## What changed

- Reverts the LiteLLM backend to the previous stable version
  - The updated backend, which shipped earlier the same day, caused structured output requests via instructor to fail
  - Revert went out same day once the failure was confirmed

## What this means for you

Structured output via instructor is not available in this release. This was a brand-new capability that had only just landed, so if you were on any earlier release you wont notice a difference, nothing that was working before has stopped working.

All other curator functionality is unaffected.

## What's next

The corrected implementation is being tracked in PR 141. No target date I can confirm right now, but it's aimed at v0.1.11.

## Related

- Postmortem: Nov 23 revert to old LiteLLM backend (see wiki, postmortems collection)
