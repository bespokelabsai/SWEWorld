# g6 — model-price-lookup

Kept here, not only in `tasks/todo.md`: two sessions write that file and the g5/g6
sections were lost once already to a concurrent rewrite. This directory has one writer.

Area: what a token costs. `external_model_cost` returns the input price as both
prices while the table carries a real `output_cost_per_million`; four cost
processors disagree about who owns the 50% batch discount (two cancel it with
`times = 2`); seven places compute the same two per-million numbers with three
different failure contracts.

Chosen against g5's lesson: the graded surface is a **cost number**, so the ticket
can name every symbol and still leave the behaviour unguessable.

Stop point: through `bracket`, then `trim`/`emit`/`horizon --arms blind,spec`. Not `clues`.

## Stages

| # | stage | cost | result |
|---|---|---|---|
| 0 | brief.md | — | verified line by line against the checkout |
| 1 | `cli new` | — | id `g6`, suite `g6_model_price_lookup` |
| 2 | `cli author` | $2.16 | 27 turns, 498s; `whole.md` 42.6KB, parts P1–P9 |
| 3 | `cli build --role oracle` | $3.64 | 43 turns, 573s; 34.9KB patch, P1–P9 green, ruff clean, unittests unchanged |
| 4 | `cli split --model sonnet` | $0.67 | **exit 1, 0 of 8 anchored** → re-cut by hand → **8 of 8** |
| 5 | `cli tests` | $4.52 | 41 turns, 841s, 9 tests; one landmine found and fixed free |
| 6 | `cli build --role naive` | $2.52 | 43 turns, 427s, 705 diff lines |
| 7 | `cli build --role spec` | $3.35 | 41 turns, 602s, 775 diff lines |
| 8 | `cli bracket` | free | **Ships: no** — see below |

Total **$16.86**.

## Step 4 — the hand re-cut (the substantive event)

The paid cut hid P2/P5's *policies* and left every invented name in the ticket, so
`leak.audit` read 0 of 8 — g5's exact signature. But the diagnosis differed: g5 had
no invented names anywhere in `whole.md`; g6 had them and the ticket printed them.
So the cut was bad, not the area.

Re-cut moves the hidden half onto names a blind engineer must invent:
- **r1** = P3's failure contract — the three reason spellings, their fixed precedence
  (provider → model → window), the window normalisation.
- **r2** = P5's `batch_multiplier()` — one owner of the discount, `1.0` for
  klusterai/inference.net (their tables are already batch tiers), `1.0` for a
  user-supplied price.

Two clauses left the ticket: the `REASONS` enumeration and the `None`/`""` → `"*"`
normalisation. **Cost $0** — the oracle implements all of P1–P9, so which parts are
hidden is a property of the cut alone. Previous cut kept at `cuts/cut-2`.

## Step 5 — what the free `test_open` read caught

`test_open` constructed `UnpricedModelError(reason="unknown_model")` and required it
to be **accepted**, while the ticket says only that `REASONS` names "the permitted
reason strings" and that the constructor raises `ValueError` for an unrecognised one.
A naive build spelling it differently would fail `open_feature`, which `ships()`
refuses outright (`tg/bracket.py:173`) — after both paid builds. That is g4's shape.

Fixed free: the reason is drawn from `UnpricedModelError.REASONS`. Verified 9/9 on
the persistent oracle tree via `bracket.measure(task, roles=['oracle'])`.

**The naive build proved this mattered.** It invented `unknown_provider`,
`unknown_model`, `missing_price` and **`unknown_completion_window`** — not
`unknown_window`. The generated test happened to hardcode the one spelling naive
shares, so it would have passed by luck; hardcoding `unknown_window` instead would
have sunk the bracket.

## Step 8 — the bracket: **Ships: yes**

```
pristine {'failed': 8}          naive {'failed': 7, 'passed': 1}
oracle   {'passed': 8}          spec  {'passed': 8}
```

All seven facts `hidden`. `open_feature` passes on naive, oracle and spec and fails on
pristine. Total **$20.88**.

It took four bracket runs. The first said no, with three blockers of three different
kinds; every fix after the spec rebuild was free.

**1. `open_feature` failed on naive** — `test_open` pinned the inferred-price marker
inside the rich markup (`[red]$0.045*[/red]`); naive wrote `[red]$0.045[/red]*`.
`whole.md` P9 states the placement, the ticket does not. Relaxed to accept either;
`rich=False` still pins `"$0.045*"` exactly.

**2. `r1.scope` was a `coincidence`** — it graded the `None`/`""` -> `"*"` window
normalisation, which naive reproduced exactly. Unhideable rather than badly cut: the
ticket must keep curator's existing `external_model_cost(model, completion_window="*",
provider="default")` signature, which hands over the wildcard default. The field was
dropped, which `declared_facts` allows — "a smaller denominator, not a hole". Seven
facts, not eight.

**3. Three spec failures, from two causes.** One was a bad build: `_wrap(model=None)`
raising `TypeError` at `cost.py:303`, and `register_price_with_litellm` returning
`{model: {...}}` instead of the four-key dict. A rebuild ($4.02, 734 lines vs 775)
fixed those. The other two were the suite grading things the requirements do not say:

- `r2.exclusions` — `discount_flag_name()` discovered the class-level flag by name but
  pinned its **polarity**, requiring `True` on the base class. spec wrote
  `_prices_are_batch_rates`, the same statement with the sign reversed. Made
  polarity-agnostic; the fact flipped to pass for $0.
- `r2.rule` — the test asked `_InferenceNetCostProcessor.cost()` to equal
  `completion_cost * batch_multiplier()`. Pricing that class at all needs P7 (the
  override reads its model from the response, the parent gates on `config.model`),
  which no arm but `oracle` is told about, so a correct spec degrades it to `0.0`
  exactly as r1's failure contract instructs. Removed from r2.rule. klusterai stays —
  it is the other provider that cancelled the discount with `times = 2` — and
  inference.net's exemption is still graded by r2.scope and r2.exclusions, which fail
  on naive and pass on spec.

Both of those are the same finding at test granularity that the hand re-cut was at cut
granularity: `ships()` reports "the requirement does not say what the suite grades",
and the cheap thing to change is usually the suite or the cut, not the area.

## Steps 10-12 — trim, emit, horizon

**`trim`** 472 -> 347 words over all 7 facts, 13 assertions dropped, $1.11 (budget
$2.95). Two came off `r2.rule` — the drift expected after inference.net was removed
from its test. **Post-trim bracket: Ships yes, all 7 still `hidden`, spec 8/8.** g4's
trim broke a fact at this step; g6's did not.

It took three passes. `error_max_structured_output_retries` killed the run on
`r1.observability`, then on `r2.exclusions_or_crossover` — a different fact each time,
so not a transient. Only the per-prompt disk cache made resuming cheap instead of a
$2.95 redo per attempt. `split` has a `--model` escape hatch for this exact class of
failure (opus + `--json-schema` failing 6/6 with `[reasoning_extraction]`); `trim` has
only `--budget`, `--dry-run` and `--rerun`. Worth giving it the same flag.

**`emit`** wrote `harbor_tasks/g6-model-price-lookup/`,
`harbor_tasks/_suites/g6_model_price_lookup/`, and the row in `tasks.generated.json`,
now `['g1','g2','g3','g4','g6']` — g5 correctly absent.

**`horizon --arms blind,spec`** wrote both apex task directories under
`out/model-price-lookup/horizon/`. Both emit gates passed: `unhosted_paths()` and
`unsolvable()`.

## Final

**$21.99.** g5 spent $17.92 to learn it could never ship; g4 cost $44.70 all-in.
Every blocker after the one spec rebuild ($4.02) was free to fix.

## Step 13 — pushed to Horizon

Both arms are live in the **nidhi-test** project, mini-batch
`b52ead5c-6e16-4552-ab96-250541fdfba2` — the same batch g1-g4's apex arms went to.
The server confirmed the project name on push; the CLI cannot resolve a batch name to
a project beforehand, so this was inferred from local metadata and verified after.

| arm | task id | version |
|---|---|---|
| `g6-model-price-lookup` (blind) | `6ff92bf3-3a22-4c72-a89f-2459b57061e7` | 1 |
| `g6-model-price-lookup-spec` | `a745885a-847e-42a4-a583-aa6f6752656d` | 1 |

**`horizon tasks push` still prompts for the task name even with `MINI_BATCH_ID`
exported**, so it dies with `EOF when reading a line` in a non-interactive shell. The
README's recipe does not mention this. Pipe the name in:

```bash
printf 'g6-model-price-lookup\n\n\n' | horizon tasks push g6-model-price-lookup
```

Also worth knowing: `horizon tasks list` returns `Error fetching tasks: 0`, and there
is no CLI command that lists mini-batches — the docs say to read the id off the web
UI's My Work tab. Local `.horizon/metadata.json` files are the only on-box record of
which batch is which. The two in use here:

- `b52ead5c-6e16-4552-ab96-250541fdfba2` — apex blind/spec/clues arms → **nidhi-test**
- `fde8a4a1-21d7-4f76-b153-6cfe480b82ff` — harbor world arms (g1, g2) → **sweworld**

**Hosted validation: all four PASSED.**

| arm | oracle | noop |
|---|---|---|
| `g6-model-price-lookup` (blind) | **1.00** | **0.00** |
| `g6-model-price-lookup-spec` | **1.00** | **0.00** |

`validate` is asynchronous — it triggers a build and returns immediately; results come
back through `horizon tasks validate-logs -a <agent>`, which reports
`Validation status: running` until done. Trigger all four, then poll.

## Step 15 — evaluation submitted

**Evaluation `9eb67aaa-6390-40bc-b715-26cd93eb7b21`** — cipher-omni, agent-type meteor,
3 runs x 2 tasks = 6 runs, machine `e2-custom-8-16384` (8 vCPU / 16 GB).
cipher first, as the gate; biggie-max after, if this clears.

**`--machine-type` accepts exactly four values and the CLI documents none of them.**
The rejection names the set:

```
e2-custom-2-4096   e2-custom-4-8192   e2-custom-8-16384   e2-custom-16-32768
```

`e2-custom-8-16384` is the 8-CPU one. Anything else (`e2-standard-8`) is a 400 with a
ZodError listing the valid options.

**Multiple task ids go in one comma-separated positional**, not as repeated arguments:
`submit ... <uuid>,<uuid>`. Space-separated gives `Got unexpected extra argument`.

Config confirmed from g4's rollouts rather than guessed: cipher-omni ran under
`agent_type: meteor`, biggie-max under `typhoon`.

### Reading the result

`tasks/lessons.md` records a cancel on g4 that destroyed ~$40 of in-flight work because
the per-run status column has no state for "in progress" that differs from failure.
Read `rollouts.errored` and `rollouts.total`. Read final scores with
`horizon rollouts pull <task-id>`, never `evaluations status`.

cipher-omni scored 0 on every g4 run and that was concluded to be a model wall, not a
task defect — g4's oracle patch was 1007 lines, 2.2x g1. **g6's is 735 lines**, so it is
a smaller build than the one cipher could not finish.

## Step 15 result — every rollout errored; the account budget is exhausted

Three evals, nine rollouts, **all errored, $0.00 spent, 0 model requests**:

| eval | model | agent | machine | result |
|---|---|---|---|---|
| `9eb67aaa-…` | cipher-omni | meteor | `e2-custom-8-16384` | 6/6 errored |
| `6be57096-…` | cipher-omni | meteor | *omitted* | 1/1 errored |
| `1feb4115-…` | cipher-omni | typhoon | *omitted* | 1/1 errored |

Every transcript: 4066 bytes, one `[user]` section, **zero assistant turns**. The grader
ran and correctly scored an untouched tree 0 of 7 — the same as `pristine` locally.

**Cause: `horizon whoami --json` reports `budget: 0.0` against `total_spend: 1040.18`.**
It is the only explanation consistent with all of:
- 0 requests and $0.00 on every rollout — they never reach the model
- identical failure across meteor AND typhoon (agent type is irrelevant to a budget block)
- identical failure with and without `--machine-type`
- hosted validation passing 1.00/0.00 — it runs `solution.sh` and noop deterministically
  and consumes no model budget, so the task looks healthy because it IS healthy
- g4's cipher-omni runs having worked earlier, before the budget ran out

**Confirmed by control:** one cipher-omni run submitted against **g4's** task
(`0919a0fe-…`), which had previously produced 27 working rollouts, errored 1/1 with
$0.00 and 0 requests — identical to g6. The failure is account-wide. g6 is exonerated.

`submit` accepts the job; the rejection happens per-rollout and surfaces **no**
`error_message`, no `rollout_error_insights`, and `steps: evaluate failed`. Nothing in
the API says "budget". **Check `whoami` first when rollouts error with zero spend.**

Two hypotheses were tested and are WRONG, recorded so they are not re-tried:
- `--machine-type e2-custom-8-16384` — control A omitted it and failed identically.
- A 46-byte `workdir.tar.gz` in the artifacts is NOT evidence `/workdir` was empty; a
  snapshot of an agent that never ran is empty either way.

**The model gate is real**, and it is what "use cipher first" means:
```
403 Forbidden: This task is gated to cipher-omni (GLM 5.2) or cheaper:
run 10+ cipher-omni rollouts below a 0.4 pass rate to unlock pricier models.
```
So biggie-max cannot be used as a control, and the 10 unlocking rollouts cannot run
without budget either.

**`horizon whoami --json` prints the account API key in plaintext.** Do not paste it.

## Step 16 — measured LOCALLY instead

Horizon budget is exhausted, so the hosted measurement is blocked indefinitely. The
local trial is not: `harbor_tasks/_loop/run.sh` unsets `ANTHROPIC_API_KEY` and
`ANTHROPIC_AUTH_TOKEN` and exports `CLAUDE_FORCE_OAUTH=1`, so agent turns bill the
Claude subscription rather than Horizon.

```bash
python3 harbor_tasks/build_tasks.py \
    --extra-tasks task_generator/tasks.generated.json --pick g6   # free
python3 task_generator/cli.py trial model-price-lookup --arm blind   # ~$7, ~25 min
python3 task_generator/cli.py trial model-price-lookup --arm spec    # the ceiling
python3 task_generator/cli.py report model-price-lookup              # -> report.md
```

`build_tasks.py` wrote `model-price-lookup` and `model-price-lookup-spec` under
`harbor_tasks/g6-model-price-lookup/`. No clues arm — `cli clues` was never run, which
is the deliberate scope decision, not a failure.

This is the same suite and the same per-fact reward keys as the hosted arms, so it
answers the question the task exists to ask — does the cut discriminate blind vs spec.
What it cannot answer is how cipher-omni specifically does, which is what the hosted
gate wants.

### Blind arm result — a real defect, found by the trial and not by the bracket

`blind-g6-1`, claude-opus-5, **$13.56** (README says ~$7), 28 min. The agent worked
properly: `provenance.pushed`, `ci_green`, `deployed` all 1.0, `suite_ok` 1.0.

**Every hidden fact scored 0.0 — the cut discriminates exactly as designed.** The agent
invented its own reason vocabulary (`incomplete_…`, `unknown_model`, not the three) and
shipped no `batch_multiplier` at all.

**But `g6.open_feature` also scored 0.0, and that is a task defect.** One assertion:

```
> assert set(entry) == {"max_tokens", "input_cost_per_token", "output_cost_per_token", "litellm_provider"}
E AssertionError: assert {'meta-llama/…Instruct-FP8'} == {'input_cost_…st_per_token'}
```

The agent's `register_price_with_litellm` returned `{model_name: {…}}` rather than the
flat four-key dict — **the same thing the first `spec` build did.** Two independent
agents, same reading. The ticket says:

> `register_price_with_litellm(price: ModelPrice) -> dict` that **writes**
> `{"max_tokens": …, …}` into `litellm.model_cost` via `litellm.register_model`

It specifies what is *written* and never what is *returned*, and `register_model` takes
`{model_name: {…}}` — so returning that is the natural reading. `naive` happened to
guess the flat dict, which is the only reason the local bracket passed `open_feature`
and this did not.

This is precisely what `ships()` refuses on: an open feature a build given only the
ticket cannot reliably produce. The bracket could not see it because it had one
sample of blind behaviour; the trial is a second, and it disagreed.

**Fix (free, no rebuild):** disambiguate the ticket — say the function returns the
entry it wrote — or relax the assertion to accept either shape. Then re-run `bracket`
(free) to confirm nothing else moved. The hidden half needs no change.

### Spec arm result — and the verdict

`spec-g6-1`, claude-opus-5, **$11.79**. Every metric **1.0**: all seven hidden facts,
`open_feature`, `hidden_mean`, `reward`. pushed / ci_green / deployed all 1.0.

## VERDICT: spec 1.00 / blind 0.00

| condition | how | got |
|---|---|---|
| 1 · blind (free bracket) | `naive` reference build | 0 coincidences |
| 2 · full spec (free bracket) | `oracle` reference build | 0 broken |
| **2 · full spec (paid)** | harbor `spec-g6-1` | **1.0000** |
| **1 · blind (paid)** | harbor `blind-g6-1` | **0.0000** |
| 3 · ticket + clues | needs a phase-3 plant | out of scope |
| 4 · clues only | needs a phase-3 plant | out of scope |

Per fact, every one of the seven: **spec 1.0, blind 0.0.** Maximum separation. The
hidden requirements are both unguessable from the ticket and fully implementable from
the requirement text — which is the whole claim a hidden-requirement task makes, and
the thing g5 never achieved (7 of 8 `coincidence`).

**Total: $47.34** — authoring $21.99, blind $13.56, spec $11.79. g4 was $44.70.

### The one caveat, and it is worth fixing

g4's verdict line reads "spec 1.00 / blind 0.00, **open_feature 1.0 on both**". g6 has
`open_feature` 1.0 on spec and **0.0 on blind**, on a single assertion:

```
> assert set(entry) == {"max_tokens", "input_cost_per_token", "output_cost_per_token", "litellm_provider"}
E AssertionError: assert {'meta-llama/…Instruct-FP8'} == {'input_cost_…st_per_token'}
```

The ticket says what `register_price_with_litellm` **writes** into `litellm.model_cost`
and never what it **returns**, and `litellm.register_model` takes `{model_name: {…}}` —
so returning that is a natural reading. Observed across five independent builds it is
roughly a coin flip: `naive` and both `spec` builds and the spec trial returned the flat
dict; the first `spec` build and the blind trial returned `{model: {…}}`.

It does not change the headline — blind scores 0.0 on every hidden fact regardless —
but it means part of the blind arm's zero is measuring an ambiguity rather than the
hidden requirements, and `ships()` exists to refuse exactly that. **Fix it before the
hosted rollouts**, since it is free and no paid stage repeats.

### Caveat fixed this session

Added one clause to the ticket, in both `task.json`'s `description` field and
`ticket.md` (hand-edited in both — `tg/steps.py` only renders one into the other
during the paid `author` step, which did not re-run):

> `register_price_with_litellm` returns that same four-key `{"max_tokens": ...,
> "input_cost_per_token": ..., "output_cost_per_token": ..., "litellm_provider":
> ...}` dict — the entry it just wrote, not `{price.model: {...}}`.

Matches the return shape `whole.md:365` already specified internally — that file
is never shown to agents, so the ambiguity was real, not a bracket bug.

Re-ran the free chain: `cli bracket model-price-lookup` (still **Ships: yes**, all
7 hidden facts unchanged, `open_feature` pass/pass/pass/pass — untouched, since the
clause doesn't move `tests/test_open.py`), `cli emit model-price-lookup`,
`harbor_tasks/build_tasks.py --extra-tasks tasks.generated.json --pick g6` (confirmed
the clause landed in both `instruction.md` files), `cli horizon model-price-lookup
--arms blind,spec` (confirmed `.horizon/metadata.json` was preserved — same task ids,
same mini-batch). No `--force` was needed on either `emit` or `horizon`.

Re-pushed both arms: `horizon tasks push g6-model-price-lookup` and
`g6-model-price-lookup-spec` — both landed as **version 2** of the existing tasks
(`6ff92bf3-3a22-4c72-a89f-2459b57061e7` / `a745885a-847e-42a4-a583-aa6f6752656d`,
project `nidhi-test`, mini-batch `b52ead5c-6e16-4552-ab96-250541fdfba2`), not new
tasks. No paid stage repeated.

### Tooling fixed this session

`tg/report.py` — `trial.rewards()` returns one dict PER TRIAL (a list even at
`n_trials == 1`); two sites called `.get` on it and raised `AttributeError: 'list'
object has no attribute 'get'`, killing `report` **after both paid arms had run**.
Folded once at the seam (`_fold`) rather than patched at each read site, so `--runs 3`
now means the arm reports its mean.

## Step 17 — cipher-omni evaluation resubmitted (2026-09-03)

Horizon budget confirmed restored: `horizon whoami --json` → `budget: 400.0` (was
`0.0` in Step 15). Resubmitted the same command Step 15 used, against the version-2
task ids:

```bash
horizon evaluations submit --model cipher-omni --runs 3 --agent-type typhoon \
  --machine-type e2-custom-8-16384 \
  6ff92bf3-3a22-4c72-a89f-2459b57061e7,a745885a-847e-42a4-a583-aa6f6752656d
```

**Evaluation ID: `1a8f685c-17e9-4466-a2ca-472080e191b2`** — 2 tasks × 3 runs = 6 total
rollouts, Cloud Batch backend. Immediately after submit, status is `running` with
`rollouts.errored: 0` (Step 15's failure showed as errors from the first poll, so a
clean start here is a good sign the budget fix actually took). Check with:
```bash
horizon evaluations status 1a8f685c-17e9-4466-a2ca-472080e191b2 --json
```
Read `rollouts.errored`/`rollouts.total`, not the per-run status column (see Step 15's
note — that misreading cost ~$40 on g4). Pull scores with `horizon rollouts pull` once
`rollouts.total` reaches 6.

## Step 17 — return contract fixed, ticket made readable, pushed as v3

**Return contract.** The ticket now says `register_price_with_litellm` "returns that
same four-key … dict — the entry it just wrote, not `{price.model: {...}}`". That was
the ambiguity the blind trial exposed: five independent builds split roughly evenly on
which dict to return.

**Ticket reformatted** from one 3271-character sentence into structured markdown — a
`### ` section per thing to add or change, specifics as bullets. 3426 chars.
Pre-reformat text kept at `cuts/ticket-before-reformat.md`.

Verified before applying, because the ticket is graded material:

| check | result |
|---|---|
| backticked spans | **60 before, 60 after, 0 dropped** |
| `leak.audit` | **7 of 7 anchored** |
| `cli bracket` | **Ships: yes**, all 7 `hidden` — identical to before |
| hosted validation v3 | **oracle 1.00 / noop 0.00 on BOTH arms** |

Both arms pushed as **version 3** in nidhi-test, label "readable ticket".
Horizon budget restored: **$361.67**.

## Formatting is now automatic in task_generator

The cause was `prompts/split.md`: `description` was specified as "One paragraph".

- **`prompts/split.md`** — now asks for structured markdown and names the failure.
- **`tg/steps.py`** — `unstructured()` folded into the re-cut loop `split` ALREADY runs
  for `leak.audit`. Same retry, same feedback channel, no new stage, no extra call
  unless the first cut ignores the instruction.
- **`cli.py`** — `cmd_split` reports it and gates on it beside the leak table.

Chosen over a post-hoc LLM reformat pass deliberately: `test_open` grades what the
ticket STATES, so a rewriting pass can silently drop a clause and make a fact no blind
build can reach. Asking for the shape at the cut adds no call and creates no
transformation that can lose anything. Prompting alone is not enough — lesson 5, prompts
are advice where gates are enforcement — hence the loop.

Discriminates on real data: passes reformatted g6, flags g1–g5.

## Next, when wanted

**Either of two, and they differ by ~$48:**

1. **Hosted evaluation** — budget is back, arms are v3, validation is green:
   ```bash
   horizon evaluations submit --model cipher-omni --runs 3 --agent-type typhoon \
     --machine-type e2-custom-8-16384 \
     6ff92bf3-3a22-4c72-a89f-2459b57061e7,a745885a-847e-42a4-a583-aa6f6752656d
   ```
   Read `rollouts.errored`/`rollouts.total`, never the per-run status column. Scores via
   `horizon rollouts pull <task-id>`. biggie-max stays 403-gated until 10+ cipher
   rollouts land below a 0.4 pass rate.

2. **`clues`** — the phase-3 plant, **$48**, two-thirds of a task's whole bill and ~175
   placement calls. Then `settle` / `reverse` / `reorder` / `reknit` / `prove`, and
   `inject` for the in-world arm. Every prior note parked this deliberately.

Still open: give `trim` the `--model` flag `split` has — it died three times on
`error_max_structured_output_retries`, a different fact each run.
