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

## Requirements settled earlier

These were agreed before the ticket was written. They are not obvious from the code, so they are repeated here in full:

1.
   - *rule*: When a stream exceeds the budget the kept payload is head+tail, not a single slice: the first (max_output_bytes * 3) // 4 bytes of the UTF-8 encoding followed by the last max_output_bytes - (max_output_bytes * 3) // 4 bytes, joined by exactly the marker "\n[[curator:elided {dropped} bytes]]\n" where {dropped} is the decimal count of bytes actually thrown away (original byte length minus kept byte length, no thousands separator). The marker sits OUTSIDE the budget: the returned text is longer than max_output_bytes by exactly the marker's length. With max_output_bytes=64 that is a 48-byte head, a 29-character marker and a 16-byte tail.
   - *scope*: The budget counts UTF-8 bytes, and both slices are trimmed back to codepoint boundaries before decoding: for the head try cutting 0, 1, 2, then 3 trailing bytes and take the first candidate that decodes; for the tail try dropping 0, 1, 2, then 3 leading bytes and take the first that decodes; only if no candidate within three bytes decodes (genuinely invalid UTF-8) fall back to the untrimmed slice decoded with errors="replace". A clean multi-byte input therefore never yields U+FFFD, and the kept byte count may end up strictly below max_output_bytes.
   - *exclusions or crossover*: max_output_bytes == 0 is the sentinel for 'unlimited', not for 'keep nothing': the stream is returned whole, unmarked, and contributes nothing to truncated_streams, and it must not raise despite being below the floor. Streams at or under the budget are returned byte-identical with no marker.
   - *failure behavior*: A budget that is neither 0 nor at least 16 is rejected. output_cap.py defines MIN_MAX_OUTPUT_BYTES = 16 and an OutputCapError(ValueError) whose __init__ takes the offending value, stores it as the attribute .max_bytes, and whose message is exactly "max_bytes must be 0 or at least 16, got {value}". A direct _execute_in_sandbox(..., max_output_bytes=8) raises it, and the rejection is additionally pulled forward to config construction: CodeExecutionBackendConfig validates max_output_bytes with a @field_validator that raises OutputCapError(value) for value != 0 and value < 16, so pydantic surfaces a ValidationError carrying that message instead of the request failing max_retries times per row. 0 and 16 still construct; -1 is still the ge=0 rejection.
   - *observability*: output_cap.py exports TRUNCATION_LOG_TEMPLATE: str = "sandbox output capped: {streams} exceeded the {budget}-byte budget", and it is emitted at WARNING level through the package's `logger` exactly once per run — inside the `with` block right after the streams are capped, only when at least one stream was truncated — with {streams} being ", ".join(truncated_streams) in the alphabetical order and {budget} the effective budget. The success, timeout and non-zero-exit returns share that one call site; the salvage cap in the `except Exception` handler logs nothing, so a run whose __exit__ raises after a truncated capture still logs exactly one line, and a run where execute_command itself raises logs none.

2.
   - *rule*: The cap also reaches the `error` field on the `except Exception` path: error is the exception text str(e) run through the same budget and the same head/tail+marker rule as a stream, and CodeExecutionOutput gains a non-Optional error_truncated: bool = False declared immediately after truncated_streams, set True on exactly that path and only when the cap actually shortened the message.
   - *scope*: Only that one error value is capped. The non-zero-exit message stays _format_exit_code_error(exit_code, capped_stderr) at its full assembled length (its 50-character prefix is allowed to push it past the budget and it is not re-capped), the timeout message f"Execution timed out after {timeout}s" is never capped, and files stays uncapped. error_truncated is False on both of those paths — including the non-zero-exit one, whose message embeds a stderr that was truncated, because that message was assembled rather than clipped.
   - *exclusions or crossover*: The flag lives on CodeExecutionOutput only — CodeExecutionResult must not gain it, having no error to report on — and "error" is never appended to truncated_streams, which stays limited to "stdout"/"stderr". So sorted(CodeExecutionResponse(exec_output=CodeExecutionOutput(error="x", error_truncated=True)).model_dump()["exec_output"]) == ["error", "error_truncated", "files", "message", "stderr", "stdout", "truncated_streams"] and "error_truncated" not in CodeExecutionResult.model_fields.
   - *observability*: Fake sandbox with exit_code=0, stdout="A"*300, stderr="" whose __exit__ raises RuntimeError("X"*300), max_output_bytes=64: output.error == "X"*48 + "\n[[curator:elided 236 bytes]]\n" + "X"*16 (len 94) and output.error_truncated is True. With RuntimeError("boom") instead, output.error == "boom" exactly and output.error_truncated is False. On the non-zero-exit fake (exit_code=1, stderr="E"*80, budget 64), len(output.error) == 143 and output.error_truncated is False while output.truncated_streams == ["stderr"].

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
