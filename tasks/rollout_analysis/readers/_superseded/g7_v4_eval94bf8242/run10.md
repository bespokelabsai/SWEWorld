# g7 run 10 (b6c8f7ac) — reward 0.625

## What this run found

The agent's research phase was genuinely thorough by construction, just uneven across
surfaces. It read every relevant curator source file in full before touching the world
(transcript lines 298-1100), then worked outward: Gitea issues (a dead end — the
indexer returned nothing for any keyword, lines 1113-1256), BookStack wiki, Mattermost
chat, and Roundcube/IMAP mail, roughly in that order.

**Mail was essentially perfect.** A single IMAP keyword search for "ledger" (and a
couple of others) found all 8 relevant threads by message id, and the agent dumped and
read every one of them in full (lines 2276-2555, 4570-4730 region). No mail clue was
lost to a fetch that didn't happen.

**Chat coverage was good but grep-shaped.** The agent dumped all 12 Mattermost channels
in full to local files (~12,000 lines, lines 2788-2865) and then repeatedly grepped
those files for clusters of technical identifiers ("ledger", "sidecar",
"TURN_LEDGER_VERSION", "next_speaker", "marker", "sentinel", etc.), reading generous
context windows around each hit. This caught the large majority of the 34 planted chat
remarks — including both herring/reversal pairs for r1 and r2, read clearly and
correctly resolved in favor of the reversals (lines 3304, 3505-3592, 3654-3656). Nine
conversational chat remarks that carry no distinctive technical keyword (l1, say23,
say24, say25, g7r2-l01, g7r2-l09, say18, plus one herring) were never independently
surfaced, because the channels were keyword-grepped rather than read end-to-end. None
of these misses cost a scored fact — the plant gives each subconclusion 4-9 redundant
remarks, and the agent's other hits covered the same ground.

**Wiki was the real gap, and it is a single mechanism that explains almost every wiki
miss.** BookStack's `/api/search` found the four decoy-looking "turn ledger" pages
(139, 143, 144, 150) and the two real ones (147, 152) quickly. But the agent's first
comment-rendering script crashed with `AttributeError: 'str' object has no attribute
'get'` on page 150's actual comment JSON shape (line 1300), and for the next batch
(139/143/144) it silently printed only `"active"`/`"archived"` status labels instead of
comment text (lines 1438-1439, 1521-1523, 1596-1598) — the real fix (walking the nested
`comment`/`children` structure returned by `/api/pages/{id}`) didn't land until line
2116-2122, triggered by manually inspecting page 147's raw JSON. By that point the
agent had already written off pages 139/143/144/150 explicitly: *"Pages 139/143/144/150
are decoy 'turn ledger' pages about a different artifact"* (line 1605) — a conclusion
drawn entirely from those pages' elaborately different BODY text (a separate in-world
`turn_ledger.json` with unrelated fields: `turns_completed`, `turns_budgeted`,
`budget_exhausted`/`error`/`cancelled`), never from their comments, which is exactly
where BookStack hides content from search and exactly where the real, on-topic clues
(`l14`, `l5`, `l11`, `g7r2-l14`) lived. The fixed comment-walker was used on only 2 of
the 8 comment-bearing pages (147 and 152) — the two the agent happened to still
consider live. The four "decoy" pages were never revisited.

A second, compounding miss: page 211 (`docs/meetings/weekly-sync-notes-week-of-jun-2-
release-ci.md`) surfaced in three separate `/api/search` result dumps ("seed message",
"multi-turn agent", "seeder partner" — lines 2237, 2245, 2266) but `/api/pages/211` was
never called at all. That single missed fetch cost three remarks at once: the one
wiki-**page-body** clue in the whole plant (`g7r2-l04`, searchable and findable, simply
never opened) plus two more wiki comments on the same page (`l2`, `g7r2-l10`).

## What it believed, and why

Both herring/reversal pairs were resolved correctly and early. For r1 (checkpoint
truncates the log vs. log wins and a disagreement raises), the agent's design summary
at line 3304 already states the reversed, correct semantics — `verify_sidecar` returns
`created`/`adopted`/`verified` or raises `TurnLedgerDesyncError`, no truncation. For r2
(case-insensitive substring-anywhere match vs. case-sensitive suffix match), the agent
found the reversal directly via a "marker"/"sentinel" grep sweep (lines 3505-3592,
3654-3656) and its final code implements exactly `response.rstrip().endswith(
COMPLETION_SENTINEL)`. At no point does the transcript show the agent taking the
herring position seriously as a design choice.

## Why each lost fact was lost

**`g7.r1.rule` = 0** — `sym("TURN_LEDGER_FILENAME")` finds nothing, because the shipped
module defines `SIDECAR_FILENAME: str = "turn_ledger.json"` (line 5304), not
`TURN_LEDGER_FILENAME`. This traces to exactly one missed remark: `g7.r1.l2`, a wiki
**comment** on page 211, is the *only* remark in the entire plant (confirmed against
`task_generator/out/agent-turn-ledger/clues/plant.json`) that carries the literal
identifier `TURN_LEDGER_FILENAME`. Page 211 was never opened (see above) — a clean,
single-point-of-failure `not_found`.

**`g7.r1.failure_behavior` = 0 and `g7.r1.observability` = 0** — both fail on the same
assertion: `error.recorded_responses` raises `AttributeError`, because the shipped
`TurnLedgerDesyncError` only carries `.path`, `.log_responses` and `.log_last_author`
(confirmed twice in the agent's own final summary, lines 8058 and 8107, and directly
in the code at lines 5038-5039, where `recorded_responses`/`recorded_last_author` are
formatted into the *message string* but never assigned to `self`). This is **not a
search or reasoning failure**. The decisive remark is `g7.r1.l12` (mail, "which state
files does the resume consistency check actually cover"), and the agent read every
message in that thread in full (lines 2483-2555), ending on nikolai's 16:15 "settled
version" reply (lines 2539-2551): *"Dermot, on your question: yes, the log side only.
That was deliberate ... with .log_responses and .log_last_author on the exception
carrying the log side."* That is exactly what the v4 world serves — confirmed against
`plant.json`'s own canonical clue text for `g7.r1.l12`, which reads identically
("`.log_responses and .log_last_author sit on it too`", never mentioning
`recorded_responses`/`recorded_last_author` as attribute names, in either its `text`
or pre-repair `repaired_from` field). `hidden_requirements.md`'s published "Where
every remark is" quote for this same clue currently shows a different, edited
version of message #135 ("no, both sides ... `.recorded_responses` and
`.recorded_last_author`") that the actual v4 world does not contain — a known,
out-of-scope answer-key/corpus desync (per the task coordinator, a local doc edit that
was never pushed into the built world). The agent also read `g7.r1.l16` (mail
111/115/116, lines 2308-2364), whose text uses the words "recorded_responses 3" and
"recorded_last_author 'advisor'" narratively, describing values the error reports —
but `plant.json`'s verbatim/forbidden-terms design for `l16` treats this as prose in
service of the *zero-calls-before-first-request* rule (which the agent did implement,
`r1.scope=1`), not as an assertion of distinct attribute names, and it is dated three
months before `l12`'s later, explicit, dated "settled version" ruling on exactly this
question. The agent weighed the two exactly as a careful reader would — trusting the
later, explicit, on-point statement over an earlier informal mention — and implemented
precisely the world it was given. Judged against what it actually read (per the task
coordinator's instruction), this is a corpus/answer-key desync, not an agent defect.

**Everything else passed.** `g7.r1.scope` (load writes nothing, compare only
`responses`+`last_author`) was carried by `l6`, `l7`, `rev1`, `rev2`, `fix30`, all
found and correctly acted on. All four `g7.r2` facts passed 1/1 — `rule` and `scope`
from `g7r2-l03`, `g7r2-l02` and the two reversals; `failure_behavior` from mail
`g7r2-l08` (AttributeError on a dict, killed at turn two) plus `rev2`'s explicit
"False, no exception"; `observability` from `g7r2-l11` (the off-by-one dataset bug),
`g7r2-l12` (PARTNER role, unstripped marker text) and `g7r2-l13` — the one wiki comment
that *was* successfully recovered (page 152, after the script fix), confirming the
fix-then-two-pages pattern above rather than a blanket inability to read comments.

## Bottom line

Three of eight facts were lost, for two genuinely different reasons: one clean
single-point-of-failure search miss (page 211 never opened, costing the
`TURN_LEDGER_FILENAME` name), and one corpus/answer-key desync entirely outside the
agent's control (the `l12` mail as actually served in this v4 world never carries the
`recorded_responses`/`recorded_last_author` attribute names the grader checks for,
though the currently-published `hidden_requirements.md` prose for that same clue
does). The wiki-comment extraction bug and the resulting "decoy" dismissal of four
pages is the largest structural weakness in this run's search strategy, but by luck of
redundant coverage it cost only one fact directly (`r1.rule`, via page 211, which is
not even one of the four dismissed pages) rather than three or four.
