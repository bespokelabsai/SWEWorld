"""g3 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and, for
the source-text checks, the submission's own files under SUBMISSION_SRC — plus, for
the one rule that says "as it shipped", the pristine tree under
CURATOR_BASELINE_DIR. It applies
the assertions the g3 suite has always made, writing a `junit.xml` whose
`classname`/`name` are the current suite's node ids — so `score.py` folds them into
the identical fact keys and `test.sh`/`score.py` are unchanged. No agent code runs
here, so the report cannot be forged; and `test.sh` locks this file to root, so the
worker cannot read the numbers below to forge an observation that matches them. That
pair is what closes the forgery in tasks/lessons.md (2026-09-09) that a uid alone
could not.

The expected values are lifted from `test_open`/`test_r1`/`test_r2`; those files stay
the human-readable source of truth and the fact<->test bijection. They live with the
suite's source and are deliberately NOT shipped in the task — their assertions would
hand the worker the answers — so the graded files here are this one, `probe.py` and
`probe_support.py`, and the `test_*::test_*` node ids below are names `score.py` folds
by, not paths. Where a test read
source with `inspect.getsource(...)` this reads the module file directly and pulls
the same class body out with the AST (parsing text executes nothing), which is both
safe in this process and a more faithful check of the graded artifact than trusting
the worker to report its own source.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import sys
from xml.sax.saxutils import escape, quoteattr

# The judge runs `python3 -I` with no PYTHONPATH, so /tests is not importable by
# default. judge_io holds the hardened reads (no symlinks, size-capped) every
# agent-influenced path goes through; harness.py cannot: it imports pytest.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import judge_io  # noqa: E402


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def raised_type(info, typename, msg=""):
    ok(info.get("raised"), f"{msg}: expected {typename}, none raised")
    ok(typename in info.get("mro", []), f"{msg}: {typename} not in {info.get('mro')}")


# ---------------------------------------------------------------------------
# Reading the submitted source (root, submission NOT importable)
# ---------------------------------------------------------------------------
def _module_source(rel_candidates) -> str:
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    for rel in rel_candidates:
        path = root / rel
        if path.is_file():
            return judge_io.read_text(path)
    raise Fail(f"cannot read source at any of {rel_candidates} under {root}")


def _baseline_source(rel: str) -> str:
    """One file as the world shipped it, from the root-owned copy the runner staged.

    `run_suites.run_split` names that copy in CURATOR_BASELINE_DIR (the
    `bespokelabs/curator` package root, so the paths below are package-relative,
    not `src/`-relative like SUBMISSION_SRC). It is how a judge asks "is this
    expression reused as-is": `protected_files` can only compare whole files,
    and every rule of that shape here is about code INSIDE a file the ticket
    tells the agent to edit.

    A missing baseline FAILS the fact rather than skipping it. Passing blind is
    how an unenforced preservation rule got through in the first place — the
    v10 reviewer found `attempts_left`'s seeding "checked" by a regex a comment
    satisfied — and a grader that cannot see the pristine tree cannot tell a
    reused expression from a deleted one.
    """
    root = os.environ.get("CURATOR_BASELINE_DIR", "")
    if not root:
        raise Fail("CURATOR_BASELINE_DIR is unset, so nothing can be compared "
                   "against the pristine tree; the runner stages it")
    path = pathlib.Path(root) / rel
    if not path.is_file():
        raise Fail(f"no pristine copy of {rel} under {root}")
    return judge_io.read_text(path)


def _class_source(src: str, name: str) -> str:
    """The source of one class body — the faithful stand-in for
    `inspect.getsource(cls)`, so a comment elsewhere in the file cannot decide a
    check the test scoped to the class."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            segment = ast.get_source_segment(src, node)
            if segment:
                return segment
    raise Fail(f"class {name!r} not found in source")


_RETRY_POLICY = ["bespokelabs/curator/request_processor/online/retry_policy.py",
                 "bespokelabs/curator/request_processor/online/retry_policy/__init__.py"]
_BASE_PROCESSOR = ["bespokelabs/curator/request_processor/online/base_online_request_processor.py",
                   "bespokelabs/curator/request_processor/online/base_online_request_processor/__init__.py"]


# The three hand-rolled rate-limit blocks section 3 of the ticket deletes. Named
# here rather than derived, because the check is "these files no longer touch the
# counters" and the file set is the ticket's own list.
_PROVIDERS = ("request_processor/online/openai_online_request_processor.py",
              "request_processor/online/anthropic_online_request_processor.py",
              "request_processor/online/litellm_online_request_processor.py")
_COUNTERS = ("num_api_errors", "num_other_errors", "num_rate_limit_errors")

# The `max_retries` probe.py configures the processor with before driving its own
# request-submission loop, so the attempts_left the production construction site
# arrives with is a number nothing else in the suite uses (the request factory
# seeds 3, the config default is 10). Must match PRODUCTION_MAX_RETRIES there.
_PRODUCTION_MAX_RETRIES = 9

# The pause the cooldown scenario must produce. probe.py pins the clock the
# processor reads to `FROZEN_NOW` and puts the tracker's horizon
# `COOLDOWN_AHEAD_SECONDS` ahead of it, so the remaining cooldown is that number
# exactly and is compared exactly. The two files must agree.
_COOLDOWN_AHEAD_SECONDS = 4.0


def _is_instance_dict(node) -> bool:
    """`x.__dict__` or `vars(x)` — the two ways to reach an object's attribute map."""
    if isinstance(node, ast.Attribute) and node.attr == "__dict__":
        return True
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "vars")


def _counter_written_by(node) -> str | None:
    """The counter name this statement writes, or None.

    Every shape a write can take, not just the one the pristine tree happens to
    use. The v12 audit found this check matched `ast.AugAssign` alone, and the
    pristine blocks are all `-= 1`: `status_tracker.num_api_errors =
    status_tracker.num_api_errors - 1`, `setattr(status_tracker,
    "num_api_errors", ...)` and a write through `__dict__`/`vars()` all left the
    double counting in place and kept the fact. The v13 review then found the
    same hole one call deeper: `object.__setattr__(status_tracker,
    "num_api_errors", ...)` is not named `setattr`, so the check waved it
    through. Six shapes are read now -- augmented, plain and annotated
    assignment, a subscript write, `del`, and the `setattr`/`delattr` family
    including `object.__setattr__` and a bound `tracker.__setattr__` -- plus a
    bulk `__dict__`/`vars()` `.update(...)`.

    Anything that names the attribute but hides the name from the AST is failed
    rather than allowed: a `setattr` whose name is computed, an `update` whose
    mapping is a variable. A grader that cannot see which attribute is written
    must not report that none was.
    """
    targets = []
    if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    elif isinstance(node, ast.Delete):
        targets = node.targets
    for target in targets:
        for inner in ([target] if not isinstance(target, (ast.Tuple, ast.List)) else target.elts):
            if isinstance(inner, ast.Attribute) and inner.attr in _COUNTERS:
                return inner.attr
            if (isinstance(inner, ast.Subscript) and isinstance(inner.slice, ast.Constant)
                    and inner.slice.value in _COUNTERS):
                return str(inner.slice.value)
    if isinstance(node, ast.Call):
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        # `setattr(obj, name, v)` / `delattr(obj, name)` and the unbound dunders
        # `object.__setattr__(obj, name, v)` all carry the name second; a bound
        # `obj.__setattr__(name, v)` carries it first. Arity is what separates
        # the bound call from the unbound one.
        if name in ("setattr", "delattr", "__setattr__", "__delattr__"):
            bound = name.startswith("__") and isinstance(func, ast.Attribute) and len(node.args) <= 2
            index = 0 if bound else 1
            if len(node.args) > index:
                attr = node.args[index]
                if isinstance(attr, ast.Constant):
                    if attr.value in _COUNTERS:
                        return str(attr.value)
                else:
                    return f"<a {name} whose attribute name the grader cannot read>"
        if name == "update" and isinstance(func, ast.Attribute) and _is_instance_dict(func.value):
            for keyword in node.keywords:
                if keyword.arg in _COUNTERS:
                    return keyword.arg
            for arg in node.args:
                if isinstance(arg, ast.Dict):
                    for key in arg.keys:
                        if isinstance(key, ast.Constant) and key.value in _COUNTERS:
                            return str(key.value)
                else:
                    return "<an attribute-map update whose keys the grader cannot read>"
    return None


def _check_providers_stop_counting():
    """No provider processor still mutates a tracker counter.

    Section 3 of the ticket is "stop double-counting": the providers re-raise and
    the base class classifies and counts once. The suite's other behavioural
    checks all run against a stub subclass of the BASE processor, so a submission
    that added the base-class routing and left all three `num_api_errors -= 1`
    compensations in place passed every fact -- the double counting the ticket
    exists to remove, undetected. Read from the source because that is what sees
    a write on a path this grader does not drive; `_check_provider_handlers_reraise`
    is the same clause read from a run of the rate-limit branch itself.

    Scope, stated exactly, because the v13 review caught this docstring
    overclaiming: the three provider modules are parsed whole rather than at the
    ticket's line ranges, so a decrement moved into a helper anywhere in the SAME
    file is caught. A write performed in a fourth module that a provider calls
    into is not -- nothing here follows a call -- though on the rate-limit path
    the behavioural check now sees it anyway, since it compares the tracker's
    three counters across the call. What remains uncovered is a write on a
    provider path nothing here drives, and that gap is left open on purpose: the
    ticket tells the agent to delete those lines, so hiding one buys no score and
    cannot touch the grader. The criterion this answers to says a violation that
    gives no advantage and cannot corrupt verification is cosmetic; chasing it
    across modules would start flagging the counter writes a correct solution is
    *supposed* to make.
    """
    for rel in _PROVIDERS:
        src = _module_source(("bespokelabs/curator/" + rel, "src/bespokelabs/curator/" + rel))
        for node in ast.walk(ast.parse(src)):
            counter = _counter_written_by(node)
            if counter:
                raise Fail(f"{rel.rsplit('/', 1)[-1]} still writes "
                           f"status_tracker.{counter} at line {node.lineno}; "
                           "the provider blocks must re-raise and let the base class count")


def _check_provider_handlers_reraise(o):
    """...and each of those blocks still raises the failure it saw.

    instruction.md:120-126 is one sentence with two halves: the three blocks
    "stop mutating tracker counters" and "just re-raise". `_check_providers_stop_counting`
    reads the first half out of the source, which is all a source read can do;
    this reads the second out of the run. A handler that deletes the decrements
    and then returns instead of raising, or that swaps the provider's exception
    for one of its own, satisfied every check here while the failure never
    reached the base class at all -- and the base class counting once is the
    whole point of the clause.

    The observations come from the worker driving each provider's rate-limit
    branch (`probe_support.drive_provider_rate_limit`). A branch the worker could
    not enter fails the fact with the error it reported: an unobservable
    requirement is not a satisfied one.
    """
    seen = o.get("providers") or {}
    for which in ("openai", "anthropic", "litellm"):
        got = seen.get(which) or {}
        ok(got.get("driven"),
           f"{which}'s rate-limit branch could not be driven, so whether it "
           f"re-raises cannot be read: {got.get('error')}")
        ok(got.get("raised"),
           f"{which}'s rate-limit branch returned instead of raising; the base "
           "class never sees the failure, so nothing classifies or counts it")
        eq(got.get("counters_after"), got.get("counters_before"),
           f"{which}'s rate-limit branch moved a tracker counter "
           f"(num_rate_limit_errors, num_api_errors, num_other_errors went "
           f"{got.get('counters_before')} -> {got.get('counters_after')}); the "
           "base class counts the failure once")
    # Identity, and only for litellm: its block is the one that CATCHES the
    # provider's own exception, so "just re-raise" is `raise e` and is observable
    # as the same object coming back out. The openai and anthropic blocks build
    # their own `Exception(f"API error: {error}")` in the pristine tree too, so
    # the most the ticket says about them is that they still raise.
    ok((seen.get("litellm") or {}).get("same_object"),
       "litellm's rate-limit handler did not re-raise the exception it caught "
       f"(what propagated: {(seen.get('litellm') or {}).get('raised')})")


def _apirequest_sites(src: str) -> list:
    """Every `APIRequest(...)` construction, and what it seeds `attempts_left` from.

    One dict per call site: its line, the AST dump of the `attempts_left=`
    expression (None when the call passes none), whether that expression reads a
    `max_retries` attribute, and whether the call unpacks a mapping.

    Bound to the construction CALL, not to the file. The v12 review found the
    previous version collecting every `attempts_left=` keyword anywhere in
    `base_online_request_processor.py` and testing set membership, so a
    submission could seed the request the processor really builds from anything
    it liked and park the pristine `attempts_left=self.config.max_retries`
    expression in a method nothing calls. An expression at a construction site
    is on the path that makes a request; one in dead code is not a site.

    `ast.dump` carries no line numbers, so moving the call or reflowing its
    arguments is not a change, while renaming what the argument reads is. Text
    is never searched: the v10 review found the original regex satisfied by a
    comment that mentioned the old line.
    """
    sites = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name != "APIRequest":
            continue
        seed = None
        for kw in node.keywords:
            if kw.arg == "attempts_left":
                seed = kw.value
        sites.append({
            "line": node.lineno,
            "dump": ast.dump(seed) if seed is not None else None,
            "reads_max_retries": seed is not None and any(
                isinstance(inner, ast.Attribute) and inner.attr == "max_retries"
                for inner in ast.walk(seed)),
            "splat": any(kw.arg is None for kw in node.keywords),
        })
    return sites


def _check_attempts_left_seeding():
    """`attempts_left` is still seeded from `config.max_retries`, as it shipped.

    r1's scope says only the amount deducted per failure changes; the seeding
    stays, and instruction.md:105 states it outright. Asked of every APIRequest
    construction in the file rather than of the file as a whole, so a pristine
    copy of the expression somewhere unreachable cannot answer for the
    construction that actually runs. `production_attempts_left` in judge_r1_scope
    is the behavioural half of the same clause: the processor's own submission
    loop builds a request and the value it arrives with is read off it.
    """
    rel = "request_processor/online/base_online_request_processor.py"
    shipped = _apirequest_sites(_baseline_source(rel))
    ok(shipped, "the pristine base processor constructs no APIRequest, so there "
                "is nothing to compare the seeding against")
    sites = _apirequest_sites(_module_source(_BASE_PROCESSOR))
    ok(sites, "nothing in base_online_request_processor.py constructs an "
              "APIRequest any more")
    for site in sites:
        where = f"the APIRequest built at line {site['line']}"
        ok(not site["splat"],
           f"{where} unpacks its arguments, so what seeds attempts_left cannot "
           "be read from the source; pass it as a keyword")
        ok(site["dump"] is not None,
           f"{where} passes no attempts_left=; the field keeps its seeding at "
           "the construction site")
        ok(site["reads_max_retries"],
           f"{where} seeds attempts_left from something that does not read "
           "config.max_retries")
    lost = sorted({s["dump"] for s in shipped} - {s["dump"] for s in sites})
    ok(not lost, "the request's attempts_left is no longer seeded the way the "
                 f"pristine tree seeds it; {lost} is gone, leaving "
                 f"{sorted(s['dump'] for s in sites)}")


def _check_retry_policy_imports():
    """retry_policy.py is standard-library only — the AST check of test_open,
    over the file on disk.

    instruction.md:11 states both halves: "Pure, standard-library only. It
    imports nothing from `aiohttp`, `time` or `random`." Only the named three
    were rejected before, so `import requests` — a third-party dependency the
    module is not allowed to have, in the file the ticket calls pure — passed.
    So the check is an ALLOWLIST: every module named resolves to this
    interpreter's standard library or to the project itself. A relative import
    is the project by construction and is not collected below.

    A named import is the only kind the AST can read, so a dynamic one is failed
    rather than allowed: `importlib.import_module("time")` and
    `__import__("random")` both satisfy a list of import statements while doing
    exactly what the ticket forbids, and a grader that cannot see what a call
    reaches for must not report that it reaches for nothing.
    """
    src = _module_source(_RETRY_POLICY)
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module.split(".")[0])
    ok(imported.isdisjoint({"aiohttp", "time", "random"}),
       f"retry_policy.py imports {sorted(imported)}; it must not reach for aiohttp, time or random")
    # Fail-closed: an interpreter that cannot name its own standard library
    # cannot decide this, and "cannot check" must never read as "checked".
    stdlib = getattr(sys, "stdlib_module_names", None)
    ok(stdlib, "this interpreter does not expose sys.stdlib_module_names, so "
               "'standard-library only' cannot be decided; the fact fails rather "
               "than passing unchecked")
    outside = sorted(imported - set(stdlib) - {"bespokelabs"})
    ok(not outside,
       f"retry_policy.py imports {outside}, which is neither the standard library "
       "nor this project; the module is standard-library only")
    dynamic = [node.lineno for node in ast.walk(tree)
               if isinstance(node, ast.Call)
               and (getattr(node.func, "id", None) == "__import__"
                    or getattr(node.func, "attr", None) == "import_module")]
    ok(not dynamic and "importlib" not in imported,
       "retry_policy.py imports a module dynamically (lines "
       f"{dynamic or sorted(imported & {'importlib'})}), so what it reaches for "
       "cannot be read; the module's imports have to be visible")


# ---------------------------------------------------------------------------
# Resolving the code that actually runs
# ---------------------------------------------------------------------------
#
# A source check that asks only "does this call appear somewhere in the file"
# is answered by code nothing runs. g1's judge measured that as a full bypass
# of its reward -- pristine statements parked under `while False:` plus a
# helper nothing references scored 11/11 -- and the same dodges satisfied the
# attempt-label clause here: `if False: format_attempt_label(0, 0)`, a call in
# a method nothing calls, a value computed once in a class body, or a second
# `def` of the method with the real one below it. So the call below is looked
# for in LIVE code only, and live means all three of:
#
#   * the definition Python binds -- module level, last `def` of a name wins,
#     and a name defined twice in one namespace is REFUSED rather than
#     resolved, because a duplicate is the vehicle every one of those dodges
#     used;
#   * reachable: a scope something outside the module enters (a public or
#     dunder method, which is how the framework calls in) or a definition live
#     code mentions by name, to a fixpoint;
#   * not in a branch a literal test closes. `if False:` is not the only
#     spelling -- `while False:`, `if not True:`, `if ():`, `for _ in []:` and
#     anything after a `return`/`raise`/`continue`/`break` are just as dead,
#     and each of those was accepted before.
_TERMINAL = (ast.Return, ast.Raise, ast.Continue, ast.Break)
_TRY = (ast.Try,) + ((ast.TryStar,) if hasattr(ast, "TryStar") else ())
_ATTEMPT_LABEL = "format_attempt_label"


def _tree(src: str) -> ast.Module:
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise Fail(f"the submission does not parse: {exc}")


def _effective(nodes: list, what: str):
    """The definition that binds, or a Fail if the name is defined twice."""
    if len(nodes) > 1:
        raise Fail(f"{what} is defined {len(nodes)} times in one namespace; Python binds "
                   "the last one, so a duplicate definition cannot stand in for the "
                   "implementation that runs")
    return nodes[-1] if nodes else None


def _literal_truth(node):
    """True/False when a test is a literal the parse itself settles, else None."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        inner = _literal_truth(node.operand)
        return None if inner is None else not inner
    try:
        return bool(ast.literal_eval(node))
    except Exception:
        # Not a literal, so nothing can be concluded: the branch stays live.
        return None


class _Live:
    """What one pass over one scope's live code found."""

    def __init__(self):
        self.calls = []    # lineno of a call to the helper, outside every handler
        self.names = set()  # every name the live code mentions
        self.defs = []     # definitions it binds without entering


def _walk_expr(node, live, *, handler, counts):
    if isinstance(node, ast.Name):
        live.names.add(node.id)
    elif isinstance(node, ast.Attribute):
        live.names.add(node.attr)
    if counts and not handler and _is_label_call(node):
        live.calls.append(node.lineno)
    if isinstance(node, ast.Lambda):
        # A lambda body runs when the lambda is called, which is not here.
        counts = False
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.stmt):
            _walk_stmt(child, live, handler=handler, counts=counts)
        else:
            _walk_expr(child, live, handler=handler, counts=counts)


def _walk_body(body, live, *, handler, counts):
    for stmt in body:
        _walk_stmt(stmt, live, handler=handler, counts=counts)
        if isinstance(stmt, _TERMINAL):
            return


def _walk_stmt(stmt, live, *, handler, counts):
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
        live.defs.append(stmt)
        for node in (list(stmt.decorator_list) + list(stmt.args.defaults)
                     + [d for d in stmt.args.kw_defaults if d is not None]):
            _walk_expr(node, live, handler=handler, counts=counts)
        return
    if isinstance(stmt, ast.ClassDef):
        for node in list(stmt.decorator_list) + list(stmt.bases):
            _walk_expr(node, live, handler=handler, counts=counts)
        # A class body does run where it is written, but what it computes there
        # is a value fixed at import; it cannot be a log line in a retry loop,
        # and it cannot make the two log sites agree.
        _walk_body(stmt.body, live, handler=handler, counts=False)
        return
    if isinstance(stmt, ast.If):
        truth = _literal_truth(stmt.test)
        _walk_expr(stmt.test, live, handler=handler, counts=counts)
        if truth is not False:
            _walk_body(stmt.body, live, handler=handler, counts=counts)
        if truth is not True:
            _walk_body(stmt.orelse, live, handler=handler, counts=counts)
        return
    if isinstance(stmt, ast.While):
        truth = _literal_truth(stmt.test)
        _walk_expr(stmt.test, live, handler=handler, counts=counts)
        if truth is not False:
            _walk_body(stmt.body, live, handler=handler, counts=counts)
        _walk_body(stmt.orelse, live, handler=handler, counts=counts)
        return
    if isinstance(stmt, (ast.For, ast.AsyncFor)):
        empty = _literal_truth(stmt.iter)
        _walk_expr(stmt.iter, live, handler=handler, counts=counts)
        if empty is not False:
            _walk_body(stmt.body, live, handler=handler, counts=counts)
        _walk_body(stmt.orelse, live, handler=handler, counts=counts)
        return
    if isinstance(stmt, _TRY):
        _walk_body(stmt.body, live, handler=handler, counts=counts)
        for caught in stmt.handlers:
            if caught.type is not None:
                _walk_expr(caught.type, live, handler=handler, counts=counts)
            _walk_body(caught.body, live, handler=True, counts=counts)
        _walk_body(stmt.orelse, live, handler=handler, counts=counts)
        _walk_body(stmt.finalbody, live, handler=handler, counts=counts)
        return
    # Anything else: its expressions, and any statement list it holds, with no
    # dead-branch pruning. Leaning live is the safe direction for a statement
    # shape this judge does not model -- it can only make the check milder.
    _walk_expr(stmt, live, handler=handler, counts=counts)


def _is_label_call(node) -> bool:
    return (isinstance(node, ast.Call)
            and (getattr(node.func, "id", None) == _ATTEMPT_LABEL
                 or getattr(node.func, "attr", None) == _ATTEMPT_LABEL))


def _accessor(func) -> bool:
    """A `@x.setter`/`@x.getter`/`@x.deleter` or `@overload` companion `def`.

    Python does rebind the name for these, but the pair is one property or one
    signature, not a decoy: refusing them would fail a submission that adds a
    setter to a property it keeps. Their bodies still count as live code.
    """
    for dec in func.decorator_list:
        if isinstance(dec, ast.Attribute) and dec.attr in ("setter", "getter", "deleter"):
            return True
        if getattr(dec, "id", None) == "overload" or getattr(dec, "attr", None) == "overload":
            return True
    return False


def _register(defs: dict, node) -> None:
    """`node` under its own name, once, whatever path reached it."""
    holder = defs.setdefault(node.name, [])
    if not any(existing is node for existing in holder):
        holder.append(node)


def _namespace_defs(body, where: str, defs: dict) -> None:
    """The `def`s one namespace binds, added to `defs` by their bare name.

    By bare name because that is what a `self.foo()` call site spells, and
    through `_effective` so a namespace that defines one name twice is a Fail.
    """
    funcs = [stmt for stmt in body
             if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for name in sorted({func.name for func in funcs}):
        same = [func for func in funcs if func.name == name]
        _effective([func for func in same if not _accessor(func)], f"{where}{name}()")
        for func in same:
            _register(defs, func)


def _live_label_calls(tree: ast.Module) -> list:
    """Lines where LIVE code outside every `except` handler calls the helper."""
    defs = {}
    _namespace_defs(tree.body, "", defs)
    classes = [stmt for stmt in tree.body if isinstance(stmt, ast.ClassDef)]
    names = [cls.name for cls in classes]
    dupes = sorted({name for name in names if names.count(name) > 1})
    if dupes:
        raise Fail(f"{', '.join(dupes)} is defined more than once at module level; Python "
                   "binds the later definition, so a decoy class cannot stand in for it")
    for cls in classes:
        _namespace_defs(cls.body, f"{cls.name}.", defs)

    # Roots: the module body (whose own calls do not count, see _walk_stmt on a
    # class body), plus every public or dunder definition, which the framework
    # calls from outside and nothing in the module has to mention.
    pending = [(tree.body, False)]
    entered = set()
    for name, nodes in defs.items():
        if not name.startswith("_") or (name.startswith("__") and name.endswith("__")):
            for node in nodes:
                entered.add(id(node))
                pending.append((node.body, True))

    calls, mentioned = [], set()
    while pending:
        body, counts = pending.pop()
        live = _Live()
        _walk_body(body, live, handler=False, counts=counts)
        calls.extend(live.calls)
        mentioned |= live.names
        for node in live.defs:
            _register(defs, node)
        for name in sorted(mentioned):
            for node in defs.get(name, []):
                if id(node) not in entered:
                    entered.add(id(node))
                    pending.append((node.body, True))
    return sorted(calls)


def _stale_attempt_arithmetic(tree: ast.Module) -> list:
    """Lines still computing an attempt number as `max_retries - attempts_left`."""
    stale = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub)):
            continue
        sides = [side.attr for side in (node.left, node.right)
                 if isinstance(side, ast.Attribute)]
        if sorted(sides) == ["attempts_left", "max_retries"]:
            stale.append(node.lineno)
    return sorted(stale)


def _check_attempt_label_shared_by_both_log_sites():
    """The retry-loop log line uses `format_attempt_label`, not its own arithmetic.

    instruction.md:117-118 states it outright -- "the retry-loop debug line at
    line 424 uses `format_attempt_label` so both log sites agree on the attempt
    number" -- and nothing graded it: the helper's OUTPUT is checked (`labels`
    above), so an implementation that wrote the helper, called it from the
    `except` block and left line 424 computing `self.config.max_retries -
    retry_request.attempts_left` passed every node while the two log sites
    disagreed by one. That arithmetic is also the line the ticket's change makes
    wrong, since `attempts_left` no longer falls by one per failure -- so both
    halves of the clause are asked for: a call in live code, and the old
    subtraction gone from the module.

    Read structurally, not by line number: a call has to appear somewhere in the
    module's LIVE code (see the comment above `_TERMINAL` for what that resolves
    to) and OUTSIDE every `except` handler. That is the retry loop, or a helper
    the retry loop calls, and not the failure path -- which is what "both log
    sites" means. Text is never searched, so a comment or a docstring mentioning
    the helper decides nothing.

    The clause and no more: WHERE the call sits is not constrained beyond "live,
    outside the handlers", because instruction.md:117-118 does not name a method.
    The reference patch calls it from the submission loop in
    `process_requests_from_file`, which is public and therefore a root; the
    pristine file's one `except` handler (526-564) does not contain the retry
    loop, so a correct solution cannot be trapped by the handler rule.
    """
    tree = _tree(_module_source(_BASE_PROCESSOR))
    ok(_live_label_calls(tree),
       "no live code outside an except handler calls format_attempt_label in "
       "base_online_request_processor.py, so the retry-loop log line is still "
       "counting attempts its own way and the two log sites disagree (a call in "
       "a dead branch, in a definition nothing reaches, or in a class body is "
       "not the log line)")
    stale = _stale_attempt_arithmetic(tree)
    ok(not stale,
       f"base_online_request_processor.py still computes max_retries - attempts_left "
       f"at line(s) {stale}; that is the attempt number the retry-loop log line used "
       "before, and the change makes it wrong -- attempts_left no longer falls by one "
       "per failure, so the label comes from format_attempt_label instead")


def _base_processor_class_source() -> str:
    return _class_source(_module_source(_BASE_PROCESSOR), "BaseOnlineRequestProcessor")


# ---------------------------------------------------------------------------
# open feature
# ---------------------------------------------------------------------------
def judge_open(o):
    # P1: the enum, its order, its str mixin
    eq(o["enum_names"], ["THROTTLE", "TRANSIENT", "CONTRACT", "TERMINAL"], "FailureClass names/order")
    eq(o["enum_values"], ["throttle", "transient", "contract", "terminal"], "FailureClass values")
    eq(o["enum_len"], 4, "FailureClass length")
    ok(o["contract_is_str"], "FailureClass.CONTRACT is not a str-valued member")

    # the module boundary: standard library only
    _check_retry_policy_imports()
    # section 3, both halves: the providers stop counting (source) and still
    # raise what they saw (the run)
    _check_providers_stop_counting()
    _check_provider_handlers_reraise(o)

    # P2: status first, then the table exactly as the ticket writes it
    eq(o["classify_status"], ["TRANSIENT", "THROTTLE", "THROTTLE", "CONTRACT", "CONTRACT",
                              "CONTRACT", "TERMINAL", "TERMINAL", "TERMINAL", "TRANSIENT",
                              "TRANSIENT", "TRANSIENT", "TRANSIENT", "CONTRACT", "TRANSIENT"],
       "classify_failure status signal")
    # P3: the type signal walks the MRO by name
    eq(o["classify_type"], ["THROTTLE", "CONTRACT", "CONTRACT", "TRANSIENT", "TRANSIENT",
                            "TRANSIENT", "TERMINAL", "TERMINAL", "CONTRACT", "CONTRACT"],
       "classify_failure type signal")
    # P4: marker order beats message position; the default is TRANSIENT
    eq(o["classify_marker"], ["THROTTLE", "THROTTLE", "THROTTLE", "THROTTLE", "TRANSIENT",
                              "TRANSIENT", "TRANSIENT", "TERMINAL", "TERMINAL", "TRANSIENT",
                              "TRANSIENT", "THROTTLE", "TRANSIENT"], "classify_failure marker signal")
    # The guarantee over all three signals: "never raises", which the ticket
    # states outright and only ordinary exceptions ever tested. Rows 2, 3 and 4
    # are the ones a blanket `try: ... except: return TRANSIENT` fails — an
    # unreadable status must not cost the message signal its answer, an
    # unreadable message must not cost a readable 429 its own, and with both
    # accessors broken the exception's TYPE still names a class.
    eq(o["classify_hostile"], ["TRANSIENT", "THROTTLE", "THROTTLE", "TERMINAL", "TRANSIENT"],
       "classify_failure must return a class whatever the exception's status "
       "and message accessors do")

    # P5/P6: the schedule, the cap before the jitter, the draw count
    eq(o["construct_calls"], [0, 0], "neither injected callable may be called at construction")
    ok(o["clock_no_default"], "clock has a default")
    ok(o["jitter_no_default"], "jitter has a default")
    eq(o["delays"], [5.0, 10.0, 20.0, 37.5, 37.5, 0.312, 0.938, 2.812, 8.438, 12.5, 12.5], "delay_for schedule")
    eq(o["draws_after_positive"], 11, "one jitter draw per positive delay")
    eq(o["zero_delays"], [0.0, 0.0], "contract/terminal delays are zero")
    eq(o["draws_after_zero"], 11, "a zero delay must not consume the jitter source")
    eq(o["clock_calls_after_delays"], 0, "delay_for has no business reading the clock")
    eq(o["clamp"], [4.0, 8.0, 8.0, 4.0], "jitter clamped to [0,1] on a 5s base throttle delay")
    raised_type(o["delay_zero_attempt_raises"], "ValueError", "delay_for at attempt 0")

    # P7: the verdict's shape, its routed counter and its reason code
    ok(o["is_dataclass"], "the verdict is not the frozen dataclass the ticket asks for")
    raised_type(o["frozen"], "FrozenInstanceError", "the verdict is not frozen")
    ok(o["v_retry"] is True, "a throttle with budget must retry")
    eq(o["v_class"], "THROTTLE", "verdict failure class")
    eq(o["v_attempt"], 1, "verdict attempt index")
    eq(o["counter_throttle"], "num_rate_limit_errors", "throttle counter")
    eq(o["reason_throttle"], "throttle:retry", "throttle reason code")
    eq(o["counter_contract"], "num_other_errors", "contract counter")
    eq(o["reason_contract"], "contract:retry", "contract reason code")
    eq(o["counter_transient"], "num_api_errors", "transient counter")
    eq(o["reason_transient"], "transient:retry", "transient reason code")
    ok(o["terminal_retry"] is False, "a terminal verdict must not retry")
    eq(o["terminal_counter"], "num_api_errors", "terminal counter")
    eq(o["terminal_reason"], "terminal:abort", "terminal reason code")
    eq(o["terminal_attempt"], 3, "terminal attempt index")
    eq(o["terminal_delay"], 0.0, "terminal delay")

    # P9: exactly one counter moves per failure
    eq(o["counter_sequence"], [[1, 0, 0], [1, 1, 0], [1, 1, 1], [1, 2, 1]], "one counter per failure")

    # P10: the summary and the shared attempt label
    eq(o["summary_a"], ["[throttle] rate limit (x3)", "[transient] boom (x2)", "[contract] bad (x1)"], "summary a")
    eq(o["summary_b"], ["[transient] a (x2)", "[contract] b (x1)"], "summary b")
    eq(o["summary_c"], ["[transient] a (x1)", "[contract] a (x1)"], "summary c")
    eq(o["summary_empty"], [], "summary empty")
    eq(o["labels"], ["attempt #1 of 11", "attempt #4 of 4", "attempt #1 of 1"], "attempt labels")
    # ...and the ticket's reason for the helper existing: the retry-loop log site
    # shares it. Source, because a debug line's text is not a behaviour any probe
    # can reach.
    _check_attempt_label_shared_by_both_log_sites()

    # the wiring: APIRequest's new fields, and the except block
    ok("attempts_made" in o["apirequest_fields"], f"APIRequest has {o['apirequest_fields']}")
    ok("failure_log" in o["apirequest_fields"], f"APIRequest has {o['apirequest_fields']}")
    eq(o["fresh_attempts_made"], 0, "fresh attempts_made")
    eq(o["fresh_failure_log"], [], "fresh failure_log")
    eq(o["fresh_attempts_left"], 3, "fresh attempts_left")
    ok(o["built_policy"], "__init__ built no RetryPolicy on the processor")
    eq(o["queue_size"], 1, "a rate-limited request with budget to spare was not re-queued")
    ok(o["queue_is_request"], "the re-queued object is not the request")
    eq(o["request_attempts_made"], 1, "request attempts_made after one failure")
    eq(o["request_failure_log"], [["THROTTLE", "API error: Rate limit reached for gpt-4o"]], "request failure_log")
    eq(o["wired_counters"], [1, 0, 0], "a 429 must be counted once, as a rate limit")

    # The give-up branch of the same except block, which only the re-queue half
    # was ever observed: the ticket names the response a request that will not
    # be retried gets, and its formatted errors.
    eq(o["exhausted_written"], 1, "a request the policy gave up on wrote no response")
    eq(o["exhausted_errors"], ["[terminal] invalid api key (x1)"],
       "the given-up request's response_errors must be the formatted failure summary")
    ok(o["exhausted_message_is_none"], "that response's response_message must be None")
    ok(o["exhausted_raw_is_none"], "that response's raw_response must be None")


# ---------------------------------------------------------------------------
# r1 — what a failure costs, and the per-request 429 waivers
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    eq(o["default_waivers"], 6, "DEFAULT_THROTTLE_WAIVERS")
    ok("throttle_waivers_left" in o["apirequest_fields"], f"APIRequest carries no waiver counter; it has {o['apirequest_fields']}")
    eq(o["fresh_waivers"], 6, "a fresh request starts at DEFAULT_THROTTLE_WAIVERS")
    ok(o["decide_var_keyword"] or {"attempts_made", "attempts_left", "throttle_waivers_left"} <= set(o["decide_params"]),
       f"decide takes {o['decide_params']}")
    eq(o["transient"], [8, 4], "a transient failure costs one attempt and no waiver")
    eq(o["contract"], [7, 4], "a contract failure costs two attempts and no waiver")
    eq(o["waived"], [True, 9, 3, 1, "throttle:retry"], "a throttle with a waiver spends the waiver, not the budget")
    eq(o["unwaived"], [True, 8, 0, 1, "throttle:retry"], "with no waivers left a throttle costs one attempt")


def judge_r1_scope(o):
    ok(o["has_waivers"], "the per-request throttle waiver budget is not implemented")
    eq(o["second_waivers"], 6, "a fresh request must start with six waivers")
    eq(o["first_waivers"], 0, "the drained request keeps its own count")
    eq(o["loop_waivers"], [5, 5, 5, 5, 5, 5], "the waiver count comes from the argument, not policy state")
    eq(o["loop_budgets"], [5, 5, 5, 5, 5, 5], "the budget comes from the argument, not policy state")
    eq(o["tracker_waiver_fields"], [], "OnlineStatusTracker gained a waiver field")
    eq(o["tracker_waiver_attrs"], [], "OnlineStatusTracker instance gained a waiver attribute")
    eq(o["config_waiver_fields"], [], "OnlineRequestProcessorConfig gained a waiver knob")
    ok(o["attempts_left_no_default"], "attempts_left must still be seeded by the caller")
    _check_attempts_left_seeding()
    # Behaviour, because source alone could be answered by a copy of the
    # expression in code nothing reaches: probe.py runs the processor's own
    # submission loop with max_retries=9 and reports the attempts_left the
    # request it built arrived with. Every other request in this suite is built
    # by the probe itself, which is why the production path went unobserved.
    #
    # Where this stops, deliberately: the recorder halts the run AT the
    # construction, so a submission could shrink `request.attempts_left` on the
    # next line and go unseen. Left open by the same "judge by advantage" rule
    # as the cross-module counter write — every budget the nine facts grade is
    # handed to `decide()` explicitly by the probe, so the real request's
    # counters are not an input to any score, and a submission that sabotages
    # them only breaks its own library. Closing it would mean driving the whole
    # submission loop against a live provider, which is exactly the network this
    # grader must not need.
    ok(o.get("production_seeding_observed"),
       "the processor's own request-submission path built no APIRequest, so the "
       "seeding of attempts_left could not be observed: "
       f"{o.get('production_error')}")
    eq(o.get("production_attempts_left"), _PRODUCTION_MAX_RETRIES,
       "the request the processor's submission loop builds must be seeded from "
       "config.max_retries")


def judge_r1_exclusions(o):
    ok(o["has_waivers"], "the per-request throttle waiver budget is not implemented")
    eq(o["dead"], [False, 0, 4, 2, "terminal:abort"], "a terminal verdict must zero the budget and leave the waivers")
    eq(o["waived"], [True, 0, 0, 5, "throttle:retry"], "an empty budget must not stop a waived throttle")
    eq(o["spent"], [False, 0, 0, 6, "throttle:exhausted"], "the throttle with waivers spent is the one that stops")


def judge_r1_failure_behavior(o):
    ok(o["has_waivers"], "the per-request throttle waiver budget is not implemented")
    eq(o["affordable"], [True, 0, 6, 1, "contract:retry"], "2 - 2 == 0 is affordable, so retried")
    eq(o["unaffordable"], [False, 0, 6, 2, "contract:exhausted"], "1 - 2 < 0, so the request ends")
    eq(o["unaffordable_budget"], 0, "the post-failure budget is clamped at zero, never negative")
    eq(o["unaffordable_delay"], 0.0, "an un-retried verdict has a zero delay")
    eq(o["draws_after_unaffordable"], o["drawn"], "a verdict that will not be retried must not ask the schedule for a delay")
    eq(o["empty"], [False, 0, 0, 10, "transient:exhausted"], "an exhausted transient ends the request")
    eq(o["empty_delay"], 0.0, "an exhausted transient has a zero delay")
    eq(o["draws_after_empty"], o["drawn"], "an exhausted transient must not consume the jitter source")


def judge_r1_observability(o):
    ok(o["has_waivers"], "the per-request throttle waiver budget is not implemented")
    eq(o["default_waivers"], 6, "DEFAULT_THROTTLE_WAIVERS")
    eq(o["fresh_waivers"], 6, "a fresh request starts at six waivers")
    eq(o["healthy"], [3, 5], "a waived throttle keeps the budget and spends one waiver")
    eq(o["broke"], [True, 2], "an empty budget still retries a waived throttle and spends the waiver")
    eq(o["spent"], [False, "throttle:exhausted", 0], "no budget and no waivers ends the request")
    eq(o["length_budget"], 1, "a contract failure at three attempts costs two")
    eq(o["last"], [False, "contract:exhausted", 0], "a contract failure at one attempt ends the request")
    eq(o["bad_key"], ["terminal:abort", 0, 6], "a terminal verdict zeroes the budget and passes the waivers through")
    # [re-queued, attempts_left after]. Three v7 runs made `length` terminal at the
    # call site and still passed the `decide`-only rows above.
    eq(o.get("length_via_request_path"), [1, 1],
       "on the request path a length-truncated response must be re-queued and charged like any contract failure, two attempts")


# ---------------------------------------------------------------------------
# r2 — an absolute cooldown horizon that only 429s extend
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    names = o["tracker_field_names"]
    ok("throttle_cooldown_until" in names, f"OnlineStatusTracker has no cooldown horizon; its fields are {names}")
    ok(names.index("throttle_cooldown_until") == names.index("time_of_last_rate_limit_error") + 1,
       f"throttle_cooldown_until is not declared immediately after time_of_last_rate_limit_error: {names}")
    eq(o["fresh_horizon"], 0.0, "a fresh tracker's horizon is zero")
    # Fail-closed, not skipped: the runner stages the pristine tree for the
    # worker too, and "we could not diff" must not read as "nothing was added".
    ok(o.get("has_baseline"),
       "the pristine OnlineStatusTracker could not be read, so 'exactly one new "
       "pause field' cannot be checked")
    eq(o["added_pause_fields"], ["throttle_cooldown_until"],
       "the requirement allows exactly one pause field")
    eq(o["long_delay"], 8.0, "first throttle delay at jitter 1.0, attempt #1")
    eq(o["long_clock_calls"], 1, "a throttle must read the injected clock exactly once")
    eq(o["long_tolre"], 500.0, "time_of_last_rate_limit_error stamped from the clock")
    eq(o["long_horizon"], 508.0, "horizon advanced to now + delay")
    eq(o["short_delay"], 4.0, "second, shorter delay")
    eq(o["short_horizon"], 508.0, "a later short delay must not shorten the horizon")
    eq(o["short_tolre"], 500.0, "time_of_last_rate_limit_error unchanged at the same instant")
    eq(o["later_delay"], 16.0, "a longer delay")
    eq(o["later_horizon"], 516.0, "a longer delay does extend the horizon")
    eq(o["remaining"], [8.001, 0.001, 0.0, 0.0], "remaining_cooldown_seconds: clamped at zero, rounded to three decimals")


def judge_r2_scope(o):
    ok(o["has_horizon"], "the tracker's throttle cooldown horizon is not implemented")
    eq(o["c1"], [0, 1, 0], "transient counter")
    eq(o["c2"], [0, 1, 1], "contract counter")
    eq(o["c3"], [0, 2, 1], "terminal counter")
    eq(o["clock_after_nonthrottle"], 0, "a non-throttle verdict must not call the injected clock")
    eq(o["horizon_after_nonthrottle"], 0.0, "a non-throttle verdict must not touch the horizon")
    eq(o["tolre_after_nonthrottle"], 0.0, "a non-throttle verdict must not stamp time_of_last_rate_limit_error")
    eq(o["c4"], [1, 2, 1], "rate-limit counter")
    eq(o["clock4"], 1, "a throttle reads the clock once")
    eq(o["horizon4"], 705.0, "horizon stamped by the throttle")
    eq(o["tolre4"], 700.0, "time_of_last stamped by the throttle")
    eq(o["c5"], [1, 3, 2], "more non-throttles move only their counters")
    eq(o["clock5"], 1, "more non-throttles cost no clock call")
    eq(o["horizon5"], 705.0, "more non-throttles leave the horizon")
    eq(o["tolre5"], 700.0, "more non-throttles leave time_of_last")
    eq(o["clock6"], 2, "the clock is called once per rate-limit failure and never otherwise")


def judge_r2_exclusions(o):
    ok(o["has_horizon"], "the tracker's throttle cooldown horizon is not implemented")
    ok(o["knob_in_config"], "seconds_to_pause_on_rate_limit vanished from the config")
    eq(o["knob_default"], 10, "the knob still defaults to 10")
    eq(o["knob_set"], 42, "the knob is still settable")
    eq(o["processor_knob"], 10, "the processor still carries the knob")
    eq(o["slept_after_lapsed"], [], "the pause was derived from the knob or from time since the last 429")
    eq(o["slept_after_never"], [], "a run that has never been throttled paused")
    ok(len(o["slept_after_ahead"]) == 1, f"a live cooldown horizon did not pause: slept {o['slept_after_ahead']}")
    # Exactly, not within a second of it. This check used to compare a live
    # `time.time()` reading taken by the probe against another taken by the
    # processor, bracketed `3.0 < slept <= 4.0`: a correct implementation failed
    # whenever the host descheduled the worker for a second in between, which is
    # a grader deciding on machine load. probe.py now freezes the clock the
    # processor reads (before building it, so a captured `time.time` is frozen
    # too) and puts the horizon exactly _COOLDOWN_AHEAD_SECONDS ahead of the
    # frozen instant, so the remaining cooldown is that number with nothing to
    # round and nothing to elapse.
    eq(o["slept_after_ahead"][0], _COOLDOWN_AHEAD_SECONDS,
       "the pause is not the horizon's remaining time: the worker froze the clock "
       f"the processor reads and put the horizon {_COOLDOWN_AHEAD_SECONDS}s ahead "
       f"of it, and the frozen clock was read {o.get('frozen_clock_reads')} time(s) "
       "during the call")
    # Asked of the syntax tree, not the text: a v7 run wrote a docstring explaining
    # why the knob is dead and lost this fact for naming it. An attribute read or an
    # exact-name string (getattr) is a read; prose that mentions it is not.
    src = _base_processor_class_source()
    reads = [
        node.lineno
        for node in ast.walk(ast.parse(src))
        if (isinstance(node, ast.Attribute) and node.attr == "seconds_to_pause_on_rate_limit")
        or (isinstance(node, ast.Constant) and node.value == "seconds_to_pause_on_rate_limit")
    ]
    ok(not reads, f"the online processor still reads the dead pause knob (class-relative lines {reads})")


def judge_r2_observability(o):
    ok(o["has_horizon"], "the tracker's throttle cooldown horizon is not implemented")
    eq(o["first_delay"], 5.0, "first throttle delay")
    eq(o["first_horizon"], 1005.0, "horizon stamped to now + delay")
    eq(o["first_tolre"], 1000.0, "time_of_last stamped from the clock")
    eq(o["second_horizon"], 1005.0, "the horizon is a monotonic maximum, not the latest assignment")
    eq(o["remaining"], [3.0, 0.5, 0.0, 0.0], "remaining_cooldown_seconds table")
    eq(o["fresh_horizon"], 0.0, "a fresh tracker's horizon is zero")
    eq(o["fresh_remaining"], 0.0, "a fresh tracker has no remaining cooldown")


JUDGES = {
    "test_open::test_open_feature__failures_are_classified_priced_and_summarised_by_the_policy_module": judge_open,
    "test_r1::test_rule__a_throttle_spends_a_waiver_a_transient_one_attempt_and_a_contract_two": judge_r1_rule,
    "test_r1::test_scope__the_waiver_allowance_is_per_request_and_lives_nowhere_else": judge_r1_scope,
    "test_r1::test_exclusions__a_terminal_verdict_discards_the_budget_and_an_empty_budget_still_retries_a_waived_throttle": judge_r1_exclusions,
    "test_r1::test_failure_behavior__exhaustion_is_tested_after_the_cost_is_charged_and_the_floor_is_zero": judge_r1_failure_behavior,
    "test_r1::test_observability__the_stated_budget_and_waiver_table_holds_exactly": judge_r1_observability,
    "test_r2::test_rule__the_cooldown_horizon_is_one_new_tracker_field_that_only_ever_moves_forward": judge_r2_rule,
    "test_r2::test_scope__only_throttles_extend_the_horizon_or_consult_the_clock": judge_r2_scope,
    "test_r2::test_exclusions__the_seconds_to_pause_knob_survives_in_config_and_is_never_read_again": judge_r2_exclusions,
    "test_r2::test_observability__the_stated_horizon_and_remaining_cooldown_table_holds_exactly": judge_r2_observability,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g3_retry_backoff_policy" '
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


def main(obs_path: str, out_path: str) -> int:
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
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
