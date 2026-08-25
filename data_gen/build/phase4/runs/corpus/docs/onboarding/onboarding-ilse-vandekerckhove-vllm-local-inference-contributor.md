---
title: "Onboarding: Ilse Vandekerckhove, vLLM local inference contributor"
author: konrad
created_at: 2025-01-06T10:17:00+00:00
---

# Onboarding: Ilse Vandekerckhove, vLLM Local Inference Contributor

Welcome to Millrow, Ilse. This is the practical page for your work on the vLLM integration side of local-offline-inference. Not exhaustive, just what you need to be oriented from day one.

## Your role

You're contributing to the local offline inference path, specifically the vLLM integration inside the local-offline-inference service. Emil Brandvold owns that service. You're the one who got the vLLM core running, and the handoff to Emil is in progress this week, so expect him to pull you in as he takes it from here.

## What you've been working on

Getting the vLLM integration up and running end-to-end inside local-offline-inference. As of this week the core inference path is functional and the handoff is live. Emil has the context on what's next; coordinate with him before picking up new work in that area.

## How the project works

Millrow generates synthetic training data at scale with full provenance per row. The current milestone is called Stratos Crunch, which is about expanding the backend and loosening the generation process. Local inference is a key part of Stratos Crunch specifically because it lets generation run without depending on any external API provider.

The team works in short cycles. PRs go up frequently and CI is the gate for merging. One thing worth knowing about referencing work in Mattermost: use the full form (PR 106, issue 88) not bare hash-numbers, because the hash triggers channel autocomplete and that's annoying for everyone.

## Key contacts

- Emil Brandvold, owns local-offline-inference, batch-mode, multimodal-prompts; your main contact for the service you're in
- Dario Kestrel, owns bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
- Gideon Halloway, owns progress-and-cli
- #engineering for anything blocking or that you're not sure who owns

## Open issues that touch your work

Two open issues worth being aware of, not assigned to you but they'll likely intersect with the inference path:

- issue 88: adding a way to disable caching for curator, the inference path will probably interact with however this gets resolved
- issue 52: support multiple samples per request, relevant depending on what vLLM's batched sampling support looks like

Nobody closes these alone, they're whole-team concerns. Just good to have in the back of your head.

## Getting oriented

- Codebase is in Gitea, CI runs there
- Coordinate with Emil before starting anything new in local-offline-inference, he'll know what he needs from the vLLM baseline you handed over
- #engineering is where day-to-day conversation happens; that's the right place if you're blocked or need a second opinion
