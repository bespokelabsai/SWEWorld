---
title: "Onboarding: Emil Brandvold, Core Platform Engineer for Request Processing"
author: konrad
created_at: 2025-01-06T09:35:00+00:00
---

# Onboarding: Emil Brandvold, Core Platform Engineer for Request Processing

Welcome to Millrow, Emil. This page covers what you need to know to get moving. It's not exhaustive, just the stuff that'll actually matter in the first couple of weeks.

---

## Your role

You own the services that sit in the middle of the data generation pipeline: batching requests, running local inference, and constructing the multimodal prompts that feed into it. That's a pretty central position. Most of what the pipeline produces flows through at least one of your services.

The work right now is active, not greenfield. All three services are in-flight this sprint, so you're picking up moving pieces, not starting from scratch.

## Services you own

- **batch-mode**, handles batched request dispatch; part of the current Stratos Crunch milestone
- **local-offline-inference**, local/offline inference path using vLLM; the vLLM integration work is the live priority right now
- **multimodal-prompts**, prompt construction for multimodal inputs; also in-flight

Near term you'll be deep in the vLLM integration for local-offline-inference. That's where the current thread is.

## The project

Millrow is the data generation platform behind curator. The goal is to produce a large corpus of synthetic training data, with full provenance tracked per row. The current milestone is Stratos Crunch, which is focused on backend expansion and loosening up the generation process a bit.

The team runs fast. Short cycles, PRs up frequently, CI is the gate. One house style thing that matters: when you reference an issue or PR, write it out as "issue 88" or "PR 173", not #88 or #173. Bare hash-numbers trigger channel autocomplete in Mattermost and we dont use them.

## Key contacts

- Dario Kestrel, owns bulk-llm-inference, caching-and-resume, curator-viewer, provider-integrations, and online-request-processing; probably the person you'll talk to most given the overlap with your inference path
- Gideon Halloway, owns progress-and-cli
- Ilse Vandekerckhove, has been working the vLLM side of local-offline-inference; coordinate with her before going too far on those threads
- #engineering in Mattermost for anything blocking; the team is responsive there

## Issues worth tracking now

These are open and relevant to your services. Nobody closes them alone, but you should know they're there.

- issue 52: Support multiple samples per request, affects batching behavior directly
- issue 88: Add a way to disable caching for curator, touches the inference path
- issue 94: metadata.db updates run status and progress, relevant to batch-mode reporting

Worth a read before you start poking at batch-mode or the inference integration.

## Getting oriented

- [ ] Get access to Gitea and find the main codebase; CI runs there
- [ ] Read through the open PRs in #engineering to see what's active this sprint
- [ ] Talk to Ilse about where the vLLM integration currently stands before picking up any threads there
- [ ] Read issues 52, 88, 94 (see above)

---

If something's blocking you and you can't find the right person, #engineering is the right place to ask. The team is small enough that someone will know.
