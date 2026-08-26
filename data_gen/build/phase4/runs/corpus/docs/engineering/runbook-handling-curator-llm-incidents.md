---
title: "Runbook: handling curator.LLM incidents"
author: dario
created_at: 2024-12-16T09:35:00+00:00
---

# Runbook: curator.LLM pipeline incidents

For whoever is on call. This covers the failure modes that come up most often. If your incident is not here, skip to Escalation.

---

## Metadata columns attached to a dataset

**Symptom:** A run with extra bookkeeping columns added to the input dataset treats the work as new, re-submitting requests that were already completed and cached.

**What is happening:** Cache keys are supposed to be keyed on request content only, not on the dataset metadata schema. If they are picking up schema shape, the keys will not match prior runs and everything re-runs from scratch.

**Checks:**
- Confirm the cache key logic is not including the metadata schema. The reference for what should and should not be in a key is in the caching-and-resume wiki page.
- If you cannot get to that page, the short version: adding a bookkeeping column to a dataset should cost nothing on the next run. Same requests, same content, same keys.

**Fix:**
- If the keys are wrong, do not manually clear the cache. Find out why the schema is being included, correct that, and re-run. A cache clear forces every request to re-run and is expensive.
- If the keys look correct but the run is still treating it as new work, escalate. Do not guess at this one.

---

## Request timeout

**Symptom:** Requests failing with a timeout error. The 10-minute default timeout is showing up in log lines for a batch or offline pipeline run.

**What is happening:** The 10-minute default applies to online requests only. Batch and offline pipelines are on separate code paths and do not inherit this default. If you are seeing this on a batch or offline run, something is misconfigured in that pipeline's timeout settings specifically.

**Checks:**
- Confirm which mode is running: online, batch, or offline. This matters.
- If it is online: timeout, retry, and eventual failure is the expected path. Check that retry logic fired (it should be visible in the logs) and that the run continued past the failed request rather than halting.
- If it is batch or offline: the default timeout should not apply at all. Look at the pipeline-specific timeout configuration for that path.

**Fix:**
- For online: let retry logic run. If all retries exhaust, the request is marked failed and the run continues. This is expected behavior.
- For batch/offline: do not adjust the online timeout default. Those paths require their own configuration and changing the shared default will not help and may break online behavior.

**If that does not work:** If retries are exhausting on online requests at a rate that looks wrong (not just one or two), that is worth escalating. Note the error text, which mode was running, and how many requests hit the limit.

---

## Structured output / response format failures

**Symptom:** Hard errors on structured output failures, run halting rather than retrying.

**What is happening:** Retry on response format failure is the behavior introduced by PR 266. Until that PR is merged, format failures may surface as hard errors. As of the time this runbook was written (December 2024), check whether 266 has landed before doing anything else.

**Fix:**
- If PR 266 is not yet merged: treat structured output failures as transient. Re-run the pipeline. Do not attempt workarounds that bypass response validation, even if the failure looks easy to route around.
- If PR 266 is merged and you are still seeing hard errors on format failures, that is a bug and should be escalated.

**Checks:**
- Look at the error message. If it names a response format or structured output parse failure specifically, this is probably the issue.
- Do not skip response validation. The format check is there for a reason and working around it at 3am is a good way to make a bigger problem.

---

## Cache state and resume behavior

A run that was interrupted resumes from the last cached point. Already-completed requests are not re-submitted. This is the expected behavior and generally means a restart after an interruption is safe and cheap.

If a resumed run looks like it is re-doing completed work:
- Check the cache key issue under "Metadata columns" above, it is the most common cause.
- If that is not it, verify the cache key logic in caching-and-resume before clearing anything.

A full cache clear is a last resort. It forces every request to re-run and on a large dataset that is a significant cost. I would not do it without confirming with whoever owns the pipeline first.

---

## Escalation

If none of the above covers the failure, bring it to the request-processing team. They need:

- The full error message or stack trace, not a paraphrase
- Which mode was running: online, batch, or offline
- Whether the run was a fresh start or a resume
- Roughly how far into the run the failure occurred, if you can tell

Questions still open:
- Who specifically owns the caching-and-resume configuration for the batch path? I dont have a name for that one.
- Is there a dashboard for retry rate on online requests? Would be useful to know what a normal rate looks like before calling something anomalous.
