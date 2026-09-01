# Was every graded thing said, or only implied? — g1

**63 of 69** assertions rest on something a remark says outright.

- `stated` **63** — a reader was told
- `implied` **2** — a reader has to work it out, and may not
- `absent` **0** — nothing in the corpus bears on it
- `not_required` **4** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g1.r1.exclusions_or_crossover#1` | stated | `g1.r1.l4`, `g1.r1.h1`, `g1.r1.h2` | dermot's l4 says the resume path expects metadata_0.json to be `{"num_jobs": n}` "and nothing else" and to "keep the span and byte fields out", explicitly overturning the earlier h1/h2 plan-in-metadat |
| `g1.r1.exclusions_or_crossover#2` | stated | `g1.r1.l4`, `g1.r1.say24`, `g1.r1.say23` | l4 states outright that n is exactly the plan's num_requests for that batch, and say24/say23 independently equate metadata's num_jobs with the batch entry's num_requests. |
| `g1.r1.failure_behavior#1` | stated | `g1.r1.f2`, `g1.r1.f3` | Konrad names BatchPlanTooFragmentedError outright as a distinct error the planner raises, and Nikolai writes tests against it. |
| `g1.r1.failure_behavior#10` | stated | `g1.r1.f4` | Emil gives the exact 600-rows-plus-5000-byte-row dataset as a bug report and states the rule "per-row oversize reports first". |
| `g1.r1.failure_behavior#11` | stated | `g1.r1.f4` | "instead of naming row 600" fixes the reported row index, and the test reads the field tolerantly. |
| `g1.r1.failure_behavior#2` | stated | `g1.r1.f2` | "its own ValueError" says the subclassing directly. |
| `g1.r1.failure_behavior#3` | stated | `g1.r1.f2` | Konrad reports his `except BatchPayloadTooLargeError` not catching it and calls that the right call, which is the decision made out loud. |
| `g1.r1.failure_behavior#4` | **implied** | `g1.r1.f2`, `g1.r1.f3`, `g1.r1.l12` | Both worked examples are limit+1 failing and nobody ever says a plan of exactly the limit (512) plans successfully, so the reader must supply the strict-`>` boundary from the word "limit"/"max". |
| `g1.r1.failure_behavior#5` | stated | `g1.r1.f2`, `g1.r1.f1` | Konrad reports the error being raised at 513 batches under the default limit, and Gideon says past a ceiling the planner should refuse to plan. |
| `g1.r1.failure_behavior#6` | stated | `g1.r1.f2` | "err.num_batches 513" is the attribute and the value verbatim. |
| `g1.r1.failure_behavior#7` | stated | `g1.r1.f2` | "err.limit 512 off the default" gives both the attribute and the default limit. |
| `g1.r1.failure_behavior#8` | stated | `g1.r1.f3`, `g1.r1.l12` | Nikolai describes exactly this test constructing BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes and expecting the raise. |
| `g1.r1.failure_behavior#9` | stated | `g1.r1.f3` | The pair (3, 2) is spelled out as the asserted num_batches and limit. |
| `g1.r1.observability#1` | stated | `g1.r1.l7` | emil gives the empty-plan case outright: it hashes the empty string and plan_id comes out e3b0c44298fc, first twelve of the sha256, no special case. |
| `g1.r1.observability#2` | stated | `g1.r1.l6`, `g1.r1.l7`, `g1.r1.l8` | the hashed string format (start-end:num_bytes joined on semicolons), the sha256[:12] truncation, and the exclusion of index/num_requests are all said out loud, so this digest is mechanical from the st |
| `g1.r1.observability#3` | stated | `g1.r1.l6` | dario names both the exact hashed string for the five-row sample and the exact result f4b1ea1573c0. |
| `g1.r1.observability#4` | n/a | — | the assertion message says 'fixture drift' — it is the suite guarding its own 11-row fixture, which the corpus owes nothing. |
| `g1.r1.observability#5` | stated | `g1.r1.l6`, `g1.r1.l7`, `g1.r1.l8` | same fully-specified rule: per-batch start-end:num_bytes joined on semicolons, sha256 first twelve, index and num_requests deliberately excluded, so a one-row-per-batch plan's id follows from what was |
| `g1.r1.observability#6` | stated | `g1.r1.say22`, `g1.r1.l10`, `g1.r1.l9`, `g1.r1.l12`, `g1.r1.l11`, `g1.r1.say23`, `g1.r1.say24`, `g1.r1.l6`, `g1.r1.l2` | nils pins the exact top-level key set and order, l9 fixes the version value 1, l12 fixes the limits sub-document, l11 fixes the top-level totals and asdict batch entries, say23/say24 fix the five per- |
| `g1.r1.observability#7` | stated | `g1.r1.l12` | nikolai says limits is dataclasses.asdict of the BatchLimits it actually planned under, naming max_requests_per_batch and max_bytes_per_batch, so patched limits must show through. |
| `g1.r1.observability#8` | stated | `g1.r1.l3`, `g1.r1.say22` | konrad asks for indent 2 and a trailing newline, and say22 puts batches last at the top level, which is exactly the ']\n}\n' tail. |
| `g1.r1.rule#1` | stated | `g1.r1.l2`, `g1.r1.l9`, `g1.r1.l6`, `g1.r1.l10`, `g1.r1.l11`, `g1.r1.l12` | Every name the export check wants is spoken aloud somewhere: PLAN_FILE_NAME (l2), PLAN_FORMAT_VERSION (l9), plan_fingerprint (l6), plan_document (l10), PlannedBatch (l11) and BatchLimits (l12). |
| `g1.r1.rule#10` | stated | `g1.r1.l7`, `g1.r1.l6` | l7 says the empty plan's plan_id is the first twelve of the sha256 of the hashed string, which is exactly what l6 describes plan_fingerprint producing. |
| `g1.r1.rule#11` | stated | `g1.r1.l12` | l12 says limits is dataclasses.asdict of the BatchLimits it planned under, and names all three fields including max_batches_per_plan. |
| `g1.r1.rule#12` | stated | `g1.r1.l13`, `g1.r1.l11` | l13 fixes num_batches at 0 for an empty plan and l11 has the viewer read the batch count straight off the top, so it is the number of batches. |
| `g1.r1.rule#13` | stated | `g1.r1.l11`, `g1.r1.say22` | l11 says the viewer reads the request total off the top level, which is the summed num_requests key named in the envelope. |
| `g1.r1.rule#14` | stated | `g1.r1.l11`, `g1.r1.say22` | Same remark commits the top-level byte total, matching the num_bytes key in nils's pinned envelope. |
| `g1.r1.rule#15` | stated | `g1.r1.l11` | l11 states the batches key is one dataclasses.asdict per PlannedBatch, index and num_requests included. |
| `g1.r1.rule#16` | stated | `g1.r1.say23`, `g1.r1.say24` | say23 lists all five fields in order and say24 shows batches[0] as a literal dict in exactly that key order. |
| `g1.r1.rule#17` | stated | `g1.r1.l10`, `g1.r1.say22`, `g1.r1.l13` | plan_document is named as the thing that writes those keys and nils's checker reads that same envelope off the written file, so the file's content is plan_document's output. |
| `g1.r1.rule#2` | stated | `g1.r1.l2` | l2 writes the constant and its literal value out: PLAN_FILE_NAME = "batch_plan.json" in the planner module. |
| `g1.r1.rule#3` | stated | `g1.r1.l9`, `g1.r1.say22` | The nit about "the 1 inlined in three seperate spots" with PLAN_FORMAT_VERSION sitting right above it fixes the constant's value at 1. |
| `g1.r1.rule#4` | stated | `g1.r1.l8` | nikolai renumbered batches by hand, got the identical id, and says outright that index and num_requests aren't in what gets hashed. |
| `g1.r1.rule#5` | stated | `g1.r1.l6` | l6 spells out the hashed string as start-end:num_bytes per batch, so the byte counts are demonstrably part of the input. |
| `g1.r1.rule#6` | stated | `g1.r1.l6`, `g1.r1.l5` | The same remark gives the spans (0-2;2-4;4-5) inside the hashed string, and l5 explains the point is to detect a moved split. |
| `g1.r1.rule#7` | n/a | `g1.r1.l6`, `g1.r1.say24` | This guards the suite's own five-row fixture, though l6's three spans happen to match it anyway. |
| `g1.r1.rule#8` | stated | `g1.r1.say22`, `g1.r1.l10` | nils pins the seven top-level keys "in that order and nothing else", and l10 re-confirms plan_format_version leads. |
| `g1.r1.rule#9` | stated | `g1.r1.l9`, `g1.r1.l10`, `g1.r1.say22` | The key is named in the envelope list and its value is fixed at 1 by the inlined-literal nit. |
| `g1.r1.scope#1` | stated | `g1.r1.l13`, `g1.r1.l14`, `g1.r1.l2`, `g1.r1.l1` | l1 and l13 commit to the plan landing on disk for auto runs (l13 specifically for the zero-row auto case), l14 scopes it to the auto branch, and l2 names PLAN_FILE_NAME = "batch_plan.json", overturnin |
| `g1.r1.scope#2` | stated | `g1.r1.l16` | l16 says outright "plan gets written before the first request file," with the crash motivating it. |
| `g1.r1.scope#3` | stated | `g1.r1.say25` | say25 states the zero-row case: "create_request_files hands back an empty list there." |
| `g1.r1.scope#4` | stated | `g1.r1.l13`, `g1.r1.say22`, `g1.r1.l11` | l13 decides the zero-row document is written with num_batches 0, and say22/l11 fix the envelope's remaining keys as plan-wide totals and the per-batch list, whose only values over an empty dataset are |
| `g1.r1.scope#5` | stated | `g1.r1.l7`, `g1.r1.l6` | l7 says the empty plan hashes the empty string with no special case, and l6 defines the canonical string as the per-batch spans joined on semicolons, so zero batches gives plan_fingerprint([]). |
| `g1.r1.scope#6` | stated | `g1.r1.l14` | l14 objects to a fixed batch_size run dropping the plan file next to the requests and rules "Keep it to the auto branch." |
| `g1.r1.scope#7` | stated | `g1.r1.l15` | l15 says the dataset-None online path has nothing to plan and "we leave the working dir alone on that route." |
| `g1.r2.exclusions_or_crossover#1` | stated | `g1.r2.h1`, `g1.r2.h2`, `g1.r2.l10`, `g1.r2.l9`, `g1.r2.l11`, `g1.r2.l8` | h1/h2 scope the sweep to requests_*.jsonl and metadata_*.json only, l9 enumerates the other files present in the working dir, and l10 states outright that everything the sweep isn't deleting is left i |
| `g1.r2.exclusions_or_crossover#2` | stated | `g1.r2.l10`, `g1.r2.l2`, `g1.r2.l12` | l10 draws the exact distinction the assertion tests — "the sweep doesn't just leave it in place, it leaves the bytes untouched, same for everything it isn't deleting" — with l2 and l12 corroborating t |
| `g1.r2.failure_behavior#1` | n/a | `g1.r2.l4`, `g1.r2.l15`, `g1.r2.l9` | This is an explicit fixture-drift guard on the suite's own seeded directory; the corpus describes a seeding (requests_0–5 plus matching metadata in l4, a stale batch_plan.json in l15, batch_objects/.a |
| `g1.r2.failure_behavior#2` | stated | `g1.r2.l14`, `g1.r2.l12` | nikolai names the exact fixture setup — max_bytes_per_batch 400 against a 600 char prompt — and says SingleRequestTooLargeError comes back. |
| `g1.r2.failure_behavior#3` | stated | `g1.r2.l14` | l14 spells out the field and its value: the error 'comes back with row_idx 1 on it, thats how we know which row blew up'. |
| `g1.r2.failure_behavior#4` | stated | `g1.r2.l14`, `g1.r2.l12` | Same decision as #2 — the oversized-row planning call raising SingleRequestTooLargeError is said outright, whatever position the call occupies in the test. |
| `g1.r2.failure_behavior#5` | stated | `g1.r2.l13`, `g1.r2.l12`, `g1.r2.l10` | dermot commits to it directly — a run that raises in the estimate step 'has no business having changed anything on disk, stale or not' — with emil's report of the emptied dir and dario's 'leaves the b |
| `g1.r2.observability#1` | stated | `g1.r2.h1`, `g1.r2.h2`, `g1.r2.l4`, `g1.r2.l8`, `g1.r2.l10` | h1/h2 name the exact delete set (requests_*.jsonl and metadata_*.json) as an entry sweep, l4 describes this very fixture — seed 0..5, plan makes three, "the listing afterwards is the assertion" — and  |
| `g1.r2.observability#2` | stated | `g1.r2.l8`, `g1.r2.l10`, `g1.r2.h2` | l8 says losing responses_0.jsonl to a blanket delete cost them a repaid batch and l10 says the sweep "leaves the bytes untouched, same for everything it isn't deleting", so an unchanged responses file |
| `g1.r2.observability#3` | stated | `g1.r2.l14` | nikolai names the exact fixture — max_bytes_per_batch pinned to 400, a 600-char prompt, and SingleRequestTooLargeError coming back. |
| `g1.r2.observability#4` | stated | `g1.r2.l14` | Same remark: the oversized single row raising SingleRequestTooLargeError under a 400-byte cap is spelled out, including the error class name. |
| `g1.r2.observability#5` | stated | `g1.r2.l13`, `g1.r2.l12` | l13 states the rule outright — a run that raises in the estimate step and never produces a plan "has no business having changed anything on disk, stale or not" — with l12 reporting the empty-working-d |
| `g1.r2.observability#6` | stated | `g1.r2.l15`, `g1.r2.l13` | l15 puts the stale plan_format_version 1 batch_plan.json in the dir before the run and l13 forbids the failed run from altering anything on disk, so the body surviving verbatim was decided aloud. |
| `g1.r2.observability#7` | stated | `g1.r2.l13`, `g1.r2.l12` | l13's "stale or not" is aimed exactly at leftover requests files surviving a run that raised before producing a plan, though it sits in unmarked tension with h1/h2's sweep-first ordering. |
| `g1.r2.rule#1` | n/a | `g1.r2.l4` | This is a guard on the suite's own five-row fixture (that five rows cannot plan more than five batches), not a behaviour the corpus owes anything about. |
| `g1.r2.rule#2` | stated | `g1.r2.h1`, `g1.r2.h2`, `g1.r2.l4`, `g1.r2.l1` | h1 and h2 both say outright that the auto branch clears requests_*.jsonl on entry before plan_request_batches runs, and l4 describes the exact seeded-0-through-5-then-plan-three listing the assertion  |
| `g1.r2.rule#3` | stated | `g1.r2.h1`, `g1.r2.h2`, `g1.r2.l4`, `g1.r2.l2` | metadata_*.json is named alongside requests_*.jsonl in both the deletion instructions (h1, h2) and in the fixture description (l4), with l2 reporting the stale metadata_3.json symptom. |
| `g1.r2.rule#4` | **implied** | `g1.r2.h2`, `g1.r2.l3`, `g1.r2.l10` | Nobody says what a surviving requests_0.jsonl should contain or that its rows run from the plan's start_idx to end_idx; the reader has to infer from "nothing new gets writen next to stale numbering" a |
| `g1.r2.scope#1` | stated | `g1.r2.l7`, `g1.r2.l5`, `g1.r2.h1`, `g1.r2.h2` | Dario says the explicit batch_size=1000 branch should keep behaving exactly as it always has and must not pick up the new behaviour, and Emil says that path leans on request files from earlier runs an |
| `g1.r2.scope#2` | stated | `g1.r2.h1`, `g1.r2.h2`, `g1.r2.l7` | The sweep is named as requests_*.jsonl plus metadata_*.json and is placed inside the auto branch, and Dario explicitly refuses that new behaviour for the integer branch, so metadata files surviving th |
| `g1.r2.scope#3` | stated | `g1.r2.l7`, `g1.r2.l5`, `g1.r2.l4` | The same 'that branch keeps its old behaviour, nothing new' instruction covers leaving a seeded requests_5.jsonl exactly as it was found; Konrad's fixture even describes seeding requests_0 through req |
| `g1.r2.scope#4` | stated | `g1.r2.l6` | Nikolai says outright that resume calls create_request_files with dataset=None purely to get the paths back and would be unhappy if that call ever started taking files away. |
| `g1.r2.scope#5` | stated | `g1.r2.l6`, `g1.r2.h1` | 'Taking files away' in the dataset=None call covers the whole sweep set, which h1/h2 define as requests_* and metadata_* together. |
| `g1.r2.scope#6` | stated | `g1.r2.l6`, `g1.r2.l10` | Nikolai frames the dataset=None call as doing nothing but returning paths, and Dario states the untouched-files rule as leaving the bytes alone rather than merely leaving files in place. |

### `g1.r1.failure_behavior#4` — implied

```python
assert len(module.plan_batches([10] * 512, one_per_batch)) == 512, "512 batches is the boundary and it is admissible"
```

Both worked examples are limit+1 failing and nobody ever says a plan of exactly the limit (512) plans successfully, so the reader must supply the strict-`>` boundary from the word "limit"/"max".

### `g1.r2.rule#4` — implied

```python
# the surviving files are the new run's, not stale content left in place
    assert row_indices(os.path.join(working_dir, "requests_0.jsonl")) == list(
        range(read_field(plan[0], "start_idx"), read_field(plan[0], "end_idx"))
    )
```

Nobody says what a surviving requests_0.jsonl should contain or that its rows run from the plan's start_idx to end_idx; the reader has to infer from "nothing new gets writen next to stale numbering" and "the working directory should hold what that run actually produced" that the low-numbered files are freshly rewritten rather than stale content left in place.
