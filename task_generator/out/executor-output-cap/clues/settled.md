# Was every graded thing said, or only implied? — g2

**59 of 72** assertions rest on something a remark says outright.

- `stated` **59** — a reader was told
- `implied` **8** — a reader has to work it out, and may not
- `absent` **1** — nothing in the corpus bears on it
- `not_required` **4** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

> **These verdicts are what provoked the rewrites, not what the plant says now.** 7 remark(s) rewritten, 3 added, 0 not fixed. Re-run `settle --dry-run` for the verdicts on the corpus as it now stands.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g2.r1.exclusions_or_crossover#1` | stated | `g2.r1.l-off-konrad`, `g2.r1.l-off-nikolai` | konrad reports setting max_output_bytes=0 and getting empty stdout as the bug and rules "0 is the one time I want all of it", so returning the stream whole at budget 0 is a decision made out loud. |
| `g2.r1.exclusions_or_crossover#2` | stated | `g2.r1.l-off-konrad`, `g2.r1.l-log-emil` | konrad's ruling attaches to the max_output_bytes=0 setting rather than to one stream, and emil's log line shows the cap governs stdout and stderr together, so "all of it" is stated for stderr as well. |
| `g2.r1.exclusions_or_crossover#3` | **implied** | `g2.r1.l-off-dermot`, `g2.r1.l-off-konrad` | nobody says what truncated_streams contains at budget 0; the reader must carry dermot's "untouched and unlisted" rule over to konrad's sentinel case, a join neither remark makes. |
| `g2.r1.exclusions_or_crossover#4` | stated | `g2.r1.l-off-dermot` | dermot names the symptom (a 900-byte stdout under the cap came back with a marker glued on) and states the rule that under the cap should be untouched. |
| `g2.r1.exclusions_or_crossover#5` | stated | `g2.r1.l-off-dermot` | dermot's closing sentence is a general rule about any stream under the cap, and an empty stderr is under the cap, so preserving it verbatim needs no extra step. |
| `g2.r1.exclusions_or_crossover#6` | stated | `g2.r1.l-off-dermot` | dermot names the field truncated_streams by its identifier, reports stdout wrongly appearing in it, and says under-cap streams should be unlisted. |
| `g2.r1.exclusions_or_crossover#7` | **implied** | `g2.r1.l-off-dermot`, `g2.r1.l-log-emil`, `g2.r1.herring-marker-inside-budget-dario` | dermot rules only on streams "under the cap" and emil's log wording says "exceeded", leaving the reader to decide unaided that len == budget is not a truncation — while the herring pushes toward slici |
| `g2.r1.exclusions_or_crossover#8` | **implied** | `g2.r1.l-off-dermot`, `g2.r1.l-log-emil`, `g2.r1.l-bytes-dario` | the equality boundary is never ruled on, so keeping an exactly-at-budget stream out of truncated_streams rests on the reader inferring that "exceeded" excludes equality. |
| `g2.r1.failure_behavior#1` | stated | `g2.r1.l-floor-dario` | Dario names MIN_MAX_OUTPUT_BYTES, puts it in output_cap.py, and attaches the value 16 to it ("a bare 16", "under 16"). |
| `g2.r1.failure_behavior#10` | stated | `g2.r1.l-floor-emil`, `g2.r1.l-floor-dario` | That a below-floor budget is refused at config construction is exactly what emil asked for, with dario fixing the floor at 16. |
| `g2.r1.failure_behavior#11` | stated | `g2.r1.l-off-nikolai`, `g2.r1.l-off-konrad`, `g2.r1.l-floor-konrad` | Nikolai says 0 should not go near the floor check, konrad wants 0 to mean everything, and the message reads "must be 0 or at least 16". |
| `g2.r1.failure_behavior#12` | stated | `g2.r1.l-floor-dario`, `g2.r1.l-floor-konrad` | The floor is inclusive by both dario's "under 16" and konrad's "at least 16", so 16 must construct. |
| `g2.r1.failure_behavior#13` | n/a | — | Read as the -1 case, this guards the pre-existing ge=0 constraint on the config field rather than anything the corpus was asked to decide. |
| `g2.r1.failure_behavior#2` | stated | `g2.r1.l-floor-nikolai` | Nikolai names the error OutputCapError and says to keep ValueError as the base. |
| `g2.r1.failure_behavior#3` | stated | `g2.r1.l-floor-konrad`, `g2.r1.l-floor-emil` | Konrad asks for the offending value hung on the exception as .max_bytes, and 8 is the offending value in both his quoted message and emil's report. |
| `g2.r1.failure_behavior#4` | stated | `g2.r1.l-floor-konrad` | Konrad quotes the message verbatim, including the interpolated 8, so the error's str is fixed by the value. |
| `g2.r1.failure_behavior#5` | stated | `g2.r1.l-floor-emil`, `g2.r1.l-floor-nikolai`, `g2.r1.l-log-nikolai` | Emil reports that max_output_bytes=8 blew up inside the sandbox, and the only error in the corpus — the floor error living beside the cap helper — is OutputCapError. |
| `g2.r1.failure_behavior#6` | stated | `g2.r1.l-floor-konrad` | Konrad's whole point is that the caught exception carries the offending value as .max_bytes so nobody has to regex the traceback. |
| `g2.r1.failure_behavior#7` | stated | `g2.r1.l-floor-dario`, `g2.r1.l-floor-konrad` | Dario says it is under 16 that has no room and konrad's message says "at least 16", so 16 itself is explicitly the accepted floor. |
| `g2.r1.failure_behavior#8` | stated | `g2.r1.l-floor-emil`, `g2.r1.l-floor-nikolai` | Emil says the config should have refused the value when he built the executor, and nikolai places the error at executor-construction time. |
| `g2.r1.failure_behavior#9` | **implied** | `g2.r1.l-floor-konrad`, `g2.r1.l-floor-emil` | Nobody says the config-level refusal reuses the sandbox's error or its wording, so the reader must decide on their own to raise OutputCapError(value) from the validator rather than any plain ValueErro |
| `g2.r1.observability#1` | **implied** | `g2.r1.l-log-emil`, `g2.r1.l-log-nikolai` | Emil quotes the rendered line verbatim and Nikolai names TRUNCATION_LOG_TEMPLATE as the constant holding that wording, but nobody ever says the substitution fields are named {streams} and {budget}, so |
| `g2.r1.observability#2` | stated | `g2.r1.l-log-gideon`, `g2.r1.l-log-emil`, `g2.r1.l-off-dermot` | Gideon asks for a warning line that fires only on runs that actually lost bytes, Emil confirms it comes out as one line naming the capped streams, and Dermot says an untouched stream must not be liste |
| `g2.r1.observability#3` | **absent** | `g2.r1.l-log-emil` | The only remark showing two streams in one line spells them "stdout, stderr", the reverse of the alphabetical "stderr, stdout" required here, and nothing anywhere says the names are sorted. |
| `g2.r1.observability#4` | stated | `g2.r1.l-log-konrad`, `g2.r1.l-log-emil`, `g2.r1.l-log-gideon` | Konrad says outright that the logging happens at the point we cut and not at the return paths, which is the decision that makes the timeout return carry the same single warning as the success return. |
| `g2.r1.observability#5` | stated | `g2.r1.l-log-konrad`, `g2.r1.l-log-emil`, `g2.r1.l-off-dermot` | Same call-site decision from Konrad covers the non-zero-exit return, and Emil's line plus Dermot's "unlisted if untouched" fix the single-stream wording for a stderr-only cut. |
| `g2.r1.observability#6` | stated | `g2.r1.l-log-gideon` | Gideon explicitly asks for the warning only on runs that actually lost bytes, so a run where nothing was cut says nothing. |
| `g2.r1.observability#7` | stated | `g2.r1.l-off-konrad`, `g2.r1.l-off-nikolai`, `g2.r1.l-log-gideon` | Konrad and Nikolai both state that 0 means no cap at all rather than a tiny one, and Gideon's rule fires the warning only when bytes were lost, so the 0 case logging nothing is the direct conjunction  |
| `g2.r1.observability#8` | **implied** | `g2.r1.l-log-konrad`, `g2.r1.l-log-emil` | Konrad complains that the cleanup-throwing row got no warning despite a capped stdout, but nobody says the salvage cap in the except handler stays silent, so the reader who follows "log at the point w |
| `g2.r1.observability#9` | stated | `g2.r1.l-log-gideon`, `g2.r1.l-log-konrad` | Gideon's rule that the line appears only on runs that actually lost bytes settles the run that captured nothing, even though that particular failure mode is never named. |
| `g2.r1.rule#1` | stated | `g2.r1.l-kept-konrad`, `g2.r1.l-seam-nikolai`, `g2.r1.l-kept-gideon`, `g2.r1.rev1`, `g2.r1.l-bytes-gideon` | Every piece of the splice is said out loud by somebody: konrad fixes the ratio ("give the top three parts to the bottom's one"), dario's rev1 says the budget is the kept bytes (so 64 splits 48/16), ni |
| `g2.r1.rule#2` | n/a | `g2.r1.l-seam-nikolai` | `marker` is the suite's own locally-built string, so this length check is self-consistency in the fixture and cannot fail on any implementation; the marker's literal wording is separately supplied by  |
| `g2.r1.rule#3` | stated | `g2.r1.rev1`, `g2.r1.l-seam-dario`, `g2.r1.herring-marker-inside-budget-dario` | rev1 says exactly this with the same number — "i asked for 64 and got 35 bytes back... budget is the kept bytes now, marker sits outside it so the return runs that much longer" — overturning the earli |
| `g2.r1.rule#4` | stated | `g2.r1.l-kept-konrad`, `g2.r1.rev1`, `g2.r1.l-seam-nikolai` | The marker's offset is just the head length, and konrad states the 3:1 top-to-bottom division of what is kept while rev1 states that what is kept is the full 64-byte budget. |
| `g2.r1.rule#5` | stated | `g2.r1.l-kept-konrad`, `g2.r1.l-seam-nikolai`, `g2.r1.rev2`, `g2.r1.l-seam-dermot` | The 24/8 split follows from konrad's stated 3:1 ratio over a kept budget, the marker text and its own-line framing come from nikolai, and dermot/rev2 state the dropped count is original minus kept. |
| `g2.r1.rule#6` | stated | `g2.r1.rev1`, `g2.r1.l-seam-dario` | Same decision as #3, made out loud twice: the cap means the kept bytes and the marker is charged outside it, so the return is exactly the marker longer than the cap. |
| `g2.r1.scope#1` | stated | `g2.r1.l-bytes-gideon`, `g2.r1.l-off-dermot`, `g2.r1.l-seam-dario` | gideon says outright that the cap is a byte count and not a character count (his Japanese fixture came back a third of the expected length), and dermot's complaint fixes that only under-cap streams co |
| `g2.r1.scope#2` | stated | `g2.r1.l-bytes-emil`, `g2.r1.l-bytes-nils` | emil reports the replacement diamond from a tail starting mid-character and states the rule ("clean input shouldnt come out mangled"), and nils prescribes the mechanism — walk the cut in one byte at a |
| `g2.r1.scope#3` | stated | `g2.r1.l-bytes-nils`, `g2.r1.l-bytes-dario`, `g2.r1.rev1`, `g2.r1.l-seam-dario`, `g2.r1.l-bytes-gideon` | every ingredient of the 18-of-20 result is said out loud — budget is bytes (gideon), budget means the kept bytes with the marker outside it (rev1 and l-seam-dario, overturning the earlier herring), wa |
| `g2.r1.scope#4` | stated | `g2.r1.l-off-dermot` | dermot names the field `truncated_streams` and the membership rule in one breath — his 900-byte stdout was wrongly listed, and a stream under the cap "should be untouched and unlisted" — so a stream t |
| `g2.r1.scope#5` | stated | `g2.r1.rev2`, `g2.r1.l-seam-dermot`, `g2.r1.l-seam-nikolai` | dermot asks for "original length minus what we kept" and gideon's rev2 states the formula as original minus kept bytes rather than original minus max_output_bytes precisely because boundary trimming k |
| `g2.r2.exclusions_or_crossover#1` | stated | `g2.r2.rev2`, `g2.r2.l-cross-1`, `g2.r2.h2` | rev2 spells the assertion out almost literally — '"error_truncated" not in CodeExecutionResult.model_fields' — with l-cross-1 giving the reason (rows carry stdout/stderr/files, never an exception), an |
| `g2.r2.exclusions_or_crossover#2` | stated | `g2.r2.rev1`, `g2.r2.l-cross-3`, `g2.r2.l-rule-3`, `g2.r2.l-scope-1`, `g2.r2.l-scope-4` | rev1 puts 'error_truncated: bool = False on CodeExecutionOutput, declared under truncated_streams' and l-cross-3 names exec_output as the dict whose every key must survive a dump/reload, so the only n |
| `g2.r2.exclusions_or_crossover#3` | stated | `g2.r2.l-rule-4`, `g2.r2.l-obs-1`, `g2.r2.l-obs-3`, `g2.r2.l-rule-1` | l-rule-4 states the True condition outright ('only comes back True where we actually took bytes off the message'), l-obs-3 fixes the False side, and l-obs-1 hands over this exact fixture — a 300-byte  |
| `g2.r2.exclusions_or_crossover#4` | stated | `g2.r2.rev1`, `g2.r2.l-cross-2`, `g2.r2.l-obs-1`, `g2.r2.h1` | rev1 retracts h1's 'error' third entry by name and says truncated_streams 'stays "stdout"/"stderr"', konrad's l-cross-2 independently insists on two stream names only, and l-obs-1's 300-byte stdout at |
| `g2.r2.exclusions_or_crossover#5` | stated | `g2.r2.l-obs-2`, `g2.r2.l-scope-1`, `g2.r2.l-scope-3` | l-obs-2 describes this fixture and its outcome directly — exit_code 1, 'E'*80 on stderr, budget 64, 'the stderr lands in the shortened list' — and l-scope-1/l-scope-3 confirm the wrapping sentence is  |
| `g2.r2.observability#1` | **implied** | `g2.r2.l-rule-2`, `g2.r2.l-rule-1`, `g2.r2.l-obs-1`, `g2.r2.l-obs-3`, `g2.r2.l-rule-4` | l-rule-2 hedges ('if we do shorten that string') and gestures at 'head and tail with the marker between' without any of the marker text, the 48/16 split, or the 236 count, so the reader must both reso |
| `g2.r2.observability#2` | **implied** | `g2.r2.l-rule-2`, `g2.r2.l-obs-1` | 94 is purely a consequence of the unstated cap format from #1 — no remark gives a resulting length, or says the marker sits outside the 64-byte budget rather than inside it. |
| `g2.r2.observability#3` | stated | `g2.r2.l-rule-4`, `g2.r2.l-obs-3`, `g2.r2.rev1`, `g2.r2.l-rule-3` | l-rule-4 says the flag 'only comes back True where we actually took bytes off the message', and this fixture is the case where bytes came off; rev1 and l-rule-3 name it error_truncated: bool on CodeEx |
| `g2.r2.observability#4` | stated | `g2.r2.l-obs-3` | dermot names the RuntimeError('boom') case and says it 'comes back byte for byte as raised'. |
| `g2.r2.observability#5` | stated | `g2.r2.l-obs-3`, `g2.r2.l-rule-3`, `g2.r2.l-rule-4` | l-obs-3 says the flag stays False for the under-budget message, and l-rule-3 pins the default to False with no Optional. |
| `g2.r2.observability#6` | stated | `g2.r2.l-scope-1`, `g2.r2.l-obs-2`, `g2.r2.l-rule-1` | l-scope-1 says the assembled sentence stays full length because 'capping it again just eats the stderr' and l-obs-2 confirms the wrapper stays whole while the stderr is the shortened one, ruling out b |
| `g2.r2.observability#7` | stated | `g2.r2.l-scope-1`, `g2.r2.l-obs-2`, `g2.r2.l-rule-1` | the stderr cap is pre-existing ('we shorten both streams'), and l-scope-1 says error is 'our own sentence with stderr pasted in', so the reader passes through an existing format rather than inventing  |
| `g2.r2.observability#8` | stated | `g2.r2.l-scope-3`, `g2.r2.l-rule-4` | emil answers this exact question — error_truncated reads False on the non-zero-exit message because 'we assembled that string rather than cut it' — and l-rule-4 gives the same rule generally. |
| `g2.r2.observability#9` | stated | `g2.r2.l-obs-2`, `g2.r2.rev1`, `g2.r2.l-cross-2` | l-obs-2 says the stderr lands in the shortened list for this fixture, and rev1/l-cross-2 fix truncated_streams to stream names only after retiring the 'error' entry from h1. |
| `g2.r2.rule#1` | stated | `g2.r2.rev1`, `g2.r2.rev2`, `g2.r2.l-rule-3` | rev1 says outright "it's error_truncated: bool = False on CodeExecutionOutput now", and rev2/l-cross-1 confirm the field lives on CodeExecutionOutput (and not on CodeExecutionResult). |
| `g2.r2.rule#2` | stated | `g2.r2.l-rule-3`, `g2.r2.rev1` | konrad says "defaulting to `False`" and dario writes the declaration as `error_truncated: bool = False`, which is exactly a non-required field. |
| `g2.r2.rule#3` | stated | `g2.r2.l-rule-3`, `g2.r2.rev1` | konrad names the annotation directly — "a plain bool ... no `Optional`" — and rev1 spells the same annotation out. |
| `g2.r2.rule#4` | stated | `g2.r2.l-rule-3`, `g2.r2.rev1` | the default value False is given twice, so a default-constructed output reading False is the decision as made out loud. |
| `g2.r2.rule#5` | stated | `g2.r2.l-rule-3`, `g2.r2.rev1` | konrad says "put it directly under truncated_streams so the two read as a pair" and rev1 repeats "declared under truncated_streams", which is the adjacency the index check enforces. |
| `g2.r2.rule#6` | n/a | `g2.r2.l-obs-1` | that the exception path sets message to the literal "error" is pre-existing behaviour the assertion uses to confirm the fixture took the raising branch; nothing about the cap turns on it. |
| `g2.r2.rule#7` | stated | `g2.r2.l-rule-2`, `g2.r2.l-rule-1`, `g2.r2.l-obs-1`, `g2.r2.l-obs-3` | dermot says if the exception string is shortened, "shorten it like a stream, head and tail with the marker between", and l-rule-1/l-obs-1/l-obs-3 establish that an over-budget exception text is what g |
| `g2.r2.rule#8` | stated | `g2.r2.l-rule-2`, `g2.r2.l-obs-1` | same decision as #7 — "shorten it like a stream" hands the reader the stream capper whole, marker-accounting included, rather than asking them to invent a length rule for error. |
| `g2.r2.rule#9` | stated | `g2.r2.l-rule-4`, `g2.r2.l-obs-3`, `g2.r2.rev1` | emil fixes the semantics — True "only ... where we actually took bytes off the message" — and dermot's under-budget case confirms the complement, so True on a genuinely shortened exception is told, no |
| `g2.r2.scope#1` | stated | `g2.r2.l-scope-1`, `g2.r2.l-rule-1`, `g2.r2.l-obs-2` | nikolai says the `error` field on a non-zero exit is "our own sentence with stderr pasted in" and that capping it "again" would eat the stderr, dario says the streams are shortened first and the messa |
| `g2.r2.scope#2` | stated | `g2.r2.l-scope-1`, `g2.r2.l-obs-2`, `g2.r2.l-rule-1` | "so that assembled `message` stays full length", "the sentance wrapped round it stays whole" and "hand that message over whole" are three separate statements that the assembled string is not re-capped |
| `g2.r2.scope#3` | stated | `g2.r2.l-scope-3`, `g2.r2.l-rule-4`, `g2.r2.rev1` | emil answers this exact question out loud — error_truncated reads False when the stderr inside the non-zero-exit message got clipped, because the string was assembled rather than cut — and l-rule-4/re |
| `g2.r2.scope#4` | stated | `g2.r2.l-scope-4` | gideon says flatly to keep files out of the budget and that files stay uncapped, with no path qualification. |
| `g2.r2.scope#5` | n/a | — | nothing in the corpus concerns the `message` field's value on a timeout; it is the suite pinning pre-existing executor behaviour that this feature does not touch. |
| `g2.r2.scope#6` | stated | `g2.r2.l-scope-2` | nils quotes the sentence in the same form ("Execution timed out after 300s") and says nothing in it is worth shortening whatever the budget ends up being, which is the decision this assertion checks. |
| `g2.r2.scope#7` | stated | `g2.r2.l-rule-4`, `g2.r2.l-rule-3`, `g2.r2.l-scope-2` | the flag is stated to be a plain bool defaulting to False that only comes back True where bytes were actually taken off the message, and the timeout sentence is stated never to be shortened, so the ru |
| `g2.r2.scope#8` | stated | `g2.r2.l-scope-4`, `g2.r2.l-obs-1` | gideon's "files stay uncapped" is categorical and is not scoped to any particular exit path, and l-obs-1 establishes the raising-__exit__ scenario as one of the cases under discussion. |

### `g2.r1.exclusions_or_crossover#3` — implied

```python
assert read_field(unlimited, "truncated_streams") == []
```

nobody says what truncated_streams contains at budget 0; the reader must carry dermot's "untouched and unlisted" rule over to konrad's sentinel case, a join neither remark makes.

### `g2.r1.exclusions_or_crossover#7` — implied

```python
assert exactly.stdout == "A" * 64, "a stream exactly at the budget was shortened"
```

dermot rules only on streams "under the cap" and emil's log wording says "exceeded", leaving the reader to decide unaided that len == budget is not a truncation — while the herring pushes toward slicing at exactly 64.

### `g2.r1.exclusions_or_crossover#8` — implied

```python
assert read_field(exactly, "truncated_streams") == []
```

the equality boundary is never ruled on, so keeping an exactly-at-budget stream out of truncated_streams rests on the reader inferring that "exceeded" excludes equality.

### `g2.r1.failure_behavior#9` — implied

```python
assert f"max_bytes must be 0 or at least 16, got {bad}" in str(rejected.value), f"the rejection of {bad} does not carry the OutputCapError message: {rejected.value}"
```

Nobody says the config-level refusal reuses the sandbox's error or its wording, so the reader must decide on their own to raise OutputCapError(value) from the validator rather than any plain ValueError with their own text.

### `g2.r1.observability#1` — implied

```python
assert TRUNCATION_LOG_TEMPLATE.format(streams="stderr, stdout", budget=64) == "sandbox output capped: stderr, stdout exceeded the 64-byte budget"
```

Emil quotes the rendered line verbatim and Nikolai names TRUNCATION_LOG_TEMPLATE as the constant holding that wording, but nobody ever says the substitution fields are named {streams} and {budget}, so the reader must invent the exact keyword names this assertion formats with.

### `g2.r1.observability#3` — absent

```python
assert warnings_of(exit_code=0, stdout="A" * 300, stderr="B" * 300, max_output_bytes=64) == ["sandbox output capped: stderr, stdout exceeded the 64-byte budget"]
```

The only remark showing two streams in one line spells them "stdout, stderr", the reverse of the alphabetical "stderr, stdout" required here, and nothing anywhere says the names are sorted.

### `g2.r1.observability#8` — implied

```python
# the salvage cap in the `except` handler is silent, so a run that captured a
    # truncated stream and then blew up on the way out still says it exactly once
    assert warnings_of(exit_code=0, stdout="A" * 300, stderr="", exit_error=RuntimeError("boom"), max_output_bytes=64) == [
        "sandbox output capped: stdout exceeded the 64-byte budget"
    ]
```

Konrad complains that the cleanup-throwing row got no warning despite a capped stdout, but nobody says the salvage cap in the except handler stays silent, so the reader who follows "log at the point we cut" to both cap sites emits two lines and fails this single-element equality.

### `g2.r2.observability#1` — implied

```python
assert blew_up.error == "X" * 48 + "\n[[curator:elided 236 bytes]]\n" + "X" * 16
```

l-rule-2 hedges ('if we do shorten that string') and gestures at 'head and tail with the marker between' without any of the marker text, the 48/16 split, or the 236 count, so the reader must both resolve the conditional into a decision and guess that the budget maps onto the existing stream helper's split.

### `g2.r2.observability#2` — implied

```python
assert len(blew_up.error) == 94
```

94 is purely a consequence of the unstated cap format from #1 — no remark gives a resulting length, or says the marker sits outside the 64-byte budget rather than inside it.
