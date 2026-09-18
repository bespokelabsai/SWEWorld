"""g4 judge: the process that decides pass/fail and NEVER imports the submission.

Reads the observations `probe.py` wrote, the directories the probe's scenarios
left under the artifacts root, and the cloned source text; writes a `junit.xml`
whose `classname`/`name` are the suite's node ids — so `score.py` folds them into
the fact keys and `test.sh`/`score.py` are unchanged. It runs as root, stdlib
only. The worker cannot read it: `test.sh` keeps /tests root-only for a split
suite, and the worker's jail holds only `probe.py`, `probe_support.py`,
`fixture_spec.py` and `harness.py`.

WHY THE ANSWERS HERE ARE NOT ENOUGH ON THEIR OWN. Keeping this file unreadable
stopped the worker copying the expected values out of it. It did not stop the
worker writing them anyway: the answers are the planted requirement, which the
world publishes, and the old fixture was the same every run. A capture of one
correct run replayed onto a tree that implemented nothing passed every hidden
fact, and r2.failure_behavior was almost entirely exception names the worker
reported. Four things close that:

  * **the inputs move every run.** `fixture_spec.derive(seed)` re-draws the
    model, dataset hash, generation params, system prompt, response model,
    prompt and parse functions, backend-knob values and combinations, run ids
    and rows, and this file works out the components an identity over THOSE
    inputs must carry. A run hash cannot be predicted from the seed alone —
    the payload's spelling is the implementation's — so hashes are graded
    relationally, but always beside the seeded components they were computed
    from, and never alone for a fact;
  * **the digest is re-derived, not inferred.** `xxh64_ref.py` is XXH64 in the
    stdlib, so `check_digest_recomputed` re-hashes the payload the module
    actually fed to xxh64 (kept by the worker as it ran) and requires the
    digest to BE that value, over bytes that carry the seeded inputs and a
    version tag. The shape check and the reordered-params scenario still run
    around it, and the hash library the source reaches for is reported beside
    the results, but those are proxies and none of them decides the fact: the
    v7 "Verifiable" review was right that proxies pass an unused `xxh64` call
    beside a hand-rolled hash, and the v9 one was right that a source scan
    reading call sites rejects a correct module that holds its entry point in
    a dict, on a class or in a default argument;
  * **the directories are read here.** The stamp `write_run_stamp` wrote, the
    cache directories `LLM.__call__` created and the stamps inside them: this
    process opens them under the artifacts root, refusing symlinks, and checks
    them against the run's inputs rather than trusting a flag;
  * **the constants that cannot be re-drawn are read out of the source** as
    well as the run: `IDENTITY_COMPONENT_KEYS`, `IDENTITY_BACKEND_PARAM_KEYS`.

The residual, stated plainly: a submission that implements the requirement inside
a forged hook — computing, from `fixture_spec`, what a correct implementation
would have produced — still passes, because it has then done the work. What is
gone is passing by repeating values that were knowable in advance.

`test_open`/`test_r1`/`test_r2` stay the human-readable reference for what each
fact means; their worked example uses the old fixed fixture ("d0",
"local-run-7"). They live in the repository's `_suites/g4_run_cache_identity/`
beside this file and are NOT shipped with the task: a split suite grades through
the probe and this judge, so shipping them would put three unread files in the
task directory.
"""
from __future__ import annotations

import ast
import base64
import json
import os
import pathlib
import stat
import sys
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_spec  # noqa: E402 - same derivation the worker used
import xxh64_ref  # noqa: E402 - XXH64 in the stdlib, so the digest is re-derived and not argued about

# The judge runs `python3 -I` with no PYTHONPATH, so /tests is not importable by
# default. judge_io holds the hardened reads (no symlink, regular file only,
# size cap, raises rather than returning empty) that EVERY agent-influenced path
# goes through: the worker's artifacts, the observations file and the cloned
# submission are all paths the agent can shape. Every suite reads them the same
# way through it, and g4 keeping a second copy of that logic was what the TB3
# "No extraneous files" review failed v9 for. harness.py cannot serve this — it
# imports pytest, which this interpreter does not have.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import judge_io  # noqa: E402


class Fail(AssertionError):
    pass


def eq(got, want, msg=""):
    if got != want:
        raise Fail(f"{msg}: {got!r} != {want!r}")


def ne(got, other, msg=""):
    if got == other:
        raise Fail(f"{msg}: {got!r} == {other!r} (should differ)")


def ok(cond, msg=""):
    if not cond:
        raise Fail(msg)


# Observations worth telling a reviewer that must NOT decide a fact. A check
# belongs here once something else settles the same question by measurement:
# keeping it as an assertion then buys no accuracy and can only fail a correct
# submission for an incidental reason (the hash-library import ban did exactly
# that — see `report_digest_hash_sources`). `main` prints these after the results.
DIAGNOSTICS: list = []


def diag(msg: str) -> None:
    DIAGNOSTICS.append(msg)


def raised(info, *, mro=None, msg="", **attrs):
    ok(isinstance(info, dict) and info.get("raised"), f"{msg}: expected an exception, none raised")
    if mro is not None:
        ok(mro in info.get("mro", []), f"{msg}: {mro} not in {info.get('mro')} ({str(info.get('str', ''))[:200]})")
    for name, value in attrs.items():
        eq(info.get(name), value, f"{msg}: {name}")


def value_of(step, msg):
    """The value of a probe step recorded with `attempt`, or the step's failure."""
    ok(isinstance(step, dict), f"{msg}: not measured")
    ok("error" not in step, f"{msg}: {step.get('error')}")
    return step.get("value")


# ---------------------------------------------------------------------------
# The answers
# ---------------------------------------------------------------------------
TWELVE = [
    "backend", "backend_params", "batch_mode", "dataset_hash", "generation_params",
    "model_name", "parse_func_hash", "prompt_func_hash", "response_format",
    "return_completions_object", "run_id", "system_prompt",
]
IDENTITY_BACKEND_KEYS = {"azure_deployment", "base_url", "batch_size", "completion_window"}
NOT_IDENTITY_KEYS = set(fixture_spec.KNOBS) - IDENTITY_BACKEND_KEYS
FN_HASH_NONE = "ef46db3751d8e999"
STAMP = "run_identity.json"
RUN_ID_PARAM = "run_id"
RUN_ID_ENV = "CURATOR_RUN_ID"
NOCACHE_PREFIX = "v3-nocache-"
NOCACHE_LEN = 27
BANNED_IMPORTS = {"random", "secrets", "uuid"}

# The digest is an xxh64 hexdigest (ticket §2). Shape cannot say which hash
# produced it, and neither can the source: both are REPORTED by
# `report_digest_hash_sources` and neither decides anything.
# `check_digest_recomputed` decides where the digest actually came from, by
# re-hashing the bytes the module fed to xxh64.
XXH64_NAMES = {"xxh64", "xxh64_hexdigest", "xxh64_intdigest", "xxh64_digest"}
BANNED_HASH_MODULES = {"hashlib", "hmac", "blake3", "mmh3", "cityhash", "farmhash",
                       "zlib", "binascii", "Crypto", "cryptography"}
MOVED_VERBATIM = "_get_function_hash"
BASELINE_ENV = "CURATOR_BASELINE_DIR"

# The open feature's own dataset, as probe.py builds it: two rows, columns a, b.
DS_SIZE = 2
DS_COLUMNS = ["a", "b"]

SURFACE_NAMES = ("RunIdentity", "RunStamp", "RunDirectoryCheck", "RunIdentityError",
                 "RunIdentityMismatch", "CachedResponseMismatch", "compute_run_identity",
                 "write_run_stamp", "read_run_stamp", "reconcile_run_directory", "_get_function_hash")

DATACLASS_FIELDS = {
    "RunIdentity": ["run_hash", "digest", "identity_version", "cache_enabled", "components"],
    "RunStamp": ["identity_version", "run_hash", "digest", "components", "created_at", "updated_at"],
    "RunDirectoryCheck": ["status", "stamp", "previous_version"],
}

NOW = "2025-01-02T03:04:05"
LATER = "2025-01-02T04:00:00"

# Where `sym` looks for a module-level name, as source files.
SYMBOL_FILES = ("bespokelabs/curator/run_identity.py", "bespokelabs/curator/run_identity",
                "bespokelabs/curator/__init__.py", "bespokelabs/curator/llm/llm.py",
                "bespokelabs/curator/db.py", "bespokelabs/curator/types/curator_response.py")

SPEC: dict = {}
ARTIFACTS = pathlib.Path("/nonexistent")


def _is_hex(value, width=None) -> bool:
    return (isinstance(value, str) and (width is None or len(value) == width) and value != ""
            and all(c in "0123456789abcdef" for c in value))


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
    """A file under the artifacts root, read through `judge_io` behind the walk.

    The component walk above is g4's own, because `judge_io` opens one path: the
    worker owns these directories, so a symlink can be any component and not
    just the last one. The open itself is `judge_io`'s (O_NOFOLLOW, regular file
    only, size cap, raising rather than returning empty), so every judge in the
    suite refuses the same things in the same way. The 4 MiB cap stays: the
    largest legitimate artifact here is a stamp file of a few hundred bytes, and
    the bytes reach a failure message that junit.xml carries out of the run.
    """
    path = _safe_path(rel)
    try:
        return judge_io.read_bytes(path, limit=4 * 1024 * 1024)
    except OSError as exc:
        raise Fail(f"{rel}: {exc}")


def entries(dirrel: str) -> tuple:
    """(directories, regular files) directly under ARTIFACTS/dirrel, symlinks refused."""
    path = _safe_path(dirrel)
    ok(stat.S_ISDIR(os.lstat(path).st_mode), f"{dirrel}: not a directory")
    dirs, files = [], []
    for name in sorted(os.listdir(path)):
        st = os.lstat(path / name)
        ok(not stat.S_ISLNK(st.st_mode), f"{dirrel}/{name}: is a symlink")
        if stat.S_ISDIR(st.st_mode):
            dirs.append(name)
        elif stat.S_ISREG(st.st_mode):
            files.append(name)
    return dirs, files


def stamp_in(dirrel: str) -> tuple:
    """(parsed stamp, raw text) of the stamp inside a run directory."""
    raw = read_bytes(f"{dirrel}/{STAMP}").decode("utf-8", errors="replace")
    try:
        parsed = json.loads(raw)
    except ValueError as exc:
        raise Fail(f"{dirrel}/{STAMP}: not JSON: {exc}")
    ok(isinstance(parsed, dict), f"{dirrel}/{STAMP}: not a JSON object")
    return parsed, raw


def run_directory(dirrel: str, name: str) -> dict:
    """A cache run directory `LLM.__call__` made: named for its stamp's run hash,
    and stamped with this run's drawn model — so it was made THIS run."""
    stamp, raw = stamp_in(f"{dirrel}/{name}")
    eq(stamp.get("run_hash"), name, f"{dirrel}/{name}: the directory is named for its stamp's run hash")
    ok(SPEC["call_model"] in raw,
       f"{dirrel}/{name}: the stamp does not describe this run's model {SPEC['call_model']!r}")
    components = stamp.get("components")
    ok(isinstance(components, dict), f"{dirrel}/{name}: the stamp carries no components")
    return components


# ---------------------------------------------------------------------------
# reading the submission's source — for the constants that cannot be re-drawn
# ---------------------------------------------------------------------------
def _symbol_sources():
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    for rel in SYMBOL_FILES:
        path = root / rel
        files = sorted(path.rglob("*.py")) if path.is_dir() else [path]
        for file in files:
            if not file.is_file():
                continue
            try:
                yield judge_io.read_text(file)
            except OSError:
                # A symlinked, irregular or oversized "source file" is not source
                # the judge will read: the caller then fails its fact for the
                # symbol it could not find, which is the honest outcome.
                continue


def _literal(node):
    """A literal value, or the set a `frozenset({...})`/`set([...])` call spells; else raises."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id in ("frozenset", "set", "tuple", "list") and len(node.args) == 1 and not node.keywords:
        inner = ast.literal_eval(node.args[0])
        return set(inner) if node.func.id in ("frozenset", "set") else list(inner)
    return ast.literal_eval(node)


def defined(name: str, check):
    """The module-level assignment of `name` somewhere `sym` looks, handed to
    `check` when it is a literal.

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
                    literal = _literal(value)
                except (ValueError, TypeError, SyntaxError):
                    continue
                check(literal, f"{name} as written in the source")
    ok(seen, f"no module of bespokelabs.curator assigns {name}")


def _run_identity_source() -> str:
    """The submission's `run_identity` module as text, from SUBMISSION_SRC.

    Parsing text executes nothing, which is why this process can read the
    module the worker imported without becoming a second importer of it.
    """
    root = pathlib.Path(os.environ.get("SUBMISSION_SRC", ""))
    candidates = ["bespokelabs/curator/run_identity.py",
                  "bespokelabs/curator/run_identity/__init__.py"]
    for rel in candidates:
        path = root / rel
        if not path.is_file():
            continue
        try:
            return judge_io.read_text(path)
        except OSError as exc:
            raise Fail(f"cannot read {path}: {exc}")
    raise Fail(f"cannot read run_identity source at any of {candidates} under {root}")


def _called(func) -> str:
    """The name a call is spelled with: `f()`, `mod.f()` and `obj.f()` alike."""
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _funcdefs(source: str, name: str) -> list:
    """Every `def name(...)` in `source`, at any nesting."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise Fail(f"unparseable source: {exc}")
    return [node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]


def _declared_frozen(node: ast.ClassDef) -> bool:
    """True iff a decorator on this class passes `frozen=True`."""
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call):
            for kw in decorator.keywords:
                if kw.arg == "frozen" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    return True
    return False


def check_frozen_dataclasses():
    """All three identity dataclasses are frozen (ticket §1).

    A mutation attempt can only catch a class the worker instantiated, and the
    worker instantiates RunIdentity, RunStamp and RunDirectoryCheck but not
    every implementation's spelling of them — the TB3 "Verifiable" review failed
    v6 for grading frozenness on RunIdentity alone. The declaration is read
    here, so a mutable RunStamp fails whether or not a scenario touched it.
    """
    found: dict = {}
    for src in _symbol_sources():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in DATACLASS_FIELDS:
                found.setdefault(node.name, []).append(_declared_frozen(node))
    for name in DATACLASS_FIELDS:
        declared = found.get(name)
        ok(declared, f"no module of bespokelabs.curator declares class {name}")
        ok(all(declared), f"{name} is not declared frozen; the ticket asks for frozen dataclasses")


def _xxh64_spellings(tree: ast.AST) -> set:
    """Every name that refers to an xxh64 entry point in this module.

    `from xxhash import xxh64 as _h` and a module-level `_h = xxh64` are both
    correct, and reading only the four published names called a module that
    does it that way "some other hash" — the same false negative the worker's
    capture had. Aliases are resolved from the module's own imports and
    assignments, so the call can be spelled however the author spelled it.
    """
    names = set(XXH64_NAMES)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "xxhash":
            for alias in node.names:
                if alias.name in XXH64_NAMES:
                    names.add(alias.asname or alias.name)
    for _ in range(3):        # `a = xxh64` then `b = a`: resolve short chains
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if isinstance(value, ast.Name) and value.id in names:
                names |= {t.id for t in targets if isinstance(t, ast.Name)}
            elif isinstance(value, ast.Attribute) and value.attr in XXH64_NAMES:
                names |= {t.id for t in targets if isinstance(t, ast.Name)}
    return names


def report_digest_hash_sources():
    """Which hash the module reaches for, read off the source (ticket §2) —
    REPORTED, and no longer asserted at all.

    `check_digest_recomputed` decides ticket §2 by re-deriving the digest from
    the bytes the module really hashed, and everything this scan can say is a
    proxy around that. Two of its assertions have now been demoted in turn for
    the same reason, and the reason is worth keeping: a proxy that cannot make
    the verdict more accurate can only make it wrong.

      * the import ban went in v9. The ticket says the digest is an xxh64
        hexdigest; it does not say `run_identity` may not import `hashlib`,
        `binascii` or `zlib` for something else, and a module that really
        hashes with one of them fails the re-hash whatever its imports look
        like (tested: the sha256[:16] variant, including the `__import__`
        spelling that dodges this scan entirely).
      * "something outside the moved function hash calls xxh64" goes now. It
        reads CALL SITES, so it can only recognise a hasher reached through a
        name — and a correct module that keeps its entry point in a dict
        (`_HASHERS["xxh64"](payload)`), on a class (`_H.fn(payload)`) or in a
        default argument (`def _d(payload, _h=xxh64)`) calls it through a
        subscript, an attribute or a parameter. Those are the same three
        patterns the capture used to miss, and the TB3 "Verifiable" review
        failed v9 over them; widening the capture to see them and leaving this
        scan to reject them would have moved the false negative rather than
        removed it. What the scan was standing in for — that the run reached
        xxh64 at all — is now MEASURED: `check_digest_recomputed` fails the
        fact when no xxh64 call was captured while the identity was computed.
    """
    source = _run_identity_source()
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise Fail(f"run_identity does not parse: {exc}")

    banned = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            banned += [a.name for a in node.names if a.name.split(".")[0] in BANNED_HASH_MODULES]
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in BANNED_HASH_MODULES:
                banned.append(node.module)
    if banned:
        diag(f"run_identity imports {sorted(set(banned))}; if the digest came from one of them "
             f"check_digest_recomputed is what fails, not this")

    # The moved `_get_function_hash` already calls xxh64, so its calls say
    # nothing about the DIGEST.
    inside = {id(n) for fn in _funcdefs(source, MOVED_VERBATIM) for n in ast.walk(fn)}
    spellings = _xxh64_spellings(tree)
    named = any(isinstance(n, ast.Call) and id(n) not in inside and _called(n.func) in spellings
                for n in ast.walk(tree))
    diag(f"run_identity calls xxh64 under a name the source resolves, outside {MOVED_VERBATIM}: "
         f"{named} (a dict entry, a class attribute or a default argument reads as False here and "
         f"is graded by the re-hash, not by this)")


def _canonical_bodies(components: dict) -> list:
    """Plausible spellings of the components with NO version tag anywhere in them.

    Used only to REFUSE: a digest that is the xxh64 of one of these is the second
    half of the v7 "Verifiable" finding — "an xxh64 of sorted components without
    the required version tag would pass". Widening this list can only reject
    more payloads, never accept more, so it errs wide. Version-ish keys are
    dropped from the mapping first: a submission that tags the payload by
    serialising the version INSIDE it has met the requirement, and its own
    rendering must not be read back as an untagged one.
    """
    plain = {k: v for k, v in components.items() if "version" not in str(k).lower()}
    items = sorted(plain.items())
    bodies = []
    for ensure_ascii in (True, False):
        for sep in ((",", ":"), (", ", ": ")):
            bodies.append(json.dumps(plain, sort_keys=True, separators=sep, ensure_ascii=ensure_ascii))
        bodies.append(json.dumps(plain, sort_keys=True, indent=2, ensure_ascii=ensure_ascii))
    bodies.append(repr(dict(items)))
    bodies.append("\n".join(f"{k}={v!r}" for k, v in items))
    bodies.append("\n".join(f"{k}={json.dumps(v, sort_keys=True)}" for k, v in items))
    bodies.append("\n".join(f"{k}:{json.dumps(v, sort_keys=True)}" for k, v in items))
    return [spelling for body in bodies for spelling in (body, body + "\n")]


def _spellings(value, depth: int = 2) -> list:
    """How one component key or value might be written into a payload."""
    forms = [repr(value), str(value)]
    for kwargs in ({"separators": (",", ":")}, {"separators": (", ", ": ")}, {"indent": 2}):
        for ensure_ascii in (True, False):
            try:
                forms.append(json.dumps(value, sort_keys=True, ensure_ascii=ensure_ascii, **kwargs))
            except (TypeError, ValueError):
                pass
    if depth > 0 and isinstance(value, dict):
        for key, inner in value.items():          # a nested mapping spelled item by item
            forms += _spellings(key, depth - 1) + _spellings(inner, depth - 1)
    if depth > 0 and isinstance(value, (list, tuple)):
        for inner in value:
            forms += _spellings(inner, depth - 1)
    return forms


def _component_spellings(components: dict) -> list:
    """Every plausible rendering of a component key or value, longest first.

    The residual — what is left of the payload once the components themselves
    are struck out of it — is where the version tag has to show up. Striking out
    only whole canonical BODIES left an unrecognised serialisation completely
    intact, and the local v8 review built a passing submission on that: a
    bespoke `key~value|key~value` payload with no version tag anywhere passed
    because a `3` happened to fall inside a function hash. Keys and values are
    struck out one at a time here, so that payload leaves only its own
    punctuation behind and fails.

    One-character spellings are skipped: a lone digit is as likely to strike out
    the version tag itself as to be data, and losing the tag would fail a correct
    submission — the error this whole check exists to avoid making twice.
    Longest first, so a short value cannot chew a hole in a longer one.
    """
    out = set()
    for key, value in components.items():
        out.update(_spellings(key))
        out.update(_spellings(value))
    return sorted((s for s in out if isinstance(s, str) and len(s) > 1), key=len, reverse=True)


def check_digest_recomputed(o):
    """The digest IS the xxh64 of a version-tagged payload over the components.

    This is the check that decides ticket §2, and it decides it by RE-DERIVING
    the value rather than arguing from proxies. Shape, relations and a source
    scan all held for v7 and the review was still right: an unused `xxh64` call
    plus a hand-rolled deterministic hash satisfied every one of them, and
    nothing established that RUN_IDENTITY_VERSION was inside the hashed bytes.

    So the worker computes one more identity — over a dataset hash drawn from
    this run's seed and used nowhere else, with every xxh64 entry point in reach
    wrapped so it keeps what it was fed — and this process hashes those bytes
    again with its own stdlib XXH64 (`xxh64_ref`, proved against known vectors
    first and against the run's own calls second). Then:

      * the digest must BE the xxh64 of a payload the module really hashed. A
        custom hash cannot satisfy that: its output is not the xxh64 of
        anything, and a forged pair cannot help either, because the comparison
        is against what THIS process computes from the payload, never against
        the digest the worker recorded beside it;
      * that payload must carry the run's seeded inputs and every component
        key, so the digest is over the identity and not over a constant;
      * and it must be more than the components serialised: a payload equal to
        any untagged spelling of them is refused, and what is left of the
        payload once every component key and value spelling is struck out of it
        has to name version 3 (or the version is a component itself).
    """
    broken = xxh64_ref.self_check()
    ok(not broken, broken)

    identity = identity_value(o["hash_identity"], "the identity computed with the hash calls captured")
    digest = identity.get("digest")
    ok(_is_hex(digest, 16), f"captured identity digest {digest!r} is not a lowercase hex xxh64")
    calls = o.get("hash_calls")
    ok(isinstance(calls, list) and calls,
       "computing an identity called no xxh64 entry point at all, so the digest is some other hash")

    rehashed, agreed = [], 0
    for call in calls:
        if not isinstance(call, dict) or not isinstance(call.get("seed"), int):
            continue
        try:
            payload = base64.b64decode(call.get("payload") or "", validate=True)
        except (ValueError, TypeError):
            continue
        mine = xxh64_ref.hexdigest(payload, call["seed"])
        rehashed.append((payload, mine))
        agreed += mine == call.get("hexdigest")
    ok(agreed, f"none of the {len(calls)} captured xxh64 calls re-hashes to the digest recorded "
               f"beside it, so what the run called xxh64 is not xxh64")

    matching = [payload for payload, mine in rehashed if mine == digest]
    ok(matching, f"digest {digest} is not the xxh64 of any of the {len(rehashed)} payloads the module "
                 f"hashed while computing the identity; it comes from some other hash")
    payload = matching[0]
    eq(identity.get("run_hash"), f"v3-{digest}", "the run hash is the recomputed digest, version-tagged")

    text = payload.decode("utf-8", "replace")
    components = identity["components"]
    for key in sorted(components):
        ok(str(key) in text, f"the payload the digest was taken over never mentions component {key!r}; "
                             f"it is not a serialisation of the identity components")
    for key, value in sorted(components.items()):
        if isinstance(value, str) and value and value.isascii():
            ok(value in text, f"component {key}={value!r} is not in the payload the digest was taken over")
    seeded = SPEC["dataset_hash"] + "-recompute"
    ok(seeded in text, f"the hashed payload does not carry this run's dataset hash {seeded!r}")
    ok(SPEC["model"] in text, f"the hashed payload does not carry this run's model name {SPEC['model']!r}")

    bodies = _canonical_bodies(components)
    residual = text
    for body in bodies:
        if body and body in residual:
            residual = residual.replace(body, "")
    for spelling in _component_spellings(components):
        if spelling in residual:
            residual = residual.replace(spelling, "")
    for body in bodies:
        ne(text, body, "the digest is taken over the components with no version tag in them at all; "
                       "the ticket asks for a version-tagged serialisation")
    version_keys = [k for k in components if "version" in str(k).lower()]
    ok(version_keys or "3" in residual,
       f"nothing outside the serialised components names identity version 3: the payload is "
       f"{text[:160]!r}, and what is left of it once every component key and value is struck out "
       f"is {residual[:80]!r}, so RUN_IDENTITY_VERSION is not part of what is hashed")


def check_moved_verbatim():
    """`_get_function_hash` moved VERBATIM into the new module (ticket §5).

    No behaviour distinguishes the pristine function from a faithful rewrite —
    the probe's three hashes agree for both — which is what the TB3 "Do not
    modify enforced" review failed v5 for. So it is compared as an AST with the
    pristine copy of `llm/llm.py` that `run_suites.stage_baseline` puts at
    CURATOR_BASELINE_DIR; comments and blank lines may move, code may not.

    A missing baseline FAILS the fact. A check that passes when it cannot look
    is exactly the silent-emptiness failure `stage_baseline` was written to
    avoid.
    """
    root = os.environ.get(BASELINE_ENV, "")
    ok(root, f"{BASELINE_ENV} is unset, so the pristine {MOVED_VERBATIM} cannot be compared")
    pristine = pathlib.Path(root) / "llm" / "llm.py"
    ok(pristine.is_file(), f"no pristine llm.py at {pristine}")
    try:
        want = _funcdefs(judge_io.read_text(pristine), MOVED_VERBATIM)
    except OSError as exc:
        raise Fail(f"cannot read the pristine llm.py at {pristine}: {exc}")
    eq(len(want), 1, f"the pristine llm.py defines {MOVED_VERBATIM} once")
    got = _funcdefs(_run_identity_source(), MOVED_VERBATIM)
    ok(got, f"run_identity.py does not define {MOVED_VERBATIM}; the ticket moves it there")
    for node in got:
        if ast.dump(node) != ast.dump(want[0]):
            raise Fail(f"{MOVED_VERBATIM} was rewritten on the way over, not moved verbatim: "
                       f"{_first_statement_diff(node, want[0])}")

    # MOVED, not copied: a tree that leaves the definition in llm/llm.py as well
    # satisfied every line above, and so did a dead `if False:` copy of it, since
    # `_funcdefs` finds a definition wherever it sits. The sibling rule in the
    # same section is already graded this way — `_hash_fingerprint` is checked
    # for being GONE (`no_hash_fingerprint`) — so the absence is what "move"
    # means here, and nothing beyond that is asserted.
    llm_py = pathlib.Path(os.environ.get("SUBMISSION_SRC", "")) / "bespokelabs" / "curator" / "llm" / "llm.py"
    try:
        left_behind = _funcdefs(judge_io.read_text(llm_py), MOVED_VERBATIM)
    except OSError as exc:
        raise Fail(f"cannot read the submission's llm.py at {llm_py}: {exc}")
    eq(len(left_behind), 0,
       f"llm/llm.py still defines {MOVED_VERBATIM}; the ticket moves it into the new module and "
       f"re-exports it, so a copy left behind is not a move")


def _first_statement_diff(got: ast.AST, want: ast.AST) -> str:
    """Where two versions of one function first part company, for a human."""
    for i, (mine, theirs) in enumerate(zip(got.body, want.body)):
        if ast.dump(mine) != ast.dump(theirs):
            return (f"statement {i + 1} is {ast.unparse(mine)[:120]!r}, "
                    f"the pristine one is {ast.unparse(theirs)[:120]!r}")
    return f"it has {len(got.body)} statements, the pristine one has {len(want.body)}"


# ---------------------------------------------------------------------------
# the expected identity, from the seed
# ---------------------------------------------------------------------------
def filtered(params) -> dict:
    return {k: v for k, v in dict(params or {}).items() if k in IDENTITY_BACKEND_KEYS}


def identity_value(step, msg) -> dict:
    """A recorded identity, with its components present and a plain dict."""
    value = value_of(step, msg)
    ok(isinstance(value, dict), f"{msg}: no identity recorded")
    ok(isinstance(value.get("components"), dict), f"{msg}: no components recorded")
    return value


def expected_stub_components(over: dict, dataset_hash: str, fh: dict, model_schema) -> dict:
    """What a stub built from `over` must be identified by (a cached run)."""
    def fn_hash(ref):
        return fh["none"] if ref is None else fh[ref]

    rf = over.get("response_format")
    gen = over["generation_params"] if "generation_params" in over else SPEC["generation_params"]
    return {
        "backend": over.get("backend", "openai"),
        "backend_params": filtered(over.get("backend_params")),
        "batch_mode": bool(over.get("batch_mode", False)),
        "dataset_hash": dataset_hash,
        "generation_params": dict(gen or {}),
        "model_name": over.get("model_name", SPEC["model"]),
        "parse_func_hash": fn_hash(over.get("parse_func")),
        "prompt_func_hash": fn_hash(over.get("prompt_func")),
        "response_format": "text" if rf is None else model_schema,
        "return_completions_object": bool(over.get("return_completions_object", False)),
        "run_id": None,
        "system_prompt": over.get("system_prompt"),
    }


_JSON_TYPES = {"str": "string", "int": "integer", "float": "number", "bool": "boolean"}


def check_model_schema(schema):
    """The worker's reference for the drawn response model is that model's
    compact, key-sorted schema — checked against the recipe, so it is not a
    string the worker could pick."""
    ok(isinstance(schema, str), f"response model schema not recorded: {schema!r}")
    try:
        parsed = json.loads(schema)
    except ValueError:
        raise Fail(f"response model schema is not JSON: {schema[:200]!r}")
    eq(json.dumps(parsed, sort_keys=True, separators=(",", ":")), schema, "the schema reference is compact and sorted")
    recipe = SPEC["response_model"]
    eq(parsed.get("title"), recipe["name"], "response model title")
    props = parsed.get("properties") or {}
    eq(sorted(props), sorted(name for name, _ in recipe["fields"]), "response model fields")
    for name, kind in recipe["fields"]:
        eq(props[name].get("type"), _JSON_TYPES[kind], f"response model field {name} type")


# ---------------------------------------------------------------------------
# the openly stated feature — one node, and the reward's first condition:
# score.py grades 1 only if this passes and every hidden fact passes.
# ---------------------------------------------------------------------------
def judge_open(o):
    eq(o["ri_version"], 3, "RUN_IDENTITY_VERSION")
    eq(o["ri_filename"], STAMP, "RUN_IDENTITY_FILENAME")
    for name in SURFACE_NAMES:
        ok(o["has_names"].get(name), f"run_identity exports no {name!r}; it has {o.get('surface')}")

    eq(o["exc_subclass"], [True, True, True], "exception hierarchy")
    eq(o["mismatch_attrs"], ["cache-dir-c", "v3-a", "v3-b", ["model_name"]], "RunIdentityMismatch attrs")
    eq(o["stale_attrs"], ["cache-dir-c", "fingerprint", "aaa", "bbb"], "CachedResponseMismatch attrs")

    for name, fields in DATACLASS_FIELDS.items():
        got = o["dataclasses"][name]
        ok(got[0], f"{name} is not a dataclass")
        eq(got[1], fields, f"{name} field order")
    check_frozen_dataclasses()

    digest = o["digest"]
    ok(_is_hex(digest, 16), f"digest {digest!r} is not a lowercase hex xxh64")
    report_digest_hash_sources()
    check_digest_recomputed(o)
    eq(o["run_hash"], f"v3-{digest}", "run hash is the digest tagged with the version")
    eq(o["identity_version"], 3, "identity_version")
    eq(o["cache_enabled"], True, "cache_enabled")
    eq(o["same_inputs_hash"], o["run_hash"], "same inputs, same run hash")
    ne(o["other_dataset_hash"], o["run_hash"], "a different dataset is a different run")
    raised(o["frozen"], mro="FrozenInstanceError", msg="frozen RunIdentity")

    # Canonical means key-sorted: the two stubs carry the SAME generation and
    # backend parameters, handed over in opposite insertion orders. A sorted
    # payload cannot tell them apart; `str(dict)` or a json.dumps without
    # sort_keys gives two digests and two cache directories for one run.
    ordered = identity_value(o["canon_ordered"], "identity over the parameters as given")
    reordered = identity_value(o["canon_reordered"], "identity over the same parameters reordered")
    eq(reordered["components"], ordered["components"], "the same parameters, whatever order they arrived in")
    eq(reordered["digest"], ordered["digest"],
       "the digest is taken over a key-sorted payload, so insertion order cannot move it")
    eq(reordered["run_hash"], ordered["run_hash"], "insertion order must not fork the cache directory")

    # the stamp file
    eq(o["stamp_sorted_keys"], ["components", "created_at", "digest", "identity_version", "run_hash", "updated_at"], "stamp keys")
    payload = o["stamp_payload"]
    eq(payload["identity_version"], 3, "stamp identity_version")
    eq(payload["run_hash"], o["run_hash"], "stamp run_hash")
    eq(payload["digest"], digest, "stamp digest")
    eq(payload["components"], o["stamp_components"], "stamp components")
    eq(payload["created_at"], NOW, "stamp created_at")
    eq(payload["updated_at"], NOW, "stamp updated_at")
    eq(o["stamp_written"], json.dumps(payload, indent=2, sort_keys=True) + "\n",
       "stamp is indent=2, sort_keys=True, one trailing newline")
    eq(o["stamp_created_at"], NOW, "returned stamp created_at")
    eq(o["again_times"], [NOW, LATER], "rewrite keeps created_at, moves updated_at")
    eq(o["again_disk_times"], [NOW, LATER], "rewrite on disk")
    ok(o["round_trip_ok"], "stamp to_dict/from_dict round trips")
    raised(o["frozen_stamp"], mro="FrozenInstanceError", msg="frozen RunStamp")

    # reading a stamp back
    eq(o["read_back_hash"], o["run_hash"], "read_run_stamp hash")
    ok(o["read_absent"], "an absent stamp reads as None")
    ok(o["read_broken"], "an unparseable stamp reads as None")
    ok(o["read_partial"], "an incomplete stamp reads as None")

    # reconciling
    eq(o["created"], ["created", None, [STAMP]], "created")
    raised(o["frozen_check"], mro="FrozenInstanceError", msg="frozen RunDirectoryCheck")
    eq(o["adopted"], ["adopted", None, ["payload.txt", STAMP], "someone else's bytes"], "adopted")
    eq(o["upgraded"], ["upgraded", 2, 3, "2024-06-01T00:00:00", NOW], "upgraded")
    eq(o["matched"], ["matched", 3, "2024-06-01T00:00:00", LATER], "matched")
    raised(o["newer_raise"], mro="RunIdentityMismatch", mismatched_components=["identity_version"], msg="newer stamp")
    eq(o["newer_after"], 4, "a newer stamp is left as found")
    raised(o["foreign_raise"], mro="RunIdentityMismatch",
           found_run_hash="v3-ffffffffffffffff", expected_run_hash=o["run_hash"],
           mismatched_components=["model_name"], msg="foreign stamp")
    eq(o["foreign_after"], [["payload.txt", STAMP], "v3-ffffffffffffffff"], "a mismatch deletes nothing")

    # llm.py
    eq(o["fn_hash_none"], FN_HASH_NONE, "_get_function_hash(None)")
    eq(o["fn_hash_none_llm"], o["fn_hash_none"], "the moved function is re-exported")
    eq(o["fn_hash_stub"][0], o["fn_hash_stub"][1], "re-exported function agrees on a real function")
    check_moved_verbatim()
    ok(o["no_hash_fingerprint"], "_hash_fingerprint is replaced, not kept")
    eq(o["backend_props"], {"backend": True, "backend_params": True}, "LLM.backend/backend_params are properties")

    # db.py migration
    ok("parse_func" in o["runs_columns_names"] and "identity_version" in o["runs_columns_names"],
       f"RUNS_COLUMNS is missing the new columns: {o['runs_columns_names']}")
    eq(o["added"], ["identity_version", "parse_func"], "validate_schema added set")
    ok("parse_func" in o["live_columns"] and "identity_version" in o["live_columns"], "live columns")
    eq(o["migrated_row"], [None, None, "s0", NOW], "existing row survives with NULLs")
    eq(o["second_validate"], [], "a second validation adds nothing")
    # "unexpected columns stay fatal" (the ticket's §6) and nothing beyond it.
    # The ticket names no exception class for that case and no wording for its
    # message, so an implementation that raises its own type is compliant;
    # requiring a RuntimeError whose message contains "mismatch" was the TB3
    # "Test instruction alignment" finding on v9 — a requirement the tests
    # invented. Fatal is what is graded; WHICH exception is reported.
    raised(o["hostile_raise"], msg="an unexpected column must stay fatal")
    diag(f"an unexpected column raised {(o['hostile_raise'].get('mro') or ['?'])[0]}: "
         f"{str(o['hostile_raise'].get('str'))[:120]!r} (fatal is what the ticket asks; the class and "
         f"message are not graded)")

    # store_metadata
    eq(o["insert_result"], "inserted", "store_metadata inserted")
    eq(o["inserted_row"], ["def q(): pass", 3, NOW, NOW, "s1", None], "inserted row")
    eq(o["update_none_session"], "updated", "store_metadata updated")
    eq(o["updated_row"], ["s1", NOW, LATER], "a None session id leaves the recorded one alone")
    eq(o["updated_count"], 1, "one row after update")
    eq(o["update_new_session"], "updated", "store_metadata updated again")
    eq(o["updated_session"], "s2", "a new session id is written")

    # curator_response
    eq(o["cr_last_field"], "run_identity", "run_identity declared last")
    ok(o["cr_last_default_none"], "run_identity default is None")
    eq(o["response_run_identity"], o["saved_dict"], "run_identity travels through to_dict")
    eq(o["on_disk_hash"], o["run_hash"], "the saved response carries the run hash")
    eq(o["loaded_run_identity"], o["saved_dict"], "load returns the run identity")
    raised(o["load_mismatch"], mro="CachedResponseMismatch", field="fingerprint",
           expected=o["ds_fingerprint"], found=o["other_fingerprint"], msg="load fingerprint mismatch")
    # All three recorded fields, not just the one a different dataset trips: the
    # fingerprint alone passing was the TB3 "Verifiable" finding on v6. Size and
    # columns are reached by editing the recorded block, because no two datasets
    # share a fingerprint while differing in their size or their columns.
    eq(o["ds_size"], DS_SIZE, "the open feature's dataset")
    eq(o["ds_columns"], DS_COLUMNS, "the open feature's dataset columns")
    raised(o["load_size_mismatch"], mro="CachedResponseMismatch", field="size",
           expected=DS_SIZE + 1, found=DS_SIZE, msg="load size mismatch")
    raised(o["load_columns_mismatch"], mro="CachedResponseMismatch", field="columns",
           expected=DS_COLUMNS + ["c"], found=DS_COLUMNS, msg="load columns mismatch")
    eq(o["load_noverify_len"], 2, "verify=False takes the dataset it is handed")
    ok(o["legacy_run_identity_none"], "a response written before run identities still loads")

    # cached-dataset flag
    ok(o["stale_stopped"], "run() reached validate_config")
    ok(o["stale_flag_cleared"], "run() clears the flag before it consults the cache")
    # The ticket's §8 asks for one thing here: `run()` sets the flag False as its
    # first statement. What a WARM cache then does — return the cached dataset,
    # set the flag back to True — is curator's existing behaviour that the ticket
    # neither states nor changes, and asserting it was the other half of the TB3
    # "Test instruction alignment" finding on v9. Reported, not graded: a warm
    # cache that behaves differently is outside what this ticket asked for.
    diag(f"warm cache: returned the cached dataset={o['warm_returns_ds']!r}, "
         f"_is_cached_dataset set back to True={o['warm_flag_set']!r} "
         f"(existing behaviour, not stated by the ticket, not graded)")

    # an identity error out of the cache is not swallowed
    raised(o["cached_mismatch_propagates"], mro="CachedResponseMismatch", msg="cache mismatch propagates")
    ok(o["cached_missing_swallowed"], "a non-identity error is still swallowed")


# ---------------------------------------------------------------------------
# r1 — what the run key is computed from
# ---------------------------------------------------------------------------
# The components r1.rule grades by value. `backend`/`backend_params` belong to
# scope and exclusions, `run_id` to r2; rule still requires all twelve KEYS.
RULE_GRADED = [k for k in TWELVE if k not in ("backend", "backend_params", "run_id")]


def exported_set(o, name: str):
    """The string constant `name` as the run exported it, out of the probe's sweep.

    The probe reports every string collection the package holds, under the
    module's own names, because naming these two constants in the worker put
    them in front of agent code. This side owns the names.
    """
    sets = o.get("const_sets")
    ok(isinstance(sets, dict), "the probe reported no exported string constants at all")
    ok(name in sets, f"the implementation exports no {name} anywhere in bespokelabs.curator")
    return sets[name]


def judge_r1_rule(o):
    eq(exported_set(o, "IDENTITY_COMPONENT_KEYS"), TWELVE, "IDENTITY_COMPONENT_KEYS")
    defined("IDENTITY_COMPONENT_KEYS", lambda got, msg: eq(list(got), TWELVE, msg))

    fh = {ref: value_of(o["fh"].get(ref), f"_get_function_hash({ref})") for ref in ("@prompt", "@parse", "none")}
    eq(fh["none"], FN_HASH_NONE, "_get_function_hash(None)")
    ok(len({fh["@prompt"], fh["@parse"], fh["none"]}) == 3,
       f"the drawn prompt and parse functions must hash apart from each other and from None: {fh}")
    schema = value_of(o["model_schema"], "the response model's schema")
    check_model_schema(schema)

    for label, over, dataset_hash in fixture_spec.component_variants(SPEC):
        got = identity_value(o["variants"].get(label), f"identity [{label}]")["components"]
        eq(sorted(got), TWELVE, f"[{label}] the identity is computed from exactly the twelve keys")
        want = expected_stub_components(over, dataset_hash, fh, schema)
        for key in RULE_GRADED:
            eq(got[key], want[key], f"[{label}] component {key}")


def judge_r1_scope(o):
    eq(value_of(o["auto_backend"], "LLM.backend (auto-detect)"), "openai", "LLM.backend resolved on the auto path")
    eq(value_of(o["declared_backend"], "LLM.backend (declared)"), "openai", "LLM.backend resolved on the declared path")
    auto = identity_value(o["auto_identity"], "identity of the auto-detected LLM")["components"]
    declared = identity_value(o["declared_identity"], "identity of the declared LLM")["components"]
    eq(auto.get("backend"), "openai", "auto-detect must not hash a declared None")
    eq(declared.get("backend"), "openai", "declared backend component")
    stub = identity_value(o["stub_identity"], "identity of a stub")["components"]
    eq(stub.get("backend"), SPEC["stub_backend"], "backend is read off the object, whatever it says")

    eq(value_of(o["auto_params"], "LLM.backend_params (none given)"), {}, "backend_params is {} when none were given")
    eq(value_of(o["configured_params"], "LLM.backend_params"), SPEC["llm_params"],
       "backend_params is what __init__ was handed")
    eq(value_of(o["after_mutation"], "LLM.backend_params after mutating a copy"), SPEC["llm_params"],
       "backend_params hands out a copy")


def judge_r1_exclusions(o):
    eq(sorted(exported_set(o, "IDENTITY_BACKEND_PARAM_KEYS")), sorted(IDENTITY_BACKEND_KEYS),
       "IDENTITY_BACKEND_PARAM_KEYS")
    defined("IDENTITY_BACKEND_PARAM_KEYS", lambda got, msg: eq(set(got), IDENTITY_BACKEND_KEYS, msg))

    scenarios = fixture_spec.knob_scenarios(SPEC)
    plain = dict(scenarios[0][1])
    baseline = identity_value(o["scenarios"].get("plain"), "identity [plain]")
    hash_of_filter: dict = {}
    for label, params in scenarios:
        seen = identity_value(o["scenarios"].get(label), f"identity [{label}]")
        carried = seen["components"].get("backend_params")
        want = filtered(params)
        for key in params:
            if key not in IDENTITY_BACKEND_KEYS:
                ok(not isinstance(carried, dict) or key not in carried,
                   f"[{label}] {key} reached the identity components as {carried!r}")
        eq(carried, want, f"[{label}] backend_params carried")
        forks = want != filtered(plain)
        if forks:
            ne(seen["run_hash"], baseline["run_hash"], f"[{label}] must fork the cache directory")
        else:
            eq(seen["run_hash"], baseline["run_hash"], f"[{label}] must not fork the cache directory")
        # Across every scenario: same identity params, same run; different, different.
        canon = json.dumps(want, sort_keys=True)
        for other_canon, other_hash in hash_of_filter.items():
            if other_canon == canon:
                eq(seen["run_hash"], other_hash, f"[{label}] same identity params, same run")
            else:
                ne(seen["run_hash"], other_hash, f"[{label}] different identity params, different run")
        hash_of_filter.setdefault(canon, seen["run_hash"])

    eq(sorted(o["noise_keys"]), sorted(NOT_IDENTITY_KEYS), "the knobs that do not fork the cache")
    noise = identity_value(o["noise"], "identity with every noise knob at once")
    eq(noise["components"].get("backend_params"), plain, "a pile of noise knobs leaves only base_url")
    eq(noise["run_hash"], baseline["run_hash"], "a pile of noise knobs does not fork the cache")


def judge_r1_observability(o):
    params = SPEC["stamp_params"]
    base = identity_value(o["identity"], "identity of the stamp scenario")
    components = base["components"]
    eq(sorted(components), TWELVE, "the stated component table holds")
    eq(components.get("backend_params"), {"base_url": params["base_url"]},
       "only the allowlisted backend param is carried")
    ok(params["api_key"] not in json.dumps(components, sort_keys=True),
       "the api key is written down in the components")

    # The stamp write_run_stamp left, read from disk.
    value_of(o["stamp_write"], "write_run_stamp")
    dirs, files = entries("r1_obs/run")
    eq(len(files), 1, f"write_run_stamp left {files} (and directories {dirs})")
    raw = read_bytes(f"r1_obs/run/{files[0]}").decode("utf-8", errors="replace")
    ok(params["api_key"] not in raw, "the stamp file is cleartext on disk, so the api key must never be a component")
    ok(params["base_url"] in raw, "the base_url does reach the stamp file")
    try:
        on_disk = json.loads(raw)
    except ValueError:
        raise Fail("the stamp file is not JSON")
    eq(on_disk.get("run_hash"), base["run_hash"], "the stamp records the scenario's run hash")
    eq(on_disk.get("components"), components, "the stamp records the scenario's components")

    rotated = identity_value(o["rotated"], "identity with a rotated key and retry budget")
    eq(rotated["components"].get("backend_params"), {"base_url": params["base_url"]}, "rotated backend_params")
    eq(rotated["run_hash"], base["run_hash"], "rotating the key, the retries or the timeout is the same run")
    for i, step in enumerate(o["changed"]):
        changed = identity_value(step, f"changed identity {i}")
        ne(changed["run_hash"], base["run_hash"], f"changed component {i} must be a different run")
    auto = identity_value(o["auto"], "auto-detected LLM")
    declared = identity_value(o["declared"], "declared LLM")
    eq(auto["run_hash"], declared["run_hash"], "two ways of saying the same backend are the same run")


# ---------------------------------------------------------------------------
# r2 — where a cache-disabled run's identity comes from
# ---------------------------------------------------------------------------
def _param(signature, name, where):
    ok(isinstance(signature, list), f"{where}: no signature ({signature!r})")
    for entry in signature:
        if entry[0] == name:
            return entry
    raise Fail(f"{where} takes {[e[0] for e in signature]}, so no caller can hand it a run id")


def require_param(o):
    eq(o.get("param"), RUN_ID_PARAM, "the keyword a run id is passed by")


def judge_r2_rule(o):
    require_param(o)
    sigs = o["signatures"]
    entry = _param(sigs["compute_run_identity"], RUN_ID_PARAM, "compute_run_identity")
    eq(entry[1], "KEYWORD_ONLY", "run_id is keyword-only")
    eq(entry[2], None, "run_id default is None")
    for where in ("_run_identity", "__call__"):
        entry = _param(sigs[where], RUN_ID_PARAM, f"LLM.{where}")
        ok(entry[1] in ("KEYWORD_ONLY", "POSITIONAL_OR_KEYWORD"), f"LLM.{where} run_id kind {entry[1]}")
        eq(entry[2], None, f"LLM.{where} run_id default is None")

    rid = SPEC["id_rule"]
    base = identity_value(o["base"], "cache-disabled identity")
    eq(base["cache_enabled"], False, "cache_enabled False")
    eq(base["components"].get(RUN_ID_PARAM), rid, "the supplied id identifies a cache-disabled run")
    for label in ("replay_same_stub", "replay_new_stub"):
        again = identity_value(o[label], label)
        eq(again["components"].get(RUN_ID_PARAM), rid, f"{label} run id")
        eq(again["run_hash"], base["run_hash"], f"{label}: same id, same directory")
    other = identity_value(o["other_id"], "a different id")
    eq(other["components"].get(RUN_ID_PARAM), SPEC["id_rule_other"], "the other id is carried")
    ne(other["run_hash"], base["run_hash"], "a different id is a different run")
    inputs = identity_value(o["other_inputs"], "the same id over different inputs")
    eq(inputs["components"].get(RUN_ID_PARAM), rid, "the same id over different inputs is carried")
    ne(inputs["run_hash"], base["run_hash"], "the same id over different inputs is a different run")


def _stopped(calls, label, count):
    ok(isinstance(calls, list) and len(calls) == count, f"{label}: {count} call(s) not made ({calls!r})")
    for i, info in enumerate(calls):
        raised(info, mro="_Stop", msg=f"{label} call {i} reached the processor")


def judge_r2_scope(o):
    require_param(o)
    eq(o.get("env"), RUN_ID_ENV, "the environment variable a default run id comes from")

    # A cached run carries no id.
    _stopped(o.get("cached"), "the cached run", 1)
    dirs, _ = entries("r2_scope/cached")
    eq(len(dirs), 1, f"one cached run made {dirs}")
    eq(run_directory("r2_scope/cached", dirs[0]).get(RUN_ID_PARAM, "<<absent>>"), None,
       "a cached run has no ephemeral id in its components")

    # Caching disabled: the environment's id identifies the run.
    _stopped(o.get("from_env"), "the environment-identified runs", 2)
    dirs, _ = entries("r2_scope/from_env")
    eq(len(dirs), 1, f"two runs of one {RUN_ID_ENV} must share one directory, made {dirs}")
    eq(run_directory("r2_scope/from_env", dirs[0]).get(RUN_ID_PARAM), SPEC["id_env"],
       "the environment's id is what the run is identified by")

    # An id handed to the call wins over the environment.
    _stopped(o.get("explicit"), "the explicitly identified run", 1)
    dirs, _ = entries("r2_scope/explicit")
    eq(len(dirs), 1, f"an explicit run id made {dirs}")
    eq(run_directory("r2_scope/explicit", dirs[0]).get(RUN_ID_PARAM), SPEC["id_explicit"],
       "an id handed to the call wins over the environment")

    # With nothing to go on, each run mints a fresh uuid4 hex of its own.
    _stopped(o.get("minted"), "the unidentified runs", 2)
    dirs, _ = entries("r2_scope/minted")
    eq(len(dirs), 2, f"two unidentified runs must not share a directory, got {dirs}")
    ids = [run_directory("r2_scope/minted", name).get(RUN_ID_PARAM) for name in dirs]
    eq(len(set(ids)), 2, f"both runs were minted the same id: {ids}")
    for value in ids:
        ok(value not in (None, "", SPEC["id_env"], SPEC["id_explicit"]), f"minted run id {value!r}")
        ok(_is_hex(value, 32), f"minted run id {value!r} is not a uuid4 hex")


def judge_r2_failure_behavior(o):
    require_param(o)
    raised(o.get("missing_absent"), mro="RunIdentityError", msg="cache-disabled, no run_id")
    raised(o.get("missing_none"), mro="RunIdentityError", msg="cache-disabled, run_id=None")
    raised(o.get("missing_empty"), mro="RunIdentityError", msg="cache-disabled, empty run_id")
    raised(o.get("cached_with_id"), mro="RunIdentityError", msg="cached run handed a run_id")
    raised(o.get("call_with_id"), mro="RunIdentityError", msg="a cached call handed a run_id")

    # The cache root the refused call was pointed at holds exactly what the
    # legitimate control call made afterwards — this run's model, this run's id
    # — and nothing from the refusal.
    raised(o.get("control"), mro="_Stop", msg="the control call into the same cache reached the processor")
    dirs, _ = entries("r2_fail/cc")
    eq(len(dirs), 1, f"a refused run must not leave a directory behind: the cache holds {dirs} "
                     "after one refused and one accepted call")
    run_directory("r2_fail/cc", dirs[0])
    raw = read_bytes(f"r2_fail/cc/{dirs[0]}/{STAMP}").decode("utf-8", errors="replace")
    ok(SPEC["id_refused"] not in raw, "the refused run id reached a stamp")


def _scan_no_randomness():
    """The AST no-randomness check of test_r2, over the file on disk.

    The ticket names `run_identity.py`; read it from SUBMISSION_SRC (parsing text
    executes nothing) rather than trusting the worker's reported source.
    """
    for node in ast.walk(ast.parse(_run_identity_source())):
        if isinstance(node, ast.Import):
            for alias in node.names:
                ok(alias.name.split(".")[0] not in BANNED_IMPORTS, f"run_identity imports {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            ok((node.module or "").split(".")[0] not in BANNED_IMPORTS, f"run_identity imports from {node.module}")
        elif isinstance(node, ast.Attribute):
            ok(node.attr != "urandom", "run_identity reads os.urandom")
        elif isinstance(node, ast.Name):
            ok(node.id != "urandom", "run_identity reads urandom")


def judge_r2_observability(o):
    require_param(o)
    uncached = identity_value(o["uncached"], "cache-disabled identity")
    run_hash = uncached["run_hash"]
    ok(isinstance(run_hash, str) and run_hash.startswith(NOCACHE_PREFIX),
       f"a cache-disabled run hash is greppable, got {run_hash!r}")
    eq(len(run_hash), NOCACHE_LEN, f"{run_hash!r} is {len(run_hash)} characters")
    eq(uncached["components"].get(RUN_ID_PARAM), SPEC["id_obs"], "the run id behind the hash")
    again = identity_value(o["uncached_again"], "the same call again")
    eq(again["components"].get(RUN_ID_PARAM), SPEC["id_obs"], "the replay's run id")
    eq(again["run_hash"], run_hash, "a replay of the same id is byte-equal")
    other = identity_value(o["uncached_other"], "a different id")
    eq(other["components"].get(RUN_ID_PARAM), SPEC["id_obs_other"], "the other run id")
    ne(other["run_hash"], run_hash, "a different id is a different run")
    cached = identity_value(o["cached"], "the cached identity")
    eq(cached["components"].get(RUN_ID_PARAM, "<<absent>>"), None, "a cached run carries no run id")
    ok(not str(cached["run_hash"]).startswith(NOCACHE_PREFIX), "a cached run is not a cache-disabled run")
    _scan_no_randomness()


JUDGES = {
    "test_open::test_open_feature__a_versioned_run_identity_stamps_reconciles_and_is_recorded": judge_open,
    "test_r1::test_rule__component_set": judge_r1_rule,
    "test_r1::test_scope__backend_resolution": judge_r1_scope,
    "test_r1::test_exclusions__backend_param_filter": judge_r1_exclusions,
    "test_r1::test_observability__stamp_contents": judge_r1_observability,
    "test_r2::test_rule__uncached_identity": judge_r2_rule,
    "test_r2::test_scope__identity_sourcing": judge_r2_scope,
    "test_r2::test_failure_behavior__refusals": judge_r2_failure_behavior,
    "test_r2::test_observability__uncached_hash_shape": judge_r2_observability,
}


def junit(results):
    fails = sum(1 for _, _, f in results if f)
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="g4_run_cache_identity" '
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
        # judge_io, not read_text: the worker owns this file, so it can be a
        # symlink to /tests/task.json by the time root opens it, and the judge
        # copies what it reads into junit.xml.
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
    # After the results, so a reviewer reading the verifier log sees which
    # observations were reported rather than graded. Nothing here is in junit.xml.
    for message in DIAGNOSTICS:
        print(f"diag: {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
