"""g6 worker: the ONLY process that imports the submission.

Runs as `nobody`. For each graded test it reproduces exactly the curator calls
that test makes and writes the resulting values — never a pass/fail — to the
observations file named on argv. `judge.py`, which never imports the submission
and which the grading uid cannot even read (test.sh locks /tests to root), turns
those values into the verdict. This is the split that closes the forgery in
`tasks/lessons.md` (2026-09-09): a uid cannot stop imported agent code from
rewriting a report its own process produces, so the process that imports the
code no longer produces the report — and the numbers it would have to forge to
pass live only in the judge it cannot read.

The curator-facing halves are lifted from `test_open`/`test_r1`/`test_r2`, same
helpers (via `probe_support`, which carries the answer-free ones), so a value
here is the value the test saw. The judge holds the assertions those tests made:
the three reason strings, the resolved prices, the discount multiplier and the
price ratios. A submission that returns forged values only forges values the
judge still checks against the real expectations — which is implementing them.
Floats go through `json` (float encoding is `repr`), so every value round-trips
to the identical double and the judge's exact `==`/approx mean what they meant
in-process.
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

# probe_support owns the curator imports and the answer-free scenario helpers;
# reuse them so a probe calls curator exactly as the test does. Importing it (and
# the calls below) runs the submission's `import bespokelabs.curator` — this
# process's whole purpose, and why it is disposable.
import pytest  # noqa: E402

import probe_support as S  # noqa: E402
from harness import read_field  # noqa: E402


def raises(fn, *args, **kwargs) -> dict:
    """Call `fn`, reporting whether it raised, its class chain, message, and the
    `reason`/model/provider/completion_window an UnpricedModelError carries."""
    try:
        fn(*args, **kwargs)
    except BaseException as exc:  # noqa: BLE001 - the test catches a type; the judge checks which
        info = {"raised": True, "mro": [c.__name__ for c in type(exc).__mro__],
                "str": str(exc)}
        for attr in ("reason", "model", "provider", "completion_window"):
            if hasattr(exc, attr):
                info[attr] = getattr(exc, attr)
        return info
    return {"raised": False, "mro": []}


# ---------------------------------------------------------------------------
# open feature — the whole stated surface (one fact)
# ---------------------------------------------------------------------------
def probe_open() -> dict:
    import dataclasses

    ModelPrice, UnpricedModelError, resolve_model_price = S.require_cost(
        "ModelPrice", "UnpricedModelError", "resolve_model_price")
    register_price_with_litellm, format_cost_strings, external_model_cost = S.require_cost(
        "register_price_with_litellm", "format_cost_strings", "external_model_cost")

    o: dict = {}

    # --- the return shape ---------------------------------------------------
    o["is_dataclass"] = bool(dataclasses.is_dataclass(ModelPrice))
    o["frozen"] = bool(ModelPrice.__dataclass_params__.frozen)
    o["fields"] = sorted(f.name for f in dataclasses.fields(ModelPrice))

    # --- the failure shape --------------------------------------------------
    o["is_lookup_error"] = issubclass(UnpricedModelError, LookupError)
    o["reasons_is_frozenset"] = isinstance(UnpricedModelError.REASONS, frozenset)
    # The reason is read live from the submission and NEVER pinned (pinning it
    # made this grade a hidden fact; see test_open). The judge rebuilds its
    # expected string from this recorded value.
    reason = sorted(UnpricedModelError.REASONS)[0]
    err = UnpricedModelError(model="ghost", provider="klusterai", completion_window="24h", reason=reason)
    o["reason"] = reason
    o["err_str"] = str(err)
    o["err_tuple"] = [err.model, err.provider, err.completion_window, err.reason]
    o["bad_reason_raises"] = raises(
        UnpricedModelError, model="m", provider=None, completion_window="*", reason="not_a_declared_reason")

    with S.pricing_sandbox():
        # --- the lookup itself ---------------------------------------------
        price = resolve_model_price(S.MAVERICK, provider="klusterai", completion_window="*")
        o["price_isinstance"] = isinstance(price, ModelPrice)
        o["price_fields"] = S.price_fields(price)
        o["price_in_per_token"] = price.input_cost_per_token
        o["price_out_per_token"] = price.output_cost_per_token

        inferred = resolve_model_price(S.INFNET_8B, provider="inference.net", completion_window="24h")
        o["inferred_per_million"] = [read_field(inferred, "input_cost_per_million"),
                                     read_field(inferred, "output_cost_per_million")]
        o["inferred_price_inferred"] = read_field(inferred, "output_price_inferred")

        # --- the back-compat shim ------------------------------------------
        o["external_model_cost"] = external_model_cost(S.INFNET_8B, "24h", "inference.net")
        o["has_get_litellm_cost_map"] = hasattr(S.cost_mod, "_get_litellm_cost_map")

        # --- the single writer into litellm's table ------------------------
        entry = register_price_with_litellm(price)
        o["entry_keys"] = sorted(entry)
        o["entry_in_per_token"] = entry["input_cost_per_token"]
        o["entry_out_per_token"] = entry["output_cost_per_token"]
        o["table_in_per_token"] = S.litellm.model_cost[S.MAVERICK]["input_cost_per_token"]
        o["table_out_per_token"] = S.litellm.model_cost[S.MAVERICK]["output_cost_per_token"]
        o["register_batch_raises"] = raises(
            register_price_with_litellm,
            resolve_model_price(S.MAVERICK, provider="klusterai", completion_window="*", batch=True))

    # --- the single formatter ----------------------------------------------
    with S.pricing_sandbox():
        o["fmt_price_plain"] = list(format_cost_strings(price, rich=False))
        o["fmt_price_rich"] = list(format_cost_strings(price, rich=True))
        o["fmt_inferred_plain"] = list(format_cost_strings(inferred, rich=False))
        inferred_rich = format_cost_strings(inferred, rich=True)
        o["fmt_inferred_rich"] = list(inferred_rich)
        o["fmt_none_plain"] = list(format_cost_strings(None, rich=False))
        o["fmt_none_rich"] = list(format_cost_strings(None, rich=True))

    # --- both trackers gained the same two fields and the same method -------
    from bespokelabs.curator.status_tracker.batch_status_tracker import BatchStatusTracker
    from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker

    with S.pricing_sandbox():
        batch_tracker = BatchStatusTracker(model=S.INFNET_8B, compatible_provider="inference.net", completion_window="24h")
        inferred_online = OnlineStatusTracker(model=S.INFNET_8B, compatible_provider="inference.net")
        known_online = OnlineStatusTracker(model=S.MAVERICK, compatible_provider="klusterai")
        trackers = {"batch": batch_tracker, "inferred_online": inferred_online, "known_online": known_online}
        o["trackers"] = {}
        for label, tracker in trackers.items():
            o["trackers"][label] = {
                "refresh_callable": callable(getattr(tracker, "refresh_model_price", None)),
                "reason": read_field(tracker, "price_unavailable_reason"),
                "refresh_result_is_none": tracker.refresh_model_price() is None,
                "output_price_inferred": read_field(tracker, "output_price_inferred"),
            }
        o["inferred_online_per_million"] = [inferred_online.input_cost_per_million, inferred_online.output_cost_per_million]
        o["inferred_online_str"] = [inferred_online.input_cost_str, inferred_online.output_cost_str]
        o["known_online_per_million"] = [known_online.input_cost_per_million, known_online.output_cost_per_million]
        o["known_online_str"] = [known_online.input_cost_str, known_online.output_cost_str]
    return o


# ---------------------------------------------------------------------------
# r1 — the failure contract of resolve_model_price
# ---------------------------------------------------------------------------
def probe_r1_rule() -> dict:
    from bespokelabs.curator.request_processor import _DEFAULT_COST_MAP

    resolve_model_price, UnpricedModelError = S.require_cost("resolve_model_price", "UnpricedModelError")
    o: dict = {"reasons": sorted(UnpricedModelError.REASONS)}

    with S.pricing_sandbox():
        rows = {}
        checked = 0
        for provider, table in _DEFAULT_COST_MAP["external"]["providers"].items():
            for model, entry in table["cost"].items():
                for window in entry["input_cost_per_million"]:
                    price = resolve_model_price(model, provider=provider, completion_window=window)
                    rows[f"{provider}/{model}/{window}"] = [read_field(price, "input_cost_per_million"),
                                                            read_field(price, "output_cost_per_million")]
                    checked += 1
        o["rows"] = rows
        o["checked"] = checked

        unanswerable = [
            dict(model="ghost-model", provider="a-provider-nobody-registered"),
            dict(model="ghost-model", provider="klusterai"),
            dict(model=S.MAVERICK, provider="klusterai", completion_window="96h"),
            dict(model="ghost-model"),
        ]
        seen = []
        for call in unanswerable:
            seen.append(raises(resolve_model_price, call.pop("model"), **call))
        o["unanswerable"] = seen
    return o


def probe_r1_exclusions() -> dict:
    resolve_model_price = S.require_cost("resolve_model_price")
    o: dict = {}

    with S.pricing_sandbox():
        o["all_wrong"] = raises(resolve_model_price, "ghost-model",
                                provider="a-provider-nobody-registered", completion_window="99h")
        o["model_wrong"] = raises(resolve_model_price, "ghost-model",
                                  provider="inference.net", completion_window="99h")

    # A litellm row present but unpriced is a failed lookup, not a None-priced
    # success. `broken` is a fake INPUT table, not an answer.
    broken = {
        "g6-null-priced": {"input_cost_per_token": None, "output_cost_per_token": 4e-06, "max_tokens": 4096},
        "g6-unpriced": {"max_tokens": 4096, "litellm_provider": "openai"},
    }
    with S.pricing_sandbox(add=broken):
        o["broken"] = {name: raises(resolve_model_price, name) for name in broken}

    with S.pricing_sandbox():
        o["wildcard"] = read_field(resolve_model_price(S.INFNET_8B, provider="inference.net", completion_window="*"),
                                   "input_cost_per_million")
        o["unlisted_window"] = raises(resolve_model_price, S.INFNET_8B,
                                      provider="inference.net", completion_window="72h")
    return o


def probe_r1_observability() -> dict:
    from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig
    from bespokelabs.curator.status_tracker.batch_status_tracker import BatchStatusTracker
    from bespokelabs.curator.status_tracker.online_status_tracker import OnlineStatusTracker

    resolve_model_price, UnpricedModelError = S.require_cost("resolve_model_price", "UnpricedModelError")
    litellm_proc, kluster_proc, infnet_proc, azure_proc = S.require_cost(
        "_LitellmCostProcessor", "_KlusterAICostProcessor", "_InferenceNetCostProcessor", "_AzureCostProcessor")

    o: dict = {}
    with S.pricing_sandbox():
        seen = []
        for call in (
            dict(model="no-such-model", provider="not-a-provider", completion_window="96h"),
            dict(model="no-such-model", provider="klusterai", completion_window="96h"),
            dict(model=S.DEEPSEEK, provider="klusterai", completion_window="96h"),
        ):
            info = raises(resolve_model_price, call.pop("model"), **call)
            seen.append(info.get("reason"))
        o["seen"] = seen

    with S.pricing_sandbox():
        config = BatchRequestProcessorConfig(model="ghost-model", completion_window="24h")
        costs = []
        for processor_cls in (litellm_proc, kluster_proc, infnet_proc, azure_proc):
            for batch in (False, True):
                processor = processor_cls(config=config, batch=batch)
                costs.append([processor_cls.__name__, batch,
                              processor.cost(completion_window="24h", prompt="a", completion="b")])
        o["degraded_costs"] = costs

    with S.pricing_sandbox():
        batch_tracker = BatchStatusTracker(model="ghost-model", compatible_provider="klusterai", completion_window="24h")
        online_tracker = OnlineStatusTracker(model="ghost-model", compatible_provider="klusterai")
        o["trackers"] = {}
        for label, tracker in (("batch", batch_tracker), ("online", online_tracker)):
            before = [tracker.input_cost_per_million, tracker.output_cost_per_million]
            reason_before = read_field(tracker, "price_unavailable_reason")
            tracker.refresh_model_price(price_model="also-a-ghost")
            o["trackers"][label] = {
                "before": before,
                "reason_before": reason_before,
                "after": [tracker.input_cost_per_million, tracker.output_cost_per_million],
                "reason_after": read_field(tracker, "price_unavailable_reason"),
            }
    return o


# ---------------------------------------------------------------------------
# r2 — one owner of the batch discount
# ---------------------------------------------------------------------------
def probe_r2_rule() -> dict:
    from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig

    base_cls, kluster_cls, infnet_cls, azure_cls = S.processors()
    resolve_model_price = S.require_cost("resolve_model_price")
    o: dict = {}

    with S.pricing_sandbox(add=S.LITELLM_ENTRY):
        with pytest.MonkeyPatch.context() as monkeypatch:
            raw = S.fixed_completion_cost(monkeypatch)
            o["raw"] = raw
            cases = [
                (base_cls, S.LITELLM_MODEL, "*"),
                (azure_cls, S.LITELLM_MODEL, "*"),
                (kluster_cls, S.MAVERICK, "*"),
                (infnet_cls, S.INFNET_8B, "24h"),
            ]
            cases = [c for c in cases if c[0] is not infnet_cls]

            per_case = []
            for processor_cls, model, window in cases:
                config = BatchRequestProcessorConfig(model=model, completion_window=window)
                for batch in (False, True):
                    processor = processor_cls(config=config, batch=batch)
                    per_case.append([processor_cls.__name__, batch,
                                     S.multiplier(processor),
                                     processor.cost(completion_window=window, prompt="a", completion="b")])
            o["applied_once"] = per_case

            substitution = []
            for processor_cls, model, window in cases:
                config = BatchRequestProcessorConfig(model=model, completion_window=window)
                processor = processor_cls(config=config, batch=True)
                before = processor.cost(completion_window=window, prompt="a", completion="b")
                factor_before = S.multiplier(processor)
                monkeypatch.setattr(processor, "batch_multiplier", lambda *a, **k: 3.0)
                after = processor.cost(completion_window=window, prompt="a", completion="b")
                substitution.append([processor_cls.__name__, before, factor_before, after])
            o["substitution"] = substitution

        factor = S.multiplier(base_cls(config=BatchRequestProcessorConfig(model=S.LITELLM_MODEL), batch=True))
        o["factor"] = factor
        o["listed"] = read_field(resolve_model_price(S.LITELLM_MODEL, batch=False), "input_cost_per_million")
        o["discounted"] = read_field(resolve_model_price(S.LITELLM_MODEL, batch=True), "input_cost_per_million")
    return o


def probe_r2_scope() -> dict:
    from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig

    base_cls, kluster_cls, infnet_cls, azure_cls = S.processors()
    resolve_model_price = S.require_cost("resolve_model_price")
    o: dict = {}

    with S.pricing_sandbox(add=S.LITELLM_ENTRY):
        config = BatchRequestProcessorConfig(model=S.LITELLM_MODEL)
        factor = S.multiplier(base_cls(config=config, batch=True))
        o["factor"] = factor

        o["out_of_batch"] = [[cls.__name__, S.multiplier(cls(config=config, batch=False))]
                             for cls in (base_cls, kluster_cls, infnet_cls, azure_cls)]
        o["azure_batch"] = S.multiplier(azure_cls(config=config, batch=True))
        o["external_batch"] = [[cls.__name__, batch, S.multiplier(cls(config=config, batch=batch))]
                               for cls in (kluster_cls, infnet_cls) for batch in (False, True)]

        external_rows = [
            (S.MAVERICK, "klusterai", "*"),
            (S.MAVERICK, "klusterai", "24h"),
            (S.DEEPSEEK, "klusterai", "72h"),
            (S.INFNET_8B, "inference.net", "24h"),
        ]
        rows = []
        for model, provider, window in external_rows:
            listed = resolve_model_price(model, provider=provider, completion_window=window, batch=False)
            batched = resolve_model_price(model, provider=provider, completion_window=window, batch=True)
            rows.append({
                "key": f"{provider}/{model}/{window}",
                "source": read_field(batched, "source"),
                "listed": [read_field(listed, "input_cost_per_million"), read_field(listed, "output_cost_per_million")],
                "batched": [read_field(batched, "input_cost_per_million"), read_field(batched, "output_cost_per_million")],
            })
        o["external_rows"] = rows

        listed = resolve_model_price(S.LITELLM_MODEL, batch=False)
        batched = resolve_model_price(S.LITELLM_MODEL, batch=True)
        o["litellm_source"] = read_field(batched, "source")
        o["litellm_listed"] = [read_field(listed, "input_cost_per_million"), read_field(listed, "output_cost_per_million")]
        o["litellm_batched"] = [read_field(batched, "input_cost_per_million"), read_field(batched, "output_cost_per_million")]
    return o


def probe_r2_exclusions() -> dict:
    from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig

    base_cls, kluster_cls, infnet_cls, azure_cls = S.processors()
    resolve_model_price = S.require_cost("resolve_model_price")
    o: dict = {}

    with S.pricing_sandbox(add=S.LITELLM_ENTRY):
        with pytest.MonkeyPatch.context() as monkeypatch:
            raw = S.fixed_completion_cost(monkeypatch)
            o["raw"] = raw
            supplied = BatchRequestProcessorConfig(model=S.LITELLM_MODEL, in_mtok_cost=3)
            user_supplied = []
            for processor_cls in (base_cls, azure_cls):
                processor = processor_cls(config=supplied, batch=True)
                user_supplied.append([processor_cls.__name__, S.multiplier(processor),
                                      processor.cost(completion_window="*", prompt="a", completion="b")])
            o["user_supplied"] = user_supplied

        config = BatchRequestProcessorConfig(model=S.LITELLM_MODEL)
        factor = S.multiplier(base_cls(config=config, batch=True))
        o["factor"] = factor
        found = S.discount_flag_name()
        if found is None:
            o["flag"] = None
            o["has_overrides"] = ("batch_multiplier" in vars(kluster_cls)
                                  and "batch_multiplier" in vars(infnet_cls))
        else:
            flag, applies = found
            o["flag"] = flag
            exempt = type("_G6Exempt", (base_cls,), {flag: not applies})
            o["exempt_mult"] = S.multiplier(exempt(config=config, batch=True))
            discounting = type("_G6Discounting", (kluster_cls,), {flag: applies})
            o["discounting_mult"] = S.multiplier(discounting(config=config, batch=True))

        with S.pricing_sandbox(add={S.DEEPSEEK: {"input_cost_per_token": 9e-06, "output_cost_per_token": 9e-06, "max_tokens": 4096}}):
            listed = resolve_model_price(S.DEEPSEEK, batch=False)
            batched = resolve_model_price(S.DEEPSEEK, batch=True)
            o["deepseek_source"] = read_field(listed, "source")
            o["deepseek_listed_in"] = read_field(listed, "input_cost_per_million")
            o["deepseek_batched_in"] = read_field(batched, "input_cost_per_million")
    return o


def probe_r2_observability() -> dict:
    from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig

    base_cls, kluster_cls, infnet_cls, azure_cls = S.processors()
    resolve_model_price = S.require_cost("resolve_model_price")
    o: dict = {}

    with S.pricing_sandbox(add=S.LITELLM_ENTRY):
        config = BatchRequestProcessorConfig(model=S.LITELLM_MODEL)
        o["multipliers"] = [
            S.multiplier(base_cls(config=config, batch=True)),
            S.multiplier(base_cls(config=config, batch=False)),
            S.multiplier(azure_cls(config=config, batch=True)),
            S.multiplier(azure_cls(config=config, batch=False)),
            S.multiplier(kluster_cls(config=config, batch=True)),
            S.multiplier(infnet_cls(config=config, batch=True)),
        ]

        with pytest.MonkeyPatch.context() as monkeypatch:
            raw = S.fixed_completion_cost(monkeypatch)
            o["raw"] = raw
            kluster_config = BatchRequestProcessorConfig(model=S.MAVERICK, completion_window="*")
            o["kluster_in_batch"] = kluster_cls(config=kluster_config, batch=True).cost(completion_window="*", prompt="a", completion="b")
            o["kluster_out_of_batch"] = kluster_cls(config=kluster_config, batch=False).cost(completion_window="*", prompt="a", completion="b")

        o["deepseek_listed"] = read_field(resolve_model_price(S.DEEPSEEK, provider="klusterai", completion_window="*", batch=False), "input_cost_per_million")
        o["deepseek_batched"] = read_field(resolve_model_price(S.DEEPSEEK, provider="klusterai", completion_window="*", batch=True), "input_cost_per_million")

        o["litellm_listed_in"] = read_field(resolve_model_price(S.LITELLM_MODEL, batch=False), "input_cost_per_million")
        o["litellm_batched_in"] = read_field(resolve_model_price(S.LITELLM_MODEL, batch=True), "input_cost_per_million")
        o["litellm_batched_out"] = read_field(resolve_model_price(S.LITELLM_MODEL, batch=True), "output_cost_per_million")
    return o


# name -> (classname, probe). classname/name reproduce the current junit nodes so
# score.fold maps them to the identical fact keys.
PROBES = {
    "test_open::test_open_feature__one_resolve_model_price_backs_the_price_the_error_the_registration_and_the_strings": probe_open,
    "test_r1::test_rule__a_failure_always_raises_one_of_three_named_reasons_instead_of_a_none_price": probe_r1_rule,
    "test_r1::test_exclusions__the_earlier_check_wins_and_neither_a_none_price_nor_a_wildcard_fallback_is_offered": probe_r1_exclusions,
    "test_r1::test_observability__the_three_reasons_read_back_and_every_caller_above_the_lookup_degrades": probe_r1_observability,
    "test_r2::test_rule__the_discount_is_applied_once_by_batch_multiplier_and_by_resolve_model_price": probe_r2_rule,
    "test_r2::test_scope__only_list_priced_sources_are_discounted_and_the_external_tables_are_left_alone": probe_r2_scope,
    "test_r2::test_exclusions__a_user_supplied_price_is_taken_as_given_and_exemption_follows_the_class_and_the_source": probe_r2_exclusions,
    "test_r2::test_observability__the_stated_multiplier_table_and_the_two_price_ratios_hold_exactly": probe_r2_observability,
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
