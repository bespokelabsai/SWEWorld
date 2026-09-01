# Batch payload planner for `batch_size="auto"`

## Target

### Files that change

| Path | Change |
| --- | --- |
| `src/bespokelabs/curator/request_processor/batch_payload_planner.py` | **new** — pure planner: `BatchLimits`, `PlannedBatch`, `payload_size_bytes`, `payload_bytes`, `plan_batches`, `BatchPayloadTooLargeError`, `SingleRequestTooLargeError` |
| `src/bespokelabs/curator/request_processor/base_request_processor.py` | `create_request_files()` — delete the nested `_get_optimal_batch_size` (lines 263‑278) and the `while True` loop (lines 282‑295); drive the `"auto"` branch from `self.plan_request_batches(dataset)` and return one path per planned batch |
| `src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py` | add `batch_limits`, `measure_request_payload()`, `plan_request_batches()`; make `create_batch_file()` (line 356) compute its size through the same helper and raise `BatchPayloadTooLargeError` |

### The disagreement being fixed (real, with lines)

1. **Two different rulers.** `base_request_processor.py:271` sizes a row as
   `len(json.dumps(request.model_dump(), default=str).encode())` — the *generic* request.
   `base_batch_request_processor.py:383` sizes the batch as
   `len("\n".join(json.dumps(r) for r in api_specific_requests).encode())` — the *API-specific*
   requests plus `n-1` newlines. For OpenAI the API request carries an envelope
   (`custom_id`/`method`/`url`/`body`) and, with a `response_format`, a `json_schema` wrapper;
   for Anthropic (`anthropic_batch_request_processor.py:181‑189`) it carries `max_tokens` and an
   instructor-generated system block. The planner can therefore pack a batch that
   `create_batch_file` refuses with `ValueError` at submission time, after every request file has
   already been written to disk.
2. **Infinite loop on an oversized first row.** `base_request_processor.py:272‑274`: when the very
   first request of a window is already `>= max_bytes_per_batch`, `batch_size = idx = 0` is
   returned; `base_request_processor.py:291` then does `start_idx += 0` and the `while True` loop
   at line 286 never terminates — it appends coroutines forever.
3. **The return value loses every batch but the first.** `request_files` is bound to
   `[requests_0.jsonl]` at line 241 and the `"auto"` branch (lines 280‑295) never rebinds it, while
   the loop writes `requests_0..requests_{N-1}`. `create_request_files` returns a 1-element list, so
   `run_batch_operations` submits batch 0 only. (`tests/integrations/test_all.py:465` and `:497`
   wrap the call in `except Exception: pass` and assert on files on disk — the bug is latent there.)
4. **The planner sizes the wrong request.** `base_request_processor.py:270` passes
   `generation_params_per_row=False` unconditionally, while the writer
   (`base_request_processor.py:346`) passes `"generation_params" in dataset.column_names`.
5. **Off-by-one at the limit.** The planner breaks on `>=` (line 272); `create_batch_file` rejects
   on `>` (line 386). A batch whose payload is exactly `max_bytes_per_batch` is legal at submission
   and split by the planner.
6. **Empty dataset.** A 0-row `Dataset` makes `_get_optimal_batch_size(0)` return
   `max_requests_per_batch` (the loop body never runs), so one empty `requests_0.jsonl` is written
   and submitted.

### May be REUSED (do not reimplement)

- `PromptFormatter.create_generic_request(row, idx, generation_params_per_row)` — `llm/prompt_formatter.py:95`.
- `BaseBatchRequestProcessor.create_api_specific_request_batch(generic_request) -> dict` — abstract at
  `base_batch_request_processor.py:236`, implemented by the openai (`:229`), azure (`:39`),
  anthropic (`:160`), mistral (`:212`) and gemini (`:227`) processors.
- `max_requests_per_batch` / `max_bytes_per_batch` properties: openai `50_000` / `200*1024*1024`,
  anthropic `100_000` / `256*1024*1024`, mistral `1_000_000` / `500*1024*1024`,
  gemini `_GEMINI_BATCH_RATELIMIT_MAP` lookup (default `50_000`) / `1024*1024*1024`.
- `BaseRequestProcessor.acreate_request_file(dataset, request_file, metadata_file, start_idx, batch_size)`
  — `base_request_processor.py:321`. Keeps writing `{"num_jobs": n}` metadata; unchanged.
- `run_in_event_loop` — `request_processor/event_loop.py`.
- `BatchRequestProcessorConfig` — `request_processor/config.py:79` (`batch_size: int | "auto"`).
- `_verify_existing_request_files` — `base_request_processor.py:156‑161`: under `batch_size="auto"`
  it cannot verify the cache and returns `[1]` on a fresh working dir, so the `"auto"` branch always
  regenerates. Unchanged; the planner does not consult `incomplete_files`.

### Must be BUILT

- The module `batch_payload_planner.py` in full (5 names below plus 2 exception classes).
- `batch_limits`, `measure_request_payload`, `plan_request_batches` on `BaseBatchRequestProcessor`.
- The rewritten `"auto"` branch of `create_request_files`.

### Environment

Python `^3.10` (`pyproject.toml:22`). Available: `datasets`, `pydantic` v2, `aiofiles`, `pytest`,
`litellm`, `instructor`. Tests construct processors without a client the way
`tests/unittests/test_batch.py:55` does — `OpenAIBatchRequestProcessor.__new__(cls)` with
`config`, `prompt_formatter`, `working_dir`, `_cost_processor` assigned by hand — and patch the two
limit properties with `unittest.mock.PropertyMock` the way `tests/integrations/test_all.py:469` does.
No network, no clients, no sleeps.

### Invariant that is NOT changing

The explicit-integer `batch_size` branch (`base_request_processor.py:297‑311`) keeps its current
behaviour exactly: `ceil(len(dataset) / batch_size)` fixed-width files, filtered by
`incomplete_files`, no byte-based resplit, no planner call. `create_batch_file` still raises for such
a batch at submission time.

## The API

### `src/bespokelabs/curator/request_processor/batch_payload_planner.py`

```python
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class BatchLimits:
    max_requests_per_batch: int
    max_bytes_per_batch: int


@dataclass(frozen=True)
class PlannedBatch:
    index: int          # 0-based position of this batch in the returned list
    start_idx: int      # inclusive dataset index of the first request
    end_idx: int        # exclusive dataset index one past the last request
    num_requests: int   # == end_idx - start_idx, always >= 1
    num_bytes: int      # exact byte length of the file `create_batch_file` will build


class BatchPayloadTooLargeError(ValueError):
    def __init__(self, *, num_requests: int, size_bytes: int, limit_bytes: int) -> None: ...
    num_requests: int
    size_bytes: int
    limit_bytes: int


class SingleRequestTooLargeError(BatchPayloadTooLargeError):
    def __init__(self, *, row_idx: int, size_bytes: int, limit_bytes: int) -> None: ...
    row_idx: int
    # num_requests is 1


def payload_size_bytes(api_specific_request: dict) -> int: ...


def payload_bytes(sizes: Sequence[int]) -> int: ...


def plan_batches(sizes: Sequence[int], limits: BatchLimits) -> list[PlannedBatch]: ...
```

### `BaseBatchRequestProcessor` additions (`batch/base_batch_request_processor.py`)

```python
    @property
    def batch_limits(self) -> BatchLimits: ...
        # BatchLimits(max_requests_per_batch=self.max_requests_per_batch,
        #             max_bytes_per_batch=self.max_bytes_per_batch)

    def measure_request_payload(self, generic_request: GenericRequest) -> int: ...
        # payload_size_bytes(self.create_api_specific_request_batch(generic_request))

    def plan_request_batches(self, dataset: "Dataset") -> list[PlannedBatch]: ...

    def create_batch_file(self, api_specific_requests: list[dict]) -> bytes: ...
        # unchanged signature; return type annotation corrected from `str` to `bytes`
        # (it already returns bytes today)
```

### `create_request_files` return

`create_request_files(dataset: Optional["Dataset"]) -> list[str]` — unchanged signature. In the
`"auto"` branch it returns `[os.path.join(self.working_dir, f"requests_{p.index}.jsonl") for p in plan]`.

## Parts

### P1 — The ruler is the submitted payload

**Behaviour.** A row's planned size is
`payload_size_bytes(self.create_api_specific_request_batch(generic_request))`, i.e. the byte length
of the provider-specific dict that `requests_from_generic_request_file` will hand to
`create_batch_file` — not the `GenericRequest` that gets written to `requests_*.jsonl`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep today's ruler: `len(json.dumps(generic_request.model_dump(), default=str).encode())`. It is
   already there, it needs no provider hook, and it looks like "the request".
2. Size the JSONL line actually written to disk: the generic request plus its trailing `"\n"`
   (`len(...) + 1`), reasoning that the request file *is* what gets uploaded.

**The observable.** OpenAI processor, `model="gpt-4o-mini"`, no `response_format`, no system prompt,
one row `{"prompt": "say 0"}`, `prompt()` returning `row["prompt"]`:
- `measure_request_payload(req)` **== 153**
  (`{"custom_id": "0", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "say 0"}]}}`).
- Alternative 1 gives **217**, alternative 2 gives **218**.
And the cross-check that ties the two sides together: for a 5-row dataset of such rows,
`plan_request_batches(...)[0].num_bytes == len(create_batch_file(all_five_api_requests))`.

### P2 — Exact serialization form

**Behaviour.** `payload_size_bytes(d)` is exactly `len(json.dumps(d).encode())`: `json.dumps` with
its stock arguments — `ensure_ascii=True`, separators `", "` / `": "`, no `default=` fallback — then
UTF-8 encoded. This is byte-identical to `base_batch_request_processor.py:383`. A non-serializable
value therefore raises `TypeError` out of the planner rather than being coerced to `str`.

**Alternatives a competent engineer would plausibly choose instead.**
1. `len(json.dumps(d, ensure_ascii=False).encode("utf-8"))` — "measure the real UTF-8 bytes", which
   is what a size-conscious engineer reaches for.
2. `len(json.dumps(d, separators=(",", ":")).encode())` — compact form, "that's what goes over the
   wire", or mirroring the `default=str` habit from `base_request_processor.py:271`.

**The observable.** Same single-row setup as P1 but with content `"café"`:
- `payload_size_bytes(api_request)` **== 157** (`"café"` escapes to 6 characters).
- Alternative 1 gives **153**; alternative 2 gives **144**.
Plus: `payload_size_bytes({"a": {1, 2}})` raises **`TypeError`** (not `ValueError`, not an int).

### P3 — File-level accounting: `sum(sizes) + (n - 1)`

**Behaviour.** `payload_bytes(sizes)` returns `sum(sizes) + len(sizes) - 1` for a non-empty
sequence and `0` for an empty one — the `n-1` separators of `"\n".join(...)`, with no trailing
newline. Every `PlannedBatch.num_bytes` is `payload_bytes` of that batch's row sizes.

**Alternatives a competent engineer would plausibly choose instead.**
1. `sum(sizes)` — ignore separators; one byte per request "is noise".
2. `sum(sizes) + len(sizes)` — treat the file as JSONL with a trailing newline per line, which is
   what `acreate_request_file` writes (`base_request_processor.py:354` writes `json.dumps(...) + "\n"`).

**The observable.** Three exact values:
- `payload_bytes([]) == 0`, `payload_bytes([10]) == 10`, `payload_bytes([10, 10, 10]) == 32`.
- `plan_batches([10]*7, BatchLimits(1000, 32))` → first batch `num_requests == 3`;
  alternative 2 gives `2`.
- `plan_batches([10]*7, BatchLimits(1000, 31))` → first batch `num_requests == 2`;
  alternative 1 gives `3`.
Also `create_batch_file([])` returns `b""` and raises nothing.

### P4 — Both limits are inclusive

**Behaviour.** A batch is admissible while `payload_bytes(batch) <= max_bytes_per_batch` **and**
`len(batch) <= max_requests_per_batch`. A batch landing exactly on either limit is kept, matching
`create_batch_file`'s `n_requests > max` / `file_content_size > max_bytes` tests.

**Alternatives a competent engineer would plausibly choose instead.**
1. Exclusive, i.e. keep today's `>=` break condition from `base_request_processor.py:272` — a batch
   that reaches the limit is closed before the reaching request.
2. Leave deliberate headroom (a common instinct once you know provider limits are approximate),
   e.g. plan against `int(max_bytes_per_batch * 0.95)` or `max_requests_per_batch - 1`.

**The observable.** `plan_batches([10]*6, BatchLimits(max_requests_per_batch=3, max_bytes_per_batch=32))`
returns **exactly 2** `PlannedBatch` objects:
`PlannedBatch(0, 0, 3, 3, 32)` and `PlannedBatch(1, 3, 6, 3, 32)`.
Alternative 1 returns 3 batches of sizes `[2, 2, 2]`; alternative 2 returns 3 batches of `[2, 2, 2]`
(headroom on count) or `[3, 3]` with `num_bytes` computed against a shrunk limit — in either case
the pair `(len(plan), plan[0].num_bytes) != (2, 32)`.

### P5 — Greedy forward fill, no rebalancing

**Behaviour.** The planner walks the sizes once in index order and adds each request to the current
batch if it still fits, otherwise closes the batch and starts a new one at that request. Batches are
contiguous, ordered, and exhaustive: `plan[0].start_idx == 0`, `plan[i].end_idx == plan[i+1].start_idx`,
`plan[-1].end_idx == len(sizes)`. Rows are never reordered, never packed bin-first-fit-decreasing, and
the batch count is never smoothed.

**Alternatives a competent engineer would plausibly choose instead.**
1. Even split: compute `k = ceil(total_bytes / max_bytes_per_batch)` and cut into `k` batches of
   `ceil(n/k)` rows so the last batch isn't a stub — a very common "balance the shards" instinct.
2. First-fit-decreasing bin packing: sort rows by size to minimise the number of batches, recording
   each batch's member indices instead of a span.

**The observable.** `plan_batches([10]*7, BatchLimits(1000, 32))` returns **exactly**
`[PlannedBatch(0, 0, 3, 3, 32), PlannedBatch(1, 3, 6, 3, 32), PlannedBatch(2, 6, 7, 1, 10)]`.
Alternative 1 returns 3 batches of sizes `[3, 2, 2]`; alternative 2 returns 3 batches whose spans
are not contiguous (or whose shape is not a span at all).

### P6 — A single oversized row raises, it does not stall

**Behaviour.** If one request's own size exceeds `max_bytes_per_batch`, `plan_batches` raises
`SingleRequestTooLargeError(row_idx=<index>, size_bytes=<that size>, limit_bytes=<limit>)`
immediately, before returning any plan. This replaces `base_request_processor.py:272‑274 + 291`,
where the same input yields `batch_size = 0` and an unterminating `while True`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Emit it as a one-request batch anyway and let `create_batch_file` raise its existing `ValueError`
   at submission — "one layer owns the limit, don't duplicate the check".
2. Skip the row (log a warning) and keep planning, so the rest of the dataset still runs.
3. Guard the loop with `max(batch_size, 1)` — the minimal patch that stops the hang and forces the
   oversized row into a batch of its own.

**The observable.** `plan_batches([10, 500, 10], BatchLimits(1000, 32))` raises
**`SingleRequestTooLargeError`**, and the caught exception satisfies:
`err.row_idx == 1`, `err.size_bytes == 500`, `err.limit_bytes == 32`, `err.num_requests == 1`,
`isinstance(err, BatchPayloadTooLargeError)` and `isinstance(err, ValueError)`.
Alternatives 1 and 3 return `[PlannedBatch(0,0,1,1,10), PlannedBatch(1,1,2,1,500), PlannedBatch(2,2,3,1,10)]`
with no exception; alternative 2 returns 1 batch of the 2 surviving rows.

### P7 — `create_request_files` returns every file it wrote, in numeric order

**Behaviour.** In the `"auto"` branch the returned list has one path per `PlannedBatch`, ordered by
`PlannedBatch.index`, i.e. `requests_0.jsonl, requests_1.jsonl, …, requests_{N-1}.jsonl`; metadata
files are written alongside as `metadata_{index}.json`. This is the fix for the stale binding at
`base_request_processor.py:241`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Leave the binding alone (today's code): return `["…/requests_0.jsonl"]` regardless of `N` — the
   loop already writes the files, so nothing looks broken locally.
2. Recompute from disk: `sorted(glob.glob(os.path.join(self.working_dir, "requests_*.jsonl")))`,
   reusing the glob already at `base_request_processor.py:216`.

**The observable.** OpenAI processor, `max_requests_per_batch` patched to `1`, generous byte limit,
11-row dataset. `create_request_files(dataset)` returns a list of length **11** whose basenames are
exactly, in order:
`["requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl", …, "requests_9.jsonl", "requests_10.jsonl"]`.
Alternative 1 returns length **1**. Alternative 2 returns length 11 but with
`basename(result[1]) == "requests_10.jsonl"` and `basename(result[10]) == "requests_9.jsonl"`.

### P8 — Row-level `generation_params` is part of the measured payload

**Behaviour.** `plan_request_batches` computes `generation_params_per_row = "generation_params" in
dataset.column_names` once and passes it into `create_generic_request(row, idx,
generation_params_per_row)`, so the planner measures the same request the writer will produce
(`base_request_processor.py:346‑352`). This is the fix for the hardcoded `False` at
`base_request_processor.py:270`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the hardcoded `False` while porting the loop — the parameter is easy to carry over verbatim,
   and the planner "only needs an estimate".
2. Pass `True` always, or `bool(self.prompt_formatter.generation_params)`, on the theory that
   generation params come from the config rather than the dataset.

**The observable.** OpenAI processor, `max_requests_per_batch=1_000_000`, `max_bytes_per_batch`
patched to **480**, 6-row dataset with columns
`{"prompt": ["say 0", …, "say 5"], "generation_params": ['{"temperature": 0.9}'] * 6}`:
- each measured payload is **173** bytes, and the plan is **3** batches
  `[PlannedBatch(0,0,2,2,347), PlannedBatch(1,2,4,2,347), PlannedBatch(2,4,6,2,347)]`;
  `create_request_files` writes 3 files with line counts `[2, 2, 2]`.
- Alternative 1 (and the `bool(self.prompt_formatter.generation_params)` flavour of alternative 2,
  whose config params are empty here) measures **153** bytes and produces **2** batches
  `[PlannedBatch(0,0,3,3,461), PlannedBatch(1,3,6,3,461)]`, line counts `[3, 3]`.
- Second dataset, same processor, columns `{"prompt": ["say 0", …, "say 5"]}` with **no**
  `generation_params` column: the plan succeeds with per-row size **153** and 2 batches
  `[PlannedBatch(0,0,3,3,461), PlannedBatch(1,3,6,3,461)]`, whereas the always-`True` flavour of
  alternative 2 raises **`KeyError('generation_params')`** out of
  `PromptFormatter.create_generic_request` (`llm/prompt_formatter.py:123` indexes `row["generation_params"]`
  inside a `try` that only catches `json.JSONDecodeError`).

### P9 — One measurement per row per planning pass

**Behaviour.** `plan_request_batches` iterates the dataset once and calls
`create_api_specific_request_batch` exactly once per row, in index order. It does not re-measure rows
when a batch is closed and it does not pre-fetch `max_requests_per_batch`-sized windows.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep today's structure — `dataset.select(range(start_idx, start_idx + max_requests_per_batch))`
   per batch, re-measuring the boundary row (and every row of the window it scanned) each time.
2. Two passes: first materialise `sizes = [measure(row) for row in dataset]`, then call
   `plan_batches`, then re-measure inside the writer for logging — a natural "separate measurement
   from planning" refactor that ends up measuring twice.

**The observable.** With `create_api_specific_request_batch` wrapped in a counting spy (a
`unittest.mock.Mock` with `side_effect` delegating to the real method), OpenAI processor,
6 rows of `{"prompt": "say N"}`, `max_requests_per_batch=6`, `max_bytes_per_batch=400`:
`spy.call_count == 6` after `create_request_files(dataset)`.
Alternative 1 gives `8` (windows measure rows 0‑2, 2‑4, 4‑5); alternative 2 gives `12`.
(The resulting plan is `[(0,2),(2,4),(4,6)]` under all three, so the count is the only separator —
that is exactly what is asserted.)

### P10 — Zero rows plans zero batches

**Behaviour.** `plan_batches([], limits) == []`, and for a `Dataset` with `len(dataset) == 0` and
`batch_size="auto"`, `create_request_files` returns `[]` and writes no `requests_*.jsonl` and no
`metadata_*.json`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Today's outcome: one empty `requests_0.jsonl` plus `metadata_0.json` with `{"num_jobs": 0}` — the
   `request_file`/`metadata_file` names are already bound at lines 240‑244, so writing them is the
   path of least resistance.
2. Raise `ValueError("dataset is empty")` at plan time — refuse to build a run with nothing in it.

**The observable.** `plan_batches([], BatchLimits(50_000, 200*1024*1024)) == []`, and after
`create_request_files(Dataset.from_dict({"prompt": []}))`:
`result == []`, `len(glob.glob(os.path.join(working_dir, "requests_*.jsonl"))) == 0`, and
`len(glob.glob(os.path.join(working_dir, "metadata_*.json"))) == 0`.
Alternative 1 gives `len(result) == 1` and one file of 0 lines; alternative 2 raises.

### P11 — The plan is written down: `batch_plan.json`

**Arbitrary:** an invented name — the sidecar file, its envelope keys and the `plan_document`
helper that builds it.

**Behaviour.** `batch_payload_planner` exports two constants and one helper:

```python
PLAN_FILE_NAME = "batch_plan.json"
PLAN_FORMAT_VERSION = 1


def plan_document(plan: Sequence[PlannedBatch], limits: BatchLimits) -> dict: ...
```

`plan_document` returns exactly these keys, in this order:

| key | value |
| --- | --- |
| `plan_format_version` | `PLAN_FORMAT_VERSION` (`1`) |
| `plan_id` | `plan_fingerprint(plan)` — P12 |
| `limits` | `dataclasses.asdict(limits)` — the three fields of `BatchLimits` |
| `num_batches` | `len(plan)` |
| `num_requests` | `sum(p.num_requests for p in plan)` |
| `num_bytes` | `sum(p.num_bytes for p in plan)` — the batch files' sizes summed, *not* a file size on disk |
| `batches` | `[dataclasses.asdict(p) for p in plan]` — five keys each, in field order |

In the `"auto"` branch of `create_request_files`, once `plan_request_batches` has returned,
`json.dumps(plan_document(plan, self.batch_limits), indent=2) + "\n"` is written to
`os.path.join(self.working_dir, PLAN_FILE_NAME)` before any request file is written. It is written
for an empty plan too. The explicit-integer `batch_size` branch and the `dataset is None` path never
write it, and `metadata_{i}.json` keeps its `{"num_jobs": n}` body unchanged — the sidecar is the
only place the plan itself is recorded, because `_verify_existing_request_files` cannot describe an
`"auto"` run's shape.

**Alternatives a competent engineer would plausibly choose instead.**
1. Write nothing. Nothing in `create_request_files` records anything beyond `metadata_{i}.json`
   today, and the plan is a return value — persisting it is not needed to make the feature work.
2. Fold the plan into the existing per-batch metadata: `metadata_{i}.json` becomes
   `{"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}`. There is already one metadata
   file per batch, so this is where a plan naturally lands.
3. A differently shaped file — `plan.json`, or a `batch_plan.jsonl` with one line per batch, or a
   bare `[{...}, {...}]` list with no version/limits envelope.

**The observable.** The end-to-end run below (OpenAI processor, 5 rows, limits patched to `3` /
`400`) leaves `batch_plan.json` in `working_dir`, and `json.load` of it equals exactly:

```python
{
    "plan_format_version": 1,
    "plan_id": "f4b1ea1573c0",
    "limits": {"max_requests_per_batch": 3, "max_bytes_per_batch": 400, "max_batches_per_plan": 512},
    "num_batches": 3,
    "num_requests": 5,
    "num_bytes": 767,
    "batches": [
        {"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307},
        {"index": 1, "start_idx": 2, "end_idx": 4, "num_requests": 2, "num_bytes": 307},
        {"index": 2, "start_idx": 4, "end_idx": 5, "num_requests": 1, "num_bytes": 153},
    ],
}
```

with `list(doc) == ["plan_format_version", "plan_id", "limits", "num_batches", "num_requests",
"num_bytes", "batches"]` and the raw text ending in `"]\n}\n"`. For the empty dataset of P10 the
file is still written and loads as
`{"plan_format_version": 1, "plan_id": "e3b0c44298fc", "limits": {"max_requests_per_batch": 3,
"max_bytes_per_batch": 400, "max_batches_per_plan": 512}, "num_batches": 0, "num_requests": 0,
"num_bytes": 0, "batches": []}` — so `os.listdir(working_dir) == ["batch_plan.json"]`. With
`batch_size=2` (the explicit-integer branch) on a 3-row dataset, `"batch_plan.json" not in
os.listdir(working_dir)`. Alternative 1 leaves no such file; alternatives 2 and 3 fail the
`json.load` equality and the `metadata_0.json == {"num_jobs": 2}` check.

### P12 — `plan_id`: 12 hex characters over the cuts

**Arbitrary:** a chosen value — the digest, the truncation length and the canonical string it is
taken over.

**Behaviour.** `batch_payload_planner` exports

```python
def plan_fingerprint(plan: Sequence[PlannedBatch]) -> str: ...
```

which builds the canonical string `";".join(f"{p.start_idx}-{p.end_idx}:{p.num_bytes}" for p in
plan)`, encodes it UTF-8, and returns the **first 12 characters** of its `hashlib.sha256`
hexdigest. An empty plan fingerprints the empty string. The fingerprint deliberately covers only
where the cuts fall and how big each batch is — `index` and `num_requests` are derivable from the
span, so two runs that cut the dataset the same way share a `plan_id` regardless of how the
`PlannedBatch` objects were constructed. It is the value of `plan_id` in `batch_plan.json`; 12
characters is what fits a log line and a working-dir name while staying collision-free at the
handful-of-plans-per-run scale.

**Alternatives a competent engineer would plausibly choose instead.**
1. The full 64-character hexdigest — no truncation decision to justify.
2. A different canonical form: `hashlib.sha256(json.dumps([asdict(p) for p in plan]).encode())`,
   reusing the serialization the sidecar already performs.
3. A different digest or width: `hashlib.md5(...).hexdigest()[:12]`, or `sha256(...)[:8]`.

**The observable.** Four exact strings:
- `plan_fingerprint([]) == "e3b0c44298fc"`.
- `plan_fingerprint(plan_batches([10] * 7, BatchLimits(1000, 32))) == "ad0828fea95e"`
  (canonical string `"0-3:32;3-6:32;6-7:10"`).
- `plan_fingerprint([PlannedBatch(0, 0, 2, 2, 307), PlannedBatch(1, 2, 4, 2, 307),
  PlannedBatch(2, 4, 5, 1, 153)]) == "f4b1ea1573c0"` — the same string the end-to-end run writes as
  `plan_id`.
- The 11-batch plan of P7 (11 rows, `max_requests_per_batch` patched to `1`) fingerprints
  `"c53f6fb95c13"`.

On the `[10] * 7` plan, alternative 1 returns the 64-character
`"ad0828fea95efac35832ae96612083c4594e1d68889f471c9b5e3bbf78bbb0b4"`, alternative 2 returns
`"a17bee2e1dab"`, and alternative 3 returns `"5147d5c318f7"` (md5) or `"ad0828fe"` (8 characters).

### P13 — A plan may not exceed 512 batches

**Arbitrary:** a chosen value — the `512` cap, carried as a third field on `BatchLimits`, with its
own error class.

**Behaviour.** `BatchLimits` gains a third field, defaulted from a module constant:

```python
_MAX_BATCHES_PER_PLAN = 512


@dataclass(frozen=True)
class BatchLimits:
    max_requests_per_batch: int
    max_bytes_per_batch: int
    max_batches_per_plan: int = _MAX_BATCHES_PER_PLAN
```

`BaseBatchRequestProcessor.batch_limits` keeps constructing `BatchLimits` with the two provider
limits only, so it carries the default `512`. After `plan_batches` has built the whole plan and
before it returns, `len(plan) > limits.max_batches_per_plan` raises

```python
class BatchPlanTooFragmentedError(ValueError):
    def __init__(self, *, num_batches: int, limit: int) -> None: ...
    num_batches: int   # the full count the plan would have needed
    limit: int
```

exported from the same module. It is a `ValueError` but **not** a `BatchPayloadTooLargeError` — a
fragmented plan is not an oversized payload. The cap exists because every planned batch becomes one
provider batch job that `BatchStatusTracker` holds in memory and polls each cycle; past a few
hundred jobs the run is almost always a misconfigured limit rather than an intended fan-out. The
row-size scan of P6 runs first, so `SingleRequestTooLargeError` wins when a dataset would trip both.

**Alternatives a competent engineer would plausibly choose instead.**
1. No cap at all — nothing in the codebase bounds the number of request files, and the two provider
   limits are the only limits the ticket mentions.
2. A cap that only warns: `logger.warning(...)` and carry on, so a large run is never blocked.
3. A cap expressed somewhere else: a `max_batches` argument on `plan_batches`, a constant checked in
   `create_request_files` after planning, or a bound derived from `max_requests_per_batch`.

**The observable.**
- `BatchLimits(1000, 32).max_batches_per_plan == 512`, and with the OpenAI processor's limits
  patched to `3` / `400`, `processor.batch_limits == BatchLimits(max_requests_per_batch=3,
  max_bytes_per_batch=400, max_batches_per_plan=512)`.
- `len(plan_batches([10] * 512, BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=1000))) == 512`
  — the boundary is admissible.
- `plan_batches([10] * 513, BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=1000))` raises
  `BatchPlanTooFragmentedError` with `err.num_batches == 513`, `err.limit == 512`,
  `isinstance(err, ValueError) is True` and `isinstance(err, BatchPayloadTooLargeError) is False`.
- An explicit cap is honoured: `plan_batches([10] * 3, BatchLimits(max_requests_per_batch=1,
  max_bytes_per_batch=1000, max_batches_per_plan=2))` raises with `err.num_batches == 3`,
  `err.limit == 2`.
- Precedence: `plan_batches([10] * 600 + [5000], BatchLimits(max_requests_per_batch=1,
  max_bytes_per_batch=1000))` raises `SingleRequestTooLargeError` with `err.row_idx == 600`, not
  `BatchPlanTooFragmentedError`.

Alternatives 1 and 2 return a 513-element list from the third bullet; alternative 3 fails the first
bullet (`BatchLimits` has two fields) and, for the `plan_batches` variants, the second and fourth.

### P14 — The `"auto"` branch sweeps the working directory first

**Arbitrary:** a deliberate departure — the surrounding code globs the working directory in order to
*reuse* what it finds (`base_request_processor.py:214`, `:216`) and never deletes anything; this
branch deletes.

**Behaviour.** In the `"auto"` branch, after `plan_request_batches(dataset)` has returned and before
`batch_plan.json` and the new request files are written, every existing
`requests_*.jsonl` and every existing `metadata_*.json` in `self.working_dir` is removed
(`glob.glob` + `os.remove`). Nothing else is touched: `responses_*.jsonl`, `*.arrow`,
`batch_objects.jsonl` and any other file survive. A previous `"auto"` run under different limits
leaves a longer numbering behind (`requests_0..9.jsonl` for a plan of 3), and those stale files are
what a later glob-based read would pick up, so the branch clears them rather than overwriting the
prefix. The sweep runs *only after* planning returns: a plan that raises
(`SingleRequestTooLargeError`, `BatchPlanTooFragmentedError`) leaves the working directory
byte-for-byte unchanged. The explicit-integer `batch_size` branch does not sweep — it still relies on
`incomplete_files` and may legitimately leave earlier files in place.

**Alternatives a competent engineer would plausibly choose instead.**
1. Delete nothing, the way every other path in the file behaves: write `requests_0..N-1` and let any
   higher-numbered leftovers sit there.
2. Sweep before planning, so the directory is clean as soon as the branch is entered.
3. Remove only the paths the new plan is about to write (i.e. truncate-on-open, which is what
   `acreate_request_file` already does), or sweep in both `batch_size` branches.

**The observable.** `working_dir` pre-populated with `requests_0.jsonl … requests_5.jsonl`,
`metadata_0.json … metadata_5.json` (each holding stale content) and `responses_0.jsonl` holding
`"keep\n"`; then the end-to-end run below (5 rows, limits `3` / `400`):

```python
sorted(os.listdir(working_dir)) == [
    "batch_plan.json",
    "metadata_0.json", "metadata_1.json", "metadata_2.json",
    "requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl",
    "responses_0.jsonl",
]
open(os.path.join(working_dir, "responses_0.jsonl")).read() == "keep\n"
```

Alternative 1 leaves 14 entries, including `requests_3.jsonl … requests_5.jsonl`. Alternative 3
leaves the same 14. And on the failure path — the same pre-populated directory plus a stale
`batch_plan.json` containing `{"plan_format_version": 1, "stale": true}`, then
`create_request_files(Dataset.from_dict({"prompt": ["ok", "x" * 600, "ok"]}))` with
`max_bytes_per_batch` patched to `400`:

```python
# raises SingleRequestTooLargeError(row_idx=1, size_bytes=748, limit_bytes=400)
sorted(os.listdir(working_dir)) == [
    "batch_plan.json",
    "metadata_0.json", "metadata_1.json", "metadata_2.json",
    "metadata_3.json", "metadata_4.json", "metadata_5.json",
    "requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl",
    "requests_3.jsonl", "requests_4.jsonl", "requests_5.jsonl",
    "responses_0.jsonl",
]
json.load(open(os.path.join(working_dir, "batch_plan.json"))) == {"plan_format_version": 1, "stale": True}
open(os.path.join(working_dir, "requests_2.jsonl")).read() == "stale\n"
```

All 14 entries survive. Alternative 2 sweeps before planning, so it leaves 2 entries here —
`batch_plan.json` and `responses_0.jsonl`.

### P15 — One summary line per planning pass

**Arbitrary:** a policy with no local evidence — the code logs per *file written*
(`base_request_processor.py:345`), never per plan; the level split and the wording of these two
records are this team's choice.

**Behaviour.** `plan_request_batches` emits exactly one record on curator's logger (`from
bespokelabs.curator.log import logger`, logger name `"curator"`) per call, after `plan_batches`
returns:

- non-empty plan, at **INFO**:
  `f"Planned {len(plan)} batch(es) for {num_requests} request(s): {num_bytes:,} bytes total, largest batch {largest.num_bytes:,} bytes in {largest.num_requests} request(s)."`
  where `num_requests` and `num_bytes` are the plan totals and `largest` is `max(plan, key=lambda
  planned: planned.num_bytes)` — the *first* batch of maximal `num_bytes` when several tie. Both
  byte figures carry `,` thousands separators; the counts do not.
- empty plan, at **WARNING**, and with no INFO line:
  `"Batch plan is empty: dataset has 0 rows; no batches will be submitted."`

**Alternatives a competent engineer would plausibly choose instead.**
1. Log nothing from the planner: `create_request_files` already logs `"Preparing request file(s) in
   …"` and `acreate_request_file` logs `"Wrote N requests to …"` per file, so the run is already
   narrated.
2. Log per planned batch instead of per plan — one line each, mirroring the existing per-file line.
3. The same summary at DEBUG (`create_batch_file` logs its size at DEBUG), or the empty-plan case at
   INFO, or folded into the same INFO line as a `0 batch(es)` summary.

**The observable.** Records captured from the `"curator"` logger during a single
`plan_request_batches` call, message text compared exactly:
- 5 rows, limits `3` / `400` → exactly one record, `INFO`,
  `"Planned 3 batch(es) for 5 request(s): 767 bytes total, largest batch 307 bytes in 2 request(s)."`
- 11 rows, `max_requests_per_batch` patched to `1` → exactly one record, `INFO`,
  `"Planned 11 batch(es) for 11 request(s): 1,685 bytes total, largest batch 155 bytes in 1 request(s)."`
  (rows 0‑9 measure 153 bytes, row 10 measures 155.)
- 6 rows with a `generation_params` column, `max_bytes_per_batch` patched to `480` (the P8 setup) →
  exactly one record, `INFO`,
  `"Planned 3 batch(es) for 6 request(s): 1,041 bytes total, largest batch 347 bytes in 2 request(s)."`
- `Dataset.from_dict({"prompt": []})` → exactly one record, `WARNING`,
  `"Batch plan is empty: dataset has 0 rows; no batches will be submitted."`

Alternative 1 captures zero records in all four cases; alternative 2 captures 3, 11, 3 and 0;
alternative 3 gets the level wrong on the first three or on the fourth.

## End to end

### Inputs

```python
from datasets import Dataset
from unittest.mock import PropertyMock, patch

dataset = Dataset.from_dict({"prompt": ["say 0", "say 1", "say 2", "say 3", "say 4"]})

# OpenAIBatchRequestProcessor built without a client (tests/unittests/test_batch.py:55 pattern):
#   config           = BatchRequestProcessorConfig(model="gpt-4o-mini", batch_size="auto")
#   prompt_formatter = PromptFormatter(model_name="gpt-4o-mini",
#                                      prompt_func=lambda row: row["prompt"],
#                                      parse_func=None, response_format=None,
#                                      generation_params={}, system_prompt=None)
#   working_dir      = tmp_path
# limits patched: max_requests_per_batch -> 3, max_bytes_per_batch -> 400

# working_dir is not empty: a previous "auto" run under a larger byte limit left
#   requests_0.jsonl … requests_5.jsonl   (each holding "stale\n")
#   metadata_0.json  … metadata_5.json    (each holding "{}\n")
# and the run's own output is there too:
#   responses_0.jsonl                     (holding "keep\n")
```

`processor.batch_limits` is
`BatchLimits(max_requests_per_batch=3, max_bytes_per_batch=400, max_batches_per_plan=512)` — the
fan-out cap keeps its default and never binds here.

### Per-row measurement

Every row's API-specific request serialises to **153** bytes, e.g. row 0:

```json
{"custom_id": "0", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "say 0"}]}}
```

`[measure_request_payload(r) for r in requests] == [153, 153, 153, 153, 153]`

### `processor.plan_request_batches(dataset)`

```python
[
    PlannedBatch(index=0, start_idx=0, end_idx=2, num_requests=2, num_bytes=307),
    PlannedBatch(index=1, start_idx=2, end_idx=4, num_requests=2, num_bytes=307),
    PlannedBatch(index=2, start_idx=4, end_idx=5, num_requests=1, num_bytes=153),
]
```

(`153*2 + 1 = 307 <= 400`; `153*3 + 2 = 461 > 400`; the count limit of 3 never binds, and
`3 <= 512` so the plan is not too fragmented.)

The call logs exactly one record on the `"curator"` logger, at `INFO`:

```
Planned 3 batch(es) for 5 request(s): 767 bytes total, largest batch 307 bytes in 2 request(s).
```

and `plan_fingerprint(plan) == "f4b1ea1573c0"`.

### `processor.create_request_files(dataset)`

```python
[f"{working_dir}/requests_0.jsonl",
 f"{working_dir}/requests_1.jsonl",
 f"{working_dir}/requests_2.jsonl"]
```

On disk:

| file | lines | `original_row_idx` values | metadata |
| --- | --- | --- | --- |
| `requests_0.jsonl` | 2 | `[0, 1]` | `metadata_0.json` → `{"num_jobs": 2}` |
| `requests_1.jsonl` | 2 | `[2, 3]` | `metadata_1.json` → `{"num_jobs": 2}` |
| `requests_2.jsonl` | 1 | `[4]` | `metadata_2.json` → `{"num_jobs": 1}` |

The six stale `requests_*.jsonl` and six stale `metadata_*.json` were removed once the plan was in
hand, so the whole directory is now exactly:

```python
sorted(os.listdir(working_dir)) == [
    "batch_plan.json",
    "metadata_0.json", "metadata_1.json", "metadata_2.json",
    "requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl",
    "responses_0.jsonl",
]
open(f"{working_dir}/responses_0.jsonl").read() == "keep\n"
```

and `json.load(open(f"{working_dir}/batch_plan.json"))` is exactly:

```python
{
    "plan_format_version": 1,
    "plan_id": "f4b1ea1573c0",
    "limits": {"max_requests_per_batch": 3, "max_bytes_per_batch": 400, "max_batches_per_plan": 512},
    "num_batches": 3,
    "num_requests": 5,
    "num_bytes": 767,
    "batches": [
        {"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307},
        {"index": 1, "start_idx": 2, "end_idx": 4, "num_requests": 2, "num_bytes": 307},
        {"index": 2, "start_idx": 4, "end_idx": 5, "num_requests": 1, "num_bytes": 153},
    ],
}
```

(`767 == 307 + 307 + 153` — the three batch files' sizes summed, not a byte count of anything on
disk. The file text ends `"]\n}\n"`.)

`create_api_specific_request_batch` was called exactly **5** times.

### The two sides now agree

```python
reqs = processor.requests_from_generic_request_file(f"{working_dir}/requests_0.jsonl", set())
len(processor.create_batch_file(reqs)) == 307      # == plan[0].num_bytes
len(processor.create_batch_file(
        processor.requests_from_generic_request_file(f"{working_dir}/requests_2.jsonl", set()))) == 153
```

and no `create_batch_file` call raises. With the pre-fix planner the same run produces a single
returned path, `plan`-equivalent batches of 2 rows (measured as 217 bytes each, so the byte budget is
spent on the wrong number), and `create_batch_file` byte counts that were never the ones planned
against.

### Oversized-row end to end

```python
big = Dataset.from_dict({"prompt": ["ok", "x" * 600, "ok"]})   # max_bytes_per_batch patched to 400
processor.create_request_files(big)
# raises SingleRequestTooLargeError(row_idx=1, size_bytes=748, limit_bytes=400)
#   - isinstance(err, ValueError) is True
#   - in a fresh working_dir: glob("requests_*.jsonl") == []
#     (nothing is written before planning completes)
```

(`748` is `payload_size_bytes` of the row‑1 API request: the 153‑byte shape above with `"say 0"`
replaced by 600 `x` characters and `custom_id` `"1"`.)

Run instead against the pre-populated `working_dir` above, plus a stale
`batch_plan.json` holding `{"plan_format_version": 1, "stale": true}`: the same
`SingleRequestTooLargeError` comes out and the directory is untouched — the sweep and the sidecar
write both sit behind a plan that never returned:

```python
sorted(os.listdir(working_dir)) == [
    "batch_plan.json",
    "metadata_0.json", "metadata_1.json", "metadata_2.json",
    "metadata_3.json", "metadata_4.json", "metadata_5.json",
    "requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl",
    "requests_3.jsonl", "requests_4.jsonl", "requests_5.jsonl",
    "responses_0.jsonl",
]
json.load(open(f"{working_dir}/batch_plan.json")) == {"plan_format_version": 1, "stale": True}
open(f"{working_dir}/requests_2.jsonl").read() == "stale\n"
```

### Empty dataset end to end

```python
processor.create_request_files(Dataset.from_dict({"prompt": []}))   # fresh working_dir
# returns []
# logs exactly one WARNING: "Batch plan is empty: dataset has 0 rows; no batches will be submitted."
# os.listdir(working_dir) == ["batch_plan.json"]
# json.load(open(f"{working_dir}/batch_plan.json")) == {
#     "plan_format_version": 1,
#     "plan_id": "e3b0c44298fc",
#     "limits": {"max_requests_per_batch": 3, "max_bytes_per_batch": 400, "max_batches_per_plan": 512},
#     "num_batches": 0, "num_requests": 0, "num_bytes": 0, "batches": [],
# }
```

(`"e3b0c44298fc"` is the first 12 characters of `sha256(b"")`, the fingerprint of the empty
canonical string.)
