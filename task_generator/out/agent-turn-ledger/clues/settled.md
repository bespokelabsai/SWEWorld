# Was every graded thing said, or only implied? — g7

**88 of 95** assertions rest on something a remark says outright.

- `stated` **88** — a reader was told
- `implied` **2** — a reader has to work it out, and may not
- `absent` **1** — nothing in the corpus bears on it
- `not_required` **4** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

> **These verdicts are what provoked the rewrites, not what the plant says now.** 3 remark(s) rewritten, 0 added, 0 not fixed. Re-run `settle --dry-run` for the verdicts on the corpus as it now stands.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g7.r1.failure_behavior#1` | stated | `g7.r1.rev1` | rev1 spells the full chain out loud: TurnLedgerDesyncError is a TurnLedgerError, "itself just a RuntimeError". |
| `g7.r1.failure_behavior#10` | stated | `g7.r1.l12` | l12 names .log_last_author explicitly as an exception attribute holding the log's author. |
| `g7.r1.failure_behavior#11` | stated | `g7.r1.l16` | l16 names recorded_last_author as coming off the exception, holding the checkpoint's author. |
| `g7.r1.failure_behavior#12` | **absent** | `g7.r1.l12` | No remark quotes any fragment of the message; l12 only concedes a message exists, leaving its entire wording, ordering, "response(s)" phrasing and !r quoting unsourced. |
| `g7.r1.failure_behavior#13` | stated | `g7.r1.rev1` | rev1 names last_author disagreement as a raising condition alongside responses. |
| `g7.r1.failure_behavior#14` | stated | `g7.r1.l12` | l12 fixes .log_last_author as the attribute holding the log's author; the SEEDER value is the suite's fixture. |
| `g7.r1.failure_behavior#15` | stated | `g7.r1.l16` | l16 fixes recorded_last_author as the attribute holding the checkpoint's author; PARTNER is fixture-side. |
| `g7.r1.failure_behavior#16` | stated | `g7.r1.l12`, `g7.r1.rev1` | l12 names .log_responses and rev1 makes clear an author-only disagreement still raises, so the matching counts still populate. |
| `g7.r1.failure_behavior#17` | stated | `g7.r1.l16`, `g7.r1.rev1` | l16 names recorded_responses and rev1 establishes the raise fires on last_author alone, so both counts are carried even when equal. |
| `g7.r1.failure_behavior#18` | stated | `g7.r1.rev1` | Same raise condition rev1 states directly. |
| `g7.r1.failure_behavior#19` | stated | `g7.r1.l16`, `g7.r1.rev1` | l16 files the four burned calls as the bug — "it should be refusing before the first call" — and rev1 confirms the raise precedes the first request. |
| `g7.r1.failure_behavior#2` | stated | `g7.r1.l9`, `g7.r1.rev2` | l9 decides a missing file is benign and the log is adopted, and rev2 supplies the exact status token "adopted" for the non-abort arm. |
| `g7.r1.failure_behavior#20` | stated | `g7.r1.l6`, `g7.r1.rev1` | l6 decides the jsonl is left alone when the two disagree, and rev1 puts the raise before the first request, so the three seeded lines stand. |
| `g7.r1.failure_behavior#3` | stated | `g7.r1.l11`, `g7.r1.rev2` | l11 makes the call for a half-written line that dies in json.loads — "we dont discard an intact log over that - adopt it". |
| `g7.r1.failure_behavior#4` | stated | `g7.r1.rev2`, `g7.r1.l10` | rev2 says a missing or below-2 version "just gets status adopted" and only a version-2 mismatch aborts. |
| `g7.r1.failure_behavior#5` | stated | `g7.r1.say20` | say20 states the verified arm nearly verbatim: version 2, responses and last_author both matching, status verified. |
| `g7.r1.failure_behavior#6` | stated | `g7.r1.rev1`, `g7.r1.l16` | rev1 says a current-version checkpoint disagreeing on responses raises TurnLedgerDesyncError. |
| `g7.r1.failure_behavior#7` | stated | `g7.r1.l10`, `g7.r1.l15` | l10 says the error's .path attribute holds the turn_ledger.json path, and l15 establishes write_sidecar hands back an absolute path for tests to compare against. |
| `g7.r1.failure_behavior#8` | stated | `g7.r1.l12` | l12 names .log_responses as an attribute on the exception carrying the log-derived count, not just message text. |
| `g7.r1.failure_behavior#9` | stated | `g7.r1.l16` | l16 reports recorded_responses coming off the exception in a stale-checkpoint repro, fixing both the name and that it is the file's side. |
| `g7.r1.observability#1` | n/a | — | This is the suite's own fixture — a fake call_single_request rigged to raise on its first call — not a behaviour the corpus owes anything to. |
| `g7.r1.observability#10` | stated | `g7.r1.l12` | l12 says the log side hangs off the exception as .log_responses 2. |
| `g7.r1.observability#11` | stated | `g7.r1.l16` | l16 reports recorded_responses 3 coming off the exception in this same stale-checkpoint repro. |
| `g7.r1.observability#12` | stated | `g7.r1.l12` | l12 names .log_last_author 'client' as an attribute of the exception, not just message text. |
| `g7.r1.observability#13` | stated | `g7.r1.l16` | l16 reports recorded_last_author 'advisor' coming off the exception. |
| `g7.r1.observability#14` | stated | `g7.r1.rev1`, `g7.r1.l16` | rev1 says the raise happens before the first request and l16 complains that four calls were burned when it should refuse before the first call. |
| `g7.r1.observability#15` | stated | `g7.r1.rev2`, `g7.r1.rev1`, `g7.r1.l6` | rev2, rev1 and l6 all say the trim-back-to-recorded-count is gone and the jsonl is left alone when the two disagree, so the 3-line log stays 3 lines. |
| `g7.r1.observability#16` | stated | `g7.r1.l9`, `g7.r1.rev2`, `g7.r1.say20`, `g7.r1.l8` | l9 says a missing json file is benign and we adopt the log, and rev2 says missing or below-version checkpoints just get status adopted, with say20/l8 establishing status as a field on the ledger. |
| `g7.r1.observability#17` | stated | `g7.r1.l9` | l9 spells out the resumed behaviour as exactly one call_single_request(advisor, 2). |
| `g7.r1.observability#18` | stated | `g7.r1.l11`, `g7.r1.l9` | l11 says an adopted intact log gets the one line appended, three becomes four. |
| `g7.r1.observability#19` | stated | `g7.r1.rev2`, `g7.r1.l10` | rev2 says a checkpoint missing the version key or below TURN_LEDGER_VERSION 2 just gets status adopted, and l10 calls pre-version-2 checkpoints stale rather than wrong. |
| `g7.r1.observability#2` | stated | `g7.r1.l13`, `g7.r1.l4` | l13 reports killing a run on its very first call and finding turn_ledger.json already there, saying the seed line alone triggers the write, and l4 repeats that the record goes out after every append,  |
| `g7.r1.observability#3` | stated | `g7.r1.l4`, `g7.r1.l13`, `g7.r1.l14`, `g7.r1.say22`, `g7.r1.say23`, `g7.r1.say24`, `g7.r1.say25`, `g7.r1.rev2` | Every element is said out loud: eight keys (l4), version 2 (rev2), responses 0/turns 1/last_author client (l13), next_speaker advisor after a client line (say24), interleave_faults 0 on a clean log (s |
| `g7.r1.observability#4` | **implied** | `g7.r1.l14`, `g7.r1.l4`, `g7.r1.l13` | No remark mentions a byte size; the reader has to notice that the fully-specified key set, values and formatting fix the file's length at 186 and that nobody ever said so. |
| `g7.r1.observability#5` | stated | `g7.r1.say21`, `g7.r1.l2` | say21 describes a clean four-turn run ending with turns 4 and l2 defines turns as the jsonl line count with the seed line included, so the completed log is four lines. |
| `g7.r1.observability#6` | **implied** | `g7.r1.l14`, `g7.r1.say21`, `g7.r1.l4` | The completed record's keys, values and formatting are all stated, but nobody attaches any byte count to the file, so 189 is left for the reader to arrive at. |
| `g7.r1.observability#7` | stated | `g7.r1.say21`, `g7.r1.rev2`, `g7.r1.say25`, `g7.r1.l4`, `g7.r1.l15` | say21 gives responses 3, turns 4, last_author advisor, next_speaker null, completed true, completion_reason agent_signal; rev2 gives version 2, say25 gives interleave_faults 0, l4 fixes the eight keys |
| `g7.r1.observability#8` | stated | `g7.r1.rev1`, `g7.r1.rev2`, `g7.r1.l16` | rev1 says a current-version checkpoint disagreeing on responses or last_author raises TurnLedgerDesyncError, which is exactly the stale 3-line-log case. |
| `g7.r1.observability#9` | stated | `g7.r1.l10`, `g7.r1.l12` | l10 says the error's .path attribute holds that turn_ledger.json path, and l12 shows it carrying the working dir's turn_ledger.json. |
| `g7.r1.rule#1` | stated | `g7.r1.l2` | l2 names the constant and its value together: "the working dir gets TURN_LEDGER_FILENAME, turn_ledger.json". |
| `g7.r1.rule#10` | stated | `g7.r1.l13`, `g7.r1.say21`, `g7.r1.l8` | l13 and say21 both report last_author as whoever wrote the final log line, and l8 calls it "who wrote last". |
| `g7.r1.rule#11` | stated | `g7.r1.say24` | say24 states next_speaker is nothing more than the partner of last_author, with a worked example. |
| `g7.r1.rule#12` | stated | `g7.r1.say25` | say25 says a clean client/advisor alternation always rebuilds interleave_faults to 0. |
| `g7.r1.rule#13` | stated | `g7.r1.say22`, `g7.r1.say21` | say22 says completed is seeded false and stays false through every append, flipping true only when the run finishes. |
| `g7.r1.rule#14` | stated | `g7.r1.say23` | say23 says completion_reason sits at "open" on every write while the run is still going. |
| `g7.r1.rule#15` | stated | `g7.r1.l4` | l4 names sidecar_state as the eight-key record and says that record is what goes back out through write_sidecar, so the method's return matches the file. |
| `g7.r1.rule#16` | stated | `g7.r1.l15` | l15 says write_sidecar already returns the absolute path it wrote. |
| `g7.r1.rule#17` | stated | `g7.r1.l15`, `g7.r1.l2` | l15 says the returned path is the path it wrote and that tests read straight off it, with l2 placing that file at turn_ledger.json in the working dir. |
| `g7.r1.rule#18` | stated | `g7.r1.l14`, `g7.r1.l15`, `g7.r1.l4` | l14 says turn_ledger.json goes out as sort_keys/indent-2 JSON and l15 says reading the working dir gives the record back as a dict, so the file's JSON is the eight-key state. |
| `g7.r1.rule#2` | stated | `g7.r1.rev2`, `g7.r1.l10` | rev2 says the stamp is the "version" key holding TURN_LEDGER_VERSION 2, and l10 repeats the constant name with the number 2. |
| `g7.r1.rule#3` | n/a | — | Boom is the suite's own injected client failure, not anything the corpus owes. |
| `g7.r1.rule#4` | n/a | `g7.r1.say25` | This checks the fixture's own log state — the alternating seed/partner/seed jsonl the base conversation loop already produces. |
| `g7.r1.rule#5` | stated | `g7.r1.say23`, `g7.r1.l13`, `g7.r1.l4` | say23 says it writes mid-run, l13 says the seed line alone triggers the write, and l4 says it goes back out after every append — so a file exists when the run dies mid-flight. |
| `g7.r1.rule#6` | stated | `g7.r1.l4` | l4 says ledger.sidecar_state is exactly eight keys and enumerates all eight by name. |
| `g7.r1.rule#7` | stated | `g7.r1.rev2` | rev2 attaches the value directly to the key: the "version" key holds TURN_LEDGER_VERSION 2. |
| `g7.r1.rule#8` | stated | `g7.r1.l13`, `g7.r1.say21`, `g7.r1.l2` | l13 pins responses 0 at the seed line and say21 pins responses 3 for a four-turn run, with l2's responses-plus-one relation fixing the count as appended responses. |
| `g7.r1.rule#9` | stated | `g7.r1.l2`, `g7.r1.l13`, `g7.r1.say21` | l2 defines turns as the jsonl line count including the seed line, i.e. responses plus one. |
| `g7.r1.scope#1` | stated | `g7.r1.l8`, `g7.r1.rev2`, `g7.r1.say20`, `g7.r1.l9` | All three status strings are named out loud as the ledger's status — "created" for a first write (l8), "adopted" for a missing/older stamp (rev2, l9), "verified" for a matching version-2 checkpoint (s |
| `g7.r1.scope#10` | stated | `g7.r1.say22`, `g7.r1.say21` | say22 says the record is seeded completed false and stays false through every append until the run finishes, and say21 shows true only on a run carried to the end. |
| `g7.r1.scope#11` | stated | `g7.r1.say23`, `g7.r1.say21` | say23 says completion_reason sits at "open" on every write while the run is still going. |
| `g7.r1.scope#12` | stated | `g7.r1.rev1`, `g7.r1.rev2`, `g7.r1.l6`, `g7.r1.say20` | rev1 and rev2 both retract the truncate-back-to-the-checkpoint behaviour, l6 says the jsonl is left alone on disagreement, and say20 says the file stays exactly as it was. |
| `g7.r1.scope#13` | stated | `g7.r1.l6`, `g7.r1.rev1`, `g7.r1.rev2` | The same retraction covers the desync path: the run raises before the first request and the log bytes are left untouched rather than trimmed. |
| `g7.r1.scope#14` | stated | `g7.r1.l6`, `g7.r1.say20`, `g7.r1.say25` | l6 and say20 commit to leaving the jsonl exactly as it was, so the recorded lines keep their authors and their order across a load. |
| `g7.r1.scope#15` | n/a | — | Boom is the suite's own injected exception and the assertion only checks that it propagates out of the run; the corpus owes nothing to that fixture plumbing. |
| `g7.r1.scope#16` | stated | `g7.r1.l8`, `g7.r1.l13` | l8 says a first write has not been compared against anything so the ledger says created, and l13 confirms the seed line alone triggers that first write. |
| `g7.r1.scope#2` | stated | `g7.r1.rev2`, `g7.r1.l9` | rev2 says a missing or below-version-2 stamp "just gets status adopted", and l9 confirms the missing-file case adopts the log. |
| `g7.r1.scope#3` | stated | `g7.r1.l6`, `g7.r1.l2`, `g7.r1.l9` | l6 says the counters rebuild from the log when the sidecar is not trusted, and l2 fixes responses as the jsonl line count minus the seed line, so the adopted record's responses follows from the fixtur |
| `g7.r1.scope#4` | stated | `g7.r1.l5`, `g7.r1.say20`, `g7.r1.l4` | l5 complains that opening a finished run had load rewrite the file and states it "gets read back and verified not replaced", and say20 says the file stays exactly as it was; l4 puts the writing at app |
| `g7.r1.scope#5` | stated | `g7.r1.say20`, `g7.r1.l8` | say20 says a version-2 checkpoint whose responses and last_author both match the log "comes back status verified". |
| `g7.r1.scope#6` | stated | `g7.r1.l2` | l2 states turns is the jsonl line count with the seed line included, i.e. responses plus one. |
| `g7.r1.scope#7` | stated | `g7.r1.l2`, `g7.r1.l6` | l2 pins responses as turns minus the seed line and l6 says the counters rebuild off the log, so the count for a three-line log is dictated. |
| `g7.r1.scope#8` | stated | `g7.r1.say24` | say24 says next_speaker is nothing more than the partner of last_author, with the worked example of a log ending on client coming back advisor. |
| `g7.r1.scope#9` | stated | `g7.r1.say25` | say25 says interleave_faults counts where the log doubles back on one author, so a clean client/advisor alternation always rebuilds to 0. |
| `g7.r2.failure_behavior#1` | stated | `g7.r2.rev2`, `g7.r2.g7r2-l08`, `g7.r2.g7r2-l09` | rev2 names is_completed and says outright that a non-str argument returns False, and l08/l09 establish the dict-shaped reply as the concrete case it covers. |
| `g7.r2.failure_behavior#2` | stated | `g7.r2.rev2`, `g7.r2.g7r2-l10` | rev2's "non-str returns False" is a general rule about is_completed's return value, and None is a non-str argument with no competing remark. |
| `g7.r2.failure_behavior#3` | stated | `g7.r2.rev2`, `g7.r2.g7r2-l09` | A list is non-str, so rev2's stated return value applies directly without the reader inferring anything. |
| `g7.r2.failure_behavior#4` | stated | `g7.r2.rev2`, `g7.r2.g7r2-l10` | An int is non-str and rev2 fixes the return as False, so the reader writes the isinstance guard because they were told to, not because they worked it out. |
| `g7.r2.observability#1` | stated | `g7.r2.g7r2-l13`, `g7.r2.g7r2-l12` | gideon's test-writing page fixes the scenario as budget 6 with "the fake answered three times", which is the call count the assertion checks, and emil pins the third reply as the sentinel-bearing one. |
| `g7.r2.observability#2` | stated | `g7.r2.g7r2-l13`, `g7.r2.say18` | l13 says "four lines in responses_0.jsonl" for exactly this run, and dermot independently reports the jsonl log at four lines. |
| `g7.r2.observability#3` | stated | `g7.r2.g7r2-l13` | l13 states "the tracker reporting three responses" for the same budget-6/three-reply run, attaching the count 3 to the tracker itself. |
| `g7.r2.observability#4` | stated | `g7.r2.g7r2-l13` | l13 names the field outright: "the ledger's own responses field at 3 too". |
| `g7.r2.observability#5` | stated | `g7.r2.g7r2-l14` | nils' ledger page says a run that ended on the marker has completion_reason reading "agent_signal", never budget. |
| `g7.r2.observability#6` | stated | `g7.r2.say19` | konrad says completed reads True on the ledger for runs the agent ended itself, calling it a finish rather than a cut-short run. |
| `g7.r2.observability#7` | stated | `g7.r2.say18`, `g7.r2.g7r2-l11` | dermot reports the dataset coming out at four rows, same count as the jsonl log, "closing message and all", and dario's l11 frames the bug as the closing message missing from the arrow file. |
| `g7.r2.observability#8` | stated | `g7.r2.g7r2-l12` | emil quotes the exact third reply string and demands that entire string be the content of the last dataset row. |
| `g7.r2.observability#9` | stated | `g7.r2.g7r2-l12` | emil's same remark specifies the role of that last row as PARTNER. |
| `g7.r2.rule#1` | stated | `g7.r2.rev1`, `g7.r2.g7r2-l02`, `g7.r2.g7r2-l12`, `g7.r2.rev2` | rev1 names the constant `COMPLETION_SENTINEL` as the operand of the endswith check and, in the same breath, identifies the thing being matched as the literal `<<END_OF_CONVERSATION>>`, with l02 and l1 |
| `g7.r2.rule#2` | stated | `g7.r2.rev1`, `g7.r2.rev2`, `g7.r2.g7r2-l05` | rev1 and rev2 give the check verbatim as `response.rstrip().endswith(COMPLETION_SENTINEL)` and l05 says explicitly that it counts as a stop when the marker is the tail end of the reply. |
| `g7.r2.rule#3` | stated | `g7.r2.rev1`, `g7.r2.rev2`, `g7.r2.g7r2-l12` | A response that is exactly the marker is a direct application of the endswith rule spelled out in rev1/rev2, and l12/l02 establish the marker as the trailing token of a closing message. |
| `g7.r2.rule#4` | stated | `g7.r2.rev1`, `g7.r2.rev2`, `g7.r2.g7r2-l03` | The endswith formula given in rev1/rev2 returns False for text lacking the marker, and l03 says the base agent's check should look for the marker rather than answer no forever, i.e. it answers no when |
| `g7.r2.scope#1` | stated | `g7.r2.rev1`, `g7.r2.rev2`, `g7.r2.g7r2-l07`, `g7.r2.g7r2-l05` | rev1 and rev2 both hand over the expression `response.rstrip().endswith(COMPLETION_SENTINEL)` by name, and l07 says explicitly that a trailing newline tacked on by providers must not change the match. |
| `g7.r2.scope#2` | stated | `g7.r2.rev2`, `g7.r2.rev1`, `g7.r2.g7r2-l07` | rev2 says trailing whitespace is ignored and names rstrip(), which covers a trailing tab as directly as a trailing newline; no inference beyond the named call is needed. |
| `g7.r2.scope#3` | stated | `g7.r2.g7r2-l05`, `g7.r2.rev1`, `g7.r2.g7r2-l04` | l05 says a marker mid-paragraph is obviously still going, and rev1/l04 record the incident where a mid-sentence paste wrongly ended the run, so suffix-only is decided out loud. |
| `g7.r2.scope#4` | stated | `g7.r2.rev1`, `g7.r2.rev2`, `g7.r2.g7r2-l06`, `g7.r2.g7r2-l12` | rev1 says case-sensitive, rev2 says exact casing, l06 says capitals included, and l12/l02 give the marker in uppercase, so a lowercase tail must not match. |
| `g7.r2.scope#5` | stated | `g7.r2.rev2`, `g7.r2.rev1`, `g7.r2.g7r2-l03` | The check named in rev1/rev2 is endswith on the sentinel, so a reply that never contains the marker returning False is the decision as stated, not something the reader must work out. |

### `g7.r1.failure_behavior#12` — absent

```python
assert str(error) == (
        f"{error.path} records 1 response(s) last authored by {SEEDER!r}, "
        f"the log holds 2 last authored by {SEEDER!r}"
    )
```

No remark quotes any fragment of the message; l12 only concedes a message exists, leaving its entire wording, ordering, "response(s)" phrasing and !r quoting unsourced.

### `g7.r1.observability#4` — implied

```python
assert path.stat().st_size == 186
```

No remark mentions a byte size; the reader has to notice that the fully-specified key set, values and formatting fix the file's length at 186 and that nobody ever said so.

### `g7.r1.observability#6` — implied

```python
assert sidecar.stat().st_size == 189
```

The completed record's keys, values and formatting are all stated, but nobody attaches any byte count to the file, so 189 is left for the reader to arrive at.
