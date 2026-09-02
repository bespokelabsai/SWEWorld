"""What an implementation must literally provide that the ticket never says.

Named for the failure it exists to stop. g1's clues arm scored 0.00 over ten
rollouts, and the two runs that got far enough to be graded at all died on
`AttributeError: module 'batch_payload_planner' has no attribute
'plan_fingerprint'`. The remarks carried the whole idea -- a sidecar file per run,
the first twelve hex of a sha256, the exact canonical string emil hashed by hand --
and never once said the word `plan_fingerprint`. A reader can infer a rule from
evidence. Nobody can infer a name that was never typed.

The generator already had the machinery: `verbatim` forces an identifier into a
remark and `keep_wording` refuses a rewrite that drops one. What was missing was
anything telling it WHICH identifiers. It committed to 22 of them -- `num_jobs`,
`incomplete_files`, `batch_plan.json` -- and to none of the six the tests graded.

The graded surface is an intersection of three texts:

    what the fact's own tests reach for    (`emit.suite_facts` maps fact -> tests)
  & what the hidden requirement states     (the half being hidden)
  - what the ticket already gives away     (the agent has that for free)

Names and values are separated because they fail differently. A name cannot be
derived from anything: if no remark says `max_batches_per_plan`, the keyword the
test passes does not exist and the fact is unscoreable however well the corpus is
read. A value usually can be -- the corpus need not print `e3b0c44298fc` as long as
somebody says which string was hashed and how much of the digest was kept -- so
values are reported to the author and never gated on.
"""
from __future__ import annotations

import ast
import dataclasses
import functools
import pathlib
import re

from . import emit
from .model import FACT_FIELDS, Task

# A dotted call whose root is one of these is the standard library doing its job,
# not a name the agent has to invent: `json.load`, `os.listdir`, `dataclasses.asdict`.
STDLIB = {"ast", "collections", "dataclasses", "datetime", "glob", "hashlib", "io",
          "itertools", "json", "math", "mock", "os", "pathlib", "pytest", "re",
          "shutil", "sys", "time", "types", "typing", "unittest"}

TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_*]+)*|\b[0-9a-f]{6,}\b|\b\d{2,}\b")
# `requests_{p.index}.jsonl` in the ticket and `requests_5.jsonl` in a test are the
# same name to a reader. Both collapse to `requests_#.jsonl` before they are compared,
# so a fixture's numbering is never mistaken for a name the ticket withheld.
VARIABLE = re.compile(r"\{[^}]*\}")
BACKTICKED = re.compile(r"`([^`]+)`")
DIGITS = re.compile(r"\d+")


def _shape(token: str) -> str:
    return DIGITS.sub("#", token)


def _tokens(text: str) -> set[str]:
    return {m.group(0).strip(".") for m in TOKEN.finditer(VARIABLE.sub("0", text or ""))}


def _spelling(token: str) -> str | None:
    """A fallback for tokens the syntax does not classify: does it LOOK chosen?

    Used only for what appears in a test's prose and literals rather than in a
    position the parser can read. `_names` below is the real classifier, because
    spelling gets `limit` wrong: it is an ordinary English word and also the
    attribute `BatchPlanTooFragmentedError` must carry, and reading it as prose is
    how the first gate passed a plant whose remarks never named it. That cost a
    hosted rollout to find.
    """
    if re.fullmatch(r"\d+|[0-9a-f]{6,}", token):
        return "value"
    if token.split(".")[0] in STDLIB:
        return None
    if "_" in token or "." in token or not token.islower():
        return "name"
    return None


# `read_field(err, "limit")` and `getattr(module, "plan_document")` are lookups by
# name: the string is an identifier the implementation must have chosen, not a value.
LOOKUPS = {"read_field", "getattr", "hasattr"}

# Attributes every Python object has. `open(path).read()` is not the implementation
# being asked for a name called `read`.
UNIVERSAL = set("""add_note append args decode encode endswith extend format get group
groups items join keys lower match pop read replace search sort split startswith strip
upper values with_traceback write""".split())


def _names(node: ast.AST, imported: set[str], local: set[str]) -> set[str]:
    """Identifiers a test reaches for by POSITION rather than by spelling.

    An attribute, a keyword argument, a dict key, a lookup string: each is a name
    somebody had to choose, and no amount of reading recovers one that was never
    written down. Position is what makes `limit` and `plan_document` the same kind
    of thing despite looking nothing alike.
    """
    found = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Attribute):
            root = child.value
            while isinstance(root, (ast.Attribute, ast.Subscript)):
                root = root.value
            while isinstance(root, ast.Call):
                root = root.func
            if isinstance(root, ast.Name) and (root.id in STDLIB or root.id in imported):
                continue
            if not child.attr.startswith("_") and child.attr not in UNIVERSAL:
                found.add(child.attr)
        elif isinstance(child, ast.Subscript):
            if isinstance(child.slice, ast.Constant) and isinstance(child.slice.value, str):
                found.add(child.slice.value)
        elif isinstance(child, ast.Call):
            callee = child.func.id if isinstance(child.func, ast.Name) else None
            if callee in LOOKUPS:
                for arg in child.args[1:]:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        found.add(arg.value)
            # A helper defined in the suite takes the suite's own keywords, not the
            # implementation's: `patched_limits(max_requests=3)` is the fixture talking.
            if callee is None or callee not in (local | imported):
                for kw in child.keywords:
                    if kw.arg:
                        found.add(kw.arg)
    return found


@dataclasses.dataclass
class Need:
    """What one hidden requirement's remarks have to say, fact by fact."""

    req_id: str
    names: dict[str, list[str]] = dataclasses.field(default_factory=dict)
    values: dict[str, list[str]] = dataclasses.field(default_factory=dict)

    @property
    def all_names(self) -> list[str]:
        return sorted({n for names in self.names.values() for n in names})

    @property
    def all_values(self) -> list[str]:
        return sorted({v for values in self.values.values() for v in values})


def _test_source(tests: pathlib.Path) -> tuple[dict[str, str], dict[str, ast.AST],
                                                dict[str, set[str]], dict[str, set[str]]]:
    """Per test function: its text, its tree, and what its file imports and defines."""
    bodies, nodes, imports, locals_ = {}, {}, {}, {}
    for path in sorted(tests.glob("test_*.py")):
        text = path.read_text()
        tree = ast.parse(text)
        lines = text.splitlines()
        imported = {(a.asname or a.name).split(".")[0] for a in ast.walk(tree)
                    if isinstance(a, ast.alias)}
        defined = {n.name for n in ast.walk(tree)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ref = f"{path.stem}::{node.name}"
                bodies[ref] = "\n".join(lines[node.lineno - 1:node.end_lineno])
                nodes[ref], imports[ref], locals_[ref] = node, imported, defined
    return bodies, nodes, imports, locals_


def _test_bodies(tests: pathlib.Path) -> dict[str, str]:
    """`test_r1::test_rule__...` -> that function's source, and only that function's.

    Per function rather than per file so a name is asked of the remarks that carry
    the fact it belongs to. A suite-wide grep would demand `plan_fingerprint` of
    r2's remarks as well, and r2 is about sweeping stale files.
    """
    out = {}
    for path in sorted(tests.glob("test_*.py")):
        lines = path.read_text().splitlines()
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[f"{path.stem}::{node.name}"] = "\n".join(
                    lines[node.lineno - 1:node.end_lineno])
    return out


def _required(task_id: str, tests: pathlib.Path, ticket: str,
              facts: list[tuple[str, str, str]]) -> dict[str, Need]:
    bodies, nodes, imports, locals_ = _test_source(tests)
    graded = emit.suite_facts(tests, task_id)
    # Only the ticket's CODE counts as already-given. It says "lands exactly on
    # either limit" as prose, and `limit` is also the attribute
    # `BatchPlanTooFragmentedError` must carry -- subtracting the English word hid
    # the identifier, and the plant then went out without anybody naming it.
    ticket_tokens = set()
    for span in BACKTICKED.findall(ticket) + [
            t for t in _tokens(ticket) if "_" in t or "." in t]:
        for token in _tokens(span):
            ticket_tokens.add(token)
            ticket_tokens.update(token.split("."))
    ticket_shapes = {_shape(t) for t in ticket_tokens}

    needs: dict[str, Need] = {}
    for req_id, field, text in facts:
        need = needs.setdefault(req_id, Need(req_id))
        key = f"{req_id}.{field}"
        reached, positional = set(), set()
        for ref in graded.get(key, []):
            reached |= _tokens(bodies.get(ref, ""))
            if ref in nodes:
                positional |= _names(nodes[ref], imports[ref], locals_[ref])
        stated = _tokens(text)
        for token in sorted(reached & stated):
            if token.endswith("_"):
                continue            # a tokenised prefix like `metadata_*.json`
            if token in ticket_tokens or _shape(token) in ticket_shapes:
                continue
            # Position first, spelling only as a fallback: `limit` is prose to a
            # speller and an attribute to the parser, and the parser is right.
            kind = "name" if token in positional else _spelling(token)
            if kind == "name":
                need.names.setdefault(field, []).append(token)
            elif kind == "value":
                need.values.setdefault(field, []).append(token)
    return needs


def required(task: Task) -> dict[str, Need]:
    """Per requirement id (`g1.r1`), what its remarks must say and must reach."""
    tests = task.dir / "tests"
    if not tests.is_dir():
        return {}
    facts = [
        (f"{task.id}.r{number}", field, (req.get("requirement") or {}).get(field) or "")
        for number, req in enumerate(task.hidden_requirements, 1)
        for field in FACT_FIELDS
        if (req.get("requirement") or {}).get(field)]
    return _required(task.id, tests, task.description, facts)


@functools.lru_cache(maxsize=1)
def _curator_tokens() -> frozenset[str]:
    """Every identifier curator already contains. Read once; it is ~200 files."""
    from .trees import SOURCE
    src = SOURCE / "src" / "bespokelabs" / "curator"
    out: set[str] = set()
    if src.is_dir():
        for path in src.rglob("*.py"):
            out |= _tokens(path.read_text(encoding="utf-8", errors="replace"))
    return frozenset(out)


def ungrounded_readers(task: Task) -> list[str]:
    """`read_field` calls where NO candidate spelling is written down anywhere.

    `required()` above intersects what the tests reach for with what the
    requirement states. A name in neither the ticket nor the requirement falls
    out of that `&` and is invisible to it -- which is not a small gap, it is the
    unscoreable case. If the grader demands a name and no arm is ever told it,
    every arm fails that fact, the spec arm included, and the task reports as
    hard when it is merely unanswerable.

    g3 shipped exactly that. `whole.md` marked the verdict's field spelling
    `throttle_waivers_after` an invented name; `split` dropped it from the
    requirement; the suite went on reading it. A hosted opus run implemented the
    whole waiver rule, spelled the field `throttle_waivers_left_after`, and
    scored 0 on all five r1 facts -- one mismatch wearing five faces. The spec
    arm's ceiling was 0.44 and nothing free could see why.

    Checked per `read_field(obj, *names)` call rather than per name, because the
    names are ALTERNATIVES: the reader passes if the object has any one of them,
    so the requirement only has to state one. Demanding all of them would flag
    every well-written reader in the suite.
    """
    tests = task.dir / "tests"
    if not tests.is_dir():
        return []
    grounded = set(_tokens(task.description))
    for req in task.hidden_requirements:
        for field in FACT_FIELDS:
            grounded |= _tokens((req.get("requirement") or {}).get(field) or "")
    grounded |= _curator_tokens()

    problems = []
    for path in sorted(tests.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            callee = node.func
            name = getattr(callee, "attr", None) or getattr(callee, "id", None)
            if name != "read_field":
                continue
            spellings = [a.value for a in node.args[1:]
                         if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if spellings and not any(s in grounded for s in spellings):
                problems.append(
                    f"{path.name}:{node.lineno}: read_field asks for "
                    f"{tuple(spellings)!r} and no arm is ever told any of them — "
                    "state one in the hidden requirement, or read the behaviour "
                    "instead of the name")
    return problems


def unsaid(names: list[str], texts: list[str]) -> list[str]:
    """The names nobody says, matched the way the phase-4 clue judge matches them.

    Case-insensitive and blind to backticks, because whether somebody wrote
    ``plan_id`` or `plan_id` is not what decides if the reader has the name. On a
    word boundary, though, and that is not fussiness: a plain substring test counts
    "the limits dataclass" as having said `limit`, and the plant that passed that
    test produced an implementation whose attribute was called `limit_batches`.
    """
    said = " ".join(texts).lower().replace("`", "")
    return [n for n in names
            if not re.search(rf"(?<![A-Za-z0-9_]){re.escape(n.lower())}(?![A-Za-z0-9_])", said)]
