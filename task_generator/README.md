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
| `bracket` | **yes** | free | pristine / naive / oracle → a verdict per fact. Every fact must read `hidden` |
| `audit` | **yes** | ? | one adversarial Catalog A/B call per fact. **Never run on g1** — `--optional` |
| `trim` | | $2.95 | cut each requirement to what its assertions actually check |
| `emit` | **yes** | free | write the harbor artifacts; refuses unless the bracket shipped |
| `clues` | **yes** | $48 | the plant. ~175 placement calls, and **two thirds of the whole bill** |
| `settle` | | $10.73 | rewrite every graded assertion a reader was left to infer |
| `reverse` | **yes** | $1 | say out loud that each herring's decision was dropped |
| `reknit` | **yes** | $2.50 | make each invented conversation say the remark as the plant now words it |
| `reorder` | **yes** | $1 | move a decision dated before the complaint it answers. `--optional` |
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
python3 harbor_tasks/build_tasks.py \
    --extra-tasks task_generator/tasks.generated.json --pick g1 [--world]
```

`--extra-tasks` is the only change this package makes outside its own directory.
It exists because ids in `data_gen/input/tasks.json` are **positional** (`t1`…`t60`)
and `SLUGS`/`SUITE_DIR` are hardcoded index dicts, so a generated task has to
carry its own id, slug and suite. The hand-written 60 are never touched.
`--world` adds a fourth arm that boots the populated image, where the remarks are
in the corpus rather than in the ticket; it needs `cli inject` to have run and the
image to have been re-baked.

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
python3 harbor_tasks/build_tasks.py --extra-tasks task_generator/tasks.generated.json \
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
