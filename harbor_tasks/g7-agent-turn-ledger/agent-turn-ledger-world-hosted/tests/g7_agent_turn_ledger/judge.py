"""g7 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote, the directories the probe's scenarios
actually ran in, and the cloned source text; writes a `junit.xml` whose
`classname`/`name` are the suite's node ids — so `score.py` folds them into the
fact keys and `test.sh`/`score.py` are unchanged. It runs as root; the worker
cannot read it, because `test.sh` keeps /tests root-only for a split suite and
the worker's jail holds only `probe.py`, `probe_support.py`, `fixture_spec.py`
and `harness.py`.

WHY THE ANSWERS HERE ARE NOT ENOUGH ON THEIR OWN. Keeping this file unreadable
stopped the worker copying the expected values out of it. It did not stop the
worker writing them anyway: the old fixture was the same every run, so a capture
of one correct run replayed onto a tree that implemented nothing scored 1.0 on
every hidden fact, and a constant file of booleans passed r2.scope and
r2.failure_behavior. Three things close that:

  * **the inputs move every run.** `fixture_spec.derive(seed)` re-draws the agent
    names, where a run dies, how long a log is, what a lying checkpoint claims
    and three shuffled lists of candidate replies, and this file works out what
    the answers must be for THOSE inputs;
  * **the directories are read here.** The checkpoint's bytes, the log's lines,
    whether loading wrote anything: this process opens the scenario directories
    under the artifacts root and compares them against what it expects, rather
    than trusting a flag the worker chose;
  * **the constants that cannot be re-drawn are read out of the source** as well
    as the run: `TURN_LEDGER_FILENAME`, `TURN_LEDGER_VERSION`,
    `COMPLETION_SENTINEL`.

The source is read for one more reason: the ticket's "reuse this as-is" clauses.
`append_response`, the `xxh64(seed_message)` run identity and "no new
dependency" are constraints on code inside files the ticket rewrites, so
`protected_files` cannot express them and no scenario can see them broken —
every fact runs against fakes in a fresh directory. `check_*` below compare
those against `CURATOR_BASELINE_DIR` and the pristine manifest, and fail the
open feature when the baseline is missing rather than passing blind.

The residual, stated plainly: a submission that implements the requirement inside
a forged hook — computing, from `fixture_spec`, what a correct implementation
would have written — still passes, because it has then done the work. What is
gone is passing by repeating values that were knowable in advance.

The node ids below are `<module>::<test>` because `score.py` folds them into the
fact keys. The pytest modules they are named after are the suite's
human-readable record of what each fact means and are kept in the repository,
not shipped with the task: a split suite grades through this file, and the
worked example in them pins the old fixed fixture ("client"/"advisor") rather
than the per-run names.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import stat
import sys
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_spec  # noqa: E402 - same derivation the worker used

# The judge runs `python3 -I` with no PYTHONPATH, so /tests is not importable by
# default. judge_io holds the hardened reads (no symlink, regular file only,
# size cap, raises rather than returning empty) that EVERY agent-influenced path
# goes through: the worker's artifacts, the observations file and the cloned
# submission are all paths the agent can shape. harness.py cannot serve this —
# it imports pytest, which this interpreter does not have.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import judge_io  # noqa: E402

# ---- the answers the hidden requirements fix, which cannot be re-drawn ------
SIDECAR = "turn_ledger.json"
LEDGER_VERSION = 2
SENTINEL = "<<END_OF_CONVERSATION>>"
STATUSES = ["adopted", "created", "verified"]
EIGHT_KEYS = sorted({
    "version", "responses", "turns", "last_author", "next_speaker",
    "interleave_faults", "completed", "completion_reason",
})

# ---- fixture inputs the open feature states ---------------------------------
SEED = "I need help with my investment strategy. What should I do?"
LOG = fixture_spec.LOG
CLOCK_ISO = fixture_spec.CLOCK_ISO

# Where `sym` looks for a module-level name, as source files.
SYMBOL_FILES = ("bespokelabs/curator/agent", "bespokelabs/curator/status_tracker/agent_status_tracker.py",
                "bespokelabs/curator/__init__.py")

SPEC: dict = {}
ARTIFACTS = pathlib.Path("/nonexistent")


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def is_true(got, msg=""):
    if got is not True:
        raise Fail(f"{msg}: {got!r} is not True")


def is_false(got, msg=""):
    if got is not False:
        raise Fail(f"{msg}: {got!r} is not False")


def raised_named(info, name, msg=""):
    ok(isinstance(info, dict) and info.get("raised"), f"{msg}: expected {name}, none raised")
    ok(name in (info.get("mro") or []), f"{msg}: {name} not in {info.get('mro')} ({info.get('str', '')[:200]})")


def value_of(step, msg):
    """The value of a probe step recorded with `attempt`, or the step's failure."""
    ok(isinstance(step, dict), f"{msg}: not measured")
    ok("error" not in step, f"{msg}: {step.get('error')}")
    return step.get("value")


# ---------------------------------------------------------------------------
# the expected run, from the seed
# ---------------------------------------------------------------------------
def seeder():
    return SPEC["seeder"]


def partner():
    return SPEC["partner"]


def author_of_line(i):
    """Line 0 is the seed, by the seeder; the two take turns from there."""
    return seeder() if i % 2 == 0 else partner()


def other(name):
    return partner() if name == seeder() else seeder()


def open_state(responses):
    """A checkpoint mid-run: `responses` generated, nothing finished."""
    last = author_of_line(responses)
    return {"version": LEDGER_VERSION, "responses": responses, "turns": responses + 1,
            "last_author": last, "next_speaker": other(last), "interleave_faults": 0,
            "completed": False, "completion_reason": "open"}


def spelled(state):
    return json.dumps(state, indent=2, sort_keys=True) + "\n"


def completes(value):
    return isinstance(value, str) and value.rstrip().endswith(SENTINEL)


# ---------------------------------------------------------------------------
# reading what the scenarios left, as root, without trusting it
# ---------------------------------------------------------------------------
def _safe_path(rel: str) -> pathlib.Path:
    """ARTIFACTS/rel, refusing a symlink anywhere below the artifacts root.

    The worker owns these directories, so any entry can be a symlink by the time
    root reads it — pointing at /opt/world-state or at a file planted before the
    run. `lstat` every component and open with O_NOFOLLOW.
    """
    ok(".." not in pathlib.PurePosixPath(rel).parts and not rel.startswith("/"), f"bad path {rel!r}")
    path = ARTIFACTS
    for part in pathlib.PurePosixPath(rel).parts:
        path = path / part
        try:
            st = os.lstat(path)
        except OSError:
            raise Fail(f"{rel}: does not exist")
        ok(not stat.S_ISLNK(st.st_mode), f"{rel}: is a symlink")
    return path


def read_bytes(rel: str) -> bytes:
    """A scenario file, read through `judge_io` behind the component walk.

    The walk above is g7's own: the worker owns these directories, so a symlink
    can be any component of the path and not just the last one. The open itself
    is `judge_io`'s (O_NOFOLLOW, regular file, size cap) so every judge in the
    suite refuses the same things in the same way, and the 4 MB cap stays — the
    largest legitimate artifact here is a hand-written log of a few KB, and the
    bytes go into a failure message that junit.xml carries out of the run.
    """
    path = _safe_path(rel)
    try:
        return judge_io.read_bytes(path, limit=4 * 1024 * 1024)
    except OSError as exc:
        raise Fail(f"{rel}: {exc}")


def exists(rel: str) -> bool:
    try:
        read_bytes(rel)
        return True
    except Fail:
        return False


def text_of(rel: str) -> str:
    return read_bytes(rel).decode("utf-8", errors="replace")


def json_of(rel: str):
    try:
        return json.loads(read_bytes(rel))
    except ValueError as exc:
        raise Fail(f"{rel}: not JSON: {exc}")


def listing(dirrel: str) -> list:
    path = _safe_path(dirrel)
    ok(path.is_dir(), f"{dirrel}: not a directory")
    return sorted(os.listdir(path))


def log_rows(dirrel: str) -> list:
    """[(name, response_message)] for every non-blank line of a scenario's log."""
    out = []
    for line in text_of(f"{dirrel}/{LOG}").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            raise Fail(f"{dirrel}/{LOG}: a line is not JSON")
        out.append((record.get("name"), record.get("response_message")))
    return out


def same_file(recorded, rel: str, msg: str):
    ok(isinstance(recorded, str) and recorded, f"{msg}: no path recorded ({recorded!r})")
    eq(os.path.realpath(recorded), os.path.realpath(str(ARTIFACTS / rel)), msg)


def plain_name(name, msg):
    ok(isinstance(name, str) and name and os.path.basename(name) == name
       and name not in (".", "..") and name != LOG,
       f"{msg}: no checkpoint name to plant under ({name!r}) — the submission neither "
       "exports the constant nor leaves a single file beside a fresh run's log")


# ---------------------------------------------------------------------------
# reading the submission's source — for the constants that cannot be re-drawn
# ---------------------------------------------------------------------------
PKG = "bespokelabs/curator"

# The pristine repository root. `CURATOR_BASELINE_DIR` is a staged copy of the
# curator PACKAGE only (run_suites.stage_baseline copies
# src/bespokelabs/curator), so the manifest is not in it; the judge is root, and
# this is the same pristine checkout `run_suites.check_protected` byte-compares
# the protected files against.
PRISTINE_REPO = pathlib.Path("/opt/world-state/input/curator")

# What the ticket says is already present (instruction.md:67), on top of the
# standard library and everything the pristine library already imports.
ALLOWED_DISTRIBUTIONS = frozenset({"bespokelabs", "pydantic", "datasets", "aiofiles", "aiohttp"})

# instruction.md:66 — "Nothing in `llm/`, `request_processor/`, `client.py`,
# `db.py` or the viewer changes." `protected_files` in task.json byte-compares
# the 23 files those three directories held when the world was baked, which says
# nothing about a file that was ADDED to one of them: a submission could put
# `request_processor/turn_ledger_helper.py` beside the processors, call it from
# the editable agent package, and every protected byte would still match. So the
# MEMBERSHIP of each directory is compared as well, against CURATOR_BASELINE_DIR.
PROTECTED_DIRS = ("llm", "request_processor", "viewer")

# The attributes instruction.md:65-66 keep, and which the source comparisons
# below read from the class body. Every one of them is compared as WRITTEN, so a
# rebind at import time would leave the compared text in place while something
# else runs; `_no_protected_rebinds` refuses that shape whatever receiver it is
# applied to.
PROTECTED_ATTRS = frozenset({"append_response", "__call__", "_setup_metadata",
                             "_hash_fingerprint"})

# Build droppings a checkout or a test run leaves behind. Ignored, because a
# submission is not modifying `request_processor/` by importing from it.
DROPPINGS = frozenset({".pyc", ".pyo", ".pyd", ".so", ".orig", ".rej"})

# instruction.md:11 — the new module takes every timestamp as a parameter.
LEDGER_MODULE = "agent/turn_ledger.py"
CLOCKS = frozenset({"time", "random", "uuid"})

# Where a dependency can be declared. A name that appears in none of these is
# not installed, so "no new dependency" is a statement about exactly these.
DEPENDENCY_TABLES = (("tool", "poetry", "dependencies"),
                     ("tool", "poetry", "group", "dev", "dependencies"),
                     ("tool", "poetry", "extras"),
                     ("project",))


def _symbol_sources():
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    for rel in SYMBOL_FILES:
        path = root / rel
        files = sorted(path.rglob("*.py")) if path.is_dir() else [path]
        for file in files:
            if not file.is_file() or file.is_symlink():
                continue
            try:
                yield judge_io.read_text(file)
            except OSError as exc:
                # A source file this judge will not read is a failed fact, never a
                # skipped one: `defined()` would otherwise report "no module
                # assigns it" for a reason that is not the submission's spelling.
                raise Fail(f"{file}: {exc}")


def defined(name: str, expected):
    """The module-level assignment of `name` somewhere `sym` looks, checked
    against `expected` when it is a literal.

    A non-literal assignment is accepted here and left to the runtime value the
    probe reported; what fails is a tree that REPORTS the constant without
    defining it at all, or defines it as a different literal.
    """
    seen = False
    for src in _symbol_sources():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.Assign):
                targets, value = node.targets, node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets, value = [node.target], node.value
            else:
                continue
            if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                seen = True
                try:
                    literal = ast.literal_eval(value)
                except ValueError:
                    continue
                eq(literal, expected, f"{name} as written in the source")
    ok(seen, f"no module of bespokelabs.curator.agent assigns {name}")


# ---------------------------------------------------------------------------
# the ticket's "do not touch this" clauses, which no behaviour can show
#
# `protected_files` in task.json covers the 25 whole files instruction.md:66
# names. It cannot cover a rule about code INSIDE a file the ticket must edit,
# and three of those rules are stated outright:
#
#   * instruction.md:65 — `MultiTurnAgenticProcessor.append_response()` is
#     reused *verbatim*, in a processor.py the ticket rewrites around it;
#   * instruction.md:66 — `Agent._hash_fingerprint` and the `xxh64(seed_message)`
#     run identity are untouched, in an agent.py the ticket also edits;
#   * instruction.md:67 — no new dependency.
#
# Every behavioural fact here runs against fakes in a tmp_path, so a submission
# that rewrote append_response to write its own record format, recomputed the
# working-directory fingerprint, or pulled in a JSON-schema library passed all
# nine facts with the ticket's stated constraints broken. Source, not behaviour,
# because the constraint IS about the source.
# ---------------------------------------------------------------------------
def _submission_src() -> pathlib.Path:
    root = os.environ.get("SUBMISSION_SRC", "")
    ok(root, "SUBMISSION_SRC is not set, so the submission's source cannot be read")
    return pathlib.Path(root)


def _baseline_pkg() -> pathlib.Path:
    """The staged pristine curator package, or a failed fact.

    Never a pass by default: a missing baseline means "unchanged" was not
    checked, and a rule nothing checks is the defect this closes.
    """
    root = os.environ.get("CURATOR_BASELINE_DIR", "")
    ok(root, "CURATOR_BASELINE_DIR is unset: the pristine tree was not staged, so the "
             "ticket's 'reused verbatim' and 'untouched' clauses cannot be checked")
    path = pathlib.Path(root)
    ok((path / "agent" / "agent.py").is_file(),
       f"CURATOR_BASELINE_DIR={root} is not a curator package")
    return path


def _tree(path: pathlib.Path, what: str) -> ast.Module:
    try:
        return ast.parse(judge_io.read_text(path))
    except (OSError, SyntaxError) as exc:
        raise Fail(f"{what}: {exc}")


def _strip_docstrings(tree: ast.Module) -> ast.Module:
    """The same tree without its docstrings, so re-wording prose is not a diff."""
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", [])
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
    return tree


# --- resolving the method the interpreter actually binds --------------------
#
# Every comparison below asks "is this still the code the world shipped?", and
# the answer means nothing unless it reads the method Python BINDS. The first
# version of this took the first `class`/`def` of the name in `ast.walk` order,
# which is the opposite of what Python does, and on a sibling task that was a
# full bypass of the whole reward: the pristine method left where the judge
# looks, and the real one bound after it by a duplicate `def`, by a `def` parked
# under `if True:` in the class body, or by an assignment. So, exactly one
# definition of the name ANYWHERE in the module, and nothing that rebinds it
# afterwards — a name defined twice is REFUSED rather than resolved, because
# nothing in this ticket has a reason to define one method twice.
#
# `tree.body` was the second version of this, and it was the same bug one level
# out: `if True:` / `for _ in [1]:` / `try:` at module level all bind a
# `class MultiTurnAgents(MultiTurnAgents)` that ast.Module.body does not hold,
# so the judge read the pristine class above it and PASSED a tree whose bound
# `__call__` had the working-directory join deleted — measured 9/9, reward 1.0.
# Hence: search the whole module, and refuse a definition that is not a direct
# statement of the module (a conditional class body is not something this ticket
# asks anyone to write, and resolving which branch runs is not this judge's job).
def _module_class(tree: ast.Module, cls: str, what: str) -> ast.ClassDef:
    nodes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == cls]
    if len(nodes) > 1:
        raise Fail(f"{what}: class {cls} is defined {len(nodes)} times in this module; Python "
                   "binds the last one, so a decoy class cannot stand in for it")
    if not nodes:
        raise Fail(f"{what}: no module-level class {cls}")
    node = nodes[0]
    if not any(stmt is node for stmt in tree.body):
        raise Fail(f"{what}: class {cls} is defined at line {node.lineno} inside a conditional, a "
                   "loop or a try at module level; whatever that binds is not the class the world "
                   "shipped at module level")
    if node.decorator_list:
        raise Fail(f"{what}: class {cls} at line {node.lineno} carries a decorator, which receives "
                   "the class and can replace any method on it after this comparison would have "
                   "read it")
    for stmt in ast.walk(tree):
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if isinstance(target, ast.Name) and target.id == cls:
                raise Fail(f"{what}: the name {cls} is reassigned at line {stmt.lineno}, so the "
                           "class read here is not the one the module exports")
            # `globals()["MultiTurnAgents"] = _Decoy` rebinds the module's export
            # without ever naming it as an assignment target; so does any other
            # namespace subscript spelled with the name as a constant.
            if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant) \
                    and target.slice.value == cls:
                raise Fail(f"{what}: the name {cls} is rebound through a namespace subscript at "
                           f"line {stmt.lineno}, which replaces the class the module exports")
    return node


def _no_protected_rebinds() -> None:
    """No file of the submission's package rebinds a method these checks read.

    Four rounds went into teaching this scan to RECOGNISE the receiver — the
    class name, an alias chain (`_M = MultiTurnAgents; _M.__call__ = _mine`),
    an import alias, `module.Class.method = ...`, `globals()["Class"]` — and
    each round produced one more spelling, the last being
    `getattr(m, "Multi" + "TurnAgenticProcessor").append_response = replacement`,
    which no static receiver analysis can resolve at all. So the receiver is no
    longer read: an assignment whose ATTRIBUTE is one of PROTECTED_ATTRS is
    refused whatever sits to its left, and a `setattr` whose name argument is
    not a plain string literal is refused fail-closed, because a computed name
    cannot be proved not to be one of them. The pristine curator package holds
    neither shape (no assignment to any of these attributes, and no `setattr`
    at all), and the ticket asks for neither, so nothing honest is refused.
    """
    pkg = _submission_src() / PKG
    for path in sorted(pkg.rglob("*.py")):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(pkg)
        for node in ast.walk(_tree(path, str(rel))):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Attribute) and target.attr in PROTECTED_ATTRS:
                        raise Fail(f"{rel} line {node.lineno} assigns .{target.attr}, which "
                                   "replaces a method the ticket keeps and this judge reads; "
                                   "the ticket asks for no such assignment, whatever object it "
                                   "is applied to")
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "setattr":
                arg = node.args[1] if len(node.args) >= 2 else None
                if not (isinstance(arg, ast.Constant) and isinstance(arg.value, str)):
                    raise Fail(f"{rel} line {node.lineno} calls setattr with a name that is not a "
                               "string literal, so it cannot be shown not to rebind a method the "
                               "ticket keeps; the pristine library calls setattr nowhere")
                if arg.value in PROTECTED_ATTRS:
                    raise Fail(f"{rel} line {node.lineno} calls setattr for {arg.value!r}, which "
                               "replaces a method the ticket keeps")


def _no_binding_in_package(name: str, clause: str) -> None:
    """The name is bound nowhere the submission added it.

    Banning `def _hash_fingerprint` was the whole check, and
    `_hash_fingerprint = _cheap_fp` in the `Agent` class body passed it while
    making the run identity a constant. So: a `def`, an assignment to the bare
    name or to `X._hash_fingerprint`, a `setattr(..., "_hash_fingerprint", ...)`
    or a namespace subscript all count. A `setattr` spelled with a computed name
    is not this function's problem: `_no_protected_rebinds` has already refused
    every `setattr` whose name is not a string literal. A file where the PRISTINE tree binds the
    name too is skipped — `llm/llm.py` and `code_executor.py` are where this
    method legitimately lives, and both are protected files anyway.
    """
    pkg = _submission_src() / PKG
    base = _baseline_pkg()
    for path in sorted(pkg.rglob("*.py")):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(pkg)
        pristine = base / rel
        if pristine.is_file() and _binds(_tree(pristine, f"the pristine {rel}"), name):
            continue
        node = _binds(_tree(path, str(rel)), name)
        if node is not None:
            raise Fail(f"{rel} binds {name} at line {node.lineno}; {clause}")


def _binds(tree: ast.Module, name: str):
    """The first node that makes `name` mean something else, or None."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node
                if isinstance(target, ast.Attribute) and target.attr == name:
                    return node
                if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant) \
                        and target.slice.value == name:
                    return node
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "setattr" \
                and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) \
                and node.args[1].value == name:
            return node
    return None


def _bound_method(tree: ast.Module, cls: str, name: str, what: str):
    """`cls.name` as the class binds it, refusing every way of rebinding it.

    Refused: two `def`s of the name in one class body (the later one wins); a
    `def` or an assignment of the name anywhere else in the class body, at any
    depth — under an `if`, a loop or a `try` — which executes after the direct
    `def` and replaces it; and `cls.name = ...` or `setattr(cls, ...)` anywhere
    in the file. A decorator, a changed signature and a changed statement need no
    special case — they are part of the dump that is compared.
    """
    klass = _module_class(tree, cls, what)
    direct = [stmt for stmt in klass.body
              if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == name]
    if len(direct) > 1:
        raise Fail(f"{what}: {cls}.{name} is defined {len(direct)} times in one class body; "
                   "Python binds the last one, so a duplicate definition is not the "
                   "implementation the world shipped")
    if not direct:
        raise Fail(f"{what}: {cls} has no {name}()")
    for stmt in klass.body:
        # The direct `def`s and the class's other members are the class as it
        # reads; what is looked for here is a SECOND binding of this one name
        # executed after it — which is every remaining kind of statement a class
        # body can hold.
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for node in ast.walk(stmt):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                raise Fail(f"{what}: {cls}.{name} is also defined at line {node.lineno}, under a "
                           "conditional or a loop in the class body — that definition is the one "
                           "the class ends up with, whatever sits beside it")
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                    raise Fail(f"{what}: {cls}.{name} is rebound by an assignment in the class "
                               f"body at line {node.lineno}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Attribute) and t.attr == name and isinstance(t.value, ast.Name)
                and t.value.id == cls for t in node.targets):
            raise Fail(f"{what}: {cls}.{name} is reassigned at line {node.lineno}")
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "setattr" \
                and node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == cls:
            raise Fail(f"{what}: setattr on {cls} at line {node.lineno} rebinds its methods")
    return direct[0]


def _identical_method(rel: str, cls: str, name: str, clause: str, *, prose: bool) -> None:
    """One method is the pristine one, compared as an AST in the method's own place.

    `prose=False` strips docstrings from both trees first, for a method whose
    constraint is about what it does rather than how it reads.
    """
    theirs, mine = _both_methods(rel, cls, name, prose=prose)
    ok(ast.dump(mine) == ast.dump(theirs),
       f"{cls}.{name} in {rel} (line {mine.lineno}) is not the method the world shipped, "
       f"and {clause}")


def _both_methods(rel: str, cls: str, name: str, *, prose: bool):
    """The pristine and the submitted `cls.name`, both as the module binds them.

    The package-wide rebind scan is NOT run here: it is not per-method any more,
    so `judge_open` runs it once before any of these comparisons rather than
    three times over the same package.
    """
    mine_tree = _tree(_submission_src() / PKG / rel, rel)
    base_tree = _tree(_baseline_pkg() / rel, f"the pristine {rel}")
    if not prose:
        _strip_docstrings(mine_tree)
        _strip_docstrings(base_tree)
    theirs = _bound_method(base_tree, cls, name, f"fixture drift: the pristine {rel}")
    mine = _bound_method(mine_tree, cls, name, rel)
    return theirs, mine


def check_append_response_verbatim():
    """instruction.md:65 — append_response is the pristine method, statement for statement.

    Compared as an AST, so reformatting, a moved comment or a re-wrapped line is
    not a change and a changed record format is. The signature is part of the
    comparison, because the processor calls it positionally. Docstrings are part
    of it too: the ticket's word here is *verbatim*.
    """
    _identical_method("agent/processor.py", "MultiTurnAgenticProcessor", "append_response",
                      "the ticket reuses it verbatim", prose=True)


def check_run_identity_untouched():
    """instruction.md:66 — `Agent._hash_fingerprint` and the xxh64(seed_message) identity.

    THREE ways to touch it, and the first two were all this checked. Override
    `_hash_fingerprint` in agent.py (it belongs to `curator.LLM`, in the
    already-protected llm/llm.py); rebuild the fingerprint itself; or leave the
    fingerprint exactly as the world wrote it and change what is DONE with it.
    The v7 review named the third precisely: `MultiTurnAgents.__call__` derives
    the fingerprint and then names the run's working directory after it, so a
    submission that keeps all three pristine `fingerprint` statements and drops
    the join — or joins something else — orphans every cache directory the
    company already has, and a statement-by-statement comparison of the
    derivation sees nothing wrong. No scenario closes it either: every fact here
    hands the processor its own directory, so `__call__` never runs under the
    grader at all.

    So the identity is compared where it is written, in the two methods that
    derive it and record it, as the module BINDS them: in `__call__`, every
    statement that binds `fingerprint`, `disable_cache` or `working_dir` — the
    three-part derivation, the `xxh64(seed_message)` in the middle of it, and
    the `os.path.join(working_dir, fingerprint)` that turns it into the run's
    directory — and in both methods the `run_hash`/`dataset_hash` entries that
    report it. NOT the whole method: a `logger.debug` added to `__call__` or an
    unrelated key added to the metadata dict changes neither the identity nor
    the directory, and instruction.md constrains the identity, not the method's
    every line. The statements are compared in order and NOTHING may bind those
    names beyond them, so dropping the join, joining something else, or
    re-deriving the fingerprint after the fact are all one comparison.
    """
    rel = "agent/agent.py"
    _no_binding_in_package("_hash_fingerprint",
                           "the ticket leaves Agent._hash_fingerprint alone, and it belongs to "
                           "curator.LLM")

    theirs, mine = _both_methods(rel, "MultiTurnAgents", "__call__", prose=False)

    # Fixture drift, before the comparison means anything: the pristine
    # __call__ really is where the seed message is hashed and where the
    # fingerprint becomes the working directory.
    ok(any(isinstance(node, ast.Name) and node.id == "xxh64" for node in ast.walk(theirs)),
       f"fixture drift: the pristine MultiTurnAgents.__call__ in {rel} does not hash the seed "
       "message")
    ok(any(isinstance(node, ast.Assign)
           and any(isinstance(t, ast.Name) and t.id == "working_dir" for t in node.targets)
           and any(isinstance(sub, ast.Name) and sub.id == "fingerprint"
                   for sub in ast.walk(node.value))
           for node in ast.walk(theirs)),
       f"fixture drift: the pristine MultiTurnAgents.__call__ in {rel} does not name the working "
       "directory after the fingerprint")

    clause = "the ticket leaves the xxh64(seed_message) run identity untouched"
    identity = ("fingerprint", "disable_cache", "working_dir")
    ok(_binding_statements(mine, identity) == _binding_statements(theirs, identity),
       f"MultiTurnAgents.__call__ in {rel} does not derive the run identity and the run's working "
       f"directory with the statements the world shipped, and {clause}")
    for key in ("run_hash",):
        ok(_mapping_value(mine, key) == _mapping_value(theirs, key),
           f"MultiTurnAgents.__call__ in {rel} does not report {key!r} as the world shipped it, "
           f"and {clause}")

    theirs, mine = _both_methods(rel, "MultiTurnAgents", "_setup_metadata", prose=False)
    eq([arg.arg for arg in mine.args.args], [arg.arg for arg in theirs.args.args],
       f"MultiTurnAgents._setup_metadata in {rel} takes different parameters than the world "
       f"shipped, and {clause}")
    for key in ("run_hash", "dataset_hash"):
        ok(_mapping_value(mine, key) == _mapping_value(theirs, key),
           f"MultiTurnAgents._setup_metadata in {rel} does not record {key!r} as the world shipped "
           f"it, and {clause}")


def _binding_statements(method, names) -> list:
    """Every statement of `method` that binds one of `names`, in source order.

    The list is compared whole, so a statement missing (the join deleted), a
    statement changed (the join pointed somewhere else) and a statement added (a
    second `working_dir = ...` further down) are the same failure. Sorted by
    line, because `ast.walk` is breadth-first and two trees that differ only in
    nesting would otherwise compare by accident.
    """
    found = []
    for node in ast.walk(method):
        if not isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(t, ast.Name) and t.id in names for t in targets):
            found.append((node.lineno, node.col_offset, ast.dump(node)))
    return [dump for _, _, dump in sorted(found)]


def _mapping_value(method, key: str) -> list:
    """The value every dict literal in `method` gives to `key`, in source order."""
    found = []
    for node in ast.walk(method):
        if not isinstance(node, ast.Dict):
            continue
        for name, value in zip(node.keys, node.values):
            if isinstance(name, ast.Constant) and name.value == key:
                found.append((value.lineno, value.col_offset, ast.dump(value)))
    return [dump for _, _, dump in sorted(found)]


def _imports(tree: ast.Module) -> set:
    """Top-level distribution names an absolute import reaches for."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def _manifest(root: pathlib.Path, what: str) -> dict:
    """The dependency names each table declares, the build requires, the floor.

    tomllib is stdlib from 3.11 and the world image's python3 is 3.12; imported
    here rather than at module scope so an older interpreter fails THIS fact
    instead of every one of the nine.
    """
    try:
        import tomllib
    except ImportError as exc:  # pragma: no cover - 3.12 in every world image
        raise Fail(f"cannot check the manifest: {exc}")
    path = root / "pyproject.toml"
    try:
        data = tomllib.loads(judge_io.read_text(path))
    except (OSError, ValueError) as exc:
        raise Fail(f"{what} pyproject.toml: {exc}")
    tables = {}
    for keys in DEPENDENCY_TABLES:
        node = data
        for key in keys:
            node = node.get(key, {}) if isinstance(node, dict) else {}
        if keys == ("project",):  # a PEP 621 manifest lists, not maps
            node = {name: None for name in (node.get("dependencies") or [])}
        tables[".".join(keys)] = sorted(node) if isinstance(node, dict) else []
    poetry = (data.get("tool") or {}).get("poetry") or {}
    return {"tables": tables,
            "requires": sorted((data.get("build-system") or {}).get("requires") or []),
            "python": (poetry.get("dependencies") or {}).get("python")}


def _dir_members(root: pathlib.Path, rel: str) -> list:
    """Every file under `root/rel`, relative to it, minus the build droppings."""
    base = root / rel
    if not base.is_dir():
        return []
    found = []
    for path in base.rglob("*"):
        if path.is_dir() or path.is_symlink():
            continue
        parts = path.relative_to(base).parts
        if "__pycache__" in parts or ".git" in parts or path.suffix in DROPPINGS:
            continue
        if any(part.endswith(".egg-info") for part in parts):
            continue
        found.append("/".join(parts))
    return sorted(found)


def check_protected_dirs_unchanged():
    """instruction.md:66 — "Nothing in `llm/`, `request_processor/`, `client.py`,
    `db.py` or the viewer changes."

    A directory-level rule, and `protected_files` can only express the file-level
    half of it. The v8 reviewer wrote the bypass out: add
    `request_processor/turn_ledger_helper.py`, drive it from the agent package
    which the ticket does open, and the 23 byte comparisons all still pass. A
    deletion is the same shape in reverse. So the membership of each directory is
    compared against the pristine tree, ignoring `__pycache__` and compiled
    droppings, which a checkout leaves behind and which change nothing.
    """
    mine, theirs = _submission_src() / PKG, _baseline_pkg()
    for rel in PROTECTED_DIRS:
        base = _dir_members(theirs, rel)
        ok(base, f"fixture drift: the pristine {rel}/ is empty or missing from "
                 f"{theirs}, so 'nothing in {rel}/ changes' cannot be checked")
        got = _dir_members(mine, rel)
        added = sorted(set(got) - set(base))
        dropped = sorted(set(base) - set(got))
        ok(not added, f"{rel}/ gains {added}; instruction.md:66 keeps the whole directory as the "
                      "world shipped it, and code the ticket may not put there is code the "
                      "grader's protected-file comparison never sees")
        ok(not dropped, f"{rel}/ loses {dropped}; instruction.md:66 keeps the whole directory as "
                        "the world shipped it")


def check_no_new_dependency():
    """instruction.md:67 — no new dependency, and Python stays at ^3.10.

    Two halves, because either alone is avoidable: the manifest (a dependency
    that is declared) and the imports (a dependency that is merely used, which
    works on a devbox that happens to have it installed and breaks in CI).
    """
    base = _baseline_pkg()
    ok((PRISTINE_REPO / "pyproject.toml").is_file(),
       f"the pristine manifest is unreadable at {PRISTINE_REPO}/pyproject.toml, so 'no new "
       "dependency' cannot be checked")
    mine = _manifest(_submission_src().parent, "the submission's")
    theirs = _manifest(PRISTINE_REPO, "the pristine")
    for table, names in theirs["tables"].items():
        added = sorted(set(mine["tables"].get(table, [])) - set(names))
        dropped = sorted(set(names) - set(mine["tables"].get(table, [])))
        ok(not added, f"pyproject.toml [{table}] gains {added}; the ticket adds no dependency")
        ok(not dropped, f"pyproject.toml [{table}] drops {dropped}")
    eq(mine["requires"], theirs["requires"], "pyproject.toml build-system requires")
    eq(mine["python"], theirs["python"], "the python constraint, which the ticket keeps at ^3.10")

    # Everything the pristine library already imports is already a dependency;
    # anything else, outside the standard library and the four the ticket names,
    # is a new one however it got installed.
    allowed = set(sys.stdlib_module_names) | set(ALLOWED_DISTRIBUTIONS)
    for file in sorted(base.rglob("*.py")):
        allowed |= _imports(_tree(file, f"the pristine {file.name}"))
    pkg = _submission_src() / PKG
    for file in sorted(pkg.rglob("*.py")):
        if file.is_symlink():
            continue
        rel = file.relative_to(pkg).as_posix()
        tree = _tree(file, rel)
        outside = sorted(_imports(tree) - allowed)
        ok(not outside, f"{rel} imports {outside}, which the pristine library never imports; "
                        "the ticket adds no dependency")
        if rel != LEDGER_MODULE:
            continue
        # instruction.md:11, while the module's source is open: the ledger takes
        # every timestamp as a parameter, which is what makes the seed record's
        # created_at checkable at all.
        reached = sorted(_imports(tree) & CLOCKS)
        ok(not reached, f"{rel} imports {reached}; it takes every timestamp as a parameter")
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "urandom":
                raise Fail(f"{rel} reaches for os.urandom at line {node.lineno}")


# ---------------------------------------------------------------------------
# open feature
# ---------------------------------------------------------------------------
def judge_open(o):
    # The ticket's scope clauses first: they are the cheapest to read and the
    # only thing here no scenario can show. The rebind scan leads, because a
    # rebind makes every comparison after it read code that is not what runs.
    _no_protected_rebinds()
    check_append_response_verbatim()
    check_run_identity_untouched()
    check_protected_dirs_unchanged()
    check_no_new_dependency()

    S_, P_ = seeder(), partner()
    eq(o["calls_names"], [P_, S_, P_, S_], "call order")
    eq(o["calls_task_ids"], [0, 1, 2, 3], "task ids")
    eq(o["n_calls"], 4, "call count")
    eq(o["n_lines"], 5, "log lines")
    eq(o["authors"], [S_, P_, S_, P_, S_], "authors")

    s = o["seed"]
    eq(s["name"], S_, "seed name")
    eq(s["response_message"], SEED, "seed message")
    eq(s["finish_reason"], "seed", "seed finish_reason")
    eq(s["response_cost"], 0.0, "seed cost")
    for key in ("token_usage_is_none", "raw_response_is_none", "raw_request_is_none",
                "parsed_is_none", "errors_is_none", "created_eq_finished"):
        is_true(s[key], f"seed {key}")
    eq(s["created_iso"], CLOCK_ISO, "seed created_at")
    eq(s["finished_iso"], CLOCK_ISO, "seed finished_at")
    eq(s["gr_model"], "gpt-4o-mini", "seed request model")
    eq(s["gr_messages"], [{"role": "user", "content": SEED}], "seed request messages")
    eq(s["gr_original_row"], {"prompt": SEED}, "seed original_row")
    eq(s["gr_original_row_idx"], 0, "seed original_row_idx")

    lg = o["ledger"]
    eq(lg["responses"], 4, "ledger responses")
    eq(lg["turns"], 5, "ledger turns")
    eq(lg["last_author"], S_, "ledger last_author")
    eq(lg["next_speaker"], None, "ledger next_speaker")
    eq(lg["interleave_faults"], 0, "ledger interleave_faults")
    is_true(lg["completed"], "ledger completed")
    eq(lg["completion_reason"], "budget", "ledger completion_reason")
    is_true(lg["entries_is_tuple"], "ledger entries is tuple")
    is_true(lg["messages_eq_history"], "ledger.messages() == conversation_history")
    eq(o["history0"], {"role": S_, "content": SEED}, "history[0]")

    tr = o["tracker"]
    eq(tr["max_turns"], 4, "max_turns")
    eq(tr["current_turn"], 4, "current_turn")
    eq(tr["num_responses"], 4, "num_responses")
    eq(tr["num_cached"], 0, "num_cached")
    eq(tr["num_errors"], 0, "num_errors")

    eq(o["columns"], ["content", "role", "source", "turn"], "dataset columns")
    eq(o["n_rows"], 5, "row count")
    eq(o["row0"], {"role": S_, "content": SEED, "turn": 0, "source": "seed"}, "row 0")
    eq(o["turns_col"], [0, 1, 2, 3, 4], "turn column")
    eq(o["sources_col"], ["seed"] + ["response"] * 4, "source column")
    eq(o["roles_col"], o["authors_after"], "role column == authors")

    eq(o["resume_calls"], [[P_, 2], [S_, 3]], "resume calls")
    eq(o["resume_n_calls"], 2, "resume call count")
    eq(o["resume_lines"], 5, "resume log lines")
    eq(o["resume_responses"], 4, "resume ledger responses")
    eq(o["resume_n_rows"], 5, "resume rows")
    eq(o["resume_num_cached"], 2, "resume num_cached")
    eq(o["resume_num_responses"], 2, "resume num_responses")
    eq(o["resume_current_turn"], 4, "resume current_turn")

    eq(o["bare_n_calls"], 1, "bare call count")
    eq(o["bare_lines"], 2, "bare log lines")
    eq(o["bare_n_rows"], 2, "bare rows")

    check_multi_system(o)


def check_multi_system(o):
    """instruction.md:44 — "When the formatter produced more than one system
    message, the first is used and the others stay in place in the body."

    Derived, never a literal: the probe reports what the fake formatter answered
    for each call, what the processor then sent, and the log's own authors and
    contents. The expected messages are rebuilt here from the first two —
    every ledger message mapped by author, its last replaced by the formatter's
    output minus the one system message that moves, and that message inserted at
    index 0. A submission that filters every system message out of the body and
    reinserts one drops the extras, which is what the oracle itself did until v9.
    """
    requests = o["multi_requests"]
    produced = o["multi_formatter_out"]
    authors, contents = o["multi_authors"], o["multi_contents"]
    eq(len(requests), 2, "calls in the multi-system scenario")
    eq(len(produced), 2, "formatter answers in the multi-system scenario")
    eq(len(authors), 3, "log lines in the multi-system scenario")

    for nth, (sent, answered) in enumerate(zip(requests, produced), start=1):
        target = authors[nth]
        history = list(zip(authors[:nth], contents[:nth]))
        mapped = [{"role": "assistant" if author == target else "user", "content": content}
                  for author, content in history]
        systems = [i for i, msg in enumerate(answered) if msg["role"] == "system"]
        ok(len(systems) > 1,
           f"fixture drift: call {nth}'s formatter answered with {len(systems)} system "
           "message(s), so the case instruction.md:44 names is not being exercised")
        body = [msg for i, msg in enumerate(answered) if i != systems[0]]
        want = [answered[systems[0]]] + mapped[:-1] + body
        eq(sent, want,
           f"the messages call {nth} was given: instruction.md:44 moves the FIRST system message "
           "to index 0 and leaves the others in place in the body")


# ---------------------------------------------------------------------------
# r1 — the checkpoint beside the log
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    eq(o["filename"], SIDECAR, "TURN_LEDGER_FILENAME")
    defined("TURN_LEDGER_FILENAME", SIDECAR)
    eq(o["version"], LEDGER_VERSION, "TURN_LEDGER_VERSION")
    defined("TURN_LEDGER_VERSION", LEDGER_VERSION)
    for name in ("read_sidecar", "write_sidecar", "verify_sidecar"):
        is_true(o["functions"].get(name), f"{name} is exported")

    die_on = SPEC["rule_die_on"]
    raised_named(o["run_raises"], "Boom", f"the run dies on call {die_on}")
    responses = die_on - 1
    expected = open_state(responses)
    eq([name for name, _ in log_rows("r1_rule_run")],
       [author_of_line(i) for i in range(die_on)], "authors in the log when the run died")

    # Written before the failure, so written after a response and not at the end.
    ok(exists(f"r1_rule_run/{SIDECAR}"),
       f"no {SIDECAR} beside the log when the run died after {responses} response(s); "
       f"the directory held {listing('r1_rule_run')}")
    on_disk = json_of(f"r1_rule_run/{SIDECAR}")
    ok(isinstance(on_disk, dict), "the checkpoint is not a JSON object")
    eq(sorted(on_disk), EIGHT_KEYS, "checkpoint keys")
    eq(on_disk, expected, "the checkpoint the failed run left")
    eq(value_of(o["read_sidecar"], "read_sidecar"), expected, "read_sidecar(working_dir)")
    eq(value_of(o["sidecar_state"], "ledger.sidecar_state()"), expected, "ledger.sidecar_state()")

    returned = value_of(o["write_returned"], "write_sidecar")
    ok(isinstance(returned, str) and os.path.isabs(returned),
       f"write_sidecar returns an absolute path: {returned!r}")
    same_file(returned, f"r1_rule_write/{SIDECAR}", "write_sidecar returns the checkpoint's path")
    eq(json_of(f"r1_rule_write/{SIDECAR}"), expected, "what write_sidecar put on disk")


def judge_r1_scope(o):
    eq(o["statuses"], STATUSES, "LEDGER_STATUSES")
    contents = SPEC["scope_contents"]
    rows = fixture_spec.alternating(seeder(), partner(), contents)
    log_bytes = fixture_spec.log_text(rows).encode()
    responses = len(contents) - 1
    last = author_of_line(responses)

    # No checkpoint: the log alone, and reading it wrote nothing.
    eq(o["adopted_status"], "adopted", "log-only status")
    eq(o["adopted_responses"], responses, "log-only responses")
    eq(listing("r1_scope_adopted"), [LOG], "load_ledger wrote to the directory")
    eq(read_bytes(f"r1_scope_adopted/{LOG}"), log_bytes, "the log after a log-only load")

    # A checkpoint that agrees on the two compared keys and lies about the rest.
    name = o["planted_name"]
    plain_name(name, "r1.scope")
    lies = SPEC["scope_lies"]
    planted = json.loads(o["planted_text"])
    eq([planted.get("responses"), planted.get("last_author")], [responses, last],
       "the planted checkpoint agrees on responses and last_author")
    eq({k: planted.get(k) for k in lies}, lies, "the planted checkpoint carries this run's lies")

    v = o["agreeing"]
    ok("error" not in v, f"loading beside an agreeing checkpoint: {v.get('error')}")
    eq(v["status"], "verified", "status beside an agreeing checkpoint")
    eq(v["turns"], len(contents), "turns come from the log, not the checkpoint")
    eq(v["responses"], responses, "responses from the log")
    eq(v["last_author"], last, "last_author from the log")
    eq(v["next_speaker"], other(last), "next_speaker from the log, not the checkpoint")
    eq(v["interleave_faults"], 0, "interleave_faults from the log")
    is_false(v["completed"], "completed from the log")
    eq(v["completion_reason"], "open", "completion_reason from the log")

    eq(listing("r1_scope_verified"), sorted([LOG, name]), "load_ledger wrote to the directory")
    eq(text_of(f"r1_scope_verified/{name}"), o["planted_text"], "the checkpoint was rewritten on load")
    eq(read_bytes(f"r1_scope_verified/{LOG}"), log_bytes, "the log was rewritten to agree with the checkpoint")

    raised_named(o["fresh_run_raises"], "Boom", "fresh run dies on its first call")
    eq(o["fresh_status"], "created", "a fresh run's ledger status")


def judge_r1_failure_behavior(o):
    ok(o["desync_mro"] is not None, "TurnLedgerDesyncError is not exported")
    ok(o["base_mro"] is not None, "TurnLedgerError is not exported")
    ok("TurnLedgerError" in o["desync_mro"], "TurnLedgerDesyncError subclasses TurnLedgerError")
    ok("RuntimeError" in o["base_mro"], "TurnLedgerError subclasses RuntimeError")

    contents = SPEC["fail_contents"]
    responses = len(contents) - 1
    last = author_of_line(responses)
    name = o["planted_name"]
    plain_name(name, "r1.failure_behavior")

    eq(o["absent_status"], "adopted", "absent checkpoint")
    eq(o["unreadable_status"], "adopted", "unreadable checkpoint")
    ok(o["old_moved"], "could not plant an older-version checkpoint: the build records no "
                       "integer beside the ledger's own fields")
    eq(o["oldversion_status"], "adopted", "older-version checkpoint")
    eq(o["agree_status"], "verified", "agreeing checkpoint")

    recorded = SPEC["fail_recorded_responses"]
    dr = o["desync_responses"]
    raised_named(dr, "TurnLedgerDesyncError", "response-count mismatch")
    eq(dr.get("log_responses"), responses, "log_responses")
    eq(dr.get("recorded_responses"), recorded, "recorded_responses")
    eq(dr.get("log_last_author"), last, "log_last_author")
    eq(dr.get("recorded_last_author"), last, "recorded_last_author")
    same_file(dr.get("path"), f"r1_fail/{name}", "error.path is the checkpoint")
    eq(dr.get("str"),
       f"{dr.get('path')} records {recorded} response(s) last authored by {last!r}, "
       f"the log holds {responses} last authored by {last!r}", "desync message")

    da = o["desync_author"]
    raised_named(da, "TurnLedgerDesyncError", "last-author mismatch")
    eq(da.get("log_last_author"), last, "author mismatch log_last_author")
    eq(da.get("recorded_last_author"), other(last), "author mismatch recorded_last_author")
    eq(da.get("log_responses"), responses, "author mismatch log_responses")
    eq(da.get("recorded_responses"), responses, "author mismatch recorded_responses")

    raised_named(o["run_raises"], "TurnLedgerDesyncError", "desync raised on the load path")
    eq(o["run_calls"], [], "a request was issued before the desync was raised")
    eq(len(log_rows("r1_fail")), len(contents), "a line was appended before the desync was raised")


def judge_r1_observability(o):
    # ---- the first write --------------------------------------------------
    raised_named(o["opening_run_raises"], "Boom", "opening run dies on its first call")
    ok(exists(f"r1_obs_opening/{SIDECAR}"),
       f"the seed line was not checkpointed before the first request: the directory "
       f"held {listing('r1_obs_opening')}")
    opening = spelled(open_state(0))
    raw = read_bytes(f"r1_obs_opening/{SIDECAR}")
    eq(raw.decode("utf-8", errors="replace"), opening, "the first checkpoint's spelling")
    eq(len(raw), len(opening.encode()), "the first checkpoint's size in bytes")

    # ---- the last write ---------------------------------------------------
    k = len(SPEC["obs_done_replies"])
    last = author_of_line(k)
    done_state = {"version": LEDGER_VERSION, "responses": k, "turns": k + 1, "last_author": last,
                  "next_speaker": None, "interleave_faults": 0, "completed": True,
                  "completion_reason": "agent_signal"}
    eq(o["done_run"].get("raised"), False, f"the finished run raised: {o['done_run'].get('str', '')[:200]}")
    eq(len(log_rows("r1_obs_done")), k + 1, "lines in the finished log")
    raw = read_bytes(f"r1_obs_done/{SIDECAR}")
    eq(raw.decode("utf-8", errors="replace"), spelled(done_state), "the last checkpoint's spelling")
    eq(len(raw), len(spelled(done_state).encode()), "the last checkpoint's size in bytes")
    eq(value_of(o["done_read_sidecar"], "read_sidecar"), done_state, "read_sidecar after the run")

    # ---- a log truncated behind the checkpoint's back ---------------------
    m = SPEC["obs_truncate_to"]
    sr = o["stale_raises"]
    raised_named(sr, "TurnLedgerDesyncError", "a truncated log beside a stale checkpoint")
    same_file(sr.get("path"), f"r1_obs_stale/{SIDECAR}", "stale error.path")
    eq(sr.get("log_responses"), m - 1, "stale log_responses")
    eq(sr.get("recorded_responses"), k, "stale recorded_responses")
    eq(sr.get("log_last_author"), author_of_line(m - 1), "stale log_last_author")
    eq(sr.get("recorded_last_author"), last, "stale recorded_last_author")
    eq(o["stale_calls"], [], "a stale checkpoint issued a request")
    eq(len(log_rows("r1_obs_stale")), m, "a stale checkpoint appended to the log")

    # ---- the same log with no checkpoint ----------------------------------
    eq(o["resume_run"].get("raised"), False, f"the resume raised: {o['resume_run'].get('str', '')[:200]}")
    eq(o["resume_status"], "adopted", "no checkpoint -> adopted")
    eq(o["resume_calls"], [[author_of_line(m), m - 1]], "the resume asks exactly one")
    eq(len(log_rows("r1_obs_resume")), m + 1, "the resume completes the log")

    # ---- an older-version checkpoint --------------------------------------
    plain_name(o["older_planted_name"], "r1.observability")
    ok(o["older_moved"], "could not plant an older-version checkpoint: the build records no "
                         "integer beside the ledger's own fields")
    eq(o["older_status"], "adopted", "older-version checkpoint -> adopted")


# ---------------------------------------------------------------------------
# r2 — the default completion signal
# ---------------------------------------------------------------------------
def require_token(o):
    """The old `require_feature`: the stock agent completes on THE token.

    The worker found its token in the submission (the constant, or a literal
    `is_completed` completes on); the candidate lists were rendered with it, so
    they only mean something if it is the token the requirement names.
    """
    ok(o.get("token") is not None,
       "Agent.is_completed's default sentinel match is not implemented: no token it completes on")
    eq(o["token"], SENTINEL, "the token Agent.is_completed completes on")


def outcomes_match(recipes, got, msg):
    ok(isinstance(got, list), f"{msg}: no outcomes recorded")
    eq(len(got), len(recipes), f"{msg}: outcome count")
    wrong = []
    for i, (recipe, answer) in enumerate(zip(recipes, got)):
        value = fixture_spec.render(recipe, SENTINEL)
        want = completes(value)
        if answer is not want:
            wrong.append(f"#{i} {recipe[0]} {value!r}: got {answer!r}, want {want}")
    ok(not wrong, f"{msg}: {len(wrong)} of {len(recipes)} wrong — " + "; ".join(wrong[:6]))


def judge_r2_rule(o):
    eq(o["completion_sentinel"], SENTINEL, "COMPLETION_SENTINEL")
    defined("COMPLETION_SENTINEL", SENTINEL)
    require_token(o)
    outcomes_match(SPEC["r2_rule"], o["outcomes"], "a reply that ends with the token completes")


def judge_r2_scope(o):
    require_token(o)
    outcomes_match(SPEC["r2_scope"], o["outcomes"],
                   "case-sensitive, suffix-only, blind to trailing whitespace")


def judge_r2_failure_behavior(o):
    require_token(o)
    outcomes_match(SPEC["r2_fail"], o["outcomes"], "a non-str reply answers False")


def judge_r2_observability(o):
    require_token(o)
    k = len(SPEC["r2_obs_replies"]) + 1
    last = f"{SPEC['r2_obs_last_text']} {SENTINEL}"
    eq(o["n_calls"], k, "calls before the token ended the conversation")
    rows = log_rows("r2_obs")
    eq(len(rows), k + 1, "log lines")
    eq(rows[-1], (author_of_line(k), last), "the log's last line is the token-bearing reply")
    eq(o["num_responses"], k, "num_responses")
    eq(o["ledger_responses"], k, "ledger responses")
    eq(o["completion_reason"], "agent_signal", "completion_reason")
    is_true(o["completed"], "ledger completed")
    eq(o["n_rows"], k + 1, "dataset rows")
    eq(o["last_content"], last, "the dataset's last row")
    eq(o["last_role"], author_of_line(k), "the dataset's last role")


JUDGES = {
    "test_open::test_open_feature__the_seed_is_logged_and_max_length_budgets_generated_responses": judge_open,
    "test_r1::test_rule__checkpoint_contract": judge_r1_rule,
    "test_r1::test_scope__loading_and_authority": judge_r1_scope,
    "test_r1::test_failure_behavior__verification_arms": judge_r1_failure_behavior,
    "test_r1::test_observability__checkpoint_on_disk": judge_r1_observability,
    "test_r2::test_rule__completion_signal": judge_r2_rule,
    "test_r2::test_scope__matching_discipline": judge_r2_scope,
    "test_r2::test_failure_behavior__non_text_replies": judge_r2_failure_behavior,
    "test_r2::test_observability__final_turn_accounting": judge_r2_observability,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g7_agent_turn_ledger" '
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
    global SPEC, ARTIFACTS
    SPEC = fixture_spec.derive(seed)
    ARTIFACTS = pathlib.Path(artifacts)

    try:
        observations = json.loads(judge_io.read_text(obs_path))
    except (OSError, ValueError) as exc:
        observations = {}
        print(f"judge: cannot read observations: {exc}", file=sys.stderr)
    if not isinstance(observations, dict):
        observations = {}

    results = []
    for node, judge in JUDGES.items():
        classname, name = node.split("::", 1)
        probe = observations.get(node)
        if not isinstance(probe, dict):
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
