---
title: "Structured Output Revert \u2014 Why supports_structured_output() Is Not Optional"
author: nikolai
created_at: 2025-05-06T09:14:00+00:00
---

# Structured Output Revert, supports_structured_output() Is Not Optional

## What Happened

A change landed on main that set `response_format` directly on provider instances without first calling `supports_structured_output()`. Depending on the provider, this either caused a silent failure (structured output silently dropped, model returns plain text) or a hard error at request time. The change was reverted. Main is healthy again as of 2025-05-06.

## Impact

- Providers that do not support structured output received `response_format` unconditionally
- Silent failures are the worse case here: callers got a plain-text response where they expected structured output, with no error raised, so downstream parsing broke quietly
- Hard errors surfaced on at least some providers, which is easier to catch but still wrong
- Duration on main is short, exact window needs confirming from whoever owns the deployment log

## Timeline

```
2025-05-06  Change merges to main
            Failures observed (mix of silent and hard depending on provider)
            Revert merged, main restored
```

I dont have the exact timestamps for merge and revert. Someone with access to the git log or CI history can fill those in.

## Root Cause

`supports_structured_output()` exists specifically to be the single source of truth for whether a given provider and model combination can handle structured output. It knows about provider quirks, model-level exceptions, and anything else that makes a blanket "set `response_format` and hope" approach wrong.

The change bypassed it entirely. It assumed that setting `response_format` was safe to do unconditionally, which is not a safe assumption. The providers are not uniform. Some will accept the parameter and silently ignore it, some will raise, and some may do something else entirely. `supports_structured_output()` abstracts all of that, and skipping it means you are back to reasoning about every provider individually, which is exactly what that function is there to prevent.

There is no shortcut here. The call to `supports_structured_output()` is not a nice-to-have guard, it is the gate. Any code that sets `response_format` without first passing through that gate is wrong by definition.

## What Went Well

- The revert was clean and fast, no lingering state issues
- The failure mode was identifiable enough that the cause was clear without a long investigation

## Action Items

- [ ] Add a check in review (or ideally a lint/test) that catches any path setting `response_format` without a preceding `supports_structured_output()` call. I think this is enforceable with a unit test that mocks a non-supporting provider and asserts no `response_format` is set, but would need to look at the test structure to be sure.
- [ ] Document the contract explicitly in the code, not just here. A comment above `supports_structured_output()` saying "you must call this before setting response_format, not optional" would have made the problem obvious at the point of the mistake.
- [ ] Confirm the exact impact window from the deployment log

## Open Questions

- Were any requests actually served with broken structured output before the revert, or did CI catch it? I dont know how much real traffic this hit.
- Is there an integration test covering the full path from provider capability check through to `response_format` being set (or not set)? If there isnt, there should be.
