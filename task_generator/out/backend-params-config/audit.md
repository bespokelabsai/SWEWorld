# Audit — g12 (backend-params-config)

| fact | bracket | audit | why |
|---|---|---|---|
| `g12.r1.rule` | hidden | **narrow** | Narrow the graded fact, or add the one probe that makes its mechanism clause visible. Pick one:

(A) Narrow -- preferred if you want to spend nothing. Restate r |
| `g12.r1.scope` | hidden | **narrow** | Narrow the fact to the intersection rule alone and stop double-counting it. Concretely: (1) delete the \"iterated in the fixed order Batch, Online, Offline\" cl |
| `g12.r1.failure_behavior` | hidden | **narrow** | Narrow the fact to its residue and re-point the two constraint-dependent probes.

1. Cut from the fact text the clauses r1.rule already entails and r1.observabi |
| `g12.r1.observability` | hidden | **cut** | Cut r1.observability as a separate fact, and salvage its two non-redundant assertions into the siblings that own those channels. Coverage does not shrink.

(1)  |
| `g12.r2.rule` | hidden | **retest** | Keep the fact — the divergent action is real and no blind implementation I can construct hits the invented field name, exclude=True and report-not-raise contrac |
| `g12.r2.scope` | hidden | **cut** | Cut `r2.scope` as written; it adds no bits over `r2.rule` and `r2.observability`. If you want to keep a fact here rather than drop it, it must be bought from `r |
| `g12.r2.exclusions_or_crossover` | hidden | **retest** | Fix the fact and the test, then re-run condition 1 with rule revealed.

1. Delete "and no litellm import" from the fact. It has no observable — `config.py` hold |
| `g12.r2.failure_behavior` | hidden | **retest** | Retest — keep the fact, fix the test. (1) Delete the `patch_lookup(monkeypatch, value=[])` block from `test_failure_behavior__a_broken_or_empty_lookup_leaves_an |
| `g12.r2.observability` | hidden | **retest** | Keep r2; fix the observability test. Four concrete changes:

1. Delete the duplicated assertions from `test_observability`: `assert FIELD not in config.model_du |

## g12.r1.rule — narrow

**Divergent action.** In config.py, a new exception class plus a name-scan that runs before any config is constructed:

```python
class BackendParamError(ValueError):
    def __init__(self, params: tuple[str, ...], expected: str, belongs_to: tuple[str, ...]) -> None:
        self.params = params
        self.expected = expected
        self.belongs_to = belongs_to
        tail = " or ".join(belongs_to) if belongs_to else "no request processor config"
        super().__init__(
            f"backend_params {', '.join(params)} not accepted by {expected}; accepted by {tail}"
        )


def _validate_backend_params(params, batch=False, backend=None):
    cls = _MODE_CONFIGS[_resolve_mode(batch, backend)]
    offending = tuple(sorted(k for k in params if k not in cls.model_fields))
    if offending:
        belongs_to = tuple(
            other.__name__
            for other in (BatchRequestProcessorConfig, OnlineRequestProcessorConfig, OfflineRequestProcessorConfig)
            if other is not cls and all(k in other.model_fields for k in offending)
        )
        raise BackendParamError(offending, cls.__name__, belongs_to)
    return cls(**_remove_none_values(params))
```

A ticket-only agent writes the last line and nothing above it: the ticket asks only that `_validate_backend_params` "validates `params` against `_MODE_CONFIGS[_resolve_mode(batch, backend)]` only and returns an instance of that class", and `extra = "forbid"` already rejects wrong-mode keys with a pydantic `ValidationError`. The class name, the three-argument constructor, the attribute names, and the pre-construction scan are all invented only by an agent who saw the clue.

**The assertion.** The pair that uniquely decides this fact rather than a sibling:

```python
early = raised_by({"batch_size": 100}, batch=False)
assert early.params == ("batch_size",)
assert early.expected == "OnlineRequestProcessorConfig"
```

It depends on more than this requirement. (1) `expected` is `_MODE_CONFIGS[_resolve_mode(False, None)].__name__`, so an agent who mis-builds `_resolve_mode` or `_MODE_CONFIGS` -- both purely open-ticket work -- fails this assertion for reasons unrelated to r1. (2) It depends on `test_open.sym("BackendParamError")` failing rather than skipping when the symbol is absent; I could not read `test_open.py` to confirm, and if `sym` skips, the blind condition reports skip rather than fail. (3) It does *not* depend on the clause it was written to test: as shown in Catalog B, a construct-first implementation satisfies it.

**Catalog A.** clean

**Catalog B.**
- `behaviour_has_no_consequence` — The clause "It is raised before pydantic runs, so no config object is constructed and no `ValidationError` is produced" has no observable in this test. A construct-then-translate implementation -- call `cls(**params)`, catch `ValidationError`, keep `e['loc'][0] for e in err.errors() if e['type'] == 'extra_forbidden'`, raise `BackendParamError` from those -- passes every probe. On `raised_by({"batch_size": 100}, batch=False)` pydantic reports both `missing` for `model` and `extra_forbidden` for `batch_size`; filtering to extras yields `early.params == ("batch_size",)` and `early.expected == "OnlineRequestProcessorConfig"`, which is exactly what the comment "an implementation that validated first would have to report that too -- or report it instead" was meant to catch, and does not. Likewise `mixed` filters to `("max_requests_per_minute",)` with `"request_timeout" not in str(mixed)`, and the no-extras probes re-raise the ValidationError unchanged. Since a failed field validation never reaches r2's `model_post_init`, the discarded half-built config leaves no trace either.

**Recommendation.** Narrow the graded fact, or add the one probe that makes its mechanism clause visible. Pick one:

(A) Narrow -- preferred if you want to spend nothing. Restate r1.rule as: "`_validate_backend_params` raises `BackendParamError(ValueError)` -- defined in `config.py` with `def __init__(self, params: tuple[str, ...], expected: str, belongs_to: tuple[str, ...])` storing those three under those names -- instead of a pydantic `ValidationError`, and it reports the offending keys even when a required field such as `model` is also missing." Drop "It is raised before pydantic runs, so no config object is constructed and no `ValidationError` is produced" from the graded text; that mechanism has no observable and currently lets a construct-then-filter implementation score as correct.

(B) Retest -- preferred if the pre-pydantic ordering is the point of the clue. Keep the clause and add a probe that watches for construction, e.g. in `test_rule`:

```python
def test_rule__nothing_is_constructed(monkeypatch):
    import config
    real = config.OnlineRequestProcessorConfig
    class Tripwire(real):
        def __init__(self, **kw):
            raise AssertionError("config was constructed")
    monkeypatch.setitem(config._MODE_CONFIGS, "online", Tripwire)
    error = raised_by({"batch_size": 100}, batch=False)
    assert error.params == ("batch_size",)
```

`Tripwire` inherits `model_fields`, so the name scan is unaffected, but any implementation that validates first dies with `AssertionError` rather than `BackendParamError`. Note this requires the implementation to read `_MODE_CONFIGS` at call time, which the ticket already mandates -- if you would rather not bind that, assert on a `model_validate`/`__init__` call counter instead.

Two smaller fixes, whichever you pick. Delete `assert not issubclass(cls, ValidationError)` and `assert not isinstance(error, ValidationError)` (and `assert isinstance(first, ValueError) is True` in `observability`): pydantic v2's `ValidationError` is a Rust type that cannot be subclassed, so no Python class can ever fail them -- the discrimination is carried entirely by `pytest.raises(cls)`. And in the sibling `scope`, no probe yields a `belongs_to` containing both the online and offline names, so the mandated fixed order `Batch, Online, Offline` is indistinguishable from `sorted()` (Batch < Offline < Online); add a key declared by both online and offline but not batch, or accept that the ordering clause is untested.

One thing I could not do: I have no file access in this session, so I did not run the suite, read `test_open.py`, or confirm the field membership the probes assume (`batch_size` absent from the online class, `max_requests_per_minute` absent from batch, `request_timeout` constrained on batch). Verify those three before acting on this.


## g12.r1.scope — narrow

**Divergent action.** `belongs_to = tuple(c.__name__ for c in (BatchRequestProcessorConfig, OnlineRequestProcessorConfig, OfflineRequestProcessorConfig) if c is not target and all(k in c.model_fields for k in offending))` — specifically the `all(...)` quantifier over the offending-key set (rather than `any(...)`), evaluated with a pure `k in c.model_fields` name test and with the mode's own class excluded. A ticket-only agent writes no such expression at all, because it writes no `BackendParamError`; but among clue-informed agents the `all` vs `any` choice is the only genuinely divergent line this fact owns.

**The assertion.** `assert both.belongs_to == ()` (for `{\"model\": \"gpt-4o\", \"max_requests_per_minute\": 600, \"tensor_parallel_size\": 2}`, batch=True) — the one assertion separating an intersection from a union. Passing it depends on more than this requirement: on sibling `rule` (the class must exist and be raised at all, via `sym(\"BackendParamError\")`), on the ticket's `_resolve_mode`/`_MODE_CONFIGS`, and on the repo fact that `max_requests_per_minute` and `tensor_parallel_size` are declared by exactly one class each. It is also duplicated by sibling `observability`'s `assert second.belongs_to == ()`, so no implementation fails it alone.

**Catalog A.**
- `codebase_already_does_it` — The clause "offending keys are decided by name only, against `_MODE_CONFIGS[mode].model_fields`" is precisely what the reused `class Config: extra = "forbid"` (ticket: "Reuse as-is: the four pydantic config classes, their `class Config: extra = \"forbid\"` (lines 38-41)") already computes: extra-forbid rejects unknown keys by name and never type-checks them. The key-selection half of this fact is inherited from code the ticket orders the agent to keep.
- `prohibition_satisfied_by_inaction` — "values are never type-checked or trial-validated for this" forbids deliberate extra work (constructing each candidate class with the params and catching ValidationError) that no engineer writes when `k in c.model_fields` is one line. The `by_name` probe (`batch_size: -5` -> belongs_to includes Offline) can only fail an implementation that went out of its way to trial-validate.
- `ticket_gives_it_away` — The "fixed order `BatchRequestProcessorConfig`, `OnlineRequestProcessorConfig`, `OfflineRequestProcessorConfig`" is verbatim the insertion order of the ticket's own literal `_MODE_CONFIGS = {"batch": Batch..., "online": Online..., "offline": Offline...}`; anyone iterating `_MODE_CONFIGS.values()` gets it for free. Likewise `expected` being the class for the resolved mode restates the ticket's "validates `params` against `_MODE_CONFIGS[_resolve_mode(batch, backend)]` only", which is what `offline_side.expected == "OfflineRequestProcessorConfig"` measures.
- `obvious_implementation_does_it` — For the membership half yes: the obvious scan is `unknown = [k for k in params if k not in cls.model_fields]`, which is by name and never trial-validates. For the intersection half no: given the sibling's message `"accepted by A or B"`, the obvious reading of a disjunctive "or" is a union (`any`), which the test rejects.

**Catalog B.**
- `observable_belongs_to_another_fact` — Every implementation error scope can catch is already caught by sibling `observability`: a union implementation fails scope's `assert both.belongs_to == ()` AND observability's `assert second.belongs_to == ()`; a trial-validating implementation fails scope's `by_name` AND observability's `assert first.belongs_to == ("BatchRequestProcessorConfig", "OfflineRequestProcessorConfig")` (the requirement itself flags this: "offline keeps its place even though \"auto\" is not a legal value for it"). Scope is graded through observability's channel.
- `no_independent_content` — Strip what `observability` measures (intersection, no-trial-validation) and what the ticket entails (`_MODE_CONFIGS` order, `expected` = class for `_resolve_mode`), and the only assertion left that is unique to scope is `offline_side.expected == "OfflineRequestProcessorConfig"`, i.e. that `vllm` beats `batch=True` — an open-feature fact. Also note the whole test is gated on `sym("BackendParamError")`, so it cannot fail independently of sibling `rule`.

**A blind build that passes anyway:**

```
null — a ticket-only implementation cannot pass. The test's first act is `sym(\"BackendParamError\")`, and nothing in the visible ticket hints that any such class exists; the ticket's stated path for an unknown key is the reused `class Config: extra = \"forbid\"`, i.e. a pydantic ValidationError. Note this makes the bracket's \"hidden\" verdict uninformative for THIS fact: all four r1 facets fail blind for the identical reason (missing class), so the bracket measured r1.rule four times, not scope once.
```

**A correct build the test rejects:**

```
null — I could not build an implementation faithful to the fact's own wording (\"whose `model_fields` contain **every** offending key — an intersection, never a union\") that the test rejects; that wording is unambiguous, and the `(Batch, Offline)` answers the suite asserts are order-invariant, so an agent using sorted order or `_MODE_CONFIGS` order both pass. The live unfairness risk is upstream of the test: the sibling-mandated message `f\"...; accepted by {' or '.join(belongs_to)}\"` reads as a disjunction, and the requirement's headline example (`batch_size` -> Batch and Offline) is a case where union and intersection agree — so a clue built on that message plus that example does NOT imply the intersection, and an agent who reasonably writes `any(...)` loses scope AND observability for one misreading. I could not read the clue files (all file tools disabled this session) to check whether the clue states the intersection outright.
```

**Recommendation.** Narrow the fact to the intersection rule alone and stop double-counting it. Concretely: (1) delete the \"iterated in the fixed order Batch, Online, Offline\" clause from the fact, or add a probe whose answer is `{Online, Offline}` (a key declared by Online and Offline but not Batch, probed in batch mode) — as written every multi-element `belongs_to` in the suite is `(\"BatchRequestProcessorConfig\", \"OfflineRequestProcessorConfig\")`, identical under insertion order, alphabetical order and dict order, so the order clause is unmeasured. (2) Delete \"values are never type-checked or trial-validated\" from the fact and drop scope's `by_name` probe, or accept it as decorative: no plausible implementation trial-validates, and observability's `first` already kills the one that would. (3) Give scope exclusive ownership of the union/intersection decision by changing observability's second probe to assert only `second.params == (\"batch_size\", \"nope\", \"tensor_parallel_size\")` and removing its `assert second.belongs_to == ()`; leave `assert both.belongs_to == ()` in scope as the single grading site. (4) Fix the test docstring: \"an intersection over the other three classes\" — there are two other classes, not three. (5) Separately verify the clue asserts the intersection explicitly; the mandated `\" or \"`-joined message argues for a union and the requirement's own headline example cannot distinguish the two.


## g12.r1.failure_behavior — narrow

**Divergent action.** The empty-`belongs_to` branch in the message builder, and only that:

```python
class BackendParamError(ValueError):
    def __init__(self, params, expected, belongs_to):
        self.params, self.expected, self.belongs_to = params, expected, belongs_to
        tail = " or ".join(belongs_to) if belongs_to else "no request processor config"
        super().__init__(f"backend_params {', '.join(params)} not accepted by {expected}; accepted by {tail}")
```

The `if belongs_to else "no request processor config"` arm is the one expression an agent that saw only r1.rule/r1.scope/r1.observability does not write — the plain f-string the spec quotes yields `"...; accepted by "` for an empty tuple, so the branch has to be added deliberately. Everything else this fact asserts (collecting all keys, `sorted`, raising before pydantic, letting ValidationError through) is code a rule-informed agent already writes. Against a truly ticket-only agent the divergent action is the whole class, but that divergence is r1.rule's, not this fact's.

**The assertion.** ```python
assert str(many) == (
    "backend_params alpha_knob, zeta_knob not accepted by BatchRequestProcessorConfig; "
    "accepted by no request processor config"
)
```
It is the only assertion in this test that a correct implementation of r1.rule + r1.scope + r1.observability can still fail. And no, it does not depend solely on this requirement: it also depends on `BackendParamError` existing at all (r1.rule), on `expected` being the mode class's `__name__` and `belongs_to` being the intersection (r1.scope), and on `_resolve_mode(batch=True, None) == "batch"` from the open ticket. Two other assertions in the same test — `vbp({"model": "gpt-4o", "request_timeout": 0}, batch=True)` and `vbp({"model": "gpt-4o", "max_retries": -1}, batch=True)` raising with exactly one error — depend on numeric constraints on pre-existing fields that the ticket declares out of scope and whose enforcement sits in code the ticket orders deleted.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — "If every key is a field of the mode's class but a value is invalid, the `pydantic.ValidationError` propagates unchanged — not caught, not wrapped, not converted." Satisfied by writing no try/except around the construction call. Violating it requires deliberate extra work no engineer here was going to do; the test cannot distinguish restraint from never having considered it.
- `entailed_by_the_open_feature` — Scoped to the graded unit: given r1.rule's "It is raised before pydantic runs, so no config object is constructed and no `ValidationError` is produced for the wrong-mode case", this fact's clause "The unknown-key scan runs first, so a call carrying both an unknown key and an invalid value raises `BackendParamError` naming only the unknown key" is a strict corollary — there is no implementation of rule that fails it. It is a restatement, not a separate fact.
- `obvious_implementation_does_it` — r1.rule/r1.scope hand the agent the constructor signature `params: tuple[str, ...]` and `_MODE_CONFIGS[mode].model_fields`. The single natural body is `tuple(sorted(set(params) - set(cls.model_fields)))` — all keys, and `sorted` because a set difference has no stable order. "All offending keys are reported together, sorted ascending by `str`, never just the first" falls out of normal engineering instinct once the plural tuple field exists.

**Catalog B.**
- `observable_belongs_to_another_fact` — Three of four clauses are asserted literally by r1.observability, not here: sorted-all-keys is `second.params == ("batch_size", "nope", "tensor_parallel_size")`; scan-first is `third.params == ("batch_size",)`; propagate-unchanged is the `fourth` probe with `loc == ("max_retries",)`. Even the ` or ` separator is measured only by observability's `str(first)` — this test's non-empty probe `str(one)` has a one-element `belongs_to`, where `' or '.join` and `', '.join` are indistinguishable. Additionally `many.belongs_to == ()` and `mixed.params` duplicate r1.scope's channel.
- `no_independent_content` — After removing what r1.rule entails and what r1.observability asserts verbatim, the unique residue is a single string literal: the tail `"; accepted by no request processor config"` when `belongs_to` is empty. Everything else in the fact fails or passes exactly when a neighbour does.

**A correct build the test rejects:**

```
Conditional on a repo detail I could not open a shell to check, but it is the ticket's own instruction that creates it. The ticket says:

> "Delete `RequestProcessorConfig.__post_init__` (line 43) ... A pydantic v2 `BaseModel` never calls them, so all three are dead today." and "Re-express **the batch-size rule** as a `field_validator(\"batch_size\")`" — only that one rule — and "Out of scope: the meanings of `max_retries` and `seconds_to_pause_on_rate_limit`."

An agent that does exactly this, and whose r1 implementation is flawless:

```python
class RequestProcessorConfig(BaseModel):
    # __post_init__ deleted per ticket; nothing re-expressed but batch_size, per ticket
    ...
```

If `max_retries >= 0` or `request_timeout > 0` lived in that dead line-43 hook rather than in a `Field(...)` — which the ticket's otherwise-unmotivated carve-out naming `max_retries` hints at — then

```python
with pytest.raises(ValidationError) as bad_value:
    vbp({"model": "gpt-4o", "request_timeout": 0}, batch=True)
```

returns a config instead of raising, and this fact fails on an implementation that got r1 entirely right and followed the visible ticket to the letter. The grading of r1.failure_behavior should not be gated on the agent's handling of a deletion the ticket ordered in a different section.
```

**Recommendation.** Narrow the fact to its residue and re-point the two constraint-dependent probes.

1. Cut from the fact text the clauses r1.rule already entails and r1.observability already measures: "The unknown-key scan runs first, so a call carrying both an unknown key and an invalid value raises `BackendParamError` naming only the unknown key" (corollary of rule's "raised before pydantic runs") and "If every key is a field of the mode's class but a value is invalid, the `pydantic.ValidationError` propagates unchanged" (prohibition-by-inaction, and observability's fourth probe). Keep this fact as: *all offending keys at once, sorted ascending by `str`; and the exact message in both forms, with the empty-`belongs_to` tail being exactly `"; accepted by no request processor config"`.*

2. In the test, delete `mixed`, the `bad_value` block, and `many.belongs_to == ()` (scope's). Keep `many.params`, `str(many)`, and `str(one)`.

3. Make the non-empty message probe discriminating: `str(one)` currently has a one-element `belongs_to`, so `', '.join` passes it. Replace it with a two-element case, e.g. `str(raised_by({"model": "gpt-4o", "batch_size": -5}, batch=False))` must equal `"backend_params batch_size not accepted by OnlineRequestProcessorConfig; accepted by BatchRequestProcessorConfig or OfflineRequestProcessorConfig"`, so the ` or ` separator is actually measured here rather than only in observability.

4. If any ValidationError probe is kept anywhere in r1, source it from a constraint this task itself creates rather than from a pre-existing field the ticket declares out of scope: use `vbp({"model": "gpt-4o", "batch_size": "AUTO"}, batch=True)`, which the ticket guarantees raises with one error at `loc == ("batch_size",)` via the new `field_validator`. Drop `request_timeout: 0` and `max_retries: -1` from r1 entirely.

Before shipping, confirm by inspection whether `max_retries`/`request_timeout` constraints live in `Field(...)` or in the line-43 `__post_init__` the ticket deletes; if the latter, step 4 is mandatory, not optional.


## g12.r1.observability — cut

**Divergent action.** *none named*

**The assertion.** assert str(first) == ("backend_params batch_size not accepted by OnlineRequestProcessorConfig; accepted by BatchRequestProcessorConfig or OfflineRequestProcessorConfig") -- the only assertion in the file that exercises the two-element form of the message tail. Yes, it depends on things other than this requirement: it depends on r1.scope's belongs_to intersection producing exactly two names in the fixed order, on r1.failure_behavior's f-string, and on r1.rule's BackendParamError existing at all (the `raised_by` helper calls `param_error()` -> `sym("BackendParamError")`, so every assertion in this test aborts if rule is unimplemented). It cannot fail for a reason attributable to this fact alone.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — Partially, for the negative halves of probes 3 and 4. `assert not isinstance(fourth.value, cls)` and `len(fourth.value.errors()) == 1` are satisfied by simply not catching and not wrapping -- the failure_behavior spec's own words, 'not caught, not wrapped, not converted'. An agent has to take deliberate action to FAIL these two; they test restraint the agent was never going to break.

**Catalog B.**
- `observable_belongs_to_another_fact` — Every channel is a sibling's. Probe 1's belongs_to duplicates scope's `by_name = raised_by({"model": "gpt-4o", "batch_size": -5}, batch=False)` -> `belongs_to == ("BatchRequestProcessorConfig", "OfflineRequestProcessorConfig")`, the identical tuple. Probe 1's message is failure_behavior's f-string. Probe 2 is failure_behavior's `many` (sorted) plus scope's `both` (empty intersection). Probe 3 is failure_behavior's `mixed` ('the unknown-key scan runs first'). Probe 4 is failure_behavior's `bad_value`. On top of that, `raised_by` resolves the class via `sym("BackendParamError")`, so the whole file is gated on r1.rule.
- `no_independent_content` — This is the primary finding. The test's own docstring concedes it: 'observability is the only one that spells the requirement's own examples out literally.' The single expression it touches that no sibling touches is `' or '.join(belongs_to)` at length two -- and that is not a branch; `str.join` handles 0, 1 and 2 identically, and failure_behavior already pins the f-string and the zero- and one-element tails. There is no line of code an agent writes for this fact that it has not already written for rule, scope and failure_behavior.

**Recommendation.** Cut r1.observability as a separate fact, and salvage its two non-redundant assertions into the siblings that own those channels. Coverage does not shrink.

(1) Move the `\"auto\"` probe into r1.scope, replacing or joining the `-5` probe:

    by_name = raised_by({\"model\": \"gpt-4o\", \"batch_size\": \"auto\"}, batch=False)
    assert by_name.params == (\"batch_size\",)
    assert by_name.belongs_to == (\"BatchRequestProcessorConfig\", \"OfflineRequestProcessorConfig\")

This is strictly the better by-name-not-by-value discriminator: `\"auto\"` is a `str` against `OfflineRequestProcessorConfig.batch_size`'s plain `int` annotation, so any trial-validation implementation MUST drop offline. The existing `-5` probe only discriminates if offline really constrains `batch_size > 0`, which the ticket never states -- it says only that offline's batch_size 'keeps its plain `int` annotation and gets no validator'. Verify that constraint in config.py before relying on `-5`; if it is absent, scope's by-name probe is vacuous today and this swap is a bug fix, not just a consolidation.

(2) Move the two-element message form into r1.failure_behavior, next to its existing zero- and one-element assertions, so all three tail lengths sit in the fact that owns the format string:

    two = raised_by({\"model\": \"gpt-4o\", \"batch_size\": \"auto\"}, batch=False)
    assert str(two) == (
        \"backend_params batch_size not accepted by OnlineRequestProcessorConfig; \"
        \"accepted by BatchRequestProcessorConfig or OfflineRequestProcessorConfig\"
    )

Drop probes 2, 3 and 4 outright -- they are verbatim re-runs of failure_behavior's `many`, `mixed` and `bad_value` with different literals.

Not `narrow`: narrowing this fact to its one useful probe leaves a fact that duplicates scope, so there is nothing left to narrow to.

Separately, and independent of this verdict: probe 4 and failure_behavior's `bad_value` both assume `max_retries` and `request_timeout` carry constraints today that reject `-1` and `0` with exactly one error. The ticket puts 'the meanings of `max_retries`' out of scope and forbids adding any numeric constraint, so those constraints must pre-exist. I could not open config.py to confirm (all file tools were disabled this session). If either field is unconstrained, the call succeeds and `pytest.raises(ValidationError)` fails a correct implementation -- check both before shipping r1.failure_behavior.


## g12.r2.rule — retest

**Divergent action.** Declaring a brand-new field on the base class and resurrecting the deleted hook in inverted form: `unsupported_generation_params: tuple[str, ...] = Field(default=(), exclude=True)` plus `def model_post_init(self, __context): supported = get_supported_openai_params(model=self.model); self.unsupported_generation_params = () if supported is None else tuple(sorted(k for k in self.generation_params if k not in supported))` wrapped in `except Exception: self.unsupported_generation_params = ()`, with `OfflineRequestProcessorConfig.model_post_init` overriding to `()` and importing nothing from litellm. The blind agent writes the opposite: it obeys the ticket's "Delete `RequestProcessorConfig.__post_init__` (line 43)... so all three are dead today" and puts nothing back, because the ticket re-expresses only the batch_size hook and is silent on the other two.

**The assertion.** `assert unsupported(config) == ("top_p",)` in test_rule, on `OnlineRequestProcessorConfig(model="gpt-4o", generation_params={"top_p": 1, "temperature": 0.5})`. It is a direct construction, not routed through `_validate_backend_params`, so it does not depend on r1 (BackendParamError) at all — only on the open feature's config classes existing plus this requirement. It DOES depend on one thing outside the implementation: whether `patch_lookup` succeeded in intercepting the implementation's chosen call path. If the patch misses (alias import), real litellm answers for gpt-4o, `top_p` is supported, the tuple is `()` and a correct build fails.

**Catalog A.**
- `ticket_gives_it_away` — PARTIAL and non-decisive. The ticket says 'Delete `RequestProcessorConfig.__post_init__` (line 43)', which guarantees the agent reads that body and sees the litellm supported-params lookup; and it establishes the precedent 'dead __post_init__ -> live pydantic v2 equivalent' by re-expressing the batch_size hook as a field_validator. A symmetric-minded blind agent could infer 'resurrect the base hook too, as model_post_init'. What the ticket does NOT leak is the whole graded contract: report-instead-of-raise, the field name, exclude=True, sorted tuple, the offline override. A faithful resurrection would RAISE, which the test rejects outright.

**Catalog B.**
- `fake_defines_the_trigger` — Applies to the `exclusions` sibling, not to `rule`. `test_exclusions` asserts `assert len(calls) == before, "the offline config asked litellm for supported params"` — the graded quantity is HOW OFTEN the trigger fires, and the counter lives inside the fake that also defines the trigger. Worse, the same fake's reachability is a precondition: a build whose call path escapes `patch_lookup` records zero calls and trips `require_feature`, converting a hard fail into a skip. For `rule` the fake supplies only the input to the graded computation (the reaction), which the rubric permits.

**A correct build the test rejects:**

```
```python
# config.py
from litellm import get_supported_openai_params as _supported_params

class RequestProcessorConfig(BaseModel):
    unsupported_generation_params: tuple[str, ...] = Field(default=(), exclude=True)

    def model_post_init(self, __context) -> None:
        try:
            supported = _supported_params(model=self.model)
        except Exception:
            supported = None
        if supported is None:
            self.unsupported_generation_params = ()
        else:
            self.unsupported_generation_params = tuple(
                sorted(k for k in self.generation_params if k not in supported)
            )
```
This satisfies every clause of r2 — declared field, exclude=True, model_post_init, sorted tuple, never raises, None yields (). It fails test_rule because `patch_lookup` only rebinds attributes literally *named* `get_supported_openai_params`; `hasattr(config_module, "get_supported_openai_params")` is False, and `_supported_params` already holds the original function object, so the fake is never called and real litellm reports `top_p` as supported for gpt-4o. A second, weaker instance: wrapping the lookup in `@functools.lru_cache` — legitimate for a per-construction network-metadata lookup, and it breaks test_failure_behavior because all four probes reuse the model name "gpt-4o".
```

**Recommendation.** Keep the fact — the divergent action is real and no blind implementation I can construct hits the invented field name, exclude=True and report-not-raise contract. Fix the test in two places, both in `patch_lookup` and the probe data. (1) Close the alias hole: capture `original = getattr(litellm, name)` before patching, then for every `bespokelabs.curator.*` module in sys.modules rebind EVERY attribute whose value `is original` (not just the attribute literally named `get_supported_openai_params`), in addition to the current `hasattr` scan. Without this, a correct build that wrote `from litellm import get_supported_openai_params as _supported_params` at module top fails `test_rule` outright. (2) Close the memoization hole: give each probe in `test_failure_behavior` and `test_observability` a distinct model name (e.g. "gpt-4o-a", "gpt-4o-b", ...), or make the fake's return value a function of the model argument, so an implementation that wraps the lookup in `functools.lru_cache` cannot serve a stale answer across the raises/None/[] variants. Separately, two non-blocking notes for the task author: the ticket's 'Reuse as-is: the four pydantic config classes' pulls against adding a field to the base class and may depress the ticket+clues condition — consider softening it to 'reuse their existing fields and `class Config`'; and `test_observability` asserts nothing that `rule`/`scope`/`exclusions`/`failure_behavior` do not already assert, so it is measuring the same thing a fifth time rather than adding a fifth measurement.


## g12.r2.scope — cut

**Divergent action.** `unsupported_generation_params: tuple[str, ...] = Field(default=(), exclude=True)` declared on `RequestProcessorConfig`, plus a base `model_post_init` that assigns `tuple(sorted(k for k in self.generation_params if k not in supported))`. That code is genuinely divergent from a blind build — but it is *r2.rule's* code, quoted verbatim in r2.rule. There is no additional expression, call or branch that an agent informed about `scope` writes and an agent informed only about `rule` does not: inheritance gives "online and batch", pydantic gives "declared field accepts caller input", and post-init assignment gives "then overwritten". Scope's marginal action is zero.

**The assertion.** `assert unsupported(supplied) == ()` (on `supplied = vbp({"model": "gpt-4o", FIELD: ("caller_said_so",), "generation_params": {"temperature": 0.5}}, batch=False)`) — the only assertion in test_scope that is not a re-run of rule's tuple. It depends on more than this requirement: (1) it depends on r2.rule, since the field and hook are declared there; (2) it depends on r1's implementation of `_validate_backend_params` — if the agent built r1's unknown-key scan and the field were a PrivateAttr rather than a `model_fields` entry, this call raises `BackendParamError` instead of returning; (3) the identical probe is re-asserted in test_observability as `supplied = vbp({"model": "gpt-4o", FIELD: ("x",)}, batch=True)`, so it cannot fail here without failing there.

**Catalog A.**
- `model_already_knows_it` — Both halves of scope beyond `rule` are documented pydantic v2 defaults, not repo facts. "a caller-supplied ... is a legal key that is accepted" is simply what a declared field does under `extra = "forbid"`, "and then overwritten by the hook" is what assigning in post-init does, and "`exclude=True` keeps it out of `model_dump()`" is the published meaning of `Field(exclude=True)`. No agent has to be told any of this once the field exists.
- `obvious_implementation_does_it` — Relative to the sibling that carries the same clue, yes: `rule` hands over the literal line `Field(default=(), exclude=True)` on the base class, and the obvious way to write it — one field, one `model_post_init` on `RequestProcessorConfig` — satisfies every clause of scope with no further thought. Online and batch inherit; the caller value is accepted and overwritten; exclude keeps it out of the dump. There is no natural correct implementation of `rule` that fails `scope`.

**Catalog B.**
- `observable_belongs_to_another_fact` — Both of scope's discriminating probes are owned by `observability`, which re-asserts them literally: `supplied = vbp({"model": "gpt-4o", FIELD: ("x",)}, batch=True); assert unsupported(supplied) == ()` and `assert FIELD not in config.model_dump()`. Scope's remaining assertions (`== ("frobnicate", "top_k")`) are `rule`'s tuple measured through a second door. Grading scope double-counts observability and rule.
- `no_independent_content` — Scope restates the consequences of `rule`'s own field declaration. Its assertion set is a subset of rule's ∪ observability's: I could not construct any build — correct or broken — that fails test_scope while passing test_rule and test_observability. "applies to every config ... in online and batch mode" is free by inheritance from `RequestProcessorConfig`; the caller-supplied and exclude clauses are restatements of `Field(default=(), exclude=True)`, which `rule` already quotes.

**Recommendation.** Cut `r2.scope` as written; it adds no bits over `r2.rule` and `r2.observability`. If you want to keep a fact here rather than drop it, it must be bought from `rule`, not narrowed in place — `rule` currently quotes the exact `Field(default=(), exclude=True)` line that makes scope automatically true. Concretely: (1) weaken `r2.rule` to state only that unsupported generation params are recorded on the config object rather than raised, dropping the `Field(...)` spelling and the `exclude=True` flag from its text; (2) let `scope` own the remaining real distinction — it is a genuine declared pydantic field (present in `model_fields`, not a `PrivateAttr`, `computed_field`, or cached property), so a caller-supplied `unsupported_generation_params` in `backend_params` survives r1's unknown-key scan, is accepted, and is then overwritten, and `exclude=True` keeps it out of `model_dump()`; (3) delete the duplicated `supplied = vbp({..., FIELD: (\"x\",)}, batch=True)` and `FIELD not in config.model_dump()` probes from `test_observability` so scope's assertion is not also observability's; (4) add to test_scope a negative that only the field reading can pass, e.g. assert `FIELD in type(online).model_fields` and that the `PrivateAttr` build raises `BackendParamError` on the supplied probe. Separately, two r2-level test-fragility issues I hit while looking for a scope-specific correct-fail, worth fixing even though they are not scope's: `patch_lookup` only covers `get_supported_openai_params`, so a build using `litellm.get_model_info(model)[\"supported_openai_params\"]` — a legitimate reading of \"looks the params up through litellm\" — runs unpatched (it happens to pass test_scope on real gpt-4o data and fails test_rule's `top_p` probe); and an ordinary `lru_cache` around the lookup passes scope but breaks `failure_behavior` and trips `exclusions`' `require_feature`. Either pin the lookup function in the requirement text or widen the patch.


## g12.r2.exclusions_or_crossover — retest

**Divergent action.** On `OfflineRequestProcessorConfig`, an offline-only short-circuit of the base hook — concretely `def model_post_init(self, __context: t.Any) -> None: self.unsupported_generation_params = ()` (or an equivalent `if isinstance(self, OfflineRequestProcessorConfig): return` / overridden `_supported_params()` returning `None`). An agent who knows only r2.rule declares the field and the base `model_post_init` and lets the offline subclass inherit it, so `OfflineRequestProcessorConfig(model="gpt-4o", generation_params=GENERATION_PARAMS)` comes out `("frobnicate", "top_k")` and calls the lookup once. So a real code difference is nameable — but its information source is the repo, not the clue: the deleted line-138 hook the ticket cites by number *is* that override.

**The assertion.** `assert len(calls) == before, \"the offline config asked litellm for supported params\"` — the only assertion in the suite unique to this fact. Passing/failing it depends on much more than this requirement: it is unreachable unless `require_feature(len(calls) > 0 and read_field(online, FIELD, default=None) == (\"frobnicate\", \"top_k\"), ...)` — r2.rule's implementation — holds; `len(calls) > 0` additionally depends on the lookup being un-memoized and reached through a name `patch_lookup` can rebind; and the second occurrence of the same assertion sits after `vbp({...}, batch=True, backend=\"vllm\")`, which depends on the open ticket's `_resolve_mode` (\"Backend `vllm` beats `batch=True`\") and on r1's unknown-key scan not rejecting the payload.

**Catalog A.**
- `codebase_already_does_it` — The fact itself concedes the source: "which is what its deleted line-138 hook's docstring claimed to do." The offline override-to-nothing already exists in the checkout, documented, at the exact line the ticket tells the agent to open and delete. Nothing about the exemption originates in the clue; only the decision to re-express the base hook does.
- `prohibition_satisfied_by_inaction` — "performs no litellm lookup and no litellm import" is satisfied by not writing a call. More concretely, the field's own default carries it: `unsupported_generation_params: tuple[str, ...] = Field(default=(), exclude=True)` means any build that declares the field but attaches the hook to the wrong class, or forgets the hook on the subclass path, yields `()` for offline for free. Only the `require_feature` gate stops that from passing.
- `ticket_gives_it_away` — The ticket names the artifact: "Delete ... `OfflineRequestProcessorConfig.__post_init__` (line 138)", and establishes the offline-is-exempt pattern one bullet later: "`OfflineRequestProcessorConfig.batch_size` keeps its plain `int` annotation and gets no validator." An agent who has just read line 138 in order to delete it has been handed the exclusion.
- `obvious_implementation_does_it` — Adding a litellm-backed check to a hierarchy whose offline member is the vLLM local-inference config invites the instinct "the local engine isn't a litellm model, don't ask litellm about it." An agent implementing r2.rule with that instinct writes the override without ever learning the exclusions clause.

**Catalog B.**
- `behaviour_has_no_consequence` — Nothing in the ticket or the dispatch table reads `unsupported_generation_params`; it is informational. And under real litellm, a vLLM model name makes the lookup raise, which failure_behavior says "the value is `()` and construction succeeds" — so overriding and inheriting produce the identical end state in production. The difference exists only under the fake.
- `observable_belongs_to_another_fact` — The value half is verbatim observability's: `assert unsupported(OfflineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS))) == ()` appears in both tests. And the call-count half is only reachable past `require_feature(len(calls) > 0 and read_field(online, FIELD, default=None) == ("frobnicate", "top_k"), ...)`, which is r2.rule's observable.
- `no_independent_content` — Strip what observability already asserts and what the gate borrows from rule, and the fact's residue is one integer comparison, `len(calls) == before` — plus an import clause with no test at all.
- `unbounded_in_time` — "performs no litellm lookup and **no litellm import**" — the import clause is a global never with no finite observation. The test never inspects imports and cannot: both classes live in `config.py`, so the base hook's import is the offline class's import, and `patch_lookup` does `import litellm` itself.
- `fake_defines_the_trigger` — The graded question is *how often* the call fires (zero), and the fake is both the call and the counter. It also authors the only condition under which firing is distinguishable — `patch_lookup(monkeypatch, value=["temperature", "max_tokens"], calls=calls)` makes a successful non-empty answer available to a model the offline class would never see in production, where the lookup raises and both implementations agree on `()`.

**A correct build the test rejects:**

```
A build that satisfies the exclusions fact exactly — the offline class overrides `model_post_init` to `()` and never asks litellm — but memoizes the lookup, an ordinary choice for a call that fires on every config construction:

```python
@functools.lru_cache(maxsize=None)
def _supported_params(model: str) -> tuple[str, ...]:
    try:
        return tuple(get_supported_openai_params(model=model) or ())
    except Exception:
        return ()


class RequestProcessorConfig(BaseModel):
    unsupported_generation_params: tuple[str, ...] = Field(default=(), exclude=True)

    def model_post_init(self, __context: t.Any) -> None:
        supported = _supported_params(self.model)
        self.unsupported_generation_params = tuple(
            sorted(k for k in (self.generation_params or {}) if k not in supported)
        )


class OfflineRequestProcessorConfig(RequestProcessorConfig):
    def model_post_init(self, __context: t.Any) -> None:
        self.unsupported_generation_params = ()
```

`test_rule` and `test_scope` run first in file order and warm the cache for `"gpt-4o"`. By the time `test_exclusions` builds its online probe, the fake is never invoked, `len(calls) > 0` is False, and `require_feature` reports the base hook as missing — for a build whose offline exclusion is perfectly correct. The same escape hatch exists for an aliased binding (`from litellm.utils import get_supported_openai_params as _gsop`), which `patch_lookup`'s `hasattr(module, name)` scan cannot rebind.
```

**Recommendation.** Fix the fact and the test, then re-run condition 1 with rule revealed.

1. Delete "and no litellm import" from the fact. It has no observable — `config.py` holds both classes, so the base hook's import is the offline class's import, and `patch_lookup` imports litellm itself. Keep only "performs no litellm lookup during offline construction."

2. Repair the gate in `test_exclusions`. Give every probe a distinct model name (`"gpt-4o-probe-a"`, `"gpt-4o-probe-b"`, ...) so a memoized lookup cannot read as "asked nobody", and split the gate: `require_feature` on the *value* only (`read_field(online, FIELD, default=None) == ("frobnicate", "top_k")`), then a plain `assert len(calls) > 0` immediately after constructing the online probe with a fresh name. That keeps the recorder-works proof without failing correct builds that cache.

3. Make the assertion carry its own weight. Construct the offline probe with the same fresh model whose patched answer is non-empty, and assert both the zero-call delta *and* that the value differs from what the base hook produced for the identical `generation_params` — the exclusion should be shown to change the answer, not just the call count. Drop the duplicated `assert unsupported(OfflineRequestProcessorConfig(...)) == ()` from `test_observability` so this fact owns its observable.

4. Then re-run discrimination in the condition that matters: ticket + a clue that reveals r2.rule but not the exclusion. Since the ticket cites `OfflineRequestProcessorConfig.__post_init__ (line 138)` by number and the fact admits the exemption is that hook's docstring, this is the run that decides whether exclusions is a fact or a restatement of rule. If it passes there, merge exclusions into rule rather than shipping it separately.


## g12.r2.failure_behavior — retest

**Divergent action.** The defensive wrapper around the litellm lookup inside `model_post_init`: `try: supported = get_supported_openai_params(model=self.model) or [] / except Exception: supported = []`. An agent that saw only `rule` writes the direct form `supported = get_supported_openai_params(model=self.model)` followed by `tuple(sorted(k for k in self.generation_params if k not in supported))` — which propagates the lookup's exception out of construction, and raises `TypeError: argument of type 'NoneType' is not iterable` when the lookup returns None. So `try/except Exception` plus the `or []` / None guard is a real, nameable code difference. Separately, a ticket-only agent writes no `unsupported_generation_params` field at all, because the open ticket says "Delete `RequestProcessorConfig.__post_init__` (line 43)" with no replacement and never mentions litellm supported-params.

**The assertion.** `patch_lookup(monkeypatch, raises=ValueError("litellm has no idea")); assert unsupported(OnlineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS))) == ()`. Passing/failing depends on more than this requirement: (1) on `rule` being implemented at all, since the field must exist for `read_field` to return anything; (2) on the build having chosen a litellm entry point that `patch_lookup` actually covers — the requirement never names the function, so an implementation reaching supported params via e.g. `ProviderConfigManager.get_provider_chat_config(...).get_supported_openai_params(...)` never sees the fake and fails here for a reason unrelated to its exception handling. And this assertion alone does not decide the fact in practice, because a no-op hook also passes it; the `value=[]` assertion is what separates them, and that one is `rule`'s.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — The stated reaction — "the value is `()` and construction succeeds" — is precisely what you get by doing nothing. Declare `unsupported_generation_params: tuple[str, ...] = Field(default=(), exclude=True)` and leave `model_post_init` empty, and three of this test's four assertions pass verbatim: `assert unsupported(OnlineRequestProcessorConfig(...)) == ()` (raises case), `assert unsupported(vbp(...)) == ()` (raises case), `assert unsupported(...) == ()` (None case). Only the borrowed `value=[]` assertion catches the no-op. The fact's failure branch is indistinguishable from inertia except via a sibling's observable.
- `obvious_implementation_does_it` — Relative to an agent that has `rule` but not this line: wrapping a best-effort third-party metadata lookup in `try/except Exception` inside a constructor is standard defensive practice, and `rule`'s own text already primes it — "Unsupported generation params are reported on the config object, not raised." An engineer told "never raise" who then calls out to litellm from `__init__` writes the try/except by reflex. The clue-specific increment over `rule` is thin.

**Catalog B.**
- `observable_belongs_to_another_fact` — The only assertion in this test that a degenerate build cannot pass is `patch_lookup(monkeypatch, value=[]); assert unsupported(every) == ("frobnicate", "temperature", "top_k")` — that is `rule`'s observable (compute the sorted tuple of unsupported params), imported here as a positive control. The sibling `exclusions` test does the same job with a *gate*, `require_feature(...)`, not a hard assert. Grading this fact therefore routes through `rule`'s channel, and the assert form means a build with a slightly different — but unspecified — `rule` semantics fails `failure_behavior`.
- `no_independent_content` — The first sentence, "The hook does not raise for any generation param, however unknown", is a restatement of `rule`'s closing line, "Unsupported generation params are reported on the config object, not raised." Only the second sentence — "If the litellm lookup returns `None`, or raises any `Exception`, the value is `()`" — carries content `rule` does not already assert. Half the fact is a neighbour echo.

**A correct build the test rejects:**

```
def model_post_init(self, __context) -> None:
    try:
        supported = get_supported_openai_params(model=self.model)
    except Exception:
        supported = None
    if not supported:            # litellm has nothing to say for this model
        self.unsupported_generation_params = ()
        return
    self.unsupported_generation_params = tuple(
        sorted(k for k in self.generation_params if k not in supported)
    )

# Satisfies every clause the requirement actually states: None -> (), any Exception -> (),
# construction succeeds, sorted tuple otherwise, and every literal probe in r2.observability
# (["temperature","max_tokens"] -> ("frobnicate","top_k"); RuntimeError("boom") -> (); None -> ()).
# `if not supported` is the idiomatic collapse of None and [], and the "litellm has no mapping
# for this model" semantics that justifies None -> () extends to [] -> () without strain.
# Nothing in r2's rule, scope, exclusions or observability specifies the empty-list case.
# test_failure_behavior rejects it:
#     patch_lookup(monkeypatch, value=[])
#     assert unsupported(every) == ("frobnicate", "temperature", "top_k")
```

**Recommendation.** Retest — keep the fact, fix the test. (1) Delete the `patch_lookup(monkeypatch, value=[])` block from `test_failure_behavior__a_broken_or_empty_lookup_leaves_an_empty_tuple`; it asserts behaviour (`[]` means "every key is unsupported") that appears nowhere in r2's rule, scope, exclusions or observability text, and it rejects the equally-valid `if not supported: return ()` reading. (2) Replace it with a positive control in the same shape the sibling already uses — `patch_lookup(monkeypatch, value=["temperature", "max_tokens"]); require_feature(read_field(OnlineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS)), FIELD, default=None) == ("frobnicate", "top_k"), "the base model_post_init that fills unsupported_generation_params from litellm")` — so a no-op hook is gated out rather than being caught by a borrowed `rule` assertion. (3) If `[] -> every key reported` is genuinely intended, it must be stated in the requirement (add to `rule`: "an empty supported list is distinct from `None`; every generation param is then reported") and asserted in `rule`'s test, not this one. (4) Name the litellm entry point in `observability` — say `litellm.get_supported_openai_params` explicitly — so the agent is not guessing which symbol `patch_lookup` covers. (5) Optionally drop the first sentence of the fact, "The hook does not raise for any generation param, however unknown", which duplicates `rule`'s "reported on the config object, not raised", leaving the fact scoped to the lookup-failure clause that is actually its own.


## g12.r2.observability — retest

**Divergent action.** The clued agent writes, on `RequestProcessorConfig`, a declared field plus a pydantic v2 hook where the ticket said only "delete":

```python
unsupported_generation_params: tuple[str, ...] = Field(default=(), exclude=True)

def model_post_init(self, __context: t.Any) -> None:
    try:
        supported = get_supported_openai_params(self.model) or []
    except Exception:
        supported = []
    self.unsupported_generation_params = tuple(
        sorted(k for k in (self.generation_params or {}) if k not in supported)
    )
```

and on `OfflineRequestProcessorConfig` an override `def model_post_init(self, __context): self.unsupported_generation_params = ()` with no litellm import. The blind agent writes nothing here: the ticket says "Delete `RequestProcessorConfig.__post_init__` (line 43)" and re-expresses only the `batch_size` hook as a `field_validator`, so the blind build simply removes the dead hook. The specific divergences are the field name `unsupported_generation_params`, `exclude=True`, the `tuple(sorted(...))` shape, and the `except Exception: supported = []` swallow in place of the old hook's raise.

**The assertion.** `assert unsupported(config) == ("frobnicate", "top_k")` — after `patch_lookup(monkeypatch, value=["temperature", "max_tokens"])` and `config = OnlineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS))`. It is the only assertion in the test that a build with no field at all cannot pass. Passing or failing it depends on two things besides this requirement: (a) which litellm entry point the build calls, since `patch_lookup` only covers the name `get_supported_openai_params` — an unpatched route is graded against live litellm data for `gpt-4o`; and (b) `harness.read_field`'s behaviour for a missing attribute. It is also not unique to this fact: the identical measurement is made in `test_scope` and gated in `test_exclusions`, so no implementation can fail this assertion while passing its siblings.

**Catalog A.**
- `prohibition_satisfied_by_inaction` — Narrowly, but really: four of observability's six assertions are satisfied by a build that has no such field at all. `assert FIELD not in config.model_dump()` is trivially true when the field was never declared, and the three `== ()` assertions (offline, broken lookup, `value=None`) are true-by-absence if `harness.read_field` returns an empty default when the attribute is missing — the sibling's use of `read_field(online, FIELD, default=None)` suggests the no-default form instead fails, which is the only thing preventing this. This does not reach the deciding assertion (`== ("frobnicate","top_k")`), so it does not sink the fact, but it means most of this test's surface measures nothing.

**Catalog B.**
- `observable_belongs_to_another_fact` — Three of the six probes are other facts' channels. `assert FIELD not in config.model_dump()` is scope's stated content ("`exclude=True` keeps it out of `model_dump()`"). The offline `()` probe is exclusions' content. Most seriously, the `RuntimeError("boom")` probe is the *only* assertion anywhere that exercises failure_behavior's actual rule — "If the litellm lookup returns `None`, or raises **any** `Exception`" — because `test_failure_behavior` only ever raises `ValueError`. A build with `except ValueError:` passes failure_behavior and fails observability, meaning observability is grading failure_behavior's clause.
- `no_independent_content` — Every assertion in `test_observability` is a duplicate. `unsupported(config) == ("frobnicate","top_k")` on the identical constructor call appears in `test_exclusions` (inside `require_feature`) and in `test_scope` (via `vbp`); `FIELD not in ...model_dump()` appears three times in `test_scope`; the offline `()` appears in `test_exclusions`; and `patch_lookup(monkeypatch, value=None)` followed by `assert unsupported(OnlineRequestProcessorConfig(model="gpt-4o", generation_params=dict(GENERATION_PARAMS))) == ()` is reproduced **byte-for-byte** from `test_failure_behavior`. The test docstring concedes it: "`observability` spells the requirement's own examples out literally." Its only non-duplicated measurement is the accidental one described in `correct_fail`.
- `fake_defines_the_trigger` — `patch_lookup` decides what counts as "the lookup". It patches only the name `get_supported_openai_params`, on `litellm`, on its defining module, and on curator modules that bound it, with `raising=False` — so a build that reads supported params through a different legitimate litellm route (e.g. `litellm.get_model_info(model)["supported_openai_params"]`) is never patched and is silently graded against real litellm data. The docstring shows the authors saw part of this ("Which import form a build chose is not the fact being graded") and covered import form but not entry point. The fact is about the reaction, yet the fake authors the trigger's identity.

**A correct build the test rejects:**

```
A build that skips the assignment when there is nothing to look up — avoiding a pointless litellm call in the common case, and consistent with r2's rule being about "params litellm does not list":

```python
def model_post_init(self, __context: t.Any) -> None:
    if not self.generation_params:
        return
    try:
        supported = get_supported_openai_params(self.model) or []
    except Exception:
        supported = []
    self.unsupported_generation_params = tuple(
        sorted(k for k in self.generation_params if k not in supported)
    )
```

This passes `test_rule` (`unsupported(OnlineRequestProcessorConfig(model="gpt-4o")) == ()` holds via the `Field(default=())`), passes `test_scope` (its supplied-value probe passes `generation_params={"temperature": 0.5}`, non-empty, so the overwrite runs), passes `test_exclusions` and passes `test_failure_behavior`. It fails `test_observability` on the single line `supplied = vbp({"model": "gpt-4o", FIELD: ("x",)}, batch=True); assert unsupported(supplied) == ()` — because that probe, uniquely, supplies the field with **no** `generation_params`, so the caller's `("x",)` survives. Nothing in r2's stated text requires the assignment to run when `generation_params` is empty; observability's one piece of independent discriminating power is an unstated constraint.

Secondary (contingent on clue wording I could not read): a build that looks supported params up via `litellm.get_model_info(self.model).get("supported_openai_params")` — a legitimate reading of r2.rule's "looks the model's supported params up through litellm" — is never reached by `patch_lookup` and fails the broken-lookup probes, which expect `()` but get a live answer.
```

**Recommendation.** Keep r2; fix the observability test. Four concrete changes:

1. Delete the duplicated assertions from `test_observability`: `assert FIELD not in config.model_dump()` (three copies live in `test_scope`), the offline `GENERATION_PARAMS -> ()` block (`test_exclusions` asserts it on the identical construction), the `patch_lookup(monkeypatch, value=None)` block (byte-for-byte identical to a line in `test_failure_behavior`), and the opening `unsupported(config) == ("frobnicate","top_k")` probe (`test_scope` asserts it via `vbp`, `test_exclusions` gates on it).

2. Move the `RuntimeError("boom")` probe into `test_failure_behavior`, and change that test's existing break from `ValueError("litellm has no idea")` to a non-`ValueError` (e.g. `KeyError`), so `except Exception` is actually required by the fact whose rule says "raises any `Exception`". Today that clause is only enforced from observability's test.

3. Decide the empty-`generation_params` question in the requirement text, not in the test. If the hook must assign unconditionally, add to r2.scope: "the hook assigns on every construction, including when `generation_params` is empty or absent, so a caller-supplied value is always replaced." If it need not, change observability's last probe to `vbp({"model": "gpt-4o", FIELD: ("x",), "generation_params": {"temperature": 0.5}}, batch=True)` — as written it rejects a reasonable early-return build for a rule nobody stated.

4. Harden `patch_lookup` against entry point, not just import form: also patch `litellm.get_model_info` (or assert the build called the patched name at least once, as `test_exclusions` already does with `calls`), so a legitimate alternative litellm route fails loudly rather than being graded against live data.

After 1-3, re-run the blind and oracle brackets on this fact alone. If what remains contains no assertion that some sibling does not already make, cut the observability field and fold its probes into `rule`, `scope` and `failure_behavior` — on the current test it carries one genuine measurement and five copies.
