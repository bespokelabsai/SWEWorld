"""g12 — the openly stated feature: one mode, one config class, one mode gate.

The ticket states, in the open:

  * `config.py` gains `_MODE_CONFIGS`, `_BACKEND_MODES` (nine entries), `_resolve_mode()`
    and `_remove_none_values()` (moved out of `_factory.py`), and a
    `_validate_backend_params(params, batch=False, backend=None)` that validates against
    `_MODE_CONFIGS[_resolve_mode(batch, backend)]` and nothing else;
  * `BackendModeError(ValueError)` with `backend` / `mode` / `supported` and an exact message;
  * the three dead `__post_init__` hooks deleted, with the batch-size rule re-expressed as
    a `field_validator("batch_size")` that accepts an int or the exact string `"auto"`;
  * a `_determine_backend()` that reads its `batch` argument and can return `"gemini"`;
  * a `create()` that copies the caller's dict, gates the mode before it builds anything,
    and delegates to `_create_config` -> `_validate_backend_params` exactly once.

All of that is one feature and scores as one test.

Deliberately NOT asserted here, because they belong to the hidden requirements and must
be measurable separately: which exception a WRONG-MODE key produces and what it carries
(r1 — so every params dict below is either entirely legal for its mode, or illegal only
in a way the open ticket already pins), and the `unsupported_generation_params` field and
its `model_post_init` (r2 — so nothing here reads that attribute or passes a non-empty
`generation_params` and inspects the result).

Also not asserted: that `_remove_none_values` is applied INSIDE
`_validate_backend_params`. The ticket says only that the helper moves into `config.py`;
where it is then called from is not open, so no params dict here carries a `None`.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

_IMPORT_ERROR = None
try:
    from bespokelabs.curator.request_processor import _factory as factory_mod
    from bespokelabs.curator.request_processor import config as config_mod
    from bespokelabs.curator.request_processor._factory import _RequestProcessorFactory
    from bespokelabs.curator.request_processor.config import (
        BatchRequestProcessorConfig,
        OfflineRequestProcessorConfig,
        OnlineRequestProcessorConfig,
        RequestProcessorConfig,
    )
except Exception as exc:  # pragma: no cover - reported per test by importable()
    _IMPORT_ERROR = exc
    factory_mod = config_mod = _RequestProcessorFactory = None
    BatchRequestProcessorConfig = OfflineRequestProcessorConfig = None
    OnlineRequestProcessorConfig = RequestProcessorConfig = None


# ---------------------------------------------------------------------------
# Guards and tolerant readers, shared with test_r1 / test_r2
# ---------------------------------------------------------------------------
def importable():
    """Curator itself must import; anything else is an environment fault, not a grade."""
    if _IMPORT_ERROR is not None:
        pytest.fail(f"curator did not import: {_IMPORT_ERROR!r}")


_MISSING = object()


def find_sym(name, default=_MISSING):
    """A new name, looked up wherever in the request_processor package it was written.

    The ticket says the new names live in `config.py`, but which module a helper or a
    table is written in is not what is being graded here, so `_factory.py` and the
    package itself are read too.
    """
    importable()
    import bespokelabs.curator.request_processor as package

    for home in (config_mod, factory_mod, package):
        if home is not None and hasattr(home, name):
            return getattr(home, name)
    return default


def sym(name):
    value = find_sym(name)
    if value is _MISSING:
        pytest.fail(f"no name {name!r} anywhere in bespokelabs.curator.request_processor")
    return value


def vbp(params, batch=False, backend=None):
    """`_validate_backend_params` called the way the ticket declares it."""
    fn = sym("_validate_backend_params")
    try:
        return fn(params, batch=batch, backend=backend)
    except TypeError as exc:
        if "batch" in str(exc) or "backend" in str(exc) or "positional" in str(exc):
            pytest.fail(
                "_validate_backend_params does not accept (params, batch=..., backend=...): "
                f"{exc}"
            )
        raise


def modes_table():
    """`_BACKEND_MODES` read as backend -> frozenset of mode names."""
    table = sym("_BACKEND_MODES")
    return {key: frozenset(value) for key, value in dict(table).items()}


def create(**kwargs):
    """`_RequestProcessorFactory.create` with the arguments it already takes."""
    importable()
    base = dict(
        model_name="gpt-4o",
        params=None,
        generation_params={},
        batch=False,
        backend=None,
        response_format=None,
    )
    base.update(kwargs)
    return _RequestProcessorFactory.create(**base)


# ---------------------------------------------------------------------------
def test_open_feature__the_mode_picks_the_class_and_the_backend_gate_fires_first(monkeypatch):
    importable()

    # --- the tables and the mode resolver -----------------------------------
    assert sym("_MODE_CONFIGS") == {
        "batch": BatchRequestProcessorConfig,
        "online": OnlineRequestProcessorConfig,
        "offline": OfflineRequestProcessorConfig,
    }

    assert modes_table() == {
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

    resolve = sym("_resolve_mode")
    assert resolve(False, None) == "online"
    assert resolve(True, None) == "batch"
    assert resolve(False, "openai") == "online"
    assert resolve(True, "openai") == "batch"
    assert resolve(False, "vllm") == "offline"
    assert resolve(True, "vllm") == "offline"          # vllm beats batch=True

    # --- the helper moved into config.py, and re-exported from _factory.py ---
    assert config_mod._remove_none_values({"a": 1, "b": None, "c": 0}) == {"a": 1, "c": 0}
    assert factory_mod._remove_none_values({"a": 1, "b": None, "c": 0}) == {"a": 1, "c": 0}

    # --- one mode, one class ------------------------------------------------
    assert type(vbp({"model": "gpt-4o", "max_retries": 3}, batch=True)) is BatchRequestProcessorConfig
    assert type(vbp({"model": "gpt-4o", "max_retries": 3}, batch=False)) is OnlineRequestProcessorConfig
    assert type(vbp({"model": "gpt-4o", "max_retries": 3}, batch=True, backend="vllm")) is OfflineRequestProcessorConfig
    assert type(vbp({"model": "gpt-4o", "max_retries": 3}, batch=False, backend="vllm")) is OfflineRequestProcessorConfig

    # `batch_size` is a field of BOTH the batch and the offline class, so the offline
    # mode is the one that decides here -- and "auto" is not an int. Today the
    # first-match-wins loop hands back a BatchRequestProcessorConfig instead. Which
    # ValueError it is (pydantic's own or a wrapper) is r1's business, not this test's.
    with pytest.raises(ValueError):
        vbp({"model": "gpt-4o", "batch_size": "auto"}, batch=False, backend="vllm")

    # --- BackendModeError -----------------------------------------------------
    mode_error = sym("BackendModeError")
    assert issubclass(mode_error, ValueError)
    err = mode_error("litellm", "batch", ("online",))
    assert err.backend == "litellm"
    assert err.mode == "batch"
    assert err.supported == ("online",)
    assert str(err) == "backend 'litellm' does not support batch mode; supported modes: online"
    assert str(mode_error("openai", "offline", ("batch", "online"))) == (
        "backend 'openai' does not support offline mode; supported modes: batch, online"
    )

    # --- the three dead hooks are gone ---------------------------------------
    for cls in (RequestProcessorConfig, BatchRequestProcessorConfig, OfflineRequestProcessorConfig):
        assert not hasattr(cls, "__post_init__"), f"{cls.__name__}.__post_init__ still exists"

    # --- batch_size: an int, or the exact string "auto" -----------------------
    assert vbp({"model": "gpt-4o", "batch_size": "auto"}, batch=True).batch_size == "auto"
    assert vbp({"model": "gpt-4o", "batch_size": 8}, batch=True).batch_size == 8
    assert BatchRequestProcessorConfig(model="gpt-4o").batch_size == 10_000

    with pytest.raises(ValidationError) as ei:
        vbp({"model": "gpt-4o", "batch_size": "huge"}, batch=True)
    errors = ei.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("batch_size",)
    assert errors[0]["type"] == "value_error"
    assert 'batch_size must be either an integer or "auto"' in str(ei.value)

    for bad in ("AUTO", "Auto", "10", ""):
        with pytest.raises(ValidationError):
            vbp({"model": "gpt-4o", "batch_size": bad}, batch=True)

    # the offline class keeps a plain int and gets no "auto" validator
    assert OfflineRequestProcessorConfig(model="gpt-4o", batch_size=256).batch_size == 256
    with pytest.raises(ValidationError):
        OfflineRequestProcessorConfig(model="gpt-4o", batch_size="auto")

    # --- _determine_backend now reads `batch` ---------------------------------
    determine = _RequestProcessorFactory._determine_backend
    assert determine("gemini/gemini-2.0-flash", {}, None, True) == "gemini"
    assert determine("gemini/gemini-2.0-flash", {}, None, False) == "litellm"
    assert determine("vertex_ai/gemini-1.5-pro", {}, None, True) == "gemini"
    assert determine("vertex_ai/gemini-1.5-pro", {}, None, False) == "litellm"
    assert determine("mistral/mistral-large-latest", {}, None, True) == "mistral"
    assert determine("mistral/mistral-large-latest", {}, None, False) == "litellm"
    assert determine("anthropic/claude-3-5-sonnet-20241022", {}, None, True) == "anthropic"
    assert determine("gpt-4o", {}, None, True) == "openai"
    assert determine("gpt-4o", {}, None, False) == "openai"

    # --- create(): copy the caller's dict, gate the mode, build once ----------
    # An unknown backend still falls through to the plain ValueError at the end.
    untouched = {"max_requests_per_minute": 5}
    with pytest.raises(ValueError) as unknown:
        create(model_name="gpt-4o", params=untouched, backend="not-a-backend", batch=False)
    assert not isinstance(unknown.value, mode_error)
    assert str(unknown.value) == "Unknown backend: not-a-backend"
    assert untouched == {"max_requests_per_minute": 5}      # today it has grown three keys

    # The mode gate fires before the API key is read: MISTRAL_API_KEY is absent, and
    # today that is what the caller is told about.
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(mode_error) as mistral:
        create(model_name="mistral/mistral-large-latest", backend="mistral", batch=False)
    assert (mistral.value.backend, mistral.value.mode, mistral.value.supported) == (
        "mistral", "online", ("batch",))
    assert str(mistral.value) == (
        "backend 'mistral' does not support online mode; supported modes: batch")

    # ... and before any config is built: these batch params are illegal for the online
    # class the litellm backend would have used, and the caller never hears about them.
    still_untouched = {"max_requests_per_minute": 5}
    with pytest.raises(mode_error) as litellm_batch:
        create(model_name="gpt-4o", params=still_untouched, generation_params={"temperature": 0.7},
               batch=True, backend="litellm")
    assert (litellm_batch.value.backend, litellm_batch.value.mode) == ("litellm", "batch")
    assert litellm_batch.value.supported == ("online",)
    assert still_untouched == {"max_requests_per_minute": 5}

    # Azure and vLLM sit on the same gate, and the deleted inline raise for azure was
    # the second half of an API-key check that no longer runs first.
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    with pytest.raises(mode_error) as azure:
        create(model_name="gpt-4o", backend="azure", batch=False)
    assert azure.value.supported == ("batch",)

    # _create_config is now the same call, so it answers with the mode's class.
    made = _RequestProcessorFactory._create_config({"model": "gpt-4o", "max_retries": 3}, True, None)
    assert type(made) is BatchRequestProcessorConfig
    assert type(_RequestProcessorFactory._create_config({"model": "gpt-4o"}, False, None)) is OnlineRequestProcessorConfig
    assert type(_RequestProcessorFactory._create_config({"model": "gpt-4o"}, True, "vllm")) is OfflineRequestProcessorConfig
