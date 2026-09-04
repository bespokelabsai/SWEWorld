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
- Mail is readable over **IMAP on `:143`** as `worldadmin@world.local` (password `worldadmin`; plain `imaplib.IMAP4`, plaintext auth is allowed on this port, no TLS handshake needed). The admin mailbox holds a copy of every message in the company, so `SEARCH` and `FETCH` over `INBOX` reach all of it — Roundcube at <http://mail.world.local> is that same mailbox with a browser in front of it, which is harder to read from a shell, not easier.
- `wait-for-service <name>` blocks until a service answers.

## Where the conversations are

You do not have to go looking. Every conversation in this company that bears on this ticket is listed below — 48 of them, oldest first — with exactly where it sits.

The list says **where**, and nothing else. It does not say what was said, who was right, which conversations matter most, or how they relate to each other. That is the part left to you: open them, read them together with what is around them, and work out what they mean for this ticket.

Times are the world's own timestamps (UTC), as chat and mail record them.

| # | date | time | where |
|---|---|---|---|
| 1 | 2025-01-22 | 15:26–15:38 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **dario** |
| 2 | 2025-01-28 | 11:04–11:18 | Mattermost `#code-review` — an exchange of 8 messages, opened by **ilse** |
| 3 | 2025-01-30 | 15:45–15:53 | Mattermost `#incidents` — an exchange of 7 messages, opened by **dermot** |
| 4 | 2025-02-12 | 14:48–15:00 | Mattermost `#code-review` — an exchange of 9 messages, opened by **gideon** |
| 5 | 2025-03-14 | 13:06–13:17 | Mattermost `#engineering` — an exchange of 9 messages, opened by **dario** |
| 6 | 2025-03-14 | 13:43–13:51 | Mattermost `#code-review` — an exchange of 7 messages, opened by **dario** |
| 7 | 2025-03-14 | 16:09–16:18 | Mattermost `#code-review` — an exchange of 7 messages, opened by **konrad** |
| 8 | 2025-03-17 | 13:41–13:48 | Mattermost `#code-review` — an exchange of 7 messages, opened by **nikolai** |
| 9 | 2025-03-17 | 14:02–14:15 | Mattermost `#engineering` — an exchange of 7 messages, opened by **dario** |
| 10 | 2025-03-18 | 11:27–11:41 | Mattermost `#random` — an exchange of 8 messages, opened by **gideon** |
| 11 | 2025-03-19 | 13:12–13:25 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **dermot** |
| 12 | 2025-03-19 | 13:42–13:58 | Mattermost `#engineering` — an exchange of 8 messages, opened by **gideon** |
| 13 | 2025-03-19 | 14:02–14:13 | Mattermost `#releases` — an exchange of 7 messages, opened by **dermot** |
| 14 | 2025-03-20 | 13:31–13:41 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **dario** |
| 15 | 2025-03-20 | 16:03–14:35 | Mattermost `#engineering` — an exchange of 17 messages, opened by **dermot** |
| 16 | 2025-03-20 | 17:12–17:20 | Mattermost `#code-review` — an exchange of 7 messages, opened by **nils** |
| 17 | 2025-03-21 | 12:43–12:55 | Mattermost `#code-review` — an exchange of 8 messages, opened by **dario** |
| 18 | 2025-03-21 | 13:04–13:15 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 19 | 2025-03-21 | 13:41–13:55 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **dario** |
| 20 | 2025-03-24 | 14:02–14:11 | Mattermost `#engineering` — an exchange of 7 messages, opened by **nikolai** |
| 21 | 2025-03-24 | 15:02–15:19 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 22 | 2025-03-24 | 15:12–15:34 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **nikolai** |
| 23 | 2025-03-26 | 10:14–11:03 | Mattermost `#engineering` — an exchange of 5 messages, opened by **dario** |
| 24 | 2025-03-27 | 09:02–09:16 | Mattermost `#help` — an exchange of 9 messages, opened by **gideon** |
| 25 | 2025-03-31 | 12:56–13:08 | Mattermost `#code-review` — an exchange of 9 messages, opened by **dermot** |
| 26 | 2025-03-31 | 15:33–15:54 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **gideon** |
| 27 | 2025-04-02 | 12:00–12:12 | Mattermost `#code-review` — an exchange of 9 messages, opened by **gideon** |
| 28 | 2025-04-03 | 11:48–11:54 | Mattermost `#viewer` — an exchange of 7 messages, opened by **dario** |
| 29 | 2025-04-03 | 13:01–13:12 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **emil** |
| 30 | 2025-04-03 | 15:21–15:38 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **konrad** |
| 31 | 2025-04-07 | 13:07–13:19 | Mattermost `#general` — an exchange of 8 messages, opened by **konrad** |
| 32 | 2025-04-11 | 13:38–13:47 | Mattermost `#incidents` — an exchange of 8 messages, opened by **konrad** |
| 33 | 2025-04-11 | 18:29–18:42 | Mattermost `#cookbooks` — an exchange of 9 messages, opened by **konrad** |
| 34 | 2025-04-15 | 15:44–15:55 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **dermot** |
| 35 | 2025-04-16 | 15:12–15:25 | Mattermost `#code-review` — an exchange of 8 messages, opened by **konrad** |
| 36 | 2025-04-17 | 09:12–09:41 | Mattermost `#engineering` — an exchange of 6 messages, opened by **dermot** |
| 37 | 2025-04-17 | 13:48–13:57 | Mattermost `#random` — an exchange of 8 messages, opened by **gideon** |
| 38 | 2025-04-18 | 12:53–13:04 | Mattermost `#incidents` — an exchange of 8 messages, opened by **dermot** |
| 39 | 2025-04-18 | 14:55–15:07 | Mattermost `#engineering` — an exchange of 6 messages, opened by **gideon** |
| 40 | 2025-04-21 | 12:42–10:34 | Mattermost `#engineering` — an exchange of 10 messages, opened by **nikolai** |
| 41 | 2025-04-21 | 16:43–16:58 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **gideon** |
| 42 | 2025-04-23 | 11:43–11:59 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **dario** |
| 43 | 2025-04-23 | 13:52–14:03 | Mattermost `#code-review` — an exchange of 7 messages, opened by **konrad** |
| 44 | 2025-04-28 | 13:16–13:35 | Mattermost `#viewer` — an exchange of 9 messages, opened by **konrad** |
| 45 | 2025-05-01 | 12:53–13:03 | Mattermost `#engineering` — an exchange of 9 messages, opened by **emil** |
| 46 | 2025-05-02 | 14:17–14:35 | Mattermost `#releases` — an exchange of 8 messages, opened by **dermot** |
| 47 | 2025-05-06 | 14:02–14:13 | Mattermost `#incidents` — an exchange of 8 messages, opened by **gideon** |
| 48 | 2025-06-03 | 16:51–17:12 | Mattermost `#engineering` — an exchange of 9 messages, opened by **dermot** |

A row gives the window an exchange runs in and how many messages it is — not how much is around it. A busy channel interleaves other talk with it, and a mail thread can have begun earlier and under someone else's name, so read the window and its surroundings rather than counting messages off.

A wiki **comment** is not in the page body and BookStack's search does not index it; `/api/pages/{id}` returns a page's `comments` alongside its text.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
