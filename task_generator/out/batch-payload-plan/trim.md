# g1 — the requirement, reduced to what is graded

**750 words → 510** across 10 facts and 63 graded assertions.

The tests, the fact keys and the oracle are untouched. What changed is what the `-spec` arm shows an implementer, and therefore what the clues have to carry.

| fact | words | assertions | dropped |
|---|---|---|---|
| `g1.r1.rule` | 169 → 118 | 16 | 6 |
| `g1.r1.scope` | 71 → 54 | 6 | 4 |
| `g1.r1.exclusions_or_crossover` | 34 → 16 | 2 | 2 |
| `g1.r1.failure_behavior` | 96 → 71 | 11 | 4 |
| `g1.r1.observability` | 117 → 96 | 7 | 3 |
| `g1.r2.rule` | 74 → 22 | 2 | 4 |
| `g1.r2.scope` | 40 → 24 | 6 | 2 |
| `g1.r2.exclusions_or_crossover` | 27 → 13 | 2 | 2 |
| `g1.r2.failure_behavior` | 36 → 18 | 4 | 3 |
| `g1.r2.observability` | 86 → 78 | 7 | 3 |

## `g1.r1.rule`

**Now (118 words):**

`batch_payload_planner` exports `PLAN_FILE_NAME = "batch_plan.json"`, `PLAN_FORMAT_VERSION = 1`, `def plan_fingerprint(plan: Sequence[PlannedBatch]) -> str` and `def plan_document(plan: Sequence[PlannedBatch], limits: BatchLimits) -> dict`. `plan_fingerprint` builds the canonical string `";".join(f"{p.start_idx}-{p.end_idx}:{p.num_bytes}" for p in plan)` — spans and batch sizes only, not `index` or `num_requests` — and returns the FIRST 12 CHARACTERS of its `hashlib.sha256` hexdigest. `plan_document` returns exactly these keys in this order: `plan_format_version` (`1`), `plan_id` (`plan_fingerprint(plan)`), `limits` (`dataclasses.asdict(limits)`), `num_batches` (`len(plan)`), `num_requests` (sum of `p.num_requests`), `num_bytes` (sum of `p.num_bytes`), `batches` (`[dataclasses.asdict(p) for p in plan]`). `BatchLimits` carries a third field `max_batches_per_plan: int = _MAX_BATCHES_PER_PLAN` with the module constant `_MAX_BATCHES_PER_PLAN = 512`. In the `"auto"` branch of `create_request_files`, once `plan_request_batches` has returned, `json.dumps(plan_document(plan, self.batch_limits), indent=2) + "\n"` is written to `os.path.join(self.working_dir, PLAN_FILE_NAME)`.

**Dropped, because no assertion checks it:**

- Opening summary sentence: "The planner module also records the plan it produced." — a topic sentence; no assertion reads it, and the write is specified precisely in the final sentence.
- "encodes it UTF-8 and" — an implementation step of plan_fingerprint that no assertion observes; assertions #4/#5/#6 only compare fingerprints of different plans for equality/inequality.
- The parenthetical "(an empty plan fingerprints the empty string)" — an edge case no assertion exercises.
- In the num_bytes entry, the gloss "the batch files' sizes summed, not any on-disk size" — a restatement of "sum of `p.num_bytes`"; assertion #14 checks exactly that sum.
- In the batches entry, "five keys each in field order" — a restatement of what dataclasses.asdict already does; assertion #16 pins the key list, and PlannedBatch's field order is pre-existing.
- "so `limits` serialises with three keys while `BaseBatchRequestProcessor.batch_limits` still constructs `BatchLimits` from the two provider limits only" — a "so" consequence clause; assertion #11 compares doc["limits"] to dataclasses.asdict(limits), which holds for any field set.

**Kept despite looking like padding:** `BatchLimits carries a third field max_batches_per_plan: int = _MAX_BATCHES_PER_PLAN with the module constant _MAX_BATCHES_PER_PLAN = 512` reads like unasserted detail — #11 (`doc["limits"] == dataclasses.asdict(limits)`) is tautological in the field set — but the test fixture must construct a `BatchLimits` to pass as `limits`, and if it does so with three arguments a two-field dataclass raises at fixture time and every one of #8–#17 errors out. The FIRST 12 CHARACTERS / hashlib.sha256 clause is likewise not read directly by any listed assertion (#7 is absent), but it is what makes plan_fingerprint deterministic and its result a JSON-serialisable string, which #10 and #17 (json.dumps round-trip of plan_id) depend on.

## `g1.r1.scope`

**Now (54 words):**

The sidecar is written in the `"auto"` branch only, before any request file is written, and for a 0-batch plan (empty dataset → a `batch_plan.json` with `num_batches: 0`, `num_requests: 0`, `num_bytes: 0`, `batches: []` and `plan_id` of the empty canonical string). The explicit-integer `batch_size` branch and the `dataset is None` path never write it.

**Dropped, because no assertion checks it:**

- ": with `batch_size=2` on a 3-row dataset, `"batch_plan.json" not in os.listdir(working_dir)`" — a worked example of the never-writes rule the same sentence already states; assertions #6 and #7 check the absence of PLAN_FILE_NAME in a listing, which the rule alone pins, and no assertion uses a 3-row dataset or batch_size=2.
- "or metadata file" — no assertion observes metadata-file ordering; assertion #2 checks only that the plan exists when the request files are written.
- "it is written" (in "and it is written for a 0-batch plan too") — restatement of "is written" from the same sentence's opening clause.
- "too" — emphasis particle, nothing checks it.

**Kept despite looking like padding:** `batch_plan.json` looks redundant beside the 0-batch parenthetical, but assertions #6 and #7 read `module.PLAN_FILE_NAME` against a directory listing, so the literal filename stays. The four-key list with its exact values and order is read verbatim by assertion #4, and \"`plan_id` of the empty canonical string\" is the only thing forcing `plan_fingerprint([])` in assertion #5. \"before any request file is written\" survives as the whole of assertion #2.

## `g1.r1.exclusions_or_crossover`

**Now (16 words):**

`metadata_{i}.json` is untouched by this: its body stays exactly `{"num_jobs": n}` with no `start_idx`/`end_idx`/`num_bytes` keys added.

**Dropped, because no assertion checks it:**

- The sidecar is the single place the plan shape is recorded — a restatement of the same exclusion rule in other words; no assertion reads a sidecar.
- because `_verify_existing_request_files` cannot describe an "auto" run — pure rationale; no assertion checks _verify_existing_request_files or the "auto" mode.

**Kept despite looking like padding:** "with no `start_idx`/`end_idx`/`num_bytes` keys added" reads like elaboration of "stays exactly `{"num_jobs": n}`", but assertion #1 checks `set(metadata) == {"num_jobs"}` and those are the exact key names an implementer would otherwise add. The body shape and `n` are also what assertion #2 (`metadata["num_jobs"] == read_field(planned, "num_requests")`) turns on.

## `g1.r1.failure_behavior`

**Now (71 words):**

`len(plan) > limits.max_batches_per_plan` raises `BatchPlanTooFragmentedError(num_batches=..., limit=...)`, exported from the same module, storing both as attributes; it subclasses `ValueError` but is NOT a `BatchPayloadTooLargeError`. `plan_batches([10]*512, BatchLimits(max_requests_per_batch=1, max_bytes_per_batch=1000))` returns 512 batches; `[10]*513` raises with `err.num_batches == 513`, `err.limit == 512`; an explicit `BatchLimits(1, 1000, max_batches_per_plan=2)` on `[10]*3` raises with `err.num_batches == 3`, `err.limit == 2`. The per-row oversize scan runs first, so `plan_batches([10]*600 + [5000], BatchLimits(1, 1000))` raises `SingleRequestTooLargeError` with `err.row_idx == 600`.

**Dropped, because no assertion checks it:**

- "After `plan_batches` has built the whole plan and before it returns" — where in the function the check sits; nothing distinguishes a check after the plan is built from one taken during, all four examples grade the same either way.
- "<the full count the plan would have needed>" and "<the limit>" — glosses on the two kwargs. The graded values are the literals `err.num_batches == 513`, `err.limit == 512` and `(3, 2)`, which stay verbatim.
- "(the boundary is admissible)" — rationale restating "returns 512 batches", which is all #4 checks.
- ", not `BatchPlanTooFragmentedError`" — restatement for emphasis; #10 only asserts `SingleRequestTooLargeError` is raised, and "The per-row oversize scan runs first" already states the ordering rule.

**Kept despite looking like padding:** "storing both as attributes" looks like padding beside the constructor signature, but #6, #7 and #9 read `num_batches` and `limit` off the caught exception, so naming them as kwargs alone would not force them onto the instance. All three worked examples survive because each pins a different assertion: 512 → #4, 513 → #5–#7, the explicit `max_batches_per_plan=2` → #8–#9, the 600-row dataset → #10–#11. "exported from the same module" is held by #1, and the `ValueError` / not-`BatchPayloadTooLargeError` clause by #2 and #3.

## `g1.r1.observability`

**Now (96 words):**

`plan_fingerprint([]) == "e3b0c44298fc"`; `plan_fingerprint(plan_batches([10]*7, BatchLimits(1000, 32))) == "ad0828fea95e"`; `plan_fingerprint([PlannedBatch(0,0,2,2,307), PlannedBatch(1,2,4,2,307), PlannedBatch(2,4,5,1,153)]) == "f4b1ea1573c0"`; the 11-batch plan of an 11-row dataset with `max_requests_per_batch` patched to `1` fingerprints `"c53f6fb95c13"`. After the 5-row OpenAI run with limits patched to `3`/`400`, `json.load(open(f"{working_dir}/batch_plan.json"))` equals exactly `{"plan_format_version": 1, "plan_id": "f4b1ea1573c0", "limits": {"max_requests_per_batch": 3, "max_bytes_per_batch": 400, "max_batches_per_plan": 512}, "num_batches": 3, "num_requests": 5, "num_bytes": 767, "batches": [{"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307}, {"index": 1, "start_idx": 2, "end_idx": 4, "num_requests": 2, "num_bytes": 307}, {"index": 2, "start_idx": 4, "end_idx": 5, "num_requests": 1, "num_bytes": 153}]}`, with the raw file text ending in `"]\n}\n"`.

**Dropped, because no assertion checks it:**

- Opening framing sentence: "Exact strings and one exact document." — a summary of what follows; no assertion checks it.
- "with `list(doc) == [\"plan_format_version\", \"plan_id\", \"limits\", \"num_batches\", \"num_requests\", \"num_bytes\", \"batches\"]`" — no assertion reads key ordering (#6 is a dict equality, which ignores order), and the same ordering is already spelled out by the exact document literal that stays, so this was a restatement.
- "and `BatchLimits(1000, 32).max_batches_per_plan == 512`" — #6 builds its expected `limits` from the implementation's own object and its comment says the fan-out cap is graded once under failure_behavior, not here; #7 checks only `max_requests_per_batch` and `max_bytes_per_batch`.

**Kept despite looking like padding:** All four fingerprint examples stay: they are four separate assertions (#1, #2, #3, #5), each turning on its own digest literal, so none is a redundant second example of one rule. The whole `batch_plan.json` literal stays verbatim for #6 and is most of the remaining word count — including `"max_batches_per_plan": 512` inside it, which #6 does not grade directly but which the document literal cannot be cut apart without corrupting the one exact document. The `3`/`400` patch clause stays for #7, and the trailing-text clause for #8. This is why the result lands near 94 words rather than 81.

## `g1.r2.rule`

**Now (22 words):**

In the `"auto"` branch of `create_request_files`, before anything new is written, every existing `requests_*.jsonl` and every existing `metadata_*.json` in `self.working_dir` is removed.

**Dropped, because no assertion checks it:**

- "after `plan_request_batches(dataset)` has returned" — a second ordering anchor; nothing is asserted about when the planning call returns relative to the removal, only that removal precedes the new writes.
- "(`glob.glob` + `os.remove`)" — names the removal mechanism; the assertions read only the resulting directory listing, never how the files went away.
- "A previous `"auto"` run under different limits leaves a longer numbering behind (e.g. `requests_0..5.jsonl` for a new plan of 3), and those stale files are what a later glob-based read would pick up," — history plus a worked example whose literals no assertion turns on; both assertions compare against `range(len(plan))` for whatever plan the run produced.
- "so the branch clears them rather than overwriting only the prefix." — the "so" clause giving the reason, and a restatement of the removal rule the first sentence already states.

**Kept despite looking like padding:** "before anything new is written" reads like scene-setting but is load-bearing: both assertions require requests_{i}.jsonl and metadata_{i}.json for i in range(len(plan)) to be present at the end, so a removal that ran after the writes would empty the directory and fail them. `self.working_dir` and both glob patterns stay verbatim because the assertions glob exactly those two patterns in that directory.

## `g1.r2.scope`

**Now (24 words):**

Sweeping belongs to the `"auto"` branch alone. The explicit-integer `batch_size` branch does not sweep, and the `dataset is None` path does not sweep either.

**Dropped, because no assertion checks it:**

- "it still relies on `incomplete_files`" — rationale for why the explicit-integer branch does not sweep; no assertion reads `incomplete_files` or checks what any branch relies on.
- "and may legitimately leave earlier request files in place" — a restatement of "does not sweep" in other words; the word "legitimately" is justification, not rule.

**Kept despite looking like padding:** "Sweeping belongs to the `\"auto\"` branch alone" is not directly asserted, but it is the only statement that sweeping happens anywhere; without it the two negatives have no positive counterpart and an implementer could satisfy #1–#6 by never sweeping at all. Both branch identifiers stay verbatim: #1–#3 target the explicit-integer `batch_size` branch's `fixed_dir` and #4–#6 target the `dataset is None` path's `none_dir`, and the file names `requests_{i}.jsonl` / `metadata_{i}.json` (including `requests_5.jsonl` and `requests_3.jsonl`) are exactly what the assertions stat and read.

## `g1.r2.exclusions_or_crossover`

**Now (13 words):**

`responses_*.jsonl`, `*.arrow`, `batch_objects.jsonl` and every other file in the working directory survive byte-for-byte.

**Dropped, because no assertion checks it:**

- "Only those two glob patterns are removed." — the same rule stated from the removal side; no assertion reads it, and the two patterns are named elsewhere in the requirement.
- "; the sweep is not a directory wipe" — a restatement for emphasis of "every other file ... survive", which the assertions already pin.

**Kept despite looking like padding:** The three literal names and "every other file in the working directory" stay because assertion #1 does `name in after` for each of them; "survive byte-for-byte" stays because assertion #2 compares `after[name] == body`, so mere presence would not pin it.

## `g1.r2.failure_behavior`

**Now (18 words):**

If planning raises — `SingleRequestTooLargeError` — the working directory is byte-for-byte what it was, stale files and all.

**Dropped, because no assertion checks it:**

- "The sweep sits behind a plan that returned." — framing/rationale for why the failure path exists; no assertion checks it.
- "or `BatchPlanTooFragmentedError`" — a second exception name that no assertion raises, catches, or inspects; the one graded name, `SingleRequestTooLargeError`, is kept verbatim.
- "nothing is removed and nothing is written, so" — the mechanism-plus-"so" restatement of the surviving rule; `snapshot(working_dir) == before` grades the byte-for-byte outcome, not the cause.

**Kept despite looking like padding:** "stale files and all" reads like flourish but stays: it is the only wording that rules out cleaning up pre-existing files on the failure path, which `assert snapshot(working_dir) == before` would catch. One gap I could not close by deleting — assertion #3 reads `read_field(caught.value, "row_idx") == 1`, and neither the original text nor the trim names `row_idx`; supplying it would be a rewrite, not a cut.

## `g1.r2.observability`

**Now (78 words):**

`working_dir` pre-populated with `requests_0.jsonl … requests_5.jsonl` (each `"stale\n"`), `metadata_0.json … metadata_5.json` and `responses_0.jsonl` (`"keep\n"`). After the successful 5-row run with limits patched to `3`/`400`: `sorted(os.listdir(working_dir)) == ["batch_plan.json", "metadata_0.json", "metadata_1.json", "metadata_2.json", "requests_0.jsonl", "requests_1.jsonl", "requests_2.jsonl", "responses_0.jsonl"]` and `open(f"{working_dir}/responses_0.jsonl").read() == "keep\n"`. Against the same directory plus a stale `batch_plan.json` holding `{"plan_format_version": 1, "stale": true}`, `create_request_files(Dataset.from_dict({"prompt": ["ok", "x"*600, "ok"]}))` with `max_bytes_per_batch` patched to `400` raises `SingleRequestTooLargeError` and all 14 entries survive, with `json.load(open(f"{working_dir}/batch_plan.json")) == {"plan_format_version": 1, "stale": True}` and `open(f"{working_dir}/requests_2.jsonl").read() == "stale\n"`.

**Dropped, because no assertion checks it:**

- (each `"{}\n"`) — the pre-populated metadata file contents. No assertion opens a metadata_*.json; only their names are read, in the two listings.
- — 8 entries — a restatement of the eight-name listing literal that immediately precedes it.
- (row_idx=1, size_bytes=748, limit_bytes=400) — the error's constructor arguments. Assertions #3 and #4 are bare `pytest.raises(module.SingleRequestTooLargeError)`; neither the row index, the 748 nor the 400 on the exception is inspected.

**Kept despite looking like padding:** The eight-name good-dir listing stays whole even though assertion #1 checks only seven of them (its `listing` helper drops `batch_plan.json`) — the other seven names and their order are read verbatim. `"stale\n"` and `"keep\n"` in the setup stay: #7 reads `requests_2.jsonl` as `STALE_REQUEST` and #2 reads `responses_0.jsonl`. `{"plan_format_version": 1, "stale": true}` is stated twice, as setup and as survival check, but the setup literal is what #6 ends up comparing against. "all 14 entries survive" reads like a summary but is the only statement of #5.
