# t1 — Prompt-level response cache keying

Add a `cache_stats()` method to `curator.LLM` that reports how many of the last run's requests were served from the local cache versus sent to the backend, so users can gauge how much a re-run will cost before running it.

## Hidden requirements

**r1**

| field | what it asks |
|---|---|
| `rule` | The cache key used to look up a prior response must be derived from the exact tuple of (rendered prompt text, model_name, response_format schema, and generation_params) — not from the raw input row alone. |
| `scope` | Applies to every request path that already calls the existing cache-lookup helper, including batch and online modes. |
| `exclusions_or_crossover` | Two rows that render to an identical prompt string but differ only in fields unused by `prompt()` must be counted as the same cache entry, not treated as separate misses. |
| `failure_behavior` | If `response_format` cannot be hashed (e.g. a dynamically constructed Pydantic model), the row must be treated as a guaranteed cache miss rather than raising. |
| `observability` | `cache_stats()` must expose a `hit_rate` float and a `misses` int that together account for 100% of processed rows. |

**r2**

| field | what it asks |
|---|---|
| `rule` | `cache_stats()` must read from the same on-disk cache directory the rest of `curator.LLM` uses, honoring `CURATOR_CACHE_DIR` if set, and must never write to or mutate the cache directory itself. |
| `scope` | Read-only access to whatever directory the existing caching layer resolves to at call time. |
| `failure_behavior` | If the cache directory does not exist yet (no prior run), return zeroed stats rather than raising a file-not-found error. |
| `observability` | The returned object must include the resolved cache directory path so users can verify which cache was inspected. |

## Versions

| version | what it is |
|---|---|
| `cache-stats/` | the ticket only — the hidden requirements are recoverable from the corpus and nowhere else |
| `cache-stats-spec/` | the control — both hidden requirements written into `instruction.md` |
| `cache-stats-clues/` | the remarks phase 3 planted, quoted in date order, herrings included — the requirement itself is never stated |
| `fixtures/oracle.py` | the informed implementation; must pass every row below |
| `fixtures/naive.py` | the obvious implementation; must pass the ticket and fail the hidden rows |

```bash
harbor run -p harbor_tasks/t1-cache-stats -a oracle
```

## Measured

| requirement | field | pristine | naive | oracle | verdict |
|---|---|---|---|---|---|
| open | `open_feature` | fail | PASS | PASS | _the ticket_ |
| r1 | `exclusions` | fail | fail | PASS | **hidden** |
| r1 | `failure_behavior` | fail | fail | PASS | **hidden** |
| r1 | `observability` | fail | PASS | PASS | coincidence |
| r1 | `rule` | fail | fail | PASS | **hidden** |
| r1 | `scope` | fail | fail | PASS | **hidden** |
| r2 | `failure_behavior` | fail | PASS | PASS | coincidence |
| r2 | `observability` | fail | PASS | PASS | coincidence |
| r2 | `rule` | fail | PASS | PASS | coincidence |
| r2 | `scope` | fail | PASS | PASS | coincidence |

4 genuinely hidden, 5 coincidence, 0 unmeasurable. See [../BRACKET.md](../BRACKET.md) for what those mean.
