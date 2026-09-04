# t3 — Rate limiter shared across chained LLM blocks

Support passing an existing rate limiter instance between two `curator.LLM` blocks in a pipeline (e.g. TopicGenerator -> Poet) so they share the same requests-per-minute budget instead of each block getting its own independent limiter.

## Hidden requirements

**r1**

| field | what it asks |
|---|---|
| `rule` | When a shared limiter is passed, the second block in the chain must NOT re-initialize `max_requests_per_minute` / `max_tokens_per_minute` from its own `backend_params`; those values must be ignored in favor of the shared limiter's configuration. |
| `scope` | Only applies when a limiter object (not raw numbers) is explicitly passed into `backend_params`. |
| `exclusions_or_crossover` | If no shared limiter is passed, each block must continue to build its own independent limiter from its own backend_params exactly as before. |

**r2**

| field | what it asks |
|---|---|
| `rule` | The shared limiter must track token and request budgets per-process, and must be reset (not reused) between two separate top-level pipeline invocations run back-to-back in the same Python process. |
| `scope` | Applies to reuse of the same limiter object across multiple `.__call__()` invocations of the pipeline. |
| `failure_behavior` | If the limiter is not reset and a second invocation starts while budget already appears exhausted from the first, it must raise a clear error rather than silently stalling forever. |
| `observability` | A `.remaining_budget()` accessor must be available on the limiter for the pipeline to log at the start of each invocation. |

## Versions

| version | what it is |
|---|---|
| `shared-limiter/` | the ticket only — the hidden requirements are recoverable from the corpus and nowhere else |
| `shared-limiter-spec/` | the control — both hidden requirements written into `instruction.md` |
| `shared-limiter-clues/` | the remarks phase 3 planted, quoted in date order, herrings included — the requirement itself is never stated |
| `fixtures/oracle.py` | the informed implementation; must pass every row below |
| `fixtures/naive.py` | the obvious implementation; must pass the ticket and fail the hidden rows |

```bash
harbor run -p failed_tasks/t3-shared-limiter -a oracle
```

## Measured

| requirement | field | pristine | naive | oracle | verdict |
|---|---|---|---|---|---|
| open | `open_feature` | fail | PASS | PASS | _the ticket_ |
| r1 | `exclusions` | fail | PASS | PASS | coincidence |
| r1 | `rule` | fail | fail | PASS | **hidden** |
| r1 | `scope` | fail | PASS | PASS | coincidence |
| r2 | `failure_behavior` | fail | fail | PASS | **hidden** |
| r2 | `observability` | fail | fail | PASS | **hidden** |
| r2 | `rule` | fail | fail | PASS | **hidden** |
| r2 | `scope` | fail | fail | PASS | **hidden** |

5 genuinely hidden, 2 coincidence, 0 unmeasurable. See [BRACKET.md](../../harbor_tasks/BRACKET.md) for what those mean.
