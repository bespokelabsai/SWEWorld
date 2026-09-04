# Unified model price resolution

Consolidate the scattered, inconsistent model-price lookups into one canonical path.

Today that logic is spread across `src/bespokelabs/curator/cost.py` — which mixes external-table and litellm-table logic ad hoc across `external_model_cost()` and four separate `cost()` methods — and across the batch/online status trackers.

### 1. Add a frozen dataclass `ModelPrice`

With these fields:

- `model: str`
- `provider: str | None`
- `completion_window: str`
- `input_cost_per_million: float`
- `output_cost_per_million: float`
- `source: str` ("litellm" or "external")
- `batch: bool`
- `output_price_inferred: bool`
- `max_tokens: int | None`

Plus `input_cost_per_token`/`output_cost_per_token` properties (`round(value, 9)` for per-million figures, `round(per_million/1e6, 15)` for per-token).

### 2. Add `UnpricedModelError(LookupError)`

- A class-level `REASONS` frozenset naming the permitted reason strings.
- A keyword-only `__init__(*, model, provider, completion_window, reason)` that raises `ValueError` for an unrecognized `reason`.
- Otherwise it produces the message `f"{reason}: model={model!r} provider={provider!r} completion_window={completion_window!r}"`.

### 3. Add `resolve_model_price(model, *, provider=None, completion_window=None, batch=False) -> ModelPrice`

The single function that consults `_DEFAULT_COST_MAP`'s external provider tables and `litellm.model_cost`. It:

- Raises `UnpricedModelError` instead of ever returning a `None`-valued price.
- Applies a batch-rate discount to the returned per-million prices where the pricing data calls for it when `batch=True`.
- When a table entry has no explicit output price, copies the input price into the output price and sets `output_price_inferred=True`.

### 4. Add `register_price_with_litellm(price: ModelPrice) -> dict`

- Writes `{"max_tokens": ..., "input_cost_per_token": ..., "output_cost_per_token": ..., "litellm_provider": ...}` into `litellm.model_cost` via `litellm.register_model`.
- Raises `ValueError` if `price.batch` is `True`.
- Returns that same four-key `{"max_tokens": ..., "input_cost_per_token": ..., "output_cost_per_token": ..., "litellm_provider": ...}` dict — the entry it just wrote, not `{price.model: {...}}`.

### 5. Add `format_cost_strings(price: ModelPrice | None, *, rich: bool) -> tuple[str, str]`

The sole place display strings like `"$0.045"` (or `"[red]$0.045[/red]"` when `rich`) are built. It:

- Appends `"*"` to the output string when `output_price_inferred` is true.
- Returns `("N/A", "N/A")` (or the `[dim]`-wrapped equivalent) for `price is None`.

### 6. Rewrite `external_model_cost(model, completion_window="*", provider="default") -> dict[str, float]`

As a thin shim over `resolve_model_price(..., batch=False)`.

### 7. Delete `_get_litellm_cost_map`

### 8. Give `BatchStatusTracker`/`OnlineStatusTracker` two new fields and one new method

New fields:

- `price_unavailable_reason: Optional[str]`
- `output_price_inferred: bool`

New method `refresh_model_price(*, price_model: str | None = None) -> Optional[str]`, called from `model_post_init`/`__post_init__` and from the batch request processors' `set_model_cost()`. It:

- Re-resolves and assigns the two per-million prices, `output_price_inferred`, and `input_cost_str`/`output_cost_str` (via `format_cost_strings`).
- Sets `price_unavailable_reason` to `None` on success or to `err.reason` on `UnpricedModelError`.
- Never raises.
