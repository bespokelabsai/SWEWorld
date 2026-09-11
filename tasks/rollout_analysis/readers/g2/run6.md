# g2 run 6 (f4648f93, eval 9f2db992) — reward 0.8889

## Summary

This run found and correctly reasoned about 39 of the 46 planted remarks (all 4 herrings, 3 of 4
reversals, 31 of 38 clues), read all 3 wiki comments and all 5 mail threads end-to-end, and shipped
a correct, complete implementation of every fact except one: `g2.r1.failure_behavior`. It pushed to
`main` (`d93123b`), CI is green including deploy, and 80/81 local tests pass (the one failure is a
pre-existing environment gap, identical on unmodified `main`). Reward 0.8889 = 8/9 facts.

## What it found and how

**Wiki (3/3 remarks, perfect).** The agent identified the three capping-related pages
(`Capping code executor output`, `Capping Executor Error Text in Responses Files and Logs`,
`Capping executor stdout and stderr in code-execution`) by walking the book's page list rather than
relying on `/api/search` (which the ticket itself warns does not index comments), then fetched each
one whole via `/api/pages/{id}` and read its comments in full. This is exactly the right technique
and it paid off — `l-log-nikolai`, `l-cross-1`, and `l-rule-4` were all recovered cleanly (lines 1092,
1486, 1537).

**Mail (5/5 remarks, perfect).** Every relevant IMAP thread — the seam-dermot 812043 thread, the
scope-3 exit-code-message thread, the rule-2 "shorten it like a stream" thread, the seam-dario
"cap should mean the kept bytes" thread, and the obs-2 fixture-review thread — was read start to
finish (lines 1948–2229). This is where the agent settled the single most consequential fact of the
run: that the marker sits *outside* the budget (`l-seam-dario`, line 2193), correctly overriding the
January chat herring that said the opposite.

**Chat (31/38 clues + 4/4 herrings + 3/4 reversals).** The agent dumped all 12 Mattermost channels to
files early (8,903 lines total) but never read any of them end to end — it grepped a fixed keyword
list (`output cap`, `truncate_output`, `elided`, `max_output_bytes`, `truncated_streams`,
`output_capped`, `floor`, `MIN`, `marker`, `warn`, and a final broad `cap` sweep) and read only the
context around each hit. That method is thorough — it recovered nearly every clue, including subtle
ones like the strict-greater-than boundary (`say25`) and the head-3/4-tail-1/4 weighting split across
three separate posts — but it has a hole: any remark whose literal wording falls outside every term
in the list is invisible, no matter how large the dumped file sitting on disk already is.

## What it missed, and why

Seven remarks were never surfaced (verified by grepping the full transcript for each one's
distinctive phrasing — none appear anywhere, not even as incidental fragments):
`g2.r1.l-floor-konrad`, `g2.r1.say26`, `g2.r1.l-bytes-dario`, `g2.r1.l-bytes-nils`,
`g2.r1.l-log-gideon`, `g2.r2.l-obs-3`, and the reversal `g2.r1.rev1`. Six of these were redundant —
the facts they carried were independently recovered through other remarks or fell out naturally from
the implementation logic (e.g. the no-op case for `g2.r2.l-obs-3` is just the early-return branch of
`cap_stream`). `g2.r1.rev1` (the reversal of the "marker inside budget" herring) was never needed
either, because the agent used a general "later record supersedes earlier chat" heuristic — reasoning
explicitly, at line 3047, that the June mail thread supersedes the January pipeline chat — and landed
on the correct rule without ever reading the specific reversal post.

**The one that cost a fact: `g2.r1.l-floor-konrad`** (#cookbooks, 2025-03-17 09:41). Its exact text is
"don't make me regex the traceback for `max_bytes must be 0 or at least 16, got 8` — hang the
offending value on the exception as `.max_bytes`" — the only place in the entire corpus that the
`OutputCapError` object needs to expose the rejected budget as a readable attribute. The agent's
keyword vocabulary for this whole area was always the compound `max_output_bytes`, never the bare
`max_bytes` this post actually uses, and the 779-line `#cookbooks` dump it created at step ~39 was
never read linearly — only grepped. As a direct result, the agent's `OutputCapError` (line 6977) has
no custom `__init__` at all: `class OutputCapError(ValueError): """..."""`, raised as
`OutputCapError(f"max_output_bytes must be at least {MIN_MAX_OUTPUT_BYTES} bytes...")`. The message
text is right; the required `.max_bytes` attribute simply doesn't exist. The grader's
`test_failure_behavior__a_budget_below_the_floor_of_sixteen_is_refused_by_outputcaperror` fails with
`AttributeError: 'OutputCapError' object has no attribute 'max_bytes'`. This is a clean `not_found` —
the requirement was stated nowhere else, the agent never saw it, and its own final "Delivered" summary
(line 7485–7505) never mentions storing the offending value on the exception at all.

## Herrings

All four herrings were found and correctly dismissed; all three available reversals were found and
correctly believed (the fourth, `rev1`, was never found but wasn't needed — see above). Notably the
agent caught a genuinely confusing exchange on its own: `g2.r2.rev2`'s dialogue opens by saying
"truncated_streams sat on CodeExecutionResult... that's the bit that's gone now", which reads as
being about `truncated_streams`, before the reply clarifies the field actually being dropped is
`error_truncated`. The agent flagged this explicitly as "the trap" (line 3657–3659) and parsed it
correctly rather than taking the first sentence at face value.

## One other note

`g2.r1.l-bytes-emil`'s post is attributed to "konrad" in the transcript this rollout actually
served (message id `tn4r3pqtitbb9qosg6ae8ob4pc`, `#engineering` 2025-12-30, line 3679), not "emil" as
the answer key prints — a world/key drift in speaker attribution only; the content and the fact it
carries are unchanged.
