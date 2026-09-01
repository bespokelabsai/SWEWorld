# Was every graded thing said, or only implied? — g1

**62 of 69** assertions rest on something a remark says outright.

- `stated` **62** — a reader was told
- `implied` **1** — a reader has to work it out, and may not
- `absent` **0** — nothing in the corpus bears on it
- `not_required` **6** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g1.r1.exclusions_or_crossover#1` | stated | `g1.r1.l3`, `g1.r1.say23`, `g1.r1.h2` | nils says outright that the metadata_{i}.json body is num_jobs and nothing else and that the reader bails on extras, explicitly asking that the span keys be kept out — overturning konrad's earlier h2  |
| `g1.r1.exclusions_or_crossover#2` | stated | `g1.r1.say25`, `g1.r1.say24` | nils states that num_requests on a batches row and num_jobs in that batch's metadata_{i}.json count the same thing and must match row for row. |
| `g1.r1.failure_behavior#1` | stated | `g1.r1.l18`, `g1.r1.l16`, `g1.r1.fix21` | dario names the exception outright — "my except for payload-too-large caught a BatchPlanTooFragmentedError" — and l16/fix21 discuss its attributes, so the reader defines it where plan_batches lives. |
| `g1.r1.failure_behavior#10` | stated | `g1.r1.l19` | nils reports the exact 600-tiny-rows-plus-one-5MB-row dataset and says what should have come back instead: SingleRequestTooLargeError, not the fragmentation error. |
| `g1.r1.failure_behavior#11` | stated | `g1.r1.l19` | nils spells out the field and the value — "SingleRequestTooLargeError naming row_idx 600". |
| `g1.r1.failure_behavior#2` | stated | `g1.r1.l18` | "the outer except ValueError should have had it" is a direct statement that the fragmentation error is a ValueError. |
| `g1.r1.failure_behavior#3` | stated | `g1.r1.l18` | dario complains that his payload-too-large handler swallowed the fragmentation error and says "those aren't the same failure", which is the subclass decision made out loud. |
| `g1.r1.failure_behavior#4` | stated | `g1.r1.l17` | nikolai writes the cap as max_batches_per_plan default 512 and adds that "a plan landing on exactly 512 is still fine". |
| `g1.r1.failure_behavior#5` | stated | `g1.r1.l17`, `g1.r1.l19`, `g1.r1.l16`, `g1.r1.l18` | the cap-checked-when-plan-is-finished rule, the named error, and nils reporting he "got the fragmentation error back" from an over-512 auto plan together say plainly that exceeding the cap raises it. |
| `g1.r1.failure_behavior#6` | stated | `g1.r1.fix21`, `g1.r1.l16` | emil names the missing attribute ("there's no num_batches on the error anywhere, just the ceiling") and konrad asks for "the count it wanted", so the attribute and its meaning were both requested. |
| `g1.r1.failure_behavior#7` | stated | `g1.r1.l16`, `g1.r1.l17` | konrad refers to `err.limit` by name and nikolai fixes the default at 512. |
| `g1.r1.failure_behavior#8` | stated | `g1.r1.l17`, `g1.r1.l8` | the cap is stated to live on the limits dataclass as a field named max_batches_per_plan with a default, and gideon confirms it became a third key in the limits block, so a caller-supplied value is the |
| `g1.r1.failure_behavior#9` | stated | `g1.r1.l17`, `g1.r1.l16`, `g1.r1.fix21` | same two attributes were asked for by name and the strict > boundary ("exactly 512 is still fine") fixes the (3, 2) case. |
| `g1.r1.observability#1` | stated | `g1.r1.l11`, `g1.r1.fix23`, `g1.r1.fix22` | l11 gives the literal return value "e3b0c44298fc" for plan_fingerprint([]) and says not to special-case it, and fix23 spells out why (zero lines join to an empty string, hashed like any other input). |
| `g1.r1.observability#2` | stated | `g1.r1.l9`, `g1.r1.l12`, `g1.r1.l10` | l9 dictates the exact pre-image ("0-2:307;2-4:307" — spans and bytes only, utf-8, sha256, front of the hexdigest) and l12 fixes the truncation at twelve hex chars, so the digest for any plan is determ |
| `g1.r1.observability#3` | stated | `g1.r1.l12`, `g1.r1.l9` | l12 quotes "f4b1ea1573c0" as what plan_fingerprint hands back and l9's worked example is the first two spans of exactly this plan. |
| `g1.r1.observability#4` | n/a | — | This is the suite guarding its own fixture (one row per batch under a patched request cap); the corpus owes it nothing. |
| `g1.r1.observability#5` | stated | `g1.r1.l9`, `g1.r1.l12`, `g1.r1.l7` | Same rule as #2 applied to more batches: l9 gives the join format by literal example, l12 the twelve-char truncation, and l7 pins the per-batch byte figure to what create_batch_file returns. |
| `g1.r1.observability#6` | stated | `g1.r1.l2`, `g1.r1.l5`, `g1.r1.l6`, `g1.r1.l7`, `g1.r1.say23`, `g1.r1.say24`, `g1.r1.l8` | Every key and its content was decided out loud — l2 (version starts at 1), l5 (plan_format_version ahead of plan_id), l6 (num_batches/num_requests straight after the limits block, requests summed), l7 |
| `g1.r1.observability#7` | stated | `g1.r1.l8` | l8 names plan_document(plan, limits)['limits'] and its byte/request keys as echoing the limits object handed in, which is what makes the patched 3/400 show up. |
| `g1.r1.observability#8` | stated | `g1.r1.l4` | l4 lays it down as a house rule: json.dumps(plan_document(...), indent=2) plus a trailing newline into batch_plan.json. |
| `g1.r1.rule#1` | stated | `g1.r1.l2`, `g1.r1.say23`, `g1.r1.l4` | dermot's wiki note names all four exports on batch_payload_planner outright: PLAN_FILE_NAME, PLAN_FORMAT_VERSION and the plan_fingerprint/plan_document pair. |
| `g1.r1.rule#10` | stated | `g1.r1.l12`, `g1.r1.fix22` | konrad says plan_id "is whatever plan_fingerprint hands back". |
| `g1.r1.rule#11` | stated | `g1.r1.l8`, `g1.r1.l17` | gideon reports the limits block grew a third key by itself when max_batches_per_plan landed on the dataclass, which is the asdict behaviour and the three-key shape. |
| `g1.r1.rule#12` | stated | `g1.r1.l6`, `g1.r1.fix21` | l6 names num_batches as a document key and fix21 equates that fragmentation count with len(plan). |
| `g1.r1.rule#13` | stated | `g1.r1.l6` | l6: "num_requests being each batch's num_requests added up". |
| `g1.r1.rule#14` | stated | `g1.r1.l7` | l7 says num_bytes is the sizes create_batch_file hands back, summed, and explicitly not what du reports. |
| `g1.r1.rule#15` | stated | `g1.r1.say23` | say23: each row under batches is dataclasses.asdict of the PlannedBatch as the planner built it, index and all. |
| `g1.r1.rule#16` | stated | `g1.r1.say24` | say24 gives the row as index, start_idx, end_idx, num_requests, num_bytes in that order and nothing else. |
| `g1.r1.rule#17` | stated | `g1.r1.l4`, `g1.r1.l13`, `g1.r1.l15` | l4 says json.dumps(plan_document(...), indent=2) plus a trailing newline goes into batch_plan.json, and l13 says it lands on the auto path before the first requests file. |
| `g1.r1.rule#2` | stated | `g1.r1.l2`, `g1.r1.l4`, `g1.r1.l13`, `g1.r1.l14` | l2 says the module holds PLAN_FILE_NAME and l4/l13/say24 repeatedly name the file batch_plan.json, so the constant's value is said out loud. |
| `g1.r1.rule#3` | stated | `g1.r1.l2` | l2: "version starts at 1 and only moves when the key set changes". |
| `g1.r1.rule#4` | stated | `g1.r1.l9` | dario's design page says hash the batches joined, "spans and bytes, not index, not num_requests". |
| `g1.r1.rule#5` | stated | `g1.r1.l9` | the same remark puts bytes into the canonical line (0-2:307), so a different size gives a different digest. |
| `g1.r1.rule#6` | stated | `g1.r1.l9` | the same remark puts the spans into the canonical line, so moving the cut changes the digest. |
| `g1.r1.rule#7` | n/a | — | this is the suite pinning its own five-row fixture, not a decision the corpus owes. |
| `g1.r1.rule#8` | **implied** | `g1.r1.l5`, `g1.r1.l6`, `g1.r1.l7` | l5 pins the first two keys and l6/l7 pin limits→num_batches→num_requests→num_bytes, but nobody says batches comes last or gives the envelope as one ordered list — the reader has to splice three remark |
| `g1.r1.rule#9` | stated | `g1.r1.l5`, `g1.r1.l2` | l5 names plan_format_version as a key of plan_document's output and l2 fixes the version at 1. |
| `g1.r1.scope#1` | stated | `g1.r1.l14`, `g1.r1.l15`, `g1.r1.l13`, `g1.r1.l2` | gideon asks for batch_plan.json on the auto path and konrad rules it out precisely for the non-auto branches, so the auto branch writing the sidecar is decided out loud. |
| `g1.r1.scope#2` | stated | `g1.r1.l13` | dario says outright that batch_plan.json wants to land before the first requests file. |
| `g1.r1.scope#3` | n/a | `g1.r1.l14`, `g1.r1.fix22` | This is the fixture's own precondition — the empty-dataset call producing no request files is pre-existing behaviour gideon merely reports as a "bare dir", not part of the change being asked for. |
| `g1.r1.scope#4` | stated | `g1.r1.l14` | gideon enumerates num_batches 0, num_requests 0, num_bytes 0, batches [] for the empty run. |
| `g1.r1.scope#5` | stated | `g1.r1.l14`, `g1.r1.fix22`, `g1.r1.fix23`, `g1.r1.l11` | gideon wants plan_id "filled in like any other run" and nils/dermot/emil confirm plan_fingerprint on zero batches hashes the empty string and returns a real digest with no special-casing. |
| `g1.r1.scope#6` | stated | `g1.r1.l15` | konrad names batch_size=2 and says no batch_plan.json should turn up in the working dir for it. |
| `g1.r1.scope#7` | stated | `g1.r1.l15` | the same remark covers "I give no dataset at all" as a no-sidecar case. |
| `g1.r2.exclusions_or_crossover#1` | stated | `g1.r2.say15`, `g1.r2.l11`, `g1.r2.l10`, `g1.r2.l12`, `g1.r2.l13` | say15 states the sweep only unlinks the two globs and that responses_*.jsonl and batch_objects.jsonl come back untouched, with l10/l11/l12 naming those same survivors and l13 explicitly rejecting a wh |
| `g1.r2.exclusions_or_crossover#2` | stated | `g1.r2.say15` | say15 says nothing else in the run dir gets opened or rewritten and that those files come back byte for byte, which is the assertion almost verbatim. |
| `g1.r2.failure_behavior#1` | n/a | — | This is a self-check on the suite's own pre-populated fixture directory, not a behaviour the corpus owes anything to. |
| `g1.r2.failure_behavior#2` | stated | — | Gideon names the exception outright — "it blew up with SingleRequestTooLargeError(...)" — and Nikolai reports the same planning abort on an oversized row. |
| `g1.r2.failure_behavior#3` | stated | — | l8 spells the error out with its fields, `SingleRequestTooLargeError(row_idx=1, size_bytes=748, limit_bytes=400)`, giving both the attribute name and the value. |
| `g1.r2.failure_behavior#4` | stated | — | Same named exception on the same oversized-row path, said out loud in l8 and corroborated by l7. |
| `g1.r2.failure_behavior#5` | stated | — | Dermot states the contract directly — "a raise should leave it exactly as it found it" — with l7 and l8 reporting the emptied directory as the bug it fixes. |
| `g1.r2.observability#1` | stated | `g1.r2.h1`, `g1.r2.l3`, `g1.r2.say15`, `g1.r2.l1` | h1 says to glob and drop stale requests_*.jsonl and metadata_*.json and l3 repeats that leftovers from a six-batch run must come off disk, while say15 fixes that only those two globs are touched, so t |
| `g1.r2.observability#2` | stated | `g1.r2.say15`, `g1.r2.l10` | say15 states responses_*.jsonl comes back byte for byte and l10 records paying twice after responses_0.jsonl was lost, so leaving its contents untouched is a decision made out loud. |
| `g1.r2.observability#3` | stated | `g1.r2.l8`, `g1.r2.l7` | l8 names SingleRequestTooLargeError with exactly the row_idx/size_bytes/limit_bytes it is raised with, and l7 confirms an oversized row aborts planning. |
| `g1.r2.observability#4` | stated | `g1.r2.l8`, `g1.r2.l7` | Same remark names the exception type raised on the oversized row, so the second raises-block rests on told information too. |
| `g1.r2.observability#5` | stated | `g1.r2.l9`, `g1.r2.l7` | dermot commits outright that a raise should leave the working directory exactly as it found it, and l7 reports the loss of files that were fine as the bug being fixed, so the full 14-entry survival is |
| `g1.r2.observability#6` | stated | `g1.r2.l9`, `g1.r2.l8`, `g1.r2.say15` | l8 complains the previous batch_plan.json was gone after the failure and l9 states the run must leave the directory exactly as found, which covers the stale plan file being readable unchanged. |
| `g1.r2.observability#7` | stated | `g1.r2.l9`, `g1.r2.say15` | "a raise should leave it exactly as it found it" is a contract on contents as well as presence, so requests_2.jsonl still reading the stale bytes was decided out loud. |
| `g1.r2.rule#1` | n/a | — | This is the suite guarding its own five-row fixture against planner drift, not a behaviour anyone in the corpus owed a statement about. |
| `g1.r2.rule#2` | stated | `g1.r2.h1`, `g1.r2.l3`, `g1.r2.l1`, `g1.r2.l5` | dario names the glob of stale requests_*.jsonl and its removal outright, l3 says overwriting the prefix isn't enough and the leftovers have to come off disk, and l1 supplies the exact requests_4/reque |
| `g1.r2.rule#3` | stated | `g1.r2.h1`, `g1.r2.h2`, `g1.r2.l2` | metadata_*.json is named in the same breath as requests_*.jsonl in h1 and h2, and l2 spells out the stale metadata_3.json from a previous split as the failure being fixed. |
| `g1.r2.rule#4` | n/a | `g1.r2.l3`, `g1.r2.say15` | That requests_0.jsonl holds the rows of plan[0] is the base create_request_files behaviour the feature request already fixes; l3 only presupposes it while arguing about the leftovers. |
| `g1.r2.scope#1` | stated | `g1.r2.l4`, `g1.r2.l5` | konrad names the explicit batch_size branch and says pulling request files out from under incomplete_files restarts half-paid runs, and dermot says the cleanup stays inside the auto sizing branch beca |
| `g1.r2.scope#2` | stated | `g1.r2.l5`, `g1.r2.h1`, `g1.r2.say15` | dermot says the whole cleanup stays in the auto branch, and h1/say15 define that cleanup as exactly the requests_*.jsonl and metadata_*.json globs, so the metadata file is covered by the same sentence |
| `g1.r2.scope#3` | stated | `g1.r2.l4`, `g1.r2.l5` | l4's stated reason for sparing the fixed branch is that its leftover request files are what incomplete_files resumes from, i.e. they survive with their contents, and a three-batch plan never rewrites  |
| `g1.r2.scope#4` | stated | `g1.r2.l6` | emil says the dataset=None leg has nothing there to tidy and to leave that one alone, which is the decision not to sweep on that path. |
| `g1.r2.scope#5` | stated | `g1.r2.l6`, `g1.r2.h1` | "leave that one alone" applies to the leg as a whole, and the sweep it would otherwise inherit is the two-glob cleanup that includes metadata_*.json. |
| `g1.r2.scope#6` | stated | `g1.r2.l6` | emil states the None leg never writes a request file at all, so a pre-existing requests_3.jsonl is left byte-identical with no further reasoning needed. |

### `g1.r1.rule#8` — implied

```python
assert list(doc) == ["plan_format_version", "plan_id", "limits", "num_batches", "num_requests", "num_bytes", "batches"], f"the sidecar's envelope is {list(doc)}"
```

l5 pins the first two keys and l6/l7 pin limits→num_batches→num_requests→num_bytes, but nobody says batches comes last or gives the envelope as one ordered list — the reader has to splice three remarks and supply the tail.
