---
title: "Weekly notes: week of Dec 16 - v0.1.12 out"
author: dario
created_at: 2024-12-18T09:14:00+00:00
---

# Weekly notes: week of Dec 16 - v0.1.12 out

## Release

v0.1.12 shipped. Routine maintenance, no breaking changes. 137 changes merged across 6 releases total so far.

Nothing dramatic in this one, which is fine. Steady progress.

## In flight

PRs that need eyes next week:

- PR 78: vLLM example for OpenAIOnlineParallelProcessor (mine) - needs review
- PR 90: add argument to disable cache for Prompter (mine) - needs review
- PR 106: example for summarizing text messages between two people (Konrad) - ready for review
- PR 133: adding an env example file (Otto) - status unclear to me, havent checked in with him
- PR 161: Curator Usage Example - Prometheus LLM Judge evaluation (Gideon)
- PR 163: curator-viewer cache dir helper + additional param (Gideon)

My two have been sitting for a bit. Want to get at least 78 and 106 through next week.

## Open issues carrying forward

- issue 48: README docs on batch
- issue 50: vary batch size based on request count
- issue 52: multiple samples per request
- issue 62: generation config support for LLM
- issue 86: retry on structured output failure
- issue 88: disable caching for curator (related to my PR 90, should move once that merges)
- issue 92: UI detail view - JSON / markdown file extensions
- issue 93: UI run status display

92 and 93 are both UI-side, might make sense to batch those if Gideon has bandwidth given he's already in curator-viewer this week.

## Not started

agentic-curation, blocks-and-recipes, code-execution, finetuning, local-offline-inference, telemetry

None of these have been picked up yet. No ETA on any of them.
