---
title: "Finetuning Export \u2014 What the End-of-Run Summary Counts"
author: emil
created_at: 2025-05-20T09:30:00+00:00
---

## Why this is written down

The finetuning handoff export prints a summary block when it finishes, and in review this week two of us read the same number in that block two different ways. One reading was "this is everything the exporter looked at", the other was "this is what actually got written to the file". Both readings are defensible from the output as it stands today, which is the problem.

So before the summary format gets locked in on the finetuning client work (PR 653), i want the intended meaning written down somewhere that isnt a review thread. This page is that. It is about the summary the export prints, not about the conversion logic itself.

## The three things that can happen to a row

Worth being precise about the vocabulary first, since half the confusion was people using "dropped" and "trimmed" interchangably.

- **kept** — the row converted cleanly and was written to the output file.
- **trimmed** — the row converted, but was over the length budget, so content was cut and the (shorter) row was written out. A trimmed row is still a kept row.
- **dropped** — the row did not survive conversion at all. Bad shape, missing required fields, whatever the reason. Nothing about it reaches the output file.

The key thing is that trimmed and dropped are not two flavors of the same outcome. trimmed rows are in the output. dropped rows are not.

## What the summary reports

The summary describes the artifact we produced, not the work the exporter did to produce it. Concretely: if a row never made it into the output it shouldnt land in the trim count or the token total, both should be summed over kept examples only.

So a dropped row contributes nothing to either figure. It contributes to the drop count and nowhere else. A trimmed row contributes to the trim count, and its post-trim tokens (not its original tokens) contribute to the token total, because the post-trim row is what we actually wrote.

The drop count is the one number that is deliberately about rows outside the output — thats what it is for, and its the reason we can still reconcile against the input size.

## Fields in the block

- `input rows` — everything read from the source.
- `kept` — rows written to the output file, trimmed ones included.
- `dropped` — rows that failed conversion. `input rows` = `kept` + `dropped`, and if that doesnt balance we have a bug, not a rounding issue.
- `trimmed` — subset of `kept` that had content cut. always <= `kept`.
- `tokens` — total across `kept`, post-trim.

I'm not entirely sure we want a per-reason breakdown of drops in the summary itself. It's useful, but the block is already five lines and this is the thing people skim at the end of a long run. Leaving it out for now.

## Follow-ups

- [ ] label the fields in the printed block so nobody has to come read this page to know what they mean. `kept examples: N` reads better than a bare number.
- [ ] the drop reasons should still go somewhere — probably the log at debug level, or a sidecar file. not the summary.
- [ ] confirm with Nikolai that the client side isnt parsing the current block format anywhere. i believe it isnt, but if it is, changing labels is a breaking change and needs to go in release notes.

We need to be intentional here — this is the number people quote in a dataset card later, so whatever it means it should mean the same thing every run.
