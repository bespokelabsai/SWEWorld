# Was every graded thing said, or only implied? — g1

**62 of 69** assertions rest on something a remark says outright.

- `stated` **62** — a reader was told
- `implied` **3** — a reader has to work it out, and may not
- `absent` **0** — nothing in the corpus bears on it
- `not_required` **4** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

> **These verdicts are what provoked the rewrites, not what the plant says now.** 1 remark(s) rewritten, 2 added, 1 not fixed. Re-run `settle --dry-run` for the verdicts on the corpus as it now stands.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g1.r1.exclusions_or_crossover#1` | stated | `g1.r1.rev2`, `g1.r1.l4`, `g1.r1.rev1` | dermot twice says the resume path reads metadata_0.json and wants `{"num_jobs": n}` "and nothing else", explicitly naming start_idx, end_idx and num_bytes as the fields that came back out and must be  |
| `g1.r1.exclusions_or_crossover#2` | stated | `g1.r1.l4`, `g1.r1.say24`, `g1.r1.say23` | l4 states the equality directly — the n in metadata_{i}.json's num_jobs "is exactly the plan's num_requests for that batch" — and say24/say23 corroborate that num_requests in the batch entry carries t |
| `g1.r1.failure_behavior#1` | stated | `g1.r1.f2`, `g1.r1.f3`, `g1.r1.l2` | konrad names BatchPlanTooFragmentedError outright as the thing the planner raised past his handler, and the planner module is where the limits dataclass and its errors live. |
| `g1.r1.failure_behavior#10` | stated | `g1.r1.f4` | emil reports that exact dataset (600 ten-byte rows plus one 5000-byte row under a 1000-byte cap) misreporting as too fragmented and rules "per-row oversize reports first". |
| `g1.r1.failure_behavior#11` | stated | `g1.r1.f4` | f4 says the error should be "naming row 600", fixing which row index the per-row error must carry, though the field spelling row_idx itself is never written here. |
| `g1.r1.failure_behavior#2` | stated | `g1.r1.f2` | "its own ValueError" says the base class in as many words. |
| `g1.r1.failure_behavior#3` | stated | `g1.r1.f2` | konrad reports that except BatchPayloadTooLargeError sailed straight past it and calls that the right call, so the non-subclass relationship is decided out loud. |
| `g1.r1.failure_behavior#4` | stated | `g1.r1.say28` | gideon reports [10]*512 at one row per batch "planned all 512 and came back clean" — the boundary count and its admissibility are both said. |
| `g1.r1.failure_behavior#5` | stated | `g1.r1.say28`, `g1.r1.f2`, `g1.r1.f1` | say28 fixes 513 as the first count that refuses and f2 attaches that refusal to BatchPlanTooFragmentedError with the 513 figure. |
| `g1.r1.failure_behavior#6` | stated | `g1.r1.f2` | f2 spells the attribute and the value together: "err.num_batches 513". |
| `g1.r1.failure_behavior#7` | stated | `g1.r1.f2`, `g1.r1.say28` | f2 says "err.limit 512 off the default", naming the attribute, the value, and that it comes from the default limit. |
| `g1.r1.failure_behavior#8` | stated | `g1.r1.f3`, `g1.r1.f2`, `g1.r1.l12` | nikolai describes exactly this test — BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes — as raising the same fragmentation error f2 named. |
| `g1.r1.failure_behavior#9` | stated | `g1.r1.f3` | f3 asserts err.num_batches == 3 and err.limit == 2 verbatim, so an explicit max_batches_per_plan being honoured is said. |
| `g1.r1.observability#1` | stated | `g1.r1.l7`, `g1.r1.l6` | l7 speaks about the hashing routine's behaviour on an empty plan ("just hashes the empty string", "first twelve of the sha256", "no special case needed") and gives e3b0c44298fc, while l6 names plan_fi |
| `g1.r1.observability#2` | **implied** | `g1.r1.l6`, `g1.r1.l7`, `g1.r1.say24`, `g1.r1.f3`, `g1.r1.l12` | The fingerprint recipe is stated but the greedy byte-cap packing that produces 3/3/1 batches from [10]*7 under a 32-byte cap is only demonstrated by the five-row sample, never stated as a rule, and ad |
| `g1.r1.observability#3` | stated | `g1.r1.l6`, `g1.r1.say23`, `g1.r1.say24` | l6 gives the exact call and result — the string plan_fingerprint hashed for the five-row sample was 0-2:307;2-4:307;4-5:153 and it came back f4b1ea1573c0 — with say23 fixing the five PlannedBatch fiel |
| `g1.r1.observability#4` | n/a | — | This is the suite guarding its own fixture against drift, so the corpus owes it nothing. |
| `g1.r1.observability#5` | stated | `g1.r1.l6`, `g1.r1.l7`, `g1.r1.l8`, `g1.r1.say28` | l6 states the hashed string's format and l7 states the sha256-first-twelve rule, l8 confirms index and num_requests are excluded, and say28 already frames one-row-per-batch planning, so the plan and i |
| `g1.r1.observability#6` | stated | `g1.r1.say22`, `g1.r1.rev1`, `g1.r1.l12`, `g1.r1.say23`, `g1.r1.say24`, `g1.r1.l6`, `g1.r1.l11`, `g1.r1.l10` | say22 pins the exact top-level key set and order, rev1 the version 1 sidecar in the working dir, l12 the limits-as-asdict and the 767 total, say23/l11 the five per-batch fields, and say24 plus l6's sp |
| `g1.r1.observability#7` | stated | `g1.r1.l12` | l12 says limits is dataclasses.asdict of the BatchLimits it planned under, naming all three fields, which is precisely the demand that the patched 3/400 show up rather than defaults. |
| `g1.r1.observability#8` | stated | `g1.r1.l3`, `g1.r1.say22` | l3 instructs dumping with indent 2 and ending the file with a newline, and say22 puts batches last, so the closing bracket-brace-newline tail is what was asked for. |
| `g1.r1.rule#1` | stated | `g1.r1.l2`, `g1.r1.l9`, `g1.r1.l6`, `g1.r1.l10`, `g1.r1.l11`, `g1.r1.l12` | l2 puts PLAN_FILE_NAME in the planner module, l9 names PLAN_FORMAT_VERSION in that same module, and l6/l10 name plan_fingerprint and plan_document as things that hash and write. |
| `g1.r1.rule#10` | stated | `g1.r1.l6`, `g1.r1.l7`, `g1.r1.l8` | l6 says plan_fingerprint's hash of the canonical string came back f4b1ea1573c0 and l7 says plan_id is the first twelve of that same sha256, pinning both expressions to one recipe. |
| `g1.r1.rule#11` | stated | `g1.r1.l12` | l12 says limits is dataclasses.asdict of the BatchLimits it planned under, naming all three fields. |
| `g1.r1.rule#12` | stated | `g1.r1.l11`, `g1.r1.l13`, `g1.r1.say22` | l11 has the viewer read num_batches straight off the top and l13 fixes it at 0 for the zero-row plan. |
| `g1.r1.rule#13` | stated | `g1.r1.l11`, `g1.r1.say22` | l11 says the request total sits at the top level alongside num_batches, which is the sum over the planned batches. |
| `g1.r1.rule#14` | stated | `g1.r1.l11`, `g1.r1.say22` | l11 names the byte total as a top-level field read off the top, i.e. the sum across batches. |
| `g1.r1.rule#15` | stated | `g1.r1.l11` | l11 says the batches key is one dataclasses.asdict per PlannedBatch, index and num_requests included. |
| `g1.r1.rule#16` | stated | `g1.r1.say23`, `g1.r1.say24` | say23 lists the five fields in that order and say24 shows batches[0] as a literal object in the same order. |
| `g1.r1.rule#17` | **implied** | `g1.r1.l10`, `g1.r1.rev1`, `g1.r1.l3`, `g1.r1.l12` | Nobody says the sidecar's contents are exactly plan_document's return value, nor that it is called as plan_document(plan, limits) — the reader must join l10's 'keys plan_document writes' to rev1's fil |
| `g1.r1.rule#2` | stated | `g1.r1.l2`, `g1.r1.rev1` | l2 quotes the assignment verbatim: PLAN_FILE_NAME = "batch_plan.json". |
| `g1.r1.rule#3` | stated | `g1.r1.l9`, `g1.r1.rev1` | rev1 fixes the version at 1 and l9 says that same inlined 1 should come from PLAN_FORMAT_VERSION sitting in the module. |
| `g1.r1.rule#4` | stated | `g1.r1.l8`, `g1.r1.l6` | l8 reports renumbering batches by hand and getting the identical id back, and says index and num_requests aren't in what gets hashed. |
| `g1.r1.rule#5` | stated | `g1.r1.l6` | l6 spells the hashed string as start-end:num_bytes per batch, so the byte size is decided to be part of the digest. |
| `g1.r1.rule#6` | stated | `g1.r1.l6`, `g1.r1.l5` | l6 puts start and end of each batch in the hashed string, and l5 says the point of the short string is to tell whether the split moved. |
| `g1.r1.rule#7` | n/a | `g1.r1.l6`, `g1.r1.say24` | This is the suite guarding its own five-row fixture against drift, not a decision the corpus owes. |
| `g1.r1.rule#8` | stated | `g1.r1.say22`, `g1.r1.l10` | say22 lists all seven top-level keys in exactly that order and says nothing else at the top level. |
| `g1.r1.rule#9` | stated | `g1.r1.rev1`, `g1.r1.l10` | rev1 states plan_format_version 1 for the sidecar and l10 keeps it as the first key plan_document writes. |
| `g1.r1.scope#1` | stated | `g1.r1.rev1`, `g1.r1.l2`, `g1.r1.l1` | rev1 decides the plan moves into a sidecar "batch_plan.json in the working dir ... auto branch only" and l2 names PLAN_FILE_NAME = "batch_plan.json" in the planner module, so writing that file on an a |
| `g1.r1.scope#2` | stated | `g1.r1.l16` | l16 says outright "plan gets written before the first request file" after describing a job dying mid-write with nothing on disk saying how many were expected. |
| `g1.r1.scope#3` | stated | `g1.r1.say25` | say25 names the function and its zero-row return directly: "create_request_files hands back an empty list there, so there's no requests_0.jsonl sitting around". |
| `g1.r1.scope#4` | **implied** | `g1.r1.l13`, `g1.r1.say22`, `g1.r1.say25` | l13 commits only to writing the file with num_batches 0 and say22 only lists the top-level keys; the reader has to supply for themselves that num_requests, num_bytes and batches come out 0, 0 and [] r |
| `g1.r1.scope#5` | stated | `g1.r1.l6`, `g1.r1.l7`, `g1.r1.l8` | l6 says the string plan_fingerprint hashed was the per-batch span/byte join and "it came back f4b1ea1573c0" — the function returns the digest over the batches — and l7 says for the empty plan it just  |
| `g1.r1.scope#6` | stated | `g1.r1.l14`, `g1.r1.rev1` | l14 explicitly forbids it — "if a fixed batch_size run also drops a plan_id file next to the requests, my loader will read that run as auto-sized. Keep it to the auto branch" — and rev1 repeats "auto  |
| `g1.r1.scope#7` | stated | `g1.r1.l15` | l15 states the dataset-None online path has "nothing to plan there, so we leave the working dir alone on that route". |
| `g1.r2.exclusions_or_crossover#1` | stated | `g1.r2.rev2`, `g1.r2.rev1`, `g1.r2.l10`, `g1.r2.l11`, `g1.r2.l8`, `g1.r2.l9` | konrad and dario both say the sweep touches only requests_*.jsonl and metadata_*.json, dario says it leaves everything it isn't deleting in place, and the corpus separately names responses_*.jsonl, th |
| `g1.r2.exclusions_or_crossover#2` | stated | `g1.r2.l10`, `g1.r2.rev2` | dario states outright that the sweep "doesn't just leave it in place, it leaves the bytes untouched, same for everything it isn't deleting", which is the byte-for-byte equality this assertion evaluate |
| `g1.r2.failure_behavior#1` | n/a | `g1.r2.l4`, `g1.r2.l15`, `g1.r2.l9` | The comment marks it as a fixture-drift guard on the suite's own pre-populated directory, and no remark counts files to 14 (l4 gives 6+6, l15 adds batch_plan.json) — the corpus owes this number nothin |
| `g1.r2.failure_behavior#2` | stated | `g1.r2.rev1`, `g1.r2.l14`, `g1.r2.l12` | rev1 says plan_request_batches threw SingleRequestTooLargeError and l14 names the class as what comes back from the oversized-row fixture, so the reader is told planning raises exactly this name. |
| `g1.r2.failure_behavior#3` | stated | `g1.r2.l14` | l14 says the error "comes back with row_idx 1 on it", attaching both the field name and the value 1 to the raised exception object. |
| `g1.r2.failure_behavior#4` | stated | `g1.r2.l14`, `g1.r2.rev1`, `g1.r2.l12` | Same class named as the outcome of planning on the oversized row by l14 and rev1; a second raising call needs no further license. |
| `g1.r2.failure_behavior#5` | stated | `g1.r2.rev1`, `g1.r2.rev2`, `g1.r2.l13`, `g1.r2.l10`, `g1.r2.l12` | rev1 and rev2 move the sweep after planning precisely because the throw wiped the dir, l13 says a run that raises has changed nothing on disk "stale or not", and l10 says untouched means the bytes the |
| `g1.r2.observability#1` | stated | `g1.r2.l4`, `g1.r2.h1`, `g1.r2.h2`, `g1.r2.rev2`, `g1.r2.l3`, `g1.r2.l1` | konrad's l4 describes this exact fixture (requests_0..5 plus matching metadata, plan makes three, "the listing afterwards is the assertion") and h1/h2/rev2 name the sweep glob as requests_*.jsonl and  |
| `g1.r2.observability#2` | stated | `g1.r2.l10`, `g1.r2.rev2`, `g1.r2.l8`, `g1.r2.l9` | l10 says the sweep "leaves the bytes untouched, same for everything it isn't deleting", and rev2/h1/h2 enumerate what it deletes without responses_*.jsonl in the list, with l8 pricing the mistake of l |
| `g1.r2.observability#3` | stated | `g1.r2.l14`, `g1.r2.rev1`, `g1.r2.l12` | nikolai names the class SingleRequestTooLargeError and the exact trigger (max_bytes_per_batch pinned to 400, a 600-char prompt), and rev1 confirms planning is what throws it. |
| `g1.r2.observability#4` | stated | `g1.r2.l14`, `g1.r2.rev1`, `g1.r2.rev2` | Same remark pair carries the second raise: the oversized row is said outright to raise SingleRequestTooLargeError out of the planning call the entry point makes. |
| `g1.r2.observability#5` | stated | `g1.r2.rev1`, `g1.r2.rev2`, `g1.r2.l13`, `g1.r2.l12` | rev1 and rev2 both reverse the order precisely because the sweep wiped a dir when the oversized row raised, and l13 states the rule flatly: a run that never gets a plan out "has no business having cha |
| `g1.r2.observability#6` | stated | `g1.r2.l15`, `g1.r2.l13` | l15 puts a stale plan_format_version 1 body in batch_plan.json before the run starts and l13 commits to nothing on disk changing on a failed run, "stale or not", which is that file. |
| `g1.r2.observability#7` | stated | `g1.r2.l13`, `g1.r2.l12`, `g1.r2.l10` | l12 raises truncation-on-open as distinct from deletion ("not just create-on-open though") and l13 plus l10 commit to the bytes of untouched files surviving a run that raised, so content and not merel |
| `g1.r2.rule#1` | n/a | — | This is the suite guarding its own five-row fixture against drift, not a behaviour the corpus owes anything to. |
| `g1.r2.rule#2` | stated | `g1.r2.h1`, `g1.r2.h2`, `g1.r2.l4`, `g1.r2.l1`, `g1.r2.rev1`, `g1.r2.rev2` | h1/h2 say the auto branch deletes requests_*.jsonl outright (rev1/rev2 only move the sweep after planning, never remove it), and l4 states the exact scenario — seed requests_0 through requests_5, let  |
| `g1.r2.rule#3` | stated | `g1.r2.h1`, `g1.r2.h2`, `g1.r2.l4`, `g1.r2.l2`, `g1.r2.rev1`, `g1.r2.rev2` | The same remarks name metadata_*.json alongside requests_*.jsonl in the sweep, l4 seeds 'matchign metadata' next to the six request files, and l2 names a surviving metadata_3.json holding a previous s |
| `g1.r2.rule#4` | stated | `g1.r2.l3`, `g1.r2.l4` | l3 says a requests_0.jsonl already sitting there gets swept with the rest and rewritten from this run's plan, 'its own start_idx to end_idx' — the file, the field names and the row range are all spoke |
| `g1.r2.scope#1` | stated | `g1.r2.l7`, `g1.r2.l5`, `g1.r2.h1`, `g1.r2.rev1` | dario says the explicit batch_size=1000 branch must not pick up the new behaviour and emil warns that clearing the files the integer path leans on makes every resume start from zero, so leaving reques |
| `g1.r2.scope#2` | stated | `g1.r2.l7`, `g1.r2.l5`, `g1.r2.h2`, `g1.r2.rev2` | every description of the sweep names it as the single pair requests_*.jsonl and metadata_*.json, so the instruction that the integer branch does not take on that behaviour covers the metadata files by |
| `g1.r2.scope#3` | stated | `g1.r2.l7`, `g1.r2.l5`, `g1.r2.l10` | l7 says that branch keeps giving the same files it always has and l10 establishes that anything not being deleted keeps its bytes, so an untouched leftover requests_5.jsonl retaining its stale content |
| `g1.r2.scope#4` | stated | `g1.r2.l6` | nikolai says create_request_files is called with dataset=None purely to get the paths back and that he would be unhappy if that call ever started taking files away. |
| `g1.r2.scope#5` | stated | `g1.r2.l6`, `g1.r2.h1`, `g1.r2.rev2` | "taking files away" is unqualified and the sweep set is consistently named as requests_*.jsonl plus metadata_*.json, so the prohibition on the dataset=None path covers metadata files too. |
| `g1.r2.scope#6` | stated | `g1.r2.l6`, `g1.r2.l10` | the dataset=None call is described as doing nothing but returning paths, which leaves the seeded requests_3.jsonl neither deleted nor rewritten. |

### `g1.r1.observability#2` — implied

```python
assert module.plan_fingerprint(module.plan_batches([10] * 7, module.BatchLimits(max_requests_per_batch=1000, max_bytes_per_batch=32))) == "ad0828fea95e"
```

The fingerprint recipe is stated but the greedy byte-cap packing that produces 3/3/1 batches from [10]*7 under a 32-byte cap is only demonstrated by the five-row sample, never stated as a rule, and ad0828fea95e appears nowhere.

### `g1.r1.rule#17` — implied

```python
# ...and the document is what `plan_document` builds for that plan.
    assert doc == json.loads(json.dumps(module.plan_document(plan, limits)))
```

Nobody says the sidecar's contents are exactly plan_document's return value, nor that it is called as plan_document(plan, limits) — the reader must join l10's 'keys plan_document writes' to rev1's file and invent the signature.

### `g1.r1.scope#4` — implied

```python
assert (empty_doc["num_batches"], empty_doc["num_requests"], empty_doc["num_bytes"], empty_doc["batches"]) == (0, 0, 0, [])
```

l13 commits only to writing the file with num_batches 0 and say22 only lists the top-level keys; the reader has to supply for themselves that num_requests, num_bytes and batches come out 0, 0 and [] rather than, say, an omitted or null batches key.
