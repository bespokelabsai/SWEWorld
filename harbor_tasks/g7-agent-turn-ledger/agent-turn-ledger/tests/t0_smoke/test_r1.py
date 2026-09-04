"""The smoke task's one requirement, stated openly in its own instruction.

  rule           `curator.world_check()` exists and returns the exact string
  observability  it is importable from the package root, not buried

Both are in the ticket. Nothing here is hidden, which is the point: a run of
this task that scores 1.0 proves the environment, the push path, the deploy
chain and the grader all work, so a zero on a real task is about the task.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.timeout(60)

EXPECTED = "sweworld ok"


def test_rule__world_check_returns_the_agreed_string():
    from bespokelabs import curator

    fn = getattr(curator, "world_check", None)
    assert callable(fn), (
        "curator.world_check is missing or not callable; the ticket asked for "
        f"a function on the package root. Public names: "
        f"{sorted(n for n in dir(curator) if not n.startswith('_'))[:25]}")
    got = fn()
    assert got == EXPECTED, f"world_check() returned {got!r}, expected {EXPECTED!r}"


def test_observability__world_check_is_on_the_package_root():
    """Importable as `from bespokelabs.curator import world_check`."""
    from bespokelabs.curator import world_check
    assert world_check() == EXPECTED
