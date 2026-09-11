"""g10 worker: the ONLY process that imports the submission.

Runs as `nobody`. For each graded test it reproduces exactly the curator calls
that test makes and writes the resulting values — never a pass/fail — to the
observations file named on argv. `judge.py`, which never imports the submission
and which the grading uid cannot even read (test.sh locks it to root), turns
those values into the verdict. This is the split that closes the forgery in
`tasks/lessons.md` (2026-09-09): a uid cannot stop imported agent code from
rewriting a report its own process produces, so the process that imports the
code no longer produces the report — and the numbers it would have to forge to
pass live only in the judge it cannot read.

The curator-facing halves are lifted from `test_open`/`test_r1`/`test_r2`, same
helpers, so a value here is the value the test saw. The judge holds the
assertions those tests made. A submission that returns forged values only forges
values the judge still checks against the real expectations — which is
implementing them. Floats go through `json` (float encoding is `repr`), so every
value round-trips to the identical double.
"""
from __future__ import annotations

import json
import os
import sys
import traceback

# The import-time environment the suite's conftest sets, applied here because
# this worker is not run under pytest.
os.environ.setdefault("CURATOR_DISABLE_RICH_DISPLAY", "1")
os.environ.setdefault("TELEMETRY_ENABLED", "false")
os.environ.setdefault("CURATOR_VIEWER", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-verifier")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-verifier")
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-verifier")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("COLUMNS", "220")

# test_open owns the curator imports and the scenario helpers; reuse them so a
# probe calls curator exactly as the test does. Importing it runs the
# submission's `import bespokelabs.curator` — this process's whole purpose, and
# why it is disposable.
# probe_support holds the answer-free helpers (the worker never imports test_open,
# whose source carries the expected answer literals). See probe_support.py.
import probe_support as S  # noqa: E402
from harness import read_field  # noqa: E402


def _strat(value):
    """A TokenLimitStrategy enum member as its plain string value."""
    return getattr(value, "value", value)


def rf(read, headers):
    """One read_rate_limit_headers call as [rpm, token axes, strategy, sources]."""
    rpm, tpm, strat, sources = S.reading_fields(read(headers))
    return [rpm, list(S.token_axes(tpm)), _strat(strat), list(sources)]


def raises(fn, *args, **kwargs) -> dict:
    """Call `fn`, reporting whether it raised, its class chain, and the axis /
    requested / limit / message a CapacityExceedsLimitError carries."""
    try:
        fn(*args, **kwargs)
    except BaseException as exc:  # noqa: BLE001 - the test catches a type; the judge checks which
        info = {"raised": True, "mro": [c.__name__ for c in type(exc).__mro__],
                "str": str(exc)}
        for attr in ("axis", "requested", "limit"):
            if hasattr(exc, attr):
                info[attr] = getattr(exc, attr)
        return info
    return {"raised": False, "mro": []}


def _floor_fraction():
    return S.find_const("CAPACITY_DEBT_FLOOR_FRACTION", "DEBT_FLOOR_FRACTION", default=None)


def _clamp_count(t):
    return read_field(t, "num_capacity_debt_clamps", "num_debt_clamps", "num_capacity_clamps")


def _has_clamp_counter(t) -> bool:
    return any(hasattr(t, n) for n in
               ("num_capacity_debt_clamps", "num_debt_clamps", "num_capacity_clamps"))


def _refund_op(t):
    for name in ("refund_capacity", "refund"):
        fn = getattr(t, name, None)
        if callable(fn):
            return fn
    return None


def _settlements(t):
    return read_field(t, "num_capacity_settlements", "num_settlements", "num_capacity_frees")


def _refunds(t):
    return read_field(t, "num_capacity_refunds", "num_refunds")


def _seed_full(t):
    limit = t.max_tokens_per_minute
    if limit is None:
        t.available_token_capacity = None
    elif isinstance(limit, (int, float)):
        t.available_token_capacity = float(limit)
    else:
        t.available_token_capacity = S.T(input=limit.input, output=limit.output)
    return t


# ---------------------------------------------------------------------------
# open feature — the whole stated surface (one fact)
# ---------------------------------------------------------------------------
def probe_open() -> dict:
    import time as _time
    mod = S.budget_module()
    strategy = mod.TokenLimitStrategy
    parse = mod.parse_limit_value
    read = mod.read_rate_limit_headers
    import bespokelabs.curator.status_tracker.online_status_tracker as ost

    o: dict = {}
    o["consts"] = {
        "req_per_min": S.const("DEFAULT_MAX_REQUESTS_PER_MINUTE"),
        "tpm_combined": S.const("DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED"),
        "in_per_min": S.const("DEFAULT_MAX_INPUT_TOKENS_PER_MINUTE"),
        "out_per_min": S.const("DEFAULT_MAX_OUTPUT_TOKENS_PER_MINUTE"),
        "origin_configured": S.const("LIMIT_ORIGIN_CONFIGURED"),
        "origin_defaulted": S.const("LIMIT_ORIGIN_DEFAULTED"),
        "origin_unlimited": S.const("LIMIT_ORIGIN_UNLIMITED"),
    }
    o["request_headers"] = list(S.const("REQUEST_LIMIT_HEADERS"))
    o["input_headers"] = list(S.const("INPUT_TOKEN_LIMIT_HEADERS"))
    o["output_headers"] = list(S.const("OUTPUT_TOKEN_LIMIT_HEADERS"))
    o["total_headers"] = list(S.const("TOTAL_TOKEN_LIMIT_HEADERS"))

    o["ost_strategy_is"] = ost.TokenLimitStrategy is strategy
    o["strategy_values"] = sorted(m.value for m in strategy)
    o["default_is_combined"] = strategy.default is strategy.combined

    o["parse_present"] = [parse("999"), parse("1.5k"), parse("2M"), parse("40000.5"),
                          parse("  60000  "), parse(4000)]
    o["parse_absent"] = [parse(a) for a in
                         ("0", 0, "1,000", "1e3", "-5", "", "unknown", None, True, 1500.0, b"12")]

    o["read_anthropic"] = rf(read, {
        "anthropic-ratelimit-requests-limit": "4000",
        "anthropic-ratelimit-input-tokens-limit": "400000",
        "anthropic-ratelimit-output-tokens-limit": "80000"})
    o["read_remaining"] = rf(read, {
        "llm_provider-anthropic-ratelimit-input-tokens-remaining": "12345",
        "llm_provider-anthropic-ratelimit-output-tokens-remaining": "678",
        "x-ratelimit-remaining-requests": "9",
        "x-ratelimit-reset-tokens": "60s"})
    o["read_empty"] = rf(read, {})
    o["read_total_ci"] = rf(read, {"X-RateLimit-Limit-Tokens": "60000"})
    o["read_pair"] = rf(read, {
        "x-ratelimit-limit-requests": "600",
        "x-ratelimit-limit-tokens": "90000",
        "x-ratelimit-limit-input-tokens": "50000",
        "x-ratelimit-limit-output-tokens": "20000"})
    o["read_half_pair"] = rf(read, {
        "x-ratelimit-limit-input-tokens": "50000", "x-ratelimit-limit-tokens": "90000"})
    o["read_zero"] = rf(read, {
        "x-ratelimit-limit-tokens": "1.5k", "x-ratelimit-limit-requests": "0"})

    # tracker: seeded full, on an injected clock
    clock = S.Clock(1000.0)
    t = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000,
                  available_request_capacity=1.0, available_token_capacity=0,
                  capacity_clock=clock)
    o["seed"] = [t.last_update_time, (abs(t.last_update_time - _time.time()) > 1e9),
                 t.available_request_capacity, t.available_token_capacity,
                 t.token_limit_origin, t.request_limit_origin]
    t.consume_capacity(S.T(input=3000, output=1000))
    seed_after_consume = t.available_token_capacity
    clock.now = 1006.0
    t.update_capacity()
    seed_after_refill = [t.available_token_capacity, t.last_update_time]
    clock.now = 996.0
    t.update_capacity()
    seed_backwards = [t.available_token_capacity, t.last_update_time]
    o["seed_dynamics"] = [seed_after_consume, seed_after_refill, seed_backwards]

    # seperate: fresh _TokenUsage every time, floored refill
    sep_clock = S.Clock(500.0)
    ts = S.tracker(token_limit_strategy=strategy.seperate, max_requests_per_minute=60,
                   max_tokens_per_minute=S.T(input=10_000, output=5_000), capacity_clock=sep_clock)
    sep_seed = list(S.token_axes(ts.available_token_capacity))
    ts.consume_capacity(S.T(input=600, output=200))
    sep_consume = list(S.token_axes(ts.available_token_capacity))
    sep_clock.now = 501.0
    ts.update_capacity()
    sep_refill = list(S.token_axes(ts.available_token_capacity))
    o["sep_dynamics"] = [sep_seed, sep_consume, sep_refill]

    # 0 is "nobody told us", None is unlimited
    td = S.tracker(max_requests_per_minute=0, max_tokens_per_minute=0)
    o["defaulted"] = [td.max_requests_per_minute, td.max_tokens_per_minute,
                      td.available_request_capacity, td.available_token_capacity,
                      td.request_limit_origin, td.token_limit_origin]

    tu = S.tracker(max_requests_per_minute=None, max_tokens_per_minute=None)
    unlimited_has = tu.has_capacity(S.T(input=10**9, output=10**9))
    tu.consume_capacity(S.T(input=10**9, output=10**9))
    o["unlimited"] = [tu.max_tokens_per_minute, tu.available_token_capacity,
                      tu.available_request_capacity, tu.request_limit_origin,
                      tu.token_limit_origin, unlimited_has is True,
                      tu.available_token_capacity, tu.available_request_capacity]

    tsu = S.tracker(token_limit_strategy=strategy.seperate, max_tokens_per_minute=None)
    o["sep_unlimited"] = [list(S.token_axes(tsu.max_tokens_per_minute)),
                          list(S.token_axes(tsu.available_token_capacity)), tsu.token_limit_origin]

    tpa = S.tracker(token_limit_strategy=strategy.seperate, max_tokens_per_minute=S.T(input=0, output=20_000))
    o["sep_partial_default"] = [list(S.token_axes(tpa.max_tokens_per_minute)), tpa.token_limit_origin]

    o["coerce_scalar_to_sep"] = list(S.token_axes(
        S.tracker(token_limit_strategy=strategy.seperate, max_tokens_per_minute=90_000).max_tokens_per_minute))
    o["coerce_sep_to_scalar"] = S.tracker(max_tokens_per_minute=S.T(input=30_000, output=20_000)).max_tokens_per_minute

    # a request that can never fit raises, and moves nothing
    raise_clock = S.Clock(1000.0)
    te = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000, capacity_clock=raise_clock)
    raise_clock.now = 1042.0
    o["raise_total"] = raises(te.has_capacity, S.T(input=9000, output=2000))
    o["raise_total_after"] = [te.last_update_time, te.available_token_capacity]

    tse = S.tracker(token_limit_strategy=strategy.seperate, max_requests_per_minute=60,
                    max_tokens_per_minute=S.T(input=1_000, output=500))
    o["raise_input"] = raises(tse.has_capacity, S.T(input=1500, output=800))

    o["unlimited_never_raises"] = tu.has_capacity(S.T(input=10**12, output=10**12)) is True
    tb = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000)
    tb.consume_capacity(S.T(input=900, output=50))
    o["empty_bucket_false"] = tb.has_capacity(S.T(input=100, output=100)) is False

    # _reserve_capacity: estimate once, all or nothing
    proc = S.StubProcessor(S.T(input=700, output=100))
    tr = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000)
    first = proc._reserve_capacity(tr, [])
    o["reserve_first"] = [list(S.token_axes(first)), tr.available_token_capacity,
                          tr.available_request_capacity, proc.estimate_calls]
    second = proc._reserve_capacity(tr, [])
    o["reserve_second"] = [second is None, tr.available_token_capacity,
                           tr.available_request_capacity, proc.estimate_calls]
    unlimited = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=None)
    third = proc._reserve_capacity(unlimited, [])
    o["reserve_unlimited"] = [list(S.token_axes(third)), proc.estimate_calls,
                              unlimited.available_token_capacity, unlimited.available_request_capacity]

    o["free_capacity_gone"] = hasattr(S.BaseOnlineRequestProcessor, "free_capacity") is False

    # apply_rate_limit_reading re-reads the default block
    fresh = S.StubProcessor(S.T(input=700, output=100))
    apply_before = [fresh.default_max_tokens_per_minute, _strat(fresh.token_limit_strategy)]
    reading = read({"x-ratelimit-limit-requests": "600",
                    "x-ratelimit-limit-input-tokens": "50000",
                    "x-ratelimit-limit-output-tokens": "20000"})
    fresh.apply_rate_limit_reading(reading)
    o["apply"] = [apply_before, _strat(fresh.token_limit_strategy),
                  fresh.header_based_max_requests_per_minute,
                  list(S.token_axes(fresh.header_based_max_tokens_per_minute)),
                  list(S.token_axes(fresh.default_max_tokens_per_minute)),
                  list(S.token_axes(fresh.max_tokens_per_minute)),
                  fresh.max_requests_per_minute]
    return o


# ---------------------------------------------------------------------------
# r1 — debt floor
# ---------------------------------------------------------------------------
def probe_r1_rule() -> dict:
    fraction = _floor_fraction()
    t = _seed_full(S.tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000))
    t.consume_capacity(S.T(input=700, output=100))
    after_consume = t.available_token_capacity
    t.free_capacity(used=S.T(input=1000, output=500), blocked=S.T(input=700, output=100))
    return {"fraction": fraction, "after_consume": after_consume,
            "after_settle": t.available_token_capacity}


def probe_r1_scope() -> dict:
    o = {"has_floor": _floor_fraction() is not None}
    if not o["has_floor"]:
        return o
    defaulted = _seed_full(S.tracker(max_requests_per_minute=60, max_tokens_per_minute=0))
    o["defaulted_limit"] = defaulted.max_tokens_per_minute
    defaulted.consume_capacity(S.T(input=90_000, output=10_000))
    o["defaulted_after_consume"] = defaulted.available_token_capacity
    defaulted.free_capacity(used=S.T(input=200_000, output=0), blocked=S.T(input=90_000, output=10_000))
    o["defaulted_after_settle"] = defaulted.available_token_capacity

    sep = _seed_full(S.tracker(token_limit_strategy=S.budget_module().TokenLimitStrategy.seperate,
                               max_requests_per_minute=60, max_tokens_per_minute=S.T(input=1_000, output=500)))
    sep.consume_capacity(S.T(input=700, output=100))
    o["sep_after_consume"] = list(S.token_axes(sep.available_token_capacity))
    sep.free_capacity(used=S.T(input=2000, output=1000), blocked=S.T(input=700, output=100))
    o["sep_after_settle"] = list(S.token_axes(sep.available_token_capacity))

    unlimited = S.tracker(max_requests_per_minute=None, max_tokens_per_minute=None)
    unlimited.consume_capacity(S.T(input=10**9, output=10**9))
    unlimited.free_capacity(used=S.T(input=10**9, output=10**9), blocked=S.T(input=1, output=1))
    o["unlimited_token"] = unlimited.available_token_capacity
    o["unlimited_request"] = unlimited.available_request_capacity
    o["defaulted_request"] = defaulted.available_request_capacity
    o["sep_request"] = sep.available_request_capacity
    return o


def probe_r1_exclusions() -> dict:
    probe = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000)
    o = {"has_floor": _floor_fraction() is not None, "has_counter": _has_clamp_counter(probe)}
    if not (o["has_floor"] and o["has_counter"]):
        return o
    clock = S.Clock(1000.0)
    refilled = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000, capacity_clock=clock)
    refilled.consume_capacity(S.T(input=700, output=100))
    clock.now = 1060.0
    refilled.update_capacity()
    o["refilled"] = [refilled.available_token_capacity, refilled.available_request_capacity,
                     _clamp_count(refilled)]
    released = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000)
    released.free_capacity(used=S.T(input=0, output=0), blocked=S.T(input=700, output=100))
    o["released"] = [released.available_token_capacity, _clamp_count(released)]
    settled = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000)
    settled.consume_capacity(S.T(input=700, output=100))
    settled.free_capacity(used=S.T(input=700, output=200), blocked=S.T(input=700, output=100))
    o["settled"] = [settled.available_token_capacity, _clamp_count(settled)]
    return o


def probe_r1_observability() -> dict:
    probe = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=1_000)
    o = {"has_counter": _has_clamp_counter(probe)}
    if not o["has_counter"]:
        return o
    sep = _seed_full(S.tracker(token_limit_strategy=S.budget_module().TokenLimitStrategy.seperate,
                               max_requests_per_minute=60, max_tokens_per_minute=S.T(input=1_000, output=500)))
    initial = _clamp_count(sep)
    sep.consume_capacity(S.T(input=700, output=100))
    after_consume = _clamp_count(sep)
    sep.free_capacity(used=S.T(input=2000, output=1000), blocked=S.T(input=700, output=100))
    after_first = _clamp_count(sep)
    sep.free_capacity(used=S.T(input=5000, output=5000), blocked=S.T(input=0, output=0))
    after_second = _clamp_count(sep)
    o["counts"] = [initial, after_consume, after_first, after_second]
    return o


# ---------------------------------------------------------------------------
# r2 — settlement vs refund
# ---------------------------------------------------------------------------
def probe_r2_rule() -> dict:
    refunded = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
    refunded.consume_capacity(S.T(input=600, output=200))
    o = {"after_consume": [refunded.available_request_capacity, refunded.available_token_capacity],
         "has_refund": _refund_op(refunded) is not None}
    if not o["has_refund"]:
        return o
    op = _refund_op(refunded)
    op(S.T(input=600, output=200))
    o["after_refund"] = [refunded.available_request_capacity, refunded.available_token_capacity]
    op(S.T(input=600, output=200))
    o["after_refund2"] = [refunded.available_request_capacity, refunded.available_token_capacity]

    settled = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
    settled.consume_capacity(S.T(input=600, output=200))
    settled.free_capacity(used=S.T(input=500, output=100), blocked=S.T(input=600, output=200))
    o["settled"] = [settled.available_token_capacity, settled.available_request_capacity]

    proc = S.StubProcessor(S.T(input=600, output=200))
    delegated = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
    blocked = proc._reserve_capacity(delegated, [])
    o["delegated_reserve"] = [delegated.available_request_capacity, delegated.available_token_capacity]
    proc._refund_capacity(delegated, blocked)
    o["delegated_refund"] = [delegated.available_request_capacity, delegated.available_token_capacity]
    return o


def probe_r2_scope() -> dict:
    def reserve():
        proc = S.StubProcessor(S.T(input=700, output=300))
        t = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
        blocked = proc._reserve_capacity(t, [])
        return proc, t, blocked

    proc, exhausted, blocked = reserve()
    reserve_state = [exhausted.available_request_capacity, exhausted.available_token_capacity]
    S.run_attempt(proc, exhausted, blocked, attempts_left=0,
                  response=S.make_response("length", S.T(input=700, output=300)))
    exhausted_state = [exhausted.available_request_capacity, exhausted.available_token_capacity]

    proc, requeued, blocked = reserve()
    request = S.run_attempt(proc, requeued, blocked, attempts_left=1,
                            response=S.make_response("length", S.T(input=700, output=300)))
    requeued_state = [request.attempts_left, requeued.available_request_capacity,
                      requeued.available_token_capacity]

    proc, succeeded, blocked = reserve()
    S.run_attempt(proc, succeeded, blocked, attempts_left=1,
                  response=S.make_response("stop", S.T(input=700, output=100)))
    success_state = [succeeded.available_request_capacity, succeeded.available_token_capacity]

    return {"reserve_state": reserve_state, "exhausted": exhausted_state,
            "requeued": requeued_state, "success": success_state}


def probe_r2_exclusions() -> dict:
    proc = S.StubProcessor(S.T(input=900, output=100))
    t = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
    blocked = proc._reserve_capacity(t, [])
    o = {"blocked_axes": list(S.token_axes(blocked)),
         "after_reserve": [t.available_request_capacity, t.available_token_capacity]}
    S.run_attempt(proc, t, blocked, attempts_left=0,
                  response=S.make_response("length", S.T(input=900, output=800)))
    o["final"] = [t.available_token_capacity, t.available_request_capacity]
    return o


def probe_r2_observability() -> dict:
    settled = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
    o = {"has_refund": _refund_op(settled) is not None}
    if not o["has_refund"]:
        return o
    o["initial"] = [_settlements(settled), _refunds(settled)]
    settled.consume_capacity(S.T(input=600, output=200))
    o["after_consume"] = [_settlements(settled), _refunds(settled)]
    settled.free_capacity(used=S.T(input=500, output=100), blocked=S.T(input=600, output=200))
    o["after_free"] = [_settlements(settled), _refunds(settled)]

    refunded = S.tracker(max_requests_per_minute=60, max_tokens_per_minute=10_000)
    refunded.consume_capacity(S.T(input=600, output=200))
    _refund_op(refunded)(S.T(input=600, output=200))
    o["refunded"] = [_settlements(refunded), _refunds(refunded)]

    unlimited = S.tracker(max_requests_per_minute=None, max_tokens_per_minute=None)
    unlimited.free_capacity(used=S.T(input=5, output=5), blocked=S.T(input=1, output=1))
    _refund_op(unlimited)(S.T(input=1, output=1))
    o["unlimited"] = [_settlements(unlimited), _refunds(unlimited),
                      unlimited.available_token_capacity, unlimited.available_request_capacity]
    return o


PROBES = {
    "test_open::test_open_feature__one_capacity_budget_decodes_limits_and_reserves_all_or_nothing": probe_open,
    "test_r1::test_rule__an_over_settled_axis_stops_at_a_quarter_of_the_limit_in_debt": probe_r1_rule,
    "test_r1::test_scope__the_floor_follows_the_normalised_limit_of_each_axis": probe_r1_scope,
    "test_r1::test_exclusions__capping_at_the_limit_and_staying_above_the_floor_do_not_count": probe_r1_exclusions,
    "test_r1::test_observability__the_clamp_counter_counts_calls_not_axes": probe_r1_observability,
    "test_r2::test_rule__a_refund_returns_the_whole_estimate_and_one_request_slot": probe_r2_rule,
    "test_r2::test_scope__both_failure_exits_refund_while_the_success_exit_settles": probe_r2_scope,
    "test_r2::test_exclusions__the_failure_refund_ignores_the_usage_the_response_reported": probe_r2_exclusions,
    "test_r2::test_observability__settlements_and_refunds_are_counted_apart_even_when_unlimited": probe_r2_observability,
}


def main(out_path: str) -> int:
    results: dict[str, dict] = {}
    for node, fn in PROBES.items():
        try:
            results[node] = {"ok": True, "obs": fn()}
        except BaseException as exc:  # noqa: BLE001 - a probe that dies is a failed fact, reported not raised
            results[node] = {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                             "trace": traceback.format_exc()[-2000:]}
    with open(out_path, "w") as fh:
        json.dump(results, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
