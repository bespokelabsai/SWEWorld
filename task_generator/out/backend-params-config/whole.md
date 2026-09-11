# Mode-aware backend parameter validation

## Target

### Files that change
- `src/bespokelabs/curator/request_processor/config.py`
  - `_validate_backend_params()` (currently line 191) — rewritten.
  - `RequestProcessorConfig.__post_init__` (line 43), `BatchRequestProcessorConfig.__post_init__`
    (line 86), `OfflineRequestProcessorConfig.__post_init__` (line 138) — all three deleted.
  - new: `BackendParamError`, `BackendModeError`, `_MODE_CONFIGS`, `_BACKEND_MODES`,
    `_resolve_mode()`, `_remove_none_values()` (moved in), a `batch_size` `field_validator`,
    a `model_post_init` on the base and on the offline config, and the field
    `unsupported_generation_params`.
- `src/bespokelabs/curator/request_processor/_factory.py`
  - `_remove_none_values()` (line 22) — becomes a re-export of the `config.py` one.
  - `_RequestProcessorFactory._create_config()` (line 29) — becomes a delegation.
  - `_RequestProcessorFactory._determine_backend()` (line 44) — gains a `gemini` branch and
    starts reading its `batch` argument.
  - `_RequestProcessorFactory.create()` (line 71) — copies `params`, gains a mode
    pre-check, drops the inline mode raises at lines 158, 175 and 185.

Nothing else in the package changes. `llm.py` keeps its own private `_remove_none_values`
(`llm/llm.py` line 385) and is untouched.

### Existing machinery to REUSE (do not reimplement)
- The four pydantic config classes and their fields: `RequestProcessorConfig`,
  `BatchRequestProcessorConfig`, `OnlineRequestProcessorConfig`,
  `OfflineRequestProcessorConfig` (`config.py` lines 8-143), including
  `class Config: extra = "forbid"` (lines 38-41). No field is added or removed except
  `unsupported_generation_params` (P10).
- `pydantic.ValidationError`, `pydantic.field_validator`, and pydantic v2's
  `model_post_init` hook — the convention already used correctly at
  `types/token_usage.py` line 9 and `status_tracker/batch_status_tracker.py` line 105.
- `_remove_none_values()` — the existing body from `_factory.py` line 22, moved into
  `config.py` verbatim.
- `litellm.litellm_core_utils.get_llm_provider_logic.get_llm_provider` (offline string
  parsing) and `litellm.get_supported_openai_params` (local table lookup), both imported
  lazily exactly where they are imported today.
- The `create()` dispatch table (`_factory.py` lines 96-190) and every processor class it
  names. The nine `base_url`/`api_key` assignments stay inline where they are; this task
  does not de-duplicate them.
- `BackendParamsType` and the four `TypedDict`s (`config.py` lines 146-188), unchanged.

### What must be BUILT
- `BackendParamError(ValueError)` and `BackendModeError(ValueError)` with the exact
  attributes and messages in "The API".
- `_MODE_CONFIGS`, `_BACKEND_MODES`, `_resolve_mode()`.
- The new `_validate_backend_params()` body.
- `BatchRequestProcessorConfig` `batch_size` field validator.
- `RequestProcessorConfig.model_post_init` and `OfflineRequestProcessorConfig.model_post_init`,
  plus the `unsupported_generation_params` field.
- The `gemini` / batch-aware branches of `_determine_backend()` and the mode pre-check in
  `create()`.

### Python / dependencies
Python 3.10 (`pyproject.toml`: `python = "^3.10"`; the interpreter in this checkout is
3.10.12). pydantic 2.13.4 (`>=2.9.2`), litellm 1.83.7 — both already required. No new
dependency. Pure, in-process, no network, no clock, no randomness, no threads.

### Latent bugs this fixes (real, with locations)
1. `config.py` lines 191-204: `_validate_backend_params()` accepts the first config class
   that validates the raw dict, and is never told the mode, so `{"batch_size": 100}` with
   `batch=False` passes here and then dies with a bare `pydantic.ValidationError` inside
   `_create_config` (`_factory.py` line 34).
2. `config.py` line 203 constructs a config that `create()` throws away (`_factory.py`
   line 84) before rebuilding it at line 94.
3. `config.py` line 199 validates the raw dict while `_factory.py` lines 31-34 strip
   `None` first, so `{"max_retries": None}` is rejected by one side and accepted by the other.
4. `config.py` lines 43, 86, 138: three `__post_init__` methods on pydantic v2 `BaseModel`s.
   Python never calls them. Consequences: the `batch_size in {int, "auto"}` rule at line 88
   is dead (`"huge"` is accepted by the `t.Union[int, str]` field at line 79), and the base
   loop at lines 57-58 would raise for *every* generation param, ignoring the
   `supported_params` it computed at line 54 — i.e. it is dead *and* wrong.
5. `_factory.py` line 83: `create()` mutates the caller's `backend_params` dict in place.
6. `_factory.py` lines 44-68: `_determine_backend()` takes `batch` (line 49) and never
   reads it, and cannot return `gemini`, so a Gemini model with `batch=True` and no
   explicit backend reaches `raise ValueError("Batch mode is not supported with LiteLLM
   backend.")` (line 158) although `GeminiBatchRequestProcessor` is wired at line 147; and
   a Mistral model with `batch=False` auto-detects to `mistral` (line 64) and dies at
   line 175.

### Explicitly out of scope
The meanings of `max_retries` and `seconds_to_pause_on_rate_limit`; what the `"auto"`
batch size *resolves to* numerically. This task decides only which config class a param
lands in, whether the value is well-formed, and what a caller sees when it is not. No
numeric constraint is added to or removed from any existing field.

---

## The API

All new names live in `src/bespokelabs/curator/request_processor/config.py`.

```python
class BackendParamError(ValueError):
    """Raised when a backend param is not a field of the config class for the requested mode."""

    params: tuple[str, ...]      # offending keys, sorted ascending by str
    expected: str                # __name__ of the config class for the requested mode
    belongs_to: tuple[str, ...]  # __name__s of the other config classes that accept ALL of `params`

    def __init__(self, params: tuple[str, ...], expected: str, belongs_to: tuple[str, ...]) -> None: ...


class BackendModeError(ValueError):
    """Raised when a backend cannot serve the requested mode."""

    backend: str                 # e.g. "litellm"
    mode: str                    # one of "batch", "online", "offline"
    supported: tuple[str, ...]   # modes the backend does support, sorted ascending by str

    def __init__(self, backend: str, mode: str, supported: tuple[str, ...]) -> None: ...
```

`str(BackendParamError(...))` is exactly:

```python
# belongs_to non-empty
f"backend_params {', '.join(params)} not accepted by {expected}; accepted by {' or '.join(belongs_to)}"
# belongs_to empty
f"backend_params {', '.join(params)} not accepted by {expected}; accepted by no request processor config"
```

`str(BackendModeError(...))` is exactly:

```python
f"backend {backend!r} does not support {mode} mode; supported modes: {', '.join(supported)}"
```

Module-level tables and helpers:

```python
_MODE_CONFIGS: dict[str, type[RequestProcessorConfig]] = {
    "batch": BatchRequestProcessorConfig,
    "online": OnlineRequestProcessorConfig,
    "offline": OfflineRequestProcessorConfig,
}

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

def _resolve_mode(batch: bool, backend: str | None) -> str: ...
    # returns "offline" | "batch" | "online"

def _remove_none_values(d: dict) -> dict: ...
    # moved verbatim from _factory.py line 22

def _validate_backend_params(
    params: BackendParamsType,
    batch: bool = False,
    backend: str | None = None,
) -> RequestProcessorConfig: ...
    # returns an instance of _MODE_CONFIGS[_resolve_mode(batch, backend)]
```

Field added to `RequestProcessorConfig` (`config.py`, after line 36):

```python
unsupported_generation_params: tuple[str, ...] = Field(default=(), exclude=True)
```

`_factory.py` signatures — unchanged shapes, new bodies:

```python
_remove_none_values = _config_remove_none_values          # re-export, same name, same behaviour

class _RequestProcessorFactory:
    @classmethod
    def _create_config(cls, params, batch, backend) -> RequestProcessorConfig: ...
        # exactly: return _validate_backend_params(params, batch, backend)

    @staticmethod
    def _determine_backend(
        model_name: str,
        config_params: BackendParamsType,
        response_format: t.Type["BaseModel"] | None = None,
        batch: bool = False,
    ) -> str: ...
        # returns one of "openai" | "anthropic" | "gemini" | "mistral" | "litellm"

    @classmethod
    def create(cls, model_name, params, generation_params, batch, backend,
               response_format, return_completions_object=False) -> "BaseRequestProcessor": ...
```

---

## Parts

### P1 — The mode picks the config class

**Behaviour.** `_validate_backend_params(params, batch, backend)` resolves exactly one
mode — `"offline"` if `backend == "vllm"`, else `"batch"` if `batch` is truthy, else
`"online"` — validates `params` against `_MODE_CONFIGS[mode]` only, and returns an instance
of that class. No other config class is ever constructed or consulted for acceptance; the
first-match-wins loop at `config.py` lines 197-203 is gone.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the trial loop but reorder it so the mode's class is tried first and the others
   remain as fallbacks — "be permissive, the caller probably knows what they meant".
2. Keep `_validate_backend_params` mode-blind exactly as it is (it is a *validator*, after
   all) and fix only `_create_config`, so validation still passes for
   `{"batch_size": 100}, batch=False` and the failure surfaces later.
3. Union the field sets: accept any key that any config class declares, then construct the
   mode's class with only the keys it knows and silently drop the rest.

**The observable.**
- `type(_validate_backend_params({"model": "gpt-4o", "max_retries": 3}, batch=True)) is BatchRequestProcessorConfig`
- `type(_validate_backend_params({"model": "gpt-4o", "max_retries": 3}, batch=False)) is OnlineRequestProcessorConfig`
- `type(_validate_backend_params({"model": "gpt-4o", "max_retries": 3}, batch=True, backend="vllm")) is OfflineRequestProcessorConfig`
  (backend `"vllm"` beats `batch=True`)
- `_validate_backend_params({"model": "gpt-4o", "batch_size": "auto"}, batch=False, backend="vllm")`
  raises `pydantic.ValidationError` — today it returns a `BatchRequestProcessorConfig`.

**Arbitrary:** none — derivable from `_factory.py` lines 30-34 (`_create_config` already
picks the class this way). Recorded so the split step knows not to hide it.

---

### P2 — `BackendParamError`

**Behaviour.** A wrong-mode param raises `BackendParamError`, a subclass of `ValueError`
defined in `config.py`, carrying `params`, `expected` and `belongs_to` as instance
attributes and rendering the exact message given in "The API". It is raised by
`_validate_backend_params` before pydantic runs, so no `ValidationError` is produced for
this case and no config object is constructed.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the existing `ValueError` with the existing message
   (`f"Backend params are not valid, please refer {validators} for more info..."`,
   line 204) and just make it fire in more cases — no new class, no attributes.
2. Let pydantic do the talking: catch nothing, let `extra="forbid"` raise its own
   `ValidationError` with `type == "extra_forbidden"`, and let the caller read `.errors()`.
3. Define a new class but subclass `Exception`, or subclass `pydantic.ValidationError`,
   rather than `ValueError`.

**The observable.**
```python
with pytest.raises(BackendParamError) as ei:
    _validate_backend_params({"model": "gpt-4o", "batch_size": 100}, batch=False)
e = ei.value
assert isinstance(e, ValueError)
assert e.params == ("batch_size",)
assert e.expected == "OnlineRequestProcessorConfig"
assert str(e) == (
    "backend_params batch_size not accepted by OnlineRequestProcessorConfig; "
    "accepted by BatchRequestProcessorConfig or OfflineRequestProcessorConfig"
)
```

**Arbitrary:** an invented name — the class `BackendParamError`, its three attribute names,
and the exact message string exist nowhere in the repository and cannot be guessed from it.

---

### P3 — Which keys offend, and where they belong

**Behaviour.** The offending keys are the keys of `params` (after None-stripping, P5) that
are not in `_MODE_CONFIGS[mode].model_fields`, reported sorted ascending as a tuple.
`belongs_to` lists the `__name__` of each *other* config class, iterated in the fixed order
`BatchRequestProcessorConfig`, `OnlineRequestProcessorConfig`, `OfflineRequestProcessorConfig`,
whose `model_fields` contain **every** offending key — membership by name only, values are
never type-checked for this. A key no config declares yields `belongs_to == ()`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Report only the first offending key and stop — one bad key, one error, message names it.
2. Report `belongs_to` as the classes that accept *any* offending key (union), rather than
   all of them (intersection).
3. Decide `belongs_to` by actually calling `OtherClass.model_validate(params)` and listing
   the classes that succeed — which would make `belongs_to` value-sensitive and would drop
   `OfflineRequestProcessorConfig` from the `batch_size="auto"` case.
4. Preserve the caller's dict insertion order instead of sorting.

**The observable.**
```python
with pytest.raises(BackendParamError) as ei:
    _validate_backend_params(
        {"model": "gpt-4o", "tensor_parallel_size": 2, "batch_size": "auto", "nope": 1},
        batch=False,
    )
e = ei.value
assert e.params == ("batch_size", "nope", "tensor_parallel_size")   # sorted, all three
assert e.belongs_to == ()          # no single class declares all three
```
and, for the intersection-vs-union split:
```python
with pytest.raises(BackendParamError) as ei:
    _validate_backend_params({"model": "gpt-4o", "batch_size": "auto"}, batch=False)
assert ei.value.belongs_to == ("BatchRequestProcessorConfig", "OfflineRequestProcessorConfig")
```
(`batch_size` is a field of both, and `"auto"` is not a valid *value* for the offline one —
which `belongs_to` deliberately ignores.)

**Arbitrary:** a policy with no local evidence — nothing in the code says whether a
wrong-mode report is per-key or aggregate, sorted or insertion-ordered, name-based or
value-based. Alternative 3 in particular is the natural thing to write given the existing
trial loop, and it produces a different tuple.

---

### P4 — A bad value in the right mode is a `ValidationError`, unwrapped

**Behaviour.** If every key is a field of the mode's config class, `_validate_backend_params`
calls the class constructor and lets any `pydantic.ValidationError` propagate unchanged —
it is not caught, not wrapped, not converted. The unknown-key scan (P3) runs first, so when
a call has both an unknown key and an invalid value, `BackendParamError` is raised and the
invalid value is never reported.

**Alternatives a competent engineer would plausibly choose instead.**
1. Wrap everything in `BackendParamError` so callers have one exception type to catch —
   with `params` holding the failing field names taken from `ValidationError.errors()`.
2. Run pydantic first and derive the offending keys from the `extra_forbidden` entries in
   `.errors()`, which reverses the precedence: the mixed dict below would then report both
   problems in one `ValidationError` with 2 entries.
3. Catch `ValidationError` and re-raise the friendly `ValueError` from line 204, preserving
   the current "one error message for all failures" behaviour.

**The observable.**
```python
with pytest.raises(ValidationError) as ei:
    _validate_backend_params({"model": "gpt-4o", "max_retries": -1}, batch=True)
assert not isinstance(ei.value, BackendParamError)
assert len(ei.value.errors()) == 1
assert ei.value.errors()[0]["loc"] == ("max_retries",)

# precedence: unknown key wins over bad value
with pytest.raises(BackendParamError) as ei2:
    _validate_backend_params({"model": "gpt-4o", "batch_size": 8, "max_retries": -1}, batch=False)
assert ei2.value.params == ("batch_size",)          # not ("batch_size", "max_retries")
```

**Arbitrary:** a policy with no local evidence — the file currently swallows every
`ValidationError` (line 200) and shows the caller one friendly `ValueError`, so "let
pydantic through untouched, but only for values" is a decision, and precedence between the
two failure kinds is stated nowhere.

---

### P5 — `None` means absent, and it is stripped first

**Behaviour.** `_validate_backend_params` applies `_remove_none_values()` to `params`
**before** the unknown-key scan and before constructing anything. So a `None` value never
produces a `BackendParamError` even when its key belongs to a different mode, and it never
produces a `ValidationError`; the field takes its declared default. `params` itself is not
mutated. A `model` key that is missing — or present with value `None`, hence stripped — is
a `pydantic.ValidationError` with one error at `loc == ("model",)`, never a
`BackendParamError`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Strip `None` *after* the unknown-key scan, so `{"batch_size": None}` with `batch=False`
   is still a wrong-mode error — defensible, since the caller did name a batch-only param.
2. Do not strip at all and keep the current line-199 behaviour: `{"max_retries": None}`
   fails, because `None` is not an `int` and the caller should not pass it.
3. Strip only the keys declared `t.Optional[...]` in the `BackendParams` TypedDicts.

**The observable.**
```python
c = _validate_backend_params({"model": "gpt-4o", "max_retries": None}, batch=True)
assert type(c) is BatchRequestProcessorConfig and c.max_retries == 10   # today: ValueError

d = {"model": "gpt-4o", "batch_size": None, "max_requests_per_minute": None}
c = _validate_backend_params(d, batch=False)          # no raise at all
assert type(c) is OnlineRequestProcessorConfig
assert c.max_requests_per_minute is None
assert d == {"model": "gpt-4o", "batch_size": None, "max_requests_per_minute": None}  # not mutated

with pytest.raises(ValidationError) as ei:
    _validate_backend_params({"model": None, "max_retries": 3}, batch=True)
assert ei.value.errors()[0]["loc"] == ("model",)
```

**Arbitrary:** a policy with no local evidence — the two sides of the codebase already
disagree (`config.py` line 199 vs `_factory.py` line 31), and the ordering of the strip
relative to the unknown-key scan, which is what makes `{"batch_size": None}, batch=False`
succeed, is invisible in both.

---

### P6 — `_determine_backend` reads its `batch` argument

**Behaviour.** `_determine_backend` keeps its first two rules and gains two mode-aware
ones, evaluated in this order: (1) `provider == "openai"` → `"openai"`; (2) `"claude"` in
the lowercased model name → `"anthropic"`; (3) `provider in {"gemini", "vertex_ai"}` →
`"gemini"` when `batch` is true, else `"litellm"`; (4) any of `codestral`, `mistral`,
`ministral`, `pixtral` in the lowercased model name → `"mistral"` when `batch` is true,
else `"litellm"`; (5) otherwise `"litellm"`. The provider comes from
`get_llm_provider(model_name)[1]` as today.

**Alternatives a competent engineer would plausibly choose instead.**
1. Add the `gemini` branch unconditionally (`provider == "gemini"` → `"gemini"` for both
   modes), matching how the `openai` and `anthropic` branches are written, and let the
   online Gemini case fail later.
2. Leave `mistral` unconditional as it is today (line 64) and treat "Mistral has no online
   backend" as a real user-facing error rather than something auto-detection should route
   around.
3. Route the non-batch Gemini and Mistral cases to `"openai"` (both providers ship
   OpenAI-compatible endpoints) rather than to `"litellm"`.
4. Keep the whole function unchanged and instead fix the mismatch at the `create()` end.

**The observable.** With `get_llm_provider` monkeypatched to return the provider in
element 1, the six-tuple is exactly:
```python
_determine_backend("gemini/gemini-2.0-flash", {}, None, True)      == "gemini"
_determine_backend("gemini/gemini-2.0-flash", {}, None, False)     == "litellm"
_determine_backend("mistral/mistral-large-latest", {}, None, True) == "mistral"
_determine_backend("mistral/mistral-large-latest", {}, None, False)== "litellm"
_determine_backend("claude-3-5-sonnet-20241022", {}, None, True)   == "anthropic"
_determine_backend("gpt-4o", {}, None, True)                       == "openai"
```
Today rows 1, 2 and 4 are `"litellm"`, `"litellm"`, `"mistral"`.

**Arbitrary:** a deliberate departure — line 62-64 plainly returns `"mistral"` regardless of
mode, and the two unconditional branches above it model the shape an engineer would copy;
row 4 contradicts what the surrounding code does.

---

### P7 — `_BACKEND_MODES` and `BackendModeError`

**Behaviour.** `config.py` gains `_BACKEND_MODES`, a dict of exactly the nine backend names
`create()` dispatches on, each mapped to the frozenset of modes it can serve, with the
contents given in "The API". `create()` computes `mode = _resolve_mode(batch, backend)`
after resolving `backend` and, if `backend` is in `_BACKEND_MODES` and `mode` is not in
`_BACKEND_MODES[backend]`, raises `BackendModeError(backend, mode, tuple(sorted(...)))`
immediately — before any config is built, before any API key is read from the environment,
and before any processor is imported. The three inline raises at `_factory.py` lines 158,
175 and 185 are deleted; the final `raise ValueError(f"Unknown backend: {backend}")`
(line 190) is kept verbatim for backends absent from the table.

**Alternatives a competent engineer would plausibly choose instead.**
1. Leave the inline raises where they are and keep their current wording — they are already
   specific and already in the right branches.
2. Build the table but key it the other way round (mode → set of backends), or express it as
   two sets, `_BATCH_ONLY_BACKENDS` / `_ONLINE_ONLY_BACKENDS`, listing only the exceptions.
3. Put the check inside `_determine_backend` so only auto-detected backends are guarded and
   an explicit `backend="mistral", batch=False` still reaches line 175.
4. Keep the existing order for Mistral and Azure — API-key check first, mode check second
   (lines 171-175, 181-185) — since a missing key is arguably the more fundamental problem.

**The observable.**
```python
assert len(_BACKEND_MODES) == 9
assert sorted(_BACKEND_MODES) == [
    "anthropic", "azure", "gemini", "inference.net", "klusterai",
    "litellm", "mistral", "openai", "vllm",
]

monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
with pytest.raises(BackendModeError) as ei:
    _RequestProcessorFactory.create(
        model_name="mistral/mistral-large-latest", params=None, generation_params={},
        batch=False, backend="mistral", response_format=None,
    )
assert (ei.value.backend, ei.value.mode, ei.value.supported) == ("mistral", "online", ("batch",))
assert str(ei.value) == "backend 'mistral' does not support online mode; supported modes: batch"

with pytest.raises(ValueError) as ei2:
    _RequestProcessorFactory.create(
        model_name="gpt-4o", params=None, generation_params={},
        batch=False, backend="not-a-backend", response_format=None,
    )
assert not isinstance(ei2.value, BackendModeError)
assert str(ei2.value) == "Unknown backend: not-a-backend"
```
Today the first call raises `ValueError("MISTRAL_API_KEY is not set.")` from line 173.

**Arbitrary:** an invented name plus a chosen value — `_BACKEND_MODES`, `BackendModeError`
and its three attributes are unguessable, the table's exact membership (nine entries, and in
particular that `klusterai` and `inference.net` are dual-mode while `azure`, `gemini` and
`mistral` are batch-only) is a decision, and moving the check ahead of the API-key read
reverses the order the code plainly uses.

---

### P8 — `create()` copies its input and validates once

**Behaviour.** `create()` performs, in this order: (1) `params = dict(params) if params
else {}` — a shallow copy, so the caller's dict is never mutated; (2) set `"model"`,
`"generation_params"` and `"return_completions_object"` on the copy; (3) resolve `backend`
via `_determine_backend` if it is `None`; (4) the P7 mode check; (5) `config =
cls._create_config(params, batch, backend)`, which is now exactly `return
_validate_backend_params(params, batch, backend)`. There is no separate
`_validate_backend_params(params)` call at line 84 and no discarded config: the object
`_validate_backend_params` returns is the object `create()` dispatches with.
`BackendModeError` therefore takes precedence over `BackendParamError`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the line-84 call as a pre-flight check and the line-94 rebuild — validate, then
   build, which is the shape the file has now.
2. Mutate `params` in place as today (line 83) — the dict came from the caller's kwargs and
   nobody has complained.
3. Validate before resolving the backend (so `backend` is still `None` and the mode
   resolution cannot see `"vllm"`), or deep-copy rather than shallow-copy.
4. Check params before modes, on the grounds that a malformed dict is the earlier error.

**The observable.**
```python
d = {"max_requests_per_minute": 5}
with pytest.raises(BackendModeError):
    _RequestProcessorFactory.create(
        model_name="gpt-4o", params=d, generation_params={"temperature": 0.7},
        batch=True, backend="litellm", response_format=None,
    )
assert d == {"max_requests_per_minute": 5}          # exactly one key; today it has four
assert list(d) == ["max_requests_per_minute"]
```
(`max_requests_per_minute` is invalid for batch mode, so this also pins mode-before-params
precedence: the raised type is `BackendModeError`, not `BackendParamError`.) Plus:
```python
c = _RequestProcessorFactory._create_config({"model": "gpt-4o", "batch_size": 8}, False, None)
```
raises `BackendParamError` — today it raises a bare `pydantic.ValidationError`.

**Arbitrary:** a policy with no local evidence, and a deliberate departure — line 83 plainly
mutates the caller's dict and lines 84/94 plainly validate-then-rebuild; both alternatives
are what reading the function suggests.

---

### P9 — `batch_size` accepts an int or the exact string `"auto"`

**Behaviour.** `BatchRequestProcessorConfig.__post_init__` (line 86) is deleted and its rule
is re-expressed as a pydantic `field_validator("batch_size")` that runs on every
construction. An `int` passes. The string `"auto"` passes. Every other `str` — including
`"AUTO"`, `"Auto"`, `""` and numeric strings like `"10"`, which are **not** coerced to int —
raises `ValueError('batch_size must be either an integer or "auto"')`, which pydantic
surfaces as a `ValidationError`. The field annotation stays `t.Union[int, str]` and the
default stays `10_000`. `OfflineRequestProcessorConfig.batch_size` keeps its plain
`int` annotation and gets no validator.

**Alternatives a competent engineer would plausibly choose instead.**
1. Rename `__post_init__` to `model_post_init` — the fix the neighbouring
   `types/token_usage.py` line 9 and `status_tracker/batch_status_tracker.py` line 105
   demonstrate, and the one-word change the code invites. It yields a `ValueError` raised
   from `__init__`, not a `ValidationError`, and a different `str(exc)`.
2. Narrow the annotation to `t.Union[int, t.Literal["auto"]]` and delete the hook entirely,
   letting pydantic generate the message (`"Input should be 'auto'"`, `type ==
   "literal_error"`).
3. Accept numeric strings by coercing them (`int("10") == 10`), which is what a reader of
   `t.Union[int, str]` might assume pydantic already does.
4. Case-fold before comparing, so `"AUTO"` is accepted.

**The observable.**
```python
with pytest.raises(ValidationError) as ei:
    _validate_backend_params({"model": "gpt-4o", "batch_size": "huge"}, batch=True)
e = ei.value
assert len(e.errors()) == 1
assert e.errors()[0]["loc"] == ("batch_size",)
assert e.errors()[0]["type"] == "value_error"
assert 'batch_size must be either an integer or "auto"' in str(e)

for bad in ("AUTO", "10", ""):
    with pytest.raises(ValidationError):
        _validate_backend_params({"model": "gpt-4o", "batch_size": bad}, batch=True)

assert _validate_backend_params({"model": "gpt-4o", "batch_size": "auto"}, batch=True).batch_size == "auto"
assert _validate_backend_params({"model": "gpt-4o", "batch_size": 8}, batch=True).batch_size == 8
assert not hasattr(BatchRequestProcessorConfig, "__post_init__")
```
Today all of `"huge"`, `"AUTO"`, `"10"` and `""` are accepted and stored verbatim.

**Arbitrary:** a deliberate departure — the file hands you a dead `__post_init__` next to
two live `model_post_init`s two directories away, so the obvious move is alternative 1,
which produces a different exception type and message; and `"10"` surviving as a string
today makes alternative 3 look like the bug to fix.

---

### P10 — `unsupported_generation_params` is reported, not raised

**Behaviour.** `RequestProcessorConfig.__post_init__` (line 43) is deleted and replaced by a
pydantic `model_post_init` that computes
`litellm.get_supported_openai_params(model=self.model)` and assigns
`self.unsupported_generation_params = tuple(sorted(k for k in self.generation_params if k
not in supported))`. It never raises: if the lookup returns `None` or raises any
`Exception`, the value is `()`. `OfflineRequestProcessorConfig` overrides `model_post_init`
to set `()` unconditionally and does not import litellm — this is what its line-138 hook's
docstring claims to do. The field is declared `Field(default=(), exclude=True)`: a
caller-supplied value is accepted as a legal backend param (it is a real field, so P3 does
not flag it) and is then overwritten, and it does not appear in `model_dump()`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Do what lines 57-58 clearly meant: rename to `model_post_init` and raise
   `ValueError(f"Generation parameter '{key}' is not supported for model '{self.model}'")`
   for each key missing from `supported_params` — the minimal, faithful repair of the
   existing bug, and what the docstring at lines 49-50 promises.
2. Keep the computed list under the name the code already uses, `self.supported_params`
   (line 54), rather than inverting it into an unsupported list.
3. Emit `logger.warning` per unsupported param and store nothing — a warning has no
   assertable structural value.
4. Let a litellm failure propagate, since an unknown model is a real problem worth
   surfacing early.

**The observable.** With `litellm.get_supported_openai_params` monkeypatched to return
`["temperature", "max_tokens"]`:
```python
gp = {"top_k": 1, "temperature": 0.5, "frobnicate": 2}
c = OnlineRequestProcessorConfig(model="gpt-4o", generation_params=gp)   # no raise
assert c.unsupported_generation_params == ("frobnicate", "top_k")
assert "unsupported_generation_params" not in c.model_dump()

assert OfflineRequestProcessorConfig(model="gpt-4o", generation_params=gp).unsupported_generation_params == ()
```
with the lookup patched to raise `RuntimeError("boom")`:
```python
assert OnlineRequestProcessorConfig(model="gpt-4o", generation_params=gp).unsupported_generation_params == ()
```
and with it returning `None`:
```python
assert OnlineRequestProcessorConfig(model="gpt-4o", generation_params=gp).unsupported_generation_params == ()
```
and the overwrite:
```python
c = _validate_backend_params(
    {"model": "gpt-4o", "unsupported_generation_params": ("x",)}, batch=True
)   # no BackendParamError
assert c.unsupported_generation_params == ()
```

**Arbitrary:** an invented name plus a deliberate departure — the field name and its tuple
shape appear nowhere in the repository, the code at line 58 plainly raises (and its
docstring plainly promises to), and `supported_params` at line 54 is the name the file
already offers for the opposite polarity.

---

## End to end

A caller asks for batch inference from Gemini and passes an online-only knob, an
explicitly-`None` knob, and a batch knob.

```python
from bespokelabs.curator.request_processor._factory import _RequestProcessorFactory
from bespokelabs.curator.request_processor.config import (
    BackendModeError, BackendParamError, _validate_backend_params,
)

backend_params = {
    "batch_size": "auto",
    "batch_check_interval": 30,
    "max_retries": None,
    "max_requests_per_minute": 600,
}
```

**Step 1 — auto-detection now sees the mode.** With `get_llm_provider` returning provider
`"gemini"`:

```python
_RequestProcessorFactory._determine_backend("gemini/gemini-2.0-flash", backend_params, None, batch=True)
# == "gemini"          (today: "litellm")
```

**Step 2 — the mode check passes.** `_resolve_mode(batch=True, backend="gemini")` is
`"batch"`, and `"batch" in _BACKEND_MODES["gemini"]`, so no `BackendModeError`.

**Step 3 — params are validated against the batch config, and fail.** `max_retries: None`
is stripped first (P5); `max_requests_per_minute` is not a field of
`BatchRequestProcessorConfig`:

```python
_validate_backend_params(dict(backend_params, model="gemini/gemini-2.0-flash"), batch=True, backend="gemini")
```
raises `BackendParamError` with, exactly:

```python
e.params      == ("max_requests_per_minute",)
e.expected    == "BatchRequestProcessorConfig"
e.belongs_to  == ("OnlineRequestProcessorConfig",)
str(e)        == ("backend_params max_requests_per_minute not accepted by "
                  "BatchRequestProcessorConfig; accepted by OnlineRequestProcessorConfig")
isinstance(e, ValueError)  is True
backend_params == {"batch_size": "auto", "batch_check_interval": 30,
                   "max_retries": None, "max_requests_per_minute": 600}   # unmutated
```

Today: `_validate_backend_params` raises
`ValueError("Backend params are not valid, please refer (<class '...BatchRequestProcessorConfig'>, ...) for more info on backend params.")`
from line 204 — because no single class accepts both `batch_size` and
`max_requests_per_minute` — and `backend_params` has already grown a `"model"` key.

**Step 4 — the caller drops the online knob and retries.**

```python
backend_params.pop("max_requests_per_minute")
c = _validate_backend_params(dict(backend_params, model="gemini/gemini-2.0-flash"), batch=True, backend="gemini")

type(c) is BatchRequestProcessorConfig
c.model                          == "gemini/gemini-2.0-flash"
c.batch_size                     == "auto"
c.batch_check_interval           == 30
c.max_retries                    == 10          # None stripped, default applied
c.completion_window              == "24h"
c.generation_params              == {}
c.unsupported_generation_params  == ()
"unsupported_generation_params" not in c.model_dump()
```

**Step 5 — the same caller with `batch=False`.**

```python
_RequestProcessorFactory.create(
    model_name="gemini/gemini-2.0-flash", params=dict(backend_params),
    generation_params={}, batch=False, backend="gemini", response_format=None,
)
```
raises `BackendModeError` with:

```python
(e.backend, e.mode, e.supported) == ("gemini", "online", ("batch",))
str(e) == "backend 'gemini' does not support online mode; supported modes: batch"
```
raised before `_create_config` runs, so the two now-invalid batch params
(`batch_size`, `batch_check_interval`) are never reported — mode beats params.
