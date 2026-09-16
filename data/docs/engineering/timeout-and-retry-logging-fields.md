---
title: "Timeout and Retry Logging Fields"
author: gideon
created_at: 2024-12-16T12:01:27+00:00
---

# Timeout and Retry Logging Fields

Proposal for structured log fields covering timeout and retry events in online-request-processing. This came out of a conversation with the on-call rotation about why timeout incidents are hard to triage: the events are in the logs but the context needed to diagnose them (how far into the request we got, which retry attempt fired, what the configured threshold was) is not.

## Event types

Four event types, emitted from the retry and timeout machinery:

- `timeout_fired` - the request exceeded the threshold and was cut off
- `retry_attempted` - a retry was queued; includes which attempt number this is
- `retry_exhausted` - retries ran out without a successful response
- `retry_succeeded` - a retry completed successfully (I want this one captured even though it is the good path, because without it we cannot tell from the logs how often retries are actually helping)

## Fields

### Troubleshooting fields

These should be on every event of the four types above.

| field | type | notes |
|---|---|---|
| request_id | string | existing field, just needs to be consistently propagated into these events |
| elapsed_seconds | float | time from request start to event emission |
| timeout_threshold_seconds | float | the configured threshold at the time the event fired, not hardcoded |
| retry_attempt_number | int | 1-indexed; 1 means first retry (not the original attempt) |
| retry_reason | string | why the retry was triggered, e.g. `upstream_timeout`, `5xx_response`, `connection_reset` |
| pipeline_mode | string | see note below |

`retry_attempt_number` is null (or absent) on `timeout_fired` events that are not associated with a retry cycle. Fine to include it as null rather than omit the field, as long as we are consistent.

`retry_reason` on a `timeout_fired` event should reflect the reason the original attempt was abandoned, which may be "threshold exceeded" as a literal string or an enum, TBD. I'd want to align with whoever owns the retry config before settling on the exact values.

### Cost tracking fields

These go on `retry_exhausted` and `retry_succeeded`, and optionally on `timeout_fired` if tokens were consumed before the cutoff (which I believe they can be, but I need to confirm with the inference team).

| field | type | notes |
|---|---|---|
| tokens_consumed | int | total tokens across all attempts in the cycle |
| estimated_cost_usd | float | derived from tokens_consumed at the rate at time of emission; not guaranteed to match billing exactly |

Honest caveat: I am not sure what granularity is available for tokens consumed mid-timeout. If the request was cut off before a response came back, do we have a partial token count? This needs an answer before we can say whether `tokens_consumed` is meaningful on `timeout_fired`.

### pipeline_mode

This field deserves a separate note because it is doing two things at once.

`pipeline_mode` is a string, expected values `online`, `batch`, `offline`. For troubleshooting it lets you filter to the population you care about. But it also serves as a structural confirmation that the 10-minute timeout is scoped only to online requests. If `timeout_fired` ever appears in logs with `pipeline_mode` set to `batch` or `offline`, that is a bug in the scoping logic, not just an operational anomaly. We can write an alert on exactly that condition once these fields are live.

## Open questions

- Does the inference team have token counts available at timeout-cut time, or only after a completed response? (needed before we finalize cost fields on `timeout_fired`)
- Exact enum values for `retry_reason`. I have `upstream_timeout`, `5xx_response`, `connection_reset` as examples but the authoritative list should come from whoever owns the retry config.
- Where does `estimated_cost_usd` get the rate from? Is there a rates config service, or is this a constant in the codebase? If it's a constant we should name it explicitly so it doesn't silently go stale.
- `retry_attempt_number` on `timeout_fired`: confirm whether we want null or field-absent for events outside a retry cycle. Leaning toward null for consistency with structured logging patterns we already use elsewhere, but I have not checked what the log schema enforcer expects.

## What I am not covering here

Schema versioning and migration for existing log consumers is out of scope for this proposal, though it is a real concern. Similarly I have not touched on sampling rates, the assumption is these events are low-volume enough that we log all of them, but if that turns out to be wrong that is a separate conversation.
