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
- `wait-for-service <name>` blocks until a service answers.

## Where the conversations are

You do not have to go looking. Every conversation in this company that bears on this ticket is listed below — 50 of them, oldest first — with exactly where it sits.

The list says **where**, and nothing else. It does not say what was said, who was right, which conversations matter most, or how they relate to each other. That is the part left to you: open them, read them together with what is around them, and work out what they mean for this ticket.

Times are the world's own timestamps (UTC), as chat and mail record them.

| # | date | time | where |
|---|---|---|---|
| 1 | 2025-01-21 | 09:14–09:28 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **emil** |
| 2 | 2025-01-21 | 13:14–13:48 | Mattermost `#engineering` — an exchange of 9 messages, opened by **emil** |
| 3 | 2025-01-21 | 15:02–15:38 | Mattermost `#releases` — an exchange of 6 messages, opened by **emil** |
| 4 | 2025-01-22 | 10:41–10:49 | Mattermost `#engineering` — an exchange of 7 messages, opened by **emil** |
| 5 | 2025-03-14 | 09:12–09:23 | Mattermost `#viewer` — an exchange of 7 messages, opened by **emil** |
| 6 | 2025-03-14 | 09:47–10:15 | Mattermost `#general` — an exchange of 6 messages, opened by **emil** |
| 7 | 2025-03-14 | 10:07–10:34 | Mattermost `#releases` — an exchange of 7 messages, opened by **emil** |
| 8 | 2025-03-14 | 10:12–10:38 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **emil** |
| 9 | 2025-03-14 | 13:12–13:49 | Mattermost `#engineering` — an exchange of 7 messages, opened by **dermot** |
| 10 | 2025-03-14 | 13:14–13:42 | Mattermost `#code-review` — an exchange of 7 messages, opened by **dario** |
| 11 | 2025-03-14 | 14:06–14:25 | Mattermost `#incidents` — an exchange of 7 messages, opened by **emil** |
| 12 | 2025-03-17 | 09:38–09:49 | Mattermost `#viewer` — an exchange of 6 messages, opened by **dario** |
| 13 | 2025-03-17 | 09:38–09:58 | Mattermost `#general` — an exchange of 7 messages, opened by **dario** |
| 14 | 2025-03-17 | 09:47–10:11 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **dario** |
| 15 | 2025-03-17 | 10:04–10:18 | Mattermost `#releases` — an exchange of 6 messages, opened by **emil** |
| 16 | 2025-03-18 | 10:07–10:24 | Mattermost `#cookbooks` — an exchange of 6 messages, opened by **emil** |
| 17 | 2025-03-18 | 10:12–10:34 | Mattermost `#general` — an exchange of 7 messages, opened by **emil** |
| 18 | 2025-03-18 | 14:09–14:29 | Mattermost `#releases` — an exchange of 7 messages, opened by **emil** |
| 19 | 2025-03-19 | 10:07–10:25 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **konrad** |
| 20 | 2025-03-19 | 13:02–13:31 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 21 | 2025-03-19 | 13:06–13:41 | Mattermost `#releases` — an exchange of 7 messages, opened by **konrad** |
| 22 | 2025-03-21 | 12:43–13:10 | Mattermost `#code-review` — an exchange of 7 messages, opened by **emil** |
| 23 | 2025-03-24 | 14:37–15:16 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **dario** |
| 24 | 2025-03-25 | 11:12–11:34 | Mattermost `#code-review` — an exchange of 7 messages, opened by **emil** |
| 25 | 2025-03-26 | 11:02–11:27 | Mattermost `#engineering` — an exchange of 7 messages, opened by **emil** |
| 26 | 2025-03-26 | 13:12–13:49 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **emil** |
| 27 | 2025-03-31 | 12:36–13:17 | Mattermost `#code-review` — an exchange of 6 messages, opened by **dario** |
| 28 | 2025-04-03 | 15:03–15:47 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **emil** |
| 29 | 2025-04-07 | 09:41–10:14 | the wiki page “Batch job status persistence across process restarts” (`docs/design/batch-job-status-persistence-across-process-restarts.md`) — an exchange of 7 **comments** opened by **emil**, not the page body |
| 30 | 2025-04-08 | 11:41–12:04 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **dermot** |
| 31 | 2025-04-08 | 13:21–13:38 | Mattermost `#code-review` — an exchange of 7 messages, opened by **konrad** |
| 32 | 2025-04-09 | 12:43–13:06 | Mattermost `#incidents` — an exchange of 7 messages, opened by **dermot** |
| 33 | 2025-04-10 | 11:03–11:31 | mail thread “sample serialized plan from the batch payload plan work” — an exchange of 7 messages from **gideon**. In `worldadmin@world.local`'s INBOX |
| 34 | 2025-04-11 | 17:02–17:38 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **konrad** |
| 35 | 2025-04-15 | 14:03–14:21 | mail thread “auto-sizing branch: sidecar on the fixed batch_size path too?” — an exchange of 7 messages from **emil**. In `worldadmin@world.local`'s INBOX |
| 36 | 2025-04-17 | 13:48–14:28 | Mattermost `#random` — an exchange of 7 messages, opened by **gideon** |
| 37 | 2025-04-17 | 15:02–15:26 | mail thread “mail: resumed batch run double-submitted ~400 requests” — an exchange of 6 messages from **gideon**. In `worldadmin@world.local`'s INBOX |
| 38 | 2025-04-18 | 11:26–11:44 | Mattermost `#incidents` — an exchange of 7 messages, opened by **nikolai** |
| 39 | 2025-04-21 | 16:43–17:07 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **dario** |
| 40 | 2025-04-22 | 10:12–10:21 | Mattermost `#viewer` — an exchange of 8 messages, opened by **emil** |
| 41 | 2025-04-23 | 17:15–17:55 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **dermot** |
| 42 | 2025-04-24 | 09:38–10:03 | Mattermost `#code-review` — an exchange of 7 messages, opened by **emil** |
| 43 | 2025-04-24 | 10:44–11:09 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **gideon** |
| 44 | 2025-05-02 | 09:14–09:41 | the wiki page “Batch job status persistence across process restarts” (`docs/design/batch-job-status-persistence-across-process-restarts.md`) — an exchange of 7 **comments** opened by **emil**, not the page body |
| 45 | 2025-05-07 | 10:09–10:26 | Mattermost `#pipeline` — an exchange of 6 messages, opened by **dermot** |
| 46 | 2025-05-08 | 09:14–09:45 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **emil** |
| 47 | 2025-05-22 | 13:38–14:09 | Mattermost `#code-review` — an exchange of 6 messages, opened by **konrad** |
| 48 | 2025-06-16 | 13:14–13:41 | Mattermost `#engineering` — an exchange of 6 messages, opened by **nikolai** |
| 49 | 2025-06-16 | 13:24–13:54 | mail thread “Week of Jun 9 recap: bulk inference fix” — an exchange of 6 messages from **emil**. In `worldadmin@world.local`'s INBOX |
| 50 | 2025-06-18 | 13:06–13:38 | Mattermost `#code-review` — an exchange of 7 messages, opened by **emil** |

A row gives the window an exchange runs in and how many messages it is — not how much is around it. A busy channel interleaves other talk with it, and a mail thread can have begun earlier and under someone else's name, so read the window and its surroundings rather than counting messages off.

A wiki **comment** is not in the page body and BookStack's search does not index it; `/api/pages/{id}` returns a page's `comments` alongside its text.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
