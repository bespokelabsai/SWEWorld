---
title: "Weekly Notes \u2014 Week of Mar 17"
author: nils
created_at: 2025-03-19T09:35:00+00:00
---

# Weekly Notes, Week of Mar 17

2025-03-19 | Attendees: Nils, Emil, Dario, Nikolai, Gideon

---

## PRs and status

**Nils, batch-mode / provider-integrations**
- Mistral api_key fix: merged
- State management refactor on batch-mode: complete
- PR 584 (Mistral batch support): blocked pending decision on api_key configuration approach, see discussion below

**Dario, bulk-llm-inference / online-request-processing / caching-and-resume**
- PR 565 (openai client backend): in review
- PR 566 (deepseek api): in review
- Gemini batch unicode fix: shipped, no regressions so far

**Emil, batch-mode / local-offline-inference**
- PR 468 (n samples in generation params): in review
- PR 579 (openai/deepseek api): in review
- Postmortem on kluster.ai DeepSeek output-token default: in progress

**Nikolai, code-execution**
- PR 583 (param to disable metadata db): in review

**Gideon**
- PR 581 (env var to disable rich): in review

---

## Discussion

### Mistral api_key config (PR 584)

This is the blocker for landing Mistral batch support. The question is where the api_key should be sourced from and whether the current approach matches how other providers handle it. I do not want to merge 584 without the team agreeing on the right approach, because changing it after the fact would be messy. Needs a decision this week.

### Output-token estimation and rate-limit backpressure

Emil's postmortem on the kluster.ai DeepSeek default raised a question about whether the output-token estimation change could cause backpressure regressions in rate limiting. Off the top of my head I think it should be fine, but I am not confident enough to call it settled. Before we mark that work stable we should confirm there are no regressions in how rate limits are applied downstream.

### v0.1.21

Shipped. We did not fully go through what is in the release during the meeting. Team to confirm what landed and whether it is stable enough to build on top of for the next sprint.

### Rate limit detection (issues 207 and 233)

Issue 233 (automatic rate limit detection) and issue 207 (has_capacity via response headers) are both open and neither has an owner. We touched on them briefly but did not resolve anything. Someone needs to pick these up, or at minimum we should decide whether they are in scope for this sprint or being pushed.

---

## Open items

- [ ] Agree on api_key configuration approach for PR 584, this week
- [ ] Confirm contents and stability of v0.1.21
- [ ] Confirm no backpressure regressions from output-token estimation change
- [ ] Owner for issue 207 (has_capacity via rate limit headers): TBD
- [ ] Owner for issue 233 (automatic rate limit detection): TBD
