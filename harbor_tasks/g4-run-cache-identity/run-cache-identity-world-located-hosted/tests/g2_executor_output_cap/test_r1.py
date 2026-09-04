"""g2 — hidden requirement r1: the shape of the cut, and what it says about itself.

    rule              head and tail are kept at 3:1 — the first `(max_output_bytes * 3) // 4`
                      bytes and the last `max_output_bytes - (max_output_bytes * 3) // 4` —
                      spliced by exactly `"\\n[[curator:elided {dropped} bytes]]\\n"`, whose
                      length is charged OUTSIDE the budget and whose count is the bytes
                      actually thrown away
    scope             the budget is on the UTF-8 encoding, and both slices are pulled back to
                      codepoint boundaries before decoding, so a clean multi-byte stream never
                      yields "�" and fewer bytes than the budget may survive
    exclusions        `max_output_bytes == 0` means unlimited, not "keep nothing"; a stream at
                      or under the budget comes back byte-identical and unlisted
    failure_behavior  `MIN_MAX_OUTPUT_BYTES == 16`, and a budget that is neither 0 nor >= 16 is
                      refused by `OutputCapError` — at request time from `_execute_in_sandbox`,
                      and up front from `CodeExecutionBackendConfig`
    observability     `TRUNCATION_LOG_TEMPLATE`, emitted at WARNING level exactly once per
                      capped run and never on the salvage path — from wherever in the
                      package the implementation chose to put the call

Every fact is graded through `_execute_in_sandbox` — a name the ticket states — except the
two the requirement spells by name (`OutputCapError` / `MIN_MAX_OUTPUT_BYTES` in
`failure_behavior`, `TRUNCATION_LOG_TEMPLATE` in `observability`), which the requirement
puts in `output_cap.py` itself. `rule` pins the ratio with two budgets; `scope` uses a
multi-byte stream and a budget under which every plausible split keeps the same 18 bytes,
so it measures boundary trimming rather than where the cut falls.
"""
from __future__ import annotations

import re
import sys

import pytest
from pydantic import ValidationError

from harness import read_field, require_feature

from bespokelabs.curator.code_executor.code_execution_backend import sandbox_backend
from bespokelabs.curator.code_executor.code_execution_backend._factory import _CodeExecutionBackendFactory
from bespokelabs.curator.code_executor.types import CodeExecutionBackendConfig

from test_open import install_sandbox, run

DIGITS = "0123456789" * 10  # 100 ASCII bytes


class LogRecorder:
    """A stand-in for the package's `logger` that keeps the warnings."""

    def __init__(self):
        self.warnings: list[str] = []

    def warning(self, message, *args, **kwargs):
        self.warnings.append(message % args if args else message)

    def log(self, level, message, *args, **kwargs):  # logger.log(logging.WARNING, ...) counts too
        if int(level) >= 30:
            self.warning(message, *args)

    def __getattr__(self, name):  # debug/info/error/exception — recorded by nobody
        return lambda *args, **kwargs: None


# =============================================================================
# rule — 3:1 head/tail, the exact marker, and the marker outside the budget
# =============================================================================
def test_rule__the_kept_head_and_tail_split_three_to_one_around_an_elision_marker(monkeypatch):
    wide = run(monkeypatch, exit_code=0, stdout=DIGITS, stderr="", max_output_bytes=64)

    head = DIGITS[:48]  # (64 * 3) // 4
    tail = DIGITS[-16:]  # 64 - 48
    marker = "\n[[curator:elided 36 bytes]]\n"  # 100 in, 64 kept, no thousands separator

    assert wide.stdout == head + marker + tail, f"expected a 48-byte head and a 16-byte tail spliced by the elision marker, got:\n{wide.stdout!r}"
    # the marker is charged outside the budget: longer than the cap by exactly its length
    assert len(marker) == 29
    assert len(wide.stdout) == 64 + 29 == 93
    assert wide.stdout.index(marker) == 48

    # a second budget, so the 3:1 ratio is pinned rather than fitted to one number
    narrow = run(monkeypatch, exit_code=0, stdout=DIGITS, stderr="", max_output_bytes=32)
    assert narrow.stdout == DIGITS[:24] + "\n[[curator:elided 68 bytes]]\n" + DIGITS[-8:], f"a 32-byte budget did not split 24/8: {narrow.stdout!r}"
    assert len(narrow.stdout) == 32 + 29 == 61


# =============================================================================
# scope — bytes, with both slices pulled back to codepoint boundaries
# =============================================================================
def test_scope__the_budget_counts_utf8_bytes_and_both_slices_land_on_codepoints(monkeypatch):
    # "€" is three bytes: 10 characters, 30 bytes. A 20-byte budget is over the
    # limit in bytes and comfortably under it in characters, so a character cap
    # would return the stream whole. Whatever the split policy, trimming to
    # codepoint boundaries keeps 18 of the 20 budgeted bytes — six characters —
    # because every 20-byte window of this stream straddles a codepoint at one
    # end or the other.
    data = "€" * 10
    out = run(monkeypatch, exit_code=0, stdout=data, stderr="", max_output_bytes=20)

    assert out.stdout != data, "10 characters / 30 bytes came back whole under a 20-BYTE budget"
    assert "�" not in out.stdout, f"a clean UTF-8 stream came back with a replacement character: {out.stdout!r}"
    assert out.stdout.count("€") == 6, f"expected the 18 decodable bytes of a 20-byte budget, got {out.stdout.count(chr(0x20ac))} characters: {out.stdout!r}"
    assert read_field(out, "truncated_streams") == ["stdout"]

    # The retained byte count is only visible in the count the elision reports,
    # so this is the one window scope has on it: 12 bytes were thrown away, not
    # 10, because trimming gave back two of the twenty budgeted bytes. Every
    # head/tail policy that trims agrees on 12; only an implementation that
    # counts the untrimmed slice (decoding it with errors="ignore" or
    # errors="replace") reports 10.
    reported = re.findall(r"\d+", out.stdout)
    assert "12" in reported, f"the elided-byte count reads {reported}; 18 of the 30 bytes survived, so 12 were dropped: {out.stdout!r}"


# =============================================================================
# exclusions — 0 is unlimited, and anything within budget is left alone
# =============================================================================
def test_exclusions__a_zero_budget_is_unlimited_and_streams_within_budget_are_untouched(monkeypatch):
    over = run(monkeypatch, exit_code=0, stdout="A" * 300, stderr="", max_output_bytes=64)
    require_feature(len(over.stdout) < 300, "the stdout/stderr byte cap")

    # 0 keeps everything rather than nothing, and does not trip the floor below
    unlimited = run(monkeypatch, exit_code=0, stdout="A" * 300, stderr="B" * 500, max_output_bytes=0)
    assert unlimited.stdout == "A" * 300, f"a budget of 0 cut the stream to {len(unlimited.stdout)} characters"
    assert unlimited.stderr == "B" * 500
    assert read_field(unlimited, "truncated_streams") == []

    under = run(monkeypatch, exit_code=0, stdout=DIGITS[:60], stderr="", max_output_bytes=64)
    assert under.stdout == DIGITS[:60]
    assert under.stderr == "", f'an empty stderr was not preserved as "": {under.stderr!r}'
    assert read_field(under, "truncated_streams") == []

    exactly = run(monkeypatch, exit_code=0, stdout="A" * 64, stderr="", max_output_bytes=64)
    assert exactly.stdout == "A" * 64, "a stream exactly at the budget was shortened"
    assert read_field(exactly, "truncated_streams") == []


# =============================================================================
# failure_behavior — the floor of 16, refused by name and refused up front
# =============================================================================
def test_failure_behavior__a_budget_below_the_floor_of_sixteen_is_refused_by_outputcaperror(monkeypatch):
    # The requirement names this module, this class and this constant.
    from bespokelabs.curator.code_executor.output_cap import MIN_MAX_OUTPUT_BYTES, OutputCapError

    assert MIN_MAX_OUTPUT_BYTES == 16
    assert issubclass(OutputCapError, ValueError)

    # The raised object, never a constructor call. This used to say
    # `OutputCapError(8)`, which grades an ARITY the corpus never states: konrad
    # settles that the value has to be readable off the exception instead of
    # regexed out of the sentence -- "we hang the offending value on the
    # exception as .max_bytes and the message can keep saying whatever it says"
    # -- and says nothing about how it is built. A `__init__(self, message,
    # max_bytes)` raised as `OutputCapError(f"...got {v}", v)` satisfies every
    # word of that and died here on a TypeError, losing the fact while passing
    # its every other assertion. Same reasoning as the relaxation in the
    # observability test below: grade what the world argued for.
    #
    # at request time
    install_sandbox(monkeypatch, exit_code=0, stdout="A" * 300, stderr="")
    with pytest.raises(OutputCapError) as refused:
        sandbox_backend._execute_in_sandbox(code="print('hi')", code_input="", timeout=10, backend_name="local", sandbox_kwargs={}, max_output_bytes=8)
    assert refused.value.max_bytes == 8
    assert str(refused.value) == "max_bytes must be 0 or at least 16, got 8"

    assert run(monkeypatch, exit_code=0, stdout="A" * 300, stderr="", max_output_bytes=16).message == "success", "16 is the floor and must be accepted"

    # and up front, so a typo fails once at construction instead of per row
    monkeypatch.delenv("CURATOR_MAX_OUTPUT_BYTES", raising=False)
    for bad in (1, 8, 15):
        with pytest.raises(ValidationError) as rejected:
            CodeExecutionBackendConfig(max_output_bytes=bad)
        assert f"max_bytes must be 0 or at least 16, got {bad}" in str(rejected.value), f"the rejection of {bad} does not carry the OutputCapError message: {rejected.value}"
    with pytest.raises(ValidationError):
        _CodeExecutionBackendFactory.create("docker", {"max_output_bytes": 8})

    assert CodeExecutionBackendConfig(max_output_bytes=0).max_output_bytes == 0
    assert CodeExecutionBackendConfig(max_output_bytes=16).max_output_bytes == 16
    with pytest.raises(ValidationError):
        CodeExecutionBackendConfig(max_output_bytes=-1)


# =============================================================================
# observability — one warning line per capped run, from the shared template
# =============================================================================
def test_observability__one_warning_line_per_capped_run_from_the_shared_template(monkeypatch):
    from bespokelabs.curator.code_executor.output_cap import TRUNCATION_LOG_TEMPLATE

    assert TRUNCATION_LOG_TEMPLATE.format(streams="stderr, stdout", budget=64) == "sandbox output capped: stderr, stdout exceeded the 64-byte budget"

    def warnings_of(**run_kwargs) -> list[str]:
        # Every module in the package that holds a `logger`, not just the sandbox
        # backend. Which file the warning is emitted from is not the requirement —
        # an implementation that logs from inside the capping helper says exactly
        # the same thing at exactly the same moment, and the corpus points there as
        # hard as it points anywhere ("we log where we cut", and the template lives
        # in output_cap.py). Grading the call's address made a behaviourally
        # identical build fail this fact and pass the other nine. One recorder
        # across all of them, so "exactly once" still means once in total.
        recorder = LogRecorder()
        for module in list(sys.modules.values()):
            name = getattr(module, "__name__", "")
            if name.startswith("bespokelabs.curator.code_executor") and hasattr(module, "logger"):
                monkeypatch.setattr(module, "logger", recorder, raising=False)
        run(monkeypatch, **run_kwargs)
        return recorder.warnings

    assert warnings_of(exit_code=0, stdout="A" * 300, stderr="", max_output_bytes=64) == ["sandbox output capped: stdout exceeded the 64-byte budget"]
    assert warnings_of(exit_code=0, stdout="A" * 300, stderr="B" * 300, max_output_bytes=64) == ["sandbox output capped: stderr, stdout exceeded the 64-byte budget"]
    assert warnings_of(exit_code=124, stdout="A" * 300, stderr="", timeout=7, max_output_bytes=64) == ["sandbox output capped: stdout exceeded the 64-byte budget"]
    assert warnings_of(exit_code=1, stdout="", stderr="E" * 300, max_output_bytes=64) == ["sandbox output capped: stderr exceeded the 64-byte budget"]

    # nothing was cut: nothing is said
    assert warnings_of(exit_code=0, stdout="A", stderr="B", max_output_bytes=64) == []
    assert warnings_of(exit_code=0, stdout="A" * 300, stderr="B" * 300, max_output_bytes=0) == []

    # the salvage cap in the `except` handler is silent, so a run that captured a
    # truncated stream and then blew up on the way out still says it exactly once
    assert warnings_of(exit_code=0, stdout="A" * 300, stderr="", exit_error=RuntimeError("boom"), max_output_bytes=64) == [
        "sandbox output capped: stdout exceeded the 64-byte budget"
    ]
    # and a run that never captured anything says nothing at all
    assert warnings_of(command_error=RuntimeError("kaboom"), max_output_bytes=64) == []
