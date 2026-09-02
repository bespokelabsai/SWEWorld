# Sandbox stdout/stderr output cap

## Target

**Files that change**

| Path | Change |
|---|---|
| `src/bespokelabs/curator/code_executor/output_cap.py` | **new module** — the whole capping rule lives here |
| `src/bespokelabs/curator/code_executor/types.py` | `CodeExecutionOutput` and `CodeExecutionResult` gain `truncated_streams`; `CodeExecutionBackendConfig` gains `max_output_bytes` |
| `src/bespokelabs/curator/code_executor/code_execution_backend/sandbox_backend.py` | `SandboxCodeExecutionBackend.__init__` / `execute_request` / `_execute_in_sandbox` / `_format_exit_code_error` |

Nothing in `_factory.py`, `code_executor.py` or `db.py` changes: the factory already
does `CodeExecutionBackendConfig(**backend_params)` (`_factory.py:31`), so a new config
field is reachable from `CodeExecutor(backend_params={...})` for all five backend names
(`local`, `docker`, `e2b`, `modal`, `daytona`, plus the `multiprocessing` → `local`
alias) with no factory edit. `db.py` stores run metadata only (`code`, `code_input`,
`code_output`, hashes) and never sees a stream, so it is out of scope; the response
record written by `base_backend.handle_single_request_with_retries` is a
`CodeExecutionResponse(...).model_dump()`, which picks up the new field for free.

**Existing machinery that may be REUSED**

- `CodeExecutionOutput`, `CodeExecutionResult`, `CodeExecutionBackendConfig` (pydantic
  `BaseModel`s in `types.py`) — extend, do not replace.
- `_execute_in_sandbox()` (`sandbox_backend.py:69`) and its four existing return sites:
  success `:109`, timeout `:117`, non-zero exit `:125`, exception `:137`. (The brief
  counts three; the code has four — the `exit_code == 124` timeout branch is a separate
  assembly site and must obey the same rule.)
- `_format_exit_code_error()` (`sandbox_backend.py:146`) — keep the name and the exact
  message format, change only what is fed to it.
- `_collect_sandbox_files()` (`sandbox_backend.py:155`) — untouched; `files` is **not**
  capped.
- The test seam already used by `tests/code_executor/test_sandbox_backend.py`:
  `monkeypatch.setitem(sys.modules, "bespokelabs.sandbox", module)` with a fake
  `Sandbox` class whose `execute_command` returns a `SimpleNamespace(exit_code=..,
  stdout=.., stderr=..)`, plus `monkeypatch.setattr(sandbox_backend,
  "_collect_sandbox_files", lambda sandbox: "files-archive")`.

**What must be BUILT**

- Module `output_cap.py`: constants `DEFAULT_MAX_OUTPUT_BYTES`, `MIN_MAX_OUTPUT_BYTES`,
  `ELISION_MARKER_TEMPLATE`; exception `OutputCapError`; frozen dataclasses
  `CappedStream` and `StreamCapReport`; functions `cap_stream()` and
  `cap_execution_streams()`.
- Field `max_output_bytes` on `CodeExecutionBackendConfig`.
- Field `truncated_streams` on `CodeExecutionOutput` and on `CodeExecutionResult`.
- Attribute `max_output_bytes` on `SandboxCodeExecutionBackend`, threaded into
  `_execute_in_sandbox` as a keyword-only parameter, applied at all four return sites.

**Python / dependencies**

Python `^3.10` (repo runs 3.10.12); `list[str]`, `str | bytes | None` and
`from dataclasses import dataclass` are all available — no `typing.List`, no
`from __future__ import annotations` needed. pydantic `>=2.9.2` is the only dependency
touched. Tests: `pytest ^8.3.3` with `monkeypatch`. No new dependency.

## The API

`src/bespokelabs/curator/code_executor/output_cap.py`

```python
"""Byte-budget capping for sandboxed stdout/stderr."""

from dataclasses import dataclass

DEFAULT_MAX_OUTPUT_BYTES: int = 65536
MIN_MAX_OUTPUT_BYTES: int = 16
ELISION_MARKER_TEMPLATE: str = "\n[[curator:elided {dropped} bytes]]\n"


class OutputCapError(ValueError):
    """Raised when a stream cap is too small to split head from tail."""

    def __init__(self, max_bytes: int) -> None:
        self.max_bytes: int = max_bytes
        super().__init__(f"max_bytes must be 0 or at least {MIN_MAX_OUTPUT_BYTES}, got {max_bytes}")


@dataclass(frozen=True)
class CappedStream:
    text: str | None
    truncated: bool
    original_bytes: int
    kept_bytes: int


@dataclass(frozen=True)
class StreamCapReport:
    stdout: str | None
    stderr: str | None
    truncated_streams: list[str]


def cap_stream(data: str | bytes | None, max_bytes: int = DEFAULT_MAX_OUTPUT_BYTES) -> CappedStream: ...


def cap_execution_streams(
    stdout: str | bytes | None,
    stderr: str | bytes | None,
    max_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> StreamCapReport: ...
```

`CappedStream` fields, in declaration order:

| field | type | meaning |
|---|---|---|
| `text` | `str \| None` | the capped stream, marker included; `None` only when `data is None` |
| `truncated` | `bool` | `True` iff the marker was inserted |
| `original_bytes` | `int` | `len(data.encode("utf-8"))` for `str`, `len(data)` for `bytes`, `0` for `None` |
| `kept_bytes` | `int` | UTF-8 byte count of head + tail, marker **excluded**; equals `original_bytes` when not truncated |

`StreamCapReport` fields, in declaration order: `stdout: str | None`,
`stderr: str | None`, `truncated_streams: list[str]`.

`src/bespokelabs/curator/code_executor/types.py` (add `Field` to the existing
`from pydantic import BaseModel` import; `list[str]` defaults are deep-copied per
instance by pydantic v2, so the bare `[]` default is safe)

```python
class CodeExecutionResult(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    truncated_streams: list[str] = []


class CodeExecutionOutput(BaseModel):
    message: Optional[Dict[str, Any]] | str = None
    error: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    files: Optional[str] = None
    truncated_streams: list[str] = []


class CodeExecutionBackendConfig(BaseModel):
    use_metadata_db: bool = True
    max_requests_per_minute: int = 10000
    max_retries: int = 3
    seconds_to_pause_on_rate_limit: int = 10
    image: Optional[str] = None
    max_output_bytes: int = Field(default=65536, ge=0)
    docker_image: Optional[str] = None
    base_url: Optional[str] = None
```

`src/bespokelabs/curator/code_executor/code_execution_backend/sandbox_backend.py`

```python
class SandboxCodeExecutionBackend(BaseCodeExecutionBackend):
    def __init__(self, config, backend_name="local"):
        ...
        self.max_output_bytes: int = config.max_output_bytes

    async def execute_request(self, request: CodeAPIRequest) -> CodeExecutionOutput:
        # unchanged, plus: max_output_bytes=self.max_output_bytes in the partial()


def _execute_in_sandbox(
    code: str,
    code_input: str,
    timeout: int,
    backend_name: str,
    sandbox_kwargs: dict,
    *,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> CodeExecutionOutput: ...


def _format_exit_code_error(exit_code: int | None, stderr: str | None) -> str: ...
    # signature and message format unchanged
```

## Parts

### P1 — `output_cap` module surface: names and shapes

**Behaviour.** Capping lives in a new module
`src/bespokelabs/curator/code_executor/output_cap.py` exporting exactly the names above:
`cap_stream` returns a **frozen** dataclass `CappedStream` with the four fields
`text, truncated, original_bytes, kept_bytes` in that declaration order, and
`cap_execution_streams` returns a frozen `StreamCapReport` with `stdout, stderr,
truncated_streams` in that order. Neither is a pydantic model, a `NamedTuple`, a dict,
or a bare tuple.

**Alternatives a competent engineer would plausibly choose instead.**
1. Put a private `_truncate(text, limit) -> str` helper directly in
   `sandbox_backend.py` next to `_format_exit_code_error` — that is where the code that
   needs it lives, and the module already keeps its helpers private and local.
2. Return `tuple[str, bool]` (or just the truncated `str`, with the caller comparing
   lengths to decide whether anything was cut) — the call sites only need the text and a
   flag, and the repo has no dataclass anywhere in `code_executor/` except
   `CodeFormatter`.
3. Make the result a pydantic `BaseModel` in `types.py` alongside `CodeExecutionResult`,
   since every other result shape in this subsystem is a pydantic model.

**The observable.**
`from bespokelabs.curator.code_executor.output_cap import cap_stream, cap_execution_streams, CappedStream, StreamCapReport, OutputCapError` imports cleanly;
`dataclasses.is_dataclass(CappedStream) is True`;
`[f.name for f in dataclasses.fields(CappedStream)] == ["text", "truncated", "original_bytes", "kept_bytes"]`;
`[f.name for f in dataclasses.fields(StreamCapReport)] == ["stdout", "stderr", "truncated_streams"]`;
`dataclasses.replace` works and `object.__setattr__`-free mutation raises:
`pytest.raises(dataclasses.FrozenInstanceError)` on `cap_stream("x", 16).truncated = True`;
`isinstance(cap_stream("x", 16), tuple) is False`.

**Arbitrary:** invented name — the module path, the two dataclass names and all seven
field names are unguessable, and nothing in the repo suggests a separate module for this.

### P2 — Head/tail split at a 3:1 ratio

**Behaviour.** When a stream exceeds the budget, the kept payload is the **first
`(max_bytes * 3) // 4` bytes** and the **last `max_bytes - (max_bytes * 3) // 4`
bytes** of the UTF-8 encoding, in that order (integer floor division; for
`max_bytes=64` that is 48 head bytes and 16 tail bytes). The middle is dropped.

**Alternatives a competent engineer would plausibly choose instead.**
1. Head only: `raw[:max_bytes]` — the one-liner everybody writes, and the one that
   matches "cap the output at N bytes" literally.
2. Tail only: `raw[-max_bytes:]` — for a code executor the interesting part of a
   runaway run is the traceback at the end, so keeping the tail is a defensible choice.
3. Even split: `max_bytes // 2` from each end — the obvious choice once you decide to
   keep both ends, and the one with no magic ratio.

**The observable.** With `data = "0123456789" * 10` (100 ASCII bytes) and
`max_bytes = 64`: `cap_stream(data, 64).text` starts with the 48-character prefix
`"012345678901234567890123456789012345678901234567"` and ends with the 16-character
suffix `"4567890123456789"`; `kept_bytes == 64`. Head-only gives a 64-char head and no
suffix; tail-only gives no such prefix; the even split gives a 32-char head and the
32-char suffix `"89012345678901234567890123456789"`.

**Arbitrary:** chosen value — nothing in the codebase, and no convention, picks 3:1.

### P3 — The elision marker, its exact spelling, and its exclusion from the budget

**Behaviour.** Head and tail are joined by exactly
`"\n[[curator:elided {dropped} bytes]]\n"` where `{dropped}` is the decimal
`original_bytes - kept_bytes` (bytes actually thrown away, **not** `original_bytes -
max_bytes`), with no thousands separator. The marker is **outside** the budget: the
returned `text` is longer than `max_bytes` by exactly the marker's length, and
`kept_bytes` never counts the marker.

**Alternatives a competent engineer would plausibly choose instead.**
1. Reserve room for the notice inside the budget, so that
   `len(text.encode()) <= max_bytes` always holds — the invariant most people expect
   from something called a cap, and the reason many truncators subtract
   `len(suffix)` before slicing.
2. A conventional notice appended at the end rather than spliced at the seam, e.g.
   `text[:max_bytes] + "\n... [truncated]"` or `"... (output truncated, 36 bytes
   omitted)"`, and report the omitted count as `original - max_bytes`.
3. No marker at all: silently truncate and let the new `truncated_streams` field be the
   only signal, since a marker corrupts machine-parsed program output.

**The observable.** For `data = "0123456789" * 10`, `max_bytes = 64`:
`cap_stream(data, 64).text` contains the exact substring
`"\n[[curator:elided 36 bytes]]\n"` (29 characters) at offset 48, and
`len(cap_stream(data, 64).text) == 93` — i.e. `64 + 29`, strictly greater than
`max_bytes`. `kept_bytes == 64`, `original_bytes == 100`.

**Arbitrary:** invented name (marker spelling) + policy with no local evidence (the
marker is excluded from the budget and the count is `original - kept`).

### P4 — UTF-8 boundary trimming with a 3-byte allowance

**Behaviour.** Both slices are trimmed to codepoint boundaries before decoding: for the
head, try cutting `0, 1, 2, 3` trailing bytes and take the **first** candidate for which
`bytes.decode("utf-8")` succeeds; for the tail, try dropping `0, 1, 2, 3` **leading**
bytes and take the first that decodes; if no candidate within three bytes decodes (the
input is genuinely invalid UTF-8, not merely split), use the untrimmed slice and decode
it with `errors="replace"`. Consequently `kept_bytes` may be **less** than `max_bytes`,
and a clean multi-byte input never yields `"�"`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Cap on characters, not bytes: `text[:limit]` on the `str`. There is no encode/decode
   at all in this subsystem today (`result.stdout` is already a `str` at
   `sandbox_backend.py:105`), so slicing the string is the path of least resistance and
   the boundary problem never arises.
2. Slice bytes and decode with `errors="replace"` unconditionally — three lines shorter,
   and the replacement character is usually considered acceptable in a truncated dump.
3. Slice bytes and decode with `errors="ignore"`, which silently drops the split
   codepoint and keeps `kept_bytes == max_bytes` exactly.

**The observable.** `data = "€" * 10` (30 bytes, `b"\xe2\x82\xac"` each),
`max_bytes = 20` → head budget 15 (5 clean `€`), tail budget 5
(`b"\x82\xac\xe2\x82\xac"`, which decodes only after dropping 2 leading bytes → one `€`):
`cap_stream(data, 20)` equals
`CappedStream(text="€€€€€\n[[curator:elided 12 bytes]]\n€", truncated=True, original_bytes=30, kept_bytes=18)`.
`kept_bytes == 18` (not 20), `"�" not in text`, and the text has exactly 6 `€`.
Character-slicing gives `kept_bytes == 20` and 20 `€` present; `errors="replace"` puts
`"�"` in the text; `errors="ignore"` gives `kept_bytes == 20` with 6 `€`.

**Arbitrary:** policy with no local evidence — the code never encodes these streams, so
nothing points to bytes-with-boundary-trimming over any of the three alternatives.

### P5 — `OutputCapError` for a cap below the floor

**Behaviour.** `cap_stream` (and therefore `cap_execution_streams`) raises
`OutputCapError`, a subclass of `ValueError`, carrying attribute `max_bytes` set to the
offending value, when `max_bytes` is negative or in `1..15` — i.e. when
`max_bytes != 0 and max_bytes < MIN_MAX_OUTPUT_BYTES` with
`MIN_MAX_OUTPUT_BYTES == 16`. The check happens **before** the `data is None` check, so
`cap_stream(None, 8)` raises rather than returning.

**Alternatives a competent engineer would plausibly choose instead.**
1. No validation at all: a tiny cap just produces a tiny head and tail; the function is
   total and nothing in the repo validates helper arguments.
2. Clamp instead of raising — `max_bytes = max(max_bytes, 16)` — since raising from
   inside `_execute_in_sandbox` turns a config typo into a failed request, and
   `base_backend.handle_single_request_with_retries` would retry it `max_retries` times.
3. Raise the stock `ValueError` (or `AssertionError`) with a message and no attribute,
   which is what the rest of the codebase does when it rejects a value (e.g. the
   `RuntimeError` in `db.validate_schema`).

**The observable.** `pytest.raises(OutputCapError)` for `cap_stream(b"x", 15)`,
`cap_stream(b"x", 1)`, `cap_stream(b"x", -1)` and `cap_stream(None, 8)`; the caught
exception satisfies `exc.value.max_bytes == 15 / 1 / -1 / 8` and
`isinstance(exc.value, ValueError) is True`. `cap_stream(b"x", 16)` does **not** raise
and returns `CappedStream(text="x", truncated=False, original_bytes=1, kept_bytes=1)`.

**Arbitrary:** invented name (`OutputCapError` + its `max_bytes` attribute) and chosen
value (the floor of 16).

### P6 — `max_bytes == 0` disables capping; `None` stays `None`

**Behaviour.** `max_bytes == 0` means *unlimited*: `cap_stream` returns the whole stream
with `truncated=False` and `kept_bytes == original_bytes`, and it does **not** raise
despite `0 < 16`. `data=None` returns `CappedStream(text=None, truncated=False,
original_bytes=0, kept_bytes=0)` — the `None` is preserved, never coerced to `""` — and
`data=b""`/`""` returns `text=""`, `truncated=False`, `original_bytes=0`.

**Alternatives a competent engineer would plausibly choose instead.**
1. `0` means "keep nothing" — the literal reading — so a zero cap yields `text` equal to
   just the marker, or an empty string.
2. Spell "disabled" as `None` on the config field (`max_output_bytes: Optional[int] =
   65536`) and reject `0`, which is how optional limits are usually expressed and how
   `image` / `base_url` are expressed in this very model.
3. Normalise `None` input to `""` so downstream consumers never see a null stream —
   attractive because `CodeExecutionResult.stdout` is a non-optional `str` while
   `CodeExecutionOutput.stdout` is `Optional[str]`, and squashing `None` reconciles them.

**The observable.** `cap_stream("A" * 100000, 0)` returns
`CappedStream(text="A"*100000, truncated=False, original_bytes=100000, kept_bytes=100000)`
— `len(text) == 100000` and no `OutputCapError`. `cap_stream(None, 64)` returns
`CappedStream(None, False, 0, 0)` with `text is None`. `cap_stream("", 64)` returns
`CappedStream("", False, 0, 0)` with `text == ""`.

**Arbitrary:** policy with no local evidence — the sentinel meaning of `0` and the
`None`-preservation rule are both unwritable from the source.

### P7 — `max_output_bytes` config field, plumbed as a keyword-only parameter

**Behaviour.** `CodeExecutionBackendConfig` gains `max_output_bytes: int = Field(
default=65536, ge=0)`; `SandboxCodeExecutionBackend.__init__` copies it to
`self.max_output_bytes`; `execute_request` passes `max_output_bytes=self.max_output_bytes`
into the `partial(_execute_in_sandbox, ...)`; and `_execute_in_sandbox` accepts it as a
**keyword-only** parameter (after a bare `*`) defaulting to `DEFAULT_MAX_OUTPUT_BYTES`.
A negative value is rejected by pydantic at config construction with `ValidationError`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Put the limit on `CodeExecutionRequestParams` next to `timeout` and `memory_limit`
   — it is a per-execution resource bound exactly like those two, and it then rides
   through `CodeFormatter` into each request without touching the backend constructor.
2. Name it `max_stdout_bytes` / `max_output_size` / `output_limit_bytes`, or express it
   in kilobytes/megabytes (`max_output_kb: int = 64`) as is common for size knobs.
3. Add it as an ordinary positional parameter of `_execute_in_sandbox` (the existing five
   are all positional-or-keyword; there is no `*` in the current signature) and read
   `config.max_output_bytes` inside the function rather than at `__init__`.

**The observable.** `CodeExecutionBackendConfig().max_output_bytes == 65536` and
`DEFAULT_MAX_OUTPUT_BYTES == 65536`; `CodeExecutionBackendConfig(max_output_bytes=0)`
constructs; `pytest.raises(ValidationError)` for `max_output_bytes=-1`;
`_CodeExecutionBackendFactory.create("docker", {"max_output_bytes": 128}).max_output_bytes == 128`
and `.max_output_bytes == 65536` for `create("local", {})`;
`inspect.signature(sandbox_backend._execute_in_sandbox).parameters["max_output_bytes"].kind is inspect.Parameter.KEYWORD_ONLY`
with `.default == 65536`, and calling `_execute_in_sandbox("c", "", 10, "local", {}, 128)`
positionally raises `TypeError`.

**Arbitrary:** invented name (`max_output_bytes`, and the constant name
`DEFAULT_MAX_OUTPUT_BYTES`) + chosen value (65536).

### P8 — All four return sites cap, including the exception path

**Behaviour.** `_execute_in_sandbox` caps at every one of its four `CodeExecutionOutput`
constructions — success (`:109`), timeout `exit_code == 124` (`:117`), non-zero exit
(`:125`) and the `except Exception` path (`:137`), where the streams come from
`getattr(result, "stdout", None)` and may legitimately be `None`. The exception path
runs `cap_execution_streams` on whatever `getattr` produced and keeps `None` as `None`
(P6), so a run that produced megabytes of stdout and then blew up in `Sandbox.__exit__`
still returns a capped `stdout`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Cap once at the read site, replacing `sandbox_backend.py:105-106`
   (`stdout = result.stdout` / `stderr = result.stderr`) with capped locals. This is the
   single obvious place — one edit, three of the four sites fixed — and it leaves the
   `except` path, which never touches those locals, uncapped.
2. Cap on the way out instead: leave `_execute_in_sandbox` alone and post-process in
   `execute_request` (or in `base_backend.handle_single_request_with_retries`, which is
   the one funnel every backend's output passes through before serialisation).
3. Cap only the success path, on the theory that error and timeout outputs are already
   small and their `stderr` is diagnostic, so truncating a traceback is worse than
   keeping it.

**The observable.** A fake `Sandbox` whose `execute_command` returns
`SimpleNamespace(exit_code=0, stdout="A"*300, stderr="")` and whose `__exit__` raises
`RuntimeError("boom")`: the returned output has `message == "error"`,
`error == "boom"`, `len(output.stdout) == 64 + 30 == 94` (the marker reads `"\n[[curator:elided 236 bytes]]\n"`),
`output.stdout.endswith("A" * 16)`, `output.truncated_streams == ["stdout"]`, and
`output.stderr == ""` — with `max_output_bytes=64`. A separate fake with
`exit_code=124, stdout="A"*300` yields `message == "timeout"`,
`error == "Execution timed out after 7s"` and `len(output.stdout) == 94`.
(Alternative 1 gives `len(output.stdout) == 300` on the `__exit__`-raises case;
alternative 3 gives 300 on the timeout case.)

**Arbitrary:** policy with no local evidence — that the `except` branch, whose streams
are salvaged with `getattr` from a possibly-half-built result, is inside the cap rather
than a best-effort passthrough.

### P9 — `_format_exit_code_error` is fed the capped stderr (fixes a real leak)

**Behaviour.** On the non-zero-exit path the value passed to `_format_exit_code_error`
is the **capped** stderr text, not `result.stderr`. `_format_exit_code_error` itself is
unchanged: same signature, same `"Program exited with status code {status}\n\nError
details:\n{stderr}"` message. This closes the leak at `sandbox_backend.py:127`, where
`error=_format_exit_code_error(result.exit_code, stderr)` embeds the entire stderr in
`error`, so an implementation that caps only the `stdout`/`stderr` fields still ships an
unbounded string in `error` through `CodeExecutionResponse` and into the response file.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep passing the raw stderr — the ticket says cap *stdout and stderr*, `error` is a
   different field, and truncating the text inside a diagnostic message loses the
   traceback tail that made the error message worth building.
2. Cap `error` independently with its own (larger) budget, or cap the assembled message
   as a whole after `_format_exit_code_error` returns, so the prefix is counted too.
3. Drop the embedded details entirely when the stderr was truncated, e.g.
   `"Program exited with status code 1 (stderr truncated; see stderr field)"`.

**The observable.** Fake sandbox with `exit_code=1, stderr="E"*80, stdout=""`,
`max_output_bytes=64`: `output.error` equals exactly
`"Program exited with status code 1\n\nError details:\n" + "E"*48 + "\n[[curator:elided 16 bytes]]\n" + "E"*16`,
so `len(output.error) == 143` and `output.error == "Program exited with status code 1\n\nError details:\n" + output.stderr`.
Alternative 1 gives `len(output.error) == 130` (50 + 80). Alternative 2 gives a different
length or a different seam offset; alternative 3 gives no `"E"` run at all.

**Arbitrary:** deliberate departure — the surrounding code plainly hands
`_format_exit_code_error` the raw stderr, and the function's docstring frames it as a
descriptive message, so reading the file leads you the wrong way.

### P10 — `truncated_streams`: a sorted list on both result types

**Behaviour.** Both `CodeExecutionOutput` and `CodeExecutionResult` gain
`truncated_streams: list[str] = []` — a plain, **non-Optional** list field on models
whose every other stream-adjacent field is `Optional`. `cap_execution_streams` fills it
with the names of the streams that were actually truncated, **sorted alphabetically**,
so the value is one of `[]`, `["stderr"]`, `["stdout"]`, `["stderr", "stdout"]`. A
stream that is `None`, empty, or under budget contributes nothing. The names are exactly
`"stdout"` and `"stderr"` — no prefix, no field path.

**Alternatives a competent engineer would plausibly choose instead.**
1. A single boolean `truncated: bool = False` (or `output_truncated`) — the caller only
   needs to know "something was cut", and the marker in the text already says which.
2. Insertion order `["stdout", "stderr"]`, matching the field order in both models, the
   argument order of `cap_execution_streams`, and the order the streams are read at
   `sandbox_backend.py:105-106`.
3. Report it as a mapping of sizes instead — `truncated: dict[str, int] = {}` mapping
   stream name to bytes dropped — which is strictly more informative and carries the
   count without parsing the marker.

**The observable.** `CodeExecutionOutput().truncated_streams == []` and
`CodeExecutionResult(stdout="a", stderr="b", exit_code=0).truncated_streams == []`
(field present on both, defaulting to an empty list, and
`CodeExecutionOutput.model_fields["truncated_streams"].is_required() is False`);
`cap_execution_streams("A"*300, "B"*300, 64).truncated_streams == ["stderr", "stdout"]`
(exactly this order — alternative 2 gives `["stdout", "stderr"]`);
`cap_execution_streams("A"*300, None, 64).truncated_streams == ["stdout"]`;
`cap_execution_streams("a", "b", 64).truncated_streams == []`;
and after a `CodeExecutionResponse(exec_output=output).model_dump()` round trip the key
`"truncated_streams"` is present under `exec_output` with the same list.

**Arbitrary:** invented name (`truncated_streams`, the exact member strings) + policy
(alphabetical ordering; non-Optional on models that are otherwise Optional).

## End to end

**Input.** A fake sandbox, no container and no subprocess:

```python
import sys
from types import ModuleType, SimpleNamespace
from bespokelabs.curator.code_executor.code_execution_backend import sandbox_backend


class FakeSandbox:
    def __init__(self, backend_name, **kwargs): ...
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    def write_file(self, path, content): ...
    def execute_command(self, command, args=None):
        return SimpleNamespace(exit_code=1, stdout="0123456789" * 10, stderr="E" * 80)


module = ModuleType("bespokelabs.sandbox")
module.Sandbox = FakeSandbox
monkeypatch.setitem(sys.modules, "bespokelabs.sandbox", module)
monkeypatch.setattr(sandbox_backend, "_collect_sandbox_files", lambda sandbox: "files-archive")

output = sandbox_backend._execute_in_sandbox(
    code="print('hi')",
    code_input="",
    timeout=10,
    backend_name="local",
    sandbox_kwargs={},
    max_output_bytes=64,
)
```

**Expected output**, as literals:

```python
output.message == "error"

output.stdout == (
    "012345678901234567890123456789012345678901234567"
    "\n[[curator:elided 36 bytes]]\n"
    "4567890123456789"
)                                  # len == 93  (48 + 29 + 16)

output.stderr == (
    "E" * 48
    + "\n[[curator:elided 16 bytes]]\n"
    + "E" * 16
)                                  # len == 93  (48 + 29 + 16)

output.error == (
    "Program exited with status code 1\n\nError details:\n"
    + output.stderr
)                                  # len == 143 (50 + 93)

output.truncated_streams == ["stderr", "stdout"]
output.files == "files-archive"
```

and the corresponding direct calls on the capping layer:

```python
cap_stream("0123456789" * 10, 64) == CappedStream(
    text="012345678901234567890123456789012345678901234567"
         "\n[[curator:elided 36 bytes]]\n"
         "4567890123456789",
    truncated=True,
    original_bytes=100,
    kept_bytes=64,
)

cap_stream(b"E" * 80, 64).kept_bytes == 64
cap_stream(b"E" * 80, 64).original_bytes == 80
cap_stream("€" * 10, 20) == CappedStream("€€€€€\n[[curator:elided 12 bytes]]\n€", True, 30, 18)
cap_stream("A" * 100000, 0) == CappedStream("A" * 100000, False, 100000, 100000)
cap_stream(None, 64) == CappedStream(None, False, 0, 0)
cap_stream(b"x", 15)          # raises OutputCapError, .max_bytes == 15

cap_execution_streams("0123456789" * 10, "E" * 80, 64) == StreamCapReport(
    stdout="012345678901234567890123456789012345678901234567"
           "\n[[curator:elided 36 bytes]]\n"
           "4567890123456789",
    stderr="E" * 48 + "\n[[curator:elided 16 bytes]]\n" + "E" * 16,
    truncated_streams=["stderr", "stdout"],
)
```

Everything above is a pure function of its arguments: no network, no sleeping, no
threads (`execute_request`'s `ThreadPoolExecutor` is not exercised — `_execute_in_sandbox`
is called directly), no subprocess, no clock, no randomness, no dict iteration order.
