"""g1 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote, the directories the probe's scenarios
actually ran in, and the cloned source text; writes a `junit.xml` whose
`classname`/`name` are the current suite's node ids — so `score.py` folds them
into the identical fact keys and `test.sh`/`score.py` are unchanged.

WHY THIS FILE NO LONGER HOLDS THE ANSWERS AS LITERALS. The split moved the
verdict out of the process that runs agent code. It left the worker AUTHORING
the values the verdict is computed from, and with a fixed fixture those values
never changed — while g1's are published in the world the agent is told to read.
A pristine tree plus one import-time `atexit` hook that rewrote
`observations.json` scored reward 1.0 on every fact. Three things close that:

  * **the inputs move every run.** `fixture_spec.derive(seed)` re-draws prompts,
    row counts and limits from the seed root picked, and this file recomputes
    what the answers must be for THOSE inputs — so there is nothing to memorise
    and nothing in the corpus to copy. What the seed stops is REPLAY, not
    derivation: curator is itself the request shape, so a worker that wants the
    row sizes can compute them (measured — byte-identical to this file's
    prices). Row sizes are priced HERE anyway, because a judge that reads its
    inputs from the worker is grading the worker's arithmetic rather than the
    run's.
  * **the directories are read here.** "The sweep ran", "the failed run left the
    place alone", "the bystanders were not touched" used to be booleans the
    worker computed. They are now this process opening the directory the run
    used and comparing it against the inputs it planted.
  * **the constants are read out of the source.** `PLAN_FILE_NAME`, the format
    version and the 512 cap cannot be re-drawn — they ARE the requirement — so
    they are checked against the module text as well as the run, and a tree that
    reports the right number without defining it fails.

The residual, stated plainly: a submission that IMPLEMENTS the rule inside a
forged hook still passes, because it has then done the work. What is gone is
passing by repeating values that were knowable in advance.

Each fact's meaning is stated where it is graded: `judge_open` and
the `judge_r1_*`/`judge_r2_*` functions below, one `ok(...)` message per
requirement, and `JUDGES` maps each to the node id `score.py` folds.
"""
from __future__ import annotations

import ast
import hashlib
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

MODEL = "gpt-4o-mini"

# The answers that cannot be re-drawn, because they are the requirement itself.
PLAN_FILE_NAME = "batch_plan.json"
PLAN_FORMAT_VERSION = 1
MAX_BATCHES_PER_PLAN = 512
DOC_KEYS = ["plan_format_version", "plan_id", "limits", "num_batches", "num_requests",
            "num_bytes", "batches"]
BATCH_KEYS = ["index", "start_idx", "end_idx", "num_requests", "num_bytes"]

PLANNER = ["bespokelabs/curator/request_processor/batch_payload_planner.py",
           "bespokelabs/curator/request_processor/batch_payload_planner/__init__.py"]

# The two files the ticket edits, relative to a curator package root. The
# preservation constraints below are about code INSIDE them, which is why a
# whole-file `protected_files` comparison cannot express any of it.
BASE_PROCESSOR = "request_processor/base_request_processor.py"
BATCH_PROCESSOR = "request_processor/batch/base_batch_request_processor.py"
BATCH_DIR = "request_processor/batch"
LIMIT_PROPERTIES = ("max_requests_per_batch", "max_bytes_per_batch")

# "No network, no clients, no sleeps" (instruction.md:98), as the planner
# module's import list. `aiofiles` used to be in here as "file IO the ticket
# does not give it" — which is a rule instruction.md does not state, so a
# correct planner that happened to import it failed open_feature on a
# requirement nobody wrote down. `time` went the same way: the ticket bans
# sleeping, not the module sleep lives in, and `time.monotonic` in a pure
# planner breaks nothing. The sleep itself is caught where it is called
# (`_sleeps`), which is the rule as written.
BANNED_IMPORTS = {"asyncio", "socket", "select", "requests", "aiohttp", "httpx",
                  "urllib", "urllib3", "openai", "anthropic", "litellm"}

UNBOUNDED_BYTES = 1_000_000

# Every read of an agent-influenced path goes through `judge_io` (O_NOFOLLOW,
# regular file, 8 MiB cap). The worker owns the artifacts tree, so
# `requests_0.jsonl` can be a symlink by the time THIS process (root) opens it —
# and the bytes it reads go into a mismatch message, which junit.xml and then
# ctrf.json carry out of the run. /tests/task.json is the answer key, so an
# unguarded read publishes it. The cap is the other half: a multi-gigabyte
# artifact cannot make the verifier overrun its budget, which scores like a
# broken harness. What is g1's own, and stays here, is that one file name comes
# from the WORKER (`o["plan_file_name"]`) and the scenario directories are the
# worker's too: see `text_of` and `adir`.

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


def has(surface, name, what="module"):
    ok(name in surface, f"{what} does not export {name}; it has {surface}")


def raised(info, *, mro=None, mro_absent=None, string=None, attrs=None, msg=""):
    ok(info.get("raised"), f"{msg}: expected an exception, none raised")
    for name in (mro or []):
        ok(name in info.get("mro", []), f"{msg}: {name} not in {info.get('mro')}")
    for name in (mro_absent or []):
        ok(name not in info.get("mro", []), f"{msg}: {name} unexpectedly in {info.get('mro')}")
    for attr, value in (attrs or {}).items():
        eq(info.get(attr), value, f"{msg}: {attr}")
    if string is not None:
        eq(info.get("str"), string, f"{msg}: message")


def check_cover(plan, n_rows, msg="cover"):
    """Contiguous, ordered and exhaustive, over the tuples the probe recorded
    ([index, start, end, num_requests, num_bytes])."""
    ok(bool(plan), f"{msg}: the plan is empty")
    eq(plan[0][1], 0, f"{msg}: does not start at row 0")
    eq(plan[-1][2], n_rows, f"{msg}: does not reach row {n_rows}")
    for i, t in enumerate(plan):
        eq(t[0], i, f"{msg}: not indexed 0..n-1")
        eq(t[3], t[2] - t[1], f"{msg}: bad span {t}")
    for earlier, later in zip(plan, plan[1:]):
        eq(earlier[2], later[1], f"{msg}: not a contiguous cover")


# ---------------------------------------------------------------------------
# the oracle: what this run's inputs should produce
# ---------------------------------------------------------------------------
def api_request(idx: int, prompt: str) -> dict:
    """The provider dict curator serialises one row into.

    The judge prices the rows from this, rather than reading a price the worker
    reports. Not because the shape is a secret — curator builds this same dict,
    so any worker can derive it — but because a judge that takes its inputs from
    the process it is grading is checking that process's arithmetic instead of
    what the run actually wrote.
    """
    return {"custom_id": str(idx), "method": "POST", "url": "/v1/chat/completions",
            "body": {"model": MODEL, "messages": [{"role": "user", "content": prompt}]}}


def prompt_of(idx: int) -> str:
    return f"{SPEC['prefix']}{idx}"


def row_size(idx: int) -> int:
    return len(json.dumps(api_request(idx, prompt_of(idx))).encode())


def row_sizes(n: int) -> list:
    return [row_size(i) for i in range(n)]


def pack(sizes, max_requests, max_bytes) -> list:
    """The greedy forward fill both limits are inclusive of, as [index, start,
    end, num_requests, num_bytes] — the shape `probe_support.tuples` records.

    A batch's byte size counts the n-1 newline separators `"\\n".join` adds.
    """
    plan, start, current = [], 0, []

    def close(end):
        plan.append([len(plan), start, end, len(current),
                     sum(current) + max(len(current) - 1, 0)])

    for idx, size in enumerate(sizes):
        nxt = current + [size]
        if current and (len(nxt) > max_requests or sum(nxt) + len(nxt) - 1 > max_bytes):
            close(idx)
            start, current = idx, [size]
        else:
            current = nxt
    if current:
        close(len(sizes))
    return plan


def fingerprint(plan) -> str:
    canonical = ";".join(f"{t[1]}-{t[2]}:{t[4]}" for t in plan)
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def document(plan, limits_asdict) -> dict:
    return {
        "plan_format_version": PLAN_FORMAT_VERSION,
        "plan_id": fingerprint(plan),
        "limits": limits_asdict,
        "num_batches": len(plan),
        "num_requests": sum(t[3] for t in plan),
        "num_bytes": sum(t[4] for t in plan),
        "batches": [dict(zip(BATCH_KEYS, t)) for t in plan],
    }


def dataset_plan(n=None, max_requests=None, max_bytes=None) -> list:
    """The plan this run's main `"auto"` fixture must produce."""
    n = SPEC["rows"] if n is None else n
    return pack(row_sizes(n),
                SPEC["max_requests"] if max_requests is None else max_requests,
                SPEC["max_bytes"] if max_bytes is None else max_bytes)


# ---------------------------------------------------------------------------
# reading the directories the scenarios ran in
# ---------------------------------------------------------------------------
def adir(name: str) -> pathlib.Path:
    path = ARTIFACTS / name
    ok(not path.is_symlink(), f"the {name} scenario directory is a symlink")
    ok(path.is_dir(), f"the {name} scenario left no working directory behind")
    return path


def listing(name: str) -> list:
    return sorted(p.name for p in adir(name).iterdir())


def text_of(name: str, filename: str) -> str:
    """One artifact file, read the way root must read a file a worker owns.

    `filename` is sometimes the worker's own word (`o["plan_file_name"]`), so it
    has to be a plain name in this scenario's directory and nothing else — a
    name of `../../../tests/task.json` would otherwise make the root judge quote
    the answer key into its own failure message. The read itself is judge_io's:
    O_NOFOLLOW, regular file, size-capped.
    """
    ok(isinstance(filename, str) and filename not in ("", ".", "..")
       and "/" not in filename and "\0" not in filename,
       f"{name}/{filename!r} is not a plain file name in the scenario directory")
    path = adir(name) / filename
    try:
        return judge_io.read_text(path)
    except FileNotFoundError:
        raise Fail(f"{name}/{filename} is missing; the directory holds {listing(name)}")
    except OSError as exc:
        raise Fail(f"{name}/{filename} is not a file this judge will read: {exc}")


def json_of(name: str, filename: str):
    return json.loads(text_of(name, filename))


def lines_in(name: str, filename: str) -> list:
    return [json.loads(line) for line in text_of(name, filename).splitlines() if line.strip()]


def rows_in(name: str, filename: str) -> list:
    """The dataset row indices one request file holds — and a check that the
    file is THIS run's.

    Indices alone are seed-independent: rows 0..n-1 look the same in every run,
    so a directory captured from an earlier run passes an index check. The
    prompt text carries the run's token, and that is what makes a planted
    directory fail.
    """
    rows = []
    for line in lines_in(name, filename):
        idx = line["original_row_idx"]
        want = prompt_of(idx)
        got = line.get("original_row", {}).get("prompt")
        eq(got, want, f"{name}/{filename} row {idx} is not from this run")
        rows.append(idx)
    return rows


def numbered(name: str, stem: str, suffix: str) -> list:
    return sorted(p.name for p in adir(name).iterdir()
                  if p.name.startswith(stem) and p.name.endswith(suffix))


def request_files(n: int) -> list:
    return [f"requests_{i}.jsonl" for i in range(n)]


def metadata_files(n: int) -> list:
    return [f"metadata_{i}.json" for i in range(n)]


def planted_names() -> list:
    """Everything `prepopulate` put in a working directory, this run."""
    return request_files(SPEC["prepop_n"]) + metadata_files(SPEC["prepop_n"])


def require_swept(name: str):
    """The gate: this run really did sweep, so "left alone" means something.

    A tree that never implements the sweep leaves the whole stale tail in place,
    and every "nothing was removed" check below would pass on it for the wrong
    reason. The old version asked the worker for this as a boolean.
    """
    tail = f"requests_{SPEC['prepop_n'] - 1}.jsonl"
    ok(tail not in listing(name),
       f'the "auto" branch\'s sweep of stale request files is not implemented '
       f"({name} still holds {tail})")


# ---------------------------------------------------------------------------
# reading the submission's source — for the constants that cannot be re-drawn
# ---------------------------------------------------------------------------
def _module_source(candidates) -> str:
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    for rel in candidates:
        path = root / rel
        if path.is_file():
            try:
                return judge_io.read_text(path)
            except OSError as exc:
                raise Fail(f"{rel} is not a file this judge will read: {exc}")
    raise Fail(f"none of {candidates} exists in the submission")


def _assigned(src: str, name: str):
    """The value the module assigns to a module-level constant.

    The LAST assignment, not the first: `PLAN_FILE_NAME = "batch_plan.json"`
    followed by `PLAN_FILE_NAME = "whatever"` binds the second one, and a check
    that reads the first is a check a duplicate defeats.
    """
    found = None
    for node in _tree(src).body:
        targets = node.targets if isinstance(node, ast.Assign) else (
            [node.target] if isinstance(node, ast.AnnAssign) and node.value is not None else [])
        for target in targets:
            if isinstance(target, ast.Name) and target.id == name:
                found = node.value
    if found is None:
        raise Fail(f"the planner module does not define {name}")
    try:
        return ast.literal_eval(found)
    except ValueError:
        raise Fail(f"{name} is not a literal in the module source")


def _field_default(src: str, classname: str, field: str):
    """A dataclass field's default, following one level of constant indirection.

    The class the module binds (see `_find_class`), and that class's last
    annotation of the field — the one a dataclass ends up with.
    """
    node = _find_class(_tree(src), classname)
    ok(node is not None, f"the planner module does not define {classname}")
    found = None
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) \
                and stmt.target.id == field and stmt.value is not None:
            found = stmt.value
    if found is None:
        raise Fail(f"{classname}.{field} has no default in the module source")
    if isinstance(found, ast.Name):
        return _assigned(src, found.id)
    try:
        return ast.literal_eval(found)
    except ValueError:
        raise Fail(f"{classname}.{field} has no literal default")


# ---------------------------------------------------------------------------
# the ticket's preservation constraints, read against the pristine tree
#
# instruction.md keeps four things as they are: `create_batch_file`'s and
# `create_request_files`'s signatures (:69, :78), the explicit-integer branch's
# behaviour (:87-89), and `max_requests_per_batch` / `max_bytes_per_batch` and
# `acreate_request_file` "reused as-is" (:93-94). None of them is a whole file —
# they live inside the two modules the ticket tells the agent to edit — so
# `protected_files` cannot say any of it, and the graded run cannot SEE most of
# it: the probe patches both limit properties (that is how a 5-row dataset
# exercises a 200 MB limit), so their real implementations never run. A rewritten
# `max_bytes_per_batch` was invisible to every behavioural check.
#
# So they are checked here, against the pristine copy, AST-identical with
# docstrings stripped: formatting and a reworded docstring are not a
# modification, a changed expression is. The explicit-integer branch is compared
# the same way (`_check_explicit_arm_preserved`), and is the one of the four
# whose behaviour the graded scenarios CAN see — it is graded both ways.
# ---------------------------------------------------------------------------
def _baseline_root() -> pathlib.Path:
    """The pristine curator package, or a Fail that says it is not readable.

    `run_suites.stage_baseline` copies it somewhere the grading uids can read
    and names it in the environment; the world image's own copy under
    /opt/world-state is the same bytes and this process is root, so it stands in
    when staging failed. With NEITHER, the check fails the fact — a "reused
    as-is" check that cannot see the original must never pass blind.
    """
    for root in (os.environ.get("CURATOR_BASELINE_DIR", ""),
                 "/opt/world-state/input/curator/src/bespokelabs/curator"):
        if root and (pathlib.Path(root) / "llm" / "llm.py").is_file():
            return pathlib.Path(root)
    raise Fail("no pristine copy of curator is readable "
               f"(CURATOR_BASELINE_DIR={os.environ.get('CURATOR_BASELINE_DIR')!r}), "
               "so the ticket's \"reused as-is\" constraints cannot be checked")


def _baseline_source(rel: str) -> str:
    path = _baseline_root() / rel
    if not path.is_file():
        raise Fail(f"fixture drift: the pristine tree has no {rel}")
    try:
        return judge_io.read_text(path)
    except OSError as exc:
        raise Fail(f"the pristine {rel} is not readable: {exc}")


def _submission_source(rel: str) -> str:
    return _module_source([f"bespokelabs/curator/{rel}", f"src/bespokelabs/curator/{rel}"])


def _strip_docstrings(node):
    """The same tree without its docstrings, so a reworded comment is not a diff."""
    for child in ast.walk(node):
        if not isinstance(child, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(child, "body", [])
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            child.body = body[1:] or [ast.Pass()]
    return node


# --- resolving the definition the interpreter actually binds ----------------
#
# Every check below asks "is this still the code the world shipped?", and the
# answer means nothing unless it reads the definition Python binds. The first
# version of these helpers took the FIRST `def`/`class` of the name in
# `ast.walk` order, which is the opposite of what Python does, and that was a
# full bypass of the reward: measured, oracle + `max_bytes_per_batch` rewritten
# to `return 10 ** 12` with a pristine copy duplicated above it + the explicit
# arm rewritten with the pristine statements parked under `while False:` scored
# 11/11. A decoy `class BaseRequestProcessor` placed earlier in the module did
# the same to both signature checks, `acreate_request_file` and `frozen=True`.
#
# So, three rules, and they are why nothing here calls `ast.walk` to find a
# definition:
#   * module level only — a class nested in a function or another class is not
#     what `from … import X` binds;
#   * last definition wins, as two `def`s of one name in one namespace do;
#   * a name defined twice is REFUSED rather than resolved. Nothing in this
#     ticket has a reason to define one name twice, and a duplicate is the
#     vehicle every one of those bypasses used.
def _tree(src: str) -> ast.Module:
    try:
        return ast.parse(src)
    except SyntaxError as exc:
        raise Fail(f"the submission does not parse: {exc}")


def _effective(nodes: list, what: str):
    """The definition that binds, or a Fail if the name is defined twice."""
    if len(nodes) > 1:
        raise Fail(f"{what} is defined {len(nodes)} times in one namespace; Python binds the "
                   "last one, so a duplicate definition is not the implementation the world "
                   "shipped")
    return nodes[-1] if nodes else None


def _classes(tree: ast.Module) -> list:
    """The module's own classes, refusing a class name defined twice."""
    nodes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    names = [node.name for node in nodes]
    dupes = sorted({name for name in names if names.count(name) > 1})
    if dupes:
        raise Fail(f"{', '.join(dupes)} is defined more than once at module level; the later "
                   "definition is the one Python binds, so a decoy class cannot stand in for it")
    return nodes


def _find_class(tree: ast.Module, name: str):
    return _effective([node for node in _classes(tree) if node.name == name], f"class {name}")


def _methods(cls: ast.ClassDef, name: str) -> list:
    return [stmt for stmt in cls.body
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == name]


def _find_def(tree: ast.Module, name: str, classname: str):
    """`classname.name`, both resolved to what the module binds."""
    cls = _find_class(tree, classname)
    if cls is None:
        return None
    return _effective(_methods(cls, name), f"{classname}.{name}")


def _find_function(tree: ast.Module, name: str):
    """A module-level `def name`, for a helper the explicit arm calls."""
    return _effective([node for node in tree.body
                       if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                       and node.name == name], f"{name}()")


def _defining_classes(tree: ast.Module, name: str) -> dict:
    """{class name: the def it binds} for every class of the module defining `name`."""
    found = {}
    for cls in _classes(tree):
        node = _effective(_methods(cls, name), f"{cls.name}.{name}")
        if node is not None:
            found[cls.name] = node
    return found


def _signature(node, *, returns: bool) -> dict:
    """Parameter names, order, annotations and defaults — never source text.

    Text would fail a submission for a line break, and the ticket explicitly
    allows one annotation to change (`create_batch_file` now returns `bytes`),
    which is why the return annotation is compared only where it is not allowed
    to move.
    """
    args = node.args
    positional = list(args.posonlyargs) + list(args.args)
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)

    def one(arg, default):
        return {"name": arg.arg,
                "annotation": ast.dump(arg.annotation) if arg.annotation else None,
                "default": ast.dump(default) if default is not None else None}

    sig = {"positional": [one(a, d) for a, d in zip(positional, defaults)],
           "positional_only": len(args.posonlyargs),
           "vararg": args.vararg.arg if args.vararg else None,
           "keyword_only": [one(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults)],
           "kwarg": args.kwarg.arg if args.kwarg else None}
    if returns:
        sig["returns"] = ast.dump(node.returns) if node.returns else None
    return sig


def _identical(rel: str, name: str, classname: str, what: str) -> None:
    """One method is the pristine one, AST-identical with docstrings stripped.

    Both sides are the definition the module binds, and the docstrings come off
    the whole tree before either is dumped.
    """
    pristine = _find_def(_strip_docstrings(_tree(_baseline_source(rel))), name, classname)
    ok(pristine is not None, f"fixture drift: the pristine {rel} has no {classname}.{name}")
    mine = _find_def(_strip_docstrings(_tree(_submission_source(rel))), name, classname)
    ok(mine is not None, f"{classname}.{name} is gone from {rel}, and the ticket {what}")
    ok(ast.dump(mine) == ast.dump(pristine),
       f"{classname}.{name} in {rel} is not the implementation the world shipped, "
       f"and the ticket {what}")


def _check_preserved_signature(rel: str, classname: str, name: str, *, returns: bool) -> None:
    pristine = _find_def(_tree(_baseline_source(rel)), name, classname)
    ok(pristine is not None, f"fixture drift: the pristine {rel} has no {classname}.{name}")
    mine = _find_def(_tree(_submission_source(rel)), name, classname)
    ok(mine is not None, f"{classname}.{name} is gone from {rel}; the ticket keeps its signature")
    eq(_signature(mine, returns=returns), _signature(pristine, returns=returns),
       f"{name}'s signature changed, and the ticket keeps it")


def _auto_arm(node) -> bool:
    """`batch_size == "auto"` — the arm of the `if` the ticket rewrites.

    The local name, not `self.config.batch_size`: the module tests that
    attribute too, in `_verify_existing_request_files`, and that `if` is not
    this one.
    """
    return (isinstance(node, ast.Compare) and len(node.ops) == 1
            and isinstance(node.ops[0], ast.Eq)
            and isinstance(node.left, ast.Name) and node.left.id == "batch_size"
            and isinstance(node.comparators[0], ast.Constant)
            and node.comparators[0].value == "auto")


def _explicit_arm(tree: ast.Module):
    """The `else:` of `if batch_size == "auto"`, in the arm's own place.

    Resolved, never searched: the class the module binds, the
    `create_request_files` that class binds, and the one `if` inside it that
    tests the local `batch_size` against `"auto"`. Two such `if`s with an else
    would make "the explicit arm" ambiguous, so that is a Fail, not a pick.
    """
    create = _find_def(tree, "create_request_files", "BaseRequestProcessor")
    if create is None:
        return None
    arms = [node for node in ast.walk(create)
            if isinstance(node, ast.If) and _auto_arm(node.test) and node.orelse]
    if len(arms) > 1:
        raise Fail(f'create_request_files tests batch_size == "auto" in {len(arms)} places '
                   "with an else arm, so which one the ticket preserves cannot be told apart")
    return arms[0].orelse if arms else None


def _called_helpers(stmts) -> tuple:
    """The helpers the live arm CALLS, in two buckets: methods, then functions.

    Call position, not mention. Collecting every `ast.Name` id and every
    `ast.Attribute` attr made "a helper the arm calls" mean "a helper whose name
    the arm happens to mention", and that is routable with nothing planted: park
    the pristine statements in an UNCALLED method named `join` and `os.path.join`
    already supplies the name. Measured on a violating arm that silently
    truncates past six files — invisible, because the fixture never draws more
    than six — 11/11, reward 1.0. Nine spellings of the same dodge passed
    (`join`, `path`, `incomplete_files`, `dataset`, `range` as methods; `join`,
    `incomplete_files`, `asyncio` as module-level functions).

    Two buckets because the two spellings resolve differently and crossing them
    reopens the hole: `self.<n>(...)` can only be the method that class binds,
    and a bare `<n>(...)` can only be a module-level function. `os.path.join(…)`
    is an `Attribute` on an `Attribute`, so it lands in neither.
    """
    methods, functions = [], []
    for stmt in stmts:
        for node in ast.walk(stmt):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name):
                functions.append(func.id)
            elif (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
                    and func.value.id == "self"):
                methods.append(func.attr)
    return methods, functions


def _holds_run(body, want) -> bool:
    """Does this statement list hold `want` as a contiguous run?"""
    return any([ast.dump(stmt) for stmt in body[i:i + len(want)]] == want
               for i in range(len(body) - len(want) + 1))


def _check_explicit_arm_preserved() -> None:
    """instruction.md:87-89, against the pristine tree.

    The clause is "the explicit-integer `batch_size` branch keeps its current
    behaviour **exactly**", and the reference patch obeys it by not touching it:
    its only hunk in this file rewrites the `"auto"` region. v20 enforced the
    clause behaviourally alone, over one drawn chunk size out of two, and the
    review of v20 named the gap precisely — an implementation fitted to the
    tested sizes passes a spot check. The fixture band is now ten wide (see
    `fixture_spec`), and the branch's own statements are compared with the
    pristine ones here.

    WHAT IS COMPARED, AND WHERE. The arm's four statements:
    `ceil(len(dataset) / batch_size)`, the two fixed-width name lists, and the
    `create_all_request_files` whose comprehension carries `if i in
    incomplete_files` — read in the arm's own place, the `orelse` of that `if`.

    IN PLACE, because "anywhere in the module" was routable. The first version
    searched every statement list in the file for a matching run and skipped
    only the ones a constant `if` excluded: `while False:`, `if not True:`,
    `if ():`, `for _ in []:` and a run sitting after a `return` are all just as
    dead and were all accepted, and `if False: self._legacy_arm` was enough to
    make an unreferenced helper look live. Measured: a behaviour-equivalent arm
    with renamed locals, plus the pristine statements parked under
    `while False:`, scored 11/11. Asking WHERE the statements are, instead of
    whether they exist somewhere, is what has no alternative spelling.

    The one refactor that still passes is the one the ticket allows: the four
    statements lifted verbatim into a helper — resolved by name, its body
    holding them as a contiguous run — that this arm CALLS, in call position
    (`_called_helpers`, which is where the mention-versus-call hole was). That
    preserves both the statements and the behaviour, and failing it would
    enforce a rule instruction.md does not state. Parking them deeper inside such a helper
    (under an `if`, a loop, another function) is not accepted: that is the
    dead-code dodge again, one level down. The `"auto"` arm of the same `if` is
    compared with nothing — it is the half the ticket asks to be rewritten.
    """
    pristine = _explicit_arm(_strip_docstrings(_tree(_baseline_source(BASE_PROCESSOR))))
    ok(pristine is not None,
       "fixture drift: the pristine create_request_files has no explicit-integer arm")
    want = [ast.dump(stmt) for stmt in pristine]

    tree = _strip_docstrings(_tree(_submission_source(BASE_PROCESSOR)))
    arm = _explicit_arm(tree)
    ok(arm is not None,
       "create_request_files has no explicit-integer arm (no else on its "
       'batch_size == "auto" test), and the ticket keeps that branch\'s behaviour exactly')
    if [ast.dump(stmt) for stmt in arm] == want:
        return
    methods, functions = _called_helpers(arm)
    candidates = ([(name, "method") for name in methods]
                  + [(name, "function") for name in functions])
    for name, kind in candidates:
        # A name that resolves to nothing — or to a duplicate, which is another
        # check's business and not this loop's — is skipped rather than reported
        # as the arm's defect. The two kinds are never tried against each other:
        # `self.<n>(...)` must be the method, a bare `<n>(...)` the function.
        try:
            helper = (_find_def(tree, name, "BaseRequestProcessor") if kind == "method"
                      else _find_function(tree, name))
        except Fail:
            continue
        if helper is not None and _holds_run(helper.body, want):
            return
    raise Fail("the explicit-integer batch_size branch is not the one the world shipped "
               "(its ceil(len(dataset) / batch_size) numbering and its `if i in "
               "incomplete_files` filter, in the arm itself or in a helper the arm calls), "
               "and the ticket keeps that branch's behaviour exactly")


def _check_limit_properties() -> None:
    """Both provider limits, in every batch module that defines one.

    The probe patches them on the class, so a rewritten limit never runs under
    the grader: source is the only witness there is.

    Named by CLASS, not "the first class that defines it". A rewritten limit in
    the class the provider actually uses, with a pristine copy in a decoy class
    above it, used to satisfy this: the pristine file says which class owns each
    property, and the submission's class of that name is the one compared.
    """
    root = _baseline_root()
    found = 0
    for path in sorted((root / BATCH_DIR).glob("*.py")):
        rel = f"{BATCH_DIR}/{path.name}"
        pristine = _tree(_baseline_source(rel))
        for prop in LIMIT_PROPERTIES:
            for classname in _defining_classes(pristine, prop):
                found += 1
                _identical(rel, prop, classname, "reuses it as-is")
    ok(found >= 2, f"fixture drift: the pristine tree defines {found} limit properties")


def _check_old_sizing_loop_gone() -> None:
    """Section 3's deletion: no `_get_optimal_batch_size`, no `while True`.

    A submission can drive the `"auto"` branch off the plan and leave the loop
    it replaced sitting in the file, where the next reader takes it for live
    code; every behavioural check passes on that.
    """
    src = _submission_source(BASE_PROCESSOR)
    for node in ast.walk(_tree(src)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_get_optimal_batch_size":
            raise Fail("base_request_processor.py still defines _get_optimal_batch_size; the ticket deletes it")
    create = _find_def(_tree(src), "create_request_files", "BaseRequestProcessor")
    ok(create is not None, "base_request_processor.py has no BaseRequestProcessor.create_request_files")
    for node in ast.walk(create):
        if isinstance(node, ast.While) and isinstance(node.test, ast.Constant) and node.test.value is True:
            raise Fail("create_request_files still holds the `while True` sizing loop; the ticket deletes it")


def _check_frozen_dataclasses() -> None:
    """`@dataclass(frozen=True)` on both, as the ticket writes them.

    A declaration, so it is read rather than provoked: nothing in the graded
    scenarios mutates a plan, so a mutable PlannedBatch behaves identically.
    """
    src = _module_source(PLANNER)
    for name in ("BatchLimits", "PlannedBatch"):
        node = _find_class(_tree(src), name)
        ok(node is not None, f"the planner module does not define {name}")
        frozen = False
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            spelling = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if spelling != "dataclass":
                continue
            frozen = frozen or any(kw.arg == "frozen" and isinstance(kw.value, ast.Constant)
                                   and kw.value.value is True for kw in decorator.keywords)
        ok(frozen, f"{name} is not a @dataclass(frozen=True), which is how the ticket declares it")


def _sleeps(node) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        spelling = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if spelling == "sleep":
            return True
    return False


def _check_no_network_clients_or_sleeps() -> None:
    """The planner is pure, and the three added methods do not sleep.

    "No network, no clients, no sleeps" is a constraint on what the ticket ADDS,
    so it is read off the new module and the new methods rather than off files
    that already import aiohttp and litellm for their own reasons.
    """
    src = _module_source(PLANNER)
    imported = set()
    for node in ast.walk(_tree(src)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module.split(".")[0])
    reached = sorted(imported & BANNED_IMPORTS)
    ok(not reached, f"the planner module imports {reached}; the ticket allows no network, "
                    "no clients and no sleeps")
    ok(not _sleeps(_tree(src)), "the planner module sleeps; the ticket allows no sleeps")

    batch_src = _submission_source(BATCH_PROCESSOR)
    for name in ("batch_limits", "measure_request_payload", "plan_request_batches"):
        node = _find_def(_tree(batch_src), name, "BaseBatchRequestProcessor")
        ok(node is not None, f"BaseBatchRequestProcessor does not define {name}")
        ok(not _sleeps(node), f"{name} sleeps; the ticket allows no sleeps")


# ---------------------------------------------------------------------------
# open feature — the whole stated surface, planner, files
# ---------------------------------------------------------------------------
REQUIRED_SURFACE = ["BatchLimits", "PlannedBatch", "payload_size_bytes", "payload_bytes",
                    "plan_batches", "BatchPayloadTooLargeError", "SingleRequestTooLargeError"]


def judge_open(o):
    for name in REQUIRED_SURFACE:
        has(o["surface"], name)

    # --- what the ticket keeps, and what it declares ------------------------
    # Source, not behaviour: the limit properties are patched in every scenario,
    # a frozen dataclass nothing mutates behaves like a mutable one, and a
    # deleted loop that was left behind still runs nothing.
    _check_preserved_signature(BATCH_PROCESSOR, "BaseBatchRequestProcessor", "create_batch_file",
                               returns=False)  # the ticket corrects `-> str` to `-> bytes`
    _check_preserved_signature(BASE_PROCESSOR, "BaseRequestProcessor", "create_request_files",
                               returns=True)
    _check_limit_properties()
    _identical(BASE_PROCESSOR, "acreate_request_file", "BaseRequestProcessor",
               'reuses it as-is, metadata body and all')
    _check_old_sizing_loop_gone()
    _check_frozen_dataclasses()
    _check_no_network_clients_or_sleeps()
    ok("ValueError" in o["btle_mro"], f"BatchPayloadTooLargeError does not subclass ValueError: {o['btle_mro']}")
    ok("BatchPayloadTooLargeError" in o["srtle_mro"],
       f"SingleRequestTooLargeError does not subclass BatchPayloadTooLargeError: {o['srtle_mro']}")
    eq(o["error_fields"], [SPEC["err_num_requests"], SPEC["err_size_bytes"], SPEC["err_limit_bytes"]],
       "the error carries the three numbers it was built with")

    # --- one row, serialised the way the provider wants it ------------------
    expected_request = api_request(0, prompt_of(0))
    eq(o["row_0_request"], expected_request, "the provider request for row 0")
    eq(o["payload_size_row0"], row_size(0), "payload_size_bytes is the UTF-8 length of json.dumps")
    eq(o["measure_generic"], o["payload_size_row0"], "measure_request_payload != payload_size_bytes")
    ok(SPEC["prefix"] in json.dumps(o["generic_dump"]),
       "the generic request does not carry this run's prompt")

    size = SPEC["unit_size"]
    eq(o["payload_bytes"], [0, size, 3 * size + 2], "payload_bytes counts the n-1 separators")

    # --- greedy forward fill, both limits inclusive, exhaustive spans -------
    per = SPEC["unit_per_batch"]
    unit_cap = per * size + per - 1
    eq(o["plan_empty"], [], "zero sizes plan zero batches")
    eq(o["plan_by_bytes"], pack([size] * SPEC["unit_rows"], 1000, unit_cap),
       f"{SPEC['unit_rows']} rows of {size} bytes under a {unit_cap}-byte budget")
    eq(o["plan_by_count"], pack([size] * SPEC["count_rows"], SPEC["count_per_batch"], UNBOUNDED_BYTES),
       f"{SPEC['count_rows']} rows at {SPEC['count_per_batch']} per batch")

    raised(o["raise_single"],
           mro=["SingleRequestTooLargeError", "BatchPayloadTooLargeError", "ValueError"],
           attrs={"row_idx": 1, "size_bytes": unit_cap + 1, "limit_bytes": unit_cap, "num_requests": 1},
           msg="a row over the byte budget on its own")

    eq(o["batch_limits"], [SPEC["echo_max_requests"], SPEC["echo_max_bytes"]],
       "batch_limits mirrors the two properties")

    # --- planning the dataset, and the files it writes ----------------------
    plan = dataset_plan()
    eq(o["plan_dataset"], plan, f"the plan of {SPEC['rows']} rows at {SPEC['max_requests']}/{SPEC['max_bytes']}")
    check_cover(o["plan_dataset"], SPEC["rows"])
    eq(o["result_rel"], request_files(len(plan)), "create_request_files result")

    # read the directory rather than ask what is in it
    for t in plan:
        eq(rows_in("open_run", f"requests_{t[0]}.jsonl"), list(range(t[1], t[2])),
           f"requests_{t[0]}.jsonl holds its planned rows")
        eq(json_of("open_run", f"metadata_{t[0]}.json")["num_jobs"], t[3],
           f"metadata_{t[0]}.json num_jobs")

    eq(o["empty_batch_file_len"], 0, "create_batch_file([]) is not empty")
    eq(o["built_sizes"], [t[4] for t in plan], "built file size == planned num_bytes")

    # create_batch_file raises the new error where it raised ValueError
    raised(o["raise_batch_file"],
           mro=["BatchPayloadTooLargeError", "ValueError"],
           attrs={"num_requests": 2, "size_bytes": row_size(0) + row_size(1) + 1,
                  "limit_bytes": SPEC["batch_file_limit"]},
           msg="create_batch_file on a batch over the byte limit")

    # every row measured exactly once, in index order — the plan's cuts can be
    # right while the rows behind them were priced twice or out of order
    eq(o["measured_row_order"], list(range(SPEC["rows"])),
       "the rows plan_request_batches measured, in the order it measured them")

    # --- row-level generation_params ----------------------------------------
    # Cut by count, so the spans are known without pricing a row that carries
    # generation params; the byte accounting is graded on the plain rows above.
    gp_expected = pack([1] * SPEC["gp_rows"], SPEC["gp_max_requests"], UNBOUNDED_BYTES)
    eq([t[:4] for t in o["gp_plan"]], [t[:4] for t in gp_expected], "the gen-params plan's spans")
    ok(all(t[4] > 0 for t in o["gp_plan"]), f"gen-params batches carry no bytes: {o['gp_plan']}")
    for t in gp_expected:
        eq(len(rows_in("open_gp", f"requests_{t[0]}.jsonl")), t[3],
           f"gen-params requests_{t[0]}.jsonl line count")

    eq(o["wide_basenames"], request_files(SPEC["wide_rows"]),
       "one file per planned batch, numeric order")

    eq(o["empty_plan"], [], "zero rows plans zero batches")
    eq(o["empty_create_result"], [], "zero rows writes no file")
    eq(o["empty_glob_requests"], [], "no stray request files")
    eq(o["empty_glob_metadata"], [], "no stray metadata files")

    # --- the explicit-integer branch is untouched ---------------------------
    # Its own dataset, and a chunk from a ten-wide band: `ceil(len(dataset) /
    # batch_size)` files of `batch_size` rows with whatever remainder the draw
    # left, which an implementation fitted to particular sizes cannot reproduce.
    chunk, n_rows = SPEC["explicit_batch_size"], SPEC["explicit_rows"]
    fixed_counts = [len(range(i, min(i + chunk, n_rows))) for i in range(0, n_rows, chunk)]
    eq(o["fixed_result_rel"], request_files(len(fixed_counts)), "explicit-integer result")
    for i, count in enumerate(fixed_counts):
        eq(len(rows_in("open_fixed", f"requests_{i}.jsonl")), count,
           f"explicit-integer requests_{i}.jsonl line count")

    # ...and it stays ceil(len(dataset) / batch_size) fixed-width files under a
    # byte budget no single row fits in: no resplit, and no planner call (which
    # would have raised under those limits rather than written anything)
    eq(o["fixed_planner_calls"], 0,
       "the explicit-integer branch called plan_request_batches; the ticket keeps it off the planner")
    ok(not o["fixed_bytes_raise"]["raised"],
       f"the explicit-integer branch now fails under a byte limit it used to ignore: "
       f"{o['fixed_bytes_raise'].get('mro')} {o['fixed_bytes_raise'].get('str')}")
    eq(numbered("open_fixed_bytes", "requests_", ".jsonl"), request_files(len(fixed_counts)),
       "explicit-integer numbering under a byte limit that cannot hold one row")
    for i, count in enumerate(fixed_counts):
        eq(len(rows_in("open_fixed_bytes", f"requests_{i}.jsonl")), count,
           f"explicit-integer requests_{i}.jsonl line count under a tight byte limit")

    # ...and its cache filter still holds: requests_0.jsonl was complete, so the
    # run left it exactly as it found it and wrote only the incomplete file
    eq(text_of("open_fixed_cache", "requests_0.jsonl"), SPEC["stale_request"] * chunk,
       "the explicit-integer branch rewrote a request file incomplete_files had excluded")
    eq(rows_in("open_fixed_cache", "requests_1.jsonl"), [chunk],
       "the explicit-integer branch did not write the file incomplete_files asked for")

    # ...and it is still the arm the world shipped. Read here rather than up with
    # the other preservation checks so the four behavioural readings above are
    # what a behavioural violation is reported as; this one catches the case they
    # cannot, a branch rewritten to suit whatever inputs a run happens to use.
    _check_explicit_arm_preserved()


# ---------------------------------------------------------------------------
# r1 — the plan is written down, in a versioned sidecar
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    for name in ("PLAN_FILE_NAME", "PLAN_FORMAT_VERSION", "plan_fingerprint", "plan_document"):
        has(o["surface"], name)

    src = _module_source(PLANNER)
    eq(o["plan_file_name"], PLAN_FILE_NAME, "PLAN_FILE_NAME")
    eq(_assigned(src, "PLAN_FILE_NAME"), PLAN_FILE_NAME, "PLAN_FILE_NAME in the module source")
    eq(o["plan_format_version"], PLAN_FORMAT_VERSION, "PLAN_FORMAT_VERSION")
    eq(_assigned(src, "PLAN_FORMAT_VERSION"), PLAN_FORMAT_VERSION, "PLAN_FORMAT_VERSION in the module source")

    # the digest is over the cuts and the sizes; index and num_requests are not in it
    eq(o["fp_same"], fingerprint(o["fp_spans"]), "plan_fingerprint of a known plan")
    eq(o["fp_same"], o["fp_relabelled"], "plan_fingerprint changed when only index/num_requests changed")
    ok(o["fp_same"] != o["fp_diff_size"], "plan_fingerprint ignores the batch sizes")
    ok(o["fp_same"] != o["fp_diff_cut"], "plan_fingerprint ignores where the cuts fall")

    plan = dataset_plan()
    eq(o["plan"], plan, "the plan this run's dataset produces")
    eq(o["batches_asdict"], [dict(zip(BATCH_KEYS, t)) for t in plan], "PlannedBatch as a dict")

    expected = document(plan, o["limits_asdict"])
    doc = json_of("r1_rule", PLAN_FILE_NAME)
    eq(list(doc), DOC_KEYS, "sidecar envelope keys")
    eq(doc, expected, "the sidecar the run left behind")
    eq(list(doc["batches"][0]), BATCH_KEYS, "a batch entry's keys")
    eq(o["plan_document_out"], doc, "plan_document(plan, limits) != the document on disk")


def judge_r1_scope(o):
    # Written at all, and describing THIS run — an empty plan's document is the
    # same every run, and a fact whose every check is seed-independent can be
    # answered by planting the directories it reads. Measured: a forgery that
    # implemented nothing passed this one fact and no other.
    plan = dataset_plan()
    ordered_doc = json_of("r1_scope_ordered", PLAN_FILE_NAME)
    eq(ordered_doc.get("num_batches"), len(plan), 'the "auto" branch wrote no plan for this run')
    eq(ordered_doc.get("batches"), [dict(zip(BATCH_KEYS, t)) for t in plan],
       "the sidecar does not describe the run that wrote it")
    eq(ordered_doc.get("plan_id"), fingerprint(plan), "the sidecar's plan_id")

    # Written before any request file of its own run. The worker records the
    # directory as it stood at the first `acreate_request_file`; THIS process
    # decides which name had to be in it, so r1.scope no longer depends on the
    # module exporting the constant that r1.rule grades.
    if o["ordered_reused_acreate"]:
        ok(PLAN_FILE_NAME in (o.get("ordered_listing_at_first_call") or []),
           "the sidecar was written after the request files, not before them: "
           f"the directory held {o.get('ordered_listing_at_first_call')}")

    # a 0-batch plan is still recorded
    eq(o["empty_create_result"], [], "empty auto run returns []")
    empty_doc = json_of("r1_scope_empty", PLAN_FILE_NAME)
    eq([empty_doc["num_batches"], empty_doc["num_requests"], empty_doc["num_bytes"], empty_doc["batches"]],
       [0, 0, 0, []], "a 0-batch plan is still recorded")
    eq(empty_doc["plan_id"], fingerprint([]), "the empty plan's plan_id")

    # the explicit-integer branch: no sidecar, and it really did run here
    ok(PLAN_FILE_NAME not in listing("r1_scope_fixed"), "the explicit-integer branch wrote a plan sidecar")
    chunk = SPEC["explicit_batch_size"]
    eq(rows_in("r1_scope_fixed", "requests_0.jsonl"), list(range(chunk)),
       "the explicit-integer branch did not write this run's rows")
    ok(PLAN_FILE_NAME not in listing("r1_scope_none"), "the `dataset is None` path wrote a plan sidecar")


def judge_r1_exclusions(o):
    ok((adir("r1_excl") / PLAN_FILE_NAME).is_file(),
       "the batch_plan.json sidecar is not implemented, so the constraint cannot be credited")  # require_feature
    plan = dataset_plan()
    eq(o["plan"], plan, "the plan this run's dataset produces")
    for t in plan:
        meta = json_of("r1_excl", f"metadata_{t[0]}.json")
        eq(sorted(meta), ["num_jobs"], "metadata carries plan fields it should not")
        eq(meta["num_jobs"], t[3], "metadata num_jobs == num_requests")


def judge_r1_failure_behavior(o):
    has(o["surface"], "BatchPlanTooFragmentedError")
    ok("ValueError" in o["bptfe_mro"], f"BatchPlanTooFragmentedError does not subclass ValueError: {o['bptfe_mro']}")
    ok("BatchPayloadTooLargeError" not in o["bptfe_mro"], "a fragmented plan is not an oversized payload")

    # The cap is the one input that is also an answer, so it is checked twice:
    # the limit the implementation actually applied, and the number its source
    # defines. Reporting 512 without defining it is not enough.
    limit = MAX_BATCHES_PER_PLAN
    eq(o["default_limit"], limit, "BatchLimits.max_batches_per_plan default")
    eq(_field_default(_module_source(PLANNER), "BatchLimits", "max_batches_per_plan"), limit,
       "max_batches_per_plan's default in the module source")
    eq(o["len_at_limit"], limit, f"{limit} batches is the boundary and it is admissible")
    raised(o["raise_over_limit"], mro=["BatchPlanTooFragmentedError"],
           attrs={"num_batches": limit + 1, "limit": limit}, msg=f"{limit + 1} batches")

    raised(o["raise_explicit_cap"], mro=["BatchPlanTooFragmentedError"],
           attrs={"num_batches": SPEC["cap_rows"], "limit": SPEC["cap_max_batches"]},
           msg="explicit max_batches_per_plan")
    raised(o["raise_oversize_first"], mro=["SingleRequestTooLargeError"],
           attrs={"row_idx": SPEC["oversize_rows"]}, msg="per-row scan wins")


def judge_r1_observability(o):
    eq(o["fp_empty"], fingerprint([]), "plan_fingerprint([])")

    wide = pack(row_sizes(SPEC["wide_rows"]), 1, UNBOUNDED_BYTES)
    eq(o["wide_plan"], wide, "one row per batch")
    eq(o["fp_wide"], fingerprint(wide), "plan_fingerprint of the one-per-batch plan")

    plan = dataset_plan()
    eq(o["plan"], plan, "the plan this run's dataset produces")
    eq(o["fp_plan"], fingerprint(plan), "plan_fingerprint of that plan")

    # the implementation's own limits are substituted, so the fan-out cap is
    # graded once, under failure_behavior, and not a second time here
    limits = o["limits_asdict"]
    ok(isinstance(limits, dict), f"the processor exposed no batch_limits to record: {limits!r}")
    eq(limits.get("max_requests_per_batch"), SPEC["max_requests"], "doc limits max_requests_per_batch")
    eq(limits.get("max_bytes_per_batch"), SPEC["max_bytes"], "doc limits max_bytes_per_batch")

    doc = json_of("r1_obs", PLAN_FILE_NAME)
    eq(doc, document(plan, limits), "the document the run leaves behind")
    raw = text_of("r1_obs", PLAN_FILE_NAME)
    ok(raw.endswith("]\n}\n"), f"the sidecar is not indented JSON with a trailing newline: {raw[-20:]!r}")


# ---------------------------------------------------------------------------
# r2 — the "auto" branch sweeps its stale numbering
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    plan = dataset_plan()
    eq(o["plan"], plan, "the plan this run's dataset produces")
    n = len(plan)
    ok(n < SPEC["prepop_n"], f"the fixture must plan fewer batches ({n}) than it pre-populated")

    eq(numbered("r2_rule", "requests_", ".jsonl"), request_files(n), "stale request files survived the run")
    eq(numbered("r2_rule", "metadata_", ".json"), metadata_files(n), "stale metadata files survived the run")
    eq(rows_in("r2_rule", "requests_0.jsonl"), list(range(plan[0][1], plan[0][2])),
       "requests_0.jsonl holds the new run's rows")


def judge_r2_scope(o):
    require_swept("r2_scope_sweep")

    # The explicit-integer branch owns its own numbering and removes nothing.
    # The run is `chunk + 1` rows at `chunk`, so it owns
    # requests_0 and requests_1 and nothing else: everything from 2 up must
    # survive. (This was `range(chunk + 1, prepop_n)`, which said the same thing
    # only while the chunk was 2 or 3 and the tail was 5-8 files long — with a
    # wider chunk it can be an empty range, and an empty range asserts nothing.
    # The run touches 0 and 1, so 2 up is the tail that must survive.)
    for name, scenario in (("explicit-integer", "r2_scope_fixed"), ("`dataset is None`", "r2_scope_none")):
        here = listing(scenario)
        untouched = range(2, SPEC["prepop_n"]) if scenario == "r2_scope_fixed" \
            else range(1, SPEC["prepop_n"])
        for i in untouched:
            ok(f"requests_{i}.jsonl" in here, f"the {name} branch removed a stale request file")
            ok(f"metadata_{i}.json" in here, f"the {name} branch removed a stale metadata file")
            eq(text_of(scenario, f"requests_{i}.jsonl"), SPEC["stale_request"],
               f"the {name} branch rewrote requests_{i}.jsonl")
            eq(text_of(scenario, f"metadata_{i}.json"), SPEC["stale_metadata"],
               f"the {name} branch rewrote metadata_{i}.json")


def judge_r2_exclusions(o):
    require_swept("r2_excl")
    for name, body in SPEC["keepers"].items():
        ok(name in listing("r2_excl"), f"the sweep removed {name}, which is not a request or metadata file")
        eq(text_of("r2_excl", name), body, f"the sweep rewrote {name}")


def judge_r2_failure_behavior(o):
    require_swept("r2_fail_sweep")

    raised(o["raise_plan"], mro=["SingleRequestTooLargeError"], attrs={"row_idx": 1},
           msg="planning raises on the oversize row")
    raised(o["raise_create"], mro=["SingleRequestTooLargeError"], msg="create_request_files raises")

    # The whole fact: the directory is exactly what was planted in it. Every
    # name and every byte comes from this run's fixture, so a directory prepared
    # in advance cannot stand in for one a failed run left alone.
    # `plan_file_name` is None when the submission exports no PLAN_FILE_NAME, and
    # then no sidecar was planted: r2 is graded on the stale files and the
    # bystanders alone.
    planted = dict.fromkeys(planted_names(), None)
    expected = set(planted) | set(SPEC["keepers"])
    if o["plan_file_name"]:
        expected |= {o["plan_file_name"]}
    eq(set(listing("r2_fail")), expected, "a planning failure changed the working directory")
    for i in range(SPEC["prepop_n"]):
        eq(text_of("r2_fail", f"requests_{i}.jsonl"), SPEC["stale_request"], f"requests_{i}.jsonl was rewritten")
        eq(text_of("r2_fail", f"metadata_{i}.json"), SPEC["stale_metadata"], f"metadata_{i}.json was rewritten")
    for name, body in SPEC["keepers"].items():
        eq(text_of("r2_fail", name), body, f"{name} was rewritten")
    if o["plan_file_name"]:
        eq(text_of("r2_fail", o["plan_file_name"]), SPEC["stale_sidecar"], "the stale sidecar was rewritten")


def judge_r2_observability(o):
    # the successful run: its own numbering, plus the bystanders, and nothing else
    plan = dataset_plan()
    expected_good = set(request_files(len(plan))) | set(metadata_files(len(plan))) | set(SPEC["keepers"])
    eq(set(listing("r2_obs_good")) - {PLAN_FILE_NAME, o["plan_file_name"]}, expected_good,
       "the working directory after a successful run")  # both names filtered: r1's fact, not this one
    for name, body in SPEC["keepers"].items():
        eq(text_of("r2_obs_good", name), body, f"the successful run rewrote {name}")

    # the failed run: exactly what it found
    raised(o["bad_plan_raises"], mro=["SingleRequestTooLargeError"], msg="planning raises")
    raised(o["bad_create_raises"], mro=["SingleRequestTooLargeError"], msg="create_request_files raises")
    expected_bad = set(planted_names()) | set(SPEC["keepers"])
    if o["plan_file_name"]:
        expected_bad |= {o["plan_file_name"]}
    eq(set(listing("r2_obs_bad")), expected_bad, "the working directory after a failed run")
    if o["plan_file_name"]:
        eq(text_of("r2_obs_bad", o["plan_file_name"]), SPEC["stale_sidecar"], "the stale sidecar was rewritten")
    eq(text_of("r2_obs_bad", f"requests_{SPEC['prepop_n'] - 1}.jsonl"), SPEC["stale_request"],
       "a stale request file was rewritten")


JUDGES = {
    "test_open::test_open_feature__auto_plans_batches_and_writes_one_file_per_planned_batch": judge_open,
    "test_r1::test_rule__the_auto_branch_records_the_plan_in_a_versioned_sidecar": judge_r1_rule,
    "test_r1::test_scope__only_the_auto_branch_writes_it_and_an_empty_plan_still_does": judge_r1_scope,
    "test_r1::test_exclusions__metadata_files_still_hold_num_jobs_and_nothing_else": judge_r1_exclusions,
    "test_r1::test_failure_behavior__a_plan_of_more_than_512_batches_is_refused": judge_r1_failure_behavior,
    "test_r1::test_observability__plan_id_is_the_first_twelve_hex_of_sha256_over_the_cuts": judge_r1_observability,
    "test_r2::test_rule__stale_request_and_metadata_files_are_removed_by_the_auto_branch": judge_r2_rule,
    "test_r2::test_scope__the_explicit_integer_branch_and_the_none_path_leave_files_alone": judge_r2_scope,
    "test_r2::test_exclusions__nothing_but_request_and_metadata_files_is_touched": judge_r2_exclusions,
    "test_r2::test_failure_behavior__a_planning_failure_removes_and_writes_nothing": judge_r2_failure_behavior,
    "test_r2::test_observability__the_working_directory_after_a_successful_and_a_failed_run": judge_r2_observability,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g1_batch_payload_plan" '
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
