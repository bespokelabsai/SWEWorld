# g6 — Unified model price resolution

*model-price-lookup*

## The ticket the agent sees

Consolidate the scattered, inconsistent model-price lookups in `src/bespokelabs/curator/cost.py` (which today mixes external-table and litellm-table logic ad hoc across `external_model_cost()` and four separate `cost()` methods) and in the batch/online status trackers into one canonical path: add a frozen dataclass `ModelPrice` with fields `model: str`, `provider: str | None`, `completion_window: str`, `input_cost_per_million: float`, `output_cost_per_million: float`, `source: str` ("litellm" or "external"), `batch: bool`, `output_price_inferred: bool`, `max_tokens: int | None`, plus `input_cost_per_token`/`output_cost_per_token` properties (`round(value, 9)` for per-million figures, `round(per_million/1e6, 15)` for per-token); add `UnpricedModelError(LookupError)` with a class-level `REASONS` frozenset naming the permitted reason strings, a keyword-only `__init__(*, model, provider, completion_window, reason)` that raises `ValueError` for an unrecognized `reason` and otherwise produces the message `f"{reason}: model={model!r} provider={provider!r} completion_window={completion_window!r}"`; add `resolve_model_price(model, *, provider=None, completion_window=None, batch=False) -> ModelPrice` as the single function that consults `_DEFAULT_COST_MAP`'s external provider tables and `litellm.model_cost`, raises `UnpricedModelError` instead of ever returning a `None`-valued price, applies a batch-rate discount to the returned per-million prices where the pricing data calls for it when `batch=True`, and — when a table entry has no explicit output price — copies the input price into the output price and sets `output_price_inferred=True`; add `register_price_with_litellm(price: ModelPrice) -> dict` that writes `{"max_tokens": ..., "input_cost_per_token": ..., "output_cost_per_token": ..., "litellm_provider": ...}` into `litellm.model_cost` via `litellm.register_model` and raises `ValueError` if `price.batch` is `True`; add `format_cost_strings(price: ModelPrice | None, *, rich: bool) -> tuple[str, str]` as the sole place display strings like `"$0.045"` (or `"[red]$0.045[/red]"` when `rich`) are built, appending `"*"` to the output string when `output_price_inferred` is true and returning `("N/A", "N/A")` (or the `[dim]`-wrapped equivalent) for `price is None`; rewrite `external_model_cost(model, completion_window="*", provider="default") -> dict[str, float]` as a thin shim over `resolve_model_price(..., batch=False)`; delete `_get_litellm_cost_map`; and give `BatchStatusTracker`/`OnlineStatusTracker` new fields `price_unavailable_reason: Optional[str]` and `output_price_inferred: bool` plus a `refresh_model_price(*, price_model: str | None = None) -> Optional[str]` method (called from `model_post_init`/`__post_init__` and from the batch request processors' `set_model_cost()`) that re-resolves and assigns the two per-million prices, `output_price_inferred`, `input_cost_str`/`output_cost_str` (via `format_cost_strings`), sets `price_unavailable_reason` to `None` on success or to `err.reason` on `UnpricedModelError`, and never raises.

## Validation protocol

| condition | how it was run | expected | got |
|---|---|---|---|
| 1 · blind | `naive` reference build, free bracket | fails every hidden fact | 0 coincidence(s) |
| 2 · full spec | `oracle` reference build, free bracket | passes everything | 0 broken |
| 2 · full spec (paid) | harbor `spec-g6-1` | 1.0 | 1.0000 |
| 1 · blind (paid) | harbor `blind-g6-1` | < 1.0 | 0.0000 |
| 3 · ticket + clues | needs a phase-3 plant | passes | out of scope |
| 4 · clues only | needs a phase-3 plant | reconstructs | out of scope |

## Per fact

| fact | bracket | audit | spec arm | blind arm | requirement |
|---|---|---|---|---|---|
| `g6.r1.rule` | hidden | — | 1.0 | 0.0 | `resolve_model_price` never returns a `ModelPrice` carrying a `None` price: every failure raises `UnpricedModelError`, a |
| `g6.r1.exclusions_or_crossover` | hidden | — | 1.0 | 0.0 | An unregistered provider is `unknown_provider` even when the model is also absent and the window is also unrecognised, a |
| `g6.r1.observability` | hidden | — | 1.0 | 0.0 | `resolve_model_price("no-such-model", provider="not-a-provider", completion_window="96h")` raises with `reason == "unkno |
| `g6.r2.rule` | hidden | — | 1.0 | 0.0 | The batch discount factor is applied by exactly one method, `batch_multiplier()`, on the cost processors; no `cost()` ov |
| `g6.r2.scope` | hidden | — | 1.0 | 0.0 | `batch_multiplier()` returns the discount factor only where the pricing data is a list price: it returns `1.0` when the  |
| `g6.r2.exclusions_or_crossover` | hidden | — | 1.0 | 0.0 | A user-supplied per-million price is never discounted: `batch_multiplier()` returns `1.0` whenever the config carries an |
| `g6.r2.observability` | hidden | — | 1.0 | 0.0 | `batch_multiplier()` is the discount factor on the base and Azure processors in batch mode and `1.0` out of it, and `1.0 |

## What authoring cost

15 agent call(s), $21.99 of subscription usage.

| step | $ | turns | s |
|---|---|---|---|
| `author` | 2.16 | 27 | 498 |
| `build-oracle` | 3.64 | 43 | 574 |
| `split` | 0.26 | 2 | 124 |
| `split` | 0.41 | 3 | 214 |
| `tests` | 4.52 | 41 | 841 |
| `build-naive` | 2.52 | 43 | 428 |
| `build-spec` | 3.35 | 41 | 603 |
| `build-spec` | 4.02 | 49 | 693 |
| `trim-g6.r1.rule` | 0.15 | 4 | 30 |
| `trim-g6.r1.exclusions_or_crossover` | 0.17 | 4 | 45 |
| `trim-g6.r1.observability` | 0.17 | 5 | 52 |
| `trim-g6.r2.rule` | 0.15 | 4 | 41 |
| `trim-g6.r2.scope` | 0.13 | 4 | 34 |
| `trim-g6.r2.exclusions_or_crossover` | 0.11 | 4 | 34 |
| `trim-g6.r2.observability` | 0.23 | 4 | 66 |
