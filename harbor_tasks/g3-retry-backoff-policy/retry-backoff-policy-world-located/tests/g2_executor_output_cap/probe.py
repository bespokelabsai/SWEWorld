"""g2 worker: the ONLY process that imports the submission.

Runs as `nobody`. For each graded test it reproduces exactly the curator calls
that test makes and writes the resulting values — never a pass/fail — to the
observations file named on argv. `judge.py`, which never imports the submission
and which the grading uid cannot even read (test.sh locks /tests to root), turns
those values into the verdict. This is the split that closes the forgery in
`tasks/lessons.md` (2026-09-09): a uid cannot stop imported agent code from
rewriting a report its own process produces, so the process that imports the
code no longer produces the report — and the numbers it would have to forge to
pass live only in the judge it cannot read.

The curator-facing halves are lifted from `test_open`/`test_r1`/`test_r2`, same
seam (`install_sandbox`, `run`, `execute`) and same answer-free plumbing
(`warnings_of`, `LogRecorder`), so a value here is the value the test saw. The
judge holds the assertions those tests made — the elision marker, the floor of
16, the `OutputCapError` message, the warning-line template and the
`error_truncated` semantics. A submission that returns forged values only forges
values the judge still checks against the real expectations, which is
implementing them.
"""
from __future__ import annotations

import inspect
import json
import os
import sys
import traceback

# The import-time environment the suite's conftest sets, applied here because
# this worker is not run under pytest.
os.environ.setdefault("CURATOR_DISABLE_RICH_DISPLAY", "1")
os.environ.setdefault("TELEMETRY_ENABLED", "false")
os.environ.setdefault("CURATOR_VIEWER", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-verifier")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-verifier")
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-verifier")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("COLUMNS", "220")

_MISSING = object()


class MonkeyPatch:
    """The slice of pytest's monkeypatch the g2 seam uses, with undo.

    `install_sandbox` wants `setitem(sys.modules, ...)`, `setattr(..., )` and
    `delenv`; `warnings_of` wants `setattr(..., raising=False)`. Nothing here
    needs the rest. `undo()` runs between probes so one test's patched
    `sys.modules["bespokelabs.sandbox"]` or module `logger` cannot leak into the
    next — the same isolation pytest's function-scoped monkeypatch gives.
    """

    def __init__(self) -> None:
        self._undo: list = []

    def setattr(self, target, name, value, raising=True):
        if not hasattr(target, name) and raising:
            raise AttributeError(name)
        old = getattr(target, name, _MISSING)
        setattr(target, name, value)
        self._undo.append(("attr", target, name, old))

    def setitem(self, dic, name, value):
        old = dic[name] if name in dic else _MISSING
        dic[name] = value
        self._undo.append(("item", dic, name, old))

    def setenv(self, name, value):
        old = os.environ.get(name, _MISSING)
        os.environ[name] = value
        self._undo.append(("env", name, old))

    def delenv(self, name, raising=False):
        old = os.environ.pop(name, _MISSING)
        self._undo.append(("env", name, old))

    def undo(self):
        for entry in reversed(self._undo):
            kind = entry[0]
            if kind == "attr":
                _, target, name, old = entry
                if old is _MISSING:
                    try:
                        delattr(target, name)
                    except AttributeError:
                        pass
                else:
                    setattr(target, name, old)
            elif kind == "item":
                _, dic, name, old = entry
                if old is _MISSING:
                    dic.pop(name, None)
                else:
                    dic[name] = old
            else:
                _, name, old = entry
                if old is _MISSING:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = old
        self._undo = []


# probe_support owns the curator imports and the seam; reuse them so a probe
# calls curator exactly as the test does. Importing it runs the submission's
# `import bespokelabs.curator` — this process's whole purpose, and why it is
# disposable. probe_support holds the answer-free helpers/inputs (the worker
# never imports test_open, whose source carries the expected answer literals).
import probe_support as S  # noqa: E402
from harness import read_field  # noqa: E402

BACKENDS = ("local", "docker", "e2b", "modal", "daytona", "multiprocessing")


def raises(fn, *args, **kwargs) -> dict:
    """Call `fn`, reporting whether it raised, its class chain, its message, and
    the `max_bytes` an `OutputCapError` hangs on itself.

    The judge cannot import `OutputCapError`/`ValidationError`, so it checks the
    raised type by the names in its MRO — the faithful stand-in for
    `pytest.raises(T)`, which is all the tests do with these exceptions.
    """
    try:
        fn(*args, **kwargs)
    except BaseException as exc:  # noqa: BLE001 - the test catches a type; the judge checks which
        info = {"raised": True, "mro": [c.__name__ for c in type(exc).__mro__],
                "str": str(exc)}
        if hasattr(exc, "max_bytes"):
            info["max_bytes"] = exc.max_bytes
        return info
    return {"raised": False, "mro": []}


# =============================================================================
# the open feature — a configurable budget, plumbed and applied
# =============================================================================
def probe_open(mp) -> dict:
    o: dict = {}
    mp.delenv("CURATOR_MAX_OUTPUT_BYTES", raising=False)

    from bespokelabs.curator.code_executor import output_cap
    o["DEFAULT_MAX_OUTPUT_BYTES"] = output_cap.DEFAULT_MAX_OUTPUT_BYTES

    cfg = S.CodeExecutionBackendConfig
    o["config_fields"] = sorted(cfg.model_fields)
    o["has_field"] = "max_output_bytes" in cfg.model_fields
    o["default_budget"] = cfg().max_output_bytes
    o["zero_budget"] = cfg(max_output_bytes=0).max_output_bytes
    o["budget_128"] = cfg(max_output_bytes=128).max_output_bytes
    o["reject_neg1"] = raises(lambda: cfg(max_output_bytes=-1))

    o["backends"] = {name: read_field(S._CodeExecutionBackendFactory.create(name, {"max_output_bytes": 128}),
                                      "max_output_bytes", default=None)
                     for name in BACKENDS}
    o["backend_local_default"] = read_field(S._CodeExecutionBackendFactory.create("local", {}),
                                            "max_output_bytes", default=None)

    params = inspect.signature(S.sandbox_backend._execute_in_sandbox).parameters
    o["sig_params"] = list(params)
    o["sig_has"] = "max_output_bytes" in params
    if o["sig_has"]:
        o["sig_kind"] = params["max_output_bytes"].kind.name
        o["sig_default"] = params["max_output_bytes"].default

    o["models"] = {}
    for label, model, instance in (
        ("output", S.CodeExecutionOutput, S.CodeExecutionOutput()),
        ("result", S.CodeExecutionResult, S.CodeExecutionResult(stdout="a", stderr="b", exit_code=0)),
    ):
        m = {"has": "truncated_streams" in model.model_fields, "fields": sorted(model.model_fields)}
        if m["has"]:
            m["required"] = model.model_fields["truncated_streams"].is_required()
            m["value"] = read_field(instance, "truncated_streams", default=None)
        o["models"][label] = m
    dumped = S.CodeExecutionResponse(exec_output=S.CodeExecutionOutput(stdout="a")).model_dump()
    o["dumped_truncated"] = dumped["exec_output"]["truncated_streams"]

    # an over-budget run comes back shortened; a positional sixth arg is refused
    S.install_sandbox(mp, exit_code=0, stdout="A" * 300, stderr="B" * 300)
    o["positional_refused"] = raises(
        lambda: S.sandbox_backend._execute_in_sandbox("print('hi')", "", 10, "local", {}, 64))
    capped = S.execute(max_output_bytes=64)
    o["capped"] = {"message": capped.message, "len_stdout": len(capped.stdout),
                   "len_stderr": len(capped.stderr),
                   "truncated_sorted": sorted(read_field(capped, "truncated_streams", default=[])),
                   "files": capped.files}

    # all four construction sites obey the budget
    sites = {
        "success": S.run(mp, exit_code=0, stdout="A" * 300, max_output_bytes=64),
        "timeout": S.run(mp, exit_code=124, stdout="A" * 300, timeout=7, max_output_bytes=64),
        "non-zero exit": S.run(mp, exit_code=1, stdout="A" * 300, max_output_bytes=64),
        # a run that produced megabytes and then blew up on the way out of the
        # `with`: `result` is populated, but no in-`with` return ever happened
        "exception": S.run(mp, exit_code=0, stdout="A" * 300, exit_error=RuntimeError("boom"),
                           max_output_bytes=64),
    }
    o["sites"] = {site: {"stdout_none": out.stdout is None,
                         "len": (None if out.stdout is None else len(out.stdout))}
                  for site, out in sites.items()}

    # the exit-code message carries the capped stderr, unchanged wording
    failed = S.run(mp, exit_code=1, stdout="", stderr="E" * 300, max_output_bytes=64)
    o["failed_len_stderr"] = len(failed.stderr)
    o["failed_error"] = failed.error
    o["failed_stderr"] = failed.stderr
    o["fmt_params"] = list(inspect.signature(S.sandbox_backend._format_exit_code_error).parameters)
    o["fmt_call"] = S.sandbox_backend._format_exit_code_error(3, "boom")

    # an under-budget run is untouched, and `files` is never capped
    untouched = S.run(mp, exit_code=0, stdout="A" * 300, stderr="", files="F" * 5000)
    o["untouched_stdout"] = untouched.stdout
    o["untouched_files"] = untouched.files
    o["untouched_truncated"] = read_field(untouched, "truncated_streams", default=None)
    return o


# =============================================================================
# r1 — the shape of the cut, and what it says about itself
# =============================================================================
def probe_r1_rule(mp) -> dict:
    wide = S.run(mp, exit_code=0, stdout=S.DIGITS, stderr="", max_output_bytes=64)
    narrow = S.run(mp, exit_code=0, stdout=S.DIGITS, stderr="", max_output_bytes=32)
    return {"wide_stdout": wide.stdout, "narrow_stdout": narrow.stdout}


def probe_r1_scope(mp) -> dict:
    data = "€" * 10  # "€" is three UTF-8 bytes: 10 chars, 30 bytes
    out = S.run(mp, exit_code=0, stdout=data, stderr="", max_output_bytes=20)
    return {"stdout": out.stdout,
            "truncated": read_field(out, "truncated_streams", default=None)}


def probe_r1_exclusions(mp) -> dict:
    over = S.run(mp, exit_code=0, stdout="A" * 300, stderr="", max_output_bytes=64)
    unlimited = S.run(mp, exit_code=0, stdout="A" * 300, stderr="B" * 500, max_output_bytes=0)
    under = S.run(mp, exit_code=0, stdout=S.DIGITS[:60], stderr="", max_output_bytes=64)
    exactly = S.run(mp, exit_code=0, stdout="A" * 64, stderr="", max_output_bytes=64)
    return {
        "over_len": len(over.stdout),
        "unlimited_stdout": unlimited.stdout,
        "unlimited_stderr": unlimited.stderr,
        "unlimited_truncated": read_field(unlimited, "truncated_streams", default=None),
        "under_stdout": under.stdout,
        "under_stderr": under.stderr,
        "under_truncated": read_field(under, "truncated_streams", default=None),
        "exactly_stdout": exactly.stdout,
        "exactly_truncated": read_field(exactly, "truncated_streams", default=None),
    }


def probe_r1_failure_behavior(mp) -> dict:
    from bespokelabs.curator.code_executor.output_cap import MIN_MAX_OUTPUT_BYTES, OutputCapError
    o = {"MIN": MIN_MAX_OUTPUT_BYTES,
         "outputcaperror_mro": [c.__name__ for c in OutputCapError.__mro__]}

    # at request time, the raised object (never a constructor call)
    S.install_sandbox(mp, exit_code=0, stdout="A" * 300, stderr="")
    o["refused"] = raises(lambda: S.sandbox_backend._execute_in_sandbox(
        code="print('hi')", code_input="", timeout=10, backend_name="local",
        sandbox_kwargs={}, max_output_bytes=8))

    o["floor16_message"] = S.run(mp, exit_code=0, stdout="A" * 300, stderr="", max_output_bytes=16).message

    # and up front, so a typo fails once at construction instead of per row
    mp.delenv("CURATOR_MAX_OUTPUT_BYTES", raising=False)
    o["bad"] = {str(bad): raises(lambda b=bad: S.CodeExecutionBackendConfig(max_output_bytes=b))
                for bad in (1, 8, 15)}
    o["docker8"] = raises(lambda: S._CodeExecutionBackendFactory.create("docker", {"max_output_bytes": 8}))
    o["cfg0"] = S.CodeExecutionBackendConfig(max_output_bytes=0).max_output_bytes
    o["cfg16"] = S.CodeExecutionBackendConfig(max_output_bytes=16).max_output_bytes
    o["neg1"] = raises(lambda: S.CodeExecutionBackendConfig(max_output_bytes=-1))
    return o


def probe_r1_observability(mp) -> dict:
    from bespokelabs.curator.code_executor.output_cap import TRUNCATION_LOG_TEMPLATE
    return {
        "template_formatted": TRUNCATION_LOG_TEMPLATE.format(streams="stderr, stdout", budget=64),
        "w_stdout_only": S.warnings_of(mp, exit_code=0, stdout="A" * 300, stderr="", max_output_bytes=64),
        "w_both": S.warnings_of(mp, exit_code=0, stdout="A" * 300, stderr="B" * 300, max_output_bytes=64),
        "w_timeout": S.warnings_of(mp, exit_code=124, stdout="A" * 300, stderr="", timeout=7, max_output_bytes=64),
        "w_stderr_only": S.warnings_of(mp, exit_code=1, stdout="", stderr="E" * 300, max_output_bytes=64),
        "w_nothing_cut": S.warnings_of(mp, exit_code=0, stdout="A", stderr="B", max_output_bytes=64),
        "w_unlimited": S.warnings_of(mp, exit_code=0, stdout="A" * 300, stderr="B" * 300, max_output_bytes=0),
        "w_salvage": S.warnings_of(mp, exit_code=0, stdout="A" * 300, stderr="",
                                   exit_error=RuntimeError("boom"), max_output_bytes=64),
        "w_never_captured": S.warnings_of(mp, command_error=RuntimeError("kaboom"), max_output_bytes=64),
    }


# =============================================================================
# r2 — the cap reaches `error`, on one path only
# =============================================================================
def probe_r2_rule(mp) -> dict:
    fields = list(S.CodeExecutionOutput.model_fields)
    o = {"fields": fields, "has_error_truncated": "error_truncated" in fields}
    if o["has_error_truncated"]:
        field = S.CodeExecutionOutput.model_fields["error_truncated"]
        o["required"] = field.is_required()
        o["annotation_is_bool"] = field.annotation is bool
        o["default_error_truncated"] = S.CodeExecutionOutput().error_truncated
        o["index_ok"] = "truncated_streams" in fields and \
            fields.index("error_truncated") == fields.index("truncated_streams") + 1

    # 200 characters of exception text under a 32-byte budget
    blew_up = S.run(mp, exit_code=0, stdout="", stderr="", exit_error=RuntimeError("Z" * 200), max_output_bytes=32)
    o["blew_message"] = blew_up.message
    o["blew_error"] = blew_up.error
    o["blew_len"] = len(blew_up.error)
    o["blew_error_truncated"] = read_field(blew_up, "error_truncated", default=None)
    return o


def probe_r2_scope(mp) -> dict:
    failed = S.run(mp, exit_code=1, stdout="", stderr="E" * 200, files="F" * 5000, max_output_bytes=32)
    timed_out = S.run(mp, exit_code=124, stdout="ok", stderr="", timeout=7, max_output_bytes=16)
    salvaged = S.run(mp, exit_code=0, stdout=S.BIG, stderr="", files="F" * 5000,
                     exit_error=RuntimeError("boom"), max_output_bytes=64)
    return {
        "failed_len_stderr": len(failed.stderr),
        "failed_error": failed.error,
        "failed_stderr": failed.stderr,
        "failed_error_truncated": read_field(failed, "error_truncated", default=None),
        "failed_files": failed.files,
        "timed_message": timed_out.message,
        "timed_error": timed_out.error,
        "timed_error_truncated": read_field(timed_out, "error_truncated", default=None),
        "salvaged_files": salvaged.files,
    }


def probe_r2_exclusions(mp) -> dict:
    o = {"output_has_flag": "error_truncated" in S.CodeExecutionOutput.model_fields,
         "result_has_flag": "error_truncated" in S.CodeExecutionResult.model_fields}
    if o["output_has_flag"]:
        dumped = S.CodeExecutionResponse(
            exec_output=S.CodeExecutionOutput(error="x", error_truncated=True)).model_dump()
        o["dumped_keys"] = sorted(dumped["exec_output"])

    both = S.run(mp, exit_code=0, stdout=S.BIG, stderr="", exit_error=RuntimeError("X" * 300), max_output_bytes=64)
    o["both_error_truncated"] = read_field(both, "error_truncated", default=None)
    o["both_truncated"] = read_field(both, "truncated_streams", default=None)

    failed = S.run(mp, exit_code=1, stdout="", stderr="E" * 300, max_output_bytes=64)
    o["failed_truncated"] = read_field(failed, "truncated_streams", default=None)
    return o


def probe_r2_observability(mp) -> dict:
    blew_up = S.run(mp, exit_code=0, stdout=S.BIG, stderr="", exit_error=RuntimeError("X" * 300), max_output_bytes=64)
    short = S.run(mp, exit_code=0, stdout=S.BIG, stderr="", exit_error=RuntimeError("boom"), max_output_bytes=64)
    failed = S.run(mp, exit_code=1, stdout="", stderr="E" * 80, max_output_bytes=64)
    return {
        "blew_error": blew_up.error,
        "blew_len": len(blew_up.error),
        "blew_error_truncated": read_field(blew_up, "error_truncated", default=None),
        "short_error": short.error,
        "short_error_truncated": read_field(short, "error_truncated", default=None),
        "failed_error": failed.error,
        "failed_len": len(failed.error),
        "failed_error_truncated": read_field(failed, "error_truncated", default=None),
        "failed_truncated": read_field(failed, "truncated_streams", default=None),
    }


# name -> probe. classname/name reproduce the current junit nodes so score.fold
# maps them to the identical fact keys.
PROBES = {
    "test_open::test_open_feature__a_configurable_byte_budget_shortens_what_the_sandbox_returns": probe_open,
    "test_r1::test_rule__the_kept_head_and_tail_split_three_to_one_around_an_elision_marker": probe_r1_rule,
    "test_r1::test_scope__the_budget_counts_utf8_bytes_and_both_slices_land_on_codepoints": probe_r1_scope,
    "test_r1::test_exclusions__a_zero_budget_is_unlimited_and_streams_within_budget_are_untouched": probe_r1_exclusions,
    "test_r1::test_failure_behavior__a_budget_below_the_floor_of_sixteen_is_refused_by_outputcaperror": probe_r1_failure_behavior,
    "test_r1::test_observability__one_warning_line_per_capped_run_from_the_shared_template": probe_r1_observability,
    "test_r2::test_rule__the_exception_message_is_capped_and_flagged_by_error_truncated": probe_r2_rule,
    "test_r2::test_scope__the_exit_code_and_timeout_messages_and_files_are_never_capped": probe_r2_scope,
    "test_r2::test_exclusions__the_flag_is_on_the_output_model_alone_and_never_a_stream_name": probe_r2_exclusions,
    "test_r2::test_observability__the_exact_error_text_and_flag_of_the_three_named_runs": probe_r2_observability,
}


def main(out_path: str) -> int:
    results: dict[str, dict] = {}
    for node, fn in PROBES.items():
        mp = MonkeyPatch()
        try:
            results[node] = {"ok": True, "obs": fn(mp)}
        except BaseException as exc:  # noqa: BLE001 - a probe that dies is a failed fact, reported not raised
            results[node] = {"ok": False,
                             "error": f"{type(exc).__name__}: {exc}",
                             "trace": traceback.format_exc()[-2000:]}
        finally:
            mp.undo()
    with open(out_path, "w") as fh:
        json.dump(results, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
