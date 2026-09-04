# g7 — the requirement, reduced to what is graded

**630 words → 499** across 8 facts and 95 graded assertions.

The tests, the fact keys and the oracle are untouched. What changed is what the `-spec` arm shows an implementer, and therefore what the clues have to carry.

| fact | words | assertions | dropped |
|---|---|---|---|
| `g7.r1.rule` | 108 → 84 | 18 | 4 |
| `g7.r1.scope` | 75 → 57 | 16 | 4 |
| `g7.r1.failure_behavior` | 118 → 99 | 20 | 3 |
| `g7.r1.observability` | 157 → 152 | 19 | 2 |
| `g7.r2.rule` | 27 → 14 | 4 | 3 |
| `g7.r2.scope` | 33 → 10 | 5 | 4 |
| `g7.r2.failure_behavior` | 29 → 8 | 4 | 4 |
| `g7.r2.observability` | 83 → 75 | 9 | 2 |

## `g7.r1.rule`

**Now (84 words):**

A JSON checkpoint sits in the same working directory: module constants `TURN_LEDGER_FILENAME: str = "turn_ledger.json"` and `TURN_LEDGER_VERSION: int = 2`, a `TurnLedger.sidecar_state() -> dict[str, t.Any]` returning exactly the eight keys `{"version": TURN_LEDGER_VERSION, "responses": int, "turns": int, "last_author": str | None, "next_speaker": str | None, "interleave_faults": int, "completed": bool, "completion_reason": str}`, and `write_sidecar(working_dir, ledger) -> str` (returns the absolute path). The file is serialized as `json.dumps(ledger.sidecar_state(), indent=2, sort_keys=True) + "\n"`, and `run()` rewrites it immediately after the seed line and again after **every** appended response.

**Dropped, because no assertion checks it:**

- "beside the log" — no assertion reads the log file or the checkpoint's position relative to it; the working directory placement is still stated.
- "the three functions `read_sidecar(working_dir) -> t.Optional[dict[str, t.Any]]`" — no assertion calls `read_sidecar`; every test reads the file directly with `json.loads(open(path).read())`.
- "and `verify_sidecar(working_dir, ledger) -> TurnLedger`" — no assertion calls `verify_sidecar` or inspects a `TurnLedger` it returns.
- "— never batched to the end of the run" — a restatement of the rewrite rule already stated by "rewrites it immediately after the seed line and again after **every** appended response", which is what `#5` and `#8` turn on.

**Kept despite looking like padding:** The full `json.dumps(ledger.sidecar_state(), indent=2, sort_keys=True) + "\n"` literal reads like over-specification, since `#18` parses the file with `json.loads` and so cannot observe `indent`, `sort_keys` or the trailing newline. It stays because it is the only clause tying the file's bytes to `sidecar_state()`, which `#18` and `#15` together require, and paraphrasing it down to `json.dumps(ledger.sidecar_state())` would edit a literal. The eight-key dict likewise looks like a transcription of `#6`–`#14`, but each of those assertions reads a key name or its type, so its spelling and ordering stay verbatim.

## `g7.r1.scope`

**Now (57 words):**

`load_ledger` is `read_log` + `build_ledger` + `verify_sidecar` and writes nothing; the `status` a ledger carries comes from that verification (`"created"` for a fresh run's first write, `"adopted"` or `"verified"` after a load). No log line is ever truncated, ignored, re-ordered or rewritten, and only two of the recorded keys are compared on load — `"responses"` and `"last_author"`.

**Dropped, because no assertion checks it:**

- "The log is the authority in every direction:" — a framing restatement of the rule that immediately follows it. No assertion checks an authority claim, only that the bytes and the author order survive (#12, #13, #14).
- "to agree with the checkpoint" — the motive for rewriting a line. The prohibition is what #12 and #13 check (bytes identical); why someone might rewrite is never read.
- "a ledger built for" — filler between the literal `"created"` and the condition that earns it. #16 checks the literal on a fresh processor's ledger, and the surviving "for a fresh run's first write" still states that condition exactly.
- "the eight" (from "the eight recorded keys") — the total key count. Nothing counts recorded keys, and the seven field names read by #5–#11 were never enumerated in this text anyway; "only two ... are compared on load" is the graded part and stays.

**Kept despite looking like padding:** "comes from that verification" reads like connective tissue but stays: deleting it strands the parenthetical as a fragment, and it is the only link between `verify_sidecar` and the three status literals graded by #1, #2, #5 and #16. "and writes nothing" is held by #4 and #12/#13. "re-ordered" alone is held by #14, so the verb list cannot be collapsed. `"responses"` and `"last_author"` are held by #3/#7 and by #15, which turns on a mismatch in exactly one of the two compared keys raising.

## `g7.r1.failure_behavior`

**Now (99 words):**

`verify_sidecar` has exactly three arms. (a) The file is absent, or unreadable as JSON, or its `"version"` is not `TURN_LEDGER_VERSION` → `status = "adopted"`. (b) The version matches **and** both `"responses"` and `"last_author"` equal the log-derived values → `status = "verified"`. (c) The version matches and either value differs → raise `TurnLedgerDesyncError(path, log_responses, recorded_responses, log_last_author, recorded_last_author)`, a subclass of `TurnLedgerError`, storing all five as attributes of those names, with message `f"{path} records {recorded_responses} response(s) last authored by {recorded_last_author!r}, the log holds {log_responses} last authored by {log_last_author!r}"`. The raise happens before any request is issued and before anything is appended.

**Dropped, because no assertion checks it:**

- "no error raised" (arm a) — no assertion checks that the adopted path is non-raising; #2–#4 only read `status == "adopted"`, which a load that returns at all already implies.
- "and the file is rewritten from the log on the next append" — no assertion inspects the sidecar after a later append; the only append-related check is #20, `len(log_lines(tmp_path)) == 3`, and that is on the desync path.
- "on the load path" — #19 (`conversation.calls == []`) and #20 (log length unchanged) pin when the raise happens; nothing checks which code path it sits on.

**Kept despite looking like padding:** "`verify_sidecar` has exactly three arms." reads like framing that (a)/(b)/(c) already enumerate, but it is the only place the subject of the spec is named, so cutting it leaves three arms attached to nothing an implementer can locate. Also forced to stay: "a subclass of `TurnLedgerError`" by #1 (`issubclass(desync, base)`); "storing all five as attributes of those names" by #7–#11, which read `error.path`, `error.log_responses`, `error.recorded_responses`, `error.log_last_author`, `error.recorded_last_author`; and the f-string verbatim by #12, which compares `str(error)` character for character.

## `g7.r1.observability`

**Now (152 words):**

Fresh run in `tmp_path` with a fake `call_single_request` that raises on its first call: `tmp_path/"turn_ledger.json"` already exists, is exactly 186 bytes (trailing newline included), and reads `{"completed": false, "completion_reason": "open", "interleave_faults": 0, "last_author": "client", "next_speaker": "advisor", "responses": 0, "turns": 1, "version": 2}` in that sorted, 2-space-indented spelling. After a completed 4-line run the file is 189 bytes and `read_sidecar(str(tmp_path)) == {"version": 2, "responses": 3, "turns": 4, "last_author": "advisor", "next_speaker": None, "interleave_faults": 0, "completed": True, "completion_reason": "agent_signal"}`. Truncating that log to its first 3 lines and leaving the stale file makes a new processor's `run()` raise `TurnLedgerDesyncError` with `.path == str(tmp_path/"turn_ledger.json")`, `.log_responses == 2`, `.recorded_responses == 3`, `.log_last_author == "client"`, `.recorded_last_author == "advisor"`, zero calls to `call_single_request` and the log still 3 lines; deleting the file instead gives `ledger.status == "adopted"` and exactly one further call. A sidecar of `{"version": 1, "responses": 2, "last_author": "client"}` against that same 3-line log also gives `"adopted"`.

**Dropped, because no assertion checks it:**

- "in an empty" (from "Fresh run in an empty `tmp_path`") - directory emptiness is fixture setup; no assertion reads it, and "Fresh run" already carries it.
- "at that moment" (from "already exists at that moment") - the timing is already fixed by "already exists" plus "raises on its first call"; nothing reads the phrase.

**Kept despite looking like padding:** "(trailing newline included)" and "in that sorted, 2-space-indented spelling" both read as padding but had to stay. The JSON object is quoted inline on a single line with no newline shown, so those two clauses are the only statement of the key ordering, 2-space indent and final newline that #3 compares byte-for-byte, and of the trailing newline that makes #4's 186 come out. `.path == str(tmp_path/"turn_ledger.json")` restates the filename from the first sentence, but #9 compares `os.path.realpath(caught.value.path)` against the sidecar, so the absolute-path form has to be spelled out rather than left to "the sidecar". "already exists" survives the cut to "at that moment" because #2 grades existence before the first `call_single_request`, and "and exactly one further call" survives because #17 and #18 both turn on the count.

## `g7.r2.rule`

**Now (14 words):**

`COMPLETION_SENTINEL` is exactly the string `"<<END_OF_CONVERSATION>>"`, and the base `Agent.is_completed(response)` returns `True` iff `response.rstrip().endswith(COMPLETION_SENTINEL)`.

**Dropped, because no assertion checks it:**

- the prose restatement of the rule, "`response` is a `str` whose right-stripped form ends with it" — the same rule stated twice, once in words and once as code; the code form is kept because it names the identifiers the assertions read
- the `isinstance(response, str) and ` guard from the kept expression — no assertion passes a non-`str` to `is_completed`
- the parentheses around the kept expression, now that it is the only statement of the rule rather than a gloss on the prose

**Kept despite looking like padding:** "exactly the string `\"<<END_OF_CONVERSATION>>\"`" reads like emphasis but the literal is compared directly by #1 (`sym("COMPLETION_SENTINEL") == SENTINEL`), so the value stays verbatim. `response.rstrip().endswith(COMPLETION_SENTINEL)` is the whole of what #2, #3 and #4 exercise — #3 needs a bare sentinel to pass, #2 needs a trailing sentinel to pass, #4 needs a sentinel-free string to fail — so the expression stays as the specification rather than a summary like "detects the sentinel".

## `g7.r2.scope`

**Now (10 words):**

Matching is case-sensitive and suffix-only, and insensitive to trailing whitespace.

**Dropped, because no assertion checks it:**

- The two True worked examples and their verdict: `: "all set <<END_OF_CONVERSATION>>" and "all set <<END_OF_CONVERSATION>>  \n" are both `True`` — demonstrations of "suffix-only" plus "insensitive to trailing whitespace", both of which the surviving sentence states. Assertions #1 and #2 interpolate SENTINEL rather than this spelled-out literal, so no graded value left with it.
- The False worked example `"<<END_OF_CONVERSATION>> but wait"` — a demonstration of "suffix-only", which the surviving sentence states; assertion #3 also interpolates SENTINEL.
- The False worked example `"all set <<end_of_conversation>>"` — a demonstration of "case-sensitive", which the surviving sentence states.
- The False worked example `"all set"` and the closing verdict `are all `False`` — a demonstration that a string with no sentinel cannot end with one, which follows from "suffix-only".

**Kept despite looking like padding:** "and insensitive to trailing whitespace" reads like a caveat but is load-bearing: assertion #2 appends a tab, not a newline, so the clause has to say "whitespace" in general rather than name a newline. The rest of the surviving sentence is graded rule with nothing spare — "case-sensitive" is the whole of #4, "suffix-only" is the whole of #3 and #5.

## `g7.r2.failure_behavior`

**Now (8 words):**

A non-`str` `response_message` returns `False` rather than raising.

**Dropped, because no assertion checks it:**

- "— the structured-output `dict`, or `None` —": an enumeration of two of the non-`str` cases; the general "non-`str`" already covers dict, None, list and int, and no assertion reads the words "structured-output".
- "`A.is_completed({\"text\": \"<<END_OF_CONVERSATION>>\"}) is False`": worked example restating assertion #1; no literal is graded here beyond "non-`str` returns `False`" (the sentinel is supplied by the fixture as SENTINEL).
- "and `A.is_completed(None) is False`": second worked example, pinning the same rule the first already pins.
- "with no `AttributeError` or `TypeError` escaping": restatement of "rather than raising" in different words; naming the two exception types adds no assertion, since no test inspects an exception type.

**Kept despite looking like padding:** "returns `False`" stays verbatim rather than becoming \"is falsy\" — all four assertions use `is False`, so identity with the `False` singleton is graded and an implementer returning `0` or `None` would fail. "non-`str`" stays as the predicate because assertions #3 and #4 (`[SENTINEL]`, `42`) are only reachable from a rule stated over all non-`str` types, not over dict/None specifically.

## `g7.r2.observability`

**Now (75 words):**

The message carrying the sentinel is a real turn: it is appended to `responses_0.jsonl`, counted in `responses`, and present in the dataset, and the conversation stops after it. End to end with `max_length = 6` and a fake whose third reply is `"Then index funds. <<END_OF_CONVERSATION>>"`: the fake is called exactly `3` times, the log holds `4` lines, `tracker.num_responses == 3`, `ledger.completion_reason == "agent_signal"`, and the dataset's last row's `content` is `"Then index funds. <<END_OF_CONVERSATION>>"`.

**Dropped, because no assertion checks it:**

- ", not a discarded control signal" — a negative restatement of "is a real turn"; the same rule said twice for emphasis, and no assertion reads it.
- "counted by `update_turn`, " — names the internal mechanism behind a count the second sentence already pins as `tracker.num_responses == 3`; no assertion mentions `update_turn`.

**Kept despite looking like padding:** "counted in `responses`" reads like a duplicate of `tracker.num_responses == 3` but is the only text covering assertion #4 (`ledger.responses == 3`), a different field on a different object. "and the conversation stops after it" is the only text covering assertion #6 (`ledger.completed is True`). "present in the dataset" plus the repeated literal `"Then index funds. <<END_OF_CONVERSATION>>"` at the end carry assertions #7 and #8, so the literal stays spelled out twice rather than back-referenced. Separately: neither the original nor the trim states the last row's `role`, so assertion #9 (`rows[-1]["role"] == PARTNER`) has no text behind it — that gap predates this edit and I did not add wording, since this task is deletion only.
