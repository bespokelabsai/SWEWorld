# g7 run 6 (abbd1b41) — eval 8deffce4 — reward 0.875

## What this run found

The agent ran a genuinely thorough archaeology pass: broad Mattermost keyword sweeps
(`sidecar`, `interleave_faults`, `sentinel`, `next_speaker`, `adopted`, `verified`,
`TURN_LEDGER_VERSION`, `write_sidecar`, `END_OF_CONVERSATION`, `sidecar_state`,
`read_sidecar`, `TurnLedgerDesyncError`) layered with targeted per-channel date-window
dumps once a hit's timestamp was known, IMAP mail searches and fetches, and BookStack
page fetches (with comments) for six of the eight wiki pages that carry planted
comments. It correctly reconstructed the full `turn_ledger.json` sidecar contract
(`TURN_LEDGER_VERSION=2`, the eight-key `sidecar_state()`, `write_sidecar`/
`read_sidecar`/`verify_sidecar`, `TurnLedgerDesyncError` with its five attributes and
exact message wording, the 186/189-byte serialisation) and the full `is_completed`
contract (`COMPLETION_SENTINEL`, `response.rstrip().endswith(...)`, case-sensitive,
suffix-only, whitespace-tolerant, non-str returns `False`). It correctly rejected all
four herrings — two of them (`g7.r1.g7-h1-checkpoint-authoritative`,
`g7.r1.g7-h2-truncate-is-the-pattern`) were never even read directly; the agent
absorbed the correct rule purely from their reversals, which restate the retracted
decision before overturning it, and its shipped docstring text ("raises
`TurnLedgerDesyncError` rather than quietly picking a winner") is close to a direct
quote of `g7.r1.rev1`.

## What it missed and why

Of 51 remarks, 22 never surfaced in the transcript at all. Most of that redundancy
was survivable — every fact except one had multiple independent carriers, so losing
any single clue rarely cost anything. Two structural gaps explain almost all of it:

1. **Mail searches were keyword-only and never exhaustive.** Seven IMAP `TEXT`
   queries (`ledger`, `sentinel`, `seed`, `next_speaker`, `interleave`, `conversation`,
   `adopt_ledger`) were run, with no full-mailbox listing. `g7.r1.l9` and
   `g7.r2.g7r2-l08` — sent the same minute, Apr 9 08:12 — never surfaced because
   neither body literally contains any of the seven searched words (they say
   "checkpoint"/"metadata json" and "AttributeError"/"stop check" instead).
2. **One wiki page was never opened**, despite appearing twice in the agent's own
   BookStack search results. `docs/meetings/weekly-sync-notes-week-of-jun-2-
   release-ci.md` (ids 85/211, "Weekly sync notes: week of Jun 2 (release + CI)")
   showed up under query `agent` (transcript line ~1250) and again under `multi-turn`
   (line ~1607), and both times the agent fetched only titles that looked more
   directly ledger-related (139, 143, 144, 150). Its later brute-force
   `/api/pages?count=500` sweep (line 3754) filtered the result to `128<=id<=170`,
   which also excludes 85/211. This is the one page holding `g7.r1.l2`,
   `g7.r2.g7r2-l04` and `g7.r2.g7r2-l10` — and, critically, `g7.r1.l2` is the **sole**
   carrier anywhere in the corpus of the literal constant name `TURN_LEDGER_FILENAME`.

There is also a genuine, if temporary, misread: after fetching wiki pages
139/143/144/150 — which between them state the exact `turn_ledger.json` schema and
byte counts — the agent's own Analysis (line 1596) concludes they describe "a
neighbouring `turn_ledger.json` artifact for run accounting, not our module" and
moves on to search elsewhere. It never explicitly reverses that judgement; it simply
re-derives the same facts independently from chat and mail later, so the dismissal
cost nothing measurable here, but it is worth flagging as a fragile pattern.

## The one lost fact: `g7.r1.rule`

`test_rule__a_versioned_checkpoint_rewritten_after_every_appended_response` fails on
its very first assertion — `sym("TURN_LEDGER_FILENAME") == "turn_ledger.json"` — with
a probe error: *"no module of bespokelabs.curator.agent exports
'TURN_LEDGER_FILENAME'"*. Everything the rest of that test would have checked
(`TURN_LEDGER_VERSION`, `sidecar_state()`'s eight keys, `write_sidecar`/
`read_sidecar`/`verify_sidecar`, the rewrite-after-every-append behaviour) is
implemented correctly in the shipped module — it is graded nowhere else because the
fact never gets past line one. The agent named its module constant
`SIDECAR_FILENAME` (transcript line 4612) instead of `TURN_LEDGER_FILENAME`, because
it never read `g7.r1.l2`, the one wiki comment that spells the name out ("The name
lives in `TURN_LEDGER_FILENAME` and the value is `turn_ledger.json`"). This is a
straightforward `not_found` — a real corpus remark, uniquely load-bearing, sitting on
a page the agent's own search surfaced and then declined to open.

## Believed vs. shipped

Both `r1` and `r2` herrings were correctly abandoned in the shipped code: no log
truncation exists anywhere in `verify_sidecar`, and `is_completed` is an exact
case-sensitive suffix match, never a case-insensitive scan. `g7.r2.failure_behavior`
is the one interesting edge case — it scored 1 despite none of its three carrying
remarks (`g7r2-l08`, `g7r2-l09`, `g7r2-l10`) ever surfacing; the agent's
`isinstance(response, str)` guard was added as ordinary defensive coding once
`is_completed`'s signature widened to `t.Any`, not because it had read about a
json-mode `AttributeError` incident. It got the requirement right by good instinct
rather than by evidence.
