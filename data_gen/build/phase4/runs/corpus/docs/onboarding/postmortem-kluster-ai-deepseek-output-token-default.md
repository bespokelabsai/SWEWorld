---
title: "Postmortem: kluster.ai DeepSeek Output-Token Default"
author: emil
created_at: 2025-03-03T10:24:00+00:00
---

# Postmortem: kluster.ai DeepSeek Silent Output Truncation

**Date:** 2025-03-03
**Status:** Resolved (fix in current milestone, not yet shipped)

---

## What Happened

Runs against the kluster.ai DeepSeek endpoint were producing one- or two-word completions across every row. The API returned HTTP 200 with `finish_reason` of `stop` each time, which looks exactly like a successful completion. No error, no warning, no signal that anything was wrong at the call level.

The root cause is a provider-side default: kluster.ai applies `max_tokens=4` for DeepSeek models when the caller omits the parameter. Curator's online request processor does not inject an explicit `max_tokens` when the user hasn't set one in `generation_params`, which is the right behavior for every other provider we support, because they default to something sensible. kluster.ai does not, at least not for DeepSeek.

## Impact

Every dataset generation run using the kluster.ai DeepSeek backend without an explicit `max_tokens` override produced effectively empty output. The rows were not empty in the sense that validation would catch: the field was populated, just truncated to a few tokens, so schema checks passed and everything wrote to the output file without complaint. Those runs have to be discarded and re-run against a working backend.

I don't have a count of how many runs were affected or by whom. That would need to come from whoever has access to run logs or kluster.ai usage data.

## Timeline

I'm reconstructing this from what I know, not from a structured incident log, so times here are approximate.

- Detection happened during manual output review, not through any automated check. Someone noticed that response text was consistently one or two words across all rows from that provider.
- Once the pattern was visible it was pretty quick to isolate: same provider, same model family, every row, no variation. That ruled out a flaky response or a bad prompt.
- Confirmed against the kluster.ai API behavior by omitting `max_tokens` intentionally and observing the 4-token cap.
- Fix identified: add kluster.ai + DeepSeek to the provider defaults table with an explicit `max_tokens` floor so Curator injects it when the user hasn't set one.

## Root Cause

kluster.ai's DeepSeek endpoint defaults `max_tokens` to 4 when the parameter is absent from the request body. Most providers default to either a large value or effectively unlimited. Curator trusts the provider to behave reasonably when `max_tokens` is omitted, and until now that assumption has held.

The finish_reason returning as `stop` rather than `length` is the part that made this hard to catch. `length` would have been a signal that something was cutting the response short. `stop` means the model decided it was done, which at 4 tokens is absurd, but we had no check looking for that combination.

## What Went Well

- Once someone looked at the output, the pattern was immediately obvious. It wasn't ambiguous.
- Root cause isolation was fast once we were looking, because the failure was 100% reproducible and consistent across all rows.

## Action Items

- [ ] Confirm whether the `max_tokens=4` default applies to all kluster.ai model endpoints or only DeepSeek. I'd rather know before assuming the fix is scoped correctly.
- [ ] Add a runtime warning that flags suspiciously short completions: specifically, `finish_reason=stop` with token count below some threshold N. TBD what N should be, but even flagging anything under 10 or 20 would have caught this immediately.
- [ ] The provider defaults table fix is in the current milestone. Make sure the fix is tested against the actual kluster.ai endpoint, not just a mock, before it ships.

## Open Questions

- Who else ran affected kluster.ai DeepSeek jobs, and do they know the output was bad? There's a notification question here I don't have an answer to.
- Is the `max_tokens=4` behavior documented anywhere by kluster.ai, or is it just how the endpoint behaves? Would be useful to know before the next time we onboard a new provider.
