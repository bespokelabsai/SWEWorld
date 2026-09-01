# Clues for g1 — Batch payload planner for `batch_size="auto"`

39 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/latest`.

Clue window `2025-03-14` to `2026-01-27`; herrings before `2025-03-13`.

**Nothing here has been inserted into the corpus.** This is the plan: what each person says, where it goes, and why it belongs there.

## The task the agent is given

Replace the ad-hoc sizing loop used by `batch_size="auto"` with a pure, testable planner. Add `src/bespokelabs/curator/request_processor/batch_payload_planner.py` exporting: `@dataclass(frozen=True) class BatchLimits` with fields `max_requests_per_batch: int` and `max_bytes_per_batch: int`; `@dataclass(frozen=True) class PlannedBatch` with fields `index: int`, `start_idx: int`, `end_idx: int`, `num_requests: int`, `num_bytes: int`; `def payload_size_bytes(api_specific_request: dict) -> int` returning `len(json.dumps(d).encode())`; `def payload_bytes(sizes: Sequence[int]) -> int` returning the exact size of the `"\n".join(...)` file those payloads produce (`0` for an empty sequence); `def plan_batches(sizes: Sequence[int], limits: BatchLimits) -> list[PlannedBatch]` walking the sizes once in index order and greedily filling contiguous, ordered, exhaustive spans (`plan[0].start_idx == 0`, `plan[i].end_idx == plan[i+1].start_idx`, `plan[-1].end_idx == len(sizes)`), keeping a batch that lands exactly on either limit and returning `[]` for no sizes; `class BatchPayloadTooLargeError(ValueError)` with `__init__(self, *, num_requests: int, size_bytes: int, limit_bytes: int) -> None` storing those three as attributes; and `class SingleRequestTooLargeError(BatchPayloadTooLargeError)` with `__init__(self, *, row_idx: int, size_bytes: int, limit_bytes: int) -> None`, storing `row_idx` and `num_requests == 1`, raised when one request's own size exceeds `max_bytes_per_batch` (instead of today's `batch_size = 0` hang). On `BaseBatchRequestProcessor` (`request_processor/batch/base_batch_request_processor.py`) add a `batch_limits` property built from `self.max_requests_per_batch` / `self.max_bytes_per_batch`, `def measure_request_payload(self, generic_request: GenericRequest) -> int` returning `payload_size_bytes(self.create_api_specific_request_batch(generic_request))` — the provider payload that is actually submitted, not the generic request written to `requests_*.jsonl` — and `def plan_request_batches(self, dataset: "Dataset") -> list[PlannedBatch]` which builds each row through `PromptFormatter.create_generic_request(row, idx, generation_params_per_row)` with `generation_params_per_row = "generation_params" in dataset.column_names`, measures each row exactly once in index order, and returns `plan_batches(sizes, self.batch_limits)`; `create_batch_file(self, api_specific_requests: list[dict]) -> bytes` keeps its signature (return annotation corrected from `str`) and raises `BatchPayloadTooLargeError` where it raises `ValueError` today, so a planned batch's `num_bytes` equals `len(create_batch_file(...))` for that batch. In `base_request_processor.py`, delete the nested `_get_optimal_batch_size` (lines 263‑278) and the `while True` loop (lines 282‑295), drive the `"auto"` branch of `create_request_files(dataset: Optional["Dataset"]) -> list[str]` (unchanged signature) off `self.plan_request_batches(dataset)`, write each planned batch through the existing `acreate_request_file(...)` as `requests_{p.index}.jsonl` with `metadata_{p.index}.json`, and return `[os.path.join(self.working_dir, f"requests_{p.index}.jsonl") for p in plan]` — one path per planned batch, in `index` order (a 0-row dataset therefore returns `[]`). The explicit-integer `batch_size` branch (lines 297‑311) keeps its current behaviour exactly: `ceil(len(dataset) / batch_size)` fixed-width files filtered by `incomplete_files`, no byte-based resplit, no planner call. `max_requests_per_batch` / `max_bytes_per_batch`, `acreate_request_file` (metadata body `{"num_jobs": n}`) and `run_in_event_loop` are reused as-is. Tests build processors via `__new__` with `config`, `prompt_formatter`, `working_dir`, `_cost_processor` assigned by hand and patch the two limit properties with `unittest.mock.PropertyMock`; no network, no clients, no sleeps.

## Every remark, in the order a reader would meet them

| date | where | who | says | carries |
|---|---|---|---|---|
| 2025-01-21 | #engineering *(new)* | dario | settled then: the plan rides in metadata_{i}.json — num_jobs plus start_idx, end_idx, num_bytes per batch. no extra file, we already write that metadata per batch. | *herring* |
| 2025-01-21 | #releases *(new)* | dario | in any case the sweep is the first thing in the auto branch — clear out requests_*.jsonl and metadata_*.json on entry, then plan_request_batches runs against a clean dir | *herring* |
| 2025-01-21 | #cookbooks *(new)* | konrad | look, order in the auto branch is settled: we delete the old requests_*/metadata_* files first, plan_request_batches second. nothing new gets writen next to stale numbering. | *herring* |
| 2025-01-22 | #engineering *(new)* | konrad | Right, so metadata_0.json comes out as {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}. The span and the size both live in the per-batch metadata, that's the shape. | *herring* |
| 2025-03-14 | #code-review *(new)* | gideon | so basically auto split one job into about 2600 request files and the submit loop crawled all afernoon. past some ceiling it should refuse to plan at all, not run it. | `failure_behavior` |
| 2025-03-14 | #engineering *(new)* | konrad | Look, I seeded the dir with requests_0.jsonl through requests_5.jsonl plus matchign metadata, then let the plan make three - the listing afterwards is the assertion. | `rule`, `observability` |
| 2025-03-14 | #releases *(new)* | dario | honestly explicit batch_size=1000 should keep giving the same fixed-width files it always has, i don't want that branch picking up new behaviour off the side | `scope` |
| 2025-03-14 | #viewer *(new)* | gideon | so basically someone ran rm -f over the working dir between runs and it took responses_0.jsonl with it, so we paid twice for a batch we had already completed. | `exclusions_or_crossover`, `observability` |
| 2025-03-14 | #general *(new)* | nils | let me think through that - the .arrow shards in the working dir are the dataset itself, drop those and we re-tokenize four million rows before anything even gets submitted | `exclusions_or_crossover` |
| 2025-03-14 | #cookbooks *(new)* | nikolai | fixture pins max_bytes_per_batch to 400 and feeds a 600 char prompt so row 1 raises SingleRequestTooLargeError before anythign comes back | `observability`, `failure_behavior` |
| 2025-03-17 | #general *(new)* | nils | let me think through that - for the fixture to prove anything, batch_plan.json has to already be sitting in the dir when we start, holding a stale plan_format_version 1 body. | `observability` |
| 2025-03-19 | #pipeline *(new)* | nils | let me think — a zero row auto run leaves the working dir completely empty and my checker can't tell that from a crash. we write the file regardless, num_batches 0. | `scope`, `observability` |
| 2025-03-21 | #code-review | nils | @Emil same class of thing on my end - metadata_3.json in my working dir still reports num_jobs from the old split, and nothing in this run touched it. | `rule` |
| 2025-03-24 | #pipeline | dario | One thing that's already clear from the sketch - the online path calls create_request_files with dataset None, nothing to plan there, so we leave the working dir alone on that route. | `scope` |
| 2025-03-25 | #code-review *(new)* | konrad | Look, the plan file lands as one enourmous line, so diffing two runs is hopeless. Dump it with indent 2 and end the file with a newline. | `rule`, `observability` |
| 2025-03-26 | #engineering *(new)* | nils | spent the morning diffing two batch runs span by span just to confirm the split hadn't moved. one short comparable string per plan would have answered that in a second. | `rule` |
| 2025-03-26 | #pipeline *(new)* | dario | for the five row sample the string plan_fingerprint hashed was 0-2:307;2-4:307;4-5:153, so start-end:num_bytes per batch joined on semicolons, and it came back f4b1ea1573c0 | `rule`, `observability` |
| 2025-03-31 | #code-review | dermot | a run that raises in the estimate step and never gets a plan out the other end has no business having changed anything on disk, stale or not | `failure_behavior` |
| 2025-04-07 | page:design/batch-job-status-persistence-across-process-restarts.md | dario | worth adding to the persists-where list: the planner module holds PLAN_FILE_NAME = "batch_plan.json" next to the limits dataclass. nothing imports it from the processor yet, shape is still moving. | `rule` |
| 2025-04-08 | #code-review *(new)* | konrad | look, my except BatchPayloadTooLargeError sailed straight past BatchPlanTooFragmentedError — 513 batches, limit 512. right call though, it is its own ValueError and my handler shoud not be touching it. | `failure_behavior` |
| 2025-04-08 | #pipeline | gideon | Related-ish, I reran auto on a trimmed dataset and the submit loop picked up requests_4.jsonl and requests_5.jsonl leftover from Tuesdays bigger run, two duplicate batches. | `rule` |
| 2025-04-09 | #incidents | dario | not that i've seen. batch_objects.jsonl is unrecoverable state though, it stays put - lose it mid-poll and there's no way back to the submitted batches, they just expire provider side. | `exclusions_or_crossover` |
| 2025-04-10 | thread:new|g1.r1.l10 *(new)* | dermot | yeah — keep plan_format_version as the first key plan_document writes; a reader that cannot find it up front has no business parsing the rest. | `rule` |
| 2025-04-11 | #cookbooks | dermot | yeah. after an auto run the working directory should hold what that run actually produced, not that mixed in with leftovers from an earlier one. | `rule` |
| 2025-04-15 | thread:new|g1.r1.l14 *(new)* | konrad | Look, if a fixed batch_size run also drops a plan_id file next to the requests, my loader will read that run as auto-sized. Keep it to the auto branch. | `scope` |
| 2025-04-17 | thread:new|g1.r2.l6 *(new)* | nikolai | i'd say careful there on resume we call create_request_files with dataset=None purely to get the paths back and i'd be unhappy if that call ever started taking files away | `scope` |
| 2025-04-17 | #random | emil | not just create-on-open though - the oversized-row failure left me staring at an empty working dir, and the split that was in there beforehand was still perfectly usable | `failure_behavior` |
| 2025-04-18 | #incidents | nikolai | renumberd the batches by hand while poking at a failure and got the identical id back right call i mean the index and num_requests arent in what gets hashed | `rule` |
| 2025-04-21 | #pipeline | emil | sounds right - though the integer batch_size path leans on files from earlier runs, incomplete_files is what skips the finished ones, clear those and every resume starts from zero | `scope` |
| 2025-04-22 | #viewer *(new)* | gideon | so basically the viewer wants num_batches and the request and byte totals off the top of the file, not walking batches and summing them itself. | `rule`, `observability` |
| 2025-04-23 | #pipeline | gideon | same gap on my end - job died writing requests_3.jsonl and nothing on disk said there were supposed to be nine. plan gets written before the first request file. | `scope`, `observability` |
| 2025-04-24 | #pipeline *(new)* | gideon | so basically someone asked me how tuesday's auto run split and I had to ls the requests_*.jsonl files and re-measure every one of them. that should be sitting on disk. | `rule`, `observability` |
| 2025-05-02 | page:design/batch-job-status-persistence-across-process-restarts.md | konrad | Look, the working dir today holds more than those two: requests_*.jsonl, metadata_*.json, responses_*.jsonl, batch_objects.jsonl (submitted batch ids we poll), plus the .arrow shards for the dataset. | `exclusions_or_crossover` |
| 2025-05-07 | #pipeline *(new)* | emil | empty plan just hashes the empty string, so plan_id comes out e3b0c44298fc, first twelve of the sha256. no special case needed. | `rule`, `observability` |
| 2025-05-08 | #pipeline *(new)* | dermot | our resume path json.loads metadata_0.json and expects {"num_jobs": n} and nothing else, so please keep the span and byte fields out of that file | `exclusions_or_crossover` |
| 2025-05-21 | #code-review *(new)* | emil | nit on the plan writer - you've got the 1 inlined in three seperate spots, and PLAN_FORMAT_VERSION is sitting right above it in the same module. | `rule` |
| 2025-06-16 | thread:<178771578160.2500381.12817086076544913041@world.local> | nikolai | good that the plan file records the caps it planned under 3 requests and 400 bytes that run otherwise three batches and 767 bytes tells you nothign a month later | `rule`, `observability` |
| 2025-06-17 | #engineering *(new)* | emil | 600 rows of 10 bytes plus one 5000 byte row under a 1000 byte cap and it said too fragmented instead of naming row 600. per-row oversize reports first. | `failure_behavior` |
| 2025-06-18 | #code-review *(new)* | nikolai | test builds BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes so i dont have to construct 513 spans then asserts err.num_batches == 3 | `failure_behavior` |

## g1.r1

**The hidden requirement:**

- **rule** — `batch_payload_planner` exports `PLAN_FILE_NAME = "batch_plan.json"`, `PLAN_FORMAT_VERSION = 1`, `def plan_fingerprint(plan: Sequence[PlannedBatch]) -> str` and `def plan_document(plan: Sequence[PlannedBatch], limits: BatchLimits) -> dict`. `plan_fingerprint` builds the canonical string `";".join(f"{p.start_idx}-{p.end_idx}:{p.num_bytes}" for p in plan)` — spans and batch sizes only, not `index` or `num_requests` — and returns the FIRST 12 CHARACTERS of its `hashlib.sha256` hexdigest. `plan_document` returns exactly these keys in this order: `plan_format_version` (`1`), `plan_id` (`plan_fingerprint(plan)`), `limits` (`dataclasses.asdict(limits)`), `num_batches` (`len(plan)`), `num_requests` (sum of `p.num_requests`), `num_bytes` (sum of `p.num_bytes`), `batches` (`[dataclasses.asdict(p) for p in plan]`). `BatchLimits` carries a third field `max_batches_per_plan: int = _MAX_BATCHES_PER_PLAN` with the module constant `_MAX_BATCHES_PER_PLAN = 512`. In the `"auto"` branch of `create_request_files`, once `plan_request_batches` has returned, `json.dumps(plan_document(plan, self.batch_limits), indent=2) + "\n"` is written to `os.path.join(self.working_dir, PLAN_FILE_NAME)`.
- **scope** — The sidecar is written in the `"auto"` branch only, before any request file is written, and for a 0-batch plan (empty dataset → a `batch_plan.json` with `num_batches: 0`, `num_requests: 0`, `num_bytes: 0`, `batches: []` and `plan_id` of the empty canonical string). The explicit-integer `batch_size` branch and the `dataset is None` path never write it.
- **exclusions_or_crossover** — `metadata_{i}.json` is untouched by this: its body stays exactly `{"num_jobs": n}` with no `start_idx`/`end_idx`/`num_bytes` keys added.
- **failure_behavior** — `len(plan) > limits.max_batches_per_plan` raises `BatchPlanTooFragmentedError(num_batches=..., limit=...)`, exported from the same module, storing both as attributes; it subclasses `ValueError` but is NOT a `BatchPayloadTooLargeError`. `plan_batches([10]*512, BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=1000))` returns 512 batches; `[10]*513` raises with `err.num_batches == 513`, `err.limit == 512`; an explicit `BatchLimits(1, 1000, max_batches_per_plan=2)` on `[10]*3` raises with `err.num_batches == 3`, `err.limit == 2`. The per-row oversize scan runs first, so `plan_batches([10]*600 + [5000], BatchLimits(1, 1000))` raises `SingleRequestTooLargeError` with `err.row_idx == 600`.
- **observability** — `plan_fingerprint([]) == "e3b0c44298fc"`; `plan_fingerprint(plan_batches([10]*7, BatchLimits(1000, 32))) == "ad0828fea95e"`; `plan_fingerprint([PlannedBatch(0,0,2,2,307), PlannedBatch(1,2,4,2,307), PlannedBatch(2,4,5,1,153)]) == "f4b1ea1573c0"`; the 11-batch plan of an 11-row dataset with `max_requests_per_batch` patched to `1` fingerprints `"c53f6fb95c13"`. After the 5-row OpenAI run with limits patched to `3`/`400`, `json.load(open(f"{working_dir}/batch_plan.json"))` equals exactly `{"plan_format_version": 1, "plan_id": "f4b1ea1573c0", "limits": {"max_requests_per_batch": 3, "max_bytes_per_batch": 400, "max_batches_per_plan": 512}, "num_batches": 3, "num_requests": 5, "num_bytes": 767, "batches": [{"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307}, {"index": 1, "start_idx": 2, "end_idx": 4, "num_requests": 2, "num_bytes": 307}, {"index": 2, "start_idx": 4, "end_idx": 5, "num_requests": 1, "num_bytes": 153}]}`, with the raw file text ending in `"]\n}\n"`.

**Reversed earlier:** The plan was first folded into the existing per-batch metadata — `metadata_{i}.json` became `{"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}` — and that was reverted a week later because readers of metadata_{i}.json assumed the `{"num_jobs": n}` shape; the plan moved out into one versioned sidecar instead.

**What a reader has to infer along the way:**

- *An auto-sized run leaves one separate, indented JSON file under a fixed module-level file name in the working dir, and the existing per-batch metadata files are not extended to carry any of it.*
  - nobody says: If people keep needing the split after the fact and the per-batch metadata is off limits for it, the record has to be its own file with a name everyone can reach for.
- *The plan carries a short stable id: the first twelve characters of the sha256 hexdigest of a canonical string built from each batch's start-end span and its byte size, joined per batch, with the batch index and request counts left out.*
  - nobody says: Two runs that split the same way must produce the same token, so only the facts that define the split can go into the hashed string, and the digest is truncated to stay readable.
- *The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.*
  - nobody says: A consumer decides whether it can read the file at all, then wants the summary, and only then the detail, so the keys come in that order.
- *The file is written on the auto branch only and before any request file, and is still written when the plan came out empty; the explicit-integer branch and the dataset-is-None path never write it.*
  - nobody says: The file is the marker that the auto sizer ran and what it intended, so it must exist exactly when the auto sizer ran, including the zero-row case, and never otherwise.
- *A plan split into more batches than a configurable ceiling, defaulting to 512, is rejected with a dedicated error carrying the batch count and the ceiling, distinct from the oversize-payload errors, and checked only after the per-row oversize scan.*
  - nobody says: A run that shatters into thousands of files is a different failure from one payload being too big, so it needs its own error and must not steal the report from the row that is genuinely oversized.

**Names the tests reach for that the ticket withholds:**

- said: `BatchPlanTooFragmentedError`, `PLAN_FILE_NAME`, `PLAN_FORMAT_VERSION`, `batch_plan.json`, `batches`, `limit`, `max_batches_per_plan`, `num_batches`, `plan_document`, `plan_fingerprint`, `plan_format_version`, `plan_id`

> **Values nobody prints:** `11`, `32`, `ad0828fea95e`, `c53f6fb95c13`. Fine if the remarks say enough to compute them; check that they do.

> **Spread:** g1.r1.sc4: two remarks in #pipeline within 5 days

> **1 of 45 graded assertions are not stated outright** — 1 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g1.r1.sc1 — An auto-sized run leaves one separate, indented JSON file under a fixed module-level file name in the working dir, and the existing per-batch metadata files are not extended to carry any of it.

*Nobody says:* If people keep needing the split after the fact and the per-batch metadata is off limits for it, the record has to be its own file with a name everyone can reach for.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g1.r1.l3` — rule, observability

**konrad**, 2025-03-25, #code-review

> Look, the plan file lands as one enourmous line, so diffing two runs is hopeless. Dump it with indent 2 and end the file with a newline.

*What a reader should take from it:* the team agrees the file is dumped indented two spaces with a trailing newline

*Step it builds toward:* `g1.r1.sc1` — An auto-sized run leaves one separate, indented JSON file under a fixed module-level file name in the working dir, and the existing per-batch metadata files are not extended to carry any of it.

*Drafted as:* The plan file lands as one enormous line, so diffing two runs is hopeless. Dump it with indent 2 and end the file with a newline.

*Why there:* None of the eight rooms is chewing on a generated plan file or its serialization. The closest topically is #engineering 2025-03-19, but that day is about the api_key approach, the throttle/estimation split and PR 584 — a formatting verdict on an artifact nobody has mentioned would land cold and draw no reply. The release threads are about notes and support tables, 2025-04-03 is review-bandwidth triage, 2025-05-22 is factory-cleanup scope, 2025-06-02 is dormancy, 2026-01-22 is the README/cookbooks gap. What's missing is the review of the batch payload plan work itself on the batch-mode branch: nils puts the artifact up after PR 584 lands, konrad reads a diff of two runs and can't, and the room settles indent and trailing newline while the file's name, keys and branch are being pinned down by nils in the same thread.

*Still leaves open:* Doesn't say what the file is named, what keys it holds, or which branch produces it.

*A new conversation in #code-review on 2025-03-25:*

```
10:42  nils: the follow-up to 584 is up, it writes the batch payload plan out to disk before we submit so a run can be inspected and replayed later. mostly small, let me think through whether the env handling is right but the shape is there
10:51  konrad: i pulled it and diffed two runs to check the api_key/env change did not shift the payloads
10:52  konrad: look, the plan file lands as one enormous line so diffing two runs is hopeless. dump it with indent 2 and end the file with a newline
10:55  gideon: ya i hit the same thing last week with a different dump, honestly though one line is fine for the machine and terrible for everyone else. so basically anything we expect a human to open should be indented
11:03  nils: fair enough. that's worth documenting somewhere, i think — is this the kind of thing that belongs in the WS-047 doc or does it just live in the writer
11:09  konrad: not entirely sure. anyway the env part looked unchanged in the diff once i could actually read it, so that half is fine from my side
```

#### `g1.r1.l2` — rule

**dario**, 2025-04-07, page:design/batch-job-status-persistence-across-process-restarts.md

> worth adding to the persists-where list: the planner module holds PLAN_FILE_NAME = "batch_plan.json" next to the limits dataclass. nothing imports it from the processor yet, shape is still moving.

*What a reader should take from it:* the team agrees the file name lives in the planner module as PLAN_FILE_NAME with the value batch_plan.json

*Step it builds toward:* `g1.r1.sc1` — An auto-sized run leaves one separate, indented JSON file under a fixed module-level file name in the working dir, and the existing per-batch metadata files are not extended to carry any of it.

*Drafted as:* planner module also holds PLAN_FILE_NAME = "batch_plan.json" next to the limits dataclass; nothing imports it from the processor yet, shape is still moving.

*Why there:* The page's central section is an inventory of where batch state lives on disk and who writes it (responses file, metadata db), plus house rules about which paths may touch which store. dario's comment adds a name the inventory doesn't cover — a plan file constant that has landed in the planner module but isn't wired into the processor — which complicates the page's "two stores" framing without answering what the file contains or who writes it, which is exactly the gap the page's own owner would have to fill. dario is a plausible reporter here: elsewhere he routinely relays what he's read in code he doesn't own, hedged and unconfirmed. It is weaker than a live chat thread would be, since no planner module appears anywhere else in these documents, so it arrives with less setup than ideal.

*Still leaves open:* Doesn't say what goes in the file, who writes it, when, or how it is formatted.

*Must appear literally:* `PLAN_FILE_NAME`, `batch_plan.json`

*Goes as a comment on the real page `design/batch-job-status-persistence-across-process-restarts.md`, at: ## What persists where:*

```
# Batch job status persistence across process restarts

## The problem

When a batch run is interrupted, the restart needs to answer three questions: which requests have already been submitted, which have received responses, and which were still in flight when the process died. Right now the answer is split across two stores, and a restart that only consults one of them gets a partial picture.

This happens more than it should. The two stores have different write paths, different owners, and nothing currently enforces that a restart reads both before deciding what to do.

## What persists where

- **Responses file**, append-only, keyed by request hash
  - written by the online processor
  - an entry is appended the moment a request is accepted, not when the response arrives back
  - that ordering matters: a restart can tell which requests went out without waiting on results
- **Metadata db**, holds the batch job records: submission IDs, status, file IDs, per-row accounting
  - written exclusively by batch-mode
  - nothing else should write to it (see house rules below)

These two stores are intentionally separate in what they track. The responses file is about cache state. The meta
```

#### `g1.r1.l1` — rule, observability

**gideon**, 2025-04-24, #pipeline

> so basically someone asked me how tuesday's auto run split and I had to ls the requests_*.jsonl files and re-measure every one of them. that should be sitting on disk.

*What a reader should take from it:* the team agrees an auto run should leave a record of its split on disk

*Step it builds toward:* `g1.r1.sc1` — An auto-sized run leaves one separate, indented JSON file under a fixed module-level file name in the working dir, and the existing per-batch metadata files are not extended to carry any of it.

*Drafted as:* Someone asked how tuesday's auto run split and I had to list the requests_*.jsonl files and re-measure every one of them. That should be sitting on disk.

*Why there:* None of the listed rooms is chewing on what an auto batch run records about itself. #pipeline 2025-03-26 is closest — Emil's resume bug is literally about the request jsonl on disk disagreeing with the provider-side job — but that thread is about the contents of the file being stale, not about a run failing to record how it split, and the rest of that day is consumed by Mistral usage extraction; dropping this in would change the subject and draw no reply. #engineering 2025-04-15 and #code-review 2025-04-28 touch batch work only as PR-queue status, #random 2025-04-25 is the model-list divergence, #code-review 2025-04-04 is PR state visibility, #incidents 2025-04-11 is the post1 release, and the March threads predate this. What's missing is a short #pipeline thread a couple of days after a Tuesday auto run, where Gideon comes in annoyed that answering "how did it split" meant reconstructing it from the files, and Emil (who owns batch-mode) agrees the run should be writing that down — with the file's name and shape, and what happens to the existing per-batch metadata, left for others in the thread.

*Still leaves open:* Doesn't say what the file is called, what shape it takes, or that the per-batch metadata stays as it is.

*A new conversation in #pipeline on 2025-04-24:*

```
14:02  dermot: separate from the status tracking thing — when an auto run splits into multiple request files, is the split boundary purely the provider row limit, or does the byte cap come into it too
14:05  gideon: so basically both, whichever trips first. but honestly though the part that bugs me is nothing records which one it was. Someone asked how tuesday's auto run split and i had to list the requests_*.jsonl files and re-measure every one of them. that should be sitting on disk somwhere
14:08  emil: let me think through that. i believe the byte check happens per request as it gets appended, so the boundary lands wherever it happens to trip, not somewhere you could predict from the config. Which is sort of the whole problem with reconstructing it after
14:10  dermot: mhm. if i had to guess tuesday was the count limit and not bytes, the prompts that day were short. not entirely sure though
14:11  gideon: ya maybe, i didn't write the numbers down after i measured, um. so we're back to square one if anyone asks again
14:14  emil: anyway — was that run before or after the batch update freq fix went in? the counts in the log looked off to me and i want to rule that out first
```

> **Problems:** longer than one remark

#### `g1.r1.l4` — exclusions_or_crossover

**dermot**, 2025-05-08, #pipeline

> our resume path json.loads metadata_0.json and expects {"num_jobs": n} and nothing else, so please keep the span and byte fields out of that file

*What a reader should take from it:* the team agrees the per-batch metadata body stays exactly {"num_jobs": n}

*Step it builds toward:* `g1.r1.sc1` — An auto-sized run leaves one separate, indented JSON file under a fixed module-level file name in the working dir, and the existing per-batch metadata files are not extended to carry any of it.

*Drafted as:* our resume path json.loads metadata_0.json and expects {"num_jobs": n} and nothing else, so please keep the span and byte fields out of there.

*Why there:* The remark is a veto on a specific proposal — adding span and byte offsets to the per-batch metadata file — and no listed room has that proposal on the table. 2025-03-24 is the closest (persisting batch state for resume) but it's still arguing metadata db vs. flat file for the batch id, with no metadata_0.json and no span/byte fields in play; dermot would be objecting to something nobody said. 2025-04-08 is field-layout talk but for failed_requests.jsonl, a different file, and nikolai already owns that spec. The others don't touch resume file formats. What's missing is a #pipeline thread on the batch payload/shard layout where gideon proposes hanging per-job byte spans off the metadata file, dermot rules that file out because resume parses it strictly, and a sibling reply puts the span and byte fields in a separate per-shard index instead.

*Still leaves open:* Doesn't say where those fields should live instead, or in what form.

*Must appear literally:* `num_jobs`

*A new conversation in #pipeline on 2025-05-08:*

```
10:412  gideon: so basically for the shard layout im thinking each shard gets its own metadata file next to the request file
```

> **Problems:** longer than one remark

### g1.r1.sc2 — The plan carries a short stable id: the first twelve characters of the sha256 hexdigest of a canonical string built from each batch's start-end span and its byte size, joined per batch, with the batch index and request counts left out.

*Nobody says:* Two runs that split the same way must produce the same token, so only the facts that define the split can go into the hashed string, and the digest is truncated to stay readable.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g1.r1.l5` — rule

**nils**, 2025-03-26, #engineering

> spent the morning diffing two batch runs span by span just to confirm the split hadn't moved. one short comparable string per plan would have answered that in a second.

*What a reader should take from it:* the team agrees a plan should reduce to one short comparable string

*Step it builds toward:* `g1.r1.sc2` — The plan carries a short stable id: the first twelve characters of the sha256 hexdigest of a canonical string built from each batch's start-end span and its byte size, joined per batch, with the batch index and request counts left out.

*Drafted as:* spent the morning comparing two runs span by span to check the split hadn't moved. one short string per plan would have answered that in a second.

*Why there:* Neither room is chewing on batch plans, run-to-run determinism, or whether a split is stable. #engineering on 03-19 is entirely v0.1.21 release stability, the throttle/estimation split from the postmortem, and the api_key blocker — Nils only surfaces there to report api_key resolved and PR 584 unblocked, and a plan-fingerprint remark would change the subject and draw no reply from a room mid-argument about who owns the throttle item. #code-review on 03-24 is pure review logistics on PR 583/584 (who has what, is CI green), and Emil signs 584 off as clean the same day; a complaint about diffing two runs span by span there would read as a design conversation dropped into a queue-management thread. The remark belongs after 584 actually lands and Nils starts running Mistral batch jobs for real — the moment where verifying the split by hand becomes his morning rather than a hypothetical. That conversation isn't in the corpus yet.

*Still leaves open:* Doesn't say how the short string is computed or what goes into it.

*A new conversation in #engineering on 2025-03-26:*

```
10:38  gideon: did the mistral batch run finish clean on your side? i see two output sets in the bucket from yesterday and honestly i cant tell if they are the same work or not
10:46  nils: they are the same work, i checked. spent the morning comparing two runs from 584 span by span to convince myself the request split hadn't moved. one short string per plan would have answered that in a second
10:53  dermot: mhm. the split is deterministic given the same inputs and the same batch size, in principle at least. that said nothing writes it down anywhere you can look at afterwards, so you're stuck diffing outputs
11:01  emil: yup, and the split is exactly the thing i'd want to be able to point at when a run looks wrong. not entirely sure where it would live thoguh, the processor doesn't really have a place for that right now
11:04  gideon: so basically a hash of the plan? or um, something shorter than a hash even, just enough to compare two of them side by side
11:12  nils: something in that direction, let me think through that properly. for now the two runs did match so the processor isn't the issue, i'll keep the comparison notes in case
```

#### `g1.r1.l6` — rule, observability

**dario**, 2025-03-26, #pipeline

> for the five row sample the string plan_fingerprint hashed was 0-2:307;2-4:307;4-5:153, so start-end:num_bytes per batch joined on semicolons, and it came back f4b1ea1573c0

*What a reader should take from it:* the team agrees the hashed string is per-batch start-end:num_bytes entries joined with semicolons

*Step it builds toward:* `g1.r1.sc2` — The plan carries a short stable id: the first twelve characters of the sha256 hexdigest of a canonical string built from each batch's start-end span and its byte size, joined per batch, with the batch index and request counts left out.

*Drafted as:* for the five row sample the string plan_fingerprint hashed was 0-2:307;2-4:307;4-5:153 and it came back f4b1ea1573c0.

*Why there:* None of the eight rooms is chewing on batch payload planning. The closest, #pipeline 2025-03-24, is about persisting the provider batch job id so a restart can reattach — nobody there has raised how the dataset gets split into batches, byte budgets per batch, or any notion of a plan identity; a concrete fingerprint over start-end:num_bytes entries would arrive from nowhere and get no reaction. The others are schema_check at construction (03-14), the gemini parts key (04-01), Mistral token usage shape (03-17), failed_requests.jsonl and DeepSeek headers (04-08), PR ordering and cost columns (04-14), the metadata panel's missing directory field (04-28), and a plain PR queue (04-22) — none touch batching by size at all. What should exist is the follow-up Dario explicitly promised on 03-24 ("I'll sketch it out and bring something back to the group"): once the batch id is written to disk, a resume has to know the plan it was written against is still the same plan, which is what plan_fingerprint is for and where the exact hashed string gets pinned down.

*Still leaves open:* Doesn't say which hash, how much of the digest is kept, or what is deliberately absent from that string.

*Must appear literally:* `plan_fingerprint`, `0-2:307;2-4:307;4-5:153`, `f4b1ea1573c0`

*A new conversation in #pipeline on 2025-03-26:*

```
10:41  dario: wrote up the sketch i promised on monday for where the batch id actually gets written - short version is we drop a small json next to the response file the moment submission returns, id plus provider plus the row range it covers
10:47  dermot: so if i'm reading that right, the resume reads those files back and skips anything already submitted. what i'm less clear on is what stops it doing that against a differently batched dataset - you re-run with a changed batch size and the ranges on disk mean something else entirely
10:58  dario: yeah that came up while i was writing it, an id on disk is honestly only useful if we can tell it was written against the same split. so i added a plan_fingerprint field to the same json. for the five row sample the string hashed was 0-2:307;2-4:307;4-5:153 and it came back f4b1ea1573c0. mismatch on resume and we just discard the whole set and start over, which is not free but i think it's the best we can do
11:06  emil: let me think through that - so the byte count is in there deliberately, not just the row indices? i believe that means an edit to a row that doesn't change its length still fingerprints the same
11:14  dario: mhm, it would. i don't think the fingerprint is the right place to catch content drift though, that's a different problem and probably wants the request hash we already compute per row
11:22  dermot: yeah ok. separate thing but does any of this survive the mistral processor landing in 584, or is the on-disk layout provider specific at that point
```

#### `g1.r1.l8` — rule

**nikolai**, 2025-04-18, #incidents

> renumberd the batches by hand while poking at a failure and got the identical id back right call i mean the index and num_requests arent in what gets hashed

*What a reader should take from it:* the team agrees index and num_requests are excluded from the hashed string

*Step it builds toward:* `g1.r1.sc2` — The plan carries a short stable id: the first twelve characters of the sha256 hexdigest of a canonical string built from each batch's start-end span and its byte size, joined per batch, with the batch index and request counts left out.

*Drafted as:* renumbered the batches by hand while poking at a failure and got the identical id back. right call, the index and the request counts are not in what gets hashed.

*Why there:* That thread is already interrogating exactly what goes into the hash — nikolai asks Dario "what does the fingerprint for a run actually include?", Dario lists the fields, and then reports a stale openai batch id being re-polled after he changed the backend. Nikolai volunteering his own hand-test (renumbering batches, getting the same id back) is a direct contribution to the live question of which fields are and aren't hashed, and he's the one already pushing on it. Nobody in the room has said anything about index or num_requests yet, so it isn't redundant, and it lands right next to Dario's batch-id observation without changing the subject.

*Still leaves open:* Doesn't say what is in the hashed string, nor how it is digested or truncated.

*Goes into the real conversation in #incidents on 2025-04-18, after 11:24 dario:*

```
09:00  nikolai: code-execution is in decent shape, sandbox isolation is holding up and I've got instrumentation passing through cleanly
09:00  nikolai: Working through the last few edge cases on the telemetry side this morning
09:00  nikolai: Did anyone manage to repro the pass-rate change from Monday, or is that still sitting open?
09:15  nikolai: Actually, answering my own question, I heard Konrad tried to repro it and his second run finished in nine seconds.
10:01  nikolai: Nine seconds sounds like it just hit the cache and skipped the actual run. Is there a way to tell whether it actually executed anything or resumed fro
10:55  nikolai: @Dario Kestrel you own caching-and-resume right, what does the fingerprint for a run actually include?
10:57  dario: yeah, that's a good question
10:58  dario: The fingerprint is in my code, so broadly: prompt hash, model, generation params, provider name
10:58  dario: Do you know if Konrad had the same provider set both times, or did anything change between the two runs?
11:10  nikolai: dunno, I'd have to check with Konrad
11:24  dario: Actually I hit something related - killed a run mid-batch, switched the backend from openai to anthropic in the same script, reran, and it went straig
11:24  dario: only spotted it because the id in the log still had the openai shape on it   <-- THE REMARK GOES HERE
12:03  nikolai: So the provider name is in the fingerprint but it's not actually being used to key the cache lookup?
12:03  nikolai: Does the fingerprint pull in anything from the code executor, or is it purely the request params?
12:51  nikolai: @Dario Kestrel still curious on the fingerprint question when you get a chance
12:51  dario: The fingerprint code is mine, but I'd need to look at what code-execution is actually feeding into it before I can promise anything about how that sid
13:01  nikolai: What does code-execution actually hand off to you, do you know what the interface looks like?
```

#### `g1.r1.l7` — rule, observability

**emil**, 2025-05-07, #pipeline

> empty plan just hashes the empty string, so plan_id comes out e3b0c44298fc, first twelve of the sha256. no special case needed.

*What a reader should take from it:* the team agrees the id is the first twelve characters of the sha256 hexdigest, with no empty-plan branch

*Step it builds toward:* `g1.r1.sc2` — The plan carries a short stable id: the first twelve characters of the sha256 hexdigest of a canonical string built from each batch's start-end span and its byte size, joined per batch, with the batch index and request counts left out.

*Why there:* No listed room has ever mentioned a plan object or a plan_id. The closest, #pipeline 2025-04-23, is about the request fingerprint (prompt + generation params, model missing) and the thin persisted job record; it ends with Dario explicitly holding all hashing changes until Nikolai can give a blast-radius count. A settled decision on how a batch payload plan's id is derived would arrive from nowhere there, answer a question nobody asked, and contradict the hold. The remaining candidates are PR-state bookkeeping (#code-review 2025-03-14, 04-04, 06-16, 07-10, 2026-01-02), release notes (#releases 2025-05-30), and None-cost rendering in the viewer — none of them touch hashing at all. The conversation that should exist is the direct follow-up to Emil's own last message on Apr 23 ("We could fix the job record side independently, just write the model into the pending record"): the pending record grows into a plan, the plan needs a stable identifier so a resumed run can tell whether the plan changed, and someone asks what the id is when the plan has no batches in it.

*Still leaves open:* Doesn't say what the string looks like when there are batches, or which batch fields feed it.

*Must appear literally:* `plan_id`, `e3b0c44298fc`

*A new conversation in #pipeline on 2025-05-07:*

```
10:12  emil: picking up that job-record gap i flagged a couple weeks back — the pending record is turning into a plan of batches rather than one flat thing, so the resume path needs somethign stable to key off
10:16  dario: is a plan identified by the request file it came from, or by the actual contents? honestly if its the filename we get bitten the first time someone edits a file in place and reruns
10:23  emil: contents. let me think through that — sorted request ids joined, sha256, take the first twelve. empty plan just hashes the empty string, so plan_id comes out e3b0c44298fc, first twelve of the sha256. no special case needed.
10:27  dermot: mhm. so a zero-batch plan still gets a directory on disk, resume opens it and finds nothing to do. that said i'd want the manifest written before any submit call, not after
10:29  gideon: wait so two runs with the exact same requests land in the same dir? um is that a colision or is that the whole point tbh
10:34  dario: thats sort of the point i think, thats what makes resume free. in any case we still havent said where any of this lives on disk, i'll write something up
```

### g1.r1.sc3 — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*Nobody says:* A consumer decides whether it can read the file at all, then wants the summary, and only then the detail, so the keys come in that order.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g1.r1.l10` — rule

**dermot**, 2025-04-10, thread:new|g1.r1.l10

> yeah — keep plan_format_version as the first key plan_document writes; a reader that cannot find it up front has no business parsing the rest.

*What a reader should take from it:* the team agrees plan_document emits plan_format_version as its first key

*Step it builds toward:* `g1.r1.sc3` — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*Drafted as:* keep plan_format_version as the first key plan_document writes; a reader that cannot find it up front has no business parsing the rest.

*Why there:* None of the four mails is chewing on serialization format at all. Two are status recaps, one is a release announcement, one is about a semaphore/OOM repro under concurrent row creation. The closest, the Apr 7 weekly update, touches PR 626's metadata schema only as a line item in dermot's own status list — dropping a settled key-ordering decision into his own recap would arrive from nowhere and draw no reply. A decision about what plan_document writes first needs a thread where someone has actually proposed the plan document layout and a sibling can answer with the remaining keys and their order. That thread should be a short mail review of the batch payload plan format, kicked off by emil circulating a sample serialized plan while ws-055 sequencing was being sorted: nikolai asking whether version detection needs a full parse, emil listing the rest of the keys, dermot settling the first-key question.

*Still leaves open:* Doesn't say what the remaining keys are or in what order they follow.

*Must appear literally:* `plan_format_version`, `plan_document`

*A new thread — **sample serialized plan from the batch payload plan work**, 2025-04-10:*

```
From: emil  To: dermot, nikolai
Attaching a sample serialized plan from the batch payload plan work — this is what plan_document spits out right now for a two-provider run. It's pretty verbose, i know, but i'd rather we look at the actual bytes than argue about a schema in the abstract.

Two things i'm not entirely sure about: the ordering of the top-level keys (currently whatever the dataclass gives us), and whether the per-request entries should carry their own provider tag or inherit it. Let me think through that second one

From: nikolai  To: emil, dermot
looked at the sample

does a consumer have to parse the whole thing before it knows what format version its looking at right now the version key is buried somewhere in the middle and off the top of my head thats a problem for anything streaming

rest looks solid enough

From: dermot  To: nikolai, emil
mhm, that is the right question to ask and the answer today is yes, which is not acceptable.

keep plan_format_version as the first key plan_document writes; a reader that cannot find it up front has no business parsing the rest. this costs us nothing on the write side — we control the emitter — and it buys a consumer the ability to reject or dispatch on a partial read rather than after materialising the whole tree. that said, it only holds if we treat ordering as part of the contract rather tha

From: emil  To: dermot, nikolai
yup, sounds right. i'll get the emitter and the byte-level test in the same change so they don't drift.

leaving the provider tag alone until i've traced the retry path — will circulate the updated sample once that's settled.

```

#### `g1.r1.l11` — rule, observability

**gideon**, 2025-04-22, #viewer

> so basically the viewer wants num_batches and the request and byte totals off the top of the file, not walking batches and summing them itself.

*What a reader should take from it:* the team agrees the document carries num_batches and the request and byte totals above the per-batch list

*Step it builds toward:* `g1.r1.sc3` — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*Drafted as:* Viewer wants num_batches and the request and byte totals off the top of the file, not by walking batches and summing them itself.

*Why there:* None of the listed rooms is chewing on a batch summary file format. #incidents 04-11 mentions "viewer cleanup" only in passing as part of a post1 release note, and the live question there is whether the upgrade is optional or strongly recommended — a file-layout decision would change the subject and get no reaction. The two #code-review days are about PR 632/643 review ownership and whether 642 touches the response path; PR 643's CuratorResponse is an in-memory run-metadata wrapper, not a file the viewer reads, so folding `num_batches` into it would quietly retarget the thread. Both #pipeline days (retry semantics/sweep order, Anthropic multimodal content blocks) never touch the viewer. The remark, plus its sibling about batch entry contents and where version/id sit, is clearly one slice of a spec discussion for the batch summary file — that conversation belongs in #viewer, where the person consuming the file is complaining about having to derive totals themselves.

*Still leaves open:* Doesn't say what a batch entry contains, where the version or id sit, or which runs produce the file.

*Must appear literally:* `num_batches`, `batches`

*A new conversation in #viewer on 2025-04-22:*

```
10:41  dermot: the run view is still walking the entire per-batch list just to render the size on a run card. on the larger runs that's a visible stall, and i saw one yesterday where the totals it printed didn't match what the run actually did
10:46  gideon: ya i ran into that on the big one last week too. so basically before anyone writes the summary file we should agree what sits at the top level. Viewer wants num_batches and the request and byte totals off the top of the file, not by walking batches and summing them itself   <-- the remark
10:52  emil: so if i'm reading that right, the top of the file is the authoritative count and the per-batch entries are just detail you open when someone drills into a single run? honestly the part i'd want to nail down is what we show when a run is still in flight and the two don't line up
10:54  gideon: um ya thats the bit i dunno about yet tbh
11:03  dermot: that said, keeping them in sync is the writer's problem, which is a seperate conversation from this one. i'll go find where the run view does the summing, late night probably
```

#### `g1.r1.l9` — rule

**emil**, 2025-05-21, #code-review

> nit on the plan writer - you've got the 1 inlined in three seperate spots, and PLAN_FORMAT_VERSION is sitting right above it in the same module.

*What a reader should take from it:* the team agrees the module carries PLAN_FORMAT_VERSION and its current value is 1

*Step it builds toward:* `g1.r1.sc3` — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*Drafted as:* nit: you inlined the 1 in three places here. there's a PLAN_FORMAT_VERSION constant sitting right above it.

*Why there:* All eight listed conversations are status/triage threads — PR numbers, blockers, who owes whom a signoff — and none contains a line-level code review or a diff anyone could nit. The one place emil pastes code (05-30) is his own PR 652 error payload, and the live question there is retry semantics, not constant duplication. No listed PR plausibly contains a plan-format module (torch import guard, finetuning client, metadata-db flag, lazy batch download), and 653/663 are explicitly still unreviewed as of 05-30, so a review pass can't be backdated onto them. The remark needs a room where emil is reading a diff and its author is present to take the nit.

*Still leaves open:* Doesn't say where the version surfaces in the written file or what else the document holds.

*Must appear literally:* `PLAN_FORMAT_VERSION`

*A new conversation in #code-review on 2025-05-21:*

```
09:47  dario: pushed the batch payload plan writer last night. would be good to get eyes on it before the next cut, it's mostly the new plan module and then wiring at the edges
11:12  emil: took a proper line by line pass through it rather than the usual triage. left a few small comments, honestly nothing that i'd call blocking
11:14  emil: nit: you inlined the 1 in three places here. there's a PLAN_FORMAT_VERSION constant sitting right above it   <-- the remark
11:31  dario: mhm that tracks. i think two of those predate me pulling it out, will clean up
11:38  nikolai: does anything read these plans back yet or is it write only right now
11:52  dario: write only for the moment. the consumer side is the next PR, or at least that's the plan
```

#### `g1.r1.l12` — rule, observability

**nikolai**, 2025-06-16, thread:<178771578160.2500381.12817086076544913041@world.local>

> good that the plan file records the caps it planned under 3 requests and 400 bytes that run otherwise three batches and 767 bytes tells you nothign a month later

*What a reader should take from it:* the team agrees the document echoes the limits the plan was built under

*Step it builds toward:* `g1.r1.sc3` — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*Drafted as:* good that the file records the caps it planned under, 3 requests and 400 bytes that run. otherwise three batches and 767 bytes tells you nothing a month later.

*Why there:* This is nikolai's own recap thread, and the live item in it is Dario's multimodal Gemini batch request creation fix plus PRs 690/691 that reviewers are being told to read together. Those are exactly the batch-splitting changes where the per-batch request and byte caps live, so a reply weighing in on the plan file the splitter writes out lands in a room already chewing on it — nikolai is the one who asked people to look at both PRs at once, so him reacting to what the review turned up is natural. Nothing in the seed mail has already made the point about the file echoing its own limits.

*Still leaves open:* Doesn't say where in the document the limits sit or what the other keys are.

*Goes as a reply into the real thread "Week of Jun 9 recap: bulk inference fix":*

```
Quick recap from last week. Dario's fix in bulk-llm-inference for multimodal Gemini batch request creation is the main thing worth knowing about — it's non-trivial and the two batch-related PRs (690 and 691) are close enough in scope that whoever reviews them will want to look at both at once.

One thing I want an answer on: PR 653, the finetuning client Shreyas originally opened, has been sitting with me. I've merged main in and there's still work to do. But if we're heading into maintenance mode after 0.1.26, does this PR actually need to land, or should it just be closed? Don't want to keep carrying it if the answer is abandon.
```

### g1.r1.sc4 — The file is written on the auto branch only and before any request file, and is still written when the plan came out empty; the explicit-integer branch and the dataset-is-None path never write it.

*Nobody says:* The file is the marker that the auto sizer ran and what it intended, so it must exist exactly when the auto sizer ran, including the zero-row case, and never otherwise.

*4 remarks — 2 reporting the problem, 2 settling the design.*

#### `g1.r1.l13` — scope, observability

**nils**, 2025-03-19, #pipeline

> let me think — a zero row auto run leaves the working dir completely empty and my checker can't tell that from a crash. we write the file regardless, num_batches 0.

*What a reader should take from it:* the team agrees an empty plan still produces the file, with zero counts

*Step it builds toward:* `g1.r1.sc4` — The file is written on the auto branch only and before any request file, and is still written when the plan came out empty; the explicit-integer branch and the dataset-is-None path never write it.

*Drafted as:* zero row auto run leaves the working dir completely empty, so my checker cannot tell it from a crash. i want the file there with num_batches 0.

*Why there:* Neither listed room is anywhere near this. #pipeline on 03-17 is a single thread about the Mistral batch client's token usage shape and whether it matches what cost accounting expects — nils is blocked on PR 584 all day and nobody mentions a plan artifact, working directories, or run inspection. #code-review on 03-24 is pure review triage (who has 583, who has 584, CI flake on the colab check); a design decision about what a zero-row run writes to disk would land as a subject change and get no reply, in a channel where every message that day is about scheduling eyes on a PR. The remark also presumes a shared object — a batch plan file with num_batches in it — that has never been named in either conversation, and it presumes someone has just proposed the alternative (write nothing when there is nothing to submit) for nils to push back on. That proposal has to exist first. The conversation it belongs to is emil laying out the plan file that gets written before submission so a run can be inspected and resumed, with nils and dario poking at the edge cases; nils is the right person to raise the zero-row case because he is the one running the automated checker over working dirs.

*Still leaves open:* Doesn't say what other runs produce the file or when in the run it is written.

*Must appear literally:* `num_batches`

*A new conversation in #pipeline on 2025-03-19:*

```
11:42  emil: one thing i'm still chewing on with the batch plan file — should it get written when the request file has no rows at all, or do we just skip it. right now the code short circuits before it ever gets to the write
11:47  dario: honestly i'd lean skip? nothing to plan for. though i guess that's only clean if whatever reads it treats missing as "nothing to do"
11:53  nils: that's exactly the part that bites me. zero row auto run leaves the working dir completely empty, so my checker cannot tell it from a crash. i want the file there with num_batches 0
12:01  emil: yup, sounds right. the empty dir case is genuinely ambigous from the outside, i've hit it too when a run dies during prep
12:04  dario: that tracks. seperate q though — for the explicit invocation path does the file land before we hand anything to the provider, or after they accept? because if it's after and submission fails halfway you've got a file describing batches that half exist
12:09  emil: let me think through that one. i believe it's currently after but i'd have to go read it again, and the resume path assumes... hm
```

#### `g1.r1.l15` — scope

**dario**, 2025-03-24, #pipeline

> One thing that's already clear from the sketch - the online path calls create_request_files with dataset None, nothing to plan there, so we leave the working dir alone on that route.

*What a reader should take from it:* the team agrees the dataset-is-None path writes no such file

*Step it builds toward:* `g1.r1.sc4` — The file is written on the auto branch only and before any request file, and is still written when the plan came out empty; the explicit-integer branch and the dataset-is-None path never write it.

*Drafted as:* the online path calls create_request_files with dataset None and there is nothing to plan there, so leave the working dir alone on that route.

*Why there:* Emil's 14:04 question ("where does that file live? per-run, per-dataset?") is exactly the open question, and Dario has just taken the action to sketch it out. Scoping which routes write anything into the working dir is his to answer, and saying the online route writes nothing is a settled piece of that sketch without touching the per-run/per-dataset question Emil actually asked. It doesn't duplicate anything said — nobody has mentioned the online path or dataset=None — and it leaves open what the auto/batch path writes, which is what Emil and Dermot keep arguing about into the evening.

*Still leaves open:* Doesn't say what the auto path writes, or whether an empty dataset counts as nothing to plan.

*Must appear literally:* `create_request_files`

*Goes into the real conversation in #pipeline on 2025-03-24, after 14:35 dario:*

```
09:00  dermot: @Emil had a 40k-row anthropic batch run die on reboot this morning, and re-running the script kicked off a fresh batch instead of reattaching to the f
09:00  dermot: both are now sitting on the provider side
09:48  dermot: does the batch job id come back in the response at submission time, or is it only held in memory during the run?
10:19  dermot: is there a way to query the provider for active batch jobs, or does any recovery path have to start from a job id we already hold?
11:21  dermot: does the current implementation write the batch id anywhere after submission, or is it just held in memory?
11:50  dario: Same thing happened to me yesterday actually
11:50  dario: @Emil, does batch-mode write the job id anywhere after submission, or is it just held in memory?
12:25  emil: let me check
12:54  emil: Checked batch-mode. The job id comes back at submission time but we're only holding it in memory, nothing gets written to disk
13:37  dario: that tracks
13:44  dario: If we write the batch id to disk at submission time, a restart has something to reattach to instead of firing off a second batch.
14:04  emil: Writing the id to disk is the right call, but where does that file live?
14:04  emil: Is it per-run, per-dataset, something else?
14:35  dario: Those are good questions, I'll sketch it out and bring something back to the group   <-- THE REMARK GOES HERE
16:01  emil: In the meantime I cancelled the duplicate batch manually on the provider side
16:23  dermot: the metadata db might be a natural home for that id
17:03  dario: Lost a 12hr anthropic batch yesterday when my ssh session died and took the python process with it
17:04  dario: The id only ever existed inside that process
17:04  dario: Spent this morning reading batch ids off the provider console and pasting one into a scratch script to pull the results down - that's fine for me once
17:13  dermot: I'm not entirely sure the metadata db is the right home for this either
17:32  emil: If the job id lives in the metadata db and someone disables it (which PR 583 explicitly allows), they've lost resume on restart with no warning.
18:17  dermot: so the metadata db can't be the only place it lives if we're allowing it to be disabled
18:28  emil: Right, and a flat file or something outside the metadata db gets complicated fast if we want it to be per-run and not just a single-slot thing.
```

#### `g1.r1.l14` — scope

**konrad**, 2025-04-15, thread:new|g1.r1.l14

> Look, if a fixed batch_size run also drops a plan_id file next to the requests, my loader will read that run as auto-sized. Keep it to the auto branch.

*What a reader should take from it:* the team agrees the explicit-integer batch_size branch never writes the file

*Step it builds toward:* `g1.r1.sc4` — The file is written on the auto branch only and before any request file, and is still written when the plan came out empty; the explicit-integer branch and the dataset-is-None path never write it.

*Drafted as:* If a fixed batch_size run starts dropping a plan_id file next to the requests, my loader will read that run as auto-sized. Keep it to the auto branch.

*Why there:* All six candidates are Konrad's weekly status roundups — PR numbers, release cuts, who owns what, comms. None of them touches batch payload sizing, sidecar files, or loader behavior at all, and none contains a design thread this could answer; a sentence about the plan_id file landing in a Monday rundown would change the subject mid-list and draw no reply. Konrad is the right person to say it (he reads run output on the examples/cookbooks and viewer side, so he is the one whose loader breaks), but the room has to be the thread where the sidecar is actually being specced. What should have existed: a short mail thread in engineering, mid-April, started by whoever is writing the auto-sizing branch, proposing that a run drop a plan_id file alongside the requests file so downstream can tell how the payload was split — with the open question of whether the explicit-integer batch_size path writes one too. Konrad answers from the consumer side and closes that question; the siblings on the thread cover what the file holds, when it gets written, and the zero-row case.

*Still leaves open:* Doesn't say what the file holds, when it is written, or what happens on a zero-row auto run.

*Must appear literally:* `plan_id`

*A new thread — **auto-sizing branch: sidecar on the fixed batch_size path too?**, 2025-04-15:*

```
From: emil  To: konrad, dario, nikolai
Morning all,

I'm most of the way through the auto-sizing branch for batch payloads and there is one thing I want to settle before I go further, since it touches what downstream people see on disk rather than just our internals.

Right now when the sizer splits a submission it writes the requests file per chunk as before, and I've added a small sidecar next to each one recording which split it came from and the parameters that produced the split. The intent is that anyone reading a finished run 

From: konrad  To: emil, dario, nikolai
Look, consistency is the wrong instinct here I think.

The sidecar is not neutral information. For a reader it is the signal. If a fixed batch_size run starts dropping a plan_id file next to the requests, my loader will read that run as auto-sized, because presence of the file is exactly what it keys on, there is no other cheap way to tell from outside. So please keep it to the auto branch.

If later you want something on the fixed path too, fine, but then it needs a different name or a field in

From: emil  To: konrad, dario, nikolai
yup, that's a fair point and one i had not considered from the reader side, thanks.

On your question — effective, after clamping. the requested value is already in the run config so recording it twice seemed redundant, though i can be talked out of that if the clamp reason itself is what people want to see.

From: nikolai  To: emil, konrad, dario
effective is right

the clamp reason would be nice eventually but i'd say don't hold the branch for it, it's a one line add later

solid enough as is

```

#### `g1.r1.l16` — scope, observability

**gideon**, 2025-04-23, #pipeline

> same gap on my end - job died writing requests_3.jsonl and nothing on disk said there were supposed to be nine. plan gets written before the first request file.

*What a reader should take from it:* the team agrees the file is written before any request file

*Step it builds toward:* `g1.r1.sc4` — The file is written on the auto branch only and before any request file, and is still written when the plan came out empty; the explicit-integer branch and the dataset-is-None path never write it.

*Drafted as:* Job died writing requests_3.jsonl and nothing on disk said there were supposed to be nine of them. Write the plan out before the first request file.

*Why there:* That day is entirely about what the persisted job record fails to hold — emil's "if someone hands me a run dir I can't tell what model it went out with... I can't tell if picking it back up is safe," dermot noting the fingerprint and job record share the gap, and emil closing with the idea of fixing the job record side independently of the cache key. Gideon has been the one pushing "do we actually know, or has nobody checked" all day, so him landing a second concrete run-dir hole (nothing says how many request files were expected) plus one settled call about ordering fits the shape of the thread. It stays clear of the cache-key work everyone agreed to hold on, and it leaves open who writes the plan, what's in it, and the empty case.

*Still leaves open:* Doesn't say which branch writes it, what it contains, or what happens when there is nothing to plan.

*Goes into the real conversation in #pipeline on 2025-04-23, after 17:13 emil:*

```
09:00  dermot: bulk-llm-inference is mostly stable, few loose ends on the proivder side
09:00  dermot: multimodal-prompts is holding, nothing urgent there
09:27  gideon: Dario, does the request fingerprint factor in model at all, or is it just prompt + params?
09:35  dermot: I mean, it should be. same prompt on a different model is not the same request
11:13  gideon: yeah but do we know for sure it actually is, or is that the thing nobody's checked?
11:40  dario: Been in the caching code most of this morning looking at exactly this - from what I can see so far, model is not explicitly part of the fingerprint
11:40  dario: It hashes on promt content and the generation params that get passed in, but model comes in as its own thing and I'm not seeing it folded into the key
11:41  dario: Still working through it to make sure I'm reading that right
12:43  emil: huh
12:43  emil: that would explain a lot
13:15  gideon: If model gets added to the key, do we have any sense of how many existing cached entries would get blown away?
13:16  dario: Honestly I don't have that count, and I'd lean toward not moving on this until we do.
14:33  gideon: Is there a way to pull that count from the cache store, or does it need instrumentation first?
15:09  emil: Related: the persisted job record doesn't store the model either, just the id, the request file path, and a timestamp
15:09  emil: and this isn't the first time either, it's bitten me twice this week
15:09  emil: that's the whole record, nothing else on it
15:09  emil: so if someone hands me a run dir I can't tell what model it went out with, and that means I can't tell if picking it back up is safe
15:35  dermot: the fingerprint and the job record have the same gap
15:39  dario: I'd want @Nikolai Berresford in this before we touch anything - I dunno off the top of my head if the count is even pullable without adding instrument
16:59  gideon: Good call holding off
16:59  gideon: That's the right move
17:13  emil: We could fix the job record side independently, just write the model into the pending record without touching the cache key at all.   <-- THE REMARK GOES HERE
```

> **Problems:** longer than one remark

### g1.r1.sc5 — A plan split into more batches than a configurable ceiling, defaulting to 512, is rejected with a dedicated error carrying the batch count and the ceiling, distinct from the oversize-payload errors, and checked only after the per-row oversize scan.

*Nobody says:* A run that shatters into thousands of files is a different failure from one payload being too big, so it needs its own error and must not steal the report from the row that is genuinely oversized.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g1.r1.f1` — failure_behavior

**gideon**, 2025-03-14, #code-review

> so basically auto split one job into about 2600 request files and the submit loop crawled all afernoon. past some ceiling it should refuse to plan at all, not run it.

*What a reader should take from it:* the team agrees a plan past some batch-count ceiling should be refused rather than run

*Step it builds toward:* `g1.r1.sc5` — A plan split into more batches than a configurable ceiling, defaulting to 512, is rejected with a dedicated error carrying the batch count and the ceiling, distinct from the oversize-payload errors, and checked only after the per-row oversize scan.

*Drafted as:* Auto turned one job into about 2600 request files and the submit loop crawled all afternoon. Past some ceiling it should refuse to plan at all.

*Why there:* None of the listed rooms is chewing on batch planning or auto batch sizing, which is what this remark reports and decides on. #pipeline 2025-05-02 is on PR 632 (CLI progress update frequency) and PR 656 (Anthropic content blocks) — "batch update-freq" is a display cadence, not a batch count, so a ceiling on how many batches the planner emits would change the subject and draw no reply. #engineering 2025-03-19 is on the throttle/estimation path after the token-count fix, and the one open decision there is about who owns the postmortem item; a planner refusal rule would arrive sideways. #viewer 2025-04-03 is duplicate jobs from restarts-in-the-gap, #code-review days are PR triage, #help is the executor digest/404 forum cases, #general is status and PR backlog. The remark needs a room where someone has actually watched auto shard a job and the submit loop drag, with the people who'd agree to cap the planner.

*Still leaves open:* Doesn't say what the ceiling is, whether it can be changed, or what the failure looks like.

*A new conversation in #code-review on 2025-03-14:*

```
10:24  dermot: while i'm in the request processing cleanup, does anyone have a feel for whether the submit loop is actually slow or whether it just looks slow because of how many files it walks
10:29  emil: you mean slow per request, or slow in aggregate? those are pretty different problems. not entirely sure we've ever measured the first one
10:33  gideon: aggregate for sure. i still have the batch run from the WS-050 sweep sitting around, auto turned one job into about 2600 request files and the submit loop crawled all afternoon
so basically none of them are big, thats the thing. its just the count
honestly though past some ceiling it should just refuse to plan at all imo, not hand you 2600 things and wish you luck
10:41  dermot: mhm. that reads as a planner problem then, not a loop problem. though if i had to guess we could get some of it back with concurrency on the submit side regardless
10:47  emil: let me think through that one, i don't want to paper over the sizing with parallelism and then discover the ceiling again at 10k. anyway i'm heads down on 581 til after lunch
10:52  gideon: ya fair. i can pull the actual timings off that run later if it helps, i think i still have the logs
```

#### `g1.r1.f2` — failure_behavior

**konrad**, 2025-04-08, #code-review

> look, my except BatchPayloadTooLargeError sailed straight past BatchPlanTooFragmentedError — 513 batches, limit 512. right call though, it is its own ValueError and my handler shoud not be touching it.

*What a reader should take from it:* the team agrees the fragmentation failure is a separate ValueError, not caught as a payload-size error, and carries the count and the ceiling

*Step it builds toward:* `g1.r1.sc5` — A plan split into more batches than a configurable ceiling, defaulting to 512, is rejected with a dedicated error carrying the batch count and the ceiling, distinct from the oversize-payload errors, and checked only after the per-row oversize scan.

*Drafted as:* My except BatchPayloadTooLargeError sailed straight past BatchPlanTooFragmentedError: 513 batches, limit 512. Right call, it is its own ValueError and my handler should not touch it.

*Why there:* Nothing in the listed rooms is chewing on batch payload planning or its exception hierarchy. The closest is #code-review 2025-04-02, but that day is entirely PR 614's cancellation fix and the per-backend job ID scoping bug; a first-person report about an except clause missing BatchPlanTooFragmentedError would change the subject mid-thread and land on dermot and emil, neither of whom is anywhere near that code that day. #releases 2025-03-19 touches batch only as "gemini unicode corruption in batch output", and the rest (finetuning PRs, GEPA, cookbook verifiers, version tags) is unrelated. Konrad did say on 2025-04-02 that he hadn't started batch examples and was waiting for the API shape to settle — the natural home is a later thread where he actually starts writing against it and trips over the split limit, with dermot, who owns bulk-llm-inference and was unblocking batch testing.

*Still leaves open:* Doesn't say where 512 comes from, whether it can be overridden, or how it interacts with oversize rows.

*Must appear literally:* `BatchPlanTooFragmentedError`, `limit`, `512`, `513`

*A new conversation in #code-review on 2025-04-08:*

```
09:41  konrad: now that 614 is in I picked up the batch examples I put off last week. the plan splitter is refusing the run before anything goes out and I cant tell if that is meant to be a payload size problem or somethign else
09:47  dermot: so it's rejecting at plan time, nothing sent yet? if i had to guess that isn't size at all, it's the number of chunks the split ends up producing
09:52  konrad: right. my except BatchPayloadTooLargeError sailed straight past BatchPlanTooFragmentedError, 513 batches, limit 512. right call I think, it is its own ValueError and my handler should not touch it. anyway I widened the catch locally just to see the rest of the run
09:59  emil: let me think through that - i believe that ceiling is per provider and not something we'd want an example bumping into at all. honestly if the docs example is producing that many chunks the input we picked for it is too big, thats a separate thing from the handler
10:04  dermot: mhm. are you exercising the 614 cancellation path in the same example or keeping those apart
10:06  konrad: apart. off the top of my head cancellation needs a longer running job before it shows anything useful
```

#### `g1.r1.f4` — failure_behavior

**emil**, 2025-06-17, #engineering

> 600 rows of 10 bytes plus one 5000 byte row under a 1000 byte cap and it said too fragmented instead of naming row 600. per-row oversize reports first.

*What a reader should take from it:* the team agrees the per-row oversize check reports first, ahead of the fragmentation check

*Step it builds toward:* `g1.r1.sc5` — A plan split into more batches than a configurable ceiling, defaulting to 512, is rejected with a dedicated error carrying the batch count and the ceiling, distinct from the oversize-payload errors, and checked only after the per-row oversize scan.

*Drafted as:* 600 rows of 10 bytes plus one 5000 byte monster under a 1000 byte cap, and it told me the plan was too fragmented instead of naming row 600.

*Why there:* None of the listed rooms is chewing on batch payload planning at all, let alone the precedence of the planner's validation errors. The closest is #engineering 2025-06-13, but that thread is about whether PR 691's auto-batch trigger is a flag or detection and whether the Pydantic fix is clean across services — a size-cap/oversize-vs-fragmentation report ordering would land there as a subject change nobody picks up. #code-review 2025-05-08 is batch-adjacent but pinned to one serialization bug and one GCS path in PR 654, and Emil spends the day stuck on that, not running cap experiments. #engineering 2025-03-14 is about concurrency-driven OOM at row creation, not per-row byte caps. What's missing is the conversation where Emil actually exercises the planner's failure modes after auto-batch detection lands and the team settles which error a plan reports when a row is both oversize and the rest is fragmented.

*Still leaves open:* Doesn't say what the fragmentation ceiling is or what the error type and attributes are.

*Must appear literally:* `5000`, `1000`, `600`

*A new conversation in #engineering on 2025-06-17:*

```
10:42  nikolai: emil are the planner errors any good yet or are you still just eyeballing the output
10:51  emil: still eyeballing honestly. threw a deliberately awful plan at it this morning, 600 rows of 10 bytes plus one 5000 byte monster under a 1000 byte cap, and it told me the plan was too fragmented instead of naming row 600. which, i mean, the fragmentation is real, but its not the thing im going to go fix
10:58  dermot: if i had to guess the size validation runs per-row on the way in and the fragmentation heuristic only has the aggregate to look at afterwards. so whichever one raises first wins and it isn't the useful one
11:03  nikolai: yep thats backwards, the oversize one should surface first every time. one row you can point at beats a shape complaint
11:09  emil: sounds right. let me think through that ordering before i touch it though, i dont want to end up suppressing the fragmentation warning entirely on plans where its actually the only problem
11:14  dermot: mhm. that said the auto batch path from 691 probably wants its own pass on this anyway, it's constructing plans nobody wrote by hand
```

#### `g1.r1.f3` — failure_behavior

**nikolai**, 2025-06-18, #code-review

> test builds BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes so i dont have to construct 513 spans then asserts err.num_batches == 3

*What a reader should take from it:* the team agrees the ceiling is a third BatchLimits field named max_batches_per_plan that callers can set, and the error exposes num_batches

*Step it builds toward:* `g1.r1.sc5` — A plan split into more batches than a configurable ceiling, defaulting to 512, is rejected with a dedicated error carrying the batch count and the ceiling, distinct from the oversize-payload errors, and checked only after the per-row oversize scan.

*Drafted as:* test builds BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes so i don't have to construct 513 spans, then asserts err.num_batches == 3.

*Why there:* None of the listed rooms is chewing on batch planning internals. The closest is #code-review 2025-06-16, where PR 691 ("batch size automation") comes up — but that whole thread is about whether 691 is even write-up ready, and emil says it's still being worked; nikolai hasn't reviewed it, so a specific test-construction detail from him there would contradict the day. The other threads are release tagging, cookbook verifier paths, PR-state visibility and workstream bookkeeping — a BatchLimits assertion arrives from nowhere in all of them. What's missing is the actual review of 691 once it got its write-up: nikolai reading the planner, emil defending the ceiling, and the sibling questions (what the default is, what the error is called, whether it fires before or after oversize rows get rejected) getting settled in the same thread.

*Still leaves open:* Doesn't say what the default ceiling is, what the error is called, or when the check runs relative to oversize rows.

*Must appear literally:* `BatchLimits(1, 1000, max_batches_per_plan=2)`, `max_batches_per_plan`, `num_batches`

*A new conversation in #code-review on 2025-06-18:*

```
13:52  emil: ok 691 has a real description on it now, covers the size bucketing and how the planner walks the spans, plus test instructions at the bottom. sorry that took until now
14:07  dario: read through it. the thing i couldnt tell from the write up is whether the ceiling on batches per plan is a hard failure or just something the planner clamps down to quietly, honestly it reads either way
14:21  nikolai: its a hard failure i pulled it down and wrote a test aganist it test builds BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes so i dont have to construct 513 spans then asserts err.num_batches == 3
14:30  emil: yup thats the intent, raise rather than clamp. i believe silently clamping would be worse for whoever's calling it, we need to be intentional here about what the caller sees back
14:38  dario: that tracks. in any case i think the 513 wants to live in a constant somewhere instead of being derived in two places, not sure that belongs in this pr though
14:46  nikolai: yeah gotta think through that one solid enough otherwise ill put the rest of the comments on the PR
```

### Herrings — believed at the time, overturned later

#### `g1.r1.h1` — herring

**dario**, 2025-01-21, #engineering

> settled then: the plan rides in metadata_{i}.json — num_jobs plus start_idx, end_idx, num_bytes per batch. no extra file, we already write that metadata per batch.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* settled: the plan rides in metadata_{i}.json — num_jobs plus start_idx, end_idx, num_bytes per batch. no extra file, that metadata is already written per batch.

*Why there:* No listed room is discussing batch payload file layout or where a split plan is recorded. pipeline|2025-03-10 is on Mistral per-line usage and the zero-default fallback; code-review|2025-02-21 is the closest but concerns a single resume offset (cache vs re-derived) and is deliberately left open as a possible blocker, so a settling answer would rewrite its ending; pipeline|2025-01-24 has the right pair and the right adjacency (what survives a restart for caching-and-resume) but the artifact is the Gemini job ID, not a plan with num_jobs and per-batch byte counts. The remark needs a room where someone is actually splitting requests into per-batch payload files and asking where the plan gets written — that day is nils's Mistral batch work continuing on 2025-03-11.

*A new conversation in #engineering on 2025-01-21:*

```
11:42  nils: ran the mistral batch test I said I'd run yesterday. the request file goes over their upload limit so I had to split it into per-batch payloads, which is fine, but now there's a plan to record somewhere - how many jobs, which row range, byte count per batch. otherwise a resumed run has no idea what it was in the middle of
11:43  nils: let me think, either we drop a plan file next to the payloads or we hang it off something we already write
11:51  dario: settled: the plan rides in metadata_{i}.json - num_jobs plus start_idx, end_idx, num_bytes per batch. no extra file, that metadata is already written per batch anyway so we'd just be duplicating state we have to keep in sync   <-- the remark
11:54  gideon: ya that's better than another file honestly. two files that can disagree is just a bug waiting
12:02  nils: makes sense. that's worth documenting somewhere though because the split only kicks in above the limit, so most runs will never see it
12:09  emil: so the byte count is per batch, not cumulative? asking because I'm not entirely sure what the mistral limit counts, whether it's the raw jsonl or after whatever they do to it
```

#### `g1.r1.h2` — herring

**konrad**, 2025-01-22, #engineering

> Right, so metadata_0.json comes out as {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}. The span and the size both live in the per-batch metadata, that's the shape.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* Right, so metadata_0.json is {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}. Span and size live in the per-batch metadata. That's the shape.

*Why there:* None of the eight rooms are looking at the on-disk batch payload artifacts. The closest is #engineering 2025-01-27, where Konrad is chasing PR 403 and asks whether generation params ride on each batch item or get set once at the job level — but that thread is about param routing and cost-calc scope, and a file listing of metadata_0.json with start_idx/end_idx/num_bytes answers a question nobody in that room asked; it would land with no reaction. The two #code-review batch mentions (PR 584 factory shape on 03-13, PR 403 references) are about class structure and review scheduling, not the shape of the written files. What's missing is a thread where someone actually opens the batch working directory: Konrad, while tracing the Gemini batch path for PR 403, wants to know how a request maps back to its chunk on resume, dumps what the writer produced, and Dario (who owns the request-processing side and said params leave provider-integrations fine) confirms which fields are authoritative for the span versus what gets recomputed. That's a #pipeline conversation the week after the 01-27 thread, and it would also cover whether num_bytes is what the size cap is checked against before a chunk is closed.

*A new conversation in #engineering on 2025-01-22:*

```
10:04  dario: quick one on the batch resume path, when we pick up a run that died halfway, are we reading the request files back off disk and recounting, or is there something authoritative sitting next to them that we trust
10:09  konrad: look, I went and opened the working dir to see what the writer actually leaves per chunk.
Right, so metadata_0.json is {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}. Span and size live in the per-batch metadata. That's the shape.
whether the resume code actually reads it or just recounts, that I did not check yet
10:15  emil: let me think through that. so the reason i'd expect the size to be written down at all is the upload limit check, you don't want to stat the file again on every retry. but if it's only ever written and never read back that's dead weight
10:21  dario: mhm. i think the honest answer is nobody decided, it just got written because it was cheap to write. which is fine until the two disagree and then you have to pick one and there's no reason to prefer either
10:24  konrad: presumably the counts are fine, its the byte total I would not trust after a partial write. anyway I am back on the params routing thing, this was a detour
```


## g1.r2

**The hidden requirement:**

- **rule** — In the `"auto"` branch of `create_request_files`, before anything new is written, every existing `requests_*.jsonl` and every existing `metadata_*.json` in `self.working_dir` is removed.
- **scope** — Sweeping belongs to the `"auto"` branch alone. The explicit-integer `batch_size` branch does not sweep, and the `dataset is None` path does not sweep either.
- **exclusions_or_crossover** — `responses_*.jsonl`, `*.arrow`, `batch_objects.jsonl` and every other file in the working directory survive byte-for-byte.
- **failure_behavior** — If planning raises — `SingleRequestTooLargeError` — the working directory is byte-for-byte what it was, stale files and all.
- **observability** — `working_dir` pre-populated with `requests_0.jsonl … requests_5.jsonl` (each `"stale\n"`), `metadata_0.json … metadata_5.json` and `responses_0.jsonl` (`"keep\n"`). After the successful 5-row run with limits patched to `3`/`400`: `sorted(os.listdir(working_dir)) == ["batch_plan.json", "metadata_0.json", "metadata_1.json", "metadata_2.json", "requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl", "responses_0.jsonl"]` and `open(f"{working_dir}/responses_0.jsonl").read() == "keep\n"`. Against the same directory plus a stale `batch_plan.json` holding `{"plan_format_version": 1, "stale": true}`, `create_request_files(Dataset.from_dict({"prompt": ["ok", "x"*600, "ok"]}))` with `max_bytes_per_batch` patched to `400` raises `SingleRequestTooLargeError` and all 14 entries survive, with `json.load(open(f"{working_dir}/batch_plan.json")) == {"plan_format_version": 1, "stale": True}` and `open(f"{working_dir}/requests_2.jsonl").read() == "stale\n"`.

**Reversed earlier:** The cleanup was originally the first statement of the `"auto"` branch, run on entry before `plan_request_batches`; it was moved to after planning returns when an oversized-row failure wiped a working directory that still held usable request files.

**What a reader has to infer along the way:**

- *A fresh auto-sized run must not leave request or metadata files from any earlier run sitting in the working directory alongside the ones it just wrote.*
  - nobody says: If a shorter plan writes fewer files than last time, the only way the directory can end up holding just this run's output is if the old ones of those two kinds are taken out first.
- *Only the automatic sizing path does this; the explicit-integer batch_size path and the dataset-is-None path must behave exactly as they do today.*
  - nobody says: Both of those paths depend on files from earlier runs still being there, so whatever removes leftovers cannot be shared code that runs on entry for everyone.
- *Only those two families of files are removed; response files, arrow shards, the batch-id file and anything else in the directory are left exactly as they were.*
  - nobody says: Everything else in that directory is either paid-for output or state needed to reach in-flight work, so a sweep has to be pattern-scoped rather than a directory wipe.
- *When sizing fails and no plan comes back, the working directory must be left exactly as it was found, stale files included.*
  - nobody says: If nothing on disk changes on the failing path, the removal cannot have happened yet at the point the failure is raised.

**Names the tests reach for that the ticket withholds:**

- said: `batch_objects.jsonl`, `batch_plan.json`, `responses_0.jsonl`

> **Said outright:** every one of the 24 assertions grading this requirement rests on a remark that states it (`settled.md`).

### The remarks, by the step they build

### g1.r2.sc1 — A fresh auto-sized run must not leave request or metadata files from any earlier run sitting in the working directory alongside the ones it just wrote.

*Nobody says:* If a shorter plan writes fewer files than last time, the only way the directory can end up holding just this run's output is if the old ones of those two kinds are taken out first.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g1.r2.l4` — rule, observability

**konrad**, 2025-03-14, #engineering

> Look, I seeded the dir with requests_0.jsonl through requests_5.jsonl plus matchign metadata, then let the plan make three - the listing afterwards is the assertion.

*What a reader should take from it:* the team agrees the check is a six-stale-in, three-planned-out directory listing

*Step it builds toward:* `g1.r2.sc1` — A fresh auto-sized run must not leave request or metadata files from any earlier run sitting in the working directory alongside the ones it just wrote.

*Drafted as:* Seeded the dir with requests_0.jsonl through requests_5.jsonl plus matching metadata, then let the plan make three. The listing afterwards is the assertion.

*Why there:* Nothing in the listed rooms is chewing on batch request-file planning or how its test is set up. The nearest is #engineering 2025-03-20, but there PR 584 is Nils's, Dermot is the reviewer, and Konrad's only line of thought that day is whether to sequence PRs 565/566/579 — a fixture detail about seeded request files from Konrad would land with no one to answer it, and the sibling remark (what else the listing holds, what the failing path does) needs someone actually discussing the test with him. The other days are auth docs, o3 support tables, torch guards, stale-PR triage. The conversation that should exist is the follow-up review of PR 584 a few days later, where the batch processor's resume-over-existing-files path is the open question and Konrad has written the test for it.

*Still leaves open:* What the listing should contain beyond the three, and what happens on the failing path.

*Must appear literally:* `requests_0.jsonl`, `requests_5.jsonl`

*A new conversation in #engineering on 2025-03-14:*

```
10:42  dermot: left inline comments on 584, most of it is nits. the one i actually care about is the request dir not being empty when the processor starts
10:48  nils: that's the one i flagged too. if i'm reading it right the processor either picks up where it left off or it re-submits everything, and i'm not sure which one we're claiming. how is that covered in the tests currently
10:53  konrad: there is a resume test for exactly this. Seeded the dir with requests_0.jsonl through requests_5.jsonl plus matching metadata, then let the plan make three. the listing afterwards is the assertion   <-- the remark
11:01  dermot: so you're saying the count is the whole check, six stale plus the three new ones and nothing rewritten. yeah ok that's what i wanted to see
11:04  konrad: mhm. anyway the metadata side is not covered as well, that one i wrote off the top of my head and it is presumably thin
11:12  nils: fair enough. that's worth documenting somewhere in the processor docstring at least, otherwise the next person reads the test and assumes more than it proves
```

> **Problems:** longer than one remark

#### `g1.r2.l2` — rule

**nils**, 2025-03-21, #code-review

> @Emil same class of thing on my end - metadata_3.json in my working dir still reports num_jobs from the old split, and nothing in this run touched it.

*What a reader should take from it:* the team agrees stale metadata files also persist across auto runs and misreport

*Step it builds toward:* `g1.r2.sc1` — A fresh auto-sized run must not leave request or metadata files from any earlier run sitting in the working directory alongside the ones it just wrote.

*Drafted as:* metadata_3.json in my working dir still reports num_jobs from the old split, and nothing in this run touched it.

*Why there:* Emil has just spent 12:26–12:41 pulling at exactly this thread: which artifacts a rerun actually depends on, how request/response files and the metadata db diverge under CURATOR_CACHE_DIR, and whether "resumable" means the same thing for both halves of a run — ending on "Is that gap tracked anywhere as an issue?" Nils is the batch-mode owner in that room (PR 584, the Mistral batch processor), so a concrete instance from his own working dir — a leftover metadata_3.json reporting num_jobs from a split that no longer exists — lands as another case of the same class rather than a new subject. It doesn't duplicate anything Emil said: Emil's point is about where files live, this one is about a file that survives and lies. It also stops short of saying what should be done with it or whether request files behave the same way, which is what Emil's follow-up would naturally pick up.

*Still leaves open:* What should happen to it, and whether request files have the same problem.

*Must appear literally:* `metadata_3.json`, `num_jobs`

*Goes into the real conversation in #code-review on 2025-03-21, after 12:41 emil:*

```
09:00  nils: PR 584 (Mistral batch) is ready for review, touches batch-mode and provider integrations
09:00  nils: Not blocking a release but i'd like to settle before end of day whether we're merging this week or pushing to next
09:00  nils: @Emil is PR 585 meant to fold retry handling in with batch submission, or is that out of scope for it?
11:00  konrad: Sorry, just saw this
11:00  konrad: I've been sitting on PR 584 as well so I'm glad Nils raised it - would be good to get a decision today one way or the other
11:39  emil: @Nils that's the thing I'm not entirely sure about. Been going back and forth on whether retry handling belongs in PR 585 or stays separate, and I'd w
11:46  nils: fair enough
11:46  nils: WS-047 doesn't have a spec page on the wiki yet, couldn't find it anywhere when I looked
11:50  dario: while we're on PRs, @Emil, does PR 579 cover the same ground as PR 565 and PR 566, or are all three meant to land separately?
12:18  emil: Sent a note to Dario and Nils on the batch status persistence doc
12:18  emil: One house rule I want on record from it: for anything that only reports on the cache, connect to the metadata db with mode=ro
12:18  emil: @Nils, free this afternoon to settle the PR 584 call?
12:26  emil: The online processor appends to the responses file the moment a request is accepted, not when it comes back. That ordering was deliberate
12:26  emil: Does retry handling in PR 585 need to account for that, or is it working above that layer?
12:41  emil: A user pointed CURATOR_CACHE_DIR at /mnt/shared expecting everything a rerun needs to live under that path. Request and response files follow it, the 
12:41  emil: Is that gap tracked anywhere as an issue?   <-- THE REMARK GOES HERE
12:48  nils: @Emil yes, free this afternoon
12:48  nils: PR 584 is ready on my end, just sitting there waiting on the merge or defer call
12:48  nils: does WS-047 need a full wiki page, or is a tracked issue sufficient for defining the CI scope?
```

#### `g1.r2.l1` — rule

**gideon**, 2025-04-08, #pipeline

> Related-ish, I reran auto on a trimmed dataset and the submit loop picked up requests_4.jsonl and requests_5.jsonl leftover from Tuesdays bigger run, two duplicate batches.

*What a reader should take from it:* the team agrees leftover request files from a previous auto run get picked up as if they were current

*Step it builds toward:* `g1.r2.sc1` — A fresh auto-sized run must not leave request or metadata files from any earlier run sitting in the working directory alongside the ones it just wrote.

*Drafted as:* Reran auto on a trimmed dataset and the submit loop picked up requests_4.jsonl and requests_5.jsonl from Tuesday's bigger run. Two duplicate batches.

*Why there:* The room is already on "which leftover files in a run directory get read back on a rerun/resume" — dermot asking whether failed_requests.jsonl is consulted on a resume pass, and dario saying he isn't sure it's settled whether the resume pass should consult it at all. Gideon reporting that the submit loop consumes stale requests_N.jsonl from an earlier auto run is the same failure shape with a concrete cost (duplicate batches), and it lands on Gideon, who's in the channel and otherwise idle that morning. It complicates dario's "write-only at completion" lean without settling what to do about the old files, which is the sibling's job. The viewer 04-03 duplicates thread is about the dashboard and restarts-in-the-gap, and gideon already traced that one there, so a second unrelated duplicate mechanism would derail it rather than contribute.

*Still leaves open:* Whether the old files should be deleted, overwritten, or ignored by the submit loop, and which other files are involved.

*Must appear literally:* `requests_4.jsonl`, `requests_5.jsonl`

*Goes into the real conversation in #pipeline on 2025-04-08, after 11:39 dermot:*

```
09:00  dermot: pr 614 is mostly through, I've got the main batch cancellaton fixes in place and just want to confirm the failed_requests.jsonl shape is right before 
09:00  dermot: @Dario does failed_requests.jsonl get read back on a resume pass, or is it only written to at the end?
09:36  gideon: Batch cancellation fixes finally clearing is a good way to start the week
10:17  dermot: has anyone seen the rate limit headers coming back from deepseek behaving oddly?
10:27  dermot: anyone know if the llama4 model ids could collide with anything in the openai or deepseek registry?
11:00  gideon: @Emil can you do a quick check on the llama4 model ids against the OpenAI and DeepSeek entries in the registry?
11:21  emil: I'll check the llama4 ids against the registry this afternoon.
11:21  emil: And Dermot, yeah - I've been seeing some inconsistent behavior from the DeepSeek rate limit headers too, worth comparing notes on that.
11:37  dario: @Dermot, honestly I'd lean toward write-only at completion, but I'm not fully sure we've settled whether the resume pass should be consulting it at al
11:39  dermot: gotcha   <-- THE REMARK GOES HERE
11:54  dario: On the DeepSeek rate limit headers, are the values coming back wrong or just absent in some responses?
12:12  emil: Absent on certain responses, not wrong values - they just don't show up at all on some calls.
12:41  dermot: ws-055 has the e2e provider credentail question still open for CI - no owner and nothing decided yet
12:41  dermot: with deepseek and llama4 both landing, which provider are we targeting for the nightly smoke run?
13:00  gideon: @Emil still need the registry result back here this afternoon to close out the provider paths today.
13:45  dario: @Emil, are you getting enough runway this afternoon to close out both the registry check and the header issue, or is one of them going to slip?
14:13  emil: - Registry check on the llama4 ids against OpenAI and DeepSeek still in progress, results before end of day
- DeepSeek header issue: headers absent on
14:40  dermot: do absent rate limit headers from deepseek affect the retry logic at all, or does that layer degrade gracefully?
15:06  dario: @Emil, want to grab 15 min before end of day to go through the DeepSeek header behavior together?
15:06  dario: I want to check whether the retry layer handles absent headers cleanly before we call it
15:51  emil: Dario, yeah - let's do it, ping me when you're free.
16:00  dermot: @Dario when you're done with Emil, can you confirm whether the resume pass should be reading failed_requests.jsonl?
16:15  dario: You mean read it to skip already-failed rows, or something else?
16:16  dario: Can't fully sign off on the retry/DeepSeek header question until I've done the sync with Emil, and that's still pending.
16:16  dermot: yeah
16:17  dermot: skip already-failed rows on retry
17:12  dario: Ok, checking now whether the resume pass is actually wired to read from it
17:31  gideon: Still waiting on Emil's registry result to close out the provider paths on my end
```

> **Problems:** longer than one remark

#### `g1.r2.l3` — rule

**dermot**, 2025-04-11, #cookbooks

> yeah. after an auto run the working directory should hold what that run actually produced, not that mixed in with leftovers from an earlier one.

*What a reader should take from it:* the team agrees an auto run's output directory should reflect only that run

*Step it builds toward:* `g1.r2.sc1` — A fresh auto-sized run must not leave request or metadata files from any earlier run sitting in the working directory alongside the ones it just wrote.

*Drafted as:* i'd like the working dir after an auto run to hold what that run actually produced, not a mix of that and something older.

*Why there:* That thread is already chewing on exactly this failure: emil's `.curator_batch` file left in the working directory from an earlier run made a rerun reattach to the old job and hand back answers for the old prompts, and dermot has been pushing on what resume state does when things change between runs. He opened the thread and is the one framing what the desired behaviour is, so a stance from him on what the working directory should look like after a run lands naturally right after emil's account. Nobody has said this yet — emil describes the symptom, dario says the key goes stale, neither states what the directory ought to contain — and it stops short of which file kinds, which other paths, or when in the run the cleanup happens.

*Still leaves open:* Which file kinds that covers, whether other paths do the same, and when in the run it happens.

*Goes into the real conversation in #cookbooks on 2025-04-11, after 17:00 emil:*

```
09:00  dermot: been working on the bespoke-stratos reproduction script in examples-cookbooks and hit something I want to sort out, the script gets edited between run
09:05  dermot: if the stratos script gets edited between runs, does reattach pick up the new version or does it continue from whatever state it cached the first time
09:18  dermot: actually, answering my own question, I think reattach just continues from the cached run state, so if the script changed it's resuming the wrong job e
09:18  dermot: does the resume key include anything from the script content, or is it purely the run id?
10:18  dermot: do the input rows factor into the resume key at all, or does reattach assume they're unchanged from the first run?
11:00  dermot: @Dario, is the resume state keyed to the same fingerprint the prompt cache uses, or is it keyed independently?
11:41  dario: keyed independently, so yeah it goes stale
16:59  emil: I hit exactly this about a month ago - stashed the batch id in a .curator_batch file in the working directory, edited the prompt template, reran, and 
17:00  emil: The response cache didn't make that mistake. My file did.   <-- THE REMARK GOES HERE
17:00  dario: does it key on the input rows at all, or just the batch id?
17:01  dario: actually, does it validate anything about the rows at all on reattach, or just blindly continues?
18:22  emil: I'll check what the resume path does for online mode on my side. For whether caching-and-resume actually validates anything on reattach, @Dario that's
18:22  dario: honest answer is I'd need to pull up the code, but my guess is it doesn't touch the rows at all on reattach
18:27  dermot: issue 124 is relevant here, inspect(func) is sensitive to comments and whitespace so even a formatter run invalidates the prompt cache fingerprint
18:27  dermot: if the resume key doesn't track that, script edits are invisible to it
```

### g1.r2.sc2 — Only the automatic sizing path does this; the explicit-integer batch_size path and the dataset-is-None path must behave exactly as they do today.

*Nobody says:* Both of those paths depend on files from earlier runs still being there, so whatever removes leftovers cannot be shared code that runs on entry for everyone.

*3 remarks — 0 reporting the problem, 3 settling the design.*

#### `g1.r2.l7` — scope

**dario**, 2025-03-14, #releases

> honestly explicit batch_size=1000 should keep giving the same fixed-width files it always has, i don't want that branch picking up new behaviour off the side

*What a reader should take from it:* the team agrees the explicit-integer branch keeps today's behaviour exactly

*Step it builds toward:* `g1.r2.sc2` — Only the automatic sizing path does this; the explicit-integer batch_size path and the dataset-is-None path must behave exactly as they do today.

*Drafted as:* explicit batch_size=1000 should keep giving the same fixed-width files it always has, i don't want that branch picking up new behaviour off the side.

*Why there:* Every listed room touches batch work only as provider coverage (#pipeline 04-09), auth/resume confirmation (#pipeline 03-31), or reuse lookup (#engineering 03-25). None of them has anyone proposing that batch sizing behave differently, so a remark ring-fencing the explicit-integer path answers a question nobody in those rooms has asked and would sit there without a reply. The missing conversation is the one where the auto/derived sizing branch is put on the table in the first place — dermot landing it on bulk-llm-inference, gideon and emil asking what happens to callers who already pass a number, and dario drawing the line that the explicit path is frozen.

*Still leaves open:* Which branch is picking up new behaviour, and what that behaviour is.

*Must appear literally:* `batch_size=1000`

*A new conversation in #releases on 2025-03-14:*

```
10:42  dermot: pushed the batch sizing change on bulk-llm-inference. if the caller doesn't pass one we now derive it off the provider's request size limit instead of the hardcoded default
10:47  gideon: wait so what happens to the code that already passes a number? we have cookbooks that pass one in and the outputs get diffed downstream tbh
10:55  dario: explicit batch_size=1000 should keep giving the same fixed width files it always has, i dont want that branch picking up new behaviour off the side. the derivation is for the unset case only, at least thats how i read it
11:03  dermot: yeah, the derived path only runs when it's none. that said i should probably log which one we took, otherwise nobody can tell from the output
11:11  emil: logging it at info would help, we've had people ask why file counts moved before and there was no way to reconstruct it after the fact
11:14  gideon: ya and maybe put the number in the manifest too? i dunno if thats scope for this one
```

#### `g1.r2.l6` — scope

**nikolai**, 2025-04-17, thread:new|g1.r2.l6

> i'd say careful there on resume we call create_request_files with dataset=None purely to get the paths back and i'd be unhappy if that call ever started taking files away

*What a reader should take from it:* the team agrees the dataset-is-None call must leave the directory untouched

*Step it builds toward:* `g1.r2.sc2` — Only the automatic sizing path does this; the explicit-integer batch_size path and the dataset-is-None path must behave exactly as they do today.

*Drafted as:* on resume we call create_request_files with dataset=None purely to get the paths back, and i'd be unhappy if that call ever started taking files away.

*Why there:* The only listed place is the Docker image pinning mail, which is entirely about backend_params={'image': ...} taking a shorter create path in the docker backend and how the container runs — nothing in it touches request-file generation, resume, or on-disk working files. A line about create_request_files with dataset=None returning paths would change the subject mid-thread and get no reply from emil or dermot, which is exactly the kind of insert a reader spots. What's missing is the thread where somebody proposes making request-file setup clean up after itself: that's the room where nikolai's objection lands, and it's also where the sibling remark (the other call shapes, and which files would be at risk) has somewhere to sit. nikolai is the right person for it — he's already the one reading a backend for its call paths before reviewing, and this is the same habit applied to the batch side.

*Still leaves open:* What the other call shapes do, and which files would be at risk.

*Must appear literally:* `create_request_files`, `dataset=None`

*A new thread — **resumed batch run double-submitted ~400 requests**, 2025-04-17:*

```
From: emil  To: nikolai, dario
Hi both,

Writing this down while it is still fresh rather than leaving it in the incident channel. The run Dermot flagged on Tuesday — the one that resubmitted somehwere around 400 requests — I went through the working dir this morning and I believe what happened is the first run got killed partway through writing requests_0.jsonl, so the file ends mid object. The resume pass then read it back, counted the lines it could parse, and regenerated everything after that point, except the provider ha

From: nikolai  To: emil, dario   <-- the remark
right your reading of the incident matches mine i pulled the same file yesterday and the last line is a truncated json object about two thirds through

the underlying thing is we write straight into the request file and we do not truncate on the way in so a resumed run happily reads back whatever the interrupted one left behind and treats a partial line as a real request until it fails to parse

on the proposed fix the bit i keep snagging on is that on resume we call create_request_files with da

From: dario  To: nikolai, emil
mhm that tracks, i had forgotten the resume path leans on that function for the paths. i went and looked and there are two other callers besides those two, both in the test helpers, so the blast radius is smaller than i feared but not zero.

in any case i'd rather we not land the clearing part and the truncation part in the same pr, they fail in different ways and i want to be able to revert one without the other. happy either way on flag vs separate call, nikolai's version of it sounds like the

```

#### `g1.r2.l5` — scope

**emil**, 2025-04-21, #pipeline

> sounds right - though the integer batch_size path leans on files from earlier runs, incomplete_files is what skips the finished ones, clear those and every resume starts from zero

*What a reader should take from it:* the team agrees the explicit-integer path depends on earlier files staying put

*Step it builds toward:* `g1.r2.sc2` — Only the automatic sizing path does this; the explicit-integer batch_size path and the dataset-is-None path must behave exactly as they do today.

*Drafted as:* the integer batch_size path leans on files from earlier runs, incomplete_files is what skips the finished ones; clear those and every resume starts from zero again.

*Why there:* That thread is already about the reattach/resume path — gideon asked whether a completed batch gets re-downloaded when the file is already local, and dario closes the day saying the rewrite now skips re-download if the file's there. Emil, who's been the one asked to define what the resume path depends on, is the natural person to point out that the local files aren't incidental: the integer batch_size path is reading them, and incomplete_files is what skips the finished ones. It complicates dario's fix rather than repeating it, and it leaves open who else touches those files, which nobody in this room has raised.

*Still leaves open:* Whether anything else in the module clears files, and where such clearing would belong instead.

*Must appear literally:* `batch_size`, `incomplete_files`

*Goes into the real conversation in #pipeline on 2025-04-21, after 16:41 dario:*

```
09:00  dermot: been thinking about the job-reuse question this week
09:00  dermot: if the stored job doesn't match what we'd send today, I think we just submit a new one and eat the 24h and the cost
09:00  dermot: a duplicate batch is a few dollars; a dataset that quietly blends two configs is a trust problem
09:43  gideon: i think that's right for a full mismatch, but do we have a clear definition of what "doesn't match" means yet?
10:08  dermot: good question, I don't think that's defined anywhere yet
10:08  dermot: @Emil Brandvold can you weigh in on what keys we'd need to compare to call it a mismatch?
11:03  gideon: +1
11:42  dario: Rewrote the reattach path over the weekend, the key-mismatch and completed-batch download cases are both handled now
11:42  dario: Ready for eyes on it when Emil weighs in on the comparison keys
12:01  emil: Gotcha, let me think through the keys.
12:24  emil: Model and the prompt inputs are obvious ones, but I'm not sure where we draw the line on generation params, does a temperature difference count as a m
12:39  dermot: @Emil Brandvold can you put together a short list of what counts as a mismatch and we treat that as the spec?
12:41  emil: Will put that together this afternoon.
14:09  gideon: So the completed-batch download, that's a re-download even if the file is already local?
14:09  gideon: And for the key mismatch, it resubmits fresh, or does it error?
14:43  dario: The completed-batch path in the old code was unconditionally re-downloading regardless of whether the file was already local, that's fixed in the rewr
15:55  emil: @Dario Kestrel can you confirm how the rewrite handles the key mismatch case, fresh submission or error?
16:40  dario: Key mismatch does a fresh submission, consistent with what Dermot said earlier
16:41  dario: Completed-batch download also fixed to skip re-download if the file's already local   <-- THE REMARK GOES HERE
```

### g1.r2.sc3 — Only those two families of files are removed; response files, arrow shards, the batch-id file and anything else in the directory are left exactly as they were.

*Nobody says:* Everything else in that directory is either paid-for output or state needed to reach in-flight work, so a sweep has to be pattern-scoped rather than a directory wipe.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g1.r2.l8` — exclusions_or_crossover, observability

**gideon**, 2025-03-14, #viewer

> so basically someone ran rm -f over the working dir between runs and it took responses_0.jsonl with it, so we paid twice for a batch we had already completed.

*What a reader should take from it:* the team agrees response files in the working dir are paid output that must not be destroyed

*Step it builds toward:* `g1.r2.sc3` — Only those two families of files are removed; response files, arrow shards, the batch-id file and anything else in the directory are left exactly as they were.

*Drafted as:* Someone ran rm -f over the working dir between runs and took responses_0.jsonl with it, so we paid twice for a batch we'd already completed.

*Why there:* No listed room is discussing working-dir cleanup, cached responses, or the cost of re-running a completed batch. #pipeline 2025-04-02 is the nearest neighbour but is scoped to failure visibility (cancel_batches misuse, failed requests in jsonl via PR 614/615), not to files being deleted between runs; a re-payment anecdote there arrives from nowhere and would get no pickup from dermot or emil. #help 2025-03-27 mentions caching-and-resume only as a one-line status before the day turns entirely to executor image digests and 404 handling. The remark is a justification inside a cleanup-scoping decision, and its sibling ("what a narrower cleanup should be scoped to, which other files matter") needs the same room, which doesn't exist yet.

*Still leaves open:* What a narrower cleanup should be scoped to, and which other files matter.

*Must appear literally:* `responses_0.jsonl`

*A new conversation in #viewer on 2025-03-14:*

```
10:12  nikolai: the cleanup step between runs is taking out more than it should

was thinking we just ship it as a purge subcommand with a dry run flag so at least you see what goes
10:15  gideon: before we do that we need to be very clear what purge is allowed to touch. so basically in january someone ran rm -f over the working dir between runs and took responses_0.jsonl with it, so we paid twice for a batch we had already completed. honestly though that file is not scratch, it is the thing we bought   <-- the remark
10:19  dermot: mhm, i remember the invoice conversation

if i had to guess the dry run flag defaults to off within a week and then we're back to the same failure mode, just with a nicer name for it
10:24  emil: let me think through that. the working dir has never really distinguished between what's derived and what isn't — it's all just files sitting next to each other. not entirely sure the flag is the interesting part
10:27  nikolai: yep

ok im gonna leave the flag out of the first cut and have it just print what it would remove

the partial shard dirs are the actual thing biting people anyway
```

#### `g1.r2.l11` — exclusions_or_crossover

**nils**, 2025-03-14, #general

> let me think through that - the .arrow shards in the working dir are the dataset itself, drop those and we re-tokenize four million rows before anything even gets submitted

*What a reader should take from it:* the team agrees the arrow files in the working dir must be preserved

*Step it builds toward:* `g1.r2.sc3` — Only those two families of files are removed; response files, arrow shards, the batch-id file and anything else in the directory are left exactly as they were.

*Drafted as:* the .arrow shards in there are the dataset itself, drop those and you re-tokenize four million rows before anything even gets submitted.

*Why there:* Neither room is anywhere near this. #engineering on 03-19 is entirely v0.1.21 stability, the throttle/estimation split from the postmortem, and the api_key decision — nothing touches the batch working directory or on-disk state. #code-review on 03-24 is scheduling review of PR 583/584; Emil has already declared PR 584 "clean, good implementation", so a warning about cleanup dropping the dataset would land after the verdict, from the PR's own author, with no one having raised cleanup at all. The remark is also explicitly half of a pair — the sibling supplies whether anything currently removes the shards and what the scoped alternative is — which means it needs a thread where someone proposed clearing the working dir. That thread doesn't exist yet. It should: after PR 584 landed, Nils moves on to Mistral batch resubmission/resume, and the obvious naive fix for a stale-state resume is to wipe the working directory between attempts. That's where Emil or Dermot proposes the wipe, Nils objects on cost grounds, and the two of them land on deleting only the response/manifest files rather than everything.

*Still leaves open:* Whether anything currently removes them, and what the scoped alternative is.

*Must appear literally:* `.arrow`

*A new conversation in #general on 2025-03-14:*

```
10:14  nils: resuming the mistral batch after last night's failure is not going cleanly. it picks up the old request ids and half of them are already expired on their side, so the resubmission just errors out partway
10:17  emil: hm. is the fix here just to start from a clean slate each attempt? i beleive if you wipe the working dir between runs you dont inherit any of that stale state
10:22  nils: let me think through that. the problem is the working dir is not scratch space, the .arrow shards in there are the dataset itself, drop those and you re-tokenize four million rows before anything even gets submitted. we would be paying an hour of cpu to avoid deleting one manifest file
10:24  emil: yeah ok that's not what i had in mind, i was picturing it as purely intermediate. fair
10:26  dermot: if i had to guess the expiry window is 24h from submission, so anything from before ~9pm yesterday is gone regardless of what you do locally
10:29  gideon: so basically the resume path just never handled expired ids? tbh I think 584 assumed everything either completes or fails, not this middle thing
```

#### `g1.r2.l10` — exclusions_or_crossover

**dario**, 2025-04-09, #incidents

> not that i've seen. batch_objects.jsonl is unrecoverable state though, it stays put - lose it mid-poll and there's no way back to the submitted batches, they just expire provider side.

*What a reader should take from it:* the team agrees the batch-id file is unrecoverable state that has to stay put

*Step it builds toward:* `g1.r2.sc3` — Only those two families of files are removed; response files, arrow shards, the batch-id file and anything else in the directory are left exactly as they were.

*Drafted as:* lose batch_objects.jsonl mid-poll and there is no way back to the submitted batches, you just sit there until they expire on the provider side.

*Why there:* That room spent the whole day on exactly this failure mode: a run that died with no local record of what it had already sent, a hand-restart that duplicated a 40k-request batch, and Emil only able to cancel because he could dig batch IDs out of last night's logs. Emil closes the day pinging Dario directly about whether caching-and-resume catches an unwritable CURATOR_CACHE_DIR before submit, so Dario answering and naming the file that actually holds the batch handles is the natural next line. It complicates the cancel story (you can only cancel what you can still identify) and adds the cost — provider-side expiry — without settling what else in the cache dir matters or what might delete it. On 2025-04-03 Dario had already made the "nothing on disk knows a job was ever opened" point himself, so it would be redundant there.

*Still leaves open:* Whether anything is currently at risk of removing it, and what else in the directory is equally load-bearing.

*Must appear literally:* `batch_objects.jsonl`

*Goes into the real conversation in #incidents on 2025-04-09, after 12:41 emil:*

```
09:00  dermot: pr 614 is nearly through, just wrapping up the last edge cases on batch cancellation
09:00  dermot: should have it ready to merge this afternoon
09:00  dermot: did anyone notice the provider spend for last night's cookbook run was unusually high?
09:18  dermot: if a batch has already been submitted to the provider, is there a way to cancel it from our side?
10:18  dermot: does anyone know if the nightly cookbook run submitted two batches last night?
10:18  dermot: I'm seeing double the expected provider spend and I think it may have been restarted by hand after a crash
10:29  dermot: ok
10:29  dermot: answering my own question - dug into the logs this morning and confirmed it
10:29  dermot: the run crashed overnight, was restarted by hand, and the restart submitted a full second batch
11:27  dermot: if the cache dir is unwritable, does the run just die with no record of what it already sent to the provider?
11:41  dario: Yeah, that's the exact issue I was trying to describe from this morning's help thread. Someone had CURATOR_CACHE_DIR on a volume with 0 bytes free, an
11:42  dario: The OSError came out of the cache write, not the API client, so the run died with no local record and they just got a traceback
11:42  dario: Paid for the batch, nothing to show for it
12:11  emil: I can cancel the duplicate batch.
12:11  emil: Pulled up the batch IDs from last night's logs. Canceling the duplicate now, should be done in a few minutes.
12:39  dermot: @Emil Brandvold does a cancel stop billing on what's already queued, or are those 40k requests already charged?
12:41  emil: Duplicate batch cancelled
12:41  emil: On the billing question, I'm not sure, that's probably going to vary by provider and whether they'd processed those requests before the cancel went th
12:41  emil: @Dario Kestrel is there anything in caching-and-resume right now that catches an unwritable CURATOR_CACHE_DIR before the batch gets submitted?   <-- THE REMARK GOES HERE
```

#### `g1.r2.l9` — exclusions_or_crossover

**konrad**, 2025-05-02, page:design/batch-job-status-persistence-across-process-restarts.md

> Look, the working dir today holds more than those two: requests_*.jsonl, metadata_*.json, responses_*.jsonl, batch_objects.jsonl (submitted batch ids we poll), plus the .arrow shards for the dataset.

*What a reader should take from it:* the team agrees on what kinds of files share the working directory

*Step it builds toward:* `g1.r2.sc3` — Only those two families of files are removed; response files, arrow shards, the batch-id file and anything else in the directory are left exactly as they were.

*Drafted as:* Working dir contents as of today: requests_*.jsonl, metadata_*.json, responses_*.jsonl, batch_objects.jsonl (submitted batch ids we poll), plus the .arrow shards for the dataset.

*Why there:* The page's "What persists where" section frames restart state as two stores (responses file + metadata db) and then admits in the CURATOR_CACHE_DIR section that "resumable" means different things per half. Konrad hit exactly this in the Mar 31 notes — he wiped a run directory by hand after the job-ID scoping bug — so he is the person who has actually looked at what is sitting in that directory. Listing the real contents complicates emil's two-store picture without yet saying which files a restart must keep, which the page's open gap still leaves for someone else.

*Still leaves open:* Which of these are transient and which have to be preserved.

*Must appear literally:* `batch_objects.jsonl`, `requests_*.jsonl`, `metadata_*.json`, `responses_*.jsonl`

*Goes as a comment on the real page `design/batch-job-status-persistence-across-process-restarts.md`, at: ## What persists where:*

```
# Batch job status persistence across process restarts

## The problem

When a batch run is interrupted, the restart needs to answer three questions: which requests have already been submitted, which have received responses, and which were still in flight when the process died. Right now the answer is split across two stores, and a restart that only consults one of them gets a partial picture.

This happens more than it should. The two stores have different write paths, different owners, and nothing currently enforces that a restart reads both before deciding what to do.

## What persists where

- **Responses file**, append-only, keyed by request hash
  - written by the online processor
  - an entry is appended the moment a request is accepted, not when the response arrives back
  - that ordering matters: a restart can tell which requests went out without waiting on results
- **Metadata db**, holds the batch job records: submission IDs, status, file IDs, per-row accounting
  - written exclusively by batch-mode
  - nothing else should write to it (see house rules below)

These two stores are intentionally separate in what they track. The responses file is about cache state. The meta
```

> **Problems:** longer than one remark

### g1.r2.sc4 — When sizing fails and no plan comes back, the working directory must be left exactly as it was found, stale files included.

*Nobody says:* If nothing on disk changes on the failing path, the removal cannot have happened yet at the point the failure is raised.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g1.r2.l14` — observability, failure_behavior

**nikolai**, 2025-03-14, #cookbooks

> fixture pins max_bytes_per_batch to 400 and feeds a 600 char prompt so row 1 raises SingleRequestTooLargeError before anythign comes back

*What a reader should take from it:* the team agrees the failing fixture uses a 400-byte cap and an oversized single row

*Step it builds toward:* `g1.r2.sc4` — When sizing fails and no plan comes back, the working directory must be left exactly as it was found, stale files included.

*Drafted as:* Fixture pins max_bytes_per_batch to 400 and feeds a 600-char prompt, so row 1 raises SingleRequestTooLargeError before anything comes back.

*Why there:* None of the eight rooms is anywhere near batch payload sizing. 04-04 is PR merge-state visibility; 05-21 is agent response shape; 04-29 is num_gpus and stdout removal; 04-16 is docker image pinning and Dermot's resume-ignores-model bug; 04-11 and 05-06 are release notes; 2026-01-22 is README/examples coverage; 05-30 is the review queue plus sandbox guarantees under a caller-supplied image. A fixture pinning max_bytes_per_batch would land in any of them as a subject change with no reply. The thread that should exist: #engineering, nikolai and dario (he owns bulk-llm-inference and has already carried the batch cancellation fix and lazy batch download), triggered by a run dying on an oversized single row. Nikolai builds the minimal repro to establish the failure is per-row and not per-batch; the rest of the thread is what the request/response files on disk look like after the raise, and whether the run is resumable from that state — which is the sibling remark's territory, not this one's.

*Still leaves open:* What the directory should look like once that raise happens.

*Must appear literally:* `max_bytes_per_batch`, `400`, `SingleRequestTooLargeError`

*A new conversation in #cookbooks on 2025-03-14:*

```
10:42  dermot: so the batch run from last night died partway and the working directory doesn't really tell you which. if i had to guess it's one bad row but the state files read the same either way
10:51  nikolai: yeah i cut a small fixture for exactly that Fixture pins max_bytes_per_batch to 400 and feeds a 600-char prompt so row 1 raises SingleRequestTooLargeError before anything comes back
10:58  dermot: mhm so nothing ever hits the provider, which is why the dir looks untouched. that said i'd expect some marker on the row itself
11:06  dario: that tracks. honestly the question for me is whether we want the example to skip the row and carry on, or bail the whole submission, because the cookbook side has to show one of them
11:14  nikolai: gotta think through that one off the top of my head skip reads friendlier but then the counts lie
11:20  dario: mhm. in any case i'll leave the batch example alone until that's settled, i've got the deepseek one to finish anyway
```

#### `g1.r2.l15` — observability

**nils**, 2025-03-17, #general

> let me think through that - for the fixture to prove anything, batch_plan.json has to already be sitting in the dir when we start, holding a stale plan_format_version 1 body.

*What a reader should take from it:* the team agrees the failing fixture pre-seeds a stale plan file to check against

*Step it builds toward:* `g1.r2.sc4` — When sizing fails and no plan comes back, the working directory must be left exactly as it was found, stale files included.

*Drafted as:* for that fixture to prove anything, batch_plan.json needs to already be in the dir beforehand holding a stale plan_format_version 1 body.

*Why there:* Neither listed room is chewing on anything this touches. The 03-19 #engineering day is v0.1.21, the throttle/estimation split and the api_key decision; the 03-25 #pipeline day is Nils *removing* fixture tests from provider-integrations and collecting coverage sign-off on 584. A plan file on disk, a plan_format_version, and a failing fixture that pre-seeds a stale one appear nowhere in either — nobody has mentioned batch_plan.json, plan versioning, or reuse of a previously written plan. Dropped into 03-25 it reads as Nils changing the subject mid-review to a test nobody asked about, and it would draw no reaction. It needs a room where someone has already hit a run picking up a plan written under the old format and the team is working out how to detect it; that thread doesn't exist yet.

*Still leaves open:* What is asserted about it afterwards, and what happens to the other seeded files.

*Must appear literally:* `batch_plan.json`, `plan_format_version`

*A new conversation in #general on 2025-03-17:*

```
10:42  dario: hit something weird locally after 584 — reran a batch in a dir i'd used before and it just... submitted. no complaint, wrong layout entirely
10:43  dario: before anyone writes the detection for it, can we get a failing test first? i don't want to guess at what the check should even be looking at
10:51  nils: let me think through that. for that fixture to prove anything, batch_plan.json needs to already be in the dir beforehand holding a stale plan_format_version 1 body. otherwise the run just writes a fresh one and everything passes for the wrong reason
10:58  emil: so the fixture has to set the dir up dirty, not clean? that's the opposite of how the other batch ones are written i think
11:04  nils: yes, and honestly that's worth documenting somewhere, the dirty-dir setup is going to surprise whoever touches it next
11:09  dario: mhm. i'll take a pass at it this afternoon unless emil already has the batch fixtures open, in which case they're all yours
```

#### `g1.r2.l13` — failure_behavior

**dermot**, 2025-03-31, #code-review

> a run that raises in the estimate step and never gets a plan out the other end has no business having changed anything on disk, stale or not

*What a reader should take from it:* the team agrees a run that raises during sizing must leave the directory exactly as it found it

*Step it builds toward:* `g1.r2.sc4` — When sizing fails and no plan comes back, the working directory must be left exactly as it was found, stale files included.

*Drafted as:* a run that never got a plan out the other end has no business having changed anything on disk, stale or not.

*Why there:* That room is already arguing about exactly this: Dario's pre-flight estimate step threw FileNotFoundError on a fresh CI container, he patched it with mkdir -p in the workflow and hates that "the estimate step is the thing that creates the cache dir", and Emil counters that the code should create it on first use. Dermot opened the whole thread ("does the cache directory get created automatically or does it need to exist first?"), so him landing the rule for the failure case — estimate raises, directory untouched — is him closing his own question, and it sharpens rather than repeats Emil's point, which was about where creation belongs, not about rollback. It also leaves the success-path question (what gets written when the run does complete) open for Dario's later "fix it at the code level" pass.

*Still leaves open:* What changes on disk when the run does succeed, and which files are involved.

*Goes into the real conversation in #code-review on 2025-03-31, after 12:34 emil:*

```
09:00  dermot: pr 565 and the openai client work are in decent shape, I've got the retry logic in pr 585 under review and a few questions on the simplestrat recipe i
09:00  dermot: @Dario Kestrel did you push a new revision to pr 565 over the weekend, I'm seeing something about a moved hook and a bypass option?
09:38  dermot: @Emil Brandvold have you had a look at the latest on pr 565 yet?
09:56  dermot: does the cache directory get created automatically or does it need to exist first?
10:20  dermot: in pr 598, is the simplestrat recipe intended to replace the existing strategy or does it sit alongside?
10:50  dermot: for pr 583, if the metadata db param is disabled does it skip schema init entirely or just skip writes?
11:18  emil: not yet, pulling it up now
11:51  dario: It needs to exist first, and that's actually the thing I wanted to flag
11:51  dario: Fresh CI container, nothing has ever run in it, pre-flight estimate step threw a FileNotFoundError on the cache dir
11:51  dario: I put a mkdir -p in the workflow to unblock it, but I hate that because now the estimate step is the thing that creates the cache Second time this mon
12:34  emil: The mkdir in the workflow is the wrong home for that, if the code expects a cache dir it should create it on first use, not lean on whatever CI step h   <-- THE REMARK GOES HERE
12:54  emil: Looked at the revision, moving the hook I can live with, but I'm less sure about the bypass
12:54  emil: Whatever we name that param is going to tell users a lot about when they're supposed to use it, and right now it doesn't
14:07  dario: @Emil Brandvold do you want to land on the bypass naming before this closes today, or leave it open?
14:17  emil: I'll land on it today, give me a bit to look at the options and I'll have something by end of afternoon.
14:35  dario: Worth thinking about whether the name signals "for debugging" vs "a legitimate production option" - those would probably land differently for users
15:07  dario: Fixing the cache dir creation at the code level and landing the bypass naming in the same pass would be cleaner than two separate PRs.
```

#### `g1.r2.l12` — failure_behavior

**emil**, 2025-04-17, #random

> not just create-on-open though - the oversized-row failure left me staring at an empty working dir, and the split that was in there beforehand was still perfectly usable

*What a reader should take from it:* the team agrees a failed sizing run destroyed usable files on disk

*Step it builds toward:* `g1.r2.sc4` — When sizing fails and no plan comes back, the working directory must be left exactly as it was found, stale files included.

*Drafted as:* The oversized-row failure left me staring at an empty working dir, and the split that was in there beforehand was still perfectly usable.

*Why there:* The room is trading war stories about helper scripts that quietly wreck a run, and gideon has just tried to generalize the lesson ("any helper that touches the cache directory is a billing risk if it creates on open"). Emil is already in the thread agreeing that silent failures are the worst kind, so him supplying a second, differently-shaped case — a failed sizing run that emptied the working dir rather than created one — lands as a complication of gideon's framing rather than a subject change. Nobody has said yet that a failure destroyed usable data on disk; the existing stories are about re-sending and double-billing, so it isn't redundant.

*Still leaves open:* What should have happened instead, and which files were lost.

*Goes into the real conversation in #random on 2025-04-17, after 13:46 gideon:*

```
09:00  gideon: ok so I did something dumb last night
09:00  gideon: typo'd the path in my cache-poking script, it did a mkdir -p on the way in, and this morning's cookbook run found a fresh empty cache dir at the typo'
09:00  gideon: the script only ever wanted to count rows.
09:00  gideon: posting this so nobody else does it.
09:00  gideon: the bill is real
09:40  dermot: oh
09:40  dermot: no. mkdir -p is such a silent little monster.
10:34  gideon: Any helper that only wants to count rows should probably just fail if the directory doesn't exist.
10:50  dermot: +1
11:46  emil: I've done exactly this
11:46  emil: Different script, same outcome
12:04  emil: ugh
12:05  emil: silent failures are the worst kind
12:40  dermot: I had one go completely dark on a provider run, no status, no error, nothing
12:40  dermot: spent half a day not sure whether to resend and risk double billing or just wait and lose the window entirely
12:43  gideon: the "do I resend or do I wait" paralysis is its own special kind of terrible
12:43  gideon: did anyone actually resend in the end, or just wait it out?
13:46  gideon: so the lesson here is basically: any helper that touches the cache directory is a billing risk if it creates on open, right?   <-- THE REMARK GOES HERE
14:25  dermot: I did resend eventually
14:25  dermot: I think that's just the call with a dead batch, not much else you can do once it stops responding
14:50  gideon: did it double-bill or were you clear?
15:20  emil: The mkdir -p thing catches you the same way, the run looks totally normal from the outside until you see the bill.
15:21  dermot: provider charged for both, or our system ran it twice?
```

### Herrings — believed at the time, overturned later

#### `g1.r2.h1` — herring

**dario**, 2025-01-21, #releases

> in any case the sweep is the first thing in the auto branch — clear out requests_*.jsonl and metadata_*.json on entry, then plan_request_batches runs against a clean dir

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* the sweep is the first statement in the auto branch — clear out requests_*.jsonl and metadata_*.json on entry, then call plan_request_batches against a clean dir.

*Why there:* None of the eight rooms is chewing on batch payload files or resubmission behaviour. The two pipeline days that touch batch mode are about cost prediction (Feb 3) and async refactor / token accounting (Feb 25) — neither has anyone asking where stale request files get cleared, so a settled implementation call about sweeping requests_*.jsonl and metadata_*.json on entry to the auto branch would land with no question behind it and no reaction after it. The code-review days are pure PR triage with no code-level detail at all, and the engineering days are int wrapping and capacity throughput. dario is plausible as the person who decides this, but there is nowhere he decides it. What's missing is a #pipeline thread about a rerun picking up leftover payload files from the previous run and double-submitting — that's the question this sentence answers.

*A new conversation in #releases on 2025-01-21:*

```
10:42  gideon: so basically i reran a job from yesterday that had only half submitted and it sent the batches out twice. the requests_*.jsonl from the first run were still sitting in the working dir and it just picked them up like they were new
10:43  gideon: honestly though i didnt even notice until the cost line looked wrong
10:47  emil: so you're saying the resume path can't tell a leftover file from one it just wrote? that's... not great
10:51  dario: right, on my branch the sweep is the first statement in the auto branch - clear out requests_*.jsonl and metadata_*.json on entry, then call plan_request_batches against a clean dir. it's not subtle but honestly its the best we can do without a run id in the filename
10:53  gideon: ya ok. um does that land before 0.1.16 goes out or is it after
10:55  dario: after i think, the notes are already up
```

#### `g1.r2.h2` — herring

**konrad**, 2025-01-21, #cookbooks

> look, order in the auto branch is settled: we delete the old requests_*/metadata_* files first, plan_request_batches second. nothing new gets writen next to stale numbering.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* Order in the auto branch is fixed: delete the old requests_*/metadata_* files first, plan second. Nothing new gets written next to stale numbering.

*Why there:* None of the listed rooms are chewing on batch payload files or resume-time cleanup. The closest, #code-review 2025-01-27, is about parameter passing for PR 403 (temperature/max_tokens vs batch_size) — a settled statement about deleting stale requests_*/metadata_* before plan_request_batches would land there as a subject change with no one to answer it, and Konrad on that day is asking questions rather than announcing decided ordering. The other candidates are multimodal/cost-map stability, sandbox uid, onboarding, WS-033 and PR triage; none touch the batch processor's file layout. What should have existed is the follow-up to Emil's "I'll dig into it first thing tomorrow" on PR 403: Emil's morning pass turns up a resume case where a rerun plans new batches alongside leftover requests_*/metadata_* from the previous run, and Konrad closes the ordering question for the auto branch while Dario weighs in from the request-processing side.

*A new conversation in #cookbooks on 2025-01-21:*

```
08:37  emil: went through 403 first thing this morning and there's a resume case i don't think we covered in the param thread from the 27th. if a run dies partway and you rerun it, the leftovers from the previous run are still sitting in the working dir and we go ahead and plan a fresh set of batches right on top of them
08:38  emil: so you end up with two generations of payload files interleaved, numbered from zero both times. honestly i'm not entirely sure what the reader is supposed to do with that
08:42  konrad: Order in the auto branch is fixed: delete the old requests_*/metadata_* files first, plan second. Nothing new gets written next to stale numbering. anyway that is the whole reason the cleanup sits above plan_request_batches and not after it
08:46  dario: mhm. is that documented anywhere or is it just the order the calls happen to be in, i.e. would someone reordering them notice they broke something or would it just silently start producing garbage
08:51  emil: we need to be intentional here because the failure is quiet either way. i belive the resume path is the only one where it matters but let me think through that, there might be a partial-write case too where the file exists but is truncated
08:54  dario: in any case that's a separate ticket i think. i'll leave a note on 403 so it doesn't get lost, best we can do before the review this afternoon
```

