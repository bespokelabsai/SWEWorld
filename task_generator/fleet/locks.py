"""The three shared resources five concurrent tasks fight over.

Nothing in `task_generator/` locks anything, because nothing in it was ever run
twice at once. Three of its writes are not safe under concurrency, and rather
than patch `tg/` -- which would put the fleet's failure modes into the
sequential path this experiment is supposed to be separable from -- each is
wrapped from outside here.

`flock`, not a threading lock, for two of them: the user runs `cli.py emit g4`
by hand while the fleet is running, and a lock only the fleet's own threads
respect would not see that.

    generated   `tg/emit.py:113-116` reads the whole tasks.generated.json array,
                filters this id out, appends and rewrites. Two emits racing lose
                a row, and the loser is a task that then exists in out/ and in
                harbor_tasks/ but is invisible to `build_tasks.py --extra-tasks`.

    trial       a harbor trial asks for 4 CPUs and 13000 MB on a 4-CPU, 15 GB
                box. Two overlapping trials do not fail cleanly; they both run
                slowly and one gets OOM-killed, which reads in the results as an
                agent failure.

    devbox      `tg/suite.py` funnels every bracket, suite and exec through
                `docker exec devbox`. Paths inside are uuid-tagged so they do
                not collide, but a bracket is four full pytest runs and five at
                once starves them all. Bounded rather than serialised: this is
                a throughput valve, not a correctness one.
"""
from __future__ import annotations

import contextlib
import fcntl
import pathlib
import threading

HERE = pathlib.Path(__file__).resolve().parent
LOCKDIR = HERE / "locks"

# Two brackets at a time. Measured intent, not a guess to tune later: a bracket
# is four sequential pytest runs of ~8s each against a container that is also
# serving whatever else is live, and the box has 4 CPUs.
DEVBOX_SLOTS = 2

_devbox = threading.BoundedSemaphore(DEVBOX_SLOTS)


@contextlib.contextmanager
def flock(name: str, *, timeout_s: float | None = None):
    """Hold an advisory lock on `locks/<name>.lock` for the block.

    Blocking by design. A fleet worker that cannot emit right now should wait
    for the worker that can, not skip the stage and carry on -- skipping is how
    a row goes missing from tasks.generated.json without anything printing.
    """
    LOCKDIR.mkdir(parents=True, exist_ok=True)
    path = LOCKDIR / f"{name}.lock"
    with open(path, "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield path
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


@contextlib.contextmanager
def devbox():
    """One of `DEVBOX_SLOTS` concurrent runs against the shared container."""
    _devbox.acquire()
    try:
        yield
    finally:
        _devbox.release()


# Which lock a stage needs. Keyed by the cli subcommand, so adding a stage to
# `plan.py` without deciding this is a KeyError rather than a silent race.
# Only the steps that are PURELY container work take the devbox slot.
#
# `build` and `tests` are nine-minute agent turns that happen to shell into the
# container for a few seconds of pytest near the end. Holding the slot across
# the whole step would serialise four nine-minute builds two at a time to
# protect eight seconds of contention -- roughly doubling the wall clock of a
# fan-out for no benefit. `bracket` and `prove` are the opposite: back-to-back
# pytest runs against the shared container with no agent turn at all.
STAGE_LOCKS = {
    "emit": ("flock", "generated"),
    "trial": ("flock", "trial"),
    "bracket": ("devbox", None),
    "prove": ("devbox", None),
}
