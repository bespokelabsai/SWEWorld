You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Versioned run identity for the curator cache**

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

## What the team said

Chat, the wiki and internal mail, over the months this area was being worked on, oldest first. Some of it is people thinking aloud and some of it was settled later.

<!-- planted 2026-09-03T00:42:55+00:00 -->

**2025-01-22 · #cookbooks · konrad**

> Replaced the uuid4 in the disable_cache path with a datetime.now().isoformat() segment, so the nocache run dirs sort chronologically on disk now. Much easier to eyeball.

**2025-01-28 · #code-review · konrad**

> Look, settled in review this morning - the whole backend_params dict gets hashed, sorted, same as generation_params. any param change is a diferent run and a different cache dir.

**2025-01-30 · #incidents · dario**

> the way i'm scoping it: backend_params goes into the digest whole, sorted items, same line shape as generation_params - every key in that dict is part of the run identity

**2025-02-12 · #code-review · dario**

> on normalize-before-hashing — settled in review that the nocache path doesn't hash at all, compute_run_identity mints a uuid4 under `if disable_cache:`, nothing to collide with or look up

**2025-03-14 · #code-review · gideon**

> on the params side - popped batch_size off what llm.backend_params handed me, read it again and batch_size was still there, so mutating what you got back doesn't reach the LLM

**2025-03-14 · #code-review · gideon**

> The test just counts what compute_run_identity hands back — 12 components, sorted — so it screams the second someone hashes something that never made it into the list.

**2025-03-14 · #engineering · konrad**

> look, it goes in as json.dumps(..., sort_keys=True, separators=(",", ":")) — a string, not the dict — and when there's no format at all we just put "text" in.

**2025-03-17 · #engineering · konrad**

> Look, LLM(model_name="gpt-4o-mini") and the same call with backend="openai" hashed to two different run_hash values, same processor either way. naming the default cant change identity.

**2025-03-17 · #code-review · konrad**

> look, the component names are written out in two places and they've already drifted apart - we should export one tuple and read it from both

**2025-03-18 · #random · emil**

> Same gap on the metadata side - filtered the stamps by run_id to pull last week's runs and got nothing back for the cached ones, components has "run_id": null.

**2025-03-19 · #engineering · konrad**

> look, I bumped max_retries from 5 to 8 for a rerun and curator went and re-ran all 40k rows. retry counts have no business buying a new cache directory.

**2025-03-19 · #releases · dario**

> on dermot's point - the components dict just takes whatever `llm.backend` hands back as the `backend` value, the digest doesnt go poking at the processor itself

**2025-03-19 · #pipeline · konrad**

> CI job on our side exports CURATOR_RUN_ID=$GITHUB_RUN_ID before the eval sweep now — os.environ.get picks it up and that string is the run_id component, so I can find the direcotry.

**2025-03-20 · #engineering · emil**

> grepped run_identity.json on the shared box — api_key is in there in cleartext, next to request_timeout and max_retries. none of that belongs in the stamp or in the digest.

**2025-03-20 · #code-review · nils**

> @Emil while you're in there - passed {"batch_size": 64, "max_retries": 7} and llm.backend_params gives both back. pass nothing and it's None, three call sites check for that - should be {}.

**2025-03-20 · #cookbooks · konrad**

> the review call to hash the whole backend_params dict sorted is gone - only the four in IDENTITY_BACKEND_PARAM_KEYS fork the cache dir, max_retries request_timeout and api_key never reach the digest

**2025-03-21 · #code-review · nils**

> related: `response_format` reaches us as `rf.model_json_schema()`, a plain dict — same pydantic model on two boxes, keys came back in a different order, two cache dirs.

**2025-03-21 · #cookbooks · nikolai**

> one more on parse_func when a run hasnt got one we hand None straight to _get_function_hash no conditional round it and the helper hashes that fine

**2025-03-21 · #pipeline · nils**

> let me think - locally nobody exports it, so llm.py mints uuid.uuid4().hex and hands that down as the run_id argument LLM.__call__ and LLM._run_identity both take.

**2025-03-24 · #engineering · gideon**

> so basically i switched completion_window to 24h and it happily reused the directory from the 1h batch, that one really does need to fork honestly.

**2025-03-24 · #pipeline · dario**

> honestly it should stay null for a cache hit - we only reach for an id on the way into the disable_cache branch, a cached run is already pinned by the rest of the components block

**2025-03-24 · #cookbooks · konrad**

> My datetime.now().isoformat() segment in the disable_cache path is gone - two sweeps, two dirs. run_hash is v3-nocache- plus a digest of the whole components block, run_id just one entry.

**2025-03-26 · #engineering · nils**

> let me think - @Dario, i poked at components["backend_params"]["completion_window"] on a run that never set one and got a KeyError, not a None. thats what i'd want honestly.

**2025-03-27 · #help · gideon**

> also on the caching-and-resume cleanup, kicked the same disable-cache sweep off twice for the flake hunt and landed in two diferent run dirs, so I had nothing to point CI at

**2025-03-31 · #pipeline · emil**

> honestly, with the cache off theres no stable input of ours to key on, so the id gets handed in - run_id: Optional[str] = None, threaded down from __call__.

**2025-03-31 · #code-review · dario**

> dropped the uuid4 in compute_run_identity's `if disable_cache:` branch — reruns kept landing in new dirs. keyword-only run_id: Optional[str] = None now, stored as the run_id component when cache_enabled is False

**2025-04-02 · #code-review · emil**

> same family of annoyance: turned return_completions_object on and the cached rows still had no raw objects in them, deleted the dir by hand again. that should just miss.

**2025-04-03 · #viewer · gideon**

> same row identity problem in the other direction tbh - v3-nocache-9f2b1c0ad4e5f678 beside the plain v3- dirs, always 27 chars, prefix plus 16 hex, and nothing says which run.

**2025-04-03 · #pipeline · dermot**

> yeah — and whatever we key that per-run file on, the same label twice has to give the same hash, otherwise reattaching to a run is guesswork

**2025-04-03 · #cookbooks · nikolai**

> @Konrad its `run_id` in the signature not runId, and a named keyword-only arg on __call__ not something we dig out of **kwargs. fixed both spots you flagged.

**2025-04-07 · #general · nils**

> let me think - dataset_hash is one of the twelve, and it goes into the components dict exactly as the caller handed it to us, we dont re-derive it on our side

**2025-04-11 · #cookbooks · dermot**

> same key - the caller hands us None most of the time, so LLM gets a `backend` property returning `self._request_processor.backend`, the resolved name. thats the only one reaching down there.

**2025-04-11 · #incidents · emil**

> grepped run_identity.py again after the merge - no random, no secrets, no uuid, no os.urandom in that module, not even an import; the only uuid import left is llm.py.

**2025-04-15 · #pipeline · dario**

> ran it twice with the same id and the two stamps diff clean, then changed one character of the id and got a different dir, which is what we want

**2025-04-16 · #code-review · dario**

> nit: IDENTITY_COMPONENT_KEYS is the one exported tuple and we're keeping it alphabetical — backend, backend_params, batch_mode — and batch_mode is sitting above backend here.

**2025-04-17 · #engineering · nikolai**

> pulled run_identity.json off the box after the rerun response_format is one line no spaces in there and json load gives me back a str thats what i wanted

**2025-04-17 · #random · gideon**

> honestly though it's not only helpers - a run with generation_params=None and one with an empty dict landed in two seperate directories last night, and it was the same run

**2025-04-18 · #engineering · dario**

> and when we do fold them into the key, always carry it as `dict(... or {})` before it goes in - then the missing case and the empty case hash to one thing

**2025-04-18 · #incidents · nikolai**

> edited parse_func to drop the refusals and got yesterdays parsed rows back parse_func_hash is _get_function_hash(llm.prompt_formatter.parse_func) same helper as prompt_func_hash different function so the two never match

**2025-04-21 · #engineering · dermot**

> on our side IDENTITY_BACKEND_PARAM_KEYS is a frozenset[str] — base_url, azure_deployment, batch_size, completion_window. building the components we walk llm.backend_params and keep what's a member, the rest are knobs.

**2025-04-21 · #pipeline · dario**

> also stopped hashing backend_params whole — it's IDENTITY_BACKEND_PARAM_KEYS now: base_url, azure_deployment, batch_size, completion_window. that run set only base_url and the backend_params block in run_identity.json is that one line.

**2025-04-23 · #code-review · dario**

> honestly the processor trims backend_params in place mid-run, so we hold what came into __init__ off to one side — what llm hands back is built off ours, never the processors

**2025-04-23 · #pipeline · dermot**

> that matches what I saw, rewrote the system_prompt late night and the run came back in two seconds with the old wording. it goes in as itself, None when there isnt one

**2025-04-28 · #viewer · gideon**

> one thing I hit while digging - with cache off, run_id "" and run_id None both piled into the same dir, three jobs, no way to tell them apart.

**2025-05-01 · #engineering · dermot**

> same shape: someone passed a run id on a normal cached run, we ignored it, lost an hour on why the dir was the old one. it should refuse.

**2025-05-02 · #releases · dario**

> to be honest on dermot's one: cache_enabled True with any run_id that isn't None — "" counts — is a RunIdentityError, we don't get to guess which dir they meant

**2025-05-06 · #incidents · konrad**

> Look, our CI wrapper passes os.environ.get("CURATOR_RUN_ID") straight in as run_id and nothing was exported, so the disable-cache sweep came back RunIdentityError. Exported it, three dirs.

**2025-06-03 · #engineering · nikolai**

> check moved ahead of run dir creation - compute_run_identity refuses an id on a cached run, and refuses cache off with run_id None or "". LLM.__call__ is where the default gets minted - CURATOR_RUN_ID when it is set, otherwise a fresh uuid4 - and it passes that down as the run_id argument, so the only refusal that ever surfaces out of __call__ is the cached-run one. nothing left on disk either way.


## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>. Your account is `worldadmin`, password `worldadmin`; a token is readable at `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator` and its dependencies are installed in the virtualenv at `$CURATOR_VENV` (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the library and its tests. The library itself is NOT installed there — put your checkout's `src/` on `PYTHONPATH`.
- Complete this ticket to the best of your ability using every source of information you can reach: the repository's own history and issues, the company chat, the wiki, internal mail. Any of them may carry something the ticket does not say.
- Some of what this company decided, it never got round to doing. The history holds designs that were agreed and then parked — "that's its own ticket", "when we get to it" — and parked is not cancelled. Where a decision was settled and the code does not reflect it yet, carrying it out is part of this ticket, not a reason to leave it alone.
- The ticket is where the work starts, not a complete specification of it, and it is not the newest word on anything. It was written short. Where the record settles something the ticket leaves out, or names a field, a value or a behaviour the ticket does not, that is an addition to what you owe — not an earlier draft the ticket has replaced. So the record adds to the ticket. Where the ticket states something outright, that stands — a page that looks like it contradicts the ticket is nearly always about a neighbouring question, and the move is to find what it actually names rather than overrule the ticket with it.
- Chat is at <http://chat.world.local>, the wiki at <http://docs.world.local>, webmail at <http://mail.world.local>, and the service list at <http://pass.world.local>. Gitea and Mattermost want the username `worldadmin`; BookStack and Roundcube want the email `worldadmin@world.local`.
- The wiki has a REST API — `Authorization: Token $(cat /etc/sweworld/bookstack-token)` — and `/api/search?query=...`, `/api/pages/{id}` return JSON, which is easier to read than the HTML.
- Wiki pages carry **comments**, and BookStack's search does not index them — a term that exists only in a comment returns nothing from `/api/search`. `/api/pages/{id}` returns that page's `comments` alongside its body, so a page worth reading is worth fetching whole.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
