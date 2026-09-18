"""g9 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote (values pulled from live curator) and the
pushed source text, and writes a `junit.xml` whose `classname`/`name` are the
current suite's node ids — so `score.py` folds them into the identical fact keys
and `test.sh`/`score.py` are unchanged. No agent code runs here, so the report
cannot be forged; and `test.sh` locks /tests to 0700 root, so the worker cannot
read this file.

WHY THIS FILE NO LONGER HOLDS THE ANSWERS AS LITERALS. The split moved the
verdict out of the process that runs agent code. It left the worker AUTHORING
the values the verdict is computed from, and with a fixed fixture those values
never changed — g9's `GOOD_TEXT`, 91, 51, `[30..38]`, `(48, 59)`, "90 bytes,
budget 90" were the same every run, and most of them are written down in the
world the agent is told to read. A pristine tree plus one import-time `atexit`
hook that rewrote `observations.json` passed every fact. Two things close that:

  * **the inputs move every run.** `fixture_spec.derive(seed)` re-draws the
    conversation, the three windows, the byte ladder and the batch from the seed
    root picked, and this file RECOMPUTES what the answers must be for those
    inputs — the policy applied here, once, in `expected()`. There is nothing to
    memorise and nothing in the corpus to copy.
  * **what only source can show is read from source.** "`format_chat_messages`
    is reused unchanged", "the `tinker.Datum` branch is untouched",
    "`example_to_dict` and `write_jsonl` are unchanged", "additions only in
    `tests/finetune/test_data_formatter.py`", the frozen `EncodingReport`
    declaration and the bytes-per-token constant are compared against the
    pristine tree and the pushed files, not taken from a worker boolean. The one
    preservation rule with no pristine twin — the prefix-tokenization boundary
    trick, which lives inside the function the ticket rewrites — is checked as a
    mechanism instead, in the source AND in the calls it must have made
    (`_check_boundary_trick_declared`, `_check_boundary_trick_used`): spans read
    off this template's character offsets are equally correct here and wrong for
    every real tokenizer, so "it came out right" does not show the trick
    survived.

The residual, stated plainly: a submission that IMPLEMENTS the policy inside a
forged hook still passes, because it has then done the work. What is gone is
passing by repeating values that were knowable in advance.

What each fact means is the `judge_*` function that grades it — the assertions
below ARE the record. `tests/task.json` states the two hidden requirements in
prose, which is where a reviewer cross-checks the constants above; nothing here
points at a document this task does not ship.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import sys
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_spec  # noqa: E402 - same derivation the worker used, same templates

# The judge runs `python3 -I` with no PYTHONPATH, so /tests is not importable by
# default. judge_io holds the hardened reads (no symlinks, size-capped) every
# agent-influenced path goes through; harness.py cannot: it imports pytest.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import judge_io  # noqa: E402

# The answers that cannot be re-drawn, because they ARE the requirement.
ALLOWED_ROLES = ("system", "user", "assistant")
REASONS = ("empty", "unknown_role", "misplaced_system", "non_alternating", "unterminated")
MIN_RETAINED_PROMPT_TOKENS = 16
FIREWORKS_BYTES_PER_TOKEN = 3
REPORT_FIELDS = ["kept", "dropped", "windowed", "dropped_indices", "supervised_tokens"]
DEFAULT_REPORT = [0, 0, 0, [], 0]
REPORT_DEFAULTS = (0, 0, 0, (), 0)
DEFAULT_MAX_SEQ_LENGTH = 2048

FINETUNE = "bespokelabs/curator/finetune"
DATA_FORMATTER = f"{FINETUNE}/data_formatter.py"
# The method instruction.md:33 puts in place of `_compute_weights`, and which
# instruction.md:39 says keeps the boundary trick.
SPANS = "DataFormatter._supervised_spans"
FIREWORKS_FORMATTER = f"{FINETUNE}/fireworks_data_formatter.py"
# The one line instruction.md:74 names. Building the trainer needs a live
# Fireworks account, so this is the stated requirement that only source can show.
FIREWORKS_TRAINER = f"{FINETUNE}/trainer/fireworks_trainer.py"
TEST_FILE = "tests/finetune/test_data_formatter.py"

# The pristine repository. `CURATOR_BASELINE_DIR` is root's staged copy of
# src/bespokelabs/curator (see run_suites.stage_baseline) and is what the
# "reused unchanged" checks compare against; the repository's own test file sits
# OUTSIDE that package, so it is read from the 0700 root tree directly. Both are
# root-owned and neither is writable by the worker. If a path is missing the
# check FAILS its fact — never passes blind.
BASELINE_PACKAGE = os.environ.get("CURATOR_BASELINE_DIR", "")
PRISTINE_TREE = pathlib.Path("/opt/world-state/input/curator")

SPEC: dict = {}


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


def raised(info, *, mro=None, msg="", **attrs):
    """Assert an exception was recorded, of the named class, carrying `attrs`."""
    ok(info.get("raised"), f"{msg}: expected an exception, none raised")
    if mro is not None:
        ok(mro in info.get("mro", []), f"{msg}: {mro} not in {info.get('mro')}")
    for name, want in attrs.items():
        eq(info.get(name), want, f"{msg}: {name}")


# ---------------------------------------------------------------------------
# The policy, applied here and nowhere the worker can read
# ---------------------------------------------------------------------------
def _spans(pairs, render) -> list:
    """Every assistant turn's half-open `[start, end)` token span, by the ticket's
    prefix-tokenization boundaries: the conversation up to but excluding the turn
    rendered WITH a generation prompt gives the start, rendered through the turn
    gives the end."""
    spans = []
    for index, (role, _) in enumerate(pairs):
        if role != "assistant":
            continue
        start = len(render(pairs[:index], True)) if index else 0
        spans.append((start, len(render(pairs[: index + 1]))))
    return spans


def expected(pairs, max_seq_length, render=None, *, assistant_only=True, per_char=1) -> dict:
    """What `to_tinker_datum` must produce for these messages at this window.

    `render=None` is the tokenizer-free branch: `fixture_spec.render_mock`'s
    `<|role|>` text, `len // 4` tokens and spans from character offsets.
    Everything else — the window, the mask, the causal shift — is common to both
    branches, which is the point of r1's scope fact.

    `per_char` is how many ids the tokenizer double returns per character: 1 for
    `FakeTokenizer`, 2 for `DenseTokenizer`, where a token index is deliberately
    NOT a character offset. The policy is the same either way, which is the whole
    reason the second geometry can tell a tokenized boundary from an arithmetic
    one.
    """
    if render is None:
        text = fixture_spec.render_mock(pairs)
        tokens = list(range(len(text) // 4))
        spans = [(start // 4, end // 4)
                 for start, end in _spans(pairs, fixture_spec.render_mock)]
    else:
        text = render(pairs)
        tokens = [ord(char) for char in text for _ in range(per_char)]
        spans = [(start * per_char, end * per_char) for start, end in _spans(pairs, render)]

    token_count = len(tokens)
    window_start = max(0, token_count - max_seq_length)
    retained = max(0, spans[-1][0] - window_start) if spans else 0
    out = {"text": text, "token_count": token_count, "window_start": window_start,
           "windowed": window_start > 0, "spans": spans, "retained": retained,
           "refused": bool(window_start > 0 and spans
                           and spans[-1][0] - window_start < MIN_RETAINED_PROMPT_TOKENS)}
    if out["refused"]:
        return out

    if assistant_only:
        weights = [0.0] * token_count
        for start, end in spans:
            # A turn the window cuts in half earns nothing, not its surviving tail.
            if start >= window_start:
                for index in range(start, min(end, token_count)):
                    weights[index] = 1.0
    else:
        weights = [1.0] * token_count

    windowed_tokens = tokens[window_start:]
    windowed_weights = weights[window_start:]
    out.update(model_input=windowed_tokens[:-1], targets=windowed_tokens[1:],
               weights=windowed_weights[1:], supervised=int(sum(windowed_weights)))
    return out


def first_violation(roles) -> tuple:
    """The `(reason, position)` of the first rule a role sequence breaks, in the
    ticket's order."""
    if not roles:
        return "empty", 0
    for index, role in enumerate(roles):
        if role not in ALLOWED_ROLES:
            return "unknown_role", index
    for index, role in enumerate(roles):
        if role == "system" and index != 0:
            return "misplaced_system", index
    want = "user"
    for index in range(1 if roles[0] == "system" else 0, len(roles)):
        if roles[index] != want:
            return "non_alternating", index
        want = "assistant" if want == "user" else "user"
    if roles[-1] != "assistant":
        return "unterminated", len(roles) - 1
    return None, None


def fireworks_line(pairs) -> str:
    """`example_to_dict` + `json.dumps(..., ensure_ascii=False)` — curator's
    existing serialization, which the ticket keeps unchanged."""
    return json.dumps({"messages": [{"role": role, "content": content}
                                    for role, content in pairs]}, ensure_ascii=False)


def fireworks_kept(examples, max_seq_length) -> tuple:
    """(kept lines, dropped input positions) under the UTF-8 byte budget. Strict
    `>`: a line that lands exactly on the budget is kept."""
    budget = max_seq_length * FIREWORKS_BYTES_PER_TOKEN
    lines, dropped = [], []
    for index, pairs in enumerate(examples):
        line = fireworks_line(pairs)
        if len(line.encode("utf-8")) > budget:
            dropped.append(index)
        else:
            lines.append(line)
    return lines, dropped


def batch_outcome(examples, max_seq_length, render=fixture_spec.render_chat) -> dict:
    """What `format_batch` must keep, drop and report for these rows."""
    kept, dropped = [], []
    for index, pairs in enumerate(examples):
        result = expected(pairs, max_seq_length, render)
        (dropped if result["refused"] else kept).append((index, pairs, result))
    return {
        "kept": kept,
        "dropped": [index for index, _, _ in dropped],
        "report": [len(kept), len(dropped),
                   sum(1 for _, _, r in kept if r["windowed"]),
                   [index for index, _, _ in dropped],
                   sum(r["supervised"] for _, _, r in kept)],
    }


def fixture_defect(spec: dict) -> str:
    """Whether THIS run's draw can grade the facts at all — checked once, first.

    The inputs move every run, which is what makes a forged observations file
    worthless, and the price is that a draw has to be CHECKED rather than
    assumed: a window that lands at index 0 windows nothing, a byte ladder that
    misses the budget grades only one side of the cut, five role cases that break
    the same rule twice grade one rule twice. Every fact already asserts the
    invariant it needs, where it needs it, and this gate says the same things
    once, up front, so a pathological draw fails every fact with ONE message
    naming the draw, instead of reading like an implementation defect. A correct
    submission can never be the reason it fires, and 20,000 seeds have not.
    """
    try:
        good = expected(spec["good"], spec["good_max_seq_length"], fixture_spec.render_chat)
        wide = expected(spec["good"], spec["wide_max_seq_length"], fixture_spec.render_chat)
        tight = expected(spec["good"], spec["tight_max_seq_length"], fixture_spec.render_chat)
        too_long = expected(spec["too_long"], spec["good_max_seq_length"],
                            fixture_spec.render_chat)
        plain = expected(spec["plain"], spec["plain_max_seq_length"])
        plain_windowed = expected(spec["plain_windowed"],
                                  spec["plain_windowed_max_seq_length"])
        dense = expected(spec["good"], spec["dense_max_seq_length"],
                         fixture_spec.render_chat, per_char=2)
        batch = batch_outcome(spec["batch"], spec["good_max_seq_length"])
        clean = batch_outcome(spec["batch"], spec["clean_max_seq_length"])
        ladder = [fireworks_line(pairs) for pairs in spec["fw_examples"]]
        kept, dropped = fireworks_kept(spec["fw_examples"], spec["fw_max_seq_length"])
        budget = spec["fw_max_seq_length"] * FIREWORKS_BYTES_PER_TOKEN
        fw_kept, fw_dropped = fireworks_kept(spec["fw_report_examples"],
                                             spec["fw_report_max_seq_length"])
        reasons = [first_violation([role for role, _ in messages])[0]
                   for messages in spec["role_cases"]]

        checks = (
            ("the narrow window must still be encodable", not good["refused"]),
            ("the narrow window's boundary must fall inside the first assistant turn",
             good["spans"] and good["spans"][0][0] < good["window_start"] < good["spans"][0][1]),
            ("an assistant turn must follow the first message, or the boundary trick "
             "makes no prefix call", any(role == "assistant" for role, _ in spec["good"][1:])),
            ("the wide window must start inside the prompt",
             wide["spans"] and 0 < wide["window_start"] <= wide["spans"][0][0]),
            ("the tight window must be refused", tight["refused"]),
            ("the over-long example must be refused", too_long["refused"]),
            ("the tokenizer-free example must supervise part of its sequence, not all of it",
             0.0 in plain["weights"] and 1.0 in plain["weights"]),
            ("the windowed tokenizer-free example must window and still be encodable",
             plain_windowed["windowed"] and not plain_windowed["refused"]),
            ("the windowed tokenizer-free boundary must fall in the prompt, before the "
             "first assistant turn, so one wrong policy cannot fail two facts",
             plain_windowed["spans"]
             and plain_windowed["window_start"] <= plain_windowed["spans"][0][0]),
            ("the windowed tokenizer-free example must supervise part of its sequence, "
             "not all of it",
             0.0 in plain_windowed["weights"] and 1.0 in plain_windowed["weights"]),
            # The dense scenario's own invariant, gated here rather than only
            # where judge_open asserts it: task.toml says every invariant the
            # facts depend on is evaluated once before anything is graded, and
            # this one was the exception.
            ("the dense window must be wide enough to leave this conversation whole",
             not dense["windowed"] and not dense["refused"]),
            ("the batch must have something to keep and something to drop",
             batch["kept"] and batch["dropped"]),
            ("the clean pass must drop nothing", not clean["dropped"]),
            ("the fireworks ladder must keep and drop", kept and dropped),
            ("one fireworks line must land exactly on the byte budget",
             any(len(line.encode("utf-8")) == budget for line in ladder)),
            ("one fireworks line must carry more bytes than characters across the budget",
             any(len(line) <= budget < len(line.encode("utf-8")) for line in ladder)),
            ("the fireworks report pass must keep and drop", fw_kept and fw_dropped),
            ("the five role cases must be the five reasons, in order",
             reasons == list(REASONS)),
        )
    except Exception as exc:  # noqa: BLE001 - an undrawable fixture is a defect, not a crash
        return f"the draw could not be evaluated: {type(exc).__name__}: {exc}"
    return "; ".join(label for label, held in checks if not held)


# ---------------------------------------------------------------------------
# What only the source can show
# ---------------------------------------------------------------------------
def _read(root: pathlib.Path, rel: str, what: str) -> str:
    path = root / rel
    try:
        return judge_io.read_text(path)
    except OSError as exc:
        raise Fail(f"cannot read the {what} copy of {rel}: {exc}")


def _submission_source(rel: str) -> str:
    """A file from the pushed tree. `rel` is relative to the repository root."""
    src = os.environ.get("SUBMISSION_SRC", "")
    ok(bool(src), "SUBMISSION_SRC is not set; the pushed source cannot be read")
    root = pathlib.Path(src).parent
    if rel.startswith("bespokelabs/"):
        root = pathlib.Path(src)
    return _read(root, rel, "pushed")


def _pristine_source(rel: str) -> str:
    """The same file from the pristine tree. Inside the curator package the
    staged baseline is used; outside it (the repository's own tests) the 0700
    root tree is read directly."""
    if rel.startswith("bespokelabs/curator/"):
        ok(bool(BASELINE_PACKAGE) and pathlib.Path(BASELINE_PACKAGE).is_dir(),
           "CURATOR_BASELINE_DIR is unset or missing: the 'reused unchanged' rules "
           "cannot be checked, so this fact fails rather than passing unchecked")
        inner = rel[len("bespokelabs/curator/"):]
        return _read(pathlib.Path(BASELINE_PACKAGE), inner, "pristine")
    ok(PRISTINE_TREE.is_dir(),
       f"the pristine tree is not readable at {PRISTINE_TREE}: the 'additions only' "
       "rule cannot be checked, so this fact fails rather than passing unchecked")
    return _read(PRISTINE_TREE, rel, "pristine")


def _shape(node) -> str:
    """The position-free AST of a definition — its name, decorators, signature
    and body — for comparing "is this the same code". Comments, formatting and a
    reworded docstring do not show up here; a changed statement, a renamed
    parameter or a dropped decorator does.

    The docstring is dropped in place, on a tree parsed fresh for this
    comparison; nothing else reads these nodes afterwards.
    """
    body = getattr(node, "body", None)
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        node.body = body[1:] or [ast.Pass()]
    return ast.dump(node, annotate_fields=True, include_attributes=False)


def _functions(source: str) -> dict:
    """{"Class.name" or "name": FunctionDef} for every function in a module."""
    found = {}
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found[f"{node.name}.{child.name}"] = child
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found[node.name] = node
    return found


def _check_unchanged(rel: str, names, why: str) -> None:
    """Every named function is still the code the pristine tree has."""
    mine = _functions(_submission_source(rel))
    theirs = _functions(_pristine_source(rel))
    for name in names:
        ok(name in theirs, f"{rel}: the pristine tree has no {name}; this check is stale")
        ok(name in mine, f"{rel}: {name} is gone, and {why}")
        if _shape(mine[name]) != _shape(theirs[name]):
            raise Fail(f"{rel}: {name} has been rewritten, and {why}")


def _tinker_branch(source: str, rel: str):
    """The `if TINKER_AVAILABLE ...` block that builds the `tinker.Datum`."""
    found = [node for node in ast.walk(ast.parse(source))
             if isinstance(node, ast.If)
             and any(isinstance(sub, ast.Name) and sub.id == "TINKER_AVAILABLE"
                     for sub in ast.walk(node.test))]
    ok(len(found) == 1,
       f"{rel}: expected exactly one `if TINKER_AVAILABLE` block, found {len(found)}; "
       "the ticket says the tinker.Datum construction is out of scope")
    return found[0]


def _check_reuse_rules() -> None:
    """The ticket's preservation constraints, which no behavioural check can see.

    instruction.md:39 reuses `format_chat_messages`, `format_example` and the
    `tinker.Datum` construction unchanged; :69 says the tinker branch is
    untouched; :75 says `example_to_dict` and `write_jsonl` are unchanged; :83
    allows additions only in the repository's formatter tests. `protected_files`
    cannot express any of them — every one of these lives inside a file the
    ticket itself edits — and a submission that rewrote them while keeping the
    probed behaviour passed every fact. `tinker` is not installed in this world,
    so the Datum branch is not even reachable behaviourally: source is the only
    thing that can show it survived.
    """
    _check_unchanged(DATA_FORMATTER,
                     ("DataFormatter.format_chat_messages", "DataFormatter.format_example"),
                     "the ticket reuses it unchanged")
    _check_unchanged(FIREWORKS_FORMATTER,
                     ("FireworksDataFormatter.example_to_dict",
                      "FireworksDataFormatter.write_jsonl"),
                     "the ticket says it is unchanged")

    mine = _submission_source(DATA_FORMATTER)
    theirs = _pristine_source(DATA_FORMATTER)
    if _shape(_tinker_branch(mine, "pushed data_formatter.py")) != \
            _shape(_tinker_branch(theirs, "pristine data_formatter.py")):
        raise Fail("data_formatter.py: the `if TINKER_AVAILABLE` Datum construction has "
                   "been changed; the ticket puts it out of scope")

    # The repository's own tests: additions only, so every test that was there is
    # still there and still the same test.
    existing = _functions(_pristine_source(TEST_FILE))
    submitted = _functions(_submission_source(TEST_FILE))
    for name, node in existing.items():
        ok(name in submitted,
           f"{TEST_FILE}: {name} has been removed; the ticket allows additions only")
        if _shape(submitted[name]) != _shape(node):
            raise Fail(f"{TEST_FILE}: {name} has been rewritten; the ticket allows "
                       "additions only, and every existing test must still pass unchanged")


# ---------------------------------------------------------------------------
# Resolving the code that actually runs
# ---------------------------------------------------------------------------
#
# A source check that asks only "does this line appear somewhere in the file" is
# answered by code nothing runs. Measured on the trainer check below: a tree
# that never wires the trainer scored 8 of 8 by adding
# `self.data_formatter = FireworksDataFormatter.from_config(config)` under
# `if False:` beside a live `self.data_formatter = _build_formatter(config)`
# whose helper called the class, and again with that line parked after a
# `return` in a module-level function nothing calls. Reward-bearing: without any
# such line the same tree fails open_feature.
#
# g1's judge measured the identical hole in its preservation checks and g3's in
# its attempt-label clause, so the three rules below are theirs rather than a
# third invention. Live means all three of:
#
#   * the definition Python BINDS — module level, the last `def` of a name in a
#     namespace wins, a name defined twice in one namespace is REFUSED rather
#     than resolved (a duplicate is the vehicle every one of those dodges used),
#     and a `Cls.attr = ...` or `setattr(Cls, ...)` anywhere in the file is
#     refused too, because the definition read here is then not the one that
#     runs;
#   * reachable: a scope something outside the module enters (a public or dunder
#     definition, which is how a caller gets in) or a definition live code
#     mentions by name, to a fixpoint;
#   * not in a branch a literal test closes. `if False:` is not the only
#     spelling — `while False:`, `if not True:`, `if ():`, `for _ in []:` and
#     anything after a `return`/`raise`/`continue`/`break` are just as dead, and
#     every one of them was accepted before.
_TERMINAL = (ast.Return, ast.Raise, ast.Continue, ast.Break)
_TRY = (ast.Try,) + ((ast.TryStar,) if hasattr(ast, "TryStar") else ())


def _tree(source: str) -> ast.Module:
    try:
        return ast.parse(source)
    except SyntaxError as exc:
        raise Fail(f"the submission does not parse: {exc}")


def _literal_truth(node):
    """True/False when a test is a literal the parse itself settles, else None."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        inner = _literal_truth(node.operand)
        return None if inner is None else not inner
    try:
        return bool(ast.literal_eval(node))
    except Exception:  # noqa: BLE001 - not a literal, so the branch stays live
        return None


class _Live:
    """What one pass over one scope's live code found."""

    def __init__(self):
        self.assigns = []   # values assigned to `self.data_formatter`
        self.returns = []   # values this scope hands back to its caller
        self.calls = set()  # every name the live code CALLS
        self.defs = []      # definitions it binds without entering


def _stores_formatter(target) -> bool:
    """Whether `target` is the instance's `data_formatter` attribute.

    `self.__dict__["data_formatter"] = ...` stores that attribute without ever
    spelling it as one, and reading it as something else was worth every fact:
    a submission wrote the conforming assignment and overwrote it one statement
    later with a class call through a helper.
    """
    if isinstance(target, ast.Attribute):
        return (target.attr == "data_formatter" and isinstance(target.value, ast.Name)
                and target.value.id == "self")
    return (isinstance(target, ast.Subscript) and isinstance(target.value, ast.Attribute)
            and target.value.attr == "__dict__" and isinstance(target.value.value, ast.Name)
            and target.value.value.id == "self"
            and isinstance(target.slice, ast.Constant)
            and target.slice.value == "data_formatter")


def _formatter_target(stmt) -> bool:
    targets = (stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target])
    return any(_stores_formatter(t) for t in targets)


def _setattr_formatter(node):
    """The value a `setattr(self, "data_formatter", <...>)` call stores, or None.

    The same attribute, by its third spelling. Class-level rebinds are refused
    in `_live_module`; an instance-level one is not a decoy pointing away from
    the wiring, it IS the wiring, so it is read as the assignment it is.
    """
    if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "setattr"
            and len(node.args) == 3 and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "self" and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "data_formatter"):
        return None
    return node.args[2]


def _walk_expr(node, live, *, counts):
    if isinstance(node, ast.Call):
        # The name a call site spells, which is how a definition the mechanism
        # was factored into is entered. A bare attribute (not just `self.x()`)
        # counts, matching how `_resolved` names a callee: leaning live is the
        # mild direction for a shape this judge does not model.
        func = node.func
        named = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if named:
            live.calls.add(named)
        if counts:
            stored = _setattr_formatter(node)
            if stored is not None:
                live.assigns.append(stored)
    if isinstance(node, ast.Lambda):
        # A lambda body runs when the lambda is called, which is not here.
        counts = False
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.stmt):
            _walk_stmt(child, live, counts=counts)
        else:
            _walk_expr(child, live, counts=counts)


def _walk_body(body, live, *, counts):
    for stmt in body:
        _walk_stmt(stmt, live, counts=counts)
        if isinstance(stmt, _TERMINAL):
            return


def _walk_stmt(stmt, live, *, counts):
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
        live.defs.append(stmt)
        for node in (list(stmt.decorator_list) + list(stmt.args.defaults)
                     + [d for d in stmt.args.kw_defaults if d is not None]):
            _walk_expr(node, live, counts=counts)
        return
    if isinstance(stmt, ast.ClassDef):
        for node in list(stmt.decorator_list) + list(stmt.bases):
            _walk_expr(node, live, counts=counts)
        # A class body does run where it is written, but what it computes there
        # is a value fixed at import: it cannot be the trainer wiring an
        # instance up, and it cannot be a helper's answer to its caller.
        _walk_body(stmt.body, live, counts=False)
        return
    if counts:
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)) and stmt.value is not None \
                and _formatter_target(stmt):
            live.assigns.append(stmt.value)
        elif isinstance(stmt, ast.Return) and stmt.value is not None:
            live.returns.append(stmt.value)
    if isinstance(stmt, ast.If):
        truth = _literal_truth(stmt.test)
        _walk_expr(stmt.test, live, counts=counts)
        if truth is not False:
            _walk_body(stmt.body, live, counts=counts)
        if truth is not True:
            _walk_body(stmt.orelse, live, counts=counts)
        return
    if isinstance(stmt, ast.While):
        truth = _literal_truth(stmt.test)
        _walk_expr(stmt.test, live, counts=counts)
        if truth is not False:
            _walk_body(stmt.body, live, counts=counts)
        _walk_body(stmt.orelse, live, counts=counts)
        return
    if isinstance(stmt, (ast.For, ast.AsyncFor)):
        empty = _literal_truth(stmt.iter)
        _walk_expr(stmt.iter, live, counts=counts)
        if empty is not False:
            _walk_body(stmt.body, live, counts=counts)
        _walk_body(stmt.orelse, live, counts=counts)
        return
    if isinstance(stmt, _TRY):
        _walk_body(stmt.body, live, counts=counts)
        for caught in stmt.handlers:
            if caught.type is not None:
                _walk_expr(caught.type, live, counts=counts)
            _walk_body(caught.body, live, counts=counts)
        _walk_body(stmt.orelse, live, counts=counts)
        _walk_body(stmt.finalbody, live, counts=counts)
        return
    # Anything else: its expressions, and any statement list it holds, with no
    # dead-branch pruning. Leaning live is the safe direction for a statement
    # shape this judge does not model — it can only make the check milder.
    _walk_expr(stmt, live, counts=counts)


def _effective(nodes: list, what: str):
    """The definition that binds, or a Fail if the name is defined twice."""
    if len(nodes) > 1:
        raise Fail(f"{what} is defined {len(nodes)} times in one namespace; Python binds the "
                   "last one, so a duplicate definition cannot stand in for the "
                   "implementation that runs")
    return nodes[-1] if nodes else None


def _accessor(func) -> bool:
    """A `@x.setter`/`@x.getter`/`@x.deleter` or `@overload` companion `def`.

    Python does rebind the name for these, but the pair is one property or one
    signature, not a decoy: refusing them would fail a submission that adds a
    setter to a property it keeps.
    """
    for deco in func.decorator_list:
        if isinstance(deco, ast.Attribute) and deco.attr in ("setter", "getter", "deleter"):
            return True
        if getattr(deco, "id", "") == "overload" or getattr(deco, "attr", "") == "overload":
            return True
    return False


def _register(defs: dict, node) -> None:
    """`node` under its own bare name, once, whatever path reached it.

    Bare, because that is what a `self.helper()` or `helper()` call site spells.
    """
    holder = defs.setdefault(node.name, [])
    if not any(existing is node for existing in holder):
        holder.append(node)


def _namespace_defs(body, where: str, defs: dict) -> None:
    """The `def`s one namespace binds, refusing a name it defines twice."""
    funcs = [stmt for stmt in body
             if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for name in sorted({func.name for func in funcs}):
        same = [func for func in funcs if func.name == name]
        _effective([func for func in same if not _accessor(func)], f"{where}{name}()")
        for func in same:
            _register(defs, func)


def _live_module(source: str) -> tuple:
    """`(defs, assigns, returns)` for the code a module actually runs.

    `assigns` is every value LIVE code assigns to `self.data_formatter`;
    `returns` maps a definition to what it hands its caller from live code,
    which is how a helper's answer is followed back to the assignment that took
    it.
    """
    tree = _tree(source)
    defs: dict = {}
    _namespace_defs(tree.body, "", defs)
    classes = [stmt for stmt in tree.body if isinstance(stmt, ast.ClassDef)]
    names = [cls.name for cls in classes]
    dupes = sorted({name for name in names if names.count(name) > 1})
    if dupes:
        raise Fail(f"{', '.join(dupes)} is defined more than once at module level; Python "
                   "binds the later definition, so a decoy class cannot stand in for it")
    for cls in classes:
        _namespace_defs(cls.body, f"{cls.name}.", defs)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)
                and t.value.id in names for t in node.targets):
            raise Fail(f"a member of {', '.join(names)} is rebound by an assignment at line "
                       f"{node.lineno}, so the definitions read here are not the ones that run")
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "setattr" \
                and node.args and isinstance(node.args[0], ast.Name) \
                and node.args[0].id in names:
            raise Fail(f"setattr on {node.args[0].id} at line {node.lineno} rebinds its "
                       "members, so the definitions read here are not the ones that run")

    assigns: list = []
    returns: dict = {}
    # Roots: the module body, plus every public or dunder definition, which a
    # caller enters from outside and nothing in the module has to mention.
    pending = [(tree.body, False, None)]
    entered = set()
    for name, nodes in defs.items():
        if not name.startswith("_") or (name.startswith("__") and name.endswith("__")):
            for node in nodes:
                entered.add(id(node))
                pending.append((node.body, True, node))

    # Entered on a CALL, never on a mention: `self._wire_ref = self._wire` names
    # a private method without running it, and entering it on the mention made
    # its assignment count for all eight facts while nothing wired anything.
    called: set = set()
    while pending:
        body, counts, owner = pending.pop()
        live = _Live()
        _walk_body(body, live, counts=counts)
        assigns.extend(live.assigns)
        if owner is not None:
            returns.setdefault(id(owner), []).extend(live.returns)
        called |= live.calls
        for node in live.defs:
            _register(defs, node)
        for name in sorted(called):
            for node in defs.get(name, []):
                if id(node) not in entered:
                    entered.add(id(node))
                    pending.append((node.body, True, node))
    return defs, assigns, returns


def _resolved(values: list, defs: dict, returns: dict, seen=None) -> list:
    """`values`, with a call to one of this module's definitions replaced by what
    that definition returns — to a fixpoint.

    So factoring the construction into a helper, one level or five, is not
    punished, and hiding it there is not rewarded. A call this module cannot
    resolve stays as it is: it satisfies neither half of the check, and the
    message says which assignment could not be followed.
    """
    seen = set() if seen is None else seen
    out = []
    for value in values:
        targets = []
        if isinstance(value, ast.Call):
            func = value.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            targets = [node for node in defs.get(name, []) if returns.get(id(node))]
        followed = [node for node in targets if id(node) not in seen]
        if not followed:
            out.append(value)
            continue
        for node in followed:
            seen.add(id(node))
            out.extend(_resolved(returns[id(node)], defs, returns, seen))
    return out


def _formatter_assignments(source: str) -> list:
    """Every value a module stores into `self.data_formatter`, live or not, by
    any of the three spellings that store it (see `_stores_formatter` and
    `_setattr_formatter`)."""
    out = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None \
                and _formatter_target(node):
            out.append(node.value)
            continue
        stored = _setattr_formatter(node)
        if stored is not None:
            out.append(stored)
    return out


def _constructs_formatter(value) -> bool:
    """Whether this expression builds a formatter by calling its class directly —
    `FireworksDataFormatter()`, which is the line instruction.md:74 replaces."""
    if not isinstance(value, ast.Call):
        return False
    func = value.func
    named = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
    return named.endswith("DataFormatter")


def _through_from_config(value) -> bool:
    """Whether this expression builds the formatter through a `from_config(...)`
    call. The receiver is not pinned: a submission may alias or subclass the
    class, and the requirement is that the CONFIG reaches the formatter."""
    return (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
            and value.func.attr == "from_config" and bool(value.args or value.keywords))


def _check_fireworks_trainer_wired() -> None:
    """instruction.md:74 — the trainer builds its formatter through `from_config`.

    The stated requirement that is a WIRING, and the only one behaviour here
    cannot show: constructing a `FireworksTrainer` wants a live Fireworks
    account, so nothing the worker runs touches this file. `from_config` can be
    implemented perfectly, and graded perfectly, while the trainer goes on
    calling `FireworksDataFormatter()` — in which case `config.max_context_length`
    still reaches nothing but the SFT job kwargs (fireworks_trainer.py:330) and
    never the file that is uploaded, which is the stated point of the change.

    So, in the code the trainer RUNS (see "Resolving the code that actually
    runs"): at least one assignment to `self.data_formatter` goes through
    `from_config`, and none of them builds the formatter by calling its class.
    Asked of LIVE code, because text was not enough — `if False:` around the
    from_config line, or that line parked after a `return`, scored all eight
    facts while the trainer went on calling the class through a helper, and
    without any such line the same tree fails this fact. Each live assignment is
    then FOLLOWED through the helpers it calls, so factoring the construction out
    (which the ticket does not forbid) is neither punished nor a hiding place.
    The line the ticket replaces is refused wherever it sits, live or dead: a
    correct trainer has no reason to call the formatter class at all.

    "Assignment" is every spelling that stores the attribute — plain,
    `setattr(self, "data_formatter", ...)` and `self.__dict__[...]` — because
    the conforming line followed by a rebind in either of the other two scored
    all eight facts; and a definition is entered on a CALL, not on a mention,
    because `self._wire_ref = self._wire` scored all eight while `_wire` never
    ran.

    The pristine tree is read first to confirm it still builds the formatter the
    old way, so the check cannot silently go stale.
    """
    theirs = _formatter_assignments(_pristine_source(FIREWORKS_TRAINER))
    ok(any(_constructs_formatter(value) for value in theirs),
       f"the pristine {FIREWORKS_TRAINER} no longer builds self.data_formatter by "
       "calling the class; this check is stale")

    source = _submission_source(FIREWORKS_TRAINER)
    for value in _formatter_assignments(source):
        ok(not _constructs_formatter(value),
           f"{FIREWORKS_TRAINER}: self.data_formatter is still built by calling the "
           "formatter class, so config.max_context_length never reaches the uploaded "
           "file; instruction.md:74 makes it FireworksDataFormatter.from_config(config)")

    defs, assigns, returns = _live_module(source)
    ok(assigns,
       f"{FIREWORKS_TRAINER}: nothing the trainer runs assigns self.data_formatter — an "
       "assignment in a dead branch, after a return, or in a definition nothing reaches "
       "wires nothing; instruction.md:74 makes it FireworksDataFormatter.from_config(config)")
    built = _resolved(assigns, defs, returns)
    for value in built:
        ok(not _constructs_formatter(value),
           f"{FIREWORKS_TRAINER}: the formatter the trainer builds at line {value.lineno} "
           "comes from calling the formatter class, so config.max_context_length never "
           "reaches the uploaded file; instruction.md:74 makes it "
           "FireworksDataFormatter.from_config(config)")
    ok(any(_through_from_config(value) for value in built),
       f"{FIREWORKS_TRAINER}: the assignment to self.data_formatter that the trainer "
       "actually runs does not go through from_config(config) — a from_config call in a "
       "dead branch, in a function nothing calls, or in a module this file does not "
       "define carries nothing here; instruction.md:74 is "
       "what carries max_context_length into the formatter the trainer uploads with")


def _called_names(node) -> set:
    """The names of the functions called under a node: `self.<name>(...)` and a
    bare `<name>(...)` — what a call site spells, which is how a definition the
    mechanism was factored into is found."""
    names = set()
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        func = sub.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) \
                and func.value.id == "self":
            names.add(func.attr)
        elif isinstance(func, ast.Name):
            names.add(func.id)
    return names


def _reachable_bodies(functions: dict, start, classname: str) -> list:
    """`start` and every definition it reaches by calling, to a fixpoint.

    ONE level was not enough, and the cost was a false negative rather than a
    bypass: a correct implementation that factored the boundary trick into a
    helper which itself called a second helper scored 0 on a rule it obeys
    (measured). What the ticket keeps is the mechanism; how many functions it is
    spread over is the submission's business.
    """
    seen, bodies, pending = set(), [], [start]
    while pending:
        node = pending.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        bodies.append(node)
        for name in sorted(_called_names(node)):
            for key in (f"{classname}.{name}", name):
                if key in functions:
                    pending.append(functions[key])
                    break
    return bodies



def _generation_prompt_flags(nodes) -> list:
    """The literal `add_generation_prompt=` of every `apply_chat_template(...)`
    call under any of `nodes`. A call that passes a non-literal flag contributes
    `None`, so it can never be mistaken for one of the two the ticket names."""
    flags = []
    for node in nodes:
        for sub in ast.walk(node):
            if not (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
                    and sub.func.attr == "apply_chat_template"):
                continue
            literal = [kw.value.value for kw in sub.keywords
                       if kw.arg == "add_generation_prompt"
                       and isinstance(kw.value, ast.Constant)]
            flags.append(literal[0] if literal else None)
    return flags


def _check_boundary_trick_declared() -> None:
    """The one preservation rule that has no pristine twin to compare.

    instruction.md:33 replaces `_compute_weights` with `_supervised_spans`, and
    :39 says the prefix-tokenization boundary trick inside it is reused
    unchanged: `apply_chat_template(pre, add_generation_prompt=True)` for the
    start index, `apply_chat_template(cumulative, add_generation_prompt=False)`
    for the end. `_check_reuse_rules` cannot cover it — the function that carried
    the trick is the one the ticket rewrites, so there is nothing to be
    byte-identical to. What CAN be compared is the mechanism: the pristine
    function makes exactly those two calls, and the function that replaces it
    must still make them.

    The search follows `self.<method>()` and module-level calls out of
    `_supervised_spans` to a fixpoint, because a submission may factor the two
    renders into a helper — and, measured, into a helper that calls a second
    helper: at one level deep that correct implementation scored 0 on a rule it
    obeys. The rule is about the mechanism, not the layout. Dead code that merely mentions the calls
    does not pass: `judge_open` also requires the calls to have really been made,
    for THIS run's conversation, with the texts handed to `encode` (which is the
    "tokenization" half of prefix tokenization, and the half an implementation
    tailored to the supplied template skips).
    """
    theirs = _functions(_pristine_source(DATA_FORMATTER))
    ok("DataFormatter._compute_weights" in theirs,
       "the pristine tree has no DataFormatter._compute_weights; this check is stale")
    want = sorted({flag for flag in _generation_prompt_flags(
        [theirs["DataFormatter._compute_weights"]]) if flag is not None})
    eq(want, [False, True],
       "the pristine boundary trick no longer renders the template both ways; "
       "this check is stale")

    mine = _functions(_submission_source(DATA_FORMATTER))
    ok(SPANS in mine,
       f"{DATA_FORMATTER}: no {SPANS}; instruction.md:33 replaces _compute_weights with it")
    eq([arg.arg for arg in mine[SPANS].args.args], ["self", "messages", "tokenizer"],
       f"{SPANS} parameters, in order")
    bodies = _reachable_bodies(mine, mine[SPANS], "DataFormatter")
    got = sorted({flag for flag in _generation_prompt_flags(bodies) if flag is not None})
    eq(got, want,
       f"{SPANS}: the prefix-tokenization boundary trick is gone. instruction.md:39 "
       "reuses apply_chat_template(pre, add_generation_prompt=True) for the start "
       "index and apply_chat_template(cumulative, add_generation_prompt=False) for "
       "the end; the flags found were")


def _check_boundary_trick_used(o) -> None:
    """The same rule, from the other side: the calls the trick makes were made.

    For every assistant turn after the first message, the conversation up to it
    must have been rendered WITH a generation prompt and through it WITHOUT one,
    and both texts must have reached `encode` — a span is a token index, so a
    boundary that never went through the tokenizer was not read off the token
    sequence. Spans computed straight from this template's character offsets are
    exactly as correct here and wrong for any real tokenizer, which is why the
    declaration check above is not enough on its own.
    """
    calls = o["template_calls"]
    encoded = {text for text, _ in o["encode_calls"]}
    for index, (role, _) in enumerate(SPEC["good"]):
        if role != "assistant" or index == 0:
            continue
        for through, flag in ((index, True), (index + 1, False)):
            prefix = SPEC["good"][:through]
            what = ("with a generation prompt" if flag else "through the turn")
            ok([prefix, flag] in calls,
               f"assistant turn {index}: the template was never rendered {what} for "
               f"the {through} messages before it; instruction.md:39 keeps the "
               "prefix-tokenization boundary trick")
            text = fixture_spec.render_chat([tuple(pair) for pair in prefix], flag)
            ok(text in encoded,
               f"assistant turn {index}: the prefix rendered {what} was never "
               "tokenized, so its span boundary is not a token index")


def _finetune_modules() -> list:
    """Every module of the pushed finetune package, as (name, parsed tree).

    A file that cannot be read or parsed is skipped rather than ending the
    search: the declaration being looked for may well be in the next file, and a
    module that does not compile fails the behavioural facts on its own.
    """
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", "")) / FINETUNE
    out = []
    for path in sorted(root.rglob("*.py")):
        try:
            out.append((path.name, ast.parse(judge_io.read_text(path))))
        except (OSError, SyntaxError, ValueError):
            continue
    ok(bool(out), f"no readable python files under {root}")
    return out


def _check_bytes_per_token_declared() -> None:
    """`FIREWORKS_BYTES_PER_TOKEN` is really 3 in the source, not just whatever
    the worker reported reading. The constant is the fact; a tree that reports
    the right number without defining it has implemented nothing."""
    for name, tree in _finetune_modules():
        for node in ast.walk(tree):
            targets = ([node.target] if isinstance(node, ast.AnnAssign)
                       else list(getattr(node, "targets", [])))
            if not any(isinstance(t, ast.Name) and t.id == "FIREWORKS_BYTES_PER_TOKEN"
                       for t in targets) or node.value is None:
                continue
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError):
                raise Fail(f"{name}: FIREWORKS_BYTES_PER_TOKEN is not a literal")
            eq(value, FIREWORKS_BYTES_PER_TOKEN, f"{name}: FIREWORKS_BYTES_PER_TOKEN")
            return
    raise Fail("no module under finetune/ defines FIREWORKS_BYTES_PER_TOKEN")


def _check_report_declared() -> None:
    """`EncodingReport` is declared frozen, with those five fields in that order
    and those defaults. Read from the source, because the field order and the
    defaults are the requirement and a worker can claim any list."""
    for name, tree in _finetune_modules():
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or node.name != "EncodingReport":
                continue
            frozen = False
            for deco in node.decorator_list:
                if not isinstance(deco, ast.Call):
                    continue
                func = deco.func
                named = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                if not named.endswith("dataclass"):
                    continue
                for kw in deco.keywords:
                    if kw.arg == "frozen" and isinstance(kw.value, ast.Constant):
                        frozen = frozen or kw.value.value is True
            ok(frozen, f"{name}: EncodingReport is not declared @dataclass(frozen=True)")
            fields, defaults = [], []
            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    fields.append(child.target.id)
                    try:
                        defaults.append(ast.literal_eval(child.value)
                                        if child.value is not None else None)
                    except (ValueError, TypeError, SyntaxError):
                        defaults.append("<not a literal>")
            eq(fields, REPORT_FIELDS, f"{name}: EncodingReport fields, in order")
            eq(tuple(defaults), REPORT_DEFAULTS, f"{name}: EncodingReport defaults")
            return
    raise Fail("no module under finetune/ declares EncodingReport")


# ---------------------------------------------------------------------------
# open feature
# ---------------------------------------------------------------------------
def judge_open(o):
    eq(o["exports"], [True] * 5, "finetune exports")
    eq(o["allowed_roles"], sorted(ALLOWED_ROLES), "ALLOWED_ROLES")
    ok(o["allowed_roles_is_frozenset"],
       "ALLOWED_ROLES is not a frozenset; instruction.md:11 declares it one")
    ok("ValueError" in o["encoding_error_mro"], "EncodingError subclasses ValueError")
    ok("EncodingError" in o["invalid_role_mro"], "InvalidRoleSequenceError subclasses EncodingError")
    ok("EncodingError" in o["tok_cap_mro"], "TokenizerCapabilityError subclasses EncodingError")

    # the ticket's preservation rules, which behaviour cannot show
    _check_reuse_rules()
    _check_boundary_trick_declared()
    _check_fireworks_trainer_wired()

    # this run's five malformed sequences: the reason and the index are worked
    # out here from the roles the fixture drew.
    seen = []
    for info, messages in zip(o["role_cases"], SPEC["role_cases"]):
        roles = [role for role, _ in messages]
        reason, position = first_violation(roles)
        ok(reason is not None, f"fixture: {roles} breaks no rule and grades nothing")
        raised(info, mro="InvalidRoleSequenceError", reason=reason, position=position,
               role_sequence=roles, msg=f"role case {roles}")
        eq(info.get("str"),
           f"invalid role sequence at position {position} ({reason}): {roles}",
           f"role case {roles} str")
        seen.append(reason)
    eq(seen, list(REASONS), "fixture: the five cases must be the five reasons, in order")
    ok(o["legal_returns_none"], "legal conversation returns None")
    ok(o["legal_example_none"], "legal example returns None")

    # the left window, the envelope and the causal shift
    good = expected(SPEC["good"], SPEC["good_max_seq_length"], fixture_spec.render_chat)
    ok(not good["refused"], "fixture: this window must still be encodable")
    ok(good["windowed"], "fixture: this window must actually window")
    obs = o["good"]
    eq(obs["metadata_surface"], ["encoding", "num_messages", "original_text"], "metadata surface")
    eq(obs["original_text"], good["text"], "metadata original_text")
    eq(obs["num_messages"], len(SPEC["good"]), "metadata num_messages")
    eq(obs["encoding_surface"],
       ["supervised_tokens", "token_count", "tokenizer", "window_start", "windowed"],
       "encoding surface")
    ok(obs["tokenizer_is_true"], "encoding tokenizer is True")
    eq(obs["token_count"], good["token_count"], "token_count")
    eq(obs["window_start"], good["window_start"], "window_start")
    ok(obs["windowed_is_bool"], "windowed is not a bool")
    eq(obs["windowed"], True, "windowed")
    eq(obs["model_input"], good["model_input"], "model_input is windowed_tokens[:-1]")
    eq(obs["targets"], good["targets"], "target_tokens is windowed_tokens[1:]")

    # one encode call over the whole text, and nothing that truncates
    for text, kwargs in o["encode_calls"]:
        ok("truncation" not in kwargs and "max_length" not in kwargs,
           f"the tokenizer was asked to truncate: {sorted(kwargs)}")
    whole = [kwargs for text, kwargs in o["encode_calls"] if text == good["text"]]
    ok(whole, "the whole chat text was never handed to encode()")
    for kwargs in whole:
        eq(kwargs.get("add_special_tokens"), False,
           "encode(chat_text, add_special_tokens=False)")

    # the boundary trick was the mechanism, not just a declaration
    _check_boundary_trick_used(o)

    # and the boundaries were read off the TOKEN sequence: under a tokenizer that
    # returns two ids per character, a span sliced on `len(text)` lands at half
    # the index it should. Every other double here is one id per character, where
    # the two are the same number and character arithmetic scores full marks.
    dense = expected(SPEC["good"], SPEC["dense_max_seq_length"], fixture_spec.render_chat,
                     per_char=2)
    ok(not dense["windowed"] and not dense["refused"],
       "fixture: the dense window must be wide enough to leave this conversation whole")
    dense_obs = o["dense"]
    eq(dense_obs["token_count"], dense["token_count"],
       "token_count under a tokenizer that is not one id per character")
    eq(dense_obs["window_start"], dense["window_start"], "dense window_start")
    eq(dense_obs["model_input"], dense["model_input"], "dense model_input")
    eq(dense_obs["weights"], dense["weights"],
       "the assistant spans must be token indices from the encoded prefixes, not "
       "character offsets into the rendered text")
    eq(dense_obs["supervised_tokens"], dense["supervised"], "dense supervised_tokens")
    for text, kwargs in o["dense_encode_calls"]:
        ok("truncation" not in kwargs and "max_length" not in kwargs,
           f"the tokenizer was asked to truncate: {sorted(kwargs)}")
    ok(any(text == dense["text"] for text, _ in o["dense_encode_calls"]),
       "the whole chat text was never handed to encode() on the dense tokenizer")

    # instruction.md:36 — the deleted fallback. A tokenizer that raises while the
    # spans are computed reaches the caller as itself, and is not smoothed into
    # all-ones weights or translated into an EncodingError.
    for key, what in (("template_raises", "apply_chat_template"), ("encode_raises", "encode")):
        info = o[key]
        raised(info, mro=fixture_spec.TokenizerFailure.__name__,
               msg=f"a tokenizer whose {what} raises")
        eq(info.get("str"), fixture_spec.TokenizerFailure.MESSAGE,
           f"the {what} failure must propagate unchanged")
        ok("EncodingError" not in info.get("mro", []),
           f"the {what} failure was translated into an EncodingError; "
           "instruction.md:36 propagates it unchanged")

    # instruction.md:34 — the role check comes first, so an example that breaks
    # both rules reports the roles and not the tokenizer
    bad_roles = [role for role, _ in SPEC["bad_roles"]]
    reason, position = first_violation(bad_roles)
    ok(reason is not None, f"fixture: {bad_roles} breaks no rule and grades nothing")
    raised(o["roles_before_tokenizer"], mro="InvalidRoleSequenceError", reason=reason,
           position=position,
           msg="validate_role_sequence runs before the tokenizer is inspected")

    # instruction.md:75 — to_jsonl_lines validates the role sequences too
    raised(o["jsonl_bad_roles"], mro="InvalidRoleSequenceError", reason=reason,
           position=position, role_sequence=bad_roles,
           msg="to_jsonl_lines on a malformed role sequence")

    # the no-tokenizer branch carries its text too
    plain = expected(SPEC["plain"], SPEC["plain_max_seq_length"])
    eq(o["plain"]["original_text"], plain["text"], "plain original_text")
    ok(o["plain"]["tokenizer_is_false"], "plain tokenizer is False")
    eq(o["plain"]["num_messages"], len(SPEC["plain"]), "plain num_messages")

    # a tokenizer with no chat template is refused, whatever the masking mode
    for info in o["no_template"]:
        raised(info, mro="TokenizerCapabilityError", missing_method="apply_chat_template",
               msg="no chat template")
        eq(info.get("str"), "tokenizer is missing required method 'apply_chat_template'",
           "no chat template str")

    # from_config carries max_context_length
    ok(o["made_is_fireworks"], "from_config returns a FireworksDataFormatter")
    eq(o["made_max_seq_length"], SPEC["context_small"], "max_context_length carried")
    ok(o["made_train_on_assistant_only_is_true"], "train_on_assistant_only default True")
    eq(o["fallback_max_seq_length"], DEFAULT_MAX_SEQ_LENGTH, "max_context_length fallback")
    eq(o["large_max_seq_length"], SPEC["context_large"],
       "a max_context_length above the default wins")


# ---------------------------------------------------------------------------
# r1 — how an example that does not fit is encoded
# ---------------------------------------------------------------------------
def judge_r1_rule(o):
    narrow = expected(SPEC["good"], SPEC["good_max_seq_length"], fixture_spec.render_chat)
    ok(not narrow["refused"], "fixture: this window must still be encodable")
    first_start, first_end = narrow["spans"][0]
    ok(first_start < narrow["window_start"] < first_end,
       "fixture: the window boundary must fall inside the first assistant turn, "
       f"not at {narrow['window_start']} against {narrow['spans']}")

    obs = o["narrow"]
    ok(all(isinstance(weight, float) for weight in obs["weights"]),
       f"weights are not floats: {obs['weights'][:8]}")
    eq(obs["weights"], narrow["weights"],
       "the straddling span must contribute nothing, not its surviving tail")
    eq(obs["supervised_tokens"], narrow["supervised"], "supervised_tokens")

    wide = expected(SPEC["good"], SPEC["wide_max_seq_length"], fixture_spec.render_chat)
    ok(0 < wide["window_start"] <= wide["spans"][0][0],
       "fixture: the wide window must start inside the prompt")
    eq(o["wide"]["window_start"], wide["window_start"], "wide window_start")
    eq(o["wide"]["weights"], wide["weights"], "wide weights")
    eq(o["wide"]["supervised_tokens"], wide["supervised"], "wide supervised_tokens")


def judge_r1_scope(o):
    plain = expected(SPEC["plain"], SPEC["plain_max_seq_length"])
    ok(0.0 in plain["weights"] and 1.0 in plain["weights"],
       "fixture: the mock path must supervise part of the sequence and not all of it")
    obs = o["plain"]
    ok(obs["tokenizer_is_false"], "plain tokenizer is False")
    eq(obs["token_count"], plain["token_count"], "plain token_count")
    eq(obs["window_start"], 0, "plain window_start")
    eq(obs["supervised_tokens"], plain["supervised"],
       "the mock path must honour train_on_assistant_only, with the header inside the span")
    eq(obs["weights"], plain["weights"], "plain weights")
    eq(obs["model_input"], plain["model_input"], "plain model_input")

    everything = expected(SPEC["plain"], SPEC["plain_max_seq_length"], assistant_only=False)
    eq(o["everything"]["weights"], everything["weights"],
       "train_on_assistant_only=False is all ones")
    eq(o["everything"]["supervised_tokens"], everything["supervised"],
       "everything supervised_tokens")

    windowed = expected(SPEC["good"], SPEC["good_max_seq_length"], fixture_spec.render_chat,
                        assistant_only=False)
    eq(o["windowed_all_ones"]["weights"], windowed["weights"],
       "windowed all-ones on the tokenizer path")

    # The other half of the same clause: this path WINDOWS, like the tokenizer
    # one. The scenario above never does (its budget is far wider than its
    # conversation), and that gap was measured — a tree that windowed only the
    # tokenizer path scored every fact here while the repository's own
    # tests/finetune/test_data_formatter.py::test_max_seq_length, which
    # instruction.md:83 says must still pass, failed on it. This draw's boundary
    # falls in the prompt, before the first assistant turn, so a wrong straddle
    # policy fails r1's rule fact and not this one as well.
    plain_windowed = expected(SPEC["plain_windowed"], SPEC["plain_windowed_max_seq_length"])
    ok(plain_windowed["windowed"] and not plain_windowed["refused"],
       "fixture: the windowed tokenizer-free example must window and still be encodable")
    pw = o["plain_windowed"]
    ok(pw["tokenizer_is_false"], "windowed plain tokenizer is False")
    eq(pw["token_count"], plain_windowed["token_count"], "windowed plain token_count")
    eq(pw["window_start"], plain_windowed["window_start"],
       "the tokenizer-free branch must take the same window as the tokenizer one, "
       "window_start = max(0, token_count - max_seq_length)")
    eq(pw["windowed"], True, "windowed plain windowed flag")
    eq(pw["weights"], plain_windowed["weights"],
       "the tokenizer-free weights must be built over the untruncated sequence and "
       "sliced with the same window_start")
    eq(pw["model_input"], plain_windowed["model_input"], "windowed plain model_input")
    eq(pw["targets"], plain_windowed["targets"], "windowed plain target_tokens")
    eq(pw["supervised_tokens"], plain_windowed["supervised"],
       "windowed plain supervised_tokens")
    eq(pw["original_text"], plain_windowed["text"], "windowed plain original_text")


def judge_r1_exclusions(o):
    eq(o["bytes_per_token"], FIREWORKS_BYTES_PER_TOKEN, "FIREWORKS_BYTES_PER_TOKEN")
    _check_bytes_per_token_declared()

    kept, dropped = fireworks_kept(SPEC["fw_examples"], SPEC["fw_max_seq_length"])
    budget = SPEC["fw_max_seq_length"] * FIREWORKS_BYTES_PER_TOKEN
    ok(kept and dropped,
       f"fixture: {len(kept)} kept and {len(dropped)} dropped at budget {budget} "
       "grades only one side of the cut")
    ok(any(len(fireworks_line(pairs).encode("utf-8")) == budget
           for pairs in SPEC["fw_examples"]),
       "fixture: no line lands exactly on the budget, so the boundary is untested")
    ok(any(len(fireworks_line(pairs)) <= budget < len(fireworks_line(pairs).encode("utf-8"))
           for pairs in SPEC["fw_examples"]),
       "fixture: no line has more UTF-8 bytes than characters across the budget, so "
       "counting characters instead would score the same")
    eq(o["lines"], kept,
       "the kept lines must be exactly the lines inside the byte budget, whole")
    eq(o["lines_byte_lens"], [len(line.encode("utf-8")) for line in kept],
       "kept line byte lengths")
    eq(o["lines_decoded"], [json.loads(line) for line in kept],
       "nothing on this path is truncated")


def judge_r1_failure_behavior(o):
    ok("EncodingError" in o["example_too_long_mro"], "ExampleTooLongError subclasses EncodingError")

    too_long = expected(SPEC["too_long"], SPEC["good_max_seq_length"], fixture_spec.render_chat)
    ok(too_long["refused"], "fixture: this example must be refused")
    raised(o["too_long_error"], mro="ExampleTooLongError",
           token_count=too_long["token_count"],
           max_seq_length=SPEC["good_max_seq_length"],
           retained_prompt_tokens=too_long["retained"],
           num_messages=len(SPEC["too_long"]), msg="over-long refusal")
    ok("ValueError" in o["too_long_error"].get("mro", []),
       "ExampleTooLongError isinstance ValueError")
    eq(o["too_long_error"].get("str"),
       f"example of {too_long['token_count']} tokens exceeds "
       f"max_seq_length={SPEC['good_max_seq_length']}: {too_long['retained']} prompt "
       f"tokens would survive, minimum is {MIN_RETAINED_PROMPT_TOKENS}",
       "over-long refusal str")

    good = expected(SPEC["good"], SPEC["good_max_seq_length"], fixture_spec.render_chat)
    ok(not good["refused"] and good["retained"] >= MIN_RETAINED_PROMPT_TOKENS,
       "fixture: the windowed conversation must be kept")
    eq(o["good_window_start"], good["window_start"], "windowed example kept")

    tight = expected(SPEC["good"], SPEC["tight_max_seq_length"], fixture_spec.render_chat)
    ok(tight["refused"], "fixture: this window must be refused")
    raised(o["tight_error"], mro="ExampleTooLongError",
           retained_prompt_tokens=tight["retained"], token_count=tight["token_count"],
           num_messages=len(SPEC["good"]),
           msg=f"only {tight['retained']} prompt tokens survive")

    unwindowed = expected(SPEC["short_header"], SPEC["short_header_max_seq_length"],
                          fixture_spec.render_short_header)
    eq(o["unwindowed"]["window_start"], 0, "unwindowed window_start")
    eq(o["unwindowed"]["token_count"], unwindowed["token_count"], "unwindowed token_count")

    batch = batch_outcome(SPEC["batch"], SPEC["good_max_seq_length"])
    ok(batch["kept"] and batch["dropped"],
       "fixture: the batch must have something to keep and something to drop")
    eq(o["batch_len"], len(batch["kept"]), "format_batch skips the refused rows")
    eq(o["batch_num_messages"], [len(pairs) for _, pairs, _ in batch["kept"]],
       "the surviving rows, in input order")
    eq(o["batch_window_starts"], [result["window_start"] for _, _, result in batch["kept"]],
       "the surviving rows' windows")


# ---------------------------------------------------------------------------
# r2 — what the formatter tells the caller it threw away
# ---------------------------------------------------------------------------
def judge_r2_rule(o):
    ok(o["report_is_dataclass"], "EncodingReport is a dataclass")
    ok(o["report_frozen_is_true"], "EncodingReport is frozen")
    eq(o["report_fields"], REPORT_FIELDS, "EncodingReport fields, in order")
    eq(o["default_report"], DEFAULT_REPORT, "EncodingReport defaults")
    _check_report_declared()

    batch = batch_outcome(SPEC["batch"], SPEC["good_max_seq_length"])
    ok(batch["kept"] and batch["dropped"],
       "fixture: the batch must have something to keep and something to drop")
    ok(o["kept_is_list"], "format_batch still returns a plain list")
    eq(o["kept_len"], len(batch["kept"]), "one datum per kept row")
    # The first four counters are recomputed here; `supervised_tokens` is checked
    # against what the kept data themselves reported, because r2's claim is that
    # the report SUMS THE KEPT ROWS — whether each row's count is right is r1's
    # rule fact, and grading it twice would make one wrong weight policy fail two
    # facts.
    eq(o["report"][:4], batch["report"][:4],
       "the report counts the kept, the dropped, their input positions and how many "
       "were windowed")
    eq(o["report"][4], sum(o["kept_supervised"]),
       "supervised_tokens sums the kept examples, matching the kept data themselves")

    clean = batch_outcome(SPEC["batch"], SPEC["clean_max_seq_length"])
    ok(not clean["dropped"], "fixture: the wide window must drop nothing")
    eq(o["clean_data_len"], len(SPEC["batch"]), "the clean pass keeps every row")
    eq(o["clean_report"][:4], clean["report"][:4], "clean report counters")
    eq(o["clean_report"][4], sum(o["clean_supervised"]),
       "clean supervised_tokens is the sum of the kept data")

    lines, dropped = fireworks_kept(SPEC["fw_report_examples"],
                                    SPEC["fw_report_max_seq_length"])
    ok(lines and dropped, "fixture: the fireworks pass must keep and drop")
    ok(o["fw_lines_is_list"], "to_jsonl_lines returns a list")
    eq(o["fw_lines"], lines, "the fireworks lines")
    eq(o["fw_report"], [len(lines), len(dropped), 0, dropped, 0],
       "fireworks report, tokenizer counters at zero")


def judge_r2_scope(o):
    eq(o["fresh_report"], DEFAULT_REPORT, "a fresh formatter carries the all-defaults report")
    batch = batch_outcome(SPEC["batch"], SPEC["good_max_seq_length"])
    # require_feature: crediting "to_tinker_datum leaves it alone" needs proof
    # that something writes the report in the first place.
    eq(o["after_batch"][:4], batch["report"][:4], "format_batch writing self.last_report")
    good = expected(SPEC["good"], SPEC["good_max_seq_length"], fixture_spec.render_chat)
    eq(o["datum_window_start"], good["window_start"], "the single-example datum was windowed")
    eq(o["report_after_success"], o["after_batch"],
       "a successful single call does not touch the report")
    raised(o["raise_too_long"], mro="ExampleTooLongError", msg="over-long single call")
    eq(o["report_after_raise"], o["after_batch"],
       "a raising single call does not touch the report")


def judge_r2_failure_behavior(o):
    batch = batch_outcome(SPEC["batch"], SPEC["good_max_seq_length"])
    ok(batch["dropped"], "fixture: the batch must drop something")
    eq(o["before"][:4], batch["report"][:4],
       "the over-long rows must be absorbed as drops, not raised")
    raised(o["raise_bad_roles"], mro="InvalidRoleSequenceError", msg="bad roles abort")
    eq(o["report_after_bad_roles"], o["before"],
       "an aborted pass must not write a partial report")
    raised(o["raise_bad_tok"], mro="TokenizerCapabilityError", msg="bad tokenizer aborts")
    eq(o["report_after_bad_tok"], o["before"],
       "an aborted pass must not write a partial report")


JUDGES = {
    "test_open::test_open_feature__roles_are_validated_and_an_over_long_example_keeps_its_completion": judge_open,
    "test_r1::test_rule__an_assistant_turn_the_window_cuts_in_half_is_not_supervised_at_all": judge_r1_rule,
    "test_r1::test_scope__the_tokenizer_free_branch_supervises_assistant_spans_from_character_offsets": judge_r1_scope,
    "test_r1::test_exclusions__fireworks_drops_over_budget_lines_by_utf8_bytes_and_truncates_nothing": judge_r1_exclusions,
    "test_r1::test_failure_behavior__a_windowed_example_with_under_sixteen_prompt_tokens_is_refused": judge_r1_failure_behavior,
    "test_r2::test_rule__both_batch_entry_points_publish_a_frozen_encoding_report": judge_r2_rule,
    "test_r2::test_scope__only_the_batch_entry_points_write_the_report": judge_r2_scope,
    "test_r2::test_failure_behavior__bad_roles_and_a_bad_tokenizer_abort_the_batch_and_write_no_report": judge_r2_failure_behavior,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g9_example_encoding" '
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
    defect = fixture_defect(SPEC)
    if defect:
        print(f"judge: this run's draw is unusable ({seed}): {defect}", file=sys.stderr)

    try:
        observations = json.loads(judge_io.read_text(obs_path))
    except (OSError, ValueError) as exc:
        observations = {}
        print(f"judge: cannot read observations: {exc}", file=sys.stderr)

    results = []
    for node, judge in JUDGES.items():
        classname, name = node.split("::", 1)
        if defect:
            results.append((classname, name, f"fixture invariant: {defect}"))
            continue
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
    # argv: observations, junit out, seed, artifacts dir. g9's scenarios are pure
    # in-process, so there is nothing in the artifacts directory to read.
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
