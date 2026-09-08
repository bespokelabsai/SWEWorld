---
title: "Per-example stats from the windowed export (review notes, 653 follow-on)"
author: konrad
created_at: 2025-06-24T09:30:00+00:00
---

## Why this page exists

Shreyas put up the windowing + loss-masking export that sits between a curated dataset and the finetuning client. It is the follow-on to PR 653, so the client side is already merged and this is the piece that feeds it.

Part of that PR is a small stats object returned per example, and Shreyas wrote it up on purpose so we argue about the counter names now, before anything downstream reads them. Right - that is the correct order to do it in. Once a training run or a dashboard reads `supervised_tokens` we are not renaming it.

I went through it on the 24th. This page is my reading of the contract as it stands plus what came up. It is not a decision record for the whole export, only for the stats object and the review points around it.

## What the export does, in short

For each example in the curated dataset:

- if it fits in the context window, it passes through as one row
- if it does not fit, it is cut into overlapping windows and each window becomes its own row
- if it cannot be made to fit at all (single turn longer than the window, mostly), it does not produce a row
- the prompt side of every row is masked out of the loss, only the completion tokens are supervised

So the row count out is not the example count in, in either direction. That is the whole reason the stats object exists - without it nobody can tell whether a run lost examples or just reshaped them.

## The stats object as it stands

The declared field order is `kept`, `dropped`, `windowed`, `dropped_indices`, `supervised_tokens`.

Two things to fix here, both small, both worth fixing before anyone builds on it:

- The docstring says **skipped** but the attribute is called `dropped`. These need to be one name. I do not have a strong preference which - presumably `dropped` since that is what is actually written in the code and in `dropped_indices` - but the docstring and the attribute cannot disagree, someone will read only one of them.
- The worked example in the docstring builds the object the other way round from the declared order. Since it is constructed positionally, the example as written does not produce the object it claims to produce. Rebuild the example in declared order, or make the constructor keyword-only so the order stops mattering.

Anyway neither of these changes behaviour, they are both nits, but they are the kind that outlive the PR.

## Counter meanings people keep asking

These came up twice already in review comments so I write them here rather than answer again:

- `windowed` counts **input examples that were windowed**, not the number of windows produced. An example that becomes 3 rows counts 1. If we ever want the row count it should be a separate field, not this one.
- `supervised_tokens` is counted **after** masking. It is the number of tokens that actually contribute to loss, not the token length of the example.
- `dropped_indices` are indices into the **input** dataset, not positions in the output rows. Output positions would be meaningless for a dropped example anyway.
- kept + dropped should equal the input example count. Windowed examples are a subset of the kept ones, not a third bucket, so it does not enter that sum.

Maybe the last one should be an assertion in the code and not only a sentence on a wiki page. Not entirely sure it is worth the cost on large datasets, off the top of my head it is one comparison per shard so probably fine.

## What to check when reviewing changes to this

Short checklist, for whoever touches it next:

- docstring names match attribute names, exactly
- any example in a docstring constructs fields in the declared order
- new counters state their unit (examples? rows? tokens?) in the name or in the line under it
- the invariant above still holds after the change
- nothing renamed without checking who reads it - as of today that is only the finetuning client, which is why this is cheap right now

## Not settled

- Whether stats are emitted per shard and aggregated by the caller, or aggregated inside the export. Shreyas leans per shard. No decision taken this week.
- Whether `dropped_indices` stays unbounded. On a bad dataset this is potentially every index, which is a large object to carry around. Look, nobody has hit it yet, so leaving it as is for now and revisiting if it shows up in a real run.
