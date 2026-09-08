---
title: "Recovering an interrupted agent turn (turn ledger resume path)"
author: nils
created_at: 2025-06-17T09:30:00+00:00
---

## Why i'm writing this down

Two runs got killed mid-turn last week — one on the eval box when the harness timed out, one because somebody (me) ctrl-c'd a loop that was further along than i thought. Both came back with a ledger that wouldn't load, and both times we fixed it by hand, differently.

That's the part i want to avoid repeating. Fixing it by hand twice is fine, fixing it by hand every time is a policy we never agreed to. So this is the intended resume path, written before anyone codes around the failure case-by-case. Nothing here is new behaviour, it's mostly a description of what the recovery actually looks like when you do it correctly plus the two or three places where it's ambiguous.

Scope is the turn ledger only. Checkpoint/weights recovery is a separate thing and i'm not touching it here.

## What the ledger is, and why there are two files

For anyone who hasn't had to look inside one:

- `turn_ledger.json` — the materialized state. One object, the full turn list, rewritten in place at the end of every turn. This is what readers load.
- `turn_ledger.jsonl` — the append log. One line per turn, appended *before* the materialized file is rewritten.

The ordering there is deliberate and it's the whole reason recovery is possible at all. The jsonl is the durable record; the json is a convenience view that happens to be the one everything reads. A turn is considered committed once its line is in the jsonl, not once the json reflects it.

The two can legitimately disagree by exactly one turn during normal operation. Anything more than one is a signal that something else went wrong and you should stop and look rather than reconcile.

## Detecting and repairing an interrupted turn

On resume, load the jsonl first and count the lines, then attempt the json. The comparison of the two counts is what tells you where you are.

The common shape of the failure is exactly what it sounds like: one of those killed runs left `turn_ledger.json` half written, and `json.loads` dies on it — truncated mid-object, because the process went away partway through the rewrite. The jsonl sitting beside it was intact, so we appended the one line that was missing and three became four. That's the repair. It is not clever and it shouldn't be; the append log already had the turn, the materialized file just hadn't caught up.

So the resume path, stated plainly:

- if both files parse and the counts match — nothing to do, resume normally.
- if the json parses and is one turn behind the jsonl — rematerialize from the jsonl, resume.
- if the json fails to parse — same thing. Discard it entirely and rematerialize from the jsonl. Do not attempt to repair the truncated json in place, there's nothing in it that isn't in the log.
- if the jsonl itself has a torn final line — drop that line and treat the turn as uncommitted. It was mid-append when we died, which means the turn didn't finish.

The useful mental model is that the json is disposable. i think most of the confusion last week came from treating it as the source of truth and trying to hand-patch it, which is more work and gets you a file nobody can vouch for.

## When not to auto-repair

Rematerializing should be automatic for the cases above. It should not be automatic when:

- the jsonl and the json disagree by more than one turn. Something wrote to one and not the other outside the normal path, and silently picking a winner will lose work.
- the jsonl is missing entirely but the json is present and valid. That's recoverable in principle — you can reconstruct the log from the view — but it means the write ordering was violated somewhere, and i'd rather someone look at it than have the tool paper over it.
- the turn ids aren't contiguous. Same reasoning.

In all three, fail loudly with the counts and both paths in the message, and let a human decide. Makes sense to be conservative here; the cost of stopping is a few minutes, the cost of a bad merge is a run you can't trust.

## Still open

Two things i didn't settle and don't want to settle unilaterally.

First: does the rematerialize happen in the resume path itself, or in a separate `ledger repair` subcommand that resume shells out to? Doing it inline is fewer moving parts, but a standalone command is the thing you actually want at 2am when you're staring at a broken directory and don't want to start a run just to fix a file. i lean standalone with resume calling it, but let me think about whether that's over-engineering for what is ultimately a forty line function.

Second: do we keep the corrupt `turn_ledger.json` as `.json.broken` before overwriting, or just drop it? Keeping it costs nothing and has already been useful once for working out *when* the process died. Dropping it means one less stale file to confuse the next person. Mild preference for keeping it, but either is fine and i'd take whichever someone feels strongly about.

Neither of these blocks writing the repair logic — the behaviour is the same in both cases, it's packaging.
