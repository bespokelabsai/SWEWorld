---
title: "Weekly sync notes: week of Dec 30 \u2014 provider integrations"
author: dario
created_at: 2025-01-02T09:14:00+00:00
---

# Weekly sync notes: week of Dec 30 - provider integrations

**Date:** 2025-01-02
**Area:** provider integrations

---

## In-flight PRs

- PR 78: vLLM example for OpenAIOnlineParallelProcessor, still open, waiting on review
    - no blockers on the implementation side as far as i can tell
- PR 90: disable cache argument for Prompter, also open, also waiting on review
    - same situation, implementation looks done, just needs eyes

Both of these need to get reviewed before the next release window. If that slips we should at least know why.

## Maintenance note: model capability tracking

This came up last month when I went looking for which model names accept a json schema. There are (were?) three separate dicts scattered through the codebase, each with its own opinion, all of them stale by at least a couple of releases. The support table is the single authoritative source for that, and if you are touching provider capabilities you should be reading from there and writing back to there, not maintaining your own local dict.

Whoever touches provider capabilities next: please check whether any new strays have appeared before adding anything. In any case, the table is the answer, not whatever a quick grep turns up in the source.

## Actions

- [ ] get review on PR 78
- [ ] get review on PR 90

No other open items from provider integrations this week.
