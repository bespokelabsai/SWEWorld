# g1 — Batch payload planner for `batch_size="auto"`

*batch-payload-plan*

## The ticket the agent sees

Replace the ad-hoc sizing loop used by `batch_size="auto"` with a pure, testable planner. Add `src/bespokelabs/curator/request_processor/batch_payload_planner.py` exporting: `@dataclass(frozen=True) class BatchLimits` with fields `max_requests_per_batch: int` and `max_bytes_per_batch: int`; `@dataclass(frozen=True) class PlannedBatch` with fields `index: int`, `start_idx: int`, `end_idx: int`, `num_requests: int`, `num_bytes: int`; `def payload_size_bytes(api_specific_request: dict) -> int` returning `len(json.dumps(d).encode())`; `def payload_bytes(sizes: Sequence[int]) -> int` returning the exact size of the `"\n".join(...)` file those payloads produce (`0` for an empty sequence); `def plan_batches(sizes: Sequence[int], limits: BatchLimits) -> list[PlannedBatch]` walking the sizes once in index order and greedily filling contiguous, ordered, exhaustive spans (`plan[0].start_idx == 0`, `plan[i].end_idx == plan[i+1].start_idx`, `plan[-1].end_idx == len(sizes)`), keeping a batch that lands exactly on either limit and returning `[]` for no sizes; `class BatchPayloadTooLargeError(ValueError)` with `__init__(self, *, num_requests: int, size_bytes: int, limit_bytes: int) -> None` storing those three as attributes; and `class SingleRequestTooLargeError(BatchPayloadTooLargeError)` with `__init__(self, *, row_idx: int, size_bytes: int, limit_bytes: int) -> None`, storing `row_idx` and `num_requests == 1`, raised when one request's own size exceeds `max_bytes_per_batch` (instead of today's `batch_size = 0` hang). On `BaseBatchRequestProcessor` (`request_processor/batch/base_batch_request_processor.py`) add a `batch_limits` property built from `self.max_requests_per_batch` / `self.max_bytes_per_batch`, `def measure_request_payload(self, generic_request: GenericRequest) -> int` returning `payload_size_bytes(self.create_api_specific_request_batch(generic_request))` — the provider payload that is actually submitted, not the generic request written to `requests_*.jsonl` — and `def plan_request_batches(self, dataset: "Dataset") -> list[PlannedBatch]` which builds each row through `PromptFormatter.create_generic_request(row, idx, generation_params_per_row)` with `generation_params_per_row = "generation_params" in dataset.column_names`, measures each row exactly once in index order, and returns `plan_batches(sizes, self.batch_limits)`; `create_batch_file(self, api_specific_requests: list[dict]) -> bytes` keeps its signature (return annotation corrected from `str`) and raises `BatchPayloadTooLargeError` where it raises `ValueError` today, so a planned batch's `num_bytes` equals `len(create_batch_file(...))` for that batch. In `base_request_processor.py`, delete the nested `_get_optimal_batch_size` (lines 263‑278) and the `while True` loop (lines 282‑295), drive the `"auto"` branch of `create_request_files(dataset: Optional["Dataset"]) -> list[str]` (unchanged signature) off `self.plan_request_batches(dataset)`, write each planned batch through the existing `acreate_request_file(...)` as `requests_{p.index}.jsonl` with `metadata_{p.index}.json`, and return `[os.path.join(self.working_dir, f"requests_{p.index}.jsonl") for p in plan]` — one path per planned batch, in `index` order (a 0-row dataset therefore returns `[]`). The explicit-integer `batch_size` branch (lines 297‑311) keeps its current behaviour exactly: `ceil(len(dataset) / batch_size)` fixed-width files filtered by `incomplete_files`, no byte-based resplit, no planner call. `max_requests_per_batch` / `max_bytes_per_batch`, `acreate_request_file` (metadata body `{"num_jobs": n}`) and `run_in_event_loop` are reused as-is. Tests build processors via `__new__` with `config`, `prompt_formatter`, `working_dir`, `_cost_processor` assigned by hand and patch the two limit properties with `unittest.mock.PropertyMock`; no network, no clients, no sleeps.

## Validation protocol

| condition | how it was run | expected | got |
|---|---|---|---|
| 1 · blind | `naive` reference build, free bracket | fails every hidden fact | 0 coincidence(s) |
| 2 · full spec | `oracle` reference build, free bracket | passes everything | 0 broken |
| 2 · full spec (horizon) | `fbcd0a6b` meteor (apex_arena MCP agent) | 1.0 | 1.0000 over 1 run(s) |
| 1 · blind (horizon) | `6629d4f7` meteor (apex_arena MCP agent) | < 1.0 | 0.0000 over 10 run(s), open feature built 8/10 |
| 1 · blind (horizon, opus) | `6629d4f7` meteor (apex_arena MCP agent) | < 1.0 | 0.0000 over 5 run(s), open feature built 5/5 |
| bracket (horizon) | hosted `validate -a oracle` / `-a noop` | 1.0 / 0.0 | 1.0 / 0.0 |
| 3 · ticket + clues | `c1523e97` v2, biggie-max, 5 runs | recovers the hidden facts | **0.6400** — 7 of 10 facts in the best runs, r2 complete in all 5 |
| 3 · ticket + clues (first plant) | `c1523e97` v1, cipher-omni, 10 runs | — | 0.0000; 9 of r1's 10 graded names were never said by any remark |
| 4 · clues only | not run | reconstructs | out of scope |

## Per fact

| fact | bracket | audit | spec arm | blind arm | requirement |
|---|---|---|---|---|---|
| `g1.r1.rule` | hidden | — | — | — | The planner module also records the plan it produced. `batch_payload_planner` exports `PLAN_FILE_NAME = "batch_plan.json |
| `g1.r1.scope` | hidden | — | — | — | The sidecar is written in the `"auto"` branch only, before any request file or metadata file is written, and it is writt |
| `g1.r1.exclusions_or_crossover` | hidden | — | — | — | `metadata_{i}.json` is untouched by this: its body stays exactly `{"num_jobs": n}` with no `start_idx`/`end_idx`/`num_by |
| `g1.r1.failure_behavior` | hidden | — | — | — | After `plan_batches` has built the whole plan and before it returns, `len(plan) > limits.max_batches_per_plan` raises `B |
| `g1.r1.observability` | hidden | — | — | — | Exact strings and one exact document. `plan_fingerprint([]) == "e3b0c44298fc"`; `plan_fingerprint(plan_batches([10]*7, B |
| `g1.r2.rule` | hidden | — | — | — | In the `"auto"` branch of `create_request_files`, after `plan_request_batches(dataset)` has returned and before anything |
| `g1.r2.scope` | hidden | — | — | — | Sweeping belongs to the `"auto"` branch alone. The explicit-integer `batch_size` branch does not sweep — it still relies |
| `g1.r2.exclusions_or_crossover` | hidden | — | — | — | Only those two glob patterns are removed. `responses_*.jsonl`, `*.arrow`, `batch_objects.jsonl` and every other file in  |
| `g1.r2.failure_behavior` | hidden | — | — | — | The sweep sits behind a plan that returned. If planning raises — `SingleRequestTooLargeError` or `BatchPlanTooFragmented |
| `g1.r2.observability` | hidden | — | — | — | `working_dir` pre-populated with `requests_0.jsonl … requests_5.jsonl` (each `"stale\n"`), `metadata_0.json … metadata_5 |

## What authoring cost

8 agent call(s), $12.47 of subscription usage.

| step | $ | turns | s |
|---|---|---|---|
| `author` | 2.30 | 33 | 477 |
| `build-oracle` | 1.76 | 31 | 254 |
| `split` | 0.57 | 2 | 165 |
| `build-naive` | 1.12 | 26 | 217 |
| `author-extend` | 3.49 | 33 | 692 |
| `build-oracle` | 1.73 | 25 | 274 |
| `split` | 0.69 | 2 | 139 |
| `build-naive` | 0.81 | 19 | 141 |
