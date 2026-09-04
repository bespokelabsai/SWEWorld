"""Shared readers for t40.

Everything is read off `sandbox_kwargs` — the dict the sandbox backend
assembles in `__init__` and hands to the sandbox library when it eventually
runs. Nothing here starts a container: docker-in-docker is not available inside
a trial, and a suite that needed it could not grade this task at all.

`SandboxCodeExecutionBackend.__init__` builds that dict from the config and
stores it, so the image, the user and the mount flags an implementation intends
to apply are all visible before anything executes.
"""
from __future__ import annotations

import pytest

from bespokelabs.curator.code_executor.code_executor import CodeExecutor


def kwargs_for(**backend_params) -> dict:
    """What the docker backend would hand the sandbox, without running it."""
    executor = CodeExecutor(backend="docker", backend_params=backend_params or None)
    backend = getattr(executor, "_code_executor", None)
    kw = getattr(backend, "sandbox_kwargs", None)
    if kw is None:
        pytest.fail(
            "the docker backend exposes no sandbox_kwargs, so what it would "
            f"pass to the sandbox cannot be read. Backend: {type(backend).__name__}")
    return dict(kw)


def image_of(kw: dict) -> str | None:
    for name in ("image", "docker_image", "image_name", "container_image"):
        if kw.get(name):
            return str(kw[name])
    return None


def _looks_like(name: str, words) -> bool:
    low = name.lower()
    return any(w in low for w in words)


def _walk(kw, prefix=""):
    """Every (dotted-name, value) pair in a nested mapping.

    Nesting matters. A real implementation grouped its sandbox settings under
    `backend_options`:

        {"image": ..., "backend_options": {"user": "65534:65534",
                                           "read_only": True, "tmpfs": {...}}}

    which is a perfectly good shape — arguably a tidier one — and a top-level
    scan reported it as "nothing says the container runs as a non-root user".
    The requirement fixes neither the key names nor the depth they live at, so
    neither does this.
    """
    if not isinstance(kw, dict):
        return
    for name, value in kw.items():
        yield (f"{prefix}{name}", value)
        if isinstance(value, dict):
            yield from _walk(value, f"{prefix}{name}.")


def user_setting(kw: dict):
    """Whatever the implementation used to say "not root", under any name."""
    for name, value in _walk(kw):
        leaf = name.rsplit(".", 1)[-1]
        if _looks_like(leaf, ("user", "uid", "run_as", "runas", "privileg")) \
                and not isinstance(value, dict):
            return name, value
    return None, None


def readonly_setting(kw: dict):
    """Whatever the implementation used to say "read-only filesystem"."""
    for name, value in _walk(kw):
        leaf = name.rsplit(".", 1)[-1]
        if _looks_like(leaf, ("read_only", "readonly", "read-only", "ro_",
                              "mount", "volume", "tmpfs", "filesystem")):
            return name, value
    return None, None


def is_non_root(value) -> bool:
    """True when the value plainly means "somebody other than root"."""
    if value is None or value is False:
        return False
    if isinstance(value, bool):
        return value                              # e.g. non_root=True
    if isinstance(value, int):
        return value != 0
    text = str(value).strip().lower()
    if not text or text in ("root", "0", "0:0", "root:root"):
        return False
    return True
