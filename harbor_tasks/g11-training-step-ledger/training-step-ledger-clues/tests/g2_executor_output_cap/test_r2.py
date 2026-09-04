"""g2 — hidden requirement r2: the cap reaches `error`, on one path only.

    rule        the `except Exception` path runs `str(e)` through the same budget and the same
                head/tail+marker rule as a stream, and `CodeExecutionOutput` carries a
                non-Optional `error_truncated: bool = False` declared right after
                `truncated_streams`, set True on exactly that path
    scope       nothing else is capped: the non-zero-exit message keeps its full assembled
                length (prefix included, never re-capped), the timeout message is never
                touched however small the budget, and `files` is not capped — with
                `error_truncated` False on both of those paths
    exclusions  the flag lives on `CodeExecutionOutput` alone, `CodeExecutionResult` does not
                gain it, and "error" never joins `truncated_streams`
    observability  the three runs the requirement spells out, as literals

`rule` uses a 200-byte message under a 32-byte budget and `observability` the requirement's
own 300-byte message under a 64-byte one, so the two are not the same measurement twice.
`scope` asserts the exit-code message against whatever stderr the output carries rather
than against a literal, so it charges only the "not re-capped" fact and leaves the shape of
the cut to r1.
"""
from __future__ import annotations

from harness import read_field, require_feature

from bespokelabs.curator.code_executor.types import (
    CodeExecutionOutput,
    CodeExecutionResponse,
    CodeExecutionResult,
)

from test_open import run

BIG = "A" * 300
EXIT_PREFIX = "Program exited with status code 1\n\nError details:\n"


# =============================================================================
# rule — the exception message is capped like a stream, and says so
# =============================================================================
def test_rule__the_exception_message_is_capped_and_flagged_by_error_truncated(monkeypatch):
    fields = list(CodeExecutionOutput.model_fields)
    assert "error_truncated" in fields, f"CodeExecutionOutput has {fields}"
    assert CodeExecutionOutput.model_fields["error_truncated"].is_required() is False
    assert CodeExecutionOutput.model_fields["error_truncated"].annotation is bool, "error_truncated is a plain bool, not an Optional one"
    assert CodeExecutionOutput().error_truncated is False
    assert fields.index("error_truncated") == fields.index("truncated_streams") + 1, f"error_truncated is not declared right after truncated_streams: {fields}"

    # 200 characters of exception text under a 32-byte budget: 24 head, 8 tail,
    # 168 thrown away — the same rule a stream gets.
    blew_up = run(monkeypatch, exit_code=0, stdout="", stderr="", exit_error=RuntimeError("Z" * 200), max_output_bytes=32)
    assert blew_up.message == "error"
    assert blew_up.error == "Z" * 24 + "\n[[curator:elided 168 bytes]]\n" + "Z" * 8, f"the exception message was not capped the way a stream is: {blew_up.error!r}"
    assert len(blew_up.error) == 32 + 30 == 62  # the marker, three digits wide here, is charged outside the budget
    assert read_field(blew_up, "error_truncated") is True


# =============================================================================
# scope — only that one error value; the other two, and files, are untouched
# =============================================================================
def test_scope__the_exit_code_and_timeout_messages_and_files_are_never_capped(monkeypatch):
    # the assembled exit-code message keeps its 50-character prefix and its full
    # length: it embeds a capped stderr, but is not itself run through the budget
    failed = run(monkeypatch, exit_code=1, stdout="", stderr="E" * 200, files="F" * 5000, max_output_bytes=32)
    require_feature(len(failed.stderr) < 200, "the stdout/stderr byte cap")
    assert failed.error == EXIT_PREFIX + failed.stderr, f"`error` is not the message assembled from the capped stderr:\nerror={failed.error!r}\nstderr={failed.stderr!r}"
    assert len(failed.error) == len(failed.stderr) + 50 > 32, f"the assembled message was re-capped, to {len(failed.error)} characters"
    assert read_field(failed, "error_truncated") is False, "error_truncated is set on the non-zero-exit path, whose message was assembled rather than clipped"
    assert failed.files == "F" * 5000, f"files was shortened to {len(failed.files)} characters; it is not part of this feature"

    # curator's own timeout text, under a budget it is twice the size of
    timed_out = run(monkeypatch, exit_code=124, stdout="ok", stderr="", timeout=7, max_output_bytes=16)
    assert timed_out.message == "timeout"
    assert timed_out.error == "Execution timed out after 7s", f"the timeout message went through the cap: {timed_out.error!r}"
    assert read_field(timed_out, "error_truncated") is False

    # and files survives the salvage path too
    salvaged = run(monkeypatch, exit_code=0, stdout=BIG, stderr="", files="F" * 5000, exit_error=RuntimeError("boom"), max_output_bytes=64)
    assert salvaged.files == "F" * 5000, f"files was shortened on the exception path, to {len(salvaged.files)} characters"


# =============================================================================
# exclusions — one model, one field, and never a third stream name
# =============================================================================
def test_exclusions__the_flag_is_on_the_output_model_alone_and_never_a_stream_name(monkeypatch):
    require_feature("error_truncated" in CodeExecutionOutput.model_fields, "the error_truncated flag on CodeExecutionOutput")
    assert "error_truncated" not in CodeExecutionResult.model_fields, f"CodeExecutionResult gained the flag as well: {sorted(CodeExecutionResult.model_fields)}"

    dumped = CodeExecutionResponse(exec_output=CodeExecutionOutput(error="x", error_truncated=True)).model_dump()
    assert sorted(dumped["exec_output"]) == ["error", "error_truncated", "files", "message", "stderr", "stdout", "truncated_streams"]

    # a run whose stdout AND whose error were both cut still names only the stream
    both = run(monkeypatch, exit_code=0, stdout=BIG, stderr="", exit_error=RuntimeError("X" * 300), max_output_bytes=64)
    assert read_field(both, "error_truncated") is True
    assert read_field(both, "truncated_streams") == ["stdout"], f'"error" leaked into truncated_streams: {read_field(both, "truncated_streams")}'

    failed = run(monkeypatch, exit_code=1, stdout="", stderr="E" * 300, max_output_bytes=64)
    assert read_field(failed, "truncated_streams") == ["stderr"]


# =============================================================================
# observability — the three runs the requirement spells out
# =============================================================================
def test_observability__the_exact_error_text_and_flag_of_the_three_named_runs(monkeypatch):
    blew_up = run(monkeypatch, exit_code=0, stdout=BIG, stderr="", exit_error=RuntimeError("X" * 300), max_output_bytes=64)
    assert blew_up.error == "X" * 48 + "\n[[curator:elided 236 bytes]]\n" + "X" * 16
    assert len(blew_up.error) == 94
    assert read_field(blew_up, "error_truncated") is True

    short = run(monkeypatch, exit_code=0, stdout=BIG, stderr="", exit_error=RuntimeError("boom"), max_output_bytes=64)
    assert short.error == "boom", f"a message within budget was rewritten: {short.error!r}"
    assert read_field(short, "error_truncated") is False, "error_truncated is set for a message the cap never shortened"

    failed = run(monkeypatch, exit_code=1, stdout="", stderr="E" * 80, max_output_bytes=64)
    assert len(failed.error) == 143, f"error is {len(failed.error)} characters; 130 means the raw stderr went into the message, 94 means it was re-capped"
    assert failed.error == EXIT_PREFIX + "E" * 48 + "\n[[curator:elided 16 bytes]]\n" + "E" * 16
    assert read_field(failed, "error_truncated") is False
    assert read_field(failed, "truncated_streams") == ["stderr"]
