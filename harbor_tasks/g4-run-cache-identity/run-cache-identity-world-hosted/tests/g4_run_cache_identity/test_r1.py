"""g4 — hidden requirement r1: what the run key is computed from.

    rule        exactly twelve component keys, exported alphabetically as
                IDENTITY_COMPONENT_KEYS; the parse function participates through
                _get_function_hash exactly as the prompt function does;
                system_prompt and return_completions_object participate;
                generation_params is always carried ({} when empty); and
                response_format is the compact sorted JSON schema, or "text"
    scope       `backend` is the RESOLVED backend read off `llm.backend`, not the
                declared `backend=` argument (None on the auto-detect path);
                `LLM.backend_params` is a copy of what __init__ was handed, {} for None
    exclusions  backend_params is filtered to the four keys of
                IDENTITY_BACKEND_PARAM_KEYS; every other knob — including api_key —
                must not fork the cache directory
    observability  the requirement's own table, as literals, plus the proof that
                no api_key reaches the stamp file

The four are four measurements. `rule` never looks at backend_params, `scope`
never compares a run hash, `exclusions` varies only backend_params, and
`observability` is the only test that writes a stamp to disk or builds a real
`curator.LLM`.

This is the human reference, over the old fixed example inputs. The grader
(probe.py/judge.py) asserts the same facts over inputs re-drawn from a per-run
seed (`fixture_spec.derive`) — model, dataset hash, generation params, system
prompt, response model, functions, backend-knob values and combinations, run ids
and rows — and reads the stamps and cache directories the scenarios leave behind,
so a value captured from one run, or typed out of this file, fits no other.
Node names are neutral on purpose: the worker's jail carries them in probe.py.
"""
from __future__ import annotations

import json

from pydantic import BaseModel

from bespokelabs import curator

from test_open import components_of, identity_for, importable, make_stub, run_hash_of, sym, NOW

TWELVE = (
    "backend",
    "backend_params",
    "batch_mode",
    "dataset_hash",
    "generation_params",
    "model_name",
    "parse_func_hash",
    "prompt_func_hash",
    "response_format",
    "return_completions_object",
    "run_id",
    "system_prompt",
)

# The knobs that change only how the work is done, and the four that change what
# comes back. `api_key` is in the first list deliberately.
NOT_IDENTITY = (
    ("max_retries", 99),
    ("request_timeout", 30),
    ("require_all_responses", False),
    ("batch_check_interval", 11),
    ("seconds_to_pause_on_rate_limit", 5),
    ("max_requests_per_minute", 4242),
    ("delete_successful_batch_files", True),
    ("api_key", "sk-rotated"),
)
IDENTITY = (
    ("azure_deployment", "deployment-b"),
    ("base_url", "https://y/v1"),
    ("batch_size", 7),
    ("completion_window", "48h"),
)


def prompt_one(row):
    return f"one: {row}"


def parse_two(row, response):
    return {"two": response}


class Answer(BaseModel):
    text: str
    score: int


class Batchy(curator.LLM):
    """A real LLM that resolves its backend from the model name alone.

    `batch=True` because the online OpenAI processor probes the provider for
    rate-limit headers as it is constructed; the batch processor does not, so
    this builds with no socket anywhere in reach.
    """

    def prompt(self, input):
        return f"Describe {input['topic']}."


# =============================================================================
# rule — twelve components, and how four of them are computed
# =============================================================================
def test_rule__component_set():
    importable()

    keys = sym("IDENTITY_COMPONENT_KEYS")
    assert tuple(keys) == TWELVE, f"IDENTITY_COMPONENT_KEYS is {tuple(keys)!r}"
    assert len(keys) == 12
    assert list(keys) == sorted(keys), "the twelve keys are declared in alphabetical order"

    components = components_of(identity_for(make_stub()))
    assert tuple(sorted(components)) == TWELVE, f"the identity was computed from {sorted(components)}"

    # The parse function participates exactly as the prompt function does.
    function_hash = sym("_get_function_hash")
    named = components_of(identity_for(make_stub(prompt_func=prompt_one, parse_func=parse_two)))
    assert named["prompt_func_hash"] == function_hash(prompt_one)
    assert named["parse_func_hash"] == function_hash(parse_two)
    assert named["parse_func_hash"] != named["prompt_func_hash"]
    assert components_of(identity_for(make_stub(parse_func=None)))["parse_func_hash"] == function_hash(None)

    # generation_params is always carried, as {} when there is nothing in it,
    # rather than being appended only when it is non-empty.
    for empty in (None, {}):
        assert components_of(identity_for(make_stub(generation_params=empty)))["generation_params"] == {}
    assert components_of(identity_for(make_stub(generation_params={"temperature": 0.7})))["generation_params"] == {"temperature": 0.7}

    # response_format is the compact, key-sorted schema, or the literal "text".
    assert components_of(identity_for(make_stub(response_format=None)))["response_format"] == "text"
    structured = components_of(identity_for(make_stub(response_format=Answer)))["response_format"]
    assert structured == json.dumps(Answer.model_json_schema(), sort_keys=True, separators=(",", ":"))

    # system_prompt and return_completions_object are carried as themselves.
    assert components_of(identity_for(make_stub(system_prompt=None)))["system_prompt"] is None
    assert components_of(identity_for(make_stub(system_prompt="be terse")))["system_prompt"] == "be terse"
    assert components_of(identity_for(make_stub(return_completions_object=True)))["return_completions_object"] is True
    assert components_of(identity_for(make_stub(return_completions_object=False)))["return_completions_object"] is False

    # ... and the two things the old fingerprint already had are still here.
    assert components_of(identity_for(make_stub(model_name="gpt-4o-mini")))["model_name"] == "gpt-4o-mini"
    assert components_of(identity_for(make_stub(batch_mode=True)))["batch_mode"] is True
    assert components_of(identity_for(make_stub(), dataset_hash="9f1c8e2b7d4a6053"))["dataset_hash"] == "9f1c8e2b7d4a6053"


# =============================================================================
# scope — the resolved backend, and a copy of the backend params
# =============================================================================
def test_scope__backend_resolution():
    importable()

    auto = Batchy(model_name="gpt-4o-mini", batch=True)          # backend= is None here
    declared = Batchy(model_name="gpt-4o-mini", backend="openai", batch=True)

    assert auto.backend == "openai", f"LLM.backend must be the resolved backend, got {auto.backend!r}"
    assert declared.backend == "openai"
    assert components_of(identity_for(auto, "d0"))["backend"] == "openai", "the auto-detect path must not hash a declared backend of None"
    assert components_of(identity_for(declared, "d0"))["backend"] == "openai"

    # The value is read off the object's own `backend`, whatever it says.
    assert components_of(identity_for(make_stub(backend="litellm")))["backend"] == "litellm"

    # backend_params is a copy of what __init__ was handed, {} when it was None.
    assert auto.backend_params == {}, f"backend_params must be {{}} when none were given, got {auto.backend_params!r}"
    given = {"batch_size": 3, "max_retries": 7}
    configured = Batchy(model_name="gpt-4o-mini", batch=True, backend_params=dict(given))
    assert configured.backend_params == given
    handed_out = configured.backend_params
    handed_out["batch_size"] = 999
    handed_out["injected"] = True
    assert configured.backend_params == given, "backend_params hands out a copy, not the dict the LLM is using"


# =============================================================================
# exclusions — four backend params are identity; the api key is not
# =============================================================================
def test_exclusions__backend_param_filter():
    importable()

    allowed = sym("IDENTITY_BACKEND_PARAM_KEYS")
    assert set(allowed) == {"azure_deployment", "base_url", "batch_size", "completion_window"}, f"the allowlist is {sorted(allowed)}"
    assert len(allowed) == 4

    plain = {"base_url": "https://x/v1"}
    baseline = run_hash_of(identity_for(make_stub(backend_params=dict(plain))))

    for key, value in NOT_IDENTITY:
        stub = make_stub(backend_params={**plain, key: value})
        carried = components_of(identity_for(stub))["backend_params"]
        assert key not in carried, f"{key} reached the identity components as {carried!r}"
        assert run_hash_of(identity_for(stub)) == baseline, f"changing {key} must not fork the cache directory"

    for key, value in IDENTITY:
        stub = make_stub(backend_params={**plain, key: value})
        carried = components_of(identity_for(stub))["backend_params"]
        assert carried.get(key) == value, f"{key} is identity and must be carried, got {carried!r}"
        assert run_hash_of(identity_for(stub)) != baseline, f"changing {key} must give a different run"

    # All eight non-identity knobs at once, and the four identity ones untouched.
    noisy = make_stub(backend_params={**plain, **dict(NOT_IDENTITY)})
    assert components_of(identity_for(noisy))["backend_params"] == plain
    assert run_hash_of(identity_for(noisy)) == baseline


# =============================================================================
# observability — the requirement's own table
# =============================================================================
def test_observability__stamp_contents(tmp_path):
    importable()

    params = {"base_url": "https://x/v1", "max_retries": 7, "api_key": "sk-secret", "request_timeout": 30}
    stub = make_stub(backend_params=dict(params))
    identity = identity_for(stub, "d0")
    components = components_of(identity)

    assert tuple(sorted(components)) == tuple(sym("IDENTITY_COMPONENT_KEYS"))
    assert len(components) == 12
    assert components["backend_params"] == {"base_url": "https://x/v1"}

    serialised = json.dumps(components, sort_keys=True, default=repr)
    assert "sk-secret" not in serialised, f"the api key is written down in the components: {serialised}"

    write_run_stamp = sym("write_run_stamp")
    write_run_stamp(tmp_path / "run", identity, now=NOW)
    stamp_text = (tmp_path / "run" / "run_identity.json").read_text()
    assert "sk-secret" not in stamp_text, "the stamp file is cleartext on disk, so the api key must never be a component"
    assert "https://x/v1" in stamp_text

    rotated = make_stub(backend_params={"base_url": "https://x/v1", "max_retries": 999, "api_key": "sk-other"})
    assert run_hash_of(identity_for(rotated, "d0")) == run_hash_of(identity), "rotating the key or the retry budget is the same run"

    for changed in (
        make_stub(backend_params=dict(params), parse_func=parse_two),
        make_stub(backend_params=dict(params), system_prompt="be terse"),
        make_stub(backend_params=dict(params), return_completions_object=True),
        make_stub(backend_params=dict(params), backend="litellm"),
    ):
        assert run_hash_of(identity_for(changed, "d0")) != run_hash_of(identity), f"{changed} must be a different run"

    # Two ways of saying the same backend are the same run.
    auto = Batchy(model_name="gpt-4o-mini", batch=True)
    declared = Batchy(model_name="gpt-4o-mini", backend="openai", batch=True)
    assert run_hash_of(identity_for(auto, "d0")) == run_hash_of(identity_for(declared, "d0"))
