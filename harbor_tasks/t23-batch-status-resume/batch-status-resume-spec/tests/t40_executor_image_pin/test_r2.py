"""t40 — hidden requirement r2: the sandbox is locked down whatever image runs.

    rule              when a caller overrides the image via backend_params, the
                      executor must still enforce the same non-root user and
                      read-only filesystem constraints applied to the default
                      pinned image — an overridden image must not run as root
                      even if its own Dockerfile defaults to root
    scope             security constraints applied regardless of which image
    failure_behavior  if the enforced settings are incompatible with a custom
                      image, the container must fail to start with a clear
                      error, not silently run with elevated privileges

Read off `sandbox_kwargs` rather than by starting a container. The names are
discovered, not fixed: the requirement says non-root and read-only, and says
nothing about what the keyword should be called.
"""
from __future__ import annotations

import pytest

from harness import unmeasured
from kit import (image_of, is_non_root, kwargs_for, readonly_setting,
                 user_setting)

pytestmark = pytest.mark.timeout(120)


def test_rule__an_overridden_image_is_not_allowed_to_run_as_root():
    """The sentence makes two claims of different strengths, and they are
    graded differently.

    ABSOLUTE — "an overridden image must not be allowed to run as root inside
    the container even if the custom image's own Dockerfile defaults to root."
    Nothing conditions that on anything, so it is required outright.

    RELATIVE — "the same non-root user and read-only filesystem mount
    constraints APPLIED TO THE DEFAULT PINNED IMAGE". That presupposes the
    default already carries such constraints, and in baseline curator it
    carries none, so there is nothing to be "the same" as. Demanding read-only
    outright asked for something the requirement only states by parity with a
    baseline that does not have it — so read-only is checked against the
    default rather than in the absolute.
    """
    override = kwargs_for(image="untrusted.io/whatever:1.0")
    assert image_of(override) == "untrusted.io/whatever:1.0", (
        "the override did not take effect, so what happens to its privileges "
        "cannot be read")

    uname, uvalue = user_setting(override)
    assert uname is not None and is_non_root(uvalue), (
        "nothing in what the backend would pass the sandbox stops an overridden "
        "image running as root, and the requirement says outright that it must "
        f"not be allowed to: {override}")

    # Read-only, by parity: only required of an override if the default has it.
    default = kwargs_for()
    dname, dvalue = readonly_setting(default)
    if dname is not None and dvalue not in (None, False):
        oname, ovalue = readonly_setting(override)
        assert oname is not None and ovalue not in (None, False), (
            f"the default image is mounted read-only ({dname}={dvalue!r}) and "
            f"an overridden one is not: {override}")


def test_scope__the_constraints_do_not_depend_on_which_image_it_is():
    """"Security constraints applied regardless of which image is used."

    Graded as consistency between two different overrides rather than as an
    absolute demand, for the same reason as above: the requirement fixes that
    the constraints do not vary with the image, not what they must be. An
    implementation that locks down one registry and trusts another fails; one
    that treats every image alike passes, whatever it decided to apply.
    """
    a = kwargs_for(image="registry.a/one:1.0")
    b = kwargs_for(image="registry.b/two:2.0")

    ua, va = user_setting(a)
    ub, vb = user_setting(b)
    assert (ua, va) == (ub, vb), (
        f"two different overridden images got different user settings — "
        f"{ua}={va!r} versus {ub}={vb!r}; the constraints are supposed to apply "
        "regardless of which image is used")

    ra, wa = readonly_setting(a)
    rb, wb = readonly_setting(b)
    assert (ra, wa) == (rb, wb), (
        f"two different overridden images got different filesystem settings — "
        f"{ra}={wa!r} versus {rb}={wb!r}")


def test_failure_behavior__an_incompatible_image_fails_loudly():
    """"...must fail to start with a clear error, not silently run with
    elevated privileges."

    UNMEASURABLE here, and skipped rather than failed. "Fail to START" is about
    what the container does when it is launched, and launching one needs Docker
    inside the trial container, which is not available. Everything else in this
    suite is read from the arguments the backend would pass; whether the daemon
    then rejects them is a fact about the daemon.

    `rule` and `scope` still grade the half that decides the outcome: an
    overridden image does not get to run as root.
    """
    unmeasured("verifying that a container FAILS TO START needs a running "
               "Docker daemon inside the trial, which is not available; the "
               "arguments that would be passed are graded instead")
