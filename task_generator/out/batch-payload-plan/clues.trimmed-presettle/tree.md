# The tree

## g1.r1

### g1.r1.sc1 — An auto-sized run leaves one separate, indented JSON file under a fixed module-level file name in the working dir, and the existing per-batch metadata files are not extended to carry any of it.

*The leap nobody states:* If people keep needing the split after the fact and the per-batch metadata is off limits for it, the record has to be its own file with a name everyone can reach for.

- **gideon** (2025-04-24, #pipeline): so basically someone asked me how tuesday's auto run split and I had to ls the requests_*.jsonl files and re-measure every one of them. that should be sitting on disk.
- **dario** (2025-04-07, page:design/batch-job-status-persistence-across-process-restarts.md): worth adding to the persists-where list: the planner module holds PLAN_FILE_NAME = "batch_plan.json" next to the limits dataclass. nothing imports it from the processor yet, shape is still moving.
- **konrad** (2025-03-25, #code-review): Look, the plan file lands as one enourmous line, so diffing two runs is hopeless. Dump it with indent 2 and end the file with a newline.
- **dermot** (2025-05-08, #pipeline): our resume path json.loads metadata_0.json and expects {"num_jobs": n} and nothing else, so please keep the span and byte fields out of that file

### g1.r1.sc2 — The plan carries a short stable id: the first twelve characters of the sha256 hexdigest of a canonical string built from each batch's start-end span and its byte size, joined per batch, with the batch index and request counts left out.

*The leap nobody states:* Two runs that split the same way must produce the same token, so only the facts that define the split can go into the hashed string, and the digest is truncated to stay readable.

- **nils** (2025-03-26, #engineering): spent the morning diffing two batch runs span by span just to confirm the split hadn't moved. one short comparable string per plan would have answered that in a second.
- **dario** (2025-03-26, #pipeline): for the five row sample the string plan_fingerprint hashed was 0-2:307;2-4:307;4-5:153, so start-end:num_bytes per batch joined on semicolons, and it came back f4b1ea1573c0
- **emil** (2025-05-07, #pipeline): empty plan just hashes the empty string, so plan_id comes out e3b0c44298fc, first twelve of the sha256. no special case needed.
- **nikolai** (2025-04-18, #incidents): renumberd the batches by hand while poking at a failure and got the identical id back right call i mean the index and num_requests arent in what gets hashed

### g1.r1.sc3 — The body is one document: a format version key first, then the id, the limits it was planned under, the batch/request/byte totals, then the per-batch entries.

*The leap nobody states:* A consumer decides whether it can read the file at all, then wants the summary, and only then the detail, so the keys come in that order.

- **emil** (2025-05-21, #code-review): nit on the plan writer - you've got the 1 inlined in three seperate spots, and PLAN_FORMAT_VERSION is sitting right above it in the same module.
- **dermot** (2025-04-10, thread:new|g1.r1.l10): yeah — keep plan_format_version as the first key plan_document writes; a reader that cannot find it up front has no business parsing the rest.
- **gideon** (2025-04-22, #viewer): so basically the viewer wants num_batches and the request and byte totals off the top of the file, not walking batches and summing them itself.
- **nikolai** (2025-06-16, thread:<178771578160.2500381.12817086076544913041@world.local>): good that the plan file records the caps it planned under 3 requests and 400 bytes that run otherwise three batches and 767 bytes tells you nothign a month later

### g1.r1.sc4 — The file is written on the auto branch only and before any request file, and is still written when the plan came out empty; the explicit-integer branch and the dataset-is-None path never write it.

*The leap nobody states:* The file is the marker that the auto sizer ran and what it intended, so it must exist exactly when the auto sizer ran, including the zero-row case, and never otherwise.

- **nils** (2025-03-19, #pipeline): let me think — a zero row auto run leaves the working dir completely empty and my checker can't tell that from a crash. we write the file regardless, num_batches 0.
- **konrad** (2025-04-15, thread:new|g1.r1.l14): Look, if a fixed batch_size run also drops a plan_id file next to the requests, my loader will read that run as auto-sized. Keep it to the auto branch.
- **dario** (2025-03-24, #pipeline): One thing that's already clear from the sketch - the online path calls create_request_files with dataset None, nothing to plan there, so we leave the working dir alone on that route.
- **gideon** (2025-04-23, #pipeline): same gap on my end - job died writing requests_3.jsonl and nothing on disk said there were supposed to be nine. plan gets written before the first request file.

### g1.r1.sc5 — A plan split into more batches than a configurable ceiling, defaulting to 512, is rejected with a dedicated error carrying the batch count and the ceiling, distinct from the oversize-payload errors, and checked only after the per-row oversize scan.

*The leap nobody states:* A run that shatters into thousands of files is a different failure from one payload being too big, so it needs its own error and must not steal the report from the row that is genuinely oversized.

- **gideon** (2025-03-14, #code-review): so basically auto split one job into about 2600 request files and the submit loop crawled all afernoon. past some ceiling it should refuse to plan at all, not run it.
- **konrad** (2025-04-08, #code-review): look, my except BatchPayloadTooLargeError sailed straight past BatchPlanTooFragmentedError — 513 batches, limit 512. right call though, it is its own ValueError and my handler shoud not be touching it.
- **nikolai** (2025-06-18, #code-review): test builds BatchLimits(1, 1000, max_batches_per_plan=2) over three sizes so i dont have to construct 513 spans then asserts err.num_batches == 3
- **emil** (2025-06-17, #engineering): 600 rows of 10 bytes plus one 5000 byte row under a 1000 byte cap and it said too fragmented instead of naming row 600. per-row oversize reports first.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): settled then: the plan rides in metadata_{i}.json — num_jobs plus start_idx, end_idx, num_bytes per batch. no extra file, we already write that metadata per batch.
- **konrad** (2025-01-22): Right, so metadata_0.json comes out as {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307}. The span and the size both live in the per-batch metadata, that's the shape.

## g1.r2

### g1.r2.sc1 — A fresh auto-sized run must not leave request or metadata files from any earlier run sitting in the working directory alongside the ones it just wrote.

*The leap nobody states:* If a shorter plan writes fewer files than last time, the only way the directory can end up holding just this run's output is if the old ones of those two kinds are taken out first.

- **gideon** (2025-04-08, #pipeline): Related-ish, I reran auto on a trimmed dataset and the submit loop picked up requests_4.jsonl and requests_5.jsonl leftover from Tuesdays bigger run, two duplicate batches.
- **nils** (2025-03-21, #code-review): @Emil same class of thing on my end - metadata_3.json in my working dir still reports num_jobs from the old split, and nothing in this run touched it.
- **dermot** (2025-04-11, #cookbooks): yeah. after an auto run the working directory should hold what that run actually produced, not that mixed in with leftovers from an earlier one.
- **konrad** (2025-03-14, #engineering): Look, I seeded the dir with requests_0.jsonl through requests_5.jsonl plus matchign metadata, then let the plan make three - the listing afterwards is the assertion.

### g1.r2.sc2 — Only the automatic sizing path does this; the explicit-integer batch_size path and the dataset-is-None path must behave exactly as they do today.

*The leap nobody states:* Both of those paths depend on files from earlier runs still being there, so whatever removes leftovers cannot be shared code that runs on entry for everyone.

- **emil** (2025-04-21, #pipeline): sounds right - though the integer batch_size path leans on files from earlier runs, incomplete_files is what skips the finished ones, clear those and every resume starts from zero
- **nikolai** (2025-04-17, thread:new|g1.r2.l6): i'd say careful there on resume we call create_request_files with dataset=None purely to get the paths back and i'd be unhappy if that call ever started taking files away
- **dario** (2025-03-14, #releases): honestly explicit batch_size=1000 should keep giving the same fixed-width files it always has, i don't want that branch picking up new behaviour off the side

### g1.r2.sc3 — Only those two families of files are removed; response files, arrow shards, the batch-id file and anything else in the directory are left exactly as they were.

*The leap nobody states:* Everything else in that directory is either paid-for output or state needed to reach in-flight work, so a sweep has to be pattern-scoped rather than a directory wipe.

- **gideon** (2025-03-14, #viewer): so basically someone ran rm -f over the working dir between runs and it took responses_0.jsonl with it, so we paid twice for a batch we had already completed.
- **konrad** (2025-05-02, page:design/batch-job-status-persistence-across-process-restarts.md): Look, the working dir today holds more than those two: requests_*.jsonl, metadata_*.json, responses_*.jsonl, batch_objects.jsonl (submitted batch ids we poll), plus the .arrow shards for the dataset.
- **dario** (2025-04-09, #incidents): not that i've seen. batch_objects.jsonl is unrecoverable state though, it stays put - lose it mid-poll and there's no way back to the submitted batches, they just expire provider side.
- **nils** (2025-03-14, #general): let me think through that - the .arrow shards in the working dir are the dataset itself, drop those and we re-tokenize four million rows before anything even gets submitted

### g1.r2.sc4 — When sizing fails and no plan comes back, the working directory must be left exactly as it was found, stale files included.

*The leap nobody states:* If nothing on disk changes on the failing path, the removal cannot have happened yet at the point the failure is raised.

- **emil** (2025-04-17, #random): not just create-on-open though - the oversized-row failure left me staring at an empty working dir, and the split that was in there beforehand was still perfectly usable
- **dermot** (2025-03-31, #code-review): a run that raises in the estimate step and never gets a plan out the other end has no business having changed anything on disk, stale or not
- **nikolai** (2025-03-14, #cookbooks): fixture pins max_bytes_per_batch to 400 and feeds a 600 char prompt so row 1 raises SingleRequestTooLargeError before anythign comes back
- **nils** (2025-03-17, #general): let me think through that - for the fixture to prove anything, batch_plan.json has to already be sitting in the dir when we start, holding a stale plan_format_version 1 body.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): in any case the sweep is the first thing in the auto branch — clear out requests_*.jsonl and metadata_*.json on entry, then plan_request_batches runs against a clean dir
- **konrad** (2025-01-21): look, order in the auto branch is settled: we delete the old requests_*/metadata_* files first, plan_request_batches second. nothing new gets writen next to stale numbering.

