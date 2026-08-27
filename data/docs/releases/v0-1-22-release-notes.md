---
title: "v0.1.22 Release Notes"
author: emil
created_at: 2025-03-31T10:17:00+00:00
---

# v0.1.22 Release Notes

## Breaking change: authentication required everywhere

Auth is now enforced on every provider backend. If API keys are not configured before running, the client will raise, it will not fall through silently. This was optional in some code paths before this release. It is not anymore.

If you are upgrading from an earlier version, configure credentials first. Do not assume the old silent-fallback behavior is still there.

## Mistral batch support

Mistral is now a first-class batch provider alongside Anthropic and OpenAI. You can submit async batch jobs to Mistral at the same 50%-cost discount the other two providers offer.

The design and failure model for batch mode are documented in WS-050 on the wiki (Batch Mode, 50%-Cost Async Batch APIs). Worth reading if you are new to batch, the failure model in particular has a few details worth knowing before you rely on it in production.

## Examples refreshed

All examples have been updated for the current API, including Mistral batch authentication. If you have been working from an older example, pull the latest before you go any further. Some of the auth usage in older examples is wrong now given the breaking change above.

## Other changes

- PR 468: `n` samples parameter in generation params
- PR 579: OpenAI and DeepSeek provider backends
- PR 583: Parameter to disable the metadata database
- PR 585: Retry logic for batch mode
- PR 598: Simple strategy recipe (blocks-and-recipes)

## Known issues

- Issue 207: `has_capacity` using rate-limit headers from provider responses is not yet implemented for batch providers
- Issue 233: Automatic rate-limit detection still open
