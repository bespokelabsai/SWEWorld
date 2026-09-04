#!/usr/bin/env python3
"""The NAIVE build of t40 — the ticket, implemented the obvious way.

    python3 naive.py <checkout>

Pins the default image and honours an override, which is exactly what the
ticket asks for and nothing more. It applies no user or filesystem constraints,
because nobody mentioned any — so it should PASS the open feature and r1, and
FAIL r2, which is the hidden half.
"""
from __future__ import annotations

import pathlib
import sys

REL = ("src/bespokelabs/curator/code_executor/code_execution_backend/"
       "sandbox_backend.py")

OLD = """        image = config.image or config.docker_image
        if image:
            self.sandbox_kwargs["image"] = image"""

NEW = '''        image = config.image or config.docker_image or "python:3.11.9-slim"
        if image:
            self.sandbox_kwargs["image"] = image'''


def main(root: str) -> int:
    path = pathlib.Path(root) / REL
    src = path.read_text()
    if 'or "python:3.11.9-slim"' in src:
        print("  = already applied")
        return 0
    if OLD not in src:
        print("  ! image anchor not found", file=sys.stderr)
        return 1
    path.write_text(src.replace(OLD, NEW, 1))
    print("  + t40 naive: pinned default image, no sandbox constraints")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
