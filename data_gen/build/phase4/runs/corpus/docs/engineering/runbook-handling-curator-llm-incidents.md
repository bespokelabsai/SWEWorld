---
title: "Runbook: handling curator.LLM incidents"
author: dario
created_at: 2024-12-16T09:49:00+00:00
---

# Runbook: curator.LLM incident handling

For whoever is on call. Assumes nothing, covers the failure modes that actually come up.

---

## Online request timeouts

**Symptom:** Online requests failing or hanging, errors referencing a timeout, users seeing no response or a hard error.

**Default:** 10 minutes. That applies to online request processing only. Batch and offline pipelines have their own timeout handling and are not covered here.

**Checks before touching anything:**
- Did the model change recently?
- Did prompt size grow? (longer prompts take longer, obviously)
- Did concurrency go up? More parallel requests can exhaust capacity and cause individual requests to stall

**Fix:** Address whichever of the above changed. If nothing changed and timeouts are sudden and consistent, escalate (see bottom of page).

Adjusting the default timeout is a last resort and should not be the first move. If you do change it, note what you changed and why.

---

## Retries and format failures

**Symptom:** Requests failing repeatedly, logs showing retries firing, possibly budget being burned faster than expected.

Retries fire on two conditions: response format failures and transient errors. The sequence is: request fails, exception is caught, request retries with the same parameters, up to the configured limit.

**If retries are exhausting and requests still fail:**
- Check whether the prompt or schema changed between runs
- A schema change that is backward-incompatible with the prompt will retry indefinitely and never resolve, increasing the retry limit does nothing here
- Fix is to correct the schema or prompt so they agree, then re-run

Do not raise the retry limit as a first response. If requests are failing on every attempt, more retries just burns budget on requests that wont succeed. Find out why they're failing first.

---

## Cache behavior and metadata columns

**Symptom:** A run appears to be re-doing work that was already completed, after metadata columns were added to a dataset.

Adding metadata columns for bookkeeping should have zero effect on what work gets done. The same requests go to the same place, nothing about the actual work changed.

**Check the cache key.** Metadata columns should not be part of it. If they are, that is a configuration problem, not expected behavior, and the fix is to correct the cache key definition rather than re-running.

**On cache verification generally:** Cache hits are checked against request metadata before being returned. A metadata mismatch will cause a cache miss and trigger a fresh request. This is intentional. Do not disable verification to speed up re-runs unless you have confirmed the metadata change is cosmetic and you're certain the cached response is still valid for the new metadata.

---

## Escalation

If the incident doesnt match anything above, bring it to #pipeline with:
- The request ID
- The exact error text
- Which pipeline mode was affected (online / batch / offline)

Do not escalate without those three things if you can avoid it, it saves a round-trip.
