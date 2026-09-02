# g4 — the requirement, reduced to what is graded

**451 words → 347** across 8 facts and 89 graded assertions.

The tests, the fact keys and the oracle are untouched. What changed is what the `-spec` arm shows an implementer, and therefore what the clues have to carry.

| fact | words | assertions | dropped |
|---|---|---|---|
| `g4.r1.rule` | 90 → 68 | 19 | 4 |
| `g4.r1.scope` | 42 → 27 | 8 | 2 |
| `g4.r1.exclusions_or_crossover` | 64 → 40 | 8 | 2 |
| `g4.r1.observability` | 79 → 79 | 9 | 2 |
| `g4.r2.rule` | 62 → 43 | 12 | 3 |
| `g4.r2.scope` | 30 → 26 | 16 | 1 |
| `g4.r2.failure_behavior` | 26 → 16 | 7 | 1 |
| `g4.r2.observability` | 58 → 48 | 10 | 1 |

## `g4.r1.rule`

**Now (68 words):**

The digest is computed over exactly twelve component keys, exported as `IDENTITY_COMPONENT_KEYS: tuple[str, ...]` in alphabetical order: `backend`, `backend_params`, `batch_mode`, `dataset_hash`, `generation_params`, `model_name`, `parse_func_hash`, `prompt_func_hash`, `response_format`, `return_completions_object`, `run_id`, `system_prompt`. The parse function participates via `_get_function_hash(llm.prompt_formatter.parse_func)` exactly as the prompt function does, `system_prompt` and `return_completions_object` participate, `generation_params` is always carried (`dict(... or {})`), and `response_format` is `json.dumps(rf.model_json_schema(), sort_keys=True, separators=(",", ":"))` or the literal string `"text"` when it is `None`.

**Dropped, because no assertion checks it:**

- "and no others" — restatement; "exactly twelve" plus the enumerated list already fixes the set that assertion #4 compares against.
- "Beyond the five values the old `_hash_fingerprint` used," — history. No assertion mentions the old fingerprint or counts what it covered; #17–#19 only check `model_name`, `batch_mode` and `dataset_hash` by name.
- "i.e. `{}` when empty" — restatement of `dict(... or {})`, which already yields `{}` for assertion #9.
- "instead of being appended only when non-empty" — rationale contrasting with the prior behaviour; nothing asserts the old conditional append.

**Kept despite looking like padding:** "exactly as the prompt function does" reads like a comparison but had to stay: it is the only place `prompt_func_hash` is specified as the function hash of the prompt function, which #5 and #7 turn on. "in alphabetical order" stays for #3 and the twelve keys in that order for #1–#4; the full `json.dumps(rf.model_json_schema(), sort_keys=True, separators=(",", ":"))` expression stays verbatim for #12 and `"text"` for #11.

## `g4.r1.scope`

**Now (27 words):**

`backend` is the *resolved* backend name read off `llm.backend`, which is `self._request_processor.backend`; `LLM.backend_params` is a copy of the dict handed to `__init__`, `{}` when it was `None`.

**Dropped, because no assertion checks it:**

- "not the declared `backend=` argument of `LLM.__init__`" — a contrastive restatement of "the *resolved* backend name ... which is `self._request_processor.backend`". No assertion reads the declared argument; naming the attribute the value comes from already determines that a declared `None` is never used.
- "(which is `None` on the common auto-detect path)" — rationale explaining why the declared argument would be wrong. Nothing asserts the declared argument's value on any path; assertion #3 only checks the hashed component is `"openai"`.

**Kept despite looking like padding:** `self._request_processor.backend` reads like an implementation aside, but it is the only statement of where the resolved name comes from, and assertions #1–#4 all turn on `LLM.backend` being `"openai"` including on the auto-detect path where the declared argument is `None`. `LLM.backend_params` "is a copy" stays for #8, which grades the copy specifically ("hands out a copy, not the dict the LLM is using") rather than just equality; "`{}` when it was `None`" stays for #6.

## `g4.r1.exclusions_or_crossover`

**Now (40 words):**

`backend_params` is filtered to exactly the four keys of `IDENTITY_BACKEND_PARAM_KEYS: frozenset[str] = frozenset({"azure_deployment", "base_url", "batch_size", "completion_window"})`. Every other backend param is not identity and must not fork the cache directory — `max_retries`, `request_timeout`, `require_all_responses`, `batch_check_interval`, `seconds_to_pause_on_rate_limit`, `max_requests_per_minute`, `delete_successful_batch_files`, and `api_key`.

**Dropped, because no assertion checks it:**

- "which is excluded deliberately even though it changes what comes back" — rationale singling out `api_key`; no assertion distinguishes it from the other excluded keys, all of which #3 and #4 grade identically.
- "because the components are written to disk in cleartext in the stamp file" — a because-clause giving the reason for the exclusion. Nothing checks cleartext, the stamp file, or why `api_key` is out, only that it is out.

**Kept despite looking like padding:** The eight-name tail (`max_retries` through `api_key`) reads like an enumeration the allowlist already implies, but #3 and #4 loop over each excluded key by name (`key not in carried`, `changing {key} must not fork the cache directory`), so every spelling had to stay. "Every other backend param is not identity and must not fork the cache directory" is the rule #3 and #4 grade, not a restatement of the allowlist sentence, which is what #1, #2, #7 and #8 grade.

## `g4.r1.observability`

**Now (79 words):**

For a stub with `backend_params={"base_url": "https://x/v1", "max_retries": 7, "api_key": "sk-secret", "request_timeout": 30}`: `tuple(sorted(compute_run_identity(S, "d0").components)) == IDENTITY_COMPONENT_KEYS` with `len == 12`; `.components["backend_params"] == {"base_url": "https://x/v1"}`; the string `"sk-secret"` occurs nowhere in the serialised components or in the written `run_identity.json`; `run_hash` is byte-equal to that of a stub differing only in `api_key`, `max_retries` and `request_timeout`; and `run_hash` differs when only the parse function, only `system_prompt`, only `return_completions_object`, or only the resolved backend differs. `LLM(model_name="gpt-4o-mini")` and `LLM(model_name="gpt-4o-mini", backend="openai")` yield the same `run_hash`.

**Dropped, because no assertion checks it:**

- Nothing deleted — the requirement is returned unchanged. It contains no reason clause, no "because"/"so that"/"which means" construction, no history or rationale, and no second or third example of a rule a first example already pins.
- Every clause maps to a graded assertion: the stub literal feeds #3/#4/#5/#6/#7; "with `len == 12`" is #2; the sorted-keys clause is #1; the two "sk-secret" locations are #4 (serialised components) and #5 (written `run_identity.json`) separately; the byte-equal clause is #7; the four "only X differs" cases are four parametrisations of #8; the closing `LLM(...)` pair is #9.

**Kept despite looking like padding:** The four alternatives in "only the parse function, only `system_prompt`, only `return_completions_object`, or only the resolved backend" read like an over-long example list, but each is a distinct `changed` case under #8, so all four stay. `"max_retries": 7` and `"request_timeout": 30` in the stub literal look like filler next to `api_key`, but #3 requires them stripped from the components and #7 requires varying them to leave `run_hash` unmoved. The written `run_identity.json` cannot be cut even though the components clause already names the same secret, because #5 and #6 read the on-disk stamp text rather than the components. `"base_url": "https://x/v1"` appears twice — in the stub and in the expected components — but #6 asserts the value survives into the stamp, so both mentions are load-bearing.

## `g4.r2.rule`

**Now (43 words):**

A cache-disabled run gets its identity from a caller-supplied id: `compute_run_identity` (and the component builder, `LLM._run_identity` and `LLM.__call__`) take a keyword-only `run_id: Optional[str] = None`, which is stored as the `run_id` component when `cache_enabled is False`, so replaying the same `run_id` is deterministic.

**Dropped, because no assertion checks it:**

- "never from randomness minted inside the identity code" — rationale contrasting with the old implementation; no assertion inspects the identity code for randomness, and #10's fresh-stub determinism is carried by the surviving determinism clause.
- "and lands in the same directory" — restatement of the preceding clause; #9 and #10 compare `run_hash_of`, which "replaying the same `run_id` is deterministic" already pins.
- "This replaces `xxh64(os.urandom(8))` at `llm.py:145-146`." — history and ticket detail; no assertion reads the removed expression or that file location.

**Kept despite looking like padding:** "so replaying the same `run_id` is deterministic" opens with "so" and reads like a consequence clause, but it is the rule #9 and #10 grade: the same id must yield the same run hash, including across a freshly built stub. Dropping it would leave nothing stating that identity is stable under replay. "which is stored as the `run_id` component when `cache_enabled is False`" is likewise the rule itself, graded by #7 and #8, and is what makes #11 and #12 (a different id, or the same id over different inputs, is a different run) follow.

## `g4.r2.scope`

**Now (26 words):**

A default id is minted from `os.environ.get("CURATOR_RUN_ID")`, falling back to `uuid.uuid4().hex`, then passed down as a parameter. A cached run carries `run_id: None` in its components.

**Dropped, because no assertion checks it:**

- "The one place a default id is minted is `LLM.__call__`:" — the uniqueness claim ("the one place") together with the minting site (`LLM.__call__`). No assertion inspects where the id is minted; #13/#14/#15/#16 only require that two unidentified runs get two distinct 32-char uuid4-hex ids, which holds wherever the mint lives.

**Kept despite looking like padding:** "then passed down as a parameter" reads like plumbing, but it is the only text implying a caller-supplied run_id exists and wins — forced by #9 (`llm(..., run_id='explicit-7')`) and #10 (`stamped_run_id(...) == "explicit-7"`). `run_id: None` stays verbatim for #3, and `uuid.uuid4().hex` stays verbatim because #16 checks length 32 and the hex alphabet, which a paraphrase like "a random id" would not produce.

## `g4.r2.failure_behavior`

**Now (16 words):**

`cache_enabled=False` with `run_id` `None` or `""` raises `RunIdentityError`; `cache_enabled=True` with a non-`None` `run_id` also raises `RunIdentityError`.

**Dropped, because no assertion checks it:**

- "— it is neither ignored nor folded into the hash": a restatement, in different words, of the rule immediately preceding it ("also raises `RunIdentityError`"). No assertion inspects a hash or checks that a `run_id` was ignored; all five raise-assertions are satisfied by the raise clause that remains.

**Kept despite looking like padding:** The two halves of the semicolon read like one rule said twice, but they are distinct input configurations — `cache_enabled=False` with an empty/`None` `run_id`, and `cache_enabled=True` with a non-`None` `run_id`. The five separate `pytest.raises(error)` assertions cover both families, so cutting either half would leave graded cases unstated. `RunIdentityError` is repeated rather than pronominalized because it is the exact name bound to `error`. Separately: assertions #6 and #7 (a refused run leaves no directory behind) have no support in the surviving text and had none in the original either — supplying it would be a rewrite, not a deletion.

## `g4.r2.observability`

**Now (48 words):**

`compute_run_identity(S, "d0", cache_enabled=False, run_id="local-run-7").run_hash` starts with `"v3-nocache-"` and has `len == 27`; a second identical call is byte-equal to it; `run_id="other"` gives a different value; `compute_run_identity(S, "d0").components["run_id"] is None`; and an AST scan of `run_identity.py` finds no import of `random`, `secrets` or `uuid` and no `urandom` attribute access.

**Dropped, because no assertion checks it:**

- The whole error-raising clause: "`pytest.raises(RunIdentityError)` for `cache_enabled=False, run_id=None`, for `run_id=""`, and for `cache_enabled=True, run_id="x"`;" — no assertion constructs an invalid call, names `RunIdentityError`, or checks any exception. That drop removes three separate ungraded design decisions: rejecting a missing `run_id` when caching is off, rejecting an empty-string `run_id`, and rejecting a `run_id` supplied when caching is on.

**Kept despite looking like padding:** `cache_enabled=False` on the first call reads like setup detail but is what assertion #6 turns on — it is the only thing tying the `"v3-nocache-"` prefix to the cache-disabled path rather than to every run, so the default call not starting with the prefix follows only from keeping it. The bare `compute_run_identity(S, "d0")` form earns its place twice, from #5 and #6. "attribute access" on `urandom` stays for #9 (`node.attr`); #10 reads `node.id`, which the surviving wording does not quite cover, but widening it would be adding text, not deleting.
