"""g2 — the openly stated feature: a configurable byte budget on sandbox output.

The ticket names every surface asserted here: `max_output_bytes` on
`CodeExecutionBackendConfig` (default 65536, `ge=0`), reachable through the
existing `CodeExecutionBackendConfig(**backend_params)` in `_factory.py` for
every backend name; `DEFAULT_MAX_OUTPUT_BYTES` out of the new `output_cap`
module; the keyword-only `max_output_bytes` parameter of `_execute_in_sandbox`,
applied at all four `CodeExecutionOutput` construction sites, with the capped
stderr handed to an otherwise untouched `_format_exit_code_error`; and a
`truncated_streams: list[str] = []` on both `CodeExecutionResult` and
`CodeExecutionOutput` that survives `CodeExecutionResponse(...).model_dump()`.

This file also holds the fake-`bespokelabs.sandbox` seam the r1/r2 suites import
— the same seam `tests/code_executor/test_sandbox_backend.py` already uses, so no
container, no subprocess and no clock is involved anywhere in this suite.

Nothing here asserts *where* the budget cuts, how the elision reads, what a
sub-floor budget does, what gets logged, or whether `error` is capped: those are
r1's and r2's hidden facts, and an implementation that gets every one of them
wrong still passes below as long as an over-budget stream comes back shortened.
"""
from __future__ import annotations

import inspect
import sys
from types import ModuleType, SimpleNamespace

import pytest
from pydantic import ValidationError

from harness import read_field, surface

from bespokelabs.curator.code_executor.code_execution_backend import sandbox_backend
from bespokelabs.curator.code_executor.code_execution_backend._factory import _CodeExecutionBackendFactory
from bespokelabs.curator.code_executor.types import (
    CodeExecutionBackendConfig,
    CodeExecutionOutput,
    CodeExecutionResponse,
    CodeExecutionResult,
)

FILES = "files-archive"


# ---------------------------------------------------------------------------
# The fake sandbox seam, shared with test_r1.py and test_r2.py
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


# =============================================================================
# the open feature — a configurable budget, plumbed and applied
# =============================================================================
def test_open_feature__a_configurable_byte_budget_shortens_what_the_sandbox_returns(monkeypatch):
    # The ticket's knob is `backend_params`; the whole suite reads the budget it
    # was handed, never an ambient one.
    monkeypatch.delenv("CURATOR_MAX_OUTPUT_BYTES", raising=False)

    # --- the new module, and the default the ticket spells out -------------
    from bespokelabs.curator.code_executor import output_cap

    assert output_cap.DEFAULT_MAX_OUTPUT_BYTES == 65536

    # --- the config field, and its pydantic floor -------------------------
    assert "max_output_bytes" in CodeExecutionBackendConfig.model_fields, (
        f"CodeExecutionBackendConfig has no max_output_bytes; it has {sorted(CodeExecutionBackendConfig.model_fields)}"
    )
    assert CodeExecutionBackendConfig().max_output_bytes == 65536
    assert CodeExecutionBackendConfig(max_output_bytes=0).max_output_bytes == 0
    assert CodeExecutionBackendConfig(max_output_bytes=128).max_output_bytes == 128
    with pytest.raises(ValidationError):
        CodeExecutionBackendConfig(max_output_bytes=-1)

    # --- reachable through the untouched factory, for every backend name ---
    for name in ("local", "docker", "e2b", "modal", "daytona", "multiprocessing"):
        backend = _CodeExecutionBackendFactory.create(name, {"max_output_bytes": 128})
        assert read_field(backend, "max_output_bytes") == 128, f"the {name} backend does not carry the budget; it has {surface(backend)}"
    assert read_field(_CodeExecutionBackendFactory.create("local", {}), "max_output_bytes") == 65536

    # --- keyword-only on the module-level function ------------------------
    params = inspect.signature(sandbox_backend._execute_in_sandbox).parameters
    assert "max_output_bytes" in params, f"_execute_in_sandbox takes {list(params)}"
    assert params["max_output_bytes"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["max_output_bytes"].default == 65536

    # --- the new field on both result types, and through model_dump -------
    for model, instance in (
        (CodeExecutionOutput, CodeExecutionOutput()),
        (CodeExecutionResult, CodeExecutionResult(stdout="a", stderr="b", exit_code=0)),
    ):
        assert "truncated_streams" in model.model_fields, f"{model.__name__} has {sorted(model.model_fields)}"
        assert model.model_fields["truncated_streams"].is_required() is False
        assert read_field(instance, "truncated_streams") == []
    dumped = CodeExecutionResponse(exec_output=CodeExecutionOutput(stdout="a")).model_dump()
    assert dumped["exec_output"]["truncated_streams"] == []

    # --- an over-budget run comes back shortened, and says so -------------
    install_sandbox(monkeypatch, exit_code=0, stdout="A" * 300, stderr="B" * 300)
    with pytest.raises(TypeError):  # the budget is keyword-only; a sixth positional is refused
        sandbox_backend._execute_in_sandbox("print('hi')", "", 10, "local", {}, 64)

    capped = execute(max_output_bytes=64)
    assert capped.message == "success"
    assert 0 < len(capped.stdout) < 300, f"stdout came back at {len(capped.stdout)} chars under a 64-byte budget"
    assert 0 < len(capped.stderr) < 300, f"stderr came back at {len(capped.stderr)} chars under a 64-byte budget"
    # both names, whatever order they are reported in: the ticket asks the field to
    # NAME the shortened streams, and r1 is where the order of the report is graded
    assert sorted(read_field(capped, "truncated_streams")) == ["stderr", "stdout"]
    assert capped.files == FILES

    # --- all four construction sites obey the budget ----------------------
    sites = {
        "success": run(monkeypatch, exit_code=0, stdout="A" * 300, max_output_bytes=64),
        "timeout": run(monkeypatch, exit_code=124, stdout="A" * 300, timeout=7, max_output_bytes=64),
        "non-zero exit": run(monkeypatch, exit_code=1, stdout="A" * 300, max_output_bytes=64),
        # a run that produced megabytes and then blew up on the way out of the
        # `with`: `result` is populated, but no in-`with` return ever happened
        "exception": run(monkeypatch, exit_code=0, stdout="A" * 300, exit_error=RuntimeError("boom"), max_output_bytes=64),
    }
    for site, out in sites.items():
        assert out.stdout is not None, f"the {site} site returned no stdout at all"
        assert 0 < len(out.stdout) < 300, f"the {site} site returned {len(out.stdout)} characters under a 64-byte budget"

    # --- the exit-code message carries the capped stderr, unchanged wording -
    failed = run(monkeypatch, exit_code=1, stdout="", stderr="E" * 300, max_output_bytes=64)
    assert len(failed.stderr) < 300
    assert failed.error == "Program exited with status code 1\n\nError details:\n" + failed.stderr, (
        f"`error` does not embed the capped stderr:\nerror={failed.error!r}\nstderr={failed.stderr!r}"
    )
    assert list(inspect.signature(sandbox_backend._format_exit_code_error).parameters) == ["exit_code", "stderr"]
    assert sandbox_backend._format_exit_code_error(3, "boom") == "Program exited with status code 3\n\nError details:\nboom"

    # --- an under-budget run is untouched, and `files` is never capped -----
    untouched = run(monkeypatch, exit_code=0, stdout="A" * 300, stderr="", files="F" * 5000)
    assert untouched.stdout == "A" * 300
    assert untouched.files == "F" * 5000
    assert read_field(untouched, "truncated_streams") == []
