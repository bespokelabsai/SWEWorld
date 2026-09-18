"""g2 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and the
cloned source text, and writes a `junit.xml` whose `classname`/`name` are the
current suite's node ids — so `score.py` folds them into the identical fact keys
and `test.sh`/`score.py` are unchanged. No agent code runs here, so the report
cannot be forged; and `test.sh` locks /tests to root, so the worker cannot read
the numbers below to forge an observation that matches them. That pair is what
closes the forgery in tasks/lessons.md (2026-09-09) that a uid alone could not.

WHY THIS FILE NO LONGER HOLDS THE SCENARIOS' ANSWERS AS LITERALS. The split moved
the verdict out of the process that runs agent code. It left the worker AUTHORING
the values the verdict is computed from, and with a fixed fixture those values
never changed — g2's were `"A" * 300` under a 64-byte budget every run, and the
rule that turns them into an answer is written down in the corpus the agent is
told to read. A pristine tree plus one import-time `atexit` hook rewriting
`observations.json` scored reward 1.0 on g1's identically-built suite. Three
things close it here:

  * **the inputs move every run.** `fixture_spec.derive(seed)` re-draws the
    budgets, the payloads, the exit code and the timeout from the seed root
    picked, and `cap()` below prices THOSE inputs — so there is nothing to
    memorise and nothing in the corpus to copy. The rule that does the pricing
    lives only here.
  * **the constants are read out of the source.** The floor of 16, the 65536
    default and the log template cannot be re-drawn — they ARE the requirement —
    so they are checked against the submission's own module text as well as
    against behaviour, and a tree that reports the right number without defining
    it fails.
  * **the code the ticket protects is compared with the pristine tree.**
    `_collect_sandbox_files` is inside a file the ticket edits, so
    `protected_files` cannot express it; the comparison is against
    `CURATOR_BASELINE_DIR`.

The residual, stated plainly: a submission that IMPLEMENTS the rule inside a
forged hook still passes, because it has then done the work. What is gone is
passing by repeating values that were knowable in advance.

Every reward-bearing expected value still lives HERE and nowhere the worker can
read: the elision marker `\\n[[curator:elided {n} bytes]]\\n` and the 3:1 split it
sits in, the floor of 16 and the `OutputCapError` message, the exit-code and
timeout message text, the `TRUNCATION_LOG_TEMPLATE` output, and the
`error_truncated` semantics. `test_open`/`test_r1`/`test_r2` stay the
human-readable source of truth and the fact<->test bijection; their worked
examples use the old fixed fixture.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import sys
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_spec  # noqa: E402 - same derivation the worker used

# The judge runs `python3 -I` with no PYTHONPATH, so /tests is not importable by
# default. judge_io holds the hardened reads (no symlinks, size-capped) every
# agent-influenced path goes through; harness.py cannot: it imports pytest.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import judge_io  # noqa: E402

# --- the answers that cannot be re-drawn, because they are the requirement ---
FLOOR = 16
DEFAULT_BUDGET = 65536
ELISION_MARKER = "\n[[curator:elided {dropped} bytes]]\n"
LOG_TEMPLATE = "sandbox output capped: {streams} exceeded the {budget}-byte budget"
FLOOR_MESSAGE = "max_bytes must be 0 or at least {value}, got {bad}"
DUMP_KEYS = ["error", "error_truncated", "files", "message", "stderr", "stdout", "truncated_streams"]

# Longest UTF-8 sequence is four bytes, so a cut inside a character is always
# repaired by moving it at most three bytes.
_MAX_BOUNDARY_SHIFT = 3

SANDBOX_BACKEND = "bespokelabs/curator/code_executor/code_execution_backend/sandbox_backend.py"
OUTPUT_CAP = "bespokelabs/curator/code_executor/output_cap.py"

# `output_cap.py` "stays a pure function of its arguments -- no clock,
# randomness, I/O or environment reads" (instruction.md, section 3). Named
# modules rather than a whitelist, so an implementation is still free to reach
# for dataclasses, typing, re or the package logger.
IMPURE_MODULES = {"os", "time", "random", "datetime", "subprocess", "socket",
                  "secrets", "tempfile", "pathlib", "shutil", "urllib", "http", "requests"}

SPEC: dict = {}


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def raised(info, *, mro=None, max_bytes=..., string=..., msg=""):
    ok(info.get("raised"), f"{msg}: expected an exception, none raised")
    if mro is not None:
        ok(mro in info.get("mro", []), f"{msg}: {mro} not in {info.get('mro')}")
    if max_bytes is not ...:
        eq(info.get("max_bytes"), max_bytes, f"{msg}: max_bytes")
    if string is not ...:
        eq(info.get("str"), string, f"{msg}: message")


# ---------------------------------------------------------------------------
# the rule, as the judge holds it: what this run's inputs should have produced
# ---------------------------------------------------------------------------
def _decode_head(chunk: bytes) -> tuple[str, int]:
    for cut in range(_MAX_BOUNDARY_SHIFT + 1):
        candidate = chunk[: len(chunk) - cut]
        try:
            return candidate.decode("utf-8"), len(candidate)
        except UnicodeDecodeError:
            continue
    return chunk.decode("utf-8", errors="replace"), len(chunk)


def _decode_tail(chunk: bytes) -> tuple[str, int]:
    for drop in range(_MAX_BOUNDARY_SHIFT + 1):
        candidate = chunk[drop:]
        try:
            return candidate.decode("utf-8"), len(candidate)
        except UnicodeDecodeError:
            continue
    return chunk.decode("utf-8", errors="replace"), len(chunk)


def cap(text, budget: int) -> tuple:
    """(capped text, was it cut) — the head+tail keep, marker outside the budget.

    This is the hidden rule. It is the reason this file is unreadable to the
    worker: hand it over and a tree that caps nothing can price every scenario
    the seed draws.
    """
    if text is None:
        return None, False
    raw = text.encode("utf-8")
    if budget == 0 or len(raw) <= budget:
        return raw.decode("utf-8", errors="replace"), False
    head_budget = (budget * 3) // 4
    head, head_bytes = _decode_head(raw[:head_budget])
    tail, tail_bytes = _decode_tail(raw[len(raw) - (budget - head_budget):])
    marker = ELISION_MARKER.format(dropped=len(raw) - head_bytes - tail_bytes)
    return f"{head}{marker}{tail}", True


def exit_prefix(code) -> str:
    """curator's own non-zero-exit wording, which the ticket freezes verbatim."""
    return f"Program exited with status code {code}\n\nError details:\n"


def log_line(streams, budget) -> str:
    return LOG_TEMPLATE.format(streams=", ".join(streams), budget=budget)


# ---------------------------------------------------------------------------
# Reading source: the submission's (root, submission NOT importable) and the
# pristine tree's (root-owned copy named in CURATOR_BASELINE_DIR)
# ---------------------------------------------------------------------------
def _submission_source(rel: str) -> str:
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    path = root / rel
    if not path.is_file():
        raise Fail(f"cannot read {rel} under {root}")
    return judge_io.read_text(path)


def _baseline_source(rel: str) -> str:
    """The pristine file, for a rule about code INSIDE a file the ticket edits.

    `CURATOR_BASELINE_DIR` is a root-owned copy of `bespokelabs/curator`, so the
    relative path drops that prefix. Absent variable or absent file FAILS the
    fact: a check that cannot be made must not pass blind.
    """
    root = os.environ.get("CURATOR_BASELINE_DIR", "")
    if not root:
        raise Fail("CURATOR_BASELINE_DIR is not set, so 'unchanged' cannot be verified")
    path = pathlib.Path(root) / rel.split("bespokelabs/curator/", 1)[-1]
    if not path.is_file():
        raise Fail(f"the pristine tree has no {path}, so 'unchanged' cannot be verified")
    return judge_io.read_text(path)


def _function(src: str, name: str, where: str):
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise Fail(f"{where} defines no {name}")


def _module_assignments(src: str) -> dict:
    """Module-level `NAME = <literal>` and `NAME: T = <literal>`, as values."""
    out = {}
    for node in ast.parse(src).body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target.id]
        if not targets or getattr(node, "value", None) is None:
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue
        for name in targets:
            out[name] = value
    return out


def _check_collect_sandbox_files_unchanged():
    """`_collect_sandbox_files` is byte-for-byte the pristine function.

    instruction.md's constraints say "`files` / `_collect_sandbox_files` is
    untouched and never capped", and the behavioural half of that is unfalsifiable
    from inside the suite: `probe_support.install_sandbox` patches the collector
    out, exactly as curator's own `test_sandbox_backend.py` does, so an agent
    could rewrite the real one to truncate or corrupt an archive and every
    `files` assertion here would still be reading fixture data. The function
    lives inside a file this ticket must edit, so `protected_files` cannot
    express it; the pristine copy root staged as CURATOR_BASELINE_DIR can.
    """
    submitted = _function(_submission_source(SANDBOX_BACKEND), "_collect_sandbox_files",
                          "the submitted sandbox_backend.py")
    pristine = _function(_baseline_source(SANDBOX_BACKEND), "_collect_sandbox_files",
                         "the pristine sandbox_backend.py")
    ok(ast.dump(submitted) == ast.dump(pristine),
       "_collect_sandbox_files was modified; the ticket says it is untouched "
       "(compared against the pristine tree, not against the patched test seam)")


def _check_execute_in_sandbox_signature():
    """The signature the ticket writes out, read off the source.

    Names, order and keyword-only-ness, not source text: the annotation and the
    way the default is spelled (`65536` or `DEFAULT_MAX_OUTPUT_BYTES`) are the
    submission's business. Checked here as well as through `inspect` because an
    observation can be forged and a pushed file cannot.
    """
    fn = _function(_submission_source(SANDBOX_BACKEND), "_execute_in_sandbox",
                   "the submitted sandbox_backend.py")
    eq([a.arg for a in fn.args.args],
       ["code", "code_input", "timeout", "backend_name", "sandbox_kwargs"],
       "_execute_in_sandbox positional parameters")
    eq([a.arg for a in fn.args.kwonlyargs], ["max_output_bytes"],
       "_execute_in_sandbox keyword-only parameters")
    ok(len(fn.args.kw_defaults) == 1 and fn.args.kw_defaults[0] is not None,
       "max_output_bytes has no default")


def _check_execute_request_passes_the_budget():
    """`execute_request` hands the budget to the partial it already builds.

    instruction.md section 2 says `execute_request` passes
    `max_output_bytes=self.max_output_bytes` into the existing
    `partial(_execute_in_sandbox, ...)`. Nothing behavioural in this suite calls
    `execute_request` -- it is async and wants a live thread pool and a request
    object -- so the plumbing is read off the source instead. The keyword is what
    is checked, not which callable receives it.
    """
    src = _submission_source(SANDBOX_BACKEND)
    fn = _function(src, "execute_request", "the submitted sandbox_backend.py")
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and any(kw.arg == "max_output_bytes" for kw in node.keywords):
            return
    raise Fail("execute_request passes no max_output_bytes= into the call it builds; "
               "the budget never reaches _execute_in_sandbox on the real path")


def _check_output_cap_module():
    """The new module the ticket asks for: its published default, and its purity.

    "It exports `DEFAULT_MAX_OUTPUT_BYTES: int = 65536` and stays a pure function
    of its arguments — no clock, randomness, I/O or environment reads"
    (instruction.md, section 3). A source check, because a forged observation can
    claim a module that was never written.
    """
    src = _submission_source(OUTPUT_CAP)
    eq(_module_assignments(src).get("DEFAULT_MAX_OUTPUT_BYTES"), DEFAULT_BUDGET,
       f"{OUTPUT_CAP} does not define DEFAULT_MAX_OUTPUT_BYTES = {DEFAULT_BUDGET}")
    imported = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module.split(".")[0])
    impure = sorted(imported & IMPURE_MODULES)
    ok(not impure, f"output_cap.py imports {impure}; the ticket says it stays a pure "
                   "function of its arguments, with no clock, randomness, I/O or environment reads")


def _output_cap_assignment(name: str, expected, msg: str):
    """One module-level constant of `output_cap.py`, read off the source.

    The behavioural check next to this one proves the value is USED; this one
    proves it is DECLARED where the requirement says, which an observation
    cannot show and a forgery cannot fake.
    """
    eq(_module_assignments(_submission_source(OUTPUT_CAP)).get(name), expected, msg)


# =============================================================================
# the open feature
# =============================================================================
def judge_open(o):
    eq(o["DEFAULT_MAX_OUTPUT_BYTES"], DEFAULT_BUDGET, "DEFAULT_MAX_OUTPUT_BYTES")
    ok(o["has_field"], f"CodeExecutionBackendConfig has no max_output_bytes; it has {o['config_fields']}")
    eq(o["default_budget"], DEFAULT_BUDGET, "default max_output_bytes")
    eq(o["zero_budget"], 0, "max_output_bytes=0")
    eq(o["plumb_budget"], SPEC["plumb_budget"], f"max_output_bytes={SPEC['plumb_budget']}")
    raised(o["reject_negative"], mro="ValidationError", msg=f"max_output_bytes={SPEC['negative']}")

    for name, value in o["backends"].items():
        eq(value, SPEC["plumb_budget"], f"the {name} backend does not carry the budget")
    eq(o["backend_local_default"], DEFAULT_BUDGET, "local backend default budget")

    ok(o["sig_has"], f"_execute_in_sandbox takes {o['sig_params']}")
    eq(o["sig_kind"], "KEYWORD_ONLY", "max_output_bytes is keyword-only")
    eq(o["sig_default"], DEFAULT_BUDGET, "max_output_bytes default")

    for label, m in o["models"].items():
        ok(m["has"], f"{label} model has {m['fields']}")
        eq(m["required"], False, f"{label}.truncated_streams is not required")
        eq(m["value"], [], f"{label}.truncated_streams default")
        # "Non-Optional, on both models" -- so None is not a value it can hold.
        # The annotation is checked by what it does NOT say, because list[str]
        # and typing.List[str] are both fine and print differently.
        ok("Optional" not in m["annotation"] and "None" not in m["annotation"],
           f"{label}.truncated_streams is Optional: {m['annotation']}")
        raised(m["none_refused"], mro="ValidationError",
               msg=f"{label}.truncated_streams=None")
    eq(o["dumped_truncated"], [], "truncated_streams through model_dump")

    raised(o["positional_refused"], mro="TypeError", msg="a positional sixth arg is refused")
    budget, out_len, err_len = SPEC["budget"], len(SPEC["over_stdout"]), len(SPEC["over_stderr"])
    eq(o["capped"]["message"], "success", "capped run message")
    ok(0 < o["capped"]["len_stdout"] < out_len,
       f"stdout came back at {o['capped']['len_stdout']} characters under a {budget}-byte budget")
    ok(0 < o["capped"]["len_stderr"] < err_len,
       f"stderr came back at {o['capped']['len_stderr']} characters under a {budget}-byte budget")
    # instruction.md:31-32 — the field "Names exactly which of "stdout" /
    # "stderr" were shortened on that run, sorted alphabetically". Compared as a
    # list, so the order IS graded: the probe used to record `sorted(...)` and
    # this line compared the sorted copy, which let a tree that returned
    # ["stdout", "stderr"] through. The warning line's own ordering is r1's
    # observability fact; this is the model field.
    eq(o["capped"]["truncated"], ["stderr", "stdout"],
       "truncated_streams names both shortened streams in alphabetical order")
    eq(o["capped"]["files"], SPEC["files"], "files passed through")

    for site, m in o["sites"].items():
        ok(not m["stdout_none"], f"the {site} site returned no stdout at all")
        ok(0 < m["len"] < out_len,
           f"the {site} site returned {m['len']} characters under a {budget}-byte budget")

    # instruction.md:56 — the `except Exception` site salvages its streams with
    # `getattr(result, "stdout", None)`, "and may be `None`". When
    # `execute_command` is what raised, there is no result to salvage from, so
    # that expression yields None for both streams; and instruction.md:32 says a
    # stream that is None "contributes nothing", so nothing is named. Nothing
    # asserted this before: the run was made only to count warnings, so a tree
    # that returned "" here, or that named a stream it never captured, passed.
    nc = o["never_captured"]
    ok(nc["stdout_is_none"],
       f"the salvage site returned stdout={nc['stdout']!r} on a run that captured nothing; "
       "getattr(result, \"stdout\", None) is None there")
    ok(nc["stderr_is_none"],
       f"the salvage site returned stderr={nc['stderr']!r} on a run that captured nothing; "
       "getattr(result, \"stderr\", None) is None there")
    eq(nc["truncated"], [],
       "a run that captured nothing shortened nothing, so truncated_streams names nothing")
    eq(nc["files"], SPEC["files"], "files is collected and left alone on the salvage path")

    ok(o["failed_len_stderr"] < err_len, "the capped stderr on the exit-code path")
    eq(o["failed_error"], exit_prefix(SPEC["exit_code"]) + o["failed_stderr"],
       "`error` embeds the capped stderr")
    eq(o["fmt_params"], ["exit_code", "stderr"], "_format_exit_code_error signature")
    eq(o["fmt_call"], exit_prefix(SPEC["fmt_exit_code"]) + SPEC["fmt_stderr"],
       "_format_exit_code_error wording")

    eq(o["untouched_stdout"], SPEC["over_stdout"], "under-budget stdout untouched")
    eq(o["untouched_files"], SPEC["files_big"], "files never capped")
    eq(o["untouched_truncated"], [], "under-budget truncated_streams")

    # The ticket's own constraints, which no observation can establish: the new
    # module exists and is pure, the signature is the one written down, and the
    # file collector is the pristine one.
    _check_output_cap_module()
    _check_execute_in_sandbox_signature()
    _check_execute_request_passes_the_budget()
    _check_collect_sandbox_files_unchanged()


# =============================================================================
# r1 — the shape of the cut
# =============================================================================
def judge_r1_rule(o):
    payload = SPEC["rule_payload"]
    for label, budget, got in (("wide", SPEC["budget"], o["wide_stdout"]),
                               ("narrow", SPEC["narrow_budget"], o["narrow_stdout"])):
        want, _ = cap(payload, budget)
        head_budget = (budget * 3) // 4
        # The payload is ASCII, so the keep is exactly `budget` bytes and the
        # marker — charged outside it — accounts for the rest of the length.
        marker = ELISION_MARKER.format(dropped=len(payload) - budget)
        eq(got, want, f"{label} ({budget}-byte budget): a {head_budget}-byte head, then "
                      f"{marker!r}, then a {budget - head_budget}-byte tail "
                      f"({budget + len(marker)} characters in all)")


def judge_r1_scope(o):
    payload = SPEC["wide_payload"]
    for budget in SPEC["wide_budgets"]:
        # .get, not [], so an observation for some other run's budgets reads as
        # "this run was never made" rather than a KeyError the harness has to
        # report as a judge error.
        got = o["runs"].get(str(budget))
        ok(got is not None,
           f"no observation for the {budget}-byte budget run; the observed runs were "
           f"{sorted(o['runs'])}")
        want, _ = cap(payload, budget)
        ok(got["stdout"] != payload,
           f"{len(payload)} characters / {len(payload.encode())} bytes came back whole "
           f"under a {budget}-BYTE budget")
        ok("�" not in got["stdout"],
           f"a clean UTF-8 stream came back with a replacement character: {got['stdout']!r}")
        eq(got["stdout"], want,
           f"the {budget}-byte cut of a mixed-width UTF-8 stream, both slices on codepoints")
        eq(got["truncated"], ["stdout"], f"truncated_streams at budget {budget}")


def judge_r1_exclusions(o):
    ok(o["over_len"] < len(SPEC["over_stdout"]),
       "the stdout/stderr byte cap is not implemented, so the constraint cannot be credited")
    eq(o["unlimited_stdout"], SPEC["unlimited_stdout"], "a budget of 0 kept everything")
    eq(o["unlimited_stderr"], SPEC["unlimited_stderr"], "a budget of 0 kept stderr")
    eq(o["unlimited_truncated"], [], "0 lists nothing")
    eq(o["under_stdout"], SPEC["under"], "under-budget stdout untouched")
    eq(o["under_stderr"], "", "an empty stderr is preserved")
    eq(o["under_truncated"], [], "under-budget lists nothing")
    eq(o["exactly_stdout"], SPEC["exact"], "a stream exactly at the budget is not shortened")
    eq(o["exactly_truncated"], [], "at-budget lists nothing")


def judge_r1_failure_behavior(o):
    eq(o["MIN"], FLOOR, "MIN_MAX_OUTPUT_BYTES")
    ok("ValueError" in o["outputcaperror_mro"], f"OutputCapError is not a ValueError: {o['outputcaperror_mro']}")
    bad = SPEC["refused_budget"]
    raised(o["refused"], mro="OutputCapError", max_bytes=bad,
           string=FLOOR_MESSAGE.format(value=FLOOR, bad=bad), msg="request-time refusal")
    eq(o["floor_message"], "success", f"{FLOOR} is the floor and must be accepted")
    for value in SPEC["sub_floor"]:
        info = o["bad"].get(str(value))
        ok(info is not None, f"no observation for the budget {value}; the observed budgets were "
                             f"{sorted(o['bad'])}")
        raised(info, mro="ValidationError", msg=f"up-front rejection of {value}")
        ok(FLOOR_MESSAGE.format(value=FLOOR, bad=value) in info.get("str", ""),
           f"the rejection of {value} does not carry the OutputCapError message: {info.get('str')!r}")
    raised(o["factory_bad"], mro="ValidationError", msg=f"factory rejects {SPEC['factory_bad']}")
    eq(o["cfg0"], 0, "0 accepted")
    eq(o["cfg_floor"], FLOOR, f"{FLOOR} accepted")
    raised(o["negative"], mro="ValidationError", msg=f"{SPEC['negative']} rejected")
    # the floor is declared where the requirement puts it, not just obeyed
    _output_cap_assignment("MIN_MAX_OUTPUT_BYTES", FLOOR,
                           f"output_cap.py does not define MIN_MAX_OUTPUT_BYTES = {FLOOR}")


def judge_r1_observability(o):
    budget = SPEC["budget"]
    eq(o["template_formatted"], log_line(["stderr", "stdout"], budget), "TRUNCATION_LOG_TEMPLATE")
    eq(o["w_stdout_only"], [log_line(["stdout"], budget)], "stdout only")
    eq(o["w_both"], [log_line(["stderr", "stdout"], budget)], "both streams")
    eq(o["w_timeout"], [log_line(["stdout"], budget)], "timeout path")
    eq(o["w_stderr_only"], [log_line(["stderr"], budget)], "stderr only")
    eq(o["w_nothing_cut"], [], "nothing cut, nothing said")
    eq(o["w_unlimited"], [], "budget 0 says nothing")
    eq(o["w_salvage"], [log_line(["stdout"], budget)], "salvage path silent, said once")
    eq(o["w_never_captured"], [], "a run that captured nothing says nothing")
    # the template is a shared constant of output_cap.py, not a string built at
    # the call site — which is what "from the shared template" means
    _output_cap_assignment("TRUNCATION_LOG_TEMPLATE", LOG_TEMPLATE,
                           "output_cap.py does not export TRUNCATION_LOG_TEMPLATE with the "
                           "agreed wording")


# =============================================================================
# r2 — the cap reaches `error`, on one path only
# =============================================================================
def judge_r2_rule(o):
    ok(o["has_error_truncated"], f"CodeExecutionOutput has {o['fields']}")
    eq(o["required"], False, "error_truncated is not required")
    ok(o["annotation_is_bool"], "error_truncated is a plain bool, not an Optional one")
    eq(o["default_error_truncated"], False, "error_truncated defaults False")
    ok(o["index_ok"], f"error_truncated is not declared right after truncated_streams: {o['fields']}")
    eq(o["blew_message"], "error", "the exception path message")
    want, _ = cap(SPEC["exc_text"], SPEC["exc_budget"])
    eq(o["blew_error"], want, "the exception message is capped like a stream")
    eq(o["blew_len"], len(want), "marker charged outside the budget")
    eq(o["blew_error_truncated"], True, "error_truncated set on the exception path")


def judge_r2_scope(o):
    prefix = exit_prefix(SPEC["exit_code"])
    ok(o["failed_len_stderr"] < len(SPEC["exit_stderr"]),
       "the stdout/stderr byte cap is not implemented")
    eq(o["failed_error"], prefix + o["failed_stderr"],
       "`error` is the message assembled from the capped stderr")
    eq(len(o["failed_error"]), o["failed_len_stderr"] + len(prefix),
       "the assembled message was re-capped")
    ok(len(o["failed_error"]) > SPEC["exc_budget"], "the assembled message keeps its full length")
    eq(o["failed_error_truncated"], False, "error_truncated is not set on the assembled exit-code path")
    eq(o["failed_files"], SPEC["files_big"], "files is not capped")
    eq(o["timed_message"], "timeout", "timeout message")
    eq(o["timed_error"], f"Execution timed out after {SPEC['timeout_secs']}s",
       "the timeout message goes through the cap")
    eq(o["timed_error_truncated"], False, "error_truncated on the timeout path")
    eq(o["salvaged_files"], SPEC["files_big"], "files survives the salvage path")


def judge_r2_exclusions(o):
    ok(o["output_has_flag"], "the error_truncated flag on CodeExecutionOutput is not implemented")
    ok(not o["result_has_flag"], "CodeExecutionResult gained the flag as well")
    eq(o["dumped_keys"], DUMP_KEYS, "model_dump keys")
    eq(o["dumped"]["error"], SPEC["exc_short"], "the dumped error")
    eq(o["dumped"]["error_truncated"], True, "the dumped flag")
    eq(o["dumped"]["truncated_streams"], [], "the dumped truncated_streams")
    eq(o["both_error_truncated"], True, "error_truncated set when the error was cut")
    eq(o["both_truncated"], ["stdout"], '"error" leaked into truncated_streams')
    eq(o["failed_truncated"], ["stderr"], "stderr named on the exit-code path")


def judge_r2_observability(o):
    budget = SPEC["budget"]
    want_error, _ = cap(SPEC["exc_text"], budget)
    eq(o["blew_error"], want_error, "the exception message capped head and tail")
    eq(o["blew_len"], len(want_error), "capped exception length")
    eq(o["blew_error_truncated"], True, "flagged truncated")
    eq(o["short_error"], SPEC["exc_short"], "a message within budget is not rewritten")
    eq(o["short_error_truncated"], False, "error_truncated not set for a message the cap never shortened")
    want_stderr, _ = cap(SPEC["exit_stderr_short"], budget)
    assembled = exit_prefix(SPEC["exit_code"]) + want_stderr
    eq(o["failed_len"], len(assembled), "the capped stderr in the message, and not re-capped")
    eq(o["failed_error"], assembled, "the assembled message embeds the capped stderr")
    eq(o["failed_error_truncated"], False, "error_truncated on the assembled exit-code path")
    eq(o["failed_truncated"], ["stderr"], "stderr named")


JUDGES = {
    "test_open::test_open_feature__a_configurable_byte_budget_shortens_what_the_sandbox_returns": judge_open,
    "test_r1::test_rule__the_kept_head_and_tail_split_three_to_one_around_an_elision_marker": judge_r1_rule,
    "test_r1::test_scope__the_budget_counts_utf8_bytes_and_both_slices_land_on_codepoints": judge_r1_scope,
    "test_r1::test_exclusions__a_zero_budget_is_unlimited_and_streams_within_budget_are_untouched": judge_r1_exclusions,
    "test_r1::test_failure_behavior__a_budget_below_the_floor_of_sixteen_is_refused_by_outputcaperror": judge_r1_failure_behavior,
    "test_r1::test_observability__one_warning_line_per_capped_run_from_the_shared_template": judge_r1_observability,
    "test_r2::test_rule__the_exception_message_is_capped_and_flagged_by_error_truncated": judge_r2_rule,
    "test_r2::test_scope__the_exit_code_and_timeout_messages_and_files_are_never_capped": judge_r2_scope,
    "test_r2::test_exclusions__the_flag_is_on_the_output_model_alone_and_never_a_stream_name": judge_r2_exclusions,
    "test_r2::test_observability__the_exact_error_text_and_flag_of_the_three_named_runs": judge_r2_observability,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g2_executor_output_cap" '
             f'tests="{len(results)}" failures="{fails}" errors="0">']
    for classname, name, failure in results:
        head = f'<testcase classname={quoteattr(classname)} name={quoteattr(name)}>'
        if failure:
            lines.append(head + f'<failure message={quoteattr(failure[:200])}>'
                         + escape(failure[:4000]) + '</failure></testcase>')
        else:
            lines.append(head + '</testcase>')
    lines.append('</testsuite></testsuites>')
    return "\n".join(lines)


def main(obs_path: str, out_path: str, seed: str) -> int:
    global SPEC
    SPEC = fixture_spec.derive(seed)

    try:
        observations = json.loads(judge_io.read_text(obs_path))
    except (OSError, ValueError) as exc:
        observations = {}
        print(f"judge: cannot read observations: {exc}", file=sys.stderr)

    results = []
    for node, judge in JUDGES.items():
        classname, name = node.split("::", 1)
        probe = observations.get(node)
        if probe is None:
            results.append((classname, name, "no observation from probe"))
            continue
        if not probe.get("ok"):
            results.append((classname, name, f"probe error: {probe.get('error', 'unknown')}"))
            continue
        try:
            judge(probe["obs"])
            results.append((classname, name, ""))
        except Fail as exc:
            results.append((classname, name, str(exc)))
        except Exception as exc:  # noqa: BLE001 - a malformed observation is a failed fact, not a crash
            results.append((classname, name, f"judge error: {type(exc).__name__}: {exc}"))

    pathlib.Path(out_path).write_text(junit(results))
    for classname, name, failure in results:
        print(f"{'FAIL' if failure else 'pass'} {classname}::{name}"
              + (f"  {failure[:160]}" if failure else ""))
    return 0


if __name__ == "__main__":
    # argv: observations, junit out, seed, artifacts dir. g2's scenarios are pure
    # in-process calls, so the artifacts directory is unused here.
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
