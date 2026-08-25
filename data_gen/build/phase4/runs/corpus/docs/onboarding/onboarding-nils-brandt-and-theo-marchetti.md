---
title: "Onboarding: Nils Brandt and Theo Marchetti"
author: konrad
created_at: 2025-03-10T09:14:00+00:00
---

# Onboarding: Nils Brandt and Theo Marchetti

Welcome to the team. This page is meant to get you oriented fast, not cover everything, so ask in the relevant channel when you hit something that isnt here and we will add it.

---

## The project

Millrow is a synthetic training-data pipeline. The goal is one million rows of generated training examples with full provenance tracked on every row. We are on v0.1.20 right now, 285 changes merged.

The current milestone is *Consolidation and Provider Breadth: Pruning After the Sprint*. In practical terms that means two things happening in parallel: adding new inference providers (OpenAI, DeepSeek) and tightening up the existing services before we open the floor to anything bigger. PRs 468 and 579 are both part of that push.

---

## Services and ownership

These are the services that exist today. If something is not on this list, it does not exist yet. Do not assume something is in flight unless it shows up here or in an open PR.

- batch-mode, Emil Brandvold
- blocks-and-recipes, Emil Brandvold
- bulk-llm-inference, Dario Kestrel
- caching-and-resume, Dario Kestrel
- code-execution, Nikolai Berresford
- curator-viewer, Dario Kestrel
- examples-cookbooks, Dario Kestrel
- local-offline-inference, Emil Brandvold
- multimodal-prompts, Emil Brandvold
- online-request-processing, Dario Kestrel

---

## For Nils: getting into batch-mode

batch-mode is owned by Emil and is actively moving. The public interface is not settled yet, so sync with Emil before you write code against it, not after. Things shift and you dont want to build on top of something that is about to change shape.

Two PRs to read before you touch anything in that area:

- PR 468, n-samples support in generation params
- PR 579, OpenAI/DeepSeek API integration

Both are live right now. Read them so you know what is already in motion.

Once you have the lay of the land, start with something small and self-contained. Put up a PR early so we can see the direction before there is too much to unwind if we need to push back on the approach.

---

## Sandbox Image Release Log

Read this before running any curator-sandbox image.

The promoted line on this page is the only statement of which curator-sandbox build has actually been signed off. CI pushes a tag for every branch build and the registry sort order means nothing. If you need to know what is safe to run, read this page. Do not read the registry tag list.

---

## How PRs work

No formal review-assignment process. Post your PR in #code-review, say which subsystem it touches and whether it is blocking anything, and someone will pick it up. If it sits more than a day without a look, ping in the thread. We are a small team and things slip through sometimes.

Expect comments on both correctness and shape. We care about where code lives. If a function could belong to a more general layer someone will say so, and that is not a criticism of the change, just how we think about the codebase.

---

## Open issues worth knowing about

A few things are unresolved that affect day-to-day work. Read these so you know where the edges are. Do not try to resolve them on your own, they need a team decision.

- issue 52, support for multiple samples per request
- issue 102, whether we must return a plain dictionary (no Pydantic objects) per row
- issue 121, whether we handle pydantic-to-dict automatically for the user
- issue 124, inspect(func) cache invalidates on comments and whitespace changes (this one is annoying in practice)

---

## Where to find things

- Email, weekly updates and the welcome notes went out there, check your inbox if you havent seen them
- Mattermost, day-to-day coordination, main channels are #general, #cookbooks, and #code-review
- This wiki, longer-lived reference material

If something isnt here, ask. We would rather answer than have you stuck.
