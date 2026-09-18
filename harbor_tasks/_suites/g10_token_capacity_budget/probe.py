"""g10 worker: the ONLY process that imports the submission.

Runs as `nobody`. For each graded test it reproduces exactly the curator calls
that test makes and writes the resulting values — never a pass/fail — to the
observations file named on argv. `judge.py`, which never imports the submission
and which the grading uid cannot even read (test.sh locks it to root), turns
those values into the verdict. This is the split that closes the forgery in
`tasks/lessons.md` (2026-09-09): a uid cannot stop imported agent code from
rewriting a report its own process produces, so the process that imports the
code no longer produces the report.

THE SCENARIOS ARE NOT FIXED. The split left this process authoring the values
the verdict is computed from, and while the scenarios were literals those values
were the same every run — so an `observations.json` written by an `atexit` hook
scored 9/9 against a tree with neither hidden requirement implemented (measured
on v11: reward 1.0 with `refund_capacity`, the failure-path refund and all three
counters deleted). Every limit, estimate, reported usage, clock step and header
value below now comes from `fixture_spec.derive(seed)`, with `seed` chosen by
root per run, and the judge recomputes what the answers must be for THOSE
inputs. Reading `fixture_spec` gains the worker nothing: it holds the questions,
not the answers.

The curator-facing halves and the node ids come from the suite's pytest
reference, `test_open.py`/`test_r1.py`/`test_r2.py` — which lives in SWEWorld at
`harbor_tasks/_suites/g10_token_capacity_budget/`, is deliberately NOT shipped in
the task's `tests/`, and works its examples on the old fixed fixture. The same
helpers are used here, so a value here is the value that reference saw on the
same inputs, and the judge holds the arithmetic it asserts. Floats go through
`json` (float encoding is `repr`), so every value round-trips to the identical
double.
"""
from __future__ import annotations

import json
import os
import sys
import traceback

# Bound BEFORE the submission is imported, and called instead of returning from
# main(). Interpreter shutdown runs `atexit` hooks the submission registered at
# import — which is how an observations file was overwritten from a tree that
# implemented nothing. Leaving through `os._exit` never reaches them. This is a
# lock on one door, not the fix: a hook can patch `open` and edit the file as it
# is written. What makes forged values worthless is that they are not knowable.
_EXIT = os._exit

# The import-time environment the pytest reference's conftest sets, applied
# here because this worker is not run under pytest.
os.environ.setdefault("CURATOR_DISABLE_RICH_DISPLAY", "1")
os.environ.setdefault("TELEMETRY_ENABLED", "false")
os.environ.setdefault("CURATOR_VIEWER", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-verifier")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-verifier")
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-verifier")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("COLUMNS", "220")

import fixture_spec  # noqa: E402 - the run's inputs; stdlib only, no answers

# probe_support owns the curator imports and the scenario helpers, so a probe
# calls curator exactly as the pytest reference does from the one definition of
# each. Importing it runs the submission's `import bespokelabs.curator` — this
# process's whole purpose, and why it is disposable. It holds only answer-free
# helpers: the expected values live in the judge (and, for humans, in the
# unshipped test_*.py), neither of which this process can read.
import probe_support as S  # noqa: E402
from harness import read_field  # noqa: E402

# Filled in by main() from argv before any probe runs.
SPEC: dict = {}


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
    import dataclasses
    import time as _time
    mod = S.budget_module()
    strategy = mod.TokenLimitStrategy
    parse = mod.parse_limit_value
    read = mod.read_rate_limit_headers
    import bespokelabs.curator.status_tracker.online_status_tracker as ost

    o: dict = {}
    # The ticket's own constants, which cannot be re-drawn: they ARE the
    # requirement, `instruction.md:11` publishes every one of them, and a value
    # nobody may change is not a value anybody has to guess.
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

    # The numbers move; the formats do not. The rejected forms are the ticket's
    # own list (`instruction.md:22`) and stay literal.
    o["parse_present"] = [parse(f"{SPEC['parse_plain_str']}"),
                          parse(f"{SPEC['parse_k_units']}.5k"),
                          parse(f"{SPEC['parse_m_units']}M"),
                          parse(f"{SPEC['parse_trunc_int']}.5"),
                          parse(f"  {SPEC['parse_spaced']}  "),
                          parse(SPEC["parse_int"])]
    o["parse_absent"] = [parse(a) for a in
                         ("0", 0, "1,000", "1e3", "-5", "", "unknown", None, True, 1500.0, b"12")]

    o["read_anthropic"] = rf(read, {
        "anthropic-ratelimit-requests-limit": str(SPEC["h_anthropic_req"]),
        "anthropic-ratelimit-input-tokens-limit": str(SPEC["h_anthropic_in"]),
        "anthropic-ratelimit-output-tokens-limit": str(SPEC["h_anthropic_out"])})
    # Remaining counters and reset timers are never read, so their values are
    # fixed: there is no answer here to re-draw, only names to ignore.
    o["read_remaining"] = rf(read, {
        "llm_provider-anthropic-ratelimit-input-tokens-remaining": "12345",
        "llm_provider-anthropic-ratelimit-output-tokens-remaining": "678",
        "x-ratelimit-remaining-requests": "9",
        "x-ratelimit-reset-tokens": "60s"})
    o["read_empty"] = rf(read, {})
    o["read_total_ci"] = rf(read, {"X-RateLimit-Limit-Tokens": str(SPEC["h_total_ci"])})
    o["read_pair"] = rf(read, {
        "x-ratelimit-limit-requests": str(SPEC["h_pair_req"]),
        "x-ratelimit-limit-tokens": str(SPEC["h_pair_total"]),
        "x-ratelimit-limit-input-tokens": str(SPEC["h_pair_in"]),
        "x-ratelimit-limit-output-tokens": str(SPEC["h_pair_out"])})
    o["read_half_pair"] = rf(read, {
        "x-ratelimit-limit-input-tokens": str(SPEC["h_half_in"]),
        "x-ratelimit-limit-tokens": str(SPEC["h_half_total"])})
    o["read_zero"] = rf(read, {
        "x-ratelimit-limit-tokens": f"{SPEC['h_zero_k_units']}.5k",
        "x-ratelimit-limit-requests": "0"})

    # The reading's own shape: a frozen dataclass whose field ORDER the ticket
    # fixes. Read off the live class rather than assumed from the four values,
    # which a plain mutable namespace would also have produced.
    reading_cls = mod.RateLimitReading
    sample = read({"x-ratelimit-limit-tokens": str(SPEC["h_total_ci"])})
    o["reading_shape"] = [dataclasses.is_dataclass(reading_cls),
                          [f.name for f in dataclasses.fields(reading_cls)]]
    o["reading_frozen"] = raises(setattr, sample, "max_requests_per_minute", 1)

    # Tuple order decides, a malformed name is skipped rather than fatal, and
    # the caller's mapping comes back exactly as it was handed over — the
    # lower-casing is of a copy. The mapping ITSELF is reported, not just a
    # verdict on it: "I did not mutate it" was a worker-computed boolean whose
    # passing value was True, and the judge now compares the mapping against the
    # inputs the seed drew.
    given = {"X-RateLimit-Limit-Requests": SPEC["h_fallthrough_bad"],
             "anthropic-ratelimit-requests-limit": str(SPEC["h_fallthrough_req"]),
             "x-ratelimit-limit-tokens": str(SPEC["h_fallthrough_total"])}
    snapshot = dict(given)
    o["read_fallthrough"] = rf(read, given)
    o["headers_after"] = given
    o["headers_untouched"] = given == snapshot
    o["read_priority"] = rf(read, {
        "x-ratelimit-limit-requests": str(SPEC["h_priority_x"]),
        "anthropic-ratelimit-requests-limit": str(SPEC["h_priority_anthropic"])})

    # tracker: seeded full, on an injected clock. `available_*_capacity` are
    # handed deliberate rubbish, which normalisation must overwrite.
    clock = S.Clock(SPEC["seed_t0"])
    t = S.tracker(max_requests_per_minute=SPEC["seed_rpm"],
                  max_tokens_per_minute=SPEC["seed_tpm"],
                  available_request_capacity=1.0, available_token_capacity=0,
                  capacity_clock=clock)
    o["seed"] = [t.last_update_time, (abs(t.last_update_time - _time.time()) > 1e9),
                 t.available_request_capacity, t.available_token_capacity,
                 t.token_limit_origin, t.request_limit_origin]
    t.consume_capacity(S.T(input=SPEC["seed_est_in"], output=SPEC["seed_est_out"]))
    seed_after_consume = t.available_token_capacity
    clock.now = SPEC["seed_t0"] + SPEC["seed_dt"]
    t.update_capacity()
    seed_after_refill = [t.available_token_capacity, t.last_update_time]
    clock.now = SPEC["seed_t0"] + SPEC["seed_back_dt"]
    t.update_capacity()
    seed_backwards = [t.available_token_capacity, t.last_update_time]
    o["seed_dynamics"] = [seed_after_consume, seed_after_refill, seed_backwards]

    # seperate: fresh _TokenUsage every time, floored refill
    sep_clock = S.Clock(SPEC["sep_t0"])
    ts = S.tracker(token_limit_strategy=strategy.seperate,
                   max_requests_per_minute=SPEC["seed_rpm"],
                   max_tokens_per_minute=S.T(input=SPEC["sep_in_limit"],
                                             output=SPEC["sep_out_limit"]),
                   capacity_clock=sep_clock)
    sep_seed = list(S.token_axes(ts.available_token_capacity))
    ts.consume_capacity(S.T(input=SPEC["sep_est_in"], output=SPEC["sep_est_out"]))
    sep_consume = list(S.token_axes(ts.available_token_capacity))
    sep_clock.now = SPEC["sep_t0"] + SPEC["sep_dt"]
    ts.update_capacity()
    sep_refill = list(S.token_axes(ts.available_token_capacity))
    o["sep_dynamics"] = [sep_seed, sep_consume, sep_refill]

    # 0 is "nobody told us", None is unlimited. Both are the ticket's fixed
    # sentinels and the values they produce are its DEFAULT_* constants.
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

    tpa = S.tracker(token_limit_strategy=strategy.seperate,
                    max_tokens_per_minute=S.T(input=0, output=SPEC["partial_out_limit"]))
    o["sep_partial_default"] = [list(S.token_axes(tpa.max_tokens_per_minute)), tpa.token_limit_origin]

    o["coerce_scalar_to_sep"] = list(S.token_axes(
        S.tracker(token_limit_strategy=strategy.seperate,
                  max_tokens_per_minute=SPEC["coerce_scalar"]).max_tokens_per_minute))
    o["coerce_sep_to_scalar"] = S.tracker(
        max_tokens_per_minute=S.T(input=SPEC["coerce_sep_in"],
                                  output=SPEC["coerce_sep_out"])).max_tokens_per_minute

    # a request that can never fit raises, and moves nothing
    raise_clock = S.Clock(SPEC["raise_t0"])
    te = S.tracker(max_requests_per_minute=SPEC["seed_rpm"],
                   max_tokens_per_minute=SPEC["raise_tpm"], capacity_clock=raise_clock)
    raise_clock.now = SPEC["raise_t0"] + SPEC["raise_bump"]
    raise_in = SPEC["raise_est_in"]
    raise_out = SPEC["raise_tpm"] + SPEC["raise_over"] - raise_in
    o["raise_total"] = raises(te.has_capacity, S.T(input=raise_in, output=raise_out))
    o["raise_total_after"] = [te.last_update_time, te.available_token_capacity]

    tse = S.tracker(token_limit_strategy=strategy.seperate,
                    max_requests_per_minute=SPEC["seed_rpm"],
                    max_tokens_per_minute=S.T(input=SPEC["raise_in_limit"],
                                              output=SPEC["raise_out_limit"]))
    o["raise_input"] = raises(tse.has_capacity, S.T(
        input=SPEC["raise_in_limit"] + SPEC["raise_in_over"],
        output=SPEC["raise_out_limit"] + SPEC["raise_out_over"]))

    o["unlimited_never_raises"] = tu.has_capacity(S.T(input=10**12, output=10**12)) is True
    # An empty bucket returns False rather than raising. The bucket's own
    # reading is reported beside the verdict, so the fact rests on a number the
    # seed drew and not only on a boolean whose passing value is False.
    tb = S.tracker(max_requests_per_minute=SPEC["seed_rpm"], max_tokens_per_minute=SPEC["empty_tpm"])
    tb.consume_capacity(S.T(input=SPEC["empty_est_in"], output=SPEC["empty_est_out"]))
    empty_left = tb.available_token_capacity
    o["empty_bucket"] = [empty_left, tb.has_capacity(
        S.T(input=SPEC["empty_ask_in"], output=SPEC["empty_ask_out"])) is False]

    # _reserve_capacity: estimate once, all or nothing
    proc = S.StubProcessor(S.T(input=SPEC["res_est_in"], output=SPEC["res_est_out"]))
    tr = S.tracker(max_requests_per_minute=SPEC["res_rpm"], max_tokens_per_minute=SPEC["res_tpm"])
    first = proc._reserve_capacity(tr, [])
    o["reserve_first"] = [list(S.token_axes(first)), tr.available_token_capacity,
                          tr.available_request_capacity, proc.estimate_calls]
    second = proc._reserve_capacity(tr, [])
    o["reserve_second"] = [second is None, tr.available_token_capacity,
                           tr.available_request_capacity, proc.estimate_calls]
    unlimited = S.tracker(max_requests_per_minute=SPEC["res_unlimited_rpm"],
                          max_tokens_per_minute=None)
    third = proc._reserve_capacity(unlimited, [])
    o["reserve_unlimited"] = [list(S.token_axes(third)), proc.estimate_calls,
                              unlimited.available_token_capacity, unlimited.available_request_capacity]

    o["free_capacity_gone"] = hasattr(S.BaseOnlineRequestProcessor, "free_capacity") is False

    # apply_rate_limit_reading re-reads the default block
    fresh = S.StubProcessor(S.T(input=SPEC["res_est_in"], output=SPEC["res_est_out"]))
    apply_before = [fresh.default_max_tokens_per_minute, _strat(fresh.token_limit_strategy)]
    reading = read({"x-ratelimit-limit-requests": str(SPEC["h_apply_req"]),
                    "x-ratelimit-limit-input-tokens": str(SPEC["h_apply_in"]),
                    "x-ratelimit-limit-output-tokens": str(SPEC["h_apply_out"])})
    fresh.apply_rate_limit_reading(reading)
    o["apply"] = [apply_before, _strat(fresh.token_limit_strategy),
                  fresh.header_based_max_requests_per_minute,
                  list(S.token_axes(fresh.header_based_max_tokens_per_minute)),
                  list(S.token_axes(fresh.default_max_tokens_per_minute)),
                  list(S.token_axes(fresh.max_tokens_per_minute)),
                  fresh.max_requests_per_minute]

    # Under `seperate` every mutation rebinds a fresh _TokenUsage. `.total` is a
    # stored pydantic field computed once at construction, so an implementation
    # that assigns to `.input` keeps the arithmetic right and leaves `.total`
    # stale — which no axis reading shows. Identity does.
    idc = S.tracker(token_limit_strategy=strategy.seperate,
                    max_requests_per_minute=SPEC["seed_rpm"],
                    max_tokens_per_minute=S.T(input=SPEC["rebind_in_limit"],
                                              output=SPEC["rebind_out_limit"]))
    seeded = idc.available_token_capacity
    idc.consume_capacity(S.T(input=SPEC["rebind_est_in"], output=SPEC["rebind_est_out"]))
    consumed = idc.available_token_capacity
    o["rebind_consume"] = [consumed is not seeded, list(S.token_axes(seeded)),
                           list(S.token_axes(consumed))]
    idc.free_capacity(used=S.T(input=SPEC["rebind_used_in"], output=SPEC["rebind_used_out"]),
                      blocked=S.T(input=SPEC["rebind_est_in"], output=SPEC["rebind_est_out"]))
    o["rebind_settle"] = [idc.available_token_capacity is not consumed,
                          list(S.token_axes(consumed))]

    # manual -> header -> default, on all three limit properties. Compared
    # against the processor's own default fields rather than the cost map's
    # numbers, which are curator's and not this ticket's to fix.
    prec = S.StubProcessor(S.T(input=1, output=1))
    prec.manual_max_requests_per_minute = SPEC["prec_manual_req"]
    prec.header_based_max_requests_per_minute = SPEC["prec_header_req"]
    prec.manual_max_tokens_per_minute = SPEC["prec_manual_tok"]
    prec.header_based_max_tokens_per_minute = SPEC["prec_header_tok"]
    prec.manual_max_concurrent_requests = SPEC["prec_manual_conc"]
    prec.header_based_max_concurrent_requests = SPEC["prec_header_conc"]
    manual = [prec.max_requests_per_minute, prec.max_tokens_per_minute, prec.max_concurrent_requests]
    prec.manual_max_requests_per_minute = None
    prec.manual_max_tokens_per_minute = None
    prec.manual_max_concurrent_requests = None
    header = [prec.max_requests_per_minute, prec.max_tokens_per_minute, prec.max_concurrent_requests]
    prec.header_based_max_requests_per_minute = None
    prec.header_based_max_tokens_per_minute = None
    prec.header_based_max_concurrent_requests = None
    o["precedence"] = [manual, header,
                       [prec.max_requests_per_minute == prec.default_max_requests_per_minute,
                        prec.max_tokens_per_minute == prec.default_max_tokens_per_minute,
                        prec.max_concurrent_requests is None]]

    # One release per attempt on every terminal path. Counted, not inferred from
    # the buckets: a release is capped at the limit, so a second one is invisible.
    # A response per attempt, never one object driven twice: the handler hands
    # it to `update_stats` and the moving window, and a shared instance would
    # make the three counts depend on the order they ran in.
    def reported(finish_reason):
        return S.make_response(finish_reason, S.T(input=SPEC["rel_est_in"],
                                                  output=SPEC["rel_resp_out"]))

    o["release_calls"] = [_release_counts(0, reported("length")),
                          _release_counts(1, reported("length")),
                          _release_counts(1, reported("stop"))]
    return o


def _release_counts(attempts_left, response):
    """[total, settlements, refunds] for one attempt through the retry handler."""
    proc = S.StubProcessor(S.T(input=SPEC["rel_est_in"], output=SPEC["rel_est_out"]))
    t = S.tracker(max_requests_per_minute=SPEC["rel_rpm"], max_tokens_per_minute=SPEC["rel_tpm"])
    blocked = proc._reserve_capacity(t, [])
    counts = S.count_releases(t)
    S.run_attempt(proc, t, blocked, attempts_left=attempts_left, response=response)
    return [counts["settle"] + counts["refund"], counts["settle"], counts["refund"]]


# ---------------------------------------------------------------------------
# r1 — debt floor
# ---------------------------------------------------------------------------
def probe_r1_rule() -> dict:
    fraction = _floor_fraction()
    t = _seed_full(S.tracker(max_requests_per_minute=SPEC["r1_rpm"],
                             max_tokens_per_minute=SPEC["r1_tpm"]))
    blocked = S.T(input=SPEC["r1_est_in"], output=SPEC["r1_est_out"])
    t.consume_capacity(blocked)
    after_consume = t.available_token_capacity
    used_out = SPEC["r1_used_out"]
    t.free_capacity(used=S.T(input=SPEC["r1_used_total"] - used_out, output=used_out),
                    blocked=blocked)
    return {"fraction": fraction, "after_consume": after_consume,
            "after_settle": t.available_token_capacity}


def probe_r1_scope() -> dict:
    o = {"has_floor": _floor_fraction() is not None}
    if not o["has_floor"]:
        return o
    defaulted = _seed_full(S.tracker(max_requests_per_minute=SPEC["r1_def_rpm"],
                                     max_tokens_per_minute=0))
    o["defaulted_limit"] = defaulted.max_tokens_per_minute
    def_blocked = S.T(input=SPEC["r1_def_est_in"], output=SPEC["r1_def_est_out"])
    defaulted.consume_capacity(def_blocked)
    o["defaulted_after_consume"] = defaulted.available_token_capacity
    defaulted.free_capacity(used=S.T(input=SPEC["r1_def_used_total"], output=0),
                            blocked=def_blocked)
    o["defaulted_after_settle"] = defaulted.available_token_capacity

    sep = _seed_full(S.tracker(token_limit_strategy=S.budget_module().TokenLimitStrategy.seperate,
                               max_requests_per_minute=SPEC["r1_sep_rpm"],
                               max_tokens_per_minute=S.T(input=SPEC["r1_sep_in_limit"],
                                                         output=SPEC["r1_sep_out_limit"])))
    sep_blocked = S.T(input=SPEC["r1_sep_est_in"], output=SPEC["r1_sep_est_out"])
    sep.consume_capacity(sep_blocked)
    o["sep_after_consume"] = list(S.token_axes(sep.available_token_capacity))
    sep.free_capacity(used=S.T(input=SPEC["r1_sep_used_in"], output=SPEC["r1_sep_used_out"]),
                      blocked=sep_blocked)
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
    probe = S.tracker(max_requests_per_minute=SPEC["excl_rpm"], max_tokens_per_minute=SPEC["excl_tpm"])
    o = {"has_floor": _floor_fraction() is not None, "has_counter": _has_clamp_counter(probe)}
    if not (o["has_floor"] and o["has_counter"]):
        return o
    blocked = S.T(input=SPEC["excl_est_in"], output=SPEC["excl_est_out"])
    clock = S.Clock(SPEC["excl_t0"])
    refilled = S.tracker(max_requests_per_minute=SPEC["excl_rpm"],
                         max_tokens_per_minute=SPEC["excl_tpm"], capacity_clock=clock)
    refilled.consume_capacity(blocked)
    clock.now = SPEC["excl_t0"] + SPEC["excl_dt"]
    refilled.update_capacity()
    o["refilled"] = [refilled.available_token_capacity, refilled.available_request_capacity,
                     _clamp_count(refilled)]
    released = S.tracker(max_requests_per_minute=SPEC["excl_rpm"], max_tokens_per_minute=SPEC["excl_tpm"])
    released.free_capacity(used=S.T(input=0, output=0), blocked=blocked)
    o["released"] = [released.available_token_capacity, _clamp_count(released)]
    settled = S.tracker(max_requests_per_minute=SPEC["excl_rpm"], max_tokens_per_minute=SPEC["excl_tpm"])
    settled.consume_capacity(blocked)
    settled.free_capacity(used=S.T(input=SPEC["excl_settle_used"], output=0), blocked=blocked)
    o["settled"] = [settled.available_token_capacity, _clamp_count(settled)]
    return o


def probe_r1_observability() -> dict:
    probe = S.tracker(max_requests_per_minute=SPEC["r1_obs_rpm"],
                      max_tokens_per_minute=SPEC["r1_obs_in_limit"])
    o = {"has_counter": _has_clamp_counter(probe)}
    if not o["has_counter"]:
        return o
    sep = _seed_full(S.tracker(token_limit_strategy=S.budget_module().TokenLimitStrategy.seperate,
                               max_requests_per_minute=SPEC["r1_obs_rpm"],
                               max_tokens_per_minute=S.T(input=SPEC["r1_obs_in_limit"],
                                                         output=SPEC["r1_obs_out_limit"])))
    blocked = S.T(input=SPEC["r1_obs_est_in"], output=SPEC["r1_obs_est_out"])
    initial = _clamp_count(sep)
    sep.consume_capacity(blocked)
    after_consume = _clamp_count(sep)
    sep.free_capacity(used=S.T(input=SPEC["r1_obs_used1_in"], output=SPEC["r1_obs_used1_out"]),
                      blocked=blocked)
    after_first = _clamp_count(sep)
    sep.free_capacity(used=S.T(input=SPEC["r1_obs_used2_in"], output=SPEC["r1_obs_used2_out"]),
                      blocked=S.T(input=0, output=0))
    after_second = _clamp_count(sep)
    o["counts"] = [initial, after_consume, after_first, after_second]
    return o


# ---------------------------------------------------------------------------
# r2 — settlement vs refund
# ---------------------------------------------------------------------------
def probe_r2_rule() -> dict:
    blocked = S.T(input=SPEC["r2_rule_est_in"], output=SPEC["r2_rule_est_out"])
    refunded = S.tracker(max_requests_per_minute=SPEC["r2_rule_rpm"],
                         max_tokens_per_minute=SPEC["r2_rule_tpm"])
    refunded.consume_capacity(blocked)
    o = {"after_consume": [refunded.available_request_capacity, refunded.available_token_capacity],
         "has_refund": _refund_op(refunded) is not None}
    if not o["has_refund"]:
        return o
    op = _refund_op(refunded)
    op(blocked)
    o["after_refund"] = [refunded.available_request_capacity, refunded.available_token_capacity]
    op(blocked)
    o["after_refund2"] = [refunded.available_request_capacity, refunded.available_token_capacity]

    settled = S.tracker(max_requests_per_minute=SPEC["r2_rule_rpm"],
                        max_tokens_per_minute=SPEC["r2_rule_tpm"])
    settled.consume_capacity(blocked)
    settled.free_capacity(used=S.T(input=SPEC["r2_rule_used_in"], output=SPEC["r2_rule_used_out"]),
                          blocked=blocked)
    o["settled"] = [settled.available_token_capacity, settled.available_request_capacity]

    proc = S.StubProcessor(S.T(input=SPEC["r2_rule_est_in"], output=SPEC["r2_rule_est_out"]))
    delegated = S.tracker(max_requests_per_minute=SPEC["r2_rule_rpm"],
                          max_tokens_per_minute=SPEC["r2_rule_tpm"])
    reserved = proc._reserve_capacity(delegated, [])
    o["delegated_reserve"] = [delegated.available_request_capacity, delegated.available_token_capacity]
    proc._refund_capacity(delegated, reserved)
    o["delegated_refund"] = [delegated.available_request_capacity, delegated.available_token_capacity]
    return o


def probe_r2_scope() -> dict:
    estimate = S.T(input=SPEC["r2_scope_est_in"], output=SPEC["r2_scope_est_out"])

    def reserve():
        proc = S.StubProcessor(estimate)
        t = S.tracker(max_requests_per_minute=SPEC["r2_scope_rpm"],
                      max_tokens_per_minute=SPEC["r2_scope_tpm"])
        blocked = proc._reserve_capacity(t, [])
        return proc, t, blocked

    proc, exhausted, blocked = reserve()
    reserve_state = [exhausted.available_request_capacity, exhausted.available_token_capacity]
    S.run_attempt(proc, exhausted, blocked, attempts_left=0,
                  response=S.make_response("length", estimate))
    exhausted_state = [exhausted.available_request_capacity, exhausted.available_token_capacity]

    proc, requeued, blocked = reserve()
    request = S.run_attempt(proc, requeued, blocked, attempts_left=1,
                            response=S.make_response("length", estimate))
    requeued_state = [request.attempts_left, requeued.available_request_capacity,
                      requeued.available_token_capacity]

    proc, succeeded, blocked = reserve()
    S.run_attempt(proc, succeeded, blocked, attempts_left=1,
                  response=S.make_response("stop", S.T(input=SPEC["r2_scope_est_in"],
                                                       output=SPEC["r2_scope_used_out"])))
    success_state = [succeeded.available_request_capacity, succeeded.available_token_capacity]

    return {"reserve_state": reserve_state, "exhausted": exhausted_state,
            "requeued": requeued_state, "success": success_state}


def probe_r2_exclusions() -> dict:
    proc = S.StubProcessor(S.T(input=SPEC["r2_excl_est_in"], output=SPEC["r2_excl_est_out"]))
    t = S.tracker(max_requests_per_minute=SPEC["r2_excl_rpm"],
                  max_tokens_per_minute=SPEC["r2_excl_tpm"])
    blocked = proc._reserve_capacity(t, [])
    o = {"blocked_axes": list(S.token_axes(blocked)),
         "after_reserve": [t.available_request_capacity, t.available_token_capacity]}
    S.run_attempt(proc, t, blocked, attempts_left=0,
                  response=S.make_response("length", S.T(input=SPEC["r2_excl_est_in"],
                                                         output=SPEC["r2_excl_resp_out"])))
    o["final"] = [t.available_token_capacity, t.available_request_capacity]
    return o


def probe_r2_observability() -> dict:
    blocked = S.T(input=SPEC["r2_obs_est_in"], output=SPEC["r2_obs_est_out"])
    settled = S.tracker(max_requests_per_minute=SPEC["r2_obs_rpm"],
                        max_tokens_per_minute=SPEC["r2_obs_tpm"])
    o = {"has_refund": _refund_op(settled) is not None}
    if not o["has_refund"]:
        return o
    o["initial"] = [_settlements(settled), _refunds(settled)]
    settled.consume_capacity(blocked)
    o["after_consume"] = [_settlements(settled), _refunds(settled)]
    settled.free_capacity(used=S.T(input=SPEC["r2_obs_used_in"], output=SPEC["r2_obs_used_out"]),
                          blocked=blocked)
    o["after_free"] = [_settlements(settled), _refunds(settled)]

    refunded = S.tracker(max_requests_per_minute=SPEC["r2_obs_rpm"],
                         max_tokens_per_minute=SPEC["r2_obs_tpm"])
    refunded.consume_capacity(blocked)
    _refund_op(refunded)(blocked)
    o["refunded"] = [_settlements(refunded), _refunds(refunded)]

    unlimited = S.tracker(max_requests_per_minute=None, max_tokens_per_minute=None)
    unlimited.free_capacity(used=S.T(input=SPEC["r2_obs_unlimited_used_in"],
                                     output=SPEC["r2_obs_unlimited_used_out"]),
                            blocked=S.T(input=SPEC["r2_obs_unlimited_blocked"],
                                        output=SPEC["r2_obs_unlimited_blocked"]))
    _refund_op(unlimited)(S.T(input=SPEC["r2_obs_unlimited_blocked"],
                              output=SPEC["r2_obs_unlimited_blocked"]))
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


def main(out_path: str, seed: str, artifacts: str) -> int:
    """`artifacts` is the root-readable scenario directory `run_split` hands both
    processes. This suite's scenarios are trackers and stub processors in memory
    — no file is an observation here — so the directory is accepted and left
    empty rather than half-used.
    """
    global SPEC
    SPEC = fixture_spec.derive(seed)

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
    code = main(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.stdout.flush()
    sys.stderr.flush()
    _EXIT(code)
