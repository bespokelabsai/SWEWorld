# t2 — Batch mode cost estimate before submission

When `batch=True` is passed to `curator.LLM`, add a pre-flight step that prints an estimated cost for the batch job before any requests are submitted to the provider.

## Hidden requirements

**r1**

| field | what it asks |
|---|---|
| `rule` | The discount factor applied to the estimate must be provider-specific: 50% off standard per-token pricing for OpenAI and Anthropic batch, but the discount must NOT be applied for any provider routed through the `litellm` backend, since litellm does not expose a distinct batch pricing tier in this codebase. |
| `scope` | Only the batch cost pre-flight estimator; does not change actual billing. |
| `exclusions_or_crossover` | litellm-backed models must show the standard (non-discounted) per-token estimate even when batch=True is set on them. |

**r2**

| field | what it asks |
|---|---|
| `rule` | The estimate must be computed from a sample of the first N rows (not the full dataset) when the dataset exceeds a size threshold, to avoid iterating the entire dataset just to print an estimate. |
| `scope` | Applies whenever the input dataset length exceeds the threshold; below it, use every row. |
| `failure_behavior` | If prompt() raises on any sampled row while estimating, skip that row from the estimate silently rather than aborting the whole pre-flight step. |
| `observability` | The printed estimate must state whether it was computed from a full pass or a sample, and the sample size used. |

## Versions

| version | what it is |
|---|---|
| `batch-cost-estimate/` | the ticket only — the hidden requirements are recoverable from the corpus and nowhere else |
| `batch-cost-estimate-spec/` | the control — both hidden requirements written into `instruction.md` |
| `batch-cost-estimate-clues/` | the remarks phase 3 planted, quoted in date order, herrings included — the requirement itself is never stated |
| `fixtures/oracle.py` | the informed implementation; must pass every row below |
| `fixtures/naive.py` | the obvious implementation; must pass the ticket and fail the hidden rows |

```bash
harbor run -p harbor_tasks/t2-batch-cost-estimate -a oracle
```

## Measured

| requirement | field | pristine | naive | oracle | verdict |
|---|---|---|---|---|---|
| open | `open_feature` | fail | PASS | PASS | _the ticket_ |
| r1 | `exclusions_or_crossover` | skip | skip | skip | unmeasurable |
| r1 | `rule` | fail | PASS | PASS | coincidence |
| r1 | `scope` | fail | PASS | PASS | coincidence |
| r2 | `failure_behavior` | skip | skip | skip | unmeasurable |
| r2 | `observability` | fail | fail | PASS | **hidden** |
| r2 | `rule` | fail | fail | PASS | **hidden** |
| r2 | `scope` | fail | fail | PASS | **hidden** |

3 genuinely hidden, 2 coincidence, 2 unmeasurable. See [../BRACKET.md](../BRACKET.md) for what those mean.
