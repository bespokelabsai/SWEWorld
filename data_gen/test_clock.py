#!/usr/bin/env python3
"""Does an artifact land in the turn that wrote it, when channels run at once?

`python3 data_gen/test_clock.py` — no dependencies, no network, under a second.
The only test in this tree, and it earns its place: the bug it covers is
invisible in a transcript. A page stamped from the wrong channel's turn reads
fine on its own page and only shows up when you check it against the chat, which
is what `scripts/check_corpus.py` had to be written to do after the fact.

Three things it holds down:

  the interval   an artifact is written over the preceding quarter hour, not in
                 the second before somebody mentions it
  the key        the cursor is per PERSONA. Channels run concurrently against
                 one shared Clock (`_batches(channels, args.concurrency)`,
                 `concurrent=True`), so a single cursor is a race: with
                 #code-review pinned at 14:32 and #pipeline pinning 09:40 first,
                 a page written by the 14:32 speaker came out stamped 09:28
  the fallback   a caller that pins nothing keeps the old seven-minute stride,
                 so phase4_run without the engine, and this file, still work

Persona is the right granularity because it is the engine's: `person_locks`
serialises one person's turn across channels "so their single agent session is
never entered twice", and the pin sits inside that lock.
"""
import asyncio
import datetime as dt
import pathlib
import random
import sys
import tempfile
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import worldapps as wa  # noqa: E402

UTC = dt.timezone.utc
DAY = dt.datetime(2025, 3, 4, 9, 0, tzinfo=UTC)


def _wiki():
    root = pathlib.Path(tempfile.mkdtemp())
    (root / "docs").mkdir()
    clock = wa.Clock()
    clock.set_day(DAY)
    return root, clock, wa.Wiki(root, clock, collections={"engineering": "Engineering"},
                                scrub=lambda t: t)


def _stamp(root, rel):
    return (root / "docs" / rel).read_text().split("created_at: ")[1].split("\n")[0]


def test_unpinned_keeps_the_stride():
    _root, clock, _wk = _wiki()
    assert clock.iso() == "2025-03-04T09:07:00+00:00"
    assert clock.iso() == "2025-03-04T09:14:00+00:00"


def test_written_before_it_is_announced():
    root, clock, wiki = _wiki()
    clock.set_now(dt.datetime(2025, 3, 4, 14, 32, tzinfo=UTC), "dermot")
    rel = wiki.write(uid="dermot", title="Batch plan", body="x", collection="engineering")
    wrote = dt.datetime.fromisoformat(_stamp(root, rel))
    gap = dt.datetime(2025, 3, 4, 14, 32, tzinfo=UTC) - wrote
    assert dt.timedelta(minutes=1) <= gap <= dt.timedelta(minutes=20), gap


def test_early_turn_stays_inside_its_day():
    root, clock, wiki = _wiki()
    clock.set_now(DAY + dt.timedelta(minutes=4), "konrad")
    rel = wiki.write(uid="konrad", title="Early", body="x", collection="engineering")
    assert dt.datetime.fromisoformat(_stamp(root, rel)) >= DAY


def test_two_writes_in_one_turn_keep_their_order():
    root, clock, wiki = _wiki()
    clock.set_now(dt.datetime(2025, 3, 4, 14, 32, tzinfo=UTC), "emil")
    a = _stamp(root, wiki.write(uid="emil", title="First", body="x", collection="engineering"))
    b = _stamp(root, wiki.write(uid="emil", title="Second", body="x", collection="engineering"))
    assert a < b <= "2025-03-04T14:32"


def test_concurrent_channels_do_not_steal_each_other_s_turn():
    """The regression this file exists for, run the way the engine runs it."""
    root, clock, wiki = _wiki()
    channels = {
        "code-review": [("dermot", 10, 5), ("konrad", 11, 30), ("emil", 13, 15)],
        "pipeline": [("dario", 9, 40), ("emil", 13, 20), ("dario", 17, 50)],
        "engineering": [("konrad", 9, 20), ("emil", 16, 40), ("dermot", 16, 45)],
        "releases": [("dario", 11, 0), ("konrad", 14, 5)],
    }
    people = {"dermot", "konrad", "dario", "emil"}
    agents = {uid: types.SimpleNamespace(uid=uid) for uid in people}
    locks = {uid: asyncio.Lock() for uid in people}
    seen = []

    async def run_channel(name, turns):
        for uid, hour, minute in turns:
            when = dt.datetime(2025, 3, 4, hour, minute, tzinfo=UTC)
            # The engine holds a person's lock across their whole turn, pin
            # included, so the only thing racing here is other people.
            async with locks[uid]:
                clock.set_now(when, uid)
                await asyncio.sleep(random.random() / 40)
                rel = wiki.write(uid=uid, title=f"{name}-{hour}{minute:02d}", body="x",
                                 collection="engineering")
                seen.append((uid, when, dt.datetime.fromisoformat(_stamp(root, rel))))
            await asyncio.sleep(random.random() / 40)

    async def main():
        await asyncio.gather(*(run_channel(n, t) for n, t in channels.items()))

    random.seed(11)
    asyncio.run(main())
    assert len(seen) == sum(len(t) for t in channels.values())
    for uid, spoke, wrote in seen:
        gap = spoke - wrote
        assert dt.timedelta(minutes=1) <= gap <= dt.timedelta(minutes=20), (uid, spoke, wrote)


def test_a_world_that_never_adopted_this_is_untouched():
    """pantry, northwind, and anything else on the same engine.

    `_pin_app_clock` is best-effort by design: it is the only way a change in
    the library can be safe for clients whose apps it has never seen. Two
    shapes have to pass through it without a mark — an agent with no app clock
    at all, and an app clock that has no `set_now` — because those are every
    world except this one.

    This is a proxy, and a partial one. The examples live in the bespoke_user
    source tree, which is not installed here; what this pins down is the
    mechanism, not their transcripts.
    """
    from bespoke_user import sim_engine as G

    class OldClock:
        """What a world that predates `set_now` hands to `attach_tools`."""
        def __init__(self):
            self.calls = 0

        def iso(self):
            self.calls += 1
            return f"old-{self.calls}"

    old = OldClock()
    agent = types.SimpleNamespace(_extra_app_clock=lambda: old)
    G._pin_app_clock(agent, "someone", dt.datetime(2025, 3, 4, 14, 32, tzinfo=UTC))
    assert old.iso() == "old-1", "a clock without set_now must be left alone"

    # And an agent that was never given tools at all.
    G._pin_app_clock(types.SimpleNamespace(), "someone", dt.datetime.now(UTC))
    G._pin_app_clock(None, "someone", dt.datetime.now(UTC))


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in tests:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"{len(tests)} passed")
