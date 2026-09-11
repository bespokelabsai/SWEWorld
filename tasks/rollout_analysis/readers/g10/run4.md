# g10 run 4 — reward 1 (all 8 facts, all provenance checks)

## What this run found

The agent built the ticket's `capacity_budget.py` module exactly as specified, then went
looking for what the ticket left out. It cloned the repo, read every relevant source file
first, checked Gitea issues (correctly dismissed as upstream noise), fetched the BookStack
wiki whole including comments (correctly implementing the `comments['active'][i]['comment']`
nested structure BookStack's own search does not index), and searched mail over IMAP
(correctly concluded to be sparse — the answer key places all 46 g10 remarks in chat, none
in wiki or mail, so this triage was right).

The decisive move was two-stage chat mining: first an all-channel Mattermost keyword search
across capacity/rate-limit vocabulary that alone surfaced roughly half the remark corpus in
one shot (transcript line 2871-2913 — a dense list of dated, attributed hits spanning January
through May), then a full per-channel dump of every channel's chronological history to
`/tmp/chat/<name>.txt`, re-grepped five more times for narrower vocabulary (counter names,
`slot`, `reserve`, `settle`, literal identifiers like `CAPACITY_DEBT_FLOOR_FRACTION` and
`_refund_capacity`). That combination is why 33 of 46 remarks surface directly in the
transcript with an identifiable step and line, including all four herrings and all four
reversals.

## What it missed, and why it didn't cost anything

13 remarks never appear verbatim anywhere in the transcript — confirmed by grepping the
full transcript for each one's distinctive phrasing (e.g. "minute two should open owing",
"gemini 503'd", "haiku call", "row A", "counting the call, not whether it moved a number").
Their channels were dumped in full to disk, but none of the agent's later grep passes
happened to match their exact wording, so they never printed to the terminal buffer this
transcript captures. In every case, though, a sibling leaf of the same subconclusion or the
matching herring-reversal exchange (which restates the old design before killing it) carried
the same fact and *was* read in full — e.g. `g10.r2.s1_l3` and `g10.r2.s1_l4` never surface,
but `g10.r2.rev1` restates their exact content ("240 in a 200 minute", "slot stays spent")
while announcing the old plan dead. For `g10.r1.scope`, three of four source leaves
(split-limit config, defaulted-0-axis, None-axis) were never surfaced by remark text at all;
the agent instead correctly derived defaulted- and None-axis handling from the ticket's own
`__post_init__` normalisation paragraph, which already states this generically for bucket
seeding, and only needed the one surfaced leaf (`s2.l4`, "request capacity never floored")
to extend that rule to the new debt floor.

One pointer-sheet artifact worth flagging: it lists `g10.r2.h1` as first surfacing at
step 9 / line 1300, but that line is original repository code
(`used_tokens: _TokenUsage = ...`), not chat — a false positive from simple text matching.
The herring's actual content only enters the transcript embedded inside `g10.r2.rev1`'s own
restatement, which the agent read in full and correctly treated as already dead.

## What it believed, and why

All four herrings were seen, all four reversals were seen, and the agent believed the
reversal in every case — never the herring. Its own words: "the Jan-2025 'one `_free_capacity`
for both outcomes, slot back everywhere' plan was explicitly declared dead in April 2025"
(line 4580), and "The debt thread confirms my implementation exactly: 0.0 is no longer the
floor" (line 8668). The shipped code matches: `free_capacity` no longer clamps at zero (it
carries debt to `-CAPACITY_DEBT_FLOOR_FRACTION * limit`), and success/failure settle through
two different tracker methods (`free_capacity` vs `refund_capacity`) rather than one shared
`_free_capacity`.

## Why nothing was lost

`lost_facts` is empty — all 8 graded facts scored 1. The agent's final commit message and
end-of-run summary (lines 8120-8210, 8724-8730) independently restate all three hidden
decisions — the debt floor, the split settlement, the two release counters — with the exact
constant/counter names and behavioural nuances (per-call not per-axis clamp counting, a
refill to the ceiling is not a clamp, the failure refund ignores reported usage) matching the
answer key almost word for word. This reads as genuine understanding rather than identifier
pattern-matching: the reasoning traces (lines 3221, 3321, 3472, 3623, 4580, 8668) show the
agent explicitly reconciling the January "settled" herrings against the April reversals
before committing to the later design, and its worked examples (240-in-a-200-minute,
800-vs-100-token overshoot) match the answer key's own worked cases.

One thing the transcript cannot confirm either way: the literal `free_capacity`/
`refund_capacity` method bodies with their counter `+=` lines never appear in the visible
terminal buffer (diff and cat output scrolled past what "Current Terminal Screen" captures),
so `g10.r2.s5_l4`'s specific claim — a counter still increments even when the touched axis is
unlimited/`None` — could not be verified against the agent's own code from the transcript
text alone; it is inferred correct from the grader scoring `r2.observability` 1.
