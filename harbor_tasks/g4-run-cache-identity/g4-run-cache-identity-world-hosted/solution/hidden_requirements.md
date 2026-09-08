# g4 — Versioned run identity for the curator cache

**This is the answer key.** Nothing here is shown to an agent in any arm. The `blind` and `world` arms get the ticket and nothing else; `spec` also gets the hidden requirements; `clues` gets the remarks quoted in its prompt but never their dates' meaning, who is wrong, or which fact anything carries; `located` gets the same world as `world` plus a map of where each remark sits, but never a quote, never which requirement a conversation serves, and never which are herrings.

| arm | what it is handed | measured |
|---|---|---|
| `blind` | the ticket | — |
| `spec` | the ticket + both hidden requirements | — |
| `clues` | the ticket + all 48 remarks, quoted | **1.00** |
| `world` | the ticket, against `sweworld:0.4.4` where the 48 remarks live in chat — this task has no wiki or mail carriers | — |
| `located` | the `world` arm plus a map naming each remark's channel, day, minute and length (or its page, or its mail subject) — the search removed, the inference left | **1.00** |

Scores are per run and live with the run, not here.

---

## The hidden requirements — stated nowhere

Two requirements, `g4.r1` and `g4.r2`. Neither is written down anywhere an agent
can read: they have to be reassembled from remarks scattered across the world.

**Eight facts, not ten.** `g4.r1` has no `failure_behavior`; `g4.r2` has no
`exclusions_or_crossover`. `score.py` takes its keys from `tasks.json` rather than
from a fixed list of five, precisely so an absent fact is not invented and does not
divide the mean by the wrong number, so each of the eight is worth one eighth.
`open_feature` (did the agent build the feature at all?) carries weight **0.0**:
building the feature scores nothing, only recovering what nobody wrote down does.

The facts, and the question each one answers:

| fact | the question it answers |
|---|---|
| `rule` | what exactly has to exist |
| `scope` | where it applies, and where it must not |
| `exclusions_or_crossover` | what has to stay untouched |
| `failure_behavior` | what happens when it goes wrong |
| `observability` | the exact values a test can read back |

---

### `g4.r1` — twelve components decide the cache key, and only four backend params count

**In one sentence:** the run's identity is a digest over exactly twelve named
components, and of everything in `backend_params` only four keys are allowed to
fork the cache — so rotating an API key or nudging `max_retries` must not mint a
new cache directory.

#### `rule` — what has to exist

`IDENTITY_COMPONENT_KEYS: tuple[str, ...]` is exported in **alphabetical order**,
twelve keys:

```python
("backend", "backend_params", "batch_mode", "dataset_hash", "generation_params",
 "model_name", "parse_func_hash", "prompt_func_hash", "response_format",
 "return_completions_object", "run_id", "system_prompt")
```

Four of them are easy to get wrong:

| component | how it is built |
|---|---|
| `parse_func_hash` | `_get_function_hash(llm.prompt_formatter.parse_func)` — exactly as the prompt function does |
| `generation_params` | always carried, `dict(... or {})` |
| `response_format` | `json.dumps(rf.model_json_schema(), sort_keys=True, separators=(",", ":"))`, or the literal `"text"` when it is `None` |
| `system_prompt`, `return_completions_object` | participate — they are not incidental |

#### `scope` — resolved, not requested

- `backend` is the **resolved** backend name read off `llm.backend`, which is
  `self._request_processor.backend` — not whatever the caller passed.
- `LLM.backend_params` is a copy of the dict handed to `__init__`, and `{}` when
  it was `None`.

#### `exclusions_or_crossover` — the four keys, and the ones that must not count

`backend_params` is filtered to exactly:

```python
IDENTITY_BACKEND_PARAM_KEYS: frozenset[str] = frozenset(
    {"azure_deployment", "base_url", "batch_size", "completion_window"})
```

Every other backend param **is not identity and must not fork the cache
directory** — `max_retries`, `request_timeout`, `require_all_responses`,
`batch_check_interval`, `seconds_to_pause_on_rate_limit`,
`max_requests_per_minute`, `delete_successful_batch_files`, and `api_key`.

#### `failure_behavior` — not declared

This requirement has no `failure_behavior` fact. Nothing to implement, and nothing
scored here.

#### `observability` — exact values

For a stub with
`backend_params={"base_url": "https://x/v1", "max_retries": 7, "api_key": "sk-secret", "request_timeout": 30}`:

| check | expected |
|---|---|
| `tuple(sorted(compute_run_identity(S, "d0").components))` | `== IDENTITY_COMPONENT_KEYS`, `len == 12` |
| `.components["backend_params"]` | `{"base_url": "https://x/v1"}` |
| the string `"sk-secret"` | occurs **nowhere** in the serialised components or in the written `run_identity.json` |
| `run_hash` vs a stub differing only in `api_key`, `max_retries`, `request_timeout` | **byte-equal** |
| `run_hash` when only the parse function, only `system_prompt`, only `return_completions_object`, or only the resolved backend differs | **differs** |
| `LLM(model_name="gpt-4o-mini")` vs `LLM(model_name="gpt-4o-mini", backend="openai")` | same `run_hash` |

> **The herring** — what the team decided first and later reversed: an earlier
> build hashed the whole `backend_params` dict (mirroring the
> `sorted(generation_params.items())` line already in `llm.py`); it was reversed
> after every `api_key` rotation and every `max_retries` tweak minted a fresh cache
> directory, and after the cleartext `api_key` was noticed in a stamp file on a
> shared box.

---

### `g4.r2` — a cache-disabled run takes its id from the caller, never from a fresh uuid

**In one sentence:** turning the cache off must not make a run unrepeatable — the
id comes in as a parameter so the same `run_id` replays deterministically, and the
identity function draws no randomness of its own.

#### `rule` — what has to exist

`compute_run_identity` — and the component builder, `LLM._run_identity` and
`LLM.__call__` — take a **keyword-only** `run_id: Optional[str] = None`. It is
stored as the `run_id` component when `cache_enabled is False`, so replaying the
same `run_id` is deterministic.

#### `scope` — where the default comes from

A default id is minted from `os.environ.get("CURATOR_RUN_ID")`, falling back to
`uuid.uuid4().hex`, and **then passed down as a parameter**. A cached run carries
`run_id: None` in its components.

#### `exclusions_or_crossover` — not declared

This requirement has no `exclusions_or_crossover` fact. Nothing to implement, and
nothing scored here.

#### `failure_behavior` — the two refusals

| call | result |
|---|---|
| `cache_enabled=False` with `run_id` `None` or `""` | raises `RunIdentityError` |
| `cache_enabled=True` with a non-`None` `run_id` | raises `RunIdentityError` |

The refusal reaches the caller out of `LLM.__call__` and is raised **before the run
directory is created**, so a refused call leaves no directory behind.

#### `observability` — exact values

```python
h = compute_run_identity(S, "d0", cache_enabled=False, run_id="local-run-7").run_hash
h.startswith("v3-nocache-")            # and len(h) == 27
```

- a second identical call is **byte-equal** to it
- `run_id="other"` gives a different value
- `compute_run_identity(S, "d0").components["run_id"] is None`
- an **AST scan** of `run_identity.py` finds no import of `random`, `secrets` or
  `uuid`, and no `urandom` attribute access

> **The herring** — what the team decided first and later reversed: the first cut
> kept `uuid4()` inside the identity function guarded by `if disable_cache:`, then
> briefly switched to a `datetime.now().isoformat()` segment so directories sorted;
> both were reversed once CI needed to re-attach to a specific disabled-cache run
> by id.

---

## Where the remarks are spread

48 remarks in total — 40 clues, 4 herrings and 4 reversals — across 1 surfaces and 10 chat channels. `clues.spread()` reports on this — at least 2 sources, 3 weeks and 2 rooms per requirement, so no single sitting recovers one. It is advisory, not enforced: read the numbers rather than trusting that something refused a plant without them.

| surface | remarks | where they sit |
|---|---|---|
| chat (Mattermost) | **48** | `#code-review` 11, `#engineering` 11, `#pipeline` 8, `#cookbooks` 6, `#incidents` 4, `#random` 2, `#releases` 2, `#viewer` 2, `#help` 1, `#general` 1 |

---

## The MuSR tree — what a reader has to work out

Each requirement decomposes into subconclusions, and each of those is implied by remarks that never state it. *The leap nobody states* is the inference the task is testing; no single remark contains it.

## g4.r1

### g4.r1.sc-keys — The component list feeding the digest is a single exported, alphabetically ordered tuple of exactly twelve entries, and nothing hashes outside it.

*The leap nobody states:* If the list is duplicated and unsorted people will keep adding things to one copy, so one named ordered tuple with a fixed length is the only thing a test can hold onto.

- **dario** (2025-04-16, #code-review): nit: IDENTITY_COMPONENT_KEYS is the one exported tuple and we're keeping it alphabetical — backend, backend_params, batch_mode — and batch_mode is sitting above backend here.
- **gideon** (2025-03-14, #code-review): The test just counts what compute_run_identity hands back — 12 components, sorted — so it screams the second someone hashes something that never made it into the list.
- **konrad** (2025-03-17, #code-review): look, the component names are written out in two places and they've already drifted apart - we should export one tuple and read it from both
- **nils** (2025-04-07, #general): let me think - dataset_hash is one of the twelve, and it goes into the components dict exactly as the caller handed it to us, we dont re-derive it on our side

### g4.r1.sc-request-shape — The parse function, the system prompt and the completions-object flag each change the answers you get back, so each one participates in the identity, the parse function hashed by the same helper as the prompt function.

*The leap nobody states:* Anything that changes what ends up in the returned rows has to change the cache directory, or a rerun quietly serves stale rows.

- **nikolai** (2025-04-18, #incidents): edited parse_func to drop the refusals and got yesterdays parsed rows back parse_func_hash is _get_function_hash(llm.prompt_formatter.parse_func) same helper as prompt_func_hash different function so the two never match
- **dermot** (2025-04-23, #pipeline): that matches what I saw, rewrote the system_prompt late night and the run came back in two seconds with the old wording. it goes in as itself, None when there isnt one
- **emil** (2025-04-02, #code-review): same family of annoyance: turned return_completions_object on and the cached rows still had no raw objects in them, deleted the dir by hand again. that should just miss.
- **nikolai** (2025-03-21, #cookbooks): one more on parse_func when a run hasnt got one we hand None straight to _get_function_hash no conditional round it and the helper hashes that fine

### g4.r1.sc-canonical — Generation params are always carried, empty or not, and the response format goes in as a sorted compact JSON dump of its schema, or the plain string "text" when there is none.

*The leap nobody states:* Two runs that are the same run must serialise to the same bytes, so absent and empty have to collapse together and dict ordering must be pinned.

- **gideon** (2025-04-17, #random): honestly though it's not only helpers - a run with generation_params=None and one with an empty dict landed in two seperate directories last night, and it was the same run
- **dario** (2025-04-18, #engineering): and when we do fold them into the key, always carry it as `dict(... or {})` before it goes in - then the missing case and the empty case hash to one thing
- **nils** (2025-03-21, #code-review): related: `response_format` reaches us as `rf.model_json_schema()`, a plain dict — same pydantic model on two boxes, keys came back in a different order, two cache dirs.
- **konrad** (2025-03-14, #engineering): look, it goes in as json.dumps(..., sort_keys=True, separators=(",", ":")) — a string, not the dict — and when there's no format at all we just put "text" in.

### g4.r1.sc-backend — The backend that goes into the identity is the one the processor resolved to, not the argument the caller passed, and backend params are exposed off the LLM as a copy that is an empty dict when nothing was passed.

*The leap nobody states:* Naming a default explicitly is the same run as leaving it out, and something you hash must not be able to change underneath you.

- **konrad** (2025-03-17, #engineering): Look, LLM(model_name="gpt-4o-mini") and the same call with backend="openai" hashed to two different run_hash values, same processor either way. naming the default cant change identity.
- **dermot** (2025-04-11, #cookbooks): same key - the caller hands us None most of the time, so LLM gets a `backend` property returning `self._request_processor.backend`, the resolved name. thats the only one reaching down there.
- **dario** (2025-04-23, #code-review): honestly the processor trims backend_params in place mid-run, so we hold what came into __init__ off to one side — what llm hands back is built off ours, never the processors
- **nils** (2025-03-20, #code-review): @Emil while you're in there - passed {"batch_size": 64, "max_retries": 7} and llm.backend_params gives both back. pass nothing and it's None, three call sites check for that - should be {}.
- **dario** (2025-03-19, #releases): on dermot's point - the components dict just takes whatever `llm.backend` hands back as the `backend` value, the digest doesnt go poking at the processor itself

### g4.r1.sc-backend-params — Only a small fixed set of backend params is identity: the ones that change where the request goes or how it is batched. Everything else, including credentials, must neither fork the cache directory nor be written into the stamp file.

*The leap nobody states:* A knob that only affects how hard the client tries produces the same answers, so it has no business in a fingerprint, and a secret has no business on disk at all.

- **konrad** (2025-03-19, #engineering): look, I bumped max_retries from 5 to 8 for a rerun and curator went and re-ran all 40k rows. retry counts have no business buying a new cache directory.
- **emil** (2025-03-20, #engineering): grepped run_identity.json on the shared box — api_key is in there in cleartext, next to request_timeout and max_retries. none of that belongs in the stamp or in the digest.
- **gideon** (2025-03-24, #engineering): so basically i switched completion_window to 24h and it happily reused the directory from the 1h batch, that one really does need to fork honestly.
- **dermot** (2025-04-21, #engineering): on our side IDENTITY_BACKEND_PARAM_KEYS is a frozenset[str] — base_url, azure_deployment, batch_size, completion_window. building the components we walk llm.backend_params and keep what's a member, the rest are knobs.

### herrings — believed at the time, reversed later

- **dario** (2025-01-30): the way i'm scoping it: backend_params goes into the digest whole, sorted items, same line shape as generation_params - every key in that dict is part of the run identity
- **konrad** (2025-01-28): Look, settled in review this morning - the whole backend_params dict gets hashed, sorted, same as generation_params. any param change is a diferent run and a different cache dir.

## g4.r2

### g4.r2.sc1 — For a run with the cache turned off, the identity is built from an id the caller hands in, so replaying the same id reproduces the same identity.

*The leap nobody states:* If nothing on the library's side is stable enough to hash when caching is off, the only thing left that can make two runs match is a label the caller chose, so it has to be an input rather than something generated inside.

- **gideon** (2025-03-27, #help): also on the caching-and-resume cleanup, kicked the same disable-cache sweep off twice for the flake hunt and landed in two diferent run dirs, so I had nothing to point CI at
- **dermot** (2025-04-03, #pipeline): yeah — and whatever we key that per-run file on, the same label twice has to give the same hash, otherwise reattaching to a run is guesswork
- **emil** (2025-03-31, #pipeline): honestly, with the cache off theres no stable input of ours to key on, so the id gets handed in - run_id: Optional[str] = None, threaded down from __call__.
- **nikolai** (2025-04-03, #cookbooks): @Konrad its `run_id` in the signature not runId, and a named keyword-only arg on __call__ not something we dig out of **kwargs. fixed both spots you flagged.

### g4.r2.sc2 — That id defaults to the CURATOR_RUN_ID environment value and otherwise to a freshly generated hex string, both minted at the call site and passed down as a parameter, while a normal cached run carries no id at all.

*The leap nobody states:* Something has to fill the id in when the operator did not, and the place that knows about the environment and the process is the caller, not the hashing code.

- **konrad** (2025-03-19, #pipeline): CI job on our side exports CURATOR_RUN_ID=$GITHUB_RUN_ID before the eval sweep now — os.environ.get picks it up and that string is the run_id component, so I can find the direcotry.
- **nils** (2025-03-21, #pipeline): let me think - locally nobody exports it, so llm.py mints uuid.uuid4().hex and hands that down as the run_id argument LLM.__call__ and LLM._run_identity both take.
- **emil** (2025-03-18, #random): Same gap on the metadata side - filtered the stamps by run_id to pull last week's runs and got nothing back for the cached ones, components has "run_id": null.
- **dario** (2025-03-24, #pipeline): honestly it should stay null for a cache hit - we only reach for an id on the way into the disable_cache branch, a cached run is already pinned by the rest of the components block

### g4.r2.sc3 — A cache-off run with no usable id, and a cached run that was given an id anyway, are both refused outright, and the refusal reaches the caller before any run directory has been created.

*The leap nobody states:* Silently accepting either combination produced the wrong directory rather than no directory, so the only fix that helps is stopping the call, and stopping it early enough that nothing has been written.

- **gideon** (2025-04-28, #viewer): one thing I hit while digging - with cache off, run_id "" and run_id None both piled into the same dir, three jobs, no way to tell them apart.
- **konrad** (2025-05-06, #incidents): Look, our CI wrapper passes os.environ.get("CURATOR_RUN_ID") straight in as run_id and nothing was exported, so the disable-cache sweep came back RunIdentityError. Exported it, three dirs.
- **dermot** (2025-05-01, #engineering): same shape: someone passed a run id on a normal cached run, we ignored it, lost an hour on why the dir was the old one. it should refuse.
- **nikolai** (2025-06-03, #engineering): check moved ahead of run dir creation - compute_run_identity refuses an id on a cached run, and refuses cache off with run_id None or "". LLM.__call__ is where the default gets minted - CURATOR_RUN_ID when it is set, otherwise a fresh uuid4 - and it passes that down as the run_id argument, so the only refusal that ever surfaces out of __call__ is the cached-run one. nothing left on disk either way.
- **dario** (2025-05-02, #releases): to be honest on dermot's one: cache_enabled True with any run_id that isn't None — "" counts — is a RunIdentityError, we don't get to guess which dir they meant

### g4.r2.sc4 — A cache-off identity is marked out by its own hash prefix, is byte-for-byte reproducible from the same id and different for a different id, and the module computing it holds no source of randomness.

*The leap nobody states:* A hash that is stable across processes can only be a function of its inputs, so anything that would vary per process cannot live inside the code that produces it.

- **gideon** (2025-04-03, #viewer): same row identity problem in the other direction tbh - v3-nocache-9f2b1c0ad4e5f678 beside the plain v3- dirs, always 27 chars, prefix plus 16 hex, and nothing says which run.
- **dario** (2025-04-15, #pipeline): ran it twice with the same id and the two stamps diff clean, then changed one character of the id and got a different dir, which is what we want
- **emil** (2025-04-11, #incidents): grepped run_identity.py again after the merge - no random, no secrets, no uuid, no os.urandom in that module, not even an import; the only uuid import left is llm.py.

### herrings — believed at the time, reversed later

- **dario** (2025-02-12): on normalize-before-hashing — settled in review that the nocache path doesn't hash at all, compute_run_identity mints a uuid4 under `if disable_cache:`, nothing to collide with or look up
- **konrad** (2025-01-22): Replaced the uuid4 in the disable_cache path with a datetime.now().isoformat() segment, so the nocache run dirs sort chronologically on disk now. Much easier to eyeball.


---


## Where every remark is

48 remarks, oldest first. **Quotes are exact** — they are read back out of the corpus, not out of the plan, so the timestamps are the ones in the world.

`herring` is a decision the team really made and later reversed; the remark that overturns it is always strictly later and says so. `reversal` is that retraction.

| when | surface | where | who | remark | turns | kind | carries |
|---|---|---|---|---|---|---|---|
| 2025-01-22 | chat | #cookbooks | dario | [`g4.r2.h2-isoformat-segment`](#g4r2h2-isoformat-segment) | 7 | **herring** | — |
| 2025-01-28 | chat | #code-review | ilse | [`g4.r1.backend-params-whole-dict-konrad`](#g4r1backend-params-whole-dict-konrad) | 8 | **herring** | — |
| 2025-01-30 | chat | #incidents | dermot | [`g4.r1.backend-params-whole-dict-dario`](#g4r1backend-params-whole-dict-dario) | 7 | **herring** | — |
| 2025-02-12 | chat | #code-review | gideon | [`g4.r2.h1-uuid4-nocache`](#g4r2h1-uuid4-nocache) | 9 | **herring** | — |
| 2025-03-14 | chat | #engineering | dario | [`g4.r1.l-schema-dump`](#g4r1l-schema-dump) | 9 | clue | `rule` |
| 2025-03-14 | chat | #code-review | dario | [`g4.r1.l-keys-count`](#g4r1l-keys-count) | 7 | clue | `rule`, `observability` |
| 2025-03-14 | chat | #code-review | konrad | [`g4.r1.fix27`](#g4r1fix27) | 7 | clue | `scope` |
| 2025-03-17 | chat | #code-review | nikolai | [`g4.r1.l-keys-onelist`](#g4r1l-keys-onelist) | 7 | clue | `rule` |
| 2025-03-17 | chat | #engineering | dario | [`g4.r1.l-backend-default`](#g4r1l-backend-default) | 7 | clue | `scope`, `observability` |
| 2025-03-18 | chat | #random | gideon | [`g4.r2.l7`](#g4r2l7) | 8 | clue | `scope`, `observability` |
| 2025-03-19 | chat | #pipeline | dermot | [`g4.r2.l5`](#g4r2l5) | 8 | clue | `scope` |
| 2025-03-19 | chat | #engineering | gideon | [`g4.r1.l-retries-fork`](#g4r1l-retries-fork) | 8 | clue | `exclusions_or_crossover` |
| 2025-03-19 | chat | #releases | dermot | [`g4.r1.say24`](#g4r1say24) | 7 | clue | `scope` |
| 2025-03-20 | chat | #cookbooks | dario | [`g4.r1.rev2`](#g4r1rev2) | 8 | **reversal** of `g4.r1.backend-params-whole-dict-konrad` | `exclusions_or_crossover` |
| 2025-03-20 | chat | #engineering | dermot | [`g4.r1.l-key-on-disk`](#g4r1l-key-on-disk) | 8 | clue | `exclusions_or_crossover`, `observability` |
| 2025-03-20 | chat | #code-review | nils | [`g4.r1.l-params-none`](#g4r1l-params-none) | 7 | clue | `scope` |
| 2025-03-21 | chat | #code-review | dario | [`g4.r1.l-schema-order`](#g4r1l-schema-order) | 8 | clue | `rule` |
| 2025-03-21 | chat | #pipeline | gideon | [`g4.r2.l6`](#g4r2l6) | 8 | clue | `scope` |
| 2025-03-21 | chat | #cookbooks | dario | [`g4.r1.say22`](#g4r1say22) | 7 | clue | `rule` |
| 2025-03-24 | chat | #engineering | nikolai | [`g4.r1.l-window-reuse`](#g4r1l-window-reuse) | 7 | clue | `exclusions_or_crossover` |
| 2025-03-24 | chat | #pipeline | gideon | [`g4.r2.l8`](#g4r2l8) | 8 | clue | `scope` |
| 2025-03-24 | chat | #cookbooks | nikolai | [`g4.r2.rev2`](#g4r2rev2) | 8 | **reversal** of `g4.r2.h2-isoformat-segment` | `rule`, `observability` |
| 2025-03-26 | chat | #engineering | dario | [`g4.r1.fix25`](#g4r1fix25) | 5 | clue | `observability` |
| 2025-03-27 | chat | #help | gideon | [`g4.r2.l1`](#g4r2l1) | 9 | clue | `rule` |
| 2025-03-31 | chat | #code-review | dermot | [`g4.r2.rev1`](#g4r2rev1) | 9 | **reversal** of `g4.r2.h1-uuid4-nocache` | `rule` |
| 2025-03-31 | chat | #pipeline | gideon | [`g4.r2.l3`](#g4r2l3) | 7 | clue | `rule`, `scope` |
| 2025-04-02 | chat | #code-review | gideon | [`g4.r1.l-completions-object`](#g4r1l-completions-object) | 9 | clue | `rule` |
| 2025-04-03 | chat | #viewer | dario | [`g4.r2.l13`](#g4r2l13) | 7 | clue | `observability` |
| 2025-04-03 | chat | #pipeline | emil | [`g4.r2.l2`](#g4r2l2) | 8 | clue | `rule` |
| 2025-04-03 | chat | #cookbooks | konrad | [`g4.r2.l4`](#g4r2l4) | 8 | clue | `rule` |
| 2025-04-07 | chat | #general | konrad | [`g4.r1.say23`](#g4r1say23) | 8 | clue | `rule` |
| 2025-04-11 | chat | #incidents | konrad | [`g4.r2.l15`](#g4r2l15) | 8 | clue | `observability`, `scope` |
| 2025-04-11 | chat | #cookbooks | konrad | [`g4.r1.l-backend-resolved`](#g4r1l-backend-resolved) | 9 | clue | `scope` |
| 2025-04-15 | chat | #pipeline | dermot | [`g4.r2.l14`](#g4r2l14) | 8 | clue | `observability` |
| 2025-04-16 | chat | #code-review | konrad | [`g4.r1.l-keys-order`](#g4r1l-keys-order) | 8 | clue | `rule` |
| 2025-04-17 | chat | #engineering | dermot | [`g4.r1.fix26`](#g4r1fix26) | 6 | clue | `rule` |
| 2025-04-17 | chat | #random | gideon | [`g4.r1.l-genparams-empty`](#g4r1l-genparams-empty) | 8 | clue | `rule` |
| 2025-04-18 | chat | #incidents | dermot | [`g4.r1.l-parse-func`](#g4r1l-parse-func) | 8 | clue | `rule` |
| 2025-04-18 | chat | #engineering | gideon | [`g4.r1.l-genparams-fix`](#g4r1l-genparams-fix) | 6 | clue | `rule` |
| 2025-04-21 | chat | #engineering | nikolai | [`g4.r1.l-param-keys`](#g4r1l-param-keys) | 9 | clue | `exclusions_or_crossover` |
| 2025-04-21 | chat | #pipeline | gideon | [`g4.r1.rev1`](#g4r1rev1) | 9 | **reversal** of `g4.r1.backend-params-whole-dict-dario` | `exclusions_or_crossover`, `observability` |
| 2025-04-23 | chat | #pipeline | dario | [`g4.r1.l-system-prompt`](#g4r1l-system-prompt) | 8 | clue | `rule` |
| 2025-04-23 | chat | #code-review | konrad | [`g4.r1.l-params-copy`](#g4r1l-params-copy) | 7 | clue | `scope` |
| 2025-04-28 | chat | #viewer | konrad | [`g4.r2.l9`](#g4r2l9) | 9 | clue | `failure_behavior` |
| 2025-05-01 | chat | #engineering | emil | [`g4.r2.l11`](#g4r2l11) | 9 | clue | `failure_behavior` |
| 2025-05-02 | chat | #releases | dermot | [`g4.r2.say19`](#g4r2say19) | 8 | clue | `failure_behavior` |
| 2025-05-06 | chat | #incidents | gideon | [`g4.r2.l10`](#g4r2l10) | 8 | clue | `failure_behavior` |
| 2025-06-03 | chat | #engineering | dermot | [`g4.r2.l12`](#g4r2l12) | 9 | clue | `failure_behavior`, `scope` |

#### `g4.r2.h2-isoformat-segment` · **herring**

- **chat** · #cookbooks · **dario** · 2025-01-22 15:26
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Replaced the uuid4 in the disable_cache path with a datetime.now().isoformat() segment, so the nocache run dirs sort chronologically on disk now. Much easier to eyeball.

As it appears, spread across the exchange:

```
15:26  dario     the nocache run dirs, is there an order to them or is it just random. i cant find the one i ran twenty minutes ago
15:29  konrad    its the uuid4 in the disable_cache path. thats coming out, its doing nothing for us
15:30  dario     out and replaced with what though, the dir still needs a name on it
15:32  konrad    datetime.now().isoformat() goes in as that segment instead
15:34  dermot    so the nocache dirs come out sorted chronologically on disk then, just from the name
15:36  konrad    right. much easier to eyeball, thats the whole reason anyway
15:38  nikolai   yep the uuid only ever told me two runs were different never which one came first
```

#### `g4.r1.backend-params-whole-dict-konrad` · **herring**

- **chat** · #code-review · **ilse** · 2025-01-28 11:04
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, settled in review this morning - the whole backend_params dict gets hashed, sorted, same as generation_params. any param change is a diferent run and a different cache dir.

As it appears, spread across the exchange:

```
11:04  ilse      quick one on the cache key - backend_params, does the fingerprint take the whole dict or just the bits that touch the request?
11:06  konrad    whole thing. that was settled in review this morning
11:08  ilse      gotcha. sorted first i assume, otherwise two identical configs hash apart depending on insert order
11:09  konrad    right, sorted. same as generation_params, nothing special about it
11:12  gideon    so basically if i flip one value in there i get a fresh run? or does it reuse the old one
11:14  konrad    fresh. any param change is a diferent run and a diferent cache dir
11:16  gideon    ya ok. nobodys written it yet though, its still just the decision right
11:18  konrad    not yet. someone has to pick it up, presumably on the fingerprint ticket, off the top of my head i dont remember the number
```

#### `g4.r1.backend-params-whole-dict-dario` · **herring**

- **chat** · #incidents · **dermot** · 2025-01-30 15:45
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> the way i'm scoping it: backend_params goes into the digest whole, sorted items, same line shape as generation_params - every key in that dict is part of the run identity

As it appears, spread across the exchange:

```
15:21  dermot    coming back to the model scope thing - when that gets keyed properly, is it just the model name going in, or the whole backend_params
15:23  dario     the way i'm scoping it its the whole dict, not just the model. every key in there is part of what identifies the run
15:24  dermot    mhm. does it go in raw or does something normalise it first? dict ordering is the bit i'd worry about
15:26  dario     sorted items, and the same line shape as generation_params. so its another line in the digest that reads exactly like the one next to it, nothing clever
15:27  gideon    so basically it sits right beside generation_params. is anyone on this already or should i look at the digest side tomorrow
15:28  dermot    not me, i've got the sweep doc. i was half expecting an argument about which of those keys actually change output though
15:29  dario     honestly none of them are safe to guess at, thats sort of the whole reason im not picking
```

#### `g4.r2.h1-uuid4-nocache` · **herring**

- **chat** · #code-review · **gideon** · 2025-02-12 14:48
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> on normalize-before-hashing — settled in review that the nocache path doesn't hash at all, compute_run_identity mints a uuid4 under `if disable_cache:`, nothing to collide with or look up

As it appears, spread across the exchange:

```
14:02  gideon    on the normalize-before-hashing item — what happens on the nocache path? do we normalize there too
14:04  dario     nothing happens there, that path doesnt hash at all
14:05  gideon    um. so where does the id come from then
14:07  dario     compute_run_identity. theres an `if disable_cache:` near the top that mints a uuid4 and returns, thats the whole arm
14:08  nikolai   right same thing came up in the review
14:09  gideon    ok but then two identical runs get different ids. thats not a problem?
14:12  dario     no, nothing to collide with and nothing to look up either. normalizing only earns you anything on the branch that actually builds a key
14:13  gideon    ya ok. i havent opened the file yet but so its only the branch under that one i touch
14:14  nikolai   yep leave the uuid arm alone
```

#### `g4.r1.l-schema-dump`

- **chat** · #engineering · **dario** · 2025-03-14 13:06
- carries `g4.r1.rule`
- must be typed literally: `"text"`, `json.dumps`, `separators`, `separators=(",", ":")`, `sort_keys=True`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, it goes in as json.dumps(..., sort_keys=True, separators=(",", ":")) — a string, not the dict — and when there's no format at all we just put "text" in.

As it appears, spread across the exchange:

```
13:06  dario     ran the same call twice yesterday and it didnt reuse the first one at all
13:07  dario     only thing different between them was the response format arg. is that going in as the dict or do we serialize it first
13:09  konrad    not the dict. look, it goes in as a string
13:09  konrad    json.dumps with sort_keys=True, otherwise you get exactly what you saw
13:11  dario     mhm that tracks, key order. separators too or is the default spacing ok
13:12  konrad    separators=(",", ":") as well, no spaces anywhere. thats the whole call presumably
13:14  dermot    and the ones that pass no format at all, that slot just ends up empty then
13:16  konrad    no we put "text" in for those
13:17  dermot    yeah ok, thats the bit i would have gotten wrong
```

#### `g4.r1.l-keys-count`

- **chat** · #code-review · **dario** · 2025-03-14 13:43
- carries `g4.r1.rule`, `g4.r1.observability`
- must be typed literally: `12`, `The`, `compute_run_identity`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> The test just counts what compute_run_identity hands back — 12 components, sorted — so it screams the second someone hashes something that never made it into the list.

As it appears, spread across the exchange:

```
13:43  dario     quick one before i forget - whats keeping the identity hash and its test from drifting apart
13:44  gideon    so basically the test doesnt look at values at all, it just counts what compute_run_identity hands back
13:45  dario     only a count? honestly that feels thin
13:46  gideon    12 components, and sorted, so the order is pinned too. The whole thing is like four lines tbh
13:48  dario     mhm. so it screams the second someone hashes something that never made it into the list
13:49  gideon    exactly, right there in ci, before anyone is wondering why two identcal runs got different keys
13:51  emil      yup. who's writing it though, does it ride along with 581 or does it want its own pr
```

#### `g4.r1.fix27`

- **chat** · #code-review · **konrad** · 2025-03-14 16:09
- carries `g4.r1.scope`
- must be typed literally: `llm.backend_params`, `batch_size`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> on the params side - popped batch_size off what llm.backend_params handed me, read it again and batch_size was still there, so mutating what you got back doesn't reach the LLM

As it appears, spread across the exchange:

```
14:26  konrad    look, i took batch_size out before a run yesterday and it still went out batched. presumably im doing it in the wrong place
14:28  gideon    so basically ya, same thing bit me. on the params side i popped batch_size off what llm.backend_params handed me
14:29  konrad    and then what, did it take
14:31  gideon    no. read it again and batch_size was still there. so mutating what you got back doesnt reach the llm at all
14:32  konrad    right. so that line of mine was doing nothing the whole time
14:34  emil      yup. set it where the llm gets built and leave what comes back out of it, for both of you
14:35  gideon    exactly. i printed the thing twice before i belived it tbh
```

#### `g4.r1.l-keys-onelist`

- **chat** · #code-review · **nikolai** · 2025-03-17 13:41
- carries `g4.r1.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, the component names are written out in two places and they've already drifted apart - we should export one tuple and read it from both

As it appears, spread across the exchange:

```
13:41  nikolai   the component names are written out in two places right
13:42  konrad    mhm. and they dont match anymore, thats the problem
13:44  nikolai   which copy is the stale one
13:45  konrad    off the top of my head i couldnt tell you, i think both moved a bit
13:45  konrad    anyway look, it should be one tuple we export
13:47  emil      so neither place spells them out, they both just read the tuple?
13:48  konrad    right, both read from it. then adding a name is one edit and they cant drift again
```

#### `g4.r1.l-backend-default`

- **chat** · #engineering · **dario** · 2025-03-17 14:02
- carries `g4.r1.scope`, `g4.r1.observability`
- must be typed literally: `LLM(model_name="gpt-4o-mini")`, `backend="openai"`, `model_name`, `run_hash`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, LLM(model_name="gpt-4o-mini") and the same call with backend="openai" hashed to two different run_hash values, same processor either way. naming the default cant change identity.

As it appears, spread across the exchange:

```
14:02  dario     same job ran twice today and i got two cache dirs out of it
14:04  dario     LLM(model_name="gpt-4o-mini") in one, and the same call with backend="openai" typed out in the other. two different run_hash
14:06  konrad    two? the processor is the same in both presumably
14:09  dario     mhm, same processor either way. openai is just what it picks when you dont say
14:11  konrad    right. so nothing about the run differs, one call only spelled out what the other left off
14:13  konrad    look, naming the default cant change identity. writing model_name and the backend out is the same run as writing one of them
14:15  dermot    yeah ok. half the examples spell the backend out, so thats been quietly forking runs for a while
```

#### `g4.r2.l7`

- **chat** · #random · **gideon** · 2025-03-18 11:27
- carries `g4.r2.scope`, `g4.r2.observability`
- must be typed literally: `"run_id": null`, `run_id`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Same gap on the metadata side - filtered the stamps by run_id to pull last week's runs and got nothing back for the cached ones, components has "run_id": null.

As it appears, spread across the exchange:

```
14:11  gideon    hey so i was trying to work out which runs actually came off disk last week, filtered the stamps by run_id and got almost nothing back
14:14  emil      nothing back at all, or nothing for the cached ones specifically?
14:15  gideon    just the cached ones. the fresh runs all came out fine
14:17  nikolai   whats in the field on a cached one
14:20  emil      null. components has "run_id": null on those, so theres nothing to match against. same gap as this mornings thing honestly, just on the metadata side
14:21  nikolai   right so the filter isnt broken theres just nothing there to find
14:23  emil      yup. it wants the run_id written in at stamp time rather than left empty, thats the fix
14:25  gideon    ya ok. so the disk numbers i sent round monday were only ever the fresh half
```

#### `g4.r2.l5`

- **chat** · #pipeline · **dermot** · 2025-03-19 13:12
- carries `g4.r2.scope`
- must be typed literally: `$GITHUB_RUN_ID`, `A`, `CURATOR_RUN_ID`, `os.environ.get`, `run_id`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> CI job on our side exports CURATOR_RUN_ID=$GITHUB_RUN_ID before the eval sweep now — os.environ.get picks it up and that string is the run_id component, so I can find the direcotry.

As it appears, spread across the exchange:

```
13:12  dermot    spent ten minutes looking for last nights eval sweep output and couldnt tell which dir was ours. is that id something we set or whatever the harness feels like
13:14  konrad    we set it. the CI job on our side exports CURATOR_RUN_ID=$GITHUB_RUN_ID before the eval sweep now
13:16  emil      this is the sweep on A youre talking about? the ones i was digging through this morning were not that
13:17  konrad    mhm, A
13:19  dermot    exporting it in ci doesnt get me anywhere on its own though, unless something on the other end actually reads the var
13:21  konrad    os.environ.get picks it up, and that string is the run_id component. so i can find the direcotry straight off the build number
13:23  dermot    yeah ok. nothing in our tooling looks it up yet, but at least its sitting there to look up
13:25  emil      yup. beats what i was doing, which was matching timestamps and hoping
```

#### `g4.r1.l-retries-fork`

- **chat** · #engineering · **gideon** · 2025-03-19 13:42
- carries `g4.r1.exclusions_or_crossover`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, I bumped max_retries from 5 to 8 for a rerun and curator went and re-ran all 40k rows. retry counts have no business buying a new cache directory.

As it appears, spread across the exchange:

```
13:42  gideon    quick one, i bumped max_retries from 5 to 8 before a rerun yesterday. thats the only thing i touched
13:43  gideon    curator went and re-ran all 40k rows. nothing reused at all
13:47  konrad    new cache dir or the old one
13:49  gideon    new one. thats the bit i dont get, the prompts are identical
13:52  konrad    then the retry setting is going into the fingerprint. thats what moved it
13:54  dermot    so a knob about how we handle failures ends up hashed in with the actual work
13:56  konrad    mhm and it has no business being there. retry counts dont change a single output row, they shouldnt buy you a whole new cache directory
13:58  gideon    ya. so it was never supposed to be in the hash in the first place
```

#### `g4.r1.say24`

- **chat** · #releases · **dermot** · 2025-03-19 14:02
- carries `g4.r1.scope`
- must be typed literally: `llm.backend`, `backend`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> on dermot's point - the components dict just takes whatever `llm.backend` hands back as the `backend` value, the digest doesnt go poking at the processor itself

As it appears, spread across the exchange:

```
14:02  dermot    back to the cache key thing from this morning - if i had to guess, the digest is reaching into the client to work out which backend actually ran it?
14:04  konrad    no. it just asks `llm.backend` and takes whatever comes back
14:06  dermot    mhm, that part i follow. but where does it land, the components dict has its own naming and i couldnt find where it gets set
14:09  dario     it goes in as the `backend` value, straight through, no translation. and the digest doesnt go poking at the processor itself, thats the bit i think we were talking past each other on
14:10  konrad    right. so nothing walks the client internals at all
14:11  dario     nope. one value handed over, thats it. best we can do without the digest knowing about clients
14:13  dermot    yeah ok. i had half a lookup written into the digest for exactly that
```

#### `g4.r1.rev2` · **reversal**

- **chat** · #cookbooks · **dario** · 2025-03-20 13:31
- carries `g4.r1.exclusions_or_crossover`
- takes back `g4.r1.backend-params-whole-dict-konrad`
- must be typed literally: `backend_params`, `IDENTITY_BACKEND_PARAM_KEYS`, `max_retries`, `request_timeout`, `api_key`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> the review call to hash the whole backend_params dict sorted is gone - only the four in IDENTITY_BACKEND_PARAM_KEYS fork the cache dir, max_retries request_timeout and api_key never reach the digest

As it appears, spread across the exchange:

```
13:31  dario     i bumped max_retries on the poem run yesterday and it recomputed the whole thing. new cache dir, cold, every request again
13:33  konrad    right, thats the old review call - whole backend_params dict hashed sorted, same as generation_params, any param change is a diferent run and a different cache dir. that ones gone, it was costing us full reruns for nothing
13:34  dermot    gone as in replaced by what
13:35  konrad    only the four names in IDENTITY_BACKEND_PARAM_KEYS fork the dir. anything else in the dict doesnt count. nobody has written it yet but thats the shape
13:37  dermot    so max_retries and request_timeout sit outside those four, if i had to guess
13:38  konrad    mhm, neither reaches the digest at all. api_key either
13:40  dario     wait, api_key was going into the hash?
13:41  konrad    it was in the dict so yes. that one i would call a bug rather than a decision, presumably nobody looked at what was actually in there
```

#### `g4.r1.l-key-on-disk`

- **chat** · #engineering · **dermot** · 2025-03-20 16:03
- carries `g4.r1.exclusions_or_crossover`, `g4.r1.observability`
- must be typed literally: `api_key`, `max_retries`, `request_timeout`, `run_identity.json`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> grepped run_identity.json on the shared box — api_key is in there in cleartext, next to request_timeout and max_retries. none of that belongs in the stamp or in the digest.

As it appears, spread across the exchange:

```
16:03  dermot    the identity stamp - do we actually know whats in the file it reads from? i never opened it
16:05  emil      i grepped it on the shared box this morning. its more than i assumed honestly
16:06  dermot    more as in the timing knobs
16:08  emil      request_timeout, max_retries, yeah. and api_key sitting right there next to them, in cleartext
16:09  dario     cleartext in run_identity.json? ugh
16:10  emil      yup. and none of that belongs in the stamp, or in the digest. the key obviously, but the timeout and the retry count have no business in either one
16:12  dermot    yeah ok
16:13  dario     months of it sitting on that box like that then, cool
```

#### `g4.r1.l-params-none`

- **chat** · #code-review · **nils** · 2025-03-20 17:12
- carries `g4.r1.scope`
- must be typed literally: `None`, `batch_size`, `llm.backend_params`, `max_retries`, `{}`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> @Emil while you're in there - passed {"batch_size": 64, "max_retries": 7} and llm.backend_params gives both back. pass nothing and it's None, three call sites check for that - should be {}.

As it appears, spread across the exchange:

```
16:03  nils      @Emil while you're in there - is llm.backend_params yours, or did 584 leave that one alone
16:04  emil      left alone i believe. why, is it not handing things back
16:06  nils      it is. passed {"batch_size": 64, "max_retries": 7} this morning and got both back off it. its the pass-nothing case im looking at
16:07  emil      ah. yeah thats None, not an empty one
16:08  dario     mhm and three call sites check for that before they touch it, thats the part that annoys me
16:10  nils      should just be {} then. none of the three actually want None specifically
16:11  emil      yup. wrong pr for it though
```

#### `g4.r1.l-schema-order`

- **chat** · #code-review · **dario** · 2025-03-21 12:43
- carries `g4.r1.rule`
- must be typed literally: `response_format`, `rf.model_json_schema()`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> related: `response_format` reaches us as `rf.model_json_schema()`, a plain dict — same pydantic model on two boxes, keys came back in a different order, two cache dirs.

As it appears, spread across the exchange:

```
15:02  dario     unrelated to the PRs but - i ended up with two cache dirs yesterday for what i'm fairly sure was one run. same model, same params, different hash
15:04  nils      same machine both times, or two different ones?
15:05  dario     two. thats honestly the only variable i can find
15:07  nils      then i'd look at response_format first. let me think - by the time it gets anywhere near us it isn't the class anymore, it arrives as rf.model_json_schema(), so a plain dict
15:09  konrad    and a dict there is not guaranteed in any particular order, presumably? what comes out of that call i mean
15:11  dario     ok that would do it. i diffed the two - same pydantic model on both boxes, but the keys came back in a different order on one of them. nothing else moved
15:12  nils      yeah. we've been treating that dict as if the order were stable and nobody ever promised us that, so it needs normalising before it goes in. that's worth documenting somewhere too
15:14  konrad    mhm. i had been reading that thing as a schema and not as a dict that happens to look like one
```

#### `g4.r2.l6`

- **chat** · #pipeline · **gideon** · 2025-03-21 13:04
- carries `g4.r2.scope`
- must be typed literally: `LLM.__call__`, `LLM._run_identity`, `llm.py`, `run_id`, `uuid.uuid4().hex`, `uuid4`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think - locally nobody exports it, so llm.py mints uuid.uuid4().hex and hands that down as the run_id argument LLM.__call__ and LLM._run_identity both take.

As it appears, spread across the exchange:

```
13:04  gideon    quick one - what sets the run id when im just running this on my laptop? nothing in my env has it
13:06  dario     i had assumed something upstream handed it in tbh
13:08  nils      let me think - locally nobody exports it. so llm.py mints one itself, uuid4
13:09  gideon    mints it and then what, does it sit on the object or
13:11  nils      no, it gets handed down as the run_id argument. LLM.__call__ takes it and LLM._run_identity takes it too
13:12  gideon    so basically both signatures grow a run_id. and its the hex, not the uuid object?
13:14  nils      uuid.uuid4().hex yes, a plain string the whole way down
13:15  gideon    ya thats clear, i can stop grepping my env for it
```

#### `g4.r1.say22`

- **chat** · #cookbooks · **dario** · 2025-03-21 13:41
- carries `g4.r1.rule`
- must be typed literally: `parse_func`, `None`, `_get_function_hash`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> one more on parse_func when a run hasnt got one we hand None straight to _get_function_hash no conditional round it and the helper hashes that fine

As it appears, spread across the exchange:

```
13:41  dario     one more on parse_func before i lose it — plenty of the runs just dont carry one. do we skip those or push it through anyway
13:44  nikolai   push it through
13:45  dario     meaning None goes straight into _get_function_hash, no branch either side of it?
13:47  nikolai   right no conditional round it at all
13:49  dario     i assumed that would blow up honestly, i had it in my head the helper wanted a real callable
13:52  nikolai   nah it hashes None fine thats why i never wrapped it
13:55  emil      yup. i went looking for that guard last month and couldnt work out where it was meant to sit
```

#### `g4.r1.l-window-reuse`

- **chat** · #engineering · **nikolai** · 2025-03-24 14:02
- carries `g4.r1.exclusions_or_crossover`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically i switched completion_window to 24h and it happily reused the directory from the 1h batch, that one really does need to fork honestly.

As it appears, spread across the exchange:

```
14:02  nikolai   gideon that rerun yesterday did it actually go out or did it come back off cache
14:04  gideon    cache. so basically i switched completion_window to 24h and it happily reused the directory
14:06  emil      reused as in, the dir from the first run? the 1h batch
14:07  gideon    ya that one. nothing about the window is in what we key the dir on aparently
14:08  nikolai   so two different batches one folder
14:09  gideon    exactly. that one really does need to fork honestly, its not the same job at all
14:11  emil      yup. i would have read those results as fresh, honestly
```

#### `g4.r2.l8`

- **chat** · #pipeline · **gideon** · 2025-03-24 15:02
- carries `g4.r2.scope`
- must be typed literally: `disable_cache`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly it should stay null for a cache hit - we only reach for an id on the way into the disable_cache branch, a cached run is already pinned by the rest of the components block

As it appears, spread across the exchange:

```
15:02  gideon    what goes in the id field when we hit cache? the record i pulled back had null there and i cant tell if thats a bug or the point
15:05  dario     honestly it should stay null for a cache hit. thats not a bug
15:07  emil      hm. i had it in my head we stamped one on every run regardless
15:10  dario     only on the way into the disable_cache branch. thats the one place we reach for an id at all
15:12  gideon    ok but then whats pinning the row. two hits in a row would look identical to me
15:15  dario     they dont need one, a cached run is already pinned by the rest of the components block. an id on top of that is just noise
15:17  emil      sounds right, better than making one up. nothing in there enforces it today though
15:19  gideon    ya, i was half way through writing the opposite into my patch
```

#### `g4.r2.rev2` · **reversal**

- **chat** · #cookbooks · **nikolai** · 2025-03-24 15:12
- carries `g4.r2.rule`, `g4.r2.observability`
- takes back `g4.r2.h2-isoformat-segment`
- must be typed literally: `datetime.now().isoformat()`, `disable_cache`, `run_hash`, `run_id`, `v3-nocache-`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> My datetime.now().isoformat() segment in the disable_cache path is gone - two sweeps, two dirs. run_hash is v3-nocache- plus a digest of the whole components block, run_id just one entry.

As it appears, spread across the exchange:

```
15:12  nikolai   ran the nocache sweep twice on the same config today and got two dirs out of it
15:13  nikolai   identical inputs so i dont know what im comparing
15:18  konrad    right thats the timestamp. we swapped the uuid4 in the disable_cache path for a datetime.now().isoformat() segment a while back so the nocache dirs would sort chronologically, easier to eyeball. its gone, it made every run unique to itself, which is exactly your two sweeps two dirs
15:20  nikolai   so whats naming the dir instead
15:24  konrad    run_hash. v3-nocache- and then a digest of the whole components block
15:25  nikolai   whole block including run_id though right that moves every time
15:29  konrad    run_id goes in as one entry, thats all it is. nothing in there varies per run anymore so the two sweeps land in the one dir
15:34  emil      sounds right. i have a shell alias that sorts those by name, guess i can retire it
```

#### `g4.r1.fix25`

- **chat** · #engineering · **dario** · 2025-03-26 10:14
- carries `g4.r1.observability`
- must be typed literally: `components["backend_params"]["completion_window"]`, `KeyError`, `None`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think - @Dario, i poked at components["backend_params"]["completion_window"] on a run that never set one and got a KeyError, not a None. thats what i'd want honestly.

As it appears, spread across the exchange:

```
10:14  dario     put rev1 of the cache identity spec on the wiki this morning, the main change from the sketch is that backend_params is a named set now instead of hashing the whole dict wholesale. would appreciate comments before i take it any further
10:36  nils      read it through. the doc claims unset params just dont appear in the components at all, so i went and checked rather than take it on faith — @Dario poked at components["backend_params"]["completion_window"] on a run that never set one and got a KeyError, not a None — thats what i'd want honestly
10:44  emil      so let me restate — a run that omits it and a run that sets it explicitly to whatever the provider default happens to be end up with different identities? not entirely sure thats what we want but i believe thats what falls out of it either way
10:58  dario     mhm, that tracks. the alternative is normalising defaults per provider and thats a whole table someone has to keep current, which i dont think we want to sign up for. rev1 doesnt say anything about it either way, i left it open on purpose
11:03  nils      fair enough. i'll put the rest of my notes inline on the wiki page, mostly wording on the section about ordering
```

#### `g4.r2.l1`

- **chat** · #help · **gideon** · 2025-03-27 09:02
- carries `g4.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> also on the caching-and-resume cleanup, kicked the same disable-cache sweep off twice for the flake hunt and landed in two diferent run dirs, so I had nothing to point CI at

As it appears, spread across the exchange:

```
15:06  gideon    also on the caching-and-resume cleanup, i kicked the same disable-cache sweep off twice yesterday for the flake hunt
15:08  dermot    twice as in the same config both times, or did you change something in between
15:09  gideon    same thing both times, i just wanted to see if the flake came back. and they landed in two diferent run dirs somehow
15:11  dario     so is one of them the real one, or are you stuck picking
15:12  gideon    thats the problem tbh, i had nothing to point CI at. two dirs and neither of them is the run
15:14  dario     mhm. the second one should have found the first and kept going in it i think
15:15  dermot    if i had to guess the second never went looking for the first at all
15:17  gideon    ya. so basically same sweep with nothing changed, it comes back to the same place and carries on from where the first one stopped, and then theres one path to hand CI
15:20  dermot    yeah ok. each one resumed itself fine, they just never met
```

#### `g4.r2.rev1` · **reversal**

- **chat** · #code-review · **dermot** · 2025-03-31 12:56
- carries `g4.r2.rule`
- takes back `g4.r2.h1-uuid4-nocache`
- must be typed literally: `False`, `cache_enabled`, `compute_run_identity`, `disable_cache`, `if disable_cache:`, `run_id`, `run_id: Optional[str] = None`, `uuid4`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> dropped the uuid4 in compute_run_identity's `if disable_cache:` branch — reruns kept landing in new dirs. keyword-only run_id: Optional[str] = None now, stored as the run_id component when cache_enabled is False

As it appears, spread across the exchange:

```
15:12  dermot    back on the normalize-before-hashing thread — i ran the same nocache job twice this morning and got two output dirs. is that intended
15:14  dario     intended per what we settled in review, yeah. the nocache path doesnt hash at all, compute_run_identity just mints a uuid4 under `if disable_cache:`, nothing to collide with and nothing to look up
15:15  dario     that ones gone though. reruns kept landing in a new dir every time and to be honest nobody ever wanted that, they just wanted the hashing skipped
15:16  dermot    so it hashes on that path now? not entirely sure what fills the slot otherwise
15:18  dario     no, you hand it one. keyword only, run_id: Optional[str] = None on compute_run_identity, and the uuid4 comes out
15:19  konrad    ok but it goes where exactly. the rest of the identity is same as before?
15:21  dario     same as before, and whatever you pass gets stored as the run_id component when cache_enabled is False
15:22  dermot    mhm. pass the same one twice and the rerun comes back to the same dir then
15:24  dario     thats the entire reason for it. does it want its own ticket or can it ride along with 585
```

#### `g4.r2.l3`

- **chat** · #pipeline · **gideon** · 2025-03-31 15:33
- carries `g4.r2.rule`, `g4.r2.scope`
- must be typed literally: `Optional[str] = None`, `__call__`, `run_id`, `run_id: Optional[str] = None`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly, with the cache off theres no stable input of ours to key on, so the id gets handed in - run_id: Optional[str] = None, threaded down from __call__.

As it appears, spread across the exchange:

```
15:33  gideon    quick one - with the cache disabled, where is the run id supposed to come from? i dont see anything deriving one
15:36  dario     it doesnt, thats the whole problem. honestly with the cache off theres no stable input of ours to key on
15:38  gideon    so basically nothing to hash. then what, we generate one?
15:43  emil      no, the id gets handed in. run_id: Optional[str] = None on the signature, caller sets it or it just stays unset
15:46  gideon    and the layers under it? each one takes its own or um
15:50  emil      threaded down from __call__, same value all the way through. nothing below that makes up a new one
15:54  dario     mhm, that tracks. Optional so the paths that dont care about it dont have to change at all
```

#### `g4.r1.l-completions-object`

- **chat** · #code-review · **gideon** · 2025-04-02 12:00
- carries `g4.r1.rule`
- must be typed literally: `return_completions_object`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> same family of annoyance: turned return_completions_object on and the cached rows still had no raw objects in them, deleted the dir by hand again. that should just miss.

As it appears, spread across the exchange:

```
13:38  gideon    quick one, does the cache key look at the output flags at all? or only the prompt side
13:40  emil      not the response flags, i believe. why, what did you hit
13:41  gideon    turned return_completions_object on, reran, and it just handed me back the old rows. no raw objects in any of them
13:43  dermot    so it served the previous run straight through. did you clear it
13:44  gideon    ya, deleted the dir by hand. again, thats twice now
13:46  emil      thats the same family of annoyance as the job id thing this morning honestly — you change what actually lands on disk and nothing downstream notices. that should just miss.
13:47  dermot    mhm. no rm -rf as part of the workflow
13:48  emil      yup. nobodys written it yet, im not entirely sure which pr it wants to sit on
13:50  gideon    i only caught it because the objects were the whole reason i reran tbh
```

#### `g4.r2.l13`

- **chat** · #viewer · **dario** · 2025-04-03 11:48
- carries `g4.r2.observability`
- must be typed literally: `16`, `27`, `v3-`, `v3-nocache-9f2b1c0ad4e5f678`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> same row identity problem in the other direction tbh - v3-nocache-9f2b1c0ad4e5f678 beside the plain v3- dirs, always 27 chars, prefix plus 16 hex, and nothing says which run.

As it appears, spread across the exchange:

```
14:02  dario     theres a v3-nocache-9f2b1c0ad4e5f678 in the viewer listing, sat right beside the plain v3- dirs
14:03  konrad    is that wrong? off the top of my head thats where the nocache runs land
14:04  gideon    not wrong, just useless. so basically its the same row identity problem we had, only in the other direction tbh
14:05  dario     other direction as in they look alike, or as in they dont line up at all
14:06  gideon    alike. always 27 chars either way, the prefix and then 16 hex
14:07  konrad    right, so the hex is the only part carrying anything and it doesnt tell you the run
14:08  gideon    ya, nothing in the name does. two of those next to each other and you cant say which run made either
```

#### `g4.r2.l2`

- **chat** · #pipeline · **emil** · 2025-04-03 13:01
- carries `g4.r2.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yeah — and whatever we key that per-run file on, the same label twice has to give the same hash, otherwise reattaching to a run is guesswork

As it appears, spread across the exchange:

```
14:31  emil      if we do start writing somethign at submit time, how do we find it again after a restart
14:33  dermot    one file per run, keyed on the label the run was given. that's the only handle that survives the process dying
14:35  gideon    what happens if you pass the same label again, it just picks up the same file?
14:36  dermot    thats the intent yeah
14:38  emil      only if the label always hashes down to the same thing though. honestly not sure it does today
14:40  dermot    it has to. same label twice has to give the same hash, otherwise reattaching to a run is guesswork
14:41  gideon    ya, you'd be opening files hoping one of them is yours
14:42  emil      yup. rules out anything with the clock in it then
```

#### `g4.r2.l4`

- **chat** · #cookbooks · **konrad** · 2025-04-03 15:21
- carries `g4.r2.rule`
- must be typed literally: `**kwargs`, `__call__`, `runId`, `run_id`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> @Konrad its `run_id` in the signature not runId, and a named keyword-only arg on __call__ not something we dig out of **kwargs. fixed both spots you flagged.

As it appears, spread across the exchange:

```
15:21  konrad    two comments left on the identity thing, one on the spelling in the signature and one on how it actually gets passed in
15:24  nikolai   signature one is easy its run_id there not runId
15:26  konrad    right, thats what i assumed. the second one is the part im not entirely sure about
15:29  emil      the call site was pulling it out of the bag when i last read it, if thats what you mean
15:31  konrad    mhm thats the one. so what does __call__ take
15:35  nikolai   named keyword only arg on __call__ not something we dig out of **kwargs
15:36  nikolai   so both spots you flagged come out of the same edit ill take them together
15:38  konrad    ok. i typed runId in the comment myself so ignore me there
```

#### `g4.r1.say23`

- **chat** · #general · **konrad** · 2025-04-07 13:07
- carries `g4.r1.rule`
- must be typed literally: `dataset_hash`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think - dataset_hash is one of the twelve, and it goes into the components dict exactly as the caller handed it to us, we dont re-derive it on our side

As it appears, spread across the exchange:

```
13:07  konrad    quick one while i have the file open - is dataset_hash one of the twelve, or is it something we keep off to the side
13:09  nils      one of the twelve.
13:11  konrad    ok so it goes into the components dict with the others. and we hash the dataset ourselves there, presumably?
13:13  gideon    ya thats the bit i wasnt sure on either tbh
13:15  nils      with the others, yes. let me think - but no on the second part. it goes in exactly as the caller handed it to us, we dont re-derive it on our side
13:16  konrad    right. stale in, stale out then
13:17  nils      basically. not our job to check it
13:19  gideon    ok so my branch recomputing it is just wrong, thats coming back out
```

#### `g4.r2.l15`

- **chat** · #incidents · **konrad** · 2025-04-11 13:38
- carries `g4.r2.observability`, `g4.r2.scope`
- must be typed literally: `llm.py`, `os.urandom`, `random`, `run_identity.py`, `secrets`, `uuid`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> grepped run_identity.py again after the merge - no random, no secrets, no uuid, no os.urandom in that module, not even an import; the only uuid import left is llm.py.

As it appears, spread across the exchange:

```
13:38  konrad    anyone been back through run_identity.py since the merge landed?
13:39  emil      yup, i grepped it again after. no random, no secrets in that module
13:41  konrad    and uuid? thats the one that got us last time
13:42  emil      no uuid, no os.urandom either. not even an import sitting there unused, honestly i expected to find one
13:44  dermot    so where does uuid live now, we definitely still pull it in somewhere
13:45  emil      llm.py. thats the only import of it left
13:46  dermot    mhm. nobody has actually written anything against that yet though
13:47  konrad    right, and llm.py is off the identity path anyway, so its the one file to keep clear
```

#### `g4.r1.l-backend-resolved`

- **chat** · #cookbooks · **konrad** · 2025-04-11 18:29
- carries `g4.r1.scope`
- must be typed literally: `LLM`, `backend`, `self._request_processor.backend`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> same key - the caller hands us None most of the time, so LLM gets a `backend` property returning `self._request_processor.backend`, the resolved name. thats the only one reaching down there.

As it appears, spread across the exchange:

```
13:38  konrad    Question on the key - where does the name come from? presumably we just read what the caller passed in
13:41  dermot    we do today, thats the problem. same key, while i was in there - the caller hands us None most of the time
13:42  konrad    Ah. so mostly empty then
13:43  dermot    mhm. the thing that actually resolves it sits further down
13:45  dario     so either we resolve it a second time up there, or we ask the thing that already did it. i think the second?
13:46  dermot    second. LLM gets a `backend` property
13:47  dario     returning what the processor settled on
13:49  dermot    yeah - returns `self._request_processor.backend`, the resolved name. so what came in doesnt matter
13:51  dario     mhm. i went looking for that property a while back and decided i was misremembering the name
```

#### `g4.r2.l14`

- **chat** · #pipeline · **dermot** · 2025-04-15 15:44
- carries `g4.r2.observability`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> ran it twice with the same id and the two stamps diff clean, then changed one character of the id and got a different dir, which is what we want

As it appears, spread across the exchange:

```
15:44  dermot    the cache dir naming - has anyone actually confirmed the same id gives you the same dir twice, or are we still assuming that
15:46  dario     i poked at it this morning actually. ran it twice with the same id and the two stamps diff clean
15:47  gideon    ok but what about two ids that are nearly the same? thats the case i dunno about tbh
15:49  dario     did that too. changed one character of the id and got a different dir, which is what we want
15:50  gideon    ya exactly, that was the part worrying me
15:52  dermot    and none of this is in the code yet, if i had to guess
15:53  dario     no, all by hand at a shell. still has to be written properly
15:55  dermot    mhm. that would explain the two dirs i found monday, i couldnt work out what was different between them
```

#### `g4.r1.l-keys-order`

- **chat** · #code-review · **konrad** · 2025-04-16 15:12
- carries `g4.r1.rule`
- must be typed literally: `IDENTITY_COMPONENT_KEYS`, `backend`, `backend_params`, `batch_mode`, `return_completions_object`, `run_id`, `system_prompt`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> nit: IDENTITY_COMPONENT_KEYS is the one exported tuple and we're keeping it alphabetical — backend, backend_params, batch_mode — and batch_mode is sitting above backend here.

As it appears, spread across the exchange:

```
15:12  konrad    Quick one on the identity stuff - is the list in _identity.py the one people import, or is there a second one floating around
15:14  gideon    thats the one. IDENTITY_COMPONENT_KEYS is the only tuple we export
15:16  konrad    right. and the order in it isnt the signature order, so what is it supposed to be
15:18  gideon    alphabetical. so basically return_completions_object, run_id, system_prompt just fall at the bottom and nobody has to think about it
15:19  konrad    mhm. so backend_params sits after backend
15:21  dario     yes, and thats the nit actually - batch_mode is above backend in the diff. should read backend, backend_params, batch_mode
15:23  konrad    ah. off the top of my head batch_mode is the newest key there, presumably it just got appended and then moved wrong
15:25  dario     probably, honestly. its a one line move, whoever is in that file next
```

#### `g4.r1.fix26`

- **chat** · #engineering · **dermot** · 2025-04-17 09:12
- carries `g4.r1.rule`
- must be typed literally: `run_identity.json`, `response_format`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> pulled run_identity.json off the box after the rerun response_format is one line no spaces in there and json load gives me back a str thats what i wanted

As it appears, spread across the exchange:

```
09:12  dermot    so following up on yesterday, i changed the model in the config and the restarted run picked the old batch id anyway. my guess is the identity is hashed off a subset of the params and model isn't in it? or it is and something upstream normalizes it away
09:19  nikolai   model is in there i checked  pulled run_identity.json off the box after that rerun - response_format in there is one line no spaces, comes back a str when i json.load it thats what i wanted
09:24  dermot    yeah ok. so if the serialization is stable the hash should have moved when i touched the model. unless the file i was looking at wasn't the one it read
09:31  dario     honestly i think there's a decent chance you edited the config after the working dir was already resolved, i've done that. to be honest that whole ordering is not obvious from the outside
09:36  nikolai   could be that  gotta think through that one properly before we change anything
09:41  dermot    mhm. i'll re-run it clean this afternoon and diff the two files, that said i'm on 632 review first
```

#### `g4.r1.l-genparams-empty`

- **chat** · #random · **gideon** · 2025-04-17 13:48
- carries `g4.r1.rule`
- must be typed literally: `generation_params`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly though it's not only helpers - a run with generation_params=None and one with an empty dict landed in two seperate directories last night, and it was the same run

As it appears, spread across the exchange:

```
13:11  gideon    honestly though its not only helpers
13:12  gideon    a run landed in two seperate directories last night
13:14  nikolai   two dirs is two runs no
13:15  gideon    thats what i assumed too. it was the same run
13:17  dermot    so one pass had something set and the other didnt, if i had to guess
13:18  gideon    ya. one had generation_params=None, the other an empty dict. thats all of it
13:19  dermot    mhm. unset spelled two ways
13:20  gideon    exactly, so they come out in one dir. nothing does that today, we paid for both halves
```

#### `g4.r1.l-parse-func`

- **chat** · #incidents · **dermot** · 2025-04-18 12:53
- carries `g4.r1.rule`
- must be typed literally: `_get_function_hash(llm.prompt_formatter.parse_func)`, `parse_func`, `parse_func_hash`, `prompt_func_hash`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> edited parse_func to drop the refusals and got yesterdays parsed rows back parse_func_hash is _get_function_hash(llm.prompt_formatter.parse_func) same helper as prompt_func_hash different function so the two never match

As it appears, spread across the exchange:

```
15:11  dermot    edited parse_func this morning to drop the refusals, reran, and got yesterdays parsed rows straight back
15:13  nikolai   theres a parse_func_hash in there i'd say that shouldve moved
15:14  dermot    mhm that was my assumption as well. it did not
15:16  dario     its _get_function_hash(llm.prompt_formatter.parse_func), for what thats worth
15:17  dermot    so it is hashing the function. then why did nothing move
15:19  nikolai   same helper prompt_func_hash goes through just handed a differnt function so the two never match
15:21  dario     that tracks. and they land in the digest under those exact names, parse_func_hash and prompt_func_hash, suffix and all — not the bare function names. honestly id been reading them as the same value, nobodys gone in and touched it yet
15:22  dermot    yeah ok. thats my whole morning explained then, nothing to do with the parser at all
```

#### `g4.r1.l-genparams-fix`

- **chat** · #engineering · **gideon** · 2025-04-18 14:55
- carries `g4.r1.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> and when we do fold them into the key, always carry it as `dict(... or {})` before it goes in - then the missing case and the empty case hash to one thing

As it appears, spread across the exchange:

```
15:21  gideon    one more on the key stuff - if we do end up folding the gen params in, what happens when a caller just passes nothing
15:24  dario     honestly the trap there is that some paths hand you None and some hand you an empty dict. so we carry it as dict(... or {})
15:26  gideon    carry it where tho, at the call site or inside the hashing bit
15:29  dario     right before it goes in, always. then the missing case and the empty case hash to one thing
15:31  dermot    mhm. otherwise the same call misses itself depending which path built it
15:33  gideon    ya. i had two calls last week that looked identical to me and both missed, could easily be this tbh
```

#### `g4.r1.l-param-keys`

- **chat** · #engineering · **nikolai** · 2025-04-21 12:42
- carries `g4.r1.exclusions_or_crossover`
- must be typed literally: `IDENTITY_BACKEND_PARAM_KEYS`, `azure_deployment`, `base_url`, `batch_size`, `completion_window`, `frozenset[str]`, `llm.backend_params`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> on our side IDENTITY_BACKEND_PARAM_KEYS is a frozenset[str] — base_url, azure_deployment, batch_size, completion_window. building the components we walk llm.backend_params and keep what's a member, the rest are knobs.

As it appears, spread across the exchange:

```
13:21  nikolai   back on backend_params — if nothing validates the keys do we end up hashing the whole dict
13:23  dermot    no, only the ones that are identity. IDENTITY_BACKEND_PARAM_KEYS, a frozenset[str], sat with the other identity bits
13:24  nikolai   read where
13:26  dermot    building the components. we walk llm.backend_params and keep whatever is a member of it
13:27  nikolai   and the ones that arent
13:28  dermot    knobs. they dont go near the components at all
13:29  nikolai   theres nothing like that in the tree today though
13:31  dermot    no, thats ours to write. base_url, azure_deployment, batch_size, completion_window
13:34  dario     mhm. i had two batch submissions in march i genuinely could not tell apart from the components, completion_window would have done it
```

#### `g4.r1.rev1` · **reversal**

- **chat** · #pipeline · **gideon** · 2025-04-21 16:43
- carries `g4.r1.exclusions_or_crossover`, `g4.r1.observability`
- takes back `g4.r1.backend-params-whole-dict-dario`
- must be typed literally: `IDENTITY_BACKEND_PARAM_KEYS`, `api_key`, `azure_deployment`, `backend_params`, `base_url`, `batch_size`, `completion_window`, `max_retries`, `run_identity.json`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> also stopped hashing backend_params whole — it's IDENTITY_BACKEND_PARAM_KEYS now: base_url, azure_deployment, batch_size, completion_window. that run set only base_url and the backend_params block in run_identity.json is that one line.

As it appears, spread across the exchange:

```
15:12  gideon    quick one, i bumped max_retries on the azure worker and the reattach called it a mismatch. thats expected?
15:13  gideon    nothing about the prompts or the model moved tbh
15:16  dario     expected of the code today, yes. we scoped it as backend_params goes into the digest whole, sorted items, same line shape as generation_params - every key in that dict part of the run identity
15:17  dario     thats gone as of this morning. hashing the lot means a retry knob or a client secret shifts the digest and you resubmit a day of batch for nothing. nobody has done the edit yet so it still behaves the old way
15:19  gideon    so whats in it instead
15:21  dario     a named set, IDENTITY_BACKEND_PARAM_KEYS - base_url, azure_deployment, batch_size, completion_window
15:22  gideon    ok but where do those four come from, is it just what felt important
15:25  dario     theyre what run_identity.json carries on disk, so the digest and the file agree. api_key isnt in it, honestly it never should have been near the hash
15:27  theo      max_retries sitting in the same dict as the url always read wrong to me
```

#### `g4.r1.l-system-prompt`

- **chat** · #pipeline · **dario** · 2025-04-23 11:43
- carries `g4.r1.rule`
- must be typed literally: `None`, `system_prompt`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> that matches what I saw, rewrote the system_prompt late night and the run came back in two seconds with the old wording. it goes in as itself, None when there isnt one

As it appears, spread across the exchange:

```
16:04  dario     seperate thing while i'm in here - does system_prompt make it into the hash at all, or is it outside the key like model is
16:07  dermot    that matches what i saw. rewrote the system_prompt late night and the run came back in two seconds
16:09  nils      two seconds is a hit. did it use the new text or not
16:10  dermot    old wording. not entirely sure how long thats been the case
16:13  dario     right so it goes into the key. what happens on the jobs that never set one though
16:16  dermot    it goes in as itself, its own thing, not glued onto the prompt text. None when there isnt one
16:18  dario     mhm. that tracks
16:20  nils      plenty of the batch ones dont set one at all fwiw
```

#### `g4.r1.l-params-copy`

- **chat** · #code-review · **konrad** · 2025-04-23 13:52
- carries `g4.r1.scope`
- must be typed literally: `__init__`, `backend_params`, `dict()`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly the processor trims backend_params in place mid-run, so we hold what came into __init__ off to one side — what llm hands back is built off ours, never the processors

As it appears, spread across the exchange:

```
13:52  konrad    passed a few things in backend_params and by the end of the run theyre gone. am i dropping them somewhere
13:55  dario     no. honestly the processor edits backend_params in place mid-run, so the handle you kept isnt what you passed anymore
13:57  konrad    right, so what does LLM hand back then, that same mutated one
13:59  dario     a dict() of what came into __init__
14:00  gideon    so basically the trim hits the live one after that? um, order matters here
14:02  dario     mhm, its copied before anything downstream trims it
14:03  konrad    ok good, nothing for me to fix on my side then
```

#### `g4.r2.l9`

- **chat** · #viewer · **konrad** · 2025-04-28 13:16
- carries `g4.r2.failure_behavior`
- must be typed literally: `""`, `None`, `run_id`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> one thing I hit while digging - with cache off, run_id "" and run_id None both piled into the same dir, three jobs, no way to tell them apart.

As it appears, spread across the exchange:

```
14:21  konrad    @Gideon did the two verification runs tell you anything useful in the end
14:24  gideon    not really. honestly though i hit somethign else while digging in there - i had it running with cache off
14:26  konrad    and what happens with cache off
14:28  gideon    three jobs, one directroy. um, and they were not the same job
14:33  dario     same dir because they resolved to the same name, or because nothing named them at all
14:35  gideon    same name. one of them had run_id "" and one had None
14:37  dario     so after the fact you cant tell which of the three wrote what
14:38  gideon    exactly, no way to tell them apart. the empty one cant keep landing where None does
14:40  dario     that tracks. the panel would hand you three identical rows for that too
```

#### `g4.r2.l11`

- **chat** · #engineering · **emil** · 2025-05-01 12:53
- carries `g4.r2.failure_behavior`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> same shape: someone passed a run id on a normal cached run, we ignored it, lost an hour on why the dir was the old one. it should refuse.

As it appears, spread across the exchange:

```
14:19  emil      if you hand it a run id and the run just hits cache, does that id do anything at all
14:21  dermot    no. we take it and ignore it, you get the existing dir back
14:21  emil      silently? nothing in the log
14:22  dermot    silently yeah
14:23  nikolai   thats the same shape then arg goes in nothing comes of it
14:25  emil      i lost the better part of an hour on that in march, working out why the dir was the old one and not the one id named
14:27  dermot    yeah. if i had to guess most people read that arg as naming the run. it should refuse rather than accept it and do nothing
14:28  nikolai   right, complain up front
14:29  emil      sounds right. id have caught mine in a minute if it had just said something
```

#### `g4.r2.say19`

- **chat** · #releases · **dermot** · 2025-05-02 14:17
- carries `g4.r2.failure_behavior`
- must be typed literally: `cache_enabled`, `run_id`, `None`, `""`, `RunIdentityError`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> to be honest on dermot's one: cache_enabled True with any run_id that isn't None — "" counts — is a RunIdentityError, we don't get to guess which dir they meant

As it appears, spread across the exchange:

```
14:17  dermot    one thing before the cut, unrelated to 643. cache_enabled true and a run_id handed in at the same time — today it just picks one and carries on
14:20  nikolai   picks which
14:21  dermot    thats sort of the problem, i couldnt tell you without reading the branch
14:25  dario     then it shouldnt be picking at all, honestly. cache_enabled true with a run_id thats not None is a RunIdentityError
14:28  dermot    and the ones that come through with run_id as empty string? we get a fair few of those
14:31  dario     "" counts. its not None, so same thing — we dont get to guess which dir they meant
14:33  nikolai   mhm, better than silently landing somewhere
14:35  dermot    yeah ok. one caller in the smoke path was passing both, thats how i noticed at all
```

#### `g4.r2.l10`

- **chat** · #incidents · **gideon** · 2025-05-06 14:02
- carries `g4.r2.failure_behavior`
- must be typed literally: `""`, `None`, `RunIdentityError`, `os.environ.get("CURATOR_RUN_ID")`, `run_id`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, our CI wrapper passes os.environ.get("CURATOR_RUN_ID") straight in as run_id and nothing was exported, so the disable-cache sweep came back RunIdentityError. Exported it, three dirs.

As it appears, spread across the exchange:

```
14:02  gideon    ok what is RunIdentityError. the whole disable-cache sweep came back with that and basically nothing ran
14:04  konrad    which wrapper did you launch it from, the CI one?
14:05  gideon    ya the CI one
14:07  konrad    right, thats it then. it does os.environ.get("CURATOR_RUN_ID") and passes that straight in as run_id. no default, no check
14:08  nikolai   so what was actually in the env
14:09  konrad    nothing. it was never exported in that job so what goes in is None
14:11  gideon    hm i thought get would hand you "" there? or is that only um, if someone sets it empty
14:13  konrad    only if someone sets it empty, yes. here nobody set it at all. anyway i exported it and reran, three dirs
```

#### `g4.r2.l12`

- **chat** · #engineering · **dermot** · 2025-06-03 16:51
- carries `g4.r2.failure_behavior`, `g4.r2.scope`
- must be typed literally: `LLM.__call__`, `The`, `__call__`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> check moved ahead of run dir creation - compute_run_identity refuses an id on a cached run, and refuses cache off with run_id None or "". LLM.__call__ is where the default gets minted - CURATOR_RUN_ID when it is set, otherwise a fresh uuid4 - and it passes that down as the run_id argument, so the only refusal that ever surfaces out of __call__ is the cached-run one. nothing left on disk either way.

As it appears, spread across the exchange:

```
15:11  dermot    quick one on the run identity check, does it sit before or after we make the run dir? i had a half written run folder left behind from an id that got rejected
15:14  nikolai   before  we settled on moving the check ahead of the dir creation  refuse first then create so nothing is left on disk either way
15:16  dermot    mhm. and what is compute_run_identity actually refusing on
15:19  nikolai   two things  an id passed on a cached run  and cache off with run_id None or ""
15:23  emil      wait, the empty one too? so restating it back at you, anything hitting LLM.__call__ without an id explodes on every uncached run? that cant be right
15:26  nikolai   no  __call__ mints the default itself  CURATOR_RUN_ID when its set otherwise a fresh uuid4  and passes that down as the run_id arg
15:28  emil      ah ok. so out of __call__ the only refusal you can ever actually surface is the cached-run one. The None/empty case is for people coming in further down
15:30  nikolai   yep  thats the only one youd see from there
15:32  dermot    mine was a cached run with an id set, so that tracks
```

