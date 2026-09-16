# Patches for `bespoke_user`

`bespoke_user` is installed, not vendored — `~/.local/lib/python3.10/site-packages/bespoke_user/`
— and phase 4 is one of its callers. A change that belongs in the library cannot
live in this repo, so it is proved in site-packages and handed over as a diff
here.

Apply with:

```bash
cd ~/.local/lib/python3.10/site-packages/bespoke_user
patch -p0 < /path/to/SWEWorld/data_gen/patches/<name>.patch
```

## `sim_engine-pin-app-clock.patch`

**The message clock and the tool clock were different clocks.**

`worldapps.Clock` advanced a private counter seven minutes per call from the
day's start. The engine computed each turn's wall-clock time in its own loop
(`cur_dt` / `turn_dt`) and handed it to nobody — its own docstring said so:
"advances alongside rather than in lockstep: the same day and the same order,
not the same instant."

The cost shows up only when you check one artifact against another. All 108 wiki
pages in the corpus landed between 09:14 and 10:38 across thirteen distinct
clock values, because that is where `day_start + 7k minutes` puts them, and none
of those values had anything to do with the conversation that produced the page.
A channel opening at 09:00 with *"the design doc is up on the wiki"* was
announcing a file stamped 09:14. 96 chat messages contradicted a page's own
`created_at`.

The patch adds three things:

* `attach_tools` hands the client's clock out as `user._extra_app_clock`, the
  same seam the apps themselves already come through. The library cannot stamp
  app writes — the clock is the client's object — but it is the only thing that
  knows what time a turn happens.
* `_pin_app_clock(agent, when)`, best-effort: a clock with no `set_now` keeps
  its own behaviour, so a client that has not adopted this is not broken by it.
* One call, immediately after `turn_dt` is computed and **before** the agent
  runs, so anything its tools write is stamped inside that turn.

The matching client-side half is `Clock.set_now()` in `data_gen/worldapps.py`,
and `data_gen/test_clock.py` covers both.

**The pin is keyed by persona, not global.** Channels run concurrently in
batches (`_batches(channels, args.concurrency)`, `concurrent=True`) against one
shared clock, so a single cursor is a race — measured: with #code-review pinned
at 14:32 and #pipeline pinning 09:40 before the first channel's tool call ran, a
page written by the 14:32 speaker came out stamped 09:28. Persona is the right
granularity because it is the engine's own: `person_locks` already serialises
one person across channels "so their single agent session is never entered
twice", and the pin sits inside that lock.

**What it does not fix.** Syncing the clocks removes arbitrary drift; it does not
make a persona write a page before announcing it, and nothing in the engine can.
That is what `scripts/check_corpus.py --fix` reconciles after a run, and what
`check_corpus.py` gates on before a bake.
