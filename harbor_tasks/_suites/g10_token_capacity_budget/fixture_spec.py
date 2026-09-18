"""g10 — the INPUTS of one grading run, derived from the seed root chose.

Stdlib only, and imported by both sides: the worker gets it in the jail (it has
to build the scenarios), the judge gets it beside `judge.py` (it has to know what
was asked in order to work out what the answer should have been). One derivation,
so the two cannot drift.

WHY A SEED AT ALL. The worker/judge split stopped the worker rewriting the
verdict; it did not stop the worker inventing the values the judge reads. An
independent review of v11 measured exactly that: `observations.json` hand-written
from the judge's own literals scored 9/9, and scored 9/9 again against a tree
with `refund_capacity`, the failure-path refund and all three counters deleted —
reward 1.0 from an implementation of neither hidden requirement. The write path
is not hypothetical: `run_suites.py` puts the submission's `src/` on the worker's
PYTHONPATH, so a pushed `src/sitecustomize.py` runs at the worker's startup and
an `atexit` hook can overwrite the file before root harvests it.

Re-drawing the limits, the estimates, the reported usages, the clock steps and
the header values every run means the numbers the judge compares against are not
knowable in advance, and the only way to produce them is to run an
implementation that actually computes them.

WHAT MAY NOT LIVE HERE. Expected outputs, and anything an expected output can be
computed FROM. The debt-floor fraction is the sharp case: `0.25` is the hidden
requirement itself, so it appears in `judge.py` (which the worker cannot read)
and is checked against the submission's own source there — never here, where the
worker would read it and price every floor without implementing one.

WHAT DELIBERATELY STAYS FIXED. The ticket's own constants and formats: the four
`DEFAULT_MAX_*` numbers, the three origin strings, the header-name tuples, the
`RateLimitReading` field order and frozen-ness, the `parse_limit_value` rejection
cases, the enum members, and the counter semantics (one increment per call).
Those ARE the requirement, they are published in `instruction.md`, and re-drawing
them is not possible — a value that cannot be changed cannot be a secret. Only
the run's scenario NUMBERS move.

Every band below is chosen so that the branch each scenario exists to exercise is
the branch it takes whatever the seed: a settlement meant to hit the debt floor
overshoots by a margin, a refill meant not to reach the ceiling is given less
time than the consumption it has to make up, and a second reservation meant to be
refused asks for more than half the bucket. A draw that quietly moved a scenario
onto the other branch would grade a rule the fact does not name, and would look
like a flaky task rather than a wrong one.
"""
from __future__ import annotations

import random


def derive(seed: str) -> dict:
    """Every input this run uses, as a plain dict. Same seed, same dict."""
    rnd = random.Random(seed)

    # Token limits are drawn in multiples of 600 and request limits in multiples
    # of 5, with every elapsed time a multiple of 6 seconds or of a whole
    # minute. Both `limit * elapsed / 60` and `limit / 60` are then exact
    # integers in binary, so every order an implementation might write the
    # refill in gives the identical double and the suite keeps its "no
    # tolerances anywhere" property. Measured over 18,000 draws: with the
    # multiple of 500 this band used first, `limit / 60 * elapsed` disagreed
    # with `limit * elapsed / 60` by one ulp on 1.4% of them; with 600 it
    # disagrees on none. A limit of 8300 with a 7-second step would put the
    # expected value one ulp from the observed one and make the fact flaky.
    def tpm() -> int:
        return rnd.randrange(8_400, 20_401, 600)

    def rpm() -> int:
        return rnd.randrange(30, 121, 5)

    spec: dict = {"seed": seed}

    # ---------------------------------------------------------------- parsing
    # `parse_limit_value` decodes a header VALUE. The formats it accepts and
    # rejects are the ticket's; only the numbers move. The fractional digit is
    # always 5 so `float("N.5") * 1000` is exact: with a 3 there, `2.3k` is
    # 2299.9999999999995 before `math.floor` and the expected value depends on
    # the order an implementation multiplies in, which the ticket does not fix.
    spec["parse_plain_str"] = rnd.randrange(101, 999)
    spec["parse_k_units"] = rnd.randint(1, 9)
    spec["parse_m_units"] = rnd.randint(2, 9)
    spec["parse_trunc_int"] = rnd.randrange(10_000, 90_001, 500)
    spec["parse_spaced"] = rnd.randrange(20_000, 90_001, 1_000)
    spec["parse_int"] = rnd.randrange(1_000, 9_001)

    # ------------------------------------------------------- header scenarios
    # Each group gets its own draws from its own band, so a run captured whole
    # tells the next run nothing: there is no single number to re-use.
    spec["h_anthropic_req"] = rnd.randrange(1_000, 9_001, 100)
    spec["h_anthropic_in"] = rnd.randrange(100_000, 900_001, 10_000)
    spec["h_anthropic_out"] = rnd.randrange(20_000, 90_001, 5_000)
    spec["h_total_ci"] = rnd.randrange(30_000, 90_001, 1_000)
    spec["h_pair_req"] = rnd.randrange(200, 901, 50)
    spec["h_pair_total"] = rnd.randrange(60_000, 120_001, 5_000)
    spec["h_pair_in"] = rnd.randrange(30_000, 70_001, 5_000)
    spec["h_pair_out"] = rnd.randrange(10_000, 25_001, 1_000)
    spec["h_half_in"] = rnd.randrange(30_000, 70_001, 5_000)
    spec["h_half_total"] = rnd.randrange(80_000, 120_001, 5_000)
    # The "0 is not a limit" case: a k-suffixed total beside a zero request
    # header, so the zero is skipped and the suffix still decodes.
    spec["h_zero_k_units"] = rnd.randint(1, 9)
    # A malformed first name in the tuple, then a good second one: the value
    # under the malformed name must stay unparseable whatever the seed, so it is
    # a word rather than a number.
    spec["h_fallthrough_bad"] = "abc"
    spec["h_fallthrough_req"] = rnd.randrange(700, 1_500, 50)
    spec["h_fallthrough_total"] = rnd.randrange(20_000, 60_001, 5_000)
    # Tuple order decides between two present-and-parseable names, so the two
    # must differ or the observation could not tell which one won.
    spec["h_priority_x"] = rnd.randrange(300, 700, 50)
    spec["h_priority_anthropic"] = rnd.randrange(800, 1_500, 50)
    spec["h_apply_req"] = rnd.randrange(300, 900, 50)
    spec["h_apply_in"] = rnd.randrange(30_000, 70_001, 5_000)
    spec["h_apply_out"] = rnd.randrange(10_000, 25_001, 1_000)

    # ------------------------------------------ combined seed/refill dynamics
    # The consumption is at least a quarter of the bucket and the elapsed time
    # buys back at most a fifth of it, so the refill lands strictly below the
    # ceiling and the fact measures the refill rate rather than the cap.
    spec["seed_rpm"] = rpm()
    seed_tpm = tpm()
    spec["seed_tpm"] = seed_tpm
    spec["seed_est_in"] = rnd.randrange(seed_tpm // 4, seed_tpm // 2, 100)
    spec["seed_est_out"] = rnd.randrange(100, max(200, seed_tpm // 10), 100)
    # Far from any wall clock: the fact asserts that the injected clock is the
    # one that seeded `last_update_time`, and it can only do that if the value
    # could not have come from `time.time()`.
    spec["seed_t0"] = float(rnd.randrange(500, 2_001, 50))
    spec["seed_dt"] = 6.0 * rnd.randint(1, 2)
    # Backwards: `elapsed` is clamped at 0, so the buckets hold still and only
    # `last_update_time` moves.
    spec["seed_back_dt"] = -float(rnd.randrange(2, 21, 2))

    # ---------------------------------------- seperate seed/refill dynamics
    # Under `seperate` the refill increment is floored per axis, so the step is
    # kept to a second or two: `floor(limit * elapsed / 60)` then stays well
    # under the consumption above, and neither axis reaches its ceiling.
    spec["sep_in_limit"] = rnd.randrange(8_000, 14_001, 500)
    spec["sep_out_limit"] = rnd.randrange(4_000, 7_001, 500)
    spec["sep_est_in"] = rnd.randrange(600, 1_201, 50)
    spec["sep_est_out"] = rnd.randrange(300, 601, 50)
    spec["sep_t0"] = float(rnd.randrange(300, 900, 50))
    spec["sep_dt"] = float(rnd.randint(1, 2))

    # ------------------------------------------------- shape coercion inputs
    # A `seperate` tracker told only an output limit defaults the input axis;
    # a scalar limit spreads to both axes; a `_TokenUsage` limit under
    # `combined` collapses to its total.
    spec["partial_out_limit"] = rnd.randrange(10_000, 30_001, 500)
    spec["coerce_scalar"] = rnd.randrange(50_000, 120_001, 1_000)
    spec["coerce_sep_in"] = rnd.randrange(20_000, 40_001, 1_000)
    spec["coerce_sep_out"] = rnd.randrange(10_000, 30_001, 1_000)

    # -------------------------------------------- an estimate that never fits
    # `requested` must exceed the limit on the axis the ticket names first, and
    # the exception's own message carries both numbers, so the overshoot is
    # drawn rather than fixed.
    raise_tpm = tpm()
    spec["raise_tpm"] = raise_tpm
    spec["raise_over"] = rnd.randrange(500, 3_001, 100)
    spec["raise_est_in"] = rnd.randrange(raise_tpm // 2, raise_tpm, 500)
    spec["raise_t0"] = float(rnd.randrange(600, 2_001, 50))
    # The clock is moved before the call: the raise must leave
    # `last_update_time` on the seeded reading, which only shows if the clock
    # has since moved on.
    spec["raise_bump"] = float(rnd.randrange(20, 80, 2))
    spec["raise_in_limit"] = rnd.randrange(800, 1_501, 100)
    spec["raise_out_limit"] = rnd.randrange(400, 701, 100)
    spec["raise_in_over"] = rnd.randrange(100, 601, 100)
    spec["raise_out_over"] = rnd.randrange(100, 401, 100)

    # ------------------------------------------------- a bucket already empty
    # Consumption takes most of the bucket and the next ask is for more than
    # what is left, so `has_capacity` is False without the estimate exceeding
    # the limit — the distinction the ticket draws between False and a raise.
    # Tenths are taken with `// 10` rather than `* 0.1`: 0.1 and 0.7 are both
    # slightly under their decimal value in binary, so `int(1500 * 0.7)` is
    # 1049, and a scenario whose consumption is one token off its band is a
    # scenario whose branch is no longer guaranteed.
    empty_tpm = rnd.randrange(1_000, 3_001, 100)
    spec["empty_tpm"] = empty_tpm
    spec["empty_est_in"] = empty_tpm * 7 // 10
    spec["empty_est_out"] = empty_tpm // 10
    spec["empty_ask_in"] = empty_tpm * 15 // 100
    spec["empty_ask_out"] = empty_tpm * 15 // 100

    # --------------------------------------------------------- reserve, twice
    # One reservation fits, the second cannot: the estimate is more than half
    # the bucket and no more than the whole of it, so the first is admitted and
    # the second refused whatever the seed. `_check_fits_limit` would RAISE on
    # an estimate over the limit, which is a different fact.
    res_tpm = rnd.randrange(1_000, 3_001, 100)
    res_total = rnd.randrange(int(res_tpm * 0.6), int(res_tpm * 0.95), 50)
    spec["res_tpm"] = res_tpm
    spec["res_rpm"] = rpm()
    spec["res_est_out"] = rnd.randrange(50, max(100, res_total // 4), 50)
    spec["res_est_in"] = res_total - spec["res_est_out"]
    spec["res_unlimited_rpm"] = rpm()

    # ------------------------------------------------- the precedence ladder
    # Six values, all distinct, so "the manual one won" cannot be satisfied by
    # returning the header one.
    ladder = rnd.sample(range(11, 99), 6)
    spec["prec_manual_req"], spec["prec_header_req"] = ladder[0], ladder[1]
    spec["prec_manual_tok"], spec["prec_header_tok"] = ladder[2], ladder[3]
    spec["prec_manual_conc"], spec["prec_header_conc"] = ladder[4], ladder[5]

    # ------------------------------------------- rebinding a seperate capacity
    spec["rebind_in_limit"] = rnd.randrange(8_000, 14_001, 500)
    spec["rebind_out_limit"] = rnd.randrange(4_000, 7_001, 500)
    spec["rebind_est_in"] = rnd.randrange(400, 1_001, 50)
    spec["rebind_est_out"] = rnd.randrange(100, 401, 50)
    spec["rebind_used_in"] = rnd.randrange(50, 201, 25)
    spec["rebind_used_out"] = rnd.randrange(25, 101, 25)

    # ------------------------------------------ one release per attempt (open)
    spec["rel_rpm"] = rpm()
    spec["rel_tpm"] = tpm()
    spec["rel_est_in"] = rnd.randrange(400, 1_001, 100)
    spec["rel_est_out"] = rnd.randrange(100, 501, 100)
    spec["rel_resp_out"] = rnd.randrange(100, 401, 100)

    # ============================== r1: the debt floor ======================
    # A settlement whose reported usage exceeds 1.25x the limit is what drives
    # an axis through the floor: below that multiple the result lands above the
    # floor and the fact would measure nothing. Every "must clamp" draw below
    # takes its usage from a band that starts at 1.4x.
    r1_tpm = tpm()
    spec["r1_tpm"] = r1_tpm
    spec["r1_rpm"] = rpm()
    spec["r1_est_in"] = rnd.randrange(r1_tpm // 5, r1_tpm // 2, 100)
    spec["r1_est_out"] = rnd.randrange(100, max(200, r1_tpm // 10), 100)
    spec["r1_used_total"] = rnd.randrange(int(r1_tpm * 1.4), int(r1_tpm * 2.2), 100)
    spec["r1_used_out"] = rnd.randrange(100, 501, 100)

    # the defaulted tracker: constructed with 0, so the limit is the ticket's
    # DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED and the floor follows it.
    spec["r1_def_rpm"] = rpm()
    spec["r1_def_est_in"] = rnd.randrange(50_000, 95_001, 5_000)
    spec["r1_def_est_out"] = rnd.randrange(1_000, 5_001, 1_000)
    spec["r1_def_used_total"] = rnd.randrange(140_000, 260_001, 10_000)

    # the seperate tracker: each axis floors against its own limit
    spec["r1_sep_rpm"] = rpm()
    r1_sep_in = rnd.randrange(800, 2_001, 100)
    r1_sep_out = rnd.randrange(400, 901, 100)
    spec["r1_sep_in_limit"] = r1_sep_in
    spec["r1_sep_out_limit"] = r1_sep_out
    spec["r1_sep_est_in"] = rnd.randrange(r1_sep_in // 4, r1_sep_in // 2, 50)
    spec["r1_sep_est_out"] = rnd.randrange(50, max(100, r1_sep_out // 4), 50)
    spec["r1_sep_used_in"] = int(r1_sep_in * 2) + rnd.randrange(0, 501, 100)
    spec["r1_sep_used_out"] = int(r1_sep_out * 2) + rnd.randrange(0, 301, 100)

    # the three non-clamps: a refill to the ceiling, a release to the ceiling,
    # and a settlement that stays above the floor.
    excl_tpm = tpm()
    spec["excl_tpm"] = excl_tpm
    spec["excl_rpm"] = rpm()
    spec["excl_est_in"] = rnd.randrange(excl_tpm // 5, excl_tpm // 2, 100)
    spec["excl_est_out"] = rnd.randrange(100, max(200, excl_tpm // 10), 100)
    spec["excl_t0"] = float(rnd.randrange(500, 2_001, 50))
    # A whole minute or more: the refill then more than covers what was
    # consumed and the cap binds, which is the case the fact says is NOT a
    # clamp.
    spec["excl_dt"] = 60.0 * rnd.randint(1, 3)
    # A settlement that must land above the floor: usage below the limit keeps
    # the result positive.
    spec["excl_settle_used"] = rnd.randrange(excl_tpm // 2, excl_tpm, 100)

    # the clamp counter: two clamping calls in a row, one increment each
    obs_in = rnd.randrange(800, 2_001, 100)
    obs_out = rnd.randrange(400, 901, 100)
    spec["r1_obs_rpm"] = rpm()
    spec["r1_obs_in_limit"] = obs_in
    spec["r1_obs_out_limit"] = obs_out
    spec["r1_obs_est_in"] = rnd.randrange(obs_in // 4, obs_in // 2, 50)
    spec["r1_obs_est_out"] = rnd.randrange(50, max(100, obs_out // 4), 50)
    spec["r1_obs_used1_in"] = int(obs_in * 2) + rnd.randrange(0, 501, 100)
    spec["r1_obs_used1_out"] = int(obs_out * 2) + rnd.randrange(0, 301, 100)
    # The second call settles against a zero reservation, so it can only push
    # the axes further below a floor they are already sitting on.
    spec["r1_obs_used2_in"] = rnd.randrange(1_000, 5_001, 500)
    spec["r1_obs_used2_out"] = rnd.randrange(1_000, 5_001, 500)

    # ============================== r2: refund vs settlement ================
    # Estimates stay under a third of the bucket: a refund is capped above at
    # the limit, so an estimate that overflowed the ceiling would make "the
    # whole estimate came back" indistinguishable from "the cap was applied".
    def r2_group(prefix: str, *, out_band=(100, 401)) -> None:
        limit = tpm()
        spec[prefix + "_tpm"] = limit
        spec[prefix + "_rpm"] = rpm()
        spec[prefix + "_est_in"] = rnd.randrange(400, 1_001, 100)
        spec[prefix + "_est_out"] = rnd.randrange(out_band[0], out_band[1], 100)

    r2_group("r2_rule")
    # The settlement in the same fact: reported usage below the reservation, so
    # the axes move UP and the request slot stays spent.
    spec["r2_rule_used_in"] = rnd.randrange(200, 601, 100)
    spec["r2_rule_used_out"] = rnd.randrange(100, 301, 100)

    r2_group("r2_scope")
    # The success path's reported usage: the output axis comes back lower than
    # the estimate, which is what separates "settled" from "refunded".
    spec["r2_scope_used_out"] = rnd.randrange(100, 301, 100)

    r2_group("r2_excl")
    # The failure path must ignore this, however large it is: a reported usage
    # ABOVE the reservation is the case that tells a refund from a settlement.
    spec["r2_excl_resp_out"] = rnd.randrange(600, 1_201, 100)

    r2_group("r2_obs")
    spec["r2_obs_used_in"] = rnd.randrange(200, 601, 100)
    spec["r2_obs_used_out"] = rnd.randrange(100, 301, 100)
    spec["r2_obs_unlimited_used_in"] = rnd.randint(2, 20)
    spec["r2_obs_unlimited_used_out"] = rnd.randint(2, 20)
    spec["r2_obs_unlimited_blocked"] = rnd.randint(1, 9)

    return spec
