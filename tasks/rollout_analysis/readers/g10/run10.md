# g10 run 10 (eval 5b468409, rollout 8dec3046) — reward 0.5

## What this run found

The agent read the ticket, then dumped every source exhaustively rather than
trusting search: 755 Gitea issues/PRs, all 228 BookStack pages fetched *whole
with comments* (correctly reasoning that search doesn't index comments), all
107 IMAP messages, and the full Mattermost history (10287 lines). Gitea, the
wiki and mail all came back essentially empty for the capacity-budget design —
correctly identified as background only. The real material was in chat, and
the agent found it through a tight, evolving set of vocabulary greps:
`capacity_budget|CapacityExceedsLimit|...`, then `num_capacity|num_debt|clamp|
counter`, then `debt|allowance|quarter`, then `discard`.

That vocabulary is a near-perfect match for **r1** (capacity debt / floor /
clamp counter): the agent recovered both r1 herrings, both r1 reversals, and
13 of r1's 16 clue leaves, including the exact 0.25 constant, its name and
location (`CAPACITY_DEBT_FLOOR_FRACTION` in `capacity_budget.py`), the
one-tick-per-call clamp-counter semantics, and (registered, if not shipped —
see below) the release-side ceiling clamp. This produced a fully correct
`num_capacity_debt_clamps` implementation (r1.observability=1), a correct debt
floor (r1.rule=1), and correct None/defaulted-axis handling (r1.scope=1,
though this was largely available from the ticket text itself plus one found
remark, `say19`).

**r2** (settle vs. refund; requeued vs. exhausted; reported-usage exclusion)
uses an almost disjoint vocabulary — "slot", "per-request", "crawl", "gap",
"requeue", "finish_reason" — that the agent's grep list never targeted. It
recovered only 4 of r2's 26 remarks: the give-up call-site thread (`s3_l3`),
the "booking is the only number we own, refund clamped" thread (`s4_l3`), and
the two counter-naming threads (`s5_l2`, `s5_l4`). Both r2 herrings, both r2
reversals, and the entire `s1`/`s2` clusters (which together establish that a
*success* frees only the gap while the slot stays spent, and a *failure*
frees the whole reservation plus the request slot) were never surfaced —
confirmed by direct text search of the transcript, which also caught one
pointer-sheet false positive (`g10.r2.h1` is *not* actually in the transcript
anywhere; its cited line is an unrelated `grep -n 'def '` code listing).

## What it believed, and why

For r1, the agent correctly identified both herrings as superseded: it found
the January "clamp at 0.0, forgive the overshoot" decisions and then the
March/April threads reversing them ("the old 0.0 clamp ... is explicitly
reversed", line 3225), and implemented the reversal, not the herring.

For r2, having never found either herring *or* either reversal, the agent had
no textual basis to believe either side — so it invented a third design from
scratch. Its own reasoning (line 5281) reads: settle with real usage when the
failed response happened to report `token_usage`, and refund the whole
booking only when it didn't. This branches on the wrong condition (presence
of a number) instead of the right one (success vs. failure), and it is
*exactly* the wrong alternative the answer key calls out by name — the failing
test's comment reads "A settlement against the reported usage would have
given 9000 + (1000-1700) == 8300.0", which is precisely the value the shipped
code produces.

## Why each lost fact was lost

- **r1.exclusions_or_crossover** (implementation_slip): the agent *did* find
  and explicitly register the requirement — "the release/refill clamp at
  max_tokens_per_minute happens quietly and is not counted" (line 2764) — but
  the shipped `free_capacity` only ever applies the lower debt floor; no
  upper-bound clamp exists anywhere in the settle path. A release of 1800
  worth of tokens against a 1000-token limit is never capped. This is a clean
  case of understanding the remark correctly and not translating it into code.

- **r2.rule** and **r2.scope** (not_found): `refund_capacity` never touches
  `available_request_capacity` — only tokens. The single remark that states
  the fix ("the estimate plus the 1.0 slot back", `g10.r2.rev1`) was never
  surfaced. r2.scope compounds this with the settle/refund branching bug: the
  exhausted-path test supplies a response *with* reported usage, so the
  agent's code takes the settle branch instead of ever reaching a refund at
  all.

- **r2.exclusions_or_crossover** (not_found): the three remarks that would
  have blocked the settle-on-reported-usage bug — `s4_l1`, `s4_l2`, and above
  all `g10.r2.rev2` (which carries the identical 800-vs-100 worked example the
  test uses) — were never surfaced. `s4_l3` *was* found and registered, but it
  only supports "refund is clamped at the ceiling," not "a failure's refund
  always ignores whatever the response reported."

## A telling gap in its own verification

The agent's 533-line self-written test suite is thorough for what it tested,
but it never exercises a release/settle that overshoots the ceiling, never
checks `refund_capacity`'s effect on `available_request_capacity`, and never
gives a failing response reported usage. It tested precisely the paths it got
right and never tested the three it got wrong — so its 84-tests-green local
verification carried no warning of any of the three r2 failures or the one r1
failure.

## Other notes

An early false-memory episode (lines ~1054-1210): the agent's first real turn
opens by summarizing the ticket as already "implemented, merged to main, CI
green," despite a genuinely fresh clone with no feature branch and no
`capacity_budget.py` on disk — an ungrounded hallucinated status. It
self-corrected within three turns by checking `origin/main`'s SHA, at some
wasted effort but no effect on the final score.
