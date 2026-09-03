You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Batch payload planner for `batch_size="auto"`**

Replace the ad-hoc sizing loop used by `batch_size="auto"` with a pure, testable planner.

### 1. New module — `src/bespokelabs/curator/request_processor/batch_payload_planner.py`

```python
@dataclass(frozen=True)
class BatchLimits:
    max_requests_per_batch: int
    max_bytes_per_batch: int

@dataclass(frozen=True)
class PlannedBatch:
    index: int
    start_idx: int
    end_idx: int
    num_requests: int
    num_bytes: int

def payload_size_bytes(api_specific_request: dict) -> int
def payload_bytes(sizes: Sequence[int]) -> int
def plan_batches(sizes: Sequence[int], limits: BatchLimits) -> list[PlannedBatch]

class BatchPayloadTooLargeError(ValueError):
    def __init__(self, *, num_requests: int, size_bytes: int, limit_bytes: int) -> None

class SingleRequestTooLargeError(BatchPayloadTooLargeError):
    def __init__(self, *, row_idx: int, size_bytes: int, limit_bytes: int) -> None
```

- `payload_size_bytes` returns `len(json.dumps(d).encode())`.
- `payload_bytes` returns the exact size of the `"\n".join(...)` file those payloads
  produce, and `0` for an empty sequence.
- `plan_batches` walks the sizes once in index order, greedily filling spans that are
  contiguous, ordered and exhaustive:
  `plan[0].start_idx == 0`, `plan[i].end_idx == plan[i+1].start_idx`,
  `plan[-1].end_idx == len(sizes)`.
  A batch that lands exactly on either limit is kept. No sizes returns `[]`.
- `BatchPayloadTooLargeError` stores its three keyword arguments as attributes.
- `SingleRequestTooLargeError` stores `row_idx`, and `num_requests == 1`. Raise it when a
  single request's own size exceeds `max_bytes_per_batch` — today that produces
  `batch_size = 0` and hangs.

### 2. `BaseBatchRequestProcessor` — `request_processor/batch/base_batch_request_processor.py`

Add:

- a `batch_limits` property, built from `self.max_requests_per_batch` /
  `self.max_bytes_per_batch`;
- `def measure_request_payload(self, generic_request: GenericRequest) -> int`, returning
  `payload_size_bytes(self.create_api_specific_request_batch(generic_request))`. That is the
  provider payload actually submitted — **not** the generic request written to
  `requests_*.jsonl`;
- `def plan_request_batches(self, dataset: "Dataset") -> list[PlannedBatch]`, which builds
  each row through
  `PromptFormatter.create_generic_request(row, idx, generation_params_per_row)` with
  `generation_params_per_row = "generation_params" in dataset.column_names`, measures each
  row exactly once in index order, and returns `plan_batches(sizes, self.batch_limits)`.

Change:

- `create_batch_file(self, api_specific_requests: list[dict]) -> bytes` keeps its signature
  (the return annotation is corrected from `str`) and raises `BatchPayloadTooLargeError`
  where it raises `ValueError` today — so a planned batch's `num_bytes` equals
  `len(create_batch_file(...))` for that batch.

### 3. `base_request_processor.py`

Delete the nested `_get_optimal_batch_size` and the `while True` loop.

Drive the `"auto"` branch of `create_request_files(dataset: Optional["Dataset"]) -> list[str]`
(signature unchanged) off `self.plan_request_batches(dataset)`:

- write each planned batch through the existing `acreate_request_file(...)` as
  `requests_{p.index}.jsonl` with `metadata_{p.index}.json`;
- return
  `[os.path.join(self.working_dir, f"requests_{p.index}.jsonl") for p in plan]` — one path
  per planned batch, in `index` order. A 0-row dataset therefore returns `[]`.

The explicit-integer `batch_size` branch keeps its current behaviour **exactly**:
`ceil(len(dataset) / batch_size)` fixed-width files filtered by `incomplete_files`, no
byte-based resplit, no planner call.

### Constraints

- `max_requests_per_batch` / `max_bytes_per_batch` and `acreate_request_file` (metadata body
  `{"num_jobs": n}`) are reused as-is.
- Everything added here must work on a processor built without `__init__` — only `config`,
  `prompt_formatter`, `working_dir` and `_cost_processor` are set, and the two limit
  properties are patched.
- No network, no clients, no sleeps.

## Requirements settled earlier

These were agreed before the ticket was written. They are not obvious from the code, so they are repeated here in full:

1.
   - *rule*: `batch_payload_planner` exports `PLAN_FILE_NAME = "batch_plan.json"`, `PLAN_FORMAT_VERSION = 1`, `def plan_fingerprint(plan: Sequence[PlannedBatch]) -> str` and `def plan_document(plan: Sequence[PlannedBatch], limits: BatchLimits) -> dict`. `plan_fingerprint` builds the canonical string `";".join(f"{p.start_idx}-{p.end_idx}:{p.num_bytes}" for p in plan)` — spans and batch sizes only, not `index` or `num_requests` — and returns the FIRST 12 CHARACTERS of its `hashlib.sha256` hexdigest. `plan_document` returns exactly these keys in this order: `plan_format_version` (`1`), `plan_id` (`plan_fingerprint(plan)`), `limits` (`dataclasses.asdict(limits)`), `num_batches` (`len(plan)`), `num_requests` (sum of `p.num_requests`), `num_bytes` (sum of `p.num_bytes`), `batches` (`[dataclasses.asdict(p) for p in plan]`). `BatchLimits` carries a third field `max_batches_per_plan: int = _MAX_BATCHES_PER_PLAN` with the module constant `_MAX_BATCHES_PER_PLAN = 512`. In the `"auto"` branch of `create_request_files`, once `plan_request_batches` has returned, `json.dumps(plan_document(plan, self.batch_limits), indent=2) + "\n"` is written to `os.path.join(self.working_dir, PLAN_FILE_NAME)`.
   - *scope*: The sidecar is written in the `"auto"` branch only, before any request file is written, and for a 0-batch plan (empty dataset → a `batch_plan.json` with `num_batches: 0`, `num_requests: 0`, `num_bytes: 0`, `batches: []` and `plan_id` of the empty canonical string). The explicit-integer `batch_size` branch and the `dataset is None` path never write it.
   - *exclusions or crossover*: `metadata_{i}.json` is untouched by this: its body stays exactly `{"num_jobs": n}` with no `start_idx`/`end_idx`/`num_bytes` keys added.
   - *failure behavior*: `len(plan) > limits.max_batches_per_plan` raises `BatchPlanTooFragmentedError(num_batches=..., limit=...)`, exported from the same module, storing both as attributes; it subclasses `ValueError` but is NOT a `BatchPayloadTooLargeError`. `plan_batches([10]*512, BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=1000))` returns 512 batches; `[10]*513` raises with `err.num_batches == 513`, `err.limit == 512`; an explicit `BatchLimits(1, 1000, max_batches_per_plan=2)` on `[10]*3` raises with `err.num_batches == 3`, `err.limit == 2`. The per-row oversize scan runs first, so `plan_batches([10]*600 + [5000], BatchLimits(1, 1000))` raises `SingleRequestTooLargeError` with `err.row_idx == 600`.
   - *observability*: `plan_fingerprint([]) == "e3b0c44298fc"`; `plan_fingerprint(plan_batches([10]*7, BatchLimits(1000, 32))) == "ad0828fea95e"`; `plan_fingerprint([PlannedBatch(0,0,2,2,307), PlannedBatch(1,2,4,2,307), PlannedBatch(2,4,5,1,153)]) == "f4b1ea1573c0"`; the 11-batch plan of an 11-row dataset with `max_requests_per_batch` patched to `1` fingerprints `"c53f6fb95c13"`. After the 5-row OpenAI run with limits patched to `3`/`400`, `json.load(open(f"{working_dir}/batch_plan.json"))` equals exactly `{"plan_format_version": 1, "plan_id": "f4b1ea1573c0", "limits": {"max_requests_per_batch": 3, "max_bytes_per_batch": 400, "max_batches_per_plan": 512}, "num_batches": 3, "num_requests": 5, "num_bytes": 767, "batches": [{"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307}, {"index": 1, "start_idx": 2, "end_idx": 4, "num_requests": 2, "num_bytes": 307}, {"index": 2, "start_idx": 4, "end_idx": 5, "num_requests": 1, "num_bytes": 153}]}`, with the raw file text ending in `"]\n}\n"`.

2.
   - *rule*: In the `"auto"` branch of `create_request_files`, before anything new is written, every existing `requests_*.jsonl` and every existing `metadata_*.json` in `self.working_dir` is removed.
   - *scope*: Sweeping belongs to the `"auto"` branch alone. The explicit-integer `batch_size` branch does not sweep, and the `dataset is None` path does not sweep either.
   - *exclusions or crossover*: `responses_*.jsonl`, `*.arrow`, `batch_objects.jsonl` and every other file in the working directory survive byte-for-byte.
   - *failure behavior*: If planning raises — `SingleRequestTooLargeError` — the working directory is byte-for-byte what it was, stale files and all.
   - *observability*: `working_dir` pre-populated with `requests_0.jsonl … requests_5.jsonl` (each `"stale\n"`), `metadata_0.json … metadata_5.json` and `responses_0.jsonl` (`"keep\n"`). After the successful 5-row run with limits patched to `3`/`400`: `sorted(os.listdir(working_dir)) == ["batch_plan.json", "metadata_0.json", "metadata_1.json", "metadata_2.json", "requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl", "responses_0.jsonl"]` and `open(f"{working_dir}/responses_0.jsonl").read() == "keep\n"`. Against the same directory plus a stale `batch_plan.json` holding `{"plan_format_version": 1, "stale": true}`, `create_request_files(Dataset.from_dict({"prompt": ["ok", "x"*600, "ok"]}))` with `max_bytes_per_batch` patched to `400` raises `SingleRequestTooLargeError` and all 14 entries survive, with `json.load(open(f"{working_dir}/batch_plan.json")) == {"plan_format_version": 1, "stale": True}` and `open(f"{working_dir}/requests_2.jsonl").read() == "stale\n"`.

## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>. Your account is `worldadmin`, password `worldadmin`; a token is readable at `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator` and its dependencies are installed in the virtualenv at `$CURATOR_VENV` (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the library and its tests. The library itself is NOT installed there — put your checkout's `src/` on `PYTHONPATH`.
- Complete this ticket to the best of your ability using every source of information you can reach: the repository's own history and issues, the company chat, the wiki, internal mail. Any of them may carry something the ticket does not say.
- Chat is at <http://chat.world.local>, the wiki at <http://docs.world.local>, webmail at <http://mail.world.local>, and the service list at <http://pass.world.local>. Gitea and Mattermost want the username `worldadmin`; BookStack and Roundcube want the email `worldadmin@world.local`.
- The wiki has a REST API — `Authorization: Token $(cat /etc/sweworld/bookstack-token)` — and `/api/search?query=...`, `/api/pages/{id}` return JSON, which is easier to read than the HTML.
- Wiki pages carry **comments**, and BookStack's search does not index them — a term that exists only in a comment returns nothing from `/api/search`. `/api/pages/{id}` returns that page's `comments` alongside its body, so a page worth reading is worth fetching whole.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
