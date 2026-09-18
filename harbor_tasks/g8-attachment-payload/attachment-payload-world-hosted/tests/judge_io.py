"""Hardened reads for the ROOT judge. Stdlib only, no pytest, no agent code.

`harness.py` cannot serve this: it imports pytest, which the judge's interpreter
(`python3 -I`, system python, no PYTHONPATH) does not have.

Why it exists. The judge runs as root and reads three kinds of path the agent can
influence: the cloned submission, the worker's artifacts directory, and the
observations file. A plain `Path.read_text()` follows symlinks, so a worker that
plants `artifacts/x -> /tests/task.json` makes the root judge read the answer key
and copy it into junit/ctrf -- the report the trial ships. An unbounded file is the
other half: the judge has a fixed budget, and a multi-gigabyte "source file" spends
it, which reads as a broken harness rather than a failed task.

So every read here refuses a symlink (O_NOFOLLOW), refuses anything that is not a
regular file, and refuses a file over the cap. It RAISES rather than returning
something empty: a judge that cannot read what it is grading must fail the fact,
never pass it blind.
"""
from __future__ import annotations

import os
import stat

# 8 MiB. The largest thing any judge reads is a curator module (tens of KiB) or an
# observations file (a few hundred KiB); the cap only has to be smaller than the
# verifier's memory budget and larger than anything legitimate.
LIMIT = 8 * 1024 * 1024


class UnsafeRead(OSError):
    """The path is a symlink, not a regular file, or over the size cap."""


def read_bytes(path, *, limit: int = LIMIT) -> bytes:
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise UnsafeRead(f"{path}: not a regular file")
        if st.st_size > limit:
            raise UnsafeRead(f"{path}: {st.st_size} bytes over the {limit} cap")
        with os.fdopen(fd, "rb") as fh:
            fd = -1
            return fh.read(limit + 1)[:limit]
    finally:
        if fd >= 0:
            os.close(fd)


def read_text(path, *, limit: int = LIMIT) -> str:
    return read_bytes(path, limit=limit).decode("utf-8", errors="replace")
