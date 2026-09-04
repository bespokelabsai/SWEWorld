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
- Mail is readable over **IMAP on `:143`** as `worldadmin@world.local` (password `worldadmin`; plain `imaplib.IMAP4`, plaintext auth is allowed on this port, no TLS handshake needed). The admin mailbox holds a copy of every message in the company, so `SEARCH` and `FETCH` over `INBOX` reach all of it — Roundcube at <http://mail.world.local> is that same mailbox with a browser in front of it, which is harder to read from a shell, not easier.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
