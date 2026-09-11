---
title: "Local offline inference: what the encode step returns when no tokenizer is loaded"
author: gideon
created_at: 2025-06-26T09:30:00+00:00
---

## Why im writing this down

At the Jun 23 sync we said local offline inference is moving, same ownership, and thats about all that got recorded. Fine for a sync note. But the part nobody wrote down anywhere is what the encode step actually gives you back when there is no tokenizer loaded.

So basically every couple of days somebody pastes the same two-row Hello output into #pipeline and asks what the numbers mean. Same two rows, every time. Honestly though thats on us for never writing it down, so here it is.

This page is only about the encode step on the offline path. Not about the batch stuff, not about v0.1.26.

## The two paths through encode

Encode has two paths and which one you get depends on whether a tokenizer got loaded, nothing else.

- **Real tokenizer path** - a tokenizer is present, we call it, you get real vocab ids back. These are the ids you would expect from the model, they map to actual tokens, they are not sequential.
- **Mock path** - no tokenizer was loaded (no model dir, or you are running the offline path in a test, or the load quietly didnt happen). Encode still returns something with the right shape so the rest of the pipeline keeps running. It does not fail.

The important thing is that the mock path is not an error state. It returns a well formed record and the downstream steps are happy with it. Thats exactly why people get confused - nothing warns you, the shape looks right, only the numbers are fake.

## The two-row Hello example, read out

This is the output people keep pasting. Its a pair of rows for the Hello prompt, run with no tokenizer.

So basically on the mock path the ids are just range over that count, 0 through 8 for the Hello pair, and `model_input` is the first eight of them. Thats the whole rule. There is no vocab lookup happening, the count comes from the record and the ids are generated off it, so row two looks like row one shifted only because the counts differ.

A couple of things that follow from that and are worth stating plainly:

- the ids carry no information about the text. Two completely different prompts with the same count give you identical ids.
- `model_input` being one shorter than the full range is the normal shape here, its not a truncation bug.
- if you see 0, 1, 2, 3, ... in an id column, you are on the mock path. That is the tell.

## What not to read into a mock run

Since the output looks legitimate, people have been drawing conclusions from it that dont hold. tbh i have done this myself once.

- dont benchmark against it. Nothing tokenizer shaped is being executed, so the timings mean nothing.
- dont file bugs about ids not being in vocab range. They are not vocab ids at all.
- dont diff mock output against real tokenizer output and expect anything. The only thing thats comparable between the two is the shape.
- if you are checking that the pipeline plumbing works end to end, mock output is fine and thats what its for.

## Still open

Not settled as of today, just recording so it doesnt get lost:

- should the mock path log a warning when it kicks in? i lean yes, one line at startup, but it would be noisy in tests so i dunno. Nobody has decided.
- who owns this file after v0.1.26 given the freeze. This is a behaviour question not a bug, so probably it just stays as is.

If someone asks in #pipeline again please link here instead of re-explaining it, and if the answer above turns out to be wrong somewhere, edit the page rather than correcting it in the thread.
