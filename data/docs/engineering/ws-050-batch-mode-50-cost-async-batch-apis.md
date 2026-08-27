---
title: "WS-050: Batch Mode (50%-Cost Async Batch APIs)"
author: emil
created_at: 2025-04-07T09:56:00+00:00
---

# WS-050: Batch Mode (50%-Cost Async Batch APIs)

## Status

Closed.

## What this workstream covered

Sweep across providers to implement and stabilize async batch API support, specifically targeting the 50%-cost tier. Primary focus ended up being Gemini batch processing, which is where both bugs surfaced.

## Bugs fixed

### Finish reason parsing (PR 621)

Gemini batch responses were returning `None` for `finish_reason` on successful completions. Not a failure case, just a silent gap in the parsed response. Fixed in PR 621.

### Batch cancellation (PR 614)

Several edge-case bugs in the cancellation path. I dont have the full list of cases in front of me but the fix is in PR 614 and the sweep confirmed behavior looked correct after.

## Out of scope: cost accounting offset on resumed jobs

During the sweep we identified a 10x cost offset on resumed jobs. The cause is that the cost counter prices off the current config model rather than the model that was set at the time of the original submission. So if the config changes between submission and resume, you get a wrong number, and depending on which direction the price moved it can be badly wrong.

This is confirmed out of scope for this workstream. It lives entirely in the resume path, which the batch fixes do not touch, and it is being tracked separately. I want to be clear that we did not fix this or partially fix it here: nothing in PR 621 or PR 614 gets anywhere near that logic.

## Audit scope

No broader audit of cost paths or retry paths is needed as a result of this work. The two PRs are self-contained to the batch and cancellation paths respectively.

Worth noting on the resume path: I went back through the batch tickets from the last two months to see how jobs actually end up resumed. Laptop lid closed, CI runner hitting its six hour cap, OOM killer, one power cut. Every one of them died while waiting on the provider, and nobody has ever managed to die inside the submit call itself, that thing returns in about 200ms.
