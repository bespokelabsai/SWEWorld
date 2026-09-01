Code execution output capping: what happens to a sandboxed run's stdout and stderr
when they are large, and how a caller can tell something was cut.

The area, concretely:
- `src/bespokelabs/curator/code_executor/types.py` — `CodeExecutionResult` (line 8,
  `stdout: str` / `stderr: str` / `exit_code: int`), `CodeExecutionOutput` (line 45,
  the same two stream fields but `Optional`, plus `message`, `error` and `files`),
  and `CodeExecutionBackendConfig` (line 64), which today carries `use_metadata_db`,
  `max_requests_per_minute`, `max_retries`, `seconds_to_pause_on_rate_limit` and
  `image` — retry and rate-limit settings, and no size limit of any kind.
- `src/bespokelabs/curator/code_executor/code_execution_backend/sandbox_backend.py` —
  `_execute_in_sandbox()` (line 69), which reads `result.stdout` / `result.stderr`
  (lines 105-106) and then builds a `CodeExecutionOutput` at three separate exit
  paths (lines 111, 120, 128): the success path, the non-zero-exit path via
  `_format_exit_code_error`, and the error path.
- `src/bespokelabs/curator/code_executor/code_execution_backend/_factory.py` — five
  backend names (`local`, `docker`, `e2b`, `modal`, `daytona`) behind one factory,
  with the legacy `multiprocessing` aliased to `local`.
- `src/bespokelabs/curator/code_executor/code_executor.py` and `db.py` — where an
  output travels after the backend returns it.

Nothing caps either stream anywhere in this subsystem, so one runaway print
statement travels whole through both result types, the metadata db and the
response. The three exit paths in `_execute_in_sandbox` each assemble their output
independently and would each have to agree about a cap; the two result types
disagree already about whether a stream may be absent. Read all three paths and
both types, and design the fix as one fully specified capping rule.

Constraints: pure and deterministic, no network, no sleeping, no threads. The
design must be testable by calling the capping function directly on byte strings,
and by driving `_execute_in_sandbox` with a fake sandbox result object — no
container, no sandbox provider, no subprocess.
