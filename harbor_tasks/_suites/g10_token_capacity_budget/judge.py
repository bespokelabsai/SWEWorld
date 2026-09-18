"""g10 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and,
for the rules no value can witness, the submission's own source under
SUBMISSION_SRC against the pristine tree at CURATOR_BASELINE_DIR. It writes a
`junit.xml` whose `classname`/`name` are the current suite's node ids — so
`score.py` folds them into the identical fact keys and `test.sh`/`score.py` are
unchanged. No agent code runs here, so the report cannot be forged; and
`test.sh` locks this file to 0600 root, so the worker cannot read the arithmetic
below.

WHY THIS FILE NO LONGER HOLDS THE ANSWERS AS LITERALS. The split moved the
verdict out of the process that runs agent code. It left the worker AUTHORING
the values the verdict is computed from, and while the fixture was fixed those
values never changed. An independent review of v11 measured the consequence: an
`observations.json` hand-written from this file's own literals passed 9/9, and
passed 9/9 again against a tree with `refund_capacity`, the failure-path refund
and all three counters deleted — reward 1.0 for implementing neither hidden
requirement. Two things close that:

  * **the inputs move every run.** `fixture_spec.derive(seed)` re-draws the
    limits, estimates, reported usages, clock steps and header values from the
    seed root picked, and this file recomputes what the answers must be for
    THOSE inputs. There is nothing to memorise and nothing in the corpus to
    copy. What stays literal is only what the ticket fixes and nobody may
    change: the four `DEFAULT_MAX_*` numbers, the origin strings, the header
    name tuples, the field order, the rejected `parse_limit_value` forms, and
    the counting semantics.
  * **the hidden requirements are witnessed in source too.** Each of the eight
    hidden facts used to read nothing but `observations.json`. Each now also
    asks root to read the submission: the debt-floor fraction's declaration, the
    three counters' declarations and where they are incremented, the tracker's
    refund operation and the processor's delegation to it, and the refund on the
    failure path of the retry handler. A forged value no longer pays unless the
    code that would produce it is really there.

The residual, stated plainly: a submission that IMPLEMENTS both requirements and
then also forges observations still passes, because it has done the work. What
is gone is passing by repeating values that were knowable in advance.

WHERE A REVIEWER FINDS THE DERIVATION. Here: every expectation below is either
the arithmetic that produces it from this run's inputs, or one of the ticket's
own published constants. The prose in `tests/task.json` states each hidden fact
in words with a worked case on the old fixed fixture, and
`solution/oracle.patch` is the reference implementation. The suite additionally
keeps a pytest reference (`test_open.py`/`test_r1.py`/`test_r2.py`) beside this
file in SWEWorld at `harbor_tasks/_suites/g10_token_capacity_budget/` as the
maintainer's fact<->assertion record; it is deliberately NOT part of the task,
because it is the human-readable copy of the same arithmetic and its home is the
repository, not the graded tree.

To re-run the grader by hand, run `run_suites.py` the way `test.sh` does: it
stages the jail (probe.py, probe_support.py, fixture_spec.py, harness.py -- no
expected value among them), runs `probe.py` as nobody against a checkout of the
submission, and then this file as root over the observations it harvested.
"""
from __future__ import annotations

import ast
import copy
import json
import math
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

# Filled in by main() from argv before any fact is judged.
SPEC: dict = {}

# The one answer that cannot be re-drawn, because it IS the requirement: a
# fraction the run chose would be a fraction the run could also be told. It
# therefore lives here, where the worker cannot read it, and is checked against
# the submission's own module text as well as against the values it produces.
CAPACITY_DEBT_FLOOR_FRACTION = 0.25


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def raised(info, *, cls=None, mro=None, axis=None, requested=None, limit=None, string=None, msg=""):
    ok(info.get("raised"), f"{msg}: expected an exception, none raised")
    # `cls` is the class the ticket NAMES; `mro` is what it must derive from.
    # Checking only the base let any ValueError carrying the right three
    # attributes pass as the ticket's own exception.
    if cls is not None:
        ok(cls in info.get("mro", []), f"{msg}: {cls} not in {info.get('mro')}")
    if mro is not None:
        ok(mro in info.get("mro", []), f"{msg}: {mro} not in {info.get('mro')}")
    if axis is not None:
        eq(info.get("axis"), axis, f"{msg}: axis")
    if requested is not None:
        eq(info.get("requested"), requested, f"{msg}: requested")
    if limit is not None:
        eq(info.get("limit"), limit, f"{msg}: limit")
    if string is not None:
        eq(info.get("str"), string, f"{msg}: message")


# ---------------------------------------------------------------------------
# The arithmetic the run's inputs imply. Each function is the rule it is named
# for, written once, so an expectation below is a formula rather than a number
# someone could have copied off an earlier run.
# ---------------------------------------------------------------------------
def _axes(input_axis, output_axis):
    """The (input, output, total) triple `_TokenUsage(input=, output=)` reports.

    `total` is a stored pydantic field set at construction, so it is the sum of
    the two axes as they were when the object was built.
    """
    total = None if input_axis is None or output_axis is None else input_axis + output_axis
    return [input_axis, output_axis, total]


def _refill_combined(available, limit, elapsed):
    """`update_capacity` under `combined`: refill at limit/minute, capped above."""
    return min(available + limit * max(0.0, elapsed) / 60.0, float(limit))


def _refill_axis(available, limit, elapsed):
    """`update_capacity` under `seperate`: the increment is floored, per axis."""
    return min(available + math.floor(limit * max(0.0, elapsed) / 60.0), limit)


def _floor_combined(limit):
    """The debt floor of the single combined axis, as a float."""
    return -limit * CAPACITY_DEBT_FLOOR_FRACTION


def _floor_axis(limit):
    """The debt floor of one `seperate` axis, kept an int by `math.ceil`."""
    return math.ceil(-limit * CAPACITY_DEBT_FLOOR_FRACTION)


def _settle_combined(available, limit, blocked_total, used_total):
    """`free_capacity` under `combined`: gain blocked-used, cap above, floor below."""
    return max(min(available + (blocked_total - used_total), float(limit)), _floor_combined(limit))


def _settle_axis(available, limit, blocked_axis, used_axis):
    """`free_capacity` on one `seperate` axis."""
    return max(min(available + (blocked_axis - used_axis), limit), _floor_axis(limit))


# ---------------------------------------------------------------------------
# Source checks: the ticket's preservation, delegation and declaration rules
#
# Behaviour cannot witness these. A provider processor needs its client and a
# network before it will answer a call, "stays exactly as it is" is a statement
# about code rather than about a value, and a refund the limit caps is invisible
# in every bucket reading. So root reads the pushed source (parsing text
# executes nothing, and the submission is not importable here) and compares it
# with the pristine tree `run_suites.stage_baseline` names in
# CURATOR_BASELINE_DIR -- which is how a rule about code INSIDE a file the
# ticket edits gets enforced at all, since `protected_files` can only speak
# about whole files. A missing baseline FAILS the fact: an unmeasured
# preservation rule is not a preserved one.
# ---------------------------------------------------------------------------
_BASE = "request_processor/online/base_online_request_processor.py"
_TRACKER = "status_tracker/online_status_tracker.py"
_BUDGET = "status_tracker/capacity_budget.py"
_ANTHROPIC = "request_processor/online/anthropic_online_request_processor.py"
_LITELLM = "request_processor/online/litellm_online_request_processor.py"
_OPENAI = "request_processor/online/openai_online_request_processor.py"
_READING_FIELDS = ["max_requests_per_minute", "max_tokens_per_minute",
                   "token_limit_strategy", "source_headers"]
# The two error counters instruction.md:76 puts out of scope.
_NOT_TOUCHED_COUNTERS = ("num_rate_limit_errors", "time_of_last_rate_limit_error")
# The tracker fields out of scope that a whole-file compare cannot cover:
# online_status_tracker.py is a file the ticket rewrites.
_TRACKER_NOT_TOUCHED = ("num_rate_limit_errors", "time_of_last_rate_limit_error", "start_time")
# The three numbers the anthropic reader used to fall back on, named by the
# ticket as the thing that goes away.
_DROPPED_FALLBACKS = (4000, 80000, 400000)

# The names the probe's tolerant readers accept for the hidden requirements'
# fields and operations. The source checks accept exactly the same sets: a
# submission that names its clamp counter `num_debt_clamps` is read the same way
# by both halves, and a stricter judge would fail a tree the probe measured as
# correct.
_CLAMP_COUNTERS = ("num_capacity_debt_clamps", "num_debt_clamps", "num_capacity_clamps")
_SETTLEMENT_COUNTERS = ("num_capacity_settlements", "num_settlements", "num_capacity_frees")
_REFUND_COUNTERS = ("num_capacity_refunds", "num_refunds")
_TRACKER_REFUNDS = ("refund_capacity", "refund")
_REFUND_CALLS = ("_refund_capacity", "refund_capacity", "refund")


def _submitted(rel: str) -> str:
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    for prefix in ("bespokelabs/curator", "src/bespokelabs/curator"):
        path = root / prefix / rel
        if path.is_file():
            return judge_io.read_text(path)
    raise Fail(f"cannot read {rel} under {root}")


def _pristine(rel: str) -> str:
    root = os.environ.get("CURATOR_BASELINE_DIR", "")
    if not root:
        raise Fail(f"CURATOR_BASELINE_DIR is unset, so nothing can witness that {rel} is "
                   "unchanged; an unmeasured preservation rule is not a pass")
    path = pathlib.Path(root) / rel
    if not path.is_file():
        raise Fail(f"no pristine copy of {rel} under {root}")
    return judge_io.read_text(path)


# Every resolver below returns the declaration python BINDS -- the LAST one --
# and refuses a name declared twice. Searching for the first match certified
# text instead of code: appending a gutted redefinition of either graded class
# left all seventeen source checks reading the abandoned declaration and scored
# reward 1.0 with the live tracker implementing neither hidden requirement, and
# a second `def refund_capacity` did the same for one method.
def _effective(nodes: list, what: str):
    """The declaration that binds, or a Fail when the name is declared twice."""
    if len(nodes) > 1:
        raise Fail(f"{what} is declared {len(nodes)} times in one namespace; python binds the "
                   "last one, so a duplicate declaration is not the implementation that runs")
    return nodes[-1] if nodes else None


def _class(src: str, name: str) -> ast.ClassDef:
    tree = ast.parse(src)
    node = _effective([n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name],
                      f"class {name}")
    if node is None:
        raise Fail(f"class {name!r} not found at module level")
    for other in ast.walk(tree):
        if isinstance(other, (ast.Assign, ast.AnnAssign)):
            targets = (other.targets if isinstance(other, ast.Assign) else [other.target])
            if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                raise Fail(f"the name {name} is reassigned at line {other.lineno}, so the class "
                           "read here is not the one the module exports")
    return node


def _method(src: str, cls: str, name: str):
    node = _effective([n for n in _class(src, cls).body
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name],
                      f"{cls}.{name}")
    if node is None:
        raise Fail(f"{cls}.{name} not found")
    return node


def _find_method(src: str, cls: str, names):
    """Whichever of these methods the class binds, or None.

    Only one of the accepted spellings may be declared, and only once: two
    `def`s of the same name mean the second is the one that runs.
    """
    members = [member for member in _class(src, cls).body
               if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
               and member.name in names]
    declared = sorted({member.name for member in members})
    if len(declared) > 1:
        raise Fail(f"{cls} declares {', '.join(declared)}; one operation, one name")
    return _effective(members, f"{cls}.{declared[0]}" if declared else "")


def _function(src: str, name: str):
    node = _effective([n for n in ast.parse(src).body
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name],
                      f"{name}()")
    if node is None:
        raise Fail(f"module-level {name} not found")
    return node


def _binding(src: str, name: str):
    """The module-level statement that binds `name`, refusing a second one."""
    found = []
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name for t in node.targets):
            found.append(node)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            found.append(node)
    node = _effective(found, f"module-level {name}")
    if node is None:
        raise Fail(f"module-level {name} not found")
    return node


def _module_bindings(src: str, name: str) -> list[str]:
    """What kind of module-level statement binds `name`, in file order.

    Kinds, not text: the point is how MANY times the module binds the name and
    how, because a submission that leaves the pristine binding alone and appends
    a second one has changed what the module exports. Measured on gutted
    redefinitions of both graded classes, which passed every other source check
    while the running code used the replacement. The same route through
    cost.py and types/generic_response.py is `protected_files` now.
    """
    out = []
    for node in ast.parse(src).body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            out.append(f"class {name}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            out.append(f"def {name}")
        elif isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name for t in node.targets):
            out.append(f"assign {name}")
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.target.id == name:
            out.append(f"assign {name}")
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if (alias.asname or alias.name.split(".")[0]) == name:
                    out.append(f"import {name}")
    return out


def _static_truth(expr):
    """True/False when a test is a literal the reader can settle, else None."""
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        inner = _static_truth(expr.operand)
        return None if inner is None else not inner
    try:
        return bool(ast.literal_eval(expr))
    except Exception:  # anything that is not a literal is not statically dead
        return None


def _dead_statements(root) -> set:
    """ids of every statement under `root` that execution cannot reach.

    An 18-line residual shim passed all eight hidden facts with every graded
    statement parked behind `while False:` or after a `return`: the increments
    and the fraction's arithmetic were all in the AST and none of them could
    ever run. Dead is only what needs nothing run to settle -- a falsy literal
    test, a loop over an empty literal, and anything after a return, a raise, a
    continue or a break.
    """
    dead = set()
    for node in ast.walk(root):
        for field in ("body", "orelse", "finalbody"):
            body = getattr(node, field, None)
            if not isinstance(body, list):
                continue
            skip = False
            if isinstance(node, (ast.If, ast.While)):
                truth = _static_truth(node.test)
                skip = (truth is False) if field == "body" else (truth is True)
            elif isinstance(node, (ast.For, ast.AsyncFor)) and field == "body":
                skip = _static_truth(node.iter) is False
            unreachable = skip
            for stmt in body:
                if unreachable:
                    dead.add(id(stmt))
                elif isinstance(stmt, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
                    unreachable = True
    return dead


def _live(root):
    """`root` and every node under it that execution can reach."""
    dead = _dead_statements(root)
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(child for child in ast.iter_child_nodes(node) if id(child) not in dead)


def _self_callees(cls: ast.ClassDef, entries) -> list:
    """The class's own methods reachable from `entries` through self.<m>() calls.

    A statement parked in a method nothing calls is not part of the operation;
    one written through a private helper is. Both directions were measured: the
    shim above passed on dead code, and a correct submission that read the
    injected clock through a one-line `_clock_now()` helper failed.
    """
    methods = {member.name: member for member in cls.body
               if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))}
    seen, queue = set(), [name for name in entries if name in methods]
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        for node in _live(methods[name]):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == "self" \
                    and node.func.attr in methods:
                queue.append(node.func.attr)
    return [methods[name] for name in sorted(seen)]


def _readable_strings(node):
    """Every string constant in this subtree that the code could actually read.

    Docstrings and bare string statements are excluded. The scans below failed
    three behaviourally-identical submissions for documenting themselves: a
    `capacity_budget.py` docstring quoting instruction.md:28's own sentence
    ("No `*-remaining`, `*-reset` or `llm_provider-*` key is ever read") and an
    anthropic reader whose docstring named the `anthropic-ratelimit-*` family it
    delegates. A string nothing evaluates reads no header.
    """
    prose = {id(child.value) for child in ast.walk(node)
             if isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant)
             and isinstance(child.value.value, str)}
    return [child for child in ast.walk(node)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
            and id(child) not in prose]


def _declarations(src: str, names) -> list[str]:
    """Every annotated declaration of these names, as sorted AST dumps.

    Sorted rather than in file order: the rule is that the declaration reads as
    the world shipped it, not that it sits on the same line.
    """
    return sorted(ast.dump(node) for node in ast.walk(ast.parse(src))
                  if isinstance(node, ast.AnnAssign)
                  and isinstance(node.target, ast.Name) and node.target.id in names)


def _targets(node):
    """Every name or attribute a statement writes to, tuple targets flattened."""
    raw = (node.targets if isinstance(node, ast.Assign)
           else [node.target] if isinstance(node, (ast.AugAssign, ast.AnnAssign)) else [])
    out = []
    while raw:
        target = raw.pop()
        if isinstance(target, (ast.Tuple, ast.List)):
            raw.extend(target.elts)  # `a.n, b = 1, 2` writes a.n just as much
        else:
            out.append(target)
    return out


def _writes(src: str, names) -> list[str]:
    """Every statement that WRITES one of these names, as sorted AST dumps.

    Comparing the DECLARATION alone was the gap the v10 reviewer named: the
    declaring line of `num_rate_limit_errors` stays untouched while a new
    `status_tracker.num_rate_limit_errors += 1` appears in a handler path, and
    the ticket calls that counter not touched.
    """
    return sorted(ast.dump(node) for node in ast.walk(ast.parse(src))
                  for target in _targets(node)
                  if getattr(target, "attr", getattr(target, "id", None)) in names)


def _same_ast(got, want, msg: str) -> None:
    # ast.dump without attributes: reformatting, comments and line numbers are
    # free, a changed expression is not.
    if ast.dump(got) != ast.dump(want):
        raise Fail(msg)


# The ONE edit instruction.md:64 asks for inside the retry handler is the
# release of the reservation on each terminal path, so a statement that is
# nothing but a call to a capacity release names the allowed edit. Everything
# else in that method is "otherwise unchanged". `_semaphore.release()` is
# deliberately NOT here: a semaphore release is not a capacity release, and
# listing it would let the finally clause be emptied.
_RELEASE_CALLS = ("_free_capacity", "_refund_capacity", "_release_capacity",
                  "free_capacity", "refund_capacity", "release_capacity", "refund")
# The retry queue, by the names it carries in the two methods that touch it.
_QUEUE_NAMES = ("retry_queue", "queue_of_requests_to_retry")


def _reaches_queue(node) -> bool:
    """True when an expression reaches the retry queue under ANY of its names.

    A bare `ast.Name` used to be the whole test, and `locals()["retry_queue"]`
    walked through it: the queue arrives as a string constant, so nothing in the
    expression is a Name at all. An attribute of the same name and a string
    naming it now count too.
    """
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in _QUEUE_NAMES:
            return True
        if isinstance(child, ast.Attribute) and child.attr in _QUEUE_NAMES:
            return True
        if isinstance(child, ast.Constant) and isinstance(child.value, str) \
                and child.value in _QUEUE_NAMES:
            return True
    return False


def _plain_operand(node) -> bool:
    """A name, an attribute chain over one, or a literal — and nothing else."""
    if isinstance(node, (ast.Constant, ast.Name)):
        return True
    if isinstance(node, ast.Attribute):
        return _plain_operand(node.value)
    return False


def _plain_release(call) -> bool:
    """Every part of a release call is a plain operand.

    A stripped statement is removed WHOLE, so nothing used to constrain what its
    arguments did. Measured on v11: appending
    `status_tracker.refund(locals()["retry_queue"].put_nowait(request) or
    self.config.__setattr__("max_retries", 99) or blocked_capacity)` to the
    except body passed the retry-queue check, the handler diff AND the
    out-of-scope check, while requeueing the request a second time and rewriting
    `config.max_retries` — both out of scope at instruction.md:76 — from inside
    the method those checks call unchanged. An argument that is itself a call, a
    subscript or a boolean operator is no longer a release the diff forgives.
    """
    return (_plain_operand(call.func)
            and all(_plain_operand(arg) for arg in call.args)
            and all(_plain_operand(kw.value) for kw in call.keywords))


class _StripReleases(ast.NodeTransformer):
    """Removes the capacity releases the ticket adds, so the rest can be diffed."""

    def visit_Expr(self, node):
        call = node.value.value if isinstance(node.value, ast.Await) else node.value
        if isinstance(call, ast.Call) and getattr(
                call.func, "attr", getattr(call.func, "id", None)) in _RELEASE_CALLS \
                and not _reaches_queue(call) and _plain_release(call):
            # A "release" handed the retry queue is not a release: it would be a
            # hole in the diff exactly the width of a requeue, so it stays in and
            # the comparison fails on it. Same for one whose arguments do work of
            # their own.
            return None
        return node

    def visit_If(self, node):
        # `if token_estimate is not None: self._refund_capacity(...)` is the same
        # edit with a guard in front of it, so an `if` left with nothing in it
        # goes too. An `if` that held anything else stays and is compared.
        self.generic_visit(node)
        return None if not node.body and not node.orelse else node


_CONTROL_BODIES = ("body", "orelse", "finalbody", "handlers")


def _parents(root) -> dict:
    """(parent, field) for every REACHABLE node under `root`.

    Only live nodes get a parent, so a statement parked behind `if False:` has
    no path back to the method and is not an operation at all.
    """
    dead = _dead_statements(root)
    out, stack = {}, [root]
    while stack:
        node = stack.pop()
        for field, value in ast.iter_fields(node):
            for child in (value if isinstance(value, list) else [value]):
                if isinstance(child, ast.AST) and id(child) not in dead:
                    out[id(child)] = (node, field)
                    stack.append(child)
    return out


def _control_chain(node, parents: dict) -> list[str]:
    """The statements that enclose `node`, outermost first, bodies emptied.

    The v12 reviewer's route: "wrap the existing queue drain/requeue operations
    in `if False:` or otherwise change their enclosing conditions while leaving
    the collected operations and their source order unchanged". Comparing the
    operation list alone forgave both. Each enclosing statement is dumped with
    its `body`/`orelse`/`finalbody`/`handlers` blanked, so what is compared is
    the condition, the iterable, the `with` items and WHICH of those blocks the
    operation sits in -- never the sibling statements, which is where the
    ticket's own edit (the reservation loop that replaces `has_capacity`) lives.
    """
    chain = []
    while id(node) in parents:
        parent, field = parents[id(node)]
        if isinstance(getattr(parent, "body", None), list):
            clone = copy.copy(parent)
            for blank in _CONTROL_BODIES:
                if isinstance(getattr(clone, blank, None), list):
                    setattr(clone, blank, [])
            chain.append(f"{field}@{ast.dump(clone)}")
        node = parent
    chain.reverse()
    return chain


def _queue_ops(src: str, cls: str, name: str) -> list[str]:
    """Every operation on the retry queue inside one method, in source order.

    Its construction, the calls on it (`empty`, `get`, `put_nowait`), every call
    it is handed to, and -- since v13 -- the chain of conditions each one is
    reached through. The SIBLING statements are still not compared, because the
    ticket rewrites the reservation loop that stands beside two of them. The
    receiver, the keyword value and the assignment target are matched as
    EXPRESSIONS rather than as bare names: `alias = queue_of_requests_to_retry`
    followed by `alias.get()`, and `locals()["retry_queue"].put_nowait(request)`,
    were both invisible while only an `ast.Name` counted.
    """
    fn = _method(src, cls, name)
    parents = _parents(fn)
    found = []
    for node in _live(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and _reaches_queue(node.func.value):
            found.append(node)
        elif isinstance(node, ast.keyword) and _reaches_queue(node.value):
            found.append(node)
        elif any(_reaches_queue(target) for target in _targets(node)):
            found.append(node)
        elif isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)) \
                and node.value is not None and _reaches_queue(node.value):
            # The statement that hands the queue to a second name. `alias =
            # queue_of_requests_to_retry` followed by `alias.get()` put the
            # whole drain out of reach of every other branch, because the calls
            # are then made on a name the ticket never mentions. The aliasing
            # statement has no counterpart in the pristine tree, so collecting
            # it is what makes the lists differ.
            found.append(node)
    found.sort(key=lambda node: (getattr(node, "lineno", 0), getattr(node, "col_offset", 0)))
    return [[ast.dump(node), _control_chain(node, parents)] for node in found]


def _calls(node, name: str) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if getattr(func, "attr", getattr(func, "id", None)) == name:
                return True
    return False


def _calls_any(node, names) -> bool:
    return any(_calls(node, name) for name in names)


def _mentions(node, name: str) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Attribute) and child.attr == name:
            return True
        if isinstance(child, ast.Name) and child.id == name:
            return True
    return False


def _import_roots(tree) -> set[str]:
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _check_out_of_scope_unchanged():
    """The out-of-scope names that live in files the ticket also REWRITES.

    The four out-of-scope FILES -- cost.py, types/token_usage.py,
    types/generic_response.py, request_processor/config.py (instruction.md:71,
    :76; `oracle.patch` touches none of them) -- are listed in
    `tests/task.json`'s `protected_files`, so root byte-compares each with the
    pristine tree before any agent code is imported and `score.py` zeroes the
    reward on a difference. That subsumes the AST compares that used to stand
    here, and catches what they could not: `RATE_LIMIT_HEADER.clear()`,
    `.update({...})` and `RATE_LIMIT_HEADER["openai"] = {...}` are none of them
    an `ast.Assign` to the name and none of them a new module-level binding, so
    a declaration compare read a pristine table while the running dict held
    whatever the submission put in it.

    What is left is the part a whole-file compare cannot express: names out of
    scope inside the two files the ticket does edit.
    """
    _same_ast(_method(_submitted(_BASE), "BaseOnlineRequestProcessor", "cool_down_if_rate_limit_error"),
              _method(_pristine(_BASE), "BaseOnlineRequestProcessor", "cool_down_if_rate_limit_error"),
              "cool_down_if_rate_limit_error is out of scope and must be left as it was")
    # ... and each graded class is bound exactly where and as often as the world
    # binds it. Comparing the FIRST declaration passed a submission that kept
    # the pristine one and appended a replacement python actually binds --
    # measured on gutted redefinitions of both graded classes.
    for rel, name in ((_TRACKER, "OnlineStatusTracker"),
                      (_BASE, "BaseOnlineRequestProcessor")):
        eq(_module_bindings(_submitted(rel), name), _module_bindings(_pristine(rel), name),
           f"{rel} binds {name} somewhere the world did not; the later binding is the one python "
           "keeps, so a second declaration replaces the first rather than sitting beside it")
    eq(_declarations(_submitted(_TRACKER), _TRACKER_NOT_TOUCHED),
       _declarations(_pristine(_TRACKER), _TRACKER_NOT_TOUCHED),
       "num_rate_limit_errors / time_of_last_rate_limit_error / start_time is out of scope and "
       "must be declared as the world shipped it")
    # ... and nothing writes the two error counters that the world did not
    # already write. A declaration compare passes a submission that leaves the
    # declaring line alone and counts a rate-limit error somewhere new, which is
    # the counter being touched.
    for rel in (_TRACKER, _BASE, _ANTHROPIC, _LITELLM, _OPENAI):
        eq(_writes(_submitted(rel), _NOT_TOUCHED_COUNTERS),
           _writes(_pristine(rel), _NOT_TOUCHED_COUNTERS),
           f"{rel} writes num_rate_limit_errors / time_of_last_rate_limit_error somewhere the "
           "world did not; the ticket puts both out of scope")


def _check_retry_queue_untouched():
    """"The retry queue and its ordering are not touched" (instruction.md:76).

    Enforced where the queue is used rather than where it is declared: the
    handler's `retry_queue.put_nowait(request)` and the loop's `.empty()` /
    `.get()`, each compared with the pristine tree. Without this a submission
    could drop the requeue, or requeue before decrementing `attempts_left`, and
    still pass -- every behavioural fact here drives ONE attempt, so nothing
    observes the order a second attempt comes back in.
    """
    for cls, name in (("BaseOnlineRequestProcessor", "process_requests_from_file"),
                      ("BaseOnlineRequestProcessor", "handle_single_request_with_retries")):
        eq(_queue_ops(_submitted(_BASE), cls, name), _queue_ops(_pristine(_BASE), cls, name),
           f"{name} changes how the retry queue is filled, drained or handed on; the retry queue "
           "and its ordering are out of scope")


def _check_provider_delegation():
    """All three readers delegate; none of them still names a header itself.

    Every behavioural check in this suite drives a stub subclass of the BASE
    processor, so a submission that wrote `read_rate_limit_headers` and left the
    anthropic reader's swapped mapping and 4000/80000/400000 fallbacks exactly
    where they were passed every fact -- with the bug the module exists to
    remove still in the shipped provider.
    """
    for rel, cls in ((_ANTHROPIC, "AnthropicOnlineRequestProcessor"),
                     (_LITELLM, "LiteLLMOnlineRequestProcessor")):
        fn = _method(_submitted(rel), cls, "get_header_based_rate_limits")
        ok(_calls(fn, "read_rate_limit_headers"),
           f"{cls}.get_header_based_rate_limits does not delegate to read_rate_limit_headers")
        for node in _readable_strings(fn):
            if "ratelimit" in node.value.lower():
                raise Fail(f"{cls}.get_header_based_rate_limits still names the header "
                           f"{node.value!r} itself; decoding headers is read_rate_limit_headers' job")
        for node in ast.walk(fn):
            if isinstance(node, ast.Constant) and not isinstance(node.value, bool) \
                    and node.value in _DROPPED_FALLBACKS:
                raise Fail(f"{cls}.get_header_based_rate_limits still carries the hardcoded "
                           f"fallback {node.value}; substituting defaults is the tracker's job")
            targets = (node.targets if isinstance(node, ast.Assign)
                       else [node.target] if isinstance(node, (ast.AugAssign, ast.AnnAssign)) else [])
            for target in targets:
                if isinstance(target, ast.Attribute) and target.attr == "token_limit_strategy":
                    raise Fail(f"{cls}.get_header_based_rate_limits still mutates "
                               "self.token_limit_strategy in place; the strategy comes from the reading")


def _check_openai_keeps_its_table():
    """openai delegates the header half only: the provider table branch stays."""
    fn = _method(_submitted(_OPENAI), "OpenAIOnlineRequestProcessor", "get_header_based_rate_limits")
    pristine = _method(_pristine(_OPENAI), "OpenAIOnlineRequestProcessor", "get_header_based_rate_limits")
    got = [ast.dump(n) for n in ast.walk(fn) if isinstance(n, ast.For)]
    want = [ast.dump(n) for n in ast.walk(pristine) if isinstance(n, ast.For)]
    eq(got, want, "openai's RATE_LIMIT_HEADER loop and its rps/tps scaling must stay exactly as they are")
    ok(_calls(fn, "read_rate_limit_headers"),
       "openai's get_header_based_rate_limits must delegate the header half to read_rate_limit_headers")


def _check_budget_module():
    """Stdlib only, 3.10 syntax, and a reading that reads nothing but *-limit."""
    src = _submitted(_BUDGET)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            raise Fail("capacity_budget.py must be Python 3.10 syntax without "
                       "`from __future__ import annotations`")
    for root in sorted(_import_roots(tree)):
        ok(root in sys.stdlib_module_names or root == "bespokelabs",
           f"capacity_budget.py imports {root!r}: the module is stdlib only, no new dependency")
    for node in _readable_strings(tree):
        low = node.value.lower()
        for banned in ("-remaining", "-reset", "llm_provider-"):
            if banned in low:
                raise Fail(f"capacity_budget.py reads {node.value!r}; only the four *-limit "
                           "header tuples are ever consulted")
    for node in ast.walk(_function(src, "read_rate_limit_headers")):
        if isinstance(node, ast.Name) and node.id.startswith("DEFAULT_MAX"):
            raise Fail(f"read_rate_limit_headers substitutes {node.id}; there are no numeric "
                       "fallbacks in the reading, defaulting is the tracker's job")


def _check_reading_declaration():
    """`@dataclass(frozen=True)` and the field order the ticket fixes."""
    cls = _class(_submitted(_BUDGET), "RateLimitReading")
    frozen = False
    for decorator in cls.decorator_list:
        if isinstance(decorator, ast.Call) and getattr(
                decorator.func, "attr", getattr(decorator.func, "id", None)) == "dataclass":
            frozen = frozen or any(
                kw.arg == "frozen" and isinstance(kw.value, ast.Constant) and kw.value.value is True
                for kw in decorator.keywords)
    ok(frozen, "RateLimitReading must be declared @dataclass(frozen=True)")
    eq([node.target.id for node in cls.body if isinstance(node, ast.AnnAssign)],
       _READING_FIELDS, "RateLimitReading field order")


def _check_reservation_loops():
    """Both loops reserve through _reserve_capacity, and the sleep is the only await."""
    fn = _method(_submitted(_BASE), "BaseOnlineRequestProcessor", "process_requests_from_file")
    # _live, not ast.walk: a reservation loop behind `if False:` is not a loop
    # the request path ever enters, and the v12 reviewer named exactly that --
    # "does not require those loops to be reachable".
    loops = [node for node in _live(fn)
             if isinstance(node, ast.While)
             and any(isinstance(child, ast.NamedExpr) for child in ast.walk(node.test))
             and _calls(node.test, "_reserve_capacity")]
    eq(len(loops), 2, "both reservation loops must read "
                      "`while (token_estimate := self._reserve_capacity(...)) is None` and must be "
                      "reachable: a loop execution cannot enter reserves nothing")
    for loop in loops:
        awaits = [node for node in _live(loop) if isinstance(node, ast.Await)]
        eq(len(awaits), 1, "the sleep must be the only await inside a reservation loop")
        ok(_calls(awaits[0], "sleep"), "the only await inside a reservation loop must be asyncio.sleep")
    ok(not _calls(fn, "has_capacity"),
       "process_requests_from_file must reserve through _reserve_capacity rather than "
       "asking has_capacity itself")


def _check_retry_handler_shape():
    """The handler is pristine apart from the releases the ticket adds.

    The structure-and-names version of this check was the v10 reviewer's other
    finding: a rewritten handler passed as long as a four-clause `try` existed
    somewhere and the four names appeared anywhere in it. So the handler is now
    diffed against pristine with the capacity releases stripped from both sides
    -- the edit instruction.md:64 requires -- which is the only way "otherwise
    unchanged" can mean what it says. The structure and name checks stay: they
    fail with a message that says which promise was broken, where the diff can
    only say the method changed.
    """
    fn = _method(_submitted(_BASE), "BaseOnlineRequestProcessor", "handle_single_request_with_retries")
    ok(any(isinstance(node, ast.Try) and node.handlers and node.orelse and node.finalbody
           for node in ast.walk(fn)),
       "the retry handler's try/except/else/finally structure must be unchanged")
    for name in ("invalid_finish_reasons", "update_stats", "update_cost_projection",
                 "append_generic_response"):
        ok(_mentions(fn, name),
           f"the retry handler no longer uses {name}, which the ticket leaves unchanged")
    _same_ast(_StripReleases().visit(fn),
              _StripReleases().visit(_method(_pristine(_BASE), "BaseOnlineRequestProcessor",
                                             "handle_single_request_with_retries")),
              "handle_single_request_with_retries is otherwise unchanged: apart from releasing the "
              "reservation on each terminal path, its except body, its exhausted branch, its else "
              "and its finally must read as the world shipped them")


def _check_limit_properties_unchanged():
    """The three limit properties keep their manual -> header -> default precedence.

    instruction.md:72 says "keep", and a precedence is an if-ladder: the probe
    can only watch three fixed scenarios come out right, which a submission
    tailored to those three numbers also manages. The ladder itself is pristine
    in the reference patch, so compare it.
    """
    for name in ("max_requests_per_minute", "max_tokens_per_minute", "max_concurrent_requests"):
        _same_ast(_method(_submitted(_BASE), "BaseOnlineRequestProcessor", name),
                  _method(_pristine(_BASE), "BaseOnlineRequestProcessor", name),
                  f"BaseOnlineRequestProcessor.{name} must keep the manual -> header -> default "
                  "precedence exactly as the world shipped it")


def _check_tracker_declares_the_limit_once():
    """`max_tokens_per_minute` is declared exactly once (instruction.md:35).

    The world ships the field twice, both defaulting to 0, so keeping the
    duplicate is invisible in every observation -- the second declaration simply
    wins and carries the same value.
    """
    declarations = [node for node in _class(_submitted(_TRACKER), "OnlineStatusTracker").body
                    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                    and node.target.id == "max_tokens_per_minute"]
    eq(len(declarations), 1,
       "OnlineStatusTracker.max_tokens_per_minute must be declared exactly once; the duplicate "
       "the world shipped goes away")


def _check_capacity_clock_scope():
    """Only update_capacity (and the re-seed) read the injected clock."""
    cls = _class(_submitted(_TRACKER), "OnlineStatusTracker")
    injected, wall = set(), set()
    for member in cls.body:
        if not isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(member):
            if isinstance(node, ast.Attribute) and node.attr == "capacity_clock":
                injected.add(member.name)
            if isinstance(node, ast.Attribute) and node.attr == "time" \
                    and isinstance(node.value, ast.Name) and node.value.id == "time":
                wall.add(member.name)
    # "Through the clock" is about which operation reads it, not about how many
    # lines that takes: a correct submission whose update_capacity went via a
    # one-line `_clock_now()` helper scored 0 on the exact set equality this
    # used to be. So the rule is that the refill and the re-seed reach the
    # clock, and that nothing OUTSIDE them does.
    refill = {member.name for member in _self_callees(cls, ("update_capacity",))}
    reseed = {member.name for member in _self_callees(cls, ("__post_init__",))}
    ok(bool(injected & refill),
       "every wall-clock read in update_capacity must go through self.capacity_clock(): neither "
       "update_capacity nor anything it calls reads the injected clock")
    ok("update_capacity" not in wall, "update_capacity still calls time.time() directly")
    ok(bool(injected & reseed),
       "__post_init__ must re-seed last_update_time from self.capacity_clock()")
    stray = sorted(injected - refill - reseed)
    ok(not stray,
       f"{', '.join(stray)} read the injected clock; only the update_capacity refill and the "
       "__post_init__ re-seed do, and the display code, start_time and _last_stats_update keep "
       "calling time.time() directly")
    assigns = [node for node in ast.walk(cls)
               if isinstance(node, ast.Assign)
               and any(isinstance(t, ast.Attribute) and t.attr == "_last_stats_update"
                       for t in node.targets)]
    ok(any(_calls(node.value, "time") for node in assigns),
       "_last_stats_update must keep calling time.time() directly")


def _check_dead_free_capacity_gone():
    """instruction.md:65: the dead `free_capacity(self, tracker, tokens)` is deleted.

    Witnessed by a worker boolean alone until now -- `hasattr(..., "free_capacity")
    is False`, whose passing value is True and which an `atexit` hook can report
    from a tree that still carries the method. Root reads the class body
    instead; the observation stays as a second witness, because a submission has
    to satisfy both.
    """
    for node in _class(_submitted(_BASE), "BaseOnlineRequestProcessor").body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "free_capacity":
            raise Fail("the dead BaseOnlineRequestProcessor.free_capacity helper (empty body, no "
                       "caller) must be deleted")


# ---------------------------------------------------------------------------
# Source checks for the HIDDEN requirements.
#
# The eight hidden facts used to read nothing but `observations.json`, which the
# process that runs agent code writes. That made them the forgeable half of the
# grade: a hand-written observations file passed all eight against a tree with
# the floor, the refund and the counters deleted. Each check below asks root for
# something the worker cannot reach -- a declaration, a method, a call site --
# so a value that claims the requirement is implemented is only accepted when
# the code that would produce it is really in the push.
#
# They are declaration-level on purpose. "Where the increment sits" is graded
# only where the requirement itself is about which operation counts; how the
# arithmetic is written stays the submission's business.
# ---------------------------------------------------------------------------
def _counter_declaration(src: str, cls: str, names):
    """The tracker's declaration of one of these counter names, or None.

    Accepts a bare `= 0` and a `field(default=0)`: the dataclass shipped here
    uses both forms for other fields, and the requirement is a counter starting
    at zero, not a spelling.
    """
    for node in _class(src, cls).body:
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
            continue
        if node.target.id not in names:
            continue
        value = node.value
        if isinstance(value, ast.Constant) and value.value == 0 and not isinstance(value.value, bool):
            return node
        if isinstance(value, ast.Call) and getattr(
                value.func, "attr", getattr(value.func, "id", None)) == "field":
            if any(kw.arg == "default" and isinstance(kw.value, ast.Constant) and kw.value.value == 0
                   for kw in value.keywords):
                return node
    return None


def _counter_writes(node, names) -> int:
    """How many REACHABLE statements inside this subtree write one of these counters."""
    return sum(1 for child in _live(node) for target in _targets(child)
               if getattr(target, "attr", getattr(target, "id", None)) in names)


# The operations a clamp can follow: the ticket's floor applies wherever a token
# axis moves, and the reference patch clamps from consume, settle and refund
# through one private helper.
_CLAMPING_OPERATIONS = ("consume_capacity", "free_capacity", "update_capacity",
                        "refund_capacity", "refund")


def _counter_writes_within(src: str, cls: str, entries, names) -> int:
    """Reachable writes of these counters inside `entries` or anything they call.

    Counted per operation rather than anywhere in the class: increments parked
    in an uncalled method, or after a `return`, scored reward 1.0 on a tree
    implementing nothing. A counter bumped through a private helper still
    counts -- the closure follows self.<m>() calls -- because how the arithmetic
    is written stays the submission's business.
    """
    klass = _class(src, cls)
    return sum(_counter_writes(member, names) for member in _self_callees(klass, entries))


def _check_debt_floor_constant():
    """`CAPACITY_DEBT_FLOOR_FRACTION: float = 0.25`, declared AND applied.

    The fraction is the hidden requirement, so it is the one number the fixture
    cannot re-draw -- which is exactly why a tree that reported floored values
    without ever declaring it used to pass. Read from the submission, compared
    with the fraction this judge holds.

    Declared is not enough. A seed stops a captured run being replayed; it does
    not stop a forgery DERIVING this run's answers from `fixture_spec`, which
    has to be in the worker's jail for the probe to build its scenarios at all
    (measured on g4, whose seeded facts fell to exactly that). So the fraction
    must also be USED somewhere in the two modules the budget lives in: a
    forgery then has to write the arithmetic that applies it, which is the rule
    rather than a claim about the rule.
    """
    budget_src = _submitted(_BUDGET)
    for name in ("CAPACITY_DEBT_FLOOR_FRACTION", "DEBT_FLOOR_FRACTION"):
        try:
            node = _binding(budget_src, name)
        except Fail:
            continue
        value = node.value
        ok(isinstance(value, ast.Constant) and not isinstance(value.value, bool)
           and value.value == CAPACITY_DEBT_FLOOR_FRACTION,
           f"{name} must be declared as the fraction of the per-minute limit an axis may go into "
           f"debt by; the module declares {ast.dump(value)}")
        # The name OR the fraction itself: an implementation that exports the
        # constant and then writes the arithmetic with the literal has still
        # written the arithmetic, and neither module carries a 0.25 in the tree
        # the world shipped, so this cannot pass vacuously.
        def computes_with_the_fraction(expr) -> bool:
            if _mentions(expr, name):
                return True
            return any(isinstance(child, ast.Constant) and not isinstance(child.value, bool)
                       and child.value == CAPACITY_DEBT_FLOOR_FRACTION
                       for child in ast.walk(expr))

        # Reachable applications only. `while False: return -1 * FRACTION` and
        # arithmetic parked after a `return` satisfied this count while no code
        # in the tree could ever put a floor under anything: reward 1.0 on an
        # 18-line shim.
        applied = 0
        for rel in (_BUDGET, _TRACKER):
            for child in _live(ast.parse(_submitted(rel))):
                # Its own binding and the import that re-exports it are not uses.
                if isinstance(child, (ast.Assign, ast.AnnAssign, ast.Import, ast.ImportFrom)):
                    continue
                if isinstance(child, (ast.BinOp, ast.UnaryOp, ast.Compare, ast.Call)) \
                        and computes_with_the_fraction(child):
                    applied += 1
        ok(applied >= 1,
           f"{name} is declared but never applied: nothing in the capacity budget or the tracker "
           "computes with it, so no code in this tree puts a floor under a negative axis")
        return
    raise Fail("the capacity-budget module declares no debt floor fraction; capacity that may go "
               "negative needs a bound, and the bound is a module constant")


def _check_clamp_counter():
    """A clamp counter is declared on the tracker, starting at zero, and incremented.

    The count itself is observed behaviourally (one increment per clamping
    call); this is the part an observation cannot witness -- that the field
    exists in the pushed tree at all.
    """
    src = _submitted(_TRACKER)
    node = _counter_declaration(src, "OnlineStatusTracker", _CLAMP_COUNTERS)
    ok(node is not None,
       "OnlineStatusTracker declares no debt-clamp counter starting at 0; a clamp nobody counts "
       f"cannot be observed (looked for {', '.join(_CLAMP_COUNTERS)})")
    ok(_counter_writes_within(src, "OnlineStatusTracker", _CLAMPING_OPERATIONS,
                              _CLAMP_COUNTERS) >= 1,
       "the debt-clamp counter is declared but no capacity operation ever increments it: an "
       "increment that no reachable path through consume, refill, settlement or refund executes "
       "counts nothing")


def _check_settlement_and_refund_counters():
    """Two counters, each incremented by its own operation and by neither the other's.

    The values are observed behaviourally; what source adds is that the two are
    really separate fields and that the settlement path does not bump the refund
    counter (or the other way round) somewhere the four probed calls do not
    reach.
    """
    src = _submitted(_TRACKER)
    for names, what in ((_SETTLEMENT_COUNTERS, "settlement"), (_REFUND_COUNTERS, "refund")):
        ok(_counter_declaration(src, "OnlineStatusTracker", names) is not None,
           f"OnlineStatusTracker declares no {what} counter starting at 0 "
           f"(looked for {', '.join(names)})")
    settle = _find_method(src, "OnlineStatusTracker", ("free_capacity",))
    refund = _find_method(src, "OnlineStatusTracker", _TRACKER_REFUNDS)
    ok(settle is not None, "OnlineStatusTracker.free_capacity not found")
    ok(refund is not None,
       f"OnlineStatusTracker declares no refund operation ({', '.join(_TRACKER_REFUNDS)})")
    # Each counter is written somewhere, and NEITHER operation writes the
    # other's. "Exactly one increment per call" is the behavioural half and is
    # graded there; requiring the increment statement to sit in the method
    # itself would fail a tree that counts through a helper, which the probe
    # measures as correct.
    for names, what, entries in ((_SETTLEMENT_COUNTERS, "settlement", ("free_capacity",)),
                                 (_REFUND_COUNTERS, "refund", (refund.name,))):
        ok(_counter_writes_within(src, "OnlineStatusTracker", entries, names) >= 1,
           f"the {what} counter is declared but {entries[0]} never increments it, directly or "
           "through anything it calls; an increment no reachable path executes counts nothing")
    eq(_counter_writes(settle, _REFUND_COUNTERS), 0,
       "free_capacity must not touch the refund counter; the two are counted apart")
    eq(_counter_writes(refund, _SETTLEMENT_COUNTERS), 0,
       f"{refund.name} must not touch the settlement counter; the two are counted apart")


def _check_refund_operation():
    """The tracker has a refund operation and the processor delegates to it.

    `_refund_capacity(self, status_tracker, blocked_capacity)` is the seam the
    handler calls, and it exists in no pristine tree; a forged observation
    claiming a refund happened is not evidence that either half is there.
    """
    tracker = _find_method(_submitted(_TRACKER), "OnlineStatusTracker", _TRACKER_REFUNDS)
    ok(tracker is not None,
       "OnlineStatusTracker declares no refund operation distinct from free_capacity "
       f"({', '.join(_TRACKER_REFUNDS)}); a failed attempt has nothing to give its reservation back to")
    positional = [arg.arg for arg in tracker.args.args if arg.arg != "self"]
    eq(len(positional), 1,
       f"{tracker.name} takes the capacity that was blocked and nothing else, so that a failed "
       f"attempt cannot be charged for what it reported; it declares {positional}")
    processor = _find_method(_submitted(_BASE), "BaseOnlineRequestProcessor", ("_refund_capacity",))
    ok(processor is not None,
       "BaseOnlineRequestProcessor declares no _refund_capacity; the handler needs one seam to "
       "give a failed attempt's reservation back through")
    ok(_calls_any(processor, _TRACKER_REFUNDS),
       "_refund_capacity must delegate to the tracker's refund operation rather than settle or "
       "adjust the buckets itself")


def _refunds_on_every_path(body) -> bool:
    """True when every way out of these statements passes a refund."""
    for stmt in body:
        if isinstance(stmt, ast.If):
            # A guard in front of the refund -- `if token_estimate is not None:
            # self._refund_capacity(...)` -- is the same edit with a condition,
            # and is the shape `_StripReleases` already forgives. Except when
            # the condition is the one that tells the two failure exits apart:
            # `if request.attempts_left > 0: refund` means the exhausted path
            # keeps the reservation, which is the defect, not the edit.
            if not stmt.orelse and not _mentions(stmt.test, "attempts_left") \
                    and _refunds_on_every_path(stmt.body):
                return True
            if stmt.orelse and _refunds_on_every_path(stmt.body) \
                    and _refunds_on_every_path(stmt.orelse):
                return True
            continue
        if _calls_any(stmt, _REFUND_CALLS):
            return True
    return False


def _check_failure_path_refunds():
    """Every terminal path through the handler's `except` refunds the reservation.

    The two failure exits are observed behaviourally, but only because the
    worker reports the buckets: with the observation forged, nothing said the
    call site existed. Root reads the handler and asks whether a refund is
    reached on every way out of the except body -- unconditionally, or in both
    branches of a conditional that is not the `attempts_left` test.
    """
    fn = _method(_submitted(_BASE), "BaseOnlineRequestProcessor",
                 "handle_single_request_with_retries")
    handlers = [handler for node in ast.walk(fn) if isinstance(node, ast.Try)
                for handler in node.handlers]
    ok(handlers, "the retry handler has no except clause to refund from")
    ok(any(_refunds_on_every_path(handler.body) for handler in handlers),
       "the except body of handle_single_request_with_retries must refund the reservation on "
       "every terminal path -- the requeued one and the exhausted one alike; a refund reached "
       "only when attempts remain leaves an exhausted request's capacity blocked until the "
       "window refills")


# ---------------------------------------------------------------------------
# open feature
# ---------------------------------------------------------------------------
def judge_open(o):
    _check_out_of_scope_unchanged()
    _check_retry_queue_untouched()
    _check_provider_delegation()
    _check_openai_keeps_its_table()
    _check_limit_properties_unchanged()
    _check_budget_module()
    _check_reading_declaration()
    _check_tracker_declares_the_limit_once()
    _check_reservation_loops()
    _check_retry_handler_shape()
    _check_capacity_clock_scope()
    _check_dead_free_capacity_gone()

    # The ticket's own constants (instruction.md:11,15): published, unchangeable,
    # and therefore not something a seed could hide.
    c = o["consts"]
    eq(c["req_per_min"], 200, "DEFAULT_MAX_REQUESTS_PER_MINUTE")
    eq(c["tpm_combined"], 100_000, "DEFAULT_MAX_TOKENS_PER_MINUTE_COMBINED")
    eq(c["in_per_min"], 100_000, "DEFAULT_MAX_INPUT_TOKENS_PER_MINUTE")
    eq(c["out_per_min"], 40_000, "DEFAULT_MAX_OUTPUT_TOKENS_PER_MINUTE")
    eq(c["origin_configured"], "configured", "LIMIT_ORIGIN_CONFIGURED")
    eq(c["origin_defaulted"], "defaulted", "LIMIT_ORIGIN_DEFAULTED")
    eq(c["origin_unlimited"], "unlimited", "LIMIT_ORIGIN_UNLIMITED")
    eq(o["request_headers"], ["x-ratelimit-limit-requests", "anthropic-ratelimit-requests-limit"], "REQUEST_LIMIT_HEADERS")
    eq(o["input_headers"], ["x-ratelimit-limit-input-tokens", "anthropic-ratelimit-input-tokens-limit"], "INPUT_TOKEN_LIMIT_HEADERS")
    eq(o["output_headers"], ["x-ratelimit-limit-output-tokens", "anthropic-ratelimit-output-tokens-limit"], "OUTPUT_TOKEN_LIMIT_HEADERS")
    eq(o["total_headers"], ["x-ratelimit-limit-tokens", "anthropic-ratelimit-tokens-limit"], "TOTAL_TOKEN_LIMIT_HEADERS")

    ok(o["ost_strategy_is"], "online_status_tracker re-exports TokenLimitStrategy")
    # `seperate` is upstream curator's own spelling of this enum member, on the
    # repository's main and referenced by all three provider processors. The
    # ticket moves the enum and re-exports it, so the member name has to survive
    # the move: correcting it here would rename a public API the ticket never
    # asked to rename and break every `strategy.seperate` in the library. Same
    # for the leading underscore of `_TokenUsage`.
    eq(o["strategy_values"], ["combined", "seperate"], "strategy members")
    ok(o["default_is_combined"], "strategy.default is combined")

    # The formats are the ticket's; the numbers are this run's.
    eq(o["parse_present"], [SPEC["parse_plain_str"],
                            SPEC["parse_k_units"] * 1_000 + 500,
                            SPEC["parse_m_units"] * 1_000_000,
                            SPEC["parse_trunc_int"],
                            SPEC["parse_spaced"],
                            SPEC["parse_int"]], "parse_limit_value present")
    eq(o["parse_absent"], [None] * 11, "parse_limit_value absent")

    eq(o["read_anthropic"], [SPEC["h_anthropic_req"],
                             _axes(SPEC["h_anthropic_in"], SPEC["h_anthropic_out"]), "seperate",
                             ["anthropic-ratelimit-requests-limit", "anthropic-ratelimit-input-tokens-limit",
                              "anthropic-ratelimit-output-tokens-limit"]], "anthropic headers")
    eq(o["read_remaining"], [None, [None, None, None], "combined", []], "remaining headers ignored")
    eq(o["read_empty"], [None, [None, None, None], "combined", []], "empty headers")
    eq(o["read_total_ci"], [None, [None, None, SPEC["h_total_ci"]], "combined",
                            ["x-ratelimit-limit-tokens"]], "case-insensitive total")
    eq(o["read_pair"], [SPEC["h_pair_req"], _axes(SPEC["h_pair_in"], SPEC["h_pair_out"]), "seperate",
                        ["x-ratelimit-limit-requests", "x-ratelimit-limit-input-tokens",
                         "x-ratelimit-limit-output-tokens"]], "complete pair beats total")
    eq(o["read_half_pair"], [None, [None, None, SPEC["h_half_total"]], "combined",
                             ["x-ratelimit-limit-tokens"]], "half pair discarded")
    eq(o["read_zero"][0], None, "zero header rpm")
    eq(o["read_zero"][1], [None, None, SPEC["h_zero_k_units"] * 1_000 + 500], "zero header tpm")
    eq(o["read_zero"][3], ["x-ratelimit-limit-tokens"], "zero header sources")

    eq(o["reading_shape"], [True, _READING_FIELDS], "RateLimitReading is a dataclass with these fields in order")
    raised(o["reading_frozen"], mro="FrozenInstanceError", msg="RateLimitReading is frozen")
    eq(o["read_fallthrough"], [SPEC["h_fallthrough_req"], [None, None, SPEC["h_fallthrough_total"]],
                               "combined",
                               ["anthropic-ratelimit-requests-limit", "x-ratelimit-limit-tokens"]],
       "a malformed first name is skipped for the next in the tuple")
    # The mapping itself, not the worker's verdict on it.
    eq(o["headers_after"], {"X-RateLimit-Limit-Requests": SPEC["h_fallthrough_bad"],
                            "anthropic-ratelimit-requests-limit": str(SPEC["h_fallthrough_req"]),
                            "x-ratelimit-limit-tokens": str(SPEC["h_fallthrough_total"])},
       "read_rate_limit_headers mutated the mapping it was handed")
    ok(o["headers_untouched"], "read_rate_limit_headers mutated the mapping it was handed")
    eq(o["read_priority"], [SPEC["h_priority_x"], [None, None, None], "combined",
                            ["x-ratelimit-limit-requests"]],
       "tuple order decides which present name wins")

    seed_tpm, seed_rpm = SPEC["seed_tpm"], SPEC["seed_rpm"]
    s = o["seed"]
    eq(s[0], SPEC["seed_t0"], "seeded last_update_time")
    ok(s[1], "injected clock, not wall clock")
    eq(s[2], float(seed_rpm), "seeded request capacity")
    eq(s[3], float(seed_tpm), "seeded token capacity")
    eq(s[4], "configured", "seeded token origin")
    eq(s[5], "configured", "seeded request origin")
    after_consume = float(seed_tpm) - (SPEC["seed_est_in"] + SPEC["seed_est_out"])
    after_refill = _refill_combined(after_consume, seed_tpm, SPEC["seed_dt"])
    eq(o["seed_dynamics"],
       [after_consume,
        [after_refill, SPEC["seed_t0"] + SPEC["seed_dt"]],
        # A clock that went backwards refills nothing and still records the time.
        [after_refill, SPEC["seed_t0"] + SPEC["seed_back_dt"]]],
       "seed consume/refill/backwards")

    sep_in, sep_out = SPEC["sep_in_limit"], SPEC["sep_out_limit"]
    sep_left_in = sep_in - SPEC["sep_est_in"]
    sep_left_out = sep_out - SPEC["sep_est_out"]
    eq(o["sep_dynamics"], [_axes(sep_in, sep_out),
                           _axes(sep_left_in, sep_left_out),
                           _axes(_refill_axis(sep_left_in, sep_in, SPEC["sep_dt"]),
                                 _refill_axis(sep_left_out, sep_out, SPEC["sep_dt"]))],
       "seperate dynamics")

    eq(o["defaulted"], [200, 100_000, 200.0, 100000.0, "defaulted", "defaulted"], "0 means defaulted")
    eq(o["unlimited"], [None, None, None, "unlimited", "unlimited", True, None, None], "None means unlimited")
    eq(o["sep_unlimited"], [[None, None, None], [None, None, None], "unlimited"], "seperate unlimited")
    eq(o["sep_partial_default"], [_axes(100_000, SPEC["partial_out_limit"]), "defaulted"],
       "seperate partial default")
    eq(o["coerce_scalar_to_sep"], _axes(SPEC["coerce_scalar"], SPEC["coerce_scalar"]),
       "scalar coerced to seperate")
    eq(o["coerce_sep_to_scalar"], SPEC["coerce_sep_in"] + SPEC["coerce_sep_out"],
       "seperate coerced to scalar")

    raise_tpm = SPEC["raise_tpm"]
    raise_requested = raise_tpm + SPEC["raise_over"]
    raised(o["raise_total"], cls="CapacityExceedsLimitError", mro="ValueError",
           axis="total", requested=raise_requested, limit=raise_tpm,
           string=f"request needs {raise_requested} total capacity but the per-minute limit is "
                  f"{raise_tpm}", msg="raise total")
    eq(o["raise_total_after"], [SPEC["raise_t0"], float(raise_tpm)], "raise moved nothing")
    raise_in = SPEC["raise_in_limit"]
    raised(o["raise_input"], cls="CapacityExceedsLimitError", mro="ValueError",
           axis="input", requested=raise_in + SPEC["raise_in_over"], limit=raise_in,
           string=f"request needs {raise_in + SPEC['raise_in_over']} input capacity but the "
                  f"per-minute limit is {raise_in}", msg="raise input")
    ok(o["unlimited_never_raises"], "unlimited axis never raises")
    eq(o["empty_bucket"],
       [float(SPEC["empty_tpm"]) - (SPEC["empty_est_in"] + SPEC["empty_est_out"]), True],
       "an empty bucket returns False rather than raising")

    res_total = SPEC["res_est_in"] + SPEC["res_est_out"]
    res_left = float(SPEC["res_tpm"]) - res_total
    res_slots = float(SPEC["res_rpm"] - 1)
    eq(o["reserve_first"], [_axes(SPEC["res_est_in"], SPEC["res_est_out"]), res_left, res_slots, 1],
       "reserve first")
    eq(o["reserve_second"], [True, res_left, res_slots, 2], "reserve refused, nothing consumed")
    eq(o["reserve_unlimited"], [_axes(SPEC["res_est_in"], SPEC["res_est_out"]), 3, None,
                                float(SPEC["res_unlimited_rpm"] - 1)], "reserve under no token limit")
    ok(o["free_capacity_gone"], "the dead free_capacity helper is gone")

    # The default block's numbers are curator's own cost map, which the ticket
    # does not touch; the header values are this run's.
    eq(o["apply"], [[100_000, "combined"], "seperate", SPEC["h_apply_req"],
                    _axes(SPEC["h_apply_in"], SPEC["h_apply_out"]),
                    [100_000, 40_000, 140_000],
                    _axes(SPEC["h_apply_in"], SPEC["h_apply_out"]), SPEC["h_apply_req"]],
       "apply_rate_limit_reading")

    rebind_left = _axes(SPEC["rebind_in_limit"] - SPEC["rebind_est_in"],
                        SPEC["rebind_out_limit"] - SPEC["rebind_est_out"])
    eq(o["rebind_consume"], [True, _axes(SPEC["rebind_in_limit"], SPEC["rebind_out_limit"]),
                             rebind_left],
       "a seperate-axis mutation must rebind a fresh _TokenUsage, leaving the old one alone")
    eq(o["rebind_settle"], [True, rebind_left], "settlement must rebind too")
    eq(o["precedence"], [[SPEC["prec_manual_req"], SPEC["prec_manual_tok"], SPEC["prec_manual_conc"]],
                         [SPEC["prec_header_req"], SPEC["prec_header_tok"], SPEC["prec_header_conc"]],
                         [True, True, True]],
       "the three limit properties keep their manual -> header -> default precedence")
    eq([counts[0] for counts in o["release_calls"]], [1, 1, 1],
       "the reservation is released exactly once per attempt on each of the exhausted, "
       "requeued and success exits")



# ---------------------------------------------------------------------------
# r1 — debt floor
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    _check_debt_floor_constant()
    limit = SPEC["r1_tpm"]
    eq(o["fraction"], CAPACITY_DEBT_FLOOR_FRACTION, "CAPACITY_DEBT_FLOOR_FRACTION")
    blocked = SPEC["r1_est_in"] + SPEC["r1_est_out"]
    eq(o["after_consume"], float(limit) - blocked, "after consume")
    # The usage is drawn above 1.25x the limit, so the settlement lands below
    # the floor and the floor is what it stops at.
    eq(o["after_settle"],
       _settle_combined(float(limit) - blocked, limit, blocked, SPEC["r1_used_total"]),
       "floored debt")
    eq(o["after_settle"], _floor_combined(limit), "the settlement must stop AT the floor")


def judge_r1_scope(o):
    _check_debt_floor_constant()
    ok(o["has_floor"], "a capacity debt floor fraction is not implemented")
    # A tracker told `0` is a tracker nobody told, so its limit — and therefore
    # its floor — is the ticket's published default.
    defaulted_limit = 100_000
    eq(o["defaulted_limit"], defaulted_limit, "defaulted limit")
    def_blocked = SPEC["r1_def_est_in"] + SPEC["r1_def_est_out"]
    eq(o["defaulted_after_consume"], float(defaulted_limit) - def_blocked, "defaulted after consume")
    eq(o["defaulted_after_settle"],
       _settle_combined(float(defaulted_limit) - def_blocked, defaulted_limit, def_blocked,
                        SPEC["r1_def_used_total"]), "defaulted floor")
    eq(o["defaulted_after_settle"], _floor_combined(defaulted_limit),
       "the defaulted tracker floors against the default it was given, not against 0")

    sep_in, sep_out = SPEC["r1_sep_in_limit"], SPEC["r1_sep_out_limit"]
    left_in = sep_in - SPEC["r1_sep_est_in"]
    left_out = sep_out - SPEC["r1_sep_est_out"]
    eq(o["sep_after_consume"], _axes(left_in, left_out), "seperate after consume")
    eq(o["sep_after_settle"],
       _axes(_settle_axis(left_in, sep_in, SPEC["r1_sep_est_in"], SPEC["r1_sep_used_in"]),
             _settle_axis(left_out, sep_out, SPEC["r1_sep_est_out"], SPEC["r1_sep_used_out"])),
       "seperate per-axis floor")
    eq(o["sep_after_settle"], _axes(_floor_axis(sep_in), _floor_axis(sep_out)),
       "each axis stops at its own floor, not at the other's")
    eq(o["unlimited_token"], None, "unlimited token untouched")
    eq(o["unlimited_request"], None, "unlimited request untouched")
    # The request slot is never floored and never returned by a settlement.
    eq(o["defaulted_request"], float(SPEC["r1_def_rpm"] - 1), "defaulted request capacity")
    eq(o["sep_request"], float(SPEC["r1_sep_rpm"] - 1), "seperate request capacity")


def judge_r1_exclusions(o):
    _check_debt_floor_constant()
    _check_clamp_counter()
    ok(o["has_floor"] and o["has_counter"], "a capacity debt floor with a clamp counter is not implemented")
    limit, slots = SPEC["excl_tpm"], SPEC["excl_rpm"]
    blocked = SPEC["excl_est_in"] + SPEC["excl_est_out"]
    # A whole minute or more of refill: both buckets come back to their ceiling,
    # and reaching a ceiling is not a clamp.
    eq(o["refilled"], [_refill_combined(float(limit) - blocked, limit, SPEC["excl_dt"]),
                       min((float(slots) - 1) + slots * SPEC["excl_dt"] / 60.0, float(slots)),
                       0], "refill caps, no clamp")
    eq(o["refilled"][0], float(limit), "the refill must reach the ceiling for this fact to mean anything")
    eq(o["released"], [_settle_combined(float(limit), limit, blocked, 0), 0], "release caps, no clamp")
    eq(o["released"][0], float(limit), "a release cannot raise an axis above its ceiling")
    eq(o["settled"], [_settle_combined(float(limit) - blocked, limit, blocked,
                                       SPEC["excl_settle_used"]), 0],
       "settlement above floor, no clamp")


def judge_r1_observability(o):
    _check_clamp_counter()
    ok(o["has_counter"], "a capacity debt clamp counter is not implemented")
    # Two calls clamp, one increment each, however many axes each one moved.
    eq(o["counts"], [0, 0, 1, 2], "one increment per clamping call")


# ---------------------------------------------------------------------------
# r2 — settlement vs refund
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    _check_refund_operation()
    limit, slots = SPEC["r2_rule_tpm"], SPEC["r2_rule_rpm"]
    blocked = SPEC["r2_rule_est_in"] + SPEC["r2_rule_est_out"]
    eq(o["after_consume"], [float(slots - 1), float(limit) - blocked], "after consume")
    ok(o["has_refund"], "a tracker refund operation is not implemented")
    eq(o["after_refund"], [float(slots), float(limit)], "refund returns whole estimate + one slot")
    eq(o["after_refund2"], [float(slots), float(limit)], "refund capped at limit")
    used = SPEC["r2_rule_used_in"] + SPEC["r2_rule_used_out"]
    eq(o["settled"], [_settle_combined(float(limit) - blocked, limit, blocked, used),
                      float(slots - 1)], "settlement keeps slot spent")
    eq(o["delegated_reserve"], [float(slots - 1), float(limit) - blocked], "delegated reserve")
    eq(o["delegated_refund"], [float(slots), float(limit)], "processor refund delegates")


def judge_r2_scope(o):
    _check_refund_operation()
    _check_failure_path_refunds()
    limit, slots = SPEC["r2_scope_tpm"], SPEC["r2_scope_rpm"]
    blocked = SPEC["r2_scope_est_in"] + SPEC["r2_scope_est_out"]
    eq(o["reserve_state"], [float(slots - 1), float(limit) - blocked], "reserve")
    eq(o["exhausted"], [float(slots), float(limit)], "exhausted failure refunds")
    eq(o["requeued"], [0, float(slots), float(limit)], "requeued failure refunds")
    # The success path settles instead: it keeps the slot and gives back only
    # the difference between what it blocked and what the response reported.
    used = SPEC["r2_scope_est_in"] + SPEC["r2_scope_used_out"]
    eq(o["success"], [float(slots - 1),
                      _settle_combined(float(limit) - blocked, limit, blocked, used)],
       "success settles")


def judge_r2_exclusions(o):
    _check_failure_path_refunds()
    limit, slots = SPEC["r2_excl_tpm"], SPEC["r2_excl_rpm"]
    blocked = SPEC["r2_excl_est_in"] + SPEC["r2_excl_est_out"]
    eq(o["blocked_axes"], _axes(SPEC["r2_excl_est_in"], SPEC["r2_excl_est_out"]), "blocked estimate")
    eq(o["after_reserve"], [float(slots - 1), float(limit) - blocked], "after reserve")
    # The response reported MORE than was blocked; the refund is the estimate,
    # so both buckets come back whole.
    eq(o["final"], [float(limit), float(slots)], "refund is the estimate, not the reported spend")


def judge_r2_observability(o):
    _check_settlement_and_refund_counters()
    ok(o["has_refund"], "a tracker refund operation distinct from settlement is not implemented")
    eq(o["initial"], [0, 0], "initial counters")
    eq(o["after_consume"], [0, 0], "consume counts as neither")
    eq(o["after_free"], [1, 0], "settlement counts a settlement")
    eq(o["refunded"], [0, 1], "refund counts a refund")
    eq(o["unlimited"], [1, 1, None, None], "both count even when no-op on unlimited")


JUDGES = {
    "test_open::test_open_feature__one_capacity_budget_decodes_limits_and_reserves_all_or_nothing": judge_open,
    "test_r1::test_rule__an_over_settled_axis_stops_at_a_quarter_of_the_limit_in_debt": judge_r1_rule,
    "test_r1::test_scope__the_floor_follows_the_normalised_limit_of_each_axis": judge_r1_scope,
    "test_r1::test_exclusions__capping_at_the_limit_and_staying_above_the_floor_do_not_count": judge_r1_exclusions,
    "test_r1::test_observability__the_clamp_counter_counts_calls_not_axes": judge_r1_observability,
    "test_r2::test_rule__a_refund_returns_the_whole_estimate_and_one_request_slot": judge_r2_rule,
    "test_r2::test_scope__both_failure_exits_refund_while_the_success_exit_settles": judge_r2_scope,
    "test_r2::test_exclusions__the_failure_refund_ignores_the_usage_the_response_reported": judge_r2_exclusions,
    "test_r2::test_observability__settlements_and_refunds_are_counted_apart_even_when_unlimited": judge_r2_observability,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g10_token_capacity_budget" '
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


def main(obs_path: str, out_path: str, seed: str, artifacts: str) -> int:
    """`artifacts` is the scenario directory `run_split` hands both processes.
    This suite's scenarios are in-process trackers, so nothing is read back from
    it; the argument is accepted because root passes it.
    """
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
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
