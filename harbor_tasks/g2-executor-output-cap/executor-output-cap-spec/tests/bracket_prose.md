| implementation | what it is | must |
|---|---|---|
| **pristine** | untouched curator | fail everything — proves the test discriminates |
| **naive** | the ticket implemented the obvious way, hidden requirements unknown | pass the open feature, fail the hidden facts |
| **oracle** | the ticket **plus** the hidden requirements | pass everything — proves the test is satisfiable |

A fact the **naive** build passes is not hidden: any competent
implementation gets it for free, so planting clues for it buys nothing.

## Measurable vs unmeasurable

A fact is **measurable** when two implementations exist — one that satisfies
it, one that does not — whose behaviour a test can tell apart. It is
**unmeasurable** when every implementation produces the same observable
behaviour, so any verdict a test returns is arbitrary.

The operational test is the bracket itself: *can an oracle be written that
passes while the naive build fails?* If yes, the fact is measurable.

### A measurable fact

`t2.r2.rule` — *above a size threshold the estimate is computed from the first
N rows, not the whole dataset.* An estimator that samples and one that does a
full pass both print a figure, but they say different things about where it
came from, and the sampling one names a size smaller than the dataset. The
test runs a 10,000-row job and reads the estimate's own description of itself.
Naive build fails it, oracle passes it.

Note what makes it measurable: not that sampling is *detectable in principle*,
but that the requirement also asks the estimate to declare which it did
(`r2.observability`). Counting `prompt()` calls could not have graded it —
curator renders every row into request files regardless — so without the
declaration this fact would have been unmeasurable too.

### An unmeasurable fact

`t2.r1.exclusions_or_crossover` — *litellm-backed models must not receive
the batch discount.* `_RequestProcessorFactory.create` raises `"Batch mode
is not supported with LiteLLM backend"`, so **no litellm batch run exists**.
An implementation that carefully excludes litellm and one that never
considered it produce identical behaviour: nothing happens either way.
There is no output to read, no call to count, no state to inspect.

### The distinction is easy to get wrong

`t1.r1.failure_behavior` was recorded as unmeasurable in the first pass and
is not. curator uses `model_json_schema()` both to hash a response_format
and to build the request, so patching the schema out of the request alone
leaves the parser validating against the model and the row fails
permanently — which looks like proof that no implementation can both skip
the cache and serve the row.

It can. Drop the `response_format` for the whole run so the request and
the parse agree, and separately remember that it was dropped so the cache
key stays unique — otherwise the schema is simply forgotten, the
fingerprint becomes stable again and the second run is a cache *hit*,
the opposite of the guaranteed miss the requirement asks for. Both halves
are needed and neither is obvious, which is what makes it worth hiding.

**So "unmeasurable" means "no oracle exists", not "I could not write one".**
Prove it by trying.

@SPLIT@## What to do about it

**Coincidences** should be rewritten in `data_gen/input/tasks.json` so the
obvious implementation is *wrong* rather than merely incomplete — or
dropped. A requirement satisfiable by omission contributes no signal,
because doing nothing is the most likely thing an agent does. t4 is the
clearest case: its naive build retries **every** empty completion, one
shortcut, and that alone passes four of its six facts.

**Unmeasurable** facts should be dropped or repointed at a seam that
exists. Scoring them zero counts a limit of curator against the agent.

Before planting a requirement, ask whether the two states it distinguishes
are separable in this codebase. All three failures here presupposed a seam:
t1 assumed hashing and sending were separable (they are, on both sides);
t2.r1 assumed a litellm batch path exists (it does not); t2.r2 assumed the
estimator renders rows itself, which the requirement never says.

## Reproducing this

```bash
# a scratch container from sweworld:repo-only-dev, with the suites and the
# fixtures copied in — the harbor task itself is not involved, which is the
# point: this measures the tests, not the plumbing around them.
docker cp harbor_tasks/_suites devbox:/tests
docker cp failed_tasks/t1-cache-stats/fixtures devbox:/fixtures/t1

docker exec devbox bash -c '
  cp -r /opt/world-state/input/curator /tmp/oracle
  python3 /fixtures/t1/oracle.py /tmp/oracle
  cd /tests && PYTHONPATH=/tmp/oracle/src:/tests \
    /opt/curator-dev/venv/bin/python -m pytest t1_cache_stats \
    -q --timeout=300 --timeout-method=signal'
```

~30 seconds per run, deterministic, no agent and no model variance. The
agent experiment this replaced took about seven hours across eight trials
and produced numbers that had to be discarded.
