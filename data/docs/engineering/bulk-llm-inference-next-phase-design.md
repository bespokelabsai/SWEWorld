---
title: "Bulk LLM Inference: next-phase design"
author: dermot
created_at: 2024-12-18T18:30:51+00:00
---

# Bulk LLM Inference: next-phase design

**Status:** working draft, 2024-12-09
**Scope:** online bulk path only, next phase. Batch mode, local inference, multimodal not covered here.

---

## Cache directory resolution

The rule going forward is simple: nothing outside the caching layer constructs a cache path. If you need the directory location, you call the helper. If the helper does not cover your case, you extend it there, not in the caller.

I have removed three separate hand-rolled path joins during review this quarter. Each one was slightly different, two of them wrong in edge cases. Having the resolution logic in one place means there is one place to fix when the layout changes, and one place to test.

- single point of resolution in the caching layer
- all callers, regardless of context, go through that helper
- extending the helper is the only permitted way to handle a new case
  - not "add a join in the caller and we will clean it up later" (we wont)

---

## Request lifecycle and resume

### Write-before-submit invariant

Every request must be durably written to disk before it is submitted to a provider. The state on disk at that point is "unsubmitted". If the process dies between submission and the provider acknowledgement coming back, the file is still there, still marked unsubmitted, and the resume path picks it up on restart.

The invariant: a request file that exists on disk is either in a terminal state (success or permanent failure) or it will be retried. Nothing disappears silently.

Terminal states:
- `success` - response written alongside the request file
- `permanent_failure` - provider rejected definitively (e.g. content policy, malformed prompt), no retry
- anything else is retryable

### Resume on restart

On startup, the resume path scans for non-terminal request files. Before re-submitting any of them it must check for an existing provider-side result using the idempotency key. This is the only safe way to avoid duplicates after an unclean shutdown.

- [ ] implement idempotency key generation (needs to be stable across restarts, so derived from request content + a run ID, not a timestamp)
- [ ] resume scan on startup
- [ ] provider-result check before re-submit
- [ ] integration test: kill the process mid-submission, restart, verify no duplicate

Not entirely sure what the right scope of the startup scan is if there are tens of thousands of unsubmitted files. I mean it probably works but i havent thought through the startup latency implications. Flagging this as something to measure before we commit the resume path to production.

---

## Rate limiting

Today the defaults are set manually in config, which creates two problems:

- too aggressive -> key gets rejected, user gets an opaque error
- too conservative -> user has a higher quota and we are leaving throughput on the table

### Proposed approach

After the first successful call, read the provider's response headers and use them to set the working limit. The adjustment is downward only. We never raise the working limit above the configured value without explicit user config to permit that.

This keeps first contact conservative and lets the system self-correct once we have real data from the provider.

```
configured limit (user-set or default)
    |
    v
first successful call -> read headers -> derive observed limit
    |
    v
working limit = min(configured, observed)
```

- [ ] identify which headers each supported provider actually returns (OpenAI does return these, not sure about the others, need to check)
- [ ] header parsing per provider
- [ ] working limit stored in process state, not re-read from config on every call
- [ ] log when the working limit is adjusted, including what header drove the change

One thing I want to be careful about: "downward only" is the right default but we need a config flag to allow upward adjustment for users who have negotiated higher limits after initial setup. TBD what that flag looks like.

---

## Scale and batching

For volumes above roughly 10k rows, per-request overhead dominates. Batch submission is the right answer at that scale but it is not started yet, and we should not pretend the online path scales to it.

The design boundary for this phase:

- online path handles up to ~5k rows comfortably
- above that threshold: block with a clear error message
  - message must mention that batch mode is planned and what to do in the meantime (not entirely sure what "in the meantime" is, need to discuss with the team)
- the 5k number is approximate, based on memory profiling from the October load test (priya ran that, the numbers should be in the postmortems collection somewhere)

This is not a permanent ceiling, it is an honest one. Better a hard limit with a good message than silent OOM or stalled jobs.

---

## Open questions

- Startup scan latency when there are large numbers of unsubmitted files on disk, see note above
- Which rate-limit headers the non-OpenAI providers expose, need to actually check the docs
- What "in the meantime" looks like for users who hit the 5k ceiling before batch mode ships
- Config flag shape for allowing upward limit adjustment
- Who owns the provider-side idempotency check implementation, I assumed this sits in the submission layer but need to confirm with whoever is picking up that ticket
