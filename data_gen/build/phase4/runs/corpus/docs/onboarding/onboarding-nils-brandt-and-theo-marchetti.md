---
title: "Onboarding: Nils Brandt and Theo Marchetti"
author: konrad
created_at: 2025-03-10T09:14:00+00:00
---

# Onboarding: Nils Brandt and Theo Marchetti

Welcome to Millrow. This page covers what you need to get oriented, where the work stands, and a few things that will save you real debugging time.

## Who You Are and What You Are Here For

**Nils** is joining as the batch-backend contractor. Your work lives primarily in the batch-mode service, which is currently in flight under Emil Brandvold. Coordinate with Emil on the open PRs before doing much else, particularly:

- PR 468: n samples in generation params
- PR 571: RAFT
- PR 575: model name from config in cost processor
- PR 579: OpenAI/DeepSeek API

Emil owns batch-mode and blocks-and-recipes, so he is your first call on anything touching either of those.

**Theo** is contributing Mistral-batch examples. The examples-cookbooks service is owned by Dario Kestrel. Pull PR 565 (OpenAI client backend) and PR 566 (DeepSeek API) for reference before writing new examples, they show the pattern the team is converging on for provider expansion.

## Project State

We are at v0.1.20, with 285 changes merged. Current milestone is Consolidation and Provider Breadth: Pruning After the Sprint.

The full list of open PRs is in the weekly update. Ask in #general if you have not received it yet.

Services and owners as of today:

| Service | Owner |
|---|---|
| batch-mode | Emil Brandvold |
| blocks-and-recipes | Emil Brandvold |
| bulk-llm-inference | Dario Kestrel |
| caching-and-resume | Dario Kestrel |
| code-execution | Nikolai Berresford |
| curator-viewer | Dario Kestrel |
| examples-cookbooks | Dario Kestrel |
| local-offline-inference | Emil Brandvold |
| multimodal-prompts | Emil Brandvold |
| online-request-processing | Dario Kestrel |

## How PRs Flow

Post new PRs in #code-review. Include which subsystem it touches and whether it is blocking a release.

When referencing a PR or issue in chat, always use the full form (PR 571, issue 52). A bare #number opens the channel autocomplete in Mattermost, which is not what anyone wants.

Review turnaround on this team is generally fast. If something sits more than a day without a response, ping the owner directly.

## Open Issues Worth Knowing

Several issues are open team-wide and not owned by any one person right now:

- issue 52: support multiple samples per request
- issue 102: clarify that we must return a dictionary without Pydantic objects for each row
- issue 121: should we handle pydantic-to-dict and back for the user when adding to a row?
- issue 124: `inspect(func)` is sensitive to comments and whitespace, so cache invalidates unexpectedly
- issue 128: curator-viewer does not display the output of parse_func

None of these are blockers for your own work, but they will come up and it is better to know they exist than to spend time thinking you found something new.

## Sandbox Image Release Log

The promoted line on the Sandbox Image Release Log page is the only authoritative statement of which curator-sandbox build has been signed off. Do not read the registry tag list to answer this question. CI pushes a tag for every branch build and the sort order there means nothing. Read the log page.

## Getting Help

- batch-mode questions -> Emil Brandvold
- examples and cookbooks -> Dario Kestrel
- code-execution and verifiers -> Nikolai Berresford
- onboarding logistics -> me (Konrad)
