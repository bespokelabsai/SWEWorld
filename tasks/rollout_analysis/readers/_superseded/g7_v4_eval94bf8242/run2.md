# g7 run 2 (49610d9b) — reward 0.625

## Summary

The agent reconstructed g7.r2 (the sentinel/`is_completed` requirement) essentially
completely — all four facts scored 1 — and reconstructed most of g7.r1 (the
sidecar/`turn_ledger.json` requirement), scoring only `scope`. It lost `rule`,
`failure_behavior` and `observability` for r1, and both losses trace to two narrow,
concrete implementation gaps rather than a broad failure to find the corpus.

## What it found, and how

Chat (Mattermost) coverage was the strongest channel. The agent built a small API
client, ran targeted keyword searches (`ledger`, `sidecar`, `sentinel`,
`TURN_LEDGER_VERSION`, …), then — for the four densest channels (`#pipeline`,
`#code-review`, `#engineering`, `#cookbooks`) plus `#incidents` — dumped whole
channel histories to `/tmp/chan_*.txt` and grepped multi-term regexes
(`sidecar|TURN_LEDGER`, `sentinel|stop marker|is_completed|END_OF|marker`,
`interleave|next_speaker|num_cached|cached`) over them, then read wide `sed`
windows around hits to recover full exchanges (e.g. transcript lines 2715-2760 for
`g7.r1.rev1`, lines 3222-3330 for both r2 reversals). This is how it recovered
**both r1 herrings and both r1 reversals**, **both r2 herrings and both r2
reversals**, and roughly two-thirds of the plain clues carrying `rule`, `scope`
and `failure_behavior` for both requirements. `#releases` and `#viewer` were
essentially never dumped, which is why `g7.r2.say18`, `g7.r1.say22` and
`g7.r1.say23` were missed outright — though none of those losses cost a fact,
since the same information was redundantly available elsewhere.

Mail (IMAP) coverage was narrower but thorough once triggered: the agent searched
a fixed list of terms (`ledger`, `interleave`, `COMPLETION_SENTINEL`,
`adopt_ledger`, `turn_ledger`, `sidecar`, `desync`, `verify_sidecar`, `TurnLedger`,
…) and fully read every thread that matched (`g7.r1.l3`, `g7.r1.l7`, `g7.r1.l12`,
`g7.r1.l16`). But three mail threads (`g7.r1.l9`, `g7.r2.g7r2-l08`,
`g7.r2.g7r2-l05`, `g7.r2.g7r2-l09` is chat not mail) never matched any of those
terms and were never found, and one (`g7.r2.g7r2-l11`, "prototype run output
before we freeze it as the reference transcript") appeared **by subject line** in
a `ledger` search-result listing at transcript line 2153-2154 but its body was
never fetched — the agent fetched threads 111-123, 124-127 and 131-135 instead of
128-129.

Wiki (BookStack) coverage used the right *technique* — the agent's own ticket
briefing (transcript line 142-143) states that BookStack search does not index
comments and "a page worth reading is worth fetching whole," and the agent did
fetch several pages whole via `/api/pages/{id}` (143, 144, 150, 139, 152),
correctly picking up comment-only clues that a plain search would have missed
(`g7.r1.l14`, `g7.r1.l5`, `g7.r1.l11`, `g7.r2.g7r2-l07`, `g7.r2.g7r2-l13`,
`g7.r2.g7r2-l14`). But it did not apply that technique *exhaustively* to every
page that ever surfaced in a search hit: "Weekly sync notes: week of Jun 2
(release + CI)" (page ids 211/85) appeared in two of its own searches (query
`agent` at transcript line 2038-2039, query `multi-turn` at line 3527-3528) and
was never fetched. That single missed page carries three remarks —
`g7.r1.l2`, `g7.r2.g7r2-l04`, `g7.r2.g7r2-l10` — including the **only** remark in
the entire 51-remark corpus that spells the literal constant name
`TURN_LEDGER_FILENAME`.

## What it believed, and why

All four herrings were seen and correctly rejected in favour of their reversals.
For r1: the checkpoint-authoritative herring ("the ledger is the source of
truth... we truncate it back") was overturned by `rev1`
("TurnLedgerError, which is honestly just a RuntimeError. nothing clever under
it," line 2721) and `rev2` ("that ones dead... it's gone," line 3823) — the
agent's shipped `verify_sidecar` never truncates the log and raises
`TurnLedgerDesyncError` instead, matching the reversal exactly. For r2: the
case-insensitive-substring-anywhere herring was overturned by `rev1` ("is_completed
is `response.rstrip().endswith(COMPLETION_SENTINEL)`, nothing else," line 3181)
and `rev2` ("there is no scan anywhere. it only looks at the end," line 3315-3320)
— the shipped `Agent.is_completed` matches this exactly, including the
non-string-returns-`False` failure behaviour and the `rstrip()`
whitespace tolerance.

## Why each lost fact was lost

**`r1.rule` (0):** `test_rule__...` asserts `sym("TURN_LEDGER_FILENAME") ==
"turn_ledger.json"` as its very first line, and fails there — a grep of the
*entire* transcript for the literal string `TURN_LEDGER_FILENAME` returns zero
hits. Lacking any source for the name, the agent invented
`SIDECAR_FILENAME: str = "turn_ledger.json"` (transcript line 4371) by analogy
with the "sidecar" vocabulary it saw everywhere (`write_sidecar`, `read_sidecar`,
`verify_sidecar`, `sidecar_state`). This is a clean `not_found`: the one remark
that names the constant (`g7.r1.l2`, a wiki comment on the never-fetched "Weekly
sync notes" page) was never surfaced, even though that page's title appeared
twice in the agent's own search results.

**`r1.failure_behavior` (0) and `r1.observability` (0):** both fail on the same
line: `AttributeError: 'TurnLedgerDesyncError' object has no attribute
'recorded_responses'`. (The observability test actually clears its 186-byte and
189-byte checks first — the agent's serialization, grounded correctly in
`g7.r1.l14`'s "sort_keys, indent 2, trailing newline" and `g7.r1.l13`/`say21`'s
exact byte counts, is right — and only fails at the very end, when it triggers a
desync and checks the same missing attribute.) The agent found `g7.r1.l16` (mail,
read in full at transcript line 2311-2320), whose text literally contains the
words "recorded_responses 3 and recorded_last_author 'advisor'" as a description
of what the error reported. It also found `g7.r1.l12` (mail, read in full at
transcript line 2527-2618), in which nikolai explicitly and "conclusively"
states: "yes, the log side only. That was deliberate... .log_responses and
.log_last_author on the exception carrying the log side. That is what is in the
tree now and I am not touching the wording again." That later, more explicit,
settled-sounding remark is what the agent's own synthesis (line 4126) and shipped
code follow: `TurnLedgerDesyncError.__init__` (line 4412-4431) takes
`recorded_responses`/`recorded_last_author` as constructor arguments — proving the
agent *did* register that these values matter — builds the message string from
them, but never assigns `self.recorded_responses` / `self.recorded_last_author`,
and its own docstring reads "Store the sidecar path and the log side of the
comparison," echoing `g7.r1.l12`'s own phrasing almost word for word. This is a
clean case of one later, corpus-served remark overriding an earlier, plainer one
(`overridden_by_other_corpus_text`) — the agent followed what it read faithfully;
the grader still requires the two attributes the world's own "settled" remark
told it not to add.

## Passed facts, briefly

`r1.scope` passed off `g7.r1.l6`/`l7`/`rev1`/`l5`/`fix30` ("we leave the jsonl
alone... the counters rebuild for free"; "load_ledger is read the log rebuild in
memory verify_sidecar nothing written"). All four r2 facts passed almost entirely
off the two dense reversal exchanges (`rev1`, `rev2`), which each bundle three of
the four facts into a single thread the agent happened to read start to finish,
plus `g7.r2.g7r2-l12`/`l13`/`l14` for the exact observability fixture numbers
(budget 6 → four log lines, three responses, `completion_reason="agent_signal"`).

## Note on g7.r1.l12

`hidden_requirements.md`'s current prose quote for `g7.r1.l12` differs from what
this rollout actually saw — that is a local, unpushed edit made after this run,
and the v4 world served the "log side only" text quoted above. The agent is
judged here against the text it actually read, which it reproduced faithfully in
its shipped code's docstring.
