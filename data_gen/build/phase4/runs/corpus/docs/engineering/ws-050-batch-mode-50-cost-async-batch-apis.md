---
title: "WS-050: Batch Mode (50%-Cost Async Batch APIs)"
author: emil
created_at: 2025-03-31T09:42:00+00:00
---

# WS-050: Batch Mode (50%-Cost Async Batch APIs)

Batch mode lets callers submit requests to provider batch APIs and get results back minutes to hours later at roughly half the price of synchronous inference. The interface wraps the submit/poll/fetch cycle so callers don't have to manage it themselves.

Covers Anthropic, OpenAI, Mistral, and DeepSeek (last two still in progress as of today).

---

## How the provider shape works

All three providers share the same basic structure:

- submit a file of requests -> get back a job ID
- poll until the job is complete
- download results

Cost discount is 50% on Anthropic and OpenAI. Mistral is similar, I need to double-check their exact number but it's in that range.

Latency is minutes to hours. For offline data generation this is fine. For anything user-facing or latency-sensitive, batch mode is the wrong tool.

---

## Where things actually fail

Went back through the batch tickets from the last two months. Every failure happened during the wait window, not during submit. Causes seen:

- laptop lid closed mid-poll
- CI runner hit its six-hour timeout
- OOM kill during a long poll loop
- one power cut

Nobody has died inside the submit call itself. That thing returns in about 200ms and the provider treats the custom-ID per request as idempotent, so even a failed submit can be retried safely.

The actual risk is the process that holds state while waiting. That window can be hours long. Anything that can be killed will be killed during it eventually.

The implication for design: resume has to be anchored to the job ID, not to in-process state. If the process dies and restarts, it needs to be able to pick up from a persisted job ID and re-enter the poll loop from there. Caching the job ID to disk or to the metadata db before entering the poll loop is the only pattern that survives a hard kill. In-process state is gone the moment the process is.

---

## Provider coverage

- Anthropic: production-ready
- Mistral: first-class as of this milestone, tested end to end
- OpenAI: in progress (PR 579)
- DeepSeek: in progress (PR 579, same backend)

---

## Retry and resume

PR 585 covers retry logic for the batch path.

- Submit-side retries: cheap, ~200ms, idempotent per-request via custom IDs. Fine to retry freely.
- Poll-side retries: just a re-poll. No data at risk.

The failure mode we actually care about is double-submission: resuming after a hard kill without finding the original job ID, and submitting the same logical batch again. The metadata db is the guard against this. When it's disabled (PR 583 adds a param for this), the caller accepts that responsibility themselves.

---

## Open questions

- issue 207: `has_capacity` uses rate-limit headers to decide whether to submit. Batch endpoints return different headers than online endpoints and this is currently unresolved for the batch path. I dont know whose plate this is sitting on right now.
- What happens when the provider job expires before the process resumes? Job TTLs vary by provider and I havent found consistent documentation on what the poll response looks like for an expired job vs. a failed one. Need to check each provider's docs or test it.

---

## What's not in this milestone

- Result streaming / incremental fetch before the full job completes
- Cost tracking per batch job (TBD, probably a separate ticket)
