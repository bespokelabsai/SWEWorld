You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Durable turn ledger for multi-turn agent conversations**

Make a multi-turn agent conversation a durable, resumable record: the seed becomes a real logged turn, resume state is derived from the log instead of a step parity, and the resumed run neither re-generates nor re-counts what it already has.

### New module `src/bespokelabs/curator/agent/turn_ledger.py`

- Module docstring: `"""The durable record of a multi-turn agent conversation."""`. It takes every timestamp as a parameter — it imports neither `time`, `random`, `uuid` nor `os.urandom`.
- Constants: `RESPONSES_FILENAME: str = "responses_0.jsonl"`, `SEED_FINISH_REASON: str = "seed"`, `COMPLETION_SENTINEL: str`, `COMPLETION_REASONS: tuple[str, ...] = ("open", "budget", "agent_signal")`, `LEDGER_STATUSES: tuple[str, ...] = ("created", "adopted", "verified")`.
- Exceptions: `TurnLedgerError(RuntimeError)` as the base for every turn-ledger failure, and `TurnLedgerCorruptError(TurnLedgerError)` with `__init__(self, path: str, line_number: int, reason: str)` storing `.path`, `.line_number` (1-based over physical lines) and `.reason`.
- Two **frozen dataclasses** (`@dataclass(frozen=True)` — not pydantic models, not `NamedTuple`s, not dicts), field order exactly:
  - `TurnEntry(turn, author, content, source)` — `turn` is the 0-based index into the log (the seed is `0`), `author` is the agent name the line was written under, `content` is `response_message` coerced with `str()` when it is not already a `str`, `source` is `"seed"` for turn 0 and `"response"` otherwise.
  - `TurnLedger(entries, seeder_name, partner_name, max_responses, responses, turns, next_speaker, last_author, interleave_faults, completed, completion_reason, status)`, where `entries` is a `tuple[TurnEntry, ...]` and never a `list`.
- `TurnLedger.messages() -> list[dict[str, str]]` returns `[{"role": entry.author, "content": entry.content}, ...]` in log order.
- Functions:
  - `build_seed_record(*, seeder_name: str, seed_message: str, model_name: str, now: datetime.datetime) -> AgentResponse`
  - `read_log(working_dir: str) -> list[AgentResponse]`
  - `build_ledger(records: t.Sequence[AgentResponse], *, seeder_name: str, partner_name: str, max_responses: int, is_completed: t.Callable[[str, t.Any], bool], status: str = "verified") -> TurnLedger`
  - `load_ledger(working_dir: str, *, seeder_name: str, partner_name: str, max_responses: int, is_completed: t.Callable[[str, t.Any], bool]) -> TurnLedger` — loads the ledger for a working directory and never writes to disk.

### Ledger semantics

- `responses == len(entries) - 1`, never negative; `turns == len(entries)`.
- `next_speaker` is the agent that did **not** write the last entry: `partner_name if last_author == seeder_name else seeder_name`. It is never computed from `len(entries) % 2`, from `responses % 2`, or from a step counter. An entry whose author is neither `seeder_name` nor `partner_name` counts as "not the seeder", so `next_speaker` becomes `seeder_name`.
- A log in which the same author appears twice in a row is **legal**: it does not raise, does not truncate the log, and does not drop the duplicate. `interleave_faults` is the number of indices `i >= 1` with `entries[i].author == entries[i - 1].author`, and the next turn still goes to the complement of the last author.
- `completion_reason` is `"agent_signal"` when the **last** entry's author's `is_completed` returns true for its content (checked on the last entry only, not on every entry); otherwise `"budget"` when `responses >= max_responses`; otherwise `"open"`. `"agent_signal"` wins when both hold. `completed` is `completion_reason != "open"`, and `next_speaker is None` exactly when `completed` is true.
- An empty log gives `(completion_reason, responses, turns, last_author, next_speaker) == ("open", 0, 0, None, None)` with `completed is False`.
- `read_log` skips lines that are empty or whitespace-only and raises `TurnLedgerCorruptError(path, line_number, reason)` for any other unparseable line, instead of letting pydantic's `ValidationError` out.

### `MultiTurnAgenticProcessor` (`src/bespokelabs/curator/agent/processor.py`)

- `__init__(self, seeder, partner, max_length, seed_message, now_fn: t.Callable[[], datetime.datetime] = datetime.datetime.now)`; keeps `self.now_fn` and `self.ledger: t.Optional[TurnLedger] = None`. `AgentStatusTracker(max_turns=self.max_length)` is unchanged.
- `load_cache(self, working_dir: str) -> TurnLedger` returns a `TurnLedger` and does not touch the status tracker at all. The processor keeps the last ledger it built on `self.ledger`.
- **The seed is a durable turn.** When `responses_0.jsonl` is absent or empty, `run()` writes exactly one line — `build_seed_record(...)` — through the existing `append_response()` *before* the first request is built, then enters the loop. That record has `name = seeder.name`, `response_message = seed_message`, `finish_reason = "seed"`, `response_cost = 0.0`, `token_usage = None`, `response_errors = None`, `raw_response = None`, `raw_request = None`, `parsed_response_message = None`, `created_at = finished_at = now_fn()`, and `generic_request = GenericRequest(model=seeder.model_name, messages=[{"role": "user", "content": seed_message}], original_row={"prompt": seed_message}, original_row_idx=0, response_format=None, generation_params={}, is_multimodal_prompt=False)`.
- **`max_length` is a budget of generated responses, not of messages.** The seed is not one. The loop condition is `while ledger.responses < self.max_length`, so an un-stopped run makes exactly `max_length` calls to `call_single_request` and leaves `max_length + 1` log lines whether it ran once or resumed five times. `APIRequest(task_id=...)` is given `ledger.responses`, the 0-based response index.
- **The ledger is re-derived after every appended response**, from the records the run has read or written so far — the list it already holds in memory, not by re-reading `responses_0.jsonl`. So `responses`, `turns`, `last_author`, `next_speaker` and `completed` all advance as the conversation goes, and the loop terminates. Two traps: a ledger built once before the loop and held has a `next_speaker` that never changes, so it asks the same agent forever; and `append_response()` writes through buffered `aiofiles`, so a ledger re-derived by reading the file back sees nothing until the buffer is flushed, with the same effect. Flush after each append so the log on disk stays current for a reader.
- Each iteration asks the agent named by `ledger.next_speaker`; `_agent_for(name)` maps a name to `seeder`/`partner` and raises `KeyError` otherwise. `run()` short-circuits on `ledger.completed`, never on a message count reaching `max_length`.
- `self.conversation_history` stays a `list[dict[str, str]]` keyed `"role"` (an agent *name*) and `"content"`, and equals `self.ledger.messages()` after every ledger update.
- `run()` calls `status_tracker.adopt_ledger(cached_responses=ledger.responses)` exactly once, immediately after the ledger is loaded and **before** the `ledger.completed` short-circuit.
- A failed turn appends nothing to the log, is recorded against the agent named by `ledger.next_speaker` (not by step parity), and the exception is still re-raised.
- `_transform_conversation_history(target_agent)` maps every ledger message to `{"role": "assistant"}` when its author equals `target.name` and `{"role": "user"}` otherwise — uniformly, with **no special case for a one-message history**. It calls `target.prompt_formatter.create_generic_request({"prompt": <content of the last message>}, 0)`, splits that result into the system message and the rest, replaces the last mapped message with the rest, and inserts the system message at index 0 **only if there is one**; an agent built without `system_prompt=` must not raise. When the formatter produced more than one system message, the first is used and the others stay in place in the body.
- `create_dataset_file(working_dir)` writes one row per log line with exactly four fields: `{"role": <the record's name>, "content": <str(response_message)>, "turn": <0-based line index>, "source": "seed" if index == 0 else "response"}`. `source` is decided by position, not by `finish_reason`. Row order is log order.

### `AgentStatusTracker` (`src/bespokelabs/curator/status_tracker/agent_status_tracker.py`)

- New fields `num_cached: int = 0` and `time_fn: t.Callable[[], float] = field(default=time.time, repr=False, compare=False)`; `start_time` and `last_update_time` come from `time_fn`.
- `update_turn(agent, response_success=False, ...)` increments **only** `num_errors` — `current_turn` and `num_responses` are left alone — while still setting `current_agent` and still accumulating any token/cost arguments given.
- New `adopt_ledger(self, *, cached_responses: int) -> None`: sets `current_turn = cached_responses`, `num_cached = cached_responses`, `num_responses = 0`, `num_errors = 0`, `total_cost = 0.0` and all three `total_tokens` counters to `0`; it does not touch `max_turns` and does not call `update_display`. So `num_responses`/`total_cost` describe *this process*, `num_cached` describes what was inherited, and `current_turn` describes the conversation.
- `stop_tracker()` removes `"time_fn"` from the telemetry metadata dict alongside `"pbar"`.

### `Agent` / `MultiTurnAgents` (`src/bespokelabs/curator/agent/agent.py`)

- `Agent.is_completed(self, response: t.Any) -> bool` currently returns `False` unconditionally, which makes the processor's stop-condition path dead code in every stock use. Give it a real default implementation in terms of `COMPLETION_SENTINEL`.
- `MultiTurnAgents.__init__(self, seeder, partner, max_length, seed_message, *, now_fn: t.Callable[[], datetime.datetime] = datetime.datetime.now)` accepts and forwards `now_fn`.

### `MultiTurnResponse` (`src/bespokelabs/curator/agent/agent_response.py`)

- `update_tracker_stats()` reports `RequestStats(total=tracker.max_turns, succeeded=tracker.num_responses, failed=tracker.num_errors, in_progress=0, cached=tracker.num_cached)`.

### Reuse, scope and dependencies

- Reuse `AgentResponse` and its `model_validate_json`/`model_dump` (the seed is written as an `AgentResponse`, no new record type), `GenericRequest`, `MultiTurnAgenticProcessor.append_response()` verbatim, `PromptFormatter.create_generic_request()` (read, never modified), `AgentTurn`, `_TokenUsage`, `ArrowWriter`/`Dataset.from_file` as already used, and `APIRequest` constructed exactly as today.
- Nothing in `llm/`, `request_processor/`, `client.py`, `db.py` or the viewer changes. `Agent._hash_fingerprint` and the `xxh64(seed_message)` run identity are untouched.
- Python `^3.10`; **no new dependency** — `pydantic`, `datasets`, `aiofiles`, `aiohttp` and stdlib `json`/`os`/`datetime`/`typing` are all already present. Tests use `pytest`, `pytest-asyncio`, `tmp_path`, `monkeypatch` and `types.SimpleNamespace`; no network, no real provider.

## What the team said

Chat, the wiki and internal mail, over the months this area was being worked on, oldest first. Some of it is people thinking aloud and some of it was settled later.

<!-- planted 2026-09-04T21:19:37+00:00 -->

**2025-01-21 · #code-review · emil**

> yup - checkpoint wins on the mismatch, log gets trimmed back to the recorded count and the run carries on. standard resumable-writer behaviour, nothing exotic.

**2025-01-22 · #code-review · dario**

> ok, settled on the sentinel check — we lowercase the whole reply and look for the token anywhere in it, position doesn't matter since agents drop it wherever they like

**2025-02-26 · #pipeline · dario**

> settled on resume semantics: turn_ledger.json is the source of truth, so if the log runs past the recorded response count we truncate it back before the first reqeust.

**2025-03-11 · #cookbooks · konrad**

> Confirming for the docs then: is_completed is a case insensitive substring scan over the whole response, nobody has to get the casing or the placment right.

**2025-03-14 · #code-review · emil**

> trimming the jsonl to the recorded count is gone, it discarded paid turns. the stamp is the "version" key holding TURN_LEDGER_VERSION 2 — missing or below that just gets status adopted, only a version-2 mismatch aborts.

**2025-03-14 · #engineering · nikolai**

> i'd say for the base agent nobody subclassed the done check should just look for the marker we already put in the prompts instead of answerign no forever

**2025-03-17 · #pipeline · nils**

> resumed yesterday's conversation this morning and had to walk the whole jsonl just to work out whose turn it was. the working dir should carry that position, not make you replay the log.

**2025-03-18 · #code-review · dario**

> dropped the lowercasing and the match-anywhere check — partner pasted <<END_OF_CONVERSATION>> mid-sentence explaining the protocol and the run cut off right there. is_completed is now response.rstrip().endswith(COMPLETION_SENTINEL), case-sensitive.

**2025-03-19 · #pipeline · gideon**

> ya so basically I made the first call_single_request blow up and turn_ledger.json is already sitting there at 186 bytes with the newline - responses 0, turns 1, last_author client.

**2025-03-19 · #engineering · dermot**

> yeah ok — next_speaker is nothing more than the partner of last_author, a log ending on client comes back with next_speaker advisor, so nobody has to replay the jsonl

**2025-03-20 · #cookbooks · dario**

> ran the negotiation demo four times today and it burns through the whole budget everytime, even when the partner writes that it has nothing left to add.

**2025-03-21 · #cookbooks · konrad**

> look, I typed it lowercase in the notebook cell and the loop still quit on me. if its a marker then it has to be the marker, capitals included.

**2025-03-24 · #pipeline · nils**

> i wrote read_sidecar for the tests - work dir in, record back as a dict. mine says version 1, responses 2, last_author client, and the 3-line log agrees on both.

**2025-03-24 · #pipeline · dario**

> per-run, yeah - a responses file pins to a record by response count and last author, nothing else. first write carries created, verified is only a load where both matched.

**2025-04-09 · mail: resume against a stale checkpoint — where is it supposed to refuse? · dermot**

> cut the jsonl to three lines, left turn_ledger.json stale - four calls burned before TurnLedgerDesyncError surfaced with recorded_responses 3, recorded_last_author 'advisor'. not one call should have fired, no line appended.

**2025-04-09 · #incidents · dermot**

> on the no-local-record side, ledger.sidecar_state() hands back eight keys — version, responses, turns, last_author, next_speaker, interleave_faults, completed, completion_reason — and i stat whatever write_sidecar hands me, after every append, seed included.

**2025-04-09 · mail: resume when the metadata json isn't on disk · konrad**

> Look, deleted the json by hand to test resume and the rerun refused to start, jsonl sitting there intact. Missing file is benign - we adopt the log, then exactly one call_single_request(advisor, 2).

**2025-04-09 · mail: stop condition in the turn loop — does it assume string content? · dermot**

> late night run — put the json-mode agent through my branch and the stop check threw AttributeError on a dict, killed the run at turn two.

**2025-04-10 · #engineering · gideon**

> ya so basically on WS-050 I pointed verify_sidecar at a turn_ledger.json json.loads chokes on - status adopted, nothing thrown. TurnLedgerDesyncError is the only raise in that module.

**2025-04-10 · mail: stop sequences: what should count as a stop before I normalise across backends · dermot**

> for me it only counts as a stop when the marker is the tail end of what the model said. if it turns up mid-paragraph it is obviously still going.

**2025-04-15 · #code-review · nikolai**

> on 639 though thats not an edge case, with response_format set the reply we pass around is a parsed object rather than text and three of the cookbooks are built that way

**2025-04-16 · #engineering · gideon**

> so basically the agent prompts page has told both agents to end their final message with <<END_OF_CONVERSATION>> since the first demo, and no code has ever looked for it.

**2025-04-22 · mail: what the run metadata says for a run that did not finish · konrad**

> A run I killed at response seven left the json still claiming one response, it only gets written when run() returns. so yes the file lies about the run.

**2025-04-24 · #code-review · dario**

> we dropped truncating the log back to turn_ledger.json, resume binned paid turns. current-version checkpoints disagreeing on responses or last_author raise TurnLedgerDesyncError — a TurnLedgerError, itself just a RuntimeError — before the first request

**2025-04-25 · #code-review · gideon**

> No, we leave the jsonl alone when the two disagree, honestly those lines cost real money and the counters rebuild for free.

**2025-04-25 · #viewer · dario**

> on the disk side - the record gets seeded at submit with completed false and stays false through every append, it only flips true once the run actually finishes

**2025-04-25 · #cookbooks · emil**

> yup — interleave_faults is just counting the spots where the log doubles back on the same author, so a clean client/advisor alternation always rebuilds to 0.

**2025-04-28 · #engineering · gideon**

> ya so basically version 2 checkpoint, responses and last_author both matching — you hand it the work dir and the ledger we rebuilt off the jsonl, comes back status verified, file untouched.

**2025-05-13 · #pipeline · emil**

> honestly half the checkpoints on my box predate TURN_LEDGER_VERSION 2 and don't even carry the same keys - those are stale, not wrong. when a version-2 one does disagree, the error's .path attribute holds that turn_ledger.json path.

**2025-05-13 · wiki: turn_ledger.json — the per-turn ledger artifact · dario**

> turn_ledger.json goes out sort_keys, indent 2, trailing newline - the byte counts in the tests ride on it. key order moved once and every diff went noisy.

**2025-05-13 · mail: resume dies at load after mid-project upgrade · emil**

> yup — the load threw for me too: checkpoint carried interleave_faults from an older build, though response count and last author matched the log exactly. comparing every key is too strict.

**2025-05-13 · wiki: Stop-Marker Matching: What Ends a Generation and What Does Not · nils**

> let me think — two of the providers tack a newline on after the marker, trailing whitespace either side of it doesnt change the match. that should not be what decides whether we stop.

**2025-06-02 · #viewer · konrad**

> Look, it does write mid-run - completion_reason sits at "open" on every write while the run is still going, it only stops saying open once the run actualy ends.

**2025-06-04 · wiki: Weekly sync notes: week of Jun 2 (release + CI) · gideon**

> so basically the working dir gets TURN_LEDGER_FILENAME, turn_ledger.json, holding what we derive off the log — turns is the jsonl line count, seed line included, so responses plus one.

**2025-06-04 · #code-review · konrad**

> Ran four turns on 685: 189 bytes, read_sidecar off the work dir gives version 2, responses 3, turns 4, last_author advisor, next_speaker null, completed true, completion_reason agent_signal

**2025-06-04 · wiki: Weekly sync notes: week of Jun 2 (release + CI) · emil**

> partner spent a turn explaining the protocol, pasted the marker mid-sentence, and the run cut off right there; that message was not an ending.

**2025-06-04 · #engineering · konrad**

> Also, scrap what I confirmed for the docs - is_completed is not a case-insensitve scan over the whole response, it's response.rstrip().endswith(COMPLETION_SENTINEL), exact casing, trailing whitespace ignored, non-str returns False.

**2025-06-11 · #engineering · konrad**

> Look, I passed the work dir in relative and the path handed back still opened from my home dir — absolute either way, /work/agent/turn_ledger.json.

**2025-06-11 · mail: which state files does the resume consistency check actually cover · nikolai**

> TurnLedgerDesyncError out of verify_sidecar on resume, str(exc) came back as /work/agent/turn_ledger.json records 1 response(s) last authored by 'client', the log holds 2 last authored by 'client' — .log_responses and .log_last_author sit on it too.

**2025-06-11 · wiki: Inspecting a finished run without mutating it · nikolai**

> i opened a finished run just to read counters and load_ledger rewrote it under me load_ledger is read the log rebuild in memory verify_sidecar nothing written

**2025-06-11 · mail: prototype run output before we freeze it as the reference transcript · dario**

> honestly i think the prototype transcript stops one message short — whatever the partner said to close things off never made it into the arrow file at all.

**2025-06-12 · wiki: Writing turn-loop tests for the executor against the deterministic fake · gideon**

> so basically budget was 6 and the fake answered three times, so four lines in responses_0.jsonl, the tracker reporting three responses, and the ledger's own responses field at 3 too.

**2025-06-13 · #pipeline · emil**

> yup - verify_sidecar, same module as write_sidecar: fed it a freshly built ledger, status created - first with turn_ledger.json deleted, then nils' version 1 record. adopted both times, nothing written.

**2025-06-13 · #engineering · emil**

> the fake's third reply is "Then index funds. <<END_OF_CONVERSATION>>" and i want that entire string sitting as the content of the last dataset row, role PARTNER.

**2025-06-13 · #releases · dermot**

> yeah ok, re-ran dario's transcript on my branch and the dataset comes out at four rows now, same count as the jsonl log, closing message and all

**2025-06-17 · wiki: Recovering an interrupted agent turn (turn ledger resume path) · nils**

> one of the killed runs left turn_ledger.json half written and json.loads dies on it — we treated it as absent, appended to the intact jsonl, three became four.

**2025-07-02 · wiki: Reading completion_reason in the agent turn ledger · nils**

> let me think through that — a run that ended on the marker did not run out of anything, so completion_reason on the ledger reads "agent_signal", never budget.

**2025-07-10 · #engineering · konrad**

> Look, our TurnLedgerError messages don't end with a full stop - I pasted that one into an assert with the sentence period still attached and lost an hour to the diff.

**2025-12-29 · wiki: Weekly sync notes: week of Jun 2 (release + CI) · konrad**

> look, one thing we did agree on regardless of placement: whatever the check ends up doing, a run should not fall over becuase an agent answered with something that is not text.

**2025-12-29 · #cookbooks · konrad**

> Right, and completed reads True on the ledger for these runs. The agent said it was done, thats a finish, not a run we cut short.

**2025-12-30 · #pipeline · konrad**

> Look, clean work dir, ran it end to end - nothing to load so verify_sidecar never fired, and the ledger came back still carying the status it was built with.


## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>. Your account is `worldadmin`, password `worldadmin`; a token is readable at `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator` and its dependencies are installed in the virtualenv at `$CURATOR_VENV` (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the library and its tests. The library itself is NOT installed there — put your checkout's `src/` on `PYTHONPATH`.
- Complete this ticket to the best of your ability using every source of information you can reach: the repository's own history and issues, the company chat, the wiki, internal mail. Any of them may carry something the ticket does not say.
- Some of what this company decided, it never got round to doing. The history holds designs that were agreed and then parked — "that's its own ticket", "when we get to it" — and parked is not cancelled. Where a decision was settled and the code does not reflect it yet, carrying it out is part of this ticket, not a reason to leave it alone.
- The ticket is where the work starts, not a complete specification of it, and it is not the newest word on anything. It was written short. Where the record settles something the ticket leaves out, or names a field, a value or a behaviour the ticket does not, that is an addition to what you owe — not an earlier draft the ticket has replaced. So the record adds to the ticket. Where the ticket states something outright, that stands — a page that looks like it contradicts the ticket is nearly always about a neighbouring question, and the move is to find what it actually names rather than overrule the ticket with it.
- Chat is at <http://chat.world.local>, the wiki at <http://docs.world.local>, webmail at <http://mail.world.local>, and the service list at <http://pass.world.local>. Gitea and Mattermost want the username `worldadmin`; BookStack and Roundcube want the email `worldadmin@world.local`.
- The wiki has a REST API — `Authorization: Token $(cat /etc/sweworld/bookstack-token)` — and `/api/search?query=...`, `/api/pages/{id}` return JSON, which is easier to read than the HTML.
- Wiki pages carry **comments**, and BookStack's search does not index them — a term that exists only in a comment returns nothing from `/api/search`. `/api/pages/{id}` returns that page's `comments` alongside its body, so a page worth reading is worth fetching whole.
- Mail is readable over **IMAP on `:143`** as `worldadmin@world.local` (password `worldadmin`; plain `imaplib.IMAP4`, plaintext auth is allowed on this port, no TLS handshake needed). The admin mailbox holds a copy of every message in the company, so `SEARCH` and `FETCH` over `INBOX` reach all of it — Roundcube at <http://mail.world.local> is that same mailbox with a browser in front of it, which is harder to read from a shell, not easier.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
