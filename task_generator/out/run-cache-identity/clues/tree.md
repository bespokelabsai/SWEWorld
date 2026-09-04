# The tree

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

