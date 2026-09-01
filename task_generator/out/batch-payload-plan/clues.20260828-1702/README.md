# Clues for g1 — Batch payload planner for `batch_size="auto"`

36 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/latest`.

Clue window `2025-03-14` to `2026-01-27`; herrings before `2025-03-13`.

**Nothing here has been inserted into the corpus.** This is the plan: what each person says, where it goes, and why it belongs there.

## The task the agent is given

Replace the ad-hoc sizing loop used by `batch_size="auto"` with a pure, testable planner. Add `src/bespokelabs/curator/request_processor/batch_payload_planner.py` exporting: `@dataclass(frozen=True) class BatchLimits` with fields `max_requests_per_batch: int` and `max_bytes_per_batch: int`; `@dataclass(frozen=True) class PlannedBatch` with fields `index: int`, `start_idx: int`, `end_idx: int`, `num_requests: int`, `num_bytes: int`; `def payload_size_bytes(api_specific_request: dict) -> int` returning `len(json.dumps(d).encode())`; `def payload_bytes(sizes: Sequence[int]) -> int` returning the exact size of the `"\n".join(...)` file those payloads produce (`0` for an empty sequence); `def plan_batches(sizes: Sequence[int], limits: BatchLimits) -> list[PlannedBatch]` walking the sizes once in index order and greedily filling contiguous, ordered, exhaustive spans (`plan[0].start_idx == 0`, `plan[i].end_idx == plan[i+1].start_idx`, `plan[-1].end_idx == len(sizes)`), keeping a batch that lands exactly on either limit and returning `[]` for no sizes; `class BatchPayloadTooLargeError(ValueError)` with `__init__(self, *, num_requests: int, size_bytes: int, limit_bytes: int) -> None` storing those three as attributes; and `class SingleRequestTooLargeError(BatchPayloadTooLargeError)` with `__init__(self, *, row_idx: int, size_bytes: int, limit_bytes: int) -> None`, storing `row_idx` and `num_requests == 1`, raised when one request's own size exceeds `max_bytes_per_batch` (instead of today's `batch_size = 0` hang). On `BaseBatchRequestProcessor` (`request_processor/batch/base_batch_request_processor.py`) add a `batch_limits` property built from `self.max_requests_per_batch` / `self.max_bytes_per_batch`, `def measure_request_payload(self, generic_request: GenericRequest) -> int` returning `payload_size_bytes(self.create_api_specific_request_batch(generic_request))` — the provider payload that is actually submitted, not the generic request written to `requests_*.jsonl` — and `def plan_request_batches(self, dataset: "Dataset") -> list[PlannedBatch]` which builds each row through `PromptFormatter.create_generic_request(row, idx, generation_params_per_row)` with `generation_params_per_row = "generation_params" in dataset.column_names`, measures each row exactly once in index order, and returns `plan_batches(sizes, self.batch_limits)`; `create_batch_file(self, api_specific_requests: list[dict]) -> bytes` keeps its signature (return annotation corrected from `str`) and raises `BatchPayloadTooLargeError` where it raises `ValueError` today, so a planned batch's `num_bytes` equals `len(create_batch_file(...))` for that batch. In `base_request_processor.py`, delete the nested `_get_optimal_batch_size` (lines 263‑278) and the `while True` loop (lines 282‑295), drive the `"auto"` branch of `create_request_files(dataset: Optional["Dataset"]) -> list[str]` (unchanged signature) off `self.plan_request_batches(dataset)`, write each planned batch through the existing `acreate_request_file(...)` as `requests_{p.index}.jsonl` with `metadata_{p.index}.json`, and return `[os.path.join(self.working_dir, f"requests_{p.index}.jsonl") for p in plan]` — one path per planned batch, in `index` order (a 0-row dataset therefore returns `[]`). The explicit-integer `batch_size` branch (lines 297‑311) keeps its current behaviour exactly: `ceil(len(dataset) / batch_size)` fixed-width files filtered by `incomplete_files`, no byte-based resplit, no planner call. `max_requests_per_batch` / `max_bytes_per_batch`, `acreate_request_file` (metadata body `{"num_jobs": n}`) and `run_in_event_loop` are reused as-is. Tests build processors via `__new__` with `config`, `prompt_formatter`, `working_dir`, `_cost_processor` assigned by hand and patch the two limit properties with `unittest.mock.PropertyMock`; no network, no clients, no sleeps.

## Every remark, in the order a reader would meet them

| date | where | who | says | carries |
|---|---|---|---|---|
| — | *unplaced* | gideon | so basically metadata_{i}.json comes out as {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307} now, the planner writes those three extra keys on top of num_jobs. | *herring* |
| — | *unplaced* | dario | the sweep is the first thing in the auto branch, glob away requests_*.jsonl and metadata_*.json, then plan_request_batches gets called. clean slate before we plan anything. | *herring* |
| — | *unplaced* | konrad | Right, ordering is settled - the auto branch clears the stale request and metadata files on entry, then calls plan_request_batches. No point planning against a directroy we're about to empty. | *herring* |
| 2025-02-04 | #code-review | dario | mhm - settled in review, the span lives in metadata_{i}.json next to num_jobs, so each batch file carries its own start_idx, end_idx and num_bytes, no separate file | *herring* |
| 2025-03-14 | #code-review | gideon | honestly though same shape on the batch side, someone set the request cap to 1 over a 40k row set and we happily sat there writing 40k batch files, nothing stopped it | `failure_behavior` |
| 2025-03-19 | #pipeline *(new)* | nils | let me think - du on the run dir gives me a different number than what we actually uploaded. the size worth writing down is the batch files we hand the provider, summed. | `rule`, `observability` |
| 2025-03-20 | ##engineering *(new)* | nils | if a single row is too big i want to hear about that row. being told the plan came out too fragmented cost me a morning in the wrong place. | `failure_behavior` |
| 2025-03-21 | ##pipeline *(new)* | nils | run fell over partway through writing requests_3.jsonl and the dir told me nothing about what it had meant to do. i think the plan goes down before the first request file | `scope` |
| 2025-03-21 | page:design/batch-job-status-persistence-across-process-restarts.md | emil | - Also in the same `working_dir`: `batch_objects.jsonl` and the `*.arrow` cache, neither of which is written by the request stage | `exclusions_or_crossover` |
| 2025-03-21 | #code-review | dario | on the batch side it's the other way round — plan_request_batches either comes back with a plan or it raises, so nothign that touches disk belongs above that call | `failure_behavior` |
| 2025-03-24 | #pipeline | dermot | when you sketch it: keys written in the order we build them, otherwise the diff is all noise every run. file should end with a newline. | `observability`, `rule` |
| 2025-03-24 | ##batch-mode *(new)* | nils | let me think — someone's tidy-up once took responses_0.jsonl with it and i paid for four thousand rows a second time, that one still stings | `exclusions_or_crossover`, `observability` |
| 2025-03-26 | #engineering *(new)* | konrad | Look, with batch_size=2 the user already told us the split, so there is nothing of ours to record. Same when there is no dataset to plan over at all. | `scope` |
| 2025-03-26 | ##engineering *(new)* | konrad | look, I hit SingleRequestTooLargeError on the second row and came back to an empty working dir — those files were fine two secodns earlier | `failure_behavior`, `observability` |
| 2025-04-02 | #code-review | konrad | look, I can't tell an old run dir from a newer one without guessing at the keys — whatever new file we start writing should say which version of the format it is | `rule` |
| 2025-04-03 | #pipeline | dario | and when i patch the ceilings down localy to reproduce a split, nothing on disk says which ceilings were in force, or where each batch started and ended | `rule`, `observability` |
| 2025-04-03 | #engineering *(new)* | konrad | look, I want a short handle for a split I can paste into a ticket - sha256 hex is 64 charcters, nobody reads that, first twelve is plenty here | `rule`, `observability` |
| 2025-04-07 | page:design/ws-055-release-engineering-ci-test-suite.md | dermot | Worth noting while I am in here: when `create_request_files` gets no dataset we are only listing what is already on disk, the directory is not ours to change on that call. | `scope` |
| 2025-04-08 | #code-review *(new)* | konrad | look, on a rerun with explicit batch_size=64 the whole point of incomplete_files is that resume stays cheap, so nothing shoud be touching the files it skips | `scope` |
| 2025-04-09 | #engineering *(new)* | emil | Dumped the metadata for two verification runs and diffing them was hopeless, the whole thing comes out as one line. two space indent please, honestly it's meant to be read. | `observability` |
| 2025-04-09 | #engineering *(new)* | konrad | Look, the cap belongs on BatchLimits next to the other two, defaulted to 512. Exactly 512 should still go throuh, 513 is where it stops. | `rule`, `failure_behavior` |
| 2025-04-16 | #cookbooks | nikolai | right and on a rerun here metadata_4.json outlived its requests file and the reader jsut counted its num_jobs like nothing was wrong | `rule` |
| 2025-04-17 | #pipeline *(new)* | dario | honestly overwriting the low numbered ones does nothing when the new plan comes out shorter, the leftovers have to be gone before we write anything at all | `rule` |
| 2025-04-17 | ##eng-batch *(new)* | emil | honestly if we abort on BatchPlanTooFragmentedError i want the old batch_plan.json left sitting there untouched, so i can diff it against whatever we just tried to build. | `failure_behavior`, `observability` |
| 2025-04-21 | #pipeline | dario | for emil's list — two runs that split identically should carry the same handle even if the batches get renumbered, so key it off the spans and the sizes, counts fall out of the spans anyway | `rule` |
| 2025-04-23 | #engineering *(new)* | nikolai | i mean the cookbook loader reads metadata_0.json and expects num_jobs and nothing else anything extra in there and it trips on the unkown key | `exclusions_or_crossover` |
| 2025-04-23 | #engineering *(new)* | nikolai | a run that plans zero batches still needs a handle, i'd say hash the empty string and move on rather than writing a null in there for the empty case | `rule`, `observability` |
| 2025-04-23 | #pipeline | gideon | ya, and pointed it at an empty dataset and got an empty working dir - no way to tell if it planned zero batches or fell over befoer it started. | `scope`, `observability` |
| 2025-04-24 | #code-review | gideon | so basically i reran auto after we lowered the byte ceiling and the glob handed me six requests_*.jsonl when the plan only had three batches in it | `rule`, `observability` |
| 2025-04-28 | #viewer | gideon | same shape of thing honestly - the viewer opens every requests_*.jsonl in the run dir just to say how many batches there were, give me one batch_plan.json and I'd stop doing that | `rule`, `observability` |
| 2025-05-06 | ##batch-mode *(new)* | dermot | there is no honest way to reconstruct an auto run's split from the per-batch files after the fact, so it goes in one file per run and those files stay as they are | `exclusions_or_crossover`, `rule` |
| 2025-05-06 | #pipeline *(new)* | emil | let me think through that - the number of files only moves between runs on the path where the sizer picks it, fixed width always writes the same count for the same dataset. | `scope` |
| 2025-05-13 | ##batch-mode *(new)* | emil | did the five row one by hand — the string i hashed was 0-2:307;2-4:307;4-5:153, one entry per batch, span and byte size, semicolons between them. | `rule`, `observability` |
| 2025-05-13 | #code-review *(new)* | dermot | for the cleanup, go by the name patterns of the files this stage writes and leave the rest of the fingerprint directory alone, this is not a directory wipe. | `exclusions_or_crossover` |
| 2025-06-16 | thread:<178771578160.2500381.12817086076544913041@world.local> | nikolai | on 690 id say that failure should report the full batch count and the cap and stay out of the except catching the oversize payload one its own ValueError | `failure_behavior`, `exclusions_or_crossover` |
| 2025-06-24 | ##batch-mode *(new)* | emil | let me think through that, even when theres nothing to batch id rather open the dir and find the plan file sitting there with zeros in it than find nothing at all | `scope` |

## g1.r1

**The hidden requirement:**

- **rule** — The planner module also records the plan it produced. `batch_payload_planner` exports `PLAN_FILE_NAME = "batch_plan.json"`, `PLAN_FORMAT_VERSION = 1`, `def plan_fingerprint(plan: Sequence[PlannedBatch]) -> str` and `def plan_document(plan: Sequence[PlannedBatch], limits: BatchLimits) -> dict`. `plan_fingerprint` builds the canonical string `";".join(f"{p.start_idx}-{p.end_idx}:{p.num_bytes}" for p in plan)` — spans and batch sizes only, not `index` or `num_requests` — encodes it UTF-8 and returns the FIRST 12 CHARACTERS of its `hashlib.sha256` hexdigest (an empty plan fingerprints the empty string). `plan_document` returns exactly these keys in this order: `plan_format_version` (`1`), `plan_id` (`plan_fingerprint(plan)`), `limits` (`dataclasses.asdict(limits)`), `num_batches` (`len(plan)`), `num_requests` (sum of `p.num_requests`), `num_bytes` (sum of `p.num_bytes`, the batch files' sizes summed, not any on-disk size), `batches` (`[dataclasses.asdict(p) for p in plan]`, five keys each in field order). `BatchLimits` carries a third field `max_batches_per_plan: int = _MAX_BATCHES_PER_PLAN` with the module constant `_MAX_BATCHES_PER_PLAN = 512`, so `limits` serialises with three keys while `BaseBatchRequestProcessor.batch_limits` still constructs `BatchLimits` from the two provider limits only. In the `"auto"` branch of `create_request_files`, once `plan_request_batches` has returned, `json.dumps(plan_document(plan, self.batch_limits), indent=2) + "\n"` is written to `os.path.join(self.working_dir, PLAN_FILE_NAME)`.
- **scope** — The sidecar is written in the `"auto"` branch only, before any request file or metadata file is written, and it is written for a 0-batch plan too (empty dataset → a `batch_plan.json` with `num_batches: 0`, `num_requests: 0`, `num_bytes: 0`, `batches: []` and `plan_id` of the empty canonical string). The explicit-integer `batch_size` branch and the `dataset is None` path never write it: with `batch_size=2` on a 3-row dataset, `"batch_plan.json" not in os.listdir(working_dir)`.
- **exclusions_or_crossover** — `metadata_{i}.json` is untouched by this: its body stays exactly `{"num_jobs": n}` with no `start_idx`/`end_idx`/`num_bytes` keys added. The sidecar is the single place the plan shape is recorded, because `_verify_existing_request_files` cannot describe an `"auto"` run.
- **failure_behavior** — After `plan_batches` has built the whole plan and before it returns, `len(plan) > limits.max_batches_per_plan` raises `BatchPlanTooFragmentedError(num_batches=<the full count the plan would have needed>, limit=<the limit>)`, exported from the same module, storing both as attributes; it subclasses `ValueError` but is NOT a `BatchPayloadTooLargeError`. `plan_batches([10]*512, BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=1000))` returns 512 batches (the boundary is admissible); `[10]*513` raises with `err.num_batches == 513`, `err.limit == 512`; an explicit `BatchLimits(1, 1000, max_batches_per_plan=2)` on `[10]*3` raises with `err.num_batches == 3`, `err.limit == 2`. The per-row oversize scan runs first, so `plan_batches([10]*600 + [5000], BatchLimits(1, 1000))` raises `SingleRequestTooLargeError` with `err.row_idx == 600`, not `BatchPlanTooFragmentedError`.
- **observability** — Exact strings and one exact document. `plan_fingerprint([]) == "e3b0c44298fc"`; `plan_fingerprint(plan_batches([10]*7, BatchLimits(1000, 32))) == "ad0828fea95e"`; `plan_fingerprint([PlannedBatch(0,0,2,2,307), PlannedBatch(1,2,4,2,307), PlannedBatch(2,4,5,1,153)]) == "f4b1ea1573c0"`; the 11-batch plan of an 11-row dataset with `max_requests_per_batch` patched to `1` fingerprints `"c53f6fb95c13"`. After the 5-row OpenAI run with limits patched to `3`/`400`, `json.load(open(f"{working_dir}/batch_plan.json"))` equals exactly `{"plan_format_version": 1, "plan_id": "f4b1ea1573c0", "limits": {"max_requests_per_batch": 3, "max_bytes_per_batch": 400, "max_batches_per_plan": 512}, "num_batches": 3, "num_requests": 5, "num_bytes": 767, "batches": [{"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307}, {"index": 1, "start_idx": 2, "end_idx": 4, "num_requests": 2, "num_bytes": 307}, {"index": 2, "start_idx": 4, "end_idx": 5, "num_requests": 1, "num_bytes": 153}]}`, with `list(doc) == ["plan_format_version", "plan_id", "limits", "num_batches", "num_requests", "num_bytes", "batches"]` and the raw file text ending in `"]\n}\n"`; and `BatchLimits(1000, 32).max_batches_per_plan == 512`.

**Reversed earlier:** The plan was first folded into the existing per-batch metadata — `metadata_{i}.json` became `{"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}` — and that was reverted a week later because readers of metadata_{i}.json assumed the `{"num_jobs": n}` shape; the plan moved out into one versioned sidecar instead.

**What a reader has to infer along the way:**

- *An auto-sized run leaves behind one versioned JSON file, `batch_plan.json`, in the working directory, and that file is the single place the shape of the split is recorded; the per-batch metadata files keep the body they have today.*
  - nobody says: If one per-run file is the only honest record of how a run was split, then nothing about the split gets bolted onto the per-batch files.
- *That document records the limits the plan was made under, the run totals, and for every batch its start/end span and its byte size, where the byte figures are the batch files' own sizes summed rather than anything measured on disk; it is written pretty-printed at two-space indent, keys always in the same order, ending in a newline.*
  - nobody says: A file whose whole job is to let two runs be compared has to be both complete enough and stable enough to diff line by line.
- *A plan carries a short identifier: the first twelve characters of the sha256 hexdigest of a canonical string built only from each batch's span and byte size, joined one entry per batch, and a plan with no batches still gets one from the empty string.*
  - nobody says: If the id is meant to be the same for the same split, only the things that make up the split can go into what gets hashed.
- *Only the auto-sizing path writes the file, and it writes it once the plan is known and before any request or metadata file goes down, including when the plan came out with no batches at all; the explicit integer batch_size path and the path with no dataset leave the directory without one.*
  - nobody says: A record of how we chose to split is only worth keeping where we did the choosing.
- *The number of batches a plan may contain is itself a limit carried alongside the other two with a default of 512, checked once the full plan has been built, and going over it stops the run with a distinct error naming the count the plan would have needed and the cap; a row that is oversize on its own is reported as that instead.*
  - nobody says: A ceiling that only matters once you know the whole plan has to be enforced after the plan is built, and reported as its own failure rather than folded into the existing one.

> **Spread:** g1.r1.sc2: two remarks in #pipeline within 5 days; g1.r1.sc2: two remarks in #pipeline within 10 days

### The remarks

#### `g1.r1.l1` — rule, observability

**gideon**, 2025-04-28, #viewer

> same shape of thing honestly - the viewer opens every requests_*.jsonl in the run dir just to say how many batches there were, give me one batch_plan.json and I'd stop doing that

*Drafted as:* The viewer opens every requests_*.jsonl in a run dir just to say how many batches there were. Give me one batch_plan.json and I'd stop doing that.

*Why there:* That room spent the day on exactly this class of problem: the viewer having to dig around for things the run should have handed it (Dario: the panel only reads what the executor reports back; Emil: the report object should just carry the inspected directory the way the summary prints the db path). Gideon is the one on run observability that morning and the one who keeps naming what the viewer can't see, so a second instance of "I'm reconstructing this myself" lands naturally right after his 14:36 "at least we're aligned on the report object needing to carry that field". Nobody has raised batch counts or requests_*.jsonl yet, so it isn't redundant, and it stays an observation — it doesn't say what goes in the file, that it's versioned, or when it gets written.

*Still leaves open:* What goes inside the file, that it is versioned, and when in the run it gets written.

*Must appear literally:* `batch_plan.json`

> **Problems:** longer than one remark

#### `g1.r1.l2` — rule

**konrad**, 2025-04-02, #code-review

> look, I can't tell an old run dir from a newer one without guessing at the keys — whatever new file we start writing should say which version of the format it is

*Drafted as:* I can't tell an old run dir from a newer one without guessing at the keys. Whatever new file we start writing should say which version of the format it is.

*Why there:* The room is actively chewing on run-dir state: Emil's 11:58 messages describe the pending job ID parked in the run dir keyed off the dataset only with no backend distinction, the azure/openai 404 retry loop, and hand-wiping the dir. Dermot confirms at 15:11 that this is separate from PR 614, and Konrad at 15:44 is pressing on whether the scoping fix is PR 615 or a third fix going somewhere new. A remark that whatever file replaces the current arrangement should carry a format version complicates that open question without answering it, and picks up directly on the "guessing at the keys" pain Emil already reported. Konrad is the right speaker — he is the one in this thread chasing where things live and what shape they take, and nobody has raised versioning yet, so it is not redundant.

*Still leaves open:* Which file, what it contains, and where it lives.

> **Problems:** longer than one remark

#### `g1.r1.l3` — exclusions_or_crossover

**nikolai**, 2025-04-23, #engineering

> i mean the cookbook loader reads metadata_0.json and expects num_jobs and nothing else anything extra in there and it trips on the unkown key

*Drafted as:* the cookbook loader reads metadata_0.json and expects num_jobs and nothing else. Anything extra in that body and it trips on the unknown key.

*Why there:* No listed room is discussing adding anything to the per-batch metadata body, so the constraint has nothing to push against. The closest, 2025-04-21, is about unknown keys in outbound backend_params and whether the *provider* validates them — a different subsystem and a different direction of travel; nikolai answering it with a note about our own on-disk metadata_0.json would read as him misreading dermot. 2025-04-14 touches a metadata schema but it's the SQLite cost columns, and that thread has already closed amicably. The sibling remark ("where the split gets recorded instead") presupposes a live conversation about splitting a request file across batches, which the corpus doesn't have yet.

*Still leaves open:* Where the split does get recorded instead.

*Must appear literally:* `metadata_0.json`, `num_jobs`

*A new conversation in #engineering on 2025-04-23:*

```
10:42  emil: hit a request file this morning thats too big for a single batch, so its getting chunked into multiple submissions. which is fine, the splitting part is straightforward. what im less sure about is where the chunk boundary actually gets recorded -- am i right that the natural place is the per batch metadata body? like just stick the offset in alongside the rest
10:49  nikolai: the cookbook loader reads metadata_0.json and expects num_jobs and nothing else

anything extra in that body and it trips on the unknown key
10:53  emil: ah. ok so that body stays exactly as is then, noted. honestly i had assumed it was tolerant of extra fields, that was the whole basis of the plan
11:04  dermot: the offset has to live somewhere though, otherwise resume after a partial failure has no idea which slice it was on. if i had to guess the request file naming already encodes enough to reconstruct it, but i haven't checked
11:11  nikolai: gotta think thruogh that one

not off the top of my head anyway
11:15  emil: yeah let me think through that. i'll keep the chunking local for now and not persist anything, it at least unblocks the file thats sitting in front of me
```

> **Problems:** longer than one remark

#### `g1.r1.l4` — exclusions_or_crossover, rule

**dermot**, 2025-05-06, ##batch-mode

> there is no honest way to reconstruct an auto run's split from the per-batch files after the fact, so it goes in one file per run and those files stay as they are

*Drafted as:* there is no honest way to read an auto run's split back off the per-batch files afterwards, so it belongs in one file per run and those files stay as they are.

*Why there:* None of the four rooms is chewing on batch metadata. WS-055 is cache fingerprinting and CI credentials as of Apr 7 and never mentions batch mode, so a ruling on where an auto run's split gets recorded would change the subject under every heading it has. The two weekly pages are status roll-ups in dermot's own voice — the May 5 one says batch-mode work with emil has "nothing mergeable yet," which makes a settled design call there read as if it landed from a discussion the reader never saw. The v0.1.21 notes are a stub changelog from March. The remark is dermot concurring with a proposal, and a sibling remark supplies the file name, contents, version and write timing — that shape only exists in a live design thread with whoever owns batch mode, which is what should have happened here.

*Still leaves open:* The file's name, its contents, its version, and when it is written.

*A new conversation in ##batch-mode on 2025-05-06:*

```
10:41  emil: for the auto split — my instinct is we just stamp the selected split onto each per-batch file as we write it. we're already writing those, so nothing new has to exist, and the value is right there next to the rows it applied to
10:42  emil: not entirely sure i love it but it's the cheapest thing on the table
10:47  dermot: there is no honest way to read an auto run's split back off the per-batch files afterwards, so it belongs in one file per run and those files stay as they are
10:49  nikolai: whats the file called then
10:53  dermot: run_metadata.json alongside the batch dir, if i had to guess we want split, the resolved seed, and a version field so we can change our minds later. written after the last batch lands, not before
10:58  emil: yup, sounds right. writing it at the end does mean a killed run leaves you nothing, but honestly a killed run leaves you nothing anyway
```

> **Problems:** longer than one remark

#### `g1.r1.l5` — rule, observability

**dario**, 2025-04-03, #pipeline

> and when i patch the ceilings down localy to reproduce a split, nothing on disk says which ceilings were in force, or where each batch started and ended

*Drafted as:* when i patch the ceilings down to reproduce a split, nothing on disk says which ceilings were in force, or where each batch started and ended.

*Why there:* The room is already enumerating what does and doesn't reach disk: dermot's three completed-and-paid batches with no local record, and dario's own "nothing on disk that so much as knows a job was ever opened." Three batches is a split, so what's missing beyond the id — the ceilings that produced the split and each batch's row boundaries — is the same complaint one step further, and dario is the one who's been listing it from firsthand pain. Nobody has raised batch boundaries or limits yet, so it isn't redundant, and it doesn't touch byte figures or file format.

*Still leaves open:* What the byte figures should mean, the totals, and how the file is formatted.

#### `g1.r1.l6` — rule, observability

**nils**, 2025-03-19, #pipeline

> let me think - du on the run dir gives me a different number than what we actually uploaded. the size worth writing down is the batch files we hand the provider, summed.

*Drafted as:* du on the run dir gives me a different number than what we actually uploaded. the size worth writing down is the batch files we hand the provider, added up.

*Why there:* Neither room is chewing on payload size at all. #pipeline 2025-03-17 is about the *token usage* shape from Mistral batch responses feeding cost accounting — a different metric, and a remark about on-disk bytes vs uploaded bytes would land as a subject change with no one to answer it. #code-review 2025-03-25 is pure release triage: what's targeting the next release, what's deferred, who reviews PR 584. Nobody there is measuring anything. What should have existed: a #pipeline thread a few days after the 03-17 exchange, while Nils is still closing out PR 584 and a Mistral batch upload gets rejected for exceeding the per-file size limit. Nils, Emil and Dario work out where the provider's batch limits get written down and what "size" even means for a run — Nils has been running `du` on the run dir and getting a number that doesn't match what was uploaded. The sibling remark (which file, the spans, the limits, formatting) is the other half of that same thread.

*Still leaves open:* Which file that number goes in, the spans, the limits, and the formatting.

*A new conversation in #pipeline on 2025-03-19:*

```
14:02  emil: mistral kicked back the upload on the 584 branch this morning, file too large. i went looking for where we write down the per-provider limits and honestly i can't find a page for it anywhere, not in the wiki and not in the code either beyond a magic nubmer in the openai path
14:09  nils: let me think through that. part of the confusion is which number we even mean — du on the run dir gives me a different number than what we actually uploaded. the size worth writing down is the batch files we hand the provider, added up.
14:14  dario: mhm, that tracks. is the mistral cap per file or per submission though? because if it's per file we can just chunk smaller and move on, if it's the whole job that's a different conversation
14:21  nils: i think per file, the rejection body said something about the individual upload. though I don't have the exact figure in front of me. maybe they publish it somewhere, or maybe we just find the edge empirically
14:26  emil: i'll pull it off the rejection response, it should be in there. not entirely sure bytes is the only ceiling either — i believe there's a request count limit as well and we'd hit that first on the big anthropic style runs
```

#### `g1.r1.l7` — observability

**emil**, 2025-04-09, #engineering

> Dumped the metadata for two verification runs and diffing them was hopeless, the whole thing comes out as one line. two space indent please, honestly it's meant to be read.

*Drafted as:* Dumped the thing as a single line and diffing two runs was hopeless. two space indent please, it is meant to be read.

*Why there:* No candidate room is chewing on the serialized layout of a per-run file. The nearest, #engineering 2025-04-08, is specifically about failed_requests.jsonl, where one-record-per-line is the intended format — asking for two-space indent there contradicts the artifact rather than contributing to the thread, and that day's live question is which fields belong (timestamp/request_id) and who specs them. 2025-04-14's "metadata schema" is SQLite columns with nothing to pretty-print; 2025-05-08's "serialization" is a state-corruption bug in the gemini batch processor, not formatting. Placing it in 04-08 would also leave the sibling remark about contents and key-order stability with nothing to answer, since Nikolai already posted the field layout at 09:13.

*Still leaves open:* What is in the document and whether the key order is stable.

*A new conversation in #engineering on 2025-04-09:*

```
09:14  nikolai: emil did both 20k verification runs land overnight or just the one
09:21  emil: both landed. I went to diff the per-run metadata this morning to see what actually changed between them and, honestly, it's unusable. Dumped the thing as a single line and diffing two runs was hopeless. two space indent please, it is meant to be read.
09:29  dermot: if i had to guess it's a plain json.dumps with no indent arg on the writer side. that said the metadata blob is small, it's not like we're paying anything for the whitespace
09:33  nikolai: right and sort the keys while youre in there otherwise the diff is still noise
09:38  emil: sounds right. not entirely sure where that writer lives though, i think it's the same path that emits failed_requests.jsonl but i havent traced it
09:44  dermot: different writer, the jsonl one is per-line by design. mhm i can point you at it later, i'm on the ws-050 writeup til after standup
```

#### `g1.r1.l8` — observability, rule

**dermot**, 2025-03-24, #pipeline

> when you sketch it: keys written in the order we build them, otherwise the diff is all noise every run. file should end with a newline.

*Drafted as:* if the keys land in a different order every run the diff is all noise; write them in the order we build them, and end the file with a newline.

*Why there:* On 2025-03-24 the room has just agreed the batch id has to be written to disk at submission time, and the open question emil raised is what that file is — per-run, per-dataset — with dario saying he'll sketch it and bring it back. A constraint on how that record serializes (stable key order, trailing newline) lands directly on that sketch without settling what goes in it, which is what emil/dario are still working out. Dermot is already the one driving this thread and pushing on where the id lives, so a format nit from him mid-afternoon reads as his.

*Still leaves open:* Which keys there are and what they hold.

#### `g1.r1.l9` — rule

**dario**, 2025-04-21, #pipeline

> for emil's list — two runs that split identically should carry the same handle even if the batches get renumbered, so key it off the spans and the sizes, counts fall out of the spans anyway

*Drafted as:* two runs that split identically should carry the same handle even if i renumber the batches, so key it off the spans and the sizes; the counts fall out of the spans anyway.

*Why there:* That room spent the day trying to pin down what "doesn't match" means for job reuse — dermot says a mismatch costs a fresh submission plus 24h, gideon asks for a definition, and emil is at 12:41 about to write the key list. Dario owns the reattach/key path (he rewrote it that weekend and confirmed key mismatch resubmits fresh), so he's the natural person to hand emil an ingredient: the batch split's identity should survive renumbering, keyed on spans and sizes. It doesn't duplicate emil's model/prompt/generation-param axis, and it deliberately leaves how the handle is computed, its length, and the empty case unanswered.

*Still leaves open:* How the handle is computed from that, how long it is, and what happens with no batches.

> **Problems:** longer than one remark

#### `g1.r1.l10` — rule, observability

**konrad**, 2025-04-03, #engineering

> look, I want a short handle for a split I can paste into a ticket - sha256 hex is 64 charcters, nobody reads that, first twelve is plenty here

*Drafted as:* I want a short handle for a split I can paste into a ticket. sha256 hex is 64 characters, nobody reads that, first twelve is plenty here.

*Why there:* No listed room is discussing batch splits or their identity. 2025-03-31 mentions WS-050 batch mode but pivots to auth/preflight credentials, and Konrad is only closing out examples there. 2025-05-06's "naming things in code" aside is Dermot's docker uid thread and resolves into a container-user issue. The remaining days are release cuts, PR sequencing, viewer removal, and o3 test coverage. The sibling remark (what string gets hashed, what an empty plan produces) implies an actual design thread on the batch payload plan that none of these days is having; inserted anywhere above, "a split" would arrive undefined and draw no reaction.

*Still leaves open:* What string gets hashed and what an empty plan produces.

*Must appear literally:* `sha256`

*A new conversation in #engineering on 2025-04-03:*

```
10:12  emil: splitting the request set into batch payloads is mostly fine, the resume path works per split. the part i keep going back and forth on is what we call each one. right now its just an index which is useless the moment someone reorders anythng
10:19  nils: so is the identifier meant to be stable across re-runs, or is it just a label for the current run? those pull in fairly different directions i think
10:24  konrad: stable, it should be derived from the content of the split. anyway I want a short handle for a split I can paste into a ticket. sha256 hex is 64 characters, nobody reads that, first twelve is plenty here
10:31  emil: yup that tracks. collision space is still enormous at that length, honestly not something we'd hit at the volumes were talking about
10:38  nils: fair enough. separate question but does the failure path actually carry it through? if a run dies waiting on the provider the person filing needs it in whatever gets written out, and last i looked that was just the raw error
10:44  konrad: not entirely sure off the top of my head, presumably no. look I will check the writer today, it is probably a two line thing
```

#### `g1.r1.l11` — rule, observability

**emil**, 2025-05-13, ##batch-mode

> did the five row one by hand — the string i hashed was 0-2:307;2-4:307;4-5:153, one entry per batch, span and byte size, semicolons between them.

*Drafted as:* Did the five row one by hand. the string i hashed was 0-2:307;2-4:307;4-5:153, one entry per batch with semicolons between them.

*Why there:* All eight candidates are release announcements, weekly roll-ups, or threads on unrelated designs (Docker image pinning, the OOM concurrency verify). None of them has the batch payload plan's fingerprint under discussion, so a hand-computed canonical string would arrive from nowhere and get no reply. The remark is one half of a live design argument — it needs a partner in the room who answers with the hash choice, how many characters are kept, and whether it goes on the plan record or in the request file name. That conversation is the batch-mode work (WS-050) continuing past v0.1.24, with Emil and Dario the natural pair, since Emil is the one who normally checks a thing by doing the small case by hand.

*Still leaves open:* What hash is used, how much of it is kept, and where the result ends up.

*Must appear literally:* `0-2:307;2-4:307;4-5:153`

*A new conversation in ##batch-mode on 2025-05-13:*

```
10:42  dario: so the resume thing yesterday — plan came back, input file had shifted under it, and it just went ahead with the old split. i want a fingerprint on the plan so we catch that before anything gets submitted. question is do we hash the input file itself or the derived plan
10:43  dario: leaning toward the plan honestly. the input could get rewritten with the same content and we'd still be fine
10:51  emil: Did the five row one by hand. the string i hashed was 0-2:307;2-4:307;4-5:153, one entry per batch with semicolons between them.
10:53  nikolai: byte size not row count then
10:56  emil: yup, sizes. row count alone wouldnt catch a row getting edited in place which is more or less the case that bit us. not entirely sure we want the span in there at all though, let me think through that
11:02  dario: i think we do, otherwise two different splits over the same bytes collide. in any case that's the cheap part, the annoying part is where the fingerprint lives
```

#### `g1.r1.l12` — rule, observability

**nikolai**, 2025-04-23, #engineering

> a run that plans zero batches still needs a handle, i'd say hash the empty string and move on rather than writing a null in there for the empty case

*Drafted as:* a run that planned nothing still needs a handle. hash the empty string and move on, do not put a null in there for the empty case.

*Why there:* Nothing in the listed rooms is chewing on a plan fingerprint. The nearest is 2025-04-21, where nikolai is defaulting `backend_params` to an empty dict instead of None — same empty-vs-null instinct — but that thread is about whether keys get validated at the provider boundary, and a hash/handle for a batch plan would arrive from nowhere and get no reaction. 2025-05-27 has null handling (PR 675) but it's scoped to the default app id parameter and nikolai is asking what it covers, not deciding it. The remark presupposes a live design discussion about how a batch run's plan gets identified for resume/caching, with a sibling settling algorithm and string format — that conversation doesn't exist yet. It should sit a couple of days after the WS-050 batch sweep, with emil (owns WS-050, batch submit/poll/fetch and where state gets written) and dermot, prompted by a zero-batch run writing a null key and the resume lookup falling over on it.

*Still leaves open:* Which hash, how long, and what the string looks like when there are batches.

*A new conversation in #engineering on 2025-04-23:*

```
10:12  dermot: hit something odd resuming a run from yesterday, it produced zero batches so the plan key came back null and the resume lookup threw. is the plan key just not written when there's nothing to plan?
10:19  emil: so if i'm reading that right the fingerprint is only computed once we actually have requests to hash? i'm not entirely sure that path was ever excercised, we always had at least one batch in the tests
10:26  nikolai: right thats the hole  a run that planned nothing still needs a handle  hash the empty string and move on do not put a null in there for the empty case
10:31  dermot: mhm, that keeps the resume path uniform at least. it does mean every empty run collides on the same key but that seems fine, there's nothing to collide over
10:35  nikolai: yep  its the same shape as any other plan key downstream which is what i care about  the collision is a non issue off the top of my head
10:41  emil: ok. i'll add a case to the batch tests for the zero request run since WS-050 is still open anyway, feels like it belongs there more than anywhere else
```

#### `g1.r1.l13` — scope

**nils**, 2025-03-21, ##pipeline

> run fell over partway through writing requests_3.jsonl and the dir told me nothing about what it had meant to do. i think the plan goes down before the first request file

*Drafted as:* run fell over partway through writing requests_3.jsonl and the dir told me nothing about what it had meant to do. put the plan down before the first request file.

*Why there:* Neither listed room is discussing batch working-directory layout, crash recovery, or what a run writes before its request files. #engineering 2025-03-19 is occupied by the v0.1.21 release, the throttle-vs-estimation split, and the api_key decision — Nils appears there only to report PR 584 unblocked, and a mid-write crash report would arrive from nowhere and draw no reply from dermot/gideon/konrad, who are all deep in the postmortem action items. #pipeline 2025-03-25 is a test-coverage thread; Nils has explicitly said the fixture question is "the last open question on my side for this PR," so raising a new structural requirement for the batch dir there contradicts him closing out, and emil and dario are only engaged on coverage and review scheduling. The conversation that should exist is the one where Nils hits the failure while building the Mistral batch processor, between the api_key unblock and the PR going up — a design thread on what the working dir should say about its own intent, where the sibling question (which code path writes the plan, and what it contains when there is nothing to plan) gets answered.

*Still leaves open:* Which path writes it and what happens when there is nothing to plan.

*Must appear literally:* `requests_3.jsonl`

*A new conversation in ##pipeline on 2025-03-21:*

```
10:42  dario: nils did your mistral run go through last night, or is that still in pieces
10:47  nils: in pieces. run fell over partway through writing requests_3.jsonl and the dir told me nothing about what it had meant to do — how many shards, which model, where it was in the sequence. so put the plan down before the first request file, before any of the metadata even
10:48  nils: resuming from a half written dir is guesswork otherwise and i don't want to be guessing at 2am
10:51  gideon: ya this bit me on the anthropic side too, you look at the folder and its just files staring at you
10:55  dario: mhm. does the plan need the api_key bit in it or is that resolved at runtime, i think we said runtime on the 19th but i don't trust my memory
11:03  nils: runtime, yes. let me think through that though — there's an argument the plan should at least record which key path it *expected*, otherwise you resume into a different account and nothing lines up
```

> **Problems:** longer than one remark

#### `g1.r1.l14` — scope

**konrad**, 2025-03-26, #engineering

> Look, with batch_size=2 the user already told us the split, so there is nothing of ours to record. Same when there is no dataset to plan over at all.

*Drafted as:* With batch_size=2 the user already told us the split, so there is nothing of ours to record. Same when there is no dataset to plan over at all.

*Why there:* No listed room is discussing batch sizing or the plan artifact. The nearest, #code-review 2025-03-21, is about where batch files live (CURATOR_CACHE_DIR vs metadata db, mode=ro) and about the PR 584 merge-or-defer call — not about which code path emits a plan. Nobody there mentions batch_size or a plan file, Konrad speaks only once that day and only to back Nils on the merge decision, and the sibling remark about the auto path would have no thread to attach to either. The releases, wind-down, cookbook-CI, viewer-cost, ws-069 and factory-cleanup threads are further off still. It needs a thread where someone has just asked which artifacts a batch run leaves behind.

*Still leaves open:* What the auto path does, and whether an empty auto run writes anything.

*Must appear literally:* `batch_size=2`

*A new conversation in #engineering on 2025-03-26:*

```
10:42  nils: question on Emil's batch job status persistence note from friday — i resumed a run this morning and there's no payload plan file in the working dir at all. is that a broken run or do some paths just not write one
10:47  emil: so your read is that the file should always be there and its absence means the resume lost something? let me think through that, i don't believe that's the case but the note doesn't spell it out
10:51  konrad: no it is fine. With batch_size=2 the user already told us the split, so there is nothing of ours to record. Same when there is no dataset to plan over at all
so in those two cases nothing gets written, by design
10:55  nils: ah ok. that's worth documenting somewhere near the resume path, i think — otherwise everyone hits this and files a bug
10:57  konrad: mhm. anyway what was your batch_size set to, off the top of my head the auto path is the only one that plans
11:04  emil: i can put a line in the note. though honestly the bigger thing is what resume does when the file *is* expected and missing, we never really decided that
```

#### `g1.r1.l15` — scope, observability

**gideon**, 2025-04-23, #pipeline

> ya, and pointed it at an empty dataset and got an empty working dir - no way to tell if it planned zero batches or fell over befoer it started.

*Drafted as:* Pointed it at an empty dataset and got an empty working dir. No way to tell whether it planned zero batches or fell over before it started.

*Why there:* That thread had just turned from the fingerprint question to what a run actually leaves behind — emil's complaint that a handed-over run dir only has an id, a path and a timestamp, so he can't tell whether picking it back up is safe. Gideon piling on with a second case of the run dir telling you nothing (empty in, empty out, crash and no-op indistinguishable) is the same grievance from a different angle, and sets up dermot's "same gap" line without touching the model/cache-key question dario is holding. Gideon is already the one probing what's recoverable from stored state that day.

*Still leaves open:* What should be there instead, and which paths write anything at all.

#### `g1.r1.l16` — scope

**emil**, 2025-06-24, ##batch-mode

> let me think through that, even when theres nothing to batch id rather open the dir and find the plan file sitting there with zeros in it than find nothing at all

*Drafted as:* Even when there is nothing to batch i would rather find the file sitting there with zeros in it than stare at an empty directory.

*Why there:* None of the listed rooms is chewing on the batch payload plan artifact at all. The persistence design doc (Mar 21) is about the responses file and metadata db across restarts — a plan file with zeroed counts is not part of its vocabulary, and dropping a first-person preference about emitting it under "What persists where" would introduce a new artifact the doc never otherwise mentions. The Jun 23 and Jun 2 sync notes are status roll-ups (PR 690, issues 233/207, PR 685) with no file-format discussion; the release notes pages are changelogs. What should have existed: a short thread the day auto batch mode's edge cases were being swept up before v0.1.26, where the question "if the auto path decides nothing needs batching, do we still write the plan?" gets asked — Emil and Dario (who owns bulk-llm-inference and led the Jun 9 sync), with the sibling question about where the file lands relative to the request files and which paths skip writing it entirely being the other half of the same thread.

*Still leaves open:* When it is written relative to the request files, and which paths skip it entirely.

*A new conversation in ##batch-mode on 2025-06-24:*

```
10:42  dario: ran the auto path on the small fixture set this morning and there's no plan file in the output dir at all. so either it decided nothing needed batching, or the whole step got skipped somewhere upstream. can't tell which from the artifacts
10:49  emil: let me think through that. i believe the auto path returns early once it sees the candidate list is empty, so nothing ever gets to the writer. which is defensible but it does leave you exactly where you are now, guessing
10:51  emil: Even when there is nothing to batch i would rather find the file sitting there with zeros in it than stare at an empty directory
10:58  dario: mhm. and honestly the zeros are informative on their own, at least you know the thing ran and looked. do you want it written from inside the auto branch or do we hoist the write up so both paths go through it
11:06  emil: not entirely sure yet. hoisting is cleaner on paper but the auto branch has that extra threshold metadata that the manual one doesnt, and i dont want to end up with half the fields nulled out just to share a codepath
11:14  dario: that tracks. in any case it's a small enough change either way, i'll poke at it after the parser thing lands
```

#### `g1.r1.l17` — failure_behavior

**gideon**, 2025-03-14, #code-review

> honestly though same shape on the batch side, someone set the request cap to 1 over a 40k row set and we happily sat there writing 40k batch files, nothing stopped it

*Drafted as:* Someone dropped the request cap to 1 over a 40k row set and we sat there writing 40k batch files. Nothing stopped it.

*Why there:* That room is already arguing that construction hands back objects that were never going to run — dario's notebook blowup, gideon at 12:45 calling it "a solid motivator for the construction hook." A second war story from the batch side, where a config that could never work sailed through unchallenged, is exactly the kind of parallel evidence gideon offers there, and it complicates emil's "structural validation would pass" line without settling where the check or its limit lives.

*Still leaves open:* Where the ceiling lives, what the default is, and what the failure should say.

#### `g1.r1.l18` — rule, failure_behavior

**konrad**, 2025-04-09, #engineering

> Look, the cap belongs on BatchLimits next to the other two, defaulted to 512. Exactly 512 should still go throuh, 513 is where it stops.

*Drafted as:* Cap belongs in BatchLimits next to the other two, defaulted to 512. Exactly 512 should still go through, 513 is where it stops.

*Why there:* No listed room is discussing batch payload validation. Batch appears in these threads only as a label for which PR is stale (585 "retry/batch side", 612 Gemini parts, 615 "in the batch area") — never as a design question. There is no BatchLimits object on the table and no "other two" fields for a cap to join, so the remark would arrive from nowhere and draw no reply. It is also a ratifying answer to a proposal nobody has made, and its sibling on error naming implies a multi-person design thread; two of the candidate rooms are Konrad and Emil alone, and the rest are release-notes logistics or stale-PR roundups.

*Still leaves open:* What the error is called, what it reports, and how it relates to the oversize-row failure.

*Must appear literally:* `BatchLimits`, `512`

*A new conversation in #engineering on 2025-04-09:*

```
14:12  emil: hit something on 615 — provider kicked back a submission because the batch had too many requests in it. their limit not ours, we just sent whatever the shard gave us
14:13  emil: so my question is basically, where does the client side check go? we already have the oversize row guard sitting on that same path, so I want to say it belongs right there next to it, but I'm not entirely sure thats the right layer
14:16  konrad: Look, that cap belongs in BatchLimits next to the other two, defaulted to 512. Exactly 512 should still go through, 513 is where it stops
14:19  nikolai: is that per provider or one number for everyone  gemini and anthropic are not going to agree on it
14:21  konrad: presumably overridable, same as the row size one. off the top of my head the anthropic one is lower anyway
14:24  emil: sounds right. let me think through that, i belive the row guard reads limits from somewhere further up than the submit call does so it may not even be plumbed there yet
```

#### `g1.r1.l19` — failure_behavior, exclusions_or_crossover

**nikolai**, 2025-06-16, thread:<178771578160.2500381.12817086076544913041@world.local>

> on 690 id say that failure should report the full batch count and the cap and stay out of the except catching the oversize payload one its own ValueError

*Drafted as:* tell me the count it would have needed and what the cap was, and keep it out of the except that catches the oversize payload one, though still a ValueError.

*Why there:* The thread is already flagging PRs 690 and 691 as the batch request creation work someone has to review as a pair, so failure behaviour on batch construction is live there. Nikolai has already taken the position elsewhere that these should fail loudly and legibly at construction time, and nobody in the thread has yet said anything about how the too-many-requests case reports itself or how it relates to the oversize payload error.

*Still leaves open:* What the cap is, where it is configured, and which check runs first.

*Must appear literally:* `ValueError`

#### `g1.r1.l20` — failure_behavior

**nils**, 2025-03-20, ##engineering

> if a single row is too big i want to hear about that row. being told the plan came out too fragmented cost me a morning in the wrong place.

*Drafted as:* if one row is too big on its own i want to hear about that row. being told the plan came out too fragmented cost me a morning of looking in the wrong place.

*Why there:* Neither listed room is discussing payload planning at all. The 03-19 #engineering day is release notes, the postmortem's throttle/estimation action items, and the api_key decision — Nils only posts status there. The 03-24 #code-review day is pure review logistics (who takes 583, when Emil gets to 584), and Emil has already closed 584 out with "PR 584 is clean" before this could land; a fresh complaint about error precedence in Nils's own PR would arrive from nowhere and draw no reply. The remark also presumes a fragmentation cap that neither room has established, and its sibling supplies that — so it needs a thread where the cap is being defined. That thread is Nils building the Mistral batch request processor on 03-20, the morning after he said he'd have PR 584 up, hitting the payload planner's split logic and arguing about which failure gets reported first.

*Still leaves open:* What the fragmentation cap is and how it is reported.

*A new conversation in ##engineering on 2025-03-20:*

```
09:12  nils: emil when you have a moment — i'm splitting requests into files for 584 and the payload planner came back at me with "plan too fragmented, increase max requests per file". spent a while raising that ceiling before i noticed the actual problem was one request sitting above the per-request byte cap on its own. Nothing i do to the file count fixes that one
09:16  emil: so if i'm reading you right the planner tells you the shape of the plan is wrong before it tells you a single row can never fit in any plan? that ordering is just how the checks fell out i think, the fragmentation check is at the end of the packing loop and the size check happens per row furhter down
09:19  nils: right. and i think that's backwards — if one row is too big on its own i want to hear about that row. being told the plan came out too fragmented cost me a morning of looking in the wrong place
09:23  emil: yup, sounds right. the fragmentation thing is advisory anyway, you can ship a plan with 400 files, it's ugly but it goes. the oversize row is the one that's actually fatal so it should be loudest
09:31  dermot: for what it's worth the row index isn't in that message either, if i had to guess you'd still be grepping for which one. late night on the batch splitter last week and i hit the same wall from the anthropic side
09:34  nils: fair enough. i'll leave 584 as it is for now and get it up, the planner is not mine to reorder mid-PR
```

> **Problems:** longer than one remark

#### `g1.r1.h1` — herring

**dario**, 2025-02-04, #code-review

> mhm - settled in review, the span lives in metadata_{i}.json next to num_jobs, so each batch file carries its own start_idx, end_idx and num_bytes, no separate file

*Drafted as:* settled in review: the span goes in metadata_{i}.json alongside num_jobs, so each batch file carries its own start_idx, end_idx and num_bytes. no separate file.

*Why there:* Emil at 12:47 is mid-argument about what batch runs persist to disk and when (the batch id written at completion, not submission, because half the providers hand back a dead job). Dario is in the room, owns request-processing-core and provider backends per his handover doc, and this is #code-review, so "settled in review" is the register of the channel. The remark answers the adjacent open question in that same thread — where the per-batch plan is recorded — without duplicating emil's point about the id. Weakness: emil's thread is about timing of writes rather than file layout, and no one has raised metadata_{i}.json, so it reads as dario volunteering a settled decision into a related argument rather than answering a direct question.

#### `g1.r1.h2` — herring

**gideon**, unplaced, —

> so basically metadata_{i}.json comes out as {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307} now, the planner writes those three extra keys on top of num_jobs.

*Drafted as:* Confirming for the docs: metadata_{i}.json is now {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307} — the planner writes the extra three keys.


## g1.r2

**The hidden requirement:**

- **rule** — In the `"auto"` branch of `create_request_files`, after `plan_request_batches(dataset)` has returned and before anything new is written, every existing `requests_*.jsonl` and every existing `metadata_*.json` in `self.working_dir` is removed (`glob.glob` + `os.remove`). A previous `"auto"` run under different limits leaves a longer numbering behind (e.g. `requests_0..5.jsonl` for a new plan of 3), and those stale files are what a later glob-based read would pick up, so the branch clears them rather than overwriting only the prefix.
- **scope** — Sweeping belongs to the `"auto"` branch alone. The explicit-integer `batch_size` branch does not sweep — it still relies on `incomplete_files` and may legitimately leave earlier request files in place — and the `dataset is None` path does not sweep either.
- **exclusions_or_crossover** — Only those two glob patterns are removed. `responses_*.jsonl`, `*.arrow`, `batch_objects.jsonl` and every other file in the working directory survive byte-for-byte; the sweep is not a directory wipe.
- **failure_behavior** — The sweep sits behind a plan that returned. If planning raises — `SingleRequestTooLargeError` or `BatchPlanTooFragmentedError` — nothing is removed and nothing is written, so the working directory is byte-for-byte what it was, stale files and all.
- **observability** — `working_dir` pre-populated with `requests_0.jsonl … requests_5.jsonl` (each `"stale\n"`), `metadata_0.json … metadata_5.json` (each `"{}\n"`) and `responses_0.jsonl` (`"keep\n"`). After the successful 5-row run with limits patched to `3`/`400`: `sorted(os.listdir(working_dir)) == ["batch_plan.json", "metadata_0.json", "metadata_1.json", "metadata_2.json", "requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl", "responses_0.jsonl"]` — 8 entries — and `open(f"{working_dir}/responses_0.jsonl").read() == "keep\n"`. Against the same directory plus a stale `batch_plan.json` holding `{"plan_format_version": 1, "stale": true}`, `create_request_files(Dataset.from_dict({"prompt": ["ok", "x"*600, "ok"]}))` with `max_bytes_per_batch` patched to `400` raises `SingleRequestTooLargeError(row_idx=1, size_bytes=748, limit_bytes=400)` and all 14 entries survive, with `json.load(open(f"{working_dir}/batch_plan.json")) == {"plan_format_version": 1, "stale": True}` and `open(f"{working_dir}/requests_2.jsonl").read() == "stale\n"`.

**Reversed earlier:** The cleanup was originally the first statement of the `"auto"` branch, run on entry before `plan_request_batches`; it was moved to after planning returns when an oversized-row failure wiped a working directory that still held usable request files.

**What a reader has to infer along the way:**

- *When an "auto" run produces a shorter plan than the run before it, the request and metadata files left over from the longer numbering are still on disk and still get read, so they have to be taken off disk before the new files are written rather than partially overwritten.*
  - nobody says: Two families of file are written per batch, so leftovers of both kinds are read back later; if writing the new plan only covers the low indices, the high ones are still there and still look real.
- *This clearing belongs only to the sizer-chosen path; the fixed-width integer path and the path that is handed no dataset both leave the working directory as they found it.*
  - nobody says: Only a path that chooses its own file count can change that count between runs, and the other paths depend on old files still being there.
- *Only the two families of file the request stage itself writes are removed; responses, arrow caches, batch object records and anything else in the working directory are left byte-for-byte.*
  - nobody says: A working directory is shared by several stages, and the expensive artifacts in it were not produced by this one.
- *Nothing is removed and nothing is written until the planner has returned a plan; if planning raises, the working directory is exactly as it was, stale files included.*
  - nobody says: A step that can abort must not have already destroyed anything by the time it aborts.

### The remarks

#### `g1.r2.l1` — rule, observability

**gideon**, 2025-04-24, #code-review

> so basically i reran auto after we lowered the byte ceiling and the glob handed me six requests_*.jsonl when the plan only had three batches in it

*Drafted as:* reran auto after we lowered the byte ceiling and the glob handed me six requests_*.jsonl when the plan only had three batches in it.

*Why there:* Gideon opens that day flagging Dario's caching-and-resume PR — the one that "reads batch_objects.jsonl on startup and reattaches by id" — and says it has "a few things worth looking at before it goes in." A concrete finding about a startup glob picking up stale request files is exactly that kind of thing, from the person who owns caching-and-resume, and it sets up the rest of the day's theme of resume reads quietly doing the wrong thing with files on disk. It complicates the PR without duplicating the silent cache-write gripe Emil and Dermot land on later.

*Still leaves open:* does not say the leftovers should be removed, or that metadata files behave the same way

*Must appear literally:* `requests_*.jsonl`

#### `g1.r2.l2` — rule

**nikolai**, 2025-04-16, #cookbooks

> right and on a rerun here metadata_4.json outlived its requests file and the reader jsut counted its num_jobs like nothing was wrong

*Drafted as:* metadata_4.json outlived its requests file on a rerun and the reader went ahead and counted its num_jobs like nothing was wrong.

*Why there:* That room is already on stale-state-from-an-earlier-run being treated as current: Dermot's rerun resumed on the pre-edit batch id and Nikolai has just diagnosed it as inheriting from the old batch rather than the config. A second, file-level instance of the same thing — a metadata file surviving its requests file and still being read as live — lands as corroboration from the person already doing the diagnosis, and it stops at the observation, leaving what-to-do and whether request files do it too for Dermot or a later message.

*Still leaves open:* does not say what should be done about it, or that request files have the same problem

*Must appear literally:* `metadata_4.json`, `num_jobs`

#### `g1.r2.l3` — rule

**dario**, 2025-04-17, #pipeline

> honestly overwriting the low numbered ones does nothing when the new plan comes out shorter, the leftovers have to be gone before we write anything at all

*Drafted as:* overwriting the low numbers does nothing when the new plan is shorter, the leftovers have to be gone before we write anything.

*Why there:* None of the listed rooms is chewing on plan/payload files being rewritten on a re-plan. #pipeline 2025-04-22 is about Anthropic token counts, the batch-mode ordering fix and sweep scope — nothing there about writing or clearing plan output, so this would arrive from nowhere and get no reaction. #viewer 2025-04-14 is the closest in flavor (dario owns the caching-and-resume side of a resumed-run bug) but that thread's stale-state problem is specifically provider metadata on the summary table, and dario has already made his diagnosis there; a second, unrelated staleness claim about shorter plans would read as a subject change. The remaining rooms are capability checks, model-name matching, executor image defaults, cookbook response objects, PR merge state and weekly status. What's missing is the conversation where a resumed run picks up payload files from a longer previous plan and someone proposes just overwriting in place — that's the thread this line answers.

*Still leaves open:* does not say which files count as leftovers, or which branch this applies to

*A new conversation in #pipeline on 2025-04-17:*

```
11:04  gideon: so basically I resumed a run last night and it came back with more requests than the plan actually asked for. the re-plan gave us 14 batches but the working dir still had the payload files from the first pass, up to 19, and the submit step just globbed the whole folder
11:09  emil: hm. let me think through that — if the writer just wrote the new plan over the existing files in place, wouldn't that cover it? same naming scheme, same dir, batch 0 through 13 get rewritten and we never have to reason about a cleanup step at all
11:16  dario: overwriting the low numbers does nothing when the new plan is shorter, the leftovers have to be gone before we write anything. 14 through 18 are still sitting there from the old pass and nothing in the new write touches them, so the glob picks them up exactly like gideon saw. best we can do is truncate the dir first and then write, i think
11:18  gideon: ya thats what got me. the files looked fine individually too, valid jsonl, right shape, just belonging to a plan that doesnt exist anymore
11:24  emil: so you're saying the re-plan itself is the thing we should be questioning here? because on resume i'd have assumed we reuse the plan we already committed to rather than recomputing it against whatever the batch size is set to today. not entirely sure when that changed
11:31  dario: honestly i don't know if it ever changed or if it was always like this and we just never resumed with a different config. either it re-plans and we accept the dir has to be authoritative for the current plan only, or it doesn't re-plan and the stored one wins. mixing the two is what bit us
```

#### `g1.r2.l4` — scope

**konrad**, 2025-04-08, #code-review

> look, on a rerun with explicit batch_size=64 the whole point of incomplete_files is that resume stays cheap, so nothing shoud be touching the files it skips

*Drafted as:* on an explicit batch_size=64 rerun incomplete_files is the whole reason resume is cheap, so nothing should be going near the files it skips.

*Why there:* None of the eight rooms is chewing on batch resume semantics. The remark is a line-level review observation about a diff that changes how batch request files are named (fixed-width integers) and, elsewhere in the same diff, clears existing files — it only lands with someone staring at that hunk. The closest candidates are wrong in kind: #releases 2025-03-31 mentions retry/resume only as a one-line "unaffected" status note from dario, and raising a file-clearing worry there would reopen a release konrad is trying to close; #code-review 2025-05-29 is entirely PR 678/679 o3 structured outputs in finetuning, nowhere near batch; #engineering 2025-03-19 touches batch mode only through cost estimation and the throttle path. Batch-mode file handling was live work in that window though — nils had the state management refactor merged into batch-mode and PR 584 for Mistral batch, and a batch cancellation fix shipped in v0.1.23.post1 — so a review thread on the request-file naming change is exactly the conversation that should exist and doesn't.

*Still leaves open:* does not say which path does clear files, or what happens when no dataset is passed

*Must appear literally:* `incomplete_files`, `batch_size=64`

*A new conversation in #code-review on 2025-04-08:*

```
10:12  nils: put up the batch request file naming change, fixed width integer indices so the files actually sort in order instead of 1, 10, 11, 2. small diff but i'd like it in before the v0.1.23 cut. it also touches when we clear existing request files on a rerun, which is the part worth a look
10:19  dario: the clearing is the bit i'd want eyes on to be honest. is that firing on every rerun or only when the request params actually changed
10:24  konrad: look, on an explicit batch_size=64 rerun incomplete_files is the whole reason resume is cheap, so nothing shuold be going near the files it skips
10:31  nils: let me think through that. i read it as only the ones being rewritten, but the condition in there is doing more than the name suggests, maybe
10:38  dario: in any case i left a comment on the loop rather than approving. not blocking the cut from my side
```

#### `g1.r2.l5` — scope

**dermot**, 2025-04-07, page:design/ws-055-release-engineering-ci-test-suite.md

> Worth noting while I am in here: when `create_request_files` gets no dataset we are only listing what is already on disk, the directory is not ours to change on that call.

*Drafted as:* when create_request_files gets no dataset we are only listing what is already on disk, the directory is not ours to change on that call.

*Why there:* The "Cache layout" section is dermot's own note-to-self written "while I have the code open", and it already establishes that requests and responses live inside the per-fingerprint directory and that the open question is which components actually touch that state. A one-line observation that the no-dataset call into `create_request_files` only reads the directory rather than writing it is exactly the kind of audit finding that section is collecting, and it leaves the sized/dataset path — and what that does to stale files — unaddressed, which is what the rest of the audit is for. Nothing above says it already; the section only asserts coverage is the problem, not which calls are read-only.

*Still leaves open:* does not say anything about the sized path or what it does to old files

*Must appear literally:* `create_request_files`

#### `g1.r2.l6` — scope

**emil**, 2025-05-06, #pipeline

> let me think through that - the number of files only moves between runs on the path where the sizer picks it, fixed width always writes the same count for the same dataset.

*Drafted as:* the number of files only ever moves between runs on the path where the sizer picks it; fixed width always writes the same count for the same dataset.

*Why there:* None of the eight rooms is chewing on how batch requests get split into payload files. The nearest neighbours are about resume keys (#cookbooks 04-11), retry scope and metadata-db location for PR 585 (#code-review 03-21), and usage extraction from batch results (#pipeline 03-26) — all downstream of submission, none of them touching chunking, file counts, or a sizer. Dropping "fixed width vs the sizer" into any of those introduces a mechanism nobody in the room has mentioned, and it would sit there without a reply. What's missing is the thread where someone reran a batch job and got a different number of request files on disk than the first time — that's where Emil, who owns batch-mode, would be pinning down which path can even do that before anyone argues about what it should do.

*Still leaves open:* does not say what should happen on either path, only where the count can change

*A new conversation in #pipeline on 2025-05-06:*

```
10:14  dario: rerun of the same dataset yesterday wrote a diferent number of request files than the first pass, so resume cant line the old submission up with the new payloads at all. is the splitting actually deterministic or is it not, because at this point im not sure what im looking at
10:22  emil: let me think through that. the number of files only ever moves between runs on the path where the sizer picks it, fixed width always writes the same count for the same dataset. so it depends a fair bit on wich one that run was on
10:29  nils: So either that run was configured with a size budget, or something shifted underneath it. Do we record which splitting mode a submission was created under, or do we only have the file list to go on?
10:35  dario: just the file list i think. the metadata has request counts but not the mode, at least not in whatever version wrote those particular files
10:41  emil: yup thats about what i remember, honestly not entirely sure the metadata even had a field for it then. id have to go back and look at when that got added
```

#### `g1.r2.l7` — exclusions_or_crossover, observability

**nils**, 2025-03-24, ##batch-mode

> let me think — someone's tidy-up once took responses_0.jsonl with it and i paid for four thousand rows a second time, that one still stings

*Drafted as:* somebody's tidy-up took responses_0.jsonl with it and I paid for four thousand rows a second time, that one still stings.

*Why there:* Neither room is chewing on cleanup of the batch working directory. #code-review on 03-24 is purely PR traffic — who is reviewing 583 vs 584, CI on the colab check — and a war story about a deletion wiping response files would change the subject and draw no reply. #pipeline on 03-21 is the cost lookup fix, VCR cassettes for the Mistral batch backend, and the missing WS-047 page; it is cost-adjacent only by coincidence, and nobody there has raised anything that removes files. The remark needs a thread where someone has actually proposed a tidy-up step that clears intermediate batch files, which is the same thread the sibling remark (what to remove instead, what else in the directory matters) lives in. That thread does not exist yet: it should be Emil coming out of the PR 584 review with a cleanup helper that wipes the run directory after submission, Nils objecting from experience, and Dermot weighing in on which of requests_0.jsonl / responses_0.jsonl / the metadata are safe to drop.

*Still leaves open:* does not say what should be removed instead, or what else in the directory matters

*Must appear literally:* `responses_0.jsonl`

*A new conversation in ##batch-mode on 2025-03-24:*

```
14:12  emil: last thing on 584 and then i'll approve — i want to fold in a small cleanup helper that wipes the batch working dir once the requests are actually submitted. right now we leave the whole staging tree sitting there and nobody ever prunes it
14:13  emil: so if i'm reading the layout right, after submit the only thing that matters is the batch id, and everythign else under there is scratch? that's my assumption anyway
14:19  nils: let me think through that. i am not opposed in principle but I have been burned by exactly this shape of helper. somebody's tidy-up took responses_0.jsonl with it and I paid for four thousand rows a second time, that one still stings
14:24  dermot: mhm. the dir is doing double duty is the problem, request staging and whatever comes back land in the same place. if i had to guess that's mostly historical
14:31  emil: yeah ok that's fair, i was thinking of it as a request-side dir only. honestly not entirely sure what the split should look like — maybe the helper takes an explicit list rather than globbing the whole thing
14:38  nils: an explicit list is safer, yes. though a list drifts the moment someone adds a new artifact and forgets to add it. we can come back to it — is 584 blocked on this or can it go in as-is and we do the cleanup separately?
```

#### `g1.r2.l8` — exclusions_or_crossover

**emil**, 2025-03-21, page:design/batch-job-status-persistence-across-process-restarts.md

> - Also in the same `working_dir`: `batch_objects.jsonl` and the `*.arrow` cache, neither of which is written by the request stage

*Drafted as:* batch_objects.jsonl and the *.arrow cache sit in the same working_dir and neither one is written by the request stage.

*Why there:* The doc's whole spine is "which store holds what, and who is allowed to write it" — responses file owned by the online processor, metadata db written exclusively by batch-mode, plus a house-rules section about not letting the wrong path write. A line pinning down two more artifacts in working_dir and stating the request stage doesn't write either of them extends that inventory rather than changing the subject, and it's emil's own doc in his own hedge-light structural voice. Nothing above already covers batch_objects.jsonl or the arrow cache, so it isn't redundant, and it stops at ownership without saying what may be cleaned up — which the CURATOR_CACHE_DIR/resume thread elsewhere would supply.

*Still leaves open:* does not say what the request stage may remove, or that anything is being removed at all

*Must appear literally:* `batch_objects.jsonl`, `*.arrow`, `working_dir`

> **Problems:** longer than one remark

#### `g1.r2.l9` — exclusions_or_crossover

**dermot**, 2025-05-13, #code-review

> for the cleanup, go by the name patterns of the files this stage writes and leave the rest of the fingerprint directory alone, this is not a directory wipe.

*Drafted as:* go by the name patterns of what we are about to write and leave the rest of the folder alone, this is not a directory wipe.

*Why there:* Every listed room that touches the cache directory is chewing on creation, not removal — the fresh-CI FileNotFoundError and workflow mkdir -p on 03-31, gideon's typo'd path re-sending 38k requests on 04-17. Nothing anywhere raises clearing or deleting files, so a scoping constraint on a removal step answers no live question and its sibling (which patterns) would have nowhere to land. 04-07 is closest, since dermot himself records the fingerprint directory layout there, but that thread is ws-050 closure and ws-055 kickoff status, not code being written. The remark is review feedback on a reset step that wipes the fingerprint directory, which needs the PR thread that the corpus is missing.

*Still leaves open:* does not say which patterns those are, or which files in the folder are at risk

*A new conversation in #code-review on 2025-05-13:*

```
14:12  emil: on the batch payload PR, the reset step at the top of the stage does an unlink across the whole fingerprint cache dir before it re-writes requests and responses. given we never settled the partial-write/resume thing from 652 i'm not entirely sure we want it that broad
14:14  nikolai: whats in there besides the request and response files
14:16  emil: metadata sidecars, and honestly whatever else somebody drops in there later, thats sort of my worry, it's a shared dir and the reset doesnt know that
14:21  dermot: go by the name patterns of what we are about to write and leave the rest of the folder alone, this is not a directory wipe. so glob the request and response filenames for this batch and unlink those, anything else in there is not ours to clear
14:23  nikolai: yep thats fine as long as the pattern actually matches what the writer produces otherwise you get half stale half fresh
14:26  dermot: mhm, that said the patterns are constructed in the same module so if they drift that's a bigger problem than the reset step
```

#### `g1.r2.l10` — failure_behavior, observability

**konrad**, 2025-03-26, ##engineering

> look, I hit SingleRequestTooLargeError on the second row and came back to an empty working dir — those files were fine two secodns earlier

*Drafted as:* hit SingleRequestTooLargeError on the second row and came back to an empty working dir; those files were fine two seconds earlier.

*Why there:* All six candidates are Konrad's weekly status mails — coordination artifacts about PR ownership, release cuts and doc/example scope. A concrete crash repro with a data-loss symptom needs an answer from whoever owns the batch planner, and the sibling remark (what the cleanup ordering should be, what the other planner failure does) implies a live back-and-forth, not a bullet in a Monday summary. Dropped into the Mar 24 or Mar 31 mail it would change the subject mid-thread and draw no reply. What should exist is a short thread the day Konrad was actually exercising the batch examples: he was updating cookbook code for the OpenAI/DeepSeek/Mistral batch providers landing together (PR 565/566/579/584), ran a multi-row batch example, and lost the working dir to an oversized row. The thread would pull in Dario and Emil (batch clients) and Nikolai, and would also cover whether the same wipe happens on the other planner failure path and where the cleanup should sit relative to the plan step — which is exactly the part this remark deliberately does not settle.

*Still leaves open:* does not say what the ordering should be, or what happens on the other planner failure

*Must appear literally:* `SingleRequestTooLargeError`

*A new conversation in ##engineering on 2025-03-26:*

```
10:412  nikolai: placeholder
```

#### `g1.r2.l11` — failure_behavior

**dario**, 2025-03-21, #code-review

> on the batch side it's the other way round — plan_request_batches either comes back with a plan or it raises, so nothign that touches disk belongs above that call

*Drafted as:* plan_request_batches either comes back with a plan or it raises, so nothing that touches disk belongs above that line.

*Why there:* Emil at 12:26 raises exactly this — the online processor's deliberate write-ordering (appending to the responses file on accept, not on return) — and asks whether PR 585's retry handling has to account for it or sits above that layer. Dario is in the room and already engaging on PR scope, so him answering with the batch-side ordering invariant lands in a live thread. It also sets up Emil's 12:41 point about which files actually live under CURATOR_CACHE_DIR without duplicating it, since the remark says nothing about what's on disk.

*Still leaves open:* does not say what is on disk to begin with or which files matter when it raises

*Must appear literally:* `plan_request_batches`

#### `g1.r2.l12` — failure_behavior, observability

**emil**, 2025-04-17, ##eng-batch

> honestly if we abort on BatchPlanTooFragmentedError i want the old batch_plan.json left sitting there untouched, so i can diff it against whatever we just tried to build.

*Drafted as:* if we bail on BatchPlanTooFragmentedError I want the old batch_plan.json still sitting there so I can diff it against what we tried.

*Why there:* Nothing in the eight listed places is discussing batch plan construction or what an abort leaves on disk. The two weekly updates are status rundowns where a design preference about abort artifacts would draw no reply; the three release mails are outbound announcements of landed work; the docker thread is about create-call paths for pinned images; Dermot's mail is a narrow request for concurrency figures. BatchPlanTooFragmentedError is not a live subject in any of them, so the remark would be answering a question nobody in those rooms had asked.

*Still leaves open:* does not say what happens to request or metadata files on that failure, or where in the flow disk work sits

*Must appear literally:* `BatchPlanTooFragmentedError`, `batch_plan.json`

*A new conversation in ##eng-batch on 2025-04-17:*

```
14:02  gideon: so basically the fragmented plan guard is up on the WS-050 branch, it bails before we ever hit the submit call. one thing i left open in review tho, what do we do about the run dir at that point? right now the abort path is kind of just... unwinding whatever it had
14:05  dermot: unwinding meaning it removes the partial shard files, or removes everything under the run dir
14:06  gideon: um. everything tbh, it reuses the same cleanup we use for a failed submit
14:11  emil: let me think through that. if we bail on BatchPlanTooFragmentedError I want the old batch_plan.json still sitting there so i can diff it against what we tried. reusing the submit cleanup is going to take that with it which is exactly the thing i'd be reaching for
14:14  nikolai: is the guard even firing before the plan gets written or after
14:16  gideon: after, i think? the threshold check needs the shard counts so it has to be after. honestly though i'd have to reread it, the ordering in there is a bit of a mess
```

#### `g1.r2.h1` — herring

**dario**, unplaced, —

> the sweep is the first thing in the auto branch, glob away requests_*.jsonl and metadata_*.json, then plan_request_batches gets called. clean slate before we plan anything.

*Drafted as:* the sweep is the first statement in the auto branch: glob away requests_*.jsonl and metadata_*.json, then call plan_request_batches. clean slate before we plan anything.

#### `g1.r2.h2` — herring

**konrad**, unplaced, —

> Right, ordering is settled - the auto branch clears the stale request and metadata files on entry, then calls plan_request_batches. No point planning against a directroy we're about to empty.

*Drafted as:* Yep, ordering is settled — we clear the stale request and metadata files on entry, then plan. No point planning against a directory we're about to empty.

