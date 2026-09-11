"""Fixtures for the curator grading suites.

Nothing here monkeypatches curator. The suites drive it against a real socket
(`fakeapi.FakeProvider`), so curator's own client code — its retry loop, its
streaming reader, its batch poller, its provider detection — runs untouched.

Two things in this file are load-bearing and were learned the hard way.

**The environment is set at IMPORT time, not in a fixture.** `curator/log.py`
reads `CURATOR_DISABLE_RICH_DISPLAY` when it is imported, and a function-scoped
fixture runs long after that. RichHandler was therefore always installed, every
captured line came back wrapped into ~21-character fragments with
`module.py:lineno` right-aligned onto the first one, and the suites' own noise
filter then discarded that first fragment of every logged line. Output matching
passed or failed on where a dollar sign happened to land.

**There is no socket guard.** The old one blocked `socket.socket.connect` to
prove nothing reached the network — and then fired on the pristine tree in 66
places across the four suites, which is how "0 passed on baseline" came to mean
"my guard is working" rather than "the feature is absent". The provider is a
real socket on 127.0.0.1; a stray call to a real provider fails on DNS or on a
missing key, loudly, without a guard that can fail the innocent.
"""
from __future__ import annotations

import os
import sys


def _put_submission_on_path() -> str:
    """Add the submission's `src` to `sys.path`, behind the stdlib.

    `run_suites.py` passes it as SUBMISSION_SRC rather than on PYTHONPATH, and
    the difference is the whole point. PYTHONPATH is searched BEFORE the
    standard library, so a pushed `src/sitecustomize.py` — or `src/os.py`, or
    `src/encodings/__init__.py` — executes while the interpreter is still
    starting, before this file, before pytest, and before any test could
    object. That is how a pristine tree was made to score 1.00 on every hidden
    fact: the payload ran, rewrote `score.py`, and no assertion was ever
    consulted.

    Inserting it here instead means the first agent code to run is the
    `import bespokelabs` below, in a process that has finished building itself.
    The entry still goes AHEAD of site-packages, because
    `_unshadow_bespokelabs_siblings` depends on the submission owning the
    `bespokelabs` name; it just no longer goes ahead of `os`.
    """
    src = os.environ.get("SUBMISSION_SRC", "")
    if not src or not os.path.isdir(src):
        return f"not applied ({src or 'unset'})"
    if src in sys.path:
        return "already present"
    import sysconfig

    purelib = sysconfig.get_paths().get("purelib", "")
    at = len(sys.path)
    for i, entry in enumerate(sys.path):
        if entry and (entry == purelib or entry.endswith("site-packages")):
            at = i
            break
    sys.path.insert(at, src)
    return f"inserted at {at}"


_SUBMISSION_STATUS = _put_submission_on_path()

# ---------------------------------------------------------------------------
# Before any curator import. Order matters; see the module docstring.
# ---------------------------------------------------------------------------
os.environ.setdefault("CURATOR_DISABLE_RICH_DISPLAY", "1")
os.environ.setdefault("TELEMETRY_ENABLED", "false")
os.environ.setdefault("CURATOR_VIEWER", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-verifier")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-verifier")
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-verifier")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
# Wide, so a log line is one line. Rich wraps to the width it infers, and 80
# columns splits an estimate away from the word "cost".
os.environ.setdefault("COLUMNS", "220")


def _unshadow_bespokelabs_siblings() -> None:
    """Let `bespokelabs.sandbox` resolve even with the submission on the path.

    The submission's `src/bespokelabs/__init__.py` is a REGULAR package, so
    once it is first on PYTHONPATH it owns the `bespokelabs` name entirely and
    every installed sibling distribution — `bespokelabs-sandbox` among them —
    becomes invisible. `run_suites.py` documents that shadowing as the reason
    curator itself must not be installed; the cost, unnoticed until now, is
    that a submission importing a sibling package cannot.

    That is a limit of this harness, not of the code being graded. A real
    agent's Docker backend imported `bespokelabs.sandbox` at construction and
    every t40 test failed with ModuleNotFoundError — scored as five failures
    when the implementation was fine. Baseline curator only escaped it by
    importing the same module lazily, inside the execution path the tests
    never reach.

    Appending the installed directory to `bespokelabs.__path__` restores the
    sibling without disturbing which copy of `bespokelabs.curator` wins: the
    submission is still first on the path.
    """
    import site
    import sysconfig

    try:
        import bespokelabs
    except ImportError:
        return
    roots = list(site.getsitepackages()) if hasattr(site, "getsitepackages") else []
    roots.append(sysconfig.get_paths().get("purelib", ""))
    for root in roots:
        if not root:
            continue
        candidate = os.path.join(root, "bespokelabs")
        if os.path.isdir(candidate) and candidate not in bespokelabs.__path__:
            bespokelabs.__path__.append(candidate)


_unshadow_bespokelabs_siblings()

import pytest  # noqa: E402

from fakeapi import HOSTS, FakeProvider  # noqa: E402

HOSTS_FILE = "/etc/hosts"


def _map_hosts() -> str:
    """Point the provider hostnames at loopback.

    curator chooses its provider branch by substring on the URL
    (`if "api.deepseek.com" in self.url`), so the tests have to use real names
    for that branch to run at all. Mapping them here means the name resolves to
    our own server and nothing ever leaves the container.

    Best effort: if /etc/hosts is not writable the tests that need a specific
    provider fail on connection, which is a clear failure rather than a silent
    wrong answer.
    """
    try:
        current = open(HOSTS_FILE).read()
    except OSError as exc:
        return f"unreadable: {exc}"
    missing = [h for h in HOSTS if h not in current]
    if not missing:
        return "already mapped"
    try:
        with open(HOSTS_FILE, "a") as fh:
            fh.write("\n# curator grading suites - provider names on loopback\n")
            fh.write("127.0.0.1 " + " ".join(missing) + "\n")
        return "mapped " + ", ".join(missing)
    except OSError as exc:
        return f"not writable ({exc}); provider-specific tests will fail to connect"


_HOSTS_STATUS = _map_hosts()


@pytest.fixture(scope="session", autouse=True)
def hosts_mapped():
    """Say once what happened to /etc/hosts, so a connection failure is
    diagnosable from the log rather than from first principles."""
    print(f"[verifier] provider hostnames: {_HOSTS_STATUS}")
    # Same reasoning as the line above: when the submission is not on the path
    # every test fails on ImportError, and that is far quicker to read here
    # than to derive from a page of collection errors.
    print(f"[verifier] submission on sys.path: {_SUBMISSION_STATUS}")
    return _HOSTS_STATUS


@pytest.fixture
def provider(tmp_path, monkeypatch):
    """A running provider, and a private cache directory for the run.

    `monkeypatch` here only touches the ENVIRONMENT — never curator itself.
    """
    monkeypatch.setenv("CURATOR_CACHE_DIR", str(tmp_path / "curator-cache"))
    monkeypatch.setenv("HF_DATASETS_CACHE", str(tmp_path / "hf"))
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("CURATOR_DISABLE_CACHE", raising=False)

    server = FakeProvider().start()
    try:
        yield server
    finally:
        server.stop()


@pytest.fixture
def output(capfd):
    """Everything the run said, however it chose to say it.

    An agent may `print()` the estimate or log it, and those land in different
    places: capfd sees file descriptors, while a logging record is intercepted
    before it reaches one. A test reading only capfd reports "no dollar figure
    reached the terminal" about an implementation whose estimate is right there
    in the log — the t2 reference implementation logged it and scored zero on
    all seven facts for exactly that reason.

    The ticket says the estimate must be printed; it does not say through which
    mechanism, so both count.
    """
    import io
    import logging

    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setLevel(logging.INFO)
    root = logging.getLogger()
    root.addHandler(handler)
    previous = root.level
    root.setLevel(min(previous, logging.INFO))

    def read() -> str:
        # Truncating gives the same "since the last read" semantics capfd has.
        # Without it the buffer accumulates, so a test comparing two runs sees
        # the first run's numbers in the second's text — which silently breaks
        # every ratio assertion, and made a correct estimator look like it
        # ignored the price.
        captured = capfd.readouterr()
        logged = buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        return "\n".join([captured.out, captured.err, logged])

    try:
        yield read
    finally:
        root.removeHandler(handler)
        root.setLevel(previous)


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
