# The tree

## g1.r1

### g1.r1.s1 — The automatically-sized path leaves behind one versioned JSON file, named by a constant the planner module exports, as the only on-disk record of how rows were split; the per-batch metadata files keep the body they have today.

*The leap nobody states:* If the only artefacts of an auto run are the request files and a metadata body nobody may extend, the split has to be described somewhere new, and there is exactly one such place.

- **gideon** (2025-04-23, #pipeline): ya same on my side - an auto run gave me 9 request files and nothing says which rows landed in requests_3.jsonl, had to reopen all of them to find one promt
- **dermot** (2025-04-24, #pipeline): for the wiki page: the planner module holds PLAN_FILE_NAME and PLAN_FORMAT_VERSION next to the two dataclasses, version starts at 1 and only moves when the key set changes.
- **nils** (2025-06-19, page:engineering/batch-payload-directory-on-disk-layout.md): let me think - our reader for metadata_{i}.json asserts the body is num_jobs and nothing else, it bails on anything extra, so please keep the span keys out of those.
- **konrad** (2025-05-14, thread:new|g1.r1.l4): Anyway while house rules are going on record - batch_plan.json should be written with indent 2 and a newline at the end, our review diffs are unreadble when it comes out on one line.

### g1.r1.s2 — That file's body is a document built by one planner helper, with a fixed key order running format version, id, the limits block, then the whole-run totals, then a row per batch; the byte total is the batch files' sizes summed.

*The leap nobody states:* Everyone reading the file reads it positionally and expects the same keys, so the document is generated once, in a settled order, from the plan objects themselves.

- **emil** (2025-04-29, #pipeline): nit on the plan_document draft — i'd put plan_format_version first and the id right after it, i want to know whether i can parse the rest before i read it.
- **nikolai** (2025-04-09, page:engineering/run-dashboard-what-it-reads-out-of-the-run-manifest.md): for the run dashbaord i read num_batches and num_requests straight after the limits block i dont walk the per batch rows myself so keep those in as well
- **dermot** (2025-04-09, thread:new|g1.r1.l7): the num_bytes beside those counts should just be the sizes create_batch_file hands back, summed — i checked the current figure against du on the dir and they don't agree.
- **gideon** (2025-04-16, #code-review): so basically the limits block in the doc came out with three keys once max_batches_per_plan landed, and my snapshot only pinned the two byte/request ones, so it's red.

### g1.r1.s3 — The document's id is a short hash of the plan's spans and byte sizes only, produced by the planner's fingerprint helper, so an empty plan hashes the empty string.

*The leap nobody states:* If two runs are compared by a single short token, the token has to be derived from exactly the fields that define the split and nothing that renumbering could change.

- **dario** (2025-04-07, page:design/batch-job-status-persistence-across-process-restarts.md): i think plan_fingerprint should hash just the batches joined, 0-2:307;2-4:307 - spans and bytes, not index, not num_requests. utf-8 encode, sha256, keep the front of the hexdigest.
- **nikolai** (2025-04-08, #engineering): first cut on request_id - sha256 hexdigest is 64 chars and the full thing just wraps the log line so twelve off the front is plenty for eyballing two runs against each other
- **emil** (2025-05-13, #code-review): honestly the empty plan case looks fine as-is to me - zero batches join to nothing, and plan_fingerprint([]) still handed back e3b0c44298fc, i don't think we need to special-case it
- **konrad** (2025-04-09, #pipeline): Right, I renamed the colum in my run notes to plan_id then, I had it down as plan_hash. It's whatever plan_fingerprint hands back - twelve hex chars, f4b1ea1573c0.
- **nils** (2025-03-14, #general): ran the auto path over an empty input this morning and plan_fingerprint still handed me back a plan_id, same one i get hashing an empty string in a repl.
- **dermot** (2025-03-17, #releases): yeah - plan_id is a digest of the canonical batch lines and nothing else; zero lines join to an empty string and that goes into sha256 like any other input.

### g1.r1.s4 — The record is written only on the auto path, before any request or metadata file goes out, and it is written even when the plan came out with no batches; the explicit-size and no-dataset paths leave the working directory exactly as it is today.

*The leap nobody states:* A record that only appears when the planner had something interesting to say is not a record, and a path where the caller chose the split has nothing for the planner to describe.

- **dario** (2025-03-24, #pipeline): honestly the other half of this - i had a run die partway through writing requests_*.jsonl and nothing on disk said what it had been aiming for. batch_plan.json wants to land before the first requests file, metadata too
- **gideon** (2025-03-14, #code-review): auto path on an empty dataset left me a bare dir. honestly though I'd want batch_plan.json anyway — num_batches 0, num_requests 0, num_bytes 0, batches [], plan_id filled in like any other run.
- **konrad** (2025-03-14, #engineering): Look, if I pass batch_size=2, or I give no dataset at all, then I picked the split myself. no batch_plan.json should be turing up in my working dir for those.

### g1.r1.s5 — A plan that comes out in too many pieces is refused once it has been built, by its own error type carrying the count it would have needed and the ceiling it broke, with the ceiling itself living on the limits dataclass with a default; a single oversized row is reported as that instead.

*The leap nobody states:* Refusing early would mean the error cannot name the real count, and two different faults caught by one except clause is how the wrong one gets swallowed.

- **konrad** (2025-03-17, #engineering): Look, auto sizing with a tigth byte cap gave me 31k request files in one dir. If we refuse that, err.limit alone is useless, I need the count it wanted.
- **nikolai** (2025-06-19, page:engineering/auto-batch-mode-what-the-planner-emits-and-what-bounds-it-pr-691.md): i'd say the cap lives on the limits dataclass as max_batches_per_plan default 512 checked once the plan is finished and a plan landing on exactly 512 is still fine
- **dario** (2025-04-24, #code-review): same family of thing honestly — my except for payload-too-large caught a BatchPlanTooFragmentedError this morning, the outer except ValueError should have had it, those aren't the same failure
- **nils** (2025-06-11, page:engineering/batch-payload-sizing-limits-splitting-and-error-precedence.md): let me think - i sent 600 tiny rows plus one 5MB row and got the fragmentation error back, when what i expected was SingleRequestTooLargeError naming row_idx 600.
- **emil** (2025-03-14, #releases): honestly, went to put the fragmentation count in our alert line and there's no num_batches on the error anywhere, just the ceiling - had to re-derive it from len(plan)

### herrings — believed at the time, reversed later

- **konrad** (2025-01-27): look, from my review pass the auto batches carry {num_jobs, start_idx, end_idx, num_bytes} in each metadata_{i}.json, so the plan lives in the per batch metadata not a seperate file

## g1.r2

### g1.r2.s1 — In the auto sizing path, the request and metadata files already sitting in the working directory are taken off disk before the new plan's files are written, rather than being partly overwritten.

*The leap nobody states:* A run that produces fewer files than the last one leaves the tail of the old numbering behind, and anything that reads the directory by pattern will pick that tail up as if it belonged to the current plan.

- **gideon** (2025-03-26, #pipeline): honestly though I hit a similar one, reran auto with a tighter byte cap and the glob still picked up requests_4.jsonl and requests_5.jsonl from yesterdays six batch run
- **nils** (2025-06-25, page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md): one caveat: metadata_3.json from the previous split still sits in the cache dir reporting its old num_jobs, so a restart reading counts back gets a plan that no longer exists.
- **dario** (2025-06-16, thread:<178771578160.2500381.12817086076544913041@world.local>): on the same note, since people will be in there anyway — writing requests_0 through requests_2 over the top isn't enough if the run before left six of them, the leftovers have to come off disk first

### g1.r2.s2 — That removal is confined to the auto path; the explicit-integer batch_size branch and the no-dataset path leave the working directory untouched.

*The leap nobody states:* A step that only makes sense because the auto path chooses its own file count should not run on paths whose file count is fixed or whose files do not exist.

- **konrad** (2025-03-14, #cookbooks): look, careful with the explicit batch_size branch - we lean on incomplete_files to skip finished work, and pulling request files out from under that restarts runs people already half paid for
- **dermot** (2025-06-26, page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md): yeah, and the cleanup stays inside the auto sizing branch, not hoisted up into create_request_files. the fixed-width branch has its own resume contract, it shouldnt inherit ours
- **emil** (2025-04-29, thread:new|g1.r2.l6): @Gideon on the request processing cleanup - the dataset=None leg never writes a request file at all, so honestly there's nothing there to tidy, i'd leave that one alone

### g1.r2.s3 — The removal is gated on planning having succeeded: if planning raises, nothing is deleted and nothing is written, and the directory is exactly as it was.

*The leap nobody states:* A run that produced no output has no business changing what is on disk, so the destructive step has to sit after the step that can refuse.

- **nikolai** (2025-04-03, #cookbooks): Had a planning run abort on an oversized row and came back to an empty working dir, nothing new written and the files that were fine gone too.
- **gideon** (2025-04-16, page:engineering/ws-050-batch-mode-50-cost-async-batch-apis.md): on submit never dying: so basically it blew up with SingleRequestTooLargeError(row_idx=1, size_bytes=748, limit_bytes=400), then i went to diff the previous batch_plan.json and there was nothing left to diff.
- **dermot** (2025-04-16, thread:new|g1.r2.l9): when the planner refuses a row i'd fix that row and rerun against the same working directory; a raise should leave it exactly as it found it

### g1.r2.s4 — Only the request and metadata files are removed; every other file in the working directory survives untouched, so this is a targeted delete and not a directory wipe.

*The leap nobody states:* The working directory holds expensive and unrecoverable artifacts alongside the cheap regenerable inputs, so the delete has to be by name rather than by folder.

- **dario** (2025-04-21, thread:<178770212973.2301745.4705747507669611471@world.local>): i hit one of these myself actually — cleared the working dir by hand between two auto runs and lost responses_0.jsonl, so we paid for those completions a second time.
- **konrad** (2025-05-02, page:design/batch-job-status-persistence-across-process-restarts.md): look, batch_objects.jsonl is missing here, its how we recover the submitted batch ids, if a rerun in the same directory removes it we cant poll what we already sent.
- **nils** (2025-04-22, #pipeline): let me think - the .arrow shards under provider-integrations are the cached dataset, not fixtures; drop those and we rebuild the whole thing before anything gets submitted
- **nikolai** (2025-06-11, thread:new|g1.r2.l13): i'd say whatever we delete gets named off what that run writes itself wiping the whole folder is a differnt operation and not the one we want here

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): i think the sweep goes as the first statement in the auto branch - glob the stale requests_*.jsonl and metadata_*.json, drop them, then plan_request_batches runs on a clean diretcory
- **emil** (2025-01-22): so to restate the order: in create_request_files we clear the old requests_*/metadata_* on entry, then call plan_request_batches - nothing stale is ever in the dir while we plan?

