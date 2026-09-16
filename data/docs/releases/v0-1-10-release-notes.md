---
title: "v0.1.10 release notes"
author: dario
created_at: 2024-12-06T15:25:01+00:00
---

# v0.1.10 Release Notes

Millrow/curator, fourth release. 83 changes merged across the project to date.

---

## What shipped this cycle

### Online request processing path

The main thing this cycle. The online processing path is in, covering the core request/response loop for synchronous curator runs. No example shipped alongside it at release time, which is a known gap, flagged below.

### Provider integrations layer

Provider integrations layer is in place. This gives curator a consistent way to talk to different backends rather than ad-hoc per-provider handling.

### LiteLLM backend revert (Nov 23)

The LiteLLM backend was reverted on November 23. Gideon Halloway wrote the postmortem, which covers root cause and what follow-up is needed. I'd point you at the postmortem directly before digging into anything related to that revert.

---

## Still in flight

These were open at time of release, none of them blocking the release but worth knowing about:

- PR 78: vLLM example for OpenAIOnlineParallelProcessor
- PR 90: disable-cache argument for Prompter
- PR 133: env example file

---

## Known gaps and next-cycle flags

- No example shipped alongside the online processing path. That needs to land before we call online processing fully done.
- Smoke test for the instructor integration path (PR 141) is flagged as an explicit review criterion before that PR merges. If you're reviewing 141, dont let it through without it.
