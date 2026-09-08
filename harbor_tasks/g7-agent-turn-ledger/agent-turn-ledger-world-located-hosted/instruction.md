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

## Where the conversations are

You do not have to go looking. Every conversation in this company that bears on this ticket is listed below — 51 of them, oldest first — with exactly where it sits.

The list says **where**, and nothing else. It does not say what was said, who was right, which conversations matter most, or how they relate to each other. That is the part left to you: open them, read them together with what is around them, and work out what they mean for this ticket.

Times are the world's own timestamps (UTC), as chat and mail record them.

| # | date | time | where |
|---|---|---|---|
| 1 | 2025-01-21 | 14:02–14:15 | Mattermost `#code-review` — an exchange of 7 messages, opened by **nikolai** |
| 2 | 2025-01-22 | 15:11–15:22 | Mattermost `#code-review` — an exchange of 8 messages, opened by **konrad** |
| 3 | 2025-02-26 | 15:38–15:49 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **dermot** |
| 4 | 2025-03-11 | 14:02–14:11 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **dermot** |
| 5 | 2025-03-14 | 13:22–15:20 | Mattermost `#engineering` — an exchange of 10 messages, opened by **konrad** |
| 6 | 2025-03-14 | 13:38–13:58 | Mattermost `#code-review` — an exchange of 9 messages, opened by **gideon** |
| 7 | 2025-03-17 | 14:02–14:16 | Mattermost `#pipeline` — an exchange of 10 messages, opened by **gideon** |
| 8 | 2025-03-18 | 13:41–14:01 | Mattermost `#code-review` — an exchange of 9 messages, opened by **gideon** |
| 9 | 2025-03-19 | 11:53–12:03 | Mattermost `#engineering` — an exchange of 7 messages, opened by **konrad** |
| 10 | 2025-03-19 | 13:03–13:11 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **gideon** |
| 11 | 2025-03-20 | 13:32–13:46 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **dermot** |
| 12 | 2025-03-21 | 14:09–14:21 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **dario** |
| 13 | 2025-03-24 | 15:02–15:24 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **emil** |
| 14 | 2025-03-24 | 18:30–18:55 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **emil** |
| 15 | 2025-04-09 | 08:12–14:10 | mail thread “resume when the metadata json isn't on disk” — an exchange of 3 messages from **konrad**. In `worldadmin@world.local`'s INBOX |
| 16 | 2025-04-09 | 08:12–13:24 | mail thread “stop condition in the turn loop — does it assume string content?” — an exchange of 3 messages from **dermot**. In `worldadmin@world.local`'s INBOX |
| 17 | 2025-04-09 | 12:43–12:55 | Mattermost `#incidents` — an exchange of 9 messages, opened by **dario** |
| 18 | 2025-04-09 | 13:20–14:52 | mail thread “resume against a stale checkpoint — where is it supposed to refuse?” — an exchange of 3 messages from **dermot**. In `worldadmin@world.local`'s INBOX |
| 19 | 2025-04-10 | 11:06–13:31 | mail thread “stop sequences: what should count as a stop before I normalise across backends” — an exchange of 3 messages from **gideon**. In `worldadmin@world.local`'s INBOX |
| 20 | 2025-04-10 | 16:33–16:48 | Mattermost `#engineering` — an exchange of 7 messages, opened by **dermot** |
| 21 | 2025-04-15 | 12:53–13:07 | Mattermost `#code-review` — an exchange of 6 messages, opened by **dario** |
| 22 | 2025-04-16 | 14:02–14:15 | Mattermost `#engineering` — an exchange of 8 messages, opened by **dermot** |
| 23 | 2025-04-22 | 09:41–15:25 | mail thread “what the run metadata says for a run that did not finish” — an exchange of 4 messages from **konrad**. In `worldadmin@world.local`'s INBOX |
| 24 | 2025-04-24 | 18:28–18:49 | Mattermost `#code-review` — an exchange of 9 messages, opened by **gideon** |
| 25 | 2025-04-25 | 12:29–12:37 | Mattermost `#viewer` — an exchange of 7 messages, opened by **dermot** |
| 26 | 2025-04-25 | 14:06–14:25 | Mattermost `#code-review` — an exchange of 8 messages, opened by **nikolai** |
| 27 | 2025-04-25 | 15:22–15:38 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **nikolai** |
| 28 | 2025-04-28 | 14:22–14:35 | Mattermost `#engineering` — an exchange of 8 messages, opened by **dermot** |
| 29 | 2025-05-13 | 10:30 | the wiki page “turn_ledger.json \u2014 the per-turn ledger artifact” (`docs/engineering/turn-ledger-json-the-per-turn-ledger-artifact.md`) — a **comment** by **dario**, and the page they hang on |
| 30 | 2025-05-13 | 10:42–14:15 | the wiki page “Stop-Marker Matching: What Ends a Generation and What Does Not” (`docs/engineering/stop-marker-matching-what-ends-a-generation-and-what-does-not.md`) — an exchange of 2 **comments** opened by **nils**, and the page they hang on |
| 31 | 2025-05-13 | 13:32–16:20 | mail thread “resume dies at load after mid-project upgrade” — an exchange of 4 messages from **dermot**. In `worldadmin@world.local`'s INBOX |
| 32 | 2025-05-13 | 15:22–15:32 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **dario** |
| 33 | 2025-06-02 | 16:51–17:02 | Mattermost `#viewer` — an exchange of 8 messages, opened by **emil** |
| 34 | 2025-06-04 | 09:14 | the wiki page “Weekly sync notes: week of Jun 2 (release + CI)” (`docs/meetings/weekly-sync-notes-week-of-jun-2-release-ci.md`) — the **page body**, written by **emil**, and the comments on it |
| 35 | 2025-06-04 | 11:26–16:40 | the wiki page “Weekly sync notes: week of Jun 2 (release + CI)” (`docs/meetings/weekly-sync-notes-week-of-jun-2-release-ci.md`) — an exchange of 2 **comments** opened by **gideon**, not the page body |
| 36 | 2025-06-04 | 13:39–13:51 | Mattermost `#code-review` — an exchange of 7 messages, opened by **emil** |
| 37 | 2025-06-04 | 18:31–18:47 | Mattermost `#engineering` — an exchange of 8 messages, opened by **dermot** |
| 38 | 2025-06-11 | 09:42–16:05 | mail thread “prototype run output before we freeze it as the reference transcript” — an exchange of 4 messages from **emil**. In `worldadmin@world.local`'s INBOX |
| 39 | 2025-06-11 | 10:12–11:03 | Mattermost `#engineering` — an exchange of 6 messages, opened by **dermot** |
| 40 | 2025-06-11 | 10:30 | the wiki page “Inspecting a finished run without mutating it” (`docs/engineering/inspecting-a-finished-run-without-mutating-it.md`) — a **comment** by **nikolai**, and the page they hang on |
| 41 | 2025-06-11 | 14:05–16:15 | mail thread “which state files does the resume consistency check actually cover” — an exchange of 4 messages from **nikolai**. In `worldadmin@world.local`'s INBOX |
| 42 | 2025-06-12 | 10:42–15:58 | the wiki page “Writing turn-loop tests for the executor against the deterministic fake” (`docs/engineering/writing-turn-loop-tests-for-the-executor-against-the-deterministic-fake.md`) — an exchange of 2 **comments** opened by **gideon**, and the page they hang on |
| 43 | 2025-06-13 | 13:04–13:22 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 44 | 2025-06-13 | 15:12–15:23 | Mattermost `#releases` — an exchange of 6 messages, opened by **konrad** |
| 45 | 2025-06-13 | 16:31–16:42 | Mattermost `#engineering` — an exchange of 6 messages, opened by **dermot** |
| 46 | 2025-06-17 | 10:30 | the wiki page “Recovering an interrupted agent turn (turn ledger resume path)” (`docs/engineering/recovering-an-interrupted-agent-turn-turn-ledger-resume-path.md`) — a **comment** by **nils**, and the page they hang on |
| 47 | 2025-07-02 | 10:24–14:51 | the wiki page “Reading completion_reason in the agent turn ledger” (`docs/engineering/reading-completion-reason-in-the-agent-turn-ledger.md`) — an exchange of 2 **comments** opened by **nils**, and the page they hang on |
| 48 | 2025-07-10 | 14:12–14:26 | Mattermost `#engineering` — an exchange of 8 messages, opened by **dermot** |
| 49 | 2025-12-29 | 11:14–15:02 | the wiki page “Weekly sync notes: week of Jun 2 (release + CI)” (`docs/meetings/weekly-sync-notes-week-of-jun-2-release-ci.md`) — an exchange of 2 **comments** opened by **konrad**, not the page body |
| 50 | 2025-12-29 | 15:04–15:21 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **nikolai** |
| 51 | 2025-12-30 | 10:09–10:26 | Mattermost `#pipeline` — an exchange of 6 messages, opened by **emil** |

A row gives the window an exchange runs in and how many messages it is — not how much is around it. A busy channel interleaves other talk with it, and a mail thread can have begun earlier and under someone else's name, so read the window and its surroundings rather than counting messages off.

A wiki **comment** is not in the page body and BookStack's search does not index it; `/api/pages/{id}` returns a page's `comments` alongside its text.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
