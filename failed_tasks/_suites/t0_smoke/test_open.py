"""The smoke task's open feature: the module exists and imports.

Deliberately trivial. This suite exists to prove the harness works — the clone
of pushed `main`, the venv, pytest, the junit-to-rewards mapping, provenance —
not to be difficult. If this scores zero, nothing measured by the real tasks
means anything.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.timeout(60)


def test_open_feature__curator_still_imports():
    """The agent's tree is importable at all.

    First thing worth knowing about any submission, and the failure that would
    otherwise show up as five confusing test errors instead of one clear one.
    """
    from bespokelabs import curator
    assert hasattr(curator, "LLM"), (
        "bespokelabs.curator imported but has no LLM; this is not curator")
