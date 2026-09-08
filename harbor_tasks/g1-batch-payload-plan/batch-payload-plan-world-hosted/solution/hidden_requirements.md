# g1 — Batch payload planner for `batch_size="auto"`

**This is the answer key.** Nothing here is shown to an agent in any arm. The `blind` and `world` arms get the ticket and nothing else; `spec` also gets the hidden requirements; `clues` gets the remarks quoted in its prompt but never their dates' meaning, who is wrong, or which fact anything carries; `located` gets the same world as `world` plus a map of where each remark sits, but never a quote, never which requirement a conversation serves, and never which four are herrings.

| arm | what it is handed | measured |
|---|---|---|
| `blind` | the ticket | **0.00** |
| `spec` | the ticket + both hidden requirements | **1.00** |
| `clues` | the ticket + all 50 remarks, quoted | **1.00** |
| `world` | the ticket, against `sweworld:0.4.7` where the 50 remarks live in chat, the wiki and mail | see `horizon/results.json` |
| `located` | the `world` arm plus a map naming each remark's channel, day, minute and length (or its page, or its mail subject) — the search removed, the inference left | **1.00** |

---

## The hidden requirements — stated nowhere

Two requirements, `g1.r1` and `g1.r2`. Neither is written down anywhere an agent
can read: they have to be reassembled from remarks scattered across the world.

Each requirement is graded as **five independent facts, 0.1 each** — so 1.00 for
the pair. `open_feature` (did the agent build the feature at all?) carries weight
**0.0**: building the feature scores nothing, only recovering what nobody wrote
down does.

The five facts, and the question each one answers:

| fact | the question it answers |
|---|---|
| `rule` | what exactly has to exist |
| `scope` | where it applies, and where it must not |
| `exclusions_or_crossover` | what has to stay untouched |
| `failure_behavior` | what happens when it goes wrong |
| `observability` | the exact values a test can read back |

---

### `g1.r1` — write a `batch_plan.json` sidecar

**In one sentence:** the `"auto"` branch also writes one versioned, fingerprinted
plan document next to the request files, and refuses a plan of more than 512 batches.

#### `rule` — what has to exist

`batch_payload_planner` gains these module-level names:

| name | value / signature |
|---|---|
| `PLAN_FILE_NAME` | `"batch_plan.json"` |
| `PLAN_FORMAT_VERSION` | `1` |
| `_MAX_BATCHES_PER_PLAN` | `512` |
| `plan_fingerprint` | `def plan_fingerprint(plan: Sequence[PlannedBatch]) -> str` |
| `plan_document` | `def plan_document(plan: Sequence[PlannedBatch], limits: BatchLimits) -> dict` |

`BatchLimits` gains a **third field**: `max_batches_per_plan: int = _MAX_BATCHES_PER_PLAN`.

**`plan_fingerprint`** builds one canonical string and hashes it:

```python
";".join(f"{p.start_idx}-{p.end_idx}:{p.num_bytes}" for p in plan)
```

Spans and batch sizes only — **not** `index`, **not** `num_requests`. It returns the
**first 12 characters** of that string's `hashlib.sha256` hexdigest.

**`plan_document`** returns exactly these keys, in exactly this order:

| key | value |
|---|---|
| `plan_format_version` | `1` |
| `plan_id` | `plan_fingerprint(plan)` |
| `limits` | `dataclasses.asdict(limits)` |
| `num_batches` | `len(plan)` |
| `num_requests` | sum of `p.num_requests` |
| `num_bytes` | sum of `p.num_bytes` |
| `batches` | `[dataclasses.asdict(p) for p in plan]` |

**Where it is written.** In the `"auto"` branch of `create_request_files`, once
`plan_request_batches` has returned:

```python
json.dumps(plan_document(plan, self.batch_limits), indent=2) + "\n"
```

goes to `os.path.join(self.working_dir, PLAN_FILE_NAME)`.

#### `scope` — where it applies

- The `"auto"` branch **only**, and **before any request file is written**.
- A 0-batch plan still writes the file. An empty dataset produces a `batch_plan.json`
  with `num_batches: 0`, `num_requests: 0`, `num_bytes: 0`, `batches: []`, and the
  `plan_id` of the empty canonical string.
- The explicit-integer `batch_size` branch **never** writes it.
- The `dataset is None` path **never** writes it.

#### `exclusions_or_crossover` — what stays untouched

`metadata_{i}.json` is untouched by this. Its body stays exactly `{"num_jobs": n}` —
no `start_idx`, `end_idx` or `num_bytes` keys added.

#### `failure_behavior` — too many batches

`len(plan) > limits.max_batches_per_plan` raises
`BatchPlanTooFragmentedError(num_batches=..., limit=...)`:

- exported from the same module, storing both values as attributes;
- it subclasses `ValueError` but is **not** a `BatchPayloadTooLargeError`.

| call | result |
|---|---|
| `plan_batches([10]*512, BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=1000))` | 512 batches, no error |
| `plan_batches([10]*513, BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=1000))` | raises, `err.num_batches == 513`, `err.limit == 512` |
| `plan_batches([10]*3, BatchLimits(1, 1000, max_batches_per_plan=2))` | raises, `err.num_batches == 3`, `err.limit == 2` |
| `plan_batches([10]*600 + [5000], BatchLimits(1, 1000))` | raises `SingleRequestTooLargeError`, `err.row_idx == 600` |

That last row is the ordering rule: **the per-row oversize scan runs first**, so an
oversized row wins over a too-fragmented plan.

#### `observability` — exact values

Fingerprints:

| input | fingerprint |
|---|---|
| `plan_fingerprint([])` | `"e3b0c44298fc"` |
| `plan_fingerprint(plan_batches([10]*7, BatchLimits(1000, 32)))` | `"ad0828fea95e"` |
| `plan_fingerprint([PlannedBatch(0,0,2,2,307), PlannedBatch(1,2,4,2,307), PlannedBatch(2,4,5,1,153)])` | `"f4b1ea1573c0"` |
| the 11-batch plan of an 11-row dataset, `max_requests_per_batch` patched to `1` | `"c53f6fb95c13"` |

After the 5-row OpenAI run with limits patched to `3` / `400`,
`json.load(open(f"{working_dir}/batch_plan.json"))` equals exactly:

```json
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
    {"index": 2, "start_idx": 4, "end_idx": 5, "num_requests": 1, "num_bytes": 153}
  ]
}
```

and the raw file text ends in `"]\n}\n"`.

> **The herring** — what the team decided first and later reversed: the plan was first
> folded into the existing per-batch metadata — `metadata_{i}.json` became
> `{"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}` — and that was
> reverted a week later because readers of `metadata_{i}.json` assumed the
> `{"num_jobs": n}` shape; the plan moved out into one versioned sidecar instead.

---

### `g1.r2` — sweep stale files, but only after planning succeeds

**In one sentence:** the `"auto"` branch clears out its own leftover request and
metadata files before writing new ones — and if planning fails, it clears nothing.

#### `rule` — what has to exist

In the `"auto"` branch of `create_request_files`, **before anything new is written**,
every existing `requests_*.jsonl` and every existing `metadata_*.json` in
`self.working_dir` is removed.

#### `scope` — where it applies

- Sweeping belongs to the `"auto"` branch **alone**.
- The explicit-integer `batch_size` branch does **not** sweep.
- The `dataset is None` path does **not** sweep.

#### `exclusions_or_crossover` — what stays untouched

`responses_*.jsonl`, `*.arrow`, `batch_objects.jsonl` and every other file in the
working directory survive byte-for-byte.

#### `failure_behavior` — planning raised

If planning raises — `SingleRequestTooLargeError` — the working directory is
byte-for-byte what it was, stale files and all. **Nothing is swept.**

#### `observability` — exact values

Starting state: `working_dir` pre-populated with `requests_0.jsonl … requests_5.jsonl`
(each holding `"stale\n"`), `metadata_0.json … metadata_5.json`, and `responses_0.jsonl`
(holding `"keep\n"`).

**After the successful 5-row run** with limits patched to `3` / `400`:

```python
sorted(os.listdir(working_dir)) == [
    "batch_plan.json",
    "metadata_0.json", "metadata_1.json", "metadata_2.json",
    "requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl",
    "responses_0.jsonl",
]
open(f"{working_dir}/responses_0.jsonl").read() == "keep\n"
```

**After a failed run.** Same directory, plus a stale `batch_plan.json` holding
`{"plan_format_version": 1, "stale": true}`. Then
`create_request_files(Dataset.from_dict({"prompt": ["ok", "x"*600, "ok"]}))` with
`max_bytes_per_batch` patched to `400` raises `SingleRequestTooLargeError`, and all
14 entries survive:

```python
json.load(open(f"{working_dir}/batch_plan.json")) == {"plan_format_version": 1, "stale": True}
open(f"{working_dir}/requests_2.jsonl").read() == "stale\n"
```

> **The herring** — what the team decided first and later reversed: the cleanup was
> originally the first statement of the `"auto"` branch, run on entry before
> `plan_request_batches`; it was moved to after planning returns when an oversized-row
> failure wiped a working directory that still held usable request files.

---

## Where the remarks are spread

50 remarks in total — 42 clues, 4 herrings and 4 reversals — scattered across three surfaces and 9 chat channels. `spread_problems()` is the gate that forces this: every requirement needs at least 2 sources, 3 weeks and 2 channels, so no single sitting recovers one.

| surface | remarks | where they sit |
|---|---|---|
| chat (Mattermost) | **44** | `#pipeline` 10, `#code-review` 8, `#cookbooks` 6, `#engineering` 5, `#releases` 5, `#incidents` 3, `#viewer` 3, `#general` 3, `#random` 1 |
| wiki (BookStack) | **2** | 2 page comments |
| mail (Roundcube/IMAP) | **4** | 4 separate threads |

> **The wiki remarks are page _comments_, not page bodies.** BookStack's `/api/search` does not index comments, so `/api/search?query=…` returns nothing for a term that lives only in one. `/api/pages/{id}` returns them alongside the body — an agent that searches instead of enumerating never sees these 2.

---

## The MuSR tree

How the remarks add up. Each requirement decomposes into **subconclusions** a reader has to
infer, and the **leaves** under each one are the individual remarks that imply it. No leaf
closes its own subconclusion alone — that is `not_fragmented()` — and the subconclusions
together have to reach the requirement, which is `tree_adds_up()`.

Quotes here are the **planted** wording from `clues/plant.json`, not what the corpus ended up
saying. Phase 4 splits a remark across speakers and rewords it in their voice, so the shipped
text differs; `Where every remark is` below has the exact corpus wording.

### g1.r1

#### g1.r1.sc1 — An auto-sized run leaves one separate, indented JSON file under a fixed module-level file name in the working dir, and the existing per-batch metadata files are not extended to carry any of it.

*The leap nobody states:* If people keep needing the split after the fact and the per-batch metadata is off limits for it, the record has to be its own file with a name everyone can reach for.

- **gideon** (2025-04-24, #pipeline): so basically someone asked me how tuesday's auto run split and I had to ls the requests_*.jsonl files and re-measure every one of them. that should be sitting on disk.
- **dario** (2025-04-07, page:design/batch-job-status-persistence-across-process-restarts.md): worth adding to the persists-where list: the planner module holds PLAN_FILE_NAME = "batch_plan.json" next to the limits dataclass. nothing imports it from the processor yet, shape is still moving.
- **konrad** (2025-03-25, #code-review): Look, the plan file lands as one enourmous line, so diffing two runs is hopeless. Whole file is json.dumps(plan_document(plan, self.batch_limits), indent=2) plus a trailing newline.
- **dermot** (2025-05-08, #pipeline): our resume path json.loads metadata_0.json and expects {"num_jobs": n} and nothing else — n is exactly the plan's num_requests for that batch, so keep the span and byte fields out.

#### g1.r1.sc2 — The plan carries a short stable id: the first twelve characters of the sha256 hexdigest of a canonical string built from each batch's start-end span and its byte size, joined per batch, with the batch index and request counts left out.

*The leap nobody states:* Two runs that split the same way must produce the same token, so only the facts that define the split can go into the hashed string, and the digest is truncated to stay readable.

- **nils** (2025-03-26, #engineering): spent the morning diffing two batch runs span by span just to confirm the split hadn't moved. one short comparable string per plan would have answered that in a second.
- **dario** (2025-03-26, #pipeline): for the five row sample plan_fingerprint built 0-2:307;2-4:307;4-5:153 — start-end:num_bytes per batch joined on semicolons — and returned f4b1ea1573c0, the first twelve hex of its sha256
- **emil** (2025-05-07, #pipeline): empty plan just hashes the empty string, so plan_id comes out e3b0c44298fc, first twelve of the sha256. no special case needed.
- **nikolai** (2025-04-18, #incidents): renumberd the batches by hand while poking at a failure and got the identical id back right call i mean the index and num_requests arent in what gets hashed
- **emil** (2025-03-19, #cookbooks): one more worth pinning next to the empty one: plan_batches([10] * 7, BatchLimits(1000, 32)) fingerprints to ad0828fea95e. no special casing, same recipe.

#### g1.r1.sc3 — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*The leap nobody states:* A consumer decides whether it can read the file at all, then wants the summary, and only then the detail, so the keys come in that order.

- **emil** (2025-05-22, #code-review): nit on the plan writer - you've got the 1 inlined in three seperate spots, and PLAN_FORMAT_VERSION is sitting right above it in the same module.
- **dermot** (2025-04-10, thread:new|g1.r1.l10): yeah — keep plan_format_version as the first key plan_document writes; a reader that cannot find it up front has no business parsing the rest.
- **gideon** (2025-04-22, #viewer): so basically the viewer reads num_batches and the request and byte totals straight off the top — and the batches key is one dataclasses.asdict per PlannedBatch, index and num_requests included.
- **nikolai** (2025-06-16, thread:<178771578160.2500381.12817086076544913041@world.local>): good that limits is dataclasses.asdict of the BatchLimits it planned under, max_requests_per_batch and max_bytes_per_batch and max_batches_per_plan — otherwise 767 bytes tells you nothign a month later
- **nils** (2025-03-18, #general): pinned the envelope in my checker: plan_format_version, plan_id, limits, num_batches, num_requests, num_bytes, batches, in that order and nothing else at the top level.
- **konrad** (2025-03-17, #cookbooks): Right, so each entry in batches carries all five fields - index, start_idx, end_idx, num_requests, num_bytes. num_jobs is metadata_0.json's name, it doesnt come along.
- **dario** (2025-03-17, #releases): and batches[0] for the five row sample is {"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307} — same numbers as metadata_0.json, just num_requests where that says num_jobs

#### g1.r1.sc4 — The file is written on the auto branch only and before any request file, and is still written when the plan came out empty; the explicit-integer branch and the dataset-is-None path never write it.

*The leap nobody states:* The file is the marker that the auto sizer ran and what it intended, so it must exist exactly when the auto sizer ran, including the zero-row case, and never otherwise.

- **nils** (2025-03-19, #pipeline): let me think — a zero row auto run leaves the working dir completely empty and my checker can't tell that from a crash. we write the file regardless, num_batches 0.
- **konrad** (2025-04-15, thread:new|g1.r1.l14): Look, if a fixed batch_size run also drops a plan_id file next to the requests, my loader will read that run as auto-sized. Keep it to the auto branch.
- **dario** (2025-03-24, #pipeline): One thing that's already clear from the sketch - the online path calls create_request_files with dataset None, nothing to plan there, so we leave the working dir alone on that route.
- **gideon** (2025-04-23, #pipeline): same gap on my end - job died writing requests_3.jsonl and nothing on disk said there were supposed to be nine. plan gets written before the first request file.
- **dermot** (2025-03-18, #releases): one more on the zero row case — create_request_files hands back an empty list there, so there's no requests_0.jsonl sitting around with nothing in it.
- **dermot** (2025-03-14, #incidents): yeah ok, one more on the zero row doc — num_requests 0, num_bytes 0, and batches is an empty list, not a key we leave off.

#### g1.r1.sc5 — A plan split into more batches than a configurable ceiling, defaulting to 512, is rejected with a dedicated error carrying the batch count and the ceiling, distinct from the oversize-payload errors, and checked only after the per-row oversize scan.

*The leap nobody states:* A run that shatters into thousands of files is a different failure from one payload being too big, so it needs its own error and must not steal the report from the row that is genuinely oversized.

- **gideon** (2025-03-14, #code-review): so basically auto split one job into about 2600 request files and the submit loop crawled all afernoon. past some ceiling it should refuse to plan at all, not run it.
- **konrad** (2025-04-08, #code-review): look, my except BatchPayloadTooLargeError sailed straight past BatchPlanTooFragmentedError — err.num_batches 513, err.limit 512 off the default. right call, its own ValueError, my handler shoud not touch it.
- **nikolai** (2025-06-18, #code-review): test builds BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes so i dont have to construct 513 spans, then asserts err.num_batches == 3 and err.limit == 2
- **emil** (2025-06-16, #engineering): 600 rows of 10 bytes plus one 5000 byte row under a 1000 byte cap and it said too fragmented instead of naming row 600. per-row oversize reports first.
- **gideon** (2025-03-17, #viewer): so basically [10] * 512 at one row per batch planned all 512 and came back clean, 513 is the first count that refuses - we bail past the ceiling, not at it.

#### herrings — believed at the time, reversed later

- **dario** (2025-01-21): settled then: the plan rides in metadata_{i}.json — num_jobs plus start_idx, end_idx, num_bytes per batch. no extra file, we already write that metadata per batch.
- **konrad** (2025-01-22): Right, so metadata_0.json comes out as {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}. The span and the size both live in the per-batch metadata, that's the shape.

### g1.r2

#### g1.r2.sc1 — A fresh auto-sized run must not leave request or metadata files from any earlier run sitting in the working directory alongside the ones it just wrote.

*The leap nobody states:* If a shorter plan writes fewer files than last time, the only way the directory can end up holding just this run's output is if the old ones of those two kinds are taken out first.

- **gideon** (2025-04-08, #pipeline): Related-ish, I reran auto on a trimmed dataset and the submit loop picked up requests_4.jsonl and requests_5.jsonl leftover from Tuesdays bigger run, two duplicate batches.
- **nils** (2025-03-21, #code-review): @Emil same class of thing on my end - metadata_3.json in my working dir still reports num_jobs from the old split, and nothing in this run touched it.
- **dermot** (2025-04-11, #cookbooks): yeah. and a requests_0.jsonl already sitting there gets swept with the rest and rewritten from this run's plan, its own start_idx to end_idx.
- **konrad** (2025-03-14, #engineering): Look, I seeded the dir with requests_0.jsonl through requests_5.jsonl plus matchign metadata, then let the plan make three - the listing afterwards is the assertion.

#### g1.r2.sc2 — Only the automatic sizing path does this; the explicit-integer batch_size path and the dataset-is-None path must behave exactly as they do today.

*The leap nobody states:* Both of those paths depend on files from earlier runs still being there, so whatever removes leftovers cannot be shared code that runs on entry for everyone.

- **emil** (2025-04-21, #pipeline): sounds right - though the integer batch_size path leans on files from earlier runs, incomplete_files is what skips the finished ones, clear those and every resume starts from zero
- **nikolai** (2025-04-17, thread:new|g1.r2.l6): i'd say careful there on resume we call create_request_files with dataset=None purely to get the paths back and i'd be unhappy if that call ever started taking files away
- **dario** (2025-03-14, #releases): honestly explicit batch_size=1000 should keep giving the same fixed-width files it always has, i don't want that branch picking up new behaviour off the side

#### g1.r2.sc3 — Only those two families of files are removed; response files, arrow shards, the batch-id file and anything else in the directory are left exactly as they were.

*The leap nobody states:* Everything else in that directory is either paid-for output or state needed to reach in-flight work, so a sweep has to be pattern-scoped rather than a directory wipe.

- **gideon** (2025-03-14, #viewer): so basically someone ran rm -f over the working dir between runs and it took responses_0.jsonl with it, so we paid twice for a batch we had already completed.
- **konrad** (2025-05-02, page:design/batch-job-status-persistence-across-process-restarts.md): Look, the working dir today holds more than those two: requests_*.jsonl, metadata_*.json, responses_*.jsonl, batch_objects.jsonl (submitted batch ids we poll), plus the .arrow shards for the dataset.
- **dario** (2025-04-09, #incidents): not that i've seen. batch_objects.jsonl is unrecoverable state - the sweep doesn't just leave it in place, it leaves the bytes untouched, same for everything it isn't deleting.
- **nils** (2025-03-14, #general): let me think through that - the .arrow shards in the working dir are the dataset itself, drop those and we re-tokenize four million rows before anything even gets submitted

#### g1.r2.sc4 — When sizing fails and no plan comes back, the working directory must be left exactly as it was found, stale files included.

*The leap nobody states:* If nothing on disk changes on the failing path, the removal cannot have happened yet at the point the failure is raised.

- **emil** (2025-04-17, #random): not just create-on-open though - the oversized-row failure left me staring at an empty working dir, and the split that was in there beforehand was still perfectly usable
- **dermot** (2025-03-31, #code-review): a run that raises in the estimate step and never gets a plan out the other end has no business having changed anything on disk, stale or not
- **nikolai** (2025-03-14, #cookbooks): fixture pins max_bytes_per_batch to 400 and feeds a 600 char prompt - SingleRequestTooLargeError comes back with row_idx 1 on it, thats how we know which row blew up.
- **nils** (2025-03-17, #general): let me think through that - for the fixture to prove anything, batch_plan.json has to already be sitting in the dir when we start, holding a stale plan_format_version 1 body.

#### herrings — believed at the time, reversed later

- **dario** (2025-01-21): in any case the sweep is the first thing in the auto branch — clear out requests_*.jsonl and metadata_*.json on entry, then plan_request_batches runs against a clean dir
- **konrad** (2025-01-21): look, order in the auto branch is settled: we delete the old requests_*/metadata_* files first, plan_request_batches second. nothing new gets writen next to stale numbering.

---

## Where every remark is

50 remarks, oldest first. **Quotes are exact** — they are read back out of the corpus, not out of the plan, so the timestamps are the ones in the world.

`herring` is a decision the team really made and later reversed; the remark that overturns it is always strictly later and says so. `reversal` is that retraction.

| when | surface | where | who | remark | turns | kind | carries |
|---|---|---|---|---|---|---|---|
| 2025-01-21 | chat | #cookbooks | emil | [`g1.r2.h2`](#g1r2h2) | 7 | **herring** | — |
| 2025-01-21 | chat | #engineering | emil | [`g1.r1.h1`](#g1r1h1) | 9 | **herring** | — |
| 2025-01-21 | chat | #releases | emil | [`g1.r2.h1`](#g1r2h1) | 6 | **herring** | — |
| 2025-01-22 | chat | #engineering | emil | [`g1.r1.h2`](#g1r1h2) | 7 | **herring** | — |
| 2025-03-14 | chat | #viewer | emil | [`g1.r2.l8`](#g1r2l8) | 7 | clue | `exclusions_or_crossover`, `observability` |
| 2025-03-14 | chat | #general | emil | [`g1.r2.l11`](#g1r2l11) | 6 | clue | `exclusions_or_crossover` |
| 2025-03-14 | chat | #releases | emil | [`g1.r2.l7`](#g1r2l7) | 7 | clue | `scope` |
| 2025-03-14 | chat | #cookbooks | emil | [`g1.r2.l14`](#g1r2l14) | 7 | clue | `observability`, `failure_behavior` |
| 2025-03-14 | chat | #engineering | dermot | [`g1.r2.l4`](#g1r2l4) | 7 | clue | `rule`, `observability` |
| 2025-03-14 | chat | #code-review | dario | [`g1.r1.f1`](#g1r1f1) | 7 | clue | `failure_behavior` |
| 2025-03-14 | chat | #incidents | emil | [`g1.r1.say30`](#g1r1say30) | 7 | clue | `scope` |
| 2025-03-17 | chat | #viewer | dario | [`g1.r1.say28`](#g1r1say28) | 6 | clue | `failure_behavior` |
| 2025-03-17 | chat | #general | dario | [`g1.r2.l15`](#g1r2l15) | 7 | clue | `observability` |
| 2025-03-17 | chat | #cookbooks | dario | [`g1.r1.say23`](#g1r1say23) | 7 | clue | `rule` |
| 2025-03-17 | chat | #releases | emil | [`g1.r1.say24`](#g1r1say24) | 6 | clue | `observability` |
| 2025-03-18 | chat | #cookbooks | emil | [`g1.r2.rev2`](#g1r2rev2) | 6 | **reversal** of `g1.r2.h2` | `rule`, `failure_behavior` |
| 2025-03-18 | chat | #general | emil | [`g1.r1.say22`](#g1r1say22) | 7 | clue | `rule` |
| 2025-03-18 | chat | #releases | emil | [`g1.r1.say25`](#g1r1say25) | 7 | clue | `scope` |
| 2025-03-19 | chat | #cookbooks | konrad | [`g1.r1.say29`](#g1r1say29) | 8 | clue | `observability` |
| 2025-03-19 | chat | #pipeline | gideon | [`g1.r1.l13`](#g1r1l13) | 8 | clue | `scope`, `observability` |
| 2025-03-19 | chat | #releases | konrad | [`g1.r2.rev1`](#g1r2rev1) | 7 | **reversal** of `g1.r2.h1` | `rule`, `failure_behavior` |
| 2025-03-21 | chat | #code-review | emil | [`g1.r2.l2`](#g1r2l2) | 7 | clue | `rule` |
| 2025-03-24 | chat | #pipeline | dario | [`g1.r1.l15`](#g1r1l15) | 7 | clue | `scope` |
| 2025-03-25 | chat | #code-review | emil | [`g1.r1.l3`](#g1r1l3) | 7 | clue | `rule`, `observability` |
| 2025-03-26 | chat | #engineering | emil | [`g1.r1.l5`](#g1r1l5) | 7 | clue | `rule` |
| 2025-03-26 | chat | #pipeline | emil | [`g1.r1.l6`](#g1r1l6) | 7 | clue | `rule`, `observability` |
| 2025-03-31 | chat | #code-review | dario | [`g1.r2.l13`](#g1r2l13) | 6 | clue | `failure_behavior` |
| 2025-04-03 | chat | #pipeline | emil | [`g1.r1.rev2`](#g1r1rev2) | 7 | **reversal** of `g1.r1.h2` | `exclusions_or_crossover`, `rule` |
| 2025-04-07 | wiki comment | docs/design/batch-job-status-persistence-across-process-restarts.md | emil | [`g1.r1.l2`](#g1r1l2) | 7 | clue | `rule` |
| 2025-04-08 | chat | #pipeline | dermot | [`g1.r2.l1`](#g1r2l1) | 7 | clue | `rule` |
| 2025-04-08 | chat | #code-review | konrad | [`g1.r1.f2`](#g1r1f2) | 7 | clue | `failure_behavior` |
| 2025-04-09 | chat | #incidents | dermot | [`g1.r2.l10`](#g1r2l10) | 7 | clue | `exclusions_or_crossover` |
| 2025-04-10 | mail | “sample serialized plan from the batch payload plan work” | gideon | [`g1.r1.l10`](#g1r1l10) | 7 | clue | `rule` |
| 2025-04-11 | chat | #cookbooks | konrad | [`g1.r2.l3`](#g1r2l3) | 7 | clue | `rule` |
| 2025-04-15 | mail | “auto-sizing branch: sidecar on the fixed batch_size path too?” | emil | [`g1.r1.l14`](#g1r1l14) | 7 | clue | `scope` |
| 2025-04-17 | chat | #random | gideon | [`g1.r2.l12`](#g1r2l12) | 7 | clue | `failure_behavior` |
| 2025-04-17 | mail | “mail: resumed batch run double-submitted ~400 requests” | gideon | [`g1.r2.l6`](#g1r2l6) | 6 | clue | `scope` |
| 2025-04-18 | chat | #incidents | nikolai | [`g1.r1.l8`](#g1r1l8) | 7 | clue | `rule` |
| 2025-04-21 | chat | #pipeline | dario | [`g1.r2.l5`](#g1r2l5) | 7 | clue | `scope` |
| 2025-04-22 | chat | #viewer | emil | [`g1.r1.l11`](#g1r1l11) | 8 | clue | `rule`, `observability` |
| 2025-04-23 | chat | #pipeline | dermot | [`g1.r1.l16`](#g1r1l16) | 8 | clue | `scope`, `observability` |
| 2025-04-24 | chat | #code-review | emil | [`g1.r1.rev1`](#g1r1rev1) | 7 | **reversal** of `g1.r1.h1` | `rule`, `scope`, `exclusions_or_crossover` |
| 2025-04-24 | chat | #pipeline | gideon | [`g1.r1.l1`](#g1r1l1) | 7 | clue | `rule`, `observability` |
| 2025-05-02 | wiki comment | docs/design/batch-job-status-persistence-across-process-restarts.md | emil | [`g1.r2.l9`](#g1r2l9) | 7 | clue | `exclusions_or_crossover` |
| 2025-05-07 | chat | #pipeline | dermot | [`g1.r1.l7`](#g1r1l7) | 6 | clue | `rule`, `observability` |
| 2025-05-08 | chat | #pipeline | emil | [`g1.r1.l4`](#g1r1l4) | 7 | clue | `exclusions_or_crossover` |
| 2025-05-22 | chat | #code-review | konrad | [`g1.r1.l9`](#g1r1l9) | 6 | clue | `rule` |
| 2025-06-16 | chat | #engineering | nikolai | [`g1.r1.f4`](#g1r1f4) | 6 | clue | `failure_behavior` |
| 2025-06-16 | mail | “Re: Week of Jun 9 recap: bulk inference fix” | emil | [`g1.r1.l12`](#g1r1l12) | 6 | clue | `rule`, `observability` |
| 2025-06-18 | chat | #code-review | emil | [`g1.r1.f3`](#g1r1f3) | 7 | clue | `failure_behavior` |

#### `g1.r2.h2` · **herring**

- **chat** · #cookbooks · **emil** · 2025-01-21 09:14
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, order in the auto branch is settled: we delete the old requests_*/metadata_* files first, plan_request_batches second. nothing new gets writen next to stale numbering.

As it appears, spread across the exchange:

```
09:14  emil      before i wire the re-plan step into the auto sizing branch i want to know what we're doing with what's already on disk. right now if a run planned at 12 shards and then we re-size down to 5, the old requests_5 through requests_11 are just... still sitting in the dir
09:15  emil      and nothing clears them today. so the submit walk globs requests_* and picks up six shards nobody planned
09:18  dermot    so the stale ones get submitted as if they were part of the new plan? that's the failure mode you're describing. and it's not only the requests files, the metadata_* ones travel with them, they'd be just as stale
09:21  konrad    look, in the auto branch the delete comes before anything else. old requests_* and metadata_* both, they go first, before we do any planing at all. i don't want to be reasoning about which of two generations a file belongs to
09:24  dario     sure but where does that put plan_request_batches exactly. do we call it and then sweep whatever doesn't match the new count, or is the sweep the first thing and plan runs into an empty dir
09:27  konrad    the second one. delete first, plan_request_batches second. that order is settled as far as i'm concerned
09:28  konrad    the whole point is nothing new gets writen next to stale numbering. if plan runs after the sweep there is no old numbering left for it to sit beside, so you never have to diff counts. anyway someone still has to actually do it in the resume path, we can do that when we get to it
```

#### `g1.r1.h1` · **herring**

- **chat** · #engineering · **emil** · 2025-01-21 13:14
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> settled then: the plan rides in metadata_{i}.json — num_jobs plus start_idx, end_idx, num_bytes per batch. no extra file, we already write that metadata per batch.

As it appears, spread across the exchange:

```
13:14  emil      different thread - i'm about to start on the batch payload planner and i've been going back and forth on where the plan actually lives. right now it's just held in memory while the run goes, so if the process dies mid-submit there's nothing on disk that says what the shape of the run was supposed to be. do we want a plan.json sitting next to the batch files, or something else
13:17  nikolai   whats reading it back though
13:18  nikolai   i mean if its only resume that cares then the question is just what resume needs to know and not much else
13:21  emil      resume mostly, yeah. it needs to figure out which batches already went out and which didn't. we need to be intentional here because whatever i pick becomes the thing everyone has to keep in sync
13:29  dario     i don't think it needs its own file honestly. we already write a metadata_{i}.json alongside every batch as we go, so the plan can just ride in there - one more file per batch is one more thing to write half of and then crash in the middle of, and then you've got a plan file and a batch file disagreeing with eachother
13:34  emil      so if i'm reading you right, i open metadata_{i}.json and it tells me enough to reconstruct the slice that batch covers? because at the moment that file is basically just bookkeeping, it doesn't say anything about where the batch sits in the overall job list
13:41  dario     right, so you'd widen it. num_jobs, and then start_idx and end_idx and num_bytes for the batch. that's enough to tell you what should have been there and to notice if it wasn't. actually num_bytes is the one that catches the truncated writes, which is the case that bit us in the resume run
13:45  dermot    mhm. that's cheap, and it keeps the fsync story the same as it is now since it's one write per batch either way. i'd want the widened file to land before anything starts trusting it on read, but that's ordering, not design
13:48  nikolai   yep solid enough we can do that whenever the planner rewrite actually happens
```

#### `g1.r2.h1` · **herring**

- **chat** · #releases · **emil** · 2025-01-21 15:02
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> in any case the sweep is the first thing in the auto branch — clear out requests_*.jsonl and metadata_*.json on entry, then plan_request_batches runs against a clean dir

As it appears, spread across the exchange:

```
15:02  emil      i'm picking up the auto sizing branch tomorrow and i keep circling back to what bit us on the resumed run. the working dir was not empty when we came back to it — there was still output sitting there from the first sizing pass, and we happily submitted a chunk of it a second time. honestly i don't think the sizing logic was wrong, it just trusted what it found on disk
15:11  dermot    so if i'm reading you right the failure isn't in how we size, it's that plan_request_batches opens up, sees requests_0.jsonl / requests_1.jsonl etc already there and writes around them instead of from scratch. that's the thing that has to change — requests_*.jsonl gets cleared out so plan_request_batches is always running against a clean dir, nothing inherited
15:19  emil      yup that's the shape of it. two things i'm still fuzzy on though. one, is the requests glob the whole story, because we also drop the metadata sidecars next to them and i believe resume reads those too. two, where does the clearing actually live — do we do it as part of the sizing probe or before we've even worked out the sizes
15:27  dario     in any case the sweep is the first thing in the auto branch, i.e. on entry, before we've computed anything at all. if it sits inside the probe you've already got a code path where the probe decides not to run and the stale files survive, which is exactly the shape of the 400 duplicates. and yes the metadata_*.json go with it — those are what convinces the resume path the work is already done, so leaving them behind gets you the same bug with a different stack trace
15:33  dermot    yeah ok, that tracks. on entry it's one line and there's nothing upstream of it that can skip it
15:38  emil      sounds right. we need to be intentional about it in the tests too but that can come when we get to it, i'm not writing the branch tonight
```

#### `g1.r1.h2` · **herring**

- **chat** · #engineering · **emil** · 2025-01-22 10:41
- carries nothing — it is here to be wrong
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Right, so metadata_0.json comes out as {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}. The span and the size both live in the per-batch metadata, that's the shape.

As it appears, spread across the exchange:

```
10:41  emil      writing the chunk writer for the batch payload plan today and im stuck on where the counts go. the jsonl per batch is fine but anything downstream has to know what is inside each one without opening it and walking the lines
10:42  konrad    look, presumaby just a small json beside each chunk. batch_0.jsonl and metadata_0.json, same index so you can pair them by name. off the top of my head it carries num_jobs and then where the chunk sits in the original request list
10:43  konrad    so for the two request case you sent, metadata_0.json would be num_jobs 2, start_idx 0, end_idx 2. end exclusive, like a slice, otherwise everyone will be off by one forever
10:45  emil      ok that covers the span. the thing that actually bit us on the resumed run was size though, nobody knew the payload was over the limit until the api came back 400. so do we keep a separate manifest somewhere for bytes, or
10:46  konrad    no. same file. num_bytes goes in there with the rest — your sample plan was 307 bytes for those two, so 307. i dont want a second file to keep in sync, that goes stale the first time someone re chunks anyway
10:47  konrad    the span and the size both living in the per batch metadata is the shape i would go with. one read per batch and you know how many, which slice, how big
10:49  emil      mm that works for me. ill leave the writer stubbed till the auto sizing branch is in, the check can read num_bytes off it when we get to it
```

#### `g1.r2.l8`

- **chat** · #viewer · **emil** · 2025-03-14 09:12
- carries `g1.r2.exclusions_or_crossover`, `g1.r2.observability`
- must be typed literally: `responses_0.jsonl`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically someone ran rm -f over the working dir between runs and it took responses_0.jsonl with it, so we paid twice for a batch we had already completed.

As it appears, spread across the exchange:

```
09:12  emil      dario forwarded me the thread about that resumed run, the one that submitted everything a second time. is that a viewer problem at all or purely cli? asking because i dont want to build ui for somebody elses bug
09:14  gideon    honestly though the viewer is kind of the only place a person would ever notice it. the run just looks normal in there, two batches, both green, nothing complaining. so basically what happened is the workign dir got cleared out between the two runs — somebody ran rm -f over it to free up space i think, or just to tidy, i dunno the exact reason
09:17  emil      ok but the plan file survived, we read it back fine afterwards. so what did it actually lose that made resume think there was nothing done
09:19  gideon    responses_0.jsonl. that one went with it
09:19  gideon    and resume only counts what it can read off disk, so with that file missing the first batch looks like zero completed and it just goes and submits it again. so we paid twice for a batch we had already completed. provider had definitly already run it, we just could not see it locally anymore
09:21  emil      that is grim. so the signal is basically plan says submitted, no responses file sitting next to it → viewer marks the run suspicious instead of green?
09:23  gideon    ya exactly. tbh i would not even try to reconstruct anything, just make it loud before someone hits resume on it. we can do that when we get to it, i am still buried in the sidecar thing this week
```

#### `g1.r2.l11`

- **chat** · #general · **emil** · 2025-03-14 09:47
- carries `g1.r2.exclusions_or_crossover`
- must be typed literally: `.arrow`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think through that - the .arrow shards in the working dir are the dataset itself, drop those and we re-tokenize four million rows before anything even gets submitted

As it appears, spread across the exchange:

```
09:47  emil      im about to write the cleanup for the resume path and i want to pick a direction before i start. do we wipe the working dir wholesale on rerun, or keep an allowlist of stuff that survives? wholesale is like nine lines and i dont have to think about it
09:56  nils      let me think through that - wholesale is tempting, and for most of what lands in there it would be correct. but the working dir is not scratch space, or at least not entirely. the .arrow shards sitting in it are the dataset itself, they are not a cache of something we have elsewhere
10:01  emil      hm ok. i had them filed in my head as prep-step output, ie something the pipeline would just make again if it wasnt there. is that wrong, or is it right but expensive
10:08  nils      right but expensive, i think. we could regenerate them in principle. it's that we drop those and we re-tokenize four million rows before anything even gets submitted - so you sit through the whole prep pass again just to get back to the point where the first request goes out
10:11  emil      fair enough, thats not a nine line change then. allowlist it is. i'll carve out the shards and let the request jsonl and the logs get cleared, those are cheap to rebuild
10:15  nils      that's worth documenting somewhere near the cleanup fn, whoever reads it next will have the same instinct you did. doesnt have to be now though, we can do that when we get to it
```

#### `g1.r2.l7`

- **chat** · #releases · **emil** · 2025-03-14 10:07
- carries `g1.r2.scope`
- must be typed literally: `batch_size=1000`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> honestly explicit batch_size=1000 should keep giving the same fixed-width files it always has, i don't want that branch picking up new behaviour off the side

As it appears, spread across the exchange:

```
10:07  emil      quick one before i start cutting the sizing code. the auto path is going to work out its own chunk boundaries off the token estimate, so the payload files come out uneven by design. what do we do about people who've already pinned the size in their config?
10:14  dario     honestly explicit batch_size=1000 should keep giving the same fixed-width files it always has. thats the whole reason anyone sets it, they've got downsteam tooling counting lines and they don't want to find out on a monday that the count moved
10:17  emil      sure but "same as it always has" is doing a lot of work in that sentence. once the auto sizer learns something new — say we start splitting on token budget instead of request count — does the pinned path inherit it? the way i'd naturally write this is one sizer with a flag on it, and then it would, by default
10:23  dario     thats the bit i'd rather we didnt do actually. i don't want that branch picking up new behaviour off the side just because we made the auto one smarter. two paths is uglier to look at, i know, but its the best we can do if we want the pinned number to still mean the same thing in six months
10:26  dermot    mhm. and easier to work out what happened when a run goes sideways, you know which of the two you were in
10:31  emil      ok. i'll keep the pinned branch dumb then and put the token stuff only under auto. not going to be in this week's cut either way, the resume dedupe thing is ahead of it
10:34  dario     no rush, we can do that when we get to it. in any case the sidecar will need to say which mode it picked or none of this is legible from the logs afterwards
```

#### `g1.r2.l14`

- **chat** · #cookbooks · **emil** · 2025-03-14 10:12
- carries `g1.r2.observability`, `g1.r2.failure_behavior`
- must be typed literally: `400`, `600`, `SingleRequestTooLargeError`, `max_bytes_per_batch`, `row_idx`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> fixture pins max_bytes_per_batch to 400 and feeds a 600 char prompt - SingleRequestTooLargeError comes back with row_idx 1 on it, thats how we know which row blew up.

As it appears, spread across the exchange:

```
10:12  emil      ok so im about to write the test for the oversize single request path and im stuck on how to trigger it without shipping a giant fixture. the real cap is in the millions of bytes, i am not putting a two meg prompt in the repo
10:19  nikolai   you dont have to the cap is config not a constant, the fixture can pin max_bytes_per_batch to 400 and youre done
10:21  emil      oh nice, thats way better. so with the cap that low what do i actually feed it, and what comes back out the other side? right now the loop just chokes somewhere down in the serializer and you get a mess
10:27  nikolai   one row with a 600 char prompt on it, that alone is over the ceiling before you even try to pack it with anything else so theres nothing to argue about, at that point it should raise SingleRequestTooLargeError not try to split it
10:29  emil      sure but the input file has a few rows in it. if the error just says too large im back to guessing which one, and thats half the pain of the current behaviour tbh
10:36  nikolai   yep thats the bit that matters, the error carries row_idx so for the fixture youd assert row_idx 1 on it and thats how you know which row blew up not just that something did
10:38  emil      good, that i can assert on. wont get to it before the sizing branch lands but ill write it up that way
```

#### `g1.r2.l4`

- **chat** · #engineering · **dermot** · 2025-03-14 13:12
- carries `g1.r2.rule`, `g1.r2.observability`
- must be typed literally: `requests_0.jsonl`, `requests_5.jsonl`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, I seeded the dir with requests_0.jsonl through requests_5.jsonl plus matchign metadata, then let the plan make three - the listing afterwards is the assertion.

As it appears, spread across the exchange:

```
13:12  dermot    coming back to the batch payload plan for a sec. right now if a run resumes into a dir that already has request files on disk, we have nothing anywhere that says the plan continues past them. it just does whatever it does and we find out in the submit log
13:19  emil      let me think through that. the failure we actually hit was it starting the numbering back at 0 and re-sending work that was already out the door. so a test for it needs a dir that is already populated before the plan ever gets called. not entirely sure how we stage that though, real fixture dir checked in, or just write the files in setup
13:26  konrad    Look, no fixture. just write them in the setup, six of them, requests_0.jsonl through requests_5.jsonl
13:26  konrad    and the matchign metadata alongside each one. otherwise the plan does not treat them as real and we are back at zero anyway, which is the bug not the test
13:34  dermot    mhm. so what is the assertion then, that requests_0.jsonl through requests_5.jsonl come out untouched? if i had to guess you want it producing something new as well, otherwise a pass just means it did nothing at all
13:41  konrad    right thats the point. after the seed you let the plan make three, and then the listing of the dir afterwards is the assertion. nothing clever, no counting internals or mocking the writer. anyway if the listing is wrong you can read why straight off it
13:49  emil      yup, that reads fine to me. im tied up verifying the semaphore + cookbooks combo this afternoon so it wont be me today, but we can do that when we get to it, whoever ends up on the resume ticket honestly
```

#### `g1.r1.f1`

- **chat** · #code-review · **dario** · 2025-03-14 13:14
- carries `g1.r1.failure_behavior`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically auto split one job into about 2600 request files and the submit loop crawled all afernoon. past some ceiling it should refuse to plan at all, not run it.

As it appears, spread across the exchange:

```
13:14  dario     different thing but while people are looking at request processing - the auto sizing in the batch payload planner. do we want it to just pick whatever number it picks, or should there be something between it and the submit path
13:19  gideon    honestly though the auto sizing is the part i don't trust right now
13:19  gideon    so basically last week it took one job and split it into like 2600 request files? because the inputs were tiny so the token estimate came out tiny per request and it just kept going. nothing in there said stop
13:27  emil      let me think through that. the planner itself finished fine i believe, it was the submit loop after it that suffered - that crawled the entire afternoon getting through them one at a time. so the count isn't the damage, the count is what makes the submit stage unusable
13:31  dario     right so is the fix a warning when the count looks silly, or does the planner clamp it down to something sane and carry on? i can see it either way to be honest, a warning is cheap but nobody reads warnings in a script
13:36  gideon    neither tbh. past some ceiling it should just refuse to plan at all. like error out of the planning step, not plan it anyway and let the submit loop find out. if the number is that far off then something upstream is wrong and running it is the wrong move
13:42  emil      sounds right. we can do that when we get to it - whoever picks up the sizing work can drop the check in, doesn't need to block 579 or the schema_check stuff
```

#### `g1.r1.say30`

- **chat** · #incidents · **emil** · 2025-03-14 14:06
- carries `g1.r1.scope`
- must be typed literally: `num_requests`, `num_bytes`, `batches`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yeah ok, one more on the zero row doc — num_requests 0, num_bytes 0, and batches is an empty list, not a key we leave off.

As it appears, spread across the exchange:

```
14:06  emil      quick one before i start on the serializer — what does the plan doc look like when the filter drops everything and theres nothing to submit? right now the sizing helper just returns none and i really dont want to be handing none to json.dumps
14:11  dermot    mhm. i'd rather not have a null in there at all. the doc still gets written, same shape as any other run, just with num_requests sitting at 0. if the consumer has to branch on "did we even get a doc" that's how you end up with the late night page
14:13  emil      ok so a zero row. what about the byte counter, omit that one? null?
14:16  dermot    num_bytes 0. not entirely sure what we'd gain by having it absent — its a count of bytes we planned to send, and we planned to send none. same treatment
14:18  emil      and batches? thats a different animal though, its a container not a counter. i was going to just not emit the key at all when theres nothing in it
14:23  dermot    yeah ok, thats the one i'd push back on. empty list, not a key we leave off. otherwise every reader downstream is doing a .get with a default and eventually somebody forgets. that said i dont care where it sits in the doc, i just dont want the key vanishing depending on the run
14:25  emil      fair. not getting to it today but ill do it that way when i wire the serializer up
```

#### `g1.r1.say28`

- **chat** · #viewer · **dario** · 2025-03-17 09:38
- carries `g1.r1.failure_behavior`
- must be typed literally: `[10] * 512`, `512`, `513`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically [10] * 512 at one row per batch planned all 512 and came back clean, 513 is the first count that refuses - we bail past the ceiling, not at it.

As it appears, spread across the exchange:

```
09:38  dario     i'm putting the size guard into the plan builder this afternoon and i keep stalling on one thing. is the ceiling the last batch count we still accept, or the first one we throw on? because those are off by one from each other and i'd rather not guess
09:41  gideon    so basically i already poked at this last week with a fake job, before any of the guard existed. i fed it `[10] * 512` at one row per batch and it planned all 512 of them, came back clean, no complaint anywhere in the payload
09:43  dario     mhm, that tracks. so 512 sits inside, fine. but that's the half i was already fairly confident about, honestly. what i don't know is what the very next one does — does it die exactly on the boundary or somewhere after it
09:45  gideon    ya i went one past too. 513 is the first count that refuses, that's the one where it stops
09:46  gideon    so we bail past the ceiling, not at it, um. the ceiling itself is still a legal plan. whoever writes the check should make it strictly greater or we lose a batch for no reason tbh
09:49  dario     ok. i'll wire the comparison that way whenever i actually get to the validator, probably not today. in any case i'll leave a note on the ticket so nobody flips it back to >= out of habit
```

#### `g1.r2.l15`

- **chat** · #general · **dario** · 2025-03-17 09:38
- carries `g1.r2.observability`
- must be typed literally: `batch_plan.json`, `plan_format_version`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think through that - for the fixture to prove anything, batch_plan.json has to already be sitting in the dir when we start, holding a stale plan_format_version 1 body.

As it appears, spread across the exchange:

```
09:38  dario     so im starting on the test for the plan upgrade path and i already dont like the shape of it. right now the run just writes out a fresh plan every time, so whatever assertion i write passes, but it passes because nothing was ever old. it doesnt tell me the migration ran, it tells me the writer works
09:42  nils      let me think through that. I take your point — the run creating its own input is the failure mode, because then you are exercising the happy path twice and calling it coverage. For the fixture to prove anything, batch_plan.json has to already be sitting in the dir when we start. Not written by setup partway through, not touched by the run first — there before anything of ours executes.
09:45  dario     mhm, that tracks. though — does it matter what's actually *in* it, or is an empty file at the right path enough to trip the branch? honestly i was going to just touch it and move on, but if the loader bails on an empty body then thats a different test than the one i want
09:51  nils      An empty body would only prove the file exists, which is not the interesting question. it has to hold a stale plan_format_version 1 body — a real one, shaped the way we were writing them before. otherwise you never get to the code that notices the version is behind and does something about it. Empty gets you a parse error at best and a silent skip at worst, and neither of those is the migration.
09:54  dario     fair. so the fixture is basically a snapshot of an old plan checked in as-is, and we dont regenerate it. in any case thats less work than what i was imagining
09:56  nils      Right, and it should be kept verbatim rather than templated, otherwise it drifts forward with the writer and stops being stale. that's worth documenting next to the fixture, i think.
09:58  dario     yeah. im not going to get to it this week to be honest, but ill put it on the ticket — we can do that when we get to it
```

#### `g1.r1.say23`

- **chat** · #cookbooks · **dario** · 2025-03-17 09:47
- carries `g1.r1.rule`
- must be typed literally: `batches`, `index`, `start_idx`, `end_idx`, `num_requests`, `num_bytes`, `num_jobs`, `metadata_0.json`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Right, so each entry in batches carries all five fields - index, start_idx, end_idx, num_requests, num_bytes. num_jobs is metadata_0.json's name, it doesnt come along.

As it appears, spread across the exchange:

```
09:47  dario     question before i start on the writer — for the plan file, does each thing in `batches` get a full record, or do we keep it thin and let the resume path recompute the offsets? honestly either is fine by me, i just don't want to write it twice
09:52  konrad    not thin. we did thin in the old one and it was painful each entry in `batches` wants `index`, `start_idx`, `end_idx`. the index so the request file can be named off it, and the two idx so you know your slice without holding the dataset in memory
09:53  konrad    anyway recomputing offsets at resume time is exactly how you get the double submit
09:58  dario     mhm, that tracks. so what about the sizing numbers then, `num_requests` and `num_bytes` — do those ride along per entry or are they only a top level thing? i was sort of assuming the header counts and the rest gets derived
10:04  konrad    they ride along. so five things on each entry, `num_requests` and `num_bytes` sitting next to the three num_bytes especially. if you dont store it you have to reserialize the whole slice again just to know whether it fits
10:05  konrad    `num_jobs` is a different animal though, that name belongs to `metadata_0.json`, it stays up there and doesnt come along into the entries. presumably nobody needs it per batch off the top of my head
10:11  dario     right ok. i'll put the five on each entry and leave the metadata file as is. the auto-sizing branch is going to want num_bytes there anyway, someone can wire that side up when we get to it
```

#### `g1.r1.say24`

- **chat** · #releases · **emil** · 2025-03-17 10:04
- carries `g1.r1.observability`
- must be typed literally: `batches[0]`, `{"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307}`, `metadata_0.json`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> and batches[0] for the five row sample is {"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307} — same numbers as metadata_0.json, just num_requests where that says num_jobs

As it appears, spread across the exchange:

```
10:04  emil      before i write the serializer part — the plan object we hand the sidecar, what's actually in batches[0] for the five row sample? i have a start and an end but i keep second guessing whether end is inclusive or not
10:07  dario     half open, same as the rest of the slicing code. so for the five row sample at two rows a batch, batches[0] is rows 0 and 1, which is start_idx 0 and end_idx 2. i think thats the least surprising way round given nothing else in there treats an end index as inclusive
10:09  emil      ok that bit i can live with. what im stuck on is the key names. do i just invent them, or is there something on disk already that carries these numbers
10:13  dario     dont invent. batches[0] for that sample should come out as {"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307} — index goes in there too so that a single batch is still self describing when someone pulls one out of the list on its own
10:15  emil      307 isnt a number im going to be able to justify from memory. where's it coming from, and is it something i can diff against rather than eyeballing
10:18  dario     its the same numbers metadata_0.json is already writing for that sample, byte cout included, so you can diff straight against the file. the one wrinkle is naming — metadata says num_jobs where we say num_requests. to be honest id rather we didnt keep two words for the same thing, but renaming what the metadata writer emits is its own migration. we can do that when we get to it
```

#### `g1.r2.rev2` · **reversal**

- **chat** · #cookbooks · **emil** · 2025-03-18 10:07
- carries `g1.r2.rule`, `g1.r2.failure_behavior`
- takes back `g1.r2.h2`
- must be typed literally: `plan_request_batches`, `requests_*.jsonl`, `metadata_*.json`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> That order is gone, deleting first cost you a split when the oversized row raised. plan_request_batches runs first now, we only sweep requests_*.jsonl and metadata_*.json after it returns a plan.

As it appears, spread across the exchange:

```
10:07  emil      before i start on the sidecar bit — which order are we doing it in on the auto branch. tuesdays run left the output dir completely empty and i'd rather not rebuild that by hand again
10:11  konrad    Look, the order we settled on was: delete the old requests_* / metadata_* files first, plan_request_batches second. so that nothing new ever gets writen next to stale numbering. that was the entire reason for it as i remember
10:12  konrad    That order is gone though. deleting first cost you a split when the oversized row raised — the plan blew up a moment after the files were already off disk and there was nothing to fall back on. thats your empty dir
10:14  konrad    plan_request_batches runs first now. off the top of my head that also means the sizing is decided before anything on disk moves at all
10:19  emil      ok but then the stale numbering thing comes back doesnt it. do we just leave the old requests_*.jsonl sitting there next to whatever the new run writes
10:24  konrad    no — we only sweep requests_*.jsonl and metadata_*.json after it returns a plan. if it raises we havnt touched anything, and a run like tuesday just doesnt delete. anyway none of this is written yet, its whoever picks up the sidecar, we can do that when we get to it
```

#### `g1.r1.say22`

- **chat** · #general · **emil** · 2025-03-18 10:12
- carries `g1.r1.rule`
- must be typed literally: `plan_format_version`, `plan_id`, `limits`, `num_batches`, `num_requests`, `num_bytes`, `batches`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> pinned the envelope in my checker: plan_format_version, plan_id, limits, num_batches, num_requests, num_bytes, batches, in that order and nothing else at the top level.

As it appears, spread across the exchange:

```
10:12  emil      the plan file dermot sent back has the batches array sitting first and the counts underneath it, and the one i generated locally came out the other way round. neither is wrong as far as the writer is concerned which is sort of the problem
10:14  emil      i'm about to write the check for this and i'd rather not write it twice. do you have a shape in mind already or should i just encode whatever the writer happens to emit today
10:19  nils      let me think through that for a moment. i do have one, and i would rather it not be whatever the writer emits, because the writer has changed twice this month alone. the top of the file wants to open with plan_format_version, then plan_id, then limits — version first so anything reading it can bail out before it tries to interpret anything underneath, and the limits up there because they're what the sizing decision was actually made against
10:23  emil      that part i'm fine with. where i'm stuck is the middle. there are three counts and i've seen them in at least two orders, and then separately whether a plan carrying an extra key up top is still a valid plan. the auto-sizing sidecar wants to stash a couple of things somewhere and i've been telling it no, but not really on any authority
10:24  emil      so strict, or strict-ish
10:31  nils      strict, i think. after limits it goes num_batches, num_requests, num_bytes, coarsest to finest, which also reads correctly out loud and that is not nothing when you're eyeballing two plans side by side at 2am. then batches last, since it's the only member that isn't a fixed size and you want all the scalars above it. and nothing else at the top level at all — the sidecar can put its things inside a batch or in a file of its own, but not up there. that's what i'm going to pin the envelope to in my checker, and a stray key at the top fails rather than warns
10:34  nils      that's worth documenting somewhere more durable than this channel eventually. maybe once the checker actually exists, we can do that when we get to it
```

#### `g1.r1.say25`

- **chat** · #releases · **emil** · 2025-03-18 14:09
- carries `g1.r1.scope`
- must be typed literally: `create_request_files`, `requests_0.jsonl`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> one more on the zero row case — create_request_files hands back an empty list there, so there's no requests_0.jsonl sitting around with nothing in it.

As it appears, spread across the exchange:

```
14:09  emil      before i keep going on the splitter rewrite — theres a case i dont have an answer for. what do we do when the filtered set comes back with literally nothing in it. zero rows
14:13  dermot    mhm, that's not hypothetical. the resumed run last week hit exactly that, everything in the shard was already accounted for so the remaining set was empty and the thing fell over on an index
14:15  dermot    the behaviour i want is the boring one. create_request_files just hands back an empty list there. no sentinel value, no raise, the caller gets a list of zero paths and decides for itself that there's nothing to submit
14:18  emil      ok that's fine for the caller. but im more worried about what it leaves behind on disk — resume globs the request dir to figure out what's already been staged, so if there's something sitting there it'll go looking for work that isnt there
14:22  dermot    yeah that's the other half of it. we don't open a writer until we actually have a row to put in it, so there's no requests_0.jsonl sitting around with nothing in it. empty dir, empty list, nothing for the glob to trip over
14:24  emil      right, i had it opening the handle at the top of the loop which is exactly how you end up with the empty one. ill move it
14:29  dermot    that said the zero path still walks through the progress bar setup and if i had to guess that divides by the row count somewhere. not entirely sure. we can look at that when we get to it
```

#### `g1.r1.say29`

- **chat** · #cookbooks · **konrad** · 2025-03-19 10:07
- carries `g1.r1.observability`
- must be typed literally: `plan_batches`, `[10] * 7`, `BatchLimits(1000, 32)`, `ad0828fea95e`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> one more worth pinning next to the empty one: plan_batches([10] * 7, BatchLimits(1000, 32)) fingerprints to ad0828fea95e. no special casing, same recipe.

As it appears, spread across the exchange:

```
10:07  konrad    the only golden fixture we have on the planner right now is the empty input one. that feels thin to me. what else goes in there before we freeze the file
10:09  gideon    ya empty is testing basically nothing lol
10:10  gideon    so basically it proves the serializer doesnt blow up on zero items and thats it. honestly though i want one where the sizing math actually has to run on somthing
10:13  dermot    the empty case is degenerate, granted. if i had to guess what you want is one that is small enough to read by hand but not trivial — a handful of identical items sitting under the caps, so the sizer does real work and still fits on one screen. emil you had a candidate for this last week, no?
10:16  emil      yeah, i think there is one more worth pinning next to the empty one: plan_batches([10] * 7, BatchLimits(1000, 32)). seven identical items, comfortably under the token cap and under the count cap, so nothing splits, but every step of the sizing still gets exercised. small enough that you can veriy the plan by eye if the fixture ever drifts
10:19  konrad    right. do you have the digest for that already or do we compute it when we write the test. and the other thing — presumably nothing splits there, so does the sizer need its own path for that case, off the top of my head it seemed like it might
10:23  emil      i walked it through by hand against the recipe we settled on, it fingerprints to ad0828fea95e. and no — no special casing, same recipe as everything else, serialize then hash. the moment we add a branch just because the input is small the fingerprints stop meaning anythin
10:25  dermot    mhm. yeah ok. whoever gets to the fixture file can drop both in then, no need to do it tonight
```

#### `g1.r1.l13`

- **chat** · #pipeline · **gideon** · 2025-03-19 13:02
- carries `g1.r1.scope`, `g1.r1.observability`
- must be typed literally: `num_batches`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> let me think — a zero row auto run leaves the working dir completely empty and my checker can't tell that from a crash. we write the file regardless, num_batches 0.

As it appears, spread across the exchange:

```
13:02  gideon    ok so basically i'm writing the check for the batch payload planner and i hit something weird. if the auto run gets a shard with zero rows the working dir is just... completely empty afterwards. no plan, no nothing
13:06  dermot    so you're saying the planner short circuits before it ever serializes anything? if i had to guess it bails out at the split step because there's nothing to split
13:09  gideon    ya exactly, it just returns early i think
13:10  gideon    problem is my checker only globs the working dir. an empty dir looks identical to the process dying halfway through, tbh i have no way to tell those two apart from outside. honestly though that feels like the planner's problem not the checker's
13:17  nils      let me think through that for a second. Either we teach the checker that empty is a legitimate terminal state, or the run leaves something on disk no matter what happened. i think the second one is the only version that survives contact with anyone else's tooling — we write the file regardless, even on the empty path.
13:21  emil      sounds right, but a plan file with waht in it though? if it's just an empty blob thats not much better, we need to be intentional here about what a reader actualy sees
13:26  nils      same shape as always, num_batches 0. That's an unambiguous statement that the planner ran and found nothing to do, and it's worth documenting alongside the field so nobody later decides zero means "unset"
13:31  dermot    yeah ok. that said nobody's touching the writer until the sizing branch lands, so whoever picks it up can do it when we get to it
```

#### `g1.r2.rev1` · **reversal**

- **chat** · #releases · **konrad** · 2025-03-19 13:06
- carries `g1.r2.rule`, `g1.r2.failure_behavior`
- takes back `g1.r2.h1`
- must be typed literally: `plan_request_batches`, `SingleRequestTooLargeError`, `requests_*.jsonl`, `metadata_*.json`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> sweep isn't first in the auto branch any more - it wiped a working dir when plan_request_batches threw SingleRequestTooLargeError, so requests_*.jsonl and metadata_*.json clear only after planning returns

As it appears, spread across the exchange:

```
13:06  konrad    so the auto branch ate a working dir on me yesterday. the whole thing, gone
13:07  konrad    I re-ran with one very long prompt in the set and came back to nothing on disk, no inputs, no outputs. What is the actual order in there? presumably planning happens before anything gets deleted
13:15  emil      other way round unfortunately, let me think through that ordering again... plan_request_batches raised SingleRequestTooLargeError on that oversized row and nothing above it catches it, so the process just died there. by the time it threw, the dir had already been emptied. the delete happens before planning is even called.
13:21  dermot    yeah, and that was deliberate for what it's worth. we settled a while back that the sweep is the first thing in the auto branch — clear out requests_*.jsonl and metadata_*.json on entry, then plan_request_batches runs against a clean dir. that said, konrad's run is exactly the hole in it, we commit to deleting before we know planning even succeeds. so am i right that what you want moved is the ordering, not the error handling?
13:26  konrad    right, but then what clears the stale shards. if some earlier run left requests_0003.jsonl sitting there and we don't sweep on entry, we mix old and new shards in the same dir. that was the whole reason for sweeping early, no?
13:35  dario     mhm it was. but the sweep isnt first in the auto branch any more, not after this. honestly a wiped dir on an input we cant even plan is a worse failure than holding stale files around a few seconds longer. so the clearing moves down — requests_*.jsonl and metadata_*.json only get cleared once plan_request_batches has actually returned, and we write the new set right after that. in any case if planning throws you still have on disk exactly what you walked in with, which is about the best we can do short of a real staging dir.
13:41  emil      sounds right. the clear and the write want to sit close together so there's no window where the dir is empty and nothing has landed yet, but that's mechanical, whoever picks the branch up can do that when they get to it
```

#### `g1.r2.l2`

- **chat** · #code-review · **emil** · 2025-03-21 12:43
- carries `g1.r2.rule`
- must be typed literally: `metadata_3.json`, `num_jobs`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> @Emil same class of thing on my end - metadata_3.json in my working dir still reports num_jobs from the old split, and nothing in this run touched it.

As it appears, spread across the exchange:

```
13:04  emil      circling back on the metadata thing. when a run comes back with a different split than what's already on disk, i'm not entirely sure anything rewrites the sidecar, or if we just leave whatever was sitting there. i went looking for the place that would do it and came up empty
13:11  dario     @Emil same class of thing on my end - the metadata json in my working dir is stale, it's still describing a split i haven't actually run since last week
13:14  konrad    which file though, and what field. off the top of my head there are like three of thsoe sidecars sitting in a working dir and they don't all mean the same thing
13:18  dario     metadata_3.json. num_jobs on it is from the old split, not the one i just ran
13:22  emil      so to restate my guess — it's getting rewritten each run but with a count carried over from the previous shape? or is it not getting rewritten at all
13:26  dario     the second one. nothing in this run touched it, honestly. mtime is still the earlier run, i checked before i said anything
13:31  nils      let me think through that. i think the shape we want is that whatever writes the split also writes the sidecar in the same pass, so a num_jobs on disk can't belong to a run that isn't the one on disk either. Nobody needs to go do that today, we can do it when we get to it — but that's worth documenting somewhere before it gets picked up
```

#### `g1.r1.l15`

- **chat** · #pipeline · **dario** · 2025-03-24 14:37
- carries `g1.r1.scope`
- must be typed literally: `create_request_files`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> One thing that's already clear from the sketch - the online path calls create_request_files with dataset None, nothing to plan there, so we leave the working dir alone on that route.

As it appears, spread across the exchange:

```
15:02  dario     ok, sketched something. the shape i landed on is a plan object we serialize into the run's working dir at submission time, one entry per request file, batch id + row range + status. that way a restart reads the plan back instead of re-submitting blind. i'll write it up properly but wanted to put it in front of you two before i go further
15:09  dermot    mhm, reads fine to me for the batch path. if i had to guess the awkward part is going to be everything that isn't batch though — you're saying every run materializes a plan in the working dir, or only the ones that actually have a provider job to reattach to?
15:16  dario     either-or is the right framing and i think it's the second one. one thing thats already clear from the sketch — the online path comes through create_request_files with dataset None, so there is no dataset to walk and no request files to enumerate
15:24  emil      so to restate it back — online still calls the same entrypoint, it just arrives with nothing in hand. does that mean we stamp an empty plan for it, or do we skip the write entirely? not entirely sure which is worse honestly, an empty plan file is at least uniform but it's also a lie
15:33  dario     nothing to plan there, so we leave the working dir alone on that route. no empty file, no stub. it's not that the plan is empty, its that there was never anything to serialize, and writing a placeholder just gives the resume logic something it has to special-case later
15:37  emil      yup, sounds right. we need to be intentional here about the resume side not treating "no plan" as "plan is corrupt", but that's downstream of this
15:41  dermot    yeah ok. that said i'd want the check to be on what came in rather than on the mode flag, since the flag has drifted from reality before. we can do that when we get to it though
```

#### `g1.r1.l3`

- **chat** · #code-review · **emil** · 2025-03-25 11:12
- carries `g1.r1.rule`, `g1.r1.observability`
- must be typed literally: `indent=2`, `json.dumps`, `plan_document`, `self.batch_limits`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Look, the plan file lands as one enourmous line, so diffing two runs is hopeless. Whole file is json.dumps(plan_document(plan, self.batch_limits), indent=2) plus a trailing newline.

As it appears, spread across the exchange:

```
11:12  emil      separate from all the PR stuff — while i'm in the batch payload plan writer, the plan file lands as one enourmous line. diffing two runs is hopeless, you get one changed line that's like 40k chars wide and github just gives up
11:16  nikolai   yep we hand the whole doc to the serializer in one shot nothing in there tells it to break lines so it doesnt
11:21  emil      so if i'm reading you right the fix is at the serialize call and not in how we build the document? i believe the doc itself is fine, its just what happens on the way to disk. is there actually one call that produces the whole file, or is it assembled in bits and i have to chase all of them
11:26  nils      let me think through that — no, it's one call. plan_document(plan, self.batch_limits) gives you the whole document, and json.dumps over that is the entire file contents. Nothing gets appended to it afterwards, so whatever you change at that call is the whole story
11:29  emil      right, but json.dumps on its own is exactly what's giving me the single line today. thats the bit i'm still stuck on honestly
11:33  konrad    look, indent=2 and you are done. json.dumps(plan_document(plan, self.batch_limits), indent=2), that is the file
11:34  konrad    plus a trailing newline on the end, otherwise the last line has no terminator and git compalins every time. anyway its small, we can do that when we get to it
```

#### `g1.r1.l5`

- **chat** · #engineering · **emil** · 2025-03-26 11:02
- carries `g1.r1.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> spent the morning diffing two batch runs span by span just to confirm the split hadn't moved. one short comparable string per plan would have answered that in a second.

As it appears, spread across the exchange:

```
11:02  emil      ok my morning is gone. the two batch runs from friday, i went through both of them plan by plan, span by span, side by side in two windows
11:05  konrad    span by span? what were you cheking exactly, that sounds like a lot of work for one thing
11:09  emil      it was one thing. i needed to confirm the split hadn't moved between the two runs, that's the whole question, yes or no. and nothing on the plan tells you that so you end up reading the spans
11:16  nils      let me think through that. so the thing you wanted wasn't the spans at all, it was whether two plans are the same plan. if each plan serialized down to one short string you could hold both up next to each other and you'd have your answer in a second instead of a morning. we have nothing like that today
11:19  konrad    short as in one line you can read? or the whole serialized blob
11:23  nils      short enough that comparing two of them is just looking at them. i think whoever is next in the serializer can drop it in, it isn't there yet
11:27  emil      yup. would have saved me today anyway
```

#### `g1.r1.l6`

- **chat** · #pipeline · **emil** · 2025-03-26 13:12
- carries `g1.r1.rule`, `g1.r1.observability`
- must be typed literally: `plan_fingerprint`, `0-2:307;2-4:307;4-5:153`, `f4b1ea1573c0`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> for the five row sample plan_fingerprint built 0-2:307;2-4:307;4-5:153 — start-end:num_bytes per batch joined on semicolons — and returned f4b1ea1573c0, the first twelve hex of its sha256

As it appears, spread across the exchange:

```
13:12  emil      different thread from the resume mess this morning, but related. when i diff two runs of the same batch job i have basically no way to tell whether the plan the second run built is the same plan as the first one. the logs just say "submitting 3 batches" and thats it
13:18  gideon    ya i hit this last week on the five row sample plan we keep around for tests, two runs looked identical in the log and were not. so basically what do you want to put in the log line? the whole serialized plan?
13:24  emil      not the whole thing, thats way too noisy. i was thinking of a short id derived from it, call it plan_fingerprint or something in that direction. one entry per batch, and each entry needs the row range it covers, start and end. what im not entirely sure about is whether the byte count belongs in there too, or if row ranges alone are enough to catch a resplit
13:31  dario     byte count should be in there honestly. two plans can cover the same rows and still differ if the serialization changed under you, which is exactly the case that bit you this morning. so per batch its start-end:num_bytes, and then you glue the batches together with semicolons. on the five row sample that comes out as 0-2:307;2-4:307;4-5:153 — you can read it left to right and see the split
13:36  gideon    ok that tracks for three batches. what happens at 400 batches though, thats a log line nobody is reading tbh. do we print that string as is?
13:44  dario     no, the string is just the input. you sha256 it and keep the first twelve hex, thats what goes in the log and in any case thats what you compare between runs. i pasted the sample one into a repl to check it looks sane, 0-2:307;2-4:307;4-5:153 gives you f4b1ea1573c0. short enough to sit at the end of a line without anyone complaining
13:49  emil      yup, twelve is fine for this, we're not defending against anyone here. i'll write it up on the resume ticket, whoever gets to that part can do it when we get to it
```

#### `g1.r2.l13`

- **chat** · #code-review · **dario** · 2025-03-31 12:36
- carries `g1.r2.failure_behavior`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> a run that raises in the estimate step and never gets a plan out the other end has no business having changed anything on disk, stale or not

As it appears, spread across the exchange:

```
15:03  dario     different corner of the pre-flight thing from this morning. i'm about to write the bit that serializes the plan out to disk and i want the failure ordering settled before i do, because right now it's whatever falls out. if the estimate step raises partway through — token counting on a bad row, cache miss, whatever — do we leave behind whatever the writer already touched, or does it back itself out
15:12  emil      let me think through that. the way i'd frame it is the plan file is the *output* of an estimate that finished, not a running log of one in progress. so if it blows up and you never get a plan out the other end, nothing new should have landed in that directory at all. write to a temp path, move it into place once you actually have the whole thing in hand. that part i'm faily confident about
15:20  dario     mhm, that tracks for the new file. the part i'm less sure about is the old one. right now the first thing that path does is unlink the stale plan from the previous run before it starts estimating anything, so if it throws you come back and the stale plan is gone and the new one never showed up. is that a delete we're allowed to do up front or does it wait too
15:27  emil      honestly not entirely sure. my instinct is a stale plan is garbage either way and clearing it early is more honest than leaving somehting sitting there that doesn't match the run anyone is currently looking at. but i can see the argument the other direction and we need to be intentional here, this is the kind of thing people build habits around
15:36  dermot    i'd wait. an unlink is a write like any other, the directory afterwards is not the directory you started with. if it throws in there the run has no business having changed anything in that folder, stale file included — you come back to it exactly as you left it. and a stale plan is only actually dangerous if something downstream claims it isn't stale, which is a separate problem from this one. that said, if i had to guess the unlink is sitting up front because it was easier than doing the temp file dance
15:44  dario     makes sense. so the unlink either moves to after the rename or it just becomes the rename. not touching that in 565, whoever ends up writing the serializer can do it when we get to it
```

#### `g1.r1.rev2` · **reversal**

- **chat** · #pipeline · **emil** · 2025-04-03 15:03
- carries `g1.r1.exclusions_or_crossover`, `g1.r1.rule`
- takes back `g1.r1.h2`
- must be typed literally: `metadata_0.json`, `{"num_jobs": 2}`, `batch_plan.json`, `batches`, `start_idx`, `end_idx`, `num_bytes`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> the resume path json.loads metadata_0.json and wants {"num_jobs": 2} and nothing else, so start_idx, end_idx and num_bytes came back out. that span and size sit in batch_plan.json under batches now

As it appears, spread across the exchange:

```
14:11  emil      im starting on the resume reader for the batch runs and i keep going back and forth on where the offsets are meant to come from. we had a run last week that resumed and the sidecar for the first batch claimed one span and the plan file claimed a differnt one, and nothing in the code has an opinion about which of them wins
14:18  dario     yeah that one. the shape we landed on back whenever was that metadata_0.json comes out as {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307} — the span and the size both living in the per batch metadata, that was the agreement. which is fine right up until something re splits and then you have two files that each think they know where batch 0 begins
14:26  dermot    mhm. that shape is gone as of this pass. the span and the size are moving into batch_plan.json, under batches, one entry per batch, and that's the only place either of them gets written. if i had to guess most of the disagreement emil hit was the sidecar being stale rather than actually wrong
14:33  emil      ok let me think through that. if the offsets live in the plan now then is the per batch metadata file just deleted outright? because i still need somehting on resume that tells me how many jobs actually went into batch 0, i cant get that from a byte range
14:41  dermot    no, it stays. the resume path json.loads metadata_0.json and what it wants out of it is {"num_jobs": 2} and nothing else. start_idx, end_idx and num_bytes come out of that file entirely, they're plan side now
14:47  gideon    wait so what about the run dirs already sitting on disk with the old keys in them. we have a few from march. do those just blow up on resume or
14:55  dermot    extra keys get ignored, the reader only reaches for the one it needs. that said the march dirs have no batches block in the plan at all so they won't resume regardless. we can write a shim for them when we get to it
```

#### `g1.r1.l2`

- **wiki comment** · docs/design/batch-job-status-persistence-across-process-restarts.md · **emil** · 2025-04-07 09:41
- carries `g1.r1.rule`
- must be typed literally: `PLAN_FILE_NAME`, `batch_plan.json`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> worth adding to the persists-where list: the planner module holds PLAN_FILE_NAME = "batch_plan.json" next to the limits dataclass. nothing imports it from the processor yet, shape is still moving.

As it appears, spread across the exchange:

```
09:41  emil      question on the persists-where section — as written its the responses file and the metadata db and thats it. but the restart path i'm sketching keeps bumping into a third artifact, the thing the planner drops before submission. am i reading that right that its just newer than the doc, or is it deliberately out of scope
09:47  nikolai   not deliberate i dont think planner module already has the name pinned PLAN_FILE_NAME = "batch_plan.json" its sitting right next to the limits dataclass
09:53  emil      yup ok. so if i follow you the planner owns both the constant and the file. does the processor pull that name in when it comes back up, or is it doing its own thing entirely
09:58  dermot    doing its own thing. nothing imports PLAN_FILE_NAME from the processor yet, the only reader today is the planner itself — that said i wouldnt treat that as permanent, the restart work will want it eventually
10:02  nikolai   and the shape isnt settled either fields moved twice last week off the top of my head so id say dont write anything against it yet
10:09  dario     mhm. i think its worth adding to the persists-where list anyway, even in that state — the whole point of that section is that a restart knows what to go look at, and leaving a file off it because its still in flux is exactly how we end up with the same split-picture problem one layer down. we can say plainly that nothing consumes it from the processor side yet and that the shape is still moving, so nobody reads it as stable. in any case thats the best we can do until someone actually wires the read path
10:14  dermot    yeah ok. ill fold it in next time im editing that page, no rush on it
```

#### `g1.r2.l1`

- **chat** · #pipeline · **dermot** · 2025-04-08 11:41
- carries `g1.r2.rule`
- must be typed literally: `requests_4.jsonl`, `requests_5.jsonl`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> Related-ish, I reran auto on a trimmed dataset and the submit loop picked up requests_4.jsonl and requests_5.jsonl leftover from Tuesdays bigger run, two duplicate batches.

As it appears, spread across the exchange:

```
13:04  dermot    before i start on the submit loop for the auto sizing branch - right now it just globs requests_*.jsonl out of the working dir and ships whatever it finds. if i had to guess that's fine on a clean run and wrong the rest of the time
13:09  dario     related-ish, i reran auto on a trimmed dataset yesterday and ended up with two duplicate batches out of it. havent chased it all the way down but i think its the same thing youre pointing at
13:12  dermot    duplicate meaning the same requests went up twice, or two distinct batch objects on the provider side
13:16  dario     two extra batch objects. trimmed set only produced three shards, but the submit loop picked up requests_4.jsonl and requests_5.jsonl sitting in there and submitted those too
13:20  gideon    ya those are leftover from tuesdays bigger run. nothing wipes the working dir between runs afaik so basically anything an older run left behind just sits there looking perfectly submittable
13:22  gideon    honestly though the glob is the bit i'd rip out. if the run tracks the shards it actualy wrote and submits off that list, stale files stop being a problem at all
13:27  emil      sounds right. we can do that whenever the sizing work comes up, doesnt need to hold up 614 imo
```

#### `g1.r1.f2`

- **chat** · #code-review · **konrad** · 2025-04-08 13:21
- carries `g1.r1.failure_behavior`
- must be typed literally: `512`, `513`, `BatchPayloadTooLargeError`, `BatchPlanTooFragmentedError`, `err.limit`, `err.num_batches`, `limit`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> look, my except BatchPayloadTooLargeError sailed straight past BatchPlanTooFragmentedError — err.num_batches 513, err.limit 512 off the default. right call, its own ValueError, my handler shoud not touch it.

As it appears, spread across the exchange:

```
13:21  konrad    look, question about the batch planner while i am still in this. i wrapped the sizing call in a try/except and my `except BatchPayloadTooLargeError` sailed straight past the thing that actually got raised
13:21  konrad    it was `BatchPlanTooFragmentedError`. is it intentioanl that this one does not come out of the payload error, or did somebody just forget to hang it off it
13:26  emil      so if i'm reading you right, you're asking whether the fragmentation one is supposed to be in the same family as the payload one. my read is no, and i don't think it's an oversight — they're two different failures. one is "this single request is too fat to send", the other is "your plan shattered into more pieces than we're willing to submit". honestly a handler that knows how to shrink a payload has nothing useful to say about the second
13:29  konrad    mhm, that part i follow. what i dont follow is the number. traceback had `err.num_batches` 513 against `err.limit` 512, and i never set 512 anywhere that i can remeber. is that mine or is it coming from somewhere else
13:33  gideon    ya that's not yours, 512 is just the default. so basically the planner takes a `limit` and if nobody passes one it fills in 512, so 513 is you going exactly one over and it bails on the spot. honestly though i'd leave it not subclassed, tbh the moment it inherits from the payload error every sizing handler in the codebase starts quietly swallowing fragmentation
13:35  nikolai   yep separate is right imo its its own ValueError and thats fine the retry story for it is completely different anyway
13:38  konrad    right, its own ValueError then, my handler shoud not touch it and i will let it raise through. anyway the fragmented case needs its own path eventually, someone can do that when we get to it, off the top of my head i dont know whose it is
```

#### `g1.r2.l10`

- **chat** · #incidents · **dermot** · 2025-04-09 12:43
- carries `g1.r2.exclusions_or_crossover`
- must be typed literally: `batch_objects.jsonl`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> not that i've seen. batch_objects.jsonl is unrecoverable state - the sweep doesn't just leave it in place, it leaves the bytes untouched, same for everything it isn't deleting.

As it appears, spread across the exchange:

```
12:38  dermot    separate thing from the duplicate batch - i want to write the cleanup sweep for stale cache dirs this week, since half of this morning was people sitting on cache dirs nobody could interpret
12:39  dermot    before i start though. my assumption is the sweep only ever removes whole directories and never opens anything it's keeping, but i'd rather hear that than assume it. is that right, or is there already something in there that rewrites files as it goes?
12:45  emil      let me think through that. the set i had in my head for deletion was the spent request and response files for runs that are fully done, those we can always re-derive from the provider side. beyond that i'm honestly not sure which files in a cache dir are regenerable and which aren't, and we need to be intentional here because getting that wrong is the same failure mode dermot was chasing at 10:29
12:49  dario     not that i've seen. nothing in the current cleanup path opens a file it isn't deleting, at least not anywhere i've looked. the one to be careful with is batch_objects.jsonl - that's unrecoverable state, it's the only local record of what we handed the provider, so if the sweep eats it the run is in exactly the position that OSError left people in this morning
12:53  dermot    mhm, but "doesn't delete it" is the weaker half of what i'm asking. if i wrote the sweep to open batch_objects.jsonl and drop the lines for batches that already came back, that leaves it in place too, and it would still be a rewrite. so is the file off limits entirely, and is that just that file or everything the sweep keeps?
12:57  dario     off limits entirely. the sweep doesn't just leave it in place, it leaves the bytes untouched - no compaction, no rewriting lines, no normalising trailing newlines, it doesn't open it for writing at all. and same for everything it isn't deleting, to be honest. delete or don't, but nothing gets edited on the way past
13:01  emil      sounds right. that also makes the sweep much easier to reason about when someone is staring at a cache dir at 2am, the mtimes on anything still there mean something. i can take the first pass at it after the cancellation work lands, we can do that when we get to it
```

#### `g1.r1.l10`

- **mail** · “sample serialized plan from the batch payload plan work” · **gideon** · 2025-04-10 11:03
- to dermot@world.local, emil@world.local, dario@world.local
- carries `g1.r1.rule`
- must be typed literally: `plan_format_version`, `plan_document`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> yeah — keep plan_format_version as the first key plan_document writes; a reader that cannot find it up front has no business parsing the rest.

As it appears, spread across the thread:

```
From: gideon@world.local
Sent: 11:03

Hi all,

Im writing the loader for the serialized plans and I hit a thing I'd like to settle before I go any further.

When we pick a file up off disk, what actually tells us which shape we're looking at? Right now I'm just trying the newest parser and catching the explosion, which honestly is not great.

Gideon

--------------------------------------------------------------

From: emil@world.local
Sent: 11:09

Hey Gideon,

There is a version field. plan_format_version — plan_document emits it when it serializes, so the information exists.

Where it lands in the output I'm less sure about. Last I looked it was going out in whatever order the fields got assembled, so it can end up buried a few hundred lines in on a big plan.

Emil

--------------------------------------------------------------

From: dario@world.local
Sent: 11:14

Hi both,

So either we keep plan_format_version where it is and the loader eats the whole document before it knows what it's reading, or we pin it somewhere predictable.

I think the second one. That's a change to plan_document though, and I don't know if anyone wants to touch that this week.

Dario

--------------------------------------------------------------

From: dermot@world.local
Sent: 11:21

Hi all,

Keep the field, it's the right field. It just needs to come out first.

The first key plan_document writes — ahead of the plan body, ahead of the metadata block, ahead of everything. That way the loader reads one key and knows what it's holding.

Not entirely sure how much of the writer that disturbs, but it should be small. The ordering is incidental as far as I can tell.

Dermot

--------------------------------------------------------------

From: gideon@world.local
Sent: 11:23

Hi Dermot,

Ya, that works for me.

But what do I do if its not there tho? Like someone hands me a file from before this and the first key is something else. Do I guess, do I fall back to the oldest parser, um.

Gideon

--------------------------------------------------------------

From: dermot@world.local
Sent: 11:27

Hey Gideon,

Don't guess. If it isn't up front the reader has no business parsing the rest of it.

Bail with something legible and let the caller deal with it. A file that won't say what it is isn't a plan, it's bytes.

Dermot

--------------------------------------------------------------

From: dario@world.local
Sent: 11:31

Hi all,

Mhm, that tracks. No half-parsed plans sitting around looking valid, best we can do is make the error loud.

We can do that when we get to the writer side. I don't think it's this week.

Dario
```

#### `g1.r2.l3`

- **chat** · #cookbooks · **konrad** · 2025-04-11 17:02
- carries `g1.r2.rule`
- must be typed literally: `end_idx`, `requests_0.jsonl`, `start_idx`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> yeah. and a requests_0.jsonl already sitting there gets swept with the rest and rewritten from this run's plan, its own start_idx to end_idx.

As it appears, spread across the exchange:

```
13:02  konrad    Different thread to the reattach stuff. When the batch payload planner writes the request files out, what happens if the working dir is not empty
13:03  konrad    we had a run tuesday that died halfway and left a truncated requests_0.jsonl behind. the rerun did not touch that file at all, just carried on and wrote the other shards. presumably some exists() check decided shard 0 was already done. anyway the batch went out with a short file in it
13:11  emil      let me think through that. the check is per file and per name, which i believe is the wrong granularity. a file existing under that name tells you nothing about whether its rows are the rows this plan wants — the plan gets computed for the whole run at once. so honestly no, a requests_0.jsonl that happens to be sitting there shouldnt earn a pass just because the name lines up with a shard we were going to write
13:19  dario     so its either we validate the leftovers somehow, line counts or a hash or whatever, or we stop treating whats on disk as meaning anything and regenerate the lot. i lean the second to be honest. validating means the plan and the files on disk have to agree on some third thing and thats one more thing to keep in sync for not much gain. in any case whatever the planner computes this run is what ends up in the files, nothing carried over from the previous one
13:24  konrad    right, but concretely the leftover one. is it deleted first or left in place, and does it keep any of the rows it had
13:33  dermot    yeah. the one thats already there goes in the sweep with the rest of them, the matching name doesnt buy it an exemption. then it comes back out written for its own start_idx to end_idx, same as every other shard in the plan. that said if i had to guess the current path never even opens it, so this is a change to the writer rather than a fix to the sweep
13:38  emil      yup. none of that is there today, the writer short circuits on exists() before it looks at the plan at all. we can do that when we get to it, im in the reader half of this for the rest of the week
```

#### `g1.r1.l14`

- **mail** · “auto-sizing branch: sidecar on the fixed batch_size path too?” · **emil** · 2025-04-15 14:03
- to konrad@world.local, gideon@world.local, nikolai@world.local, dario@world.local
- carries `g1.r1.scope`
- must be typed literally: `plan_id`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> Look, if a fixed batch_size run also drops a plan_id file next to the requests, my loader will read that run as auto-sized. Keep it to the auto branch.

As it appears, spread across the thread:

```
From: emil@world.local
Sent: 14:03

Hi all,

Before I start on the auto-sizing branch I have a question about the sidecar.

The plan is to drop a tiny file next to the requests with the plan_id in it, so a resumed run can find its way back to the plan it came from.

Do I write that on both paths, or only when we're auto sizing? Writing it unconditionally is less branching honestly.

Emil

--------------------------------------------------------------

From: nikolai@world.local
Sent: 14:07

Hey Emil,

Fixed path doesnt need it as far as I can tell. You already know the sizing up front so theres nothing to recover.

I mean writing it anyway is harmless from where Im sitting, but I havent looked at what reads it downstream.

Nikolai

--------------------------------------------------------------

From: konrad@world.local
Sent: 14:11

Hi Emil,

Look, if a fixed batch_size run also drops a plan_id file next to the requests, my loader will read that run as auto-sized.

That file is the whole signal on my side, presence or absense of it.

Konrad

--------------------------------------------------------------

From: emil@world.local
Sent: 14:13

Hi Konrad,

Hm, so you're saying the loader never looks at the config at all, just the directory?

Could it not check batch_size and decide from that?

Emil

--------------------------------------------------------------

From: konrad@world.local
Sent: 14:16

The config is not always next to the outputs by then. We get handed the request dir on its own in some cases, so no, not reliably.

Anyway simplest is you keep it to the auto branch and I dont have to guess.

Konrad

--------------------------------------------------------------

From: nikolai@world.local
Sent: 14:18

Yep, that works for me.

Nikolai

--------------------------------------------------------------

From: emil@world.local
Sent: 14:21

Yup, fine. Ill gate it.

Wont be today though, 638 is eating my afternoon. We can do that when we get to it.

Emil
```

#### `g1.r2.l12`

- **chat** · #random · **gideon** · 2025-04-17 13:48
- carries `g1.r2.failure_behavior`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> not just create-on-open though - the oversized-row failure left me staring at an empty working dir, and the split that was in there beforehand was still perfectly usable

As it appears, spread across the exchange:

```
13:11  gideon    unrelated q while im in here — im about to write the working dir bit for the batch payload planner and honestly i dont know which way to go. right now if the dir isnt there it just dies on you. what should it do instead
13:19  dermot    if i had to guess you want it created when the planner opens it. the planner owns that directory, it's the thing that writes the split into it, so making people mkdir it up front is just ceremony. that said i'd keep that in the planner only
13:28  emil      sounds right. not just create-on-open though. let me think through that for a sec — the open path is the easy half, the half i actually care about is what it does on the way out when somehting fails
13:31  gideon    what do you mean on the way out. like what else is there tbh
13:40  emil      the oversized-row failure last month. planner choked on a row over the limit and by the time i got back to the terminal it had tidied up after itself, left me staring at an empty working dir. it wiped the thing it was working in
13:44  dermot    so you're saying it cleared the directory as part of failing. was there anything in there you needed, or was it mid-write and garbage anyway
13:51  emil      no, thats the part that bugs me. the split that was in there beforehand was still perfectly usable — good one from the previous run sitting right there, and it took it out along with everythign else. i'd have just resumed off it
```

#### `g1.r2.l6`

- **mail** · “mail: resumed batch run double-submitted ~400 requests” · **gideon** · 2025-04-17 15:02
- to nikolai@world.local, dermot@world.local, emil@world.local, dario@world.local
- carries `g1.r2.scope`
- must be typed literally: `create_request_files`, `dataset=None`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> i'd say careful there on resume we call create_request_files with dataset=None purely to get the paths back and i'd be unhappy if that call ever started taking files away

As it appears, spread across the thread:

```
From: gideon@world.local
Sent: 15:02

Hi all,

Separate thing. I'm partway into the stale file cleanup.

So basically the plan was create_request_files wipes anything already sitting in the request dir before it writes the new shards, because right now a killed run leaves half written jsonl behind and we happily pick it up next time.

Gideon

--------------------------------------------------------------

From: nikolai@world.local
Sent: 15:07

Hey Gideon,

I'd say careful there. On resume we call create_request_files with dataset=None.

Nikolai

--------------------------------------------------------------

From: dermot@world.local
Sent: 15:11

Hi both,

So on the resume path we're calling it for path derivation rather than to actually produce anything, that the shape of it?

If I had to guess the resumer just wants to know where the files it already wrote live.

Dermot

--------------------------------------------------------------

From: gideon@world.local
Sent: 15:14

Wait, so with dataset None it still goes down the same function?

Tbh I assumed it bails out early and does nothing. Um, that changes my whole plan then.

Gideon

--------------------------------------------------------------

From: nikolai@world.local
Sent: 15:19

Right, it goes through purely to get the paths back. Nothing new gets written on that branch, and I'd be unhappy if that call ever started taking files away.

Nikolai

--------------------------------------------------------------

From: gideon@world.local
Sent: 15:26

Ya fair.

Honestly though the half written shard problem is still real, it bit us twice last month. I'll leave the delete out of there and find another spot for it, i dunno, maybe wherever we decide a run is fresh.

Can do that when I get to it, 632 first.

Gideon
```

#### `g1.r1.l8`

- **chat** · #incidents · **nikolai** · 2025-04-18 11:26
- carries `g1.r1.rule`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> renumberd the batches by hand while poking at a failure and got the identical id back right call i mean the index and num_requests arent in what gets hashed

As it appears, spread across the exchange:

```
13:38  nikolai   dario separate thing but on the batch payload plan side i renumberd the batches by hand yesterday while poking at a failure
13:39  nikolai   and i got the identical id back off it which i wasnt expecting so is that the planner ignoring me or is that on purpose
13:44  dario     mhm that's the digest doing roughly what i had in mind, at least as far as i've sketched it so far. the id comes off the serialized request bodies in order and nothing about how the run happened to get chopped up goes near it
13:47  nikolai   ok but chopped up how far though if i glue two batches together into one of 400 does that move it, im not clear whether the count itself is in there or not
13:51  dario     honestly i havent written that bit yet so this is me deciding it out loud, but the way i want it is the payload is the payload. i think if the size of a batch shifted the id then resuming after anyone touches the sizing would refetch the whole run, which is the exact thing we're trying not to do
13:54  nikolai   right call i mean the index and num_requests arent in what gets hashed then
13:56  dario     that tracks. in any case it's not built yet, i'll keep both out when i get to writing the actual hash
```

#### `g1.r2.l5`

- **chat** · #pipeline · **dario** · 2025-04-21 16:43
- carries `g1.r2.scope`
- must be typed literally: `batch_size`, `incomplete_files`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> sounds right - though the integer batch_size path leans on files from earlier runs, incomplete_files is what skips the finished ones, clear those and every resume starts from zero

As it appears, spread across the exchange:

```
15:02  dario     before i start on the resume path for the auto-sizing branch — the integer batch_size case is the one i keep tripping over. does it build its own request files, or is it just picking up whatever an earlier run left sitting in the working dir? honestly cant tell from reading it
15:07  dermot    if i had to guess it's the latter, and i'm fairly confident actually. the integer batch_size path leans on the files from earlier runs, it doesn't regenerate anything. it walks what's already on disk and shards from there
15:09  gideon    wait so what is the thing that actually decides a file is done though? like if i resume, something has to know not to resubmit the ones that already came back. i dunno where that lives tbh
15:16  emil      sounds right, that matches what i remember of it. and to gideon's point — incomplete_files is what skips the finished ones. it's the list that gets handed forward, anythign already downloaded just drops out of it before we submit
15:19  dario     ok that's the bit i was missing. so then if someone wipes the working dir mid-experiment — does it pick up where it stopped, or does it just start over from nothing?
15:24  emil      clear those and every resume starts from zero, there's nothing else holding the state. which is honestly fine as a default, but we need to be intentional here and put some kind of warning in front of it. can do that when we get to it
15:26  dermot    yeah ok. worth a line in the docstring too, whoever ends up with it
```

#### `g1.r1.l11`

- **chat** · #viewer · **emil** · 2025-04-22 10:12
- carries `g1.r1.rule`, `g1.r1.observability`
- must be typed literally: `PlannedBatch`, `batches`, `dataclasses.asdict`, `index`, `num_batches`, `num_requests`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically the viewer reads num_batches and the request and byte totals straight off the top — and the batches key is one dataclasses.asdict per PlannedBatch, index and num_requests included.

As it appears, spread across the exchange:

```
10:12  emil      im about to wire up the plan panel and i dont know what shape to expect back from the planner. right now i do my own reduce over the batch list just to get a count which feels dumb
10:14  gideon    ya honestly that reduce is the thing i want to kill. so basically the viewer shouldnt be counting anything itself, num_batches sits right at the top of the object next to the totals
10:15  emil      totals meaning what, just the request count?
10:16  gideon    request total and the byte total, both up top. so the header row is three reads and no loop tbh
10:17  emil      ok that covers the header. the table under it still needs per batch rows tho and thats where i got stuck last week — the entries came back as bare lists of request ids, no batch number on them, so i was infering position from array order which falls apart the second anyone sorts the thing
10:19  gideon    right, none of that is written yet, we can do that part when we get to it. but the shape i want is the batches key holding one dataclasses.asdict per PlannedBatch, straight up, nothing hand rolled. which means index comes along for free and you never have to infer position and num_requests too since its already on the dataclass, so your row doesnt have to len() the id list either
10:20  emil      does asdict not choke on the nested request objects
10:21  gideon    it recurses, its fine. i dunno if we want the whole payload in there forever but for now ya, everythign on the dataclass goes out as is
```

#### `g1.r1.l16`

- **chat** · #pipeline · **dermot** · 2025-04-23 17:15
- carries `g1.r1.scope`, `g1.r1.observability`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> same gap on my end - job died writing requests_3.jsonl and nothing on disk said there were supposed to be nine. plan gets written before the first request file.

As it appears, spread across the exchange:

```
15:47  dermot    different thread, but while we're on job records — the resume path on batch jobs. i restarted one on friday and it re-submitted work that had already gone out. if i had to guess, the resumer just globs whatever request files are sitting in the dir and treats that as the full set?
15:56  dario     that's more or less it from what i remember. it sees requests_0 through requests_n and takes n as the end of the run. which is fine right up until the writer gets interrupted, and then honestly there is no way for it to tell a complete set apart from a truncated one, it looks identical on disk
16:04  emil      same gap on my end. had a job die partway through writing requests_3.jsonl back in march and the resume happily picked up from there like nothing was missing. we ended up re-running the whole thing because nobody trusted the output
16:09  dermot    so nothing in that directory told you the run was supposed to be bigger than what was actually sitting there. not a count, not a manifest, nothing
16:13  emil      no. nothing on disk said there were supposed to be nine. the plan holds that number in memory the entire time it's running, it just never survives the process dying, so all you inherit is the files it managed to finish
16:19  gideon    ok so basically its an ordering thing. the plan gets written before the first request file, not at the end. then whatever picks the run back up reads it and knows it wanted nine and only got 3, and it can work out the differnce itself
16:21  gideon    tbh the writer also has to be fine with the plan already being there, otherwise a retry just stomps the one that's on disk
16:27  dario     mhm, that tracks. nobody's in the writer this week though, in any case we can do that when we get to it
```

#### `g1.r1.rev1` · **reversal**

- **chat** · #code-review · **emil** · 2025-04-24 09:38
- carries `g1.r1.rule`, `g1.r1.scope`, `g1.r1.exclusions_or_crossover`
- takes back `g1.r1.h1`
- must be typed literally: `metadata_{i}.json`, `batch_plan.json`, `plan_format_version`, `1`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> a week of resume runs choking on keys they didn't expect, so the plan's out of metadata_{i}.json into a sidecar: batch_plan.json in the working dir, plan_format_version 1, auto branch only

As it appears, spread across the exchange:

```
11:06  emil      ok i need to raise something before dermot's cleanup lands on top of it. i have spent basically the whole week on resume runs and every single one of them died the same way — we open metadata_{i}.json to rebuild the plan and it comes back with keys we never expected. older runs, runs from the branch emil-2 whatever, they all have a slightly different shape in there and the reader just falls over
11:09  dermot    mhm. that is the decision we made though, and i think it is worth saying out loud since it was a while ago: the plan rides in metadata_{i}.json. num_jobs at the top, and then start_idx, end_idx, num_bytes for each batch. no extra file, on the grounds that we already write that metadata per batch so why add one. that said, after this week i do not think it holds
11:11  gideon    ya i mean the metadata file is a dumping ground at this point, everyone who touches it adds a field
11:12  gideon    so what replaces it then, a seperate file that only has the plan in it?
11:17  dario     either we keep teaching the reader every shape we have ever written into that file, or the plan stops living in there entirely, and honestly the second one is the only one that ends. so: pull it out to a sidecar. batch_plan.json, in the working directory alongside everything else we drop there. metadata_{i}.json goes back to being per batch metadata and nothing else, and the resume path never reads it for planning again
11:24  emil      sounds right. two things still open for me though — if we are creating a brand new file lets be intentional about it, because we are going to be reading files written by april-us in november and i do not want to repeat this exact week. so it needs something on it to say what generation it is? and the other one, does the path where the user hands us their own batch sizes write one of these too, or is it just the sizing path
11:31  dario     yeah put plan_format_version in it, and it ships as 1 from the first write, not absent-means-one, absent means somethign is wrong. and it's only the auto sizing branch that writes it — if you gave us the batch boundaries yourself there is no computed plan to record, so no file. best we can do without inventing a schema for user input too
```

#### `g1.r1.l1`

- **chat** · #pipeline · **gideon** · 2025-04-24 10:44
- carries `g1.r1.rule`, `g1.r1.observability`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> so basically someone asked me how tuesday's auto run split and I had to ls the requests_*.jsonl files and re-measure every one of them. that should be sitting on disk.

As it appears, spread across the exchange:

```
10:44  gideon    unrelated to the pbar stuff, sorry. someone asked me this morning how tuesday's auto run actually split up and i could not answer it, at all
10:45  gideon    like the planner decides the sizes at submit time and then... nothing keeps it? or am i missing where it goes
10:53  emil      you mean the per-file request counts the auto sizer landed on, right? i believe nothing persists those. it computes the split, writes the payloads, and moves on. there might be a debug log line if the run had it turned up but Honestly i'm not entirely sure that survives either
10:56  gideon    ya that matches what i found. so basically i had to ls the requests_*.jsonl files in the run dir just to see how many there even were
11:02  emil      and then what, you opened each one? that sounds miserable for a question someone asked in passing
11:05  gideon    wc -l on every single one of them, ya. re-measured all of them by hand just to answer a question. honestly though that whole thing should be sitting on disk already, writen out at the time the plan is made, not somethign you reconstruct three days later
11:09  emil      sounds right. we can do that when we get to it, the planner is queued behind the sizing branch anyway
```

#### `g1.r2.l9`

- **wiki comment** · docs/design/batch-job-status-persistence-across-process-restarts.md · **emil** · 2025-05-02 09:14
- carries `g1.r2.exclusions_or_crossover`
- must be typed literally: `batch_objects.jsonl`, `requests_*.jsonl`, `metadata_*.json`, `responses_*.jsonl`
- find it: open the page — `/api/pages/{id}` returns its `comments`; BookStack search does not index them

What the remark has to leave a reader with:

> Look, the working dir today holds more than those two: requests_*.jsonl, metadata_*.json, responses_*.jsonl, batch_objects.jsonl (submitted batch ids we poll), plus the .arrow shards for the dataset.

As it appears, spread across the exchange:

```
09:14  emil      the page talks about the two stores like that's the whole picture, and i'm the one about to write the resume scan on top of it. so before i start — is responses file + metadata db actually everything a restart has to open, or is that just the part that matters for the cache story?
09:19  konrad    look, the working dir today holds more than those two. off the top of my head there is requests_*.jsonl and metadata_*.json sitting next to each other per batch, and then responses_*.jsonl which is the one the doc is talking about
09:20  konrad    so allready three before you get to anything else. and the naming is per batch so whatever you write has to glob, not stat one path
09:26  emil      ok let me think through that. requests_ is what we serialized out, metadata_ is the per batch record, responses_ is what we accepted back. but none of those tells me a batch is still *open* on the provider side does it — if we die between submit and the first poll i'm guessing. or is the id in metadata_ and i just haven't looked hard enough
09:31  konrad    no that one is batch_objects.jsonl. the submitted batch ids we poll are in there, thats what the poller actually reads. metadata_ is more the accounting side of it
09:33  konrad    and the .arrow shards for the dataset live in the same dir, which nobody counts as state but presumably they are. i would not let a half written shard mean anything to your scan. anyway not entirely sure what the right handling is there
09:41  emil      yup, that was the bit i had backwards, i was going to go read submission ids out of completely the wrong file. the shard question i'll leave alone for now — we need to be intentional there but honestly i'd rather decide it when i actually get to that branch
```

#### `g1.r1.l7`

- **chat** · #pipeline · **dermot** · 2025-05-07 10:09
- carries `g1.r1.rule`, `g1.r1.observability`
- must be typed literally: `plan_id`, `e3b0c44298fc`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> empty plan just hashes the empty string, so plan_id comes out e3b0c44298fc, first twelve of the sha256. no special case needed.

As it appears, spread across the exchange:

```
10:09  dermot    question on the plan builder before i get too far. if the filter drops every row we end up serializing a plan with zero requests in it. do we raise there, or is an empty plan a legitimate thing to hand downstream
10:14  emil      let me think through that. honestly i'd rather not carve out a branch for the empty case. the plan_id is a digest over the serialized plan and an empty plan serialises to an empty string, which sha256 has a perfectly good answer for. so it just hashes the empty string and carries on like any other plan
10:16  dermot    ok. i still need to be able to spot it though — how much of the digest are we actually keeping, and what does the empty one come out as? if it's sitting in a log line i want to recognise it
10:21  emil      first twelve of the sha256 hex, thats all we keep. so the empty one is always e3b0c44298fc, every time. once you've seen it once or twice its pretty unmistakable, if that shows up in the plan_id column you know the filter ate everything upstream. no special case needed, just that value turning up
10:24  dermot    works for me, i'll leave it on the same code path then
10:26  emil      yup. the resume side will need to not choke on a zero-request plan either but thats separate, we can do that when we get to it
```

#### `g1.r1.l4`

- **chat** · #pipeline · **emil** · 2025-05-08 09:14
- carries `g1.r1.exclusions_or_crossover`
- must be typed literally: `metadata_0.json`, `num_jobs`, `num_requests`, `{"num_jobs": n}`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> our resume path json.loads metadata_0.json and expects {"num_jobs": n} and nothing else — n is exactly the plan's num_requests for that batch, so keep the span and byte fields out.

As it appears, spread across the exchange:

```
09:14  emil      before i write the sidecar for the batch payload planner — i was going to dump everything the plan already knows per batch. request span, start/end byte offsets into the jsonl, num_requests. one file per batch. any reason not to?
09:22  dermot    not entirely sure you want all of that in there. the resume path already reads one of those files today, it json.loads metadata_0.json straight off disk and goes looking for a single key. it isn't really a general sidecar, it's closer to a count
09:27  emil      a count of what though. requests we planned into that batch, or jobs that actually came back? those two diverge the second a run half-fails and i'd rather not write the wrong one and find out in three weeks
09:34  dermot    the planned one. n is exactly the num_requests the plan carries for that batch, nothing derived - resume only wants to know how many it was supposed to be looking at
09:36  emil      ok that's easy then. and it tolerates extra keys? i'd put num_jobs first and leave the span + offsets next to it, they're genuinely useful when you're staring at a broken run
09:43  dermot    i'd keep them out. what lands on disk is {"num_jobs": n} and nothing else — the span and the byte fields are useful, agreed, but not to that reader, and i spent a late night with it once. that said, put them in the log line instead and you lose nothing
09:45  emil      yeah ok. log line it is. i'll do the writer side when i get to the planner rewrite
```

#### `g1.r1.l9`

- **chat** · #code-review · **konrad** · 2025-05-22 13:38
- carries `g1.r1.rule`
- must be typed literally: `PLAN_FORMAT_VERSION`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> nit on the plan writer - you've got the 1 inlined in three seperate spots, and PLAN_FORMAT_VERSION is sitting right above it in the same module.

As it appears, spread across the exchange:

```
13:38  konrad    going through the plan writer changes. minor thing, not a blocker - the format version is just typed in as a literal 1 at the point where the header gets serialized. is that on purpose or leftover from the prototype
13:44  nikolai   not on purpose id say and its not just the header, i counted it in three seperate spots in there all writing the same bare 1
13:49  konrad    right so presumably we want a constant for it. do we add one, or is there something already i missed. off the top of my head i dont remeber seeing one when i skimmed
14:02  emil      you didnt miss it exactly, its just not obvious - PLAN_FORMAT_VERSION is already defined, and its sitting right above in the same module. so nothing to introduce, those literals should just be reading it instead of carrying their own copy.  honestly the only reason it reads oddly is the definition and the use are close enough that you skim past both
14:06  nikolai   yep not worth its own PR though whoever is next in that file can fold it in
14:09  konrad    mhm. ill leave it as a nit on the review so it doesnt get lost, anyway we can do that when we get to it
```

#### `g1.r1.f4`

- **chat** · #engineering · **nikolai** · 2025-06-16 13:14
- carries `g1.r1.failure_behavior`
- must be typed literally: `5000`, `1000`, `600`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> 600 rows of 10 bytes plus one 5000 byte row under a 1000 byte cap and it said too fragmented instead of naming row 600. per-row oversize reports first.

As it appears, spread across the exchange:

```
13:14  nikolai   separate thing while i'm not blocked on anyone  the batch payload sizer error is useless when it rejects a run  i got payload too fragmented back and thats the entire message
13:22  emil      let me think through that. "too fragmented" reads like it's complaining about the shape of the batch as a whole rather than any single record, which is fine as a category but not much help to whoever has to fix the input. what did you actually hand it
13:25  nikolai   synthetic corpus  600 rows at 10 bytes each plus one big one  cap was 1000 bytes
13:30  emil      ok so if i'm reading that right the little ones pack down fine and the whole problem is the one record. how far over is it, is it 1200ish and just awkward or is it way out
13:33  nikolai   way out  5000  and the message never says row 600 is the one that cant fit  it just says fragmented and stops
13:41  emil      yeah that's backwards, i believe. before it says anything about fragmentation at all it should walk the rows and report the ones that don't fit on their own — index, size, done — and only then talk about packing if there's still anything left to talk about. we need to be intentional here becaue the per-row oversize report is the part anyone is actually going to read. not urgent, whoever picks up the sizer can do it when we get to it
```

#### `g1.r1.l12`

- **mail** · “Re: Week of Jun 9 recap: bulk inference fix” · **emil** · 2025-06-16 13:24
- to nikolai@world.local, dario@world.local, konrad@world.local, nolan@world.local
- carries `g1.r1.rule`, `g1.r1.observability`
- must be typed literally: `767`, `BatchLimits`, `dataclasses.asdict`, `limits`, `max_batches_per_plan`, `max_bytes_per_batch`, `max_requests_per_batch`
- find it: Roundcube, or IMAP on :143 as worldadmin@world.local

What the remark has to leave a reader with:

> good that limits is dataclasses.asdict of the BatchLimits it planned under, max_requests_per_batch and max_bytes_per_batch and max_batches_per_plan — otherwise 767 bytes tells you nothign a month later

As it appears, spread across the thread:

```
From: emil@world.local
Sent: 13:24

Hi everyone,

Wanted to bring something up while I was getting started on the serializer for the batch payload plan. Half of what I was going to do today is blocked on people who arent here, so I started looking through some of the plan files from the Sunday run.

One of the batches closed out at 767 bytes and I couldnt really tell you why. Was that the cap, was it the request count, or did it just run out of rows to put in? I want to make sure we are being intentional about what actually lands in the JSON before I start putting this together.

Emil

--------------------------------------------------------------

From: nikolai@world.local
Sent: 13:29

Hey Emil,

Yeah thats the gap. Plan needs a limits key sitting next to the batches. Whatever BatchLimits it planned under gets written out with it.

That should give us enough context later to figure out why a batch ended where it did instead of having to infer it from the numbers.

Nikolai

--------------------------------------------------------------

From: emil@world.local
Sent: 13:35

Hi Nikolai,

So limits as in the whole object, not just the one number that happened to bite?

Im thinking dataclasses.asdict on the instance and dropping the dict in as is. One thing Im not entirely sure about though is whether BatchLimits is only per batch stuff. Does it carry the ceiling on how many batches a plan gets too?

Emil

--------------------------------------------------------------

From: nikolai@world.local
Sent: 13:42

Yep, asdict on it. You get max_requests_per_batch and max_bytes_per_batch and max_batches_per_plan out of it, all three.

No reason to write one and leave the others. The plan should capture the full set of limits it was created under.

Nikolai

--------------------------------------------------------------

From: emil@world.local
Sent: 13:47

Yup, sounds right.

Honestly max_batches_per_plan is the one Id have forgotten to include if I was just looking at the batch-level stuff. Its also the one that explains most of the truncations that look wrong at first glance.

Ill make sure that stays in the serialized object.

Emil

--------------------------------------------------------------

From: nikolai@world.local
Sent: 13:54

Right, thats the whole point of it.

767 bytes on its own in a plan file tells you nothign a month later. You want the limits it was planned under sitting right there beside the number.

Nobodys writing the serializer today anyway, so we can do that when we get to it.

Nikolai
```

#### `g1.r1.f3`

- **chat** · #code-review · **emil** · 2025-06-18 13:06
- carries `g1.r1.failure_behavior`
- must be typed literally: `BatchLimits(1, 1000, max_batches_per_plan=2)`, `err.limit == 2`, `err.num_batches == 3`, `max_batches_per_plan`, `num_batches`
- find it: Mattermost search, or the channel on that date

What the remark has to leave a reader with:

> test builds BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes so i dont have to construct 513 spans, then asserts err.num_batches == 3 and err.limit == 2

As it appears, spread across the exchange:

```
13:06  emil      separate from the 691 scope question - the plan level cap has no coverage at all right now. i started sketching a test this morning and stopped, because with the real defaults the only way i can see to actually trip max_batches_per_plan is to hand it a fixture with something like 513 spans in it. honestly that feels like the wrong shape for a unit test
13:12  nikolai   dont use the real defaults then  the limits are a constructor arg for exactly this reason so just pass your own in the test and make them small
13:17  emil      right so you're saying build a limits object with the cap set low, like 2, and then feed it just enough input that it wants a third batch? i'm not entirely sure what the other two numbers should be so the sizing still does something sensible
13:24  nikolai   BatchLimits(1, 1000, max_batches_per_plan=2)  one per batch and a byte ceiling thats never the binding constraint so the count is what splits it then build the plan over three sizes and it wants three batches which is one past the cap  no 513 spans
13:29  emil      sounds right. though i dont want the assertion to just be "it raised" - if we're going to the trouble of raising a typed error it should tell you what it saw versus what it was allowed, and i believe the one that carries the count it wanted is num_batches? let me think through that one
13:35  nikolai   yep  err.num_batches == 3 and err.limit == 2 both on the raised error thats the whole assertion
13:38  emil      yup ok, that's small enough that i can just write it when i circle back to 691 this afternoon
```
