# The tree

## g2.r1

### g2.r1.sc-kept — When a stream goes over the budget the part that comes back is the front of it plus its end, with most of the allowance spent on the front, roughly three parts front to one part end.

*The leap nobody states:* If the useful material sits at both ends of a long log, a single slice from one end cannot be the right thing to keep, and the split has to favour the end people read first.

- **gideon** (2025-04-24, #engineering): honestly though, whatever we cut, keep the last few lines - every failing run I look at has the actual excpetion sitting right at the very bottom.
- **konrad** (2025-03-20, #code-review): look, most of what I need is at the top of the log anyway - so if we do keep both ends, head gets three parts of the cap and tail one.
- **nils** (2025-03-19, #engineering): A plain first-64k cut left me with the pip install banner and none of the traceback, which is the only part i opened the log for.

### g2.r1.sc-seam — The two kept pieces are joined by one fixed marker line that carries the decimal number of bytes actually thrown away, and the marker's own length is charged on top of the budget rather than taken out of it.

*The leap nobody states:* A number in the seam is only useful if it equals the difference between what came in and what came back, which it can only do if the seam itself is not competing with the payload for the allowance.

- **nikolai** (2025-04-23, #help): right so in the notebook cell its `[[curator:elided 812043 bytes]]` alone on its own line, top of the log above it bottom below
- **dermot** (2025-04-09, thread:new|g2.r1.l-seam-dermot): the seam claims 812014 bytes went, but the cell is 812043 shorter than the raw log; it should be original length minus what we kept, i want the bytes actually dropped.
- **dario** (2025-06-11, thread:new|g2.r1.l-seam-dario): i asked for 64 and got 35 bytes of program output back — the marker came out of my allowance. in any case the cap should mean the kept bytes.

### g2.r1.sc-bytes — The allowance is measured in encoded bytes, and each cut is walked back up to three bytes to a character boundary before decoding, with replacement characters used only when the bytes were genuinely not decodable, so a clean run can come back slightly under the allowance and never shows a replacement character.

*The leap nobody states:* A byte budget lands mid character on multi-byte text, so the only way to avoid mangling clean input is to give back a few bytes at the edges rather than force the decode.

- **gideon** (2025-04-15, #engineering): The cap is a byte count, not a character count, so my Japanese fixture came back about a third of the lenght I guessed. took me a while to spot that honestly.
- **emil** (2025-12-30, #engineering): capped a CJK log and the join came back with a replacement diamond, the tail starts mid character so it's not valid UTF-8. clean input shouldnt come out mangled.
- **nils** (2025-03-21, #engineering): for a ragged edge just walk the cut in one at a time, three at most, and only fall back to replace if it still won't decode.
- **dario** (2025-03-14, #code-review): if backing off to a boundary leaves us a byte or two under the cap, honestly just leave it there, we shouldn't be padding back out to land exactly on the number

### g2.r1.sc-off — Zero means no cap at all, so the stream is handed back whole and unmarked and is not reported as shortened, and a stream already inside the budget is returned exactly as it arrived with no marker either.

*The leap nobody states:* Zero is the value people reach for when they want the old unlimited behaviour back, so it cannot be treated as a tiny budget, and untouched output should not be advertised as touched.

- **konrad** (2025-03-17, #code-review): Set max_output_bytes to 0 on the branch expecting the raw firehose, got empty stdout instead. Look, 0 means all of it back unmarked, and truncated_streams stays empty.
- **nikolai** (2025-05-13, #code-review): i'd say 0 shouldnt be going anywhere near the floor check, its not somebody asking for a tiny cap
- **dermot** (2025-04-24, #code-review): ran the boundary cases: with the default cap a 900 byte stdout comes back marked and in truncated_streams, under it untouched and unlisted, exactly on the cap whole.
- **emil** (2025-03-18, #releases): on the wording, equal isnt exceeded - a stdout that lands exactly on max_output_bytes doesnt show up in truncated_streams, thats settled

### g2.r1.sc-floor — Any budget that is neither zero nor at least sixteen is refused up front by a named error carrying the offending value, and the refusal happens when the config is built rather than once per row inside the sandbox.

*The leap nobody states:* A budget too small to hold both a front and an end piece cannot be honoured at all, and an argument error that only shows up per request is discovered after the retries have already been spent.

- **emil** (2025-03-14, #code-review): Same shape from my end - max_output_bytes=8 blew up inside the sandbox once per row and burned every retry, the config should have refused it when i built the executor
- **dario** (2025-03-14, #pipeline): i think that floor wants to be a named thing in output_cap.py, MIN_MAX_OUTPUT_BYTES, rather than a bare 16 sitting in two places - under 16 there's honestly no room for a head and a tail.
- **nikolai** (2025-03-14, #cookbooks): i'd say call it OutputCapError, ValueError as the base since the cookbook setup cells catch that - and the config validator should raise that same error, not its own ValueError
- **konrad** (2025-03-17, #cookbooks): look, don't make me regex the traceback for `max_bytes must be 0 or at least 16, got 8` - hang the offending value on the exception as .max_bytes
- **dario** (2025-03-14, #incidents): honestly there's nothing for us to reword there - the field_validator hands the offending value straight into that error, and pydantic's ValidationError comes back out carrying its message verbatim

### g2.r1.sc-log — A single warning line is emitted per run, only when something was actually shortened, naming the streams that were shortened together in that one line and the effective budget, and it is emitted at the moment the streams are cut rather than on the way out of the run.

*The leap nobody states:* One line per row is what makes the log greppable, and logging at the cut is the only placement that still records a run which falls over after the output was captured.

- **gideon** (2025-04-29, #pipeline): honestly though, can we get a warning line when it fires, but only on runs that actaully lost bytes - I spent an hour blaming the model for the short output.
- **emil** (2025-05-01, #pipeline): ok ran it, one line — `sandbox output capped: stderr, stdout exceeded the 65536-byte budget`, not `sandbox output capped: stdout, stderr exceeded the 65536-byte budget`, since we sort streams and stdout was the fat one.
- **nikolai** (2025-06-17, page:engineering/capping-executor-stdout-and-stderr-in-code-execution.md): whats in output_cap.py so far the cap helper the floor the error and TRUNCATION_LOG_TEMPLATE which is formatted with {streams} and {budget}
- **konrad** (2025-05-01, #cookbooks): The row whose sandbox threw on cleanup had its stdout capped, no warnign anywhere. anyway the except handler's salvage cap logs nothing, we log where we cut.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): in any case, the marker counts against the budget: head is sliced to max_bytes - len(marker), so the string we hand back never exceeds max_output_bytes.
- **gideon** (2025-01-22): so basically the dropped count in the marker is original length minus max_output_bytes, that's the number, don't recompute it from the kept slices.

## g2.r2

### g2.r2.s-rule — On the exception path the error string is put through the same byte budget and the same head/tail-with-marker shortening as a stream, and the output object carries a plain boolean flag, defaulted false and declared right after truncated_streams, that is set only when bytes were actually removed from that string.

*The leap nobody states:* A value that can be arbitrarily long and is handed straight to a caller belongs under the same budget as the other unbounded values, and a caller who cannot tell a whole message from a shortened one needs it recorded next to the shortening it already records.

- **dario** (2025-04-18, #incidents): honestly the part that worries me there: sandbox teardown threw last night and the entrie 300kb repr came back to us in `error` — we shorten both streams then hand that message over whole
- **dermot** (2025-04-21, thread:new|g2.r2.l-rule-2): yeah — shorten it like a stream, same helper: three quarters of the budget as head, last quarter as tail, `\n[[curator:elided <dropped> bytes]]\n` between.
- **konrad** (2025-04-21, #cookbooks): look, just a plain bool defaulting to False, no Optional — and put it drectly under truncated_streams so the two read as a pair
- **emil** (2025-05-14, page:engineering/capping-executor-error-text-in-responses-files-and-logs.md): wiki nit: it's `error_truncated`, single underscore, not errorTruncated — and it only comes back `True` where we actually took bytes off the message, not any time a run raises.

### g2.r2.s-scope — Nothing else is put through the budget: the assembled non-zero-exit sentence keeps its full length even though the stderr inside it was shortened, the timeout sentence is left alone, files are left alone, and the flag reads false on both of those paths.

*The leap nobody states:* A string the team composed itself is not the same kind of value as a string that came back from someone else's program, so the flag is about the clipping we did, not about anything embedded in what we wrote.

- **nikolai** (2025-03-20, #cookbooks): on a non-zero exit the `error` field is our own sentence with stderr pasted in so that assembled `message` stays full length capping it again just eats the stderr
- **nils** (2025-03-14, #general): let me think - `Execution timed out after 300s` is a sentence we wrote ourselves, nothing in it is worth shortening, whatever the budget ends up set to.
- **emil** (2025-04-18, thread:new|g2.r2.l-scope-3): someone will ask what `error_truncated` reads when the stderr inside that non-zero exit message got clipped — i'd leave it `False` there, we assembled that string rather than cut it.
- **gideon** (2025-03-17, #viewer): so basically please keep files out of the budget, my viewer diffs them and a clipped artefact is just a broken artefact — files stay uncapped.

### g2.r2.s-cross — The flag belongs to the output object alone and never to the result rows, and the list of shortened stream names stays limited to the two stream names, with the whole set of output keys expected to survive a dump and reload.

*The leap nobody states:* A field only goes where the thing it describes exists, and a list consumers index by stream name stops being usable the moment a non-stream name is allowed into it.

- **gideon** (2025-04-22, page:engineering/capping-code-executor-output.md): so basically the schema test walks `CodeExecutionResult.model_fields` per row, and rows carry stdout, stderr and files, never an exception, so `error_truncated` is not going in there.
- **konrad** (2025-03-14, #releases): look, my notebook does "stdout" in truncated_streams to pick what to fold, anything in there thats not a stream name folds a pane that doesnt exist. two stream names only.
- **nils** (2025-03-17, #general): let me think - the round trip is what bit us last time: set it `True`, dump, then confirm every key is still on `exec_output` after the reload.

### g2.r2.s-obs — The behaviour is pinned by fakes: a long exception raised out of teardown comes back shortened with the flag set, a short one comes back byte for byte with it unset, and a non-zero exit shows a shortened stderr while its own sentence stays whole and unflagged.

*The leap nobody states:* The three cases people keep arguing about are exactly the three fixtures worth writing down, and the numbers on them are what settle the argument.

- **gideon** (2025-03-18, #viewer): so basically the fixture I have: fake sandbox exits 0 with 300 bytes of stdout, and `__exit__` raises `RuntimeError("X"*300)`, budget set to 64.
- **nikolai** (2025-06-24, thread:new|g2.r2.l-obs-2): second fixture is exit_code 1 with `"E"*80` on stderr at the same 64 budget the stderr lands in the shortened list but the sentance wrapped round it stays whole
- **dermot** (2025-03-17, #releases): third case is a `RuntimeError("boom")`, well under the budget - comes back byte for byte as raised and the flag stays `False`.
- **emil** (2025-03-19, #releases): let me think through that - the marker rides on top of the budget rather than inside it, so gideon's 64 case comes back at 94 bytes of `error`.

### herrings — believed at the time, reversed later

- **dario** (2025-01-21): settled then: error truncation rides in truncated_streams as a third entry, "error", right next to stdout and stderr. no separate field for it.
- **gideon** (2025-01-21): so basically truncated_streams is on CodeExecutionResult too, not just CodeExecutionOutput. same field name on both, so it's one place to check either way.

