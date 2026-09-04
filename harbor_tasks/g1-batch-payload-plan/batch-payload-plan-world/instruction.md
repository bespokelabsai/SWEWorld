You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Batch payload planner for `batch_size="auto"`**

The employees deferred this work or never finished it, which is why you need to implement it now.

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

## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>. Your account is `worldadmin`, password `worldadmin`; a token is readable at `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator` and its dependencies are installed in the virtualenv at `$CURATOR_VENV` (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the library and its tests. The library itself is NOT installed there — put your checkout's `src/` on `PYTHONPATH`.
- Complete this ticket to the best of your ability using every source of information you can reach: the repository's own history and issues, the company chat, the wiki, internal mail. Any of them may carry something the ticket does not say. The employees in this company may have written design docs and had conversations about design decisions for this particular task that were left out, or forgotten, when this ticket was written. You may need to search through the company's chat, wiki and mail to find them. If you find something that wasn’t included in the main ticket and differs a bit, it may have just been forgotten in the ticket, but you should go with what the corpus says as long as it was decided on. The employees may have pushed something to be done later, which is why you’re doing it now, so don’t treat that as a reason not to do it.
- Chat is at <http://chat.world.local>, the wiki at <http://docs.world.local>, webmail at <http://mail.world.local>, and the service list at <http://pass.world.local>. Gitea and Mattermost want the username `worldadmin`; BookStack and Roundcube want the email `worldadmin@world.local`.
- The wiki has a REST API — `Authorization: Token $(cat /etc/sweworld/bookstack-token)` — and `/api/search?query=...`, `/api/pages/{id}` return JSON, which is easier to read than the HTML.
- Wiki pages carry **comments**, and BookStack's search does not index them — a term that exists only in a comment returns nothing from `/api/search`. `/api/pages/{id}` returns that page's `comments` alongside its body, so a page worth reading is worth fetching whole.
- Mail is readable over **IMAP on `:143`** as `worldadmin@world.local` (password `worldadmin`; plain `imaplib.IMAP4`, plaintext auth is allowed on this port, no TLS handshake needed). The admin mailbox holds a copy of every message in the company, so `SEARCH` and `FETCH` over `INBOX` reach all of it — Roundcube at <http://mail.world.local> is that same mailbox with a browser in front of it, which is harder to read from a shell, not easier.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
