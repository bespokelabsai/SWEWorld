# Was every graded thing said, or only implied? — g1

**55 of 69** assertions rest on something a remark says outright.

- `stated` **55** — a reader was told
- `implied` **10** — a reader has to work it out, and may not
- `absent` **0** — nothing in the corpus bears on it
- `not_required` **4** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g1.r1.exclusions_or_crossover#1` | stated | `g1.r1.l4`, `g1.r1.h1`, `g1.r1.h2` | dermot (l4) says outright that the resume path expects metadata_0.json to be `{"num_jobs": n}` and nothing else and asks that the span and byte fields be kept out, overturning the earlier h1/h2 plan-i |
| `g1.r1.exclusions_or_crossover#2` | **implied** | `g1.r1.l8`, `g1.r1.l4`, `g1.r1.h2` | num_requests is only named in passing as a per-batch field excluded from the hash (l8) and num_jobs only as the metadata body (l4); nobody states that the plan's per-batch num_requests must equal the  |
| `g1.r1.failure_behavior#1` | stated | `g1.r1.f2`, `g1.r1.f1` | konrad names BatchPlanTooFragmentedError outright as a thing his handler met at runtime, and gideon establishes the planner should refuse past a ceiling. |
| `g1.r1.failure_behavior#10` | stated | `g1.r1.f4` | f4 gives the dataset (600 ten-byte rows plus a 5000-byte row under a 1000-byte cap) and the ordering ruling "per-row oversize reports first" as a correction to it reporting fragmentation. |
| `g1.r1.failure_behavior#11` | stated | `g1.r1.f4` | f4 says the error should be "naming row 600", fixing both that the row index is carried and that its value is 600. |
| `g1.r1.failure_behavior#2` | stated | `g1.r1.f2` | f2 says in so many words "it is its own ValueError". |
| `g1.r1.failure_behavior#3` | stated | `g1.r1.f2` | f2 reports that an `except BatchPayloadTooLargeError` sailed straight past it and calls that the right call, which is the non-subclassing decision made out loud. |
| `g1.r1.failure_behavior#4` | stated | `g1.r1.f2`, `g1.r1.f3` | f2 pins the default cap at 512 with 513 as the failing count, and f3's "so i dont have to construct 513 spans" independently fixes 513 as the first inadmissible count, leaving 512 admissible. |
| `g1.r1.failure_behavior#5` | stated | `g1.r1.f2` | f2 reports exactly the 513-batches-against-limit-512 case raising BatchPlanTooFragmentedError. |
| `g1.r1.failure_behavior#6` | stated | `g1.r1.f3`, `g1.r1.f2` | f3 gives the attribute name verbatim as err.num_batches and f2 gives the 513 count for the default-limit case. |
| `g1.r1.failure_behavior#7` | **implied** | `g1.r1.f2`, `g1.r1.f3` | the value 512 is stated but nobody ever writes err.limit — the reader must decide on their own that f2's prose "limit 512" is the attribute name rather than max_batches_per_plan, the only field name f |
| `g1.r1.failure_behavior#8` | stated | `g1.r1.f3` | f3 describes precisely this test: BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes tripping the fragmented error. |
| `g1.r1.failure_behavior#9` | stated | `g1.r1.f3`, `g1.r1.f2` | f3 states the assertion err.num_batches == 3 for that exact construction, and the reported cap of 2 is the max_batches_per_plan it names in the same sentence. |
| `g1.r1.observability#1` | stated | `g1.r1.l7` | emil gives the empty-plan case outright: it hashes the empty string and plan_id comes out e3b0c44298fc, first twelve of the sha256, no special case. |
| `g1.r1.observability#2` | stated | `g1.r1.l6`, `g1.r1.l7`, `g1.r1.l8` | The whole recipe is said out loud — start-end:num_bytes per batch joined on semicolons, first twelve hex of sha256, with index and num_requests deliberately excluded — so a reader following it lands o |
| `g1.r1.observability#3` | stated | `g1.r1.l6` | dario quotes this exact five-row case, the exact hashed string 0-2:307;2-4:307;4-5:153, and the exact result f4b1ea1573c0. |
| `g1.r1.observability#4` | n/a | — | This is the suite guarding its own fixture (11 rows at one batch each) and its message says so; the corpus owes it nothing. |
| `g1.r1.observability#5` | stated | `g1.r1.l6`, `g1.r1.l7`, `g1.r1.l8` | Same fully-specified fingerprint recipe — span string joined on semicolons, sha256 truncated to twelve, index/num_requests left out — determines this digest for the one-row-per-batch plan. |
| `g1.r1.observability#6` | **implied** | `g1.r1.l10`, `g1.r1.l11`, `g1.r1.l12`, `g1.r1.l8`, `g1.r1.h1`, `g1.r1.h2`, `g1.r1.l6`, `g1.r1.l9` | Every ingredient is mentioned somewhere — version first, plan_id, recorded caps, top-level totals, per-batch spans and bytes — but nobody ever writes the document out, so the reader must supply the to |
| `g1.r1.observability#7` | stated | `g1.r1.l12`, `g1.r1.f3` | nikolai says the plan file records the caps it planned under, naming that run's 3 requests and 400 bytes, and BatchLimits is referred to by its keyword fields elsewhere. |
| `g1.r1.observability#8` | stated | `g1.r1.l3` | konrad's fix is literally 'dump it with indent 2 and end the file with a newline', which is exactly the trailing "]\n}\n" the assertion checks. |
| `g1.r1.rule#1` | stated | `g1.r1.l2`, `g1.r1.l9`, `g1.r1.l6`, `g1.r1.l10` | All four exported names are spelled out in passing — PLAN_FILE_NAME (l2), PLAN_FORMAT_VERSION (l9), plan_fingerprint (l6), plan_document (l10) — as things living in the planner module. |
| `g1.r1.rule#10` | stated | `g1.r1.l7`, `g1.r1.l6` | l7 says plan_id is the first twelve of the sha256 of the hashed string, which is exactly what l6 describes plan_fingerprint returning. |
| `g1.r1.rule#11` | **implied** | `g1.r1.l12`, `g1.r1.l2` | l12 only says the file should record the caps it planned under and names two of them, leaving the key name and the whole-dataclass asdict form (including max_batches_per_plan) for the reader to settle |
| `g1.r1.rule#12` | stated | `g1.r1.l11`, `g1.r1.l13` | l11 asks for num_batches off the top of the file and l13 names it directly (num_batches 0 for a zero-row run). |
| `g1.r1.rule#13` | stated | `g1.r1.l11` | l11 asks for the request total at the top level precisely so the viewer does not walk batches and sum them itself. |
| `g1.r1.rule#14` | stated | `g1.r1.l11`, `g1.r1.l12` | The same remark asks for the byte total off the top, and l12 quotes a run's aggregate byte figure as something the file carries. |
| `g1.r1.rule#15` | **implied** | `g1.r1.l11`, `g1.r1.l1`, `g1.r1.l16`, `g1.r1.h2` | A per-batch list is clearly wanted and l11 calls it batches, but nobody says each entry is the full PlannedBatch dict — the only per-batch shape ever written down (h2) has four fields and a different  |
| `g1.r1.rule#16` | **implied** | `g1.r1.l8`, `g1.r1.h2`, `g1.r1.h1` | No remark lists a batch entry's keys; the reader has to decide that all five dataclass fields including index and num_requests survive into the file, against h1/h2's narrower four-field shape. |
| `g1.r1.rule#17` | stated | `g1.r1.l14`, `g1.r1.l1`, `g1.r1.l16`, `g1.r1.l3`, `g1.r1.l10` | The auto-branch-only placement (l14), the on-disk plan file (l1, l16), the indent-2-plus-newline dump (l3) and plan_document as the thing that writes the keys (l10) are each decided out loud. |
| `g1.r1.rule#2` | stated | `g1.r1.l2` | l2 writes the assignment verbatim: PLAN_FILE_NAME = "batch_plan.json". |
| `g1.r1.rule#3` | stated | `g1.r1.l9`, `g1.r1.l10` | l9's nit is precisely that the literal 1 is inlined where PLAN_FORMAT_VERSION already sits, which names the constant's value. |
| `g1.r1.rule#4` | stated | `g1.r1.l8` | l8 reports renumbering batches by hand and getting the identical id, and says outright that index and num_requests are not in what gets hashed. |
| `g1.r1.rule#5` | stated | `g1.r1.l6` | l6 gives the canonical string as start-end:num_bytes per batch, so byte counts are part of what is hashed. |
| `g1.r1.rule#6` | stated | `g1.r1.l6` | The same remark fixes the spans in the hashed string, so moving a cut changes the fingerprint. |
| `g1.r1.rule#7` | n/a | `g1.r1.l6`, `g1.r1.l12` | This guards the suite's own fixture, and the corpus happens to corroborate it anyway (five rows at 3/400 giving three batches). |
| `g1.r1.rule#8` | **implied** | `g1.r1.l10`, `g1.r1.l11`, `g1.r1.l12`, `g1.r1.l7` | Only the first key is pinned by l10; the reader must assemble the remaining six from scattered mentions and then guess their relative order and that nothing else is present. |
| `g1.r1.rule#9` | stated | `g1.r1.l10`, `g1.r1.l9` | l10 names the key plan_format_version in the document and l9 fixes its value at 1. |
| `g1.r1.scope#1` | stated | `g1.r1.l1`, `g1.r1.l2`, `g1.r1.l14`, `g1.r1.l16`, `g1.r1.l13` | l2 names PLAN_FILE_NAME = "batch_plan.json" and l14 says outright to keep the plan file to the auto branch, with l1/l16 demanding it be on disk for auto runs. |
| `g1.r1.scope#2` | stated | `g1.r1.l16` | l16 says in as many words that the plan gets written before the first request file, because a job died mid-write with nothing on disk saying how many were expected. |
| `g1.r1.scope#3` | **implied** | `g1.r1.l13` | l13 only says a zero row auto run leaves the working dir empty; the reader must supply that create_request_files therefore returns an empty list rather than, say, one empty request file. |
| `g1.r1.scope#4` | stated | `g1.r1.l13`, `g1.r1.l11` | l13 commits to writing the file regardless with num_batches 0, and l11 fixes num_batches plus the request and byte totals as top-of-file fields alongside batches, which for a zero row run are all empt |
| `g1.r1.scope#5` | stated | `g1.r1.l7`, `g1.r1.l6` | l7 says the empty plan hashes the empty string with no special case, giving plan_id e3b0c44298fc, which is exactly plan_fingerprint([]). |
| `g1.r1.scope#6` | stated | `g1.r1.l14` | l14 objects to a fixed batch_size run dropping a plan file next to the requests and rules that it stay in the auto branch. |
| `g1.r1.scope#7` | stated | `g1.r1.l15` | l15 says the dataset-None online path has nothing to plan and leaves the working dir alone on that route. |
| `g1.r2.exclusions_or_crossover#1` | stated | `g1.r2.h1`, `g1.r2.h2`, `g1.r2.l10`, `g1.r2.l11`, `g1.r2.l9`, `g1.r2.l8` | h1/h2 define the sweep's scope out loud as exactly requests_*.jsonl and metadata_*.json, l9 enumerates the other inhabitants of the dir, and l10 ("batch_objects.jsonl ... it stays put") and l11 (dropp |
| `g1.r2.exclusions_or_crossover#2` | **implied** | `g1.r2.l13`, `g1.r2.l2`, `g1.r2.l10` | Nobody says the survivors' contents must be identical after the sweep — l13 forbids changing anything on disk only for a run that raises in the estimate step, and l2 merely observes a stale metadata f |
| `g1.r2.failure_behavior#1` | n/a | `g1.r2.l4`, `g1.r2.l15`, `g1.r2.l9` | This is the suite checking the shape of its own seeded fixture (a file count), not behaviour the implementation must produce, though l4 and l15 do name most of the seeded files. |
| `g1.r2.failure_behavior#2` | stated | `g1.r2.l14` | Nikolai says outright that with max_bytes_per_batch pinned to 400 and a 600 char prompt the planning call raises SingleRequestTooLargeError. |
| `g1.r2.failure_behavior#3` | **implied** | `g1.r2.l14` | l14 names row 1 as the offender, but nobody says the raised exception carries the offending row index as a readable field, so the reader must supply that the error exposes row_idx at all. |
| `g1.r2.failure_behavior#4` | stated | `g1.r2.l14` | Same explicitly stated failure mode as #2 — the oversized single row makes planning raise SingleRequestTooLargeError. |
| `g1.r2.failure_behavior#5` | stated | `g1.r2.l13`, `g1.r2.l12` | Dermot states the rule directly — a run that raises in the estimate step has no business having changed anything on disk, stale or not — and Emil complains about exactly the oversized-row failure empt |
| `g1.r2.observability#1` | stated | `g1.r2.h1`, `g1.r2.h2`, `g1.r2.l4`, `g1.r2.l3`, `g1.r2.l8` | h1 and h2 both name the exact cleanup scope (requests_*.jsonl and metadata_*.json, on entry), l4 seeds six pairs and says the post-run listing is the assertion, and l8 marks responses_0.jsonl as the f |
| `g1.r2.observability#2` | stated | `g1.r2.h1`, `g1.r2.h2`, `g1.r2.l8`, `g1.r2.l9` | The delete list is enumerated twice and excludes responses, and l8 spells out the concrete cost of a sweep that took responses_0.jsonl with it, so preserving its contents is what the reader was told t |
| `g1.r2.observability#3` | stated | `g1.r2.l14` | l14 gives the error class by name together with the 400-byte limit and 600-char prompt that trigger it. |
| `g1.r2.observability#4` | stated | `g1.r2.l14`, `g1.r2.l15` | Same remark names SingleRequestTooLargeError and its trigger, and l15 puts the stale plan in the directory the second raise runs against. |
| `g1.r2.observability#5` | stated | `g1.r2.l13`, `g1.r2.l12`, `g1.r2.l4` | l13 states outright that a run raising in the estimate step must have changed nothing on disk, 'stale or not', which is exactly the surviving 14 entries l4's seeding produces. |
| `g1.r2.observability#6` | stated | `g1.r2.l15`, `g1.r2.l13` | l15 fixes the stale plan_format_version 1 body as already present and l13 says a run that never gets a plan out the other end leaves disk untouched, so the file is neither rewritten nor removed. |
| `g1.r2.observability#7` | stated | `g1.r2.l13`, `g1.r2.l4`, `g1.r2.l12` | l13's 'has no business having changed anything on disk' covers contents and not merely presence, and l12 reinforces that the pre-existing split must remain usable after the oversized-row failure. |
| `g1.r2.rule#1` | n/a | — | This is a self-check on the suite's own fixture (five rows must plan between one and five batches), not a behaviour the corpus owes anyone. |
| `g1.r2.rule#2` | stated | — | h1 and h2 both say outright that the auto branch clears out requests_*.jsonl on entry before plan_request_batches runs, and l4 describes exactly the seeded 0-5 / plan-makes-three listing check. |
| `g1.r2.rule#3` | stated | — | h1 and h2 name metadata_*.json alongside requests_*.jsonl as what gets deleted first, and l2/l4 confirm stale metadata_N.json is the thing being complained about. |
| `g1.r2.rule#4` | stated | — | The sweep h1/h2 describe globs requests_*.jsonl, which includes requests_0.jsonl, so the file must be regenerated by the new run; l3 restates that the dir should hold what the run actually produced. |
| `g1.r2.scope#1` | stated | `g1.r2.l7`, `g1.r2.l5` | dario fences the explicit batch_size branch off from the new behaviour by name and emil says clearing those earlier-run files breaks resume, so keeping requests_i.jsonl in that branch is a decision ma |
| `g1.r2.scope#2` | stated | `g1.r2.l7`, `g1.r2.l5` | the same two remarks cover the metadata files, which l5 pairs with requests as the earlier-run state incomplete_files reads. |
| `g1.r2.scope#3` | stated | `g1.r2.l5`, `g1.r2.l7` | l5 makes the contents of earlier-run files load-bearing for resume, and l7 says the branch keeps behaving exactly as it always has, so leaving a stale requests_5.jsonl untouched is told, not inferred. |
| `g1.r2.scope#4` | stated | `g1.r2.l6` | nikolai says the dataset=None call exists purely to get the paths back and must never start taking files away, which is this assertion. |
| `g1.r2.scope#5` | stated | `g1.r2.l6` | the same remark forbids that call removing anything, with no exception carved out for metadata. |
| `g1.r2.scope#6` | stated | `g1.r2.l6` | a call described as existing purely to return paths writes nothing, so the stale body of requests_3.jsonl surviving follows from what nikolai committed to. |

### `g1.r1.exclusions_or_crossover#2` — implied

```python
assert metadata["num_jobs"] == read_field(planned, "num_requests")
```

num_requests is only named in passing as a per-batch field excluded from the hash (l8) and num_jobs only as the metadata body (l4); nobody states that the plan's per-batch num_requests must equal the batch's metadata num_jobs, so the reader has to infer the two counts are the same number.

### `g1.r1.failure_behavior#7` — implied

```python
assert read_field(caught.value, "limit") == 512
```

the value 512 is stated but nobody ever writes err.limit — the reader must decide on their own that f2's prose "limit 512" is the attribute name rather than max_batches_per_plan, the only field name f3 actually shows.

### `g1.r1.observability#6` — implied

```python
assert doc == {
        "plan_format_version": 1,
        "plan_id": "f4b1ea1573c0",
        # taken from the implementation's own limits, so the fan-out cap is graded once,
        # under failure_behavior, and not a second time here
        "limits": json.loads(json.dumps(dataclasses.asdict(limits))),
        "num_batches": 3,
        "num_requests": 5,
        "num_bytes": 767,
        "batches": [
            {"index": 0, "start_idx": 0, "end_idx": 2, "num_requests": 2, "num_bytes": 307},
            {"index": 1, "start_idx": 2, "end_idx": 4, "num_requests": 2, "num_bytes": 307},
            {"index": 2, "start_idx": 4, "end_idx": 5, "num_requests": 1, "num_bytes": 153},
        ],
    }
```

Every ingredient is mentioned somewhere — version first, plan_id, recorded caps, top-level totals, per-batch spans and bytes — but nobody ever writes the document out, so the reader must supply the top-level "batches" and "limits" key names and the five per-batch key names (notably index and num_requests, which h1/h2 called num_jobs in a file l4 later strips).

### `g1.r1.rule#11` — implied

```python
assert doc["limits"] == dataclasses.asdict(limits)
```

l12 only says the file should record the caps it planned under and names two of them, leaving the key name and the whole-dataclass asdict form (including max_batches_per_plan) for the reader to settle.

### `g1.r1.rule#15` — implied

```python
assert doc["batches"] == [dataclasses.asdict(p) for p in plan]
```

A per-batch list is clearly wanted and l11 calls it batches, but nobody says each entry is the full PlannedBatch dict — the only per-batch shape ever written down (h2) has four fields and a different name for the count.

### `g1.r1.rule#16` — implied

```python
assert list(doc["batches"][0]) == ["index", "start_idx", "end_idx", "num_requests", "num_bytes"], f"a batch entry's keys are {list(doc['batches'][0])}"
```

No remark lists a batch entry's keys; the reader has to decide that all five dataclass fields including index and num_requests survive into the file, against h1/h2's narrower four-field shape.

### `g1.r1.rule#8` — implied

```python
assert list(doc) == ["plan_format_version", "plan_id", "limits", "num_batches", "num_requests", "num_bytes", "batches"], f"the sidecar's envelope is {list(doc)}"
```

Only the first key is pinned by l10; the reader must assemble the remaining six from scattered mentions and then guess their relative order and that nothing else is present.

### `g1.r1.scope#3` — implied

```python
assert empty.create_request_files(Dataset.from_dict({"prompt": []})) == []
```

l13 only says a zero row auto run leaves the working dir empty; the reader must supply that create_request_files therefore returns an empty list rather than, say, one empty request file.

### `g1.r2.exclusions_or_crossover#2` — implied

```python
assert after[name] == body, f"{name} was rewritten by the sweep"
```

Nobody says the survivors' contents must be identical after the sweep — l13 forbids changing anything on disk only for a run that raises in the estimate step, and l2 merely observes a stale metadata file that "nothing in this run touched", so the reader has to extend "don't delete it" into "don't rewrite it" on their own.

### `g1.r2.failure_behavior#3` — implied

```python
assert read_field(caught.value, "row_idx") == 1
```

l14 names row 1 as the offender, but nobody says the raised exception carries the offending row index as a readable field, so the reader must supply that the error exposes row_idx at all.
