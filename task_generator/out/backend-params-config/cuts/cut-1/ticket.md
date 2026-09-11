# Mode-aware backend parameter validation

Make `_validate_backend_params` mode-aware so backend params are checked against the one config class that will actually be built, and make the factory refuse impossible backend/mode combinations before it does any work.

All new names live in `src/bespokelabs/curator/request_processor/config.py`; the factory changes are in `src/bespokelabs/curator/request_processor/_factory.py`. Nothing else in the package changes (`llm/llm.py` keeps its own private helper and is untouched).

### `_validate_backend_params` picks exactly one config class
- New signature: `_validate_backend_params(params: BackendParamsType, batch: bool = False, backend: str | None = None) -> RequestProcessorConfig`.
- Add `_resolve_mode(batch: bool, backend: str | None) -> str` returning `"offline"` when `backend == "vllm"`, else `"batch"` when `batch` is truthy, else `"online"`.
- Add `_MODE_CONFIGS: dict[str, type[RequestProcessorConfig]] = {"batch": BatchRequestProcessorConfig, "online": OnlineRequestProcessorConfig, "offline": OfflineRequestProcessorConfig}`.
- Validate against `_MODE_CONFIGS[_resolve_mode(batch, backend)]` only and return an instance of that class. The current first-match-wins trial loop over all config classes is deleted — no other config class is constructed.

### New exception types in `config.py`
- `class BackendParamError(ValueError)` with `__init__(self, params: tuple[str, ...], expected: str, belongs_to: tuple[str, ...]) -> None`, storing all three as instance attributes: `params` (the supplied backend param keys that are not fields of the mode's config class), `expected` (the `__name__` of the config class for the requested mode), `belongs_to` (the `__name__`s of the other request-processor config classes implicated by those keys, `()` when there are none).
- `str(BackendParamError(...))` is exactly `f"backend_params {', '.join(params)} not accepted by {expected}; accepted by {' or '.join(belongs_to)}"`, or, when `belongs_to` is empty, `f"backend_params {', '.join(params)} not accepted by {expected}; accepted by no request processor config"`.
- `class BackendModeError(ValueError)` with `__init__(self, backend: str, mode: str, supported: tuple[str, ...]) -> None`, storing `backend`, `mode` and `supported` (the modes that backend does support, sorted ascending). `str(...)` is exactly `f"backend {backend!r} does not support {mode} mode; supported modes: {', '.join(supported)}"`.

### `_BACKEND_MODES` and the mode pre-check
- Add to `config.py`:
```python
_BACKEND_MODES: dict[str, frozenset[str]] = {
    "openai": frozenset({"online", "batch"}),
    "anthropic": frozenset({"online", "batch"}),
    "klusterai": frozenset({"online", "batch"}),
    "inference.net": frozenset({"online", "batch"}),
    "gemini": frozenset({"batch"}),
    "mistral": frozenset({"batch"}),
    "azure": frozenset({"batch"}),
    "litellm": frozenset({"online"}),
    "vllm": frozenset({"offline"}),
}
```
- `create()` computes the mode after resolving `backend` and, when `backend` is in the table and the mode is not in its frozenset, raises `BackendModeError(backend, mode, tuple(sorted(...)))` before any config is built, before any API key is read from the environment and before any processor module is imported.
- The three inline mode raises in the `create()` dispatch table (`"Batch mode is not supported with LiteLLM backend."`, and the Mistral and Azure ones) are deleted. The trailing `raise ValueError(f"Unknown backend: {backend}")` stays verbatim and still fires for backends absent from the table.

### `create()` and `_create_config`
- `create()` first makes a shallow copy of `params` (`dict(params) if params else {}`) and sets `"model"`, `"generation_params"` and `"return_completions_object"` on the copy; the caller's dict is not mutated.
- Order inside `create()`: copy → populate → resolve `backend` via `_determine_backend` when it is `None` → mode pre-check → `config = cls._create_config(params, batch, backend)` → dispatch. The old pre-flight `_validate_backend_params(params)` call and the config object it produced and discarded are gone; the object returned by validation is the object dispatched with.
- `_RequestProcessorFactory._create_config(cls, params, batch, backend) -> RequestProcessorConfig` keeps its signature and delegates to `_validate_backend_params`.
- The nine inline `base_url`/`api_key` assignments in the dispatch table stay where they are; this task does not de-duplicate them.

### `_determine_backend` reads its `batch` argument
Same signature (`model_name`, `config_params`, `response_format=None`, `batch=False`), returning one of `"openai" | "anthropic" | "gemini" | "mistral" | "litellm"`. Provider still comes from `get_llm_provider(model_name)[1]`, imported lazily where it is today. Rules, in order:
1. provider `"openai"` → `"openai"`;
2. `"claude"` in the lowercased model name → `"anthropic"`;
3. provider in `{"gemini", "vertex_ai"}` → `"gemini"` when `batch`, else `"litellm"`;
4. any of `codestral`, `mistral`, `ministral`, `pixtral` in the lowercased model name → `"mistral"` when `batch`, else `"litellm"`;
5. otherwise `"litellm"`.

### The three dead `__post_init__` hooks
`RequestProcessorConfig.__post_init__`, `BatchRequestProcessorConfig.__post_init__` and `OfflineRequestProcessorConfig.__post_init__` are dataclass hooks on pydantic v2 `BaseModel`s — Python never calls them. Delete all three and re-express what they were for with pydantic v2 mechanisms (`field_validator`, `model_post_init`), of which there are working examples in `types/token_usage.py` and `status_tracker/batch_status_tracker.py`.
- `batch_size` on `BatchRequestProcessorConfig` gets a `field_validator("batch_size")` that runs on every construction: an `int` passes, the exact string `"auto"` passes, and every other `str` raises `ValueError('batch_size must be either an integer or "auto"')`, which pydantic surfaces as a `ValidationError` with one error at `loc == ("batch_size",)` and `type == "value_error"`. Numeric strings such as `"10"` are not coerced. The annotation stays `t.Union[int, str]` and the default stays `10_000`. `OfflineRequestProcessorConfig.batch_size` keeps its plain `int` annotation and gets no validator.
- The base config's hook is replaced by a `model_post_init` that handles the `generation_params` vs. `litellm.get_supported_openai_params` concern the deleted hook was written for, keeping the lazy litellm import exactly where it is today. `OfflineRequestProcessorConfig` overrides `model_post_init` and does not consult litellm at all, as its docstring already claims.

### Constraints
- Python 3.10, pydantic 2.x, litellm already required — no new dependency, no network, no clock, no randomness, no threads.
- The four config classes, `class Config: extra = "forbid"`, `BackendParamsType` and the four `TypedDict`s stay as they are; no existing field changes annotation or default, and no numeric constraint is added to or removed from any field.
- Out of scope: the meaning of `max_retries` and `seconds_to_pause_on_rate_limit`, and what `"auto"` resolves to numerically.
