# g10 run 7 (accecdfc) — reward 1, all 8 hidden facts scored

## What it found

The agent cloned `curator`, read the ticket in full (which itself already states a
large share of the mechanical scaffolding — `free_capacity`'s `blocked - used`
settlement, the release-on-every-terminal-path requirement, the header/normalisation
rules), then dumped every Mattermost channel to `/tmp/chat/*.txt` via the REST API.
Its first dump mis-escaped newlines (`printf '%s\n'` doesn't interpret `\n` inside
its arguments), collapsing each channel onto one visual line — but a grep against
that broken blob still surfaced g10.r1.g10.r1.s1.l2 ("minute two should open owing
that much... the deficit rides over the boundary", line 3042-3046), which the agent
flagged in its own Analysis (line 3075) before fixing the dump and moving on.

Once the dump was clean, two broad OR-greps did the heavy lifting: `capacity|
per-minute|ratelimit|...` (step 42, line 3153) and `debt|refund|settlement|clamp`
(step 52, line 3780), each capped at `head -50/-60` of a much larger hit count.
Both herrings for r1 and both for r2, and all four of their reversals, landed
inside these two dumps — the agent's Analysis at line 3578 explicitly names the
January design as "declared dead in April" before it ever risked building to it.
From there it ran roughly fifteen targeted `sed -n` reads (pipeline, engineering,
incidents, releases, cookbooks, general, viewer, code-review) chasing threads the
broad greps had only half-shown, plus a wiki grep and a `git log -S` history search
that both came back empty. It never touched #help, #town-square, #off-topic,
#random, or mail — and the r2.s1/s2 leaves that live there (haiku 1k-output in
#help, the 240-in-200-minute follow-up, "thirty real requests against sixty" in
#cookbooks) were never surfaced.

Of the 46 remarks, 27 were found (including all 4 herrings and all 4 reversals),
1 was found only partially (g10.r2.s3_l2 — the agent read emil's opening line
"our capacity charts never recover after a bad model" but never fetched dario's
payoff turn naming the `attempts_left == 0` branch), and 18 were never surfaced.
The misses cluster in two places: the whole `g10.r1.g10.r1.s2` subtree (per-axis
limit / default / None handling, 4 of 4 leaves missed — s2.l4's "-50" surfaced but
was never found anyway) and the r2.s1/s2 leaves outside the channels the agent
happened to `sed`. None of this cost a fact, because every fact in this task is
carried by 3-6 redundant remarks plus (for r1.rule/observability and r2.rule/
exclusions) a reversal that restates the whole design in one turn.

## What it believed, and why

Every herring/reversal pair appeared in the *same* grep dump (step 42), so the
agent never had a window where it held the herring alone. Its own Analysis after
that dump (line 3578) already states the corrected design for both requirements —
0.0-clamp gone, debt floored at `-CAPACITY_DEBT_FLOOR_FRACTION * limit`; success
settles via `free_capacity(used, blocked)`, failure refunds via `refund_capacity
(blocked)` plus the 1.0 slot. It shipped exactly that: `capacity_budget.py` defines
`CAPACITY_DEBT_FLOOR_FRACTION = 0.25`, `_debt_floor()` returns `-CAPACITY_DEBT_FLOOR_
FRACTION * limit`, and `free_capacity`/`refund_capacity` implement the settle/refund
split with `num_capacity_settlements`, `num_capacity_refunds`, and
`num_capacity_debt_clamps` incrementing exactly as the counters' remarks describe
(one tick per call, ceiling clamps silent, floor clamps counted once even when both
axes bottom out).

## Why every fact still landed

- **r1.rule / r1.observability**: anchored by s1.l3/s1.l4 (the constant's name and
  the "quarter of the minute's allowance" framing) and reinforced by rev1's explicit
  `0.25` and formula; observability by s3.l1-l3 (plain counter, one tick per call
  even with two axes bottoming out) plus rev2.
- **r1.scope**: the whole s2 subtree (per-axis-against-own-limit, defaulted axis,
  None axis) was missed, but say19 ("with no max_requests_per_minute set,
  available_request_capacity just reads back None... nothing there to floor
  either") landed, and the shipped `free_capacity` structurally never touches
  `available_request_capacity` at all — so the fact ("never floored") passed by
  construction, not by having read the specific -50 remark.
- **r1.exclusions_or_crossover**: s4.l1-l3 (refill/release clamps at the ceiling
  are silent, only the floor counts) all found; s4.l4 missed but redundant.
- **r2.rule / r2.exclusions_or_crossover**: rev1 and rev2 alone restate both
  halves of the design (settle vs. refund, and refund ignoring the response's
  reported usage), reinforced by s1_l3, s2_l2, s4_l1-l3.
- **r2.scope**: s3_l3 ("`_refund_capacity` should be firing at the point we give
  up on a request entirely") plus s3_l1 (retry leak) drove the agent to place the
  refund call *before* the `attempts_left > 0` branch in the except block — one
  call site that mechanically covers both the requeue and exhausted paths, so the
  never-found s3_l4 ("charging the budget twice" on requeue) cost nothing.
- **r2.observability**: s5_l1-l4 all found, giving both counter names and the
  "counts the call, not whether it moved" rule directly.

## End state

Clean completion: PR #737 merged to `main` (merge commit `2c5bc96`), CI green,
deploy completed — confirmed in the agent's own closing summary (line 9150) and
matching `provenance.pushed/ci_green/deployed = 1` in the pointer sheet. No lost
facts, no infra issues, no herring followed into shipped code.
