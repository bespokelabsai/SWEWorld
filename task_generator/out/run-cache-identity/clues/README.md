# Clues for g4 — Versioned run identity for the curator cache

48 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/latest`.

Clue window `2025-03-14` to `2026-01-27`; herrings before `2025-03-13`.

**Nothing here has been inserted into the corpus.** This is the plan: what each person says, where it goes, and why it belongs there.

## The task the agent is given

Replace the ad-hoc cache fingerprint in `llm/llm.py` with an explicit, versioned run identity.

### 1. New module — `src/bespokelabs/curator/run_identity.py`

Top-level, so `db.py` can import it without a cycle. It exports:

- `RUN_IDENTITY_VERSION: int = 3` and `RUN_IDENTITY_FILENAME: str = "run_identity.json"`.
- An exception family `RunIdentityError(RuntimeError)`, with subclasses
  `RunIdentityMismatch(path, expected_run_hash, found_run_hash, mismatched_components)` and
  `CachedResponseMismatch(cache_dir, field, expected, found)` — each argument kept as a same-named attribute.
- Frozen dataclasses `RunIdentity(run_hash, digest, identity_version, cache_enabled, components)`,
  `RunStamp(identity_version, run_hash, digest, components, created_at, updated_at)` with `to_dict()` / `from_dict()`,
  and `RunDirectoryCheck(status, stamp, previous_version)`.
- Functions `compute_run_identity(llm, dataset_hash, *, cache_enabled: bool = True, ...)` — duck-typed on the
  object it is handed, no `isinstance`, no import of `LLM` — plus
  `write_run_stamp(run_cache_dir, identity, *, now: str, created_at: Optional[str] = None)`,
  `read_run_stamp(run_cache_dir) -> Optional[RunStamp]` and
  `reconcile_run_directory(run_cache_dir, identity, *, now: str) -> RunDirectoryCheck`.

### 2. The digest and the run hash

- `digest` is a 16-char lowercase `xxh64` hexdigest over a canonical, key-sorted, version-tagged
  serialisation of the identity components.
- `run_hash` for a normal cached run is `f"v3-{digest}"`, and is the cache directory name.

### 3. The stamp file

- Holds exactly `identity_version`, `run_hash`, `digest`, `components`, `created_at`, `updated_at`,
  as `json.dumps(..., indent=2, sort_keys=True)` plus a trailing newline.
- `created_at` is preserved when supplied; `updated_at` is always `now`.
- `read_run_stamp` returns `None` for an absent, unparseable or incomplete file.

### 4. `reconcile_run_directory`

Returns `status` in `"created" | "adopted" | "upgraded" | "matched"`:

- create/stamp a missing or empty directory,
- adopt an unstamped non-empty one,
- rewrite an older-version stamp keeping its `created_at`,
- refresh `updated_at` on an exact match.

`previous_version` is `None` for a create and for an adopt, the old integer for an upgrade, and `3` for a match.

It raises `RunIdentityMismatch` (deleting nothing) when a same-version stamp disagrees or a newer
`identity_version` is found, with `mismatched_components` the alphabetically sorted differing component keys,
or `("identity_version",)`.

### 5. `llm/llm.py`

- Move `_get_function_hash` verbatim into the new module and re-export it there.
- Delete `_hash_fingerprint` in favour of `LLM._run_identity(dataset_hash, *, cache_enabled: bool, ...)`.
- Add `LLM.backend` and `LLM.backend_params` properties.
- `LLM.__call__` reconciles the run directory before using it.
- `LLM._get_cached_response` re-raises `RunIdentityError`, while still returning `None`
  (with the existing warning) for anything else.

### 6. `db.py`

- Add `RUNS_COLUMNS`, including new `parse_func` and `identity_version` columns.
- `validate_schema()` migrates missing columns forward via `ALTER TABLE` and returns the tuple of names
  it added; unexpected columns stay fatal.
- `store_metadata()` writes `parse_func` and `identity_version`, updates `session_id` only when the
  incoming value is not `None`, and returns `"inserted"` or `"updated"`.

### 7. `curator_response.py`

- Add a `run_identity: Optional[Dict[str, Any]] = None` field, declared last, and emit it from `to_dict()`.
- `load(cls, cache_dir, dataset, *, verify: bool = True)` checks the recorded `"dataset"` block
  (`fingerprint`, `size`, `columns`) against the dataset it is handed, raising `CachedResponseMismatch`
  on the first differing field, and skipping the check when the key is absent or `verify=False`.

### 8. `base_request_processor.py`

`BaseRequestProcessor.run()` sets `self._is_cached_dataset = False` as its first statement.

## Every remark, in the order a reader would meet them

| date | where | who | says | carries |
|---|---|---|---|---|
| 2025-01-22 | #cookbooks *(new)* | konrad | Replaced the uuid4 in the disable_cache path with a datetime.now().isoformat() segment, so the nocache run dirs sort chronologically on disk now. Much easier to eyeball. | *herring* |
| 2025-01-28 | #code-review *(new)* | konrad | Look, settled in review this morning - the whole backend_params dict gets hashed, sorted, same as generation_params. any param change is a diferent run and a different cache dir. | *herring* |
| 2025-01-30 | #incidents | dario | the way i'm scoping it: backend_params goes into the digest whole, sorted items, same line shape as generation_params - every key in that dict is part of the run identity | *herring* |
| 2025-02-12 | #code-review | dario | on normalize-before-hashing — settled in review that the nocache path doesn't hash at all, compute_run_identity mints a uuid4 under `if disable_cache:`, nothing to collide with or look up | *herring* |
| 2025-03-14 | #code-review *(new)* | gideon | The test just counts what compute_run_identity hands back — 12 components, sorted — so it screams the second someone hashes something that never made it into the list. | `rule`, `observability` |
| 2025-03-14 | #engineering *(new)* | konrad | look, it goes in as json.dumps(..., sort_keys=True, separators=(",", ":")) — a string, not the dict — and when there's no format at all we just put "text" in. | `rule` |
| 2025-03-14 | #code-review | gideon | on the params side - popped batch_size off what llm.backend_params handed me, read it again and batch_size was still there, so mutating what you got back doesn't reach the LLM | `scope` |
| 2025-03-17 | #code-review *(new)* | konrad | look, the component names are written out in two places and they've already drifted apart - we should export one tuple and read it from both | `rule` |
| 2025-03-17 | #engineering *(new)* | konrad | Look, LLM(model_name="gpt-4o-mini") and the same call with backend="openai" hashed to two different run_hash values, same processor either way. naming the default cant change identity. | `scope`, `observability` |
| 2025-03-18 | #random | emil | Same gap on the metadata side - filtered the stamps by run_id to pull last week's runs and got nothing back for the cached ones, components has "run_id": null. | `scope`, `observability` |
| 2025-03-19 | #engineering *(new)* | konrad | look, I bumped max_retries from 5 to 8 for a rerun and curator went and re-ran all 40k rows. retry counts have no business buying a new cache directory. | `exclusions_or_crossover` |
| 2025-03-19 | #releases *(new)* | dario | on dermot's point - the components dict just takes whatever `llm.backend` hands back as the `backend` value, the digest doesnt go poking at the processor itself | `scope` |
| 2025-03-19 | #pipeline *(new)* | konrad | CI job on our side exports CURATOR_RUN_ID=$GITHUB_RUN_ID before the eval sweep now — os.environ.get picks it up and that string is the run_id component, so I can find the direcotry. | `scope` |
| 2025-03-20 | #code-review | nils | @Emil while you're in there - passed {"batch_size": 64, "max_retries": 7} and llm.backend_params gives both back. pass nothing and it's None, three call sites check for that - should be {}. | `scope` |
| 2025-03-20 | #engineering *(new)* | emil | grepped run_identity.json on the shared box — api_key is in there in cleartext, next to request_timeout and max_retries. none of that belongs in the stamp or in the digest. | `exclusions_or_crossover`, `observability` |
| 2025-03-20 | #cookbooks *(new)* | konrad | the review call to hash the whole backend_params dict sorted is gone - only the four in IDENTITY_BACKEND_PARAM_KEYS fork the cache dir, max_retries request_timeout and api_key never reach the digest | `exclusions_or_crossover` |
| 2025-03-21 | #code-review | nils | related: `response_format` reaches us as `rf.model_json_schema()`, a plain dict — same pydantic model on two boxes, keys came back in a different order, two cache dirs. | `rule` |
| 2025-03-21 | #cookbooks *(new)* | nikolai | one more on parse_func when a run hasnt got one we hand None straight to _get_function_hash no conditional round it and the helper hashes that fine | `rule` |
| 2025-03-21 | #pipeline *(new)* | nils | let me think - locally nobody exports it, so llm.py mints uuid.uuid4().hex and hands that down as the run_id argument LLM.__call__ and LLM._run_identity both take. | `scope` |
| 2025-03-24 | #engineering *(new)* | gideon | so basically i switched completion_window to 24h and it happily reused the directory from the 1h batch, that one really does need to fork honestly. | `exclusions_or_crossover` |
| 2025-03-24 | #pipeline *(new)* | dario | honestly it should stay null for a cache hit - we only reach for an id on the way into the disable_cache branch, a cached run is already pinned by the rest of the components block | `scope` |
| 2025-03-24 | #cookbooks *(new)* | konrad | My datetime.now().isoformat() segment in the disable_cache path is gone - two sweeps, two dirs. run_hash is v3-nocache- plus a digest of the whole components block, run_id just one entry. | `rule`, `observability` |
| 2025-03-26 | #engineering *(new)* | nils | let me think - @Dario, i poked at components["backend_params"]["completion_window"] on a run that never set one and got a KeyError, not a None. thats what i'd want honestly. | `observability` |
| 2025-03-27 | #help | gideon | also on the caching-and-resume cleanup, kicked the same disable-cache sweep off twice for the flake hunt and landed in two diferent run dirs, so I had nothing to point CI at | `rule` |
| 2025-03-31 | #pipeline *(new)* | emil | honestly, with the cache off theres no stable input of ours to key on, so the id gets handed in - run_id: Optional[str] = None, threaded down from __call__. | `rule`, `scope` |
| 2025-03-31 | #code-review | dario | dropped the uuid4 in compute_run_identity's `if disable_cache:` branch — reruns kept landing in new dirs. keyword-only run_id: Optional[str] = None now, stored as the run_id component when cache_enabled is False | `rule` |
| 2025-04-02 | #code-review | emil | same family of annoyance: turned return_completions_object on and the cached rows still had no raw objects in them, deleted the dir by hand again. that should just miss. | `rule` |
| 2025-04-03 | #pipeline | dermot | yeah — and whatever we key that per-run file on, the same label twice has to give the same hash, otherwise reattaching to a run is guesswork | `rule` |
| 2025-04-03 | #cookbooks *(new)* | nikolai | @Konrad its `run_id` in the signature not runId, and a named keyword-only arg on __call__ not something we dig out of **kwargs. fixed both spots you flagged. | `rule` |
| 2025-04-03 | #viewer | gideon | same row identity problem in the other direction tbh - v3-nocache-9f2b1c0ad4e5f678 beside the plain v3- dirs, always 27 chars, prefix plus 16 hex, and nothing says which run. | `observability` |
| 2025-04-07 | #general *(new)* | nils | let me think - dataset_hash is one of the twelve, and it goes into the components dict exactly as the caller handed it to us, we dont re-derive it on our side | `rule` |
| 2025-04-11 | #cookbooks | dermot | same key - the caller hands us None most of the time, so LLM gets a `backend` property returning `self._request_processor.backend`, the resolved name. thats the only one reaching down there. | `scope` |
| 2025-04-11 | #incidents *(new)* | emil | grepped run_identity.py again after the merge - no random, no secrets, no uuid, no os.urandom in that module, not even an import; the only uuid import left is llm.py. | `observability`, `scope` |
| 2025-04-15 | #pipeline *(new)* | dario | ran it twice with the same id and the two stamps diff clean, then changed one character of the id and got a different dir, which is what we want | `observability` |
| 2025-04-16 | #code-review *(new)* | dario | nit: IDENTITY_COMPONENT_KEYS is the one exported tuple and we're keeping it alphabetical — backend, backend_params, batch_mode — and batch_mode is sitting above backend here. | `rule` |
| 2025-04-17 | #random | gideon | honestly though it's not only helpers - a run with generation_params=None and one with an empty dict landed in two seperate directories last night, and it was the same run | `rule` |
| 2025-04-17 | #engineering *(new)* | nikolai | pulled run_identity.json off the box after the rerun response_format is one line no spaces in there and json load gives me back a str thats what i wanted | `rule` |
| 2025-04-18 | #incidents | nikolai | edited parse_func to drop the refusals and got yesterdays parsed rows back parse_func_hash is _get_function_hash(llm.prompt_formatter.parse_func) same helper as prompt_func_hash different function so the two never match | `rule` |
| 2025-04-18 | #engineering | dario | and when we do fold them into the key, always carry it as `dict(... or {})` before it goes in - then the missing case and the empty case hash to one thing | `rule` |
| 2025-04-21 | #engineering | dermot | on our side IDENTITY_BACKEND_PARAM_KEYS is a frozenset[str] — base_url, azure_deployment, batch_size, completion_window. building the components we walk llm.backend_params and keep what's a member, the rest are knobs. | `exclusions_or_crossover` |
| 2025-04-21 | #pipeline | dario | also stopped hashing backend_params whole — it's IDENTITY_BACKEND_PARAM_KEYS now: base_url, azure_deployment, batch_size, completion_window. that run set only base_url and the backend_params block in run_identity.json is that one line. | `exclusions_or_crossover`, `observability` |
| 2025-04-23 | #pipeline | dermot | that matches what I saw, rewrote the system_prompt late night and the run came back in two seconds with the old wording. it goes in as itself, None when there isnt one | `rule` |
| 2025-04-23 | #code-review *(new)* | dario | honestly the processor trims backend_params in place mid-run, so we hold what came into __init__ off to one side — what llm hands back is built off ours, never the processors | `scope` |
| 2025-04-28 | #viewer | gideon | one thing I hit while digging - with cache off, run_id "" and run_id None both piled into the same dir, three jobs, no way to tell them apart. | `failure_behavior` |
| 2025-05-01 | #engineering | dermot | same shape: someone passed a run id on a normal cached run, we ignored it, lost an hour on why the dir was the old one. it should refuse. | `failure_behavior` |
| 2025-05-02 | #releases *(new)* | dario | to be honest on dermot's one: cache_enabled True with any run_id that isn't None — "" counts — is a RunIdentityError, we don't get to guess which dir they meant | `failure_behavior` |
| 2025-05-06 | #incidents *(new)* | konrad | Look, our CI wrapper passes os.environ.get("CURATOR_RUN_ID") straight in as run_id and nothing was exported, so the disable-cache sweep came back RunIdentityError. Exported it, three dirs. | `failure_behavior` |
| 2025-06-03 | #engineering | nikolai | check moved ahead of run dir creation - compute_run_identity refuses an id on a cached run, and refuses cache off with run_id None or "". LLM.__call__ is where the default gets minted - CURATOR_RUN_ID when it is set, otherwise a fresh uuid4 - and it passes that down as the run_id argument, so the only refusal that ever surfaces out of __call__ is the cached-run one. nothing left on disk either way. | `failure_behavior`, `scope` |

## g4.r1

**The hidden requirement:**

- **rule** — The digest is computed over exactly twelve component keys, exported as `IDENTITY_COMPONENT_KEYS: tuple[str, ...]` in alphabetical order: `backend`, `backend_params`, `batch_mode`, `dataset_hash`, `generation_params`, `model_name`, `parse_func_hash`, `prompt_func_hash`, `response_format`, `return_completions_object`, `run_id`, `system_prompt`. The parse function participates via `_get_function_hash(llm.prompt_formatter.parse_func)` exactly as the prompt function does, `system_prompt` and `return_completions_object` participate, `generation_params` is always carried (`dict(... or {})`), and `response_format` is `json.dumps(rf.model_json_schema(), sort_keys=True, separators=(",", ":"))` or the literal string `"text"` when it is `None`.
- **scope** — `backend` is the *resolved* backend name read off `llm.backend`, which is `self._request_processor.backend`; `LLM.backend_params` is a copy of the dict handed to `__init__`, `{}` when it was `None`.
- **exclusions_or_crossover** — `backend_params` is filtered to exactly the four keys of `IDENTITY_BACKEND_PARAM_KEYS: frozenset[str] = frozenset({"azure_deployment", "base_url", "batch_size", "completion_window"})`. Every other backend param is not identity and must not fork the cache directory — `max_retries`, `request_timeout`, `require_all_responses`, `batch_check_interval`, `seconds_to_pause_on_rate_limit`, `max_requests_per_minute`, `delete_successful_batch_files`, and `api_key`.
- **observability** — For a stub with `backend_params={"base_url": "https://x/v1", "max_retries": 7, "api_key": "sk-secret", "request_timeout": 30}`: `tuple(sorted(compute_run_identity(S, "d0").components)) == IDENTITY_COMPONENT_KEYS` with `len == 12`; `.components["backend_params"] == {"base_url": "https://x/v1"}`; the string `"sk-secret"` occurs nowhere in the serialised components or in the written `run_identity.json`; `run_hash` is byte-equal to that of a stub differing only in `api_key`, `max_retries` and `request_timeout`; and `run_hash` differs when only the parse function, only `system_prompt`, only `return_completions_object`, or only the resolved backend differs. `LLM(model_name="gpt-4o-mini")` and `LLM(model_name="gpt-4o-mini", backend="openai")` yield the same `run_hash`.

**Reversed earlier:** An earlier build hashed the whole `backend_params` dict (mirroring the `sorted(generation_params.items())` line already in `llm.py`); it was reversed after every `api_key` rotation and every `max_retries` tweak minted a fresh cache directory, and after the cleartext `api_key` was noticed in a stamp file on a shared box.

**What a reader has to infer along the way:**

- *The component list feeding the digest is a single exported, alphabetically ordered tuple of exactly twelve entries, and nothing hashes outside it.*
  - nobody says: If the list is duplicated and unsorted people will keep adding things to one copy, so one named ordered tuple with a fixed length is the only thing a test can hold onto.
- *The parse function, the system prompt and the completions-object flag each change the answers you get back, so each one participates in the identity, the parse function hashed by the same helper as the prompt function.*
  - nobody says: Anything that changes what ends up in the returned rows has to change the cache directory, or a rerun quietly serves stale rows.
- *Generation params are always carried, empty or not, and the response format goes in as a sorted compact JSON dump of its schema, or the plain string "text" when there is none.*
  - nobody says: Two runs that are the same run must serialise to the same bytes, so absent and empty have to collapse together and dict ordering must be pinned.
- *The backend that goes into the identity is the one the processor resolved to, not the argument the caller passed, and backend params are exposed off the LLM as a copy that is an empty dict when nothing was passed.*
  - nobody says: Naming a default explicitly is the same run as leaving it out, and something you hash must not be able to change underneath you.
- *Only a small fixed set of backend params is identity: the ones that change where the request goes or how it is batched. Everything else, including credentials, must neither fork the cache directory nor be written into the stamp file.*
  - nobody says: A knob that only affects how hard the client tries produces the same answers, so it has no business in a fingerprint, and a secret has no business on disk at all.

**Names the tests reach for that the ticket withholds:**

- said: `IDENTITY_BACKEND_PARAM_KEYS`, `IDENTITY_COMPONENT_KEYS`, `The`, `batch_mode`, `generation_params`, `model_name`, `parse_func_hash`, `prompt_func_hash`, `response_format`, `return_completions_object`, `separators`, `system_prompt`

> **Spread:** one source only (slack); g4.r1.sc-keys: two remarks in #code-review within 3 days; g4.r1.sc-backend-params: two remarks in #engineering within 1 days; g4.r1.sc-backend-params: two remarks in #engineering within 4 days

> **11 of 44 graded assertions are not stated outright** — 1 absent, 10 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g4.r1.sc-keys — The component list feeding the digest is a single exported, alphabetically ordered tuple of exactly twelve entries, and nothing hashes outside it.

*Nobody says:* If the list is duplicated and unsorted people will keep adding things to one copy, so one named ordered tuple with a fixed length is the only thing a test can hold onto.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g4.r1.l-keys-count` — rule, observability

**gideon**, 2025-03-14, #code-review

> The test just counts what compute_run_identity hands back — 12 components, sorted — so it screams the second someone hashes something that never made it into the list.

*What a reader should take from it:* the team agrees the identity is built from exactly twelve components and a test pins the count

*Step it builds toward:* `g4.r1.sc-keys` — The component list feeding the digest is a single exported, alphabetically ordered tuple of exactly twelve entries, and nothing hashes outside it.

*Drafted as:* The test just asserts the tuple has 12 entries, so it screams the second someone hashes something that never made it into the list.

*Why there:* Every listed room is either at the wrong stage or on a different subject. The only thread about cache identity is #pipeline 2025-04-23, and there the fingerprint is still an open discovery — dario has just found that model isn't folded into the key and is explicitly holding off pending a blast-radius count from Nikolai. A remark reporting that a test already pins a twelve-entry identity tuple would contradict that room: it asserts an implementation that doesn't exist yet on 04-23, and it would land with nobody able to react to it. The code-review days are about PR numbers, merge states, structured output and the container user arg; none of them touch the cache key, so the remark would arrive from nowhere. What's missing from the corpus is the follow-up: the review of the PR that actually adds model to the fingerprint, where the components get enumerated and the count gets pinned. Gideon is the right person there — he's the one who asked "does the request fingerprint factor in model at all" on 04-23 and pushed on whether anyone had checked, so him reporting what the test guards is the natural close of his own thread.

*Still leaves open:* What the tuple is called and what order it is in.

*Must appear literally:* `12`, `The`, `compute_run_identity`

*A new conversation in #code-review on 2025-03-14:*

```
13:43  dario: quick one before i forget - whats keeping the identity hash and its test from drifting apart
13:44  gideon: so basically the test doesnt look at values at all, it just counts what compute_run_identity hands back
13:45  dario: only a count? honestly that feels thin
13:46  gideon: 12 components, and sorted, so the order is pinned too. The whole thing is like four lines tbh
13:48  dario: mhm. so it screams the second someone hashes something that never made it into the list
13:49  gideon: exactly, right there in ci, before anyone is wondering why two identcal runs got different keys
13:51  emil: yup. who's writing it though, does it ride along with 581 or does it want its own pr
```

#### `g4.r1.l-keys-onelist` — rule

**konrad**, 2025-03-17, #code-review

> look, the component names are written out in two places and they've already drifted apart - we should export one tuple and read it from both

*What a reader should take from it:* the team agrees there is a single exported list of component keys

*Step it builds toward:* `g4.r1.sc-keys` — The component list feeding the digest is a single exported, alphabetically ordered tuple of exactly twelve entries, and nothing hashes outside it.

*Drafted as:* we're writing the component names out in two places and they've already drifted apart; export one tuple and read it from both.

*Why there:* No candidate room is discussing cache-key identity or fingerprint components. The nearest shape (code-review 2025-05-29) is a duplicated *model* list in finetuning, so planting it there would require rewriting the fact into model names and losing the component-keys take. general|2025-04-07 names caching-and-resume only as a clean-over-the-weekend standup line, with no code-level thread to attach to and nobody who would respond. The conversation this belongs to — Konrad reading the fingerprint builder after a bad cache reuse, with Dario as the owner of caching-and-resume — is missing from the corpus.

*Still leaves open:* The name of the tuple, its length, and its ordering.

*A new conversation in #code-review on 2025-03-17:*

```
13:41  nikolai: the component names are written out in two places right
13:42  konrad: mhm. and they dont match anymore, thats the problem
13:44  nikolai: which copy is the stale one
13:45  konrad: off the top of my head i couldnt tell you, i think both moved a bit
13:45  konrad: anyway look, it should be one tuple we export
13:47  emil: so neither place spells them out, they both just read the tuple?
13:48  konrad: right, both read from it. then adding a name is one edit and they cant drift again
```

#### `g4.r1.say23` — rule

**nils**, 2025-04-07, #general

> let me think - dataset_hash is one of the twelve, and it goes into the components dict exactly as the caller handed it to us, we dont re-derive it on our side

*What a reader should take from it:* the team agrees dataset_hash is a component key carried through verbatim as passed in

*Step it builds toward:* `g4.r1.sc-keys` — The component list feeding the digest is a single exported, alphabetically ordered tuple of exactly twelve entries, and nothing hashes outside it.

*Drafted as:* and dataset_hash is one of the twelve - it goes into the components dict exactly as the caller handed it to us, we dont re-derive it on our side

*Why there:* Neither listed room is anywhere near this. #pipeline on 03-19 is weekly-notes triage: gemini unicode, the Mistral api_key blocker on PR 584, and who runs the throttle-path check after the rate-limiter postmortem — nothing about run cache identity, and a line about a twelve-part components dict would land in the middle of "who's checking the throttle path" with no one to answer it. #code-review on 03-25 is pure release triage (what's targeting the release, what's deferred, where WS-047 lives); nobody there is reading code internals at all, and Nils is the one asking for review eyes, not narrating fingerprint construction. The remark presumes a live argument about what the cache key is built from and how each piece is treated, which the corpus needs a room for: someone finds reruns missing cache and asks what actually goes into the fingerprint, Nils walks the components dict, and the sibling remark covers the rest of the tuple and canonicalisation of the other fields.

*Still leaves open:* does not say what else is in the tuple, where dataset_hash sits in it, or how the other components are canonicalised

*Must appear literally:* `dataset_hash`

*A new conversation in #general on 2025-04-07:*

```
13:07  konrad: quick one while i have the file open - is dataset_hash one of the twelve, or is it something we keep off to the side
13:09  nils: one of the twelve.
13:11  konrad: ok so it goes into the components dict with the others. and we hash the dataset ourselves there, presumably?
13:13  gideon: ya thats the bit i wasnt sure on either tbh
13:15  nils: with the others, yes. let me think - but no on the second part. it goes in exactly as the caller handed it to us, we dont re-derive it on our side
13:16  konrad: right. stale in, stale out then
13:17  nils: basically. not our job to check it
13:19  gideon: ok so my branch recomputing it is just wrong, thats coming back out
```

> **Problems:** longer than one remark

#### `g4.r1.l-keys-order` — rule

**dario**, 2025-04-16, #code-review

> nit: IDENTITY_COMPONENT_KEYS is the one exported tuple and we're keeping it alphabetical — backend, backend_params, batch_mode — and batch_mode is sitting above backend here.

*What a reader should take from it:* the team agrees the component keys live in one exported tuple, sorted alphabetically

*Step it builds toward:* `g4.r1.sc-keys` — The component list feeding the digest is a single exported, alphabetically ordered tuple of exactly twelve entries, and nothing hashes outside it.

*Drafted as:* nit: `IDENTITY_COMPONENT_KEYS` isn't in alphabetical order, `batch_mode` is sitting above `backend` in the tuple.

*Why there:* Every listed room is either reviewing a different PR (632/626 on 04-14, schema_check on 03-14) or discussing caching and batch mode at the scope/ownership level rather than reading a diff (pipeline 04-09, viewer 04-25). A line-level nit about an exported identity tuple needs that PR to be open in the room; nowhere listed has it, and dropping it into 04-14 would change the subject just as dario is closing the thread out. The conversation that should exist is the code review of the caching-and-resume identity fingerprint PR, following on from the 04-09 pipeline thread where the batch submission path was flagged as uncovered — dario is the established caching-and-resume reviewer, emil owns the batch side and supplies which components are in the tuple.

*Still leaves open:* How many entries the tuple is meant to have, and which components are in it.

*Must appear literally:* `IDENTITY_COMPONENT_KEYS`, `backend`, `backend_params`, `batch_mode`, `return_completions_object`, `run_id`, `system_prompt`

*A new conversation in #code-review on 2025-04-16:*

```
15:12  konrad: Quick one on the identity stuff - is the list in _identity.py the one people import, or is there a second one floating around
15:14  gideon: thats the one. IDENTITY_COMPONENT_KEYS is the only tuple we export
15:16  konrad: right. and the order in it isnt the signature order, so what is it supposed to be
15:18  gideon: alphabetical. so basically return_completions_object, run_id, system_prompt just fall at the bottom and nobody has to think about it
15:19  konrad: mhm. so backend_params sits after backend
15:21  dario: yes, and thats the nit actually - batch_mode is above backend in the diff. should read backend, backend_params, batch_mode
15:23  konrad: ah. off the top of my head batch_mode is the newest key there, presumably it just got appended and then moved wrong
15:25  dario: probably, honestly. its a one line move, whoever is in that file next
```

> **Problems:** claims verbatim 'return_completions_object' but does not contain it; claims verbatim 'run_id' but does not contain it; claims verbatim 'system_prompt' but does not contain it

### g4.r1.sc-request-shape — The parse function, the system prompt and the completions-object flag each change the answers you get back, so each one participates in the identity, the parse function hashed by the same helper as the prompt function.

*Nobody says:* Anything that changes what ends up in the returned rows has to change the cache directory, or a rerun quietly serves stale rows.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g4.r1.say22` — rule

**nikolai**, 2025-03-21, #cookbooks

> one more on parse_func when a run hasnt got one we hand None straight to _get_function_hash no conditional round it and the helper hashes that fine

*What a reader should take from it:* the team agrees a missing parse_func is passed to the hash helper as None rather than guarded with a conditional

*Step it builds toward:* `g4.r1.sc-request-shape` — The parse function, the system prompt and the completions-object flag each change the answers you get back, so each one participates in the identity, the parse function hashed by the same helper as the prompt function.

*Drafted as:* one more on parse_func - when a run hasnt got one we hand None straight to _get_function_hash, no conditional around it, the helper hashes that fine

*Why there:* No listed room is discussing run cache identity, fingerprinting, or function hashing at all. The three code-review days are review-queue status threads (who's picking up 653/663/690/691) rather than line-level reads; the only technically substantive one, 2025-05-08, is on gemini batch serialization and a bad GCS upload path — adjacent-sounding but a different subsystem, and Emil owns it, so a parse_func/_get_function_hash note there would land as a subject change with no reply. #random 2025-04-25 is the duplicate model-name lists, #engineering 2025-03-24 is cost estimation and the examples table, #cookbooks 2025-04-16 is docker image pinning and resume inheriting the old batch id. What this remark needs is the thread where the composition of the run fingerprint gets pinned down — the same thread that would carry the sibling point about the prompt function's helper output and parse_func_hash being an exported component key.

*Still leaves open:* does not say which helper output the prompt function gets, nor that parse_func_hash is one of the exported component keys

*Must appear literally:* `parse_func`, `None`, `_get_function_hash`

*A new conversation in #cookbooks on 2025-03-21:*

```
13:41  dario: one more on parse_func before i lose it — plenty of the runs just dont carry one. do we skip those or push it through anyway
13:44  nikolai: push it through
13:45  dario: meaning None goes straight into _get_function_hash, no branch either side of it?
13:47  nikolai: right no conditional round it at all
13:49  dario: i assumed that would blow up honestly, i had it in my head the helper wanted a real callable
13:52  nikolai: nah it hashes None fine thats why i never wrapped it
13:55  emil: yup. i went looking for that guard last month and couldnt work out where it was meant to sit
```

#### `g4.r1.l-completions-object` — rule

**emil**, 2025-04-02, #code-review

> same family of annoyance: turned return_completions_object on and the cached rows still had no raw objects in them, deleted the dir by hand again. that should just miss.

*What a reader should take from it:* the team agrees the completions-object flag is part of the run identity

*Step it builds toward:* `g4.r1.sc-request-shape` — The parse function, the system prompt and the completions-object flag each change the answers you get back, so each one participates in the identity, the parse function hashed by the same helper as the prompt function.

*Drafted as:* turned return_completions_object on and the cached rows still had no raw objects in them, deleted the dir by hand again. it should just miss.

*Why there:* Emil is already mid-rant there about run identity being under-keyed — the pending job ID keyed off the dataset only with no backend distinction, and him "wiping the dir by hand" after the 404 loop. A second instance in the same family (a flag that changes the output shape but doesn't change the cache identity, so stale rows come back and he deletes the dir manually again) lands as more of the same annoyance from the same person in the same breath, and it settles that the flag belongs in the identity without touching prompt text or the parse function.

*Still leaves open:* Whether the prompt text or the parse function are handled the same way.

*Must appear literally:* `return_completions_object`

*Goes into the real conversation in #code-review on 2025-04-02, after 11:58 emil:*

```
09:00  dermot: pr 614 is up, cancellation fix in bulk-llm-inference. its blocking batch testing so I'd appreciate eyes on it today
09:20  konrad: Is PR 615 connected to this or a separate bug entirely?
09:20  dermot: I might have oversimplified it - I'm not entirely sure pr 615 isn't touching the same root cause. I'd need to look more carefully before I could say t
10:02  konrad: I pulled up WS-050 just now
10:02  konrad: Nothing in there about the examples side of batch, so I'm not sure if that's coming in a separate doc somewhere or just not written yet?
10:03  konrad: Haven't started on batch examples yet. Was going to wait until the API shape settles a bit more before writing anything up.
11:25  dermot: has anyone had a chance to look at PR 614 yet?
11:57  emil: Weekly Notes, Week of Mar 31 are up: meetings/weekly-notes-week-of-mar-31.md
11:57  emil: Worth flagging one thing in there, the pending job ID is keyed off the dataset only, no backend distinction, so the plain openai path and an azure dep
11:57  emil: Moved a cookbook to azure last week and the restart polled a job the openai endpoint doesn't own
11:58  emil: related annoyance: the pending job id gets parked in the run dir keyed off the dataset only, no backend distinction
11:58  emil: moved a cookbook to azure last week, the restart polled a job the openai endpoint doesn't own, sat in a 404 retry loop for twenty minutes before givin   <-- THE REMARK GOES HERE
12:11  emil: Does the job ID scoping fix belong in PR 615 or should it go in its own PR?
15:11  dermot: sorry, been in a call - so the 404 loop was the job id not scoped per backend, that's separate from what PR 614 fixes.
15:44  konrad: So PR 615 wasn't touching the backend scoping at all then?
15:44  konrad: PR 614 is separate from the scoping issue, that much is settled now.
15:44  konrad: Does PR 615 touch the backend scoping at all, or is that a third fix going somewhere new?
16:07  konrad: WS-050 doesn't say anything about the examples side
16:07  konrad: Is that in scope for this milestone or coming after?
16:10  emil: Haven't had a chance to check PR 615's scope since this morning, I'll look at it and report back.
16:10  emil: Is PR 614 ready to merge or does it still need another pass?
16:34  emil: Who's reviewing PR 614, does it have someone on it yet?
17:02  emil: Does PR 614 need to land today or is tomorrow fine?
17:38  dermot: pr 614 is ready from my side, I haven't heard that anyone's reviewed it yet. I'd like to get it in today if we can, it's blocking batch testing
17:39  konrad: Is Dario looking at it or does it still need someone to pick it up?
17:39  konrad: Or should I just take a look at it?
17:40  emil: I'll take it.
17:40  konrad: Is that Dario?
17:40  konrad: - *Root cause confirmed:* job ID not scoped per backend
17:40  dermot: Konrad, was that you?
18:08  konrad: That wasn't me, I thought someone else had grabbed it
18:09  konrad: @Dario are you on PR 614?
18:09  konrad: I'm around for another hour or so if someone needs a second set of eyes on PR 614.
18:26  dermot: konrad, go ahead and take it if you're around.
```

#### `g4.r1.l-parse-func` — rule

**nikolai**, 2025-04-18, #incidents

> edited parse_func to drop the refusals and got yesterdays parsed rows back parse_func_hash is _get_function_hash(llm.prompt_formatter.parse_func) same helper as prompt_func_hash different function so the two never match

*What a reader should take from it:* the team agrees the parse function is hashed into the identity exactly as the prompt function is

*Step it builds toward:* `g4.r1.sc-request-shape` — The parse function, the system prompt and the completions-object flag each change the answers you get back, so each one participates in the identity, the parse function hashed by the same helper as the prompt function.

*Drafted as:* edited parse_func to drop the refusals and cache handed me back yesterday's parsed rows. `parse_func_hash` belongs right next to `prompt_func_hash`, same helper.

*Why there:* That whole day is nikolai pressing dario on what the run fingerprint actually includes — dario lists prompt hash, model, generation params, provider name, dario reports his own backend-switch cache reuse, and dario just said he'd need to see what code-execution feeds in before promising anything. Nikolai handing over his own concrete repro from his subsystem, and naming the field he wants alongside the prompt one, is exactly the next thing he'd type there; it answers dario's 12:51 without settling the prompt-text/completions question.

*Still leaves open:* Whether the prompt text and the completions flag matter too.

*Must appear literally:* `_get_function_hash(llm.prompt_formatter.parse_func)`, `parse_func`, `parse_func_hash`, `prompt_func_hash`

*Goes into the real conversation in #incidents on 2025-04-18, after 12:51 dario:*

```
09:00  nikolai: code-execution is in decent shape, sandbox isolation is holding up and I've got instrumentation passing through cleanly
09:00  nikolai: Working through the last few edge cases on the telemetry side this morning
09:00  nikolai: Did anyone manage to repro the pass-rate change from Monday, or is that still sitting open?
09:15  nikolai: Actually, answering my own question, I heard Konrad tried to repro it and his second run finished in nine seconds.
10:01  nikolai: Nine seconds sounds like it just hit the cache and skipped the actual run. Is there a way to tell whether it actually executed anything or resumed fro
10:55  nikolai: @Dario Kestrel you own caching-and-resume right, what does the fingerprint for a run actually include?
10:57  dario: yeah, that's a good question
10:58  dario: The fingerprint is in my code, so broadly: prompt hash, model, generation params, provider name
10:58  dario: Do you know if Konrad had the same provider set both times, or did anything change between the two runs?
11:10  nikolai: dunno, I'd have to check with Konrad
11:24  dario: Actually I hit something related - killed a run mid-batch, switched the backend from openai to anthropic in the same script, reran, and it went straig
11:24  dario: only spotted it because the id in the log still had the openai shape on it
12:03  nikolai: So the provider name is in the fingerprint but it's not actually being used to key the cache lookup?
12:03  nikolai: Does the fingerprint pull in anything from the code executor, or is it purely the request params?
12:51  nikolai: @Dario Kestrel still curious on the fingerprint question when you get a chance
12:51  dario: The fingerprint code is mine, but I'd need to look at what code-execution is actually feeding into it before I can promise anything about how that sid   <-- THE REMARK GOES HERE
13:01  nikolai: What does code-execution actually hand off to you, do you know what the interface looks like?
```

#### `g4.r1.l-system-prompt` — rule

**dermot**, 2025-04-23, #pipeline

> that matches what I saw, rewrote the system_prompt late night and the run came back in two seconds with the old wording. it goes in as itself, None when there isnt one

*What a reader should take from it:* the team agrees the system prompt is part of the run identity

*Step it builds toward:* `g4.r1.sc-request-shape` — The parse function, the system prompt and the completions-object flag each change the answers you get back, so each one participates in the identity, the parse function hashed by the same helper as the prompt function.

*Drafted as:* rewrote the system_prompt in the cookbook and the run came back in two seconds with the old wording. i want a fresh directory for that.

*Why there:* That room is mid-investigation into exactly what the request fingerprint hashes on — dario has just reported that model "comes in as its own thing" and isn't folded into the key, while the key covers prompt content plus generation params. Dermot has already staked out the identity position at 09:35 ("same prompt on a different model is not the same request"), so him producing a second, empirically-observed argument of the same kind — system_prompt is another arg that isn't in the key, and he wants it to be — lands as corroboration of dario's finding rather than a new subject. It also sets up his later 15:35 line about the fingerprint and the job record sharing a gap. Nothing here has made the point yet, and it leaves the parse function / completions flag untouched.

*Still leaves open:* Whether the parse function or the completions flag behave the same way.

*Must appear literally:* `None`, `system_prompt`

*Goes into the real conversation in #pipeline on 2025-04-23, after 11:41 dario:*

```
09:00  dermot: bulk-llm-inference is mostly stable, few loose ends on the proivder side
09:00  dermot: multimodal-prompts is holding, nothing urgent there
09:27  gideon: Dario, does the request fingerprint factor in model at all, or is it just prompt + params?
09:35  dermot: I mean, it should be. same prompt on a different model is not the same request
11:13  gideon: yeah but do we know for sure it actually is, or is that the thing nobody's checked?
11:40  dario: Been in the caching code most of this morning looking at exactly this - from what I can see so far, model is not explicitly part of the fingerprint
11:40  dario: It hashes on promt content and the generation params that get passed in, but model comes in as its own thing and I'm not seeing it folded into the key
11:41  dario: Still working through it to make sure I'm reading that right   <-- THE REMARK GOES HERE
12:43  emil: huh
12:43  emil: that would explain a lot
13:15  gideon: If model gets added to the key, do we have any sense of how many existing cached entries would get blown away?
13:16  dario: Honestly I don't have that count, and I'd lean toward not moving on this until we do.
14:33  gideon: Is there a way to pull that count from the cache store, or does it need instrumentation first?
15:09  emil: Related: the persisted job record doesn't store the model either, just the id, the request file path, and a timestamp
15:09  emil: and this isn't the first time either, it's bitten me twice this week
15:09  emil: that's the whole record, nothing else on it
15:09  emil: so if someone hands me a run dir I can't tell what model it went out with, and that means I can't tell if picking it back up is safe
15:35  dermot: the fingerprint and the job record have the same gap
15:39  dario: I'd want @Nikolai Berresford in this before we touch anything - I dunno off the top of my head if the count is even pullable without adding instrument
16:59  gideon: Good call holding off
16:59  gideon: That's the right move
17:13  emil: We could fix the job record side independently, just write the model into the pending record without touching the cache key at all.
```

> **Problems:** longer than one remark

### g4.r1.sc-canonical — Generation params are always carried, empty or not, and the response format goes in as a sorted compact JSON dump of its schema, or the plain string "text" when there is none.

*Nobody says:* Two runs that are the same run must serialise to the same bytes, so absent and empty have to collapse together and dict ordering must be pinned.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g4.r1.l-schema-dump` — rule

**konrad**, 2025-03-14, #engineering

> look, it goes in as json.dumps(..., sort_keys=True, separators=(",", ":")) — a string, not the dict — and when there's no format at all we just put "text" in.

*What a reader should take from it:* the team agrees the format goes in as a sorted compact JSON schema dump, or the literal string text

*Step it builds toward:* `g4.r1.sc-canonical` — Generation params are always carried, empty or not, and the response format goes in as a sorted compact JSON dump of its schema, or the plain string "text" when there is none.

*Drafted as:* dump it with sort_keys and `separators=(",", ":")` so it's stable, and put the string "text" in when there's no format at all.

*Why there:* None of the listed rooms is chewing on serialization for stability. The nearest candidates all miss: #engineering 2025-05-23 is about whether the OpenAI-compatible *response shape* breaks existing callers (a compatibility question, resolved by running the existing tests), not about how a format field gets written down; #code-review 2025-03-19 does touch JSON encoding, but that fix is gemini emitting surrogate pairs instead of the emoji — an ensure_ascii problem, nothing to do with key ordering or a default value; #viewer 2025-06-03 has the shape of a None-default discussion but the field is cost, and Emil has already claimed the null-handling check. Dropping sort_keys/separators and a literal "text" fallback into any of them changes the subject with no one above to answer and no one below to react. What's missing from the corpus is the conversation where the run cache key gets pinned down — the request fingerprint has to include the response format, and two runs with the same schema were landing on different keys because the dict came out in a different order. That's the room where "dump it compact and sorted, and 'text' when there's no format" is a decision rather than trivia, and it's also where the sibling remark naming the field and explaining why ordering matters lives.

*Still leaves open:* Which field is being dumped and why the ordering bit anyone.

*Must appear literally:* `"text"`, `json.dumps`, `separators`, `separators=(",", ":")`, `sort_keys=True`

*A new conversation in #engineering on 2025-03-14:*

```
13:06  dario: ran the same call twice yesterday and it didnt reuse the first one at all
13:07  dario: only thing different between them was the response format arg. is that going in as the dict or do we serialize it first
13:09  konrad: not the dict. look, it goes in as a string
13:09  konrad: json.dumps with sort_keys=True, otherwise you get exactly what you saw
13:11  dario: mhm that tracks, key order. separators too or is the default spacing ok
13:12  konrad: separators=(",", ":") as well, no spaces anywhere. thats the whole call presumably
13:14  dermot: and the ones that pass no format at all, that slot just ends up empty then
13:16  konrad: no we put "text" in for those
13:17  dermot: yeah ok, thats the bit i would have gotten wrong
```

> **Problems:** longer than one remark

#### `g4.r1.l-schema-order` — rule

**nils**, 2025-03-21, #code-review

> related: `response_format` reaches us as `rf.model_json_schema()`, a plain dict — same pydantic model on two boxes, keys came back in a different order, two cache dirs.

*What a reader should take from it:* the team agrees the response format schema must serialise deterministically into the identity

*Step it builds toward:* `g4.r1.sc-canonical` — Generation params are always carried, empty or not, and the response format goes in as a sorted compact JSON dump of its schema, or the plain string "text" when there is none.

*Drafted as:* same pydantic model, two boxes, two cache dirs. the `response_format` schema dict is going in with whatever key order it happened to come out with.

*Why there:* Emil has just opened the cache-identity/resumability thread in that room — the metadata db not following CURATOR_CACHE_DIR, "resumable" meaning two different things depending on which half of the run you ask about (12:41). Nils's remark lands on the same wound from the other side: even with the cache dir pointed somewhere shared, the identity itself isn't stable across machines because the response_format schema dict goes in with arbitrary key order. Nils is the natural speaker — PR 584 is his and the structured-output path is what he's been in all week — and nobody in either day has made this point, so it complicates Emil's question rather than repeating it. The 03-25 log is pure PR triage with no cache talk at all, so it would arrive from nowhere there. It states the settled part (must serialise deterministically) and leaves how, and the no-format case, untouched.

*Still leaves open:* How the schema should be serialised, and what happens when there is no format at all.

*Must appear literally:* `response_format`, `rf.model_json_schema()`

*Goes into the real conversation in #code-review on 2025-03-21, after 12:41 emil:*

```
09:00  nils: PR 584 (Mistral batch) is ready for review, touches batch-mode and provider integrations
09:00  nils: Not blocking a release but i'd like to settle before end of day whether we're merging this week or pushing to next
09:00  nils: @Emil is PR 585 meant to fold retry handling in with batch submission, or is that out of scope for it?
11:00  konrad: Sorry, just saw this
11:00  konrad: I've been sitting on PR 584 as well so I'm glad Nils raised it - would be good to get a decision today one way or the other
11:39  emil: @Nils that's the thing I'm not entirely sure about. Been going back and forth on whether retry handling belongs in PR 585 or stays separate, and I'd w
11:46  nils: fair enough
11:46  nils: WS-047 doesn't have a spec page on the wiki yet, couldn't find it anywhere when I looked
11:50  dario: while we're on PRs, @Emil, does PR 579 cover the same ground as PR 565 and PR 566, or are all three meant to land separately?
12:18  emil: Sent a note to Dario and Nils on the batch status persistence doc
12:18  emil: One house rule I want on record from it: for anything that only reports on the cache, connect to the metadata db with mode=ro
12:18  emil: @Nils, free this afternoon to settle the PR 584 call?
12:26  emil: The online processor appends to the responses file the moment a request is accepted, not when it comes back. That ordering was deliberate
12:26  emil: Does retry handling in PR 585 need to account for that, or is it working above that layer?
12:41  emil: A user pointed CURATOR_CACHE_DIR at /mnt/shared expecting everything a rerun needs to live under that path. Request and response files follow it, the 
12:41  emil: Is that gap tracked anywhere as an issue?   <-- THE REMARK GOES HERE
12:48  nils: @Emil yes, free this afternoon
12:48  nils: PR 584 is ready on my end, just sitting there waiting on the merge or defer call
12:48  nils: does WS-047 need a full wiki page, or is a tracked issue sufficient for defining the CI scope?
```

#### `g4.r1.l-genparams-empty` — rule

**gideon**, 2025-04-17, #random

> honestly though it's not only helpers - a run with generation_params=None and one with an empty dict landed in two seperate directories last night, and it was the same run

*What a reader should take from it:* the team agrees an absent generation params dict and an empty one are the same run

*Step it builds toward:* `g4.r1.sc-canonical` — Generation params are always carried, empty or not, and the response format goes in as a sorted compact JSON dump of its schema, or the plain string "text" when there is none.

*Drafted as:* Run with generation_params=None and a run with an empty dict landed in two different directories last night, and it was the same run.

*Why there:* The 04-17 #random thread is already gideon's own post-mortem on cache directories as a billing risk — his 13:46 line generalises it to "any helper that touches the cache directory is a billing risk if it creates on open". This complicates that framing: the split isn't only helpers creating dirs on open, the key itself splits on generation_params=None vs {}, so one run got two directories. Same person, same day, same running theme of a normal-looking run quietly paying twice; it leaves the fix and the response format serialisation untouched.

*Still leaves open:* What to do about it, and how the response format is serialised.

*Must appear literally:* `generation_params`

*Goes into the real conversation in #random on 2025-04-17, after 13:46 gideon:*

```
09:00  gideon: ok so I did something dumb last night
09:00  gideon: typo'd the path in my cache-poking script, it did a mkdir -p on the way in, and this morning's cookbook run found a fresh empty cache dir at the typo'
09:00  gideon: the script only ever wanted to count rows.
09:00  gideon: posting this so nobody else does it.
09:00  gideon: the bill is real
09:40  dermot: oh
09:40  dermot: no. mkdir -p is such a silent little monster.
10:34  gideon: Any helper that only wants to count rows should probably just fail if the directory doesn't exist.
10:50  dermot: +1
11:46  emil: I've done exactly this
11:46  emil: Different script, same outcome
12:04  emil: ugh
12:05  emil: silent failures are the worst kind
12:40  dermot: I had one go completely dark on a provider run, no status, no error, nothing
12:40  dermot: spent half a day not sure whether to resend and risk double billing or just wait and lose the window entirely
12:43  gideon: the "do I resend or do I wait" paralysis is its own special kind of terrible
12:43  gideon: did anyone actually resend in the end, or just wait it out?
13:46  gideon: so the lesson here is basically: any helper that touches the cache directory is a billing risk if it creates on open, right?   <-- THE REMARK GOES HERE
14:25  dermot: I did resend eventually
14:25  dermot: I think that's just the call with a dead batch, not much else you can do once it stops responding
14:50  gideon: did it double-bill or were you clear?
15:20  emil: The mkdir -p thing catches you the same way, the run looks totally normal from the outside until you see the bill.
15:21  dermot: provider charged for both, or our system ran it twice?
```

#### `g4.r1.l-genparams-fix` — rule

**dario**, 2025-04-18, #engineering

> and when we do fold them into the key, always carry it as `dict(... or {})` before it goes in - then the missing case and the empty case hash to one thing

*What a reader should take from it:* the team agrees generation params are always carried, normalised to an empty dict when unset

*Step it builds toward:* `g4.r1.sc-canonical` — Generation params are always carried, empty or not, and the response format goes in as a sorted compact JSON dump of its schema, or the plain string "text" when there is none.

*Drafted as:* so always carry it as `dict(... or {})` before it goes in, then the missing case and the empty case hash to one thing.

*Why there:* The room is mid-discussion on exactly this: emil hit stale truncated output after raising max_tokens and asked whether changing generation params should invalidate on its own, and dario has just confirmed max_tokens isn't in the cache key today. Dario is the caching-and-resume person in that thread, so the settled normalisation rule for folding params into the key is his to state, and it lands as the next beat after his 14:53 line rather than changing the subject. It stops short of naming the field or how the schema gets dumped, which the sibling supplies.

*Still leaves open:* Which field this is about, and how the schema itself is dumped.

*Goes into the real conversation in #engineering on 2025-04-18, after 14:53 dario:*

```
09:00  gideon: - PR 632 is ready, just waiting on a review pass
- still poking at the batch update frequency logic, i think thre's one more edge case to flush out
09:00  gideon: @Emil Brandvold is there an env var already for skipping the cache check, or does forcing a resubmit currently require touching the files?
10:11  gideon: @Emil Brandvold is this for local debugging or are you hitting it in CI too?
10:34  gideon: @Emil Brandvold does the caching layer have any existing env var for forcing a cache miss, or is that not wired up at all right now?
11:29  gideon: @Dario Kestrel do you know if there's anything in caching-and-resume for skipping the cache check without touching files?
12:54  dario: There's already an env var in caching-and-resume for forcing a cache miss
12:54  dario: I'll check what CI's actually setting this afternoon before we point anyone at it or name a new one
13:03  gideon: nice, thanks Dario
13:13  dario: Does anyone have a preference on reusing the existing var versus adding a dedicated one for forcing resubmit, or should I just report what CI sets and
13:26  gideon: I'd lean towards reusing the existing one, but @Emil Brandvold should probably weigh in since it's his debug workflow.
13:39  dario: @Emil Brandvold when you hit this, is it local or also in CI, and do you know if the var name matters to you or just that there is one?
14:09  gideon: so waiting on Dario to check what CI sets, then we can figure out reuse vs. new var
14:51  emil: Same shape of thing with max_tokens for me - response came back truncated mid-sentence, I raised max_tokens, reran, and got handed the same truncated 
14:51  emil: This was local - is the expectation that people bust the whole cache when generation params change, or should changing max_tokens be invalidating on i
14:51  emil: To be clear on the sequence: truncated mid-sentence with max_tokens, raised max_tokens, reran, got handed the same truncated text again.
14:52  emil: Deleting the cache directory is what finally cleared it, and that took out four thousand rows that were perfectly fine along with it.
14:53  dario: Yeah
14:53  dario: that's current behavior in caching-and-resume - max_tokens isn't part of the cache key   <-- THE REMARK GOES HERE
```

> **Problems:** longer than one remark

### g4.r1.sc-backend — The backend that goes into the identity is the one the processor resolved to, not the argument the caller passed, and backend params are exposed off the LLM as a copy that is an empty dict when nothing was passed.

*Nobody says:* Naming a default explicitly is the same run as leaving it out, and something you hash must not be able to change underneath you.

*5 remarks — 0 reporting the problem, 5 settling the design.*

#### `g4.r1.l-backend-default` — scope, observability

**konrad**, 2025-03-17, #engineering

> Look, LLM(model_name="gpt-4o-mini") and the same call with backend="openai" hashed to two different run_hash values, same processor either way. naming the default cant change identity.

*What a reader should take from it:* the team agrees naming the default backend explicitly must not change the run identity

*Step it builds toward:* `g4.r1.sc-backend` — The backend that goes into the identity is the one the processor resolved to, not the argument the caller passed, and backend params are exposed off the LLM as a copy that is an empty dict when nothing was passed.

*Drafted as:* LLM(model_name="gpt-4o-mini") and the exact same call with backend="openai" gave me two cache dirs today, and it resolves to the same processor either way.

*Why there:* None of the eight rooms is chewing on caching, fingerprints, or run identity, and none touches how a backend is named or resolved. The closest, #engineering 2025-05-21, is a settled-shape argument about whether the agent response is a plain dict, and #code-review 2025-03-17 only names PR 581/583 as "config PRs" in a triage/scheduling sense — nothing in either thread would react to two cache dirs from one call. Dropping it into any of them changes the subject and draws exactly the attention a plant draws. What's missing is a day where somebody re-runs an example, sees the run re-execute instead of hitting cache, and the team decides the cache key is wrong. Konrad is the right person to open it (he lives in examples-cookbooks and does the "here's what I hit this morning" burst), Dermot owns bulk-llm-inference where the cache dirs actually land, and Emil would push on where the backend name should be read from and how backend params get exposed — the sibling arm.

*Still leaves open:* Where the backend name should be read from instead, and how backend params are exposed.

*Must appear literally:* `LLM(model_name="gpt-4o-mini")`, `backend="openai"`, `model_name`, `run_hash`

*A new conversation in #engineering on 2025-03-17:*

```
14:02  dario: same job ran twice today and i got two cache dirs out of it
14:04  dario: LLM(model_name="gpt-4o-mini") in one, and the same call with backend="openai" typed out in the other. two different run_hash
14:06  konrad: two? the processor is the same in both presumably
14:09  dario: mhm, same processor either way. openai is just what it picks when you dont say
14:11  konrad: right. so nothing about the run differs, one call only spelled out what the other left off
14:13  konrad: look, naming the default cant change identity. writing model_name and the backend out is the same run as writing one of them
14:15  dermot: yeah ok. half the examples spell the backend out, so thats been quietly forking runs for a while
```

#### `g4.r1.say24` — scope

**dario**, 2025-03-19, #releases

> on dermot's point - the components dict just takes whatever `llm.backend` hands back as the `backend` value, the digest doesnt go poking at the processor itself

*What a reader should take from it:* the team agrees the identity components read the `backend` value off the LLM object's own attribute rather than resolving it in the digest code

*Step it builds toward:* `g4.r1.sc-backend` — The backend that goes into the identity is the one the processor resolved to, not the argument the caller passed, and backend params are exposed off the LLM as a copy that is an empty dict when nothing was passed.

*Drafted as:* on dermot's point - the components dict just takes `llm.backend`, whatever the object says it is. the digest doesnt go poking at the processor itself.

*Why there:* None of the eight rooms is chewing on cache-key identity at all. The two that touch caching (#pipeline 2025-04-29) are about scope of Nikolai's stdout removal and whether provider changes touch the resume path — nobody there has raised a components dict or a digest, and dermot isn't in the room, so "on dermot's point" would be answering a point nobody made. The rooms where dermot is present are about the response object and `.choices` (#cookbooks 05-05), PR landing calls (#engineering 04-17, 04-10) and the gpt-4o capability table (#engineering 03-17) — that last one is the closest in flavour, since it's about what the model object reports about itself, but it's a litellm `get_model_info()` matcher question from March, weeks before any fingerprint work, and a remark about the digest's components dict would land there as a subject change with no reply. What's missing is the conversation where dario and dermot actually settle what goes into a run's cache identity: dermot explains where `llm.backend` gets resolved and what it returns, dario confirms the components dict just consumes it. That thread belongs in #pipeline right after the 04-29 caching-and-resume validation dario left open, with gideon and emil around since they were both in that thread.

*Still leaves open:* what `llm.backend` actually returns, and where that value gets worked out - dermot's remark has that.

*Must appear literally:* `llm.backend`, `backend`

*A new conversation in #releases on 2025-03-19:*

```
14:02  dermot: back to the cache key thing from this morning - if i had to guess, the digest is reaching into the client to work out which backend actually ran it?
14:04  konrad: no. it just asks `llm.backend` and takes whatever comes back
14:06  dermot: mhm, that part i follow. but where does it land, the components dict has its own naming and i couldnt find where it gets set
14:09  dario: it goes in as the `backend` value, straight through, no translation. and the digest doesnt go poking at the processor itself, thats the bit i think we were talking past each other on
14:10  konrad: right. so nothing walks the client internals at all
14:11  dario: nope. one value handed over, thats it. best we can do without the digest knowing about clients
14:13  dermot: yeah ok. i had half a lookup written into the digest for exactly that
```

#### `g4.r1.l-params-none` — scope

**nils**, 2025-03-20, #code-review

> @Emil while you're in there - passed {"batch_size": 64, "max_retries": 7} and llm.backend_params gives both back. pass nothing and it's None, three call sites check for that - should be {}.

*What a reader should take from it:* the team agrees the backend params property returns an empty dict when none were passed

*Step it builds toward:* `g4.r1.sc-backend` — The backend that goes into the identity is the one the processor resolved to, not the argument the caller passed, and backend params are exposed off the LLM as a copy that is an empty dict when nothing was passed.

*Drafted as:* backend_params is None unless you pass it and now three call sites have to check for that. just give me {} back from the property.

*Why there:* On 3/20 Emil has just said at 17:10 that he'll do a quick pass on PR 584 because it touches batch-mode, which he owns — that's the one moment in either day where the room is actually looking at the batch backend code rather than at release sequencing. Nils flagging a concrete annoyance he hit while building the Mistral processor against that backend lands directly on Emil's pass, and it's his own PR so he's the one who'd have counted the call sites. The 3/25 log is pure defer/target triage with no code-level talk anywhere in it, so the same line there would change the subject.

*Still leaves open:* Whether the dict is shared or copied, and which backend name is used.

*Must appear literally:* `None`, `batch_size`, `llm.backend_params`, `max_retries`, `{}`

*Goes into the real conversation in #code-review on 2025-03-20, after 17:10 emil:*

```
09:00  nils: PR 584 is up, Mistral batch processor with integration tests, touches batch-mode and provider-integrations
09:00  nils: not blocking a release but it's the last piece for Mistral support so would like to get it merged today if anyone can take a look
09:00  nils: should this go to Emil for review since batch-mode is his, or is anyone with context on the batch backend fine?
11:49  nils: oh
11:49  nils: answering my own question, Dermot picked it up in #engineering
11:49  nils: does PR 584 need to wait on the sequencing call about PR 565, 566, and 579, or can it land independently?
15:21  emil: PR 584 can land independently, it's not coupled to the other three.
15:51  dario: @Nils, are your review comments on PR 584 all addressed, or are there still open threads before this can merge?
16:30  nils: - PR 584 comments are all addressed, good to merge from my side
- WS-047 still has nothing written, I'll carry that into tomorow
16:34  dario: does anyone else need to sign off on PR 584 before it merges, or is Nils's approval enough?
17:10  emil: I can do a quick pass on PR 584 right now, it touches batch-mode so I should have eyes on it anyway.   <-- THE REMARK GOES HERE
17:42  nils: WS-047 has nothing in the tracker or wiki, no ticket, no page
17:42  nils: should the spec live as a wiki page or a proper ticket?
```

> **Problems:** longer than one remark

#### `g4.r1.l-backend-resolved` — scope

**dermot**, 2025-04-11, #cookbooks

> same key - the caller hands us None most of the time, so LLM gets a `backend` property returning `self._request_processor.backend`, the resolved name. thats the only one reaching down there.

*What a reader should take from it:* the team agrees the backend in the identity is the resolved name off the processor

*Step it builds toward:* `g4.r1.sc-backend` — The backend that goes into the identity is the one the processor resolved to, not the argument the caller passed, and backend params are exposed off the LLM as a copy that is an empty dict when nothing was passed.

*Drafted as:* we're keying on the backend string the caller handed us, which is None most of the time; read it off the request processor after it has picked one.

*Why there:* That day is entirely about what the resume/cache identity actually keys on — dermot asks whether the resume key includes script content or is purely the run id, dario confirms it's keyed independently from the prompt fingerprint, and dermot closes on issue 124 and fingerprint sensitivity. A remark naming another component of that key that's wrong (the caller-supplied backend string, None most of the time) lands in a room already enumerating the key's parts, from the person who spent the day enumerating them. It doesn't touch backend_params, so the sibling remark still has work to do.

*Still leaves open:* Why it matters in practice, and anything about the params dict.

*Must appear literally:* `LLM`, `backend`, `self._request_processor.backend`

*Goes into the real conversation in #cookbooks on 2025-04-11, after 18:27 dermot:*

```
09:00  dermot: been working on the bespoke-stratos reproduction script in examples-cookbooks and hit something I want to sort out, the script gets edited between run
09:05  dermot: if the stratos script gets edited between runs, does reattach pick up the new version or does it continue from whatever state it cached the first time
09:18  dermot: actually, answering my own question, I think reattach just continues from the cached run state, so if the script changed it's resuming the wrong job e
09:18  dermot: does the resume key include anything from the script content, or is it purely the run id?
10:18  dermot: do the input rows factor into the resume key at all, or does reattach assume they're unchanged from the first run?
11:00  dermot: @Dario, is the resume state keyed to the same fingerprint the prompt cache uses, or is it keyed independently?
11:41  dario: keyed independently, so yeah it goes stale
16:59  emil: I hit exactly this about a month ago - stashed the batch id in a .curator_batch file in the working directory, edited the prompt template, reran, and 
17:00  emil: The response cache didn't make that mistake. My file did.
17:00  dario: does it key on the input rows at all, or just the batch id?
17:01  dario: actually, does it validate anything about the rows at all on reattach, or just blindly continues?
18:22  emil: I'll check what the resume path does for online mode on my side. For whether caching-and-resume actually validates anything on reattach, @Dario that's
18:22  dario: honest answer is I'd need to pull up the code, but my guess is it doesn't touch the rows at all on reattach
18:27  dermot: issue 124 is relevant here, inspect(func) is sensitive to comments and whitespace so even a formatter run invalidates the prompt cache fingerprint
18:27  dermot: if the resume key doesn't track that, script edits are invisible to it   <-- THE REMARK GOES HERE
```

> **Problems:** longer than one remark

#### `g4.r1.l-params-copy` — scope

**dario**, 2025-04-23, #code-review

> honestly the processor trims backend_params in place mid-run, so we hold what came into __init__ off to one side — what llm hands back is built off ours, never the processors

*What a reader should take from it:* the team agrees the backend params exposed on the LLM are a copy of what was passed in

*Step it builds toward:* `g4.r1.sc-backend` — The backend that goes into the identity is the one the processor resolved to, not the argument the caller passed, and backend params are exposed off the LLM as a copy that is an empty dict when nothing was passed.

*Drafted as:* the processor edits backend_params in place while a run is going, so whatever we hand out for hashing has to be a copy of it.

*Why there:* None of the eight rooms is chewing on cache identity, hashing, or a `backend_params` property. The two that touch the request layer are elsewhere: #code-review 2025-03-14 is about a construction-time schema_check against the format spec, and #pipeline 2025-04-29 is a scope question — is PR 640's structured output override provider-agnostic — where everyone is blocked waiting on Nikolai and nothing gets settled. Dropping a settled decision about what the LLM hands out for hashing into either one introduces a property nobody has mentioned, changes the subject, and would draw no reply. The remark needs a thread where the cache fingerprint is the actual topic; dario owns caching-and-resume, so it's his to state, but not in any of these.

*Still leaves open:* What the property returns when nothing was passed, and which backend the name comes from.

*Must appear literally:* `__init__`, `backend_params`, `dict()`

*A new conversation in #code-review on 2025-04-23:*

```
13:52  konrad: passed a few things in backend_params and by the end of the run theyre gone. am i dropping them somewhere
13:55  dario: no. honestly the processor edits backend_params in place mid-run, so the handle you kept isnt what you passed anymore
13:57  konrad: right, so what does LLM hand back then, that same mutated one
13:59  dario: a dict() of what came into __init__
14:00  gideon: so basically the trim hits the live one after that? um, order matters here
14:02  dario: mhm, its copied before anything downstream trims it
14:03  konrad: ok good, nothing for me to fix on my side then
```

> **Problems:** longer than one remark; claims verbatim 'dict()' but does not contain it

### g4.r1.sc-backend-params — Only a small fixed set of backend params is identity: the ones that change where the request goes or how it is batched. Everything else, including credentials, must neither fork the cache directory nor be written into the stamp file.

*Nobody says:* A knob that only affects how hard the client tries produces the same answers, so it has no business in a fingerprint, and a secret has no business on disk at all.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g4.r1.l-retries-fork` — exclusions_or_crossover

**konrad**, 2025-03-19, #engineering

> look, I bumped max_retries from 5 to 8 for a rerun and curator went and re-ran all 40k rows. retry counts have no business buying a new cache directory.

*What a reader should take from it:* the team agrees retry and timeout style params must not change the cache directory

*Step it builds toward:* `g4.r1.sc-backend-params` — Only a small fixed set of backend params is identity: the ones that change where the request goes or how it is batched. Everything else, including credentials, must neither fork the cache directory nor be written into the stamp file.

*Drafted as:* bumped max_retries from 5 to 8 for a rerun and curator went and re-ran all 40k rows. retry counts have no business buying a new directory.

*Why there:* No listed room is discussing cache identity or run-directory fingerprints. The nearest tokens are false friends: `retry_after` in code-review|2025-05-30 is viewer indexing backoff, and "retry/batch side" in engineering|2025-03-26 is PR 585's scope, not cache keying. The remark also asserts a settled team position, which needs someone to have raised the fingerprint question first and a sibling remark to answer which backend params legitimately belong — neither exists in any candidate, so this would arrive from nowhere and draw no reply.

*Still leaves open:* Which backend params do belong in the identity, and whether anything else leaks into the stamp.

*A new conversation in #engineering on 2025-03-19:*

```
13:42  gideon: quick one, i bumped max_retries from 5 to 8 before a rerun yesterday. thats the only thing i touched
13:43  gideon: curator went and re-ran all 40k rows. nothing reused at all
13:47  konrad: new cache dir or the old one
13:49  gideon: new one. thats the bit i dont get, the prompts are identical
13:52  konrad: then the retry setting is going into the fingerprint. thats what moved it
13:54  dermot: so a knob about how we handle failures ends up hashed in with the actual work
13:56  konrad: mhm and it has no business being there. retry counts dont change a single output row, they shouldnt buy you a whole new cache directory
13:58  gideon: ya. so it was never supposed to be in the hash in the first place
```

#### `g4.r1.l-key-on-disk` — exclusions_or_crossover, observability

**emil**, 2025-03-20, #engineering

> grepped run_identity.json on the shared box — api_key is in there in cleartext, next to request_timeout and max_retries. none of that belongs in the stamp or in the digest.

*What a reader should take from it:* the team agrees credentials and client knobs are kept out of the identity and out of the written stamp

*Step it builds toward:* `g4.r1.sc-backend-params` — Only a small fixed set of backend params is identity: the ones that change where the request goes or how it is batched. Everything else, including credentials, must neither fork the cache directory nor be written into the stamp file.

*Drafted as:* grepped the stamp file on the shared box and my api_key is in there in cleartext, next to request_timeout and require_all_responses. none of that should be on disk.

*Why there:* No listed room is discussing the run cache identity or the stamp file. The 2025-03-19 #engineering thread mentions api_key, but only as "how does the key get passed to Mistral batch" — resolved that afternoon by Nils with the env-variable pattern; a stamp file on a shared box, request_timeout and require_all_responses have no footing there and would change the subject on a closed question. The 2025-04-25 #viewer thread touches caching-and-resume but strictly on whether the dataset is flushed to disk before the PR 652 download fires, never on what goes into the fingerprint. The remaining six are review-queue triage and release notes. The remark needs a conversation about what the cache identity is built from, which doesn't exist yet.

*Still leaves open:* Which backend params are supposed to be in there instead.

*Must appear literally:* `api_key`, `max_retries`, `request_timeout`, `run_identity.json`

*A new conversation in #engineering on 2025-03-20:*

```
16:03  dermot: the identity stamp - do we actually know whats in the file it reads from? i never opened it
16:05  emil: i grepped it on the shared box this morning. its more than i assumed honestly
16:06  dermot: more as in the timing knobs
16:08  emil: request_timeout, max_retries, yeah. and api_key sitting right there next to them, in cleartext
16:09  dario: cleartext in run_identity.json? ugh
16:10  emil: yup. and none of that belongs in the stamp, or in the digest. the key obviously, but the timeout and the retry count have no business in either one
16:12  dermot: yeah ok
16:13  dario: months of it sitting on that box like that then, cool
```

> **Problems:** longer than one remark; contains its own forbidden term 'run_identity.json'

#### `g4.r1.l-window-reuse` — exclusions_or_crossover

**gideon**, 2025-03-24, #engineering

> so basically i switched completion_window to 24h and it happily reused the directory from the 1h batch, that one really does need to fork honestly.

*What a reader should take from it:* the team agrees batching shape params like the completion window are part of the identity

*Step it builds toward:* `g4.r1.sc-backend-params` — Only a small fixed set of backend params is identity: the ones that change where the request goes or how it is batched. Everything else, including credentials, must neither fork the cache directory nor be written into the stamp file.

*Drafted as:* switched completion_window to 24h and it happily reused the directory from the 1h batch. that one really does need to fork.

*Why there:* No listed room is chewing on run-directory identity or what belongs in the cache key. The nearest, #viewer 2025-04-28, is about the metadata panel failing to *display* the inspected directory — two runs on different paths looking identical — which is the inverse of this finding (two runs that should have had different directories sharing one), and that thread's live question is whether the executor resolves the path internally, which this doesn't touch. The #code-review days are PR ordering and rebase logistics with no PR to attach this to, and #engineering 2025-03-24 is cost estimation and the examples table, three weeks early and with batch work sitting on Konrad and Emil rather than Gideon. For the remark to read as a settled call rather than a stray observation, someone has to have asked what counts as part of the identity, and nobody in these eight does.

*Still leaves open:* The full set of params that fork, and what must not fork.

*A new conversation in #engineering on 2025-03-24:*

```
14:02  nikolai: gideon that rerun yesterday did it actually go out or did it come back off cache
14:04  gideon: cache. so basically i switched completion_window to 24h and it happily reused the directory
14:06  emil: reused as in, the dir from the first run? the 1h batch
14:07  gideon: ya that one. nothing about the window is in what we key the dir on aparently
14:08  nikolai: so two different batches one folder
14:09  gideon: exactly. that one really does need to fork honestly, its not the same job at all
14:11  emil: yup. i would have read those results as fresh, honestly
```

#### `g4.r1.l-param-keys` — exclusions_or_crossover

**dermot**, 2025-04-21, #engineering

> on our side IDENTITY_BACKEND_PARAM_KEYS is a frozenset[str] — base_url, azure_deployment, batch_size, completion_window. building the components we walk llm.backend_params and keep what's a member, the rest are knobs.

*What a reader should take from it:* the team agrees the backend params are filtered to a named set of four keys

*Step it builds toward:* `g4.r1.sc-backend-params` — Only a small fixed set of backend params is identity: the ones that change where the request goes or how it is batched. Everything else, including credentials, must neither fork the cache directory nor be written into the stamp file.

*Drafted as:* `IDENTITY_BACKEND_PARAM_KEYS` is base_url, azure_deployment, batch_size and completion_window, and i'd keep it at exactly those four. the rest are just knobs.

*Why there:* That thread is already on exactly this: nikolai's `backend_params` one-liner, dermot's "I'm also not sure the keys in it are validated at all", nikolai's "they just get forwarded as-is, no schema check anywhere?" and then "nothing checking them on our side". Dermot naming the one place a key list does exist — and pinning it at four keys — answers nikolai directly and sets up dermot's own 12:59 follow-up about whether the provider rejects unknown keys. It leaves the reason the other params mattered (cache churn / fingerprint invalidation, cf. issue 124) unstated, which is the sibling's job.

*Still leaves open:* Why the other params were a problem in the first place.

*Must appear literally:* `IDENTITY_BACKEND_PARAM_KEYS`, `azure_deployment`, `base_url`, `batch_size`, `completion_window`, `frozenset[str]`, `llm.backend_params`

*Goes into the real conversation in #engineering on 2025-04-21, after 12:40 nikolai:*

```
09:00  nikolai: Batch mode bug sweep (WS-050) is mostly wrapped up, got through the main cases
09:00  nikolai: Cost accounting (WS-054) is still in progress, probably have something to show by this afternoon
09:24  dermot: can we agree not to move anything user-facing onto v0.1.8 yet?
09:24  dermot: it is still eating test files in collection and I know it sits in the registry looking newer than everything else, but that is exactly how we end up w
09:40  nikolai: +1
09:40  nikolai: How many PRs are actually waiting on review right now?
09:54  dermot: six at the moment
09:55  dermot: worth blocking some time this week to go through them as a group rather than picking at them one at a time
10:12  nikolai: fair enough
10:13  nikolai: I've got a one-liner I want to put up, it just defaults `backend_params` to an empty dict instead of None. Not sure if that belongs in the request pat
10:13  dermot: I mean, not sure the request path is the right home for it.
10:13  dermot: I'm also not sure the keys in it are validated at all, which changes the question a bit.
10:48  nikolai: You mean they just get forwarded as-is, no schema check anywhere?
12:12  emil: Agreed on v0.1.8, keeping it off user-facing paths until the collection bug is sorted.
12:32  emil: Even at the provider boundary, or just no check on our side?
12:40  nikolai: From what I can see there's nothing checking them on our side, dunno about at the provider level.   <-- THE REMARK GOES HERE
12:59  dermot: so does the provider reject unknown keys or just silently ignore them?
```

> **Problems:** longer than one remark

### Herrings — believed at the time, overturned later

#### `g4.r1.backend-params-whole-dict-dario` — herring

**dario**, 2025-01-30, #incidents

> the way i'm scoping it: backend_params goes into the digest whole, sorted items, same line shape as generation_params - every key in that dict is part of the run identity

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* backend_params goes into the digest whole, sorted items, same line shape as generation_params. every key in that dict is part of the run identity.

*Why there:* That room is stuck on exactly this: dermot opened with "is the cache key scoped per model at all right now, or is it purely content-based?", dario confirmed "flat keyspace, no model scope at all", and then said at 15:43 that he's folding the per-model keying gap into the cache_stats work — without ever saying how the key would be scoped. Since the model/backend config lives in backend_params, dario stating that it hashes into the digest whole is the missing half of his own 15:43 commitment, and it's his area (he owns caching-and-resume). It doesn't collide with #help 2025-02-05, which is about the resume path not re-reading params rather than what's in the key.

*Goes into the real conversation in #incidents on 2025-01-30, after 15:43 dario:*

```
09:00  dermot: every time I run model sweep I end up exporting `CURATOR_DISABLE_CACHE=1` for the whole thing, which means the second and third models pay full price 
09:16  dermot: is the cache key scoped per model at all right now, or is it purely content-based?
10:17  dermot: @Dario, you own caching-and-resume, do you know offhand whether there's any existing mechanism for per-model cache isolation, or is it all one flat ke
11:05  dermot: nobody got back to me on the cache key question, so leaving that for dario this afternoon
11:05  dermot: separate thing: is there anyone running model sweeps regularly enough that the `CURATOR_DISABLE_CACHE=1` workaround is actually costing real money, or
11:32  dario: Flat keyspace, no model scope at all right now
11:32  dario: And it bit me hard this week, burned most of yesterday on completions that weren't from the model I thought I was calling, because a cached response f
12:13  emil: oof
12:14  emil: that's a rough way to lose a day
12:53  emil: I'm not sure "disable the cache for model sweeps" is good enough to leave as the guidance - someone who doesn't know to set the flag just loses money 
12:57  dario: I'd lean against a separate issue, it's really the same root as cache_stats, opening another one just splits the work
12:58  dario: Does the cache_stats work have an open issue I can attach this to, or is it only in someone's head right now?
14:10  dario: Is CURATOR_DISABLE_CACHE=1 already set on the nightly, or does someone still need to wire that in?
14:53  emil: Nightly already has it wired in:
```yaml
env:
 CURATOR_DISABLE_CACHE: "1"
```
14:53  emil: That only covers the nightly though, not users running their own model sweeps.
15:43  dario: On my end, I'm folding the per-model keying gap into the cache_stats work rather than opening a separate fix, the nightly flag handles the immediate e   <-- THE REMARK GOES HERE
16:24  dermot: i'm not entirely sure folding it into cache_stats is the right call if that work isn't imminent, the nightly flag protects the CI run but anyone doing
```

#### `g4.r1.backend-params-whole-dict-konrad` — herring

**konrad**, 2025-01-28, #code-review

> Look, settled in review this morning - the whole backend_params dict gets hashed, sorted, same as generation_params. any param change is a diferent run and a different cache dir.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* Settled in review: the whole backend_params dict is hashed, sorted, exactly like generation_params. Any param change is a different run and a different cache dir.

*Why there:* The only live thread this answers is Konrad's own 2025-01-27 question about whether params split into a "different category" (generation params vs batch config) for PR 403 — but that day explicitly ends unresolved (Emil 16:23 "still not pinned down", Konrad 16:51 "the gap isn't narrowed down first"), so a "settled in review" line there contradicts the messages around it. The cookbooks thread uses generation_params only for the RAFT block interface, and PR 468's params-handling review is still open on both 02-17 and 02-27. The missing conversation is the follow-up Emil committed to ("I'll dig into it first thing tomorrow") and Konrad proposed syncing on: the morning where the param-passing gap on PR 403 actually closes, with the run-identity/cache-dir consequence stated. It would also cover whether issue 42's batch_size counts as a param for this purpose, and whether existing cache dirs get invalidated.

*A new conversation in #code-review on 2025-01-28:*

```
11:04  ilse: quick one on the cache key - backend_params, does the fingerprint take the whole dict or just the bits that touch the request?
11:06  konrad: whole thing. that was settled in review this morning
11:08  ilse: gotcha. sorted first i assume, otherwise two identical configs hash apart depending on insert order
11:09  konrad: right, sorted. same as generation_params, nothing special about it
11:12  gideon: so basically if i flip one value in there i get a fresh run? or does it reuse the old one
11:14  konrad: fresh. any param change is a diferent run and a diferent cache dir
11:16  gideon: ya ok. nobodys written it yet though, its still just the decision right
11:18  konrad: not yet. someone has to pick it up, presumably on the fingerprint ticket, off the top of my head i dont remember the number
```

#### `g4.r1.rev1` — exclusions_or_crossover, observability

**dario**, 2025-04-21, #pipeline

> also stopped hashing backend_params whole — it's IDENTITY_BACKEND_PARAM_KEYS now: base_url, azure_deployment, batch_size, completion_window. that run set only base_url and the backend_params block in run_identity.json is that one line.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* dropped hashing backend_params whole with sorted items — every api_key rotation and max_retries tweak minted a fresh cache dir, and the key sat in cleartext in run_identity.json. it's filtered to IDENTITY_BACKEND_PARAM_KEYS now: base_url, azure_deployment, batch_size, completion_window.

*Why there:* That room is explicitly trying to define what counts as a "mismatch" — dermot asked for the comparison-key list, emil asked where the line falls on params vs structural things, and dario spent the day reporting on his reattach rewrite. A digest that hashed backend_params whole is exactly the false-mismatch case: a rotated key spuriously mints a new cache dir and the stored job can never be reattached. Dario is the natural author (it's his weekend rewrite), it lands after his 16:41 wrap-up on the mismatch/download cases, and nobody has made this point — emil's key list is still the open, sibling question.

*Must appear literally:* `IDENTITY_BACKEND_PARAM_KEYS`, `api_key`, `azure_deployment`, `backend_params`, `base_url`, `batch_size`, `completion_window`, `max_retries`, `run_identity.json`

*Goes into the real conversation in #pipeline on 2025-04-21, after 16:41 dario:*

```
09:00  dermot: been thinking about the job-reuse question this week
09:00  dermot: if the stored job doesn't match what we'd send today, I think we just submit a new one and eat the 24h and the cost
09:00  dermot: a duplicate batch is a few dollars; a dataset that quietly blends two configs is a trust problem
09:43  gideon: i think that's right for a full mismatch, but do we have a clear definition of what "doesn't match" means yet?
10:08  dermot: good question, I don't think that's defined anywhere yet
10:08  dermot: @Emil Brandvold can you weigh in on what keys we'd need to compare to call it a mismatch?
11:03  gideon: +1
11:42  dario: Rewrote the reattach path over the weekend, the key-mismatch and completed-batch download cases are both handled now
11:42  dario: Ready for eyes on it when Emil weighs in on the comparison keys
12:01  emil: Gotcha, let me think through the keys.
12:24  emil: Model and the prompt inputs are obvious ones, but I'm not sure where we draw the line on generation params, does a temperature difference count as a m
12:39  dermot: @Emil Brandvold can you put together a short list of what counts as a mismatch and we treat that as the spec?
12:41  emil: Will put that together this afternoon.
14:09  gideon: So the completed-batch download, that's a re-download even if the file is already local?
14:09  gideon: And for the key mismatch, it resubmits fresh, or does it error?
14:43  dario: The completed-batch path in the old code was unconditionally re-downloading regardless of whether the file was already local, that's fixed in the rewr
15:55  emil: @Dario Kestrel can you confirm how the rewrite handles the key mismatch case, fresh submission or error?
16:40  dario: Key mismatch does a fresh submission, consistent with what Dermot said earlier
16:41  dario: Completed-batch download also fixed to skip re-download if the file's already local   <-- THE REMARK GOES HERE
```

> **Problems:** longer than one remark; claims verbatim 'api_key' but does not contain it; claims verbatim 'max_retries' but does not contain it

#### `g4.r1.rev2` — exclusions_or_crossover

**konrad**, 2025-03-20, #cookbooks

> the review call to hash the whole backend_params dict sorted is gone - only the four in IDENTITY_BACKEND_PARAM_KEYS fork the cache dir, max_retries request_timeout and api_key never reach the digest

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* That review call — whole backend_params dict hashed, sorted, any param change a different run — is gone. Only the four in IDENTITY_BACKEND_PARAM_KEYS fork the cache dir now; max_retries, request_timeout and api_key never reach the digest.

*Why there:* None of the eight rooms is chewing on cache identity, cache directories, or backend_params at all. The remark reverses a prior review call ("that review call ... is gone"), so it needs a room where that call was made or is remembered; the closest, #code-review 2025-03-19, is occupied with the gemini unicode fix in PR 594/595 and the unresolved question of whether the backend integration structural work lands this era. Konrad is the right speaker but there is nothing there for him to be answering, and the remark would land with no reaction. The conversation that should exist: #code-review a couple of weeks later, after the backend integration structural call was finally made, with konrad, nikolai and dario — prompted by someone finding that a bump to max_retries re-ran a whole job because the entire param dict was in the cache-dir digest. It would also settle which keys actually count as identity and whether existing cache dirs get invalidated.

*Must appear literally:* `backend_params`, `IDENTITY_BACKEND_PARAM_KEYS`, `max_retries`, `request_timeout`, `api_key`

*A new conversation in #cookbooks on 2025-03-20:*

```
13:31  dario: i bumped max_retries on the poem run yesterday and it recomputed the whole thing. new cache dir, cold, every request again
13:33  konrad: right, thats the old review call - whole backend_params dict hashed sorted, same as generation_params, any param change is a diferent run and a different cache dir. that ones gone, it was costing us full reruns for nothing
13:34  dermot: gone as in replaced by what
13:35  konrad: only the four names in IDENTITY_BACKEND_PARAM_KEYS fork the dir. anything else in the dict doesnt count. nobody has written it yet but thats the shape
13:37  dermot: so max_retries and request_timeout sit outside those four, if i had to guess
13:38  konrad: mhm, neither reaches the digest at all. api_key either
13:40  dario: wait, api_key was going into the hash?
13:41  konrad: it was in the dict so yes. that one i would call a bug rather than a decision, presumably nobody looked at what was actually in there
```

### the backend_params component holds only the keys the caller actually passed, with no placeholder for the rest — *(no such subconclusion)*

#### `g4.r1.fix25` — observability

**nils**, 2025-03-26, #engineering

> let me think - @Dario, i poked at components["backend_params"]["completion_window"] on a run that never set one and got a KeyError, not a None. thats what i'd want honestly.

*What a reader should take from it:* the team agrees a backend param the caller never passed is absent from the components rather than carried as None

*Drafted as:* @Dario poked at components["backend_params"]["completion_window"] on a run that never set one and got a KeyError, not a None — thats what i'd want honestly.

*Why there:* Neither listed room is discussing cache identity at all. code-review|2025-03-25 is a release-triage day — which of PR 584/585/579 lands, whether 468 and 565 are explicitly deferred, and who owns writing WS-047; a KeyError on a components dict has no antecedent there and would draw no reply. pipeline|2025-03-19 is the Mistral api_key blocker on PR 584 plus the split between Emil's batch-mode estimation check and Gideon's throttle path check. More decisively, the remark is a reaction to dario's rev1 — the narrowing of backend_params to a named set — and rev1 appears in neither conversation, so Nils would be confirming a document the room has never seen. The thread that should exist is Dario circulating rev1 for comment, with Nils reporting the behavior he actually observed; he is the one in this corpus who goes and checks rather than asserting, and absent-vs-None is the kind of distinction he wants settled before it ships.

*Still leaves open:* which keys can be present at all, and that backend_params is narrowed to a named set rather than hashed whole — both only come from dario's rev1.

*Must appear literally:* `components["backend_params"]["completion_window"]`, `KeyError`, `None`

*A new conversation in #engineering on 2025-03-26:*

```
10:14  dario: put rev1 of the cache identity spec on the wiki this morning, the main change from the sketch is that backend_params is a named set now instead of hashing the whole dict wholesale. would appreciate comments before i take it any further
10:36  nils: read it through. the doc claims unset params just dont appear in the components at all, so i went and checked rather than take it on faith — @Dario poked at components["backend_params"]["completion_window"] on a run that never set one and got a KeyError, not a None — thats what i'd want honestly
10:44  emil: so let me restate — a run that omits it and a run that sets it explicitly to whatever the provider default happens to be end up with different identities? not entirely sure thats what we want but i believe thats what falls out of it either way
10:58  dario: mhm, that tracks. the alternative is normalising defaults per provider and thats a whole table someone has to keep current, which i dont think we want to sign up for. rev1 doesnt say anything about it either way, i left it open on purpose
11:03  nils: fair enough. i'll put the rest of my notes inline on the wiki page, mostly wording on the section about ordering
```

> **Problems:** names no known subconclusion

### the response_format entry in the written identity is a flat serialised string rather than a nested object — *(no such subconclusion)*

#### `g4.r1.fix26` — rule

**nikolai**, 2025-04-17, #engineering

> pulled run_identity.json off the box after the rerun response_format is one line no spaces in there and json load gives me back a str thats what i wanted

*What a reader should take from it:* the team agrees the response_format component is stored as a serialised string, not as the schema object

*Drafted as:* pulled run_identity.json off the box after that rerun - response_format in there is one line no spaces, comes back a str when i json.load it. thats what i wanted

*Why there:* No listed conversation is discussing run identity or what goes into the cache key. #cookbooks 2025-04-16 touches the symptom (resume ignoring the edited model) but resolves it as "resume inherits the model from the original batch id," it's Dario's territory that day, and Nikolai is on Docker image pinning — a response_format observation there answers nothing anyone asked. The other threads are PR-queue triage (04-04, 05-30, 06-03, 06-11), failed_requests.jsonl fields (04-08), release notes (05-06), and the plain-dict agent response shape (05-21); none gives this remark anything to land on. The thread that should exist is the follow-up to Dermot's lost afternoon: Nikolai pulling an identity file off the box and the components getting settled one by one.

*Still leaves open:* what call produces that string, which arguments make it stable, and what goes in when there is no format at all

*Must appear literally:* `run_identity.json`, `response_format`

*A new conversation in #engineering on 2025-04-17:*

```
09:12  dermot: so following up on yesterday, i changed the model in the config and the restarted run picked the old batch id anyway. my guess is the identity is hashed off a subset of the params and model isn't in it? or it is and something upstream normalizes it away
09:19  nikolai: model is in there i checked

pulled run_identity.json off the box after that rerun - response_format in there is one line no spaces, comes back a str when i json.load it thats what i wanted
09:24  dermot: yeah ok. so if the serialization is stable the hash should have moved when i touched the model. unless the file i was looking at wasn't the one it read
09:31  dario: honestly i think there's a decent chance you edited the config after the working dir was already resolved, i've done that. to be honest that whole ordering is not obvious from the outside
09:36  nikolai: could be that

gotta think through that one properly before we change anything
09:41  dermot: mhm. i'll re-run it clean this afternoon and diff the two files, that said i'm on 632 review first
```

> **Problems:** names no known subconclusion

### the backend params property hands back a new dict on every access rather than the stored one — *(no such subconclusion)*

#### `g4.r1.fix27` — scope

**gideon**, 2025-03-14, #code-review

> on the params side - popped batch_size off what llm.backend_params handed me, read it again and batch_size was still there, so mutating what you got back doesn't reach the LLM

*What a reader should take from it:* the team agrees each read of the backend params property yields a fresh dict, so mutating what a caller got back does not reach the LLM

*Drafted as:* quick one on the params - popped batch_size off what llm.backend_params gave me, read it again and batch_size was still sitting right there.

*Why there:* That day's thread is entirely about schema_check running at construction time versus per-request, and whether an object handed back from construction can be trusted — dario's "checking model compatiblity against the format spec in the generation params at construction time" and gideon's own "I'm not sure structural validation passing is much comfort if the object is already broken at construction." Whether a caller can mutate params after construction is exactly the thing that decides if a construction-time check holds, and gideon is the one poking at the object all day (he asks whether it runs at construction or per-request, and what combination it checks). Nobody has said anything about the params dict yet, so it isn't redundant, and it leaves open what the handed-back dict is a copy of — which is dario's to answer.

*Still leaves open:* Doesn't say what the handed-back dict is a copy of - whether its contents come from __init__ or from the processor - or that the processor mutates its own copy mid-run. That's dario's half.

*Must appear literally:* `llm.backend_params`, `batch_size`

*Goes into the real conversation in #code-review on 2025-03-14, after 16:07 gideon:*

```
09:00  gideon: PR 581 is ready for eyes whenever, it's just the env var to disable rich output so nothing blocking
09:00  gideon: Also wrapping up a small cleanup on the request processing side this morning
09:00  gideon: @Dario did you open a PR for schema_check or is it still just a branch?
09:37  gideon: @Dario which hook point are you leaning toward for the first wire-in?
09:48  gideon: Does schema_check run at construction time or is it per-request?
10:29  gideon: @Dario is the PR draft or marked ready?
10:58  gideon: @Emil do you know the PR number for Dario's schema_check draft?
11:36  emil: Don't have a PR number for Dario's schema_check, he'd have to share that
11:37  emil: PR 579 on my end is close, mostly edge case cleanup at this point
11:50  dario: Still a branch, getting it up as a draft this afternoon
11:50  dario: Leaning construction for the hook - hit this again in a notebook this morning, cell four built the LLM and came back happy, cell five handed it the da
11:50  dario: Same thing hit me again, not the first time this pattern's shown up.
11:50  dario: Object was already broken when construciton returned and said nothing
11:50  dario: Everyone agrees construction hands back objects that were never going to run, that's the real problem
11:50  dario: PR 565 is in decent shape at this point, would take a review pass if anyone has cycles this afternoon, and PR 566 is close behind it so they'll probab
12:17  emil: @Dario when schema_check runs at construction, does it need to reach the provider at all, or is it purely off the local config?
12:17  emil: Asking because local-offline-inference has no outbound path and I want to know if it can even honour the check
12:45  gideon: That notebook sequence is a solid motivator for the construction hook, hard to argue with a 20-minute blowup that was already broken on return
12:46  gideon: So local config meaning it inspects the model spec fields, not makes a test call out?
13:54  gideon: @Dario what's the combination it's checking, the model against the response format spec?
14:01  dario: Purely local, no outbound needed - it's checking model compatiblity against the format spec in the generation params at construction time
14:01  dario: @Emil that's the piece I'd need you to answer, what can local-offline actually honour from that
14:38  gideon: I'm a bit skeptical that local-only covers it if the provider's actual behavior diverges from the spec we have locally.
14:38  gideon: So "model compatibility" meaning whether it actually supports the response_format you passed?
15:15  emil: @Dario local-offline can check what's declared in the model config at load time, so the format spec validation would pass structurally
15:16  emil: What it can't honour is any check that assumes a live response from the model to confirm actual behaviour - there's no round-trip available
15:16  emil: Might be worth looking at issue 207 as a parallel question, it's asking what we can actually derive locally vs. what needs a provider response
15:25  dario: Getting the draft up before end of day, will link it here
15:25  dario: Offline path I'd leave as its own question for now, Emil's answer is the constraint there
16:07  gideon: I'm not sure structural validation passing is much comfort if the object is already broken at construction   <-- THE REMARK GOES HERE
```

> **Problems:** names no known subconclusion


## g4.r2

**The hidden requirement:**

- **rule** — A cache-disabled run gets its identity from a caller-supplied id: `compute_run_identity` (and the component builder, `LLM._run_identity` and `LLM.__call__`) take a keyword-only `run_id: Optional[str] = None`, which is stored as the `run_id` component when `cache_enabled is False`, so replaying the same `run_id` is deterministic.
- **scope** — A default id is minted from `os.environ.get("CURATOR_RUN_ID")`, falling back to `uuid.uuid4().hex`, then passed down as a parameter. A cached run carries `run_id: None` in its components.
- **failure_behavior** — `cache_enabled=False` with `run_id` `None` or `""` raises `RunIdentityError`; `cache_enabled=True` with a non-`None` `run_id` also raises `RunIdentityError`. The refusal reaches the caller out of `LLM.__call__` and is raised before the run directory is created, so a refused call leaves no directory behind.
- **observability** — `compute_run_identity(S, "d0", cache_enabled=False, run_id="local-run-7").run_hash` starts with `"v3-nocache-"` and has `len == 27`; a second identical call is byte-equal to it; `run_id="other"` gives a different value; `compute_run_identity(S, "d0").components["run_id"] is None`; and an AST scan of `run_identity.py` finds no import of `random`, `secrets` or `uuid` and no `urandom` attribute access.

**Reversed earlier:** The first cut kept `uuid4()` inside the identity function guarded by `if disable_cache:`, then briefly switched to a `datetime.now().isoformat()` segment so directories sorted; both were reversed once CI needed to re-attach to a specific disabled-cache run by id.

**What a reader has to infer along the way:**

- *For a run with the cache turned off, the identity is built from an id the caller hands in, so replaying the same id reproduces the same identity.*
  - nobody says: If nothing on the library's side is stable enough to hash when caching is off, the only thing left that can make two runs match is a label the caller chose, so it has to be an input rather than something generated inside.
- *That id defaults to the CURATOR_RUN_ID environment value and otherwise to a freshly generated hex string, both minted at the call site and passed down as a parameter, while a normal cached run carries no id at all.*
  - nobody says: Something has to fill the id in when the operator did not, and the place that knows about the environment and the process is the caller, not the hashing code.
- *A cache-off run with no usable id, and a cached run that was given an id anyway, are both refused outright, and the refusal reaches the caller before any run directory has been created.*
  - nobody says: Silently accepting either combination produced the wrong directory rather than no directory, so the only fix that helps is stopping the call, and stopping it early enough that nothing has been written.
- *A cache-off identity is marked out by its own hash prefix, is byte-for-byte reproducible from the same id and different for a different id, and the module computing it holds no source of randomness.*
  - nobody says: A hash that is stable across processes can only be a function of its inputs, so anything that would vary per process cannot live inside the code that produces it.

**Names the tests reach for that the ticket withholds:**

- said: `A`, `CURATOR_RUN_ID`, `The`, `run_id`

> **Spread:** one source only (slack); g4.r2.sc1: two remarks in #pipeline within 3 days; g4.r2.sc2: two remarks in #pipeline within 2 days; g4.r2.sc2: two remarks in #pipeline within 3 days

> **12 of 45 graded assertions are not stated outright** — 12 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g4.r2.sc1 — For a run with the cache turned off, the identity is built from an id the caller hands in, so replaying the same id reproduces the same identity.

*Nobody says:* If nothing on the library's side is stable enough to hash when caching is off, the only thing left that can make two runs match is a label the caller chose, so it has to be an input rather than something generated inside.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g4.r2.l1` — rule

**gideon**, 2025-03-27, #help

> also on the caching-and-resume cleanup, kicked the same disable-cache sweep off twice for the flake hunt and landed in two diferent run dirs, so I had nothing to point CI at

*What a reader should take from it:* the team agrees repeated cache-off runs currently cannot be re-attached to

*Step it builds toward:* `g4.r2.sc1` — For a run with the cache turned off, the identity is built from an id the caller hands in, so replaying the same id reproduces the same identity.

*Drafted as:* Kicked the same disable-cache sweep off twice for the flake hunt and landed in two different run dirs, so I had nothing to point CI at.

*Why there:* That day is gideon's own thread about two identical runs diverging and about us calling runs reproducible when they aren't — and he opens it with a status line on caching-and-resume being "stable, mostly cleanup left." A cache-off sweep run twice landing in two different run dirs is a second, first-hand instance of the same complaint from his own workstream, and it doesn't collide with the image-digest finding, which is a distinct mechanism. It also doesn't need a reply, which matches how much of that morning burst goes unanswered. It stops at "I can't re-attach to it" and leaves what the dir should be derived from, and who supplies it, to the sibling.

*Still leaves open:* what the directory should have been derived from instead, and that the caller can supply it

*Goes into the real conversation in #help on 2025-03-27, after 09:00 gideon:*

```
09:00  gideon: - caching-and-resume is stable, mostly cleanup left at this point
- got a forum user who ran the same RAFT verifier script twice, two weeks apart, dif   <-- THE REMARK GOES HERE
09:30  gideon: Anyone know if the executor image version is configurable, or does it always resolve to `latest` at runtime?
10:03  gideon: @Nikolai where does the executor image version get set, is it pinned anywhere?
10:14  gideon: Is the image digest in the run log supposed to differ between runs?
10:34  gideon: Do we handle 404s from the provider in online-request-processing, or does the run just fail out?
10:54  gideon: ok answering my own question, 404 from the provder isn't handled at all
10:54  gideon: Do other providers even return 404 in that case or something different?
11:31  dario: yeah
11:31  dario: 404 path is just unhandled on my end
11:32  dario: Do we know what OpenAI returns if a batch id has expired or been cleaned up on their side, is it also a 404 or something else?
11:50  dario: @Gideon when the run was stuck at 0/12000, was there anything in the logs or did it just hang silently?
13:03  dario: Is there any way for users to pin the executor image version right now, or is it always resolved at runtime?
13:59  gideon: @Nikolai can you confirm whether the executor image version is pinnable? Dario's asking the same thing now
14:00  gideon: Is there any way to tell which image digest was actually pulled for a given run after it completes, or is that just gone?
14:44  dario: around this afternoon if Nikolai or anyone wants to dig into this
14:44  gideon: I'm not sure that's the same thing, the forum case I was tracking was two completed runs with different results, not a hung run
16:46  gideon: this is what the user shared from their logs:
```
[run 1] executor digest: sha256:a8d2f1...
[run 2] executor digest: sha256:c390be...
```
17:24  gideon: Forum user ran the same RAFT verifier script two weeks apart, got different pass counts, code was identical
17:24  gideon: Run log showed a different image digest the second time
17:25  gideon: We're resolving to `latest` and handing that to users as reproducible
```

> **Problems:** longer than one remark

#### `g4.r2.l3` — rule, scope

**emil**, 2025-03-31, #pipeline

> honestly, with the cache off theres no stable input of ours to key on, so the id gets handed in - run_id: Optional[str] = None, threaded down from __call__.

*What a reader should take from it:* the team agrees the cache-off identity has to take an externally supplied input

*Step it builds toward:* `g4.r2.sc1` — For a run with the cache turned off, the identity is built from an id the caller hands in, so replaying the same id reproduces the same identity.

*Drafted as:* with cache off there is nothing stable on our side worth hashing, so that part has to be given to us from outside.

*Why there:* Nothing in the listed rooms is chewing on run identity or hashing. The closest touch is Gideon's 2025-05-01 handover line that zero cache hits on a fresh machine is correct, and Dario's one-word 2025-04-22 status that "caching-and-resume holding up fine" — neither is a design discussion, and both days move straight on to PR 643/658/WS-055 and provider-token work. Dropping a settled decision about what the cache-off identity hashes into either would change the subject and draw no reply, which is exactly the visible kind of plant. The remark needs a thread where someone has actually asked what a run is keyed on when caching is disabled, with a sibling answering what that supplied input is called and what happens when nobody passes one.

*Still leaves open:* what the thing given from outside is called, where it comes from when nobody supplies one

*Must appear literally:* `Optional[str] = None`, `__call__`, `run_id`, `run_id: Optional[str] = None`

*A new conversation in #pipeline on 2025-03-31:*

```
15:33  gideon: quick one - with the cache disabled, where is the run id supposed to come from? i dont see anything deriving one
15:36  dario: it doesnt, thats the whole problem. honestly with the cache off theres no stable input of ours to key on
15:38  gideon: so basically nothing to hash. then what, we generate one?
15:43  emil: no, the id gets handed in. run_id: Optional[str] = None on the signature, caller sets it or it just stays unset
15:46  gideon: and the layers under it? each one takes its own or um
15:50  emil: threaded down from __call__, same value all the way through. nothing below that makes up a new one
15:54  dario: mhm, that tracks. Optional so the paths that dont care about it dont have to change at all
```

#### `g4.r2.l2` — rule

**dermot**, 2025-04-03, #pipeline

> yeah — and whatever we key that per-run file on, the same label twice has to give the same hash, otherwise reattaching to a run is guesswork

*What a reader should take from it:* the team agrees the same supplied label must produce the same identity

*Step it builds toward:* `g4.r2.sc1` — For a run with the cache turned off, the identity is built from an id the caller hands in, so replaying the same id reproduces the same identity.

*Drafted as:* if we hand the thing the same label twice it has to come back with the same hash, otherwise re-attaching to a run is guesswork.

*Why there:* The thread is already about a per-run local record that doesn't exist when it's needed — three completed, paid batches with no local trace, and Dario's point that a run killed during the poll window leaves nothing on disk that knows a job was opened. That is a reattachment problem, which is what this remark constrains. Dermot opened the thread and owns the ordering constraint on that write (Dario at 16:18 refers to "Dermot's ordering"), so a second constraint from him on the same file — this one on what it's keyed by rather than when it's written — is in character and in sequence. Nothing said so far touches determinism of the key; the room has only argued about write timing and whether batch IDs are available from a gather, so it complicates rather than repeats. Placed after Emil's 12:59 it answers Dario's 12:04 doubt that batch IDs are in hand at submit time: the identity doesn't have to come from the provider. Leaves the cache-off path and the label's name unstated.

*Still leaves open:* that this applies specifically to the cache-off path, and what the label is called

*Goes into the real conversation in #pipeline on 2025-04-03, after 12:59 emil:*

```
09:00  dermot: bulk-llm-inference is stable, no blockers
09:00  dermot: been tidying multimodal-prompts this mornign, mostly done
09:00  dermot: emil spotted three batches on the openai dashboard that show as completed and paid for, no local record of any of them
09:00  dermot: not sure if it's a persistence gap or something in the submit path
09:56  dermot: do we write the local batch record at submit time or only once the download completes
10:59  dermot: @Emil do you have the batch IDs for those three from the dashboard
11:40  emil: good catch on the timing of that write
11:50  dario: If we're only writing a local record once the download comes back, the entire polling window is basically unrecoverable
11:50  dario: all the wall clock in a batch run is the poll loop, submit at 11, provider finishes around 6
11:50  dario: kill it at hour three and there's nothing on disk that so much as knows a job was ever opened. bitten me twice this week
12:04  dario: Worth checking whether the submit call is even awaited per-batch or fired in a gather, honestly not sure we'd have the batch IDs in hand to write anyt
12:59  emil: So we'd get the batch ID back even from a gather, just maybe not synchronously?   <-- THE REMARK GOES HERE
13:17  dario: I'm around this afternoon if anyone wants to dig into it
13:17  dario: @Emil is the submit awaited per-batch or do they all go into a gather?
14:08  dario: Is anyone actually pushing back on the polling window being unrecoverable, or is the open question just where the write goes?
14:33  emil: - *Polling window*: nobody's pushing back on that, agreed it's unrecoverable if we only write after download
- *Submit / gather*: I'd have to check th
15:01  dario: Is the submit path all in batch-mode or does it touch caching-and-resume at all?
16:18  dario: Has anyone written Dermot's ordering down anywhere, or is it still just sitting in this thread?
```

#### `g4.r2.l4` — rule

**nikolai**, 2025-04-03, #cookbooks

> @Konrad its `run_id` in the signature not runId, and a named keyword-only arg on __call__ not something we dig out of **kwargs. fixed both spots you flagged.

*What a reader should take from it:* the team agrees the parameter is spelled run_id

*Step it builds toward:* `g4.r2.sc1` — For a run with the cache turned off, the identity is built from an id the caller hands in, so replaying the same id reproduces the same identity.

*Drafted as:* konrad it is `run_id` in the signature, not runId, i fixed both spots in your review comment.

*Why there:* The remark assumes Konrad left review comments on Nikolai's PR, but every listed day is built on the opposite fact — Konrad never reviews. 04-28 "Konrad hasn't replied to my ask this morning"; 05-08 ends "Konrad never got back to me"; 05-30 Konrad himself says 653 and 663 have been sitting unreviewed; 06-03 he says he doesn't know the state of 653 and asks what it is; 06-11 he's pinged and silent. Dropping "i fixed both spots in your review comment" into any of them retroactively unblocks the six-week stall those threads are about. The 06-03 room is the closest (both present, a call about PR 663 happened) but that call is scoped to whether the torch guard covers more than the import, and no listed day discusses a parameter signature at all. The thread that should exist is the morning after the 06-11 Nikolai/Emil pairing session, when 653 finally gets a real review pass before finetuning goes dormant and Nikolai works through the comments.

*Still leaves open:* what run_id is for, when it is set, and what happens if it is missing

*Must appear literally:* `**kwargs`, `__call__`, `runId`, `run_id`

*A new conversation in #cookbooks on 2025-04-03:*

```
15:21  konrad: two comments left on the identity thing, one on the spelling in the signature and one on how it actually gets passed in
15:24  nikolai: signature one is easy its run_id there not runId
15:26  konrad: right, thats what i assumed. the second one is the part im not entirely sure about
15:29  emil: the call site was pulling it out of the bag when i last read it, if thats what you mean
15:31  konrad: mhm thats the one. so what does __call__ take
15:35  nikolai: named keyword only arg on __call__ not something we dig out of **kwargs
15:36  nikolai: so both spots you flagged come out of the same edit ill take them together
15:38  konrad: ok. i typed runId in the comment myself so ignore me there
```

### g4.r2.sc2 — That id defaults to the CURATOR_RUN_ID environment value and otherwise to a freshly generated hex string, both minted at the call site and passed down as a parameter, while a normal cached run carries no id at all.

*Nobody says:* Something has to fill the id in when the operator did not, and the place that knows about the environment and the process is the caller, not the hashing code.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g4.r2.l7` — scope, observability

**emil**, 2025-03-18, #random

> Same gap on the metadata side - filtered the stamps by run_id to pull last week's runs and got nothing back for the cached ones, components has "run_id": null.

*What a reader should take from it:* the team agrees cached runs record a null id in their components

*Step it builds toward:* `g4.r2.sc2` — That id defaults to the CURATOR_RUN_ID environment value and otherwise to a freshly generated hex string, both minted at the call site and passed down as a parameter, while a normal cached run carries no id at all.

*Drafted as:* filtered the stamps by run_id to pull last week's runs and got nothing back for the cached ones, the field is null there.

*Why there:* That room is already chewing on the cache quietly failing to record what produced its rows — dermot's point that swapping models just replays the previous model's stored answers with "no warning, nothing to tell you something quietly shifted." Emil has just tied that failure mode to the kluster postmortem he's writing, so a second symptom of the same gap — cached rows carrying no run identity at all, so you can't even query which run they came from — lands as him adding evidence rather than changing the subject. Nobody has made the provenance/metadata point yet; dermot's is about model identity, not the stamped field, and it leaves open whether the null is correct or what non-cached runs stamp there.

*Still leaves open:* whether that null is right, and what the field holds on the other path

*Must appear literally:* `"run_id": null`, `run_id`

*Goes into the real conversation in #random on 2025-03-18, after 11:25 emil:*

```
09:00  gideon: PR 581 is up, just needs a quick review
09:00  gideon: Lost most of yesterday to something unrelated but I'll get back to it this afternoon
09:22  dermot: fyi there's a new claude versoin out this morning, in case anyone's got model names hardcoded anywhere for testing
09:57  gideon: release notes are here if anyone wants the details: https://docs.anthropic.com/en/release-notes/api
10:13  dermot: worth knowing that if anyone's swapping in the new model name against our cached inference, you don't automatically get fresh answers
10:13  dermot: changing the model currently just returns whatever the previous model already stored, no warning, nothing to tell you something quietly shifted
10:43  gideon: for real, ran into exactly that yesterday
11:25  emil: That whole failure mode applies to the postmortem I've been writing up too, we had the kluster issue go silent the same way.   <-- THE REMARK GOES HERE
11:29  gideon: same pattern, silent is the worst kind of wrong
11:29  gideon: Swapped gpt-4o-mini for gpt-4o on the reannotation set yesterday and lost most of the day to it
11:29  gideon: Run finished in nine seconds, summary said everything came off disk, outputs were the mini ones
11:29  gideon: Only notcied because the formatting was too sloppy for 4o
11:49  dermot: that said, gideon caught it because mini is noticeably sloppier
11:49  dermot: not sure we'd spot it if the two models were closer in quality, the silence would just look like a clean run
11:50  dermot: a model mismatch should probably be treated the same as a cache miss
12:28  emil: Loud and wrong beats quiet and wrong every time.
12:39  dermot: yeah
12:39  dermot: I'd rather get an error I can fix than a clean run I have to second-guess
```

#### `g4.r2.l5` — scope

**konrad**, 2025-03-19, #pipeline

> CI job on our side exports CURATOR_RUN_ID=$GITHUB_RUN_ID before the eval sweep now — os.environ.get picks it up and that string is the run_id component, so I can find the direcotry.

*What a reader should take from it:* the team agrees CURATOR_RUN_ID is where the id comes from when the operator sets one

*Step it builds toward:* `g4.r2.sc2` — That id defaults to the CURATOR_RUN_ID environment value and otherwise to a freshly generated hex string, both minted at the call site and passed down as a parameter, while a normal cached run carries no id at all.

*Drafted as:* A CI job now exports CURATOR_RUN_ID=$GITHUB_RUN_ID before the eval sweep so I can find the directory again once it finishes.

*Why there:* No listed room is discussing run identity or where a run's output directory comes from. The releases and code-review threads are release/PR logistics; #engineering 2025-05-29 is ws-069 close-out and #engineering 2026-01-22 is README/cookbook coverage; #viewer 2025-03-27 touches a CURATOR_* flag but is arguing about whether local viewer is being removed, so an env var for locating sweep output would change the subject and draw no response. The remark only lands in a thread where "how do we identify a run" is already the open question — which the corpus doesn't have yet. It should exist: someone loses the output of a finished eval sweep, the team works out that an operator-set id is the answer, and Konrad's CI job is the concrete case that settles the operator half while leaving the unset case and cached runs open for others.

*Still leaves open:* what happens when the variable is not exported, and whether it applies to cached runs too

*Must appear literally:* `$GITHUB_RUN_ID`, `A`, `CURATOR_RUN_ID`, `os.environ.get`, `run_id`

*A new conversation in #pipeline on 2025-03-19:*

```
13:12  dermot: spent ten minutes looking for last nights eval sweep output and couldnt tell which dir was ours. is that id something we set or whatever the harness feels like
13:14  konrad: we set it. the CI job on our side exports CURATOR_RUN_ID=$GITHUB_RUN_ID before the eval sweep now
13:16  emil: this is the sweep on A youre talking about? the ones i was digging through this morning were not that
13:17  konrad: mhm, A
13:19  dermot: exporting it in ci doesnt get me anywhere on its own though, unless something on the other end actually reads the var
13:21  konrad: os.environ.get picks it up, and that string is the run_id component. so i can find the direcotry straight off the build number
13:23  dermot: yeah ok. nothing in our tooling looks it up yet, but at least its sitting there to look up
13:25  emil: yup. beats what i was doing, which was matching timestamps and hoping
```

> **Problems:** longer than one remark

#### `g4.r2.l6` — scope

**nils**, 2025-03-21, #pipeline

> let me think - locally nobody exports it, so llm.py mints uuid.uuid4().hex and hands that down as the run_id argument LLM.__call__ and LLM._run_identity both take.

*What a reader should take from it:* the team agrees the fallback id is a fresh uuid4 hex minted at the call site and passed down

*Step it builds toward:* `g4.r2.sc2` — That id defaults to the CURATOR_RUN_ID environment value and otherwise to a freshly generated hex string, both minted at the call site and passed down as a parameter, while a normal cached run carries no id at all.

*Drafted as:* locally nobody exports anything, so we mint a fresh uuid4 hex up in llm.py and pass it down as an argument.

*Why there:* Neither listed room is chewing on run/cache identity. The 03-19 engineering thread's live design question is specifically how the *api_key* gets passed for Mistral batch, and nils already closes it at 15:34 with the env-variable pattern — dropping a uuid4 hex fallback minted in llm.py there would conflate two different settings and change the subject mid-thread. The 03-24 code-review thread is pure review logistics (who has 583, when emil gets to 584); emil declares 584 clean without any technical back-and-forth, so a design detail from nils would land with no one picking it up, and the sibling remark that supplies the env-supplied case and the argument name lives elsewhere anyway. What's missing is the design conversation itself: emil, having just reviewed PR 584, asks where the id comes from when nothing's set in the environment, and nils gives the either-or — env-supplied on one side, minted locally on the other.

*Still leaves open:* what the environment-supplied case looks like, and what the argument is called

*Must appear literally:* `LLM.__call__`, `LLM._run_identity`, `llm.py`, `run_id`, `uuid.uuid4().hex`, `uuid4`

*A new conversation in #pipeline on 2025-03-21:*

```
13:04  gideon: quick one - what sets the run id when im just running this on my laptop? nothing in my env has it
13:06  dario: i had assumed something upstream handed it in tbh
13:08  nils: let me think - locally nobody exports it. so llm.py mints one itself, uuid4
13:09  gideon: mints it and then what, does it sit on the object or
13:11  nils: no, it gets handed down as the run_id argument. LLM.__call__ takes it and LLM._run_identity takes it too
13:12  gideon: so basically both signatures grow a run_id. and its the hex, not the uuid object?
13:14  nils: uuid.uuid4().hex yes, a plain string the whole way down
13:15  gideon: ya thats clear, i can stop grepping my env for it
```

> **Problems:** longer than one remark

#### `g4.r2.l8` — scope

**dario**, 2025-03-24, #pipeline

> honestly it should stay null for a cache hit - we only reach for an id on the way into the disable_cache branch, a cached run is already pinned by the rest of the components block

*What a reader should take from it:* the team agrees the cached path is meant to carry no id

*Step it builds toward:* `g4.r2.sc2` — That id defaults to the CURATOR_RUN_ID environment value and otherwise to a freshly generated hex string, both minted at the call site and passed down as a parameter, while a normal cached run carries no id at all.

*Drafted as:* it should stay null for those, a cached run is already pinned by everything else in the components block.

*Why there:* No listed room has the question on the table. code-review|2025-04-24 is Dario's own caching-and-resume PR and mentions reattaching by id, but the entire thread is the silently swallowed cache write and the missing warning path — nobody asks what a cache-hit entry carries, so a ruling on a null id in the components block would follow "+1" as a subject change with no reply. viewer|2025-04-28 is about the inspected directory field and whether the executor resolves it at all, a different field and a different open question. The pipeline and releases threads don't touch caching at all. Dario is the right voice for this ruling; there's just no day where it was asked of him.

*Still leaves open:* which runs are not cached and what they carry instead

*Must appear literally:* `disable_cache`

*A new conversation in #pipeline on 2025-03-24:*

```
15:02  gideon: what goes in the id field when we hit cache? the record i pulled back had null there and i cant tell if thats a bug or the point
15:05  dario: honestly it should stay null for a cache hit. thats not a bug
15:07  emil: hm. i had it in my head we stamped one on every run regardless
15:10  dario: only on the way into the disable_cache branch. thats the one place we reach for an id at all
15:12  gideon: ok but then whats pinning the row. two hits in a row would look identical to me
15:15  dario: they dont need one, a cached run is already pinned by the rest of the components block. an id on top of that is just noise
15:17  emil: sounds right, better than making one up. nothing in there enforces it today though
15:19  gideon: ya, i was half way through writing the opposite into my patch
```

> **Problems:** longer than one remark

### g4.r2.sc3 — A cache-off run with no usable id, and a cached run that was given an id anyway, are both refused outright, and the refusal reaches the caller before any run directory has been created.

*Nobody says:* Silently accepting either combination produced the wrong directory rather than no directory, so the only fix that helps is stopping the call, and stopping it early enough that nothing has been written.

*5 remarks — 2 reporting the problem, 3 settling the design.*

#### `g4.r2.l9` — failure_behavior

**gideon**, 2025-04-28, #viewer

> one thing I hit while digging - with cache off, run_id "" and run_id None both piled into the same dir, three jobs, no way to tell them apart.

*What a reader should take from it:* the team agrees an empty id on a cache-off run currently collides runs into one directory

*Step it builds toward:* `g4.r2.sc3` — A cache-off run with no usable id, and a cached run that was given an id anyway, are both refused outright, and the refusal reaches the caller before any run directory has been created.

*Drafted as:* Var was unset in the container so run_id came through as "" and three disable-cache jobs piled into one directory.

*Why there:* That thread is already about run directories being invisible — Gideon opened it asking whether the executor even exposes which directory was inspected, and Dario's 11:32 framing is that "two runs against different paths look identical in the metadata panel." Gideon is the one doing the digging there (he self-answers at 09:29, types "hmm" at 11:06), so a burst reporting what he actually found in the container reads as his. It also lands usefully against Emil's 12:43/14:04 "cheap fix, just add the field" push: if three cache-off runs are genuinely sharing one directory because run_id resolved empty, the panel field alone won't separate them. It stops at the collision and leaves the correct behaviour and the cached-path counterpart to the sibling.

*Still leaves open:* what should have happened instead, and the opposite mix-up on the cached path

*Must appear literally:* `""`, `None`, `run_id`

*Goes into the real conversation in #viewer on 2025-04-28, after 13:14 gideon:*

```
09:00  gideon: Batch update freq fix is basically wrapped up, switching focus to run observability stuff this morning
09:00  gideon: End-of-run summary tables are next on my list
09:00  gideon: @Konrad, heard you pushed two verification runs to compare, what fields is the metadata panel actually showing you?
09:00  gideon: Trying to understand what's missing
09:29  gideon: Ok, answering my own question a bit, I think the panel probably doesn't show which directory was actually inspected. Does the executor even expose tha
10:04  gideon: @Dario, what does the metadata panel pull from currently?
11:06  gideon: hmm
11:31  dario: The panel just reads off whatever the executor reports back, so if the direcory isn't in that object it won't show up
11:32  dario: Once the executor exposes a resolved value for it, @Gideon can you sketch what that field should look like in the metadata panel?
11:32  dario: The executor doesn't include the inspected directory in what it reports back, so two runs against different paths look identical in the metadata panel
11:54  emil: Does the executor actually resolve the path internally and just not include it in what it hands back?
12:43  emil: Assuming it does resolve it internally, the fix is just adding it to what the report object hands back, right?
13:14  gideon: I'll sketch the field for the metadata panel once that value is available on the report object.   <-- THE REMARK GOES HERE
13:48  dario: Honestly I'm not sure the executor resolves the path internally at all - if it doesn't, it's more involved than just surfacing a field. Nikolai would 
13:48  dario: @Nikolai does the executor resolve the inspected directory internally, or is that something it would need to do before it could hand a value back on t
14:03  emil: The report object should carry the inspected directory as a field, same way the end-of-run summary already prints the db path.
14:04  emil: This is a cheap fix for the support loop, that's why I'd rather just add the field than chase the resolve question.
14:04  emil: If the executor needs to resolve it first, how much work is that?
14:36  gideon: at least we're aligned on the report object needing to carry that field, that part's settled
```

#### `g4.r2.l11` — failure_behavior

**dermot**, 2025-05-01, #engineering

> same shape: someone passed a run id on a normal cached run, we ignored it, lost an hour on why the dir was the old one. it should refuse.

*What a reader should take from it:* the team agrees supplying an id on a cached run must be refused rather than ignored

*Step it builds toward:* `g4.r2.sc3` — A cache-off run with no usable id, and a cached run that was given an id anyway, are both refused outright, and the refusal reaches the caller before any run directory has been created.

*Drafted as:* someone passed an id on a normal cached run and we ignored it, then spent an hour wondering why the dir was the old one; it should refuse.

*Why there:* That thread ends with exactly the live question this speaks to: nikolai's non-docker path falls through to an unhandled case when no image tag is configured, and at 12:51 he says he hasn't decided whether it should warn or raise. Dermot is the one who asked the warn-vs-raise question at 12:34, so him answering it with a precedent from the caching side — an input that got silently ignored and cost an hour of confusion — lands as him arguing the case rather than changing the subject. It states the settled position ("it should refuse") without touching the missing-id direction or spelling out where the refusal has to live, which the sibling remark covers.

*Still leaves open:* the reverse case where the id is missing, and where the refusal has to come out

*Goes into the real conversation in #engineering on 2025-05-01, after 12:51 nikolai:*

```
09:00  dermot: been in release config this morning
09:00  dermot: I want to flag something about how we're picking the executor image default before end of day
09:44  nikolai: same, I've been looking at what's still unresolved in code-execution before we cut anything
09:44  nikolai: I've got the open items in code-execution mostly mapped out, just working through what actually needs to block a release versus what can follow on aft
10:17  dermot: @Nikolai Berresford what's the plan for the executor image default, has that tag been decided yet?
10:35  nikolai: Not decided yet, that's one of the things I'm trying to nail down before we cut a release. I've got a list of what's still open on my end but the tag 
10:37  dario: fair enough
10:37  dario: - *bulk-llm-inference*: mostly stable, tidying up a few edge cases around request batching
- *caching-and-resume*: resume logic is solid, just want to
11:19  dermot: gotcha
11:19  dermot: while that's still open, whatever we bake in as the default has to be a build somebody actually signed off, not just the newest thing out of CI green
11:20  dermot: we've shipped a container before that nobody had run the verifier suite against, I'd rather not repeat that
11:31  nikolai: @Dermot Callaghan when you say signed off, you mean a specific pinned digest, not just a tagged release?
11:32  dermot: not quite. I was thinking about whether someone ran the verifier on that build, not specifically about digest pinning. I'm not sure those are the same
11:42  dario: honestly I'd lean toward both mattering, but are those actually separate gates or do we want one check that covers both?
12:09  nikolai: Separately, the non-docker path in code-execution is erroring on startup if no image tag is configured, it's not a graceful fallback, just blows up
12:34  dermot: @Nikolai is that blow-up on the non-docker path intentional, or should it be warning instead of hard erroring?
12:51  nikolai: Not intentional, it just falls through to an unhandled case. I dunno if it should warn or raise, that's actually the bit I haven't decided yet.   <-- THE REMARK GOES HERE
```

#### `g4.r2.say19` — failure_behavior

**dario**, 2025-05-02, #releases

> to be honest on dermot's one: cache_enabled True with any run_id that isn't None — "" counts — is a RunIdentityError, we don't get to guess which dir they meant

*What a reader should take from it:* the team agrees a cached run refuses any run_id that is not None, empty string included

*Step it builds toward:* `g4.r2.sc3` — A cache-off run with no usable id, and a cached run that was given an id anyway, are both refused outright, and the refusal reaches the caller before any run directory has been created.

*Drafted as:* on dermot's one: cache_enabled True with any run_id that isn't None — "" counts — is a RunIdentityError. we don't get to guess which dir they meant.

*Why there:* Neither listed room is chewing on run identity. #cookbooks 2025-05-05 is auth docs and grepping `.choices` out of examples-cookbooks; Dermot's live question there is which cookbooks need response-object updates, so a caching rule arrives from nowhere and nobody would answer it. #pipeline 2025-04-29 is the right people but the wrong day: every thread is unanswered scope questions aimed at Nikolai and Tomas, Dermot isn't present so "on dermot's one" has no referent, and dario's own 11:50 message says caching-and-resume is still unvalidated for him — handing down a settled RunIdentityError rule hours later reads as two different conversations. The remark needs a room where Dermot has actually put the question on the table.

*Still leaves open:* says nothing about what happens with the cache off, nor about where in the call the refusal is raised relative to the run directory being created

*Must appear literally:* `cache_enabled`, `run_id`, `None`, `""`, `RunIdentityError`

*A new conversation in #releases on 2025-05-02:*

```
14:17  dermot: one thing before the cut, unrelated to 643. cache_enabled true and a run_id handed in at the same time — today it just picks one and carries on
14:20  nikolai: picks which
14:21  dermot: thats sort of the problem, i couldnt tell you without reading the branch
14:25  dario: then it shouldnt be picking at all, honestly. cache_enabled true with a run_id thats not None is a RunIdentityError
14:28  dermot: and the ones that come through with run_id as empty string? we get a fair few of those
14:31  dario: "" counts. its not None, so same thing — we dont get to guess which dir they meant
14:33  nikolai: mhm, better than silently landing somewhere
14:35  dermot: yeah ok. one caller in the smoke path was passing both, thats how i noticed at all
```

#### `g4.r2.l10` — failure_behavior

**konrad**, 2025-05-06, #incidents

> Look, our CI wrapper passes os.environ.get("CURATOR_RUN_ID") straight in as run_id and nothing was exported, so the disable-cache sweep came back RunIdentityError. Exported it, three dirs.

*What a reader should take from it:* the team agrees a missing or empty id on a cache-off run must be an error

*Step it builds toward:* `g4.r2.sc3` — A cache-off run with no usable id, and a cached run that was given an id anyway, are both refused outright, and the refusal reaches the caller before any run directory has been created.

*Drafted as:* That should have stopped at the door with an error rather than quietly sharing a dir between three jobs.

*Why there:* None of the eight rooms is anywhere near this. The two #cookbooks days are about example freshness, live-API verification and CI wiring; the three #code-review days are PR queue triage, model identifier strings and wind-down bookkeeping; #viewer 2025-06-03 is the closest in shape (a guard, a None value, a display that breaks) but it is specifically about pricing lookup and cost rendering, and Konrad has already closed his side of it — dropping a cache-directory collision in there would change the subject and get no reaction. Nobody in any of these conversations has mentioned caching, run ids, or run working directories at all, so a verdict that "no id plus cache off must error" would be the first and only mention of the entire subsystem, arriving as a conclusion with no discussion behind it. What should have existed is the day someone noticed three concurrent runs writing into the same cache dir because the run id was empty and caching was switched off — Konrad reacting to that finding is exactly where this line lands, and it leaves the sibling question (which id/cache combinations are bad, and whether the error comes from the CLI or deeper in) still open for someone else.

*Still leaves open:* which combinations count as bad, and where the error has to surface

*Must appear literally:* `""`, `None`, `RunIdentityError`, `os.environ.get("CURATOR_RUN_ID")`, `run_id`

*A new conversation in #incidents on 2025-05-06:*

```
14:02  gideon: ok what is RunIdentityError. the whole disable-cache sweep came back with that and basically nothing ran
14:04  konrad: which wrapper did you launch it from, the CI one?
14:05  gideon: ya the CI one
14:07  konrad: right, thats it then. it does os.environ.get("CURATOR_RUN_ID") and passes that straight in as run_id. no default, no check
14:08  nikolai: so what was actually in the env
14:09  konrad: nothing. it was never exported in that job so what goes in is None
14:11  gideon: hm i thought get would hand you "" there? or is that only um, if someone sets it empty
14:13  konrad: only if someone sets it empty, yes. here nobody set it at all. anyway i exported it and reran, three dirs
```

> **Problems:** longer than one remark; claims verbatim '""' but does not contain it; claims verbatim 'None' but does not contain it

#### `g4.r2.l12` — failure_behavior, scope

**nikolai**, 2025-06-03, #engineering

> check moved ahead of run dir creation - compute_run_identity refuses an id on a cached run, and refuses cache off with run_id None or "". LLM.__call__ is where the default gets minted - CURATOR_RUN_ID when it is set, otherwise a fresh uuid4 - and it passes that down as the run_id argument, so the only refusal that ever surfaces out of __call__ is the cached-run one. nothing left on disk either way.

*What a reader should take from it:* the team agrees the refusal surfaces from __call__ and happens before the run directory exists

*Step it builds toward:* `g4.r2.sc3` — A cache-off run with no usable id, and a cached run that was given an id anyway, are both refused outright, and the refusal reaches the caller before any run directory has been created.

*Drafted as:* The refusal needs to reach the caller out of __call__; right now it fires after the dir is made and i am sweeping up empty stamped dirs.

*Why there:* That room spends the day on where the code-execution guard actually fires — Konrad asks at 09:49 whether it falls back cleanly or just skips the import, Emil asks at 12:10 whether it covers calls further down the stack, and at 16:49 Nikolai says he's extending it past the import himself. A note on where the refusal has to surface from, and the empty stamped dirs he's cleaning up while doing it, is the implementation detail that work turns up, and it settles Konrad's morning question (it raises to the caller, it doesn't fall back) without saying which cases get refused.

*Still leaves open:* which situations are refused in the first place

*Must appear literally:* `LLM.__call__`, `The`, `__call__`

*Goes into the real conversation in #engineering on 2025-06-03, after 16:49 nikolai:*

```
09:00  konrad: Cost-safety fix on the finetuning side is in, and I want to make sure we're aligned on the safeguard approach before anything else moves forward today
09:00  konrad: Happy to walk through it with whoever has eyes on the broader dormancy plan
09:18  nikolai: PR 663 is my piece of that picture on the code-execution side, torch safety fix, and I want it in before we call dormancy locked
09:49  konrad: Nikolai, what does the fix actually do when torch isn't present, does it fall back cleanly or just skip the import?
10:08  nikolai: Around this morning if you want to walk through it together rather than back-and-forth in comments
10:34  konrad: Quick call or just a thread where we can drop code?
11:03  nikolai: call works
12:10  emil: Does PR 663 guard just the import, or does it also cover any torch calls further down the stack?
12:50  emil: PR 683's litellm structured-output detection hasn't been validated against actual provider responses, and it's sitting without a reviewer.
13:17  konrad: @Emil, for PR 683, what would a validation against actual provider responses actually look like?
13:18  konrad: Is there a test setup already or would someone need to wire one up?
13:33  konrad: Are we aligned that guarding at the pricing lookup is enough, or does the viewer need its own layer on top?
14:02  konrad: Nikolai, did anything come up from the call that changes the picture on PR 663?
14:18  nikolai: That provider-validation gap in PR 683 is a real find, @Emil, that's exactly the kind of thing that bites you on a provider you haven't tested against
15:01  emil: Which providers are you thinking, the ones litellm supports but we haven't actually run against, or something more specific?
15:09  emil: Has anyone actually run the litellm structured-output detection in PR 683 against a real provider response, or is it untested so far?
15:37  nikolai: The guard in PR 663 only covers the import
15:52  emil: @Dario, you own code-execution, worth a look at whether the torch guard in PR 663 needs to extend past the import before it merges.
16:22  emil: Anyone know why the litellm structured-output check in PR 683 would return inconsistent results on the same provider across runs?
16:49  nikolai: That's my subsystem, not Dario's - I already surfaced the guard gap on 663 and I'm extending it past the import now   <-- THE REMARK GOES HERE
17:13  konrad: With 663's guard getting extended and 683 still unresolved, are we actually able to call all three fixes safe today, or is that slipping?
17:48  nikolai: Guard extension on PR 663 is done and I've pushed the update, so that one's ready for eyes when someone has a chance.
18:09  emil: If PR 683 isn't getting reviewed today, we could at least mark it explicitly as post-dormancy so it's not just floating.
18:09  emil: PR 683 is open and unreviewed, calling it explicitly post-dormancy for now, will pick it back up after the milestone.
18:18  konrad: Cost fix on my end is solid, the guard on the pricing lookup is in and unknown models return None cleanly
18:19  konrad: With 663's guard now extended and 683 explicitly deferred, the two active fixes look sound to me
18:19  nikolai: 663 is updated but nobody's actually reviewed the extension yet, dunno if "sound" is quite the right word before that happens.
18:19  emil: Right, "sound" and "reviewed" are two different things.
18:19  emil: Someone should take a look at the updated PR 663 before we call torch safety confirmed, Nikolai pushed the guard extension and it needs actual eyes on
```

> **Problems:** longer than one remark

### g4.r2.sc4 — A cache-off identity is marked out by its own hash prefix, is byte-for-byte reproducible from the same id and different for a different id, and the module computing it holds no source of randomness.

*Nobody says:* A hash that is stable across processes can only be a function of its inputs, so anything that would vary per process cannot live inside the code that produces it.

*3 remarks — 1 reporting the problem, 2 settling the design.*

#### `g4.r2.l13` — observability

**gideon**, 2025-04-03, #viewer

> same row identity problem in the other direction tbh - v3-nocache-9f2b1c0ad4e5f678 beside the plain v3- dirs, always 27 chars, prefix plus 16 hex, and nothing says which run.

*What a reader should take from it:* the team agrees a cache-off run hash carries its own prefix ahead of the digest

*Step it builds toward:* `g4.r2.sc4` — A cache-off identity is marked out by its own hash prefix, is byte-for-byte reproducible from the same id and different for a different id, and the module computing it holds no source of randomness.

*Drafted as:* Viewer is showing v3-nocache-9f2b1c0ad4e5f678 beside the plain v3- dirs and nothing on the row tells me which run that was.

*Why there:* That room is already stuck on viewer rows that don't identify the run behind them — Gideon spent the morning on two dashboard entries with identical request counts he couldn't tell apart, and he and Emil have just agreed to spec what the viewer should show when reattach lands. A second row-identity case, where a cache-off run dir sits next to the plain ones and the row still says nothing, feeds that spec conversation rather than starting a new one, and Gideon is the one carrying the viewer complaints that day. Nothing said so far covers directory naming, so it isn't redundant; the naming convention itself (nocache prefix ahead of the digest) is stated as an existing fact, leaving the id-reproducibility and tail question untouched.

*Still leaves open:* whether the same id reproduces that string, and where the tail comes from

*Must appear literally:* `16`, `27`, `v3-`, `v3-nocache-9f2b1c0ad4e5f678`

*Goes into the real conversation in #viewer on 2025-04-03, after 11:46 emil:*

```
09:00  gideon: PR 600 is almost ready, just finishing up the edge case where the env var gets read before the logger initializes
09:00  gideon: Should have it up for review this morning
09:00  gideon: Has anyone run into duplicate jobs showing up on the dashboard?
09:41  gideon: Answering my own Q - traced it
09:41  gideon: User ctrl-c'd while the first status line was still printing, restarted beofre we heard anything back from the provider
09:41  gideon: Two jobs on the same account, four minutes apart, identical request counts
10:13  gideon: I think restarts in the gap is the explanation - that window is maybe 90 seconds right after the first submission, before we hear back from the provid
11:13  gideon: Should we try to address this in the progress code or just wait for the reattach to land first?
11:13  gideon: I'm not sure a patch there makes sense before that's in
11:15  emil: Want to grab 15 min this afternoon to talk through what the viewer should show when reattach lands?
11:16  emil: Makes sense to spec that before the code gets there
11:29  gideon: I'm free this afternoon, though not sure how much of the viewer state we can nail down before the reattach shape is clearer
11:29  gideon: Is the idea just to sketch it loosely?
11:29  gideon: Are we calling it restarts-in-the-gap, or does someone have a different theory on the duplicates?
11:45  emil: Restarts-in-the-gap tracks for me. Seeing the same pattern in the submission log:

```
[10:42:11] submitted batch job a1b2c3 (n=500)
[10:46:04] submit
11:46  emil: What does the progress display currently show if you reconnect to a run that's already mid-flight?   <-- THE REMARK GOES HERE
```

#### `g4.r2.l15` — observability, scope

**emil**, 2025-04-11, #incidents

> grepped run_identity.py again after the merge - no random, no secrets, no uuid, no os.urandom in that module, not even an import; the only uuid import left is llm.py.

*What a reader should take from it:* the team agrees the identity module contains no randomness of its own

*Step it builds toward:* `g4.r2.sc4` — A cache-off identity is marked out by its own hash prefix, is byte-for-byte reproducible from the same id and different for a different id, and the module computing it holds no source of randomness.

*Drafted as:* grepped run_identity.py for random and uuid again after the merge, still nothing in there; the day either shows up we lose reproducibility.

*Why there:* None of the listed rooms is debugging anything — they're all review-queue status threads (PR 652/653/663/675/681/683/690/691, release gating) plus one release-announcement day in #incidents. The remark reports a second grep after a merge, which presupposes a live hunt for a source of nondeterminism in run identity; nothing in any candidate day has opened that hunt, so it would arrive from nowhere and draw no reply. The closest adjacency, Dermot's caching-and-resume partial-write question on 2025-04-25, is about viewer download behavior against a half-written dataset, not about what makes a run's identity vary between runs. What should have existed is a short investigation thread the day someone noticed identical inputs re-running instead of hitting cache: Emil reporting that the identity module itself is clean, and someone else (Dermot, who owns the caching-and-resume side) supplying where the varying value actually comes from and what it's called.

*Still leaves open:* where the varying value is produced instead, and what it is called

*Must appear literally:* `llm.py`, `os.urandom`, `random`, `run_identity.py`, `secrets`, `uuid`

*A new conversation in #incidents on 2025-04-11:*

```
13:38  konrad: anyone been back through run_identity.py since the merge landed?
13:39  emil: yup, i grepped it again after. no random, no secrets in that module
13:41  konrad: and uuid? thats the one that got us last time
13:42  emil: no uuid, no os.urandom either. not even an import sitting there unused, honestly i expected to find one
13:44  dermot: so where does uuid live now, we definitely still pull it in somewhere
13:45  emil: llm.py. thats the only import of it left
13:46  dermot: mhm. nobody has actually written anything against that yet though
13:47  konrad: right, and llm.py is off the identity path anyway, so its the one file to keep clear
```

> **Problems:** longer than one remark

#### `g4.r2.l14` — observability

**dario**, 2025-04-15, #pipeline

> ran it twice with the same id and the two stamps diff clean, then changed one character of the id and got a different dir, which is what we want

*What a reader should take from it:* the team agrees identical ids give byte-equal identities and different ids give different ones

*Step it builds toward:* `g4.r2.sc4` — A cache-off identity is marked out by its own hash prefix, is byte-for-byte reproducible from the same id and different for a different id, and the module computing it holds no source of randomness.

*Drafted as:* ran it twice with the same id and the two stamps diff clean, changed one character of the id and got a different dir, which is what we want.

*Why there:* No listed room is chewing on cache identity determinism. code-review|2025-03-31 is about whether the cache dir gets created at all and how to name the bypass param — ids, stamps and per-id dirs would all be new nouns there. pipeline|2025-03-26 touches cache key computation but settles it by 12:41 and spends the rest of the day on Mistral usage extraction; a determinism result would answer a closed question. viewer|2025-04-14 hands Dario the caching fix but ends with him just starting it that evening, so a verification result can't yet exist. The conversation that should have existed is the next-day follow-up on that handoff, where the fix lands as a per-run cache identity and Dario reports the checks he ran on it.

*Still leaves open:* what the dir name looks like, and where the id comes from

*A new conversation in #pipeline on 2025-04-15:*

```
15:44  dermot: the cache dir naming - has anyone actually confirmed the same id gives you the same dir twice, or are we still assuming that
15:46  dario: i poked at it this morning actually. ran it twice with the same id and the two stamps diff clean
15:47  gideon: ok but what about two ids that are nearly the same? thats the case i dunno about tbh
15:49  dario: did that too. changed one character of the id and got a different dir, which is what we want
15:50  gideon: ya exactly, that was the part worrying me
15:52  dermot: and none of this is in the code yet, if i had to guess
15:53  dario: no, all by hand at a shell. still has to be written properly
15:55  dermot: mhm. that would explain the two dirs i found monday, i couldnt work out what was different between them
```

### Herrings — believed at the time, overturned later

#### `g4.r2.h1-uuid4-nocache` — herring

**dario**, 2025-02-12, #code-review

> on normalize-before-hashing — settled in review that the nocache path doesn't hash at all, compute_run_identity mints a uuid4 under `if disable_cache:`, nothing to collide with or look up

*A herring: stated as settled at the time, overturned later (from 2025-03-17).*

*Drafted as:* settled it in review: the nocache branch mints a uuid4 inside compute_run_identity, guarded by `if disable_cache:` — nothing to collide with, nothing to look up.

*Why there:* Gideon raises the pickler postmortem's normalize-before-hashing action item twice that day (10:33–10:34 and again 14:45–14:46) as sitting unfiled in caching-and-resume territory, and nobody engages with the substance. Dario is active in the thread all afternoon and has an established habit of dropping a settled decision into #code-review when the doc for it isn't up (cf. his ValueError note on 03-04). Scoping the hashing item — the disabled-cache path never hashes because compute_run_identity mints a uuid4 under `if disable_cache:` — contributes to that live thread rather than opening a new one, and nothing already said covers it. The one strain is that no caching PR under review is named that day, so "settled in review" is slightly free-floating.

*Goes into the real conversation in #code-review on 2025-02-12, after 14:46 gideon:*

```
09:00  gideon: - *PR 493* (progress bar revamp) is up and ready for review
- touches progress-and-cli only, no release blocker but want it in today
09:03  gideon: Anyone free to take a look at PR 493 this morning?
09:14  dermot: pr 490 and 491 are both sitting without reviewers, I want those through today so they're in good shape to land tomorrow.
09:49  gideon: What subsystems do 490 and 491 touch?
09:50  gideon: oh wait
09:50  gideon: 490 is ratelimit/togetherai so that's online-request-processing, I can take that
09:50  gideon: What does 491 touch?
10:17  nikolai: 491 is curator/client, so that's Dario's side.
10:33  gideon: Pulled up the pickler postmortem just now
10:34  gideon: The normalize-before-hashing action item is in caching-and-resume territory so that's mine
10:34  gideon: Has Emil filed anything for that yet, or is it still just sitting in the doc?
11:09  konrad: Not sure on the Emil issue, I'd just ping him directly.
11:55  dario: Also, PR 468 has been sitting five days now
11:55  dario: Honestly not sure whether we push to land it or just close it given issue 52 is still open and the scope around multi-sample hasn't really settled
12:18  emil: On PR 468, I'm leaning toward just closing it, issue 52 is still too unsettled and keeping a five-day-old PR open against a moving scope doesn't make 
12:18  emil: PR 491 still needs a reviewer if anyone can take a look this afternoon, I want both 490 and 491 in a position to land tomorrow
12:36  emil: PR 490 has Gideon on it now, PR 491 still needs a reviewer, want that one covered today so both can land tomorrow
12:36  emil: Also, the request-processing handover doc still isn't on the wiki, so I'm a bit in the dark on that side until Dario gets it up
12:39  dermot: anyone free to take pr 491 this afternoon?
13:15  emil: @Dermot, PR 491 is yours if you want it, curator/client, no release blocker but I need it reviewed today to land tomorrow.
13:15  emil: Also, the request-processing handover doc from Dario still isn't on the wiki, I checked and it's not there yet, so that piece is still on him.
13:18  gideon: PR 493 still hasn't had a reviewer since I posted it this morning
13:18  gideon: Anyone free this afternoon?
13:18  gideon: Have PR 496 coming up that needs eyes before end of day too.
13:58  dario: That handover doc is further from done than "mostly drafted" implied, the resume sections in particular are taking more time than I expected.
13:59  dario: So close PR 468, get someone on PR 493 and PR 496 to merge today, and then 490 and 491 are both pending review to land tomorrow.
13:59  gideon: someone's actually picking up 493 and 496 today?
13:59  gideon: If nobody's on PR 493 yet, I need a reviewer this afternoon, progress-and-cli, not blocking a release
14:02  dermot: I'll take pr 491 and pr 493.
14:11  dario: PR 496 still needs someone, does that land today or do we push it?
14:45  gideon: Pulled up the pickler postmortem earlier, the normalize-before-hashing action item falls in caching-and-resume, which is mine, but nothing's been file
14:46  gideon: It's sitting in the doc without a PR or issue yet
14:46  gideon: Dermot on PR 493, that one's been waiting all day, glad it's moving.   <-- THE REMARK GOES HERE
15:29  emil: Closing PR 468, Dario's call makes sense and I was already leaning that way. PR 490 has Gideon and PR 491 has Dermot, so both should be in good shape 
15:31  gideon: PR 490 review is done on my end, ready to land tomorrow.
15:59  dario: @Dermot where are you on PR 496?
16:37  dermot: I've got 491 and 493, didn't take 496
17:17  dario: @Gideon is PR 496 yours, do you have anyone on it?
17:37  gideon: Yeah 496 is mine, still no reviewer on it.
17:37  gideon: 493 getting done is the good news today at least.
17:38  dario: What subsystem does it touch?
17:43  gideon: progress-and-cli, same area as 493
18:08  dario: Honestly not sure that one makes it today then, that's pretty late to be picking up a new review.
18:08  gideon: i think it's a pretty quick review though, same subsystem as 493 which Dermot just went through
18:08  dermot: not sure same subsystem means same complexity though
18:19  dario: fair, Dermot's point stands
```

#### `g4.r2.h2-isoformat-segment` — herring

**konrad**, 2025-01-22, #cookbooks

> Replaced the uuid4 in the disable_cache path with a datetime.now().isoformat() segment, so the nocache run dirs sort chronologically on disk now. Much easier to eyeball.

*A herring: stated as settled at the time, overturned later (from 2025-03-17).*

*Drafted as:* Replaced the uuid4 in the disable_cache path with a datetime.now().isoformat() segment, so the nocache run dirs sort chronologically on disk. Much easier to eyeball.

*Why there:* Nothing in the listed rooms is chewing on run-directory identity or the disable_cache path. The closest hook is #code-review 2025-02-17, where Konrad's weekly flags "unexplained cache churn" — but that thread is squarely about Emil's pickler regression and about PRs 495/502/468 waiting on reviewers, and a note that Konrad had swapped uuid4 for a timestamp in the nocache run dirs would land as a subject change nobody answers. The other candidates are multimodal mime types, the post4 hotfix, cookbook recipe checks, the docker sandbox uid, and cost/1n token fields — none of them touch caching at all. What should have existed is a short thread a couple of days after the cache-churn flag, where the cache-identity work gets picked up properly: Konrad reporting what he changed in the disable_cache path, Emil confirming it doesn't interact with the pickler fingerprint fix he still owes a PR for, and Gideon asking whether the nocache dirs are ever collected or just accumulate.

*A new conversation in #cookbooks on 2025-01-22:*

```
15:26  dario: the nocache run dirs, is there an order to them or is it just random. i cant find the one i ran twenty minutes ago
15:29  konrad: its the uuid4 in the disable_cache path. thats coming out, its doing nothing for us
15:30  dario: out and replaced with what though, the dir still needs a name on it
15:32  konrad: datetime.now().isoformat() goes in as that segment instead
15:34  dermot: so the nocache dirs come out sorted chronologically on disk then, just from the name
15:36  konrad: right. much easier to eyeball, thats the whole reason anyway
15:38  nikolai: yep the uuid only ever told me two runs were different never which one came first
```

#### `g4.r2.rev1` — rule

**dario**, 2025-03-31, #code-review

> dropped the uuid4 in compute_run_identity's `if disable_cache:` branch — reruns kept landing in new dirs. keyword-only run_id: Optional[str] = None now, stored as the run_id component when cache_enabled is False

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* dropped the uuid4 in compute_run_identity's `if disable_cache:` branch — every rerun of the same sweep landed in a new dir and ci could never re-attach. it takes a keyword-only run_id now, stored as the run_id component when cache_enabled is False.

*Why there:* That room is already on dario's PR 565 revision with its "bypass option", and on cache identity failing in a fresh CI container — dermot asked about the new revision, dario complained about CI never having a cache dir, emil is pushing on what the bypass param means. A note that the disable-cache branch stopped minting a uuid4 per run and now takes a caller-supplied run_id lands directly on both threads (it's why CI could never re-attach), comes from the person who owns that branch, and doesn't duplicate the mkdir/naming points anyone has already made.

*Must appear literally:* `False`, `cache_enabled`, `compute_run_identity`, `disable_cache`, `if disable_cache:`, `run_id`, `run_id: Optional[str] = None`, `uuid4`

*Goes into the real conversation in #code-review on 2025-03-31, after 12:54 emil:*

```
09:00  dermot: pr 565 and the openai client work are in decent shape, I've got the retry logic in pr 585 under review and a few questions on the simplestrat recipe i
09:00  dermot: @Dario Kestrel did you push a new revision to pr 565 over the weekend, I'm seeing something about a moved hook and a bypass option?
09:38  dermot: @Emil Brandvold have you had a look at the latest on pr 565 yet?
09:56  dermot: does the cache directory get created automatically or does it need to exist first?
10:20  dermot: in pr 598, is the simplestrat recipe intended to replace the existing strategy or does it sit alongside?
10:50  dermot: for pr 583, if the metadata db param is disabled does it skip schema init entirely or just skip writes?
11:18  emil: not yet, pulling it up now
11:51  dario: It needs to exist first, and that's actually the thing I wanted to flag
11:51  dario: Fresh CI container, nothing has ever run in it, pre-flight estimate step threw a FileNotFoundError on the cache dir
11:51  dario: I put a mkdir -p in the workflow to unblock it, but I hate that because now the estimate step is the thing that creates the cache Second time this mon
12:34  emil: The mkdir in the workflow is the wrong home for that, if the code expects a cache dir it should create it on first use, not lean on whatever CI step h
12:54  emil: Looked at the revision, moving the hook I can live with, but I'm less sure about the bypass
12:54  emil: Whatever we name that param is going to tell users a lot about when they're supposed to use it, and right now it doesn't   <-- THE REMARK GOES HERE
14:07  dario: @Emil Brandvold do you want to land on the bypass naming before this closes today, or leave it open?
14:17  emil: I'll land on it today, give me a bit to look at the options and I'll have something by end of afternoon.
14:35  dario: Worth thinking about whether the name signals "for debugging" vs "a legitimate production option" - those would probably land differently for users
15:07  dario: Fixing the cache dir creation at the code level and landing the bypass naming in the same pass would be cleaner than two separate PRs.
```

#### `g4.r2.rev2` — rule, observability

**konrad**, 2025-03-24, #cookbooks

> My datetime.now().isoformat() segment in the disable_cache path is gone - two sweeps, two dirs. run_hash is v3-nocache- plus a digest of the whole components block, run_id just one entry.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* My datetime.now().isoformat() segment in the disable_cache path is gone — sorted nicely but two identical sweeps still got two dirs. run_hash is now v3-nocache- plus a digest of the caller's run_id, so a replay lands in the same dir.

*Why there:* None of the listed rooms is anywhere near cache identity. The two #code-review days are about PR 594/595 (gemini unicode), PR 604 (prompt/parse shape) and the stale queue; the #engineering days are the null-value fix and the OpenAI-compatible response shape; the release and viewer days are tagging and a version tag rendering. Nothing in any of them mentions caching, run directories, or disable_cache, and in all of them Konrad is either reviewing somebody else's PR or chasing status — never reporting that a line of his own was replaced. Dropping "two identical sweeps got two dirs" into any of those changes the subject and would sit there unanswered. What this needs is the review thread where someone caught that disable_cache runs were keyed on wall-clock time, so a re-run of the same sweep never landed on its predecessor; Konrad's line is his reply after cutting the timestamp segment out.

*Must appear literally:* `datetime.now().isoformat()`, `disable_cache`, `run_hash`, `run_id`, `v3-nocache-`

*A new conversation in #cookbooks on 2025-03-24:*

```
15:12  nikolai: ran the nocache sweep twice on the same config today and got two dirs out of it
15:13  nikolai: identical inputs so i dont know what im comparing
15:18  konrad: right thats the timestamp. we swapped the uuid4 in the disable_cache path for a datetime.now().isoformat() segment a while back so the nocache dirs would sort chronologically, easier to eyeball. its gone, it made every run unique to itself, which is exactly your two sweeps two dirs
15:20  nikolai: so whats naming the dir instead
15:24  konrad: run_hash. v3-nocache- and then a digest of the whole components block
15:25  nikolai: whole block including run_id though right that moves every time
15:29  konrad: run_id goes in as one entry, thats all it is. nothing in there varies per run anymore so the two sweeps land in the one dir
15:34  emil: sounds right. i have a shell alias that sorts those by name, guess i can retire it
```

> **Problems:** longer than one remark

