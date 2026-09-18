"""g4 — the INPUTS of one grading run, derived from the seed root chose.

Stdlib only, and imported by both sides: the worker gets it in the jail (it has
to build the scenarios), the judge gets it beside `judge.py` (it has to know what
was asked in order to work out what the answer should have been). One
derivation, so the two cannot drift.

WHY A SEED AT ALL. The worker/judge split stopped the worker rewriting the
verdict; it did not stop the worker inventing the values the judge reads. The
old g4 fixture was the same every run — one dataset hash, one run id, one base
URL, one api key, one list of knob values — so every run hash, every component and
every stamp was the same too, and an observations file captured from one
correct run (or typed out of the requirement) passed on a tree that implemented
nothing. So every value the identity is computed FROM moves here: the model
name, the dataset hash, the generation params, the system prompt, the
structured response model, the prompt and parse functions, the base URL, the
api key, every backend knob's value, which knobs are combined, the run ids, the
rows. The run hashes follow them, and the judge checks the components they are
computed from against these inputs rather than against a literal.

WHAT MAY NOT LIVE HERE. Expected outputs and the answers the hidden requirements
fix: which components the identity has, which backend knobs are identity, the
shape of a cache-disabled run hash, where a default run id comes from, the stamp
file's name. `KNOBS` names the backend parameters a scenario varies — they are
the question, not the answer — and says nothing about which of them fork the
cache; the judge alone holds that partition.

Words are drawn at variable width on purpose: they are spelled into the
components, so the canonical payload and every digest move with them
(tasks/lessons.md, 2026-09-14: "randomising an input that does not change the
answer is decoration").
"""
from __future__ import annotations

import random

_ALPHABET = "abcdefghijkmnpqrstuvwxyz"

# The backend parameters the exclusions scenarios vary, in no meaningful order,
# with the kind of value each takes. Nothing here says which fork the cache.
KNOBS = {
    "api_key": "secret",
    "azure_deployment": "word",
    "base_url": "url",
    "batch_check_interval": "int",
    "batch_size": "int",
    "completion_window": "window",
    "delete_successful_batch_files": "bool",
    "max_requests_per_minute": "int",
    "max_retries": "int",
    "request_timeout": "int",
    "require_all_responses": "bool",
    "seconds_to_pause_on_rate_limit": "int",
}

# Models the auto-detect path resolves without a network: the backend is chosen
# from the name, so these must be names the resolver already knows.
_KNOWN_MODELS = ("gpt-4o-mini", "gpt-4o", "gpt-4.1-nano", "gpt-4.1-mini")

# The only backend params a real batch LLM accepts at construction; a stub takes
# anything, a real `LLM` validates against its processor's config.
_BATCH_PARAMS = ("max_retries", "batch_check_interval", "batch_size")


def _word(rnd: random.Random, lo: int = 3, hi: int = 11) -> str:
    return "".join(rnd.choice(_ALPHABET) for _ in range(rnd.randint(lo, hi)))


def _text(rnd: random.Random) -> str:
    return " ".join(_word(rnd) for _ in range(rnd.randint(1, 4)))


def _hex(rnd: random.Random, lo: int = 8, hi: int = 24) -> str:
    return "".join(rnd.choice("0123456789abcdef") for _ in range(rnd.randint(lo, hi)))


def _value(rnd: random.Random, kind: str):
    if kind == "secret":
        return "sk-" + _word(rnd, 8, 24)
    if kind == "word":
        return _word(rnd, 4, 14)
    if kind == "url":
        return f"https://{_word(rnd, 3, 10)}.example.test/v{rnd.randint(1, 9)}"
    if kind == "int":
        # Two digits at least. The judge strikes every component value out of the
        # hashed payload and asks what is left to name the identity version; a
        # one-character value is ambiguous with that tag, so it is neither struck
        # out (it could BE the tag) nor trustworthy if it stays. Drawing 10 and up
        # removes the ambiguity, and no fact depends on the magnitude.
        return rnd.randint(10, 99_999)
    if kind == "window":
        return f"{rnd.randint(2, 96)}h"
    if kind == "bool":
        return rnd.random() < 0.5
    raise ValueError(kind)


def _fresh(rnd: random.Random, kind: str, avoid):
    while True:
        value = _value(rnd, kind)
        if value not in avoid:
            return value


def _run_id(rnd: random.Random, taken) -> str:
    while True:
        value = f"{_word(rnd, 2, 8)}-{rnd.randint(1, 10 ** rnd.randint(1, 6))}"
        if value not in taken:
            taken.add(value)
            return value


def _function(rnd: random.Random, prefix: str, arity: int) -> dict:
    """A function a scenario builds from source: its name and body text move, so
    its `_get_function_hash` does too."""
    args = "row" if arity == 1 else "row, response"
    return {"name": f"{prefix}_{_word(rnd, 3, 9)}", "args": args, "body": _text(rnd)}


# Names a pydantic BaseModel already owns. A drawn field spelled like one of
# these does not build a model at all, so the scenario would fail on the draw
# rather than on the submission. It is a 1-in-10^5 draw and it happened to
# nobody, but a flake a reviewer can name is a finding either way, and refusing
# the word costs one comparison.
_RESERVED_FIELD_NAMES = frozenset({
    "dict", "json", "copy", "schema", "schema_json", "construct", "validate",
    "fields", "parse_obj", "parse_raw", "parse_file", "from_orm", "update_forward_refs",
})


def _model(rnd: random.Random) -> dict:
    """A structured response model: a class name and 1-3 typed fields."""
    names = []
    while len(names) < rnd.randint(1, 3):
        name = _word(rnd, 3, 9)
        if name not in names and name not in _RESERVED_FIELD_NAMES:
            names.append(name)
    return {"name": _word(rnd, 4, 10).capitalize(),
            "fields": [[name, rnd.choice(["str", "int", "float", "bool"])] for name in names]}


def derive(seed: str) -> dict:
    """Every input this run uses, as a plain dict. Same seed, same dict."""
    rnd = random.Random(seed)
    spec: dict = {"seed": seed}

    # ---- the stub every identity scenario starts from -------------------------
    spec["model"] = f"m-{_word(rnd, 3, 11)}"
    spec["alt_model"] = f"m-{_word(rnd, 13, 20)}"
    spec["dataset_hash"] = _hex(rnd)
    spec["alt_dataset_hash"] = _hex(rnd, 25, 31)
    gen = {}
    while len(gen) < rnd.randint(1, 3):
        gen[_word(rnd, 3, 10)] = round(rnd.uniform(0, 2), rnd.randint(1, 4))
    spec["generation_params"] = gen
    spec["system_prompt"] = _text(rnd)
    spec["prompt_fn"] = _function(rnd, "prompt", 1)
    spec["parse_fn"] = _function(rnd, "parse", 2)
    spec["response_model"] = _model(rnd)
    spec["stub_backend"] = _word(rnd, 4, 13)
    spec["batch_mode"] = rnd.random() < 0.5

    # ---- backend params ----------------------------------------------------
    spec["plain_url"] = _value(rnd, "url")
    knobs = list(KNOBS)
    rnd.shuffle(knobs)
    spec["knob_order"] = knobs
    spec["knob_values"] = {k: _fresh(rnd, KNOBS[k], {spec["plain_url"]}) for k in knobs}
    subsets = []
    for _ in range(rnd.randint(3, 6)):
        chosen = rnd.sample(knobs, rnd.randint(2, len(knobs)))
        subsets.append({k: _fresh(rnd, KNOBS[k], {spec["plain_url"]}) for k in chosen})
    spec["knob_subsets"] = subsets

    # ---- the stamp scenario --------------------------------------------------
    spec["stamp_params"] = {
        "base_url": _value(rnd, "url"),
        "max_retries": _value(rnd, "int"),
        "api_key": _value(rnd, "secret"),
        "request_timeout": _value(rnd, "int"),
    }
    spec["rotated_params"] = {
        "base_url": spec["stamp_params"]["base_url"],
        "max_retries": _fresh(rnd, "int", {spec["stamp_params"]["max_retries"]}),
        "api_key": _fresh(rnd, "secret", {spec["stamp_params"]["api_key"]}),
        "request_timeout": _fresh(rnd, "int", {spec["stamp_params"]["request_timeout"]}),
    }
    spec["stamp_now"] = (f"20{rnd.randint(26, 39)}-{rnd.randint(1, 9):02d}-{rnd.randint(1, 28):02d}"
                         f"T{rnd.randint(0, 23):02d}:{rnd.randint(0, 59):02d}:{rnd.randint(0, 59):02d}")

    # ---- real LLMs ------------------------------------------------------------
    spec["known_model"] = rnd.choice(_KNOWN_MODELS)
    spec["llm_params"] = {k: _value(rnd, "int") for k in rnd.sample(_BATCH_PARAMS, rnd.randint(1, 3))}
    spec["mutation"] = [_word(rnd, 5, 13), _value(rnd, "int")]
    # A model name the openai backend is DECLARED for, so it need not be known.
    spec["call_model"] = f"{rnd.choice(_KNOWN_MODELS)}-{_word(rnd, 3, 10)}"
    spec["rows"] = [{"topic": _text(rnd)} for _ in range(rnd.randint(1, 3))]

    # ---- run ids ----------------------------------------------------------------
    taken: set = set()
    for name in ("id_rule", "id_rule_other", "id_env", "id_explicit", "id_refused",
                 "id_control", "id_obs", "id_obs_other", "id_probe"):
        spec[name] = _run_id(rnd, taken)
    _assert_invariants(spec)
    return spec


def _assert_invariants(spec: dict) -> None:
    """The properties of a draw the suite's facts are allowed to assume.

    Reproducibility is the point of the seed, and the defence of it is that the
    REWARD does not move even though the inputs do. That only holds while every
    draw has the shape the facts expect: a fact that asks "does the hash move
    when only the model does" is meaningless on a run that drew the same model
    twice. Each of these is already impossible by construction above — they are
    a drift guard, not a filter — so if one ever fires it is a bug in this file,
    and both sides derive from the same seed, so both fail here, loudly, with the
    defect named, instead of reporting a mysteriously failing fact.
    """
    def need(cond, why):
        if not cond:
            raise AssertionError(f"fixture_spec drew a degenerate run for seed {spec['seed']!r}: {why}")

    need(spec["model"] != spec["alt_model"], "the two model names are the same")
    need(spec["dataset_hash"] != spec["alt_dataset_hash"], "the two dataset hashes are the same")
    need(spec["prompt_fn"] != spec["parse_fn"], "the prompt and parse functions are identical")
    fields = [name for name, _ in spec["response_model"]["fields"]]
    need(len(fields) == len(set(fields)), f"the response model has duplicate fields {fields}")
    need(not set(fields) & _RESERVED_FIELD_NAMES, f"a response model field shadows a BaseModel attribute: {fields}")
    need(set(spec["knob_values"]) == set(KNOBS), "a backend knob was drawn no value")
    need(spec["plain_url"] not in spec["knob_values"].values(), "a knob was drawn the plain base_url")
    need(spec["stamp_params"]["base_url"] == spec["rotated_params"]["base_url"],
         "the rotated params moved the base_url, which is the one knob that must not move")
    need(all(spec["stamp_params"][k] != spec["rotated_params"][k]
             for k in ("max_retries", "api_key", "request_timeout")),
         "a rotated knob kept its old value, so the rotation scenario proves nothing")
    ids = [spec[k] for k in spec if k.startswith("id_")]
    need(len(ids) == len(set(ids)), "two run ids collided")
    # Every drawn value is spelled with at least two characters (see `_value`):
    # the judge strikes the component values out of the hashed payload to see
    # what is left naming the identity version, and a one-character value is
    # ambiguous with that tag.
    thin = [v for v in list(spec["knob_values"].values()) + list(spec["stamp_params"].values())
            + [spec["model"], spec["dataset_hash"], spec["plain_url"]] if len(str(v)) < 2]
    need(not thin, f"a drawn value is a single character: {thin}")


# ---------------------------------------------------------------------------
# scenarios both sides enumerate
# ---------------------------------------------------------------------------
# Override values starting "@" are recipes the worker builds (probe_support.resolve)
# and the judge reads back through the worker's own reference for them.
def component_variants(spec: dict) -> list:
    """[label, stub overrides, dataset hash]: one stub per way a component can move."""
    dh = spec["dataset_hash"]
    return [
        ["base", {}, dh],
        ["named", {"prompt_func": "@prompt", "parse_func": "@parse"}, dh],
        ["parse_absent", {"prompt_func": "@prompt", "parse_func": None}, dh],
        ["gen_none", {"generation_params": None}, dh],
        ["gen_empty", {"generation_params": {}}, dh],
        ["structured", {"response_format": "@model"}, dh],
        ["prompted", {"system_prompt": spec["system_prompt"]}, dh],
        ["completions", {"return_completions_object": True}, dh],
        ["batched", {"batch_mode": True}, dh],
        ["renamed", {"model_name": spec["alt_model"]}, dh],
        ["other_data", {}, spec["alt_dataset_hash"]],
    ]


def knob_scenarios(spec: dict) -> list:
    """[label, backend_params]: the plain params, each knob alone, drawn subsets, all."""
    plain = {"base_url": spec["plain_url"]}
    out = [["plain", dict(plain)]]
    for key in spec["knob_order"]:
        out.append([f"knob:{key}", {**plain, key: spec["knob_values"][key]}])
    for i, subset in enumerate(spec["knob_subsets"]):
        out.append([f"subset:{i}", {**plain, **subset}])
    out.append(["every", {**plain, **spec["knob_values"]}])
    return out


def changed_stamp_stubs(spec: dict) -> list:
    """Overrides that each move exactly one thing away from the stamp scenario's stub."""
    return [
        {"parse_func": "@parse"},
        {"system_prompt": spec["system_prompt"]},
        {"return_completions_object": True},
        {"backend": spec["stub_backend"]},
    ]
