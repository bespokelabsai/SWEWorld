# g7 run 8 (52b53639) — reward 0.875

## What this run found

This was a strong, disciplined run (7 of 8 hidden facts, 0.875). The agent used three
sources deliberately and in a sensible order: it opened the wiki FIRST (steps 14-21,
transcript lines ~1450-1900), fetching pages via `/api/pages/{id}` — which returns body
*and* comments together — having correctly internalized the ticket's hint that BookStack
search does not index comments. That gave it, before touching chat or mail at all, the
core sidecar facts: `TURN_LEDGER_VERSION`, `completion_reason` values, `load_ledger`/
`verify_sidecar` semantics, and the byte-exact `sort_keys=True, indent=2` serialization
(wiki comments on pages 139, 143, 144, 150, 152, 147). It then swept Mattermost with a
server-side full-text search over eight technical terms (`ledger, seed, next_speaker,
sentinel, interleave, sidecar, desync, turn`), and when that surfaced a rich vein it
dumped *every* channel in full (code-review 3243 lines, engineering 2501, pipeline 2009,
releases 665, cookbooks 774, viewer 312, incidents 243) and grepped the dumps for
rotating technical-keyword patterns. Mail was read over raw IMAP with two TEXT-search
term lists, pulling 43 full messages that were then read start to finish.

Crucially, the agent caught and correctly resolved all four herrings. Both r1 herrings
("checkpoint is authoritative, truncate the log on mismatch") and both r2 herrings
("lowercase, match-anywhere sentinel check") were seen, and so were all four reversals —
the agent's Analysis at transcript line 3857 explicitly states "No trimming" after
reading the reversal, and the final `is_completed` body (line 5518-5520) is close to a
verbatim transcription of `g7.r2.rev2`'s chat line. There is no herring-driven damage
anywhere in this run.

## What it missed, and why

Seven near-misses cost nothing (their facts were independently recovered from other
remarks): `g7.r1.l1`, `g7.r2.g7r2-l01`, `g7.r2.g7r2-l09`, `g7.r1.say23`, `g7.r1.fix26`,
`g7.r2.say18`. These share one root cause — **search strategy that is keyword-shaped,
not channel-shaped**. The agent dumped full channels but then read them almost
exclusively through grep patterns built from technical vocabulary already recovered
(`sidecar`, `ledger`, `SENTINEL`, `TURN_LEDGER_VERSION`, `trim`, `cached`, `adopt`).
Remarks phrased in plain English with no technical noun in them — "walked the whole
jsonl to work out whose turn it was," "burns through the whole budget," "our
TurnLedgerError messages don't end with a full stop," "dataset comes out at four rows
now" — never matched any pattern and were never seen, even though the raw text sat on
disk in `/tmp/ch_*.txt` the whole time. `#releases` (665 lines) is the extreme case: it
was dumped but never grepped or read at all.

Mail had a structural gap of its own: both IMAP `TEXT` search term lists (`ledger,
turn_ledger, next_speaker, seed, interleave, COMPLETION_SENTINEL, adopt_ledger,
multi-turn, "turn ledger"` and then `ledger, interleave, resume`) are r1-biased — neither
contains a marker/sentinel/stop-related word. The two r2 mail threads
(`g7.r2.g7r2-l05` "stop sequences," `g7.r2.g7r2-l08` "stop condition... AttributeError
on a dict") were therefore never fetched at all; `g7.r2.failure_behavior` still scored 1
because `g7.r2.rev2`'s chat line ("False. no exception.") independently carries the same
fact.

**The one lost fact — `g7.r1.rule` — has a single, clean cause.** The test's first
assertion is `sym("TURN_LEDGER_FILENAME") == "turn_ledger.json"`, where `sym()` searches
seven candidate modules for that exact name. The agent's shipped `turn_ledger.py`
(printf-written at transcript line 5055) defines `SIDECAR_FILENAME: str =
"turn_ledger.json"` — right module, right value, wrong name. The only remark in the
entire 51-remark corpus that spells out `TURN_LEDGER_FILENAME` verbatim is a BookStack
page *comment* on "Weekly sync notes: week of Jun 2 (release + CI)" (page id 85,
duplicated as 211): *"so basically the working dir gets TURN_LEDGER_FILENAME,
turn_ledger.json, holding what we derive off the log."* That page's body surfaced as a
top hit in at least five separate searches the agent itself ran (transcript lines
1758-1759, 1785-1786, 1798-1799, 3960-3961, 4130-4131) — it was right there, named
"Weekly sync notes: week of Jun 2 (release + CI)," appearing in almost every broad
query — but the agent never called `/api/pages/85` or `/api/pages/211`. It seems to have
been dismissed as one more generic "Weekly Notes" page among dozens of near-identically
named ones once the agent had settled on the deduplicated "engineering-vop" book
(pages 139-152) as its wiki source of truth. Since it's a comment, not a body, BookStack
search could never have surfaced it either way — only opening the page would have
worked, and that's the one page in the run's own top search results that never got
opened. Everything else about `rule` — `TURN_LEDGER_VERSION`, `read_sidecar`,
`write_sidecar`, `verify_sidecar`'s existence and behavior — was independently and
correctly recovered from other remarks (`l10`, `l8`-thread, `l4`, code-review 1929/1963),
so this is a pure naming miss, not a comprehension failure.

## A note on `g7.r1.l12`

Per the coordinator's flag: the answer key's current text of this mail thread differs
from what this run's world actually served. The v4 world's `nikolai` 16:15 reply reads
*"yes, the log side only. That was deliberate... .log_responses is the count and
.log_last_author is the name"* (transcript line 2458), whereas the current key has since
been edited (locally, unpushed) to *"no, both sides... .recorded_responses and
.recorded_last_author are what the file claims."* Judged against what the agent actually
saw: it read the older "log side only" text but still shipped a `TurnLedgerDesyncError`
carrying all four attributes (`.recorded_responses`, `.recorded_last_author`,
`.log_responses`, `.log_last_author`) exactly as the (both-versions-agreeing) grader
requires. It got there because the exception's own f-string message construction forces
both pairs to exist, and because `g7.r1.l16`'s mail independently uses
`recorded_responses`/`recorded_last_author` phrasing. No fact was affected by the stale
text; `g7.r1.failure_behavior` and `g7.r1.observability` both scored 1.

## Provenance

Clean: commit `0193f3f` merged to `main`, CI run 14 green on checkout/tests/deploy,
`curator.world.local` answered healthy post-deploy, 55 new tests plus a stable 101-pass
unit suite (transcript line 10250).
