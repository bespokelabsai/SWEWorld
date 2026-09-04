# t4 — DeepSeek empty-response retry handling

Add automatic retry-on-empty-response handling for the `openai`-compatible backend when used against DeepSeek's API, since DeepSeek intermittently returns empty completions under load.

## Hidden requirements

**r1**

| field | what it asks |
|---|---|
| `rule` | An empty (zero-length) completion string from DeepSeek must be treated as a retryable failure and re-queued using the backend's existing retry/backoff path, not surfaced to `parse()` as a valid response. |
| `scope` | Only applies when the resolved base_url points at DeepSeek's API; must not change retry behavior for other openai-compatible endpoints, which may legitimately return short or empty strings as valid content. |
| `failure_behavior` | After `max_retries` is exhausted on empty responses, the row must fail with an error message that explicitly names DeepSeek and empty-response retries as the cause, not a generic timeout message. |

**r2**

| field | what it asks |
|---|---|
| `rule` | This special-casing must live entirely inside the openai-compatible backend's response-handling path and must not require the caller to pass any DeepSeek-specific flag; detection of 'this is DeepSeek' must be inferred from the configured base_url alone. |
| `scope` | Backend-internal detection only. |
| `exclusions_or_crossover` | Must not add a new public `backend_params` key like `is_deepseek` — the ticket's contract is that existing `backend_params` (base_url, api_key, max_retries) are the only inputs. |

## Versions

| version | what it is |
|---|---|
| `deepseek-empty-retry/` | the ticket only — the hidden requirements are recoverable from the corpus and nowhere else |
| `deepseek-empty-retry-spec/` | the control — both hidden requirements written into `instruction.md` |
| `deepseek-empty-retry-clues/` | the remarks phase 3 planted, quoted in date order, herrings included — the requirement itself is never stated |
| `fixtures/oracle.py` | the informed implementation; must pass every row below |
| `fixtures/naive.py` | the obvious implementation; must pass the ticket and fail the hidden rows |

```bash
harbor run -p failed_tasks/t4-deepseek-empty-retry -a oracle
```

## Measured

| requirement | field | pristine | naive | oracle | verdict |
|---|---|---|---|---|---|
| open | `open_feature` | fail | PASS | PASS | _the ticket_ |
| r1 | `failure_behavior` | fail | fail | PASS | **hidden** |
| r1 | `rule` | fail | PASS | PASS | coincidence |
| r1 | `scope` | fail | fail | PASS | **hidden** |
| r2 | `exclusions` | fail | PASS | PASS | coincidence |
| r2 | `rule` | fail | PASS | PASS | coincidence |
| r2 | `scope` | fail | PASS | PASS | coincidence |

2 genuinely hidden, 4 coincidence, 0 unmeasurable. See [BRACKET.md](../../harbor_tasks/BRACKET.md) for what those mean.
