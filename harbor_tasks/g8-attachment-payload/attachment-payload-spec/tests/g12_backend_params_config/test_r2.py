"""g12 — hidden requirement r2: unsupported generation params are reported, not raised.

    rule            a declared `unsupported_generation_params` field plus a pydantic
                    model_post_init that fills it with the sorted tuple of generation
                    params litellm does not list for the model -- and never raises
    scope           the base hook runs for every config `_validate_backend_params`
                    builds in online and batch mode; the field is real, so a
                    caller-supplied value is accepted and then overwritten, and
                    `exclude=True` keeps it out of model_dump()
    exclusions      the offline config overrides the hook to `()` unconditionally and
                    performs no litellm lookup at all
    failure_behavior  a lookup that returns None, or that raises, leaves `()` and lets
                    construction succeed
    observability   the literal probes the requirement spells out

The five are five measurements. `rule` never touches the offline class and never breaks
the lookup, `scope` never breaks the lookup either and is the only one that goes through
`_validate_backend_params` for both modes, `exclusions` is the only one that counts
lookups, `failure_behavior` is the only one that breaks the lookup for the ONLINE class
without asserting a computed tuple, and `observability` spells the requirement's own
examples out literally.
"""
from __future__ import annotations

import sys

import pytest

from harness import read_field, require_feature

from test_open import (
    OfflineRequestProcessorConfig,
    OnlineRequestProcessorConfig,
    RequestProcessorConfig,
    importable,
    vbp,
)

FIELD = "unsupported_generation_params"

GENERATION_PARAMS = {"top_k": 1, "temperature": 0.5, "frobnicate": 2}


def patch_lookup(monkeypatch, value=None, raises=None, calls=None):
    """Replace litellm's supported-params lookup wherever the implementation reads it.

    Set on the `litellm` package, on the module that defines the function, and on any
    curator module that has bound the name -- so an implementation that did
    `import litellm` and one that did `from litellm import get_supported_openai_params`
    are patched the same way. Which import form a build chose is not the fact being
    graded.
    """
    name = "get_supported_openai_params"

    def fake(*args, **kwargs):
        if calls is not None:
            calls.append((args, kwargs))
        if raises is not None:
            raise raises
        return value

    import litellm

    homes = [litellm]
    defining = sys.modules.get(getattr(getattr(litellm, name, None), "__module__", ""), None)
    if defining is not None:
        homes.append(defining)
    for mod_name, module in list(sys.modules.items()):
        if module is None or not mod_name.startswith("bespokelabs.curator"):
            continue
        if hasattr(module, name):
            homes.append(module)
    for home in homes:
        monkeypatch.setattr(home, name, fake, raising=False)


def unsupported(config):
    return read_field(config, FIELD)


def test_rule__the_hook_records_the_unsupported_generation_params_instead_of_raising(monkeypatch):
    importable()
    patch_lookup(monkeypatch, value=["temperature", "max_tokens"])

    # Reported, not raised: today the base hook's body would raise for the FIRST
    # generation param it saw, supported or not -- if anything ever called it.
    config = OnlineRequestProcessorConfig(model="gpt-4o", generation_params={"top_p": 1, "temperature": 0.5})
    assert unsupported(config) == ("top_p",)

    # Sorted, and a tuple.
    many = OnlineRequestProcessorConfig(
        model="gpt-4o", generation_params={"zeta": 1, "temperature": 0.5, "alpha": 2}
    )
    assert unsupported(many) == ("alpha", "zeta")
    assert isinstance(unsupported(many), tuple)

    # Everything supported, and nothing supplied, both give the empty default.
    assert unsupported(OnlineRequestProcessorConfig(model="gpt-4o", generation_params={"temperature": 0.5})) == ()
    assert unsupported(OnlineRequestProcessorConfig(model="gpt-4o")) == ()
    assert unsupported(RequestProcessorConfig(model="gpt-4o")) == ()


def test_scope__every_online_and_batch_config_gets_it_and_a_supplied_value_is_overwritten(monkeypatch):
    importable()
    patch_lookup(monkeypatch, value=["temperature", "max_tokens"])

    # Both modes, built the way the factory builds them.
    online = vbp({"model": "gpt-4o", "generation_params": dict(GENERATION_PARAMS)}, batch=False)
    batch = vbp({"model": "gpt-4o", "generation_params": dict(GENERATION_PARAMS)}, batch=True)
    assert type(online) is OnlineRequestProcessorConfig
    assert unsupported(online) == ("frobnicate", "top_k")
    assert unsupported(batch) == ("frobnicate", "top_k")

    # A real, declared field: supplying it is legal, and the hook then overwrites it.
    supplied = vbp(
        {"model": "gpt-4o", FIELD: ("caller_said_so",), "generation_params": {"temperature": 0.5}},
        batch=False,
    )
    assert unsupported(supplied) == ()

    # exclude=True: it is not part of the dumped config.
    assert FIELD not in online.model_dump()
    assert FIELD not in batch.model_dump()
    assert FIELD not in supplied.model_dump()


def test_exclusions__the_offline_config_sets_it_empty_and_never_asks_litellm(monkeypatch):
    importable()
    calls = []
    patch_lookup(monkeypatch, value=["temperature", "max_tokens"], calls=calls)

    # Proof the lookup and the recorder both work, so the offline zero below means
    # "asked nobody" rather than "this checkout asks nobody, ever".
    online = OnlineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS))
    require_feature(
        len(calls) > 0 and read_field(online, FIELD, default=None) == ("frobnicate", "top_k"),
        f"the base model_post_init that fills {FIELD} from litellm",
    )

    before = len(calls)
    offline = OfflineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS))
    assert unsupported(offline) == ()
    assert len(calls) == before, "the offline config asked litellm for supported params"

    # Through the factory's own path, with the offline mode resolved from the backend.
    from_factory = vbp(
        {"model": "gpt-4o", "generation_params": dict(GENERATION_PARAMS)}, batch=True, backend="vllm"
    )
    assert type(from_factory) is OfflineRequestProcessorConfig
    assert unsupported(from_factory) == ()
    assert len(calls) == before


def test_failure_behavior__a_broken_or_empty_lookup_leaves_an_empty_tuple(monkeypatch):
    importable()

    # A lookup that raises: construction still succeeds, and the answer is empty.
    patch_lookup(monkeypatch, raises=ValueError("litellm has no idea"))
    assert unsupported(OnlineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS))) == ()
    assert unsupported(vbp({"model": "gpt-4o", "generation_params": dict(GENERATION_PARAMS)}, batch=True)) == ()

    # A lookup with nothing to say.
    patch_lookup(monkeypatch, value=None)
    assert unsupported(OnlineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS))) == ()

    # A model that supports nothing at all is still not an error; every key is reported.
    patch_lookup(monkeypatch, value=[])
    every = OnlineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS))
    assert unsupported(every) == ("frobnicate", "temperature", "top_k")


def test_observability__the_probes_the_requirement_spells_out(monkeypatch):
    importable()
    patch_lookup(monkeypatch, value=["temperature", "max_tokens"])

    config = OnlineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS))
    assert unsupported(config) == ("frobnicate", "top_k")
    assert FIELD not in config.model_dump()

    assert unsupported(
        OfflineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS))
    ) == ()

    patch_lookup(monkeypatch, raises=RuntimeError("boom"))
    assert unsupported(OnlineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS))) == ()

    patch_lookup(monkeypatch, value=None)
    assert unsupported(OnlineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS))) == ()

    patch_lookup(monkeypatch, value=["temperature", "max_tokens"])
    supplied = vbp({"model": "gpt-4o", FIELD: ("x",)}, batch=True)
    assert unsupported(supplied) == ()
