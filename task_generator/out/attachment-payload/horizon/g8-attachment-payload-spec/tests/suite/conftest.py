"""Environment for the grading suite, set at IMPORT time.

Deliberately thinner than `harbor_tasks/_suites/conftest.py`, and only in the ways
this suite allows: it drives no sockets, so the fake provider and the /etc/hosts
mapping that file carries have nothing to do here. What is kept is the one thing
that file calls load-bearing — the environment set BEFORE any curator import,
because `curator/log.py` reads `CURATOR_DISABLE_RICH_DISPLAY` when it is imported
and a function-scoped fixture runs long after that.

The other thing kept is `_unshadow_bespokelabs_siblings`, lifted verbatim. A first
version of this file dropped it -- the reasoning was that this suite drives no
sockets, so the fake provider and the /etc/hosts mapping had nothing to do here,
and the unshadow looked like part of the same machinery. It is not: it is about the
`bespokelabs` NAME. Hosted collection then died with `KeyError:
'bespokelabs.curator'` in the import machinery, three collection errors, every
fact scored 0 -- while the identical suite passed 11/11 in a local container.
When trimming a file whose own docstring says two things are load-bearing, keep
both.
"""
import os

os.environ.setdefault("CURATOR_DISABLE_RICH_DISPLAY", "1")
os.environ.setdefault("TELEMETRY_ENABLED", "false")
os.environ.setdefault("CURATOR_VIEWER", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-verifier")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-verifier")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
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
