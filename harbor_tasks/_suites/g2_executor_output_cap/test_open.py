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

The fake-`bespokelabs.sandbox` seam the r1/r2 suites import — the same seam
`tests/code_executor/test_sandbox_backend.py` already uses — now lives in
`probe_support.py`, so no container, no subprocess and no clock is involved
anywhere in this suite, and the worker (`probe.py`) and this human reference
share ONE definition of the seam and cannot drift. The names are re-exported
below so `from test_open import install_sandbox, run` keeps working.

Two things this file no longer records on its own, because they cannot run here.
The suite is graded by `probe.py` + `judge.py`, and `judge.py` also checks what
only the root side can see: that `output_cap.py` declares
`DEFAULT_MAX_OUTPUT_BYTES = 65536` and imports no clock, randomness, I/O or
environment module; that `_execute_in_sandbox`'s pushed signature is the one the
ticket writes; that `execute_request` passes `max_output_bytes=` into the partial
it builds (no test here calls that async path); and that `_collect_sandbox_files`
is AST-identical to the pristine tree, which needs the baseline copy root stages
as CURATOR_BASELINE_DIR and which this seam deliberately patches out. The inputs
below are the ORIGINAL fixed fixture, kept as the worked example; the graded run
re-draws them per seed from `fixture_spec.py`.

Nothing here asserts *where* the budget cuts, how the elision reads, what a
sub-floor budget does, what gets logged, or whether `error` is capped: those are
r1's and r2's hidden facts, and an implementation that gets every one of them
wrong still passes below as long as an over-budget stream comes back shortened.
"""
from __future__ import annotations

import inspect

import pytest
from pydantic import ValidationError

from harness import read_field, surface

# The answer-free seam/inputs live in probe_support so the worker (probe.py) and
# this human reference share ONE definition and cannot drift. The expected
# VALUES this test asserts stay here (and in judge.py); probe_support holds none.
from probe_support import (  # noqa: F401 - install_sandbox/run are re-exported for test_r1/test_r2
    FILES,
    CodeExecutionBackendConfig,
    CodeExecutionOutput,
    CodeExecutionResponse,
    CodeExecutionResult,
    _CodeExecutionBackendFactory,
    execute,
    install_sandbox,
    run,
    sandbox_backend,
)


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
    # both names, in the order the ticket asks for them: "sorted alphabetically"
    # (instruction.md:31-32). Asserted as a list, not through `sorted()` — the
    # sorted comparison this line used to make graded the test rather than the
    # submission, and ["stdout", "stderr"] passed it. r1's observability fact
    # grades the ordering inside the WARNING line; this is the model field.
    assert read_field(capped, "truncated_streams") == ["stderr", "stdout"]
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

    # --- the salvage site with nothing to salvage --------------------------
    # `execute_command` itself raises, so `result` is still None and the ticket's
    # own expression -- `getattr(result, "stdout", None)`, instruction.md:56 --
    # comes back None on both streams; a None stream "contributes nothing" to
    # truncated_streams (instruction.md:32), and `files` is still collected.
    never = run(monkeypatch, command_error=RuntimeError("boom"), files=FILES, max_output_bytes=64)
    assert never.stdout is None, f"the salvage site returned stdout={never.stdout!r} on a run that captured nothing"
    assert never.stderr is None, f"the salvage site returned stderr={never.stderr!r} on a run that captured nothing"
    assert read_field(never, "truncated_streams") == []
    assert never.files == FILES

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
