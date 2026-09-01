# Clues for g1 — Batch payload planner for `batch_size="auto"`

39 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/latest`.

Clue window `2025-03-14` to `2026-01-27`; herrings before `2025-03-13`.

**Nothing here has been inserted into the corpus.** This is the plan: what each person says, where it goes, and why it belongs there.

## The task the agent is given

Replace the ad-hoc sizing loop used by `batch_size="auto"` with a pure, testable planner. Add `src/bespokelabs/curator/request_processor/batch_payload_planner.py` exporting: `@dataclass(frozen=True) class BatchLimits` with fields `max_requests_per_batch: int` and `max_bytes_per_batch: int`; `@dataclass(frozen=True) class PlannedBatch` with fields `index: int`, `start_idx: int`, `end_idx: int`, `num_requests: int`, `num_bytes: int`; `def payload_size_bytes(api_specific_request: dict) -> int` returning `len(json.dumps(d).encode())`; `def payload_bytes(sizes: Sequence[int]) -> int` returning the exact size of the `"\n".join(...)` file those payloads produce (`0` for an empty sequence); `def plan_batches(sizes: Sequence[int], limits: BatchLimits) -> list[PlannedBatch]` walking the sizes once in index order and greedily filling contiguous, ordered, exhaustive spans (`plan[0].start_idx == 0`, `plan[i].end_idx == plan[i+1].start_idx`, `plan[-1].end_idx == len(sizes)`), keeping a batch that lands exactly on either limit and returning `[]` for no sizes; `class BatchPayloadTooLargeError(ValueError)` with `__init__(self, *, num_requests: int, size_bytes: int, limit_bytes: int) -> None` storing those three as attributes; and `class SingleRequestTooLargeError(BatchPayloadTooLargeError)` with `__init__(self, *, row_idx: int, size_bytes: int, limit_bytes: int) -> None`, storing `row_idx` and `num_requests == 1`, raised when one request's own size exceeds `max_bytes_per_batch` (instead of today's `batch_size = 0` hang). On `BaseBatchRequestProcessor` (`request_processor/batch/base_batch_request_processor.py`) add a `batch_limits` property built from `self.max_requests_per_batch` / `self.max_bytes_per_batch`, `def measure_request_payload(self, generic_request: GenericRequest) -> int` returning `payload_size_bytes(self.create_api_specific_request_batch(generic_request))` — the provider payload that is actually submitted, not the generic request written to `requests_*.jsonl` — and `def plan_request_batches(self, dataset: "Dataset") -> list[PlannedBatch]` which builds each row through `PromptFormatter.create_generic_request(row, idx, generation_params_per_row)` with `generation_params_per_row = "generation_params" in dataset.column_names`, measures each row exactly once in index order, and returns `plan_batches(sizes, self.batch_limits)`; `create_batch_file(self, api_specific_requests: list[dict]) -> bytes` keeps its signature (return annotation corrected from `str`) and raises `BatchPayloadTooLargeError` where it raises `ValueError` today, so a planned batch's `num_bytes` equals `len(create_batch_file(...))` for that batch. In `base_request_processor.py`, delete the nested `_get_optimal_batch_size` (lines 263‑278) and the `while True` loop (lines 282‑295), drive the `"auto"` branch of `create_request_files(dataset: Optional["Dataset"]) -> list[str]` (unchanged signature) off `self.plan_request_batches(dataset)`, write each planned batch through the existing `acreate_request_file(...)` as `requests_{p.index}.jsonl` with `metadata_{p.index}.json`, and return `[os.path.join(self.working_dir, f"requests_{p.index}.jsonl") for p in plan]` — one path per planned batch, in `index` order (a 0-row dataset therefore returns `[]`). The explicit-integer `batch_size` branch (lines 297‑311) keeps its current behaviour exactly: `ceil(len(dataset) / batch_size)` fixed-width files filtered by `incomplete_files`, no byte-based resplit, no planner call. `max_requests_per_batch` / `max_bytes_per_batch`, `acreate_request_file` (metadata body `{"num_jobs": n}`) and `run_in_event_loop` are reused as-is. Tests build processors via `__new__` with `config`, `prompt_formatter`, `working_dir`, `_cost_processor` assigned by hand and patch the two limit properties with `unittest.mock.PropertyMock`; no network, no clients, no sleeps.

## Every remark, in the order a reader would meet them

| date | where | who | says | carries |
|---|---|---|---|---|
| 2025-01-21 | #releases *(new)* | dario | settled then, the span lives in metadata_{i}.json right next to num_jobs, so each file carries its own start_idx, end_idx and num_bytes. no separate plan file, in any case | *herring* |
| 2025-01-21 | #cookbooks *(new)* | dario | i think the sweep goes as the first statement in the auto branch - glob the stale requests_*.jsonl and metadata_*.json, drop them, then plan_request_batches runs on a clean diretcory | *herring* |
| 2025-01-22 | #cookbooks *(new)* | emil | so to restate the order: in create_request_files we clear the old requests_*/metadata_* on entry, then call plan_request_batches - nothing stale is ever in the dir while we plan? | *herring* |
| 2025-01-27 | #engineering | konrad | look, from my review pass the auto batches carry {num_jobs, start_idx, end_idx, num_bytes} in each metadata_{i}.json, so the plan lives in the per batch metadata not a seperate file | *herring* |
| 2025-03-14 | #code-review *(new)* | gideon | auto path on an empty dataset left me a bare dir. honestly though I'd want batch_plan.json anyway — num_batches 0, num_requests 0, num_bytes 0, batches [], plan_id filled in like any other run. | `scope`, `observability` |
| 2025-03-14 | #engineering *(new)* | konrad | Look, if I pass batch_size=2, or I give no dataset at all, then I picked the split myself. no batch_plan.json should be turing up in my working dir for those. | `scope` |
| 2025-03-14 | #releases *(new)* | emil | honestly, went to put the fragmentation count in our alert line and there's no num_batches on the error anywhere, just the ceiling - had to re-derive it from len(plan) | `failure_behavior` |
| 2025-03-14 | #general *(new)* | nils | ran the auto path over an empty input this morning and plan_fingerprint still handed me back a plan_id, same one i get hashing an empty string in a repl. | `rule` |
| 2025-03-14 | #cookbooks *(new)* | konrad | look, careful with the explicit batch_size branch - we lean on incomplete_files to skip finished work, and pulling request files out from under that restarts runs people already half paid for | `scope` |
| 2025-03-17 | #engineering *(new)* | konrad | Look, auto sizing with a tigth byte cap gave me 31k request files in one dir. If we refuse that, err.limit alone is useless, I need the count it wanted. | `failure_behavior`, `observability` |
| 2025-03-17 | #releases *(new)* | dermot | yeah - plan_id is a digest of the canonical batch lines and nothing else; zero lines join to an empty string and that goes into sha256 like any other input. | `scope` |
| 2025-03-17 | #cookbooks *(new)* | nikolai | i'd say whatever we delete gets named off what that run writes itself, wiping the folder is a differnt operation and not the one we want | `exclusions_or_crossover` |
| 2025-03-18 | #engineering *(new)* | nikolai | i'd say the cap goes on the limits dataclass as max_batches_per_plan default 512 checked once the plan is finished and a plan landing on exactly 512 is still fine | `failure_behavior`, `rule` |
| 2025-03-18 | #releases *(new)* | emil | @Gideon on the request processing cleanup - the dataset=None leg never writes a request file at all, so honestly there's nothing there to tidy, i'd leave that one alone | `scope` |
| 2025-03-19 | #engineering *(new)* | nils | let me think - i sent 600 tiny rows plus one 5MB row and got the fragmentation error back, when what i wanted was SingleRequestTooLargeError with row_idx 600 named in it. | `failure_behavior` |
| 2025-03-19 | #releases *(new)* | dermot | when the planner refuses a row i want to fix that one row and rerun against the same working directory, not rebuild everything that was already sitting there | `failure_behavior` |
| 2025-03-21 | page:design/batch-job-status-persistence-across-process-restarts.md | nils | metadata_3.json from the previous split is still sitting in the cache dir reporting its old num_jobs, so a restart reading counts back gets a plan that no longer exists. | `rule` |
| 2025-03-21 | thread:<178778732260.3143269.10750283081321891939@world.local> | dario | on the same note — writing requests_0 through requests_2 over the top isn't enough if the run before left six of them, the leftovers have to come off disk first | `rule` |
| 2025-03-21 | page:design/batch-job-status-persistence-across-process-restarts.md | gideon | so basically submission blew up with SingleRequestTooLargeError(row_idx=1, size_bytes=748, limit_bytes=400), then i went to diff against the previous batch_plan.json and there was nothing left to diff. | `failure_behavior`, `observability` |
| 2025-03-21 | page:design/batch-job-status-persistence-across-process-restarts.md | konrad | look, batch_objects.jsonl is missing here, its how we recover the submitted batch ids, if a rerun in the same directory removes it we cant poll what we already sent. | `exclusions_or_crossover` |
| 2025-03-24 | #pipeline | dario | honestly the other half of this - i had a run die partway through writing requests_*.jsonl and nothing on disk said what it had been aiming for. batch_plan.json wants to land before the first requests file, metadata too | `scope` |
| 2025-03-25 | #pipeline | nils | let me think - the .arrow shards under provider-integrations are the cached dataset, not fixtures; drop those and we rebuild the whole thing before anything gets submitted | `exclusions_or_crossover` |
| 2025-03-26 | #pipeline | gideon | honestly though I hit a similar one, reran auto with a tighter byte cap and the glob still picked up requests_4.jsonl and requests_5.jsonl from yesterdays six batch run | `rule` |
| 2025-04-02 | #code-review *(new)* | dermot | the num_bytes next to those counts should just be the sizes create_batch_file hands back, summed — i checked the current figure against du on the dir and they don't agree. | `rule` |
| 2025-04-03 | #cookbooks | nikolai | Had a planning run abort on an oversized row and came back to an empty working dir, nothing new written and the files that were fine gone too. | `failure_behavior` |
| 2025-04-08 | #engineering | nikolai | first cut on request_id - sha256 hexdigest is 64 chars and the full thing just wraps the log line so twelve off the front is plenty for eyballing two runs against each other | `observability` |
| 2025-04-09 | #code-review *(new)* | konrad | Anyway while house rules are going on record - batch_plan.json should be written with indent 2 and a newline on the end, our review diffs are unreadble when it comes out on one line. | `rule`, `observability` |
| 2025-04-09 | #pipeline *(new)* | konrad | Right, I renamed the colum in my run notes to plan_id then, I had it down as plan_hash. It's whatever plan_fingerprint hands back - twelve hex chars, f4b1ea1573c0. | `rule` |
| 2025-04-16 | #code-review *(new)* | gideon | so basically the limits block in the doc came out with three keys once max_batches_per_plan landed, and my snapshot only pinned the two byte/request ones, so it's red. | `rule`, `failure_behavior` |
| 2025-04-21 | thread:<178770212973.2301745.4705747507669611471@world.local> | dario | i hit one of these myself actually — cleared the working dir by hand between two auto runs and lost responses_0.jsonl, so we paid for those completions a second time. | `exclusions_or_crossover`, `observability` |
| 2025-04-23 | #pipeline | gideon | ya same on my side - an auto run gave me 9 request files and nothing says which rows landed in requests_3.jsonl, had to reopen all of them to find one promt | `rule` |
| 2025-04-24 | #pipeline *(new)* | dermot | for the wiki page: the planner module holds PLAN_FILE_NAME and PLAN_FORMAT_VERSION next to the two dataclasses, version starts at 1 and only moves when the key set changes. | `rule` |
| 2025-04-24 | #code-review | dario | same family of thing honestly — my except for payload-too-large caught a BatchPlanTooFragmentedError this morning, the outer except ValueError should have had it, those aren't the same failure | `failure_behavior` |
| 2025-04-29 | #pipeline *(new)* | emil | nit on the plan_document draft — i'd put plan_format_version first and the id right after it, i want to know whether i can parse the rest before i read it. | `rule` |
| 2025-05-13 | #pipeline *(new)* | nikolai | for the run dashbaord i read num_batches and num_requests right after the limits block i dont walk the per batch rows so keep those rows in as well | `rule`, `observability` |
| 2025-05-13 | #code-review *(new)* | emil | honestly the empty plan case looks fine as-is to me - zero batches join to nothing, and plan_fingerprint([]) still handed back e3b0c44298fc, i don't think we need to special-case it | `observability` |
| 2025-06-10 | #pipeline *(new)* | nils | let me think - our metadata_{i}.json reader asserts the body is num_jobs and nothing else, it bails on anything extra. so please keep the span keys out of those. | `exclusions_or_crossover` |
| 2025-06-19 | #engineering *(new)* | dario | i think plan_fingerprint should hash just the batches joined, 0-2:307;2-4:307 - spans and bytes, not index, not num_requests. utf-8 encode, sha256, keep the front of the hexdigest. | `rule`, `observability` |
| 2025-06-25 | page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md | dermot | yeah, and the cleanup stays inside the auto sizing branch, not hoisted up into create_request_files. the fixed-width branch has its own resume contract, it shouldnt inherit ours | `scope` |

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

> **Spread:** g1.r1.s1: two remarks in #pipeline within 1 days; g1.r1.s5: two remarks in #engineering within 1 days; g1.r1.s5: two remarks in #engineering within 1 days

### The remarks

#### `g1.r1.l1` — rule

**gideon**, 2025-04-23, #pipeline

> ya same on my side - an auto run gave me 9 request files and nothing says which rows landed in requests_3.jsonl, had to reopen all of them to find one promt

*Drafted as:* auto run gave me 9 request files and nothing anywhere says which rows landed in requests_3.jsonl. had to reopen all of them to find one prompt.

*Why there:* Emil has just laid out that the persisted job record only holds an id, a request file path and a timestamp, so handing someone a run dir tells them nothing about what actually went out. Gideon is already in that thread pressing on what can and can't be recovered after the fact (the cache-entry count question), so him piling on with a second instance of the same gap — an auto-split run leaving no record of which rows went where — lands as agreement rather than a topic change, and it sets up Dermot's "the fingerprint and the job record have the same gap" and Emil's later proposal to fix the record side.

*Still leaves open:* what should be written instead, what it is called, or where it goes

*Goes into the real conversation in #pipeline on 2025-04-23, after 15:09 emil:*

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
15:09  emil: Related: the persisted job record doesn't store the model either, just the id, the request file path, and a timestamp  <-- the remark goes here
15:09  emil: and this isn't the first time either, it's bitten me twice this week  <-- the remark goes here
15:09  emil: that's the whole record, nothing else on it  <-- the remark goes here
15:09  emil: so if someone hands me a run dir I can't tell what model it went out with, and that means I can't tell if picking it back up is safe  <-- the remark goes here
15:35  dermot: the fingerprint and the job record have the same gap
15:39  dario: I'd want @Nikolai Berresford in this before we touch anything - I dunno off the top of my head if the count is even pullable without adding instrument
16:59  gideon: Good call holding off
16:59  gideon: That's the right move
17:13  emil: We could fix the job record side independently, just write the model into the pending record without touching the cache key at all.
```

> **Problems:** longer than one remark

#### `g1.r1.l2` — rule

**dermot**, 2025-04-24, #pipeline

> for the wiki page: the planner module holds PLAN_FILE_NAME and PLAN_FORMAT_VERSION next to the two dataclasses, version starts at 1 and only moves when the key set changes.

*Drafted as:* wiki: planner file also holds PLAN_FILE_NAME and PLAN_FORMAT_VERSION beside the two dataclasses, version is 1 and only moves when the key set does.

*Why there:* None of the listed rooms is chewing on a planner module, a plan file, or its dataclasses. The nearest fit, #pipeline 2025-04-21, is about job reuse and which keys make a stored job a "mismatch"; Emil owes a list, Dario owes the reattach rewrite, and a constants-and-format-version note about a wiki page arrives as a new subject with nothing to answer and nobody to react. The releases threads are about notes and sign-off, the code-review threads about PR 644 rendering and PR 565's bypass naming, viewer is about local-vs-hosted. Dermot writing "for the wiki page" also presupposes a doc that somebody is actively drafting, which doesn't exist in any of these days. What should have existed: a #pipeline thread a few days after the 04-21 job-reuse discussion, once the planner that emits the batch payload plan has landed, where Dermot and Dario settle what goes on the wiki page for it — Dermot covering the module surface (the file-name constant and format version beside the two dataclasses), Dario covering what the file actually contains and at which point in the submit path it gets written, with Emil folding in the mismatch-key list he promised on the 21st.

*Still leaves open:* what the file named by that constant actually contains, and when it gets written

*Must appear literally:* `PLAN_FILE_NAME`, `PLAN_FORMAT_VERSION`

*A new conversation in #pipeline on 2025-04-24:*

```
11:12  dario: now that the reattach rewrite is in i should probably write the planner up on the wiki, or at least start the page. i can take the resume/reattach side of it if you want to take the plan file itself
11:19  dermot: yeah ok, i'll take the plan file half
11:24  dermot: for the wiki page: planner file holds PLAN_FILE_NAME and PLAN_FORMAT_VERSION beside the two dataclasses, version is 1 and only moves when the key set does
11:31  dario: mhm that tracks. i'll link out to your section from the reattach part rather than restating any of it, there's already enough drift between the docstrings and what's actually there
11:40  emil: if either of you touches the page today can you leave the old resume notes in place for now, i think there's still something in there about the pre-rewrite layout that nikolai was referencing last week. not entirely sure it's still accurate but
11:46  dermot: i wasn't planning to delete anything, just adding below. that said the old section is going to read strangely next to it
```

#### `g1.r1.l3` — exclusions_or_crossover

**nils**, 2025-06-10, #pipeline

> let me think - our metadata_{i}.json reader asserts the body is num_jobs and nothing else, it bails on anything extra. so please keep the span keys out of those.

*Drafted as:* our metadata_{i}.json reader asserts the body is num_jobs and nothing else, it bails on anything extra. so please keep span keys out of those.

*Why there:* None of the listed rooms is chewing on the shape of per-batch payload sidecars. The persistence design page is the nearest miss: it is about the sqlite metadata db vs the append-only responses file and about read-only opens on restart, and it never mentions numbered metadata_{i}.json files or spans at all — a comment introducing both a new on-disk artifact and a new constraint about span keys would be the first anyone there had heard of either, and Emil's page gives nils nothing to pick up. The weekly notes and release notes are status ledgers, not places where a reader assertion gets argued. What should have existed is the batch-payload-splitting thread itself: when a payload gets sharded across numbered request files, someone has to record which row range landed in which shard, and the obvious first suggestion is to hang start/end keys off the per-shard metadata. That is the moment nils pushes back with what the reader actually accepts, and the moment someone else answers with where the span information should live instead.

*Still leaves open:* where the span information is supposed to live instead

*A new conversation in #pipeline on 2025-06-10:*

```
10:412  emil: placeholder
```

> **Problems:** longer than one remark

#### `g1.r1.l4` — rule, observability

**konrad**, 2025-04-09, #code-review

> Anyway while house rules are going on record - batch_plan.json should be written with indent 2 and a newline on the end, our review diffs are unreadble when it comes out on one line.

*Drafted as:* Write batch_plan.json with indent 2 and a newline on the end, our review diffs are unreadable when it comes out on one line.

*Why there:* All six candidates are konrad's weekly status mails — PR triage, release cuts, examples-cookbooks. None is discussing repo conventions, generated artifacts, or anything a formatting house rule would attach to, and none mentions a batch plan file. The remark's opening ("while house rules are going on record") only works in a room actively recording conventions, and it needs someone who owns the writer to answer it. In a weekly update it would change the subject and sit unanswered. The right room is the WS-055 (Release Engineering, CI & Test Suite) conventions thread konrad himself flagged on Apr 7 — Dermot's design was posted, the team was reading it and pinning down owners and rules, and generated-file formatting would surface exactly there.

*Still leaves open:* what is inside the file and which runs produce it

*Must appear literally:* `batch_plan.json`

*A new conversation in #code-review on 2025-04-09:*

```
10:12  dermot: before WS-055 gets properly underway i'd like to settle a few repo level rules so they don't get relitigated in every review. lint config stays as it is, no per-package overrides. fixtures live under tests/fixtures/<module>/ and generated files are committed rather than gitignored
10:19  emil: so fixtures per module rather than one shared tests/fixtures dir, is that the read? i believe we have a couple already sitting at the top level from the batch-mode work, not entirely sure who put them there
10:24  konrad: right, per module is fine by me. Anyway while house rules are going on record - batch_plan.json should be written with indent 2 and a newline on the end, our review diffs are unreadble when it comes out on one line
10:31  dario: mhm, that tracks. i think whatever is writing it is just calling json.dump with the defaults, so honestly it's a two line change, someone just has to actually go and do it
10:40  dermot: yeah ok. that said the one i actually wanted settled is whether the fixture files get regenerated in ci or by hand, because if i had to guess that's where the arguments start
```

#### `g1.r1.l5` — rule

**emil**, 2025-04-29, #pipeline

> nit on the plan_document draft — i'd put plan_format_version first and the id right after it, i want to know whether i can parse the rest before i read it.

*Drafted as:* review nit: plan_document should lead with plan_format_version and then the id, i want to know whether i can parse the rest before i read it.

*Why there:* Every listed room is doing PR triage, ownership chasing, or a specific behavioral question (429 headers, read-only mounts, stopping criterion placement) — none has a drafted document schema in front of it, so a key-ordering nit has nothing to attach to and would get no reply. The closest, #pipeline 2025-04-24, is gideon and emil on whether batch job status tracking stayed accurate after the pbar change; it ends on there being no end-to-end lifecycle test. A plan_document appears nowhere in it. The sibling remark (remaining keys, their order, what the id derives from) also implies a thread where the full schema is being walked through, which no candidate is.

*Still leaves open:* what the remaining keys are, in what order, and what the id is derived from

*Must appear literally:* `plan_document`, `plan_format_version`

*A new conversation in #pipeline on 2025-04-29:*

```
11:14  gideon: so basically i drafted the thing we talked about last week, the submitter writes it out right before it submits so we have an artifact to diff against job state later. keys as of now: id, created_at, provider, model, request_count, request_files, metadata, plan_format_version. honestly though the naming is not final, tell me what looks wrong
11:19  dario: is request_files paths relative to the working dir or absolute? i think relative is the only thing that survives someone moving the cache dir, but you may have a reason
11:21  gideon: relative ya. absolute breaks the moment anyone copies a run dir around
11:34  emil: review nit on the plan_document — i'd put plan_format_version first and the id right after it. i want to know whether i can parse the rest before i read it, and right now the version is sitting at the bottom where i only find it after i've already guessed at everything above. not entirely sure it matters for the writer but it matters a lot for anything reading these later
11:41  dario: mhm. that tracks, an old reader hitting a new file should be able to bail early rather than half parse it. in any case is metadata a free-form dict or are we going to end up with a schema for that too, because i've seen how that goes
11:44  gideon: free form for now, i dunno, i kept it open on purpose because the provider side wants to stuff stuff in there. we can tighten later if it gets bad
```

#### `g1.r1.l6` — rule, observability

**nikolai**, 2025-05-13, #pipeline

> for the run dashbaord i read num_batches and num_requests right after the limits block i dont walk the per batch rows so keep those rows in as well

*Drafted as:* for the run dashboard i read num_batches and num_requests straight after the limits block instead of walking the per-batch rows, so keep those rows in as well.

*Why there:* Nothing in the listed rooms is chewing on the shape of a batch payload/manifest document. The design page (Mar 21, Emil) is about *where* state persists — responses file vs metadata db, `mode=ro` opens, CURATOR_CACHE_DIR — not about a serialized document with a version/id header, a limits block, whole-run totals and per-batch rows. The release notes and the three sync-notes pages are status surfaces; a schema-layout remark under any of them changes the subject and gets no reply. The handover page touches the viewer surface but from the response-contract angle (PR 643), not run-level totals. What actually should exist is the conversation where the batch payload layout gets nailed down: Emil owns the writer (metadata db / batch-mode), Nikolai owns progress-and-cli and is the one reading totals for the run dashboard, Dario's viewer is the other consumer. That thread is where "keep the per-batch rows even though I read the totals off the top" is a live constraint someone has to answer, and where a sibling can supply the version/id keys ahead of the limits block and the third total.

*Still leaves open:* the version and id keys ahead of the limits block, and what the third total is

*Must appear literally:* `num_batches`

*A new conversation in #pipeline on 2025-05-13:*

```
10:42  emil: ok so batch mode writes a payload doc next to the metadata db and i have a draft layout for it - top level config block, then the limits block (token + request ceilings), then one row per batch with the provider batch id, state, counts, timestamps. before i freeze the key names i'd like to hear from the two consumers, the CLI progress bar and the viewer. what are you actually reading out of it
10:51  nikolai: for the run dashbaord i read num_batches and num_requests straight after the limits block rather than walking the per batch rows so keep those rows in as well
10:58  emil: yup that sounds right, i had them in the draft but i was honestly half tempted to drop them since they're derivable. Let me think through that - if you're not walking the rows then deriving them costs you the whole parse, which defeats the point
11:06  dario: the viewer walks the rows either way so i don't have a strong opinion, though i think keeping them is cheap. one thing i do care about is whether the per batch state is the provider's raw string or something we normalise - are you passing it through or mapping it to our own enum
11:14  emil: not entirely sure yet. raw string is less work now but i believe we'll regret it the first time a provider renames a state on us. we need to be intentional here, ill open a seperate thread for it
```

#### `g1.r1.l7` — rule

**dermot**, 2025-04-02, #code-review

> the num_bytes next to those counts should just be the sizes create_batch_file hands back, summed — i checked the current figure against du on the dir and they don't agree.

*Drafted as:* the num_bytes sitting with those counts should be what create_batch_file handed back, summed. i compared it against du on the dir and they disagree.

*Why there:* None of the four mails is chewing on a batch payload manifest at all. The OOM/concurrency thread is about semaphores and row creation for a verify run; the two weekly updates are PR-status roundups where a field-level correction to a spec would be a subject change nobody answers; and the v0.1.21 release note is dermot announcing two shipped fixes to a wide list, not reviewing a document. The remark is a reviewer picking up one line of a spec that lists per-batch counts, num_bytes, a key order, and which runs emit the file — it only reads as always-there if the spec is in front of both people. What should have existed: a #code-review thread the day the batch payload plan draft went up, dermot and the doc's author (emil, with gideon weighing in), walking the field list top to bottom — the other totals and key ordering, whether resumed runs re-emit the file, and dermot's du check on the byte figure.

*Still leaves open:* the other totals, the key order, and which runs produce the file

*A new conversation in #code-review on 2025-04-02:*

```
10:12  emil: put the batch payload plan draft up on the wiki, its ahead of the submission path so theres nothing to actually run it against yet. mainly want eyes on the field list before i go further with it
10:18  gideon: what is the counts section covering exactly? like per request or per file. the doc has n_requests and then a total sitting right under it and I couldnt tell if those are the same thing counted twice
10:27  dermot: the num_bytes sitting next to those counts should just be what create_batch_file handed back, summed. i checked it against du on the dir and they dont agree
10:34  emil: hm, let me think through that. i beleive du is picking up the manifest and whatever else we leave in there, so its not measuring the same set of files
10:36  gideon: ya plus block padding, so basically those two numbers are never going to line up no matter what we do
10:41  dermot: mhm. that said i'd still rather the doc say where the number came from, right now it just says bytes
```

#### `g1.r1.l8` — rule, failure_behavior

**gideon**, 2025-04-16, #code-review

> so basically the limits block in the doc came out with three keys once max_batches_per_plan landed, and my snapshot only pinned the two byte/request ones, so it's red.

*Drafted as:* Heads up, the limits block in the doc came out with three keys once the cap field landed and my snapshot test pinned two.

*Why there:* None of the eight rooms has the batch payload plan document, the limits dataclass, or a doc snapshot test in flight. The batch-adjacent threads are about gemini response parsing (04-01), the CLI batch update frequency in PR 632 (04-14, 04-23), and whether anyone has walked the batch submission path (04-09) — none of them is chewing on a serialised limits block, a per-plan cap landing, or a fixture going red, and no cap field has ever been mentioned. Dropped into any of them the remark introduces three new objects at once and would draw no reply. The sibling remark that supplies the field's name, default and place in the document also needs a counterpart in the room, which only exists if the thread is about the payload plan doc to begin with.

*Still leaves open:* what the cap field is called, what it defaults to, and where the block sits in the document

*Must appear literally:* `max_batches_per_plan`

*A new conversation in #code-review on 2025-04-16:*

```
10:12  dermot: the doc fixture for the batch payload plan is red on main since the per-plan cap merged. is that expected fallout or did something regress
10:16  gideon: ya that's mine. so basically the limits block in the doc came out with three keys once max_batches_per_plan landed, and my snapshot only had the two byte/request ones pinned, so it's red
10:16  gideon: honestly though i'm not sure if the fixture is wrong or the assumption is, tbh
10:24  emil: so you're asking whether the block is supposed to track the dataclass as it grows, or stay at the pair you wrote down. let me think through that, i believe the serialiser just dumps the whole thing
10:31  dermot: if i had to guess it's the fixture, but that's a whole other thread. can you just re-pin it for now so main goes green, we can argue the shape after PR 632 is in
10:33  gideon: ok ya, re-pinning. will put it on the pile
```

#### `g1.r1.l9` — rule, observability

**dario**, 2025-06-19, #engineering

> i think plan_fingerprint should hash just the batches joined, 0-2:307;2-4:307 - spans and bytes, not index, not num_requests. utf-8 encode, sha256, keep the front of the hexdigest.

*Drafted as:* plan_fingerprint should join the batches as 0-2:307;2-4:307, spans and bytes only. index and num_requests must not move it.

*Why there:* None of the eight pages is chewing on batch payload planning at the byte level. The batch-adjacent ones are about something else: WS-050 is a closed workstream on Gemini batch bugs and a cost offset, the persistence design page is about which store a restart reads and CURATOR_CACHE_DIR portability, and the June syncs are PR/issue roll-ups (690, 691, 233, 207) with no implementation detail at this grain. Nowhere in the listed rooms has anyone mentioned a plan, a span, a byte budget, or a fingerprint, so a message naming the exact canonical string would be the only line of its kind on the page and would draw no reply. Where it belongs is the thread where the batch payload planner was actually being reviewed: emil owns batch mode and auto batch mode is landing in v0.1.26, and the open question is what a resumed run compares against when it recomputes the plan — dario had already worked through the resume path for WS-050 (every death is while waiting on the provider, never inside submit), so he is the one who cares that the identifier covers spans and bytes and not the bookkeeping fields. That thread would also cover whether a plan whose fingerprint differs on resume aborts or re-submits, and where the fingerprint gets written next to the batch job records in the metadata db.

*Still leaves open:* what is done to that string and how much of the result is kept

*Must appear literally:* `0-2:307;2-4:307`, `index`, `num_requests`, `plan_fingerprint`, `sha256`

*A new conversation in #engineering on 2025-06-19:*

```
10:42  emil: quick one on the planner in 691 — for the stable id on a recomputed plan, what actually goes into the hash? my assumption was the whole batch object serialized, but that pulls in the per batch index and the request counts and i'm not entirely sure those should be in there
10:43  emil: like if a resume splits the same rows the same way but the counts get recomputed slightly differently, do we want that to be a different plan or the same plan
10:51  dario: so plan_fingerprint hashes just the batches joined, 0-2:307;2-4:307 — spans and bytes, not index or num_requests. utf-8 encode, sha256, keep the front of the hexdigest. the reasoning being that the index is positional and derivable and the counts are honestly just a view on the same spans, so putting them in only gives you spurious mismatches
10:58  nikolai: yeah thats fine i mean the spans are the plan everything else is bookkeeping
11:04  emil: sounds right. so to restate — if i resume and the recomputed one differs at all in where the boundaries fall we bail out rather than trying to reconcile? i believe that's what we want for 0.1.26 at least, we can be smarter later
11:09  nikolai: bail out is solid enough for now, reconciling half submitted batches is a whole other thing
```

#### `g1.r1.l10` — observability

**nikolai**, 2025-04-08, #engineering

> first cut on request_id - sha256 hexdigest is 64 chars and the full thing just wraps the log line so twelve off the front is plenty for eyballing two runs against each other

*Drafted as:* twelve hex characters off the front of the sha256 is plenty for comparing two runs by eye, the full digest just wraps the log line.

*Why there:* That thread ends with Emil pushing back that "the fields aren't the work, figuring out what goes in them is" and asking Nikolai to spec what timestamp and request_id should actually contain, with Nikolai agreeing to write it up. A first concrete detail on the request_id format — how long the id is and why — lands directly on that ask, from the person who owns the spec, and it deliberately leaves open what gets hashed, which is the rest of the spec Emil was asking for.

*Still leaves open:* what string is being hashed in the first place

*Must appear literally:* `sha256`

*Goes into the real conversation in #engineering on 2025-04-08, after 18:15 nikolai:*

```
09:00  nikolai: failed_requests.jsonl is wired up on my end
09:00  nikolai: Not totally sure the current field layout is what anyone downstream actually needs for debugging batch failures though
09:03  dermot: @Nikolai what fields does it have right now?
09:13  nikolai: Each line looks roughly like this:

```json
{"row_idx": 14, "error": "RateLimitError", "provider": "openai", "model": "gpt-4o", "attempt": 2}
```
10:21  dermot: no request id or timestamp?
10:30  dermot: are the deepseek, llama4, and openai additions all targeting the same release?
10:58  nikolai: fair, good catch
11:33  emil: Are we adding timestamp and request_id before this ships, or punting that to a follow-up?
11:50  dario: Separate from the jsonl fields question, I think we need to confirm the DeepSeek and OpenAI integrations aren't touching anything that would step on t
12:05  emil: WS-055 isn't in the tracker - went looking and found nothing there
12:05  emil: Has Dermot filed it somewhere else, or is it still outstanding?
12:39  dermot: ws-055 is on the wiki, not the tracker. I just pulled it up - still mostly design notes, no owner on the stub provider or e2e credentials, and the rel
12:41  emil: Sounds like it's mostly a placeholder
12:41  emil: Is the CI pipeline piece part of what's still undecided?
12:51  nikolai: Punting timestamp and request_id to a follow-up
12:51  nikolai: @Emil, can you keep that on the list so it doesn't get lost?
13:42  dario: Did anyone actually check the DeepSeek integration against the rate-limit layer specifically, or is that still open from this morning?
14:08  emil: Got it, I'll track the follow-up
14:08  emil: Is the current schema enough to trace a batch failure without the timestamp, or are we going to hit a wall on debugging until that lands?
14:38  dermot: are we planning to stage the three provider additions or ship them all at once?
14:46  dario: - Rate-limit path check for DeepSeek and OpenAI still open on my end, not fully closed out yet
- The absent headers Emil flagged are the main thing I'
14:47  dario: I'd be a bit cautious about shipping all three at once with the DeepSeek header issue still not sorted
15:11  dermot: so do we hold deepseek and ship the other two, or block all three?
15:21  dario: Syncing with Emil this afternoon on whether the retry layer handles the absent DeepSeek headers cleanly, that check isn't done yet.
16:07  dermot: that's going to land before end of day?
16:42  emil: Pulled up WS-055 - the release process section is all TBD and the stub provider and e2e credentials have no owner
17:07  dario: Just getting into the sync with Emil now, should have a read on the DeepSeek/rate-limit question before we wrap today
17:25  dermot: pr 614 is ready for review on my end
17:52  nikolai: Without timestamp and request_id, the current schema is going to be pretty useles for tracing which requests failed and when in any real batch.
18:05  nikolai: I think I was too quick to punt timestamp and request_id, the schema's not really useful without them
18:06  emil: Good to walk it back, but adding them tonight feels rushed.
18:13  nikolai: They're two fields, that's not really a night's work.
18:14  emil: The fields aren't the work, figuring out what goes in them is.
18:14  emil: @Nikolai, can you put together a quick spec on what timestamp and request_id should actually contain before those go in?
18:15  nikolai: Yeah, I'll put something together  <-- the remark goes here
18:27  dario: Honestly I'm not comfortable calling the DeepSeek integration clean yet with the header issue still untraced, so do we hold it or are we accepting the
18:28  dario: Actually, answering my own question, I'd lean toward holding DeepSeek and shipping OpenAI and llama4 separately until the header issue is traced
```

#### `g1.r1.l11` — observability

**emil**, 2025-05-13, #code-review

> honestly the empty plan case looks fine as-is to me - zero batches join to nothing, and plan_fingerprint([]) still handed back e3b0c44298fc, i don't think we need to special-case it

*Drafted as:* empty plan hashed the empty string and came back e3b0c44298fc, which is fine by me, no special case needed there.

*Why there:* Nothing in the listed rooms is chewing on batch payload plans, plan hashing, or resume identity. The March/April pipeline threads are about Mistral batch clients, token-usage shape and an ordering sweep; #engineering is on semaphores and cost-streaming skew; #cookbooks is examples tables and CI wiring; #viewer is None-cost rendering; #incidents is the post1 announce. A remark about `plan_fingerprint([])` returning `e3b0c44298fc` would land in any of them as a subject change with nobody to answer it, and emil's role in each is asking for verification, not reporting a hash he already ran. What's missing is the review thread where the batch payload planner's fingerprint is actually being read line by line — the empty-plan guard question only comes up when someone is looking at the function and its callers, and a sibling remark there covers how a non-empty plan is serialized and what the id field is called in the file.

*Still leaves open:* how a non-empty plan is turned into a string, and what the id is called in the file

*Must appear literally:* `e3b0c44298fc`, `plan_fingerprint([])`

*A new conversation in #code-review on 2025-05-13:*

```
10:14  gideon: Put the batch payload planner up for review, it's small but the fingerprint part I want someone to look at properly. So basically caching-and-resume keys off that hash, so what happens when a plan comes back with zero batches in it, does that need an explicit guard or no
10:21  dario: before the empty case, i think i need the normal path first, is a non-empty plan serialized as the raw batch dicts or is there some canonical form it goes through befor hashing? and what's the id field actually called on the plan object, plan_id or something else
10:29  emil: let me think through that - honestly the empty plan case looks fine to me as is, zero batches join to nothing and plan_fingerprint([]) still handed back e3b0c44298fc when i ran it, no need to special-case it
10:35  dario: mhm, that tracks. still not entirely clear to me on the serialization though, if it's the raw dicts then key ordering is going to bite us at some point on the resume side
10:37  gideon: ya the ordering thing is fair. tbh I never checked what dict order looks like coming out of the planner, will look after standup
```

#### `g1.r1.l12` — rule

**konrad**, 2025-04-09, #pipeline

> Right, I renamed the colum in my run notes to plan_id then, I had it down as plan_hash. It's whatever plan_fingerprint hands back - twelve hex chars, f4b1ea1573c0.

*Drafted as:* Renamed the column in my run notes to plan_id to match what the sidecar calls it, I had it down as plan_hash.

*Why there:* None of the eight rooms is chewing on a plan document's schema. They're on release contents (2025-03-19), the gemini `parts` key and stale cookbook examples (2025-04-01), 0.1.24 plus PRs 652/654 (2025-05-05), factory cleanup scope (2025-05-22), the null-value fix in PR 675 (2025-05-27), the viewer download path (2025-06-02), a doc version tag (2025-07-10), and PR triage (2026-01-02). A field-name correction about plan_id/plan_hash and a twelve-hex-char plan_fingerprint value would land in every one of them as a subject change with nobody positioned to answer it — and the sibling remark that explains how the fingerprint is computed has no speaker in any of those threads either. What should have existed: a #pipeline thread while the batch payload plan doc was being written up, where Emil states the id field name and how plan_fingerprint derives it, Konrad reconciles it against the column name in his run notes, and Dario asks whether the fingerprint is stable across reruns of the same payload.

*Still leaves open:* how that value is computed and from which fields

*Must appear literally:* `f4b1ea1573c0`, `plan_fingerprint`, `plan_hash`, `plan_id`

*A new conversation in #pipeline on 2025-04-09:*

```
10:412  emil: placeholder
```

#### `g1.r1.l13` — scope

**dario**, 2025-03-24, #pipeline

> honestly the other half of this - i had a run die partway through writing requests_*.jsonl and nothing on disk said what it had been aiming for. batch_plan.json wants to land before the first requests file, metadata too

*Drafted as:* a run died partway through writing requests_*.jsonl and i had nothing saying what it had been aiming for. that wants to be on disk before the first file.

*Why there:* That thread is already stuck on exactly this: emil confirmed the job id is only held in memory, dermot proposed the metadata db, emil objected that it can be disabled, and by 18:28 emil is worrying that "a flat file or something outside the metadata db gets complicated fast if we want it to be per-run". Dario had taken the action item at 14:35 to sketch the on-disk shape and had already told his own lost-batch story at 17:03, so a second symptom — a run dying mid-write with nothing on disk saying what it was aiming for — plus a concrete ordering constraint against the per-run requests files is his to add, and it complicates emil's "flat file gets complicated" without settling what the file holds or which runs write it.

*Still leaves open:* what that record contains, what it is called, and which runs produce it

*Must appear literally:* `batch_plan.json`, `requests_*.jsonl`

*Goes into the real conversation in #pipeline on 2025-03-24, after 18:28 emil:*

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
14:35  dario: Those are good questions, I'll sketch it out and bring something back to the group
16:01  emil: In the meantime I cancelled the duplicate batch manually on the provider side
16:23  dermot: the metadata db might be a natural home for that id
17:03  dario: Lost a 12hr anthropic batch yesterday when my ssh session died and took the python process with it
17:04  dario: The id only ever existed inside that process
17:04  dario: Spent this morning reading batch ids off the provider console and pasting one into a scratch script to pull the results down - that's fine for me once
17:13  dermot: I'm not entirely sure the metadata db is the right home for this either
17:32  emil: If the job id lives in the metadata db and someone disables it (which PR 583 explicitly allows), they've lost resume on restart with no warning.
18:17  dermot: so the metadata db can't be the only place it lives if we're allowing it to be disabled
18:28  emil: Right, and a flat file or something outside the metadata db gets complicated fast if we want it to be per-run and not just a single-slot thing.  <-- the remark goes here
```

> **Problems:** longer than one remark

#### `g1.r1.l14` — scope, observability

**gideon**, 2025-03-14, #code-review

> auto path on an empty dataset left me a bare dir. honestly though I'd want batch_plan.json anyway — num_batches 0, num_requests 0, num_bytes 0, batches [], plan_id filled in like any other run.

*Drafted as:* Empty dataset on the auto path left me a bare dir. I'd still want a batch_plan.json out of it, num_batches 0, so I can see it ran at all.

*Why there:* None of the listed rooms is chewing on a batch planning artifact at all. The pipeline days are on Mistral usage extraction (3/26), cancel_batches and failed-request jsonl visibility (4/02), Anthropic token accounting and PR 632's update-freq (4/22, 5/02); #engineering is on the v0.1.21 throttle audit (3/19) and cost streaming/PR 638 (4/15); #viewer is on PR 624 log noise; #code-review is on schema_check at construction. A remark asserting what `batch_plan.json` must contain on an empty dataset would answer nothing anyone had asked in those rooms and would draw no reply — and the sibling remark it depends on (the rest of the document, which other paths write it) implies a thread where the plan file's contract is actually the subject. That thread should have been in #pipeline, prompted by Gideon running the auto path while shaking out the batch payload planner and getting a bare output dir with no plan file, alongside the explicit/split paths that do write one, plus who owns the empty-dataset case and whether downstream resume can rely on the file always existing.

*Still leaves open:* what the rest of the document holds and which other paths write it

*Must appear literally:* `batch_plan.json`, `batches`, `num_batches`, `num_bytes`, `num_requests`, `plan_id`

*A new conversation in #code-review on 2025-03-14:*

```
10:24  dermot: while i was in the batch upload refactor i noticed the payload planner doesn't leave the same thing on disk depending on which path you come in through. explicit size vs auto. if i had to guess it's just that nobody wrote down what the artifact is supposed to be
10:29  gideon: ya i ran into exactly this yesterday, was shaking it out over a few datasets. the auto path on an empty dataset left me a bare dir. explicit size gives me a file with num_requests 0 and that's fine. honestly though i'd still want batch_plan.json — num_batches 0, num_bytes 0, batches [], plan_id filled in like any other run
10:41  emil: let me think through that. the downstream reader doesn't really have a way to tell "nothing to do" apart from "the planner never got there" if one path just... doesn't write. not entirely sure which of the two is the odd one out though
10:47  dermot: mhm. that said i'd want to know whether the auto path is even reaching the writer or whether it returns early before it has anything to write. different fix
10:52  gideon: returns early i think, um, at least that's what it looked like when i was stepping through it. i dunno if that's deliberate. can pull the trace later, am on the request processing cleanup this morning
```

> **Problems:** longer than one remark

#### `g1.r1.l15` — scope

**konrad**, 2025-03-14, #engineering

> Look, if I pass batch_size=2, or I give no dataset at all, then I picked the split myself. no batch_plan.json should be turing up in my working dir for those.

*Drafted as:* If I pass batch_size=2, or no dataset at all, I picked the split myself. Nothing new should be turning up in my working dir for those.

*Why there:* None of the eight rooms is chewing on batch splitting at all. The closest, #code-review 2025-04-02, is about the cancellation fix (PR 614) and the pending job ID being parked in the run dir keyed off the dataset — an artifact-in-the-run-dir topic, but a different artifact and a different bug; dropping batch_plan.json and batch_size=2 into that thread introduces a feature nobody has mentioned and would get no reaction. #engineering 2025-03-19 is batch-adjacent but entirely about the token-count fix, throttling and the postmortem action items. The May/June/July threads are finetuning, PR triage and dormancy. The remark presumes a live argument about which call paths write a plan record, and that argument never happens anywhere in the corpus, so it needs the thread where the auto-split PR is being reviewed — with the sibling remark from Emil or Dermot supplying what does get written when the caller didn't choose the split.

*Still leaves open:* what does turn up on the path where the split was not picked by the caller

*Must appear literally:* `batch_plan.json`, `batch_size=2`

*A new conversation in #engineering on 2025-03-14:*

```
10:42  emil: reading through the auto batch size PR now. one thing i want to make sure of before i approve - the plan record gets written on every path, or only when we actually did the selecting?
10:47  konrad: this is what i wanted to raise actually
10:48  konrad: Look, if I pass batch_size=2, or no dataset at all, then I picked the split myself. No batch_plan.json should be turing up in my working dir for those.
10:55  dermot: so your read is the write belongs in the auto branch only, not in whatever wrapper calls into it. if i had to guess it's sitting a level too high right now
11:03  emil: let me think through that. the wrapper is also where the dataset gets resolved so there may be a reason it ended up there, not entirely sure it was deliberate though
11:09  dermot: worth checking against the row-count path too while you're in there, that one goes through the same helper last i looked
```

#### `g1.r1.l16` — failure_behavior, observability

**konrad**, 2025-03-17, #engineering

> Look, auto sizing with a tigth byte cap gave me 31k request files in one dir. If we refuse that, err.limit alone is useless, I need the count it wanted.

*Drafted as:* Auto sizing with a tight byte cap gave me 31k request files in one dir. If we start refusing that, tell me how many it needed, not just the ceiling.

*Why there:* None of the listed rooms is chewing on batch payload plan sizing. The closest, #code-review 2025-03-21, is about PR 584's merge-or-defer call, retry scope, and cache/metadata db paths — nobody there has raised auto sizing, byte caps, file counts per directory, or an error carrying an `err.limit` field, so a concrete field report about 31k request files would change the subject and draw no reply. The other candidates are release-notes coordination (#releases 05-06, 05-30), viewer null-cost handling (#viewer 06-03), milestone status (#engineering 03-31), PR triage during wind-down (#code-review 07-10), and GEPA null scores (#code-review 2026-01-27). What this remark needs is the thread where the planner's refusal behaviour is being designed — where a sibling remark names the ceiling and names the failure — and that conversation doesn't exist yet. Konrad running the auto sizer with a tight byte cap and landing 31k files in one directory is exactly what prompts it.

*Still leaves open:* what the ceiling is, what it is called, and what the failure is named

*Must appear literally:* `err.limit`

*A new conversation in #engineering on 2025-03-17:*

```
10:41  dario: while the provider work is parked i was poking at the batch payload planner — is the number of request files bounded anywhere, or is it purely whatever falls out of the byte cap you hand it
10:46  konrad: purely the cap as far as i can tell, nothing checks the resulting count
10:47  konrad: Auto sizing with a tigth byte cap gave me 31k request files in one dir. If we refuse that, err.limit on its own is useless — i need the count it wanted.
10:55  dario: mhm, that tracks. knowing the ceiling doesnt tell you if you're at 31k or 310, which is the part that decides whether you retune the cap or give up on auto sizing entirely
11:02  konrad: right. presumably the token cap path has the same shape but i have not looked at it properly, off the top of my head
11:09  dario: in any case i'm still on the capability table thing this afternoon, so if you write any of this up i'll read it tonight
```

#### `g1.r1.l17` — failure_behavior, rule

**nikolai**, 2025-03-18, #engineering

> i'd say the cap goes on the limits dataclass as max_batches_per_plan default 512 checked once the plan is finished and a plan landing on exactly 512 is still fine

*Drafted as:* the cap lives on the limits dataclass as max_batches_per_plan, default 512, and a plan landing on exactly 512 is still admissible.

*Why there:* Nothing in the listed rooms is chewing on batch payload planning internals. The batch-mode syncs (Jun 11, Jun 23) are status-and-deferral notes about rate-limit issues 207/233 and whether auto batch mode ships in v0.1.26 — no one there is placing fields or picking defaults. The Jun 16 sync is a PR/issue roll-up. The docker pinning doc is nikolai's own but is about image tags and backend_params, and the handover is cost/cache/viewer. A concrete "put it on the limits dataclass, default 512, inclusive" ruling dropped into any of those changes the subject and gets no reply. What should have existed: a #pipeline thread the day after the Jun 16 sync, prompted by Emil building out PR 691 (auto batch mode) and hitting the question of how many batches a single payload plan may emit — where the cap lives, what the default is, what the boundary does, and (the sibling remark) what happens and what the error is called when a plan runs past it.

*Still leaves open:* what happens when the plan goes past it, and what that failure is called

*Must appear literally:* `max_batches_per_plan`

*A new conversation in #engineering on 2025-03-18:*

```
10:14  emil: working through auto batch mode on PR 691 and i hit a question i dont have a good answer for. we need to be intentional here — theres nothing stopping a plan from exploding into thousands of batches right now. so where does the ceiling live, and what number do we pick? my guess is its a config thing but honestly not entirely sure
10:21  nikolai: i'd say the cap goes on the limits dataclass as max_batches_per_plan default 512 checked once the plan is finished and a plan landing on exactly 512 is still fine
10:26  emil: sounds right. checking after the fact is simpler than trying to bail mid-split anyway, we'd have to unwind half a plan otherwise
10:33  dario: is 512 something we landed on from actual payload sizes, or is it just a round number that felt safe? i think either is fine to be honest, just want to know which one it is before the v0.1.26 cut
10:39  nikolai: off the top of my head its the second one, i mean nobody's gotten near it in the runs i've seen
10:44  dario: mhm, that tracks. in any case i'd rather have the number written down somewhere than not, we can move it later if someone actually hits it
```

#### `g1.r1.l18` — failure_behavior

**dario**, 2025-04-24, #code-review

> same family of thing honestly — my except for payload-too-large caught a BatchPlanTooFragmentedError this morning, the outer except ValueError should have had it, those aren't the same failure

*Drafted as:* my except for payload-too-large swallowed BatchPlanTooFragmentedError this morning. those are not the same failure and i want to catch them apart.

*Why there:* That thread is already deep in error-path hygiene — dermot opened the day tidying "the last few error paths" in bulk-llm-inference, and the evening turns into emil and dermot picking apart an except body that swallows a cache-write failure silently. Dario is present and already responding ("+1" at 18:26), so a second concrete example of an except clause catching the wrong thing lands as him piling on rather than changing the subject. It complicates the discussion the right way: the others are excepts that say nothing, this one is an except that catches a failure it was never meant to own, which is what makes the fragmentation error's own type the point. It leaves open when that error gets raised and what it carries.

*Still leaves open:* when that error is raised and what it carries

*Must appear literally:* `BatchPlanTooFragmentedError`, `ValueError`

*Goes into the real conversation in #code-review on 2025-04-24, after 18:26 dario:*

```
09:00  dermot: bulk-llm-inference cleanup is mostly done, just tidying up the last few error paths before I put it up for review this afternoon.
09:36  gideon: Dario's got a first pass up for review, reads batch_objects.jsonl on startup and reattaches by id, touches caching-and-resume
09:36  gideon: Not blocking a release but has a few things worth looking at before it goes in
16:49  dermot: not entirely sure, but I think if the cache write fails it just swallows it silently
17:26  gideon: does it log the path anywhere when it swallows it, or is the failure completely invisible?
17:28  dermot: from what I can tell, completely invisible, no path anywhere.
17:59  emil: ugh, that's the exact thing
18:23  emil: That bare `pass` in the cache-write except needs to go, at minimum it should log a warning with the path.
18:24  emil: adjacent gripe, the one place we do already wrap a cache write in try/except, the except body is a bare pass
18:24  emil: burned an hour last week wondering why a rerun redid everything from scratch, turned out the write had failed on a permissions thing on a mounted dir 
18:26  dario: +1  <-- the remark goes here
```

#### `g1.r1.l19` — failure_behavior

**nils**, 2025-03-19, #engineering

> let me think - i sent 600 tiny rows plus one 5MB row and got the fragmentation error back, when what i wanted was SingleRequestTooLargeError with row_idx 600 named in it.

*Drafted as:* 600 tiny rows plus one 5MB row and it came back fragmented. the row index is the thing i actually needed named there.

*Why there:* None of the listed rooms is chewing on batch payload size limits or error precedence. The batch-mode page that exists (batch job status persistence) is about which store a restart reads and CURATOR_CACHE_DIR portability — a repro about oversized rows and error classes would change the subject there and get no reaction. WS-055 and the weekly notes are release/CI/PR-triage surfaces; the docker pinning and structured-output pages are unrelated subsystems. The remark is also empirical (someone just ran a submission and read the traceback), which reads as chat, not as a comment on a two-month-old design doc. What should have existed: a #pipeline thread while nils is working through batch request file splitting, where he posts the repro and emil — who owns batch-mode — supplies the other half, i.e. what the fragmentation limit actually is and what the count on that error refers to. The thread would also cover where the size check sits relative to the splitter and whether the per-row limit is provider-specific.

*Still leaves open:* what the fragmentation limit is and what the count on that error means

*Must appear literally:* `600`, `SingleRequestTooLargeError`, `row_idx`

*A new conversation in #engineering on 2025-03-19:*

```
10:42  emil: quick one on the payload splitting - when a submission blows the size limit, are we raising per-row or per-batch? i believe it's supposed to be per row but the tests i'm reading dont say that clearly
10:47  nils: let me think - i sent 600 tiny rows plus one 5MB row and got the fragmentation error back. i wanted SingleRequestTooLargeError with row_idx 600 named there.   <-- the remark
10:51  emil: hm. so the splitter is deciding it cant fragment before anything looks at the individual row. not entirely sure which check is meant to run first honestly
10:54  nils: that's my question too - is the size check meant to sit in the splitter, or upstream of it in validation? either way the message the user gets right now is misleading
11:02  emil: upstream i'd guess, but i'd want to look at where the limit constant is actually read before saying that. it's on the batch-mode branch somewhere
```

#### `g1.r1.h1` — herring

**dario**, 2025-01-21, #releases

> settled then, the span lives in metadata_{i}.json right next to num_jobs, so each file carries its own start_idx, end_idx and num_bytes. no separate plan file, in any case

*Drafted as:* settled: the span lands in metadata_{i}.json alongside num_jobs, so each file carries start_idx, end_idx and num_bytes. no separate plan file.

*Why there:* None of the eight rooms is chewing on how batch payload shards record their spans. The closest topically is #pipeline 2025-02-21, but that day is about whether the batch e2e asserts reuse counts and whether to hold PR 532 over the resume-offset question — a "settled then" about a metadata schema would land in that thread with no prior discussion to settle and no one to answer, and it would read as changing the subject at the exact moment the room is stuck on a deferral. The rest (release notes, PR triage, per-row generation_params, Mistral usage fields) are further away still. What's missing is the thread where the request-file splitting layout actually got argued: does the shard plan live in a sidecar file listing every span, or does each metadata_{i}.json carry its own. That naturally follows the async batch file path work from PR 532 and sits with emil (batch mode) and gideon (reassembled output / resume), with dario making the call at the end.

*A new conversation in #releases on 2025-01-21:*

```
10:42  gideon: picking 532 back up now that the hold is off. one thing though - once the async path splits a request set across several payload files, what actually records which rows landed in which file? i don't see anything
10:48  emil: let me think through that. so you're saying resume can't tell where it left off because the shard boundaries aren't written down anywhere, and reassembly has the same problem in reverse? that sounds right to me, we'd need a span per shard either way
10:55  dario: settled then: the span goes in metadata_{i}.json right next to num_jobs, so each file carreis its own start_idx, end_idx and num_bytes. no separate plan file
10:57  gideon: ya ok that works for me. so basically nothing new to read on startup, we just glob whats already there
11:06  emil: yup. i'm not entirely sure what that does to the partial-write case honestly, if a file gets truncated mid flush the counts lie to you. but that's probably its own thread
11:11  dario: mhm, seperate problem i think. in any case i'd rather not hold 532 on it - can you drop it on the PR or do you want me to open something
```

#### `g1.r1.h2` — herring

**konrad**, 2025-01-27, #engineering

> look, from my review pass the auto batches carry {num_jobs, start_idx, end_idx, num_bytes} in each metadata_{i}.json, so the plan lives in the per batch metadata not a seperate file

*Drafted as:* Reminder from review: metadata for auto batches is {"num_jobs", "start_idx", "end_idx", "num_bytes"}. The per-batch metadata is where the plan lives.

*Why there:* On 2025-01-27 Konrad is alone in the weeds on PR 403's batch path, asking in a burst whether generation params ride on each batch item or get set once at the job level, and whether batch cost calc is per-backend. A finding from his read of the batch code about what each metadata_{i}.json actually records lands directly in that thread — it partly answers his own structural question (Konrad routinely half-answers himself) and sets up Dario's 16:38 point that params are going out fine but aren't making it into the batch entries. The other rooms are about PR ownership, uid wording, or review bar, and this would arrive from nowhere there.

*Goes into the real conversation in #engineering on 2025-01-27, after 09:13 konrad:*

```
09:00  konrad: Weekly update for the week of Jan 20 just went out to the team
09:00  konrad: v0.1.16 shipped, but PR 403 is still stuck, params aren't routing through the Gemini batch path and cost calc doesn't cover all batch backends yet
09:13  konrad: @Emil for PR 403, are the generation params supposed to pass through as part of the request body on each batch item, or do they get set once at the jo  <-- the remark goes here
10:21  konrad: Does anyone know if the cost calc for batch is supposed to handle all backends with a single formula, or is each backend expected to provide its own c
11:13  konrad: @Emil did anyone validate PR 406 after it merged, or did it go in without a post-merge check?
16:38  dario: Params are going out from provider-integrations fine, they're just not making it into the batch entries in PR 403.
18:28  emil: gotcha
18:28  dario: Read the weekly, it flags the param routing as needing eyes from my side but doesn't go further on cost calc scope
18:28  dario: Is each batch backend expected to provide its own cost estimate, or is there supposed to be one shared formula?
```

#### `g1.r1.fix21` — failure_behavior

**emil**, 2025-03-14, #releases

> honestly, went to put the fragmentation count in our alert line and there's no num_batches on the error anywhere, just the ceiling - had to re-derive it from len(plan)

*Drafted as:* Went to put the fragmentation count in our alert line and there's no num_batches anywhere on the error, just the ceiling. had to re-derive it from len(plan).

*Why there:* Nothing in the listed rooms is chewing on batch-plan fragmentation or the ceiling error. The two #pipeline days are about sweep order/WS-050 (04-01) and job-reuse mismatch keys (04-21); the three #releases days and #general are notes/dormancy logistics; #viewer is PR 624 log lines; #code-review 2026-01-02 is PR triage with no code detail at all. Dropping a `plan_batches` error-attribute complaint into any of them changes the subject and would draw no reply — and the sibling remark (ceiling attribute name, its value, where the check runs in plan_batches) needs a room where someone is actually walking through that function, which none of these are. What's missing is the day a run tripped the max-batches ceiling and the error text turned out to say nothing about how big the plan was: Emil hitting it from the alerting side, Dario or Dermot explaining the check itself, and the two of them settling that the needed count gets carried on the error as num_batches.

*Still leaves open:* what the ceiling attribute is called, what value it holds, and when in plan_batches the check runs

*Must appear literally:* `num_batches`, `len(plan)`

*A new conversation in #releases on 2025-03-14:*

```
09:12  dermot: overnight run died in plan_batches against the max batches ceiling. the alert text tells you the limit and nothing else, so i had no idea if we were two over or two hundred
09:14  gideon: ya i saw that this morning. had to open the job log to even guess tbh
09:21  emil: honestly, went to put the fragmentation count in our alert line and there's no num_batches on the error anywhere, just the ceiling - had to re-derive it from len(plan). not entirely sure why it was left off   <-- the remark
09:24  dario: that tracks. i think the ceiling check predates the planner returning anything useful, so whoever raised it only had the limit in scope
09:26  dermot: mhm. either way the run needs rescheduling before the 0.1.21 cut, i'll kick it with the shard size halved
09:28  gideon: so basically we find out at 3am again if halving is enough, cool
```

#### `g1.r1.fix22` — rule

**nils**, 2025-03-14, #general

> ran the auto path over an empty input this morning and plan_fingerprint still handed me back a plan_id, same one i get hashing an empty string in a repl.

*Drafted as:* ran the auto path over an empty input this morning and plan_fingerprint still handed me a plan_id back, same one i get hashing an empty string in a repl.

*Why there:* Neither listed room is chewing on plan identity or hashing. #pipeline 2025-03-17 is entirely the Mistral batch client and whether the token-usage dict shape matches what cost accounting expects — the day ends with PR 584 blocked on that one question plus missing wiki pages. #code-review 2025-03-25 is release triage: which of 584/585/579 land, deferring 468 and 565, and the nonexistent WS-047 scope. A probe result about plan_fingerprint returning a plan_id for empty input answers nothing live in either and would draw no reaction; in the code-review thread it is also out of character for that day, where Nils is asking for review rather than reporting findings. The conversation that should have existed: mid-week in #pipeline, prompted by review of the batch payload plan builder, where someone asks whether plan_id is deterministic across runs for the same plan — Nils reports the empty-input edge, and a sibling message pins down the digest, its width, and the canonical string for a non-empty plan.

*Still leaves open:* what the digest actually is, how wide the value is, and what the canonical string looks like for a non-empty plan

*Must appear literally:* `plan_fingerprint`, `plan_id`

*A new conversation in #general on 2025-03-14:*

```
10:42  emil: so on the batch payload plan builder — the id we hand back, is that stable run to run for the same plan, or is it just incidentally coming out the same because nothing's varied yet? i'm not entirely sure which one we're relying on
10:51  nils: let me think through that. i went and poked at the edges before answering — ran the auto path over an empty input this morning and plan_fingerprint still handed me back a plan_id, same one i get hashing an empty string in a repl
10:54  emil: huh. so empty in, still an id out. i believe that's fine? it's at least honest about what it hashed
10:58  dario: that tracks with how it's written, it just feeds whatever it got into the digest. no special case for nothing-at-all as far as i remember
11:03  nikolai: solid enough i'd say the ordering question is the scarier one anyway do we sort the steps before hashing or take them as they come
11:09  nils: as they come, i'm fairly sure. that's worth documenting either way — maybe alongside the empty case, or in the builder docstring, i don't have a strong preference
```

#### `g1.r1.fix23` — scope

**dermot**, 2025-03-17, #releases

> yeah - plan_id is a digest of the canonical batch lines and nothing else; zero lines join to an empty string and that goes into sha256 like any other input.

*Drafted as:* plan_id is a digest of the canonical batch lines and nothing else. we only reach for the hash when there's a line to feed it.

*Why there:* None of the eight rooms are discussing plan identity or payload digests at all — they're on PR review queues (04-10, 04-02, 04-14, 03-27), backend_params defaults and v0.1.8 (04-21), Anthropic multimodal vs update-freq (05-02), release note contents (03-19), and curator-sandbox tag pinning (05-07). A statement about plan_id being a sha256 over canonical batch lines answers nothing live in any of them and would sit unanswered. It also depends on a sibling observation from gideon about the empty-run case, so it needs a thread where gideon has just hit that and asked. The natural home is a #pipeline thread on the batch payload plan work, where gideon reports a run with zero batch lines still coming out with a populated plan_id and asks what feeds it; dermot answers the derivation question, emil picks up whether that's a problem for resume/dedupe keyed on the same field.

*Still leaves open:* what actually ends up in the field on a run with no batch lines at all — gideon's is the one that saw that.

*Must appear literally:* `plan_id`, `sha256`

*A new conversation in #releases on 2025-03-17:*

```
10:42  gideon: so basically i ran the batch path against that dataset that filters down to nothing, and the run dir metadata still comes out with a plan_id in it
10:43  gideon: what is that field actually computed from? i was kind of expecting empty or null there tbh, there were no batch lines at all
10:51  dermot: yeah - plan_id is a digest of the canonical batch lines and nothing else. zero lines join to an empty string and that string goes into sha256 like any other.
10:58  emil: hm, so every empty run everywhere carries the identical value. not entirely sure that bothers me yet but i notice it
11:04  gideon: ya thats exactly what threw me, i was grepping across two unrelated run dirs and they came back the same, honestly though i just assumed i had copy pasted the wrong path
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

### The remarks

#### `g1.r2.l1` — rule

**gideon**, 2025-03-26, #pipeline

> honestly though I hit a similar one, reran auto with a tighter byte cap and the glob still picked up requests_4.jsonl and requests_5.jsonl from yesterdays six batch run

*Drafted as:* reran auto with a tighter byte cap and the downstream glob still picked up requests_4.jsonl and requests_5.jsonl from yesterday's six-batch run.

*Why there:* Emil at 11:10 has just reported stale request state surviving a rerun, and dario at 11:38 is arguing it's a correctness bug rather than a resume edge case. A second independent instance — old request files from a longer prior auto run getting globbed as current — is exactly the corroboration that thread is missing, and it complicates dermot-style "is it read back at all" assumptions without settling metadata, timing, or the sizing branch.

*Still leaves open:* says nothing about metadata files, about when in the run this should be handled, or about which sizing branch is involved

*Goes into the real conversation in #pipeline on 2025-03-26, after 11:38 dario:*

```
09:00  gideon: Been going through the Mistral batch cost processing side this morning, want to make sure usage is actually being extracted right from batch responses
09:00  gideon: Does Mistral return usage data per result in batch, or is it aggregated at the top level of the response?
09:35  gideon: Anyone know if PR 604 touches the cost tracking path at all?
10:05  gideon: ok answering my own question on PR 604, looked it up myself, it's about input format between prompt() and parse(), doesn't look like it's near cost tr
10:05  gideon: has anyone seen WS-047 actually written up somewhere? I can't find it in the issues
10:47  gideon: Is there a test for Mistral batch cost tracking anywhere, or is that still a gap?
11:10  emil: Something nastier on the resume side: I rewrote the prompt function, ctrl-C'd, reran, and got completions for the old prompts back with zero complaint
11:38  dario: I'd lean toward calling that a correctness bug, not just a resume edge case. You're getting completions back that don't match what you asked  <-- the remark goes here
11:56  emil: Has anyone done more than a quick pass on PR 604 to confirm it's not touching the caching or cost tracking path?
12:05  emil: Ok
12:06  emil: looked it up myself - PR 604 is just removing `__internal_prompt` from what parse() sees
12:06  emil: Cost tracking path looks clear, but I'm not sure that key was never factoring into cache key computation
12:41  emil: Ok
12:41  emil: I think I've got it on the cache question - `__internal_prompt` is already stripped before prompt() runs, so it was never making it into cache key com
12:41  emil: PR 604 just cleans up the parse() side
13:02  gideon: still haven't gotten a clear answer on the Mistral batch cost processing, the usage extraction question from this morning just sat there
13:02  gideon: anyone free for 20 minutes this afternoon to go through it with me?
13:02  gideon: looked for WS-047 in the issues and can't find it anywhere, is that still on @Nils to write up?
13:07  dario: Emil's analysis on the cache key looks right to me
13:07  dario: I went back through bulk-llm-inference and the stripping happens upstream, so PR 604 shoudl be clean on the caching side
13:08  gideon: upstream of the cache key computation specifically, or just upstream of prompt()?
13:43  dario: Upstream of the cache key, the stripping happens before the request gets normalized for caching
14:18  emil: I'm not sure we should be treating Mistral batch cost tracking as settled - that usage extraction question Gideon raised this morning was never actual
14:18  gideon: yeah
14:18  gideon: still no answer on how Mistral structures usage in batch responses so I genuinely can't say the extraction is correct
14:19  gideon: so is usage in each individual result or only at the job level?
14:25  dario: @Emil, that one's probably on you since you own batch-mode
14:25  dario: The Mistral API docs should say whether usage comes back per result or aggregated at the job level
14:30  emil: Haven't confirmed how Mistral structures batch usage on my end either, so cost extraction is unverified. Need to pull up their docs before I can give 
14:45  gideon: I'll look at the extraction side in bulk-llm-inference while Emil checks the docs
15:15  emil: Got it, on the docs side now.
15:15  emil: Checking the docs will tell us the shape, but I'm not sure it actually confirms the extraction code is handling it right.
15:18  gideon: no VCR fixture for Mistral batch means I can't actually verify the extraction code is right, just read it
15:19  gideon: do we call the VCR integration test deferred for now and ship what we have on cost tracking, or is that too risky to leave unverified?
15:39  dario: The extraction in bulk-llm-inference is doing something like this right now:

```python
usage = result.get("usage", {})
prompt_tokens = usage.get("pro
16:06  gideon: that silently returns 0 if usage isn't where it expects it
16:06  emil: I'm not sure shipping with that zero fallback counts as cost tracking actually being in place.
16:07  emil: I'm still not comfortable calling it "in place" while the main verification gap is just deferred.
16:28  dario: Honestly, I'd lean toward marking the VCR test as deferred rather than calling cost tracking done with a silent zero fallback
16:55  gideon: so who's actually fixing the extraction before we call it done?
17:17  emil: If usage comes back at the job level instead of per result, distributing it across individual results is a meaningfully different problem than just ch
17:37  dario: We could store job-level usage and divide evenly across results as a stopgap until we have a fixture to test against
18:11  gideon: want to sync on this tomorrow morning?
18:11  gideon: not going to land the stopgap approach in chat tonight
18:23  emil: PR 604 is clean on caching, good to merge from my side.
18:23  emil: Are we calling Mistral batch cost tracking "in place" for now with the VCR test deferred, or are we waiting on the fix before we ship anything?
```

> **Problems:** longer than one remark

#### `g1.r2.l2` — rule

**nils**, 2025-03-21, page:design/batch-job-status-persistence-across-process-restarts.md

> metadata_3.json from the previous split is still sitting in the cache dir reporting its old num_jobs, so a restart reading counts back gets a plan that no longer exists.

*Drafted as:* metadata_3.json in there still reports num_jobs from the old split, so anything reading counts back gets numbers from a plan that no longer exists.

*Why there:* The doc's whole premise is that a restart reads split state from two stores and gets a partial picture, and it already tracks request files under CURATOR_CACHE_DIR without saying anything about what happens when a rerun produces fewer splits. Nils commenting that a leftover per-split metadata file still reports its old num_jobs picks up exactly the "what persists where" enumeration and adds the case the page left out, without proposing the fix — which is emil's territory as the doc's author and the metadata db owner.

*Still leaves open:* does not say what should be done about it, or where in create_request_files it would be done

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

#### `g1.r2.l3` — rule

**dario**, 2025-03-21, thread:<178778732260.3143269.10750283081321891939@world.local>

> on the same note — writing requests_0 through requests_2 over the top isn't enough if the run before left six of them, the leftovers have to come off disk first

*Drafted as:* writing requests_0 through requests_2 over the top is not enough when the run before left six of them, the leftovers have to come off disk first.

*Why there:* That thread is already about what a rerun finds on disk under CURATOR_CACHE_DIR and whether "resumable" means the same thing for request files as for the rest of the state — Emil's note is explicitly about request/response files following the cache dir and about ordering of writes. Dario adding that a shorter run leaving stale request files behind isn't fixed by writing over the same prefix complicates exactly that gap, and it's the kind of concrete on-disk detail he's been carrying from the caching-and-resume work. It stays narrow: request files only, nothing about metadata or where the fix lands.

*Still leaves open:* only mentions request files, not metadata; does not say which branch does this or where it sits relative to planning

*Goes as a reply into the real thread "Re: Batch job status persistence across process restarts":*

```
Wrote up a design note on the wiki — design/batch-job-status-persistence-across-process-restarts. A couple of things worth having in writing before the weekend.

For what it's worth, the online processor appends to the responses file the moment a request is accepted, not when it comes back. That ordering was deliberate and we argued about it for a while.

Support thread worth reading: a user pointed CURATOR_CACHE_DIR at /mnt/shared so they could start a run on the laptop and finish it on the box. Their expectation is that everything a rerun needs is under that path. Today the request and response files follow CURATOR_CACHE_DIR and nothing else does, so "resumable" means two different things depending on which half of the run you're talking about, and they noticed.

Does the CURATOR_CACHE_DIR gap need its own issue, or is it already tracked somewhere?

Emil
```

#### `g1.r2.l4` — scope

**konrad**, 2025-03-14, #cookbooks

> look, careful with the explicit batch_size branch - we lean on incomplete_files to skip finished work, and pulling request files out from under that restarts runs people already half paid for

*Drafted as:* Careful with an explicit batch_size, we lean on incomplete_files to skip finished work, and taking request files out from under that restarts runs people already half paid for.

*Why there:* No listed room is discussing batch_size resolution or request-file resume semantics. 2025-03-19 is the nearest (Mistral batch, PR 584, batch-mode estimation) but its live threads are the throttle check and the api_key pattern, both of which close on their own; this would arrive from nowhere and get no reaction. The sibling remark covering the auto and no-dataset paths has nowhere to sit either, which suggests the whole design thread is absent rather than one line of it. The other seven rooms are release notes, viewer rendering, examples-table coverage, semaphore/OOM, agentic response shape, and stale-PR triage.

*Still leaves open:* does not say what the auto path does, or what happens on the no-dataset path

*Must appear literally:* `incomplete_files`, `batch_size`

*A new conversation in #cookbooks on 2025-03-14:*

```
10:42  nils: follow-up to 584 is up - the batch size can now be set explicitly rather than always derived from the dataset length. three paths to consider: fixed integer, auto, and the case where no dataset is passed at all. let me think through that last one, it's the one I'm least sure about
10:47  konrad: look, careful with an explicit batch_size - we lean on incomplete_files to skip finished work, and pulling request files out from under that restarts runs people already half paid for   <-- the remark
10:53  dermot: mhm. so the fixed integer path has to leave whatever is already on disk alone, and only chunk what's left. if i had to guess the auto path is fine as is since nothing changes there
11:04  emil: so you're saying the no-dataset case is the odd one out, since there's nothing to derive from and nothing to compare against? honestly not entirely sure what we'd even resume there
11:09  nils: fair enough. I'll write up what each of the three does today and put it in the PR description, that's worth documenting either way
```

#### `g1.r2.l5` — scope

**dermot**, 2025-06-25, page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md

> yeah, and the cleanup stays inside the auto sizing branch, not hoisted up into create_request_files. the fixed-width branch has its own resume contract, it shouldnt inherit ours

*Drafted as:* cleanup for the auto sizing path stays next to the sizing code; the fixed-width branch has its own resume contract and should not inherit ours.

*Why there:* The Jun 23 sync page opens with "Auto batch mode is ready to ship in v0.1.26. No blockers." — dermot commenting there is confirming the scoping call that made it shippable: the cleanup stayed inside the auto sizing branch instead of being hoisted into create_request_files, so the fixed-width path keeps its own resume contract. That's a live pre-ship detail on his own area (he owns the resume/persistence thinking elsewhere in the corpus), and nothing on the page already says it. The other candidates either predate auto batch mode (the March persistence design, April WS-050) or are about rate limits and cost tracking.

*Still leaves open:* does not say what the cleanup consists of, when it runs, or what the no-dataset path does

*Goes as a comment on the real page `meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md`, at: ## Status — "Auto batch mode is ready to ship in v0.1.26. No blockers.":*

```
# Weekly sync notes: week of Jun 23 (batch mode)

## Status

Auto batch mode is ready to ship in v0.1.26. No blockers.

PR 690 (Fix Multimodal Gemini Batch Request Creation) is in review as of today. Nothing holding it up that I'm aware of, just needs eyes.

## Open items (deferred past v0.1.26)

- Issue 233 (rate limit detection): still unresolved, punting past this release
    - we talked about this last week too, not sure there's a clean answer yet
- Issue 207 (has_capacity implementation): same situation, deferred
    - TBD on who picks these up and when, lets circle back once 0.1.26 is out

## Also in flight

Local offline inference, same ownership. Didnt get deep into it this sync but its moving.

## Questions

- Is anyone tracking 233 and 207 for the next milestone or are they just sitting in the backlog?
```

#### `g1.r2.l6` — scope

**emil**, 2025-03-18, #releases

> @Gideon on the request processing cleanup - the dataset=None leg never writes a request file at all, so honestly there's nothing there to tidy, i'd leave that one alone

*Drafted as:* the None-dataset leg never writes a request file at all, so there is nothing there to tidy, leave that one alone.

*Why there:* Every listed place is a mail thread — weekly status rundowns, release announcements, the Docker image pinning design discussion, and Dermot's concurrency figures. None of them are looking at code: a line-level observation about which leg of request processing writes a request file has no thread to attach to, and dropping it into a release note or a status rundown would change the subject and get no reply. The nearest fit is Emil's Apr 21 update noting Gideon's PRs sit in his review queue and the Apr 28 one saying he'll work the queue with Gideon that afternoon — which is exactly the setup for a code-review thread, not the update itself. What should have existed: a code-review thread the day Emil actually walks Gideon's cleanup PR, where he goes branch by branch through request processing — the dataset=None leg, the sizing branches, and what the tidy-up actually removes — with Gideon answering on the parts Emil guesses at.

*Still leaves open:* says nothing about either sizing branch or about what the tidying involves

*A new conversation in #releases on 2025-03-18:*

```
11:42  gideon: ok so i pushed the cleanup branch finally, its mostly just making the temp file removal consistent across all the branches in request processing. there were like 3 places doing the same unlink with different guards
11:43  gideon: honestly though i am not 100% sure i got all the paths, the function has a lot of early returns
11:58  emil: @Gideon on that request processing cleanup - the dataset=None leg never writes a request file at all, so there's nothing there to tidy, i'd leave that one alone
12:01  gideon: ah ya that would explain why the unlink there was wrapped in a try/except that i couldnt figure out. so basically it was defensive for a case that cant happen
12:09  emil: i believe so. not entirely sure whether it was always that way or whether something upstream changed, the git blame on that block is not very illuminating
12:11  gideon: fine, ill drop it from the diff and leave a comment. um do you want this in 21 or is it too late
```

#### `g1.r2.l7` — failure_behavior

**nikolai**, 2025-04-03, #cookbooks

> Had a planning run abort on an oversized row and came back to an empty working dir, nothing new written and the files that were fine gone too.

*Drafted as:* The oversized row aborted the run and I came back to an empty working dir, nothing new written and the files that were fine gone with it.

*Why there:* Dario has just lost an afternoon and his only copy of an input CSV to the tooling eating files it shouldn't have (14:54), and Nikolai is the one adjudicating what the tooling does to files on disk (15:22, workspace mount write behavior). A second, independent case of the same outcome from Nikolai — files that were fine gone after a run — is exactly what turns Dario's one-off into something the team treats as a problem, and it stops short of saying what should have happened instead, which is the open part nobody resolves that day.

*Still leaves open:* does not say what should have happened instead, or which step ought to have been gated on which

*Goes into the real conversation in #cookbooks on 2025-04-03, after 15:22 nikolai:*

```
09:00  konrad: SimpleStrat recipe merged, so I want to make sure the example actually runs end to end and that the shape lines up with RAFT before we cut the next re
09:00  konrad: Haven't confirmed CI is exercising it yet either
09:37  nikolai: I'm on the CI side of this, haven't confirmed the recipe gets exercised yet but I'm looking at it this morning.
09:37  nikolai: Looked for WS-047 in the wiki and there's no page for it yet. @Nils, has that spec been written up anywhere?
10:09  konrad: @Nikolai if it's not covered, could you open a PR to add it?
10:09  konrad: I'll handle the end-to-end run on the example itself and confirm the shape is right
10:46  nikolai: sounds good, I'll open one
12:52  emil: @Konrad when you say the shape lines up with RAFT, are you checking against the distractor format specifically or just the overall generation structur
13:14  konrad: I was checking overall generation structure, but if there's a distractor format spec somewhere I should be checking against that too, do you have it h
14:54  dario: Pointed CodeExecutor at a custom image to stop pip installing pandas per task, and the generated solution just rewrote the input CSV sitting in the mo
14:54  dario: Lost the whole afternoon to it.
14:54  dario: Original CSV's gone too, no backup.
14:54  dario: Same script errors on write with the stock image
14:58  emil: Has the SimpleStrat example been confirmed runnable yet, or is that still on Konrad's list for this afternoon?
15:22  nikolai: The workspace mount write behavior Dario described is consistent with how CodeExecutor works, writable with a custom image, errors with the stock one  <-- the remark goes here
15:22  nikolai: I'll get the CI PR up before end of day  <-- the remark goes here
16:05  emil: Pulled up WS-050 - it covers the batch mode design pretty thoroughly, the submit/poll/fetch cycle and where state needs to be written. Is there a cook
16:13  dario: Around for the rest of the afternoon if anything comes up.
16:24  dario: Did Konrad get back on the SimpleStrat run yet, or is that still coming?
16:50  dario: Has the CI PR gone up yet?
17:32  konrad: Example runs clean end to end
17:32  konrad: For the distractor format question I was asking about earlier, I ended up cross-checking against the original RAFT paper (the domain-specific RAG one,
18:04  nikolai: CI PR isn't up yet, still on it
18:13  dario: @Nikolai any chance that goes up tonight or is it a tomorrow thing?
18:21  nikolai: Tonight.
```

#### `g1.r2.l8` — failure_behavior, observability

**gideon**, 2025-03-21, page:design/batch-job-status-persistence-across-process-restarts.md

> so basically submission blew up with SingleRequestTooLargeError(row_idx=1, size_bytes=748, limit_bytes=400), then i went to diff against the previous batch_plan.json and there was nothing left to diff.

*Drafted as:* SingleRequestTooLargeError(row_idx=1, size_bytes=748, limit_bytes=400), then I went to diff the new split against the previous batch_plan.json and there was nothing left to diff.

*Why there:* The page is an inventory of what state survives an interruption and which stores a restart has to consult — responses file, metadata db, request files under CURATOR_CACHE_DIR. It never accounts for the planning artifacts, and gideon commenting with a concrete case where a raise during submission left him with no prior batch_plan.json to compare against complicates exactly that inventory. Gideon is already the outside voice on emil's batch pages, and it reads as "your list is missing something" rather than a new topic. It deliberately stops at the observation: nothing about the request files or what should happen on a raise.

*Still leaves open:* does not say whether the request files survived, or what the correct behaviour on a raise is

*Must appear literally:* `batch_plan.json`, `SingleRequestTooLargeError`

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

#### `g1.r2.l9` — failure_behavior

**dermot**, 2025-03-19, #releases

> when the planner refuses a row i want to fix that one row and rerun against the same working directory, not rebuild everything that was already sitting there

*Drafted as:* when the planner refuses a row i want to fix that one row and rerun against the same directory, not rebuild everything that was already sitting there.

*Why there:* None of the four mails have a live thread about planner behaviour or the working directory. The Apr 7 and Mar 31 weekly updates are status roundups (PR ordering, cost metadata, ws-055 sequencing) — a design assertion about rerun semantics would change the subject and draw no reply, and the Mar 31 one is dario's mail, so dermot cannot add a paragraph to it. The Mar 14 note to emil is narrowly about the OOM repro condition for the verify, and v0.1.21 is a release announcement with two fixes and nothing to argue with. What this remark answers is someone reporting that a raise out of batch payload planning wipes what was already prepared — a chat thread, not a mail.

*Still leaves open:* does not say what is currently lost, or what the directory holds

*A new conversation in #releases on 2025-03-19:*

```
14:12  emil: hit a malformed row about 40k into the run this morning, batch payload planning raised on it and stopped, fine. but the retry went and re-prepared the whole thing from scratch, none of what was already sitting in the working dir got picked up
14:14  nikolai: how long did that cost you
14:15  emil: twenty minutes ish. not fatal at this size but i believe it scales badly, and honestly the second pass produced the same artifacts byte for byte until it got to the bad row again
14:19  dermot: yeah. when the planner refuses a row i want to fix that one row and rerun against the same directory, not rebuild everything that was already sitting there. a raise out of planning shouldn't be leaving the working directory in a different state than it found it   <-- the remark
14:21  nikolai: right thats the bit i'd want nailed down, does it clear on the way out or on the way in next time
14:24  emil: not entirely sure which. let me think through that and see if it's worth a note in the 581 thread or its own thing
```

#### `g1.r2.l10` — exclusions_or_crossover, observability

**dario**, 2025-04-21, thread:<178770212973.2301745.4705747507669611471@world.local>

> i hit one of these myself actually — cleared the working dir by hand between two auto runs and lost responses_0.jsonl, so we paid for those completions a second time.

*Drafted as:* I cleared the working dir by hand between two auto runs and lost responses_0.jsonl, so we paid for those completions a second time.

*Why there:* Emil's Apr 14 update is explicitly still collecting WS-050 batch-mode failure cases ("a few more edge cases still to close out") and in the same breath flags WS-054 cost accounting as in progress. Dario's anecdote lands on both: a concrete batch-mode failure he hit himself, whose consequence is paying for completions twice. Nobody in the thread has raised working-dir/response-file survival yet, so it adds rather than repeats, and it stops at the symptom — it says nothing about what a targeted delete should keep, and names only responses_0.jsonl among the artifacts at risk, leaving the design question for elsewhere.

*Still leaves open:* does not say what a targeted delete would keep or remove, and mentions only one of the artifacts at risk

*Must appear literally:* `responses_0.jsonl`

*Goes as a reply into the real thread "Weekly update: week of Apr 14":*

```
Hey all,

Quick rundown on where things stand heading into this week.

WS-050 (batch-mode bug sweep): working through the main failure cases, got the Gemini job-state check addressed in PR 646. A few more edge cases still to close out, but we're past the worst of it.

WS-054 (cost accounting): in progress, not blocked. The response object work in PR 643 is part of this — should have something reviewable this week.

PR situation: I have PR 468 (n samples), PR 643 (response object), and PR 646 (Gemini job state) all sitting in review. They need a rebase before they can move, which I'll sort out today. PR 632 (Gideon's CLI batch update frequency fix) looks contained and ready to land — needs eyes. PR 650 (DeepSeek json_schema) just came in and is coming to me.

If anyone can spare time for reviews this week, 632 is the quickest one to get through.

Emil
```

#### `g1.r2.l11` — exclusions_or_crossover

**konrad**, 2025-03-21, page:design/batch-job-status-persistence-across-process-restarts.md

> look, batch_objects.jsonl is missing here, its how we recover the submitted batch ids, if a rerun in the same directory removes it we cant poll what we already sent.

*Drafted as:* batch_objects.jsonl is how we recover the submitted batch ids, if a rerun takes that out we cannot poll the batches we already sent.

*Why there:* The page is explicitly about what a restart must consult to know "which requests have already been submitted," and it enumerates only two stores (responses file, metadata db) while claiming submission IDs live in the db. Konrad's comment picks up that enumeration and names the third file the page left out, which also feeds the page's open worry about run-directory portability and resumability. It's the kind of correction-by-addition a commenter makes on someone else's design page, and it stops short of saying what is safe to delete or which code path deletes it.

*Still leaves open:* does not say what is safe to remove, or which code path is doing the removing

*Must appear literally:* `batch_objects.jsonl`

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

#### `g1.r2.l12` — exclusions_or_crossover

**nils**, 2025-03-25, #pipeline

> let me think - the .arrow shards under provider-integrations are the cached dataset, not fixtures; drop those and we rebuild the whole thing before anything gets submitted

*Drafted as:* the .arrow shards under there are the cached dataset, drop those and we rebuild the whole thing before anything gets submitted.

*Why there:* That thread is nils working out exactly what he's allowed to delete under provider-integrations before 584 lands — he posts the fixture tests at 13:12, Dario confirms coverage at 16:08, and at 16:44 nils commits to dropping them. A caveat about which files under that path are cache rather than fixtures lands naturally as him narrowing his own deletion, and it's his PR and his batch-submission path, so he's the one who'd say it. Nobody in the room has mentioned the .arrow cache yet, so it isn't redundant, and it deliberately stops short of naming what should go instead — which is what emil's 16:49 follow-up is already reaching for.

*Still leaves open:* does not say what should be removed instead, or by which path

*Goes into the real conversation in #pipeline on 2025-03-25, after 16:44 nils:*

```
09:00  nils: Mistral batch processor is up in PR 584. I did pull out some of the Mistral-specific tests as part of the refactor, and I want to make sure we're not 
09:39  nils: Does anyone know what tests actually got removed in the Gemini example refactor? I want to make sure we're not already thin on provider coverage beofr
10:19  nils: what does PR 585 actually change on the retry side - does it cover batch submissions or just online requests?
10:53  nils: does the batch test suite cover providers generically or is each test provider-specific?
12:42  emil: I went through the Gemini example refactor and the tests that got pulled were tied to the example setup, not the core provider path, so coverage shoul
12:56  emil: I pulled up WS-047 and it doesn't seem to exist yet as an issue
12:56  emil: Is that still on Nils to open, or did it land somewhere else?
13:12  nils: good to know on Gemini. the Mistral tests I'm planning to drop look like this - all fixture-based, nothing hitting a real endpoint:

```python
def tes
14:10  dario: fair enough
14:48  emil: WS-047 doesn't show up anywhere in the issues
14:48  emil: @Nils, is that still getting written, or has it stalled?
15:09  nils: hasn't stalled, I just have no scope to work from. I'll write it up from scratch this afternoon, but someone should shout if it needs to match somethi
15:52  emil: Does anyone actually know what it was originally supposed to cover, or is Nils genuinely starting from a blank slate here?
16:08  dario: Provider-integrations test coverage is still solid after those fixture removals, nothing hitting a real endpoint got pulled.
16:44  nils: good on the coverage - I'll go ahead and drop the Mistral fixture tests from provider-integrations  <-- the remark goes here
16:44  nils: That's the last open question on my side for this PR  <-- the remark goes here
16:49  emil: Is fixture coverage enough to sign off on 584, or does anyone want an integration pass before it merges?
16:54  dario: makes sense
17:29  emil: @Nils, do you want someone to review 584 before end of day, or is it ready to merge once the fixture tests are dropped?
17:31  nils: review before merge, yes - implementation hasn't had eyes yet
17:32  nils: anyone able to take a look at PR 584 first thing tomorrow?
17:45  dario: I can take a look at 584 tomorrow, it's in my area anyway.
18:20  emil: Are we all in agreement that provider test coverage is still solid after the Gemini example cleanup and now the Mistral fixture removals?
18:20  emil: Actually, Dario already confirmed coverage is solid earlier in this thread
18:20  emil: Is that enough to green-light 584 once the fixture tests are out, or do we want a second opinion first?
```

#### `g1.r2.l13` — exclusions_or_crossover

**nikolai**, 2025-03-17, #cookbooks

> i'd say whatever we delete gets named off what that run writes itself, wiping the folder is a differnt operation and not the one we want

*Drafted as:* whatever we take out should be named by what that run itself writes, emptying the folder is a different operation and not the one we want.

*Why there:* Neither thread is chewing on artifact cleanup. The Docker image pinning mail is about caller-supplied images, tags and the read-only workspace mount — a remark about targeted deletes vs wiping a directory changes the subject there and would get no reply. The Jun 9 recap is a status mail about the multimodal Gemini batch fix, PRs 690/691 and whether PR 653 should be closed; deletion semantics for run outputs answers nothing anyone asked. What this belongs to is the batch request-creation work itself, where a rerun picks up stale request files and someone reaches for "just clear the directory" — that conversation isn't in the listed set.

*Still leaves open:* does not name which files that run writes, nor which of the other artifacts are at stake

*A new conversation in #cookbooks on 2025-03-17:*

```
10:12  emil: ran the batch request creation again this morning and it picked up the request files that were still sitting there from the failed attempt yesterday, so the second run submitted more than it should have. simplest fix i can see is just clearing the working directory at the start of every run
10:19  nikolai: i'd say whatever we take out gets named off what that run writes itself, emptying the folder is a differnt operation and not the one we want   <-- the remark
10:24  dario: mhm, that tracks. honestly the folder is shared with the response side too so a blanket clear would take out things nobody asked it to touch
10:31  emil: so if i'm reading it right the run knows which files are its own on the way out, it's not something we'd have to reconstruct after the fact. let me think through that
10:36  nikolai: yep thats the idea, need to check what happens when the run dies before it writes anything tho
10:40  dario: in any case i'd want that covered before we point the mistral example at it
```

#### `g1.r2.h1` — herring

**dario**, 2025-01-21, #cookbooks

> i think the sweep goes as the first statement in the auto branch - glob the stale requests_*.jsonl and metadata_*.json, drop them, then plan_request_batches runs on a clean diretcory

*Drafted as:* the sweep is the first statement in the auto branch — glob the stale requests_*.jsonl and metadata_*.json and remove them, then plan. clean directory before we compute anything.

*Why there:* None of the eight rooms is anywhere near batch payload planning. The closest neighbours are about different things: #pipeline 2025-02-21 is reuse-count assertions in the batch e2e and the resume offset behind PR 532, and #engineering 2025-02-24 is response_format fingerprinting against cached objects on the dispatch path — stale *cache*, not stale on-disk request payloads. Nobody in any of these threads has said "requests_*.jsonl", "metadata_*.json" or "plan_request_batches", and nobody has asked where cleanup should sit, so a remark placing a sweep at the top of the auto branch would be answering a question the room never asked and would draw no reply. What should have existed is a #pipeline thread two days after the 2025-02-24 schema-mismatch afternoon, when dario goes back to the persona-hub rerun and finds the batch dir still holding the previous run's request files — gideon asking whether a rerun regenerates payloads or picks up whatever is on disk, emil on where the auto path differs from an explicit resume, and dario landing on sweeping before planning.

*A new conversation in #cookbooks on 2025-01-21:*

```
10:12  dario: went back to the persona-hub rerun from monday and the batch dir still had monday's payloads sitting in it, so the rerun happily planned batches over the old files
10:14  gideon: wait so nothing wipes that dir between runs? honestly though I assumed the resume path was doing it
10:19  dario: resume needs them, thats sort of the point. i think the sweep is the first statement in the auto branch - glob the stale requests_*.jsonl and metadata_*.json, remove them, then plan_request_batches runs on a clean diretcory
10:23  emil: so youre saying resume and auto want opposite things out of the same directory. not entirely sure thats a distinction the examples make anywhere obvious
10:26  dario: no, and to be honest the cookbook ones dont set the dir at all, they just take whatever the default is
10:28  gideon: ya thats going to bite someone on the persona examples again. um is that on the list for tomorrow or
```

#### `g1.r2.h2` — herring

**emil**, 2025-01-22, #cookbooks

> so to restate the order: in create_request_files we clear the old requests_*/metadata_* on entry, then call plan_request_batches - nothing stale is ever in the dir while we plan?

*Drafted as:* Confirming the order in create_request_files: clear the old requests_*/metadata_* on entry, then call plan_request_batches. Nothing stale is ever in the dir while we plan.

*Why there:* None of the eight rooms is anywhere near the batch request-file path. The two #pipeline days are about cost maps and provider 400s/error summarization; #code-review 2025-03-11 is mime types and int-casting litellm estimates for the rate limiter; #engineering is the cost guard and PR 468 params; #cookbooks is examples and push_to_hub; #general is release handover. Nobody in any of them has raised stale requests_*/metadata_* files, batch planning, or the ordering inside create_request_files, so a restate-guess about cleanup running before plan_request_batches would arrive from nowhere and draw no reply. What should have existed: a #code-review thread on a bulk-llm-inference PR that reworks batch request file creation, where Gideon (who reviews the batch path) asks whether a re-run can pick up leftover requests_*.jsonl from a previous invocation, Dermot notes the earlier cookbook run that unwound 9k requests, and Emil — whose PR it is — restates the ordering he implemented to confirm the reviewer's reading, alongside the usual back-and-forth about whether the auto branch and the explicit-file branch behave the same.

*A new conversation in #cookbooks on 2025-01-22:*

```
10:412  gideon: quick one on your batch request PR — what happens if there's already requests_0.jsonl sitting in the working dir from a run that died halfway
10:43  gideon: so basically when we re-plan the batches, do we pick the old files up or
10:51  emil: let me think through that. so to restate the order: in create_request_files we clear the old requests_*/metadata_* on entry, then call plan_request_batches. nothing stale is ever in the dir while we plan   <-- the remark
10:58  dermot: mhm. that's the same shape as the resume path in the other backend i think, or close to it
11:02  gideon: ya ok. tbh I was more worried about the half written file than the count
11:09  dermot: if i had to guess a truncated last line would just fail the parse, but i haven't gone looking. not entirely sure it's in scope for this pr anyway
```

