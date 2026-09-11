"""g12 — hidden requirement r1: what a wrong-mode backend param raises, and what it carries.

    rule            a BackendParamError(ValueError) defined with (params, expected,
                    belongs_to) and stored under those three names, raised INSTEAD of a
                    pydantic ValidationError and before any config is constructed
    scope           offending keys and `belongs_to` are decided by NAME against
                    `_MODE_CONFIGS[mode].model_fields` -- an intersection over the other
                    three classes in their fixed order, never a union, never a trial
                    validation
    failure_behavior  every offending key at once, sorted, in the two exact message
                    forms; a bad VALUE in the right mode stays a bare ValidationError;
                    the unknown-key scan runs first
    observability   the four literal probes the requirement spells out

The four are four measurements. `rule` never inspects `belongs_to` for a two-class
answer, `scope` never reads a message string, `failure_behavior` never asserts the
class's own constructor, and `observability` is the only one that spells the
requirement's own examples out literally.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from test_open import importable, sym, vbp


def param_error():
    """The class the requirement names, or a clear failure."""
    cls = sym("BackendParamError")
    return cls


def raised_by(params, **kw):
    """The BackendParamError a call produces, or a failure naming what came instead."""
    cls = param_error()
    with pytest.raises(cls) as info:
        result = vbp(params, **kw)
        pytest.fail(f"no BackendParamError for {params!r} ({kw}); it returned {result!r}")
    return info.value


def test_rule__a_wrong_mode_key_raises_backend_param_error_before_pydantic_runs():
    importable()
    cls = param_error()

    # A ValueError, and not pydantic's own error class.
    assert issubclass(cls, ValueError)
    assert not issubclass(cls, ValidationError)

    # The constructor takes the three arguments in order and stores them under those names.
    made = cls(("batch_size",), "OnlineRequestProcessorConfig", ("BatchRequestProcessorConfig",))
    assert made.params == ("batch_size",)
    assert made.expected == "OnlineRequestProcessorConfig"
    assert made.belongs_to == ("BatchRequestProcessorConfig",)

    # `batch_size` is not a field of the online class, so the online mode rejects it --
    # with this error rather than with a ValidationError. Today `extra = "forbid"` would
    # be the one talking, and only from inside a half-built config.
    error = raised_by({"model": "gpt-4o", "batch_size": 100}, batch=False)
    assert isinstance(error, ValueError)
    assert not isinstance(error, ValidationError)
    assert error.params == ("batch_size",)
    assert error.expected == "OnlineRequestProcessorConfig"

    # Raised BEFORE pydantic runs, so nothing is constructed: `model` is required and
    # absent here, and an implementation that validated first would have to report that
    # too -- or report it instead.
    early = raised_by({"batch_size": 100}, batch=False)
    assert early.params == ("batch_size",)
    assert early.expected == "OnlineRequestProcessorConfig"


def test_scope__membership_is_by_field_name_and_belongs_to_is_an_intersection():
    importable()

    # `expected` is the __name__ of the class for the resolved mode, whichever mode that is.
    batch_side = raised_by({"model": "gpt-4o", "max_requests_per_minute": 600}, batch=True)
    assert batch_side.expected == "BatchRequestProcessorConfig"
    assert batch_side.belongs_to == ("OnlineRequestProcessorConfig",)

    online_side = raised_by({"model": "gpt-4o", "tensor_parallel_size": 2}, batch=False)
    assert online_side.expected == "OnlineRequestProcessorConfig"
    assert online_side.belongs_to == ("OfflineRequestProcessorConfig",)

    offline_side = raised_by({"model": "gpt-4o", "batch_check_interval": 30}, batch=True, backend="vllm")
    assert offline_side.expected == "OfflineRequestProcessorConfig"
    assert offline_side.belongs_to == ("BatchRequestProcessorConfig",)

    # An intersection, never a union: the online class declares one of these two keys and
    # the offline class the other, so no single class accepts both.
    both = raised_by(
        {"model": "gpt-4o", "max_requests_per_minute": 600, "tensor_parallel_size": 2}, batch=True
    )
    assert both.params == ("max_requests_per_minute", "tensor_parallel_size")
    assert both.belongs_to == ()

    # By NAME, never by trial validation: -5 is a legal int for the batch class but the
    # offline class constrains batch_size > 0, so a class list built by calling
    # model_validate would drop the offline one here. Membership does not look at values.
    by_name = raised_by({"model": "gpt-4o", "batch_size": -5}, batch=False)
    assert by_name.params == ("batch_size",)
    assert by_name.belongs_to == ("BatchRequestProcessorConfig", "OfflineRequestProcessorConfig")

    # A key no config class declares belongs nowhere.
    nowhere = raised_by({"model": "gpt-4o", "definitely_not_a_field": 1}, batch=True)
    assert nowhere.params == ("definitely_not_a_field",)
    assert nowhere.belongs_to == ()


def test_failure_behavior__all_keys_at_once_and_a_bad_value_stays_a_validation_error():
    importable()
    cls = param_error()

    # Every offending key, sorted -- not just the first, and not in insertion order.
    many = raised_by({"model": "gpt-4o", "zeta_knob": 1, "alpha_knob": 2}, batch=True)
    assert many.params == ("alpha_knob", "zeta_knob")
    assert many.belongs_to == ()
    assert str(many) == (
        "backend_params alpha_knob, zeta_knob not accepted by BatchRequestProcessorConfig; "
        "accepted by no request processor config"
    )

    # The other message form, with somewhere to point at.
    one = raised_by({"model": "gpt-4o", "max_requests_per_minute": 600}, batch=True)
    assert str(one) == (
        "backend_params max_requests_per_minute not accepted by BatchRequestProcessorConfig; "
        "accepted by OnlineRequestProcessorConfig"
    )

    # A bad VALUE for a key the mode's class does declare: pydantic's error, unchanged.
    with pytest.raises(ValidationError) as bad_value:
        vbp({"model": "gpt-4o", "request_timeout": 0}, batch=True)
    assert not isinstance(bad_value.value, cls)
    assert len(bad_value.value.errors()) == 1
    assert bad_value.value.errors()[0]["loc"] == ("request_timeout",)

    # The unknown-key scan runs first, so the bad value is never reported alongside it.
    mixed = raised_by(
        {"model": "gpt-4o", "max_requests_per_minute": 600, "request_timeout": 0}, batch=True
    )
    assert mixed.params == ("max_requests_per_minute",)
    assert "request_timeout" not in str(mixed)


def test_observability__the_four_probes_the_requirement_spells_out():
    importable()
    cls = param_error()

    first = raised_by({"model": "gpt-4o", "batch_size": "auto"}, batch=False)
    assert first.params == ("batch_size",)
    assert first.expected == "OnlineRequestProcessorConfig"
    assert first.belongs_to == ("BatchRequestProcessorConfig", "OfflineRequestProcessorConfig")
    assert str(first) == (
        "backend_params batch_size not accepted by OnlineRequestProcessorConfig; "
        "accepted by BatchRequestProcessorConfig or OfflineRequestProcessorConfig"
    )
    assert isinstance(first, ValueError) is True

    second = raised_by(
        {"model": "gpt-4o", "tensor_parallel_size": 2, "batch_size": "auto", "nope": 1},
        batch=False,
    )
    assert second.params == ("batch_size", "nope", "tensor_parallel_size")
    assert second.belongs_to == ()

    third = raised_by({"model": "gpt-4o", "batch_size": 8, "max_retries": -1}, batch=False)
    assert third.params == ("batch_size",)

    with pytest.raises(ValidationError) as fourth:
        vbp({"model": "gpt-4o", "max_retries": -1}, batch=True)
    assert not isinstance(fourth.value, cls)
    assert len(fourth.value.errors()) == 1
    assert fourth.value.errors()[0]["loc"] == ("max_retries",)
