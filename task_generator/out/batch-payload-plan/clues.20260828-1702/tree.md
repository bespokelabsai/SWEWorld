# The tree

## g1.r1

### g1.r1.sc1 — An auto-sized run leaves behind one versioned JSON file, `batch_plan.json`, in the working directory, and that file is the single place the shape of the split is recorded; the per-batch metadata files keep the body they have today.

*The leap nobody states:* If one per-run file is the only honest record of how a run was split, then nothing about the split gets bolted onto the per-batch files.

- **gideon** (2025-04-28, #viewer): same shape of thing honestly - the viewer opens every requests_*.jsonl in the run dir just to say how many batches there were, give me one batch_plan.json and I'd stop doing that
- **konrad** (2025-04-02, #code-review): look, I can't tell an old run dir from a newer one without guessing at the keys — whatever new file we start writing should say which version of the format it is
- **nikolai** (2025-04-23, #engineering): i mean the cookbook loader reads metadata_0.json and expects num_jobs and nothing else anything extra in there and it trips on the unkown key
- **dermot** (2025-05-06, ##batch-mode): there is no honest way to reconstruct an auto run's split from the per-batch files after the fact, so it goes in one file per run and those files stay as they are

### g1.r1.sc2 — That document records the limits the plan was made under, the run totals, and for every batch its start/end span and its byte size, where the byte figures are the batch files' own sizes summed rather than anything measured on disk; it is written pretty-printed at two-space indent, keys always in the same order, ending in a newline.

*The leap nobody states:* A file whose whole job is to let two runs be compared has to be both complete enough and stable enough to diff line by line.

- **dario** (2025-04-03, #pipeline): and when i patch the ceilings down localy to reproduce a split, nothing on disk says which ceilings were in force, or where each batch started and ended
- **nils** (2025-03-19, #pipeline): let me think - du on the run dir gives me a different number than what we actually uploaded. the size worth writing down is the batch files we hand the provider, summed.
- **emil** (2025-04-09, #engineering): Dumped the metadata for two verification runs and diffing them was hopeless, the whole thing comes out as one line. two space indent please, honestly it's meant to be read.
- **dermot** (2025-03-24, #pipeline): when you sketch it: keys written in the order we build them, otherwise the diff is all noise every run. file should end with a newline.

### g1.r1.sc3 — A plan carries a short identifier: the first twelve characters of the sha256 hexdigest of a canonical string built only from each batch's span and byte size, joined one entry per batch, and a plan with no batches still gets one from the empty string.

*The leap nobody states:* If the id is meant to be the same for the same split, only the things that make up the split can go into what gets hashed.

- **dario** (2025-04-21, #pipeline): for emil's list — two runs that split identically should carry the same handle even if the batches get renumbered, so key it off the spans and the sizes, counts fall out of the spans anyway
- **konrad** (2025-04-03, #engineering): look, I want a short handle for a split I can paste into a ticket - sha256 hex is 64 charcters, nobody reads that, first twelve is plenty here
- **emil** (2025-05-13, ##batch-mode): did the five row one by hand — the string i hashed was 0-2:307;2-4:307;4-5:153, one entry per batch, span and byte size, semicolons between them.
- **nikolai** (2025-04-23, #engineering): a run that plans zero batches still needs a handle, i'd say hash the empty string and move on rather than writing a null in there for the empty case

### g1.r1.sc4 — Only the auto-sizing path writes the file, and it writes it once the plan is known and before any request or metadata file goes down, including when the plan came out with no batches at all; the explicit integer batch_size path and the path with no dataset leave the directory without one.

*The leap nobody states:* A record of how we chose to split is only worth keeping where we did the choosing.

- **nils** (2025-03-21, ##pipeline): run fell over partway through writing requests_3.jsonl and the dir told me nothing about what it had meant to do. i think the plan goes down before the first request file
- **konrad** (2025-03-26, #engineering): Look, with batch_size=2 the user already told us the split, so there is nothing of ours to record. Same when there is no dataset to plan over at all.
- **gideon** (2025-04-23, #pipeline): ya, and pointed it at an empty dataset and got an empty working dir - no way to tell if it planned zero batches or fell over befoer it started.
- **emil** (2025-06-24, ##batch-mode): let me think through that, even when theres nothing to batch id rather open the dir and find the plan file sitting there with zeros in it than find nothing at all

### g1.r1.sc5 — The number of batches a plan may contain is itself a limit carried alongside the other two with a default of 512, checked once the full plan has been built, and going over it stops the run with a distinct error naming the count the plan would have needed and the cap; a row that is oversize on its own is reported as that instead.

*The leap nobody states:* A ceiling that only matters once you know the whole plan has to be enforced after the plan is built, and reported as its own failure rather than folded into the existing one.

- **gideon** (2025-03-14, #code-review): honestly though same shape on the batch side, someone set the request cap to 1 over a 40k row set and we happily sat there writing 40k batch files, nothing stopped it
- **konrad** (2025-04-09, #engineering): Look, the cap belongs on BatchLimits next to the other two, defaulted to 512. Exactly 512 should still go throuh, 513 is where it stops.
- **nikolai** (2025-06-16, thread:<178771578160.2500381.12817086076544913041@world.local>): on 690 id say that failure should report the full batch count and the cap and stay out of the except catching the oversize payload one its own ValueError
- **nils** (2025-03-20, ##engineering): if a single row is too big i want to hear about that row. being told the plan came out too fragmented cost me a morning in the wrong place.

### herrings — believed at the time, reversed later

- **dario** (2025-02-04): mhm - settled in review, the span lives in metadata_{i}.json next to num_jobs, so each batch file carries its own start_idx, end_idx and num_bytes, no separate file
- **gideon** (—): so basically metadata_{i}.json comes out as {"num_jobs": 2, "start_idx": 0, "end_idx": 2, "num_bytes": 307} now, the planner writes those three extra keys on top of num_jobs.

## g1.r2

### g1.r2.s1 — When an "auto" run produces a shorter plan than the run before it, the request and metadata files left over from the longer numbering are still on disk and still get read, so they have to be taken off disk before the new files are written rather than partially overwritten.

*The leap nobody states:* Two families of file are written per batch, so leftovers of both kinds are read back later; if writing the new plan only covers the low indices, the high ones are still there and still look real.

- **gideon** (2025-04-24, #code-review): so basically i reran auto after we lowered the byte ceiling and the glob handed me six requests_*.jsonl when the plan only had three batches in it
- **nikolai** (2025-04-16, #cookbooks): right and on a rerun here metadata_4.json outlived its requests file and the reader jsut counted its num_jobs like nothing was wrong
- **dario** (2025-04-17, #pipeline): honestly overwriting the low numbered ones does nothing when the new plan comes out shorter, the leftovers have to be gone before we write anything at all

### g1.r2.s2 — This clearing belongs only to the sizer-chosen path; the fixed-width integer path and the path that is handed no dataset both leave the working directory as they found it.

*The leap nobody states:* Only a path that chooses its own file count can change that count between runs, and the other paths depend on old files still being there.

- **konrad** (2025-04-08, #code-review): look, on a rerun with explicit batch_size=64 the whole point of incomplete_files is that resume stays cheap, so nothing shoud be touching the files it skips
- **dermot** (2025-04-07, page:design/ws-055-release-engineering-ci-test-suite.md): Worth noting while I am in here: when `create_request_files` gets no dataset we are only listing what is already on disk, the directory is not ours to change on that call.
- **emil** (2025-05-06, #pipeline): let me think through that - the number of files only moves between runs on the path where the sizer picks it, fixed width always writes the same count for the same dataset.

### g1.r2.s3 — Only the two families of file the request stage itself writes are removed; responses, arrow caches, batch object records and anything else in the working directory are left byte-for-byte.

*The leap nobody states:* A working directory is shared by several stages, and the expensive artifacts in it were not produced by this one.

- **nils** (2025-03-24, ##batch-mode): let me think — someone's tidy-up once took responses_0.jsonl with it and i paid for four thousand rows a second time, that one still stings
- **emil** (2025-03-21, page:design/batch-job-status-persistence-across-process-restarts.md): - Also in the same `working_dir`: `batch_objects.jsonl` and the `*.arrow` cache, neither of which is written by the request stage
- **dermot** (2025-05-13, #code-review): for the cleanup, go by the name patterns of the files this stage writes and leave the rest of the fingerprint directory alone, this is not a directory wipe.

### g1.r2.s4 — Nothing is removed and nothing is written until the planner has returned a plan; if planning raises, the working directory is exactly as it was, stale files included.

*The leap nobody states:* A step that can abort must not have already destroyed anything by the time it aborts.

- **konrad** (2025-03-26, ##engineering): look, I hit SingleRequestTooLargeError on the second row and came back to an empty working dir — those files were fine two secodns earlier
- **dario** (2025-03-21, #code-review): on the batch side it's the other way round — plan_request_batches either comes back with a plan or it raises, so nothign that touches disk belongs above that call
- **emil** (2025-04-17, ##eng-batch): honestly if we abort on BatchPlanTooFragmentedError i want the old batch_plan.json left sitting there untouched, so i can diff it against whatever we just tried to build.

### herrings — believed at the time, reversed later

- **dario** (—): the sweep is the first thing in the auto branch, glob away requests_*.jsonl and metadata_*.json, then plan_request_batches gets called. clean slate before we plan anything.
- **konrad** (—): Right, ordering is settled - the auto branch clears the stale request and metadata files on entry, then calls plan_request_batches. No point planning against a directroy we're about to empty.

