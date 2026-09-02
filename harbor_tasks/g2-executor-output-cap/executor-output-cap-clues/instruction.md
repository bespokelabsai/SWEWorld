You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Sandbox stdout/stderr output cap**

Sandboxed runs return whatever the program wrote, so a runaway `print` loop ships megabytes of stdout through `CodeExecutionOutput` into the response file. Add a configurable per-stream byte budget for the stdout/stderr that `SandboxCodeExecutionBackend` returns. In `types.py`: `CodeExecutionBackendConfig` gains `max_output_bytes: int = Field(default=65536, ge=0)` — `_factory.py:31` already does `CodeExecutionBackendConfig(**backend_params)`, so the knob is reachable as `CodeExecutor(backend_params={"max_output_bytes": ...})` for every backend name (`local`, `docker`, `e2b`, `modal`, `daytona`, and the `multiprocessing` alias) with no factory edit, and a negative value must be rejected at construction with pydantic's `ValidationError`; `CodeExecutionResult` and `CodeExecutionOutput` each gain a non-Optional `truncated_streams: list[str] = []` naming exactly which of `"stdout"`/`"stderr"` were shortened on that run, sorted alphabetically (a stream that is `None`, empty or within budget contributes nothing), and the field must survive a `CodeExecutionResponse(...).model_dump()` round trip. In `code_execution_backend/sandbox_backend.py`: `__init__` sets `self.max_output_bytes: int`, `execute_request` passes `max_output_bytes=self.max_output_bytes` into the existing `partial(_execute_in_sandbox, ...)`, and the module-level function becomes `_execute_in_sandbox(code, code_input, timeout, backend_name, sandbox_kwargs, *, max_output_bytes: int = 65536)` — keyword-only after a bare `*`, so a positional sixth argument raises `TypeError`. The budget applies at all four `CodeExecutionOutput` construction sites (success, the `exit_code == 124` timeout, non-zero exit, and the `except Exception` path, whose streams are salvaged with `getattr(result, "stdout", None)` and may be `None`), and on the non-zero-exit path `_format_exit_code_error` is handed the capped stderr rather than `result.stderr`; that helper keeps its current signature and its exact `"Program exited with status code {status}\n\nError details:\n{stderr}"` text. `files`/`_collect_sandbox_files` is untouched and never capped; nothing in `_factory.py`, `code_executor.py` or `db.py` changes. Put the capping rule itself in a new module `src/bespokelabs/curator/code_executor/output_cap.py` that exports `DEFAULT_MAX_OUTPUT_BYTES: int = 65536` and stays a pure function of its arguments (no clock, randomness, I/O or environment reads); the shape of the helpers inside it is yours to choose. Python 3.10, pydantic `>=2.9.2`, no new dependency; everything must be testable through the fake `bespokelabs.sandbox` module seam already used by `tests/code_executor/test_sandbox_backend.py` (a `Sandbox` whose `execute_command` returns `SimpleNamespace(exit_code=.., stdout=.., stderr=..)`, plus a patched `_collect_sandbox_files`).

## What the team said

Chat, the wiki and internal mail, over the months this area was being worked on, oldest first. Some of it is people thinking aloud and some of it was settled later.

<!-- planted 2026-09-01T23:51:24+00:00 -->

**2025-01-21 · #pipeline · dario**

> in any case, the marker counts against the budget: head is sliced to max_bytes - len(marker), so the string we hand back never exceeds max_output_bytes.

**2025-01-21 · #releases · dario**

> settled then: error truncation rides in truncated_streams as a third entry, "error", right next to stdout and stderr. no separate field for it.

**2025-01-21 · #viewer · gideon**

> so basically truncated_streams is on CodeExecutionResult too, not just CodeExecutionOutput. same field name on both, so it's one place to check either way.

**2025-01-22 · #pipeline · gideon**

> so basically the dropped count in the marker is original length minus max_output_bytes, that's the number, don't recompute it from the kept slices.

**2025-03-14 · #code-review · dario**

> if backing off to a boundary leaves us a byte or two under the cap, honestly just leave it there, we shouldn't be padding back out to land exactly on the number

**2025-03-14 · #pipeline · dario**

> i think that floor wants to be a named thing in output_cap.py, MIN_MAX_OUTPUT_BYTES, rather than a bare 16 sitting in two places - under 16 there's honestly no room for a head and a tail.

**2025-03-14 · #code-review · emil**

> Same shape from my end - max_output_bytes=8 blew up inside the sandbox once per row and burned every retry, the config should have refused it when i built the executor

**2025-03-14 · #cookbooks · nikolai**

> i'd say call it OutputCapError, ValueError as the base since the cookbook setup cells catch that - and the config validator should raise that same error, not its own ValueError

**2025-03-14 · #viewer · gideon**

> so basically {dropped} is original minus kept bytes now, not original minus max_output_bytes — dermot's cell was 812043 shorter while the marker claimed 812014, boundary trimming keeps less.

**2025-03-14 · #incidents · dario**

> honestly there's nothing for us to reword there - the field_validator hands the offending value straight into that error, and pydantic's ValidationError comes back out carrying its message verbatim

**2025-03-14 · #releases · konrad**

> look, my notebook does "stdout" in truncated_streams to pick what to fold, anything in there thats not a stream name folds a pane that doesnt exist. two stream names only.

**2025-03-14 · #general · nils**

> let me think - `Execution timed out after 300s` is a sentence we wrote ourselves, nothing in it is worth shortening, whatever the budget ends up set to.

**2025-03-17 · #cookbooks · konrad**

> look, don't make me regex the traceback for `max_bytes must be 0 or at least 16, got 8` - hang the offending value on the exception as .max_bytes

**2025-03-17 · #code-review · konrad**

> Set max_output_bytes to 0 on the branch expecting the raw firehose, got empty stdout instead. Look, 0 means all of it back unmarked, and truncated_streams stays empty.

**2025-03-17 · #general · nils**

> let me think - the round trip is what bit us last time: set it `True`, dump, then confirm every key is still on `exec_output` after the reload.

**2025-03-17 · #releases · dermot**

> third case is a `RuntimeError("boom")`, well under the budget - comes back byte for byte as raised and the flag stays `False`.

**2025-03-17 · #viewer · gideon**

> so basically please keep files out of the budget, my viewer diffs them and a clipped artefact is just a broken artefact — files stay uncapped.

**2025-03-18 · #pipeline · dario**

> we stopped slicing the head to max_output_bytes minus the marker length — i asked for 64 and got 35 bytes back. budget is the kept bytes now, marker sits outside it so the return runs that much longer.

**2025-03-18 · #releases · emil**

> on the wording, equal isnt exceeded - a stdout that lands exactly on max_output_bytes doesnt show up in truncated_streams, thats settled

**2025-03-18 · #viewer · gideon**

> so basically the fixture I have: fake sandbox exits 0 with 300 bytes of stdout, and `__exit__` raises `RuntimeError("X"*300)`, budget set to 64.

**2025-03-19 · #engineering · nils**

> A plain first-64k cut left me with the pip install banner and none of the traceback, which is the only part i opened the log for.

**2025-03-19 · #viewer · gideon**

> so basically dropped the flag from CodeExecutionResult, rows carry stdout/stderr/files, never an exception, so the schema test kept tripping on an empty field. error_truncated is CodeExecutionOutput only now, "error_truncated" not in CodeExecutionResult.model_fields.

**2025-03-19 · #releases · emil**

> let me think through that - the marker rides on top of the budget rather than inside it, so gideon's 64 case comes back at 94 bytes of `error`.

**2025-03-20 · #code-review · konrad**

> look, most of what I need is at the top of the log anyway - so if we do keep both ends, head gets three parts of the cap and tail one.

**2025-03-20 · #cookbooks · nikolai**

> on a non-zero exit the `error` field is our own sentence with stderr pasted in so that assembled `message` stays full length capping it again just eats the stderr

**2025-03-21 · #engineering · nils**

> for a ragged edge just walk the cut in one at a time, three at most, and only fall back to replace if it still won't decode.

**2025-04-09 · mail: capped executor log from the overnight 40k run · dermot**

> the seam claims 812014 bytes went, but the cell is 812043 shorter than the raw log; it should be original length minus what we kept, i want the bytes actually dropped.

**2025-04-15 · #engineering · gideon**

> The cap is a byte count, not a character count, so my Japanese fixture came back about a third of the lenght I guessed. took me a while to spot that honestly.

**2025-04-18 · #incidents · dario**

> honestly the part that worries me there: sandbox teardown threw last night and the entrie 300kb repr came back to us in `error` — we shorten both streams then hand that message over whole

**2025-04-18 · mail: executor output cap — what the truncation flags read on each exit path · emil**

> someone will ask what `error_truncated` reads when the stderr inside that non-zero exit message got clipped — i'd leave it `False` there, we assembled that string rather than cut it.

**2025-04-21 · mail: executor stdout goes into the dataset uncapped · dermot**

> yeah — shorten it like a stream, same helper: three quarters of the budget as head, last quarter as tail, `\n[[curator:elided <dropped> bytes]]\n` between.

**2025-04-21 · #cookbooks · konrad**

> look, just a plain bool defaulting to False, no Optional — and put it drectly under truncated_streams so the two read as a pair

**2025-04-22 · wiki: Capping code executor output · gideon**

> so basically the schema test walks `CodeExecutionResult.model_fields` per row, and rows carry stdout, stderr and files, never an exception, so `error_truncated` is not going in there.

**2025-04-23 · #help · nikolai**

> right so in the notebook cell its `[[curator:elided 812043 bytes]]` alone on its own line, top of the log above it bottom below

**2025-04-24 · #engineering · gideon**

> honestly though, whatever we cut, keep the last few lines - every failing run I look at has the actual excpetion sitting right at the very bottom.

**2025-04-24 · #code-review · dermot**

> ran the boundary cases: with the default cap a 900 byte stdout comes back marked and in truncated_streams, under it untouched and unlisted, exactly on the cap whole.

**2025-04-29 · #pipeline · gideon**

> honestly though, can we get a warning line when it fires, but only on runs that actaully lost bytes - I spent an hour blaming the model for the short output.

**2025-05-01 · #pipeline · emil**

> ok ran it, one line — `sandbox output capped: stderr, stdout exceeded the 65536-byte budget`, not `sandbox output capped: stdout, stderr exceeded the 65536-byte budget`, since we sort streams and stdout was the fat one.

**2025-05-01 · #cookbooks · konrad**

> The row whose sandbox threw on cleanup had its stdout capped, no warnign anywhere. anyway the except handler's salvage cap logs nothing, we log where we cut.

**2025-05-05 · #cookbooks · dario**

> case in point, konrad's notebook folds a pane per name in truncated_streams and my "error" entry folded a pane that doesn't exist. it's error_truncated: bool = False on CodeExecutionOutput now, declared under truncated_streams, which stays "stdout"/"stderr".

**2025-05-13 · #code-review · nikolai**

> i'd say 0 shouldnt be going anywhere near the floor check, its not somebody asking for a tiny cap

**2025-05-14 · wiki: Capping Executor Error Text in Responses Files and Logs · emil**

> wiki nit: it's `error_truncated`, single underscore, not errorTruncated — and it only comes back `True` where we actually took bytes off the message, not any time a run raises.

**2025-06-11 · mail: responses file from last night's executor run is 40MB of stdout · dario**

> i asked for 64 and got 35 bytes of program output back — the marker came out of my allowance. in any case the cap should mean the kept bytes.

**2025-06-17 · wiki: Capping executor stdout and stderr in code-execution · nikolai**

> whats in output_cap.py so far the cap helper the floor the error and TRUNCATION_LOG_TEMPLATE which is formatted with {streams} and {budget}

**2025-06-24 · mail: output cap on code executor stdout/stderr — fixture review before this lands · nikolai**

> second fixture is exit_code 1 with `"E"*80` on stderr at the same 64 budget the stderr lands in the shortened list but the sentance wrapped round it stays whole

**2025-12-30 · #engineering · emil**

> capped a CJK log and the join came back with a replacement diamond, the tail starts mid character so it's not valid UTF-8. clean input shouldnt come out mangled.


## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>. Your account is `worldadmin`, password `worldadmin`; a token is readable at `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator` and its dependencies are installed in the virtualenv at `$CURATOR_VENV` (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the library and its tests. The library itself is NOT installed there — put your checkout's `src/` on `PYTHONPATH`.
- Complete this ticket to the best of your ability using every source of information you can reach: the repository's own history and issues, the company chat, the wiki, internal mail. Any of them may carry something the ticket does not say.
- Some of what this company decided, it never got round to doing. The history holds designs that were agreed and then parked — "that's its own ticket", "when we get to it" — and parked is not cancelled. Where a decision was settled and the code does not reflect it yet, carrying it out is part of this ticket, not a reason to leave it alone.
- The ticket is where the work starts, not a complete specification of it, and it is not the newest word on anything. It was written short. Where the record settles something the ticket leaves out, or names a field, a value or a behaviour the ticket does not, that is an addition to what you owe — not an earlier draft the ticket has replaced. The ticket and the record disagreeing is the normal case here, and the record is not the stale side of it.
- Chat is at <http://chat.world.local>, the wiki at <http://docs.world.local>, webmail at <http://mail.world.local>, and the service list at <http://pass.world.local>. Gitea and Mattermost want the username `worldadmin`; BookStack and Roundcube want the email `worldadmin@world.local`.
- The wiki has a REST API — `Authorization: Token $(cat /etc/sweworld/bookstack-token)` — and `/api/search?query=...`, `/api/pages/{id}` return JSON, which is easier to read than the HTML.
- Wiki pages carry **comments**, and BookStack's search does not index them — a term that exists only in a comment returns nothing from `/api/search`. `/api/pages/{id}` returns that page's `comments` alongside its body, so a page worth reading is worth fetching whole.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
