# Was every graded thing said, or only implied? — g4

**58 of 89** assertions rest on something a remark says outright.

- `stated` **58** — a reader was told
- `implied` **22** — a reader has to work it out, and may not
- `absent` **1** — nothing in the corpus bears on it
- `not_required` **8** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

> **These verdicts are what provoked the rewrites, not what the plant says now.** 16 remark(s) rewritten, 4 added, 1 not fixed. Re-run `settle --dry-run` for the verdicts on the corpus as it now stands.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g4.r1.exclusions_or_crossover#1` | stated | `g4.r1.l-param-keys`, `g4.r1.rev1`, `g4.r1.rev2` | Two remarks enumerate exactly base_url, azure_deployment, batch_size, completion_window as the contents of the named constant IDENTITY_BACKEND_PARAM_KEYS. |
| `g4.r1.exclusions_or_crossover#2` | stated | `g4.r1.l-param-keys`, `g4.r1.rev2` | "i'd keep it at exactly those four, the rest are just knobs" and "only the four in IDENTITY_BACKEND_PARAM_KEYS" state the cardinality outright. |
| `g4.r1.exclusions_or_crossover#3` | stated | `g4.r1.rev2`, `g4.r1.l-key-on-disk`, `g4.r1.l-param-keys` | rev2 says max_retries, request_timeout and api_key "never reach the digest", and the list is declared closed, so every non-allowlisted key is excluded by the stated rule rather than by inference. |
| `g4.r1.exclusions_or_crossover#4` | stated | `g4.r1.rev2`, `g4.r1.l-retries-fork`, `g4.r1.rev1` | "only the four ... fork the cache dir" plus konrad's verdict that "retry counts have no business buying a new cache directory" decide the unchanged-hash behaviour aloud. |
| `g4.r1.exclusions_or_crossover#5` | stated | `g4.r1.rev2`, `g4.r1.backend-params-whole-dict-dario`, `g4.r1.l-params-copy` | rev2 commits the four keys to the digest and the surviving shape from the whole-dict remarks ("same line shape as generation_params", handed out as a copy) makes the component a dict carrying those ke |
| `g4.r1.exclusions_or_crossover#6` | stated | `g4.r1.l-window-reuse`, `g4.r1.rev2` | gideon reports completion_window reusing the directory and rules "that one really does need to fork", matching rev2's statement that the four fork the cache dir. |
| `g4.r1.exclusions_or_crossover#7` | stated | `g4.r1.rev2`, `g4.r1.l-param-keys`, `g4.r1.backend-params-whole-dict-konrad` | The closed allowlist plus the named backend_params component means a dict with extra knobs mixed in reduces to the same filtered dict as the plain one. |
| `g4.r1.exclusions_or_crossover#8` | stated | `g4.r1.rev2`, `g4.r1.rev1`, `g4.r1.l-param-keys` | That non-identity keys never reach the digest is said directly, so extra knobs leave the run hash at baseline. |
| `g4.r1.observability#1` | stated | `g4.r1.l-keys-onelist`, `g4.r1.l-keys-order` | Konrad says the component names must live in one exported tuple read from both places and Dario names that tuple IDENTITY_COMPONENT_KEYS and says it is kept alphabetical, which is exactly sorted(compo |
| `g4.r1.observability#2` | stated | `g4.r1.l-keys-count`, `g4.r1.l-keys-onelist` | Gideon drops the number outright — the tuple has 12 entries — and the tuple is the component-name list, so the component count is told to the reader. |
| `g4.r1.observability#3` | stated | `g4.r1.rev1`, `g4.r1.rev2`, `g4.r1.l-param-keys`, `g4.r1.l-params-none` | Three remarks say the backend_params contribution is exactly the four keys of IDENTITY_BACKEND_PARAM_KEYS with base_url among them, and Nils fixes the shape as a dict, so a stub whose only listed key  |
| `g4.r1.observability#4` | stated | `g4.r1.l-key-on-disk`, `g4.r1.rev2`, `g4.r1.rev1` | Emil says api_key does not belong in the identity and Konrad says api_key never reaches the digest, so the key must not appear among the serialised components. |
| `g4.r1.observability#5` | stated | `g4.r1.l-key-on-disk`, `g4.r1.rev1` | Emil grepped the stamp file and found api_key in cleartext and says it does not belong on disk; Dario names the file run_identity.json and calls the cleartext key a reason for the change. |
| `g4.r1.observability#6` | **implied** | `g4.r1.l-key-on-disk`, `g4.r1.rev1`, `g4.r1.l-param-keys` | Nobody says what the stamp file contains after the fix; the reader has to compose Emil's grep (the file holds backend params) with the retained-keys list to conclude base_url is still written there, a |
| `g4.r1.observability#7` | stated | `g4.r1.rev1`, `g4.r1.rev2`, `g4.r1.l-retries-fork`, `g4.r1.l-key-on-disk` | Konrad states max_retries, request_timeout and api_key never reach the digest and Dario says key rotations and max_retries tweaks must stop minting fresh cache dirs — i.e. the same run. |
| `g4.r1.observability#8` | stated | `g4.r1.l-parse-func`, `g4.r1.l-system-prompt`, `g4.r1.l-completions-object`, `g4.r1.l-backend-resolved`, `g4.r1.l-keys-order` | Each of the four forks is decided out loud: parse_func_hash sits next to prompt_func_hash, the rewritten system_prompt should have been a fresh cache dir, toggling return_completions_object should mis |
| `g4.r1.observability#9` | stated | `g4.r1.l-backend-default` | Konrad reports the exact two calls, LLM(model_name="gpt-4o-mini") and the same with backend="openai", and states naming the default backend explicitly cannot change run identity. |
| `g4.r1.rule#1` | **implied** | `g4.r1.l-keys-order`, `g4.r1.l-keys-onelist`, `g4.r1.l-keys-count`, `g4.r1.l-parse-func`, `g4.r1.l-system-prompt`, `g4.r1.l-completions-object`, `g4.r1.l-schema-order` | The tuple's name, its count and its alphabetical ordering are said out loud and most member names surface somewhere in passing, but nobody ever lists the twelve together and `run_id` and `dataset_hash |
| `g4.r1.rule#10` | stated | `g4.r1.l-genparams-fix`, `g4.r1.backend-params-whole-dict-konrad`, `g4.r1.l-genparams-empty` | generation_params is spoken of throughout as a digest component, and dario's `dict(... or {})` fixes that it is carried as the dict itself. |
| `g4.r1.rule#11` | stated | `g4.r1.l-schema-dump` | Konrad says that when there's no format at all we put the string "text" in. |
| `g4.r1.rule#12` | stated | `g4.r1.l-schema-dump`, `g4.r1.l-schema-order` | Konrad gives sort_keys and separators=(",", ":") verbatim, and nils identifies the thing being dumped as the pydantic model's response_format schema going into the identity. |
| `g4.r1.rule#13` | **implied** | `g4.r1.l-system-prompt` | Dermot establishes that system_prompt must fork the cache dir but says nothing about representation, leaving the reader to decide that an absent prompt is carried as None rather than normalised to ""  |
| `g4.r1.rule#14` | stated | `g4.r1.l-system-prompt` | Dermot names system_prompt and says rewriting its wording should have produced a fresh cache dir, i.e. the prompt text itself is in the identity under that key. |
| `g4.r1.rule#15` | stated | `g4.r1.l-completions-object` | Emil names return_completions_object and says turning it on should miss the cache, putting the flag in the components under that key. |
| `g4.r1.rule#16` | stated | `g4.r1.l-completions-object` | The same remark makes the flag a component carried as itself; the False side is the same decision with no alternative representation in play. |
| `g4.r1.rule#17` | **implied** | `g4.r1.l-backend-default` | model_name appears only as a constructor argument in konrad's backend complaint; nobody says it is a component key of the digest, so its membership is inferred from the surrounding story rather than t |
| `g4.r1.rule#18` | stated | `g4.r1.l-keys-order`, `g4.r1.l-window-reuse` | Dario names batch_mode as one of the entries sitting in IDENTITY_COMPONENT_KEYS. |
| `g4.r1.rule#19` | **absent** | — | No remark in the corpus mentions dataset_hash, a dataset fingerprint, or anything the reader could map onto this key or its passed-in value. |
| `g4.r1.rule#2` | stated | `g4.r1.l-keys-count`, `g4.r1.l-keys-onelist`, `g4.r1.l-keys-order` | Gideon says the tuple has 12 entries and konrad/dario name IDENTITY_COMPONENT_KEYS as the one exported tuple, so the count attaches to the right name. |
| `g4.r1.rule#3` | stated | `g4.r1.l-keys-order` | Dario says outright that IDENTITY_COMPONENT_KEYS is kept alphabetical, and flags batch_mode sitting above backend as the violation to fix. |
| `g4.r1.rule#4` | **implied** | `g4.r1.l-keys-count`, `g4.r1.l-keys-onelist`, `g4.r1.l-keys-order` | That the computed components dict has exactly the same twelve keys as the exported tuple follows from 'export one tuple and read it from both', but the twelve keys themselves are never enumerated and  |
| `g4.r1.rule#5` | stated | `g4.r1.l-parse-func` | Nikolai names `prompt_func_hash` as an existing component produced by a helper over the prompt function, which is exactly what this assertion checks. |
| `g4.r1.rule#6` | stated | `g4.r1.l-parse-func` | Nikolai says `parse_func_hash` belongs right next to `prompt_func_hash` using the same helper, naming both the key and its computation. |
| `g4.r1.rule#7` | **implied** | `g4.r1.l-parse-func` | Nobody says the two hashes must differ; the reader has to conclude from 'same helper, two different functions' that the parse hash is not accidentally the prompt hash. |
| `g4.r1.rule#8` | **implied** | `g4.r1.l-parse-func` | No remark discusses a missing parse_func at all, so passing None straight through the helper rather than guarding with a conditional is the reader's own call. |
| `g4.r1.rule#9` | stated | `g4.r1.l-genparams-fix`, `g4.r1.l-genparams-empty` | Dario prescribes `dict(... or {})` so the missing case and the empty case hash to one thing, which is precisely this assertion. |
| `g4.r1.scope#1` | **implied** | `g4.r1.l-backend-resolved`, `g4.r1.l-backend-default` | dermot says the identity should read the backend off the request processor instead of the caller's None, but nobody says the LLM object itself carries a `backend` attribute reporting the resolved name |
| `g4.r1.scope#2` | **implied** | `g4.r1.l-backend-default`, `g4.r1.l-backend-resolved` | konrad names `backend="openai"` only as a constructor keyword; no remark says the LLM exposes a `backend` attribute at all, so the reader has to supply the existence of the accessor being read here. |
| `g4.r1.scope#3` | stated | `g4.r1.l-backend-resolved`, `g4.r1.l-backend-default`, `g4.r1.l-keys-order` | dermot says the backend we key on must be read off the request processor after it picks one rather than the caller's None, and konrad says the implicit call must land in the same cache dir as the one  |
| `g4.r1.scope#4` | stated | `g4.r1.l-backend-default`, `g4.r1.l-backend-resolved` | konrad's complaint is literally about the run declared with backend="openai", and he rules that it must hash the same as the implicit one, so "openai" is the backend component for the declared LLM. |
| `g4.r1.scope#5` | **implied** | `g4.r1.l-backend-resolved` | the only remark on where the value comes from points at the request processor, so nobody says the identity code reads the object's own `.backend` — the reader must decide on their own to resolve insid |
| `g4.r1.scope#6` | stated | `g4.r1.l-params-none` | nils says backend_params comes back None unless you pass it and that the property should just return {}. |
| `g4.r1.scope#7` | stated | `g4.r1.l-params-none`, `g4.r1.l-params-copy` | nils' "comes back None unless you pass it" states the round-trip for the passed case, and dario's copy rule keeps the handed-out dict equal to the one given. |
| `g4.r1.scope#8` | stated | `g4.r1.l-params-copy` | dario says the processor edits backend_params in place mid-run so whatever is handed out must be a copy of it. |
| `g4.r2.failure_behavior#1` | stated | `g4.r2.l10`, `g4.r2.l9` | Konrad says cache-off with no id "should have stoped at the door with an error", which is the decision to raise made out loud. |
| `g4.r2.failure_behavior#2` | stated | `g4.r2.l9`, `g4.r2.l10` | Gideon reports the run_id arriving as "" with cache off and Konrad answers that exact incident by saying it should have errored at the door. |
| `g4.r2.failure_behavior#3` | stated | `g4.r2.l11` | Dermot describes a run id passed on a normal cached run being ignored and says plainly "it should refuse." |
| `g4.r2.failure_behavior#4` | **implied** | `g4.r2.l11`, `g4.r2.l10` | The corpus names only three refusal scenarios, so a fourth parametrized case — most likely an empty-string id on the cached path — rests on the reader deciding that "someone passed a run id" also cove |
| `g4.r2.failure_behavior#5` | **implied** | `g4.r2.l11`, `g4.r2.l10`, `g4.r2.l12` | A fifth case exceeds anything described; the reader must extrapolate the refusal rule to a combination no remark reports as a symptom or settles in review. |
| `g4.r2.failure_behavior#6` | stated | `g4.r2.l12` | Nikolai says the refusal currently fires after the run dir is already made and that he is sweeping up empty stamped dirs, which is the requirement that a refused call leave no directory. |
| `g4.r2.failure_behavior#7` | **implied** | `g4.r2.l12`, `g4.r2.l11` | The reader must supply that the ordering fix in l12 — which never names a path — also governs the cached-run refusal, since l11's complaint there is dir reuse rather than dir creation. |
| `g4.r2.observability#1` | stated | `g4.r2.rev2`, `g4.r2.rev1`, `g4.r2.l13` | konrad's rev2 says outright that in the disable_cache path "run_hash is v3-nocache- plus a digest of the callers run_id", and rev1 names the `cache_enabled is False` / keyword-only `run_id` signature  |
| `g4.r2.observability#10` | **implied** | `g4.r2.l15`, `g4.r2.rev2` | As with the attribute form, the bare name urandom is never named in the corpus and only follows if the reader extends emil's grep for random/uuid to entropy in general. |
| `g4.r2.observability#2` | **implied** | `g4.r2.l13`, `g4.r2.rev2` | No remark gives a length or a digest width; the reader has to notice gideon's incidental viewer string v3-nocache-9f2b1c0ad4e5f678, count it to 27, and decide that 16 hex characters is the rule rather |
| `g4.r2.observability#3` | stated | `g4.r2.l2`, `g4.r2.l14`, `g4.r2.rev1` | dermot's l2 states the rule ("the same label twice has to give the same hash") and dario's l14 reports running it twice with the same id and getting clean-diffing stamps. |
| `g4.r2.observability#4` | stated | `g4.r2.l14`, `g4.r2.rev2` | dario's l14 says changing one character of the id gave a different dir "which is what we want", and rev2 makes run_hash a digest of that run_id. |
| `g4.r2.observability#5` | stated | `g4.r2.l8`, `g4.r2.l7`, `g4.r2.rev1` | dario's l8 decides out loud that it should stay null for a cache hit, emil's l7 reports the field being null for cached runs, and rev1 names it as the run_id component stored only when cache_enabled i |
| `g4.r2.observability#6` | stated | `g4.r2.rev2`, `g4.r2.l13` | rev2 scopes the v3-nocache- prefix to the disable_cache path and gideon's l13 shows those dirs sitting "beside the plain v3- dirs", so the cached form is named as a distinct, unprefixed one. |
| `g4.r2.observability#7` | stated | `g4.r2.l15`, `g4.r2.rev1`, `g4.r2.rev2` | emil's l15 says he grepped run_identity.py for random and uuid and found nothing, and that either one appearing costs reproducibility; rev1 records the uuid4 being dropped from that very branch. |
| `g4.r2.observability#8` | stated | `g4.r2.l15`, `g4.r2.rev1` | Same decision as the plain-import case — l15 bans random and uuid from run_identity.py by name regardless of import form, with rev1 removing the uuid4 that was there. |
| `g4.r2.observability#9` | **implied** | `g4.r2.l15`, `g4.r2.rev2` | Nobody mentions urandom or os entropy at all; the reader must generalize l15's "random and uuid" ban into a rule against every nondeterministic source. |
| `g4.r2.rule#1` | stated | `g4.r2.rev1`, `g4.r2.l4` | rev1 says outright that compute_run_identity's disable_cache branch now takes a run_id, and l4 pins the spelling as `run_id` in the signature. |
| `g4.r2.rule#10` | stated | `g4.r2.l1`, `g4.r2.rev2`, `g4.r2.l14`, `g4.r2.l15` | The whole complaint (l1, rev2) is about two separate launches of the same sweep landing in two dirs, and rev2/l14 settle that the nocache hash is a digest of the caller's run_id, so a fresh object wit |
| `g4.r2.rule#11` | stated | `g4.r2.l14` | l14: changed one character of the id and got a different dir, "which is what we want". |
| `g4.r2.rule#12` | **implied** | `g4.r2.rev1`, `g4.r2.l8`, `g4.r2.rev2`, `g4.r2.l3` | The reader must infer from "stored as the run_id component" plus l8's "everything else in the components block" that the whole block is hashed — while rev2's flat "v3-nocache- plus a digest of the cal |
| `g4.r2.rule#2` | stated | `g4.r2.rev1` | rev1 says "keyword-only run_id now" about compute_run_identity. |
| `g4.r2.rule#3` | **implied** | `g4.r2.l10`, `g4.r2.l9`, `g4.r2.l11` | Nobody names a default; the reader has to conclude from "with no id and cache off that should have stopped at the door" that the parameter is omittable, and then pick None themselves over a required a |
| `g4.r2.rule#4` | **implied** | `g4.r2.l6`, `g4.r2.l12`, `g4.r2.l3`, `g4.r2.l4` | l6 has llm.py minting the id itself and passing it down, l3 says the input must come from outside and l12 says the refusal must surface out of __call__ — together they point at the LLM layer accepting |
| `g4.r2.rule#5` | **implied** | `g4.r2.rev1`, `g4.r2.l6`, `g4.r2.l4` | The "keyword-only" wording in rev1 is about compute_run_identity only; nothing describes the LLM-side parameter's kind, so a reader plumbing it through **kwargs would fail this and never be told other |
| `g4.r2.rule#6` | **implied** | `g4.r2.l10`, `g4.r2.l3`, `g4.r2.rev1` | Same gap as #3, one layer up: the error-on-missing-id complaints suggest the argument can be omitted, but no remark attaches None to the LLM-side parameter. |
| `g4.r2.rule#7` | n/a | `g4.r2.rev1` | This re-reads the flag the test itself passed in, a fixture precondition; rev1 does name the field cache_enabled anyway. |
| `g4.r2.rule#8` | stated | `g4.r2.rev1`, `g4.r2.rev2` | rev1 says the id is "stored as the run_id component when cache_enabled is False" — the component name and the fact that the caller's value goes in it are both said out loud. |
| `g4.r2.rule#9` | stated | `g4.r2.l14`, `g4.r2.l2`, `g4.r2.rev2`, `g4.r2.l15` | l2 says the same label twice has to give the same hash and l14 reports running it twice with the same id and getting clean-diffing stamps. |
| `g4.r2.scope#1` | n/a | `g4.r2.l8` | The `with pytest.raises(_Stop)` is the suite's own abort sentinel used to run the pipeline up to the identity/dir step; the corpus owes nothing to test scaffolding. |
| `g4.r2.scope#10` | stated | `g4.r2.rev1` | Dario states the caller's run_id is "stored as the run_id component when cache_enabled is False", which is exactly what the stamped value is asserted to be. |
| `g4.r2.scope#11` | n/a | `g4.r2.l6` | Test-local sentinel used to abort the first unidentified run; no corpus claim is at stake. |
| `g4.r2.scope#12` | n/a | `g4.r2.l6` | Same sentinel abort for the second unidentified run, purely fixture mechanics. |
| `g4.r2.scope#13` | stated | `g4.r2.l6`, `g4.r2.rev2`, `g4.r2.l14`, `g4.r2.l9` | Nils says a fresh uuid4 hex is minted per local run, and rev2/l14 say the dir is a digest of the caller's run_id so differing ids give differing dirs — with l9 treating jobs piling into one dir as the |
| `g4.r2.scope#14` | stated | `g4.r2.l6` | "we mint a fresh uuid4 hex" per run is a decision made out loud that two unidentified runs get different ids. |
| `g4.r2.scope#15` | stated | `g4.r2.l9`, `g4.r2.l10`, `g4.r2.l6` | Gideon reports the empty-string id as the defect and Konrad says that state must never quietly proceed, while l6 says a real uuid4 hex is minted instead. |
| `g4.r2.scope#16` | stated | `g4.r2.l6` | Nils names the exact format — "a fresh uuid4 hex" — which is the 32 lowercase hex characters the assertion checks. |
| `g4.r2.scope#2` | n/a | `g4.r2.l8` | That a single cached invocation produces exactly one run directory is baseline behaviour and the fixture's own setup for the next assertion. |
| `g4.r2.scope#3` | stated | `g4.r2.l8`, `g4.r2.l7` | Dario says outright it "should stay null for a cache hit" and names the components block, with Emil corroborating the field is null for cached runs. |
| `g4.r2.scope#4` | n/a | `g4.r2.l5` | Harness plumbing: the _Stop sentinel is how the test stops the run after the directory is made. |
| `g4.r2.scope#5` | n/a | `g4.r2.l5` | Harness plumbing: the second _Stop-wrapped invocation exists only to produce a repeat run for the directory count. |
| `g4.r2.scope#6` | stated | `g4.r2.l5`, `g4.r2.l2`, `g4.r2.l14` | Konrad exports CURATOR_RUN_ID specifically so the directory can be found again, Dermot says the same label twice must give the same hash, and Dario confirms same id twice gives one dir. |
| `g4.r2.scope#7` | **implied** | `g4.r2.l5`, `g4.r2.l6`, `g4.r2.rev1` | Nobody says the value of CURATOR_RUN_ID itself is what gets stored as the run_id component — the reader must chain l6's "nobody exports anything, so we mint" with rev1's "stored as the run_id componen |
| `g4.r2.scope#8` | n/a | `g4.r2.rev1` | The _Stop wrapper is the suite's mechanism for executing one call, not a behavioural claim. |
| `g4.r2.scope#9` | stated | `g4.r2.rev1`, `g4.r2.l4`, `g4.r2.l6` | Dario announces a keyword-only `run_id`, Nikolai fixes the spelling of `run_id` in the signature, and Nils says it is passed down as an argument from llm.py. |

### `g4.r1.observability#6` — implied

```python
assert "https://x/v1" in stamp_text
```

Nobody says what the stamp file contains after the fix; the reader has to compose Emil's grep (the file holds backend params) with the retained-keys list to conclude base_url is still written there, and could reasonably write only the hash and metadata.

### `g4.r1.rule#1` — implied

```python
assert tuple(keys) == TWELVE, f"IDENTITY_COMPONENT_KEYS is {tuple(keys)!r}"
```

The tuple's name, its count and its alphabetical ordering are said out loud and most member names surface somewhere in passing, but nobody ever lists the twelve together and `run_id` and `dataset_hash` are never mentioned by anyone, so the exact tuple has to be assembled — and partly invented — by the reader.

### `g4.r1.rule#13` — implied

```python
# system_prompt and return_completions_object are carried as themselves.
    assert components_of(identity_for(make_stub(system_prompt=None)))["system_prompt"] is None
```

Dermot establishes that system_prompt must fork the cache dir but says nothing about representation, leaving the reader to decide that an absent prompt is carried as None rather than normalised to "" or hashed.

### `g4.r1.rule#17` — implied

```python
# ... and the two things the old fingerprint already had are still here.
    assert components_of(identity_for(make_stub(model_name="gpt-4o-mini")))["model_name"] == "gpt-4o-mini"
```

model_name appears only as a constructor argument in konrad's backend complaint; nobody says it is a component key of the digest, so its membership is inferred from the surrounding story rather than told.

### `g4.r1.rule#19` — absent

```python
assert components_of(identity_for(make_stub(), dataset_hash="9f1c8e2b7d4a6053"))["dataset_hash"] == "9f1c8e2b7d4a6053"
```

No remark in the corpus mentions dataset_hash, a dataset fingerprint, or anything the reader could map onto this key or its passed-in value.

### `g4.r1.rule#4` — implied

```python
assert tuple(sorted(components)) == TWELVE, f"the identity was computed from {sorted(components)}"
```

That the computed components dict has exactly the same twelve keys as the exported tuple follows from 'export one tuple and read it from both', but the twelve keys themselves are never enumerated and two of them are never named at all.

### `g4.r1.rule#7` — implied

```python
assert named["parse_func_hash"] != named["prompt_func_hash"]
```

Nobody says the two hashes must differ; the reader has to conclude from 'same helper, two different functions' that the parse hash is not accidentally the prompt hash.

### `g4.r1.rule#8` — implied

```python
assert components_of(identity_for(make_stub(parse_func=None)))["parse_func_hash"] == function_hash(None)
```

No remark discusses a missing parse_func at all, so passing None straight through the helper rather than guarding with a conditional is the reader's own call.

### `g4.r1.scope#1` — implied

```python
assert auto.backend == "openai", f"LLM.backend must be the resolved backend, got {auto.backend!r}"
```

dermot says the identity should read the backend off the request processor instead of the caller's None, but nobody says the LLM object itself carries a `backend` attribute reporting the resolved name — a reader can satisfy dermot by reaching into `_request_processor.backend` inside the identity function and leaving `llm.backend` as the declared None.

### `g4.r1.scope#2` — implied

```python
assert declared.backend == "openai"
```

konrad names `backend="openai"` only as a constructor keyword; no remark says the LLM exposes a `backend` attribute at all, so the reader has to supply the existence of the accessor being read here.

### `g4.r1.scope#5` — implied

```python
# The value is read off the object's own `backend`, whatever it says.
    assert components_of(identity_for(make_stub(backend="litellm")))["backend"] == "litellm"
```

the only remark on where the value comes from points at the request processor, so nobody says the identity code reads the object's own `.backend` — the reader must decide on their own to resolve inside the LLM property and have the digest read that attribute.

### `g4.r2.failure_behavior#4` — implied

```python
with pytest.raises(error):
```

The corpus names only three refusal scenarios, so a fourth parametrized case — most likely an empty-string id on the cached path — rests on the reader deciding that "someone passed a run id" also covers "", which nobody says.

### `g4.r2.failure_behavior#5` — implied

```python
with pytest.raises(error):
```

A fifth case exceeds anything described; the reader must extrapolate the refusal rule to a combination no remark reports as a symptom or settles in review.

### `g4.r2.failure_behavior#7` — implied

```python
assert cached not in run_dirs(cache)
```

The reader must supply that the ordering fix in l12 — which never names a path — also governs the cached-run refusal, since l11's complaint there is dir reuse rather than dir creation.

### `g4.r2.observability#10` — implied

```python
assert node.id != "urandom", f"{module.__name__} reads urandom"
```

As with the attribute form, the bare name urandom is never named in the corpus and only follows if the reader extends emil's grep for random/uuid to entropy in general.

### `g4.r2.observability#2` — implied

```python
assert len(run_hash) == 27, f"{run_hash!r} is {len(run_hash)} characters"
```

No remark gives a length or a digest width; the reader has to notice gideon's incidental viewer string v3-nocache-9f2b1c0ad4e5f678, count it to 27, and decide that 16 hex characters is the rule rather than one sample.

### `g4.r2.observability#9` — implied

```python
assert node.attr != "urandom", f"{module.__name__} reads os.urandom"
```

Nobody mentions urandom or os entropy at all; the reader must generalize l15's "random and uuid" ban into a rule against every nondeterministic source.

### `g4.r2.rule#12` — implied

```python
# ... and so is the same id over different inputs.
    assert run_hash_of(identity_for(stub, "other", cache_enabled=False, run_id="local-run-7")) != run_hash_of(identity)
```

The reader must infer from "stored as the run_id component" plus l8's "everything else in the components block" that the whole block is hashed — while rev2's flat "v3-nocache- plus a digest of the callers run_id" and l3's "nothing stable on our side worth hashing" push them toward a hash of the id alone, which fails this.

### `g4.r2.rule#3` — implied

```python
assert params["run_id"].default is None
```

Nobody names a default; the reader has to conclude from "with no id and cache off that should have stopped at the door" that the parameter is omittable, and then pick None themselves over a required arg or an empty-string default (l9 even shows an empty string arriving).

### `g4.r2.rule#4` — implied

```python
assert "run_id" in taken, f"{name} takes {list(taken)}, so no caller can hand it a run id"
```

l6 has llm.py minting the id itself and passing it down, l3 says the input must come from outside and l12 says the refusal must surface out of __call__ — together they point at the LLM layer accepting a caller's id, but no remark says __call__ or the component builder takes a run_id parameter.

### `g4.r2.rule#5` — implied

```python
assert taken["run_id"].kind in (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
```

The "keyword-only" wording in rev1 is about compute_run_identity only; nothing describes the LLM-side parameter's kind, so a reader plumbing it through **kwargs would fail this and never be told otherwise.

### `g4.r2.rule#6` — implied

```python
assert taken["run_id"].default is None
```

Same gap as #3, one layer up: the error-on-missing-id complaints suggest the argument can be omitted, but no remark attaches None to the LLM-side parameter.

### `g4.r2.scope#7` — implied

```python
assert stamped_run_id(cache, named[0]) == "ci-job-42", "the environment's id is what the run is identified by"
```

Nobody says the value of CURATOR_RUN_ID itself is what gets stored as the run_id component — the reader must chain l6's "nobody exports anything, so we mint" with rev1's "stored as the run_id component".
