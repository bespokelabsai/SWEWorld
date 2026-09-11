# task_generator

Authors a hidden-requirement task by **designing the whole implementation first
and cutting it afterwards**, and proves the cut discriminates before spending
anything on an agent trial.

It is the front half that `harbor_tasks/` was missing. That half runs the
experiment — blind / `-spec` / `-clues` arms, per-fact reward keys, OAuth-only
trials — but the 60 tasks it draws from were written ticket-first with hidden
requirements attached afterwards, and the measured bracket says what that cost:
**13 of 29 facts are coincidences**, passed by an implementation that never saw
the requirement, and 3 are unmeasurable. Each of those was discovered after a
paid trial.

## Overview: the whole pipeline, and the clues arm, in brief

Each task goes from a brief to up to **five gradable arms of the same ticket**,
proving the gap between them rather than asserting it:

```
author → build oracle/naive/spec → split → tests → bracket (gate: every fact
must read `hidden`) → emit (writes the harbor artifacts) → [clues, optional]
→ horizon (renders blind/spec/clues as hosted arms) → trial / hosted eval
```

- **`blind`** — the ticket alone. Should score ~0.
- **`spec`** — ticket + the hidden requirements, stated outright. Should score
  ~1.00: proof the requirements as written are sufficient to solve it.
- **`clues`** — ticket + every planted remark quoted inline, date-ordered. The
  ceiling — can an agent use evidence once it has already been pulled out for
  it.
- **`world`** / **`world-hosted`** — the plain blind ticket, but run against an
  actual populated SWEWorld image whose chat, wiki and mail genuinely contain
  those same remarks, scattered among everything else. The real test: can an
  agent find the evidence itself, not just use it once handed over. See "The
  in-world arm" below. (`world-hosted` is the same arm pushed to Horizon, and
  lives in a separate project, `sweworld`, from the apex arms' `nidhi-test`.)

**How a plant becomes a corpus (`cli.py clues <slug>`, `tg/clues.py`):** unlike
`data_gen/phase3_plant.py`, which plants into conversation *specs* before
anything is simulated, this plants **after** — into a corpus that already
exists. Per hidden requirement: build a MuSR-style tree of subconclusions and
leaf remarks, write any reversed-decision herrings, place each leaf in a real
carrier (an existing chat day, wiki page, comment or mail thread) or invent one
only if nothing fits, then turn a single remark into a real multi-turn exchange
(`reknit`) and judge which claims actually survived it. `cli.py prove` then
builds from just the ticket and the remarks and scores it with the real suite,
to prove the plant is solvable before anything is trusted; `cli.py repair`
fixes only the remarks `prove` blames, in place, rather than re-rolling the
whole tree. `cli.py settle` is the strictest check of all — it decomposes each
requirement's own test assertions and judges every one `stated` / `implied` /
`absent` / `not_required` against the corpus (see "Rubric conditions 3 and 4"
below).

`tg/clues.py` itself only writes `out/<slug>/clues/` — the plant ledger, not
the corpus. `tg/inject.py` is the only code that writes into an actual copy of
the corpus (`messages.jsonl`, `comments.jsonl`, `docs/*.md`, `emails/*.eml`),
which is what the `world` arm needs a re-baked image for.

## The two loops

```
                          free, ~1 min, deterministic          paid, ~20 min, ~$9
  author ─ build oracle ─ split ─ tests ─ build naive ─ BRACKET ─ audit ─ emit ─ trial
                                                          │
                                          nothing is emitted until every fact
                                          reads `hidden` here
```

**The bracket is the gate.** One suite, three trees:

| verdict | pristine | naive | oracle | what it means |
|---|---|---|---|---|
| `hidden` | fail | fail | pass | ships |
| `coincidence` | fail | **pass** | pass | Catalog A — the clue was unnecessary |
| `vacuous` | **pass** | pass | pass | the test does not require the feature to exist |
| `broken` | — | — | **fail** | Catalog B, or the test is wrong |

`naive` is written by a separate `claude -p` that has seen only `ticket.md` — the
rubric's blind condition, mechanised, for about a dollar instead of nine. It is
built in a **system temp directory**, not under this repo, because the answer key
sits in `out/<slug>/facts.json` and an agent that wandered into it would
invalidate the one measurement the package exists to make.

Folding is done by `harbor_tasks/_suites/score.py` — imported, not
reimplemented — so a fact key here means exactly what it will mean in
`jobs/<job>/result.json`. A free bracket that disagreed with the paid trial about
what `g1.r1.rule` means would make the comparison unreadable.

## Commands

One command runs the whole thing and stops at the first gate that does not pass:

```bash
cli() { python3 task_generator/cli.py "$@"; }

cli new  <slug> --brief "<the area, and what is hard about it>"
cli make <slug> --dry-run       # the stages, the gates, the projected spend
cli make <slug>                 # walk them; stops at the first failed gate
cli make <slug> --from clues    # resume after fixing whatever it printed
```

`make --dry-run` prints the table below out of `tg/recipe.py`, with a `spent`
column read from this task's own `spend.json`, so "what is left to pay" is a
subtraction rather than a guess.

| stage | gate | budget | what it is for |
|---|---|---|---|
| `new` | | — | scaffold `out/<slug>/` from the brief you wrote |
| `author` | | $5.79 | the whole specification, nothing hidden yet |
| `build --role oracle` | | $3.49 | implement all of it |
| `split` | **yes** | $1.26 | cut into ticket + hidden requirements. Fails unless every fact has an invented anchor the ticket does not print |
| `tests` | **yes** | ? | one decisive test per fact, green on the oracle. Never measured — largest per-call budget here |
| `build --role naive` | | $1.93 | ticket only, fresh context, isolated tree |
| `build --role spec` | | $2.00 | the ceiling arm's twin — builds from what `-spec` is actually handed, not from `whole.md` |
| `bracket` | **yes** | free | pristine / naive / oracle / spec → a verdict per fact. Every fact must read `hidden` |
| `audit` | **yes** | ? | one adversarial Catalog A/B call per fact. **Never run on g1** — `--optional` |
| `trim` | | $2.95 | cut each requirement to what its assertions actually check |
| `emit` | **yes** | free | write the harbor artifacts; refuses unless the bracket shipped |
| `clues` | **yes** | $48 | the plant. ~175 placement calls, and **two thirds of the whole bill** |
| `settle` | | $10.73 | rewrite every graded assertion a reader was left to infer |
| `reverse` | **yes** | $1 | say out loud that each herring's decision was dropped |
| `reorder` | **yes** | $1 | move a decision dated before the complaint it answers. Before `reknit`, not after |
| `reknit` | **yes** | $9 | turn each remark into the exchange it was made in |
| `prove --runs 3` | **yes** | $5.50 | build from ticket + remarks alone, three times, and score with the real suite |
| `horizon --arms blind,spec,clues` | **yes** | free | the hosted arms. Name `clues` or its gate does not run |
| `inject` | **yes** | free | write the plant into a copy of the corpus, for the in-world arm. `--optional` |

Then measure. Locally first — one machine, one model, the instruction the only
variable — and spend hosted rollouts only on what the local bracket cannot answer:

```bash
cli trial <slug> --arm blind        # ~25 min, ~$7
cli trial <slug> --arm spec         # the ceiling
cli trial <slug> --arm clues        # the remarks, quoted in the ticket
cli report <slug>                   # -> report.md, the four-condition matrix
```

And to build the harbor arms after `emit`:

```bash
python3 task_generator/build_tasks.py \
    --extra-tasks task_generator/tasks.generated.json --pick g1 [--world]
```

`harbor_tasks/` is this package's **output tree**: `build_tasks.py`,
`build_located_arm.py`, `refresh_answer_key.py` and `tg/emit.py` all write into
it, and nothing there writes back. What the package does not touch is the
hand-written 60 in `data_gen/input/tasks.json`, which is what `--extra-tasks` is
for: ids in that file are **positional** (`t1`…`t60`)
and `SLUGS`/`SUITE_DIR` are hardcoded index dicts, so a generated task has to
carry its own id, slug and suite. The hand-written 60 are never touched.
`--world` adds a fourth arm that boots the populated image, where the remarks are
in the corpus rather than in the ticket; it needs `cli inject` to have run and the
image to have been re-baked.

### The hosted arms, end to end

`cli horizon <slug> --arms blind,spec[,clues]` writes one apex task directory per
arm under `out/<slug>/horizon/`. Emitting is where two gates fire:
`unhosted_paths()` refuses a suite that reads outside `/workdir`, `/tests`, `/tmp`
and ordinary Linux, and `unsolvable()` refuses a clues arm whose digest never
types a graded name — the latter only when `clues` is one of the arms, which is
why the flag defaults to naming all three.

**The `horizon` CLI is not on `PATH`.** It lives in its own virtualenv:

```bash
export PATH="$HOME/horizon_env/bin:$PATH"
export HORIZON_API_KEY=...  MINI_BATCH_ID=...

cd task_generator/out/<slug>/horizon
horizon tasks push g<N>-<slug>                        # the blind arm
horizon tasks push g<N>-<slug>-spec                   # the spec arm

horizon tasks validate --mode hosted --agent oracle   # must come back 1.00
horizon tasks validate --mode hosted --agent noop     # must come back 0.00
horizon tasks validate-logs                           # -> <arm>/.validation/

horizon evaluations submit --model biggie-max --runs 3 <task-id>
horizon evaluations watch <eval-id>
horizon rollouts pull <task-uuid>                     # -> horizon/.rollouts/v<N>/
```

`validate -m hosted -a oracle | -a noop` **is this package's own bracket in
Horizon's idiom**, and it is the only way to run it: the `apex_arena:base` image
lives in Horizon's project, not on this box, so the Dockerfile these arms emit
cannot be built locally. `validate-logs` is how the result comes back.

`push` writes `.horizon/metadata.json` — task uuid, name, mini-batch, version —
and `horizon.emit()` reads that file before `rmtree` and writes it back, because
losing it makes the next push create a **second task** rather than a new version.

Rollouts land as `<model>_run<N>_<id>.json` carrying `score` and a
`grade_result.subscores` map keyed exactly like the local bracket (`g1.r1.rule`),
so a hosted number and a local number are directly comparable. Hosted models are
Horizon's own roster (`biggie-max`, `cipher-omni`, `lumen`) and the agent type
that works is `meteor` — `cascade` failed all 20 rollouts with no task binding.
**`meteor` is right for THESE arms only.** Agent type is a function of the task
FORMAT, and the `-world*` arms under `harbor_tasks/` are `format: harbor`, whose
roster is a different one — `typhoon` is what their rollouts have actually run on.
Submitting a harbor task with `meteor` fails the whole evaluation in ~3 minutes
with `rollouts.total: 0`, zero spend and `steps: [provision pending, evaluate
failed]` — the same signature as an exhausted budget, so check the format in
`.horizon/metadata.json` before reaching for `whoami`.
A new task is **gated to `cipher-omni`** until 10+ rollouts land below a 0.4 pass
rate; `--model biggie-max` returns `403 Forbidden` until then.

**While an evaluation is running, its status table lies.** `horizon evaluations
status` renders every unfinished rollout as `failed` with no score, which is
indistinguishable from twenty genuine failures. The truth is in `status --json`:
`rollouts.errored` counts what actually broke, `rollouts.total` counts what has
finished. g4's first evaluation was cancelled on the strength of that column while
all twenty runs were healthy and mid-flight at 64–237 messages each — $17.03
spent, no refund, and no measurement, against hosted validations that had already
returned oracle 1 / noop 0 on both arms. Use `watch` for progress and `--json` for
a verdict, and budget the wall-clock against a task that already worked: g3's
rollouts finished in about 8 minutes, so a longer ticket still going at 13 minutes
is a long task, not a hung one.

Three commands are not in the recipe because they only make sense as answers to
something a gate printed: `repair` (rewrite what a proof blamed), `replace`
(re-place every remark, same wording), and `suite` / `exec`, which are how the
authoring agents run code and are not meant to be typed by a person.

### What the gates cost when they are missing

Four days of g1 were the clues arm, and almost all of it was defects that no gate
caught. The two worth knowing before you start:

**`prove` used to build once.** The defect it exists to find is stochastic — one
remark said "the string `plan_fingerprint` hashed was `0-2:307;…`", which reads as
the string the function *returns*, and three builds in five implemented it that
way. A single build returned 11 of 11 on that plant, and went on returning 11 of 11
through four hosted versions scoring 0.48 to 0.79. Five local rollouts at half an
hour each eventually found it. Three builds at ninety seconds would have. **Facts
that fail together, on the same runs, are one defect in one remark** — the grid in
`clues/proof.md` is there to make that visible rather than sampled at.

**A gate wired to one command is not a gate.** `unreversed` was reachable only
through `reverse` and `out_of_order` only through `reorder`, so four herrings sat
in a measured corpus never retracted and the plant passed everything it had.
`clues.finish()` is the single tail every pass ends at, and it now runs all of
them — including `unknit`, which reads the invented conversations that until
recently nothing ever opened.

## Running it stage by stage

`cli make <slug>` is the recipe, and it is not how g1, g2 or g3 were actually
built. Every one of them was walked one stage at a time, because **`make` cannot
tell a fatal exit from an advisory one** — `split` and `bracket` both exit
non-zero on a heuristic, and a driver that stops on every non-zero exit stops on
a perfectly good artifact while a driver that ignores them spends $19 into a cut
that was already dead. `make` is for the second pass, when you already know what
this area does; `make --from <stage>` is for resuming after you fixed whatever a
gate printed.

So: this is the walkthrough. Per stage, the command, what it writes, and the one
thing to read before you type the next one. `cli() { python3 task_generator/cli.py "$@"; }`
from the repo root throughout.

### Before anything: the brief

The brief is the one input the package cannot produce, and it is the difference
between a task that brackets and a task that does not (`## Nothing here is
specific to one task`). Read the area first — 15 minutes in `curator/` — and look
for the shape that brackets: **two sides that disagree, where the disagreement is
reachable.** g1 had `create_request_files` and `create_batch_file` disagreeing
about how big a batch is; g2 had three exit paths assembling output independently
and two result types disagreeing about whether a stream may be absent; g3 had a
retry queue, a cooldown and a config each with a different answer for what a
failure costs.

Write it in the shape the existing ones use (`out/*/brief.md`): the area in one
sentence, then `The area, concretely:` with **exact files and line numbers**, then
the disagreement stated plainly, then `Constraints:` — pure, deterministic, no
network, no sleeping, no threads, clock and randomness injected, and the specific
fakes the suite is allowed to build. Twenty-five to forty-five lines. An area
where one implementation is obvious produces parts with no alternatives, and a
fact drawn from such a part is one a blind agent passes for free.

### `cli make <slug> --dry-run`

Free. Prints the stage table with a `spent` column read from this task's own
`spend.json`, so what is left to pay is a subtraction. Run it first and again
whenever you lose the thread.

### 1. `cli new <slug> --brief "$(cat brief.txt)"`

Writes `out/<slug>/brief.md` and a skeleton `task.json`. The id is assigned by
scanning `out/*/task.json` for the next free `g<N>` — pass `--id` only to override
that. Slug `foo-bar` gives suite `g<N>_foo_bar` and harbor dir `g<N>-foo-bar`.

**Read:** that the id and suite are what you expected. Everything downstream keys
off them, and `emit` writes them into `harbor_tasks/`.

### 2. `cli author <slug>` — $5.79

Writes `whole.md`: the whole specification, in parts, nothing hidden yet.

**Read:** that every part names **at least two alternatives a competent engineer
would plausibly pick instead**, and then apply the stricter test the prompt now
carries — *could a competent engineer, with the ticket and the surrounding source,
arrive at this by reading?* If yes it is not hidden, however many alternatives
exist. At least half the parts must carry content the codebase **cannot** supply:
an invented name, a chosen value, a policy with no local evidence, or a deliberate
departure from what the surrounding code plainly does. A `whole.md` that fails
this reads fine and brackets at `naive 10/11`; it is much cheaper to notice here
than after `tests`.

### 3. `cli build --role oracle <slug>` — $3.49

Implements all of `whole.md` in a persistent tree at `.trees/<slug>/oracle/`.
Writes `fixtures/oracle.{patch,py}`.

**Read:** nothing yet. The oracle is judged by the bracket, not by inspection.

### 4. `cli split <slug>` — $1.26 — **gate, and the noisiest one**

Cuts `whole.md` into `ticket.md` (visible half A) and `hidden.md` (B and C), and
writes `task.json` and `fact_sources.json`. The previous cut is archived to
`cuts/cut-N/`, so nothing is lost by re-cutting. It re-cuts itself once, without
being asked, when it detects the ticket leaked a name its own facts need.

**Read:** `tg/leak.py`'s anchor audit, which `cli.py split` prints. It takes the
identifiers each fact quotes, subtracts the ones the ticket prints and the ones
already in the source tree, and reports what is left. It flagged 8 of g1 cut 1's
9 coincidences *before any naive build existed*.

**The exit code is a prediction, not a verdict.** `split` exits 1 when any fact
rests on no invented name. It called 4 of its 5 predictions correctly on g2 — and
g1 ships with 5 of 10 facts unanchored, because a fact can rest on a chosen value
or on a policy the code is silent about instead of on a name. Read the audit, then
decide.

### 5. `cli tests <slug>` — the largest per-call budget here — **gate**

Writes `tests/test_open.py`, `test_r1.py`, `test_r2.py`: one decisive test per
declared fact, green on the oracle. Re-freezes the oracle afterwards if the tree
moved.

**Read:** what each test reaches for, because that is the graded surface and
everything downstream is measured against it, not against the prose. A suite that
reads a path outside the hosted roots will bracket 10/10 locally and score 0
hosted — that is exactly what g3 did, reading `/opt/world-state/input/curator/...`,
which exists in the devbox and in no `apex_arena` image. `harness.baseline_text()`
is the one function allowed to know where a baseline lives, and
`horizon.unhosted_paths()` now refuses a suite that reaches around it — but it
refuses at `horizon`, several hundred dollars downstream of here.

### 6–7. `cli build --role naive` ($1.93) and `--role spec` ($2.00)

Both build in **isolated trees in a system temp directory**, not under this repo,
because the answer key sits in `out/<slug>/` and an agent that wandered into it
would invalidate the one measurement the package exists to make.

`naive` sees only `ticket.md` — the rubric's blind condition, mechanised, for
about a dollar instead of nine. `spec` sees what the `-spec` arm is actually
handed. Do not skip `spec` because the oracle already passes: the oracle builds
from `whole.md` and so shares the author's assumptions. **g3's spec arm capped at
0.44 hosted** because `split` dropped a field spelling the suite still graded, and
nothing local had ever built from the requirement alone to notice.

### 8. `cli bracket <slug>` — free, ~1 min — **the gate**

One suite, four trees, a verdict per fact. Folding is done by
`harbor_tasks/_suites/score.py`, imported rather than reimplemented, so a fact key
here means exactly what it will mean in `jobs/<job>/result.json`.

| verdict | pristine | naive | oracle | what to do |
|---|---|---|---|---|
| `hidden` | fail | fail | pass | ship it |
| `coincidence` | fail | **pass** | pass | `author --extend`, **not** another `split` |
| `vacuous` | **pass** | pass | pass | the test does not require the feature to exist — fix the test |
| `broken` | — | — | **fail** | a real defect. Stop here |
| `unreachable` | fail | fail | pass, **spec fails** | the requirement does not say what the suite grades |

**Two of these are worth stopping for and the rest are not.** `broken` and
`unreachable` are real defects — the second means a build given the ticket *and*
the hidden requirements still fails, so the requirement's wording is wrong, and no
amount of re-cutting will help. A `coincidence`, by contrast, comes off a `naive`
tree built **exactly once**, so one sample of a stochastic process decided it;
`failed_tasks/BRACKET.md` records 14 hidden / 13 coincidence across t1–t4 and
those tasks shipped.

**On coincidences, do not re-cut.** This is the one decision the tool does not
make for you and it cost g2 about $6 to learn: three further `split` calls moved
the anchor count 2 → 4 → 2 and changed nothing, because re-cutting only chooses
*which* parts to hide, and every part was derivable from the surrounding source.
One `cli author <slug> --extend` — which keeps the parts and the oracle and only
adds parts carrying content the codebase cannot supply — took `naive` from 5/10 to
1/10. **A coincidence is a fact about the specification, not about the cut.**

### The paid clue passes checkpoint; run them detached

`plan`, `repair`, `reknit`, `replace`, `reverse` and `reorder` all mutate one
`ledger` in place and write it ONCE, at the end, through `finish()`. That single
tail is deliberate — the first three each grew their own copy of it with a
different hole — but it means an interrupted pass loses every call it has paid
for, and leaves `plant.json` reading exactly as it did before.

So each of them now starts at `clues.resume(task, stamp)`, which picks up
`.{stamp}.partial.json` when an earlier pass was interrupted; `checkpoint()`
writes that file after each item; and `finish()` deletes it once the real artifact
is on disk. A kill costs one call rather than the whole pass.

Launch them **detached**, not merely in the background:

```bash
setsid nohup python3 task_generator/cli.py reknit <slug> > reknit.log 2>&1 < /dev/null &
```

Eleven of g4's eighteen stages run longer than ten minutes, which is where several
harnesses cut a child off. Detaching removes the question; tuning a timeout only
moves it.

### `open_feature` is graded but not gated, and that is where a bad suite hides

`bracket.ships()` looks at the hidden facts. `score.py` computes
`reward = hidden_mean`, and `hidden_mean` **excludes** `open_feature`. So a suite
whose open-feature test is unreachable from the ticket passes every gate in this
package and ships, and the damage only shows up as an uninterpretable headline:
a blind arm scoring 0.00 cannot then be told apart from an agent that built
nothing at all, which is the whole reason the number is reported.

g4 hit exactly this. `open_feature` failed on **both** `naive` and `spec` with one
assertion, `assert None == 3`. Two independently built trees failing the same
assertion is one defect, not variance — and the defect was that `test_open` graded
`RunDirectoryCheck.previous_version` across the four reconcile statuses, which
`whole.md` specifies in full, `ticket.md` mentions only as a name inside a
constructor signature, and the hidden requirements never mention at all. **No arm
stated it.** The oracle passed because the oracle builds from `whole.md`.

This is the same shape that capped g3's spec arm at 0.44 hosted, one level up: not
a hidden requirement the suite grades and the spec does not state, but a *visible*
one the suite grades and the **ticket** does not state. `split` compresses the
specification into the ticket, and compression is lossy exactly where a part has a
lot of small enumerated values.

**`ships()` now refuses on both halves of this**, so it is a gate rather than a
thing to remember. `open_feature` must pass on `naive` — a build given only the
ticket must be able to produce the feature, or the test grades something the
ticket does not state — and it is no longer exempt from the spec-reachability
check, because `spec` is handed the ticket *and* every hidden requirement, so a
key `spec` cannot reach is a key no arm can reach.

Both were measured against every bracket on disk before being trusted, which is
the rule for any new detector here: the g4 cut that shipped green now reads
`ships=False` with both messages, and g1, g2 and g3 are unchanged at `True`. The
healthy shape is `naive: {'failed': 8, 'passed': 1}` with the one pass being
`open_feature` — the agent built the feature from the ticket alone and recovered
none of the hidden requirements. `failed: 9` is not a better result; it is a suite
no blind agent can reach.

The repair is a ticket amendment, not a re-cut: state the missing detail in
`task.json`'s `description` (the field `emit` ships) and in `ticket.md`, snapshot
the previous cut, then assert `hidden_requirements` is byte-identical before and
after so the fix cannot have softened a hidden verdict — and rebuild `naive` and
`spec`, because a tree built from a ticket that no longer exists is not evidence
about the one that ships. Re-running `split` instead would re-roll which facts are
hidden, and on g4 that was a measured 8-of-8 already in hand.

### 9. `cli audit <slug>` — advisory

One adversarial Catalog A/B call per fact. `--optional` in the recipe, never run
on g1. Skipping it is a decision; make it one.

### 10. `cli trim <slug>` — $2.95

Cuts each hidden requirement down to what its assertions actually check. Re-run
`bracket` after, since it changes what the spec arm is handed.

### 11. `cli emit <slug>` — free — **gate**

Writes `harbor_tasks/<id>-<slug>/`, `harbor_tasks/_suites/<suite>/` and this
task's row in `tasks.generated.json`. Refuses unless the bracket shipped, and
`emit.check_bijection` proves every declared fact has a test and every test a
fact.

### Then measure

Locally first — one machine, one model, the instruction the only variable — and
spend hosted rollouts only on what the local bracket cannot answer. A hosted
average multiplies a completion rate by a recovery rate and five rollouts cannot
separate them; the same three arms on Harbor with one model gave 1.00 / 1.00 /
0.00 at n=1 and no ambiguity at all.

**Two numbers are the verdict:** `spec ≈ 1.00` says the suite is satisfiable, and
`blind ≈ 0.00` says the requirements are genuinely hidden. `open_feature` at 1.0
on that blind arm is the load-bearing part of the zero — it means the agent built
the feature competently and still recovered nothing. A blind 0.00 with
`open_feature` at 0 says only that the agent failed to build anything.

And when several facts fail: **perfectly correlated per-fact failures are ONE
defect, not variance.** Three of g1's facts failed together on 3 of 5 rollouts
with byte-identical assertion errors, and the cause was a single ambiguous
sentence. Find it before sampling more, and read the failing assertion's two sides
rather than the fact's name.

## The in-world arm

The `clues` arm quotes all fifty remarks in the ticket. That measures whether an
agent can *use* scattered evidence, and it is the ceiling. The `world` arm is the
real article: the blind ticket, byte for byte, against an image whose chat, wiki and
mail contain those same fifty remarks, in the rooms and on the days the plant chose.

```bash
cli reknit <slug>          # the invented conversations must SAY the remark
cli inject <slug>          # -> a copy of the corpus with the plant written in
python3 data_gen/install_corpus.py --run <run>-<id>
make bake-image TAG=0.4.2  # gated on world-verify
python3 task_generator/build_tasks.py --extra-tasks task_generator/tasks.generated.json \
        --pick g1 --world
cli trial <slug> --arm world
```

Three things about this are worth knowing before you run it.

**`reknit` is the step that makes a plant into a corpus**, and it is where most of
the realism lives. A remark on its own is one person saying a settled thing into a
room; what a reader believes is a team working something out. So the exchange is
written *because* the decision was being taken: somebody raises it, somebody answers
part of it, the first pushes on what is still unclear, and the answer completes it.

Three properties it enforces, each because the version without it read wrong:

- **No turn carries the whole remark.** The first version of this pass forced the
  remark into one message verbatim and guarded it with a substring test. That
  guaranteed the information was present and guaranteed it read as recited. The
  guard is now inverted — a turn containing the whole remark is a finding.
- **Nothing is built yet.** The implementation is the agent's job, so the corpus has
  to read as a decision taken and not yet carried out. Past tense is for the
  problem, never the solution.
- **Every identifier is still typed literally.** Fragmenting a rule is fine;
  fragmenting a name is not, because a rule can be inferred from evidence and a name
  cannot.

Because the remark is now spread over four turns, carriage cannot be checked by
searching for it. A second call is shown the remark and the finished exchange — not
the writer's own account of where it put things — and lists every claim with
present/absent; `carried` is computed from those rows in code. Anything left over
lands on the clue as `uncarried` and `finish()` reports it on every pass.

**The read-back gate decodes.** Mail bodies are quoted-printable and chat is
JSON-escaped, so a substring search over the raw files reports remarks missing from a
corpus that has them.

**BookStack's `/api/search` does not index page comments.** A remark planted as a
comment is reachable only by opening the page — which `/api/pages/{id}` does return,
comments included, and which the instruction points the agent at. `inject` reports
any graded identifier that is typed *only* there, because a name cannot be inferred.

## What the first task measured, and the rule it produced

`g1` was cut twice. Both cuts are on disk (`out/<slug>/cuts/`), because the first
one is the evidence for the second's shape.

| | cut 1 | cut 2 |
|---|---|---|
| oracle | 11/11 | 11/11 |
| pristine | 0/11 | 0/11 |
| naive | **10/11** | 1/11 |
| facts `hidden` | **1 of 10** | **10 of 10** |

The suite was good in both: decisive on an untouched checkout, satisfiable on the
reference. What was wrong was the cut, and two things caused it.

**The ticket printed the answers.** `prompts/split.md` used to say the ticket "must
state the API openly, including exact names and signatures" — which is Catalog A's
*ticket gives it away*, instructed above the rubric that forbids it. Rubric §1's
"exact signatures" constrains **the requirement**, so a grader can check it; not
the ticket.

**And the codebase supplied the rest.** Every part of the specification named two
plausible alternatives, as asked. The alternatives were real — and mostly already
resolved by reading curator. A blind engineer opens `create_batch_file`, sees
`"\n".join(...)`, and writes the separator rule unaided; writes `<=` because it is
natural; copies the existing column check; returns the list they just built.

So the rule that now runs through `prompts/author_whole.md` and `prompts/split.md`
is stricter than "name two alternatives":

> Could a competent engineer, with the ticket and the surrounding source, arrive at
> this by reading? If yes it is not hidden, however many alternatives exist.

And a positive requirement, because refusing bad facts does not produce good ones.
At least half the specification's parts must carry content the codebase **cannot**
supply, of four kinds: **an invented name**, **a chosen value**, **a policy with no
local evidence**, or **a deliberate departure** from what the surrounding code
plainly does. In cut 1 exactly one fact survived and it was the first kind — an
invented exception subclass. Cut 2 was built on all four: a `batch_plan.json`
sidecar with a 12-hex `plan_id` over a specific canonical string, a `512`-batch
cap, a working-directory sweep that contradicts what the code relies on, and a
one-line-per-pass logging policy. Ten for ten.

Two mechanisms carry this rather than trusting a prompt to be read:

- **`tg/leak.py`** — the two Catalog A patterns that are checkable for free. Take
  the identifiers a fact quotes, subtract the ones the ticket prints, subtract the
  ones already in the source tree, and see what is left. It flagged 8 of cut 1's 9
  coincidences *before any naive build existed*, and did not flag the one that
  measured `hidden`. `cli.py split` prints it and exits non-zero.
- **feedback into the re-cut** — `author --extend` and `split` are both handed the
  measured verdicts and the naive diff, told not to declare as hidden anything
  findable in it. `--extend` keeps the specification and the oracle and only adds
  parts, because a re-author throws away work that was not wrong.

The lesson underneath both, recorded in `tasks/lessons.md`: **a pasted rubric loses
to the instruction above it.** Prompts are advice; gates are enforcement.

## Nothing here is specific to one task

`tg/*.py` contains no module name, no fact name and no test name. A task's
substance lives entirely in `out/<slug>/` and the method lives in `prompts/` and
`rubric.md`. Adding task two is `cli new` plus the same nine commands.

The one thing worth tuning per area is the **brief**. `prompts/author_whole.md`
asks the specification to break the feature into parts, and to give every part
*at least two alternatives a competent engineer would plausibly pick instead*.
That requirement is the whole anti-coincidence mechanism: a part with no
alternatives is entailed by the feature, and a fact drawn from it is one a blind
agent passes for free. A brief that points at an area where real design decisions
were made produces good parts; a brief that points at an area with one obvious
implementation produces facts the bracket will reject.

## What is automated, and what is not

Task two (`g2`, executor-output-cap) was built end to end in one afternoon and
measured at **spec 1.00 / blind 0.00**. What it cost, out of its own `spend.json`:

| stage | calls | $ |
|---|---|---|
| tests | 2 | 6.33 |
| split | 7 | 4.47 |
| author-extend | 1 | 3.00 |
| build --role oracle | 2 | 2.11 |
| author | 1 | 2.05 |
| build --role naive | 2 | 1.03 |
| **total** | **15** | **18.99** (65 min of model time) |

Plus two agent trials at roughly $7 each. **~$33 against g1's $88**, and hours
rather than four days.

**Every stage is automated.** Fifteen model calls across ten commands, each
producing a reviewable artifact: the specification, the oracle patch, the cut, the
suite, the naive build, the bracket, the harbor arms, the Horizon arms. Nobody
wrote code, wrote a test, or made a design decision about output capping.

**The judgement between stages is not.** Four things were done by hand, and only
two of them were real work:

1. **Choosing the area** (~15 minutes reading curator). `code_executor` has no
   output cap anywhere, twin result types that disagree about whether a stream may
   be absent, and three exit paths that each assemble output independently. That
   "two sides disagree and the disagreement is reachable" shape is what brackets
   well, and nothing here finds it for you.
2. **Writing the brief** — 25 lines naming exact files and line numbers.
3. **Diagnosing `--extend` rather than another cut** (below).
4. Sequencing, and telling an advisory gate from a fatal one.

Items 1 and 2 are irreducible: they are the taste. Item 3 cost about $6 of the
$19 and should not have.

### The one decision the tool does not make for you

When `bracket` reports coincidences, the instinct is to re-cut — hide different
facts. **That does not work**, and it is worth knowing before you spend on it.

g2's first bracket read `naive 5/10`: four hidden facts reproduced by a build that
only had the ticket. Three further `split` calls moved the anchor count 2 → 4 → 2
and changed nothing, because re-cutting only chooses *which* parts to hide, and
every part was derivable from the surrounding source. One `author --extend` — which
keeps the parts and the oracle and adds parts carrying content the codebase cannot
supply — took it to `naive 1/10`, nine hidden facts and no coincidences.

The rule: **a coincidence is a fact about the specification, not about the cut.**
Re-cut when the ticket LEAKED a name its own facts need — `split` now detects that
itself and re-cuts once without being asked. Extend when the naive build derived
the fact from the code.

### Reading the gates

Two of them exit non-zero on a heuristic rather than a defect, and a driver script
that treats every non-zero exit as fatal will stop on a perfectly good artifact:

- **`split`** exits 1 when any fact rests on no invented name. That is a
  *predictor* of coincidence — it called four of its five predictions correctly on
  g2 — but g1 ships with five of ten facts unanchored, because a fact can rest on a
  chosen value or a policy the code is silent about instead of on a name.
- **`bracket`** builds `naive` exactly ONCE, so a single sample of a stochastic
  process decides every coincidence verdict — the same defect `prove` had before it
  gained `--runs 3`. `failed_tasks/BRACKET.md` records 14 hidden / 13 coincidence
  across t1–t4, and those tasks shipped.

Read both, then measure. **The verdict is `cli.py trial --arm spec` and
`--arm blind`** — an agent, ~25 minutes and ~$7 each. spec ≈ 1.00 says the suite is
satisfiable; blind ≈ 0.00 says the requirements are genuinely hidden. `open_feature`
at 1.0 on the blind arm is the load-bearing part of that zero: it means the agent
built the feature competently and still recovered nothing.

The one bracket result worth stopping for is the **oracle** failing. That is a real
defect rather than a heuristic being pessimistic.

## Auth

Agent turns run on `CLAUDE_CODE_OAUTH_TOKEN`, and `tg/auth.py` **removes**
`ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` from the child environment rather
than merely deprioritising them. The CLI prefers the key when both are set and
says so in one log line nobody reads; every harbor job from `spec-recheck-*`
through `clues-t4-1` carries that line, and `jobs/aborted-spec-t12-1-apikey/` is
the trial that had to be thrown away for it. A missing token is a refusal to
launch, never a fallback.

Never `--bare`: its own help text says auth becomes `ANTHROPIC_API_KEY` only.
Always `--safe-mode`: without it CLAUDE.md discovery walks up from the working
directory and hands the naive agent this repo's description of the
hidden-requirement machinery.

## Where things are

```
out/<slug>/
  brief.md            what the area is
  whole.md            the whole specification, parts and alternatives
  ticket.md           the visible half (A)
  hidden.md           the hidden half (B, C) — what the -spec arm carries
  task.json           id / slug / suite + the tasks.json entry
  fact_sources.json   per fact: which part, and what a blind agent picks instead
  tests/              test_open.py, test_r1.py, test_r2.py
  fixtures/           oracle.{patch,py}, naive.{patch,py}
  bracket.json/.md    the gate
  audit.json/.md      Catalog A/B, per fact
  report.md           the four-condition matrix
  spend.json          every agent call, what it cost
  logs/               every rendered prompt and raw reply
.trees/<slug>/<role>/ persistent working checkouts (gitignored)
```

`logs/<step>.prompt.md` is the exact text the model was given, substitutions
included — a step that came out wrong is diagnosable there rather than by
re-deriving it.

## Rubric conditions 3 and 4 — the clues arm

`cli.py clues <slug>` writes the remarks that hide this task's requirements and
places each one in the finished phase-4 corpus (`tg/clues.py`, `tg/corpus.py`).
`cli.py horizon <slug> --arms clues` then renders those remarks, in date order and
unlabelled, in place of the requirements the `-spec` arm states outright.

**Solvability is measured, not assumed.** `cli.py prove <slug>` gives an agent the
ticket and the remarks — byte for byte what the hosted arm shows, in a tree isolated
the way `naive` is — lets it build, and scores it with the same suite that scores the
paid arm. Two dollars and four minutes, and it hands back the assertion text, so
`plan_id` holding `0-2:307;2-4:307;4-5:153` names the ambiguous remark instead of a
hosted 0.60 saying only that something is wrong. `cli.py repair <slug>` then rewrites
the remarks that proof blames, in place: a re-plant would re-roll the whole tree,
including everything the same proof just showed is working, and placement — which
conversation each remark sits in, and what it answers — is the expensive part.

The loop closed on g1 in three rounds: 7/11, then 10/11, then 11/11. What each round
found is worth knowing, because none of it is visible without measuring:

1. `limit` — the attribute `BatchPlanTooFragmentedError` must carry. No remark said
   it and the implementation called it `limit_batches`.
2. A step nobody said: remarks gave the canonical string and, separately, "twelve
   hex off the front of the sha256", and never that the first is hashed to get the
   second. `plan_id` came out holding the raw string.
3. A remark that contradicted the settled thing. Two remarks had the empty-plan
   fingerprint right; a third, dated later, said the hash is only reached "when
   there's a line to feed it" — and the latest word wins in a reader's head. The
   repair stage now sees every remark in the requirement, not only the ones filed
   under the failing fact, which is the only reason it could find that one.

**The clues must also carry the graded surface, and that is checked before anything
is spent.**
`tg/surface.py` intersects three texts — what a fact's own tests reach for, what
its hidden requirement states, what the ticket already gives away — and separates
what is left into *names* and *values*:

- a **name** cannot be inferred. If no remark says `plan_fingerprint`, the
  attribute the test reads does not exist and the fact scores zero however well the
  corpus is read. The tree stage is given the names per fact, is re-asked once when
  it does not say them, and `horizon --arms clues` refuses to emit an arm whose
  digest is missing one (`--force` to measure it anyway). Names are found by
  POSITION in the test — an attribute, a keyword, a dict key, a `read_field` string
  — never by spelling: `limit` looks like prose and is an identifier, and reading it
  as prose is how a plant shipped without anybody naming it.
- a **value** usually can be inferred — nobody need print `e3b0c44298fc` as long as
  somebody says which string was hashed and how much of the digest was kept — so
  values are reported in `clues/README.md` and never gated on.

This is the whole difference between the first clues arm and the ones after it. The
first cost ten hosted rollouts to discover that its remarks conveyed the idea and
never once typed the word `plan_fingerprint`; every graded run died on
`AttributeError` before any of the reasoning mattered.

**And a name being present is not the same as a decision being made.** On g1's r2
the names were all there, three remarks said the sweep almost outright, and every
hosted run built the ticket and ignored them. The clues arm has never cleared 0.70
against a spec arm that scores 1.00, and it splits in two: a rollout either engages
a requirement and scores 0.80–0.90, or skips it and scores 0.00–0.50. Nothing that
was free could see why, because by the time that mattered every free check was
green — no unsaid name, and by any regex you like, every step had somebody sounding
assertive.

`cli.py settle <slug>` is the check that can. **It decomposes against the tests
rather than the prose**: a requirement's `rule` is a 250-word paragraph and its test
makes seventeen assertions, and the assertions are what is scored, are atomic by
construction, and cost nothing to enumerate. Sixty-nine of them grade g1's two
hidden requirements. Each is put to a judge along with every placed remark in that
requirement — the whole requirement, herrings included and unlabelled, exactly what
a reader meets — under four verdicts:

| | |
|---|---|
| `stated` | somebody says it; the reader puts it in *because they were told to* |
| `implied` | the reader could work it out, and nobody said it |
| `absent` | nothing in the corpus bears on it |
| `not_required` | the assertion checks the suite's own fixture |

`implied` is the finding, and it is the whole point. It is the verdict a remark like

> ya same on my side - an auto run gave me 9 request files and nothing says which
> rows landed in requests_3.jsonl, had to reopen all of them to find one promt

earns: true, in the right room, in the right voice, and it tells nobody to write a
file. Everything else in the package calls it a pass.

What `settle` then writes is the smallest change that makes the claim stated —
preferring a rewrite of a remark that is already placed, because the conversation it
sits in and what it answers is the expensive half, and minting a new remark only
where no rewrite can carry the claim without becoming a specification. Two rules
keep it from flattening the corpus into an answer key: **one claim per remark**, and
**every step keeps one person still complaining**, because someone hitting a problem
and someone else settling it is what makes a record read as a company. Difficulty
comes from dispersion and from the herrings, not from nobody ever committing.

### `reverse` — the herring has to be put down out loud

`clue_herrings.md` forbids any hint that the decision will be revisited, and that is
right: somebody recording a decision does not know it is about to be overturned.
Placement then dates every herring strictly before the earliest real clue. Both
correct, and together they left a corpus where nothing ever said the reversal had
happened — a reader met a confident January remark and a confident May remark that
disagreed, with nothing to say which one won.

The January one usually wins that argument. A herring states a whole shape in one
line — `{"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}` — where the
clues replacing it are spread over five people and three months. The most quotable
remark in the corpus was the wrong one.

`stage_reversals` writes one remark per herring, placed after it, in which somebody
says plainly that the old decision is gone. Three things it must do, and the prompt
names the failure behind each: name the dropped thing in **the earlier remark's own
nouns**, so the two line up for anyone who reads both; say it is dropped **in the
past tense as a fact**, not as a proposal; and say **what replaced it** with the
exact identifiers. A cause when there is one — *"it wiped a working dir when
`plan_request_batches` threw `SingleRequestTooLargeError`"* — is what makes a reader
trust the new decision instead of splitting the difference between the two.

A reversal is neither a leaf nor a herring. It carries facts, so it counts for
`coverage` and takes the same wording checks; it is paired to the herring it answers
by `reverses`, so `unreversed()` can report a herring nothing retracts, or a
retraction dated at or before the thing it retracts — which, to a reader going in
date order, undoes a decision nobody has made yet. `reverses` is in
`clue_digest.WITHHELD`: it names which remark was the wrong one.

`plan()` plants reversals itself. The `reverse` pass exists for plants already
measured, where re-planting to gain a retraction would re-roll every remark that was
already right.
