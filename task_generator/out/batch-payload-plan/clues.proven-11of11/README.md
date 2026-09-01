# Clues for g1 — Batch payload planner for `batch_size="auto"`

39 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/latest`.

Clue window `2025-03-14` to `2026-01-27`; herrings before `2025-03-13`.

**Nothing here has been inserted into the corpus.** This is the plan: what each person says, where it goes, and why it belongs there.

## The task the agent is given

Replace the ad-hoc sizing loop used by `batch_size="auto"` with a pure, testable planner. Add `src/bespokelabs/curator/request_processor/batch_payload_planner.py` exporting: `@dataclass(frozen=True) class BatchLimits` with fields `max_requests_per_batch: int` and `max_bytes_per_batch: int`; `@dataclass(frozen=True) class PlannedBatch` with fields `index: int`, `start_idx: int`, `end_idx: int`, `num_requests: int`, `num_bytes: int`; `def payload_size_bytes(api_specific_request: dict) -> int` returning `len(json.dumps(d).encode())`; `def payload_bytes(sizes: Sequence[int]) -> int` returning the exact size of the `"\n".join(...)` file those payloads produce (`0` for an empty sequence); `def plan_batches(sizes: Sequence[int], limits: BatchLimits) -> list[PlannedBatch]` walking the sizes once in index order and greedily filling contiguous, ordered, exhaustive spans (`plan[0].start_idx == 0`, `plan[i].end_idx == plan[i+1].start_idx`, `plan[-1].end_idx == len(sizes)`), keeping a batch that lands exactly on either limit and returning `[]` for no sizes; `class BatchPayloadTooLargeError(ValueError)` with `__init__(self, *, num_requests: int, size_bytes: int, limit_bytes: int) -> None` storing those three as attributes; and `class SingleRequestTooLargeError(BatchPayloadTooLargeError)` with `__init__(self, *, row_idx: int, size_bytes: int, limit_bytes: int) -> None`, storing `row_idx` and `num_requests == 1`, raised when one request's own size exceeds `max_bytes_per_batch` (instead of today's `batch_size = 0` hang). On `BaseBatchRequestProcessor` (`request_processor/batch/base_batch_request_processor.py`) add a `batch_limits` property built from `self.max_requests_per_batch` / `self.max_bytes_per_batch`, `def measure_request_payload(self, generic_request: GenericRequest) -> int` returning `payload_size_bytes(self.create_api_specific_request_batch(generic_request))` — the provider payload that is actually submitted, not the generic request written to `requests_*.jsonl` — and `def plan_request_batches(self, dataset: "Dataset") -> list[PlannedBatch]` which builds each row through `PromptFormatter.create_generic_request(row, idx, generation_params_per_row)` with `generation_params_per_row = "generation_params" in dataset.column_names`, measures each row exactly once in index order, and returns `plan_batches(sizes, self.batch_limits)`; `create_batch_file(self, api_specific_requests: list[dict]) -> bytes` keeps its signature (return annotation corrected from `str`) and raises `BatchPayloadTooLargeError` where it raises `ValueError` today, so a planned batch's `num_bytes` equals `len(create_batch_file(...))` for that batch. In `base_request_processor.py`, delete the nested `_get_optimal_batch_size` (lines 263‑278) and the `while True` loop (lines 282‑295), drive the `"auto"` branch of `create_request_files(dataset: Optional["Dataset"]) -> list[str]` (unchanged signature) off `self.plan_request_batches(dataset)`, write each planned batch through the existing `acreate_request_file(...)` as `requests_{p.index}.jsonl` with `metadata_{p.index}.json`, and return `[os.path.join(self.working_dir, f"requests_{p.index}.jsonl") for p in plan]` — one path per planned batch, in `index` order (a 0-row dataset therefore returns `[]`). The explicit-integer `batch_size` branch (lines 297‑311) keeps its current behaviour exactly: `ceil(len(dataset) / batch_size)` fixed-width files filtered by `incomplete_files`, no byte-based resplit, no planner call. `max_requests_per_batch` / `max_bytes_per_batch`, `acreate_request_file` (metadata body `{"num_jobs": n}`) and `run_in_event_loop` are reused as-is. Tests build processors via `__new__` with `config`, `prompt_formatter`, `working_dir`, `_cost_processor` assigned by hand and patch the two limit properties with `unittest.mock.PropertyMock`; no network, no clients, no sleeps.

## Every remark, in the order a reader would meet them

| date | where | who | says | carries |
|---|---|---|---|---|
| — | *unplaced* | dario | settled then: the span goes in metadata_{i}.json right next to num_jobs, so each file carries its own start_idx, end_idx and num_bytes. no separate plan file. | *herring* |
| — | *unplaced* | dario | i think the sweep is the first statement in the auto branch - glob the stale requests_*.jsonl and metadata_*.json, remove them, then plan_request_batches runs on a clean diretcory | *herring* |
| — | *unplaced* | emil | so to restate the order: in create_request_files we clear the old requests_*/metadata_* on entry, then call plan_request_batches. nothing stale is ever in the dir while we plan. | *herring* |
| 2025-01-27 | #code-review | konrad | look, from my review pass the auto batches carry {num_jobs, start_idx, end_idx, num_bytes} in each metadata_{i}.json, so the plan lives in the per-batch metadata, not a separate file | *herring* |
| 2025-03-14 | #code-review | emil | @Gideon on that request processing cleanup - the dataset=None leg never writes a request file at all, so there's nothing there to tidy, i'd leave that one alone | `scope` |
| 2025-03-19 | #pipeline *(new)* | nils | ran the auto path over an empty input this morning and plan_fingerprint still handed me back a plan_id, same one i get hashing an empty string in a repl. | `rule` |
| 2025-03-20 | #code-review *(new)* | gideon | so the limits block in the doc came out with three keys once max_batches_per_plan landed, and my snapshot only had the two byte/request ones pinned, so it's red. | `rule`, `failure_behavior` |
| 2025-03-20 | #pipeline *(new)* | nils | let me think - i sent 600 tiny rows plus one 5MB row and got the fragmentation error back. i wanted SingleRequestTooLargeError with row_idx 600 named there. | `failure_behavior` |
| 2025-03-20 | #code-review *(new)* | konrad | look, careful with an explicit batch_size - we lean on incomplete_files to skip finished work, and pulling request files out from under that restarts runs people already half paid for | `scope` |
| 2025-03-21 | #code-review | konrad | Anyway while house rules are going on record - batch_plan.json should be written with indent 2 and a newline on the end, our review diffs are unreadble when it comes out on one line. | `rule`, `observability` |
| 2025-03-21 | thread:<178778732260.3143269.10750283081321891939@world.local> | dario | i hit this myself actually — cleared the working dir by hand between two auto runs and lost responses_0.jsonl, so we paid for those completions a second time. | `exclusions_or_crossover`, `observability` |
| 2025-03-24 | #pipeline *(new)* | nils | let me think - our metadata_{i}.json reader asserts the body is num_jobs and nothing else, it bails on anything extra. so please keep span keys out of those. | `exclusions_or_crossover` |
| 2025-03-24 | #pipeline *(new)* | nils | let me think - the .arrow shards under there are the cached dataset, drop those and we rebuild the whole thing before anything gets submitted. | `exclusions_or_crossover` |
| 2025-03-26 | #pipeline | gideon | honestly though I hit a similar one, reran auto with a tighter byte cap and the downstream glob still picked up requests_4.jsonl and requests_5.jsonl from yesterdays six batch run | `rule` |
| 2025-03-26 | #pipeline *(new)* | nils | metadata_3.json from the previous split is still sitting in there reporting its old num_jobs, so anything reading counts back gets a plan that no longer exists. | `rule` |
| 2025-04-03 | #pipeline | dario | a run died partway through writing requests_*.jsonl and nothing on disk said what it had been aiming for. batch_plan.json wants to land before the first requests file, metadata too. | `scope` |
| 2025-04-08 | #pipeline *(new)* | dario | so plan_fingerprint hashes just the batches joined, 0-2:307;2-4:307 - spans and bytes, not index or num_requests. utf-8 encode, sha256, keep the front of the hexdigest. | `rule`, `observability` |
| 2025-04-08 | #engineering *(new)* | nikolai | the sha256 hexdigest is 64 chars and the full thing just wraps the log line - twelve off the front is plenty for eyballing two runs against each other | `observability` |
| 2025-04-08 | #pipeline *(new)* | konrad | right, I renamed the column in my run notes to plan_id then, I had it down as plan_hash. it's whatever plan_fingerprint hands back - twelve hex chars, f4b1ea1573c0. | `rule` |
| 2025-04-08 | #pipeline *(new)* | dermot | when the planner refuses a row i want to fix that one row and rerun against the same directory, not rebuild everything that was already sitting there | `failure_behavior` |
| 2025-04-09 | #pipeline *(new)* | dermot | the num_bytes sitting next to those counts should just be what create_batch_file handed back, summed. i checked it against du on the dir and they don't agree. | `rule` |
| 2025-04-09 | #pipeline | gideon | so basically batch submission blew up with SingleRequestTooLargeError(row_idx=1, size_bytes=748, limit_bytes=400), then I went to diff against the previous batch_plan.json and there was nothing left to diff | `failure_behavior`, `observability` |
| 2025-04-10 | #pipeline *(new)* | konrad | Auto sizing with a tigth byte cap gave me 31k request files in one dir. If we refuse that, err.limit on its own is useless — I need the count it wanted. | `failure_behavior`, `observability` |
| 2025-04-10 | #engineering *(new)* | konrad | look, batch_objects.jsonl is how we recover the submitted batch ids, if a rerun removes it we cant poll the batches we already sent. | `exclusions_or_crossover` |
| 2025-04-15 | #code-review *(new)* | konrad | Look, if I pass batch_size=2, or no dataset at all, then I picked the split myself. No batch_plan.json should be turing up in my working dir for those. | `scope` |
| 2025-04-22 | #pipeline *(new)* | emil | honestly the empty plan case looks fine to me as is - zero batches join to nothing and plan_fingerprint([]) still handed back e3b0c44298fc, no need to special-case it | `observability` |
| 2025-04-22 | #pipeline *(new)* | dario | honestly writing requests_0 through requests_2 over the top isn't enough when the run before left six of them, the leftovers have to come off disk first | `rule` |
| 2025-04-23 | #pipeline | gideon | ya same thing on my side - auto run gave me 9 request files and nothing says which rows landed in requests_3.jsonl, had to reopen all of them to find one promt | `rule` |
| 2025-04-23 | #pipeline *(new)* | dermot | for the wiki page: planner file holds PLAN_FILE_NAME and PLAN_FORMAT_VERSION beside the two dataclasses, version is 1 and only moves when the key set does. | `rule` |
| 2025-04-23 | #pipeline *(new)* | emil | honestly, went to put the fragmentation count in our alert line and there's no num_batches on the error anywhere, just the ceiling - had to re-derive it from len(plan). | `failure_behavior` |
| 2025-04-24 | #pipeline *(new)* | gideon | the auto path on an empty dataset left me a bare dir. I'd still want batch_plan.json — num_batches 0, num_bytes 0, batches [], plan_id filled in like any other run. | `scope`, `observability` |
| 2025-04-24 | #code-review | dario | same family of thing — my except for payload-too-large caught BatchPlanTooFragmentedError this morning. my outer except ValueError should have been the one to get it, those aren't the same failure. | `failure_behavior` |
| 2025-05-06 | #code-review *(new)* | dermot | yeah, keeping the cleanup inside the auto sizing branch rather than hoisting it up into create_request_files. the fixed-width branch has its own resume contract, it shouldnt inherit ours | `scope` |
| 2025-05-13 | #pipeline *(new)* | dermot | yeah - plan_id is a digest of the canonical batch lines and nothing else. zero lines join to an empty string and that string goes into sha256 like any other. | `scope` |
| 2025-05-14 | #code-review *(new)* | emil | review nit on the plan_document — i'd put plan_format_version first and the id right after it, i want to know whether i can parse the rest before i read it. | `rule` |
| 2025-06-11 | #pipeline *(new)* | nikolai | the oversized row aborted the run and i came back to an empty working dir nothign new written and the files that were fine gone with it | `failure_behavior` |
| 2025-06-17 | #pipeline *(new)* | nikolai | for the run dashbaord i read num_batches and num_requests straight after the limits block rather than walking the per batch rows so keep those rows in as well | `rule`, `observability` |
| 2025-06-19 | #pipeline *(new)* | nikolai | i'd say whatever we take out gets named off what that run writes itself, emptying the folder is a differnt operation and not the one we want | `exclusions_or_crossover` |
| 2025-06-24 | #pipeline *(new)* | nikolai | i'd say the cap goes on the limits dataclass as max_batches_per_plan default 512, checked once the plan is finished, and a plan landing on exactly 512 is still fine. | `failure_behavior`, `rule` |

## g1.r1

**The hidden requirement:**

- **rule** — The planner module also records the plan it produced. `batch_payload_planner` exports `PLAN_FILE_NAME = "batch_plan.json"`, `PLAN_FORMAT_VERSION = 1`, `def plan_fingerprint(plan: Sequence[PlannedBatch]) -> str` and `def plan_document(plan: Sequence[PlannedBatch], limits: BatchLimits) -> dict`. `plan_fingerprint` builds the canonical string `";".join(f"{p.start_idx}-{p.end_idx}:{p.num_bytes}" for p in plan)` — spans and batch sizes only, not `index` or `num_requests` — encodes it UTF-8 and returns the FIRST 12 CHARACTERS of its `hashlib.sha256` hexdigest (an empty plan fingerprints the empty string). `plan_document` returns exactly these keys in this order: `plan_format_version` (`1`), `plan_id` (`plan_fingerprint(plan)`), `limits` (`dataclasses.asdict(limits)`), `num_batches` (`len(plan)`), `num_requests` (sum of `p.num_requests`), `num_bytes` (sum of `p.num_bytes`, the batch files' sizes summed, not any on-disk size), `batches` (`[dataclasses.asdict(p) for p in plan]`, five keys each in field order). `BatchLimits` carries a third field `max_batches_per_plan: int = _MAX_BATCHES_PER_PLAN` with the module constant `_MAX_BATCHES_PER_PLAN = 512`, so `limits` serialises with three keys while `BaseBatchRequestProcessor.batch_limits` still constructs `BatchLimits` from the two provider limits only. In the `"auto"` branch of `create_request_files`, once `plan_request_batches` has returned, `json.dumps(plan_document(plan, self.batch_limits), indent=2) + "\n"` is written to `os.path.join(self.working_dir, PLAN_FILE_NAME)`.
- **scope** — The sidecar is written in the `"auto"` branch only, before any request file or metadata file is written, and it is written for a 0-batch plan too (empty dataset → a `batch_plan.json` with `num_batches: 0`, `num_requests: 0`, `num_bytes: 0`, `batches: []` and `plan_id` of the empty canonical string). The explicit-integer `batch_size` branch and the `dataset is None` path never write it: with `batch_size=2` on a 3-row dataset, `"batch_plan.json" not in os.listdir(working_dir)`.
- **exclusions_or_crossover** — `metadata_{i}.json` is untouched by this: its body stays exactly `{"num_jobs": n}` with no `start_idx`/`end_idx`/`num_bytes` keys added. The sidecar is the single place the plan shape is recorded, because `_verify_existing_request_files` cannot describe an `"auto"` run.
- **failure_behavior** — After `plan_batches` has built the whole plan and before it returns, `len(plan) > limits.max_batches_per_plan` raises `BatchPlanTooFragmentedError(num_batches=<the full count the plan would have needed>, limit=<the limit>)`, exported from the same module, storing both as attributes; it subclasses `ValueError` but is NOT a `BatchPayloadTooLargeError`. `plan_batches([10]*512, BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=1000))` returns 512 batches (the boundary is admissible); `[10]*513` raises with `err.num_batches == 513`, `err.limit == 512`; an explicit `BatchLimits(1, 1000, max_batches_per_plan=2)` on `[10]*3` raises with `err.num_batches == 3`, `err.limit == 2`. The per-row oversize scan runs first, so `plan_batches([10]*600 + [5000], BatchLimits(1, 1000))` raises `SingleRequestTooLargeError` with `err.row_idx == 600`, not `BatchPlanTooFragmentedError`.
- **observability** — Exact strings and one exact document. `plan_fingerprint([]) == "e3b0c44298fc"`; `plan_fingerprint(plan_batches([10]*7, BatchLimits(1000, 32))) == "ad0828fea95e"`; `plan_fingerprint([PlannedBatch(0,0,2,2,307), PlannedBatch(1,2,4,2,307), PlannedBatch(2,4,5,1,153)]) == "f4b1ea1573c0"`; the 11-batch plan of an 11-row dataset with `max_requests_per_batch` patched to `1` fingerprints `"c53f6fb95c13"`. After the 5-row OpenAI run with limits patched to `3`/`400`, `json.load(open(f"{working_dir}/batch_plan.json"))` equals exactly `{"plan_format_version": 1, "plan_id": "f4b1ea1573c0", "limits": {"max_requests_per_batch": 3, "max_bytes_per_batch": 400, "max_batches_per_plan": 512}, "num_batches": 3, "num_requests": 5, "num_bytes": 767, "batches": [{"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307}, {"index": 1, "start_idx": 2, "end_idx": 4, "num_requests": 2, "num_bytes": 307}, {"index": 2, "start_idx": 4, "end_idx": 5, "num_requests": 1, "num_bytes": 153}]}`, with `list(doc) == ["plan_format_version", "plan_id", "limits", "num_batches", "num_requests", "num_bytes", "batches"]` and the raw file text ending in `"]\n}\n"`; and `BatchLimits(1000, 32).max_batches_per_plan == 512`.

**Reversed earlier:** The plan was first folded into the existing per-batch metadata — `metadata_{i}.json` became `{"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}` — and that was reverted a week later because readers of metadata_{i}.json assumed the `{"num_jobs": n}` shape; the plan moved out into one versioned sidecar instead.

**What a reader has to infer along the way:**

- *The automatically-sized path leaves behind one versioned JSON file, named by a constant the planner module exports, as the only on-disk record of how rows were split; the per-batch metadata files keep the body they have today.*
  - nobody says: If the only artefacts of an auto run are the request files and a metadata body nobody may extend, the split has to be described somewhere new, and there is exactly one such place.
- *That file's body is a document built by one planner helper, with a fixed key order running format version, id, the limits block, then the whole-run totals, then a row per batch; the byte total is the batch files' sizes summed.*
  - nobody says: Everyone reading the file reads it positionally and expects the same keys, so the document is generated once, in a settled order, from the plan objects themselves.
- *The document's id is a short hash of the plan's spans and byte sizes only, produced by the planner's fingerprint helper, so an empty plan hashes the empty string.*
  - nobody says: If two runs are compared by a single short token, the token has to be derived from exactly the fields that define the split and nothing that renumbering could change.
- *The record is written only on the auto path, before any request or metadata file goes out, and it is written even when the plan came out with no batches; the explicit-size and no-dataset paths leave the working directory exactly as it is today.*
  - nobody says: A record that only appears when the planner had something interesting to say is not a record, and a path where the caller chose the split has nothing for the planner to describe.
- *A plan that comes out in too many pieces is refused once it has been built, by its own error type carrying the count it would have needed and the ceiling it broke, with the ceiling itself living on the limits dataclass with a default; a single oversized row is reported as that instead.*
  - nobody says: Refusing early would mean the error cannot name the real count, and two different faults caught by one except clause is how the wrong one gets swallowed.

**Names the tests reach for that the ticket withholds:**

- said: `BatchPlanTooFragmentedError`, `PLAN_FILE_NAME`, `PLAN_FORMAT_VERSION`, `batch_plan.json`, `batches`, `limit`, `max_batches_per_plan`, `num_batches`, `plan_document`, `plan_fingerprint`, `plan_format_version`, `plan_id`

> **Values nobody prints:** `10`, `1000`, `11`, `153`, `32`, `5000`, `513`, `ad0828fea95e`, `c53f6fb95c13`. Fine if the remarks say enough to compute them; check that they do.

> **Spread:** g1.r1.s1: two remarks in #pipeline within 0 days; g1.r1.s3: two remarks in #pipeline within 0 days

### The remarks

#### `g1.r1.l1` — rule

**gideon**, 2025-04-23, #pipeline

> ya same thing on my side - auto run gave me 9 request files and nothing says which rows landed in requests_3.jsonl, had to reopen all of them to find one promt

*Drafted as:* auto run gave me 9 request files and nothing anywhere says which rows landed in requests_3.jsonl. had to reopen all of them to find one prompt.

*Why there:* That room is already on "a run dir doesn't tell you what the run did" — Emil at 15:09 says the persisted job record holds only the id, request file path and timestamp, so he can't tell what a handed-over run went out with, and Dermot at 15:35 generalizes it to "the fingerprint and the job record have the same gap." Gideon piling on with his own instance (auto-split request files, no record of which rows went where) is exactly the kind of second data point he supplies elsewhere in this thread, and it sets up Emil's 17:13 "write it into the pending record" without pre-empting it — Gideon only reports the symptom and the cost, never what should be recorded or where.

*Still leaves open:* what should be written instead, what it is called, or where it goes

> **Problems:** longer than one remark

#### `g1.r1.l2` — rule

**dermot**, 2025-04-23, #pipeline

> for the wiki page: planner file holds PLAN_FILE_NAME and PLAN_FORMAT_VERSION beside the two dataclasses, version is 1 and only moves when the key set does.

*Drafted as:* wiki: planner file also holds PLAN_FILE_NAME and PLAN_FORMAT_VERSION beside the two dataclasses, version is 1 and only moves when the key set does.

*Why there:* All four listed places are release-engineering and incident material: WS-055 is about CI gating, cache fingerprinting and the release job; v0.1.21 is an unfilled changelog stub; the two postmortems are about a behavioral regression in v0.1.23 and a capability-assumption revert in the cookbook examples. None of them is chewing on the planner module's public surface, so a line about what constants sit beside the two dataclasses would change the subject in every one of them and draw no reaction. It also reads as someone dictating a line for a wiki page mid-discussion ("wiki: ..."), which is chat register, not prose that could sit under a heading in dermot's postmortem voice. What should have existed is the thread where the batch-payload planner's module surface got pinned down — someone drafting the design page asks what the planner actually exports, dermot answers with the two dataclasses plus the file-name constant and the format version, and someone else (the sibling remark) covers what lands in that file and at what point in the run it gets written. Same thread would also have covered where the file sits relative to the cache root and whether the version bump is tied to schema changes only.

*Still leaves open:* what the file named by that constant actually contains, and when it gets written

*Must appear literally:* `PLAN_FILE_NAME`, `PLAN_FORMAT_VERSION`

*A new conversation in #pipeline on 2025-04-23:*

```
10:12  gideon: writing up the batch payload planner page and the draft only lists the two dataclasses. what else does the planner module actually export? i dont want the wiki to be half the surface area
10:19  dermot: wiki: planner file also holds PLAN_FILE_NAME and PLAN_FORMAT_VERSION beside the two dataclasses, version is 1 and only moves when the key set does
10:21  gideon: ah ok. so basically the version is not a general "we changed something" marker, its scoped to the keys
10:24  dermot: mhm. renaming a field would count, adding a comment obviously would not. that said i am not entirely sure anyone has had to bump it yet
10:26  gideon: ya nothing in the history that i saw. ill put it in the page as-is and flag the bump rule as a note, tbh the reader will care more about the dataclasses anyway
10:31  gideon: unrelated but is there a plan doc for the reuse thing from monday or is that still just the thread
```

#### `g1.r1.l3` — exclusions_or_crossover

**nils**, 2025-03-24, #pipeline

> let me think - our metadata_{i}.json reader asserts the body is num_jobs and nothing else, it bails on anything extra. so please keep span keys out of those.

*Drafted as:* our metadata_{i}.json reader asserts the body is num_jobs and nothing else, it bails on anything extra. so please keep span keys out of those.

*Why there:* Both #code-review days are release-sequencing and review-assignment threads — which PRs land, who signs off on PR 584, whether WS-047 has a spec. Nobody in either room is discussing batch file formats, span/trace data, or where it should be written; the closest touchpoint is nikolai's PR 583 param to disable the metadata db, which is a different subsystem (code-execution) from the per-batch metadata_{i}.json request files. Dropping a format constraint into either day changes the subject and would draw no reply, and the remark also depends on a live proposal to put span keys somewhere — a proposal that never surfaces in these two threads. It needs the conversation where someone actually suggested stashing span data alongside the batch metadata.

*Still leaves open:* where the span information is supposed to live instead

*A new conversation in #pipeline on 2025-03-24:*

```
11:42  emil: wiring the trace context through submit_batch now and the obvious place to stash the span id is the per-batch metadata file, since it's already written out right next to the request file. so my read is that's an open dict we can just add a key to? not entirely sure though, i don't want to break the resume path
11:49  nils: let me think through that. it is not open, unfortunately - our metadata_{i}.json reader asserts the body is num_jobs and nothing else, it bails on anything extra. so please keep span keys out of those.
11:51  nikolai: yeah i hit that a while back when i was debugging the anthropic resume thing, it just blows up rather than ignoring the extra field
11:54  emil: ok. honestly then the span id probably wants to live wherever we're already tracking the batch job id, not in a file on disk at all
11:56  nikolai: which is the other thing thats unclear right now, whether that id even comes back at submission
```

> **Problems:** longer than one remark

#### `g1.r1.l4` — rule, observability

**konrad**, 2025-03-21, #code-review

> Anyway while house rules are going on record - batch_plan.json should be written with indent 2 and a newline on the end, our review diffs are unreadble when it comes out on one line.

*Drafted as:* Write batch_plan.json with indent 2 and a newline on the end, our review diffs are unreadable when it comes out on one line.

*Why there:* That room is already reviewing batch-mode work (PR 584 Mistral batch, PR 585 retry handling) and Emil has just put a house rule on record from the batch status persistence note ("connect to the metadata db with mode=ro"). Konrad is present, has said he's been sitting on PR 584, and a second convention — how the batch plan file gets serialized — reads as him piggybacking on the house-rules moment rather than changing the subject. It stays a formatting/review-ergonomics point and leaves the file's contents and which runs emit it untouched. The one strain is that batch_plan.json hasn't been named earlier in the thread, but code-review nits routinely name a file cold.

*Still leaves open:* what is inside the file and which runs produce it

*Must appear literally:* `batch_plan.json`

#### `g1.r1.l5` — rule

**emil**, 2025-05-14, #code-review

> review nit on the plan_document — i'd put plan_format_version first and the id right after it, i want to know whether i can parse the rest before i read it.

*Drafted as:* review nit: plan_document should lead with plan_format_version and then the id, i want to know whether i can parse the rest before i read it.

*Why there:* None of the listed rooms has any plan document in play — they are chewing on PR merge state (04-04), hosted vs local viewer (03-27), release scope and stranded reviewers (06-18, 06-03, 05-30), response-path layering on PRs 642/643 (04-16), batch lifecycle test coverage (04-24), and the cancellation race (04-09). plan_document and plan_format_version are never mentioned anywhere in this history, so the nit would be the first appearance of the artifact, would change the subject, and would have nobody above it to be answering. Emil pasting a schema and arguing about its shape is in character (cf. the dataset_not_ready JSON on 05-30), but there is no PR here whose diff contains a plan document to nit about. The sibling remark that supplies the remaining keys and the id derivation implies a PR author walking the team through a proposed layout, which no listed thread is doing.

*Still leaves open:* what the remaining keys are, in what order, and what the id is derived from

*Must appear literally:* `plan_document`, `plan_format_version`

*A new conversation in #code-review on 2025-05-14:*

```
10:12  gideon: opened the PR for the serialized plan doc that batch payload assembly reads, would appreciate eyes before anything downstream starts depending on the key order. so basically the layout right now is: id, created_at, source_dataset, steps[], then the payload hints at the bottom
10:13  gideon: the id is a hash of steps[] + source_dataset currently, tbh i'm not sure that's right, if we ever reorder steps the id changes and honestly i dunno if that's a feature or a bug
10:21  nikolai: why is created_at second thats not something anyone reads programmatically

i'd say put the stuff a parser needs up front and the human metadata after
10:34  emil: review nit along the same lines: plan_document should lead with plan_format_version and then the id. i want to know whether i can parse the rest before i read it. Everything else can come after in whatever order reads nicely
10:39  gideon: hm ok. um does it need a version at all this early though, we are the only consumer right now and honestly i'd rather not carry the field around forever if it never changes
10:44  nikolai: adding it later is the expensive one

whats the hash actually covering btw, steps only or the hints too
```

#### `g1.r1.l6` — rule, observability

**nikolai**, 2025-06-17, #pipeline

> for the run dashbaord i read num_batches and num_requests straight after the limits block rather than walking the per batch rows so keep those rows in as well

*Drafted as:* for the run dashboard i read num_batches and num_requests straight after the limits block instead of walking the per-batch rows, so keep those rows in as well.

*Why there:* Neither mail is chewing on a document schema. The Jun 16 recap is a status mail about PRs 690/691 and the fate of PR 653 — a remark about which keys sit after a "limits block" and whether per-batch rows stay would arrive from nowhere and get no reply there. The Docker image pinning thread is about backend_params and read-only workspaces, a different subject entirely. The remark also presupposes a sibling nearby settling the version/id keys and the third total, i.e. an ongoing back-and-forth over one file's layout, which neither thread is having. What should exist is a short #pipeline thread the day after the batch request creation work lands, where whoever is writing the run plan/summary document proposes dropping the per-batch rows to keep it small, and the people consuming it say what they read out of it.

*Still leaves open:* the version and id keys ahead of the limits block, and what the third total is

*Must appear literally:* `num_batches`

*A new conversation in #pipeline on 2025-06-17:*

```
10:42  dario: wrote up the summary doc alongside the multimodal request creation fix. question though, now that the whole-run totals are sitting in there right after the limits block, do we keep the per batch rows or drop them. honestly they're mostly redundant at that point
10:43  dario: i think it's either both or just the totals, i don't want half of each
10:51  nikolai: for the run dashboard i read num_batches and num_requests straight after the limits block instead of walking the per-batch rows so keep those rows in as well
10:52  nikolai: i mean the rows are the only place you can see a batch come back short so dropping them costs us that
11:04  emil: so you're saying the rows are basically the per batch failure surface and the totals are just the cheap read. that sounds right to me, though i'm not entirely sure what the doc looks like for a run with 400 batches, that's a lot of rows to scroll past
11:09  dario: mhm, that tracks. i'll leave both in for now and we can figure out the 400 batch case when someone actually hits it. best we can do before the fix lands anyway
```

#### `g1.r1.l7` — rule

**dermot**, 2025-04-09, #pipeline

> the num_bytes sitting next to those counts should just be what create_batch_file handed back, summed. i checked it against du on the dir and they don't agree.

*Drafted as:* the num_bytes sitting with those counts should be what create_batch_file handed back, summed. i compared it against du on the dir and they disagree.

*Why there:* Every listed room is chewing on something else: batch-id persistence and where the record file lives (04-03, 03-24), model-vs-resume staleness (03-18, 04-11, 04-16), image/tag pinning (05-07, 04-16), streaming routing and cache (06-26), PR queue and backend_params (04-21). None of them has a document or manifest on the table with per-run counts and a num_bytes field, and none mentions create_batch_file at all — so a remark correcting what that byte total is measuring lands with nothing above it to answer and nothing below it to react. The 04-03 thread is the nearest neighbour (dario closes it asking whether Dermot's ordering has been written down anywhere), but that record is about batch ids surviving the poll window, not about sizing payload files, and dropping a du comparison into it changes the subject. What's missing is the follow-up: someone actually drafts the batch submission manifest that 04-03 asked for, lists the keys and the totals it should carry, and dermot — who's been in the submit path all week — checks the byte figure against the directory and finds it doesn't match.

*Still leaves open:* the other totals, the key order, and which runs produce the file

*A new conversation in #pipeline on 2025-04-09:*

```
10:14  dario: ok so the per-run batch manifest draft, writing it at submit time: run_id, provider, model, then the counts (num_requests, num_batches, num_bytes) and the list of batch ids. emitted by any run that actually submits, so not cache-only resumes. poke holes in it please, i'd rather find out now than after we backfill
10:21  emil: the shape looks broadly right to me. the one thing i'm not entirely sure about is whether the counts are meant to describe what we submitted or what came back, because those diverge the moment anything gets cancelled
10:29  dermot: the num_bytes sitting with those counts should be what create_batch_file handed back, summed. i compared it against du on the dir and they disagree
10:36  dario: mhm that tracks, honestly. i think i'd been writing it as whatever the dir measured because it was easier to reach for at that point in the flow
10:41  dermot: yeah. that said the divergence isn't huge, it's just consistently off in one direction which is what made me look
10:47  emil: let me think through that later today. on the emit condition though, cache-only resumes not writing a manifest means a resumed run has no record at all, which i believe is going to bite someone
```

#### `g1.r1.l8` — rule, failure_behavior

**gideon**, 2025-03-20, #code-review

> so the limits block in the doc came out with three keys once max_batches_per_plan landed, and my snapshot only had the two byte/request ones pinned, so it's red.

*Drafted as:* Heads up, the limits block in the doc came out with three keys once the cap field landed and my snapshot test pinned two.

*Why there:* None of the eight rooms is chewing on document serialisation. 03-18 and the kluster postmortem thread touch the output-token cap only as a release-gate/ownership question — nobody there is looking at a rendered doc, a limits block, or a snapshot test, so a red-test report lands as a subject change with nothing to react to. 04-04 has a card template in it (PR 619), but that room spends the whole day unable to read PR state, and a concrete "my snapshot broke" observation would sit oddly next to people who can't see the repo at all. 05-05 is release/backlog triage, 04-15 and 04-21 are status rooms, 04-07 is the resume cost bug, 03-26 is capability-check fail-open. What should have existed is the code-review thread the day after the cap field merged: gideon rerunning tests, finding the doc's limits block serialising the whole dataclass and therefore gaining a key, with dario or emil confirming the block is the dataclass dumped whole and naming the field and its default.

*Still leaves open:* what the cap field is called, what it defaults to, and where the block sits in the document

*Must appear literally:* `max_batches_per_plan`

*A new conversation in #code-review on 2025-03-20:*

```
10:12  nils: the doc rendering tests are red for me this morning after pulling main, or is that just my checkout being stale
10:19  gideon: nope red here too. so basically the limits block in the doc came out with three keys once the cap field landed and my snapshot test pinned two, so it fails on the diff
10:20  gideon: the output token cap one i mean. tbh i didnt think that woud reach the docs page at all
10:27  emil: yup i saw something similar on the provider page render, though there i believe it was the ordering that shifted and not the key count. not entirely sure they're the same failure
10:41  dario: mhm. in any case if you're already in that file, the fixture under tests/docs has the same shape and it'll probably go next
10:44  nils: i'll hold off on 584 until that settles then, don't want to be chasing a red suite that isn't mine
```

#### `g1.r1.l9` — rule, observability

**dario**, 2025-04-08, #pipeline

> so plan_fingerprint hashes just the batches joined, 0-2:307;2-4:307 - spans and bytes, not index or num_requests. utf-8 encode, sha256, keep the front of the hexdigest.

*Drafted as:* plan_fingerprint should join the batches as 0-2:307;2-4:307, spans and bytes only. index and num_requests must not move it.

*Why there:* Every listed room is chewing on something else, and none of them has a live thread about how a batch plan is fingerprinted. The nearest fits fail on specifics: 03-26 raises the real motivator (Emil ctrl-C'd, reran, and got completions for the old prompts back because nobody compared the on-disk jsonl to the provider job) but then spends the rest of the day on Mistral usage extraction; 04-03 is about *whether* a local batch record gets written at submit time, not what canonical string goes in it. The remark presumes the plan struct's fields are already on the table — it says index and num_requests must not move the value, which only lands if someone has just proposed including them. Dropped into either day it arrives from nowhere, names fields nobody has mentioned, and draws no reply. What should exist is the follow-up those two days point at: dario and emil sitting down over the batch payload plan and deciding what identity means for a plan, with gideon asking the resume-side questions.

*Still leaves open:* what is done to that string and how much of the result is kept

*Must appear literally:* `0-2:307;2-4:307`, `index`, `num_requests`, `plan_fingerprint`, `sha256`

*A new conversation in #pipeline on 2025-04-08:*

```
10:12  emil: starting on the batch record we said has to be written at submit time. the thing I keep circling is what actually identifies the plan, because right now a resume just sees a job id on the provider side and has nothing to compare it against. my guess is it's the spans plus the sizes, but I'm not entirely sure what belongs in the string
10:17  dario: plan_fingerprint should join the batches as 0-2:307;2-4:307, spans and bytes only. index and num_requests must not move it. i think if the index is in there then any reorder rewrites the whole thing for no reason, and the request count is derivable from the span anyway
10:19  gideon: what happens if the prompts change but the bytes come out the same? like same length, different content
10:23  dario: then we miss it, to be honest. spans and sizes is about the best we can do without hashing the payload itself, which i havent really thought thruogh yet
10:28  emil: yup, thats the tradeoff. we need to be intentional here about where the hash gets computed though, on the writer side we're already streaming the jsonl out so it might be close to free
```

#### `g1.r1.l10` — observability

**nikolai**, 2025-04-08, #engineering

> the sha256 hexdigest is 64 chars and the full thing just wraps the log line - twelve off the front is plenty for eyballing two runs against each other

*Drafted as:* twelve hex characters off the front of the sha256 is plenty for comparing two runs by eye, the full digest just wraps the log line.

*Why there:* None of the eight rooms is chewing on run identity or hashing. The closest touch is 2025-04-03, where Emil raises WS-050 and "the job ID has to be persisted before we enter the poll loop" — but that job ID comes back from the provider, it isn't something we derive, so a message about truncating a sha256 hexdigest would arrive from nowhere and get no reply. The rest are review-queue triage (04-14, 06-16), sandbox tag pinning (05-07), the cookbook verifier (06-04), release notes (04-11), README coverage (2026-01-22) and maintenance-mode cadence (06-25) — a hash-length remark changes the subject in all of them. What's missing is the design thread where the batch payload gets a local fingerprint: someone has to say what string is hashed, and nikolai settles the width. That's a distinct conversation, a few days before Emil pulls up WS-050.

*Still leaves open:* what string is being hashed in the first place

*Must appear literally:* `sha256`

*A new conversation in #engineering on 2025-04-08:*

```
14:22  emil: writing up WS-050 and i keep hitting the same gap — a submitted batch needs a local id that survives a resume, otherwise a rerun has no way to match itself back to its request file and just resubmits blind. leaning toward hashing the request file
14:24  konrad: what goes into the hash exactly? the file bytes, or the rows after we parse them
14:26  nikolai: bytes i'd say, parsing gives you room to disagree with yourself later. and twelve hex characters off the front of the sha256 is plenty for comparing two runs by eye the full digest just wraps the log line
14:28  emil: sounds right. Though im not entirely sure the file alone is enough — if someone bumps temperature between runs we'd want a differnt id, and i believe those params are on the request object not in the jsonl
14:30  nikolai: hm. gotta think through that one off the top of my head half of them are already serialized per row
14:31  konrad: maybe. anyway I am on the ws-055 call in a minute, can look after
```

#### `g1.r1.l11` — observability

**emil**, 2025-04-22, #pipeline

> honestly the empty plan case looks fine to me as is - zero batches join to nothing and plan_fingerprint([]) still handed back e3b0c44298fc, no need to special-case it

*Drafted as:* empty plan hashed the empty string and came back e3b0c44298fc, which is fine by me, no special case needed there.

*Why there:* Nothing in the listed rooms is chewing on plan fingerprinting. The nearest neighbours are about cache *keys* (#engineering 2025-04-18: max_tokens not in the key; #random 2025-03-18: model swap silently reusing cached rows) and about cost/resume paths — none of them have anyone serializing a plan or deriving an id from it, so a hash digest would arrive from nowhere and get no reply. The 2026-01-02 and 2025-05-30 code-review days are PR triage, not design. What's missing is the thread where the batch payload plan first gets a stable identity: dermot has been living in the batch submit/cancel path (PR 614) and the 04-18 discussion left "what actually invalidates a run" unsettled, so a follow-up on hashing the plan so resume can tell whether it changed is the conversation this belongs to. Emil, who lost 4000 cached rows to that same ambiguity, is exactly the one to have poked at the degenerate case.

*Still leaves open:* how a non-empty plan is turned into a string, and what the id is called in the file

*Must appear literally:* `e3b0c44298fc`, `plan_fingerprint([])`

*A new conversation in #pipeline on 2025-04-22:*

```
10:38  dermot: picking up from friday, the reason emil ended up nuking the whole cache dir is that nothing in the stored state actually describes the plan we submitted. so i want to give each batch payload plan a deterministic id, hash over the normalized request set plus the generation params, written next to the job id at submit time. then resume compares and can at least tell you it's resuming into a different plan than the one that went out
10:41  dermot: the case i keep going back and forth on is the degenerate one, a plan with zero requests in it. either that's an error at construction time and we never hash it, or it's a normal plan that just happens to be empty. if i had to guess we've got code paths that build an empty plan on a fully-cached rerun
10:52  emil: let me think through that. i sketched the hashing bit locally last night to see what actually falls out — empty plan hashed the empty string and came back e3b0c44298fc, which is fine by me, no special case needed there. a plan id is a fingerprint of what we're about to send, and "nothing" is still a legitimate thing to fingerprint. raising at construction just moves the error somewhere less usefull imo
10:56  dermot: yeah ok, i'll leave it as a plain hash then. that said the normalization is the part that worries me more, ordering especially. two runs that build the same requests in a different order should not produce two ids
11:03  dario: is normalization sorting the requests, or is it hashing them in the order the plan was built? because if it's the latter then anything that touches iteration order upstream silently invalidates every resume, and honestly i don't think we'd notice for a while
11:09  dermot: sorted by request id before hashing was the intent, but i haven't written it yet. i'll put the params half in the same pr so it's all one thing to review
```

#### `g1.r1.l12` — rule

**konrad**, 2025-04-08, #pipeline

> right, I renamed the column in my run notes to plan_id then, I had it down as plan_hash. it's whatever plan_fingerprint hands back - twelve hex chars, f4b1ea1573c0.

*Drafted as:* Renamed the column in my run notes to plan_id to match what the sidecar calls it, I had it down as plan_hash.

*Why there:* Nothing in the listed rooms is chewing on a plan sidecar or its id key. #cookbooks 2025-03-20 does argue about "columns," but those are wiki table columns (name/task/provider/batch/verifier) for the examples index — a plan_id/plan_hash rename would be a topic change nobody could react to. #code-review 2025-04-02 is the nearest neighbour: Emil's complaint that the pending job id gets parked in the run dir keyed off the dataset only, with no backend distinction. But that thread is settling PR 614 vs PR 615 scope, and no one there has mentioned a sidecar, a plan document, or any key named plan_id — the term would arrive from nowhere. The remark needs a room where the sidecar's schema is actually on the table, so someone can also be supplying how the value is computed. That thread is the natural follow-on to the run-dir problem raised on Apr 2: once the id has to be scoped by more than the dataset, the batch payload plan gets written next to the payload with its own id key, and people discover they've been calling it different things in code, notes and the wiki. Konrad is the right person to own the notes-side correction — he keeps run notes and on Apr 2 he was the one pushing to pin down which fix lives where.

*Still leaves open:* how that value is computed and from which fields

*Must appear literally:* `f4b1ea1573c0`, `plan_fingerprint`, `plan_hash`, `plan_id`

*A new conversation in #pipeline on 2025-04-08:*

```
10:12  dermot: one thing from the sidecar work last week, the wiki page still describes the id field the way i wrote it in the first draft, which doesn't match what the writer actually emits
10:14  konrad: Renamed the column in my run notes to plan_id to match what the sidecar calls it, I had it down as plan_hash
10:14  konrad: anyway the notes were only for me so no harm, but if someone else had read them
10:19  emil: so the wiki is the odd one out at this point? i believe dario wrote most of that section before the sidecar existed at all, honestly it may just need a pass
10:23  dermot: mhm. i'll get to it, though not today — pr 619 review is eating the morning
```

#### `g1.r1.l13` — scope

**dario**, 2025-04-03, #pipeline

> a run died partway through writing requests_*.jsonl and nothing on disk said what it had been aiming for. batch_plan.json wants to land before the first requests file, metadata too.

*Drafted as:* a run died partway through writing requests_*.jsonl and i had nothing saying what it had been aiming for. that wants to be on disk before the first file.

*Why there:* The whole day is about how early the run's state hits disk — dermot's "do we write the local batch record at submit time or only once the download completes", dario's polling-window point, and emil at 14:33 confirming nobody's pushing back and the open question is where the write goes. This pushes the boundary one step earlier than submit (before the request files are even written), which is exactly the "ordering" dario asks at 16:18 whether anyone has written down. Dario is already the one supplying first-hand loss anecdotes in this thread, so a second one from him reads as continuous rather than new.

*Still leaves open:* what that record contains, what it is called, and which runs produce it

*Must appear literally:* `batch_plan.json`, `requests_*.jsonl`

> **Problems:** longer than one remark

#### `g1.r1.l14` — scope, observability

**gideon**, 2025-04-24, #pipeline

> the auto path on an empty dataset left me a bare dir. I'd still want batch_plan.json — num_batches 0, num_bytes 0, batches [], plan_id filled in like any other run.

*Drafted as:* Empty dataset on the auto path left me a bare dir. I'd still want a batch_plan.json out of it, num_batches 0, so I can see it ran at all.

*Why there:* No listed room is discussing what the batch planning path writes to disk. #random 4/17 is adjacent (Gideon, empty directories, runs that look like they never happened) but it's specifically about a cache dir created by mkdir -p and 38k re-sent requests — batch_plan.json/num_batches would arrive from nowhere there and #random isn't where an output contract gets agreed. The #pipeline threads in range are all on PR 632, Anthropic tokens, Mistral usage extraction and DeepSeek headers; none touch plan artifacts. The sibling remark (rest of the document, which other paths write it) implies a design thread that doesn't exist yet.

*Still leaves open:* what the rest of the document holds and which other paths write it

*Must appear literally:* `batch_plan.json`, `batches`, `num_batches`, `num_bytes`, `num_requests`, `plan_id`

*A new conversation in #pipeline on 2025-04-24:*

```
11:42  emil: quick one on the batch side, when the auto planner gets a dataset that's under one batch worth of requests, does it still go through the normal write path or does it short circuit somewhere earlier
11:47  gideon: so basically i hit the degenerate version of that yesterday. Empty dataset on the auto path left me a bare dir, nothing in it at all. I'd still want a batch_plan.json out of it, num_batches 0, so i can see it ran at all
honestly though right now there is no way to tell apart "planner ran and there was nothing to do" from "planner never ran"
11:53  dario: mhm, that's the annoying part. is it actually skipping the write, or is it bailing before it even builds the plan object? those are different fixes
11:56  gideon: i dunno, didnt trace it that far tbh. i just noticed the dir was empty and moved on because i was chasing the status thing
12:04  emil: yup. i believe the resume path reads that dir too, so whatever we do there is not purely cosmetic. not entirely sure it cares about an empty plan vs a missing one though
12:09  dario: in any case i'd want to know what resume does with it before we change the write behavior. separately, did the batch status polling end up on the same interval as the pbar update or is that still its own thing
```

> **Problems:** longer than one remark

#### `g1.r1.l15` — scope

**konrad**, 2025-04-15, #code-review

> Look, if I pass batch_size=2, or no dataset at all, then I picked the split myself. No batch_plan.json should be turing up in my working dir for those.

*Drafted as:* If I pass batch_size=2, or no dataset at all, I picked the split myself. Nothing new should be turning up in my working dir for those.

*Why there:* None of the listed rooms is chewing on batch split sizing or on what gets written into the working dir when the caller doesn't pick the split. The closest is #code-review 2025-04-02, but that day's run-dir thread is specifically about the pending job ID being keyed off the dataset with no backend distinction (emil's azure 404 loop) and about PR 614 vs 615 scope — a remark about an explicit-integer batch_size branch and a no-dataset path writing no plan record would change the subject and draw no reply. The other candidates are throttle/estimation (3-19), semaphore + dict validation (3-14), release notes (5-30, 7-10, 12-30), cookbook response objects (5-05) and viewer download plumbing (6-02). What's missing is the review thread on the auto-split PR itself, where dermot explains that the auto path drops a plan record in the working dir and konrad pins down that the two caller-chosen paths write nothing — konrad is exactly the person who does that kind of "what are the branches, plainly" pass on a PR.

*Still leaves open:* what does turn up on the path where the split was not picked by the caller

*Must appear literally:* `batch_plan.json`, `batch_size=2`

*A new conversation in #code-review on 2025-04-15:*

```
10:14  dermot: pr 641 is up, automatic batch split sizing. 614 landing finally unblocked the batch tests so it's reviewable now. short version, if you leave batch_size unset it derives the split from the dataset size
10:21  konrad: going through the branches. which ones actually touch disk? that is the part i want to be sure abuot
10:26  dermot: only the derived path as far as i can tell. it writes the computed plan out alongside the request files so a resume can pick the same split back up
10:29  konrad: right. If I pass batch_size=2, or no dataset at all, I picked the split myself. Nothing new should be turning up in my working dir for those.
10:34  dermot: mhm, that's the intent. that said the guard sits inside the sizing helper right now, not at the call site
10:41  emil: honestly i'd put it at the call site. the helper is going to get called from the resume path too eventually and then you're relying on it staying honest in two places
```

#### `g1.r1.l16` — failure_behavior, observability

**konrad**, 2025-04-10, #pipeline

> Auto sizing with a tigth byte cap gave me 31k request files in one dir. If we refuse that, err.limit on its own is useless — I need the count it wanted.

*Drafted as:* Auto sizing with a tight byte cap gave me 31k request files in one dir. If we start refusing that, tell me how many it needed, not just the ceiling.

*Why there:* None of these rooms is chewing on batch payload planning. The two batch-adjacent days are about something else entirely: 2025-03-31 #engineering is Mistral batch auth, examples currency and a preflight-credentials tangent, and 2025-03-19 is the throttle/estimation path and the api_key decision — a complaint about auto sizing sharding a plan into 31k files, plus a request about what a refusal should report, would change the subject in either and land with no reply. The other five rooms (release notes, viewer null cost, PR triage, importorskip) have no surface for it at all. What's missing is the conversation where the planner's file-count behavior is actually being decided — konrad reporting the fragmentation he hit, someone else naming the ceiling and the failure — and that day doesn't exist yet in this history.

*Still leaves open:* what the ceiling is, what it is called, and what the failure is named

*Must appear literally:* `err.limit`

*A new conversation in #pipeline on 2025-04-10:*

```
10:12  nils: while we're on batch-mode, is the request file layout something we decided or something that just happened? one directory per plan, flat, no sharding as far as i can tell
10:19  konrad: look, i hit this yesterday shaking out batch-mode after WS-050. Auto sizing with a tight byte cap gave me 31k request files in one dir. If we start refusing that, tell me how many it needed, not just the ceiling
10:20  konrad: submit never even started. planner just sat there writing
10:31  emil: so the read is that the ceiling on its own doesn't tell you anything actionable, you'd still be guessing at what cap to set. yup, that tracks. honestly the number it wanted is the only part that helps you
10:44  nils: i think the awkward part is deciding whether that's a hard refusal or just a loud warning. let me think about where the check would even live, it's presumably before any files touch disk or it's pointless
```

#### `g1.r1.l17` — failure_behavior, rule

**nikolai**, 2025-06-24, #pipeline

> i'd say the cap goes on the limits dataclass as max_batches_per_plan default 512, checked once the plan is finished, and a plan landing on exactly 512 is still fine.

*Drafted as:* the cap lives on the limits dataclass as max_batches_per_plan, default 512, and a plan landing on exactly 512 is still admissible.

*Why there:* None of the three rooms is chewing on batch planning limits. The image-pinning design doc is about a pinned tag and the `backend_params` override path, and a batch cap under any of its headings would change the subject. The structured-output incident page is a post-mortem about `supports_structured_output()` being the gate — an unrelated ceiling has nowhere to sit. The Jun 16 sync notes come closest, since PR 691 (auto batch mode) is open there, but that page is a status list: PRs, release state, carried-over issues. It records that the auto batch mode question is unresolved; it does not settle field names or defaults, and a dataclass field with a default and a boundary rule would be the only decided design detail on the page. The remark also needs a sibling nearby saying what happens past the cap and what that failure is called, which implies a back-and-forth, not a bullet in nikolai's own notes. What should have existed: a #pipeline thread the week after the sync, once auto batch mode forced someone to bound how much a single plan can expand to — nikolai and Emil, working out where the ceiling lives (limits dataclass vs. plan builder), what the default is, whether the boundary is inclusive, and what the overflow error is named.

*Still leaves open:* what happens when the plan goes past it, and what that failure is called

*Must appear literally:* `max_batches_per_plan`

*A new conversation in #pipeline on 2025-06-24:*

```
10:12  emil: was poking at auto batch mode ahead of 0.1.26 and i fed it a request set that i thought was mid sized, ended up planning something like 4100 batches before i killed it. honestly not entirely sure the planner has any notion of when to stop
10:13  emil: so the guess is theres supposed to be a ceiling somewhere and it just isnt wired into the auto path? or was there never one
10:29  nikolai: there is one the cap lives on the limits dataclass as max_batches_per_plan default 512 and a plan landing on exactly 512 is still admissible so its not a strict less than
10:34  emil: ok that tracks, i believe the auto path builds its own limits object instead of taking the one thats already threaded through, which would explain why mine sailed past it. let me think through that one
10:41  nikolai: yep thats plausible i havent read that constructor closely gotta think through that one
10:47  emil: ill pull the repro into a test either way, we need to be intentional here about which layer owns the check
```

#### `g1.r1.l18` — failure_behavior

**dario**, 2025-04-24, #code-review

> same family of thing — my except for payload-too-large caught BatchPlanTooFragmentedError this morning. my outer except ValueError should have been the one to get it, those aren't the same failure.

*Drafted as:* my except for payload-too-large swallowed BatchPlanTooFragmentedError this morning. those are not the same failure and i want to catch them apart.

*Why there:* That thread is already a chain of gripes about over-broad/silent excepts — dermot tidying "the last few error paths", dermot finding a cache-write failure swallowed invisibly, emil's "adjacent gripe" about the bare `pass`. Dario is present and his 18:26 "+1" is a natural place to hang his own instance: an except clause catching a different failure than the one it was written for. It contributes a second concrete case to a live complaint rather than opening a new topic, and it deliberately stops at the observation — it says the two failures are distinct without saying when BatchPlanTooFragmentedError is raised or what it carries.

*Still leaves open:* when that error is raised and what it carries

*Must appear literally:* `BatchPlanTooFragmentedError`, `ValueError`

#### `g1.r1.l19` — failure_behavior

**nils**, 2025-03-20, #pipeline

> let me think - i sent 600 tiny rows plus one 5MB row and got the fragmentation error back. i wanted SingleRequestTooLargeError with row_idx 600 named there.

*Drafted as:* 600 tiny rows plus one 5MB row and it came back fragmented. the row index is the thing i actually needed named there.

*Why there:* Neither listed room is chewing on batch payload validation. 03-17 is entirely about the token-usage shape that cost accounting expects and the missing wiki pages; 03-25 is about provider test coverage and who reviews PR 584 before merge. A report of a submission coming back "fragmented" because of one oversized row would change the subject in both, and nobody there would pick it up — worse, the sibling remark that explains the fragmentation limit and what its count means has nowhere to land on either day. What's missing is the day nils actually exercised the Mistral batch submit path with a real file and hit the error, between the 03-17 refactor and the 03-25 review push: him pasting the case that produced it, emil or dario reading the limit off the validator, and the two of them working out that the single-row size failure never gets named because the fragmentation check reports first.

*Still leaves open:* what the fragmentation limit is and what the count on that error means

*Must appear literally:* `600`, `SingleRequestTooLargeError`, `row_idx`

*A new conversation in #pipeline on 2025-03-20:*

```
10:42  emil: has anyone pointed 584 at an actual payload file yet or has it all been the fixtures? i believe the fixtures are all more or less uniform row sizes, which doesn't excercise much of the validation path
10:51  nils: i ran it against one of the production dumps this morning. 600 tiny rows plus one 5MB row and it came back fragmented. the row index is the thing i actually needed named there — PR 584 tells me the file is fragmented and stops, so i ended up bisecting the file by hand to find the row that was actually the problem
10:55  dario: right, a single oversized row shoud come back as the per-row failure, before anything gets as far as the fragmentation check. thats the ordering that pass exists for. honestly i'd have expected 584 to name the row and never mention fragmentation at all there
10:58  nils: makes sense. that's worth documenting somewhere, the ordering isn't obvious reading the validator top to bottom
11:04  emil: seperate thing but is a 5MB row even legal on their side? i thought mistral's per-request cap sat lower than that
```

#### `g1.r1.h1` — herring

**dario**, unplaced, —

> settled then: the span goes in metadata_{i}.json right next to num_jobs, so each file carries its own start_idx, end_idx and num_bytes. no separate plan file.

*Drafted as:* settled: the span lands in metadata_{i}.json alongside num_jobs, so each file carries start_idx, end_idx and num_bytes. no separate plan file.

#### `g1.r1.h2` — herring

**konrad**, 2025-01-27, #code-review

> look, from my review pass the auto batches carry {num_jobs, start_idx, end_idx, num_bytes} in each metadata_{i}.json, so the plan lives in the per-batch metadata, not a separate file

*Drafted as:* Reminder from review: metadata for auto batches is {"num_jobs", "start_idx", "end_idx", "num_bytes"}. The per-batch metadata is where the plan lives.

*Why there:* Konrad has just split hairs at 11:15–11:16 over whether issue 42 is generation params or batch config like batch_size — this is him continuing the burst with what he saw on the review side, showing where auto-batch planning is actually recorded, which keeps the batch-config category distinct from the param-passing that's blocking PR 403.

#### `g1.r1.fix21` — failure_behavior

**emil**, 2025-04-23, #pipeline

> honestly, went to put the fragmentation count in our alert line and there's no num_batches on the error anywhere, just the ceiling - had to re-derive it from len(plan).

*Drafted as:* Went to put the fragmentation count in our alert line and there's no num_batches anywhere on the error, just the ceiling. had to re-derive it from len(plan).

*Why there:* None of the eight rooms is anywhere near this. The two #pipeline days are about job-reuse mismatch keys (04-21) and retry classification / sweep order (04-01); the three #releases days are notes-and-tag logistics; #engineering 04-10 is PR 614/624 review traffic; #general 06-02 is dormancy; #code-review 2026-01-02 is PR triage. Nobody in any of them has mentioned plan_batches, a fragmentation ceiling, or what the error carries, so a remark about alerting off the error's fields has no thread to attach to and no one to answer it. What's missing is the thread where that ceiling check gets added and someone asks what the raised error should hold — emil would be the one who hit it first from the alerting side, with dario (who owns the batch submit/reattach path) and dermot (who set the "eat the cost, don't blend configs" policy) on the other end.

*Still leaves open:* what the ceiling attribute is called, what value it holds, and when in plan_batches the check runs

*Must appear literally:* `num_batches`, `len(plan)`

*A new conversation in #pipeline on 2025-04-23:*

```
14:12  dario: put the ceiling check into plan_batches, it raises before we submit anything now. still deciding what the error should carry though — either just the limit we blew past, or the limit plus what the submission actually wanted
14:19  emil: Went to put the fragmentation count in our alert line and there's no num_batches anywhere on the error, just the ceiling. had to re-derive it from len(plan).
14:24  dario: mhm, that tracks. i think i wrote it assuming the caller already had the plan in hand, which, to be honest, is only true inside plan_batches itself
14:31  dermot: the alerting path doesn't have the plan though, it's reading off the exception in the retry wrapper. so if i had to guess emil is not the only one who'll hit that
14:38  gideon: ya and the number is the whole point of the alert honestly, "you exceeded the ceiling" tells you nothing about by how much. like was it 1200 or was it 40000
14:45  dario: yeah. in any case that's a separate change from the check itself, i don't want to hold 640 on it
```

#### `g1.r1.fix22` — rule

**nils**, 2025-03-19, #pipeline

> ran the auto path over an empty input this morning and plan_fingerprint still handed me back a plan_id, same one i get hashing an empty string in a repl.

*Drafted as:* ran the auto path over an empty input this morning and plan_fingerprint still handed me a plan_id back, same one i get hashing an empty string in a repl.

*Why there:* Neither room is anywhere near this. #code-review 2025-03-25 is pure release triage — which of 584/585/579/468/565 lands or gets deferred, plus the missing WS-047 writeup; nobody there mentions plans, hashing, or determinism, and a fingerprint edge case dropped into that queue would change the subject and get no reply. #pipeline 2025-03-17 is the Mistral batch client and whether token usage lands in the shape cost accounting expects; it's the closer channel, but the day's live question is the usage dict, not plan identity, and nils spends it walking back "nearly ready" rather than reporting edge-case runs. The remark also needs a sibling nearby to supply the digest, the width, and the canonical string for a non-empty plan — neither transcript has anyone who would answer that. What should have existed: a #pipeline thread a couple of days after the 03-17 refactor, once nils is exercising the auto path end to end, where he reports the empty-input result and emil (or dario) answers with what plan_fingerprint actually digests and how the canonical string is built for a real plan. Same cast, same channel, and it gives the "empty plan fingerprints the empty string" agreement somewhere to land.

*Still leaves open:* what the digest actually is, how wide the value is, and what the canonical string looks like for a non-empty plan

*Must appear literally:* `plan_fingerprint`, `plan_id`

*A new conversation in #pipeline on 2025-03-19:*

```
10:42  emil: so you're saying the auto path is fully exercised end to end now after the refactor, or is there still a manual step in there somewhere? i want to know before i point the gemini side at it
10:49  nils: mostly end to end, i've been walking it through. one thing though — ran the auto path over an empty input this morning and plan_fingerprint still handed me a plan_id back, same one i get hashing an empty string in a repl. is that intended, or should fingerprinting refuse an empty plan
10:53  dario: i think that's just what it does, it hashes whatever it gets handed and an empty thing is still a thing to hash. to be honest i don't know that anyone decided it, it just
10:58  emil: yup, i believe it's fallen out of the implementation rather than been chosen. not entirely sure it matters downstream though, the submission would fail on its own further along
11:04  nils: fair enough. that's worth documenting somewhere at least, even if we leave the behaviour. anyway the rest of the path looked clean, gemini side should be safe to point at it
```

#### `g1.r1.fix23` — scope

**dermot**, 2025-05-13, #pipeline

> yeah - plan_id is a digest of the canonical batch lines and nothing else. zero lines join to an empty string and that string goes into sha256 like any other.

*Drafted as:* plan_id is a digest of the canonical batch lines and nothing else. we only reach for the hash when there's a line to feed it.

*Why there:* No listed room is chewing on how plan_id is derived. #pipeline 2025-03-24 and #code-review 2025-04-02 are about the provider-issued batch job id — where to persist it and how it's keyed — which is an id received, not a digest computed from batch lines; dermot explaining digest derivation there answers a question nobody asked and gets no reaction. #random 2025-04-17 shares the "empty thing looks normal" flavour but is a billing war-stories thread about mkdir -p. #engineering 2025-04-21 touches empty-dict-vs-None but on backend_params validation, a different object. Also, gideon needs to be somewhere he'd plausibly be reporting a field value off a real zero-line run, and neither room he appears in (PR 614 review status, the mkdir -p postmortem) is that.

*Still leaves open:* what actually ends up in the field on a run with no batch lines at all — gideon's is the one that saw that.

*Must appear literally:* `plan_id`, `sha256`

*A new conversation in #pipeline on 2025-05-13:*

```
10:42  gideon: ok so basically i reran the cookbook notebook this morning and every single request came back from cache, nothing got submitted at all. but the run metadata still has an id written against it and honestly it looks wrong to me? like it doesnt match anything
10:43  gideon: what is that field even supposed to come from tbh. i dunno if im reading it wrong
10:51  dermot: plan_id is a digest of the canonical batch lines and nothing else. we only reach for the hash when there's a line to feed it
10:52  gideon: ya ok so with a full cache hit theres nothing to digest at all, that tracks. so where is the value in my metadata comign from then
10:58  emil: let me think through that — i believe the metadata writer runs regardless of whether anything was submitted, so it may just be carrying whatever the previous run left in the resume file. not entirely sure though, i havent looked at that path since the cache rework
11:04  dermot: that said, the cookbooks were touched last week too. worth checking whether you're on the updated one before we chase the writer
```


## g1.r2

**The hidden requirement:**

- **rule** — In the `"auto"` branch of `create_request_files`, after `plan_request_batches(dataset)` has returned and before anything new is written, every existing `requests_*.jsonl` and every existing `metadata_*.json` in `self.working_dir` is removed (`glob.glob` + `os.remove`). A previous `"auto"` run under different limits leaves a longer numbering behind (e.g. `requests_0..5.jsonl` for a new plan of 3), and those stale files are what a later glob-based read would pick up, so the branch clears them rather than overwriting only the prefix.
- **scope** — Sweeping belongs to the `"auto"` branch alone. The explicit-integer `batch_size` branch does not sweep — it still relies on `incomplete_files` and may legitimately leave earlier request files in place — and the `dataset is None` path does not sweep either.
- **exclusions_or_crossover** — Only those two glob patterns are removed. `responses_*.jsonl`, `*.arrow`, `batch_objects.jsonl` and every other file in the working directory survive byte-for-byte; the sweep is not a directory wipe.
- **failure_behavior** — The sweep sits behind a plan that returned. If planning raises — `SingleRequestTooLargeError` or `BatchPlanTooFragmentedError` — nothing is removed and nothing is written, so the working directory is byte-for-byte what it was, stale files and all.
- **observability** — `working_dir` pre-populated with `requests_0.jsonl … requests_5.jsonl` (each `"stale\n"`), `metadata_0.json … metadata_5.json` (each `"{}\n"`) and `responses_0.jsonl` (`"keep\n"`). After the successful 5-row run with limits patched to `3`/`400`: `sorted(os.listdir(working_dir)) == ["batch_plan.json", "metadata_0.json", "metadata_1.json", "metadata_2.json", "requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl", "responses_0.jsonl"]` — 8 entries — and `open(f"{working_dir}/responses_0.jsonl").read() == "keep\n"`. Against the same directory plus a stale `batch_plan.json` holding `{"plan_format_version": 1, "stale": true}`, `create_request_files(Dataset.from_dict({"prompt": ["ok", "x"*600, "ok"]}))` with `max_bytes_per_batch` patched to `400` raises `SingleRequestTooLargeError(row_idx=1, size_bytes=748, limit_bytes=400)` and all 14 entries survive, with `json.load(open(f"{working_dir}/batch_plan.json")) == {"plan_format_version": 1, "stale": True}` and `open(f"{working_dir}/requests_2.jsonl").read() == "stale\n"`.

**Reversed earlier:** The cleanup was originally the first statement of the `"auto"` branch, run on entry before `plan_request_batches`; it was moved to after planning returns when an oversized-row failure wiped a working directory that still held usable request files.

**What a reader has to infer along the way:**

- *In the auto sizing path, the request and metadata files already sitting in the working directory are taken off disk before the new plan's files are written, rather than being partly overwritten.*
  - nobody says: A run that produces fewer files than the last one leaves the tail of the old numbering behind, and anything that reads the directory by pattern will pick that tail up as if it belonged to the current plan.
- *That removal is confined to the auto path; the explicit-integer batch_size branch and the no-dataset path leave the working directory untouched.*
  - nobody says: A step that only makes sense because the auto path chooses its own file count should not run on paths whose file count is fixed or whose files do not exist.
- *The removal is gated on planning having succeeded: if planning raises, nothing is deleted and nothing is written, and the directory is exactly as it was.*
  - nobody says: A run that produced no output has no business changing what is on disk, so the destructive step has to sit after the step that can refuse.
- *Only the request and metadata files are removed; every other file in the working directory survives untouched, so this is a targeted delete and not a directory wipe.*
  - nobody says: The working directory holds expensive and unrecoverable artifacts alongside the cheap regenerable inputs, so the delete has to be by name rather than by folder.

**Names the tests reach for that the ticket withholds:**

- said: `batch_objects.jsonl`, `batch_plan.json`, `responses_0.jsonl`

> **Spread:** g1.r2.s1: two remarks in #pipeline within 0 days; g1.r2.s2: two remarks in #code-review within 6 days; g1.r2.s3: two remarks in #pipeline within 1 days

### The remarks

#### `g1.r2.l1` — rule

**gideon**, 2025-03-26, #pipeline

> honestly though I hit a similar one, reran auto with a tighter byte cap and the downstream glob still picked up requests_4.jsonl and requests_5.jsonl from yesterdays six batch run

*Drafted as:* reran auto with a tighter byte cap and the downstream glob still picked up requests_4.jsonl and requests_5.jsonl from yesterday's six-batch run.

*Why there:* At 11:10 Emil describes exactly this failure family — request jsonl on disk not matching what actually gets used on a rerun — and Dario at 11:38 escalates it to "a correctness bug, not just a resume edge case." Gideon is in the room all day and habitually chimes in with a corroborating case; a second symptom (stale requests_N.jsonl from a longer prior auto run being globbed back in) strengthens Dario's framing without resolving metadata files, timing, or which sizing branch owns it.

*Still leaves open:* says nothing about metadata files, about when in the run this should be handled, or about which sizing branch is involved

> **Problems:** longer than one remark

#### `g1.r2.l2` — rule

**nils**, 2025-03-26, #pipeline

> metadata_3.json from the previous split is still sitting in there reporting its old num_jobs, so anything reading counts back gets a plan that no longer exists.

*Drafted as:* metadata_3.json in there still reports num_jobs from the old split, so anything reading counts back gets numbers from a plan that no longer exists.

*Why there:* Neither listed room is on this topic. #pipeline 2025-03-17 is one narrow thread — Mistral batch client done, token usage shape unconfirmed, PR 584 blocked, missing wiki pages — all response-side and cost-accounting; a stale on-disk split plan is a different layer and Nils spends that day narrowing his one blocker, not opening another. #code-review 2025-03-25 is pure release triage (what lands, what defers, who reviews 584, where WS-047 lives) with zero code-level detail; Nikolai's PR 583 mention is the metadata *db* as a scoping label, not files on disk. The sibling remark also has to name where in create_request_files the fix goes, which needs two people reading the same function — nobody is in that mode on either day.

*Still leaves open:* does not say what should be done about it, or where in create_request_files it would be done

*A new conversation in #pipeline on 2025-03-26:*

```
10:14  nikolai: quick one while im in create_request_files for 583 does anyone rely on the old request files sticking around between runs or is that dir safe to treat as scratch
10:22  nils: not safe at the moment, that's actually something i hit yesterday. i re-ran a job with a smaller split and the dir still had the previous run's files in it - metadata_3.json in there still reports num_jobs from the old split, so anything reading counts back gets numbers from a plan that no longer exists
10:26  nikolai: yeah thats the same spot i mean the metadata write already knows the run params so clearing or overwriting on the way in is like four lines

off the top of my head it belongs right where we resolve the dir not at read time
10:41  emil: so if i'm following, the counts that feed the cost accounting are coming off those same metadata files? that would explain some of what i was seeing last week when the numbers didnt line up with what i expected for the run size
10:53  nils: possibly, though i'd want to check whether the cost path reads metadata or recomputes from the manifest before we tie those together. let me think through that one
10:58  nikolai: ill leave it out of 583 anyway that pr is scoped to the disable flag and its already big enough
```

#### `g1.r2.l3` — rule

**dario**, 2025-04-22, #pipeline

> honestly writing requests_0 through requests_2 over the top isn't enough when the run before left six of them, the leftovers have to come off disk first

*Drafted as:* writing requests_0 through requests_2 over the top is not enough when the run before left six of them, the leftovers have to come off disk first.

*Why there:* No listed room is chewing on stale batch request files. The viewer thread (04-25) is about dataset flush for the download feature and wants a yes/no guarantee from Dario, not a new failure mode on the submission side. The 03-31 code-review disk thread is a missing cache dir, already resolved by Emil, and re-opening it with a different disk bug reads as a topic change. The 04-09 pipeline thread scopes batch submission only as "has anyone exercised it against the provider changes". The remark needs a room where a re-run has just submitted requests nobody asked for, with others present to supply the metadata question and where the cleanup sits relative to planning.

*Still leaves open:* only mentions request files, not metadata; does not say which branch does this or where it sits relative to planning

*A new conversation in #pipeline on 2025-04-22:*

```
11:14  dermot: re-ran a batch job against a trimmed dataset this morning and it submitted requests that are not in the dataset anymore. if i had to guess the working dir is just stale, the new plan only wrote three files and there are six sitting there
11:21  dario: yeah that would do it. writing requests_0 through requests_2 over the top is not enough when the run before left six of them, the leftovers have to come off disk first. we clobber the ones that happen to collide and the rest just sit there looking legitimate to whatever picks them up later
11:26  emil: mm. so anything that globs the dir picks up the old ones too, they don't look any different from the new batch. not entirely sure the submit path can tell them apart at all
11:31  dermot: it can't, as far as i can tell it just enumerates. that said i only hit it because the second run was smaller, if it had been the same size or bigger nothing would have looked wrong
11:38  dario: mhm, thats the part that bothers me honestly, the failure is silent in the common case. anyway i have to go look at 632 before it goes stale again
```

#### `g1.r2.l4` — scope

**konrad**, 2025-03-20, #code-review

> look, careful with an explicit batch_size - we lean on incomplete_files to skip finished work, and pulling request files out from under that restarts runs people already half paid for

*Drafted as:* Careful with an explicit batch_size, we lean on incomplete_files to skip finished work, and taking request files out from under that restarts runs people already half paid for.

*Why there:* No listed room is chewing on batch request-file creation or resume semantics. The 2025-03-19 and 2025-03-24 #engineering days are about the throttle/cost-estimation path, api_key config and the examples/pricing table; #code-review 2025-05-22 is on PR 667 multiturn state and stale-PR triage; the #releases days are announcement logistics. A remark about a fixed-integer batch_size branch clobbering request files and breaking incomplete_files resume would land in any of them as a subject change with nobody positioned to react. The sibling remark covering the auto path and the no-dataset path implies a line-by-line read of one specific PR, which none of these threads is doing. What should have existed is a #code-review thread on the PR that makes batch_size configurable, in the active batch-mode window in late March, with Konrad reviewing and Nils — who owns the Mistral batch work — walking the three branches.

*Still leaves open:* does not say what the auto path does, or what happens on the no-dataset path

*Must appear literally:* `incomplete_files`, `batch_size`

*A new conversation in #code-review on 2025-03-20:*

```
09:41  nils: now that 584 is unblocked I put up the batch size configuration PR, it's three branches really: auto sizing, an explicit integer from the user, and the case where there's no dataset at all
09:42  nils: the auto path is the one I spent the most time on, the other two are fairly mechanical. would rather have eyes on whether the split is right than on the arithmetic
09:58  konrad: look, careful with an explicit batch_size. we lean on incomplete_files to skip the work that is already finished, and if you take the request files out from under that, the run starts over and people have half paid for it already
10:06  nils: fair enough, let me think through that. i think the explicit branch only rewrites when the requested size differs from what's on disk, but I'd have to go read it again to be sure
10:14  dermot: so you're saying the no-dataset branch never touches the files at all? that one i'm less worried about
10:21  gideon: honestly though the auto path is where I would spend the review time, so basically everything else downstream inherits whatever it picks
```

#### `g1.r2.l5` — scope

**dermot**, 2025-05-06, #code-review

> yeah, keeping the cleanup inside the auto sizing branch rather than hoisting it up into create_request_files. the fixed-width branch has its own resume contract, it shouldnt inherit ours

*Drafted as:* cleanup for the auto sizing path stays next to the sizing code; the fixed-width branch has its own resume contract and should not inherit ours.

*Why there:* None of the four listed places is chewing on batch payload sizing. WS-055 is a release-engineering/CI charter (cache fingerprints, gating, tagging) and never touches request-file construction; the May 5 weekly notes are a status roll-up in reporting voice, where a scoping call about where cleanup lives inside a branch would read as a stray code comment; v0.1.21 notes are a stub changelog from March; the v0.1.23.post1 postmortem is about a hotfix gate and would have to invent a regression to attach this to. The remark is a reviewer settling a placement argument on a specific diff, and it needs the sibling remark (what the cleanup does, when it fires, what the no-dataset path does) sitting right next to it — that only works in a code-review thread on the auto-sizing PR. The natural home is emil's batch-mode work, which the May 5 notes already flag as in flight with nothing mergeable yet, i.e. exactly the WIP-review stage where this call gets made.

*Still leaves open:* does not say what the cleanup consists of, when it runs, or what the no-dataset path does

*A new conversation in #code-review on 2025-05-06:*

```
10:42  emil: pushed the auto batch sizing branch, not opening a PR yet but if anyone has ten minutes i'd take early eyes on it. one thing i keep going back and forth on: the leftover shard cleanup currently lives inside the auto branch, and i believe it could just as easily be hoisted to the top of the function so both sizing modes get it for free
10:43  emil: honestly the argument for hoisting is mostly that it reads cleaner, which is not a great argument on its own
10:51  dario: before the readability question, what does hoisting do to resume? does the cleanup run before we've looked at what's already on disk, or after? because if it's before then a rerun on the fixed width path starts deleting shards it was going to reuse
11:06  dermot: cleanup for the auto sizing path stays next to the sizing code; the fixed-width branch has its own resume contract and should not inherit ours. lifting it to the top of create_request_files means one cleanup rule for two paths that don't agree on what a stale shard is
11:14  dario: mhm, that tracks. i'd still want a test that reruns fixed width with shards already sitting there, we don't have one and i'm not entirely sure the current behaviour is what we think it is
11:20  emil: yup, i can add that. will leave it where it is for now and put the rerun test in the same branch, that said the naming in there is still rough so don't read too much into it
```

#### `g1.r2.l6` — scope

**emil**, 2025-03-14, #code-review

> @Gideon on that request processing cleanup - the dataset=None leg never writes a request file at all, so there's nothing there to tidy, i'd leave that one alone

*Drafted as:* the None-dataset leg never writes a request file at all, so there is nothing there to tidy, leave that one alone.

*Why there:* Gideon opened the day (09:00) saying he was wrapping up "a small cleanup on the request processing side" and nobody ever picks it up — the thread is left dangling while the room drifts to schema_check. Emil is already replying to Gideon in that 11:36–11:37 burst (PR number question, PR 579 status), so him tacking on a note about which leg of the request-file path actually has anything to clean up lands naturally and answers a live, unanswered item. It also doesn't collide with the construction-hook discussion, and nothing said so far touches the dataset=None path.

*Still leaves open:* says nothing about either sizing branch or about what the tidying involves

#### `g1.r2.l7` — failure_behavior

**nikolai**, 2025-06-11, #pipeline

> the oversized row aborted the run and i came back to an empty working dir nothign new written and the files that were fine gone with it

*Drafted as:* The oversized row aborted the run and I came back to an empty working dir, nothing new written and the files that were fine gone with it.

*Why there:* Neither mail is chewing on anything this touches. The Apr 16 thread is a code-review pre-read about docker backend_params image pinning — nikolai's own open question there is what the sandbox repo publishes and whether create should fail loudly; a wiped working dir from a planning run is a different system entirely. The Jun 16 recap has exactly two live items, dario's multimodal Gemini batch request fix (PRs 690/691) and the go/no-go on PR 653; a fresh incident report about an oversized row aborting a run and taking good files with it would change the subject in a status mail nikolai himself wrote to close the week, and nothing in it would draw a reply. The remark is also explicitly half of a pair — the other half says which step should have been gated on which — which needs a room where a fix is being argued, not a recap. What should exist is a same-day thread in #pipeline the week of Jun 9, nikolai reporting the aborted run against batch-payload-plan and losing the working dir, dario and emil pulling on whether the plan should validate before anything is written and where the oversized row should have been caught, which is also where the sibling remark lands.

*Still leaves open:* does not say what should have happened instead, or which step ought to have been gated on which

*A new conversation in #pipeline on 2025-06-11:*

```
10:14  dario: did the rerun over the new inputs actually finish or is it still chewing, i wanted to eyeball the outputs before we talk about the schema thing
10:21  nikolai: nope died maybe a third of the way in one of the rows is way over size batch-payload-plan aborted the run and i came back to an empty working dir nothing new written and the files that were fine gone with it
10:26  emil: so youre saying it took out the stuff that had already landed, not just the partial from this run? that seems like more than it needed to do honestly
10:28  nikolai: right whole dir the two shards from thursday were sitting in there as well
10:35  dario: mhm. finding the oversized row is easy at least, i'd bet on the one out of the vendor dump, it's been fat since they changed the export. in any case i still have thursday on the archive box if you need it back today
10:41  emil: i believe the size ceiling is configurable? not entirely sure where though, let me think through that one after the call
```

#### `g1.r2.l8` — failure_behavior, observability

**gideon**, 2025-04-09, #pipeline

> so basically batch submission blew up with SingleRequestTooLargeError(row_idx=1, size_bytes=748, limit_bytes=400), then I went to diff against the previous batch_plan.json and there was nothing left to diff

*Drafted as:* SingleRequestTooLargeError(row_idx=1, size_bytes=748, limit_bytes=400), then I went to diff the new split against the previous batch_plan.json and there was nothing left to diff.

*Why there:* That day the room is explicitly trying to get the batch submission path covered before calling Dermot's provider changes clean, and Dermot hands that path to Gideon at 15:36. Gideon starting on it after his DM with Emil and immediately hitting a planning-time raise that wipes the working artifacts complicates exactly the "is batch submission clean" question Dario flagged at 15:11, without touching the gemini response-shape thread Emil owns. Nobody has said anything yet about failures destroying prior state, so it isn't redundant — and it deliberately leaves open whether the request files survived, which someone else has to answer.

*Still leaves open:* does not say whether the request files survived, or what the correct behaviour on a raise is

*Must appear literally:* `batch_plan.json`, `SingleRequestTooLargeError`

#### `g1.r2.l9` — failure_behavior

**dermot**, 2025-04-08, #pipeline

> when the planner refuses a row i want to fix that one row and rerun against the same directory, not rebuild everything that was already sitting there

*Drafted as:* when the planner refuses a row i want to fix that one row and rerun against the same directory, not rebuild everything that was already sitting there.

*Why there:* None of the eight rooms are chewing on the planner or on what a run leaves behind in its working directory. The closest is #general 2025-04-29, but that thread's live question is abort-vs-fallback when a *stored job* can't be reused, and rewriting the remark to fit it would replace "planner refuses a row" with a different failure — changing what the remark says. #pipeline 2025-03-24 is about where a batch job id gets persisted after a reboot, not about a validation raise mid-plan, so "the planner refuses a row" would arrive with no referent and get no reaction. What's missing is the thread where someone hits a planning-stage refusal on a bad row and reruns — that's where the team lands on a raise being non-destructive, and where the sibling remark can say what the directory actually holds and what got thrown away.

*Still leaves open:* does not say what is currently lost, or what the directory holds

*A new conversation in #pipeline on 2025-04-08:*

```
09:41  emil: the overnight payload planning run raised on one malformed row about a third of the way in. fixed the row this morning and kicked it off again and it just... started the whole directory over
09:42  emil: not entirely sure yet whether it wiped what was there or just ignored it and rewrote, i havent gone through the timestamps
09:47  dermot: when the planner refuses a row i want to fix that one row and rerun against the same directory, not rebuild everything that was already sitting there. if i had to guess the raise unwinds before anything gets marked done, so the second pass has no reason to believe the prepared shards are hers— sorry, are usable
09:53  dario: mhm. is that the same marker the resume path reads, or does planning keep its own thing separate from the batch state
09:56  dermot: separate as far as i know. that said i've only looked at it from the submit side
10:04  emil: i'll pull the failed row out and re-run against a copy of the dir tonight so we at least know which of the two it is. honestly the bigger cost was the eight hours not the rewrite
```

#### `g1.r2.l10` — exclusions_or_crossover, observability

**dario**, 2025-03-21, thread:<178778732260.3143269.10750283081321891939@world.local>

> i hit this myself actually — cleared the working dir by hand between two auto runs and lost responses_0.jsonl, so we paid for those completions a second time.

*Drafted as:* I cleared the working dir by hand between two auto runs and lost responses_0.jsonl, so we paid for those completions a second time.

*Why there:* That thread is already arguing about what "resumable" means when only the request and response files follow CURATOR_CACHE_DIR, and Emil is asking whether the gap needs its own issue. Dario is on the thread and a concrete incident — losing a response file to a manual cleanup and paying for the completions again — is exactly the kind of evidence that makes the gap a real cost rather than a design nit. It complicates Emil's framing without settling what a targeted delete should keep, which the sibling remark handles.

*Still leaves open:* does not say what a targeted delete would keep or remove, and mentions only one of the artifacts at risk

*Must appear literally:* `responses_0.jsonl`

#### `g1.r2.l11` — exclusions_or_crossover

**konrad**, 2025-04-10, #engineering

> look, batch_objects.jsonl is how we recover the submitted batch ids, if a rerun removes it we cant poll the batches we already sent.

*Drafted as:* batch_objects.jsonl is how we recover the submitted batch ids, if a rerun takes that out we cannot poll the batches we already sent.

*Why there:* The remark is a constraint offered into a live argument about a rerun clearing a batch working directory, and it needs a sibling naming the removing code path. No candidate room is on that. #releases 2025-04-11 names a "jsonl handling fix" but is purely about announce copy and notes ownership. #cookbooks 2025-04-03 has Dario's lost CSV and Emil reading WS-050 on where batch state gets written, but the loss there is CodeExecutor overwriting a mounted input, not a rerun deleting its own state, and Konrad is occupied with the SimpleStrat run and RAFT distractors. The other six are provider PR sequencing, cost/examples tables, factory cleanup scope, ws-069 close-out, and viewer rendering. Dropped anywhere in that list it changes the subject and draws no reply. It belongs the day before the 0.1.23 cut, where the jsonl handling fix actually came from.

*Still leaves open:* does not say what is safe to remove, or which code path is doing the removing

*Must appear literally:* `batch_objects.jsonl`

*A new conversation in #engineering on 2025-04-10:*

```
14:12  nils: ran a batch job a second time into a working dir that already had output in it, and it came back with nothing to poll. traced it to the cleanup step that clears the request and response files on start
14:13  nils: so the rerun wipes state that the first run was still depending on. or at least that's what it looks like from here
14:19  konrad: batch_objects.jsonl is how we recover the submitted batch ids, if a rerun takes that out we cannot poll the batches we already sent
14:20  konrad: the requests and responses are fine to clear presumably. anyway that file is not the same category of thing
14:34  dermot: so you're saying this is in the 0.1.23 cut as it stands? we're tagging tomorrow
14:41  nils: let me think, the cleanup landed before the branch point so yes i think it's in. i'll look at what the fix costs
```

#### `g1.r2.l12` — exclusions_or_crossover

**nils**, 2025-03-24, #pipeline

> let me think - the .arrow shards under there are the cached dataset, drop those and we rebuild the whole thing before anything gets submitted.

*Drafted as:* the .arrow shards under there are the cached dataset, drop those and we rebuild the whole thing before anything gets submitted.

*Why there:* Neither room is chewing on files on disk. #engineering 2025-03-19 is entirely release notes for v0.1.21, the output-token fix, and who owns the throttle check — nobody there mentions caches, working directories, or anything that would be deleted, and nils' two messages that day are about the api_key decision and PR 584 timing. #pipeline 2025-03-25 does have nils removing things, but the thing being removed is Mistral fixture tests from provider-integrations, and the whole thread's question is test coverage, not on-disk state; a warning about .arrow shards there would read as answering a question nobody asked, and Dario/Emil's coverage sign-off exchange gives it nothing to attach to. The remark presupposes someone has just proposed wiping a directory before a batch resubmission — that proposal doesn't exist in either transcript. It belongs the day before 584 goes up, when nils is actually re-running stuck Mistral batches and someone suggests clearing state to unstick one; that's also where the sibling remark naming the right path to delete has somewhere to land.

*Still leaves open:* does not say what should be removed instead, or by which path

*A new conversation in #pipeline on 2025-03-24:*

```
10:12  nils: the mistral run I kicked off while finishing the processor for 584 is wedged partway through submission. some of the request files went up, the rest didn't, and the client is sitting there waiting on a job id that i don't think ever came back
10:19  emil: honestly could you not just clear out the working dir and resubmit form scratch? i'm not entirely sure there's anything in there worth preserving if the submisison never completed cleanly
10:26  nils: let me think through that. the request files under the working dir, sure, those are cheap to regenerate. but the .arrow shards under there are the cached dataset, drop those and we rebuild the whole thing before anything gets submitted
10:31  dario: mhm, and that's not a five minute rebuild either at 40k rows. actually i think emil hit the same thing on the anthropic side this morning
10:38  emil: fair, so the safe thing is scoping the delete to just the request files. we need to be intentional here about what the resubmit path is allowed to touch, becuase right now i believe it's mostly whatever the person running it decides
10:44  nils: right. and it isn't documented anywhere that i can find, which is worth documenting once i know what the recovery path actually looks like
```

#### `g1.r2.l13` — exclusions_or_crossover

**nikolai**, 2025-06-19, #pipeline

> i'd say whatever we take out gets named off what that run writes itself, emptying the folder is a differnt operation and not the one we want

*Drafted as:* whatever we take out should be named by what that run itself writes, emptying the folder is a different operation and not the one we want.

*Why there:* The remark rules on the shape of a delete operation — by-name versus directory wipe — and needs a live proposal to wipe a folder sitting above it. Image pinning is about tags and the backend_params bypass, with nothing being removed. The structured-output page is a postmortem about a skipped gate, not file cleanup. The Jun 16 sync is the closest, since it parks "issue 124 - inspect cache invalidation on whitespace", but that line is an unowned carried-over question in a PR roll-up, not a decision in progress; a design ruling in that bullet list would read as pasted in. What's missing is the room where someone hits a half-finished batch run leaving artifacts behind and proposes clearing the cache dir.

*Still leaves open:* does not name which files that run writes, nor which of the other artifacts are at stake

*A new conversation in #pipeline on 2025-06-19:*

```
10:12  emil: hit a batch run this morning that died about two thirds through and left a pile of half written shards in its cache dir, the retry then picks them up and gets very confused. honestly the simplest thing i can see is have the retry path clear the directory first and start clean — thats what im imagining anyway, or is that too blunt
10:15  shreyas: thats basically 124 right, we parked it in the sync yesterday because nobody wanted it
10:16  emil: yup same thing. so it has an owner now i guess
10:21  nikolai: on 124 whatever we take out should be named by what that run itself writes emptying the folder is a diffrent operation and not the one we want
10:25  emil: sounds right. i believe the manifest already has the shard names in it from the plan step so its not like we'd have to go discover them, though i'm not entirely sure it gets flushed before the workers start
10:29  shreyas: it gets written at plan time yeah. whether its fsynced is another question
```

#### `g1.r2.h1` — herring

**dario**, unplaced, —

> i think the sweep is the first statement in the auto branch - glob the stale requests_*.jsonl and metadata_*.json, remove them, then plan_request_batches runs on a clean diretcory

*Drafted as:* the sweep is the first statement in the auto branch — glob the stale requests_*.jsonl and metadata_*.json and remove them, then plan. clean directory before we compute anything.

#### `g1.r2.h2` — herring

**emil**, unplaced, —

> so to restate the order: in create_request_files we clear the old requests_*/metadata_* on entry, then call plan_request_batches. nothing stale is ever in the dir while we plan.

*Drafted as:* Confirming the order in create_request_files: clear the old requests_*/metadata_* on entry, then call plan_request_batches. Nothing stale is ever in the dir while we plan.

