# g3 run 9 (445beca6, eval 035777f5) — reward 0.6667

## What this run found

The search strategy was grep-first: the agent dumped the full Mattermost export to
`/tmp/chat.txt.n` and swept it with wide retry-vocabulary regexes
(`retry_policy|RetryPolicy|classify_failure|FailureClass|failure class|thro...`), landing on 8+
remarks per sweep (transcript L1369-1400). Mail was read properly — both threads
(`g3.r1.l8`, `g3.r1.l12` / `g3.r2.s4d`) were fetched and read start-to-finish (12-22 lines hit
each), not skimmed. Wiki was fetched via a page-plus-comments script
(`python3 /tmp/pw.py <id>`), so both wiki-comment remarks (`g3.r1.l5`, `g3.r2.s1a`) were found
early (steps 23, 25) — BookStack's comment-indexing gap cost this run nothing. Where the agent
found an interesting offset it followed up with a targeted `sed -n 'X,Yp'` range read against the
same export, which is how it caught the full v9-rewritten `g3.r1.l1` exchange (see below).

Of 49 remarks, 42 were surfaced (some only as a single opening line via a grep hit rather than the
full exchange — notably `g3.r2.s1c`, transcript L2145). Seven were never surfaced at all:
`g3.r2.say23`, `g3.r2.s2a`, `g3.r2.s4c`, `g3.r1.l7`, `g3.r2.s2d`, `g3.r1.l13`, `g3.r1.l9` — all sit
in channel-days the regex sweeps didn't happen to dump in full. Four of those seven turned out not
to matter (their content was reconstructed from other remarks or from reading the live source
tree). One — `g3.r1.l13` — mattered a great deal.

**Task instruction check (v9 rewrite of `g3.r1.l1`):** the run did see the rewritten thread in
full. Step 67 (transcript L3180-3222) is a targeted `sed` range read that surfaces konrad's new
14:12 line verbatim: *"and length does come good on a retry now and then, so dont stop retrying
it, it just shouldnt get as many goes as a timeout"* (L3207). The shipped code gets this right:
`finish_reason was length` raises `ValueError`, `classify_failure`'s type-based signal maps it to
CONTRACT, CONTRACT costs 2 attempts but is still retried while budget allows — a *contract,
charged-2-and-retried* verdict, not a terminal one. `g3.r1.rule` scored 1.

## What it missed, and why

All four hidden requirements' herrings were correctly resolved: the agent saw both the herring and
its reversal for THROTTLE-costs-nothing (`g3.r1.h1/rev1`), the waiver-pool origin
(`g3.r1.h2/rev2`), and both cooldown-horizon herrings (`g3.r2.h1/h2` and their reversals), and
shipped the reversed design in every case (waiver pool of 6, `max()`-floor cooldown).

Three of nine facts scored 0, and they trace to two distinct defects:

**`g3.r1.exclusions_or_crossover` and `g3.r1.observability` (same root cause).** The shipped
`decide()` charges TERMINAL failures a cost of 0, so `attempts_left` passes through *untouched*
instead of being zeroed (grader: `[False, 5, 4, 2, 'terminal:abort'] != [False, 0, 4, 2,
'terminal:abort']`). The one remark that states this rule, `g3.r1.l13` ("`invalid api key` at
seven left gives terminal:abort, attempts to zero, passes untouched at six"), was never found. The
agent filled the gap by misreading two things it *did* find: it reused `g3.r2.say20`
("nothing else on the tracker moves") — which is about the tracker's *counters*, a different
requirement — as if it applied to the request's own `attempts_left`; and it glossed mail
`g3.r1.l8` at L2772 as "MSG 114 mentions auth failures shouldn't consume remaining attempts
(TERMINAL abort — consistent)" even though that mail never mentions TERMINAL or auth failures at
all — it is entirely about THROTTLE waivers. Both misreadings point the same way, toward "TERMINAL
touches nothing," which is exactly backwards. Everything else in the same requirement (the
waived-throttle-still-retries-at-zero exclusion, carried by `g3.r1.l14`/`g3.r1.l15`, and the
whole failure_behavior clamp/no-jitter-on-exhaustion logic) is correct and passes; the fault is
narrowly the TERMINAL branch.

**`g3.r2.rule`.** `remaining_cooldown_seconds` clamps at zero but never rounds to three decimals
(grader: `[8.000900000000001, ...] != [8.001, ...]`). The only remark carrying that instruction,
`g3.r2.s1c`, was seen only as its opening line ("...handed me back -3.2... is negative meant to
mean something there?", L2147) via a grep hit; the reply with "clamp at 0.0, round to three
decimals" and the `4.999999999998` example was never dumped. The agent's own design notes (L4609)
show the gap directly: `max(0.0, throttle_cooldown_until - now)` — clamp kept, `round(...,3)`
silently dropped. The monotonic-`max()` floor and the tracker-field placement, carried by eight
other remarks, are both correct and pass in the same test function; `g3.r2.observability` passed
separately only because its own test values (1002.0/1004.5/1005.0/1099.0 against a horizon of
1005.0) happen to be exact floats that don't expose the missing rounding.

## Passed facts, briefly

`g3.r1.rule`/`g3.r1.scope`/`g3.r1.failure_behavior` and `g3.r2.scope`/`g3.r2.exclusions_or_crossover`/
`g3.r2.observability` all trace to remarks the agent found and correctly synthesized — the
CONTRACT-costs-2 / THROTTLE-waiver-of-6 design, the per-request (not per-run, not per-config)
placement of the waiver counter, the deduct-then-check-then-clamp ordering with no jitter draw on
an exhausted verdict, the throttle-only clock/stamp gating, and the dead `seconds_to_pause_on_rate_limit`
knob left in `config.py` unread.

## End reason

Not applicable — the run completed cleanly: pushed, CI green, deployed, `suite_ok=1`.
