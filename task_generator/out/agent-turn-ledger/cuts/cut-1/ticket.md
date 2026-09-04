# Durable turn ledger for resumable multi-turn agent runs

# The agent turn ledger

Make a resumed multi-turn agent conversation come out identical to one that never restarted, by turning the run directory into a durable, self-describing record of the conversation.

Today `MultiTurnAgenticProcessor` keeps the seed message only in memory, dispatches turns by `step % 2`, overloads one integer as both "message count" and "conversation finished", and re-counts every cached line into the status tracker on resume. Replace that with an explicit ledger value.

### New module `src/bespokelabs/curator/agent/turn_ledger.py`

- Constants: `RESPONSES_FILENAME: str = "responses_0.jsonl"`, `SEED_FINISH_REASON: str = "seed"`, `COMPLETION_REASONS: tuple[str, ...] = ("open", "budget", "agent_signal")`.
- Exceptions: `TurnLedgerError(RuntimeError)`; `TurnLedgerCorruptError(TurnLedgerError)` with `__init__(self, path: str, line_number: int, reason: str)` storing all three as attributes (`line_number` is 1-based over physical lines).
- Frozen dataclasses, exactly these field names in this order:
  - `TurnEntry(turn: int, author: str, content: str, source: str)` — `turn` is the 0-based log index, `author` the agent name the line was written under, `content` the `response_message` coerced with `str()`, `source` is `"seed"` for turn 0 and `"response"` otherwise.
  - `TurnLedger(entries, seeder_name, partner_name, max_responses, responses, turns, next_speaker, last_author, interleave_faults, completed, completion_reason)` — `entries` is a `tuple[TurnEntry, ...]`, never a list; `responses == len(entries) - 1` clamped at 0; `turns == len(entries)`; `next_speaker`/`last_author` are `str | None`. Method `messages() -> list[dict[str, str]]` returning `[{"role": entry.author, "content": entry.content}, ...]` in log order.
- Functions:
  - `build_seed_record(*, seeder_name: str, seed_message: str, model_name: str, now: datetime.datetime) -> AgentResponse`
  - `read_log(working_dir: str) -> list[AgentResponse]`
  - `build_ledger(records, *, seeder_name: str, partner_name: str, max_responses: int, is_completed: t.Callable[[str, t.Any], bool]) -> TurnLedger`
  - `load_ledger(working_dir: str, *, seeder_name: str, partner_name: str, max_responses: int, is_completed: t.Callable[[str, t.Any], bool]) -> TurnLedger` — the read path used by `load_cache`; it does not generate anything.
- The module takes no new dependency and imports neither `time`, `random`, `uuid` nor `os.urandom`; every timestamp it writes arrives as a parameter.

### The seed becomes a durable turn

- When `responses_0.jsonl` is absent or empty, `run()` writes **one line** — the seed — through the existing `append_response()` **before** the first request is built, then enters the loop.
- The seed line is an `AgentResponse` with `name = seeder.name`, `response_message = seed_message`, `finish_reason = "seed"`, `response_cost = 0.0`, `token_usage = None`, `response_errors = None`, `raw_response = None`, `raw_request = None`, `parsed_response_message = None`, `created_at = finished_at = now_fn()`, and `generic_request = GenericRequest(model=seeder.model_name, messages=[{"role": "user", "content": seed_message}], original_row={"prompt": seed_message}, original_row_idx=0, response_format=None, generation_params={}, is_multimodal_prompt=False)`.
- `read_log` skips empty/whitespace-only lines and raises `TurnLedgerCorruptError` for any other unparseable line instead of letting pydantic's `ValidationError` escape.

### `max_length` is a budget of generated responses

- `max_length` counts model-generated responses; the seed is not one. The loop condition is `while ledger.responses < self.max_length`, so an uninterrupted run makes exactly `max_length` calls to `call_single_request` and leaves `max_length + 1` lines in the log — and a run that resumed five times leaves the same.
- `APIRequest(task_id=...)` receives `ledger.responses` (the 0-based response index), not a message-parity step.
- `AgentStatusTracker(max_turns=self.max_length)` is unchanged.

### Turn order comes from the log, not from a parity

- `next_speaker` is the complement of `last_author`: `partner_name if last_author == seeder_name else seeder_name`. An author that is neither name counts as "not the seeder".
- A log where the same author appears twice in a row is legal: it does not raise and does not truncate. Count those adjacencies (indices `i >= 1` with `entries[i].author == entries[i-1].author`) in `interleave_faults` and still hand the turn to the complement of the last author.

### Completion is a flag and a reason

- `completion_reason` is `"agent_signal"` when the **last** entry's author's `is_completed` returns true for that entry's content (checked on the last entry only); otherwise `"budget"` when `responses >= max_responses`; otherwise `"open"`. `"agent_signal"` wins when both hold.
- `completed == (completion_reason != "open")`, and `next_speaker is None` exactly when `completed`. An empty log gives `("open", 0, 0, None, None)` for `(completion_reason, responses, turns, last_author, next_speaker)`.
- `run()` short-circuits on `ledger.completed` — never on a count comparison. The processor passes `is_completed` as a callable that dispatches to the authoring agent's `Agent.is_completed(content)`.

### `processor.py`

- `__init__` gains `now_fn: t.Callable[[], datetime.datetime] = datetime.datetime.now`; the processor keeps the most recently built ledger on `self.ledger: t.Optional[TurnLedger]`.
- `load_cache(working_dir: str) -> TurnLedger` (was `-> int`) and no longer touches the status tracker.
- `self.conversation_history` stays a `list[dict[str, str]]` of `{"role": <agent name>, "content": ...}` and equals `self.ledger.messages()` after every ledger update.
- Add `_agent_for(name: str) -> Agent` mapping a name to seeder or partner, `KeyError` otherwise.
- `_transform_conversation_history(target)` maps each message to `{"role": "assistant"}` when its author is `target.name` and `{"role": "user"}` otherwise — uniformly, with no special case for a one-message history. It then calls `target.prompt_formatter.create_generic_request({"prompt": <content of the last message>}, 0)`, replaces the last mapped message with the formatter's non-system messages, and inserts the system message at index 0 **only if the formatter produced one**; an agent built without `system_prompt=` must yield a system-less request rather than an `IndexError`. If the formatter produced more than one system message, the first is hoisted and the rest stay in the body.
- `create_dataset_file` writes one row per log line with exactly four fields: `{"role": <record name>, "content": str(response_message), "turn": <0-based line index>, "source": "seed" if index == 0 else "response"}`. `source` is decided by position, not by `finish_reason`. Row order is log order.

### `agent_status_tracker.py`

- New fields `num_cached: int = 0` and `time_fn: t.Callable[[], float] = field(default=time.time, repr=False, compare=False)`; `start_time`/`last_update_time` come from `time_fn`.
- `update_turn(agent, response_success=False, ...)` increments **only** `num_errors` — `current_turn` and `num_responses` are left alone — while still setting `current_agent` and still accumulating any token/cost arguments given.
- New `adopt_ledger(*, cached_responses: int)`: sets `current_turn = cached_responses`, `num_cached = cached_responses`, `num_responses = 0`, `num_errors = 0`, `total_cost = 0.0` and all three `total_tokens` counters to `0`; it does not touch `max_turns` and does not call `update_display`. `run()` calls it exactly once, immediately after the ledger is loaded and **before** the `ledger.completed` short-circuit.
- `stop_tracker()` drops `"time_fn"` from the telemetry metadata dict alongside `"pbar"`.
- Nothing is appended to the log for a failed turn, so a retry is the same speaker at the same budget position; `run()` records the failure against the agent named by `ledger.next_speaker` and re-raises.

### `agent.py` / `agent_response.py`

- `MultiTurnAgents.__init__(..., *, now_fn: t.Callable[[], datetime.datetime] = datetime.datetime.now)` accepts and forwards `now_fn`.
- `MultiTurnResponse.update_tracker_stats` fills `RequestStats(total=tracker.max_turns, succeeded=tracker.num_responses, failed=tracker.num_errors, in_progress=0, cached=tracker.num_cached)`.

### Reuse and scope

- Reuse `AgentResponse` and its `model_validate_json`/`model_dump`, `GenericRequest`, `append_response()` verbatim, `AgentTurn`/`_TokenUsage`, `ArrowWriter` + `Dataset.from_file` as already used.
- Nothing in `llm/`, `request_processor/`, `client.py`, `db.py` or the viewer changes. `Agent._hash_fingerprint` and the `xxh64(seed_message)` run identity are out of scope.
- Python `^3.10`; no new dependency. Tests use `pytest`, `pytest-asyncio`, `tmp_path`, `monkeypatch`, `types.SimpleNamespace` — no network.
