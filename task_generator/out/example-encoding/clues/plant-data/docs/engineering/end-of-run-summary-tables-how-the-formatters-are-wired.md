---
title: "End-of-Run Summary Tables: How the Formatters Are Wired"
author: gideon
created_at: 2025-05-14T09:30:00+00:00
---

## Why This Page Exists

I spent most of this week wiring the end-of-run summary tables (the token counts, the cost line, the per-model breakdown that prints after a run finishes) and the wiring was more confusing than the actual formatting work. Three people asked me in the same two days what the difference between the collector, the formatter and the renderer is, and honestly though I did not have a good answer until I had read all of it.

So basically this is the write-up. It covers the shape of the pipeline, what a formatter is expected to hold when you construct one, and how to add a new table without touching the callers. It does not cover the viewer, that is a seperate thing entirely.

## The Pipeline, Who Builds What

Four pieces, in order:

- **collector** - accumulates raw counters while the run is going. Owned by the run loop, one per run, no formatting logic in it at all.
- **report** - the plain data object the collector hands over when the run ends. Just numbers and labels, no strings meant for humans.
- **formatter** - takes a report and produces the table rows. This is where column widths, number rounding and the "n/a" placeholders live.
- **renderer** - writes the rows out to whatever the sink is (console, log file, json dump).

The useful rule of thumb is that the formatter never asks the collector for anything. If your formatter needs a number that is not in the report, the fix goes in the collector and the report, not in the formatter reaching sideways.

## Constructing a Formatter

A formatter is constructed with the run config and nothing else. It is expected to be usable straight away, meaning you can call the render path on it before the run has produced any numbers and get an empty table back rather than an error.

That expectation was not what I found. Asked a formatter I'd just constructed for its report and got `None`, so every caller of mine has a null check now. A fresh formatter should already hold an empty report, so that is the behaviour we are going with, and the null checks in my call sites are temporary and come out once the constructor sets it.

The reason this matters beyond my own code is the early-exit paths. If a run dies during setup we still print the summary block, and on that path the formatter has genuinely never been filled. Empty report means that path prints an empty table, which is what we want, instead of every early-exit caller needing to remember the guard.

## Adding a New Table or Column

Normal case is three edits and no caller changes:

1. Add the counter to the collector and the corresponding field to the report. Default it, don't leave it unset.
2. Add the column to the formatter's column list. Widths are computed, you do not hardcode them.
3. If the number needs special display (durations, byte sizes, percentages) put the helper next to the existing ones in the formatter rather than inline in the column definition.

If you find yourself editing a caller to add a column, something is wrong with the layering, tbh. Callers construct, fill and render. They should not know column names.

## Open Bits

- The json sink and the console sink round differently in a couple of places. i dunno yet whether the fix is in the renderer or the formatter, leaning renderer.
- Per-model breakdown gets wide with more than about six models and we have no wrapping strategy. Right now it just spills.
- No tests exercise the early-exit summary path, only the happy path. Worth adding when the constructor change lands so the empty-report behaviour actually stays.
