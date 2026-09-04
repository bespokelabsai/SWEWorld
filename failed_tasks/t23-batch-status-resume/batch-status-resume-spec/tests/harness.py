"""Readers the suites import directly.

Separate from `conftest.py` because a conftest is not an importable module: it
is loaded by pytest for its fixtures, and `from ..conftest import ...` needs a
parent package the tests directory does not have.
"""
from __future__ import annotations

import io
import pathlib
import tokenize

import pytest

# The tree the world shipped. Anything that differs from it is the agent's.
BASELINE = pathlib.Path("/opt/world-state/input/curator/src/bespokelabs/curator")


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
        base = BASELINE / rel
        if base.exists():
            try:
                if base.read_text(encoding="utf-8", errors="replace") == body:
                    continue                      # untouched
            except OSError:
                pass
        out[str(rel)] = code_only(body)
    return out
