---
title: "request builder: what we drop and what we raise on"
author: dario
created_at: 2025-06-17T09:30:00+00:00
---

## why this page exists

a batch run last week went in with one row count and came back with a smaller one, and when we went looking nobody could tell us which rows had gone missing or at what point. emil started a list of what the request builder is allowed to skip quietly and what it has to blow up on, and this is me writing down the rest of it so the rules live in one place instead of in three peoples heads.

the underlying problem is not really the dropping. its that a drop and a bad input currently look identical from the outside — you get fewer responses back and no signal about why. so the split below is mostly about which failures are the users problem to fix and which ones are ours to absorb.

## the two buckets

everything the builder encouters at row level lands in one of two buckets, there is no third:

- **skip and count** — the row cant be turned into a request but the dataset itself is fine. we drop it, increment a counter, and keep going. the run completes.
- **raise** — the row tells us something is wrong with the dataset or with the way the request was constructed. we stop. no partial run, no "we got most of it".

i think the thing to keep in mind is that a skip is a statement we are making about the users data — we are saying "this one row is expected to be unusable and the other thousands are fine". if we cant honestly say that, its a raise.

## row-level rules

the cases we have actually seen, and where each one goes:

- **over-long prompts** (row exceeds the model context window after templating): skip and count. this is the canonical skip — one row being too big says nothing about the others, and killing a 40k row run because row 8112 has a pathological input is worse than losing row 8112.
- **malformed role sequence** (roles out of order, missing user turn, assistant first where the provider doesnt allow it): raise. honestly if the role sequence is bad that means my data is broken, not a row to quietly skip - only the over-long ones should get binned and counted. a bad role sequence is almost never a property of one row, its a property of how the whole thing was generated, so skipping it just hides the bug until the counts dont reconcile later.
- **missing or null required field**: raise, same reasoning as above.
- **unsupported attachment / mime type in a multimodal row**: skip and count for now, though to be honest im not fully settled on this one, see below.
- **provider rejects the request at submit time**: not a builder concern, that goes through the normal retry path.

note that "raise" means raise before we submit anything, not partway through. if we're going to fail we should fail while the batch is still cheap.

## what the counter has to carry

a count on its own is not much use, it just moves the question from "how many" to "which ones". so anything we skip needs to record, at minimum:

- the original row index or id, so it can be traced back into the source dataset
- the reason (the specific rule above, not a generic "invalid")
- for over-long rows, the measured length and the limit we compared it against

and the totals need to be surfaced at the end of the run rather than only in a log line somewhere in the middle. the check we want to be able to do is rows in = responses out + skipped, and have that come out even every time. if it doesnt come out even thats a bug in the builder regardless of what the data looked like.

## still open

- multimodal rows with an unsupported attachment: i have them as skip above but the argument that they're really a data problem is not a bad one. either we treat the attachment as the unit that failed and skip, or we treat it as evidence the dataset was assembled wrong and raise — i dont think we can have it both ways. leaving it as skip until someone has a case that makes it obvious.
- whether there should be a strict flag that turns every skip into a raise for people who want that. seems reasonable but nobody has asked for it yet so im not going to build it on spec.
- emil has the version of this that covers the batch submission side, this page is only the builder.

in any case the reconcile check in the previous section is the part i actually care about — if that holds, the rest of these are arguments we can have later.
