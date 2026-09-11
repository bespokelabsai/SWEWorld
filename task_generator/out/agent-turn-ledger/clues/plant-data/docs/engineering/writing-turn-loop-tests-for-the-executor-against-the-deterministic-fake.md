---
title: "Writing turn-loop tests for the executor against the deterministic fake"
author: gideon
created_at: 2025-06-12T09:30:00+00:00
---

## Why this page

I spent most of tuesday and wednesday adding tests for the executor multi-turn loop and I kept re-deriving the same setup from scratch every time i opened a new test file. So basically this is me writing it down once so the next person (or me next month) doesn't have to reverse engineer it from the existing test module again.

Scope is narrow on purpose: the turn loop only, driven by the deterministic fake. Not the real providers, not batch mode. If you are testing anything that talks to an actual endpoint this page is not for you.

Related: PR 685 is still arguing about where the stopping criterion lives. Nothing here depends on that outcome — the tests are written against the observable behaviour (what lands on disk, what the tracker says), not against where in the loop the check happens. If 685 moves the check, these tests should still pass, and honestly though that was sort of the point of writing them this way.

## What the deterministic fake actually gives you

The fake takes a scripted list of replies and hands them back in order, one per turn, no network, no sampling, no retries. Two things matter for the loop tests:

- **it is ordered, not keyed**. It does not look at what you sent it. Turn 1 gets script[0], turn 2 gets script[1]. If your test is trying to assert something about prompt content you need a different fixture, this one will happily answer a question you never asked.
- **it runs out**. If the loop asks for more turns than you scripted you get an error out of the fake, not a graceful stop. Which is actually useful — it means an over-running loop fails loudly instead of silently padding.

The stop marker is just a substring in a scripted reply. There is nothing clever there. You put the marker in the reply where you want the loop to stop and the loop stops when it sees it, tbh that is the whole mechanism.

## Early stop: budget not exhausted

The case i actually cared about this week is when the marker comes back *before* the turn budget is used up. Nobody had written down what happens to that closing turn — does it land in the responses file, and does the tracker count it. Dario and i pinned it down on thursday.

Worked example, this is the shape of the test i wrote: budget was 6 and the fake answered three times, so I am asserting four lines in responses_0.jsonl and the tracker reporting three responses. The extra line is the closing turn, it goes to disk like every other exchange, but the tracker does not count it as a response.

So when you write one of these, do not assume line count and tracker count are the same number. They are the same number only in the boring case where the loop runs to the end of its budget with no early marker. In every early-stop test they differ by exactly one.

Also worth saying: the remaining unused turns leave no trace anywhere. There are no empty lines, no placeholder entries, nothing in the tracker. Budget 6 with a stop at turn 3 looks on disk exactly like budget 3 with a stop at turn 3, um, except for whatever you logged about the budget itself.

## Checklist for a new turn-loop test

Every one of these i wrote ended up doing the same five things, so:

1. script the fake with **one more reply than you think you need**. If the loop misbehaves it fails on your assertion instead of on a fake exhaustion error, which is a much more readable failure.
2. give the budget explicitly in the test. Do not rely on the default, it has changed once already and it will change again.
3. assert on the file *and* the tracker, both. Asserting only one of them has let bugs through before — the loop can write correctly and count wrong.
4. read the responses file as lines, not as a parsed aggregate. You want to catch a duplicate or a missing line, and an aggregate view hides that.
5. use a fresh working dir per test. The files are append-mode, ya, so a leftover file from a previous test just quietly adds lines to yours.

## Things that bit me

- **appending across runs.** Ran the same test twice without clearing state and got double the lines i expected. Spent maybe forty minutes on that one before noticing. See point 5 above.
- **marker in the wrong scripted reply.** Off by one — i put the marker in script[2] thinking that was turn 2. It is turn 3. Easy mistake, hard to see when you are reading your own fixture.
- **asserting exact reply text.** I did this at first and it broke as soon as anything touched how replies are stored. Assert on counts and on a substring you control, not on the full serialized shape.
- **assuming the tracker is flushed when the loop returns.** It is, currently, but i dunno if that is guaranteed anywhere. I read it after the loop returns and it works. If someone makes it async this is the assumption that breaks, so flagging it here.

If you hit something else, add it to this list rather than starting a new page.
