# Hidden requirements — g6 (model-price-lookup)

## r1
- **rule** — When `provider` is a named external provider (neither `None` nor `"default"`), `resolve_model_price` reads only that provider's entry in `_DEFAULT_COST_MAP["external"]["providers"][provider]["cost"]` and never consults `litellm.model_cost`, even if `litellm.model_cost` already has an entry under the same model key.
- **scope** — This external-only reading applies precisely when `provider` is named; when `provider` is `None` or `"default"`, the lookup reads only `litellm.model_cost` and never touches the external table.
- **exclusions_or_crossover** — If the named provider's table lacks the model, the function must raise `UnpricedModelError(reason="unknown_model")` rather than falling back to whatever `litellm.model_cost` has under that key.
- **observability** — With a model present in both tables under different numbers, `resolve_model_price(model, provider="klusterai", completion_window="*")` returns the external table's numbers with `source == "external"`, not litellm's numbers; a call with a provider whose table lacks the model raises even though `litellm.model_cost` would have answered.

## r2
- **rule** — `resolve_model_price(..., batch=True)` must return per-million numbers identical to the `batch=False` call whenever the winning price came from the external provider table; the batch-rate discount is applied only to prices that came from `litellm.model_cost`.
- **scope** — The exemption is decided purely by which source answered the lookup (the resolved `source` field), not by inspecting or special-casing the provider string.
- **exclusions_or_crossover** — A price resolved with `provider=None`/`"default"` (source `"litellm"`) is not exempt: its `batch=True` per-million numbers must still come out lower than its `batch=False` numbers by the same fixed factor.
- **observability** — For an external-table provider (e.g. `"klusterai"`), `resolve_model_price(model, provider="klusterai", completion_window="*", batch=True).input_cost_per_million` equals the `batch=False` call's value exactly (e.g. both `0.2`); for a `litellm`-sourced model the `batch=True` value is exactly half the `batch=False` value.
- *earlier, reversed*: the team once applied the fixed batch discount uniformly to every source inside the base cost processor, then had klusterai/inference.net multiply their own result by 2 to cancel it back out because their tables were already batch-tier prices; that compensating multiply was later dropped in favor of exempting external-sourced prices at the resolution layer instead
