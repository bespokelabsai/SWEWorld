# g12 — the requirement, reduced to what is graded

**556 words → 421** across 9 facts and 73 graded assertions.

The tests, the fact keys and the oracle are untouched. What changed is what the `-spec` arm shows an implementer, and therefore what the clues have to carry.

| fact | words | assertions | dropped |
|---|---|---|---|
| `g12.r1.rule` | 69 → 56 | 11 | 3 |
| `g12.r1.scope` | 63 → 38 | 12 | 3 |
| `g12.r1.failure_behavior` | 102 → 78 | 10 | 4 |
| `g12.r1.observability` | 100 → 86 | 12 | 1 |
| `g12.r2.rule` | 53 → 37 | 6 | 2 |
| `g12.r2.scope` | 46 → 34 | 7 | 2 |
| `g12.r2.exclusions_or_crossover` | 27 → 12 | 5 | 2 |
| `g12.r2.failure_behavior` | 28 → 19 | 4 | 2 |
| `g12.r2.observability` | 68 → 61 | 6 | 2 |

## `g12.r1.rule`

**Now (56 words):**

When a key of `params` is not a field of the config class for the resolved mode, `_validate_backend_params` raises `BackendParamError(ValueError)` — a class defined in `config.py` with `def __init__(self, params: tuple[str, ...], expected: str, belongs_to: tuple[str, ...]) -> None` storing those three as instance attributes. It is raised before pydantic runs, so no `ValidationError` is produced.

**Dropped, because no assertion checks it:**

- "no config object is constructed and" — a consequence of raising before pydantic runs; no assertion inspects whether a config object exists.
- "`params`, `expected`, `belongs_to`" after "instance attributes" — a restatement of the three names already given verbatim in the `__init__` signature immediately before; the attribute names an implementer must produce are still stated exactly.
- "for the wrong-mode case" — scope restatement of the opening clause, which already says the trigger is a key that is not a field of the resolved mode's config class.

**Kept despite looking like padding:** \"a class defined in `config.py`\" reads like locating detail, but every assertion reaches the class or an instance of it by name (#1 `issubclass(cls, ValueError)`, #3-#5 on `made`), so the module the implementer must define `BackendParamError` in has to stay for those lookups to resolve. \"It is raised before pydantic runs\" also survives: #10 and #11 read `early.params` and `early.expected` off an error produced before any config object is validated, and #2/#7 turn on no `ValidationError` being what surfaces.

## `g12.r1.scope`

**Now (38 words):**

The offending keys are decided by name only, against `_MODE_CONFIGS[mode].model_fields`. `expected` is that class's `__name__`. `belongs_to` lists the `__name__` of each *other* config class, iterated in the fixed order `BatchRequestProcessorConfig`, `OnlineRequestProcessorConfig`, `OfflineRequestProcessorConfig`, whose `model_fields` contain **every** offending key.

**Dropped, because no assertion checks it:**

- "an intersection, never a union" — restates the surviving "whose `model_fields` contain **every** offending key", which is already what makes `both.belongs_to == ()` (#8) come out empty rather than a union of Online and Offline.
- "and values are never type-checked or trial-validated for this" — restates the surviving opening rule "decided by name only"; no assertion inspects a field value or a validation attempt.
- "A key no config class declares yields `belongs_to == ()`." — a worked edge case already pinned by the surviving rule: no class's `model_fields` contains `definitely_not_a_field`, so the fixed-order iteration yields the empty tuple for #11/#12 without restating it.

**Kept despite looking like padding:** "by name only" reads like emphasis left over from the type-check clause I cut, but it has to stay on its own: `nowhere.params == ("definitely_not_a_field",)` (#11) and `nowhere.belongs_to == ()` (#12) only hold if membership is a name lookup against `model_fields` — a value-based or trial-validation test would error or reclassify instead of reporting the key. The `*other*` qualifier is load-bearing for #2/#4/#6, where the mode's own class is absent from `belongs_to`, and the three class names must stay in the listed order for `by_name.belongs_to == ("BatchRequestProcessorConfig", "OfflineRequestProcessorConfig")` (#10).

## `g12.r1.failure_behavior`

**Now (78 words):**

All offending keys are reported together, sorted ascending by `str`. `str(e)` is exactly `f"backend_params {', '.join(params)} not accepted by {expected}; accepted by {' or '.join(belongs_to)}"`, and when `belongs_to` is empty the tail is exactly `"; accepted by no request processor config"`. If every key is a field of the mode's class but a value is invalid, the `pydantic.ValidationError` propagates unchanged. A call carrying both an unknown key and an invalid value raises `BackendParamError` naming only the unknown key.

**Dropped, because no assertion checks it:**

- "never just the first" — restatement of "reported together"; #1 pins the whole tuple already
- "— not caught, not wrapped, not converted" — three restatements of "propagates unchanged"
- "The unknown-key scan runs first, so" — the reason/mechanism; no assertion reads scan order, only its result
- "and the invalid value is never reported" — #10 follows from the retained f-string (which uses only params, expected, belongs_to) plus "naming only the unknown key"

**Kept despite looking like padding:** The clause \"when `belongs_to` is empty the tail is exactly `\"; accepted by no request processor config\"`\" reads like a second worked example of the message format, but assertion #3 checks that exact empty-case string, and it is not derivable from the f-string (`' or '.join(())` would give an empty tail, not this literal). Assertion #2 (`belongs_to == ()`) also depends on the empty case being a real state.

## `g12.r1.observability`

**Now (86 words):**

`_validate_backend_params({"model": "gpt-4o", "batch_size": "auto"}, batch=False)` raises with `e.params == ("batch_size",)`, `e.expected == "OnlineRequestProcessorConfig"`, `e.belongs_to == ("BatchRequestProcessorConfig", "OfflineRequestProcessorConfig")`, and `str(e) == "backend_params batch_size not accepted by OnlineRequestProcessorConfig; accepted by BatchRequestProcessorConfig or OfflineRequestProcessorConfig"`; `isinstance(e, ValueError)` is `True`. `_validate_backend_params({"model": "gpt-4o", "tensor_parallel_size": 2, "batch_size": "auto", "nope": 1}, batch=False)` gives `e.params == ("batch_size", "nope", "tensor_parallel_size")` and `e.belongs_to == ()`. `_validate_backend_params({"model": "gpt-4o", "batch_size": 8, "max_retries": -1}, batch=False)` gives `e.params == ("batch_size",)`, while `_validate_backend_params({"model": "gpt-4o", "max_retries": -1}, batch=True)` raises a `ValidationError` that is not a `BackendParamError`, with one error at `loc == ("max_retries",)`.

**Dropped, because no assertion checks it:**

- (offline keeps its place even though `"auto"` is not a legal value for it)" — a why-clause justifying why OfflineRequestProcessorConfig appears in belongs_to. No assertion checks a reason; #3 reads the exact tuple, which the surviving text still states verbatim.

**Kept despite looking like padding:** The third and fourth calls read like repeats of the first — the third asserts `params == ("batch_size",)` a second time, and the fourth is another rejection — but each is graded on its own input. #8 turns on the third call's `max_retries: -1` NOT joining `params`, and #9–#12 turn on the fourth call's `batch=True` yielding a plain `ValidationError` with one error at `("max_retries",)`. Both stay, literal dicts included.

## `g12.r2.rule`

**Now (37 words):**

`RequestProcessorConfig` gains the field `unsupported_generation_params: tuple[str, ...] = Field(default=(), exclude=True)` and a pydantic `model_post_init`: it looks the model's supported params up through litellm and assigns `self.unsupported_generation_params = tuple(sorted(k for k in self.generation_params if k not in supported))`.

**Dropped, because no assertion checks it:**

- "that replaces the deleted `__post_init__`" — history about the prior implementation; no assertion reads `__post_init__` or its absence.
- "Unsupported generation params are reported on the config object, not raised." — a restatement of the assignment already specified; the surviving clause assigning the field already fixes the reporting-not-raising behaviour that #1 and #2 exercise.

**Kept despite looking like padding:** `exclude=True` is not read by any assertion, but it sits inside the verbatim field declaration whose name, `tuple[str, ...]` type and `default=()` are graded by #3, #4, #5 and #6, so the literal stays intact rather than being edited mid-expression. Likewise `sorted` and the `not in supported` comprehension stay: #2's `(\"alpha\", \"zeta\")` ordering and #1's `(\"top_p\",)` turn on them.

## `g12.r2.scope`

**Now (34 words):**

The base hook applies to every config built through `_validate_backend_params` in online and batch mode. A caller-supplied `unsupported_generation_params` in `backend_params` is accepted and then overwritten by the hook; `exclude=True` keeps it out of `model_dump()`.

**Dropped, because no assertion checks it:**

- "Because the field is real and declared," — a why-clause explaining what makes the caller-supplied key legal; no assertion checks the reason.
- "a legal key that is" — restates "is accepted" in different words; the acceptance is already stated by "is accepted and then overwritten by the hook".

**Kept despite looking like padding:** "in online and batch mode" reads like scope padding but stays: #2 and #3 grade `unsupported(online)` and `unsupported(batch)` separately, so both modes must be named. "accepted and then overwritten by the hook" stays for #4 (`unsupported(supplied) == ()`), which turns on the supplied value being taken and then replaced rather than rejected. "`exclude=True` keeps it out of `model_dump()`" stays for #5–#7. The identifier `_validate_backend_params` stays as the named mechanism. Nothing in the text names `OnlineRequestProcessorConfig` or the tuple `("frobnicate", "top_k")` from #1–#3, so no trim there was possible.

## `g12.r2.exclusions_or_crossover`

**Now (12 words):**

`OfflineRequestProcessorConfig` overrides `model_post_init` to set `()` unconditionally and performs no litellm lookup.

**Dropped, because no assertion checks it:**

- "and no litellm import" — no assertion inspects imports; assertions #2 and #5 count litellm supported-params calls, covered by the surviving "performs no litellm lookup"
- ", which is what its deleted line-138 hook's docstring claimed to do" — history/rationale about the removed hook and its docstring; no assertion reads the line number, the hook, or the docstring

**Kept despite looking like padding:** \"overrides `model_post_init`\" and \"unconditionally\" read like mechanism detail, but assertions #1 and #4 require `()` from two construction paths — direct instance and factory result — so the text must state that the empty tuple is set on every init rather than in one case. Separately: assertion #3 (`type(from_factory) is OfflineRequestProcessorConfig`) has no support anywhere in the original 27 words, so no wording could be kept for it; adding the factory would be a rewrite, not a trim.

## `g12.r2.failure_behavior`

**Now (19 words):**

The hook does not raise. If the litellm lookup returns `None`, or raises any `Exception`, the value is `()`.

**Dropped, because no assertion checks it:**

- "for any generation param, however unknown" — scope emphasis; the bare absolute "does not raise" already covers every param, including the unknown "frobnicate" that assertion #4 expects returned rather than raised.
- "and construction succeeds" — restatement of "does not raise" in different words; no assertion constructs an object and separately checks that construction completed, they only read the return of unsupported(...).

**Kept despite looking like padding:** Both failure modes stay ("returns `None`, or raises any `Exception`") even though they read like a pair of examples for one rule. Assertions #1–#3 only observe `unsupported(...) == ()` for `model="gpt-4o"` and never reveal which path litellm took, so an implementer who handled only one of the two could still fail them. The literal `()` stays because `== ()` is exactly what #1–#3 compare against, and the tuple return type it fixes is what #4's `("frobnicate", "temperature", "top_k")` also depends on.

## `g12.r2.observability`

**Now (61 words):**

With the supported-params lookup patched to return `["temperature", "max_tokens"]`, `OnlineRequestProcessorConfig(model="gpt-4o", generation_params={"top_k": 1, "temperature": 0.5, "frobnicate": 2})` has `unsupported_generation_params == ("frobnicate", "top_k")`, while `"unsupported_generation_params" not in c.model_dump()`. The same arguments to `OfflineRequestProcessorConfig` give `()`. With the lookup patched to raise `RuntimeError("boom")`, or to return `None`, the online config gives `()`. `_validate_backend_params({"model": "gpt-4o", "unsupported_generation_params": ("x",)}, batch=True)` returns a config with `unsupported_generation_params == ()`.

**Dropped, because no assertion checks it:**

- "constructs without raising and" (first sentence) — no assertion checks successful construction as a separate outcome; assertion #1 reads the attribute off the constructed object, which only evaluates if construction returned.
- "still constructs and" (third sentence) — same for the raising/None lookup cases; assertions #4 and #5 read `unsupported(...)` off the constructed config, so "gives `()`" already carries the non-raising behaviour.

**Kept despite looking like padding:** The third sentence's two patch scenarios ("patched to raise `RuntimeError(\"boom\")`, or to return `None`") read like one rule with a redundant second example, but they are two distinct assertions (#4 and #5) with identical assertion text — drop either patch and an implementer handles only one failure mode. Likewise the second sentence ("The same arguments to `OfflineRequestProcessorConfig` give `()`") reads like a restatement of the first, but it is assertion #3; the online/offline split is the graded decision. No sentence gives a reason, so there was no "why" clause or rationale to cut, and the 47-word target is unreachable without removing a graded literal.
