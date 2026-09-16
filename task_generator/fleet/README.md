# fleet — five tasks at once

> New to the pipeline this drives? Read
> [`docs/task-generator-guide.html`](../../docs/task-generator-guide.html) or the "In brief"
> section of [`task_generator/README.md`](../README.md) first.

`task_generator/` builds one task per hand-walked pass through ~20 stages. This
walks five at a time. It is **additive and droppable**: it drives `cli.py` as a
subprocess exactly as a person would type it, it edits no file outside this
directory, and if it does not work the whole experiment is

```bash
rm -rf task_generator/fleet task_generator/out/<the new slugs> \
       harbor_tasks/g{7,8,9,10,11}-* harbor_tasks/_suites/g{7,8,9,10,11}_*
git checkout task_generator/tasks.generated.json
```

after which the sequential path is exactly as it was.

## Run it

```bash
python3 task_generator/fleet/orchestrate.py start --dry-run --ids g7,g8,g9,g10,g11
python3 task_generator/fleet/orchestrate.py verify          # free; calibrates the gates

setsid nohup python3 task_generator/fleet/orchestrate.py start \
    --ids g7,g8,g9,g10,g11 --through B --budget-usd 350 \
    > /tmp/fleet.log 2>&1 < /dev/null &

python3 task_generator/fleet/orchestrate.py status
python3 task_generator/fleet/orchestrate.py note "a learning every later judge call reads"
python3 task_generator/fleet/orchestrate.py resume
```

Detached, not merely backgrounded: eleven of g4's eighteen stages ran longer than
ten minutes, which is where several harnesses cut a child off.

`--through` defaults to **B** and phase C must be named. Phase A is the cut
through `emit`; phase B is the spec and blind arms proven on Horizon. Phase C
(the plant) is written and gated. Phase D (the in-world arm) is not built and
`plan.phase_d()` raises rather than silently doing nothing.

## What it actually adds

Not the stages -- those are `tg/recipe.STAGES`, imported rather than copied. What
it adds is the four things a person does around each one:

| | |
|---|---|
| `plan.py` | the phase boundaries, the re-bracket after `trim`, and everything on Horizon (which appears in no script anywhere in the repo) |
| `locks.py` | the three shared resources five concurrent tasks fight over |
| `gates.py` | the reader for detectors that already existed and had none |
| `judge.py` | the decisions the README says are not automated, each answering with one value from a closed enum |
| `hosted.py` | the `horizon` CLI, with each of its documented edges handled where it is handled |
| `state.py` | one atomic read-modify-write; `runs/<id>/state.json` is the record |
| `worker.py` | one task's state machine |

## Why it does not use `cli.py make`

`make` "cannot tell a fatal exit from an advisory one -- `split` and `bracket`
both exit non-zero on a heuristic, and a driver that stops on every non-zero exit
stops on a perfectly good artifact while a driver that ignores them spends $19
into a cut that was already dead." Telling those apart is what `gates.py` and
`judge.py` are for, and it is the reason this exists at all.

## The three concurrency hazards, and why none of them is patched

Patching them would put the fleet's failure modes into the sequential path, which
is the one thing this experiment must not do.

| hazard | worked around by |
|---|---|
| `cli new` globs `out/*/task.json` for the next free id | `--id` is always passed explicitly |
| `emit` rewrites the whole `tasks.generated.json` array | `flock` on `locks/generated.lock` — take the same lock if you emit by hand |
| a harbor trial wants 4 CPU / 13000 MB on a 4-CPU box | measure on Horizon; `locks/trial.lock` around any local trial |

## Verified before it was trusted

- `orchestrate.py verify` replays every `bracket.json` in `out/`. It ships g1, g2,
  g3, g4 and g6, refuses g5 on seven coincidences, and catches every archived bad
  cut — g1's cut-1, g2's three wasted re-cuts, and g4's pre-amendment cut with the
  `open_feature`-fails-on-naive message. That is every bracket decision on record.
- Five concurrent `new` calls: unique ids, no lost state field, every attempt
  counter and history row kept.
- `flock` holds across threads and across processes.
- The judge, given g5's real bracket and its real `naive.patch`, answered
  `author_extend` and ruled out `resplit` — the call that cost g2 $6.

## Writing a brief: keep the open feature small in INVENTED SURFACE

Measured across the five tasks of the first run, on the rate at which a
ticket-only hosted rollout managed to build the open feature at all:

| task | ticket | `test_open` asserts | blind build rate |
|---|---|---|---|
| example-encoding | 7.4k | 35 | **8/11** |
| training-step-ledger | 10.3k | 93 | **7/10** |
| token-capacity-budget | 10.9k | 102 | 3/10 |
| agent-turn-ledger | 10.2k | 52 | **1/11** |
| attachment-payload | 9.3k | 60 | **0/4** |

**It does not track ticket length or test size.** `token-capacity-budget` has
twice the assertions of `agent-turn-ledger` and builds three times as often.

What it tracks is how much brand-new public API has to be invented *exactly*
right. `example-encoding` and `training-step-ledger` change behaviour inside
files that already exist, so the shapes are given. `agent-turn-ledger` asks for
a new module with frozen dataclasses (not pydantic, not NamedTuple) in an exact
field order, `entries` as a `tuple` and never a `list`, six module-level
functions with exact signatures, and an exception carrying three named
attributes — and one deviation fails `test_open`.

### Correction, from reading the transcripts rather than the scores

The table above is real but the first explanation for it was wrong. Reading
`agent-turn-ledger`'s eleven blind transcripts gives two concrete causes:

**Three of eleven rollouts, the opus one included, lost their shell.**
`AgentStatusTracker.__post_init__` starts a rich/tqdm LIVE DISPLAY (lines
97-100). In a non-TTY container session that wedges the terminal: the agent
sends `echo ok`, `pwd`, `ls` and gets nothing back for the rest of the rollout,
then marks the task complete unverified. The task is ABOUT the tracker, so
exercising the thing under test is what killed the session.

**So the sharper brief criterion is: avoid an area whose code starts a live
display, spawns a pager, or takes over the terminal when merely constructed.**
An agent cannot help exercising the thing it is implementing.

The remaining eight built plausible implementations, self-certified with import
checks, and got the exact semantics wrong -- most likely the seed-logging that
`test_open` pins as `authors() == [SEEDER, PARTNER, SEEDER, PARTNER, SEEDER]`.
They had no choice about the self-certification: **a blind agent cannot run the
graded suite**, and neither can the local `naive` build (both get `cli exec`,
never `cli suite`). The local build passes anyway because it can iterate freely
against a container, where a rollout has turn limits and a shell that can die.
That is an execution-affordance gap, not an information gap, and it means a
local `naive` pass on `open_feature` does NOT predict the hosted blind arm.

The surface argument below still holds as a secondary factor, but it is
fragile in a one-shot hosted rollout even when the ticket states every word of
it. A local `naive` build passes it, because a local build iterates against
`cli suite`; a rollout gets one attempt.

Why it matters: `open_feature` at 1.0 is what makes a blind 0.00 readable. An
open feature the blind arm cannot build turns the headline number into "the
agent built nothing", and the arm then costs many rollouts to measure at all —
`agent-turn-ledger` needed eleven to get one usable sample.

So when writing a brief, prefer an area where the feature is a **behaviour
change inside existing shapes**. `example-encoding`'s brief asked for "pure
functions over lists, one tokenizer fake" and built 8 times in 11.
