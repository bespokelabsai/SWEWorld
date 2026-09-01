# Overnight loop — results

Run 2026-08-27. Every trial: Claude Opus 5 on
`CLAUDE_CODE_OAUTH_TOKEN`, through the real world — clone, push, CI, deploy.
Every score below comes from a trial that pushed and deployed green.

## The headline

| task | spec | blind | hidden facts | coincidences | discriminates |
|---|---|---|---|---|---|
| t1 `cache-stats` | 0.778–0.889 | 0.5556 | 4 | 5 | **yes** |
| t2 `batch-cost-estimate` | 1.0 | 0.6 | 2 | 2 | **yes** |
| t3 `shared-limiter` | 1.0 | 0.1429 | 6 | 1 | **yes** |
| t4 `deepseek-empty-retry` | 1.0 | 0.667 | 2 | 4 | **yes** |

`spec` = both hidden requirements written into the ticket. `blind` = the
ticket alone. A fact is **hidden** when the blind agent fails it and the
spec agent passes; a **coincidence** when the blind agent passes it
anyway, which means no corpus could ever make it discriminate.

## What the loop actually did

The premise was yours: an agent handed the requirement verbatim must
pass, and if it does not, the validation is wrong rather than the agent.
That held up. **Twenty-two grading bugs** were found this way, every one
failing an implementation that did follow the requirement.

Three of the four tasks now reach a **full pass** on spec.

t1 is the exception, and its result is worth stating precisely rather than as a
number. Across five runs on the corrected tests **every one of its ten tests
passed at least once**, and eight passed in every run. So no test is
unsatisfiable — the two that vary (`r1.exclusions` 2/5, `r1.failure_behavior`
1/5) are the two that require editing code paths the agent did not write:
curator's run-level fingerprint, and its per-row miss accounting. No single run
landed both. Best score 0.889.

That is a stronger claim than "t1 scores 0.889", and it is the one the evidence
supports: the suite is achievable, and what remains is agent variance on two
hard facts rather than a grading defect.

| | attempts to reach a sound suite |
|---|---|
| t1 | - |
| t2 | 1 |
| t3 | 5 |
| t4 | 1 |

## The bugs, by kind

**Grading a second mechanism the requirement never names.** t1's cache
tests demanded curator's run-level fingerprint change; the requirement
describes a prompt-level key and nothing else. Three facts, three runs.

**Picking one reading of an ambiguous sentence.** t1's ticket asks
`cache_stats()` to report "the last run's requests ... so users can gauge
how much a re-run will cost" — a retrospective number and a prospective
one, in a single sentence. The tests assumed the first; an agent built the
second. Now graded only where the two agree.

**Encoding a design decision the ticket leaves open.** t3's suite required
the limiter to be *extractable from a block*. The ticket says "passing an
existing rate limiter instance", so a class the caller constructs is the
plainest reading — and what every agent built. Two runs scored 0.14 for it.

**Assuming a value's type.** t3's `remaining_budget()` returned a
`RateLimitBudget` dataclass carrying requests and tokens. The test wanted a
builtin and read it as "not a number". The requirement names the accessor,
not its return type.

**Requiring a channel the ticket does not fix.** t3's blind agent passed
its limiter as an `LLM(...)` argument rather than through `backend_params`.
`backend_params` is named only in a *hidden* fact, so the blind agent could
not have known — and the open feature failed for it.

**Testing a scenario the requirement does not describe.** t3's
`r2.failure_behavior` built a budget too small for one request. The
requirement is about a *second invocation against an un-reset limiter*.

## Two findings that belong in `tasks.json`, not the tests

### t4's requirements largely describe code that already existed

t4 discriminates on **two** of six facts, and the other four are unreachable by
any grader — not because the tests are weak but because untouched curator
already satisfies them. `openai_online_request_processor.py:92` ships with:

```python
if "api.deepseek.com" in self.url:
    self.api_key = self.config.api_key or os.getenv("DEEPSEEK_API_KEY")
    self._longlived_response = True
```

That is `r2.rule` ("detection inferred from base_url alone"), `r2.scope`
("backend-internal only") and `r1.scope` ("only when base_url points at
DeepSeek") — all three already true before the agent starts. A blind agent
added one line inside that pre-existing branch and satisfied every one.
`r1.rule` is a genuine coincidence: retrying an empty completion is the ticket.

**This section originally read "t4 measures nothing", on a blind score of 1.0.**
That was wrong, and the way it was wrong is the most useful lesson here — see
below.

### Two requirement pairs contradict themselves

`t3.r2.rule` says the limiter must be reset between invocations;
`t3.r2.failure_behavior` says what must happen *if it is not*. An
implementation satisfying the first can never reach the second — the
oracle proved it by simply succeeding. Recorded as unmeasured rather than
failed. A t2 pair has the same shape.

## The bracket is not enough

Every task was gated on oracle-passes / naive-discriminates / pristine-fails
before each re-run. t4 was green on all three throughout — and three of its
tests still did not check what the requirement said:

- `r1.failure_behavior` asked for an error naming "DeepSeek **and
  empty-response retries**". The test checked only the first half, and matched
  `deepseek` anywhere — including the endpoint URL `api.deepseek.com`. One
  blind submission passed on `"Response is empty: the API returned a completion
  with no content"`, which names neither.
- `r2.exclusions` and `r2.scope` rejected only *suspiciously named* additions
  (`is_deepseek`, `empty`). A field called `provider_quirks` would have passed
  while breaking the same contract.
- t2's `r1.exclusions` scanned source for a litellm carve-out and passed on
  `import litellm; from litellm import model_cost` — litellm imported for its
  pricing table by an implementation that never considered the exclusion.

All three fixtures in the bracket are ones I wrote, so none of them can catch a
test that grades the wrong thing. **Only reading real submissions against the
requirement found these.** Tightening the first two moved t4's blind score from
1.0 to 0.667; the third was reverted to unmeasured, because a passing grade
that means nothing is worse than no grade at all.

That check — for every fact the blind arm PASSES, read the submission and
confirm it genuinely satisfies the requirement — belongs in the loop from the
start, not as an afterthought.

## Why a fact ends up unmeasurable — five patterns

Every one of these came from a real case in this run, not from theory. They are
worth checking against a requirement **before** phase 3 spends clue budget on
it, because none of them can be fixed by writing a better test.

### 1. The state the fact describes is unreachable

`t2.r1.exclusions` — *"litellm-backed models must show the standard estimate
even when batch=True"*. `_RequestProcessorFactory.create` raises `"Batch mode is
not supported with LiteLLM backend"`, so **no litellm batch run exists**. An
implementation that carefully excludes litellm and one that never heard of it
produce identical behaviour: nothing happens either way.

*Tell:* the requirement names a combination of features the codebase refuses to
put together.

### 2. The fact contradicts a sibling fact

`t3.r2.failure_behavior` — *"**if the limiter is not reset** and a second
invocation starts while budget already appears exhausted, it must raise"*. Its
sibling `t3.r2.rule` says the limiter **must** be reset between invocations. An
implementation satisfying the rule never reaches the failure branch — the
oracle proved it by simply succeeding (`DID NOT RAISE`).

*Tell:* one field's precondition is the negation of what another field requires.

### 3. The behaviour has no consequence

`t2.r2.failure_behavior` — *"if `prompt()` raises on a sampled row, skip it
silently rather than aborting the pre-flight"*. curator renders every row into
request files regardless of the estimator, so a row that cannot render kills
the run either way. Skipping it changes nothing anyone can see.

*Tell:* the requirement asks for graceful handling of something that is fatal
one layer down.

### 4. The only observable belongs to a different fact

`t2.r2.rule` — *"the estimate must be computed from a sample of the first N
rows"*. Counting `prompt()` calls cannot separate the estimator's traversal
from the run's own, so the sole channel is the estimate **saying** it sampled —
which is `t2.r2.observability`, a different field. Grading `rule` through it
scores one observable twice under two names, and fails an implementation that
samples silently.

*Tell:* to test field A you have to require field B.

### 5. The fact has no independent content

`t4.r2.scope` — *"Backend-internal detection only."* The available test
(no new public parameter) is already `t4.r2.exclusions`, and the sentence
itself restates the second half of `t4.r2.rule`. There is nothing left for it
to grade that a sibling does not already cover.

*Tell:* you cannot state what would distinguish satisfying this field from
satisfying its neighbours.

### 6. The claim is unbounded in time

*"must raise a clear error rather than **silently stalling forever**"*
(`t3.r2.failure_behavior`). "Forever" is not observable; a test can only watch
a finite window and call a timeout a stall. That is a proxy, and it is a
flaky one — a slow host turns a correct implementation into a "stall". Any
requirement phrased with *never*, *forever*, or *always* has this problem, and
the fix is to state the bound the test will actually use.

### 7. The observable needs an environment the harness cannot build

`t3.r2.rule` says the limiter tracks budgets **per-process**. Testing that
honestly means a second interpreter, and a suite that runs everything in one
process can only pretend. Same shape as any fact about restart behaviour,
signal handling, or concurrency across workers.

### 8. The fake defines the very thing being graded

t4's requirements are about how DeepSeek behaves under load. The suite's
provider returns an empty completion **because the test told it to**, so it can
confirm the agent's reaction but never that the trigger is real. Harmless here
— the reaction is the requirement — but a fact phrased as *"must handle the
case where the provider does X"* is only as true as the fixture, and a fact
about *how often* or *under what conditions* X happens is not gradeable at all.

### The anti-pattern: "I could not think of a test"

`t1.r1.failure_behavior` was recorded as unmeasurable and **was not**. curator
calls `model_json_schema()` both to hash a `response_format` and to build the
request, so patching it out of one place leaves the row failing permanently —
which looks like proof that no implementation can both skip the cache and serve
the row. It can: drop the format for the whole run so request and parse agree,
and separately remember it was dropped so the key stays unique. Two halves,
neither obvious.

**"Unmeasurable" has to mean "no oracle exists", not "I did not find one".**
The way to tell them apart is to write the oracle and watch it pass.

### A near neighbour: measurable but never discriminating

`t4.r2.rule`, `t4.r2.scope` and `t4.r1.scope` are all testable — the tests pass.
They just pass for **everyone**, because curator already ships
`if "api.deepseek.com" in self.url` at
`openai_online_request_processor.py:92`. The fact describes code that existed
before the task began. That is a coincidence rather than an unmeasurable, but
it is equally useless as a hidden requirement, and it has the same cure:
rewrite the requirement, not the test.

## Why a fact ends up a coincidence — six patterns

A coincidence is a fact the blind agent passes anyway. It is not a broken test
— the test measures correctly, it just always says yes. **This is the bigger
problem in these four tasks: 15 coincidences against 5 unmeasurables.** No
corpus, no re-plant and no phase-4 work changes any of them, because the agent
never needed the information.

### 1. The codebase already does it

`t4.r2.rule`, `t4.r2.scope`, `t4.r1.scope` — *"detection inferred from base_url
alone"*, *"backend-internal only"*, *"only when base_url points at DeepSeek"*.
curator ships `if "api.deepseek.com" in self.url` at
`openai_online_request_processor.py:92`. An agent adding one line inside that
branch satisfies all three without knowing they exist.

*Check before planting:* grep the baseline for the behaviour. If it is there,
the fact is dead on arrival.

### 2. A prohibition satisfied by doing nothing

`t2.r1.scope` (*"does not change actual billing"*), `t3.r1.exclusions`
(*"without a shared limiter each block keeps its own"*), `t4.r2.exclusions`
(*"must not add a public knob"*). Untouched code satisfies every one of them.
This suite guards them with `require_feature`, which at least stops crediting
an agent who wrote nothing — but the fact still cannot distinguish an agent who
**knew** the constraint from one who never had the chance to violate it.

*Check:* prefer positive obligations. AlphaShop's graders reached the same rule
independently: a prohibition is satisfied by inaction, and inaction is what an
agent most often does.

### 3. The model already knows it

`t2.r1.rule` — *"50% off standard per-token pricing for OpenAI and Anthropic
batch"*. That is published pricing. The blind agent wrote `* 0.5` on both input
and output cost with nobody telling it to.

*Check:* if the fact is a documented industry convention, planting it teaches
the agent nothing it did not have.

### 4. The ticket gives it away

t4's ticket is *"DeepSeek empty-response retry handling"*. Scoping the retry to
DeepSeek and naming DeepSeek in the error are what that sentence already says.
The hidden requirement restates its own ticket.

*Check:* read the ticket and the fact together. If the fact sounds like a
paraphrase, it is one.

### 5. Entailed by the open feature

`t1.r2.rule` and `t1.r2.observability` — *"read from the same on-disk cache
directory"*, *"report the resolved cache directory"*. You cannot write
`cache_stats()` at all without reading the cache directory, and having found it
you naturally report it. The fact is a consequence of building the feature, not
an extra constraint on it.

*Check:* ask whether a competent implementation of the OPEN feature could
plausibly violate this. If not, it is not a requirement.

### 6. The obvious implementation happens to do it

`t1.r1.rule` and `t1.r1.scope` after they were narrowed to grade only their own
stated text: curator's fingerprint already covers model, generation params and
schema, and its run-level cache already serves a repeated dataset on the batch
path. Not entailed, not pre-existing in spirit — just the path of least
resistance.

*Check:* write the naive fixture FIRST, before planting. That is a 30-second
run, and it answers "would an agent do this anyway?" better than any amount of
argument.

### The relationship between the two lists

Unmeasurable and coincidence are not the same failure and do not have the same
cure. **Unmeasurable** means no test can tell two implementations apart, so the
fact scores nothing and is dropped from the mean. **Coincidence** means the
test works fine and always passes, so the fact quietly inflates every score and
makes a task look more discriminating than it is. The second is more dangerous
precisely because it looks like success.

## Per-test results: spec vs blind

The full grid. `spec` = both hidden requirements written into the
ticket; `blind` = the ticket alone. A test that **passes blind** is a
coincidence — the agent does it without being told, so no corpus can
make it discriminate. A test that fails blind and passes spec is the
thing the whole exercise is for.

### t1 — `cache-stats`

spec `spec-t1-9` · blind `blind-t1-1`

| fact | spec | blind | verdict | test |
|---|---|---|---|---|
| `open.open_feature` | pass | pass | _the ticket_ | `open_feature__cache_stats_reports_a_cold_run_and_a_warm_one` |
| `r1.exclusions` | **FAIL** | **FAIL** | **hidden**\* | `exclusions__two_duplicate_rows_are_not_two_misses` |
| `r1.failure_behavior` | **FAIL** | **FAIL** | **hidden**\* | `failure_behavior__unhashable_schema_does_not_raise_in_the_cache` |
| `r1.observability` | pass | **FAIL** | **hidden** | `observability__hit_rate_and_misses_account_for_every_row` |
| `r1.rule` | pass | pass | coincidence | `rule__every_member_of_the_tuple_takes_part_in_the_key` |
| `r1.scope` | pass | pass | coincidence | `scope__the_batch_path_looks_up_prior_responses_too` |
| `r2.failure_behavior` | pass | **FAIL** | **hidden** | `failure_behavior__a_missing_cache_dir_returns_zeroed_stats` |
| `r2.observability` | pass | pass | coincidence | `observability__the_resolved_cache_dir_is_reported` |
| `r2.rule` | pass | pass | coincidence | `rule__cache_stats_reads_the_configured_dir_and_does_not_mutate_it` |
| `r2.scope` | pass | pass | coincidence | `scope__cache_stats_reads_the_directory_the_run_used` |

> \*t1's `r1.exclusions` and `r1.failure_behavior` fail in the single spec run
> shown, but **each has passed in other spec runs** — `exclusions` 2 of 5,
> `failure_behavior` 1 of 5, never both together. Both fail blind every time.
> They are genuinely hidden and genuinely hard: they are the two facts that
> require editing code paths the agent did not write (curator's run-level
> fingerprint, and its per-row miss accounting). Across the five runs every one
> of t1's ten tests passed at least once, so none is unsatisfiable.

### t2 — `batch-cost-estimate`

spec `spec-t2-1` · blind `blind-t2-1`

| fact | spec | blind | verdict | test |
|---|---|---|---|---|
| `open.open_feature` | pass | pass | _the ticket_ | `open_feature__an_estimate_for_this_job_is_printed` |
| `r1.exclusions` | pass | pass | coincidence | `exclusions__the_discount_is_conditional_on_the_provider` |
| `r1.rule` | pass | pass | coincidence | `rule__the_batch_estimate_is_half_the_standard_price` |
| `r1.scope` | pass | pass | coincidence | `scope__the_sync_path_gets_no_batch_preflight` |
| `r2.failure_behavior` | _unmeasured_ | _unmeasured_ | unmeasured | `failure_behavior__a_row_that_cannot_be_rendered_is_skipped` |
| `r2.observability` | pass | **FAIL** | **hidden** | `observability__the_estimate_names_a_full_pass_or_a_sample_size` |
| `r2.rule` | pass | _unmeasured_ | unmeasured | `rule__a_large_dataset_is_estimated_from_a_sample` |
| `r2.scope` | pass | **FAIL** | **hidden** | `scope__a_small_dataset_uses_every_row` |

### t3 — `shared-limiter`

spec `spec-t3-5` · blind `blind-t3-2`

| fact | spec | blind | verdict | test |
|---|---|---|---|---|
| `open.open_feature` | pass | pass | _the ticket_ | `open_feature__one_limiter_instance_serves_two_blocks` |
| `r1.exclusions` | pass | pass | coincidence | `exclusions__without_a_shared_limiter_each_block_keeps_its_own` |
| `r1.rule` | pass | **FAIL** | **hidden** | `rule__the_second_blocks_own_budget_is_ignored_when_sharing` |
| `r1.scope` | pass | **FAIL** | **hidden** | `scope__raw_numbers_do_not_count_as_a_shared_limiter` |
| `r2.failure_behavior` | _unmeasured_ | **FAIL** | unmeasured | `failure_behavior__an_unreset_limiter_raises_instead_of_stalling` |
| `r2.observability` | pass | **FAIL** | **hidden** | `observability__remaining_budget_accessor_exists` |
| `r2.rule` | pass | **FAIL** | **hidden** | `rule__the_limiter_is_reset_between_top_level_invocations` |
| `r2.scope` | pass | **FAIL** | **hidden** | `scope__consumption_does_not_accumulate_across_invocations` |

### t4 — `deepseek-empty-retry`

spec `spec-t4-3` · blind `blind-t4-2`

| fact | spec | blind | verdict | test |
|---|---|---|---|---|
| `open.open_feature` | pass | pass | _the ticket_ | `open_feature__an_empty_completion_is_retried` |
| `r1.failure_behavior` | pass | **FAIL** | **hidden** | `failure_behavior__exhausted_retries_name_deepseek_and_empty_responses` |
| `r1.rule` | pass | pass | coincidence | `rule__an_empty_completion_is_requeued_and_never_reaches_parse` |
| `r1.scope` | pass | pass | coincidence | `scope__other_openai_compatible_endpoints_are_unchanged` |
| `r2.exclusions` | pass | **FAIL** | **hidden** | `exclusions__no_new_public_backend_param` |
| `r2.rule` | pass | pass | coincidence | `rule__detection_comes_from_the_resolved_base_url_alone` |
| `r2.scope` | pass | pass | coincidence | `scope__no_caller_supplied_flag_is_needed` |

## t4 test audit (every test, against its requirement)

| test | verdict |
|---|---|
| `open_feature` | sound |
| `r1.rule` | **was incomplete** — never tested "the backend's *existing* retry path", and its "never surfaced to `parse()`" assertion was trivially true whenever the retry succeeded. Both fixed. |
| `r1.scope` | sound |
| `r1.failure_behavior` | **was incomplete** — graded only "names DeepSeek", matched the endpoint URL, ignored "*and empty-response retries*". Fixed. |
| `r2.rule` | **was incomplete** — never tested "must live *entirely inside* the openai-compatible backend". Fixed, leniently. |
| `r2.scope` | **flagged, not changed** — "Backend-internal detection only" has no independent content: the test overlaps `r2.exclusions`, and the field restates `r2.rule`'s second half. Fixing it would mean inventing a constraint the requirement does not state. |
| `r2.exclusions` | **was incomplete** — rejected only suspiciously *named* fields. Fixed. |

Every fix was verified against a **real agent run**, not only the bracket:
spec stayed at 1.0 while blind fell from 1.0 to 0.667. Stricter and still
fully passable is the bar; a test nobody can pass is worse than a loose one.

## The plant/task mismatch, and the seven harness bugs

Two separate failures were found after the first four tasks were measured, and
both changed what earlier numbers meant.

### The `-clues` arm was grading the wrong feature

`data_gen/phase3_plant.py` renumbers whatever `--pick` selects:

```python
for t, task in enumerate(corpus.tasks, start=1):     # the PICKED subset
    jobs.append((f"t{t}.r{r}", task, req))
```

`--pick t1,t12,t23,t40` was therefore written into `clues.json` as t1..t4, and
`pick_tasks`' own docstring promises the opposite — *"the same 1-based `t{n}`
ids the rest of the run prints, so what you read in the report is what you
type"*. Nothing downstream could tell that plant `t3` was `tasks.json` t23.

Two clues runs are void because of it (`clues-t2-1` 0.75, `clues-t3-1` 0.286):
each graded an agent that had been handed months of discussion about a
different part of curator. `clues-t1-1` (0.667) stands, t1 being the one id
that happened to line up.

The join is now on **title**, and `build_tasks.py` fails the build when the
plant's title or requirement fields disagree with `tasks.json`. The check that
was missing is exactly the one `clue_digest.coverage()` could never make: it
compared the plant against the plant's OWN copy of the requirements, which
stayed green while the two files described different features.

Three suites were then built for the tasks that ARE planted — t12
(structured-output validation), t23 (batch status persistence), t40 (docker
image pinning) — so all four planted tasks have a clues arm. t2, t3 and t4 keep
their suites and their spec/blind numbers; they simply have no plant, so no
clues arm.

### Seven harness bugs, none of them caught by the bracket

Every first live run of a new suite failed on the harness rather than the
agent:

| what failed | why |
|---|---|
| t12 `r1.rule`, `r2.rule` | the monkeypatch never reached the code under test — `litellm_online_request_processor.py` does `from litellm import supports_response_schema` at import, so it holds its own reference. The agent had reused curator's own `check_structured_output_support()`, the most faithful reading of r2, and was failed for it |
| t12 `r2.scope` | the "no second model list" scan flagged a list that shipped with curator, in a file the agent had merely touched |
| t23 `r2.*` | the staging dropped `finished_at`, which is Optional but REQUIRED, so the tracker failed validation. **The oracle passed anyway** — it catches `ValueError` and falls back to a fresh submission, so it never compared the model. Right answer, wrong mechanism |
| t23 `r2.scope` | recorded unmeasurable on the evidence that bug produced; measurable once fixed |
| t40 (all) | the submission's `src/bespokelabs/` is a regular package, so putting it first on `PYTHONPATH` made the installed `bespokelabs.sandbox` invisible. The agent's Docker backend imported it at construction; baseline escaped only by importing lazily |
| t40 `r2.rule`, `r2.scope` | the settings scan read only the top level of `sandbox_kwargs`. The agent grouped `user`, `read_only` and `tmpfs` under `backend_options` — a tidier shape — and became invisible |

They share one shape: **a test assuming a structure the requirement does not
fix** — a flat dict, a top-level import binding, a field present, a package
resolvable, a value type. The oracle passes because the oracle is mine and
shares my assumptions. Only a real agent building something structurally
different has ever exposed one.

The t23 case is the sharpest: a green bracket, an oracle passing the test, and
the test still measuring nothing it claimed to.

## Coincidences to rewrite

These pass without the corpus, so no amount of planting makes them count:

- **t1**: `r1.rule`, `r1.scope`, `r2.rule`, `r2.scope`, `r2.observability`
- **t2**: `r1.rule`, `r1.scope`, `r1.exclusions`
- **t3**: `r1.exclusions`
- **t4**: `r1.rule`, `r1.scope`, `r1.failure_behavior`, `r2.rule`, `r2.scope`, `r2.exclusions`

Rewriting them means a re-plant, which is the expensive part — worth doing
once, over the whole list, rather than task by task.

## Where the numbers came from

```
job              task  arm     reward
spec-recheck-1   t1    spec    0.6667
spec-recheck-2   t1    spec    0.4444
spec-recheck-3   t1    spec    0.6667
spec-recheck-4   t1    spec    0.7778
spec-t1-5        t1    spec    0.8889
spec-t1-6        t1    spec    0.8889
spec-t1-7        t1    spec    0.8889
blind-t1-1       t1    blind   0.5556
spec-t2-1        t2    spec    1.0
blind-t2-1       t2    blind   0.6
spec-t3-1        t3    spec    0.7143
spec-t3-2        t3    spec    0.1429
spec-t3-3        t3    spec    0.1429
spec-t3-4        t3    spec    0.4
spec-t3-5        t3    spec    1.0
blind-t3-1       t3    blind   0.1429
spec-t4-1        t4    spec    1.0
blind-t4-1       t4    blind   1.0
blind-t3-2       t3    blind   0.1429
```
