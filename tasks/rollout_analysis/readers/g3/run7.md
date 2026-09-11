# g3 run 7 (d13866db) — reward 1, all 9 facts pass

## What this run found

This run solved the ticket end to end (PR #737 → merge `d914d47` → CI green → deployed
release `20260911153848-d914d47`) and scored 1 on all nine declared facts. It got there
through a brute-force **bulk-dump-then-grep** strategy rather than targeted searching:
it dumped all 12 Mattermost channels in full (~10k posts, `dumpchat.py` → `/tmp/chat/*.txt`),
all IMAP mail to numbered files, and ~120 BookStack wiki pages with their comments
(`dumpwiki.py` → `/tmp/wiki/*.txt`, of which only 114/120 actually succeeded), then ran
roughly twenty iterative keyword-grep passes over the dumps (`throttle_waivers_left`,
`DEFAULT_THROTTLE_WAIVERS`, `throttle_cooldown_until`, `CONTRACT`, `contract:exhausted`,
`remaining_cooldown_seconds`, `seconds_to_pause_on_rate_limit`, etc.), consolidating
findings into a `spec.txt` before writing any code (line 2971). This surfaced 44 of the
49 planted remarks, including all 4 herrings and all 4 reversals, and it correctly sided
with every reversal over its herring (waiver-pool THROTTLE cost, and `max()` cooldown
horizon) rather than the earlier, parked decision.

## What it missed and why

Five remarks (all four with `found: "no"` groups below) never surfaced, and all five
misses trace to identifiable process gaps rather than misreading:

- **`g3.r1.l5` and `g3.r2.s1a`** (the two wiki *comments*) — the agent explicitly knew
  BookStack search doesn't index comments (it says so in the ticket) and separately
  grepped every dumped page's `=== COMMENTS ===` section for exactly the right terms
  (`retry|429|throttle|waiver|backoff|attempts`, line 4945) — a search that would have
  caught both clues' text. But `dumpwiki.py` only captured 114 of 120 pages, and neither
  carrier page (id 64 "Weekly Notes — Week of Mar 24"; id ~87/207 "Weekly sync notes:
  week of Jun 9") appears anywhere else in the transcript, so both were apparently among
  the 6 pages that silently failed to dump.
- **`g3.r1.l12`** (mail, "smoke run timings ... before we cut 0.1.26") — its subject line
  *did* appear in a bulk mail-subject grep (line 2052–2059), but the agent explicitly
  triaged it away: "The two key threads: 108-111 (revoked key) and 113,115,117,118 (429
  handling)" (line 2065) — the four bodies (112/114/116/119) were never opened.
- **`g3.r2.s2a`** (#cookbooks, "tiny backof ... pulled our wait back down under a
  second") — never surfaced despite the same channel and nearly the same date window
  being read for `h2`/`rev2` a few lines away; this exchange carries none of the literal
  identifiers (`throttle_cooldown_until`, `max()`, `DEFAULT_THROTTLE_WAIVERS`) the
  agent's keyword passes were anchored on.
- **`g3.r1.l1`** (#code-review, 2025-06-03 — **the thread this rerun specifically checks
  for**, since v9 rewrote konrad's 14:12 line) — this is the notable finding: it never
  surfaced *at all*. The whole #code-review channel (3439 lines) was dumped and grepped
  repeatedly, but no keyword pass ever included `finish_reason` or `length`, and grepping
  the transcript for either the pre-rewrite wording ("stops being retryable, fail it out
  on the first") or the v9 wording ("does come good on a retry now and then...") returns
  zero hits anywhere.

## What it shipped for `finish_reason == "length"` (the notable question)

Even having missed `g3.r1.l1` entirely, the shipped code gets this case right for the
rewritten world. `ValueError("finish_reason was length")` (line 549 of the base
processor) classifies as `CONTRACT` via the exception-type table; `_ATTEMPT_COSTS[CONTRACT]
= 2` (retry_policy.py, line 5235); and `decide()` only refuses a retry when
`attempts_left - cost < 0` (line 5379–5382). So a length failure is **charged 2 attempts
and retried** when the budget allows it — matching the v9 rewrite ("dont stop retrying
it, it just shouldnt get as many goes as a timeout"), not the old "fail it out on the
first." The agent reached this independently, from `g3.r1.l2` (2025-06-26, #pipeline:
"two attempts off for a malformed-output failure ... one is too generous") together
with `l16`/`l17`/`say23-r1` on the deduct-then-check ordering — not from `l1` at all.

## What it believed, and why

All four herrings were read and all four reversals were read, and in every case the
agent's own consolidated record cites the reversed/current rule, never the herring:
`DEFAULT_THROTTLE_WAIVERS = 6` / waiver-pool THROTTLE cost (superseding "THROTTLE costs
0 forever, no ceiling") and the `max()` cooldown horizon (superseding "plain
assignment/last-write-wins"). Both show up correctly in the shipped `RetryPolicy.decide`
and `record_verdict` (lines 5330–5429).

## Why no fact was lost

`reward` = 1 and every one of the 9 declared facts scored 1, so there is nothing in
`lost_facts`. This held despite 5/49 remarks (~10%) never being seen, because
`spread_problems()` guarantees at least 2 independent sources per requirement, and the
agent's exhaustive channel-by-channel dump-and-grep of chat was thorough enough that
every fact had at least one surviving carrier: `g3.r1.rule`/`scope` from `rev2`/`l2`/`l7`/
`l11`, `g3.r1.exclusions_or_crossover` from `l13`/`l14`/`l15`, `g3.r1.failure_behavior`
from `l16`/`l17`/`l18`/`l19`/`say23`/`say24`, `g3.r1.observability` from `rev2`/`l17`/
`l13`/`l15`, `g3.r2.rule` from `s1b`/`rev1`/`rev2`/`say19`/`s1c`, `g3.r2.scope` from
`s3a`/`s3b`/`s3c`/`say20`/`say21`/`say22`/`s2d`, `g3.r2.exclusions_or_crossover` from
`say23`/`s4c`/`s4a`/`s4b`/`s4d`, and `g3.r2.observability` from `s2c`/`s1c`/`s1d`.
