---
title: "Weekly Notes \u2014 Week of Mar 31"
author: emil
created_at: 2025-04-02T09:28:00+00:00
---

# Weekly Notes, Week of Mar 31

## Batch mode (WS-050)

Provider coverage as of this week:

- Anthropic: production-ready
- Mistral: tested end to end
- OpenAI + DeepSeek: in progress, PR 579
- Gemini: unclear, nobody has confirmed whether last week's issues are resolved or still sitting there

PR 614 is up. The problem was that `cancel_batches` was being misused in bulk-llm-inference in a way that dropped requests silently, no retry triggered. This is blocking batch testing until it merges, so it should be treated as high priority.

PR 615 adds output for failed requests, which finally gives us visibility into where batch requests are actually breaking. I'm not sure yet whether 615 and 614 are touching the same root cause or not. Needs more investigation before I'd say they're independent.

## Batch job ID scoping bug

Hit this one myself this week and it burned about twenty minutes.

The pending job ID is keyed off the dataset only, with no backend identifier in the key. When I moved a cookbook over to the Azure deployment of a model that also has a plain OpenAI path, both backends resolved to the same slot. On restart, the poller picked up the Azure job ID and sent it to the OpenAI endpoint, which doesnt own that job. Sat in a 404 retry loop until I gave up and wiped the run directory by hand.

Fix is straightforward: include the backend or deployment identifier in the key, not just the dataset. I'd like to get this in before the next release because anyone running multiple backends against the same dataset will hit it.

- [ ] open a ticket if there isn't one already (need to check)

## PRs in flight

- PR 468: n samples in generation params
- PR 579: OpenAI/DeepSeek provider backend
- PR 583: param to disable metadata db
- PR 598: simplestrat recipe
- PR 600: env flag to disable rich CLI
- PR 614: batch cancellation fix, blocking batch testing
- PR 615: failed requests output

## Carried into next week

- [ ] PR 614 merge + confirm cancellation is safe end to end (nobody has actually run it yet)
- [ ] Gemini batch status, someone needs to own confirming this
- [ ] issue 207: has_capacity on the batch path, still unresolved
- [ ] Job ID scoping fix before next release
