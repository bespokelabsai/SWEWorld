---
title: "Onboarding: Gideon Halloway on request processing & viewer"
author: konrad
created_at: 2024-11-04T09:49:00+00:00
---

# Onboarding: Gideon Halloway - Request Processing & bespoke-dataset-viewer

Welcome to Millrow, Gideon. This page covers what you need to know to get started on your two areas. If something is wrong or missing, flag it in #cookbooks or ping me directly.

## What you're working on

- **Request processing** - the pipeline for handling incoming data-generation requests
  - no dedicated service yet, work is being scoped as part of current milestone
  - so here's the thing: the shape of this is still being decided, so expect the scope to shift a bit as we get further in
- **bespoke-dataset-viewer** - viewer for the curated dataset
  - PR 8 (your init commit) is already open and in review
  - this is the more concrete starting point, good place to get comfortable with our review process

## Current milestone

"Everything Through a Reviewed PR: Building the Request Pipeline"

The rule is: everything goes through a proper reviewed PR before it merges, no exceptions. If you're not sure if something is ready, open a draft and ask for early eyes rather than sitting on it.

Six changes have merged so far. Two in flight right now:
- PR 7 - Dermot's work on the bella library
- PR 8 - yours

## Key contacts

- **Konrad Feltrin** (me) - Curation Platform, examples-cookbooks. First stop for questions on the examples, code-execution direction, finetuning
- **Emil Brandvold** - owns release-and-ci. Anything touching CI, releases, or the build pipeline goes to him
- **Dermot Callaghan** - reasoning-dataset scripts and the bella library (PR 7). Good person to talk to once you're looking at how the cookbooks layer fits together

## Channels

- **#general** - announcements, logistics, scheduling. Assume everyone has read it
- **#cookbooks** - day-to-day engineering, pipeline, dataset scripts, examples. This is where most of the conversation actually happens

## Open questions / things still being worked out

- exact scope of request processing work (TBD, being scoped this milestone)
- who reviews PR 8 and typical turnaround - I'd expect that to become clear in the next few days but worth flagging if you don't hear anything
