"""t40 — the openly stated feature: a pinned default, overridable by the caller.

The ticket asks for the Docker backend's image to be pinned to a specific tag
rather than `latest`, and for `backend_params` to be able to override it.
Untouched curator sets no image at all — `sandbox_kwargs` comes back `{}` — so
the sandbox library's own default applies, which is the `latest` the ticket is
complaining about.
"""
from __future__ import annotations

import pytest

from kit import image_of, kwargs_for

pytestmark = pytest.mark.timeout(120)


def test_open_feature__a_default_image_is_set_and_can_be_overridden():
    default = image_of(kwargs_for())
    assert default, (
        "the docker backend passes no image at all, so the sandbox library's "
        "own default applies — which is the unpinned `latest` the ticket asks "
        f"to replace. sandbox_kwargs: {kwargs_for()}")

    override = image_of(kwargs_for(image="example.io/custom:9.9"))
    assert override == "example.io/custom:9.9", (
        f"backend_params={{'image': ...}} did not take effect; the backend "
        f"would use {override!r}")
