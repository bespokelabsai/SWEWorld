# g10 run5 (eval 5b468409, rollout 97d72c87) — reward 1

## Verdict

This run recovered both hidden requirements completely and correctly. All 8 graded facts
(`g10.r1.rule/scope/exclusions_or_crossover/observability`, `g10.r2.rule/scope/exclusions_or_crossover/observability`)
scored 1, `open_feature`/`suite_ok`/all three `provenance.*` facts are 1, and the run ended
cleanly: merged to `main`, CI green, and the running service confirmed on the deployed commit
(transcript line 9479, 9494–9498). The agent's own final file-write (visible in the raw rollout
JSON as the `newblock3.py` heredoc, message index 225, but only as a `wc -l` echo in the rendered
markdown transcript) is airtight evidence: `_debt_floor()` computes `-CAPACITY_DEBT_FLOOR_FRACTION
* limit` per axis, a single boolean `clamped` bumps `num_capacity_debt_clamps` exactly once per
call regardless of how many axes bottomed out, ceiling clamps (`min(settled, limit)`) never touch
that counter, `free_capacity()` and `refund_capacity()` are two distinct methods (the former never
touches the request slot, the latter always does, capped at the limit), and `refund_capacity()`
uses only `blocked` — never the response's reported usage. Every clause of the answer key's
`rule`/`scope`/`exclusions_or_crossover`/`observability` text for both `g10.r1` and `g10.r2` maps
onto a line of this shipped code.

## What it found and how

The agent worked breadth-first across every source before writing any code. It read the
pre-existing tracker/processor source in full (steps 1–45), then dumped BookStack's entire wiki —
179 pages including comments (line 2711–2861) — and correctly concluded the wiki was unrelated to
this ticket (line 5148); this matches the plant record exactly, since all 46 g10 remarks live in
chat and none in wiki or mail. It also fetched Gitea issue 207 with comments and background-scraped
all issues/PRs, and searched mail over IMAP, finding nothing g10-relevant in either. The decisive
move was bulk-dumping all 12 Mattermost channels to local files at once (line 3485–3499: pipeline
2036 messages, releases 694, viewer 319, etc.) and running one composite keyword grep
(capacity/refund/settle/debt/reserv/booking-family terms) across all of them, which returned very
uneven per-channel hit counts: pipeline 24, engineering 21, code-review 13, incidents 8, releases 9,
cookbooks 4, general 4, viewer 7, **help 0**. It then widened context window by window around each
hit, cross-checking every herring against its later reversal the moment it appeared ("that was the
review call last year... and its gone" — line 3910).

34 of 46 planted remarks were traced with a specific step/line and read in context; all 4 herrings
were correctly recognized as superseded *before* any code was written, and all 4 reversals were
read and followed. The design assembled from this reading (synthesized at transcript line 6211) is
essentially a word-for-word match to the answer key's `rule`/`scope`/`exclusions_or_crossover`/
`observability` text for both requirements.

## What it missed, and why it didn't matter

12 of 46 remarks (~26%) were never surfaced, confirmed absent from both the rendered transcript and
the raw rollout JSON by direct string search. The pattern is legible: channels with fewer initial
keyword hits (cookbooks, general, releases, viewer, and especially help) got only one or two narrow
context windows each, so remarks sitting in a different part of the same file — a different day, a
different thread — were never read. `#pipeline`, despite being the most heavily read channel
(2036 lines), still has gaps: `g10.r1.g10.r1.s2.l2` ("the row where the caller passed 0 is A"),
`g10.r1.g10.r1.s2.l3` ("settle threw doing arithmetic on a None"), `g10.r2.s2_l1` ("gemini 503'd on
everything"), and `g10.r1.g10.r1.s1.l2` (the single latest-dated remark in the whole plant,
2025-05-13, at the very tail of the dump) all fell in unread stretches. `#help` is the starkest
case: it returned exactly 0 hits on the one composite grep, and with only one remark ever planted
there (`g10.r2.s1_l1`, the haiku over-reservation profile) the agent never opened it by hand — that
remark was structurally unreachable by this search strategy regardless of how much time was spent.

None of these gaps cost a fact. The plant deliberately carries each fact on multiple independent
remarks across channels and dates (`clues.spread()`'s ≥2 sources / ≥3 weeks / ≥2 rooms design), and
every fact that lost a remark still had at least one other remark, plus the reversal exchanges (which
each restate the settled rule richly), landing in a window the agent did read. For example,
`g10.r1.scope` lost three of its five carrying remarks (`s2.l2`, `s2.l3`, `s2.l4`) but was still
recovered whole from `s2.l1`'s split-limit story and `say19`'s None-axis story, both of which the
agent read in full.

## Herrings

All four herrings (`g10.r1.clamp-at-zero-decision`, `g10.r1.clamp-at-zero-rationale`, `g10.r2.h1`,
`g10.r2.h2`) were seen, and all four reversals (`g10.r1.rev1`, `g10.r1.rev2`, `g10.r2.rev1`,
`g10.r2.rev2`) were seen and correctly identified as the current truth. In every case the agent's
own Analysis text names the herring as "the old call... its gone" the moment the reversal turns up,
rather than treating it as live even transiently. The shipped code follows every reversal and no
herring.
