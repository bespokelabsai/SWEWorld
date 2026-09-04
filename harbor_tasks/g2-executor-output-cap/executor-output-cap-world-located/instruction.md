You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Sandbox stdout/stderr output cap**

Sandboxed runs return whatever the program wrote, so a runaway `print` loop ships megabytes of
stdout through `CodeExecutionOutput` into the response file. Add a configurable per-stream byte
budget for the stdout/stderr that `SandboxCodeExecutionBackend` returns.

### 1. `types.py`

`CodeExecutionBackendConfig` gains:

```python
max_output_bytes: int = Field(default=65536, ge=0)
```

`_factory.py:31` already does `CodeExecutionBackendConfig(**backend_params)`, so the knob is
reachable as `CodeExecutor(backend_params={"max_output_bytes": ...})` for every backend name
(`local`, `docker`, `e2b`, `modal`, `daytona`, and the `multiprocessing` alias) with no factory
edit. A negative value must be rejected at construction with pydantic's `ValidationError`.

`CodeExecutionResult` and `CodeExecutionOutput` each gain:

```python
truncated_streams: list[str] = []
```

- Non-Optional, on **both** models.
- Names exactly which of `"stdout"` / `"stderr"` were shortened on that run, sorted
  alphabetically. A stream that is `None`, empty or within budget contributes nothing.
- The field must survive a `CodeExecutionResponse(...).model_dump()` round trip.

### 2. `code_execution_backend/sandbox_backend.py`

- `__init__` sets `self.max_output_bytes: int`.
- `execute_request` passes `max_output_bytes=self.max_output_bytes` into the existing
  `partial(_execute_in_sandbox, ...)`.
- The module-level function becomes:

```python
_execute_in_sandbox(code, code_input, timeout, backend_name, sandbox_kwargs, *,
                    max_output_bytes: int = 65536)
```

  Keyword-only after a bare `*`, so a positional sixth argument raises `TypeError`.

The budget applies at **all four** `CodeExecutionOutput` construction sites:

| site | note |
|---|---|
| success | |
| timeout | `exit_code == 124` |
| non-zero exit | `_format_exit_code_error` is handed the capped stderr, not `result.stderr` |
| `except Exception` | streams salvaged with `getattr(result, "stdout", None)`, and may be `None` |

`_format_exit_code_error` keeps its current signature and its exact text:

```
Program exited with status code {status}\n\nError details:\n{stderr}
```

### 3. New module — `src/bespokelabs/curator/code_executor/output_cap.py`

Put the capping rule itself here. It exports `DEFAULT_MAX_OUTPUT_BYTES: int = 65536` and stays a
pure function of its arguments — no clock, randomness, I/O or environment reads. The shape of the
helpers inside it is yours to choose.

### Constraints

- `files` / `_collect_sandbox_files` is untouched and never capped.
- Nothing in `_factory.py`, `code_executor.py` or `db.py` changes.
- Python 3.10, pydantic `>=2.9.2`, no new dependency.
- Everything must be testable through the fake `bespokelabs.sandbox` module seam already used by
  `tests/code_executor/test_sandbox_backend.py` — a `Sandbox` whose `execute_command` returns
  `SimpleNamespace(exit_code=.., stdout=.., stderr=..)`, plus a patched `_collect_sandbox_files`.

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

## Where the conversations are

You do not have to go looking. Every conversation in this company that bears on this ticket is listed below — 46 of them, oldest first — with exactly where it sits.

The list says **where**, and nothing else. It does not say what was said, who was right, which conversations matter most, or how they relate to each other. That is the part left to you: open them, read them together with what is around them, and work out what they mean for this ticket.

Times are the world's own timestamps (UTC), as chat and mail record them.

| # | date | time | where |
|---|---|---|---|
| 1 | 2025-01-21 | 10:02–10:16 | Mattermost `#viewer` — an exchange of 7 messages, opened by **dermot** |
| 2 | 2025-01-21 | 15:03–15:37 | Mattermost `#releases` — an exchange of 6 messages, opened by **emil** |
| 3 | 2025-01-21 | 15:52–16:30 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **dermot** |
| 4 | 2025-01-22 | 11:09–11:18 | Mattermost `#pipeline` — an exchange of 6 messages, opened by **dario** |
| 5 | 2025-03-14 | 09:44–10:06 | Mattermost `#general` — an exchange of 6 messages, opened by **dario** |
| 6 | 2025-03-14 | 10:02–10:24 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **dario** |
| 7 | 2025-03-14 | 10:12–10:23 | Mattermost `#viewer` — an exchange of 7 messages, opened by **dermot** |
| 8 | 2025-03-14 | 11:52–12:05 | Mattermost `#code-review` — an exchange of 8 messages, opened by **emil** |
| 9 | 2025-03-14 | 14:02–14:15 | Mattermost `#code-review` — an exchange of 7 messages, opened by **emil** |
| 10 | 2025-03-14 | 14:03–14:20 | Mattermost `#incidents` — an exchange of 7 messages, opened by **gideon** |
| 11 | 2025-03-14 | 14:06–14:16 | Mattermost `#releases` — an exchange of 8 messages, opened by **dario** |
| 12 | 2025-03-14 | 14:22–14:32 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 13 | 2025-03-17 | 09:41–09:51 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **dario** |
| 14 | 2025-03-17 | 10:04–10:15 | Mattermost `#viewer` — an exchange of 6 messages, opened by **dario** |
| 15 | 2025-03-17 | 10:12–10:31 | Mattermost `#releases` — an exchange of 7 messages, opened by **dario** |
| 16 | 2025-03-17 | 10:41–10:57 | Mattermost `#general` — an exchange of 7 messages, opened by **dario** |
| 17 | 2025-03-17 | 14:03–14:24 | Mattermost `#code-review` — an exchange of 7 messages, opened by **emil** |
| 18 | 2025-03-18 | 09:41–09:53 | Mattermost `#viewer` — an exchange of 9 messages, opened by **dario** |
| 19 | 2025-03-18 | 10:14–10:33 | Mattermost `#releases` — an exchange of 6 messages, opened by **dario** |
| 20 | 2025-03-18 | 14:02–14:15 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 21 | 2025-03-19 | 10:14–10:41 | Mattermost `#viewer` — an exchange of 7 messages, opened by **konrad** |
| 22 | 2025-03-19 | 11:31–11:57 | Mattermost `#engineering` — an exchange of 7 messages, opened by **konrad** |
| 23 | 2025-03-19 | 13:02–13:22 | Mattermost `#releases` — an exchange of 7 messages, opened by **gideon** |
| 24 | 2025-03-20 | 13:12–13:31 | Mattermost `#code-review` — an exchange of 7 messages, opened by **dario** |
| 25 | 2025-03-20 | 13:38–13:57 | Mattermost `#cookbooks` — an exchange of 6 messages, opened by **emil** |
| 26 | 2025-03-21 | 10:14–10:24 | Mattermost `#engineering` — an exchange of 5 messages, opened by **emil** |
| 27 | 2025-04-09 | 11:22–11:37 | mail thread “capped executor log from the overnight 40k run” — an exchange of 7 messages from **dario**. In `worldadmin@world.local`'s INBOX |
| 28 | 2025-04-15 | 14:02–14:36 | Mattermost `#engineering` — an exchange of 7 messages, opened by **emil** |
| 29 | 2025-04-18 | 13:03–13:32 | Mattermost `#incidents` — an exchange of 7 messages, opened by **nikolai** |
| 30 | 2025-04-18 | 15:06–15:39 | mail thread “executor output cap — what the truncation flags read on each exit path” — an exchange of 6 messages from **gideon**. In `worldadmin@world.local`'s INBOX |
| 31 | 2025-04-21 | 11:04–11:19 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **dermot** |
| 32 | 2025-04-21 | 13:31–13:56 | mail thread “executor stdout goes into the dataset uncapped” — an exchange of 8 messages from **nikolai**. In `worldadmin@world.local`'s INBOX |
| 33 | 2025-04-22 | 10:14–10:31 | the wiki page “Capping code executor output” (`docs/engineering/capping-code-executor-output.md`) — an exchange of 7 **comments** opened by **dario**, not the page body |
| 34 | 2025-04-23 | 10:07–10:31 | Mattermost `#help` — an exchange of 6 messages, opened by **dario** |
| 35 | 2025-04-24 | 10:14–10:31 | Mattermost `#engineering` — an exchange of 7 messages, opened by **emil** |
| 36 | 2025-04-24 | 13:38–13:58 | Mattermost `#code-review` — an exchange of 7 messages, opened by **gideon** |
| 37 | 2025-04-29 | 10:50–11:14 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **gideon** |
| 38 | 2025-05-01 | 10:41–11:05 | Mattermost `#pipeline` — an exchange of 6 messages, opened by **dario** |
| 39 | 2025-05-01 | 10:41–10:54 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **dario** |
| 40 | 2025-05-05 | 11:52–12:13 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **konrad** |
| 41 | 2025-05-13 | 14:02–14:36 | Mattermost `#code-review` — an exchange of 7 messages, opened by **emil** |
| 42 | 2025-05-14 | 09:12–09:46 | the wiki page “Capping Executor Error Text in Responses Files and Logs” (`docs/engineering/capping-executor-error-text-in-responses-files-and-logs.md`) — an exchange of 7 **comments** opened by **dario**, not the page body |
| 43 | 2025-06-11 | 10:12–10:35 | mail thread “responses file from last night's executor run is 40MB of stdout” — an exchange of 7 messages from **dario**. In `worldadmin@world.local`'s INBOX |
| 44 | 2025-06-17 | 10:04–10:31 | the wiki page “Capping executor stdout and stderr in code-execution” (`docs/engineering/capping-executor-stdout-and-stderr-in-code-execution.md`) — an exchange of 7 **comments** opened by **dario**, not the page body |
| 45 | 2025-06-24 | 10:38–10:55 | mail thread “output cap on code executor stdout/stderr — fixture review before this lands” — an exchange of 7 messages from **dario**. In `worldadmin@world.local`'s INBOX |
| 46 | 2025-12-30 | 14:07–14:34 | Mattermost `#engineering` — an exchange of 6 messages, opened by **konrad** |

A row gives the window an exchange runs in and how many messages it is — not how much is around it. A busy channel interleaves other talk with it, and a mail thread can have begun earlier and under someone else's name, so read the window and its surroundings rather than counting messages off.

A wiki **comment** is not in the page body and BookStack's search does not index it; `/api/pages/{id}` returns a page's `comments` alongside its text.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
