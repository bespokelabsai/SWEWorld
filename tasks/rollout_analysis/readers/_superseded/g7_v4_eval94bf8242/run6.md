# g7 run 6 (7da788a3) — reward 0.625

## What this run found

This run's search was competent and disciplined for a 151-step rollout. It did not
lean on BookStack's free-text search alone — it fetched wiki pages whole through
`/api/pages/{id}` (body + comments together), which is exactly what the world's own
hint says to do since comments aren't indexed. That single habit is why it caught
eight separate wiki-comment clues (l2, l5, l14, g7r2-l07, g7r2-l10, g7r2-l13,
g7r2-l14, g7r2-l04) that a search-only agent would have missed entirely. For mail it
used IMAP `SEARCH`/`FETCH` directly and dumped whole threads to local files rather
than reading snippets, which is why long five-message threads (l12, l16, l3, l7) were
captured completely, in order, with every reply. For Mattermost it combined the
search API (terms like `sentinel`, `COMPLETION_SENTINEL`, `turn_ledger`) with
targeted channel-window dumps around the dates search hits pointed at.

Of 51 planted remarks, 33 were solidly found and correctly read (transcript lines
verified: e.g. l12 at 3002-3138, l2 at 2558-2592, g7r2-l14 at 2055-2098, fix27/fix30
at 4017-4126). All four herring/reversal pairs resolved correctly — the shipped code
matches every reversal and never a herring, even where two of the herrings
(`g7-h2-truncate-is-the-pattern`, `h2-sentinel-placement-free`) were only ever seen
secondhand, quoted inside their own reversal's opening line, never as an
independently-read original exchange. The agent also showed real judgment on wiki
page 144 ("recovering an interrupted agent turn"): its body describes a plausible but
non-canonical two-file repair scheme (a separate `turn_ledger.jsonl` append log, a
`.json.broken` backup). The agent read it in full and explicitly flagged it
"possibly a decoy" (line 2038) rather than implementing any of it — correct, since
none of that scaffolding appears in the grader.

## What it missed, and why

Fourteen remarks were never surfaced by any search in this run (confirmed by
re-grepping the transcript for each remark's distinctive phrases: zero hits for all
fourteen). The pattern is telling: several are mail threads sent the *same morning*
as threads that were read. `g7.r1.l9` ("resume when the metadata json isn't on
disk", konrad, 2025-04-09 08:12) and `g7.r2.g7r2-l08` ("stop condition in the turn
loop", dermot, 2025-04-09 08:12) are sibling threads from the identical timestamp —
only the second was opened. That suggests the mail search terms used that session
didn't enumerate every thread even when a neighboring one was found and read. The
single most consequential miss is `g7.r1.l8` (#pipeline, 2025-03-24 18:30): "first
write carries created, verified is only a load where both matched" — the one remark
that states the created/verified distinction the grader actually tests, and it was
never found.

Wiki page 144's real planted comment (`g7.r1.l11`, by nils, carrying
`failure_behavior`) was also never surfaced — the agent read the page's *body* in
full but the comment underneath it, which carries the actual graded content, never
got printed or quoted anywhere in the transcript. Correctly dismissing the body's
decoy content meant nothing was implemented from it, but it also meant the real
comment went unused; this had no scoring consequence since `failure_behavior=0` for
a different, unrelated reason (below).

## What it believed, and why

Every herring in this task was correctly rejected in favor of its reversal. The
clearest case: `g7.r1.g7-h1-checkpoint-authoritative` (dermot, "turn_ledger.json is
the source of truth ... truncate it back") was superseded by `g7.r1.rev1` (gideon,
"we dropped truncating the log back ... disagreeing checkpoints raise
TurnLedgerDesyncError"), both read in full, and the shipped `verify_sidecar` raises
on a version-2 mismatch rather than truncating anything — textbook correct. Same
story for the sentinel-matching herrings: the shipped `Agent.is_completed` is
`response.rstrip().endswith(COMPLETION_SENTINEL)`, case-sensitive and suffix-only,
matching both reversals and neither herring.

## Why each lost fact was lost

**`g7.r1.scope` (0)** — `test_scope` asserts that a brand-new run's very first write,
before any sidecar could possibly be checked, reports `status == "created"`. The
shipped code instead returns `"verified"`. The ticket itself specifies
`build_ledger(..., status: str = "verified")` as the default signature (transcript
line 85) — that default is fine everywhere except one call site. Inside
`MultiTurnAgenticProcessor.run()`, right after the seed line is appended, the code
calls `ledger = self._build_ledger(records)` with no `status=` override, so it
silently takes the "verified" default even though nothing was checked against
anything. The only place the agent *did* wire up `status="created"` was inside
`load_ledger()`'s internal call to `build_ledger`, immediately followed by
`verify_sidecar` overwriting it to `"adopted"` or `"verified"` — so in the agent's
mental model, "created" was purely a transient internal value on the load path, never
a status that a fresh, never-checked write should persist and report externally.
This is exactly the gap `g7.r1.l8` would have closed, and it was never found.

**`g7.r1.failure_behavior` (0) and `g7.r1.observability` (0)** — both fail on the
identical line: `TurnLedgerDesyncError` has no `.recorded_responses` /
`.recorded_last_author` attributes, even though the constructor receives both values
and uses them in the message string. This was not a random omission — it is exactly
what the agent decided after reading `g7.r1.l12` (mail thread "which state files does
the resume consistency check actually cover") in full, across five messages. The
thread's final reply, as actually served in this v4 world (transcript lines
3123-3138), settles the question explicitly: *"yes, the log side only. That was
deliberate ... with .log_responses and .log_last_author on the exception carrying the
log side. That is what is in the tree now and I am not touching the wording again."*
This directly contradicts an earlier mail (`g7.r1.l16`) that describes the exception
in prose as surfacing "recorded_responses 3 and recorded_last_author 'advisor'" — the
agent found and noted both (Analysis, line 3400), and correctly deferred to the
later, explicitly-"settled" thread over the earlier informal mention. **Per the
coordinator**, this is a known, expected mismatch: the answer key's current text for
this remark was edited locally on 2026-09-10 to read "no, both sides ...
`.recorded_responses` and `.recorded_last_author` are what the file claims" and that
edit was never pushed to the v4 corpus this rollout actually ran against. Judged
against what the agent actually read, it implemented the remark faithfully; the fact
loss here is a corpus/answer-key version mismatch, not a reading or implementation
error.

## Facts that passed, and on what

`g7.r1.rule` rode on `l2`/`l4`/`l3`/`l14` (filename, version, eight-key
`sidecar_state()`, rewrite-after-every-append, exact serialisation) — all read and
wired in verbatim. `g7.r2.rule` and `g7.r2.scope` rode almost entirely on `g7.r2.rev1`
(the sentinel-matching reversal) plus `g7r2-l07`'s whitespace-tolerance nuance.
`g7.r2.failure_behavior` passed on a generalization from `g7r2-l10` ("a run should not
fall over because an agent answered with something that is not text") rather than
from the more pointed AttributeError-on-dict remarks (`g7r2-l08`, `g7r2-l09`), which
were both missed — the general principle was enough to get `is_completed` to return
`False` on any non-`str` input. `g7.r2.observability` rode on `g7r2-l13`, `g7r2-l14`
and `g7r2-l11`, all found and read in full via whole-page comment fetches.
