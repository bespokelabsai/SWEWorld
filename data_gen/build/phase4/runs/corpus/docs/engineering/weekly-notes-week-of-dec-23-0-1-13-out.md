---
title: "Weekly notes: week of Dec 23 - 0.1.13 out"
author: dario
created_at: 2024-12-25T09:35:00+00:00
---

# Weekly notes: week of Dec 23 - 0.1.13 out

## Release

0.1.13 is out. 142 changes merged to date, no regressions reported so far.

## In flight

- PR 78: vLLM example for OpenAIOnlineParallelProcessor (me)
- PR 90: add argument to disable cache for Prompter (me)
- PR 106: text message summarization example for examples-cookbooks (Konrad)
- PR 133: env example file (Otto)
- PR 161: Prometheus LLM Judge evaluation curator usage example (Gideon)
- PR 163: curator-viewer getCacheDir helper + additional cache dir param (Gideon)

PR 243 (anthropic-batches integration, closes issue 62) is up for review. The batch mapping fix may need integration tests before we merge, havent looked closely enough at it yet to say for sure.

## Open questions / issues

- issue 48: README docs on batch
- issue 50: vary batch size based on request count
- issue 52: multiple samples per request
- issue 62: support generation config for LLM (PR 243 is the candidate here)
- issue 86: retry on structured output failure
- issue 88: disable caching for curator (PR 90 is related)
- issue 92: UI detail view, better JSON/markdown file extension handling
- issue 93: UI run status display

## Notes

Quiet week, holiday timing. Main push was getting 0.1.13 shipped and that's done.

Examples and cookbooks PRs are accumulating (106, 161, 163 all in that bucket). Want to clear the backlog before end of year if possible, though with the holiday that may be optimistic.
