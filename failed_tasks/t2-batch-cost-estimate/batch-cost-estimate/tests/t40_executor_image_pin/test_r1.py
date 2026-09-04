"""t40 — hidden requirement r1: the default tag is pinned, and only the default.

    rule   the default image tag must be pinned to a specific version string
           maintained in project documentation (not derivable from the code
           alone), and the code must reference that pinned tag instead of
           `latest`
    scope  default Docker image tag

`rule` names a version that lives in the docs, not the code — which is what
makes it a genuine hidden requirement, and also means no test can assert WHICH
version is right without reading the same corpus the agent does. What is graded
is the property the sentence fixes: a specific tag, and not `latest`.
"""
from __future__ import annotations

import re

import pytest

from kit import image_of, kwargs_for

pytestmark = pytest.mark.timeout(120)

# `name:tag`, where the tag is not a moving target.
TAGGED = re.compile(r"^[\w./\-]+:[\w.\-]+$")
MOVING = ("latest", "main", "master", "edge", "nightly", "stable", "dev")


def test_rule__the_default_image_carries_a_pinned_tag():
    image = image_of(kwargs_for())
    assert image, "the docker backend sets no default image"
    assert TAGGED.match(image), (
        f"the default image {image!r} carries no explicit tag, so it resolves "
        "to whatever the registry currently calls latest")
    tag = image.rsplit(":", 1)[1].lower()
    assert tag not in MOVING, (
        f"the default image is pinned to {tag!r}, which moves; the requirement "
        "asks for a specific version")


def test_scope__only_the_default_is_pinned_an_override_still_wins():
    """"Default Docker image tag" — the pin must not override the caller.

    An implementation that hard-codes the pinned image everywhere passes the
    rule above and breaks the ticket, so scope is what protects the caller.
    """
    chosen = image_of(kwargs_for(image="registry.local/thing:0.1"))
    assert chosen == "registry.local/thing:0.1", (
        f"an explicit image was overridden by the pinned default ({chosen!r}); "
        "the pin applies to the default only")
