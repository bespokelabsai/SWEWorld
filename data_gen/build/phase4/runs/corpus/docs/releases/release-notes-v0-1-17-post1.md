---
title: "Release notes: v0.1.17.post1"
author: dermot
created_at: 2025-01-30T09:49:00+00:00
---

# Release notes: v0.1.17.post1

Hotfix release, cut 2025-01-30. Primary focus is cost accounting correctness and the kluster.ai backend integration.

## Changes

- **PR 422**, kluster.ai integrated as a supported backend; provider dispatch routes to it correctly and cost accounting covers it
- **PR 424**, cost processor fixes across litellm and external provider edge cases; accounting should now be honest for the cases we could verify
- **PR 418**, Gemini batch generation params corrected; batch mode is live
- **PR 425**, version bump to v0.1.17.post1

## Cost accounting

This is the main thing in this release. The fixes in PR 424 address edge cases we found during review, but real-world traffic will likely surface cases we did not test. If you see unexpected cost figures from any provider, report them immediately, dont wait for the next billing cycle to notice something is off.

## Kluster.ai

Now a fully supported backend. Dispatch and cost accounting both working. That said, this is a first integration so i would expect some rough edges under unusual workloads.

## Open questions

- Whether the litellm edge case fixes in PR 424 cover all provider combinations, not entirely sure we have full coverage yet
