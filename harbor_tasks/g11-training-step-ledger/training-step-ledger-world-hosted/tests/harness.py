"""Readers the suites import directly.

Separate from `conftest.py` because a conftest is not an importable module: it
is loaded by pytest for its fixtures, and `from ..conftest import ...` needs a
parent package the tests directory does not have.
"""
from __future__ import annotations

import functools
import io
import os
import pathlib
import tarfile
import tokenize

import pytest

# The tree the world shipped. Anything that differs from it is the agent's.
#
# Resolved through the environment because the suites no longer run as root:
# `/opt/world-state` is 0700, so the drop uid cannot read this path and
# `Path.exists()` answers False on PermissionError rather than raising.
# `changed_source()` would then report the WHOLE library as changed and fail
# quietly in both directions at once — some facts passing on untouched curator,
# others failing on a correct one. `run_suites.py` stages a readable copy and
# names it here; the default keeps the local bracket and the devbox working.
BASELINE = pathlib.Path(os.environ.get(
    "CURATOR_BASELINE_DIR",
    "/opt/world-state/input/curator/src/bespokelabs/curator"))

# The same tree, where a Horizon image keeps it. `/opt/world-state` is
# SWEWorld's pristine checkout and exists in no apex_arena image, so a suite
# that reached for BASELINE directly passed the local bracket 10 of 10 and then
# failed hosted validation at 0.89 on a bare FileNotFoundError. The Dockerfile
# copies the vendored tarball into /tests, which apex_arena creates root-owned
# and 0700 — so it is a baseline the grader can read and the agent cannot.
BASELINE_ARCHIVE = pathlib.Path("the staged pristine tree (CURATOR_BASELINE_DIR)")
_ARCHIVE_PREFIX = "./src/bespokelabs/curator/"


# ---------------------------------------------------------------------------
# Readers the suites share
# ---------------------------------------------------------------------------
def surface(obj) -> list[str]:
    if isinstance(obj, dict):
        return sorted(obj)
    return sorted(k for k in dir(obj) if not k.startswith("_"))


def read_field(obj, *names, default=...):
    """A field by any of several names, from a dict, dataclass or model.

    The requirement fixes field NAMES where it names them; it never fixes the
    container. An agent returning a dict, a dataclass or a pydantic model has
    satisfied it equally, and one that called its counter `sent` rather than
    `misses` failed a whole run on spelling before this existed.
    """
    for name in names:
        if isinstance(obj, dict) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            return getattr(obj, name)
    if hasattr(obj, "to_dict"):
        as_dict = obj.to_dict()
        for name in names:
            if name in as_dict:
                return as_dict[name]
    if default is not ...:
        return default
    raise AssertionError(
        f"expected one of {names} on {type(obj).__name__}; it has {surface(obj)}")


def cache_stats_of(llm):
    """`cache_stats()` is named in t1's ticket, so it is fair to require."""
    fn = getattr(llm, "cache_stats", None)
    if not callable(fn):
        pytest.fail("curator.LLM has no callable cache_stats(); its public "
                    f"surface is {surface(llm)}")
    return fn()


def require_feature(is_present: bool, what: str) -> None:
    """Guard a preservation constraint with proof the feature exists.

    Several hidden facts are stated as things that must NOT change — no new
    public knob, each block keeps its own limiter, no estimate on the sync
    path. Every one is trivially true of a checkout nobody touched, so a test
    that only checks the negative scores full marks for an agent who wrote
    nothing. Three of t4's exclusion tests did exactly that on the pristine
    tree.
    """
    if not is_present:
        pytest.fail(
            f"{what} is not implemented, so the constraint that goes with it "
            "cannot be credited: an untouched checkout satisfies it by doing "
            "nothing.")


def unmeasured(why: str) -> None:
    """Drop this fact from the score instead of failing it.

    Distinct from `require_feature`, which FAILS. Use that when the absence
    proves non-compliance; use this when the absence means the suite cannot
    SEE compliance either way. `score.py` treats a skip as unmeasured and
    removes it from the mean, so a fact nobody can observe stops counting
    against the agent rather than reading as a zero they earned.
    """
    pytest.skip(f"not observable here: {why}")


def printed_text(capfd, caplog) -> str:
    """Everything the run said, however it chose to say it.

    An agent may `print()` the estimate or log it. Those land in different
    places — capfd sees file descriptors, pytest's logging plugin intercepts
    records before they reach one — and a test that reads only capfd reports
    "no dollar figure reached the terminal" about an implementation whose
    estimate is right there in the log. The reference implementation logged it
    and scored zero on all seven of t2's facts for exactly that reason.

    The ticket says the estimate must be printed; it does not say through which
    mechanism, so both count.
    """
    captured = capfd.readouterr()
    return "\n".join([captured.out, captured.err, caplog.text])


# ---------------------------------------------------------------------------
# Reading the submitted source
# ---------------------------------------------------------------------------
def code_only(src: str) -> str:
    """Executable code and ordinary string literals; comments and docstrings out.

    Borrowed from AlphaShop's fraud-hold-queue grader, for the reason its own
    docstring gives: a correct solution SAYS what it does in a comment, and a
    naive text scan then fails it for documenting the requirement it satisfies.

    String literals are kept deliberately — a threshold or a discount written
    into an f-string or a SQL fragment is still real code. Falls back to the raw
    text when a file will not tokenize, because failing open would silently
    disable every check built on this.
    """
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return src

    starters = {tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT,
                tokenize.ENCODING}
    out: list[str] = []
    prev = tokenize.NEWLINE
    for tok in toks:
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.STRING and prev in starters:
            continue                              # statement-position: a docstring
        out.append(tok.string)
        if tok.type not in (tokenize.NL, tokenize.COMMENT):
            prev = tok.type
    return " ".join(out)


@functools.lru_cache(maxsize=1)
def _archived_baseline() -> dict[str, str]:
    """The whole baseline out of the tarball, read once.

    Once, because `changed_source()` asks per file and curator is several
    hundred of them; reopening the archive each time turned a millisecond check
    into a visible pause in every suite that calls it.
    """
    if not BASELINE_ARCHIVE.exists():
        return {}
    out: dict[str, str] = {}
    try:
        with tarfile.open(BASELINE_ARCHIVE) as tar:
            for member in tar.getmembers():
                if not member.isfile() or not member.name.startswith(_ARCHIVE_PREFIX):
                    continue
                handle = tar.extractfile(member)
                if handle is None:
                    continue
                out[member.name[len(_ARCHIVE_PREFIX):]] = handle.read().decode(
                    "utf-8", errors="replace")
    except (OSError, tarfile.TarError):
        return {}
    return out


def baseline_text(rel) -> str | None:
    """The file as the world shipped it, or None where no baseline exists.

    Never raises. A test that reads the baseline to prove the agent ADDED
    something must degrade rather than error when there is nothing to diff
    against — an environment without a baseline is not a failed requirement.
    """
    direct = BASELINE / rel
    if direct.exists():
        try:
            return direct.read_text(encoding="utf-8", errors="replace")
        except OSError:
            pass
    return _archived_baseline().get(str(rel))


def changed_source() -> dict[str, str]:
    """Every curator file the agent added or edited, comments stripped.

    Diffed against the tree the world shipped rather than scanned whole: a
    pattern like `0.5` occurs all over an untouched library, so an unscoped
    search would report a hit for an agent who wrote nothing. Only what changed
    is theirs to be graded on.
    """
    import bespokelabs.curator

    live = pathlib.Path(bespokelabs.curator.__file__).parent
    out: dict[str, str] = {}
    for path in sorted(live.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(live)
        try:
            body = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if baseline_text(rel) == body:
            continue                              # untouched
        out[str(rel)] = code_only(body)
    return out
