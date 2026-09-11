# g7 run 7 (065160cb) — reward 0.875

## What this run found

The agent recovered both hidden requirements almost completely: 7 of 8 facts scored 1. It
worked in three sweeps — BookStack (paginated page listing, then `/api/pages/{id}` fetches
that deliberately include comments, since it correctly understood early on, line 4831, that
BookStack search does not index comments), Mattermost (dump every channel to
`/tmp/chat/<channel>.txt`, then single-keyword `grep` across all of them, then re-read
promising windows in full), and IMAP mail (a handful of individual `SEARCH` keyword queries,
never an unfiltered listing of the mailbox). This caught all four reversals, all four
herrings (correctly resolved — the agent never once implemented a herring's behaviour; see
below), the one indexed wiki-page-body clue, all eight wiki-comment clues, and the great
majority of chat and mail clues.

`g7.r2` (the completion sentinel) came out perfectly: `COMPLETION_SENTINEL =
"<<END_OF_CONVERSATION>>"`, `is_completed` as `response.rstrip().endswith(COMPLETION_SENTINEL)`
(case-sensitive, suffix-only, `False` on non-str), and the dataset/observability shape (four
log lines for three responses, `completion_reason == "agent_signal"`, the closing turn
unstripped in the dataset with role `PARTNER`) all landed cleanly, each traceable to a specific
remark or reversal (`g7.r2.rev1`, `g7.r2.rev2`, `g7.r2.g7r2-l02`, `g7.r2.g7r2-l07`,
`g7.r2.g7r2-l12`, `g7.r2.g7r2-l13`, `g7.r2.g7r2-l14`).

`g7.r1` (the durable turn-ledger sidecar) scored 1 on `rule`, `scope` and `failure_behavior` —
the eight-key `sidecar_state()`, the `TurnLedgerDesyncError` message format and its five
attributes, the "only responses+last_author are compared" rule, and the "adopted on missing
or old-version, raise only on a current-version mismatch" branching were all reconstructed
correctly and shipped. `observability` scored 0.

## What it missed, and why

Ten of the 43 clue-remarks and two of the four herrings were never surfaced in any tool
output: `g7.r2.g7r2-l03` (#engineering, "nobody subclassed... marker instead of answering no
forever"), `g7.r1.l1` ("walked the whole jsonl to work out whose turn it was"),
`g7.r2.g7r2-l01`/`g7r2-l06` (#cookbooks — the negotiation-demo budget overrun, and the
capitals-matter complaint), `g7.r2.g7r2-l09` (639/`response_format` edge case),
`g7.r1.say23` (completion_reason stays "open" mid-run), `g7.r1.fix26` (no trailing period on
`TurnLedgerError` messages), and two mail threads: `g7.r1.l9` ("resume when the metadata json
isn't on disk") and `g7.r2.g7r2-l08` ("stop condition in the turn loop — does it assume string
content?"). None of these was individually load-bearing — every fact they carry was also
reachable through a different remark — but `g7.r1.l9` is notable: it states almost the exact
scenario ("deleted the json by hand... rerun refused to start... Missing file is benign - we
adopt the log") that the run's one lost fact gets wrong, and it was never read because the
mail search used only keywords like `ledger`, `sentinel`, `next_speaker`, `adopt_ledger`,
`seed_message`, `turn_ledger`, `interleave` — none of which appear in that thread's subject or
body. The Mattermost keyword-grep strategy had the same blind spot: two remarks
(`g7.r1.l6`, `g7.r1.say25`) were caught only as a bare question in a one-line grep hit, with
the answer that actually carries the fact never appearing anywhere else in the transcript
(confirmed by exhaustive text search) — the agent apparently inferred the correct rule from
adjacent remarks rather than from these two directly.

One corpus wrinkle deserves a note, per the coordinator's flag: `g7.r1.l12` (mail, "which
state files does the resume consistency check actually cover") was served to this v4 world in
an older, locally-edited form than the current answer key describes. Nikolai's final reply, as
the agent actually read it at transcript line 4437, says the desync error carries "the log
side only... deliberately no matching pair for the ledger side" — i.e. only
`.log_responses`/`.log_last_author`, not a matching `recorded_*` pair. Taken alone this would
have produced a wrong `TurnLedgerDesyncError`. The agent didn't take it alone: minutes later
it read the separate `g7.r1.l16` thread ("resume against a stale checkpoint"), which names
`recorded_responses`/`recorded_last_author` explicitly (line 4495), and at line 4529 it folded
both attribute pairs into the exception design, arriving at the shape the real grader wants.
So the agent effectively overrode a misleading remark using a second, independent one — the
`failure_behavior` fact passing is not evidence the agent trusted `l12` as written.

## The lost fact: `g7.r1.observability`

The failing assertion is precise:

```
assert read_field(second.ledger, "status") == "adopted"
AssertionError: assert 'created' == 'adopted'
```

Setup: a working directory already has a 3-line log (one seed, two responses); the sidecar is
deleted by hand; `run()` is called again for one more turn. `verify_sidecar` correctly reports
`status="adopted"` (missing sidecar, log wins) — but by the time the run finishes, the ledger's
status has flipped to `"created"`.

The root cause is a single design decision the agent wrote out loud twice and never tested
against this exact sequence. At transcript lines 5149–5163, deciding how to reconcile the
ticket's stated `build_ledger` default (`status="verified"`) against chat evidence of a
`"created"` status, it read remark `g7.r1.fix30` — "clean work dir, ran it end to end - nothing
to load, so verify_sidecar never fired, and the ledger came back still carrying the status it
was built with" (line 2408–2410) — and generalised it: *"in the processor, ledgers derived
in-memory during a run [are] built with status='created'"* (line 5151), reaffirmed at line
7986: *"_build_ledger default status='created'. ✓"*. `fix30` describes only the brand-new,
log-less case. The agent's rule applies `status="created"` as the default for **every**
in-run ledger rebuild — including the rebuild that happens after the very next appended
response following a resume. So a resume that correctly starts life as `"adopted"` (via
`verify_sidecar`) gets that status silently overwritten by `"created"` the moment the loop
appends one more line, because the per-append rebuild helper doesn't inherit or thread through
the previous status — it defaults it.

This is best classified as a **found_misread**: the agent found and correctly quoted the
relevant remark (`fix30`), but read its scope too broadly, missing the narrower rule implied
by the cumulative record — `g7.r1.l9` ("adopt the log" on a missing sidecar, one more call),
`g7.r1.l6`/`fix27` ("adopted" persists, "nothing rewritten... stays exactly as it was" for
`"verified"`) — that a status set by loading must survive subsequent appends within the same
run, and only a load event (or the very first, log-less write) should set `"created"`/
`"adopted"`/`"verified"` from scratch. Notably, the agent's own 302-line unit test suite for
`turn_ledger.py` tests "delete sidecar on an empty dir" and "stale sidecar on a truncated log"
separately, but never the combination the harbor grader's end-to-end test exercises — deleting
the sidecar on an *existing, multi-line* log and then resuming — so nothing caught the bug
before submission.

## Herrings

All four herrings were correctly discarded, and their reversals correctly implemented. Two
(`g7.r1.g7-h2-truncate-is-the-pattern`, `g7.r2.h2-sentinel-placement-free`) were never read at
their own original dates — the agent only ever saw them quoted back, already refuted, inside
their reversal's dialogue (`g7.r1.rev2` line 2775, `g7.r2.rev2` line 3574) — but that was
enough: nothing in the shipped code truncates the jsonl on mismatch, and nothing in
`is_completed` scans case-insensitively or matches mid-text.

## Bottom line

Every lost point in this run traces to one place: a design decision made explicitly (and
flagged with its own "Hmm" — line 5149, 5153) that generalised a true but narrow remark into a
default that breaks a case the agent never wrote a test for. Search coverage was good but not
exhaustive — mail in particular relied on a short, sidecar-vocabulary keyword list that missed
two threads, one of which stated the exact failing scenario almost verbatim — but the facts
those misses would have threatened were all independently covered elsewhere, so `g7.r1.observability`
is the only fact this run actually lost.
