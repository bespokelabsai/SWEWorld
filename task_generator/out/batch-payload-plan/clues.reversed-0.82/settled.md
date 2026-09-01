# Was every graded thing said, or only implied? — g1

**63 of 69** assertions rest on something a remark says outright.

- `stated` **63** — a reader was told
- `implied` **2** — a reader has to work it out, and may not
- `absent` **0** — nothing in the corpus bears on it
- `not_required` **4** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

> **These verdicts are what provoked the rewrites, not what the plant says now.** 1 remark(s) rewritten, 1 added, 0 not fixed. Re-run `settle --dry-run` for the verdicts on the corpus as it now stands.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g1.r1.exclusions_or_crossover#1` | stated | `g1.r1.rev2`, `g1.r1.l4`, `g1.r1.rev1` | dermot says twice, in rev2 and l4, that the resume path wants {"num_jobs": n} "and nothing else" and that start_idx, end_idx and num_bytes came back out / stay out, with rev1 confirming the plan moved |
| `g1.r1.exclusions_or_crossover#2` | stated | `g1.r1.l4`, `g1.r1.say24`, `g1.r1.say23` | l4 states directly that n is exactly the plan's num_requests for that batch, and say24/say23 confirm num_requests is the plan's name for what metadata calls num_jobs. |
| `g1.r1.failure_behavior#1` | stated | `g1.r1.f2`, `g1.r1.f3`, `g1.r1.f1` | konrad names BatchPlanTooFragmentedError outright in a code-review of the planner, and nikolai's test note treats it as the error the planner raises. |
| `g1.r1.failure_behavior#10` | stated | `g1.r1.f4` | emil reports the exact 600-rows-plus-5000-byte-row dataset misreporting as too fragmented and settles it with "per-row oversize reports first". |
| `g1.r1.failure_behavior#11` | stated | `g1.r1.f4` | "instead of naming row 600" fixes both that the row index is carried on the error and that its value for this dataset is 600, though the attribute spelling row_idx itself is only alluded to. |
| `g1.r1.failure_behavior#2` | stated | `g1.r1.f2` | "its own ValueError" is the decision said aloud. |
| `g1.r1.failure_behavior#3` | stated | `g1.r1.f2` | konrad reports his `except BatchPayloadTooLargeError` sailing past it and endorses that as the right call, which is exactly the non-subclass relationship. |
| `g1.r1.failure_behavior#4` | **implied** | `g1.r1.f2`, `g1.r1.f1` | the default 512 is stated and 513 is reported as raising, but nobody says a 512-batch plan is admissible, so the reader must supply that the comparison is `>` and not `>=` — an off-by-one implementati |
| `g1.r1.failure_behavior#5` | stated | `g1.r1.f2`, `g1.r1.f1` | f1 says past some ceiling it should refuse to plan, and f2 reports the refusal happening as BatchPlanTooFragmentedError at 513 batches under the default. |
| `g1.r1.failure_behavior#6` | stated | `g1.r1.f2` | "err.num_batches 513" is written out, attribute and value. |
| `g1.r1.failure_behavior#7` | stated | `g1.r1.f2` | "err.limit 512 off the default" gives both the attribute and that 512 is the default ceiling. |
| `g1.r1.failure_behavior#8` | stated | `g1.r1.f3`, `g1.r1.l12` | nikolai describes the exact construction BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes raising the fragmented error, and l12 confirms max_batches_per_plan is a real BatchLimits field. |
| `g1.r1.failure_behavior#9` | stated | `g1.r1.f3` | the asserted pair (3, 2) is quoted verbatim as what the test checks, so an explicit limit overriding the default is said aloud. |
| `g1.r1.observability#1` | stated | `g1.r1.l7` | emil gives the empty-plan case, the exact digest e3b0c44298fc, and that it is the first twelve of the sha256 of the empty string with no special case. |
| `g1.r1.observability#2` | stated | `g1.r1.l6`, `g1.r1.l7`, `g1.r1.l8` | the hashed string format (start-end:num_bytes joined on semicolons), the sha256-first-twelve truncation, and the exclusion of index/num_requests are all said out loud, which fixes this digest determin |
| `g1.r1.observability#3` | stated | `g1.r1.l6`, `g1.r1.say24` | dario names the exact five-row spans and the exact returned id f4b1ea1573c0. |
| `g1.r1.observability#4` | n/a | — | this is the suite guarding its own fixture (11 rows at one batch each), not a decision the corpus owes. |
| `g1.r1.observability#5` | stated | `g1.r1.l6`, `g1.r1.l7`, `g1.r1.l8` | same fully-specified digest recipe as #2, applied to a one-row-per-batch split, so the value follows from what was said rather than from a guess. |
| `g1.r1.observability#6` | stated | `g1.r1.say22`, `g1.r1.rev1`, `g1.r1.l10`, `g1.r1.say23`, `g1.r1.say24`, `g1.r1.l11`, `g1.r1.l12`, `g1.r1.l6` | nils pins the exact top-level key set and order, rev1/l10 pin plan_format_version 1 first, say23/say24/l11 pin the five per-batch fields and the sample's numbers, l11 pins the top-level totals and l12 |
| `g1.r1.observability#7` | stated | `g1.r1.l12` | nikolai says limits is dataclasses.asdict of the BatchLimits the run actually planned under, naming all three fields. |
| `g1.r1.observability#8` | stated | `g1.r1.l3`, `g1.r1.say22` | konrad orders indent 2 plus a trailing newline, and say22's key order puts batches last, which is what produces the "]\n}\n" tail. |
| `g1.r1.rule#1` | stated | `g1.r1.l2`, `g1.r1.l9`, `g1.r1.l6`, `g1.r1.l10`, `g1.r1.l11`, `g1.r1.l12` | Every graded name is spoken aloud in the module: PLAN_FILE_NAME (l2), PLAN_FORMAT_VERSION (l9), plan_fingerprint (l6), plan_document (l10), with PlannedBatch (l11) and BatchLimits (l12) named too. |
| `g1.r1.rule#10` | stated | `g1.r1.l7`, `g1.r1.l6` | l7 reports plan_id coming out as the first twelve of the sha256 that l6 attributes to plan_fingerprint, tying the key to that function. |
| `g1.r1.rule#11` | stated | `g1.r1.l12` | l12 says limits is dataclasses.asdict of the BatchLimits it planned under, and enumerates the three fields. |
| `g1.r1.rule#12` | stated | `g1.r1.l13`, `g1.r1.l11` | l11 has the viewer reading num_batches off the top and l13 fixes the empty-plan case at num_batches 0, which is the count of batches. |
| `g1.r1.rule#13` | stated | `g1.r1.l11`, `g1.r1.say22` | l11 calls the top-level num_requests and num_bytes 'the request and byte totals', i.e. summed over the batches. |
| `g1.r1.rule#14` | stated | `g1.r1.l11`, `g1.r1.say22` | Same remark names num_bytes as a total read straight off the top of the document. |
| `g1.r1.rule#15` | stated | `g1.r1.l11`, `g1.r1.say23` | l11 states the batches key is one dataclasses.asdict per PlannedBatch, index and num_requests included. |
| `g1.r1.rule#16` | stated | `g1.r1.say23`, `g1.r1.say24` | say23 lists all five per-entry fields in that exact order and say24 shows batches[0] as a literal dict in the same order. |
| `g1.r1.rule#17` | stated | `g1.r1.rev1`, `g1.r1.l3`, `g1.r1.l10`, `g1.r1.l14`, `g1.r1.l16` | rev1 puts the plan in batch_plan.json in the working dir on the auto branch, l3 fixes indent 2 plus a trailing newline, and l10 identifies plan_document as what writes that document. |
| `g1.r1.rule#2` | stated | `g1.r1.l2`, `g1.r1.rev1` | l2 gives the constant and its literal value verbatim, and rev1 independently names batch_plan.json as the sidecar in the working dir. |
| `g1.r1.rule#3` | stated | `g1.r1.rev1`, `g1.r1.l9` | rev1 fixes plan_format_version at 1 and l9 tells the reader the constant PLAN_FORMAT_VERSION holds that 1. |
| `g1.r1.rule#4` | stated | `g1.r1.l8`, `g1.r1.l6` | l8 reports renumbering batches by hand and getting the identical id, and says outright that index and num_requests are not in what gets hashed. |
| `g1.r1.rule#5` | stated | `g1.r1.l6` | l6 spells the hashed string as start-end:num_bytes per batch, so the byte counts are part of the input by decision, not inference. |
| `g1.r1.rule#6` | stated | `g1.r1.l6`, `g1.r1.l5` | l6's canonical string carries each batch's start and end, and l5 states the whole point is telling whether the split moved. |
| `g1.r1.rule#7` | n/a | `g1.r1.l6` | The comment flags this as a fixture-drift guard on the suite's own five-row sample, which l6 happens to corroborate at three batches anyway. |
| `g1.r1.rule#8` | stated | `g1.r1.say22`, `g1.r1.l10` | say22 pins all seven top-level keys in exactly that order and nothing else, and l10 re-fixes plan_format_version as the first key. |
| `g1.r1.rule#9` | stated | `g1.r1.rev1`, `g1.r1.l9` | rev1 states the sidecar carries plan_format_version 1. |
| `g1.r1.scope#1` | stated | `g1.r1.rev1`, `g1.r1.l2`, `g1.r1.l13` | rev1 puts the plan in a sidecar `batch_plan.json` in the working dir on the auto branch, l2 names the constant, and l13 insists the file is written even for a zero-row auto run. |
| `g1.r1.scope#2` | stated | `g1.r1.l16` | l16 says outright "plan gets written before the first request file" after describing a job that died mid-write with nothing on disk saying how many were expected. |
| `g1.r1.scope#3` | stated | `g1.r1.say25` | say25 states the zero-row case directly: create_request_files hands back an empty list and no empty requests_0.jsonl is left behind. |
| `g1.r1.scope#4` | stated | `g1.r1.l13`, `g1.r1.say22` | l13 fixes the zero-row document as written-regardless with num_batches 0, and say22 pins the envelope's always-present keys, leaving the remaining zeros and empty batches list as forced arithmetic rat |
| `g1.r1.scope#5` | stated | `g1.r1.l7`, `g1.r1.l6` | l7 says the empty plan just hashes the empty string with no special case, and l6 defines the fingerprint string plan_fingerprint hashes. |
| `g1.r1.scope#6` | stated | `g1.r1.l14`, `g1.r1.rev1` | l14 asks explicitly that a fixed batch_size run not drop the plan file next to the requests, and rev1 scopes the sidecar to the auto branch only. |
| `g1.r1.scope#7` | stated | `g1.r1.l15` | l15 says the dataset-None online route has nothing to plan and leaves the working dir alone. |
| `g1.r2.exclusions_or_crossover#1` | stated | `g1.r2.rev2`, `g1.r2.l10`, `g1.r2.l9`, `g1.r2.l8`, `g1.r2.l11`, `g1.r2.h1`, `g1.r2.h2` | rev2 scopes the sweep to exactly requests_*.jsonl and metadata_*.json, l9 names the other files in the dir, and l10 says everything the sweep isn't deleting stays, with l8 and l11 spelling out the cos |
| `g1.r2.exclusions_or_crossover#2` | stated | `g1.r2.l10`, `g1.r2.l2` | l10 states outright that the sweep doesn't merely leave untouched files in place but leaves their bytes untouched, and l2 corroborates a surviving metadata file that nothing in the run modified. |
| `g1.r2.failure_behavior#1` | n/a | `g1.r2.l4`, `g1.r2.l15` | The assertion is an explicit fixture-drift guard on the suite's own pre-populated directory, so the corpus owes it nothing (though l4's six requests plus matching metadata and l15's stale batch_plan.j |
| `g1.r2.failure_behavior#2` | stated | `g1.r2.l14`, `g1.r2.rev1` | l14 says outright that a fixture pinning max_bytes_per_batch to 400 against a 600-char prompt makes SingleRequestTooLargeError come back, and rev1 names the same exception being thrown by plan_request |
| `g1.r2.failure_behavior#3` | stated | `g1.r2.l14` | l14 says the error 'comes back with row_idx 1 on it, thats how we know which row blew up' — the field name and the value are both handed over. |
| `g1.r2.failure_behavior#4` | stated | `g1.r2.l14`, `g1.r2.rev2` | Same exception decision as #2, said out loud in l14 and echoed by rev2's 'when the oversized row raised'. |
| `g1.r2.failure_behavior#5` | stated | `g1.r2.rev1`, `g1.r2.rev2`, `g1.r2.l13`, `g1.r2.l10` | rev1 and rev2 both reverse the order specifically so a SingleRequestTooLargeError leaves the dir unswept, l13 says a run that raises before producing a plan must not have changed anything on disk 'sta |
| `g1.r2.observability#1` | stated | `g1.r2.l4`, `g1.r2.rev2`, `g1.r2.h1`, `g1.r2.h2`, `g1.r2.l3`, `g1.r2.l8` | Konrad spells out the fixture (requests_0–5 plus matching metadata, plan makes three, "the listing afterwards is the assertion") and the h1/h2/rev2 line names exactly requests_*.jsonl and metadata_*.j |
| `g1.r2.observability#2` | stated | `g1.r2.l10`, `g1.r2.l8`, `g1.r2.l9` | Dario commits outright that the sweep "leaves the bytes untouched, same for everything it isn't deleting", and l8's double-pay incident is specifically about responses_0.jsonl going missing. |
| `g1.r2.observability#3` | stated | `g1.r2.l14`, `g1.r2.rev1` | Nikolai names the fixture (max_bytes_per_batch pinned to 400, a 600-char prompt) and the exact exception SingleRequestTooLargeError that comes back from it. |
| `g1.r2.observability#4` | stated | `g1.r2.l14`, `g1.r2.rev1` | Same remark: the oversized-row path raising SingleRequestTooLargeError is said out loud by both nikolai and dario. |
| `g1.r2.observability#5` | stated | `g1.r2.l13`, `g1.r2.rev2`, `g1.r2.rev1`, `g1.r2.l12`, `g1.r2.l15` | Dermot states the rule normatively — a run that raises before a plan comes out "has no business having changed anything on disk, stale or not" — and rev1/rev2 move the sweep behind the plan for precis |
| `g1.r2.observability#6` | stated | `g1.r2.l15`, `g1.r2.l13` | Nils pins batch_plan.json as already present holding a stale plan_format_version 1 body, and l13's "changed anything on disk, stale or not" covers not rewriting or truncating it on the failing path. |
| `g1.r2.observability#7` | stated | `g1.r2.l12`, `g1.r2.l13`, `g1.r2.l10` | Emil raises create-on-open explicitly — the oversized-row failure emptied the working dir when "the split that was in there beforehand was still perfectly usable" — so preserving the seeded request-fi |
| `g1.r2.rule#1` | n/a | `g1.r2.l4` | This is a self-check on the suite's own five-row fixture (a sanity bound on how many batches it planned), not a behaviour the corpus owes anything about. |
| `g1.r2.rule#2` | stated | `g1.r2.l4`, `g1.r2.h1`, `g1.r2.h2`, `g1.r2.rev1`, `g1.r2.rev2`, `g1.r2.l1` | konrad describes exactly this fixture — seed requests_0 through requests_5, let the plan make three, and the listing afterwards is the assertion — and h1/h2/rev1/rev2 all name requests_*.jsonl as the  |
| `g1.r2.rule#3` | stated | `g1.r2.h1`, `g1.r2.h2`, `g1.r2.rev1`, `g1.r2.rev2`, `g1.r2.l4`, `g1.r2.l2` | metadata_*.json is named alongside requests_*.jsonl in every statement of the sweep, konrad's fixture seeds 'matchign metadata', and nils reports a stale metadata_3.json surviving a run as the symptom |
| `g1.r2.rule#4` | **implied** | `g1.r2.l2`, `g1.r2.l3`, `g1.r2.h1` | Nobody says the surviving requests_0.jsonl must carry the new plan's start_idx..end_idx rows; the reader has to combine nils's stale-content complaint and dermot's 'should hold what that run actually  |
| `g1.r2.scope#1` | stated | `g1.r2.l7`, `g1.r2.l5`, `g1.r2.h1`, `g1.r2.rev1` | dario rules the explicit batch_size=1000 branch out of "new behaviour off the side" and emil says the integer path leans on files from earlier runs so clearing them restarts every resume from zero, wh |
| `g1.r2.scope#2` | stated | `g1.r2.l7`, `g1.r2.l5`, `g1.r2.h2`, `g1.r2.rev2` | the same two remarks cover metadata_*.json, which is named alongside requests_*.jsonl in every statement of what the sweep deletes and where it deletes it. |
| `g1.r2.scope#3` | stated | `g1.r2.l7`, `g1.r2.l10`, `g1.r2.l5` | dario keeps the explicit branch on its old behaviour and separately says non-deleted files keep their bytes untouched, so a stale higher-numbered file surviving byte-identical is what was described, n |
| `g1.r2.scope#4` | stated | `g1.r2.l6` | nikolai says outright that resume calls create_request_files with dataset=None purely to get paths back and that he would be unhappy if that call ever started taking files away. |
| `g1.r2.scope#5` | stated | `g1.r2.l6`, `g1.r2.h1` | "taking files away" covers the pair the sweep is always described as deleting together, requests_*.jsonl and metadata_*.json. |
| `g1.r2.scope#6` | stated | `g1.r2.l6`, `g1.r2.l10` | a dataset=None call described as existing only to return paths writes nothing, and dario's "leaves the bytes untouched" states the no-mutation rule explicitly. |

### `g1.r1.failure_behavior#4` — implied

```python
assert len(module.plan_batches([10] * 512, one_per_batch)) == 512, "512 batches is the boundary and it is admissible"
```

the default 512 is stated and 513 is reported as raising, but nobody says a 512-batch plan is admissible, so the reader must supply that the comparison is `>` and not `>=` — an off-by-one implementation would be equally consistent with f2.

### `g1.r2.rule#4` — implied

```python
# the surviving files are the new run's, not stale content left in place
    assert row_indices(os.path.join(working_dir, "requests_0.jsonl")) == list(
        range(read_field(plan[0], "start_idx"), read_field(plan[0], "end_idx"))
    )
```

Nobody says the surviving requests_0.jsonl must carry the new plan's start_idx..end_idx rows; the reader has to combine nils's stale-content complaint and dermot's 'should hold what that run actually produced' with the base write behaviour to conclude a pre-existing requests_0.jsonl must be replaced rather than left in place.
