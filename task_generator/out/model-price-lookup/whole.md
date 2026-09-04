# Unified model price resolution

## Target

### Files that change

| File | What happens to it |
| --- | --- |
| `src/bespokelabs/curator/cost.py` | Gains `ModelPrice`, `UnpricedModelError`, `resolve_model_price()`, `register_price_with_litellm()`, `format_cost_strings()`. `external_model_cost()` becomes a thin shim over `resolve_model_price()`. `_get_litellm_cost_map()` is deleted. All four `cost()` methods stop doing discount arithmetic and route through `batch_multiplier()`. |
| `src/bespokelabs/curator/status_tracker/batch_status_tracker.py` | `model_post_init()` delegates to a new `refresh_model_price()`; two new fields (`price_unavailable_reason`, `output_price_inferred`); `_format_cost_str()` delegates to `format_cost_strings()`. |
| `src/bespokelabs/curator/status_tracker/online_status_tracker.py` | `__post_init__()` delegates to the same lookup with `batch=False`; same two new fields; cost strings from `format_cost_strings()`. |
| `src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py` | `set_model_cost()` (line 320) stops computing prices; it calls `self.tracker.refresh_model_price()` then `start_tracker`. |
| `src/bespokelabs/curator/request_processor/batch/azure_batch_request_processor.py` | `set_model_cost()` (line 45) uses `refresh_model_price(price_model="azure/…")` and its return value instead of an `in model_cost` membership test. |
| `src/bespokelabs/curator/request_processor/batch/mistral_batch_request_processor.py` | `set_model_cost()` (line 77) likewise with `"mistral/…"`. |
| `src/bespokelabs/curator/request_processor/_default_rate_limits.json` | **Unchanged.** It is the source of truth; the code is what is wrong. |

### Existing machinery that may be REUSED (do not rebuild)

- `_DEFAULT_COST_MAP` from `bespokelabs.curator.request_processor.__init__` (loads `_default_rate_limits.json` at import).
- `litellm.model_cost` (a plain `dict`), `litellm.register_model`, `litellm.completion_cost`.
- `RequestProcessorConfig.in_mtok_cost` / `.out_mtok_cost` (`request_processor/config.py:32-33`).
- `USE_RICH_DISPLAY` from `bespokelabs.curator.log`.
- `BatchStatusTracker` / `OnlineStatusTracker` field sets, `start_tracker(console)`, `cost_info()`.
- `COST_PROCESSOR` / `cost_processor_factory` dispatch table (`cost.py:148-156`) — the mapping itself is fine.
- `_KlusterAICostProcessor._registered_models` / `._wrap()` memoisation keys — keep the `model + "." + completion_window` format.

### What must be BUILT

- `ModelPrice` (frozen dataclass) — the single return shape.
- `UnpricedModelError(LookupError)` — the single failure contract.
- `resolve_model_price()` — the single lookup.
- `register_price_with_litellm()` — the single writer into `litellm.model_cost`.
- `format_cost_strings()` — the single source of the displayed per-million strings.
- `_LitellmCostProcessor.batch_multiplier()` + the `_BATCH_DISCOUNT_APPLIES` class attribute — the single owner of the batch discount.
- `BatchStatusTracker.refresh_model_price()` / `OnlineStatusTracker.refresh_model_price()`.

### Latent bugs this fixes (real, in the checkout)

1. `cost.py:76-77` — reads `input_cost_per_million` and returns it as *both* prices. `output_cost_per_million` is never read, so klusterai `Llama-4-Maverick` output is reported at `0.2`/Mtok instead of `0.8`/Mtok and `DeepSeek-R1` output at `3.0` instead of `5.0`.
2. `cost.py:93` + `cost.py:47` — `times = 2` cancels the parent's `*= 0.5`, so a klusterai/inference.net batch is billed at full price by accident rather than by decision.
3. `cost.py:116-118` vs `cost.py:42` — `_InferenceNetCostProcessor` registers `kwargs["completion_response"]["model"]` but the parent gates on `self.config.model`; when they differ the parent's `if` fails and `cost()` silently returns `0.0`. When neither `completion_response` nor `model` is in `kwargs`, `model` is `None` and `_wrap(None, window)` raises `TypeError`.
4. `base_batch_request_processor.py:325-326` (halves) vs `batch_status_tracker.py:111-122` (does not) — the same model reports a 2x different `input_cost_per_million` depending on whether `requests_to_responses` or `cancel_batches` ran, and that number reaches `CuratorResponse.cost_info`.
5. `batch_status_tracker.py:117-121` passes `completion_window=None` when the tracker was built without one; `None not in {"*", "24h", …}` raises `KeyError`, which the bare `except Exception` at line 124 turns into `None` prices for a model that is fully priced in the table.
6. `base_batch_request_processor.py:328-341` does not catch the `KeyError` that `external_model_cost` raises for an unknown model/window; `set_model_cost()` propagates it out of `requests_to_responses`.
7. `cost.py:55,58` — every externally-priced model is registered into litellm's global table as `max_tokens: 8192, litellm_provider: "openai"`, overwriting the real `max_tokens` (e.g. `1048576` for Maverick).

### Environment

Python `^3.10` (checkout runs on 3.10). Dependencies already present: `litellm==1.83.7`, `pydantic>=2.9.2`, `rich^13.7`, `pytest^8.3.3`. No new dependencies. Everything is a pure function of `_DEFAULT_COST_MAP`, `litellm.model_cost`, and the arguments; no network, no clock, no threads. `time.time` is only touched by the pre-existing `start_time` fields, which the pricing code never reads.

---

## The API

All of the following live in `src/bespokelabs/curator/cost.py`.

```python
_BATCH_DISCOUNT_FACTOR: float = 0.5
_PER_MILLION_NDIGITS: int = 9
_PER_TOKEN_NDIGITS: int = 15


class UnpricedModelError(LookupError):
    """Raised when the price table cannot answer for (model, provider, completion_window)."""

    REASONS: frozenset[str] = frozenset({"unknown_provider", "unknown_model", "unknown_window"})

    model: str
    provider: str | None
    completion_window: str
    reason: str

    def __init__(self, *, model: str, provider: str | None, completion_window: str, reason: str) -> None: ...
```

`__init__` is keyword-only. It asserts nothing about `reason` beyond membership in `REASONS`; if `reason not in REASONS` it raises `ValueError`. The single argument handed to `LookupError.__init__` is exactly:

```python
f"{reason}: model={model!r} provider={provider!r} completion_window={completion_window!r}"
```

so `str(err)` is that string verbatim.

```python
@dataclasses.dataclass(frozen=True)
class ModelPrice:
    model: str                          # the key the price was found under
    provider: str | None                # normalized provider key; None for the litellm path
    completion_window: str              # normalized; never None, never ""
    input_cost_per_million: float       # after the batch multiplier, rounded to 9 dp
    output_cost_per_million: float      # after the batch multiplier, rounded to 9 dp
    source: str                         # "litellm" | "external"
    batch: bool                         # the `batch` argument, echoed
    output_price_inferred: bool         # True iff the output price was copied from the input price
    max_tokens: int | None              # from the table entry; None if the source has no max_tokens

    @property
    def input_cost_per_token(self) -> float: ...   # round(input_cost_per_million / 1e6, 15)

    @property
    def output_cost_per_token(self) -> float: ...  # round(output_cost_per_million / 1e6, 15)


def resolve_model_price(
    model: str,
    *,
    provider: str | None = None,
    completion_window: str | None = None,
    batch: bool = False,
) -> ModelPrice:
    """The one lookup. Raises UnpricedModelError; never returns None-valued prices."""


def register_price_with_litellm(price: ModelPrice) -> dict:
    """Write `price` into litellm.model_cost and return the entry that was written.

    Raises ValueError if `price.batch` is True.
    """


def format_cost_strings(price: ModelPrice | None, *, rich: bool) -> tuple[str, str]:
    """Return (input_cost_str, output_cost_str). The only place display strings are built."""


def external_model_cost(
    model: str,
    completion_window: str = "*",
    provider: str = "default",
) -> dict[str, float]:
    """Back-compat shim. Signature unchanged (positional-friendly).

    Returns {"input_cost_per_token": float, "output_cost_per_token": float}
    with both values taken from resolve_model_price(..., batch=False).
    Never returns None values; raises UnpricedModelError instead.
    """
```

Cost processors:

```python
class _LitellmCostProcessor:
    _BATCH_DISCOUNT_APPLIES: bool = True

    def __init__(self, config, batch: bool = False) -> None: ...
    def batch_multiplier(self) -> float: ...
    def price_model(self, **kwargs) -> str: ...
    def cost(self, *, completion_window: str = "*", **kwargs) -> float: ...


class _KlusterAICostProcessor(_LitellmCostProcessor):
    _BATCH_DISCOUNT_APPLIES: bool = False
    _PROVIDER: str = "klusterai"


class _InferenceNetCostProcessor(_LitellmCostProcessor):
    _BATCH_DISCOUNT_APPLIES: bool = False
    _PROVIDER: str = "inference.net"


class _AzureCostProcessor(_LitellmCostProcessor):
    _BATCH_DISCOUNT_APPLIES: bool = True   # inherited value, stated for clarity
```

Trackers:

```python
class BatchStatusTracker(BaseModel):
    price_unavailable_reason: Optional[str] = Field(default=None)
    output_price_inferred: bool = Field(default=False)

    def refresh_model_price(self, *, price_model: str | None = None) -> Optional[str]:
        """Re-resolve prices from self.model (or `price_model`) and assign
        input_cost_per_million / output_cost_per_million / output_price_inferred /
        price_unavailable_reason / input_cost_str / output_cost_str.

        Returns None on success, or the UnpricedModelError.reason string on failure.
        Never raises UnpricedModelError.
        """


@dataclass
class OnlineStatusTracker:
    price_unavailable_reason: Optional[str] = None
    output_price_inferred: bool = False

    def refresh_model_price(self, *, price_model: str | None = None) -> Optional[str]: ...
```

---

## Parts

### P1 — `ModelPrice` / `UnpricedModelError` shape and numeric normalisation

**Behaviour.** The lookup's only success value is a frozen `ModelPrice` dataclass with the nine fields above in that order, and its only failure value is `UnpricedModelError`, a subclass of `LookupError` that is **not** a subclass of `KeyError`, carrying `.model`, `.provider`, `.completion_window`, `.reason`, a class-level `REASONS` frozenset of exactly `{"unknown_provider", "unknown_model", "unknown_window"}`, and the message string given verbatim above. Every per-million number a `ModelPrice` exposes is `round(value, 9)`; every per-token number is `round(per_million / 1e6, 15)`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the existing `dict[str, float]` with `input_cost_per_token` / `output_cost_per_token` keys as the return shape — it is what all seven call sites already unpack — and keep raising bare `KeyError` (`cost.py:71,74`), since every caller (`online_status_tracker.py:125`, `agent_status_tracker.py:129`) already catches `KeyError`. Subclassing `KeyError` rather than `LookupError` is the conservative choice for exactly that reason.
2. Return a `pydantic.BaseModel` (the trackers are pydantic already) or a `NamedTuple`, expose prices per *token* rather than per *million* (that is the unit `litellm.model_cost` uses and the unit the current function returns), and do no rounding at all — floats are floats.
3. Model failure as a sentinel rather than an exception: return `ModelPrice(input_cost_per_million=None, ...)` or `None`, preserving `cost.py:68`'s "unregistered provider yields Nones" behaviour for every failure instead of just one.

**The observable.**
```python
issubclass(UnpricedModelError, LookupError) is True
issubclass(UnpricedModelError, KeyError) is False
UnpricedModelError.REASONS == frozenset({"unknown_provider", "unknown_model", "unknown_window"})

err = UnpricedModelError(model="ghost", provider="klusterai", completion_window="24h", reason="unknown_model")
str(err) == "unknown_model: model='ghost' provider='klusterai' completion_window='24h'"
(err.model, err.provider, err.completion_window, err.reason) == ("ghost", "klusterai", "24h", "unknown_model")

with pytest.raises(ValueError):
    UnpricedModelError(model="m", provider=None, completion_window="*", reason="not_found")

dataclasses.is_dataclass(ModelPrice) and ModelPrice.__dataclass_params__.frozen is True
[f.name for f in dataclasses.fields(ModelPrice)] == [
    "model", "provider", "completion_window", "input_cost_per_million",
    "output_cost_per_million", "source", "batch", "output_price_inferred", "max_tokens",
]

p = resolve_model_price("meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                        provider="klusterai", completion_window="*")
p.input_cost_per_token == 2e-07      # exactly; not 2.0000000000000002e-07
p.output_cost_per_token == 8e-07     # exactly; not 8.000000000000001e-07
```

**Arbitrary:** invented name (`UnpricedModelError`, `ModelPrice`, `REASONS`, the exact message format) + chosen value (rounding at 9 and 15 digits) + deliberate departure (`LookupError`, not the `KeyError` every existing caller catches).

---

### P2 — Source precedence: a named external provider wins, and does not fall back

**Behaviour.** When `provider` is neither `None` nor `"default"`, `resolve_model_price` reads **only** `_DEFAULT_COST_MAP["external"]["providers"][provider]["cost"]` and never consults `litellm.model_cost`, even if `litellm.model_cost` contains an entry under the same model key; and if that provider's table does not contain the model, it raises rather than falling back to litellm. When `provider` is `None` or `"default"`, it reads **only** `litellm.model_cost`. `source` is `"external"` in the first case and `"litellm"` in the second.

**Alternatives a competent engineer would plausibly choose instead.**
1. litellm first, external second — the order every existing call site uses (`batch_status_tracker.py:109-118`, `online_status_tracker.py:105-119`, `base_batch_request_processor.py:322-341` all test `in model_cost` before touching `external_model_cost`), and the order that makes `_KlusterAICostProcessor.cost()` work today, since it registers into litellm and then lets the parent read litellm back.
2. External first, then fall back to litellm when the provider's table lacks the model — strictly more forgiving, and it means a klusterai deployment of `gpt-4o-mini` still gets a price instead of an exception.
3. Merge: take the input price from whichever source has it and the output price from whichever source has it.

**The observable.** With `litellm.model_cost` monkeypatched to contain `"deepseek-ai/DeepSeek-R1": {"input_cost_per_token": 9e-06, "output_cost_per_token": 9e-06, "max_tokens": 4096}`:
```python
p = resolve_model_price("deepseek-ai/DeepSeek-R1", provider="klusterai", completion_window="*")
(p.input_cost_per_million, p.output_cost_per_million, p.source) == (3.0, 5.0, "external")
p.max_tokens == 163840          # from the JSON table, not litellm's 4096

with pytest.raises(UnpricedModelError) as e:
    resolve_model_price("gpt-4o-mini", provider="klusterai")   # present in litellm.model_cost
e.value.reason == "unknown_model"
```
An implementation that reads litellm first returns `(9.0, 9.0, "litellm")` for the first call; one that falls back returns a `ModelPrice` instead of raising for the second.

**Arbitrary:** deliberate departure — the surrounding code unanimously checks litellm first, and the "no fallback" rule contradicts the instinct to be forgiving.

---

### P3 — The failure contract: three reasons, a fixed check order, and who swallows

**Behaviour.** `resolve_model_price` raises `UnpricedModelError` and never returns a `ModelPrice` with a `None` price. The `reason` is decided in this exact order: `"unknown_provider"` if `provider` is not `None`/`"default"` and is not a key of `_DEFAULT_COST_MAP["external"]["providers"]`; else `"unknown_model"` if the model key is absent from the chosen source, or is present in `litellm.model_cost` but has a missing or `None` `input_cost_per_token`; else `"unknown_window"` if the (normalized) `completion_window` is not a key of that model's `input_cost_per_million` map. `completion_window=None` and `completion_window=""` are both normalized to `"*"` **before** any lookup. The four `cost()` methods and both trackers catch `UnpricedModelError` and degrade (`0.0` and `None` respectively); nothing above `resolve_model_price` re-raises it.

**Alternatives a competent engineer would plausibly choose instead.**
1. Preserve `cost.py:68` exactly: an unregistered provider is not an error, it is "no price known", so return `{None, None}` / a `ModelPrice` with `None` prices, and reserve exceptions for unknown model and unknown window as today.
2. Treat a `None` completion window as the *configured* default `"24h"` (`BatchRequestProcessorConfig.completion_window` defaults to `"24h"`, `config.py:83`) rather than the wildcard `"*"`, or leave it un-normalized and let it raise as it does today.
3. Fall back through windows: if `"48h"` is missing, use `"*"`; a missing window is a data gap, not a user error.

**The observable.**
```python
resolve_model_price("m", provider="not-a-provider").                      # reason "unknown_provider"
resolve_model_price("no-such-model", provider="klusterai").               # reason "unknown_model"
resolve_model_price("deepseek-ai/DeepSeek-R1", provider="klusterai",
                    completion_window="96h").                            # reason "unknown_window"
resolve_model_price("no-such-model")                                     # reason "unknown_model"

# normalization, on data where "*" and the 24h tier differ:
a = resolve_model_price("meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                        provider="klusterai", completion_window=None)
b = resolve_model_price("meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                        provider="klusterai", completion_window="")
a.completion_window == b.completion_window == "*"
a.input_cost_per_million == 0.2      # not 0.25 (the "24h" tier), not None
```
Precedence is pinned by a case where two reasons compete:
```python
resolve_model_price("no-such-model", provider="not-a-provider", completion_window="96h")
# reason == "unknown_provider", not "unknown_model" and not "unknown_window"
resolve_model_price("no-such-model", provider="klusterai", completion_window="96h")
# reason == "unknown_model", not "unknown_window"
```
And the swallow boundary:
```python
_LitellmCostProcessor(config=BatchRequestProcessorConfig(model="totally-unknown"),
                      batch=False).cost(model="totally-unknown", prompt="a", completion="b") == 0.0
```
(no exception — this keeps `tests/unittests/test_batch.py::test_azure_cost_processor_falls_back_without_azure_specific_pricing` green).

**Arbitrary:** policy with no local evidence (the three reason spellings, their precedence order, `None -> "*"` rather than `-> "24h"`, no window fallback) + deliberate departure (`cost.py:68`'s silent `{None, None}` for an unknown provider becomes an exception).

---

### P4 — Output prices are read, and an absent one is marked, not silently mirrored

**Behaviour.** The output price comes from `provider_cost[model]["output_cost_per_million"][window]` (external) or `litellm.model_cost[model]["output_cost_per_token"] * 1e6` (litellm). If that map/key is absent, or its value is `None`, the output price is set equal to the **input price for the same window** and `ModelPrice.output_price_inferred` is set to `True`; whenever a real output price was found, `output_price_inferred` is `False`. An absent output price is never an `UnpricedModelError`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep `cost.py:77`'s behaviour — return the input price as the output price — with no flag at all. It is what the file does today, what `_LitellmCostProcessor.__init__` does at `cost.py:23` for `out_mtok_cost is None`, and it produces identical numbers, so nothing in the repo suggests a flag is wanted.
2. Treat a missing output price as unknown: raise `UnpricedModelError(reason="unknown_model")`, or return `output_cost_per_million=0.0`, or `None`. Every `inference.net` entry lacks `output_cost_per_million` entirely, so this is a live decision, and "don't invent a price you don't have" is a defensible team position.
3. Mirror from the `"*"` tier rather than the requested tier, on the theory that per-window numbers are batch tiers and shouldn't set a list price.

**The observable.**
```python
p = resolve_model_price("meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                        provider="klusterai", completion_window="*")
(p.input_cost_per_million, p.output_cost_per_million, p.output_price_inferred) == (0.2, 0.8, False)

q = resolve_model_price("meta-llama/llama-3.1-8b-instruct/fp-8",
                        provider="inference.net", completion_window="24h")
(q.input_cost_per_million, q.output_cost_per_million, q.output_price_inferred) == (0.045, 0.045, True)

r = resolve_model_price("deepseek-ai/DeepSeek-R1", provider="klusterai", completion_window="*")
(r.input_cost_per_million, r.output_cost_per_million) == (3.0, 5.0)   # today both are 3.0
```
Reading the real output price is what separates this from the current code; the `output_price_inferred` flag is what separates it from alternative 1 and, together with the absence of an exception, from alternative 2.

**Arbitrary:** invented name (`output_price_inferred`) + policy with no local evidence (a data gap is mirrored *and* marked, rather than mirrored silently or refused).

---

### P5 — One owner of the batch discount: `batch_multiplier()`

**Behaviour.** The literal `0.5` appears in exactly one place in the pricing path, `_BATCH_DISCOUNT_FACTOR`, and it is applied by exactly one function, `_LitellmCostProcessor.batch_multiplier()` (for `cost()`) and by `resolve_model_price(batch=True)` (for displayed per-million prices). `batch_multiplier()` returns `1.0` when `self.batch` is false; `1.0` when `self.config.in_mtok_cost is not None` (a user-supplied price is taken as given and is never discounted); `1.0` when the class's `_BATCH_DISCOUNT_APPLIES` is `False`; otherwise `_BATCH_DISCOUNT_FACTOR`. `_BATCH_DISCOUNT_APPLIES` is `True` on `_LitellmCostProcessor` (and thus `_AzureCostProcessor`) and `False` on `_KlusterAICostProcessor` and `_InferenceNetCostProcessor`, because the per-window numbers in `_default_rate_limits.json` are already those providers' batch tiers. Symmetrically, `resolve_model_price` applies `_BATCH_DISCOUNT_FACTOR` when `batch=True` **and** `source == "litellm"`, and applies nothing when `source == "external"`. No `cost()` override multiplies or divides its result by anything.

**Alternatives a competent engineer would plausibly choose instead.**
1. Delete the `times = 2` hack (`cost.py:93`, `cost.py:119`) and let the parent's `*= 0.5` stand for everyone — the obvious reading of "four owners, keep one": keep the parent's, drop the subclasses'. Batch klusterai then costs half.
2. Keep the discount where `set_model_cost` puts it (`base_batch_request_processor.py:325-326`): the discount is a *display/estimate* concern applied to per-million numbers only, while `cost()` reports what litellm says, undiscounted.
3. Discount everything uniformly, including user-supplied `in_mtok_cost`/`out_mtok_cost` — the user gave a list price, and batch is half of list, so halving it is consistent.

**The observable.** With `cfg = BatchRequestProcessorConfig(model=M)` and `litellm.completion_cost` monkeypatched to return `4.0`, and `litellm.model_cost` monkeypatched to contain `M`:
```python
_LitellmCostProcessor(config=cfg, batch=True).batch_multiplier()  == 0.5
_LitellmCostProcessor(config=cfg, batch=False).batch_multiplier() == 1.0
_AzureCostProcessor(config=cfg, batch=True).batch_multiplier()    == 0.5
_KlusterAICostProcessor(config=cfg, batch=True).batch_multiplier()      == 1.0
_InferenceNetCostProcessor(config=cfg, batch=True).batch_multiplier()   == 1.0
_LitellmCostProcessor(config=BatchRequestProcessorConfig(model=M, in_mtok_cost=3),
                      batch=True).batch_multiplier() == 1.0

_LitellmCostProcessor(config=cfg, batch=True).cost(prompt="a", completion="b") == 2.0
_KlusterAICostProcessor(config=cfg_kluster, batch=True).cost(
    completion_window="*", prompt="a", completion="b") == 4.0

_LitellmCostProcessor._BATCH_DISCOUNT_APPLIES is True
_KlusterAICostProcessor._BATCH_DISCOUNT_APPLIES is False
_InferenceNetCostProcessor._BATCH_DISCOUNT_APPLIES is False

resolve_model_price("deepseek-ai/DeepSeek-R1", provider="klusterai",
                    completion_window="*", batch=True).input_cost_per_million == 3.0   # not 1.5
```
Alternative 1 gives `2.0` for the klusterai `cost()` call and has no `_BATCH_DISCOUNT_APPLIES` attribute; alternative 3 gives `0.5` for the `in_mtok_cost` multiplier.

**Arbitrary:** invented name (`batch_multiplier`, `_BATCH_DISCOUNT_APPLIES`, `_BATCH_DISCOUNT_FACTOR`) + policy with no local evidence (external-table prices and user-supplied `in_mtok_cost` are exempt; litellm-sourced prices are not).

---

### P6 — Registration into `litellm.model_cost` writes list prices and true metadata

**Behaviour.** `register_price_with_litellm(price)` raises `ValueError` if `price.batch` is `True` — the global table only ever holds undiscounted list prices, so the discount can never be applied twice — and otherwise calls `litellm.register_model({price.model: entry})` and returns `entry`, where `entry` is exactly `{"max_tokens": price.max_tokens if price.max_tokens is not None else 8192, "input_cost_per_token": price.input_cost_per_token, "output_cost_per_token": price.output_cost_per_token, "litellm_provider": price.provider if price.provider is not None else "openai"}` — four keys, no more. `_get_litellm_cost_map` is gone.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep `cost.py:55,58` as they are: `max_tokens: 8192` and `litellm_provider: "openai"` for everything, because litellm validates provider names and `"inference.net"` is not one litellm knows — writing the real provider risks breaking `completion_cost`.
2. Register the *effective* (already discounted) prices for a batch run, so that `litellm.completion_cost` returns the final number and no multiplier is needed downstream. This is the natural way to make P5's "one owner" true without a multiplier at all.
3. Take `max_tokens` from the table but leave the provider alone, or copy the whole table entry through.

**The observable.** After `register_price_with_litellm(resolve_model_price("meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8", provider="klusterai", completion_window="24h"))`:
```python
litellm.model_cost["meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"] == {
    "max_tokens": 1048576,
    "input_cost_per_token": 2.5e-07,
    "output_cost_per_token": 2.5e-07,
    "litellm_provider": "klusterai",
}
with pytest.raises(ValueError):
    register_price_with_litellm(resolve_model_price(
        "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        provider="klusterai", completion_window="24h", batch=True))
```
Alternative 1 writes `8192` / `"openai"`; alternative 2 never raises and writes `1.25e-07`.

**Arbitrary:** policy with no local evidence (the `ValueError` guard on a batch-resolved price is a rule nothing in the repo hints at). The `max_tokens`/`litellm_provider` values are honestly derivable from `_default_rate_limits.json` and the provider key.

---

### P7 — Which model name a cost processor prices, and it is the same one it looks up

**Behaviour.** `_LitellmCostProcessor.price_model(**kwargs)` returns the model name used for *both* registration and lookup, resolved in this order: `kwargs["completion_response"]["model"]` if `"completion_response"` is present in `kwargs` and that mapping has a non-empty `"model"`; else `kwargs["model"]` if present and non-empty; else `self.config.model`. It never returns `None`. `cost()` sets `kwargs["model"] = self.price_model(**kwargs)` before calling `litellm.completion_cost`, and gates on that same name being in `litellm.model_cost` (returning `0.0` if it is not). The klusterai/inference.net memoisation key uses that same resolved name.

**Alternatives a competent engineer would plausibly choose instead.**
1. Make the config authoritative: `self.config.model` is what the user asked for and what the parent already gates on (`cost.py:42`), so use it for both registration and lookup and ignore what the response echoed back. This fixes the register-one/look-up-another mismatch just as well, in the opposite direction.
2. Keep the response-model-only reading (`cost.py:115-118`) verbatim, including `model = kwargs.get("model", None)` and the `None` that follows when neither key is present, and just make the parent read the same variable.
3. Raise on the missing case — pricing a request with no identifiable model is a bug worth surfacing.

**The observable.** With `litellm.completion_cost` monkeypatched to record its kwargs and return `1.0`, `config.model == "meta-llama/llama-3.1-8b-instruct/fp-8"`, and `litellm.model_cost` containing both fp-8 names:
```python
p = _InferenceNetCostProcessor(config=cfg, batch=False)
p.cost(completion_response={"model": "meta-llama/llama-3.2-3b-instruct/fp-8"}, completion_window="24h")
captured["model"] == "meta-llama/llama-3.2-3b-instruct/fp-8"     # today: config.model, gated out, 0.0

p.price_model() == "meta-llama/llama-3.1-8b-instruct/fp-8"       # today: TypeError from _wrap(None, ...)
p.price_model(model="x") == "x"
p.price_model(completion_response={"model": "y"}, model="x") == "y"
p.price_model(completion_response={}) == "meta-llama/llama-3.1-8b-instruct/fp-8"
```
Alternative 1 yields `"meta-llama/llama-3.1-8b-instruct/fp-8"` for the first assertion; alternatives 2 and 3 raise on the fourth.

**Arbitrary:** policy with no local evidence (the three-step precedence, and specifically that an empty/absent `completion_response["model"]` falls through to `config.model` instead of raising). The "register and look up the same name" half is derivable from `cost.py:42` vs `cost.py:123`.

---

### P8 — One place the per-million numbers come from, and the two entry points agree

**Behaviour.** `BatchStatusTracker.refresh_model_price(price_model=None)` is the only code that assigns `input_cost_per_million` / `output_cost_per_million` on a batch tracker; it calls `resolve_model_price(price_model or self.model, provider=self.compatible_provider, completion_window=self.completion_window, batch=True)`, assigns the two prices and `output_price_inferred`, sets `price_unavailable_reason = None`, refreshes the cost strings, and returns `None`; on `UnpricedModelError` it sets both prices to `None`, `output_price_inferred = False`, `price_unavailable_reason = err.reason`, refreshes the cost strings, and returns `err.reason`. `model_post_init` calls it with no arguments. `BaseBatchRequestProcessor.set_model_cost` (line 320) contains no price arithmetic: it calls `self.tracker.refresh_model_price()` and then `self.tracker.start_tracker(self._tracker_console)`. Azure's and Mistral's overrides call `refresh_model_price(price_model="azure/…" / "mistral/…")` and, if the return value is not `None`, call `refresh_model_price()` again before starting the tracker. Consequence: a tracker that was only constructed (the `cancel_batches` path) and a tracker that also went through `set_model_cost` (the `requests_to_responses` path) hold identical prices. `batch=True` is hard-coded for `BatchStatusTracker`; `OnlineStatusTracker.refresh_model_price` is identical except it passes `batch=False` and `completion_window="*"`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Leave `model_post_init` undiscounted (as at `batch_status_tracker.py:111-122`) and let `set_model_cost` apply the 50% (as at `base_batch_request_processor.py:325-326`) — that is the current split, and it is defensible: the tracker doesn't know whether the run is really a batch until the processor tells it.
2. Keep the bare `except Exception` (`batch_status_tracker.py:124`) and just log the warning, without recording any reason; a failed price lookup is already visible as `N/A` in the display.
3. Have `set_model_cost` keep ownership of the numbers and make the tracker's `model_post_init` do nothing at all — one writer, but the *other* one.

**The observable.** With `console = rich.console.Console(file=io.StringIO())`:
```python
t = BatchStatusTracker(model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                       compatible_provider="klusterai", completion_window="24h")
(t.input_cost_per_million, t.output_cost_per_million) == (0.25, 0.25)
t.price_unavailable_reason is None
t.refresh_model_price() is None
(t.input_cost_per_million, t.output_cost_per_million) == (0.25, 0.25)   # idempotent; not 0.125

# litellm-sourced, batch: discounted once, by the tracker, on both paths
# litellm.model_cost["gpt-4o-mini"] monkeypatched to input 2e-06 / output 8e-06
u = BatchStatusTracker(model="gpt-4o-mini")
(u.input_cost_per_million, u.output_cost_per_million) == (1.0, 4.0)
u.refresh_model_price() is None and (u.input_cost_per_million, u.output_cost_per_million) == (1.0, 4.0)

# window normalisation reaches the tracker
v = BatchStatusTracker(model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                       compatible_provider="klusterai")            # completion_window is None
(v.input_cost_per_million, v.output_cost_per_million) == (0.2, 0.8)  # today: (None, None)

# failure contract at the tracker
w = BatchStatusTracker(model="ghost-model", compatible_provider="klusterai", completion_window="24h")
(w.input_cost_per_million, w.output_cost_per_million) == (None, None)
w.price_unavailable_reason == "unknown_model"
w.refresh_model_price(price_model="also-ghost") == "unknown_model"
```
Alternative 1 gives `(0.5, 2.0)` after `refresh_model_price()` on `u` but `(2.0, 8.0)` at construction; alternative 2 has no `price_unavailable_reason` attribute.

**Arbitrary:** invented name (`refresh_model_price`, its `Optional[str]` return-the-reason contract, `price_unavailable_reason`) + policy with no local evidence (the batch tracker always resolves with `batch=True`; both entry points must agree).

---

### P9 — `format_cost_strings` and the inferred-price marker

**Behaviour.** `format_cost_strings(price, *, rich)` is the only place a displayed per-million string is built. For `price is None` it returns `("[dim]N/A[/dim]", "[dim]N/A[/dim]")` when `rich` is true and `("N/A", "N/A")` when false. Otherwise the input string is `f"${price.input_cost_per_million:.3f}"` and the output string is the same for the output price, with a single `"*"` appended immediately after the digits when `price.output_price_inferred` is true; when `rich` is true each string is wrapped as `f"[red]{s}[/red]"` — the marker sits inside the markup. A price of `0.0` renders as `"$0.000"`, not `"N/A"`. Both trackers build their `input_cost_str` / `output_cost_str` by calling this function with `rich=USE_RICH_DISPLAY`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the two hand-rolled formatters (`batch_status_tracker.py:_format_cost_str`, `online_status_tracker.py:__post_init__` lines 130-137) exactly as they are — `f"[red]${v:.3f}[/red]"` with no marker, since nothing about an inferred price is displayed today and adding a symbol to a currency column is a UI decision nobody asked for.
2. Mark the inferred price differently: a trailing `" (est.)"`, a `"~"` prefix (`"~$0.045"`), a `[dim]` colour instead of `[red]`, or put the marker outside the markup (`"[red]$0.045[/red]*"`).
3. Render a zero price as `"N/A"` or `"free"` rather than `"$0.000"`, since `0.0` is what a missing price degrades to elsewhere in the codebase.

**The observable.**
```python
inferred = resolve_model_price("meta-llama/llama-3.1-8b-instruct/fp-8",
                               provider="inference.net", completion_window="24h")
format_cost_strings(inferred, rich=False) == ("$0.045", "$0.045*")
format_cost_strings(inferred, rich=True)  == ("[red]$0.045[/red]", "[red]$0.045*[/red]")

known = resolve_model_price("meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                            provider="klusterai", completion_window="*")
format_cost_strings(known, rich=False) == ("$0.200", "$0.800")

format_cost_strings(None, rich=False) == ("N/A", "N/A")
format_cost_strings(None, rich=True)  == ("[dim]N/A[/dim]", "[dim]N/A[/dim]")
```
and, on a tracker (`CURATOR_DISABLE_RICH_DISPLAY=1`, so `USE_RICH_DISPLAY` is false):
```python
t = BatchStatusTracker(model="meta-llama/llama-3.1-8b-instruct/fp-8",
                       compatible_provider="inference.net", completion_window="24h")
(t.input_cost_str, t.output_cost_str) == ("$0.045", "$0.045*")
t.output_price_inferred is True
```

**Arbitrary:** invented name (`format_cost_strings`) + policy with no local evidence (the `"*"` marker, its position inside the rich markup, and `0.0 -> "$0.000"`).

---

## End to end

### Setup (pure, no network, no clock)

```python
import io, litellm, pytest
from rich.console import Console
from bespokelabs.curator.cost import (
    ModelPrice, UnpricedModelError, resolve_model_price,
    register_price_with_litellm, format_cost_strings,
    external_model_cost, _KlusterAICostProcessor,
)
from bespokelabs.curator.request_processor.config import BatchRequestProcessorConfig
from bespokelabs.curator.status_tracker.batch_status_tracker import BatchStatusTracker

MODEL = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
# table entry: max_tokens 1048576
#   input_cost_per_million  {"*": 0.2, "24h": 0.25, "48h": 0.2, "72h": 0.15}
#   output_cost_per_million {"*": 0.8, "24h": 0.25, "48h": 0.2, "72h": 0.15}

console = Console(file=io.StringIO())   # env: CURATOR_DISABLE_RICH_DISPLAY=1
monkeypatch.setattr(litellm, "completion_cost", lambda **kw: 4.0)
```

### 1. The lookup

```python
price = resolve_model_price(MODEL, provider="klusterai", completion_window=None, batch=True)

price == ModelPrice(
    model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
    provider="klusterai",
    completion_window="*",
    input_cost_per_million=0.2,
    output_cost_per_million=0.8,
    source="external",
    batch=True,
    output_price_inferred=False,
    max_tokens=1048576,
)
price.input_cost_per_token  == 2e-07
price.output_cost_per_token == 8e-07
```
(Today: `external_model_cost(MODEL, completion_window=None, provider="klusterai")` raises `KeyError("Completion window None is not supported …")`, and with `completion_window="*"` it returns `{"input_cost_per_token": 2.0000000000000002e-07, "output_cost_per_token": 2.0000000000000002e-07}` — the output price wrong by 4x.)

### 2. Registration

```python
list_price = resolve_model_price(MODEL, provider="klusterai", completion_window="*")   # batch=False
register_price_with_litellm(list_price) == {
    "max_tokens": 1048576,
    "input_cost_per_token": 2e-07,
    "output_cost_per_token": 8e-07,
    "litellm_provider": "klusterai",
}
litellm.model_cost[MODEL]["max_tokens"] == 1048576          # today: 8192
litellm.model_cost[MODEL]["litellm_provider"] == "klusterai" # today: "openai"

with pytest.raises(ValueError):
    register_price_with_litellm(price)                       # price.batch is True
```

### 3. The cost processor

```python
cfg  = BatchRequestProcessorConfig(model=MODEL, completion_window="*")
proc = _KlusterAICostProcessor(config=cfg, batch=True)

proc.batch_multiplier() == 1.0
proc._BATCH_DISCOUNT_APPLIES is False
proc.price_model() == MODEL
proc.cost(completion_window="*", prompt="hi", completion="there") == 4.0   # 4.0 * 1.0, once
_KlusterAICostProcessor(config=cfg, batch=False).cost(
    completion_window="*", prompt="hi", completion="there") == 4.0
```
(Today: `4.0 * 0.5 * 2 == 4.0` — the same number, reached by two mistakes cancelling.)

### 4. The tracker, both entry points

```python
# the cancel_batches path: constructed, set_model_cost never called
t1 = BatchStatusTracker(model=MODEL, compatible_provider="klusterai", completion_window=None,
                        n_total_requests=3)
(t1.input_cost_per_million, t1.output_cost_per_million) == (0.2, 0.8)
t1.price_unavailable_reason is None
t1.output_price_inferred is False
(t1.input_cost_str, t1.output_cost_str) == ("$0.200", "$0.800")

# the requests_to_responses path: set_model_cost -> refresh_model_price
t2 = BatchStatusTracker(model=MODEL, compatible_provider="klusterai", completion_window=None,
                        n_total_requests=3)
t2.refresh_model_price() is None
t2.start_tracker(console)
(t2.input_cost_per_million, t2.output_cost_per_million) == (0.2, 0.8)

(t1.input_cost_per_million, t1.output_cost_per_million) == \
    (t2.input_cost_per_million, t2.output_cost_per_million)
```
(Today: `t1` is `(None, None)` because `completion_window=None` raises inside the bare `except`; after `set_model_cost` with `completion_window="*"` it would be `(0.2, 0.2)` — undiscounted on the external branch, output wrong. With a litellm-priced model the same two paths give `(2.0, 8.0)` and `(1.0, 4.0)`, a 2x disagreement.)

### 5. Failure

```python
t3 = BatchStatusTracker(model="ghost-model", compatible_provider="klusterai", completion_window="24h")
(t3.input_cost_per_million, t3.output_cost_per_million) == (None, None)
t3.price_unavailable_reason == "unknown_model"
(t3.input_cost_str, t3.output_cost_str) == ("N/A", "N/A")

with pytest.raises(UnpricedModelError) as excinfo:
    external_model_cost("ghost-model", "24h", "klusterai")
excinfo.value.reason == "unknown_model"
str(excinfo.value) == "unknown_model: model='ghost-model' provider='klusterai' completion_window='24h'"
isinstance(excinfo.value, KeyError) is False
```

### 6. An inference.net model, end to end

```python
external_model_cost("meta-llama/llama-3.1-8b-instruct/fp-8", "24h", "inference.net") == {
    "input_cost_per_token": 4.5e-08,
    "output_cost_per_token": 4.5e-08,
}
t4 = BatchStatusTracker(model="meta-llama/llama-3.1-8b-instruct/fp-8",
                        compatible_provider="inference.net", completion_window="24h")
(t4.input_cost_per_million, t4.output_cost_per_million) == (0.045, 0.045)
t4.output_price_inferred is True
(t4.input_cost_str, t4.output_cost_str) == ("$0.045", "$0.045*")
```
