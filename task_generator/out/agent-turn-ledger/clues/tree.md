# The tree

## g7.r1

### g7.r1.s1 — A small JSON companion file sits in the same working directory as the response log, its contents nothing but the counters the ledger already derives off that log plus a format stamp, and it is rewritten every time a line is appended, starting with the seed line rather than only at the end of the run.

*The leap nobody states:* If a file is meant to tell you where a conversation stands without replaying the log, it is only useful when it is written as often as the log is.

- **nils** (2025-03-17, #pipeline): resumed yesterday's conversation this morning and had to walk the whole jsonl just to work out whose turn it was. the working dir should carry that position, not make you replay the log.
- **gideon** (2025-06-04, page:meetings/weekly-sync-notes-week-of-jun-2-release-ci.md): so basically the working dir gets TURN_LEDGER_FILENAME, turn_ledger.json, holding what we derive off the log — turns is the jsonl line count, seed line included, so responses plus one.
- **konrad** (2025-04-22, thread:new|g7.r1.l3): A run I killed at response seven left the json still claiming one response, it only gets written when run() returns. so yes the file lies about the run.
- **dermot** (2025-04-09, #incidents): on the no-local-record side, ledger.sidecar_state is exactly eight keys — version, responses, turns, last_author, next_speaker, interleave_faults, completed, completion_reason. it goes back out through write_sidecar after every append, seed line included.
- **konrad** (2025-06-04, #code-review): Ran a clean four-turn conversation through to the end on 685: file lands at 189 bytes - responses 3, turns 4, last_author advisor, next_speaker null, completed true, completion_reason agent_signal
- **konrad** (2025-06-02, #viewer): Look, it does write mid-run - completion_reason sits at "open" on every write while the run is still going, it only stops saying open once the run actualy ends.
- **dermot** (2025-03-19, #engineering): yeah ok — next_speaker is nothing more than the partner of last_author, a log ending on client comes back with next_speaker advisor, so nobody has to replay the jsonl

### g7.r1.s2 — Loading a ledger is a read: it writes nothing back, and it never shortens, reorders or edits the log, whose lines are the expensive, authoritative part. The comparison against the file is only the recorded response count and last author, and the ledger comes back carrying which outcome that comparison had, including the untested state of a fresh run's first write.

*The leap nobody states:* The side that costs money to produce is the side you trust, and a derived summary can always be rebuilt from it.

- **nikolai** (2025-04-24, page:design/batch-job-status-persistence-across-process-restarts.md): same goes for the responses file i opened a finished run to look at counters and load rewrote it under me it gets read back and verified not replaced
- **gideon** (2025-04-25, #code-review): No, we leave the jsonl alone when the two disagree, honestly those lines cost real money and the counters rebuild for free.
- **emil** (2025-05-13, thread:new|g7.r1.l7): yup — the load threw for me too: checkpoint carried interleave_faults from an older build, though response count and last author matched the log exactly. comparing every key is too strict.
- **dario** (2025-06-24, page:engineering/resume-behavior-for-auto-batch-mode-matching-responses-files-to-job-records.md): on "a restart needs both" — a responses file is pinned to its job record by response count and who wrote last; a first write compares against nothing, so the ledger says created, not verified.
- **gideon** (2025-04-28, #engineering): ya so basically version 2 checkpoint, responses and last_author both matching the log, ledger comes back status verified and the file stays exactly as it was
- **dario** (2025-04-25, #viewer): on the disk side - the record gets seeded at submit with completed false and stays false through every append, it only flips true once the run actually finishes
- **emil** (2025-04-25, #cookbooks): yup — interleave_faults is just counting the spots where the log doubles back on the same author, so a clean client/advisor alternation always rebuilds to 0.

### g7.r1.s3 — A checkpoint that is absent, unparseable, or stamped with a superseded version carries no information and the run simply takes the log's word for everything; only a current-version file whose two recorded values disagree with the log is fatal, and it fails with a dedicated error naming the file and both sides' figures.

*The leap nobody states:* You can only call a file wrong if you know it was written by the code you are running now; otherwise it is just old.

- **konrad** (2025-04-09, thread:new|g7.r1.l9): Look, deleted the json by hand to test resume and the rerun refused to start, jsonl sitting there intact. Missing file is benign - we adopt the log, then exactly one call_single_request(advisor, 2).
- **emil** (2025-05-13, #pipeline): honestly half the checkpoints on my box predate TURN_LEDGER_VERSION 2 and don't even carry the same keys - those are stale, not wrong. when a version-2 one does disagree, the error's .path attribute holds that turn_ledger.json path.
- **nils** (2025-04-07, page:engineering/ws-050-batch-mode-50-cost-async-batch-apis.md): one of those killed runs left half a json line and resume died in json.loads. we dont discard an intact log over that - adopt it, append the one line, three becomes four.
- **nikolai** (2025-06-11, thread:new|g7.r1.l12): TurnLedgerDesyncError on resume, message verbatim: /work/agent/turn_ledger.json records 1 response(s) last authored by 'client', the log holds 2 last authored by 'client'. .log_responses and .log_last_author sit on it too.

### g7.r1.s4 — The file is on disk from the moment the seed line lands, written in one fixed spelling that is stable across runs and loadable back through a reader of its own, and on a disagreement the run stops before it issues a request or appends anything, leaving the log exactly as it found it.

*The leap nobody states:* A checkpoint you can only inspect by hand, or that only appears once a run succeeds, is not something a test or a person can lean on.

- **gideon** (2025-03-19, #pipeline): ya so basically I killed the run on its very first call and turn_ledger.json is already there at 186 bytes exactly - responses 0, turns 1, last_author client.
- **dario** (2025-04-09, page:engineering/payload-plan-file-what-the-tests-hold-on-to.md): sort_keys and indent 2 with a trailing newline please, exactly how turn_ledger.json goes out - the key order moved between two runs and every test diff after that was noise.
- **nils** (2025-03-24, #pipeline): i wrote read_sidecar for the tests rather than leave it - hand it the working dir, get the record back as a dict. write_sidecar already returns the absolute path it wrote, so tests read straight off that.
- **dermot** (2025-04-09, thread:new|g7.r1.l16): ran the stale-checkpoint repro late last night - four calls burned before TurnLedgerDesyncError surfaced, though recorded_responses 3 and recorded_last_author 'advisor' do come off the exception. it should be refusing before the first call.

### herrings — believed at the time, reversed later

- **dario** (2025-02-26): settled on resume semantics: turn_ledger.json is the source of truth, so if the log runs past the recorded response count we truncate it back before the first reqeust.
- **emil** (2025-01-21): yup - checkpoint wins on the mismatch, log gets trimmed back to the recorded count and the run carries on. standard resumable-writer behaviour, nothing exotic.

## g7.r2

### g7.r2.g7r2-s1 — The base agent's default stop-check must actually decide from the fixed end marker the prompts already ask for, whose text is <<END_OF_CONVERSATION>>, instead of always answering no.

*The leap nobody states:* if the prompts demand a specific closing token and the default check never fires, the default check is meant to read that token

- **dario** (2025-03-20, #cookbooks): ran the negotiation demo four times today and it burns through the whole budget everytime, even when the partner writes that it has nothing left to add.
- **gideon** (2025-04-16, #engineering): so basically the agent prompts page has told both agents to end their final message with <<END_OF_CONVERSATION>> since the first demo, and no code has ever looked for it.
- **nikolai** (2025-03-14, #engineering): i'd say for the base agent nobody subclassed the done check should just look for the marker we already put in the prompts instead of answerign no forever

### g7.r2.g7r2-s2 — A reply counts as a stop only when the marker, spelled exactly as written down to capitalisation, is the last thing in the message, with any trailing whitespace ignored.

*The leap nobody states:* people report near-misses in three directions (mid-sentence, wrong case, trailing newline) and the only match rule that satisfies all three at once is an exact end-of-text match after trimming

- **emil** (2025-06-04, page:meetings/weekly-sync-notes-week-of-jun-2-release-ci.md): partner spent a turn explaining the protocol, pasted the marker mid-sentence, and the run cut off right there; that message was not an ending.
- **dermot** (2025-04-10, thread:new|g7.r2.g7r2-l05): for me it only counts as a stop when the marker is the tail end of what the model said. if it turns up mid-paragraph it is obviously still going.
- **konrad** (2025-03-21, #cookbooks): look, I typed it lowercase in the notebook cell and the loop still quit on me. if its a marker then it has to be the marker, capitals included.
- **nils** (2025-05-13, page:engineering/stop-marker-matching-what-ends-a-generation-and-what-does-not.md): let me think — two of the providers tack a newline on after the marker, trailing whitespace either side of it doesnt change the match. that should not be what decides whether we stop.

### g7.r2.g7r2-s3 — A reply that is not text is simply not a stop: the check answers no and the run continues rather than raising.

*The leap nobody states:* if a non-text reply must not crash the run and must not end it either, the check has to quietly answer no

- **dermot** (2025-04-09, thread:new|g7.r2.g7r2-l08): late night run — put the json-mode agent through my branch and the stop check threw AttributeError on a dict, killed the run at turn two.
- **nikolai** (2025-04-15, #code-review): on 639 though thats not an edge case, with response_format set the reply we pass around is a parsed object rather than text and three of the cookbooks are built that way
- **konrad** (2025-12-29, page:meetings/weekly-sync-notes-week-of-jun-2-release-ci.md): look, one thing we did agree on regardless of placement: whatever the check ends up doing, a run should not fall over becuase an agent answered with something that is not text.

### g7.r2.g7r2-s4 — The message carrying the marker is an ordinary turn: it is written to the log, counted among the responses and present in the dataset, the run ends after it, and the ledger records the end as the agent's own signal rather than budget.

*The leap nobody states:* stopping on a marker is a normal end of conversation, so the turn that triggered it is recorded like every other turn rather than discarded

- **dario** (2025-06-11, thread:new|g7.r2.g7r2-l11): honestly i think the prototype transcript stops one message short — whatever the partner said to close things off never made it into the arrow file at all.
- **emil** (2025-06-13, #engineering): the fake's third reply is "Then index funds. <<END_OF_CONVERSATION>>" and i want that entire string sitting as the content of the last dataset row, role PARTNER.
- **gideon** (2025-06-12, page:engineering/writing-turn-loop-tests-for-the-executor-against-the-deterministic-fake.md): so basically budget was 6 and the fake answered three times, so four lines in responses_0.jsonl, the tracker reporting three responses, and the ledger's own responses field at 3 too.
- **nils** (2025-07-02, page:engineering/reading-completion-reason-in-the-agent-turn-ledger.md): let me think through that — a run that ended on the marker did not run out of anything, so completion_reason on the ledger reads "agent_signal", never budget.
- **dermot** (2025-06-13, #releases): yeah ok, re-ran dario's transcript on my branch and the dataset comes out at four rows now, same count as the jsonl log, closing message and all
- **konrad** (2025-12-29, #cookbooks): Right, and completed reads True on the ledger for these runs. The agent said it was done, thats a finish, not a run we cut short.

### herrings — believed at the time, reversed later

- **dario** (2025-01-22): ok, settled on the sentinel check — we lowercase the whole reply and look for the token anywhere in it, position doesn't matter since agents drop it wherever they like
- **konrad** (2025-03-11): Confirming for the docs then: is_completed is a case insensitive substring scan over the whole response, nobody has to get the casing or the placment right.

