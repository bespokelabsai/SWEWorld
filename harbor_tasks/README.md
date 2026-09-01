# harbor_tasks

Harbor tasks built from `data_gen/input/tasks.json`, one folder per task
holding every version of it.

```
t1-cache-stats/
    cache-stats/          the real task — the ticket, and nothing about the
                          hidden requirements
    cache-stats-spec/     the control — the same task with both hidden
                          requirements written into instruction.md
    cache-stats-clues/    every remark phase 3 planted for this task, quoted
                          in date order with who said it and where, herrings
                          among them — the requirement is never stated
    fixtures/oracle.py    the informed implementation
    fixtures/naive.py     the obvious one
    README.md             what this task asks, and whether each fact is
                          measurable (generated)
```

The three arms decompose a low blind score, which is otherwise ambiguous
between three different failures. `-spec` asks whether the requirement can be
implemented once stated; `-clues` whether it can be *inferred* from the raw
remarks; the blind arm whether those remarks can be *found* in a world at all.
`-clues` matching its `-spec` twin means the plant is sufficient and any blind
gap is retrieval; `-clues` matching the blind arm means the plant is too thin
and no amount of corpus work will fix it.

`t0-smoke/` is the environment sanity task: no hidden requirements, no
control, and it exists to separate "the world is broken" from "the agent
failed".

Shared, not per task: `_suites/` (the graders, copied into every task's
`tests/` at build time), `_env/Dockerfile` (the `sweworld:repo-only-dev`
base), `build_tasks.py` (emits the tasks), `make_bracket.py` (emits the
reports), and `BRACKET.md` (whether the hidden requirements are real).

## Running

```bash
harbor run -c harbor_tasks/all.yaml -a oracle          # everything
harbor run -p harbor_tasks/t1-cache-stats -a oracle    # one task, both versions
harbor run -p harbor_tasks/t1-cache-stats/cache-stats  # one version
```

**`-p harbor_tasks` runs nothing.** Harbor expands a dataset directory with a
single non-recursive `iterdir()` (`models/job/config.py`), so a folder of
folders-of-tasks reads as a folder with no tasks in it. `all.yaml` names each
group directory, which is why it exists.

The same rule explains the leaf names. A trial lands in
`jobs/<job>/<task-dir-name>__<hash>/`, so the directory name *is* the task
name in every result table — `blind/` and `spec/` inside each folder would
have produced four indistinguishable `blind__<hash>` rows.

## Rebuilding

```bash
python3 harbor_tasks/build_tasks.py --limit 4     # or --pick t7,t12
python3 harbor_tasks/make_bracket.py              # after re-measuring
python3 harbor_tasks/clue_digest.py t1            # read one clue dump
```

`build_tasks.py` is idempotent and rewrites `tests/` wholesale from
`_suites/`. It reads `data_gen/build/clues.json` for the `-clues` arm, so
**rebuild after every phase-3 re-plant** — a re-plant rewrites that file
wholesale and the instructions would otherwise quote remarks the corpus no
longer contains. Each `-clues` instruction carries an HTML comment stamping
the plant it was built from, so a stale one is visible rather than silent.
Two build-time gates fail the run rather than emit a bad arm: an answer-key
leak (a `settles` clause or subconclusion reaching the instruction, which
would make it a reworded `-spec`) and a coverage gap (a fact no planted remark
carries, which the arm could not pass for reasons that are not the agent's). `make_bracket.py` reads `_suites/bracket_matrix.txt` and never
measures anything itself, so regenerating the prose cannot quietly change a
number.
