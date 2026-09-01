# Clues for g1 — Batch payload planner for `batch_size="auto"`

50 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/latest`.

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
| 2025-03-14 | #incidents *(new)* | dermot | yeah ok, one more on the zero row doc — num_requests 0, num_bytes 0, and batches is an empty list, not a key we leave off. | `scope` |
| 2025-03-14 | #engineering *(new)* | konrad | Look, I seeded the dir with requests_0.jsonl through requests_5.jsonl plus matchign metadata, then let the plan make three - the listing afterwards is the assertion. | `rule`, `observability` |
| 2025-03-14 | #releases *(new)* | dario | honestly explicit batch_size=1000 should keep giving the same fixed-width files it always has, i don't want that branch picking up new behaviour off the side | `scope` |
| 2025-03-14 | #viewer *(new)* | gideon | so basically someone ran rm -f over the working dir between runs and it took responses_0.jsonl with it, so we paid twice for a batch we had already completed. | `exclusions_or_crossover`, `observability` |
| 2025-03-14 | #general *(new)* | nils | let me think through that - the .arrow shards in the working dir are the dataset itself, drop those and we re-tokenize four million rows before anything even gets submitted | `exclusions_or_crossover` |
| 2025-03-14 | #cookbooks *(new)* | nikolai | fixture pins max_bytes_per_batch to 400 and feeds a 600 char prompt - SingleRequestTooLargeError comes back with row_idx 1 on it, thats how we know which row blew up. | `observability`, `failure_behavior` |
| 2025-03-17 | #cookbooks *(new)* | konrad | Right, so each entry in batches carries all five fields - index, start_idx, end_idx, num_requests, num_bytes. num_jobs is metadata_0.json's name, it doesnt come along. | `rule` |
| 2025-03-17 | #releases *(new)* | dario | and batches[0] for the five row sample is {"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307} — same numbers as metadata_0.json, just num_requests where that says num_jobs | `observability` |
| 2025-03-17 | #viewer *(new)* | gideon | so basically [10] * 512 at one row per batch planned all 512 and came back clean, 513 is the first count that refuses - we bail past the ceiling, not at it. | `failure_behavior` |
| 2025-03-17 | #general *(new)* | nils | let me think through that - for the fixture to prove anything, batch_plan.json has to already be sitting in the dir when we start, holding a stale plan_format_version 1 body. | `observability` |
| 2025-03-18 | #general *(new)* | nils | pinned the envelope in my checker: plan_format_version, plan_id, limits, num_batches, num_requests, num_bytes, batches, in that order and nothing else at the top level. | `rule` |
| 2025-03-18 | #releases *(new)* | dermot | one more on the zero row case — create_request_files hands back an empty list there, so there's no requests_0.jsonl sitting around with nothing in it. | `scope` |
| 2025-03-18 | #cookbooks *(new)* | konrad | That order is gone, deleting first cost you a split when the oversized row raised. plan_request_batches runs first now, we only sweep requests_*.jsonl and metadata_*.json after it returns a plan. | `rule`, `failure_behavior` |
| 2025-03-19 | #pipeline *(new)* | nils | let me think — a zero row auto run leaves the working dir completely empty and my checker can't tell that from a crash. we write the file regardless, num_batches 0. | `scope`, `observability` |
| 2025-03-19 | #cookbooks *(new)* | emil | one more worth pinning next to the empty one: plan_batches([10] * 7, BatchLimits(1000, 32)) fingerprints to ad0828fea95e. no special casing, same recipe. | `observability` |
| 2025-03-19 | #releases *(new)* | dario | sweep isn't first in the auto branch any more - it wiped a working dir when plan_request_batches threw SingleRequestTooLargeError, so requests_*.jsonl and metadata_*.json clear only after planning returns | `rule`, `failure_behavior` |
| 2025-03-21 | #code-review | nils | @Emil same class of thing on my end - metadata_3.json in my working dir still reports num_jobs from the old split, and nothing in this run touched it. | `rule` |
| 2025-03-24 | #pipeline | dario | One thing that's already clear from the sketch - the online path calls create_request_files with dataset None, nothing to plan there, so we leave the working dir alone on that route. | `scope` |
| 2025-03-25 | #code-review *(new)* | konrad | Look, the plan file lands as one enourmous line, so diffing two runs is hopeless. Whole file is json.dumps(plan_document(plan, self.batch_limits), indent=2) plus a trailing newline. | `rule`, `observability` |
| 2025-03-26 | #engineering *(new)* | nils | spent the morning diffing two batch runs span by span just to confirm the split hadn't moved. one short comparable string per plan would have answered that in a second. | `rule` |
| 2025-03-26 | #pipeline *(new)* | dario | for the five row sample plan_fingerprint built 0-2:307;2-4:307;4-5:153 — start-end:num_bytes per batch joined on semicolons — and returned f4b1ea1573c0, the first twelve hex of its sha256 | `rule`, `observability` |
| 2025-03-31 | #code-review | dermot | a run that raises in the estimate step and never gets a plan out the other end has no business having changed anything on disk, stale or not | `failure_behavior` |
| 2025-04-03 | #pipeline | dermot | the resume path json.loads metadata_0.json and wants {"num_jobs": 2} and nothing else, so start_idx, end_idx and num_bytes came back out. that span and size sit in batch_plan.json under batches now | `exclusions_or_crossover`, `rule` |
| 2025-04-07 | page:design/batch-job-status-persistence-across-process-restarts.md | dario | worth adding to the persists-where list: the planner module holds PLAN_FILE_NAME = "batch_plan.json" next to the limits dataclass. nothing imports it from the processor yet, shape is still moving. | `rule` |
| 2025-04-08 | #code-review *(new)* | konrad | look, my except BatchPayloadTooLargeError sailed straight past BatchPlanTooFragmentedError — err.num_batches 513, err.limit 512 off the default. right call, its own ValueError, my handler shoud not touch it. | `failure_behavior` |
| 2025-04-08 | #pipeline | gideon | Related-ish, I reran auto on a trimmed dataset and the submit loop picked up requests_4.jsonl and requests_5.jsonl leftover from Tuesdays bigger run, two duplicate batches. | `rule` |
| 2025-04-09 | #incidents | dario | not that i've seen. batch_objects.jsonl is unrecoverable state - the sweep doesn't just leave it in place, it leaves the bytes untouched, same for everything it isn't deleting. | `exclusions_or_crossover` |
| 2025-04-10 | thread:new|g1.r1.l10 *(new)* | dermot | yeah — keep plan_format_version as the first key plan_document writes; a reader that cannot find it up front has no business parsing the rest. | `rule` |
| 2025-04-11 | #cookbooks | dermot | yeah. and a requests_0.jsonl already sitting there gets swept with the rest and rewritten from this run's plan, its own start_idx to end_idx. | `rule` |
| 2025-04-15 | thread:new|g1.r1.l14 *(new)* | konrad | Look, if a fixed batch_size run also drops a plan_id file next to the requests, my loader will read that run as auto-sized. Keep it to the auto branch. | `scope` |
| 2025-04-17 | thread:new|g1.r2.l6 *(new)* | nikolai | i'd say careful there on resume we call create_request_files with dataset=None purely to get the paths back and i'd be unhappy if that call ever started taking files away | `scope` |
| 2025-04-17 | #random | emil | not just create-on-open though - the oversized-row failure left me staring at an empty working dir, and the split that was in there beforehand was still perfectly usable | `failure_behavior` |
| 2025-04-18 | #incidents | nikolai | renumberd the batches by hand while poking at a failure and got the identical id back right call i mean the index and num_requests arent in what gets hashed | `rule` |
| 2025-04-21 | #pipeline | emil | sounds right - though the integer batch_size path leans on files from earlier runs, incomplete_files is what skips the finished ones, clear those and every resume starts from zero | `scope` |
| 2025-04-22 | #viewer *(new)* | gideon | so basically the viewer reads num_batches and the request and byte totals straight off the top — and the batches key is one dataclasses.asdict per PlannedBatch, index and num_requests included. | `rule`, `observability` |
| 2025-04-23 | #pipeline | gideon | same gap on my end - job died writing requests_3.jsonl and nothing on disk said there were supposed to be nine. plan gets written before the first request file. | `scope`, `observability` |
| 2025-04-24 | #pipeline *(new)* | gideon | so basically someone asked me how tuesday's auto run split and I had to ls the requests_*.jsonl files and re-measure every one of them. that should be sitting on disk. | `rule`, `observability` |
| 2025-04-24 | #code-review | dario | a week of resume runs choking on keys they didn't expect, so the plan's out of metadata_{i}.json into a sidecar: batch_plan.json in the working dir, plan_format_version 1, auto branch only | `rule`, `scope`, `exclusions_or_crossover` |
| 2025-05-02 | page:design/batch-job-status-persistence-across-process-restarts.md | konrad | Look, the working dir today holds more than those two: requests_*.jsonl, metadata_*.json, responses_*.jsonl, batch_objects.jsonl (submitted batch ids we poll), plus the .arrow shards for the dataset. | `exclusions_or_crossover` |
| 2025-05-07 | #pipeline *(new)* | emil | empty plan just hashes the empty string, so plan_id comes out e3b0c44298fc, first twelve of the sha256. no special case needed. | `rule`, `observability` |
| 2025-05-08 | #pipeline *(new)* | dermot | our resume path json.loads metadata_0.json and expects {"num_jobs": n} and nothing else — n is exactly the plan's num_requests for that batch, so keep the span and byte fields out. | `exclusions_or_crossover` |
| 2025-05-22 | #code-review *(new)* | emil | nit on the plan writer - you've got the 1 inlined in three seperate spots, and PLAN_FORMAT_VERSION is sitting right above it in the same module. | `rule` |
| 2025-06-16 | thread:<178771578160.2500381.12817086076544913041@world.local> | nikolai | good that limits is dataclasses.asdict of the BatchLimits it planned under, max_requests_per_batch and max_bytes_per_batch and max_batches_per_plan — otherwise 767 bytes tells you nothign a month later | `rule`, `observability` |
| 2025-06-16 | #engineering *(new)* | emil | 600 rows of 10 bytes plus one 5000 byte row under a 1000 byte cap and it said too fragmented instead of naming row 600. per-row oversize reports first. | `failure_behavior` |
| 2025-06-18 | #code-review *(new)* | nikolai | test builds BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes so i dont have to construct 513 spans, then asserts err.num_batches == 3 and err.limit == 2 | `failure_behavior` |

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

> **Values nobody prints:** `11`, `c53f6fb95c13`. Fine if the remarks say enough to compute them; check that they do.

> **Spread:** g1.r1.sc4: two remarks in #pipeline within 5 days

> **3 of 45 graded assertions are not stated outright** — 3 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g1.r1.sc1 — An auto-sized run leaves one separate, indented JSON file under a fixed module-level file name in the working dir, and the existing per-batch metadata files are not extended to carry any of it.

*Nobody says:* If people keep needing the split after the fact and the per-batch metadata is off limits for it, the record has to be its own file with a name everyone can reach for.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g1.r1.l3` — rule, observability

**konrad**, 2025-03-25, #code-review

> Look, the plan file lands as one enourmous line, so diffing two runs is hopeless. Whole file is json.dumps(plan_document(plan, self.batch_limits), indent=2) plus a trailing newline.

*What a reader should take from it:* the team agrees the file is dumped indented two spaces with a trailing newline

*Step it builds toward:* `g1.r1.sc1` — An auto-sized run leaves one separate, indented JSON file under a fixed module-level file name in the working dir, and the existing per-batch metadata files are not extended to carry any of it.

*Drafted as:* The plan file lands as one enormous line, so diffing two runs is hopeless. Dump it with indent 2 and end the file with a newline.

*Why there:* None of the eight rooms is chewing on a generated plan file or its serialization. The closest topically is #engineering 2025-03-19, but that day is about the api_key approach, the throttle/estimation split and PR 584 — a formatting verdict on an artifact nobody has mentioned would land cold and draw no reply. The release threads are about notes and support tables, 2025-04-03 is review-bandwidth triage, 2025-05-22 is factory-cleanup scope, 2025-06-02 is dormancy, 2026-01-22 is the README/cookbooks gap. What's missing is the review of the batch payload plan work itself on the batch-mode branch: nils puts the artifact up after PR 584 lands, konrad reads a diff of two runs and can't, and the room settles indent and trailing newline while the file's name, keys and branch are being pinned down by nils in the same thread.

*Still leaves open:* Doesn't say what the file is named, what keys it holds, or which branch produces it.

*Must appear literally:* `indent=2`, `json.dumps`, `plan_document`, `self.batch_limits`

*A new conversation in #code-review on 2025-03-25:*

```
11:12  emil: unrelated to the PR queue, but i pulled the plan file from two consecutive runs on the bulk path this morning and tried to diff them and honestly it was hopeless. forty minutes and i still couldn't tell you which batch changed. is a readable diff just not something we get out of that file, or am i holding it wrong
11:17  nikolai: not something you get right now no
the writer just does json.dumps on plan_document(plan, self.batch_limits) and writes the string out, thats it, no formatting args anywhere near it
11:23  emil: ok so if im reading that back right, the entire document comes out of that one call, nothing further down is assembling it field by field. which would mean the fix lives on that line and not in the plan builder at all? i'm not entirely sure i believe it's that contained
11:29  konrad: right, it is that contained. look, the whole file is that one json.dumps, nothing else writes into it, which is exactly why it lands as one enourmous line
11:30  konrad: so indent=2 on the dumps and a trailing newline at the end of the file, and your diff becomes readable. that is the whole change. nobody has typed it yet though, presumably it goes in with whatever touches the writer next
11:34  nils: the trailing newline is doing more work there than it sounds like, i think. without it git flags the last line on every single run and you end up with noise on the one line you actually care about. we went round on exactly this with the config dumps in january
```

> **Problems:** longer than one remark

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

> **Problems:** longer than one remark

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
10:31  gideon: someone from evals pinged me this morning asking how tuesday's auto run split, like how many requests ended up in each batch
10:32  gideon: and i realized there is nowhere i can point them. tbh i stared at the run log for a while and there is nothing in there about the split at all, just start and done
10:40  emil: you mean the auto sizing run from tuesday, the overnight one? if i'm following you, the only surviving trace of that split is the request files themselves, so the way in is ls'ing the requests_*.jsonl in the working dir and reading the shape off the file list
10:43  gideon: ya exactly, thats what i ended up doing. ls the requests_*.jsonl files, count them, ok fine, 14 of them
10:44  gideon: but the filenames dont tell you anything past that. so then i had to go re-measure every one of them, line counts, token totals, all of it, just to answer a question the sizer already had the answer to on tuesday night
10:51  emil: let me think through that. so the sizer works all of this out at split time and then honestly just drops it on the floor, and the only route back is recomputing it from the artifcats afterwards. that is backwards, i believe, for something we're going to be asked about every week
10:55  gideon: so basically that should be sitting on disk. it knows the per batch counts the second it decides them, write them out next to the request files and nobody has to reconstruct anything. honestly though i dunno which ticket it hangs off, probably whoever takes the sizer branch next
```

> **Problems:** longer than one remark

#### `g1.r1.l4` — exclusions_or_crossover

**dermot**, 2025-05-08, #pipeline

> our resume path json.loads metadata_0.json and expects {"num_jobs": n} and nothing else — n is exactly the plan's num_requests for that batch, so keep the span and byte fields out.

*What a reader should take from it:* the team agrees the per-batch metadata body stays exactly {"num_jobs": n}

*Step it builds toward:* `g1.r1.sc1` — An auto-sized run leaves one separate, indented JSON file under a fixed module-level file name in the working dir, and the existing per-batch metadata files are not extended to carry any of it.

*Drafted as:* our resume path json.loads metadata_0.json and expects {"num_jobs": n} and nothing else, so please keep the span and byte fields out of there.

*Why there:* The remark is a veto on a specific proposal — adding span and byte offsets to the per-batch metadata file — and no listed room has that proposal on the table. 2025-03-24 is the closest (persisting batch state for resume) but it's still arguing metadata db vs. flat file for the batch id, with no metadata_0.json and no span/byte fields in play; dermot would be objecting to something nobody said. 2025-04-08 is field-layout talk but for failed_requests.jsonl, a different file, and nikolai already owns that spec. The others don't touch resume file formats. What's missing is a #pipeline thread on the batch payload/shard layout where gideon proposes hanging per-job byte spans off the metadata file, dermot rules that file out because resume parses it strictly, and a sibling reply puts the span and byte fields in a separate per-shard index instead.

*Still leaves open:* Doesn't say where those fields should live instead, or in what form.

*Must appear literally:* `metadata_0.json`, `num_jobs`, `num_requests`, `{"num_jobs": n}`

*A new conversation in #pipeline on 2025-05-08:*

```
09:47  wes: question on the sidecar while im in the batch payload writer — im about to emit metadata_0.json next to each payload and i want to put the request span in it (start/end index) plus the byte offsets, since im already computing both. any reason not to? the resume path is the only consumer as far as i can tell
09:48  wes: asking partly because the resume on the 4/29 rerun came back with a job count that didnt match the payload and i never chased it properly
09:53  dermot: the resume path doesn't walk that file, it just does a json.loads on metadata_0.json and pulls one key off the resulting dict. num_jobs. so the span and the offsets wouldn't be read by anything, they'd just be sitting there
09:56  wes: sitting there is ok though isnt it? nobodys parsing them but theyre nice to have next to the payload for debugging. and separately — num_jobs is what exactly, the lines i actually wrote out after dedupe, or the count i was handed?
10:04  dermot: no, keep the span and the byte fields out of it. the object is {"num_jobs": n} and nothing else — thats the whole shape the loader is written against and i'd rather not have it drift.

and n is the plan's num_requests for that batch, exactly. not a recount of what landed on disk. so at serialize time you're copying a number you already have, if i had to guess thats where the 4/29 mismatch came from, something recounted
10:06  wes: ok. and the name — is it always _0 or does it index off the batch number
10:09  dermot: always _0. it's one file per batch directory, the suffix is vestigial
```

> **Problems:** longer than one remark

### g1.r1.sc2 — The plan carries a short stable id: the first twelve characters of the sha256 hexdigest of a canonical string built from each batch's start-end span and its byte size, joined per batch, with the batch index and request counts left out.

*Nobody says:* Two runs that split the same way must produce the same token, so only the facts that define the split can go into the hashed string, and the digest is truncated to stay readable.

*5 remarks — 0 reporting the problem, 5 settling the design.*

#### `g1.r1.say29` — observability

**emil**, 2025-03-19, #cookbooks

> one more worth pinning next to the empty one: plan_batches([10] * 7, BatchLimits(1000, 32)) fingerprints to ad0828fea95e. no special casing, same recipe.

*What a reader should take from it:* the team agrees plan_fingerprint of plan_batches([10] * 7, BatchLimits(1000, 32)) is ad0828fea95e

*Step it builds toward:* `g1.r1.sc2` — The plan carries a short stable id: the first twelve characters of the sha256 hexdigest of a canonical string built from each batch's start-end span and its byte size, joined per batch, with the batch index and request counts left out.

*Drafted as:* one more constant worth pinning next to the empty one: plan_batches([10] * 7, BatchLimits(1000, 32)) fingerprints ad0828fea95e. no special casing, same recipe.

*Why there:* Every listed room is PR-status triage or release-notes bookkeeping — who reviews 683, whether 653 gets closed, whether o3-mini is in the support table. None of them is chewing on batch planning internals, and none has a golden-fingerprint table with an "empty one" already pinned for this to sit next to. The closest thread (code-review 2025-06-16) touches PR 691 only as "batch size automation, not write-up ready" — dropping a specific plan_fingerprint constant into that queue-status back-and-forth would change the subject cold and get no reaction from Nikolai, who is only asking whether things are reviewable. Emil is the right author, but the room that pins these constants hasn't happened yet: it's the follow-up where he's actually writing up 691 and filling in the planner's fixture table.

*Still leaves open:* why that plan comes out three batches rather than seven — the packing that produces those spans is settled elsewhere, not here.

*Must appear literally:* `plan_batches`, `[10] * 7`, `BatchLimits(1000, 32)`, `ad0828fea95e`

*A new conversation in #cookbooks on 2025-03-19:*

```
10:41  konrad: quick question on the golden fingerprints. right now the only plan we pin is the empty one, presumably because that was the one that kept regressing? feels thin as a net if the serializer moves under us
10:44  emil: let me think through that. yeah, one is thin. theres one more worth pinning next to the empty one imo — plan_batches([10] * 7, BatchLimits(1000, 32)). seven tiny items, nowhere near either cap, so the whole thing lands as a single batch. covers the ordinary case that the empty plan cant say anything about
10:47  dermot: mhm. that said the load bearing part of that fixture isn't the packing, it's that the batch carries seven entries and the per item counts have to come out in order. if i had to guess that's where a drift would actually surface
10:49  konrad: right. so what does it come out as, concretely. and does it want its own handling on the write side — i had it in my head the empty plan has an early return in there, or something like it
10:53  emil: ad0828fea95e. and no, no special casing for it, it just goes down the same recipe as everything else. not in the fixtures yet, i have it sitting in a scratch buffer
10:56  gideon: ah ok. i was reading the 32 as bytes for some reason and couldnt work out how 7 items fit, its the item cap. so basically nothing in that case is anywhere near a boundry
```

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
11:04  emil: i just lost the entire morning to diffing two batch runs against each other. friday's run and the one i kicked off last night, both plans open side by side, walking them span by span
11:08  konrad: what were you looking for in there. a request that went missing or
11:13  emil: honestly nothing that specific. i only wanted to confirm the split hadnt moved between the two, same boundaries in the same order. and it hadnt. so that is a whole morning spent to buy one yes
11:17  konrad: mhm but there has to be something cheaper than reading every span by hand. presumably the plan knows its own boundaries already, off the top of my head i am not entirely sure what you would compare instead
11:24  nils: let me think through that. the builder has the boundaries in hand at the moment it writes the plan, so it can fold them down into one short string and carry that on the plan itself. then what you compare is the two strings, not the contents
11:28  nils: and that comparison is a second, maybe less. equal strings means the split is identical and you never open the spans at all. nothing puts it on the plan today, the serialized plan comes out without it, but that's worth documenting in the format either way
11:33  emil: yup, that is exactly the question i was asking for four hours. i have a half finished span walker sitting in a scratch file that i can just delete now
```

#### `g1.r1.l6` — rule, observability

**dario**, 2025-03-26, #pipeline

> for the five row sample plan_fingerprint built 0-2:307;2-4:307;4-5:153 — start-end:num_bytes per batch joined on semicolons — and returned f4b1ea1573c0, the first twelve hex of its sha256

*What a reader should take from it:* the team agrees the hashed string is per-batch start-end:num_bytes entries joined with semicolons

*Step it builds toward:* `g1.r1.sc2` — The plan carries a short stable id: the first twelve characters of the sha256 hexdigest of a canonical string built from each batch's start-end span and its byte size, joined per batch, with the batch index and request counts left out.

*Drafted as:* for the five row sample the string plan_fingerprint hashed was 0-2:307;2-4:307;4-5:153 and it came back f4b1ea1573c0.

*Why there:* None of the eight rooms is chewing on batch payload planning. The closest, #pipeline 2025-03-24, is about persisting the provider batch job id so a restart can reattach — nobody there has raised how the dataset gets split into batches, byte budgets per batch, or any notion of a plan identity; a concrete fingerprint over start-end:num_bytes entries would arrive from nowhere and get no reaction. The others are schema_check at construction (03-14), the gemini parts key (04-01), Mistral token usage shape (03-17), failed_requests.jsonl and DeepSeek headers (04-08), PR ordering and cost columns (04-14), the metadata panel's missing directory field (04-28), and a plain PR queue (04-22) — none touch batching by size at all. What should exist is the follow-up Dario explicitly promised on 03-24 ("I'll sketch it out and bring something back to the group"): once the batch id is written to disk, a resume has to know the plan it was written against is still the same plan, which is what plan_fingerprint is for and where the exact hashed string gets pinned down.

*Still leaves open:* Doesn't say which hash, how much of the digest is kept, or what is deliberately absent from that string.

*Must appear literally:* `plan_fingerprint`, `0-2:307;2-4:307;4-5:153`, `f4b1ea1573c0`

*A new conversation in #pipeline on 2025-03-26:*

```
13:12  gideon: So basically I'm back on the serialized plan and I still can't tell what we're actually hashing to decide two plans are the same plan. Is it the whole file, or some subset of it? Because the file has a timestamp in it which is already a problem tbh, a rerun would never match itself
13:19  emil: let me think through that. i believe the field is called plan_fingerprint and it is deliberately not the whole file - just the batch boundaries. timestamp and model name stay out of it, for exactly the reason you said
13:24  gideon: ok ya but boundaries how exactly though. the row indices only, or does the payload size go in as well? um, two plans can have identical row ranges and completely different bytes if someone edits the prompt function underneath
13:31  dario: the byte count goes in, thats honestly the whole reason it exists. per batch its start-end:num_bytes, and then the batches get joined on semicolons in order. so for the five row sample plan what gets built is 0-2:307;2-4:307;4-5:153 - two full batches and then the leftover
13:33  gideon: right, last one is short because only one row is left over. And then that string is the fingerprint itself or is there a hash step on top
13:38  dario: hash step. sha256 over that string and we keep the first twelve hex, so the five row sample returned f4b1ea1573c0 when i checked it by hand. twelve is plenty for what we use it for i think, in any case its cheap to widen later if we ever need to
13:42  emil: yup. nothing written against it yet though, the plan builder still just dumps the ranges out and moves on. i can pick it up under the resume ticket unless someone wants it filed on its own
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
14:02  lena: ran the nightly against a plan with zero items yesterday and i still can't tell if plan_id is blowing up or just quietly not there. the sidecar wrote out an id anyway, which surprised me, i'd assumed empty meant we bail before we ever get that far
14:07  emil: let me think through that. the id comes off the seralized item blob, and for an empty plan the blob is just the empty string. so it hashes the empty string. there's nothing to bail on really, hashlib is perfectly happy hashing nothing at all
14:10  lena: sure but happy != something i can rely on, in my head anyway. do we get a stable value out of that or do we want a sentinel slotted in so it's obvious downstream the plan was empty
14:15  emil: its stable. sha256 of the empty string, truncated to the first twelve like every other id we mint, which comes out e3b0c44298fc, every time, on every box. honestly i'd rather we didnt invent a sentinel here — an empty plan with a real id reconciles fine and a magic value is one more thing everyone has to remember
14:17  lena: so no special case at all then
14:21  emil: no. no branch for it. i beleive there's still an `if not items: return None` guard sitting in the sidecar path left over from the old code, that's the thing that has to come out, but nobody's gone near it yet
14:23  lena: ok. ill see if it fits under the batch payload ticket or if it wants its own
```

### g1.r1.sc3 — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*Nobody says:* A consumer decides whether it can read the file at all, then wants the summary, and only then the detail, so the keys come in that order.

*7 remarks — 1 reporting the problem, 6 settling the design.*

#### `g1.r1.say23` — rule

**konrad**, 2025-03-17, #cookbooks

> Right, so each entry in batches carries all five fields - index, start_idx, end_idx, num_requests, num_bytes. num_jobs is metadata_0.json's name, it doesnt come along.

*What a reader should take from it:* the team agrees a batch entry keeps all five PlannedBatch fields under those names

*Step it builds toward:* `g1.r1.sc3` — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*Drafted as:* Right, so each entry in batches carries all five fields — index, start_idx, end_idx, num_requests, num_bytes. num_jobs is metadata_0.json's name, it doesnt come along.

*Why there:* None of the listed rooms is chewing on the shape of a batch plan document. The two that touch batch-mode are about other things entirely: 2025-03-19 is Konrad approving a gemini unicode surrogate fix and a version bump, and 2025-04-11 is release notes for the batch cancellation hotfix. The rest are PR triage, sandbox guarantees, agentic curation state, cookbook response-object updates, and version tag format. A settled decision about which PlannedBatch fields survive into each entry of `batches`, and that `num_jobs` only shows up in the `metadata_0.json` filename, needs someone to have just asked what the plan file looks like — nobody does, and dropping it into any of these threads would change the subject and get no reply. It also needs a second speaker present to supply the asdict/placement half, which the sibling remark covers. The natural home is a working thread while the request-file planner is actually being written: Konrad on batch-mode, Nikolai poking at it from the backend integration side, one of them asking plainly what lands on disk.

*Still leaves open:* doesn't say the entries are produced by asdict over the plan, nor where they sit in the document.

*Must appear literally:* `batches`, `index`, `start_idx`, `end_idx`, `num_requests`, `num_bytes`, `num_jobs`, `metadata_0.json`

*A new conversation in #cookbooks on 2025-03-17:*

```
11:04  dario: quick one on the plan serialization — when we write out `batches`, is each entry meant to be the full record or just the offsets? i've been carrying start_idx and end_idx and nothing else and the reader on the other side is unhappy about it
11:06  konrad: look, offsets alone are not enough. each entry needs `index` as well, otherwise you cannot tell which batch you are looking at once the list gets reoredered
11:07  konrad: and the two counts, num_requests and num_bytes. we had those in the old dict, presumably they just fell out somewhere in the rewrite
11:09  dario: ok that tracks. so the two counts plus index on top of the offsets. what about num_jobs though, does that ride along in every entry or is it once at the top and everything below inherits it
11:11  konrad: num_jobs is not one of them at all. that name only lives in metadata_0.json, it is the count for that file. it doesnt come along into the entries
11:12  konrad: so all five fields in every entry and thats it, nothing else
11:14  dario: mhm. honestly i think i confused myself because the metadata file and the plan both have num-something in them and i assumed same shape
11:16  konrad: anyway im not getting to it today. do you want it folded into the sidecar ticket or sitting on its own
```

> **Problems:** longer than one remark

#### `g1.r1.say24` — observability

**dario**, 2025-03-17, #releases

> and batches[0] for the five row sample is {"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307} — same numbers as metadata_0.json, just num_requests where that says num_jobs

*What a reader should take from it:* the team agrees each entry under batches uses index, start_idx, end_idx, num_requests and num_bytes, with num_requests where the metadata file says num_jobs

*Step it builds toward:* `g1.r1.sc3` — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*Drafted as:* and batches[0] for the five row sample is {"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307} — same numbers as metadata_0.json, different names.

*Why there:* No listed room is discussing the batch payload document at all. The 04-03 and 04-08 #code-review days are PR/blocker triage; #viewer 04-14 is the provider-label mismatch and release notes; #viewer 04-28 is what the executor's report object carries about the inspected directory; #cookbooks is the response-object/.choices sweep; #help is executor image digests. metadata_0.json, a five-row sample, and a batches array appear nowhere, and this remark is explicitly a second course to sibling remarks about the envelope, ordering, version and limits — none of which any of these rooms has served. Dropped into any of them it changes the subject and gets no reply.

*Still leaves open:* says nothing about the top-level envelope, its ordering, the version key, or what limits holds — a reader still needs the sibling remarks for the document around it.

*Must appear literally:* `batches[0]`, `{"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307}`, `metadata_0.json`

*A new conversation in #releases on 2025-03-17:*

```
10:24  priya: quick one before i write the fixture — the serialized plan for the five row sample, what's actually in batches[0]? i can generate it from the run but i'd rather assert against something we've agreed on than against whatever the code happens to emit today
10:31  dario: honestly the easiest way to think about it is that batches[0] for the five row sample is the same numbers we already write into metadata_0.json. nothing new is being computed there, it's the same first batch, just travelling inside the plan instead of sitting next to the shards
10:33  priya: same numbers i believe, it's the keys i'm stuck on. metadata_0.json says num_jobs. does the plan keep that spelling or do i have to translate it on the way in? because if it's the former i can just load the sidecar in the test and compare dicts, and if not i'm writing the literal by hand
10:41  dario: write the literal. it's {"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307} — num_requests where the sidecar says num_jobs, and everything else carries over unchanged, same index, same offsets, same byte count. i went back and forth on whether to keep num_jobs for symmetry but the plan is request-shaped everywhere else and having one field call them jobs was the thing that confused me for twenty minutes last week, so
10:43  priya: yeah no that's the right call, jobs was a leftover from the old runner anyway. so the dict above goes in as-is and i don't touch the sidecar writer
10:52  dario: correct, sidecar stays exactly as it is for now. in any case nobody's written any of this yet — i'd put it on the batch plan ticket rather than spinning a new one, and whoever has room picks it up. probably not me before thursday to be honest
```

#### `g1.r1.say22` — rule

**nils**, 2025-03-18, #general

> pinned the envelope in my checker: plan_format_version, plan_id, limits, num_batches, num_requests, num_bytes, batches, in that order and nothing else at the top level.

*What a reader should take from it:* the team agrees plan_document writes exactly those seven keys in that order and no others

*Step it builds toward:* `g1.r1.sc3` — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*Drafted as:* pinned the envelope in my checker — plan_format_version, plan_id, limits, num_batches, num_requests, num_bytes, batches, in that order and nothing else in there.

*Why there:* Both listed #code-review days are pure traffic control — who reviews PR 584, what lands before the release, whether PR 468/565 get deferred, and the running thread that WS-047 has no spec anywhere. Neither day contains a single line about plan_document, batch payload formats, or a schema checker; the closest hook is Nils confirming on 03-25 that nobody handed him a scope for WS-047, which is still the "there is nothing written" stage, not the "I have pinned the envelope keys in my validator" stage. Dropping a seven-key envelope decision into either day changes the subject mid-triage and no one there is positioned to react to it. What's missing is the follow-up: once Nils accepts he owns WS-047 from scratch, he starts writing the plan format and a checker alongside it, and needs Emil (batch-mode owner) to agree the top-level shape before the values get argued about.

*Still leaves open:* says nothing about what any of the values hold — how plan_id is derived, what limits or batches contain.

*Must appear literally:* `plan_format_version`, `plan_id`, `limits`, `num_batches`, `num_requests`, `num_bytes`, `batches`

*A new conversation in #general on 2025-03-18:*

```
10:12  dario: the plan json i pulled off the failed run last night has num_bytes sitting between batches and limits. is that meaningful or does keys go wherever
10:19  nils: let me think through that. it's meaningful now, or it will be — i pinned the envelope in my checker: plan_format_version, then plan_id, then limits. Version first so if we ever bump it you can tell what you're holding without parsing the rest of the thing.
10:23  dario: ok limits third. what about the counts, and does it care if something extra turns up at the top? the file that broke had a `generated_at` up there and i genuinely don't know if that's us or the sidecar putting it in
10:31  nils: after limits it goes num_batches, num_requests, num_bytes, and then batches last — sizes before the payload, so anything reading it streams the numbers before it walks into the big array. and nothing else at the top level, that's the part i care about. a stray generated_at is the exact thing i'd rather have blow up than get shrugged at, so it comes back as a mismatch same as a reorder would.
10:34  dario: fair. is that landing this week or is it waiting on the sizing branch
10:41  nils: whoever gets to the validation ticket first, honestly. could be me thursday. the shape isn't going to move under you though, so no reason not to write against it — that's worth documenting somewhere better than this channel, i'll put it on the ticket.
10:43  dario: i'll drop the order assert into the diff tool in the meantime so we stop eyeballing these
```

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
From: None  To: 


From: None  To: 


From: None  To: 


From: None  To: 


From: None  To: 


From: None  To: 


From: None  To: 


```

#### `g1.r1.l11` — rule, observability

**gideon**, 2025-04-22, #viewer

> so basically the viewer reads num_batches and the request and byte totals straight off the top — and the batches key is one dataclasses.asdict per PlannedBatch, index and num_requests included.

*What a reader should take from it:* the team agrees the document carries num_batches and the request and byte totals above the per-batch list

*Step it builds toward:* `g1.r1.sc3` — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*Drafted as:* Viewer wants num_batches and the request and byte totals off the top of the file, not by walking batches and summing them itself.

*Why there:* None of the listed rooms is chewing on a batch summary file format. #incidents 04-11 mentions "viewer cleanup" only in passing as part of a post1 release note, and the live question there is whether the upgrade is optional or strongly recommended — a file-layout decision would change the subject and get no reaction. The two #code-review days are about PR 632/643 review ownership and whether 642 touches the response path; PR 643's CuratorResponse is an in-memory run-metadata wrapper, not a file the viewer reads, so folding `num_batches` into it would quietly retarget the thread. Both #pipeline days (retry semantics/sweep order, Anthropic multimodal content blocks) never touch the viewer. The remark, plus its sibling about batch entry contents and where version/id sit, is clearly one slice of a spec discussion for the batch summary file — that conversation belongs in #viewer, where the person consuming the file is complaining about having to derive totals themselves.

*Still leaves open:* Doesn't say what a batch entry contains, where the version or id sit, or which runs produce the file.

*Must appear literally:* `PlannedBatch`, `batches`, `dataclasses.asdict`, `index`, `num_batches`, `num_requests`

*A new conversation in #viewer on 2025-04-22:*

```
10:41  rhea: ok dumb question about the plan json before i wire up the summary bar — for the counts at the top of the viewer, am i walking the list and adding it up myself, or is that stuff already sitting somewhere
10:44  gideon: you dont have to walk anything. num_batches is right there at the root of the payload, just read the field
10:45  gideon: on that broken run in march i was summing it by hand like an idiot and it came out one off because of an empty batch at the tail, so um, dont do what i did
10:47  rhea: heh ok. what about the request count and the bytes though, thats the other two things in the bar. same deal or is that on me
10:50  gideon: same deal, both totals sit next to num_batches at the top level. request total and byte total. so the bar is three field reads and thats it, no reduce
honestly though the thing i'd actually look at is `batches`, i dunno if you opened it yet
10:52  rhea: not properly. i assumed it was trimmed down to like ids and offsets
10:56  gideon: nah its one dataclasses.asdict per PlannedBatch, straight through, nothing filtered. so every field on the dataclass is there as-is, index and num_requests included, which means per row you dont compute anything either, you just take the key you want for the column
nobody has written the reader side yet tho, thats still sitting on whoever grabs the viewer ticket this week
10:58  rhea: oh. thats way less work than i had in my head, i already had half a reducer written
```

#### `g1.r1.l9` — rule

**emil**, 2025-05-22, #code-review

> nit on the plan writer - you've got the 1 inlined in three seperate spots, and PLAN_FORMAT_VERSION is sitting right above it in the same module.

*What a reader should take from it:* the team agrees the module carries PLAN_FORMAT_VERSION and its current value is 1

*Step it builds toward:* `g1.r1.sc3` — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*Drafted as:* nit: you inlined the 1 in three places here. there's a PLAN_FORMAT_VERSION constant sitting right above it.

*Why there:* All eight listed conversations are status/triage threads — PR numbers, blockers, who owes whom a signoff — and none contains a line-level code review or a diff anyone could nit. The one place emil pastes code (05-30) is his own PR 652 error payload, and the live question there is retry semantics, not constant duplication. No listed PR plausibly contains a plan-format module (torch import guard, finetuning client, metadata-db flag, lazy batch download), and 653/663 are explicitly still unreviewed as of 05-30, so a review pass can't be backdated onto them. The remark needs a room where emil is reading a diff and its author is present to take the nit.

*Still leaves open:* Doesn't say where the version surfaces in the written file or what else the document holds.

*Must appear literally:* `PLAN_FORMAT_VERSION`

*A new conversation in #code-review on 2025-05-22:*

```
14:04  konrad: small thing on the plan writer while i am in there - the format version goes out as a bare 1 in the serialised payload. is that delibrate or just leftover
14:11  nikolai: its not one place either
i counted three
the header  the per shard block  and the fallback we write when the manifest comes back empty
14:13  konrad: mhm. so what do we point those at, do we add a constant or is there one already
off the top of my head i dont remember seeing one in that file
14:22  emil: let me think through that - theres nothing to add, PLAN_FORMAT_VERSION is allready defined in that same module, litterally sitting a few lines above the writer. i believe it just got skipped as the writer grew. those spots should be reading from it instead of each one carrying thier own copy
14:26  nikolai: yep
swapping them onto the constant is solid enough
bumping it later shouldnt mean grepping the module for stray 1s
14:29  konrad: right, ill drop it as a nit on the PR then, not a blocker
whoever takes the rebase can do the swap, maybe me tomorow if nobody gets there first
```

#### `g1.r1.l12` — rule, observability

**nikolai**, 2025-06-16, thread:<178771578160.2500381.12817086076544913041@world.local>

> good that limits is dataclasses.asdict of the BatchLimits it planned under, max_requests_per_batch and max_bytes_per_batch and max_batches_per_plan — otherwise 767 bytes tells you nothign a month later

*What a reader should take from it:* the team agrees the document echoes the limits the plan was built under

*Step it builds toward:* `g1.r1.sc3` — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*Drafted as:* good that the file records the caps it planned under, 3 requests and 400 bytes that run. otherwise three batches and 767 bytes tells you nothing a month later.

*Why there:* This is nikolai's own recap thread, and the live item in it is Dario's multimodal Gemini batch request creation fix plus PRs 690/691 that reviewers are being told to read together. Those are exactly the batch-splitting changes where the per-batch request and byte caps live, so a reply weighing in on the plan file the splitter writes out lands in a room already chewing on it — nikolai is the one who asked people to look at both PRs at once, so him reacting to what the review turned up is natural. Nothing in the seed mail has already made the point about the file echoing its own limits.

*Still leaves open:* Doesn't say where in the document the limits sit or what the other keys are.

*Must appear literally:* `767`, `BatchLimits`, `dataclasses.asdict`, `limits`, `max_batches_per_plan`, `max_bytes_per_batch`, `max_requests_per_batch`

*Goes as a reply into the real thread "Week of Jun 9 recap: bulk inference fix":*

```
Quick recap from last week. Dario's fix in bulk-llm-inference for multimodal Gemini batch request creation is the main thing worth knowing about — it's non-trivial and the two batch-related PRs (690 and 691) are close enough in scope that whoever reviews them will want to look at both at once.

One thing I want an answer on: PR 653, the finetuning client Shreyas originally opened, has been sitting with me. I've merged main in and there's still work to do. But if we're heading into maintenance mode after 0.1.26, does this PR actually need to land, or should it just be closed? Don't want to keep carrying it if the answer is abandon.
```

### g1.r1.sc4 — The file is written on the auto branch only and before any request file, and is still written when the plan came out empty; the explicit-integer branch and the dataset-is-None path never write it.

*Nobody says:* The file is the marker that the auto sizer ran and what it intended, so it must exist exactly when the auto sizer ran, including the zero-row case, and never otherwise.

*6 remarks — 2 reporting the problem, 4 settling the design.*

#### `g1.r1.say30` — scope

**dermot**, 2025-03-14, #incidents

> yeah ok, one more on the zero row doc — num_requests 0, num_bytes 0, and batches is an empty list, not a key we leave off.

*What a reader should take from it:* the team agrees the empty plan document carries num_requests 0, num_bytes 0 and batches as an empty list

*Step it builds toward:* `g1.r1.sc4` — The file is written on the auto branch only and before any request file, and is still written when the plan came out empty; the explicit-integer branch and the dataset-is-None path never write it.

*Drafted as:* one more on the zero row doc — num_requests 0, num_bytes 0, and batches is an empty list, not a key we leave off.

*Why there:* No listed room is discussing the batch payload plan document at all. The releases days are cut timing and sign-off; the engineering days are semaphore/OOM and llama4 scoping; cookbooks is auth docs and the `.choices` grep; viewer is local-viewer removal. #code-review 2025-04-14 is the closest since Emil pastes a metadata schema, but that thread's live question is PR 632/626 ordering and the schema is only evidence they don't overlap — a zero-row field list there answers nothing and would draw no reply. Decisive: the sibling remark assigns whether the file is written, what num_batches reads and what the id comes out as to nils and emil, and nils is not present in any candidate conversation. The remark is one turn in a plan-schema thread that isn't among the options.

*Still leaves open:* whether the file is written at all on a zero row run, what num_batches reads, and what the id comes out as — nils and emil have those.

*Must appear literally:* `num_requests`, `num_bytes`, `batches`

*A new conversation in #incidents on 2025-03-14:*

```
09:38  marek: the empty shard from last night's rerun — sh-0007, nothing routed to it — the plan doc it wrote back is missing half its keys and the loader keyerrors on it. before i patch the loader, what's that doc supposed to look like when there's genuinely nothing to send
09:44  dermot: so the doc itself serialized fine and the problem is that the writer drops the fields when they're empty, and downstream we assume they're there — is that the shape of it? asking because if it's the writer i'd rather fix it there than teach every reader to tolerate a hole
09:46  marek: yeah that's it. writer's got a `if v:` filter on the way out so anything zero or empty vanishes. plan doc for the empty shard is basically just the shard id and a timestamp
09:51  dermot: right, drop the filter then. the zero doc is a real row, it just has nothing in it. num_requests 0, num_bytes 0, both written out as zeros — a counter that's absent and a counter that's zero are not the same claim and we shouldn't be making the reader guess which one it's looking at
09:54  marek: ok that unblocks the counters. the list is the one i'm less sure about though — do we write it as an empty container, or is it fine for the key to just not appear when no batches got planned? current reader does a .get with a default and iterates, so it can't tell the difference, but the json diff against the sample doc definitely can
09:59  dermot: yeah ok, one more on the zero row doc — batches is an empty list, not a key we leave off. same reasoning as the counters, a missing key reads like the planner never got to that shard and an empty list reads like it got there and found nothing to do, and at 2am on a late night those are very different things to be staring at
10:02  marek: makes sense. nobody's on the writer yet, i'll raise it in standup so it doesn't sit for another week
```

#### `g1.r1.say25` — scope

**dermot**, 2025-03-18, #releases

> one more on the zero row case — create_request_files hands back an empty list there, so there's no requests_0.jsonl sitting around with nothing in it.

*What a reader should take from it:* the team agrees create_request_files returns no request file paths at all for an empty dataset

*Step it builds toward:* `g1.r1.sc4` — The file is written on the auto branch only and before any request file, and is still written when the plan came out empty; the explicit-integer branch and the dataset-is-None path never write it.

*Drafted as:* one more on the zero row case — create_request_files hands back an empty list there, no requests_0.jsonl sitting around with nothing in it.

*Why there:* None of the eight rooms is discussing batch request-file creation or empty datasets at all — they're on resume cost accounting, capability lookups, cancellation/job-id scoping, viewer download, image pinning, and semaphore gating. The nearest vocabulary match (#engineering 3/14, "row-creation") is an OOM-under-concurrency thread, and dropping a zero-row edge case into it would derail konrad chasing dermot for concurrency figures. Decisively, the remark opens as the second half of an exchange with nils, who is not present in any listed conversation, so there is no first half for it to pick up.

*Still leaves open:* whether anything at all gets written to the working dir for a zero row run, and what shape it has — that is nils's point in the same thread

*Must appear literally:* `create_request_files`, `requests_0.jsonl`

*A new conversation in #releases on 2025-03-18:*

```
10:42  ines: quick one before i forget — what does the writer actually do if a shard comes back with zero rows? we hit that on the rerun last week and i couldn't tell from the logs whether it wrote something or skipped
10:47  dermot: if i had to guess it never gets far enough to write. create_request_files sees an empty frame and just hands back an empty list of paths, so the loop downstream has nothing to iterate over
10:49  ines: right but the empty list is the return value. does it still touch disk on the way out? the run that broke left a pile of junk in the working dir and i'm trying to work out if a zero row shard is part of that
10:54  dermot: no, nothing gets opened. so there's no requests_0.jsonl sitting there with nothing in it — the file only comes into existence if there was a row to put in it
10:56  ines: ok good, that's what i was hoping. means the cleanup pass doesn't need a special case for zero byte files
11:01  dermot: mhm. that said whoever picks it up should make the empty branch explicit in the writer rather than leaning on the frame being falsy. late night me is not going to remember why it happens to work. not entirely sure which ticket that hangs off
11:03  ines: i'll grab it, can ride along on the sizing one
```

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
13:41  gideon: so i pointed the auto sizing path at a table that came back with zero rows this morning, just to see what happens. the working dir afterwards is completely empty. no plan file, no batch dirs, literally nothing in there
13:42  gideon: which i did not expect tbh, i assumed there would at least be a stub sitting there
13:47  dermot: if i had to guess the serializer never gets reached on that path. zero batches, so the thing it writes from has nothing to iterate, and it returns before it ever opens a handle. nobody wrote the empty case, it just falls out of the loop being empty
13:53  gideon: ya thats what it looks like from the trace. the problem is my checker only polls that directory. an empty dir and the process dying halfway through look exactly the same from outside, theres nothing in there to tell them apart. so a legit zero row run reads as a crash and i cant distinguish them
13:59  nils: let me think through that. i think the fix is that we write the file regardless — even when there is nothing to size at all, the file still lands. a run that produced nothing still ran, and it should leave evidence of that on disk. Otherwise you are asking the absence of a file to mean two different things
14:02  emil: yup, sounds right. so its a real plan file in the normal spot, not some sentinal marker — just with num_batches sitting at 0? nothing has been written against that yet fwiw, the writer still early-returns, so someone has to actually go in and do it
14:06  nils: yeah, num_batches 0, and otherwise the same shape as any other plan, empty batch list. the directory itself is already there by that point anyway, the sizing pass mkdirs up front before it decides anything, so it is only ever the file that goes missing today
```

> **Problems:** longer than one remark

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

> **Problems:** longer than one remark

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
From: None  To: 


From: None  To: 


From: None  To: 


From: None  To: 


From: None  To: 


From: None  To: 


From: None  To: 


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

*5 remarks — 0 reporting the problem, 5 settling the design.*

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
13:24  emil: gideon the thing you were poking at yesterday on the auto sizing run — am i right that the slowness was mostly the sheer number of request files, and not anything in the submit path itself?
13:29  gideon: ya more or less. so basically auto split one job into about 2600 request files, i counted them in the plan dir because i didnt beleive the first number
13:30  gideon: and then the submit loop crawled all afernoon. it never actually failed which is the annoying part, it just kept grinding
13:33  dario: hm. so at that size do we want it chunking itself into a few smaller plans, or does it just not go? i dont love either honestly but i think i like the silent chunking less
13:37  emil: we need to be intentional here. a warning line at plan time gets scrolled past, i've watched it happen more than once, and chunking behind someone's back means the plan sitting on disk isnt the plan they asked for
13:41  gideon: ya exactly. so past some ceiling it should refuse to plan at all, not run it — planner errors out right there and you never get a plan file, instead of building 2600 entries and letting the submit loop discover it. nothing does that today obviously, the planner just takes whatever the estimator hands back and writes it out
13:44  dario: mhm, that tracks. though im still curious what the estimator was doing to land on 2600 for a single job, that smells like it sized off token count and not rows
```

> **Problems:** longer than one remark

#### `g1.r1.say28` — failure_behavior

**gideon**, 2025-03-17, #viewer

> so basically [10] * 512 at one row per batch planned all 512 and came back clean, 513 is the first count that refuses - we bail past the ceiling, not at it.

*What a reader should take from it:* the team agrees a plan of exactly 512 batches is accepted and only 513 or more is rejected

*Step it builds toward:* `g1.r1.sc5` — A plan split into more batches than a configurable ceiling, defaulting to 512, is rejected with a dedicated error carrying the batch count and the ceiling, distinct from the oversize-payload errors, and checked only after the per-row oversize scan.

*Drafted as:* so basically [10] * 512 one-per-batch planned all 512 and came back clean - 513 is the first count that refuses. we bail past the ceiling, not at it.

*Why there:* None of the listed rooms is chewing on batch-payload planning limits at all. The two batch-flavoured threads are about something else entirely: #pipeline 2025-04-07 is Gemini finish-reason/cancellation fixes and the resume-path cost mispricing, and #pipeline 2025-04-22 is the batch-mode ordering root-cause fix, the Anthropic token-count issue, and who reviews PR 632. #engineering 2025-04-16 is cost-streaming skew and throttling, #viewer 2025-04-28 is the metadata panel, #code-review 2025-03-14 is schema_check at construction (adjacent in spirit — validate before you do the work — but it is a March thread about model/response_format compatibility, with no planner and no ceiling). Dropping a boundary-test result for a 512-batch cap into any of them changes the subject and would draw no reply. What is missing is the review thread on the planner PR itself, where a reviewer asks whether the max-batches limit is inclusive and Gideon reports the off-by-one check he actually ran — the same thread where the error type, the configurability of the ceiling, and its ordering against the per-row oversize scan get settled.

*Still leaves open:* which error 513 raises, what attributes it carries, that the ceiling is configurable, and where it sits relative to the per-row oversize scan - all of that is f2, f3 and f4's ground

*Must appear literally:* `[10] * 512`, `512`, `513`

*A new conversation in #viewer on 2025-03-17:*

```
09:47  dario: quick one on the batch planner while i have it open — when the ceiling says 512, is 512 itself a size we can actually plan, or is 512 already the thing that gets kicked back? i've honestly been reading the validator both ways all morning
09:52  gideon: so basically i poked at this yesterday because the sidecar was confusing me too. i handed it `[10] * 512` at one row per batch and it planned the whole thing. all 512, came back clean, nothing truncated in the plan file
09:53  gideon: so 512 is not the reject point, its a size you can genuinely ask for
09:58  dario: makes sense, though that only pins the top of the allowed range for me, not where the refusing starts. did you actually push past it or are we inferring? i think the difference matters, because one of those means the boundary is inclusive and the other means we just never tested the edge
10:04  gideon: ya i went one higher after. 513 is the first count that refuses — thats where it gives up. so we bail past the ceiling, not at it. you only see the error once you've already gone over, the ceiling itself is still legal
10:07  dario: mhm, that's the reading i wanted. in any case the error copy is wrong then, it currently says something like "up to 512" in a way that reads as if 512 were banned. should be phrased off 513 / "more than 512". i'll drop that on whoever ends up with the validator ticket, not touching it today
```

> **Problems:** longer than one remark

#### `g1.r1.f2` — failure_behavior

**konrad**, 2025-04-08, #code-review

> look, my except BatchPayloadTooLargeError sailed straight past BatchPlanTooFragmentedError — err.num_batches 513, err.limit 512 off the default. right call, its own ValueError, my handler shoud not touch it.

*What a reader should take from it:* the team agrees the fragmentation failure is a separate ValueError, not caught as a payload-size error, and carries the count and the ceiling

*Step it builds toward:* `g1.r1.sc5` — A plan split into more batches than a configurable ceiling, defaulting to 512, is rejected with a dedicated error carrying the batch count and the ceiling, distinct from the oversize-payload errors, and checked only after the per-row oversize scan.

*Drafted as:* My except BatchPayloadTooLargeError sailed straight past BatchPlanTooFragmentedError: 513 batches, limit 512. Right call, it is its own ValueError and my handler should not touch it.

*Why there:* Nothing in the listed rooms is chewing on batch payload planning or its exception hierarchy. The closest is #code-review 2025-04-02, but that day is entirely PR 614's cancellation fix and the per-backend job ID scoping bug; a first-person report about an except clause missing BatchPlanTooFragmentedError would change the subject mid-thread and land on dermot and emil, neither of whom is anywhere near that code that day. #releases 2025-03-19 touches batch only as "gemini unicode corruption in batch output", and the rest (finetuning PRs, GEPA, cookbook verifiers, version tags) is unrelated. Konrad did say on 2025-04-02 that he hadn't started batch examples and was waiting for the API shape to settle — the natural home is a later thread where he actually starts writing against it and trips over the split limit, with dermot, who owns bulk-llm-inference and was unblocking batch testing.

*Still leaves open:* Doesn't say where 512 comes from, whether it can be overridden, or how it interacts with oversize rows.

*Must appear literally:* `512`, `513`, `BatchPayloadTooLargeError`, `BatchPlanTooFragmentedError`, `err.limit`, `err.num_batches`, `limit`

*A new conversation in #code-review on 2025-04-08:*

```
13:12  konrad: look, something odd out of the retry run this morning. my except BatchPayloadTooLargeError did not fire at all, the thing sailed straight past it and up to the top of the worker
13:13  konrad: what actualy came out was BatchPlanTooFragmentedError. presumably these are siblings? off the top of my head i assumed one caught the other
13:19  gideon: nope, they don't inherit from each other. so basically the fragmented one is its own ValueError subclass sitting next to the payload one, not under it. honestly though they are different failures - one is "this single batch is too fat to send", the other is "you sliced the plan into too many pieces"
13:24  konrad: mhm. and the fields are not the same either then? the traceback had err.num_batches printed on it which my handler never reads, so maybe that is why the format string blew up after
13:29  nikolai: right thats the fragmented one it carries err.num_batches and err.limit and nothing else
yours was 513 batches against err.limit 512 and nobody set that on the run its just the default limit we ship
13:33  konrad: 513 over 512, one single batch over the line. anyway that settles it for me - its own error with its own fields is the right call, my handler shoud not be touching it at all. i will leave the payload catch as is and let the fragmented one keep going up
13:36  gideon: exactly. and tbh the fragmented one deserves its own path where it actually reports the count back instead of dying in the worker, um, whoever ends up writing that. i dunno if it makes this release or the next ticket
```

> **Problems:** longer than one remark

#### `g1.r1.f4` — failure_behavior

**emil**, 2025-06-16, #engineering

> 600 rows of 10 bytes plus one 5000 byte row under a 1000 byte cap and it said too fragmented instead of naming row 600. per-row oversize reports first.

*What a reader should take from it:* the team agrees the per-row oversize check reports first, ahead of the fragmentation check

*Step it builds toward:* `g1.r1.sc5` — A plan split into more batches than a configurable ceiling, defaulting to 512, is rejected with a dedicated error carrying the batch count and the ceiling, distinct from the oversize-payload errors, and checked only after the per-row oversize scan.

*Drafted as:* 600 rows of 10 bytes plus one 5000 byte monster under a 1000 byte cap, and it told me the plan was too fragmented instead of naming row 600.

*Why there:* None of the listed rooms is chewing on batch payload planning at all, let alone the precedence of the planner's validation errors. The closest is #engineering 2025-06-13, but that thread is about whether PR 691's auto-batch trigger is a flag or detection and whether the Pydantic fix is clean across services — a size-cap/oversize-vs-fragmentation report ordering would land there as a subject change nobody picks up. #code-review 2025-05-08 is batch-adjacent but pinned to one serialization bug and one GCS path in PR 654, and Emil spends the day stuck on that, not running cap experiments. #engineering 2025-03-14 is about concurrency-driven OOM at row creation, not per-row byte caps. What's missing is the conversation where Emil actually exercises the planner's failure modes after auto-batch detection lands and the team settles which error a plan reports when a row is both oversize and the rest is fragmented.

*Still leaves open:* Doesn't say what the fragmentation ceiling is or what the error type and attributes are.

*Must appear literally:* `5000`, `1000`, `600`

*A new conversation in #engineering on 2025-06-16:*

```
13:44  nikolai: ran a synthetic file through the batch splitter this morning and the failure it came back with is useless
13:46  nikolai: input was 600 rows of ten bytes each and then one row on the end thats 5000 bytes, cap set to 1000. all it said was the input was too fragmented to batch
13:53  emil: let me think through that. i'm fairly sure the fragmentation line is just the fallthrough — the packer does its pass, notices it didnt place everything, and emits that. it has no idea *why* anything is left over, so it reaches for the only explanation it knows about
13:55  nikolai: ok but the why is not subtle here. one row is five times the cap, its never going into any bin. it should be telling me which row instead of making me diff the input to find it
14:01  emil: yup, agreed, and honestly the fix is upstream of the packer entirely. Walk the rows first, anything over the cap gets reported on its own terms with its index — for your file thats row 600, zero indexed — and we never get as far as saying anything about fragmentation. the fragmentation message only makes sense once every row is individually placeable
14:03  nikolai: does it bail on the first one it finds or keep going
14:05  emil: collect them all and print the lot, i believe. one oversize row is very rarely one oversize row in practice
```

#### `g1.r1.f3` — failure_behavior

**nikolai**, 2025-06-18, #code-review

> test builds BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes so i dont have to construct 513 spans, then asserts err.num_batches == 3 and err.limit == 2

*What a reader should take from it:* the team agrees the ceiling is a third BatchLimits field named max_batches_per_plan that callers can set, and the error exposes num_batches

*Step it builds toward:* `g1.r1.sc5` — A plan split into more batches than a configurable ceiling, defaulting to 512, is rejected with a dedicated error carrying the batch count and the ceiling, distinct from the oversize-payload errors, and checked only after the per-row oversize scan.

*Drafted as:* test builds BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes so i don't have to construct 513 spans, then asserts err.num_batches == 3.

*Why there:* None of the listed rooms is chewing on batch planning internals. The closest is #code-review 2025-06-16, where PR 691 ("batch size automation") comes up — but that whole thread is about whether 691 is even write-up ready, and emil says it's still being worked; nikolai hasn't reviewed it, so a specific test-construction detail from him there would contradict the day. The other threads are release tagging, cookbook verifier paths, PR-state visibility and workstream bookkeeping — a BatchLimits assertion arrives from nowhere in all of them. What's missing is the actual review of 691 once it got its write-up: nikolai reading the planner, emil defending the ceiling, and the sibling questions (what the default is, what the error is called, whether it fires before or after oversize rows get rejected) getting settled in the same thread.

*Still leaves open:* Doesn't say what the default ceiling is, what the error is called, or when the check runs relative to oversize rows.

*Must appear literally:* `BatchLimits(1, 1000, max_batches_per_plan=2)`, `err.limit == 2`, `err.num_batches == 3`, `max_batches_per_plan`, `num_batches`

*A new conversation in #code-review on 2025-06-18:*

```
14:02  emil: question on the batch planner tests while i'm in there — how are we actually exercising the path where a plan runs past the batch ceiling? every version of that fixture i sketch out ends up enormous, i'm generating input for ages just to trip one guard
14:06  nikolai: dont grow the input shrink the limit
in the test just build BatchLimits(1, 1000, max_batches_per_plan=2) and hand it three sizes
14:09  emil: let me think through that. so rather than feeding it enough work to naturally spill into four or five batches, you drop max_batches_per_plan to 2 and give it just barely enough to make three. thats the whole trick? mostly to keep the fixture readable i assume
14:12  nikolai: yep thats the point so i dont have to construct 513 spans just to get it over the line
nobody is reading that test twice
14:16  emil: sounds right. though is the assertion just that it raises? honestly that feels thin to me — i'd want to know the error is reporting the right numbers back and not merely blowing up with something generic, we need to be intentional here becuase that message surfaces to users
14:20  nikolai: no its checking both fields off the error
err.num_batches == 3 and err.limit == 2
num_batches is what it actually planned out limit is what it was allowed to plan
14:23  emil: yup thats enough for me. i'd keep it off 690 though, that review already has plenty moving around in it
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
13:38  nikolai: when a run dies partway through submit how is the resume path meant to figure out which requests went into which batch
right now im re deriving the ranges off the request files themselves and its wrong the second a batch gets split for size
do we need to drop a plan file next to the payloads or
13:44  dermot: so the guess is a plan.json sitting alongside the request files, one per run? i don't think it needs to be a new artifact. that information belongs in metadata_{i}.json — we already emit one of those per batch at submit time, so there is somewhere to put it that the resume path can already find
13:47  nikolai: ok but metadata today is what, model name submit timestamp the request id
none of that tells me rows 4000 through 8000 landed in batch 2 and if i dont know that the reducer stitches the responses back in the wrong order
totals alone dont get me there
13:52  emil: let me think through that. i believe the top of it wants num_jobs at minimum, so you know how many batches you're waiting on before you go opening any of them. beyond that im not entirely sure what the per batch entry looks like, dario was the last one in the serializer
13:58  dario: yeah num_jobs at the top, and then per batch you get start_idx, end_idx and num_bytes. thats the ordering and the size without having to read a single payload back off disk.

and the reason it lives there rather than in somethign of its own is honestly just that we're already writing metadata_{i}.json for every batch anyway — a second plan file next to it is a second thing that can drift out of sync with the first, and that bites you months later when nobody remembers which one is authoritative. in any case, one artifact per batch is the best we can do here i think
14:02  dermot: mhm. num_bytes is in there already for the size ceiling check, so realistically it's only the two indices that are actually new
```

#### `g1.r1.h2` — herring

**konrad**, 2025-01-22, #engineering

> Right, so metadata_0.json comes out as {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}. The span and the size both live in the per-batch metadata, that's the shape.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* Right, so metadata_0.json is {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}. Span and size live in the per-batch metadata. That's the shape.

*Why there:* None of the eight rooms are looking at the on-disk batch payload artifacts. The closest is #engineering 2025-01-27, where Konrad is chasing PR 403 and asks whether generation params ride on each batch item or get set once at the job level — but that thread is about param routing and cost-calc scope, and a file listing of metadata_0.json with start_idx/end_idx/num_bytes answers a question nobody in that room asked; it would land with no reaction. The two #code-review batch mentions (PR 584 factory shape on 03-13, PR 403 references) are about class structure and review scheduling, not the shape of the written files. What's missing is a thread where someone actually opens the batch working directory: Konrad, while tracing the Gemini batch path for PR 403, wants to know how a request maps back to its chunk on resume, dumps what the writer produced, and Dario (who owns the request-processing side and said params leave provider-integrations fine) confirms which fields are authoritative for the span versus what gets recomputed. That's a #pipeline conversation the week after the 01-27 thread, and it would also cover whether num_bytes is what the size cap is checked against before a chunk is closed.

*A new conversation in #engineering on 2025-01-22:*

```
10:09  dario: quick one on the plan serialization — when we write a plan out, is there one manifest for the whole run or does every batch get its own thing next to it
10:11  konrad: per batch. the first one lands as metadata_0.json sitting beside the payload, then _1 and so on
10:12  konrad: contents is num_jobs plus where the batch sits in the request list. off the top of my head for the two job case it reads {"num_jobs": 2, "start_idx": 0, "end_idx": 2, ...} , end is exclusive
10:13  dario: ok that gives me the span. but is there anything in there for how big the payload is, or do i have to stat the file to find out
10:15  konrad: right, num_bytes is the other key. 307 for that same little one. so span and size both live in the per batch metdata, there is no seperate size manifest anywhere
10:16  dario: that's better actually, saves me the extra stat in the loader. nobody's written it yet though has anyone
10:18  konrad: not yet no. presumably it goes on the sidecar ticket, maybe whoever picks that up. anyway i am not getting to it today
```

#### `g1.r1.rev1` — rule, scope, exclusions_or_crossover

**dario**, 2025-04-24, #code-review

> a week of resume runs choking on keys they didn't expect, so the plan's out of metadata_{i}.json into a sidecar: batch_plan.json in the working dir, plan_format_version 1, auto branch only

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* the plan riding in metadata_{i}.json is gone — a week of resume runs choking on keys they didn't expect. it moved out to one sidecar, batch_plan.json in the working dir, plan_format_version 1, written in the auto branch only.

*Why there:* Gideon opens the day by putting Dario's first pass up for review — it reads batch_objects.jsonl on startup, reattaches by id, and touches caching-and-resume, with "a few things worth looking at before it goes in." A note from Dario about what the on-disk resume artifacts look like in that change is exactly what the author of that PR would post into that room while reviewers are picking it up, and it lands in the same subsystem the rest of the day (cache writes, silent resume breakage) is chewing on. Nobody there has said anything about where the plan is persisted, so it isn't redundant, and Dario is the caching-and-resume owner.

*Must appear literally:* `metadata_{i}.json`, `batch_plan.json`, `plan_format_version`, `1`

*Goes into the real conversation in #code-review on 2025-04-24, after 09:36 gideon:*

```
09:00  dermot: bulk-llm-inference cleanup is mostly done, just tidying up the last few error paths before I put it up for review this afternoon.
09:36  gideon: Dario's got a first pass up for review, reads batch_objects.jsonl on startup and reattaches by id, touches caching-and-resume
09:36  gideon: Not blocking a release but has a few things worth looking at before it goes in   <-- THE REMARK GOES HERE
16:49  dermot: not entirely sure, but I think if the cache write fails it just swallows it silently
17:26  gideon: does it log the path anywhere when it swallows it, or is the failure completely invisible?
17:28  dermot: from what I can tell, completely invisible, no path anywhere.
17:59  emil: ugh, that's the exact thing
18:23  emil: That bare `pass` in the cache-write except needs to go, at minimum it should log a warning with the path.
18:24  emil: adjacent gripe, the one place we do already wrap a cache write in try/except, the except body is a bare pass
18:24  emil: burned an hour last week wondering why a rerun redid everything from scratch, turned out the write had failed on a permissions thing on a mounted dir 
18:26  dario: +1
```

#### `g1.r1.rev2` — exclusions_or_crossover, rule

**dermot**, 2025-04-03, #pipeline

> the resume path json.loads metadata_0.json and wants {"num_jobs": 2} and nothing else, so start_idx, end_idx and num_bytes came back out. that span and size sit in batch_plan.json under batches now

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* we pulled start_idx, end_idx and num_bytes back out of metadata_0.json — the resume path json.loads it and wants {"num_jobs": 2} and nothing else. that span and size sit in batch_plan.json now, under batches.

*Why there:* That thread is already about what does and doesn't get written to disk for a batch — dermot opened it asking whether the local batch record is written at submit or only after download, and dario's 15:01 question is specifically whether the submit path touches caching-and-resume. dermot answering with what the resume path actually reads out of metadata_0.json, and where the span/size fields went instead, lands directly on that. It's his file and his workstream, and nobody in the thread has said anything about the on-disk layout yet, so it isn't redundant.

*Must appear literally:* `metadata_0.json`, `{"num_jobs": 2}`, `batch_plan.json`, `batches`, `start_idx`, `end_idx`, `num_bytes`

*Goes into the real conversation in #pipeline on 2025-04-03, after 15:01 dario:*

```
09:00  dermot: bulk-llm-inference is stable, no blockers
09:00  dermot: been tidying multimodal-prompts this mornign, mostly done
09:00  dermot: emil spotted three batches on the openai dashboard that show as completed and paid for, no local record of any of them
09:00  dermot: not sure if it's a persistence gap or something in the submit path
09:56  dermot: do we write the local batch record at submit time or only once the download completes
10:59  dermot: @Emil do you have the batch IDs for those three from the dashboard
11:40  emil: good catch on the timing of that write
11:50  dario: If we're only writing a local record once the download comes back, the entire polling window is basically unrecoverable
11:50  dario: all the wall clock in a batch run is the poll loop, submit at 11, provider finishes around 6
11:50  dario: kill it at hour three and there's nothing on disk that so much as knows a job was ever opened. bitten me twice this week
12:04  dario: Worth checking whether the submit call is even awaited per-batch or fired in a gather, honestly not sure we'd have the batch IDs in hand to write anyt
12:59  emil: So we'd get the batch ID back even from a gather, just maybe not synchronously?
13:17  dario: I'm around this afternoon if anyone wants to dig into it
13:17  dario: @Emil is the submit awaited per-batch or do they all go into a gather?
14:08  dario: Is anyone actually pushing back on the polling window being unrecoverable, or is the open question just where the write goes?
14:33  emil: - *Polling window*: nobody's pushing back on that, agreed it's unrecoverable if we only write after download
- *Submit / gather*: I'd have to check th
15:01  dario: Is the submit path all in batch-mode or does it touch caching-and-resume at all?   <-- THE REMARK GOES HERE
16:18  dario: Has anyone written Dermot's ordering down anywhere, or is it still just sitting in this thread?
```

> **Problems:** longer than one remark


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
13:26  dermot: coming back to the batch payload plan - the part that decides how many request files it's going to write. if i had to guess the case we have no coverage for is the dir that isn't empty already, i.e. we point it at an output dir that's half written and it has to keep going from there instead of starting over. is that the hole
13:33  emil: yeah that's the hole. let me think through that - the way i'd build it is you don't run the thing twice to get there, you just make the directory look like a run already happened. put the request files down yourself, then run the plan once against it and see whether it picks up the numbering or stomps on what's there
13:37  dermot: mhm. how many do you lay down though, and does it need the sidecars too or is the requests enough. that said i'm not entirely sure what you'd assert on at the end, listing the dir feels a bit thin
13:41  konrad: look, i did this by hand yesterday to convince myself it even breaks. i seeded the dir with requests_0.jsonl through requests_5.jsonl, and the matchign metadata file alongside each one - without those the plan doesnt treat them as completed batches at all, it just ignores them
13:44  emil: right so six of them sitting there before anything runs. and then the plan is supposed to add what, some fixed number more? and you check that by...
13:47  konrad: three. you set the input size so there is exactly three batches left for it to make, and then the listing of the dir afterwards is the assertion, nothing else. 0 through 5 still there untouched plus the three new ones
13:47  konrad: anyway nobody has written it yet. off the top of my head it wants to ride on the resume ticket, whoever ends up with that
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

> yeah. and a requests_0.jsonl already sitting there gets swept with the rest and rewritten from this run's plan, its own start_idx to end_idx.

*What a reader should take from it:* the team agrees an auto run's output directory should reflect only that run

*Step it builds toward:* `g1.r2.sc1` — A fresh auto-sized run must not leave request or metadata files from any earlier run sitting in the working directory alongside the ones it just wrote.

*Drafted as:* i'd like the working dir after an auto run to hold what that run actually produced, not a mix of that and something older.

*Why there:* That thread is already chewing on exactly this failure: emil's `.curator_batch` file left in the working directory from an earlier run made a rerun reattach to the old job and hand back answers for the old prompts, and dermot has been pushing on what resume state does when things change between runs. He opened the thread and is the one framing what the desired behaviour is, so a stance from him on what the working directory should look like after a run lands naturally right after emil's account. Nobody has said this yet — emil describes the symptom, dario says the key goes stale, neither states what the directory ought to contain — and it stops short of which file kinds, which other paths, or when in the run the cleanup happens.

*Still leaves open:* Which file kinds that covers, whether other paths do the same, and when in the run it happens.

*Must appear literally:* `end_idx`, `requests_0.jsonl`, `start_idx`

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

> **Problems:** longer than one remark

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
10:41  mira: quick one before i keep going on the auto sizing branch. if someone passes a batch size explicitly, does the sidecar still get consulted at all? reading the plan builder i genuinely cant tell if the explicit value is a floor or just a starting hint for the sizer
10:46  dario: neither, i think. explicit is explicit — if you hand it batch_size=1000 the planner shouldnt be asking the sidecar anything at all, it chunks at 1000 and thats the end of the decision. the sizer is only there for the case where nobody said
10:49  mira: ok that part i follow. the bit im stuck on is downstream of it though. the auto path changes what the writer emits — batches come out different lengths so the per file widths stop being uniform. does that land on the explicit path too, or
10:55  dario: no. honestly explicit batch_size=1000 should keep giving the same fixed width files it always has, same as what shipped, nothing about the on disk shape moves for anyone who was already passing a size. and to be honest as the branch stands right now it does route both through the new sizer, which is how the friday run came back with that ragged tail file. that needs undoing before it goes anywhere
10:58  mira: so the sizer just doesnt run there. even though its already wired into that call site and it'd technically produce the same answer for a fixed size
11:02  dario: right, keep the fixed path on the old writer call. i dont want that branch picking up new behaviour off the side of the auto work — even if the numbers happen to agree today, thats the sort of thing that quietly stops agreeing in six months and nobody remembers why. two paths, one of them frozen. in any case the sidecar output can still get written into the plan either way, nobody reads it on the explicit side, its cheap to leave
11:04  mira: mhm. then ill leave sizing_mode on both, its already in the serialiser and yanking it back out is more churn than just letting it sit there
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

*A new thread — **mail: resumed batch run double-submitted ~400 requests**, 2025-04-17:*

```
From: None  To: 


From: None  To: 


From: None  To: 


From: None  To: 


From: None  To: 


From: None  To: 


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
10:07  petra: billing pinged me about the mar 11 numbers. same shard shows up submitted twice on friday's run. did someone kick it off by hand?
10:09  gideon: no it was the scheduled one both times, i checked the trigger. so basically between the two runs the working dir got emptied out, someone ran rm -f over it, i am pretty sure its the cleanup step in the wrapper scrpit
10:11  petra: thats just scratch though right. tmp shards and the log. why would wiping it make anything resubmit
10:13  gideon: because responses_0.jsonl lives in there too, thats where the completed batch lands before the merge step picks it up. so the second run looks in the dir, sees nothing, decides the batch never happened and submits the whole thing over again. we paid twice for a batch we had already completed, tbh thats the part that bugs me, the data was fine, we just bought it a second time
10:15  petra: oh thats grim. so we stop rm -f ing the dir and thats that?
10:17  gideon: partly ya but honestly though the disk should not be the thing we trust in the first place. the batch ids want to go into a manifest that lives outside the working dir, and then on startup we ask the provider for the status of every id in there before we submit anything at all. if one comes back completed we just download the results again instead of paying for it
10:18  petra: ya ok. thats clearly the right shape. ill leave the cleanup step alone in the meantime so we dont eat it again
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
10:09  tomas: question for whoever knows the working dir layout - can the cleanup step just wipe the whole run directory between runs? right now we leave everything and the disk usage on the box is getting silly
10:10  tomas: i have it as one rmtree on the root right now which is obviously the lazy version
10:14  nils: let me think through that - it depends which half of that directory you mean. the plan json, the per batch manifests, the request logs, all of that gets rebuilt in seconds, i have no attachment to any of it
10:17  tomas: thats the half thats big though? or is it. i assumed the manifests were the bulk of it

so is there something in there we actually cant lose, or is it more that you'd rather keep it around for debugging
10:21  nils: no, its the shard dir. the .arrow shards in the working dir are the dataset itself, thats not a cache of anything - the loader reads straight off them when it builds the batches
10:24  tomas: huh. i had those filed in my head as materialized from the parquet in blob storage, so if we blew them away we'd just pull again and eat a download
10:27  nils: the parquet is pre tokenization, so theres nothing upstream to pull that would help. drop those and we re-tokenize four million rows before anything even gets submitted, ie you pay it whether or not the run ends up going anywhere. so the sweep gets the plan dir and the logs and leaves the shards where they are
10:29  tomas: ok yeah. that means cleanup cant take a root path anymore, it needs the list of things its allowed to touch. nothing written yet, im still in the config loader
```

#### `g1.r2.l10` — exclusions_or_crossover

**dario**, 2025-04-09, #incidents

> not that i've seen. batch_objects.jsonl is unrecoverable state - the sweep doesn't just leave it in place, it leaves the bytes untouched, same for everything it isn't deleting.

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

> **Problems:** longer than one remark

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

*4 remarks — 2 reporting the problem, 2 settling the design.*

#### `g1.r2.l14` — observability, failure_behavior

**nikolai**, 2025-03-14, #cookbooks

> fixture pins max_bytes_per_batch to 400 and feeds a 600 char prompt - SingleRequestTooLargeError comes back with row_idx 1 on it, thats how we know which row blew up.

*What a reader should take from it:* the team agrees the failing fixture uses a 400-byte cap and an oversized single row

*Step it builds toward:* `g1.r2.sc4` — When sizing fails and no plan comes back, the working directory must be left exactly as it was found, stale files included.

*Drafted as:* Fixture pins max_bytes_per_batch to 400 and feeds a 600-char prompt, so row 1 raises SingleRequestTooLargeError before anything comes back.

*Why there:* None of the eight rooms is anywhere near batch payload sizing. 04-04 is PR merge-state visibility; 05-21 is agent response shape; 04-29 is num_gpus and stdout removal; 04-16 is docker image pinning and Dermot's resume-ignores-model bug; 04-11 and 05-06 are release notes; 2026-01-22 is README/examples coverage; 05-30 is the review queue plus sandbox guarantees under a caller-supplied image. A fixture pinning max_bytes_per_batch would land in any of them as a subject change with no reply. The thread that should exist: #engineering, nikolai and dario (he owns bulk-llm-inference and has already carried the batch cancellation fix and lazy batch download), triggered by a run dying on an oversized single row. Nikolai builds the minimal repro to establish the failure is per-row and not per-batch; the rest of the thread is what the request/response files on disk look like after the raise, and whether the run is resumable from that state — which is the sibling remark's territory, not this one's.

*Still leaves open:* What the directory should look like once that raise happens.

*Must appear literally:* `400`, `600`, `SingleRequestTooLargeError`, `max_bytes_per_batch`, `row_idx`

*A new conversation in #cookbooks on 2025-03-14:*

```
10:41  dario: does anything actually cover the single-request-over-the-cap path? i went digging through the batcher tests this morning and all i can find is the happy split, batches come out under the limit, assert the counts, done
10:44  nikolai: not yet no its the cheap one to add though the fixture just pins max_bytes_per_batch to 400 and feeds it a prompt thats 600 chars so theres no batch anywhere it fits
10:48  dario: right, so it can't place it at all. what does it do with it though — skip the row and carry on, or does the whole plan fall over
10:51  nikolai: SingleRequestTooLargeError and it comes back before any batches get built i mean theres nowhere to put the thing so theres no plan to hand you
10:54  dario: ok, i'm fine with that. the bit i keep chewing on is debugging — someone's got 40k prompts in a jsonl and one of them is fat, a bare exception type doesn't tell them which one
10:57  nikolai: the error carries row_idx thats the whole point of it being on there in the fixture its 1 you read the index off the exception and thats the row that blew up
11:02  nikolai: 400 is arbitrary btw off the top of my head anything under the prompt length trips it 400 just reads obvious sitting next to 600
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
10:41  dario: question on the plan version fixture before i keep going — the way its written now it makes a tmp dir, runs the writer, asserts plan_format_version comes out 2. and it passes. but honestly i cant tell if its passing because the migration works or just becasue theres nothing there to migrate
10:47  nils: let me think through that. i think you've more or less answered it in the asking — an empty dir hands you a 2 for free, the writer never takes the upgrade branch at all, it just writes current. so for the fixture to prove anything the directory can't be empty when the run starts.
10:52  dario: mhm, that tracks. "not empty" is doing a lot of work there though. dropping any old junk file in wont trip it either, the writer only looks at the one path. so is it the file being present, or the file having the wrong contents
10:58  nils: Both. batch_plan.json has to already be sitting in the dir when we start, and what's in it has to be a stale plan_format_version 1 body — the old field layout, the ranges written the way v1 wrote them. then a 2 on disk at the end actually means the writer read something old and rewrote it, rather than never having looked.
11:03  dario: ok so the fixture carries the v1 file as a checked in blob and the test copies it into the tmp dir first. thats actually less work than i had in my head, i was going to build the thing field by field in the test body
11:06  nils: a literal file is much easier to eyeball when it does break, and that's worth documenting in a line above it. i'd lift the one we pulled off the february run rather than invent the fields, since we know that one round tripped badly.
11:09  dario: the feb one still has the duplicated batch id in it fwiw. ill trim that out before it goes in
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
11:02  emil: so i re-ran the auto sizing path over the same working dir this morning and the plan came back with nine batches when the sweep had settled on six. took me a while — requests_6.jsonl through requests_8.jsonl were still sitting on disk from the run before, when the batch size was smaller. nothing removes them
11:09  dermot: so if i'm reading that right, a second run only overwrites the files it happens to produce this time, and anything with a higher index from the previous run just survives and gets counted? not entirely sure whether metadata_*.json has the same problem or if those get rewritten wholesale
11:16  emil: yup, exact same problem, metadata_6.json and friends were still there too. Honestly i dont think the plan builder looks at the directory at all before it starts writing, it just writes what it has and whatever else is lying around is somebody elses problem
11:24  dario: yeah we should just clear them out on entry i think. glob requests_*.jsonl and metadata_*.json in the working dir and unlink, before anything in there gets touched. its not like theres anything in a stale one we want, the whole point is the sizes changed
11:31  dermot: mhm. where does that sit relative to the sweep though — if i had to guess you'd want the clear after it, since the sweep is what tells you the batch count in the first place. that said the sweep is reading out of the same directory, so
11:40  dario: in any case the sweep is the first thing in the auto branch, so the clear goes ahead of that — nothing else has run at that point, its litterally the top of the branch. then plan_request_batches runs against a clean dir and whatever comes out of it is the entire plan, no archaeology
11:47  emil: sounds right. and the sweep does a couple of trial encodes into that same dir on the way to picking a size, so if the clear went after it wed be wiping the thing we just measured
```

#### `g1.r2.h2` — herring

**konrad**, 2025-01-21, #cookbooks

> look, order in the auto branch is settled: we delete the old requests_*/metadata_* files first, plan_request_batches second. nothing new gets writen next to stale numbering.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* Order in the auto branch is fixed: delete the old requests_*/metadata_* files first, plan second. Nothing new gets written next to stale numbering.

*Why there:* None of the listed rooms are chewing on batch payload files or resume-time cleanup. The closest, #code-review 2025-01-27, is about parameter passing for PR 403 (temperature/max_tokens vs batch_size) — a settled statement about deleting stale requests_*/metadata_* before plan_request_batches would land there as a subject change with no one to answer it, and Konrad on that day is asking questions rather than announcing decided ordering. The other candidates are multimodal/cost-map stability, sandbox uid, onboarding, WS-033 and PR triage; none touch the batch processor's file layout. What should have existed is the follow-up to Emil's "I'll dig into it first thing tomorrow" on PR 403: Emil's morning pass turns up a resume case where a rerun plans new batches alongside leftover requests_*/metadata_* from the previous run, and Konrad closes the ordering question for the auto branch while Dario weighs in from the request-processing side.

*A new conversation in #cookbooks on 2025-01-21:*

```
09:41  dermot: the auto sizing rerun yesterday, i went back through the output dir. we dropped the target from 5k to 2k so it planned 5 batches, but the directory had requests_0 through requests_11 in it. seven of those were from the run before. am i right that nothing clears that dir ahead of planning?
09:44  dario: yeah, nothing does. actually the planner only writes the files it produces, it has no opinion at all about what was sitting there first. so on a shrink you keep the tail of the old run, requests_5 onward, and the matching metadata_ files too, and they look exactly like real batches from the outside
09:46  konrad: look, order in the auto branch is settled — this was the thing we went around on friday. the old requests_* and metadata_* files get deleted first, thats the first thing that happens in that path. anyway nobody has writen any of it yet, its still just the decision
09:48  dermot: first as in before each file is written, or first as in before the planning call at all? if i had to guess you mean plan_request_batches doesn't get entered until the dir is clean
09:51  konrad: right, before plan_request_batches. delete is one, plan_request_batches is two. that way nothing new ever gets writen next to stale numbering, which is the whole point of doing it in that order
09:54  emil: yup. and honestly the metadata_ ones were the worse half of it — the leftover requests_ files i could at least eyeball by size, but the stale metadata_ is what fed the row count check on monday and made it come back green
```

#### `g1.r2.rev1` — rule, failure_behavior

**dario**, 2025-03-19, #releases

> sweep isn't first in the auto branch any more - it wiped a working dir when plan_request_batches threw SingleRequestTooLargeError, so requests_*.jsonl and metadata_*.json clear only after planning returns

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* the sweep isn't the first thing in the auto branch any more, we moved it. it wiped a working dir when plan_request_batches threw SingleRequestTooLargeError, so now we clear requests_*.jsonl and metadata_*.json only after planning returns.

*Why there:* No listed room is on batch payload planning or working-dir cleanup. #pipeline 03-31 is Mistral auth staying provider-side; #pipeline 04-07 is whether gideon's 10x resume cost bug is in scope for ws-050, and a destructive-sweep fix would cut across dario's own attempt to close that. #code-review 03-14 (schema_check at construction) and 04-14 (who takes PR 632) are review-logistics threads, #help 03-27 is executor image digests, #engineering 04-28 is serving-infra ownership, #cookbooks 05-05 is the `.choices` grep. The remark is a settled fix reported after a user hit data loss; it needs the day that report landed. dario is the right author — he owns bulk-llm-inference and caching-and-resume, as he states on 04-28 — but the room for it doesn't exist yet.

*Must appear literally:* `plan_request_batches`, `SingleRequestTooLargeError`, `requests_*.jsonl`, `metadata_*.json`

*A new conversation in #releases on 2025-03-19:*

```
13:12  konrad: Question about the auto-sizing branch. Gideon lost his working dir this morning, the requests_*.jsonl and metadata_*.json were just gone and nothing came back to replace them. anyway is that expected or did he do somethign odd on his end
13:19  emil: let me think through that. the sweep sits right at the top of the auto branch, before anything gets planned. so if the planning step doesnt come back you've already paid for the delete and got nothing out of it. i believe that's what he walked into
13:23  konrad: right but what makes the planning step not come back. off the top of my head it either sizes the batches or it doesnt
13:31  dermot: plan_request_batches raises SingleRequestTooLargeError when one row won't fit inside a batch on its own. nothing catches it in the auto path, it propagates straight out of the call. by that point the dir has already been emptied. if i had to guess gideon had one enormous prompt sitting in his input file
13:35  konrad: ok so what do we do, catch it or stop deleting first
13:44  dario: not catch it, that error is real and the run should stop there. what goes is the ordering we agreed back in whenever that was — in any case the sweep is the first thing in the auto branch, clear out requests_*.jsonl and metadata_*.json on entry, then plan_request_batches runs against a clean dir. that's gone, it cost gideon most of a day. the clearing moves down past planning: planning returns, then we remove the old files. if it throws, nothign on disk gets touched
13:49  emil: sounds right. the clean-dir thing was only ever there so stale shards from an earlier run don't get picked up, and that still holds if you clear after, just a bit later in the same call
13:52  konrad: mhm. someone should look at the sidecar as well, presumably it copied the same sweep over. not entirely sure whose ticket that lands on
```

#### `g1.r2.rev2` — rule, failure_behavior

**konrad**, 2025-03-18, #cookbooks

> That order is gone, deleting first cost you a split when the oversized row raised. plan_request_batches runs first now, we only sweep requests_*.jsonl and metadata_*.json after it returns a plan.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* That order is gone - deleting old requests_*/metadata_* first, planning second, cost Emil a perfectly good split when one oversized row raised. plan_request_batches runs first now, and we only sweep requests_*.jsonl and metadata_*.json once it hands back a plan.

*Why there:* No listed room is discussing batch request planning or the lifecycle of the request/metadata files. The nearest, #engineering 2025-03-19, is about token counts feeding the throttle check and the batch-mode cost estimation audit — Konrad's part there is deciding what blocks what, not reporting a landed reorder. #engineering 2025-03-14 shares the word "row" but is about semaphore gating and OOM under concurrent load. The remark also assumes everyone remembers Emil losing a split to a mid-plan raise, and nothing in the corpus establishes that incident, so wherever it lands the reader has to invent the backstory.

*Must appear literally:* `plan_request_batches`, `requests_*.jsonl`, `metadata_*.json`

*A new conversation in #cookbooks on 2025-03-18:*

```
10:12  marta: konrad do you know what happened to the auto-sizing rerun from friday? the batch dir is empty. no requests_ files, no metadata json, and no plan either. like the run never touched it
10:15  konrad: yes i looked at this yesterday morning. it raised inside planning, there was one row over the payload cap
10:15  konrad: so it threw before it had writen anything to disk. the dir being empty is not the bug, it is the after effect
10:18  marta: after effect of what though. we still had the split from the tuesday run in there, i was going to rerun against it. that is just gone?
10:21  konrad: gone, yes, sorry. look, we settled the order in the auto branch a while back, november or so - delete the old requests_*/metadata_* first, plan_request_batches second, so nothing new gets writen next to stale numbering
10:22  konrad: that order is gone. deleting first is exactly what cost you the split when the oversized row raised, the delete already happened and then nothing came back to replace it
10:25  marta: ok but the stale numbering thing was a real problem, that is why we did it that way. if we stop deleting up front what stops a 3 batch run leaving batch 4 and 5 sitting there from before
10:29  konrad: plan_request_batches runs first now. we only sweep the requests_*.jsonl and metadata_*.json after it returns a plan, and at that point we know the count, so anything above it goes in the same pass. presumably that is cheaper anyway, one walk instead of two
10:31  marta: huh. the delete is still the first statement in that function on main, i was reading it this morning and could not work out why it was where it was
```

> **Problems:** longer than one remark

