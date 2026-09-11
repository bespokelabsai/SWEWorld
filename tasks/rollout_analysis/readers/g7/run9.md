# g7 run 9 (eval 8deffce4, rollout bfd713dc) — reward 0.875

## What this run found

The run completed cleanly end to end: pushed, CI green, deployed, and the open feature (durable
seed turn, log-derived resume) built correctly. Of the eight graded hidden-requirement facts, seven
scored 1. The agent recovered the full `g7.r2` design — sentinel is a case-sensitive, suffix-only,
whitespace-tolerant match that returns `False` on a non-string reply, and the sentinel-carrying
message is a real, logged, counted turn — almost entirely from two exchanges: the Mar-18 reversal
of the case-insensitive-substring herring (`g7.r2.rev1`, "is_completed is
response.rstrip().endswith(COMPLETION_SENTINEL), nothing else") and the Jun-4 reversal of the
placement-free herring (`g7.r2.rev2`, "exact casing yes... False. no exception"). Both were quoted
into the shipped `Agent.is_completed` almost verbatim. `g7.r1`'s scope, failure_behavior and
observability facts were rebuilt with equal precision — the eight sidecar keys, the 186/189-byte
serialization, the two-field (`responses`/`last_author`) comparison, the `TurnLedgerDesyncError`
message format copied character-for-character out of mail `g7.r1.l12` — all reproduced exactly and
confirmed passing by the grader's probes.

## What it missed, and why

**`g7.r1.rule` scored 0** on its very first assertion: `sym("TURN_LEDGER_FILENAME") == "turn_ledger.json"`
failed with `probe error: Failed: no module of bespokelabs.curator.agent exports
'TURN_LEDGER_FILENAME'`. The shipped module names the constant `SIDECAR_FILENAME` instead
(transcript line 4415), a plausible name the agent invented by analogy with the ticket's own
`RESPONSES_FILENAME` — but wrong. This is a clean `not_found`, not an implementation slip: the
literal identifier `TURN_LEDGER_FILENAME` appears in exactly **one** of the 51 planted remarks in
the whole answer key — `g7.r1.l2`, a wiki page *comment* on
`docs/meetings/weekly-sync-notes-week-of-jun-2-release-ci.md` ("The name lives in
TURN_LEDGER_FILENAME and the value is turn_ledger.json"). Every other remark that mentions the
sidecar filename uses only the bare string `"turn_ledger.json"`, never the Python identifier, and
the ticket itself never names the constant at all — the whole checkpoint feature is a hidden
requirement.

That page is the clearest near-miss of the run. It surfaced **twice** in the agent's own BookStack
searches ("Weekly sync notes: week of Jun 2 (release + CI)", transcript lines 1958–1972 and
2004–2006, under queries for "end marker" and others) but the agent never called
`/api/pages/{85 or 211}` to fetch it — it only ever opened pages 139, 143, 144, 147, 150 and 152.
Since BookStack does not index comments, nothing short of that fetch would have surfaced `l2`. The
same unopened page also carries `g7.r2.g7r2-l04` (indexed page body, scope) and
`g7.r2.g7r2-l10` (comment, failure_behavior) — both facts still scored 1 because other remarks
supplied the same information, but `l2` was the sole carrier of the one literal the grader checks
first.

Thirteen other remarks were also never surfaced, all for the same structural reason: **discovery
was keyword-search-only**, never a linear read. Chat search used six fixed grep patterns (`marker`;
`last_author|turn_ledger.json|read_sidecar|eight`; a `TurnEntry|build_ledger|...` set; a
`ledger|sidecar|seed\b|next_speaker|cached` set; two date-scoped greps) plus one live Mattermost
full-text search for `ledger`. Every channel that held a missed remark (`#pipeline`, `#cookbooks`,
`#viewer`, `#releases`, `#engineering`, `#code-review`) was fully dumped to disk — the misses
(`l1`, `say25`, `say23`, `fix26`, `say18`, `g7r2-l01`, `g7r2-l09`) are pure vocabulary gaps: none of
"jsonl"/"position" (l1), "interleave_faults" (say25), "completion_reason" (say23), "full stop"
(fix26), "four rows" (say18), "budget" (g7r2-l01), or "639"/"AttributeError" (g7r2-l09) appear in
any of the six patterns. Mail fared the same way: one search for `ledger` (12 hits, 4 threads) plus
a follow-up batch of single-word searches, three of which (`sentinel`, `next_speaker`,
`adopt_ledger`) returned **zero hits**. The three missed mail threads (`l9`, `g7r2-l08`, `g7r2-l05`)
are all squarely on-topic — a deleted-sidecar resume test, an `AttributeError` on a dict reply, and
suffix-vs-substring marker matching — but none uses the word "ledger" or "sidecar" in subject or
body, and no broader query ("stop", "marker", "resume", "checkpoint") was ever tried against mail.

## What it believed

All four herrings were correctly avoided; none reached the shipped code. Two
(`g7.r1.g7-h1-checkpoint-authoritative`, the "checkpoint truncates the log" design, and
`g7.r2.h2-sentinel-placement-free`, the "case-insensitive scan anywhere" design) were seen directly
via search snippets, immediately followed by their reversals in the same dump. One
(`g7.r2.h1-sentinel-substring-ci`) was only ever seen as restated inside its own reversal's
dialogue, never in its original Jan-22 wording. One (`g7.r1.g7-h2-truncate-is-the-pattern`) was
never seen at all, but its reversal (`rev2`, "the stamp is the version key... only a version-2
mismatch aborts") alone gave the complete corrected rule. In every case the agent registered the
reversal as the settled design and implemented it; no herring behavior appears in the shipped code.

## Notable

Two wiki comments the agent *did* fetch (`l14` on page 150, `l11` on page 144) were initially
misjudged in its own Analysis text as belonging to "a different, neighbouring artifact" and
registered `noted` rather than `requirement` — yet the content was used correctly in the final code
regardless (both facts scored 1), so the misjudgment was harmless. The one page that mattered
(`Weekly sync notes: week of Jun 2`) was never even opened to be misjudged.
