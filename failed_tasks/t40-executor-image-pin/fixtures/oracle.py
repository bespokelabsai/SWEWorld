#!/usr/bin/env python3
"""The ORACLE build of t40 — the ticket plus both hidden requirements.

    python3 oracle.py <checkout>

`SandboxCodeExecutionBackend.__init__` builds `sandbox_kwargs` and passes only
what the caller gave it, so with no image the sandbox library falls back to its
own `latest` and nothing is constrained.

r1: a pinned default tag, used when the caller names no image.
r2: the non-root user and read-only filesystem go on REGARDLESS of which image
    is running — applied after the image is chosen, so an override cannot skip
    them, which is the whole point of the fact.

The pinned version here stands in for the one the project documentation
carries; the tests grade that a specific tag is used and that it does not move,
not which number it is.
"""
from __future__ import annotations

import pathlib
import sys

REL = ("src/bespokelabs/curator/code_executor/code_execution_backend/"
       "sandbox_backend.py")

OLD = """        # Prefer explicit `image`, fall back to legacy `docker_image`
        image = config.image or config.docker_image
        if image:
            self.sandbox_kwargs["image"] = image"""

NEW = '''        # Prefer explicit `image`, fall back to legacy `docker_image`, then
        # to the pinned default. Unpinned meant the sandbox library's own
        # `latest`, which changes under a running pipeline.
        image = config.image or config.docker_image or DEFAULT_DOCKER_IMAGE
        if image:
            self.sandbox_kwargs["image"] = image
        # Applied AFTER the image is chosen, so an overridden image gets the
        # same constraints as the pinned one. A custom image whose Dockerfile
        # defaults to root does not get to run as root here.
        self.sandbox_kwargs["user"] = NON_ROOT_USER
        self.sandbox_kwargs["read_only"] = True'''


def main(root: str) -> int:
    path = pathlib.Path(root) / REL
    src = path.read_text()
    if "DEFAULT_DOCKER_IMAGE" in src:
        print("  = already applied")
        return 0
    if OLD not in src:
        print("  ! image anchor not found", file=sys.stderr)
        return 1

    src = src.replace(OLD, NEW, 1)
    # Module-level, so it is one place to change when the docs move.
    marker = "\nclass SandboxCodeExecutionBackend"
    if marker not in src:
        marker = "\nclass "
    src = src.replace(
        marker,
        '\n# The tag the project documentation pins the executor to.\n'
        'DEFAULT_DOCKER_IMAGE = "python:3.11.9-slim"\n'
        '# uid:gid of the unprivileged account the sandbox images ship with.\n'
        'NON_ROOT_USER = "1000:1000"\n' + marker, 1)
    path.write_text(src)
    print("  + t40.r1: default image pinned to a specific tag")
    print("  + t40.r2: non-root user and read-only fs applied to any image")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
