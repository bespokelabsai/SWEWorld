---
title: "Stop-Marker Matching: What Ends a Generation and What Does Not"
author: nils
created_at: 2025-05-13T09:30:00+00:00
---

## Why This Note Exists

**Date:** 2025-05-13  
**Status:** rule recorded below, provider notes still being filled in

On monday night's run the same prompt set was sent to two backends and came back with materially different transcripts. one backend stopped where we expected it to. the other kept generating well past the end marker, several hundred tokens of continuation in some cases, until it hit the max token ceiling.

Same prompts, same marker, same version of our loop. so the difference is not in what we asked for, it is in what we accepted as an ending. I went back through the raw responses rather than the parsed ones, since the parser had already thrown away exactly the thing that mattered, and this is the write-up of what turned up there. that's worth documenting somewhere permanent, because I do not think this is the last time we add a backend.

## What The Raw Responses Show

Comparing the unparsed payloads side by side:

- the marker itself is emitted by every backend we tested. nobody is dropping it or spelling it differently, which was my first guess and it was wrong.
- two of the providers tack a newline on after the marker, and that should not be what decides whether we stop. the trailing newline is a formatting habit of the backend, not a signal about the content, and our loop was treating the presence or absence of it as meaningful without anyone having decided that it was.
- one backend splits the marker across two streamed chunks. neither chunk contains the full marker, so any check that runs per-chunk sees nothing.
- whitespace *before* the marker also varies, one provider indents it, though this one we were already tolerating by accident.

so there were two separate things going on, the newline and the chunk boundary, and they happened to produce the same symptom.

## The Rule We Are Matching On

what we settled on, so it is written down in one place:

1. matching runs against the accumulated text, not against an individual streamed chunk. a marker split across a chunk boundary still counts as a match.
2. the accumulated text is right-stripped of whitespace before the comparison. trailing newlines, spaces and carriage returns are all discarded for the purposes of the check.
3. the comparison is on the marker string itself, exact, case sensitive. we are not doing a regex here and I would prefer we keep it that way, a regex invites people to encode provider quirks into the pattern and then nobody can read it six months later.
4. whatever whitespace was stripped for matching is preserved in the stored response. the strip is a matching concern only, we should not be silently editing what the model actually returned.

maybe there is an argument for normalising the marker case as well, emil raised it, but nothing we have seen so far needs it and I would rather not widen the rule on speculation.

## When You Add A Backend

Before a new provider goes into the rotation, run the marker fixture set against it and check the *raw* response, not the parsed one. specifically:

- does the marker come back intact, and spelled exactly as sent
- what, if anything, is appended after it
- does it survive streaming, or does it arrive split

if any of those three answers is surprising, note it in the provider table rather than fixing it locally in the loop. the loop should stay one rule; the per-provider oddities belong in documentation where the next person can find them.

## Still Open

- the provider table does not yet have a column for any of this. I will add one, though someone should sanity check the entries for the backends I did not personally test.
- the overnight run that overran still needs its cost accounted for, those continuations were not free and they were not useful either.
- let me think about whether the fixture set is actually broad enough. it covers a marker at the very end of a response, which is the common case, but I am not certain it covers a response where the marker appears mid-text and the model then keeps going anyway. that is a different failure and we may not currently detect it at all.
