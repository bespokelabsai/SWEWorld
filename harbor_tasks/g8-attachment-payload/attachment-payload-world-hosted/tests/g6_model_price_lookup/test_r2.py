"""g6 — hidden requirement r2: one owner of the batch discount.

    rule       the discount is applied by exactly one method, `batch_multiplier()`, and
               nothing downstream multiplies or divides again: a `cost()` is its raw
               litellm figure times that method's return value, whatever it returns; and
               `resolve_model_price(batch=True)` applies the very same factor
    scope      the factor is returned only where the pricing data is a list price — never
               out of batch mode, never on klusterai or inference.net — and symmetrically
               `resolve_model_price` discounts a litellm-sourced price and leaves an
               external one exactly as the table lists it
    exclusions a user-supplied per-million price is taken as given and never discounted,
               and the exemption is driven by a class-level flag and by which source
               answered the lookup, not by matching a provider name at the point of use
    observability the literal table: 0.5 on the base and Azure processors in batch mode,
               1.0 everywhere else, and the two `resolve_model_price` ratios

`rule` and `scope` are written in terms of the factor the implementation returns rather
than the number `0.5`, so that `observability` — which pins the number — is the only test
that fails when the discount is the wrong size but correctly owned.
"""
from __future__ import annotations

import pytest

from harness import read_field, require_feature

from test_open import DEEPSEEK, INFNET_8B, MAVERICK, pricing_sandbox, require_cost

try:
    import litellm
except Exception:  # pragma: no cover
    litellm = None

try:
    from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig
except Exception:  # pragma: no cover
    BatchRequestProcessorConfig = None

# A model that exists only in litellm's table, so that "litellm-sourced" is unambiguous.
LITELLM_MODEL = "g6-litellm-priced-model"
LITELLM_ENTRY = {
    LITELLM_MODEL: {"input_cost_per_token": 2e-06, "output_cost_per_token": 8e-06, "max_tokens": 4096, "litellm_provider": "openai"},
    f"azure/{LITELLM_MODEL}": {"input_cost_per_token": 2e-06, "output_cost_per_token": 8e-06, "max_tokens": 4096, "litellm_provider": "azure"},
}


def fixed_completion_cost(monkeypatch, value=4.0):
    """Pin litellm's own cost computation, wherever the pricing module reached for it."""
    import bespokelabs.curator.cost as cost_mod

    monkeypatch.setattr(litellm, "completion_cost", lambda **kwargs: value)
    if hasattr(cost_mod, "completion_cost"):
        monkeypatch.setattr(cost_mod, "completion_cost", lambda **kwargs: value)
    return value


def multiplier(processor):
    """`batch_multiplier()` off a processor, or a legible failure when there is none."""
    method = getattr(processor, "batch_multiplier", None)
    if not callable(method):
        pytest.fail(f"{type(processor).__name__} has no callable batch_multiplier(); the batch discount has no single owner")
    return method()


def processors():
    return require_cost("_LitellmCostProcessor", "_KlusterAICostProcessor", "_InferenceNetCostProcessor", "_AzureCostProcessor")


def discount_flag_name():
    """The class-level boolean that says whether a processor's prices are list prices.

    Discovered rather than named, and rather than oriented: r2 says the exemption is
    decided by a class-level flag, not what the flag is called or which way it points.
    A flag spelled `_prices_are_batch_rates` (False on the base, True on the two whose
    tables are already batch tiers) says exactly what `_BATCH_DISCOUNT_APPLIES` says
    with the sign reversed, and a `spec` build wrote it that way -- pinning the
    polarity failed the fact for a build that had satisfied it, which `ships()` reads
    as the requirement not saying what the suite grades.

    Returns (name, applies_value) where `applies_value` is the value meaning "discount
    this class", or None when no such attribute exists.
    """
    base, kluster, infnet, _ = processors()
    for name, value in vars(base).items():
        if name.startswith("__") or not isinstance(value, bool):
            continue
        if getattr(kluster, name, "absent") is (not value) and getattr(infnet, name, "absent") is (not value):
            return name, value
    return None


# =============================================================================
# rule — one applier; a cost is completion_cost * batch_multiplier() and no more
# =============================================================================
def test_rule__the_discount_is_applied_once_by_batch_multiplier_and_by_resolve_model_price():
    base_cls, kluster_cls, infnet_cls, azure_cls = processors()
    resolve_model_price = require_cost("resolve_model_price")

    with pricing_sandbox(add=LITELLM_ENTRY):
        with pytest.MonkeyPatch.context() as monkeypatch:
            raw = fixed_completion_cost(monkeypatch)
            cases = [
                (base_cls, LITELLM_MODEL, "*"),
                (azure_cls, LITELLM_MODEL, "*"),
                (kluster_cls, MAVERICK, "*"),
                (infnet_cls, INFNET_8B, "24h"),
            ]
            # `_InferenceNetCostProcessor` is not among them, and cannot be: pricing it
            # at all needs `whole.md`'s P7 -- the override reads its model from the
            # response while the parent gates on `config.model` -- which no arm but
            # `oracle` is told about, so a correct `spec` degrades it to 0.0 exactly as
            # r1's failure contract instructs. Grading it here failed r2.rule for a build
            # that had the discount ownership right, which `ships()` reads as the
            # requirement not saying what the suite grades. klusterai stays, and it is the
            # other provider that cancelled the discount with `times = 2`, so the claim is
            # still held against the behaviour it exists to catch; inference.net's
            # exemption is graded by r2.scope and r2.exclusions.
            cases = [c for c in cases if c[0] is not infnet_cls]
            for processor_cls, model, window in cases:
                config = BatchRequestProcessorConfig(model=model, completion_window=window)
                for batch in (False, True):
                    processor = processor_cls(config=config, batch=batch)
                    expected = raw * multiplier(processor)
                    actual = processor.cost(completion_window=window, prompt="a", completion="b")
                    assert actual == pytest.approx(expected), f"{processor_cls.__name__}(batch={batch}) is not completion_cost * batch_multiplier()"

            # The method is the ONLY thing standing between the raw figure and the
            # answer: substitute it and the whole answer moves with it, so no override
            # is quietly multiplying or dividing on the way out.
            for processor_cls, model, window in cases:
                config = BatchRequestProcessorConfig(model=model, completion_window=window)
                processor = processor_cls(config=config, batch=True)
                before = processor.cost(completion_window=window, prompt="a", completion="b")  # also lets it register
                factor_before = multiplier(processor)
                assert factor_before, f"{processor_cls.__name__} reports a zero multiplier"
                assert before, f"{processor_cls.__name__} priced at zero; nothing to substitute against"
                monkeypatch.setattr(processor, "batch_multiplier", lambda *a, **k: 3.0)
                after = processor.cost(completion_window=window, prompt="a", completion="b")
                # Relative, not absolute: the answer must move exactly as the multiplier
                # moved, whatever the figure it started from. That is the whole of r2's
                # claim -- one owner, nothing else multiplying on the way out.
                assert after == pytest.approx(before / factor_before * 3.0), (
                    f"{processor_cls.__name__} applies something other than batch_multiplier()"
                )

        # `resolve_model_price(batch=True)` applies that same one factor to a
        # litellm-sourced price, rather than a second discount of its own.
        factor = multiplier(base_cls(config=BatchRequestProcessorConfig(model=LITELLM_MODEL), batch=True))
        listed = read_field(resolve_model_price(LITELLM_MODEL, batch=False), "input_cost_per_million")
        discounted = read_field(resolve_model_price(LITELLM_MODEL, batch=True), "input_cost_per_million")
        assert discounted == pytest.approx(listed * factor)


# =============================================================================
# scope — the factor only where the data is a list price
# =============================================================================
def test_scope__only_list_priced_sources_are_discounted_and_the_external_tables_are_left_alone():
    base_cls, kluster_cls, infnet_cls, azure_cls = processors()
    resolve_model_price = require_cost("resolve_model_price")

    with pricing_sandbox(add=LITELLM_ENTRY):
        config = BatchRequestProcessorConfig(model=LITELLM_MODEL)
        factor = multiplier(base_cls(config=config, batch=True))
        assert 0.0 < factor < 1.0, f"the batch discount factor is {factor!r}"

        # Out of batch mode nothing is discounted, on any processor.
        for processor_cls in (base_cls, kluster_cls, infnet_cls, azure_cls):
            assert multiplier(processor_cls(config=config, batch=False)) == 1.0, processor_cls.__name__

        # In batch mode the two list-priced processors discount ...
        assert multiplier(azure_cls(config=config, batch=True)) == factor

        # ... and the two whose external tables already list batch tiers do not, in
        # either mode.
        for processor_cls in (kluster_cls, infnet_cls):
            for batch in (False, True):
                assert multiplier(processor_cls(config=config, batch=batch)) == 1.0, f"{processor_cls.__name__}(batch={batch})"

        # Symmetrically in the lookup: an external row comes back exactly as listed ...
        external_rows = [
            (MAVERICK, "klusterai", "*"),
            (MAVERICK, "klusterai", "24h"),
            (DEEPSEEK, "klusterai", "72h"),
            (INFNET_8B, "inference.net", "24h"),
        ]
        for model, provider, window in external_rows:
            listed = resolve_model_price(model, provider=provider, completion_window=window, batch=False)
            batched = resolve_model_price(model, provider=provider, completion_window=window, batch=True)
            assert read_field(batched, "source") == "external"
            for field in ("input_cost_per_million", "output_cost_per_million"):
                assert read_field(batched, field) == read_field(listed, field), f"{provider}/{model}/{window} was discounted on the {field}"

        # ... while a litellm-sourced row is discounted by that one factor.
        listed = resolve_model_price(LITELLM_MODEL, batch=False)
        batched = resolve_model_price(LITELLM_MODEL, batch=True)
        assert read_field(batched, "source") == "litellm"
        for field in ("input_cost_per_million", "output_cost_per_million"):
            assert read_field(batched, field) == pytest.approx(read_field(listed, field) * factor), field


# =============================================================================
# exclusions — a price the user supplied is never discounted, and the exemption
# is a property of the class and of the source, not of a provider spelling
# =============================================================================
def test_exclusions__a_user_supplied_price_is_taken_as_given_and_exemption_follows_the_class_and_the_source():
    base_cls, kluster_cls, infnet_cls, azure_cls = processors()
    resolve_model_price = require_cost("resolve_model_price")

    with pricing_sandbox(add=LITELLM_ENTRY):
        with pytest.MonkeyPatch.context() as monkeypatch:
            raw = fixed_completion_cost(monkeypatch)
            # A processor that WOULD discount, carrying an explicit input price.
            supplied = BatchRequestProcessorConfig(model=LITELLM_MODEL, in_mtok_cost=3)
            for processor_cls in (base_cls, azure_cls):
                processor = processor_cls(config=supplied, batch=True)
                assert multiplier(processor) == 1.0, f"{processor_cls.__name__} discounted a user-supplied price"
                assert processor.cost(completion_window="*", prompt="a", completion="b") == pytest.approx(raw)

        # The exemption is a property of the class. Flip the flag on a fresh subclass of
        # the discounting base and it stops discounting; flip it on a subclass of an
        # exempt processor and it starts — neither of which a provider-name match at the
        # point of use could do.
        config = BatchRequestProcessorConfig(model=LITELLM_MODEL)
        factor = multiplier(base_cls(config=config, batch=True))
        found = discount_flag_name()
        flag, applies = found if found else (None, None)
        if flag is None:
            # No flag: the only other class-level way to say it is an override, which is
            # equally "decided by the class". Anything else is a name match at the point
            # of use, which r2 rules out.
            require_feature(
                "batch_multiplier" in vars(kluster_cls) and "batch_multiplier" in vars(infnet_cls),
                "a class-level flag (or a per-class batch_multiplier override) marking which processors are exempt",
            )
        else:
            exempt = type("_G6Exempt", (base_cls,), {flag: not applies})
            assert multiplier(exempt(config=config, batch=True)) == 1.0
            discounting = type("_G6Discounting", (kluster_cls,), {flag: applies})
            assert multiplier(discounting(config=config, batch=True)) == factor

        # And in the lookup the exemption follows which source answered, not the shape of
        # the model name: a model whose name belongs to an external provider's table is
        # still discounted when litellm is what priced it.
        with pricing_sandbox(add={DEEPSEEK: {"input_cost_per_token": 9e-06, "output_cost_per_token": 9e-06, "max_tokens": 4096}}):
            listed = resolve_model_price(DEEPSEEK, batch=False)
            batched = resolve_model_price(DEEPSEEK, batch=True)
            assert read_field(listed, "source") == "litellm"
            assert read_field(batched, "input_cost_per_million") == pytest.approx(read_field(listed, "input_cost_per_million") * factor)


# =============================================================================
# observability — the stated table of multipliers and ratios
# =============================================================================
def test_observability__the_stated_multiplier_table_and_the_two_price_ratios_hold_exactly():
    base_cls, kluster_cls, infnet_cls, azure_cls = processors()
    resolve_model_price = require_cost("resolve_model_price")

    with pricing_sandbox(add=LITELLM_ENTRY):
        config = BatchRequestProcessorConfig(model=LITELLM_MODEL)
        assert multiplier(base_cls(config=config, batch=True)) == 0.5
        assert multiplier(base_cls(config=config, batch=False)) == 1.0
        assert multiplier(azure_cls(config=config, batch=True)) == 0.5
        assert multiplier(azure_cls(config=config, batch=False)) == 1.0
        assert multiplier(kluster_cls(config=config, batch=True)) == 1.0
        assert multiplier(infnet_cls(config=config, batch=True)) == 1.0

        with pytest.MonkeyPatch.context() as monkeypatch:
            raw = fixed_completion_cost(monkeypatch)
            kluster_config = BatchRequestProcessorConfig(model=MAVERICK, completion_window="*")
            in_batch = kluster_cls(config=kluster_config, batch=True).cost(completion_window="*", prompt="a", completion="b")
            out_of_batch = kluster_cls(config=kluster_config, batch=False).cost(completion_window="*", prompt="a", completion="b")
            assert in_batch == out_of_batch == pytest.approx(raw)

        # DeepSeek-R1's "*" tier is a klusterai batch tier already: 3.0 either way.
        listed = read_field(resolve_model_price(DEEPSEEK, provider="klusterai", completion_window="*", batch=False), "input_cost_per_million")
        batched = read_field(resolve_model_price(DEEPSEEK, provider="klusterai", completion_window="*", batch=True), "input_cost_per_million")
        assert listed == batched == 3.0

        # A litellm-sourced model is halved, exactly.
        assert read_field(resolve_model_price(LITELLM_MODEL, batch=False), "input_cost_per_million") == 2.0
        assert read_field(resolve_model_price(LITELLM_MODEL, batch=True), "input_cost_per_million") == 1.0
        assert read_field(resolve_model_price(LITELLM_MODEL, batch=True), "output_cost_per_million") == 4.0
