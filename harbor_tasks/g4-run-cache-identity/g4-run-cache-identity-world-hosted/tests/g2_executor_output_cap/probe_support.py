"""g2 — answer-free scenario helpers shared by the worker (probe.py) and the
human reference (test_open.py).

This module holds ONLY the curator imports, the fake-`bespokelabs.sandbox` seam,
the scenario drivers and the answer-free plumbing the probe needs; it contains NO
expected-output value. That is load-bearing: `run_split` copies this file into
the worker's jail, so it is inside the process that runs agent code. If any
reward-bearing expected value ever appeared here — the elision marker, the floor
16, an `OutputCapError` message, the warning-line template, the `error_truncated`
semantics — a forging worker could read it and hand back an `observations.json`
that matches the judge without implementing the requirement. Those answers live
only in `judge.py` (and, for humans, in `test_open.py`), which the worker cannot
read.

The only literals here are scenario INPUTS: `FILES` (the archive the sandbox
returns), `DIGITS`/`BIG` (streams fed in), and the budgets/streams passed to
`run`. A budget of 16 or 32 here is a value handed to the code under test, never
the fact that 16 is the floor.

`test_open.py` imports these names so there is a single definition of each helper
— the probe cannot drift from the reference — and the r1/r2 suites keep importing
the seam through `test_open` (`from test_open import install_sandbox, run`).
"""
from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

from bespokelabs.curator.code_executor.code_execution_backend import sandbox_backend
from bespokelabs.curator.code_executor.code_execution_backend._factory import _CodeExecutionBackendFactory
from bespokelabs.curator.code_executor.types import (
    CodeExecutionBackendConfig,
    CodeExecutionOutput,
    CodeExecutionResponse,
    CodeExecutionResult,
)

# Scenario INPUTS (not answers). FILES is the archive the fake sandbox hands
# back; the suite asserts it is NEVER capped, so it is fed in and read out.
FILES = "files-archive"
DIGITS = "0123456789" * 10  # 100 ASCII bytes, an over-budget stream
BIG = "A" * 300


# ---------------------------------------------------------------------------
# The fake sandbox seam, shared with test_open / test_r1 / test_r2
# ---------------------------------------------------------------------------
def install_sandbox(
    monkeypatch,
    *,
    exit_code: int = 0,
    stdout: str = "",
    stderr: str = "",
    files: str = FILES,
    command_error: BaseException | None = None,
    exit_error: BaseException | None = None,
):
    """Install a fake `bespokelabs.sandbox` that returns exactly what it is given.

    `command_error` makes `execute_command` raise (so the backend's `except`
    branch sees `result is None`); `exit_error` makes `Sandbox.__exit__` raise
    (so that branch sees a fully populated result).
    """

    class FakeSandbox:
        def __init__(self, backend_name, **kwargs):
            self.backend_name = backend_name
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            if exit_error is not None:
                raise exit_error
            return False

        def write_file(self, path, content):
            pass

        def execute_command(self, command, args=None):
            if command_error is not None:
                raise command_error
            return SimpleNamespace(exit_code=exit_code, stdout=stdout, stderr=stderr)

    module = ModuleType("bespokelabs.sandbox")
    module.Sandbox = FakeSandbox
    monkeypatch.setitem(sys.modules, "bespokelabs.sandbox", module)
    monkeypatch.setattr(sandbox_backend, "_collect_sandbox_files", lambda sandbox: files)
    # every run in this suite is judged on the budget it was handed, never on an
    # ambient one; nothing here sets this variable, so nothing may inherit it
    monkeypatch.delenv("CURATOR_MAX_OUTPUT_BYTES", raising=False)


def execute(*, timeout: int = 10, max_output_bytes=None):
    """Call `_execute_in_sandbox` directly; omit the budget entirely when None."""
    kwargs = {} if max_output_bytes is None else {"max_output_bytes": max_output_bytes}
    return sandbox_backend._execute_in_sandbox(
        code="print('hi')",
        code_input="",
        timeout=timeout,
        backend_name="local",
        sandbox_kwargs={},
        **kwargs,
    )


def run(monkeypatch, *, timeout: int = 10, max_output_bytes=None, **sandbox):
    """Install the fake sandbox and run one execution through it."""
    install_sandbox(monkeypatch, **sandbox)
    return execute(timeout=timeout, max_output_bytes=max_output_bytes)


# ---------------------------------------------------------------------------
# Observability plumbing — answer-free (holds no template text, only records it)
# ---------------------------------------------------------------------------
class LogRecorder:
    """A stand-in for the package's `logger` that keeps the warnings.

    Records whatever the implementation says; it fixes no wording of its own.
    """

    def __init__(self):
        self.warnings: list[str] = []

    def warning(self, message, *args, **kwargs):
        self.warnings.append(message % args if args else message)

    def log(self, level, message, *args, **kwargs):  # logger.log(logging.WARNING, ...) counts too
        if int(level) >= 30:
            self.warning(message, *args)

    def __getattr__(self, name):  # debug/info/error/exception — recorded by nobody
        return lambda *args, **kwargs: None


def warnings_of(monkeypatch, **run_kwargs) -> list[str]:
    """The WARNING lines one capped run emits, from wherever the package logs.

    Every module in the package that holds a `logger`, not just the sandbox
    backend: which file the warning is emitted from is not the requirement, so
    one recorder is installed across all of them and "exactly once" still means
    once in total. Answer-free — it returns whatever was said and asserts
    nothing about it.
    """
    recorder = LogRecorder()
    for module in list(sys.modules.values()):
        name = getattr(module, "__name__", "")
        if name.startswith("bespokelabs.curator.code_executor") and hasattr(module, "logger"):
            monkeypatch.setattr(module, "logger", recorder, raising=False)
    run(monkeypatch, **run_kwargs)
    return recorder.warnings
