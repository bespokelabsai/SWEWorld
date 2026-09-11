# g7 run 9 (ac588a0c) — reward 0.875

## What this run found

This is a strong, disciplined run. It read every source of company memory it was
told exists — Gitea issues, the BookStack wiki, the full IMAP mailbox, and the
entire Mattermost history — and it did so at unusual depth: it downloaded all
135 mails and all ~10,169 chat posts to local JSON files and then ran dozens of
targeted greps against them (transcript lines 2039-2987), rather than relying on
single searches. It cross-checked its reconstructed sidecar schema against the
reported 186/189-byte counts by literally running `json.dumps(sort_keys=True,
indent=2)` and comparing lengths (lines 4040-4056) before writing a line of
implementation code. That rigor is why `r1.scope`, `r1.failure_behavior`,
`r1.observability`, and all four `r2` facts scored 1: the exact schema
(`TURN_LEDGER_VERSION=2`, the eight `sidecar_state()` keys, the three
`verify_sidecar` arms, the exact `TurnLedgerDesyncError` message wording, the
sentinel `<<END_OF_CONVERSATION>>` and its case-sensitive suffix match, the
non-string-returns-`False` failure mode, the off-by-one dataset row count) were
all recovered correctly and shipped correctly (final module dump, lines
4370-4620; processor rewrite, lines 4769-5195).

All four herrings were seen only *inside the same grep dump as their reversals*
(lines 2506-2880) — the run never had a live window where it actually believed a
herring; by the time it read the Jan/Feb "checkpoint authoritative" or
"substring, case-insensitive" chat threads, the March/April/June reversals were
already sitting in the same file. Its own Analysis text at every stage states
the *reversed* rule ("no truncation... TurnLedgerDesyncError raised before the
first request", line 3633; "case sensitive... False for non-str", line 3354),
never the herring. All four herrings were correctly dismissed and none leaked
into the shipped code.

## What it missed, and why

The one lost fact, `g7.r1.rule` (test asserts `sym("TURN_LEDGER_FILENAME") ==
"turn_ledger.json"`), traces to a single missing literal identifier. The name
`TURN_LEDGER_FILENAME` appears in exactly one remark in the whole corpus —
`g7.r1.l2`, a wiki *comment* by gideon on the page "Weekly sync notes: week of
Jun 2 (release + CI)" (BookStack page ids 85/211). This page is not obscure: the
agent's own `/api/search` calls surfaced it three separate times, always near
the top of the results — under query `turn+ledger` (lines 1469/1481), under
`agent` (lines 1470/1482), and again under `agent+loop` (lines 3110-3111). Each
time the agent built a shortlist of "highly relevant" pages and the weekly-sync
page was left off it: first explicitly ("Found highly relevant wiki pages: 143,
144, 150, 139, 152", line 1526), then implicitly via a second-pass title-keyword
filter over all 500 wiki pages (`['agent','turn','ledger','conversat','seed',
'multi']`, lines 4068-4074) that a title like "Weekly sync notes" simply does
not match. The agent then concluded "I've read all agent/ledger wiki pages"
(line 4080) — a false belief born from a filter, not a search failure. Never
having seen the identifier, it invented a perfectly reasonable name of its own,
`SIDECAR_FILENAME` (line 4383), which the grader's `sym()` helper — which
searches every module of `bespokelabs.curator.agent` for the *exact* name —
correctly fails to find.

Everything else about `g7.r1` that this same never-opened page also carried
(`g7.r2.g7r2-l04`, the page body's `scope` clue about mid-sentence sentinel
matches; `g7.r2.g7r2-l10`, a comment about non-text tolerance) had no effect on
the score, because those facts (`r2.scope`, `r2.failure_behavior`) were already
recovered from other, independently-found remarks (`g7.r2.rev1`/`rev2`, the
`g7r2-l07` wiki comment, the `g7r2-l08` mail thread).

A second, smaller near-miss involves a comment-dumper script crash: the first
fetch of page 150 ("turn_ledger.json — the per-turn ledger artifact") threw an
`AttributeError` before printing any comments (lines 1605-1610), so `g7.r1.l14`
(dario's comment about `sort_keys`/`indent 2`/byte-count stability) was never
actually read. The agent noted the gap ("Comments on 150 ... remain partially
unread", line 4080) and planned to recheck it, but the very next turn jumped
straight into implementation code and the retry never happened. This didn't
cost a fact — `observability` was independently recovered from `l13`, `l15`,
`l4`, `l16`, `fix27` and `say21` — but it is a second instance of the same
pattern: a plan to re-check a source, stated and then dropped once
implementation momentum took over.

Two mail threads (`g7.r1.l7` "resume dies at load after mid-project upgrade",
`g7.r2.g7r2-l05` "stop sequences: what should count as a stop before I
normalise across backends") were downloaded along with all 135 mails but never
surfaced, because the keyword filter the agent grepped with
(`['ledger','seeder','next_speaker','turn_ledger','multi-turn','multiturn',
'seed_message','agent']`, lines 2046-2062) matches none of the words either
thread's body actually uses — verified directly against the answer-key text
(zero hits for any of those eight words in either thread). Both carry `scope`
facts that were recovered elsewhere, so no score was lost, but it is the same
shape of miss as the wiki filtering: broad collection, narrow keyword-based
selection.

One extra wrinkle, flagged by the coordinator: `g7.r1.l12`'s mail 135 (nikolai,
16:15) is quoted differently in the current answer key ("no, both sides") than
what this v4 world actually served, which reads "yes, the log side only ...
deliberately no matching pair for the ledger side" (transcript line ~2400).
That served text is actually *wrong* against the grader, which requires all
four attributes (`recorded_responses`/`recorded_last_author`/`log_responses`/
`log_last_author`). The agent's shipped `TurnLedgerDesyncError.__init__` (line
~4383) stores all four anyway — most likely because its own message f-string
needed both sides as local values, so storing them symmetrically was the
natural implementation choice, not a considered rejection of nikolai's claim.
Judged against what the rollout actually saw, this is a case where the world
told it something false and it built the right thing regardless; it had no
effect on the reward.

## Why each lost fact was lost — summary

Only one fact was lost, `g7.r1.rule`, and the mechanism is narrow and specific:
one required literal identifier (`TURN_LEDGER_FILENAME`) lived in a single wiki
*comment*, on a page that search surfaced three times but that a
title/topic-keyword pre-filter excluded every time, compounded by a script
crash that dropped a second page's comments and was never retried. Everything
else the requirement needed — the correct byte-for-byte schema, the correct
three-arm failure behaviour, the correct value, and the correct match
discipline for `r2` — was recovered and shipped correctly, which is why this is
a 0.875 rather than a materially lower score: one naming miss out of eight
facts, in a run whose search strategy was otherwise exhaustive and whose final
implementation matched the reconstructed design almost exactly.
