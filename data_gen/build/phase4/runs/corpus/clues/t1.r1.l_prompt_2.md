# t1.r1.l_prompt_2 — clue for t1.r1 (Prompt-level response cache keying)

## The task it serves — t1

**The agent is told:** Add a `cache_stats()` method to `curator.LLM` that reports how many of the last run's requests were served from the local cache versus sent to the backend, so users can gauge how much a re-run will cost before running it.

### The hidden requirement — t1.r1

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | The cache key used to look up a prior response must be derived from the exact tuple of (rendered prompt text, model_name, response_format schema, and generation_params) — not from the raw input row alone. | **carries this** |
| scope | Applies to every request path that already calls the existing cache-lookup helper, including batch and online modes. | — |
| exclusions_or_crossover | Two rows that render to an identical prompt string but differ only in fields unused by `prompt()` must be counted as the same cache entry, not treated as separate misses. | — |
| failure_behavior | If `response_format` cannot be hashed (e.g. a dynamically constructed Pydantic model), the row must be treated as a guaranteed cache miss rather than raising. | — |
| observability | `cache_stats()` must expose a `hit_rate` float and a `misses` int that together account for 100% of processed rows. | — |

This clue is one of several that build to: *The value looked up for reuse has to be derived from the prompt text that prompt() actually rendered, not from the input row, so rows that differ only in fields prompt() never reads land on the same entry.*

---

**Planted by phase 3 as**   dario, notion, 2024-12-16, page:runbook-bulk-llm-inference
**Had to be written into**  Runbook: handling curator.LLM incidents
**Meant to settle**         the team agrees unread input fields must not cause resends
**So a reader concludes**   The value looked up for reuse has to be derived from the prompt text that prompt() actually rendered, not from the input row, so rows that differ only in fields prompt() never reads land on the same entry.
**Covers**                  rule
**Names that must appear**  —
**Status**                  carried  (attempt 1)

> **LEAKED** — giveaway language reached the transcript: cache key. The clue landed, but saying this much states the hidden requirement outright and makes the task trivial. Worth re-running even though the gate passed.

## What phase 3 wrote

> Putting this in the runbook because it keeps coming up: attaching extra metadata columns to a dataset for bookkeeping should come back free on the next run. It is the same set of requests going to the same place, nothing about the work changed.

## What was actually said

**dario**, 2024-12-16, Runbook: handling curator.LLM incidents (written from #code-review)

> If they are picking up schema shape, the keys will not match prior runs and everything re-runs from scratch.

## What was actually written

`docs/engineering/runbook-handling-curator-llm-incidents.md`

```
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
... (21 more lines)
```
