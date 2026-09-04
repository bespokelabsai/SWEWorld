# The agent turn ledger

## Target

**Files that change**

| Path | Change |
|---|---|
| `src/bespokelabs/curator/agent/turn_ledger.py` | **new module** — the durable conversation record: the seed record, the log reader, the `TurnLedger` value, the `turn_ledger.json` sidecar, the desync/corrupt exception family, the completion vocabulary and the sentinel. |
| `src/bespokelabs/curator/agent/processor.py` | `MultiTurnAgenticProcessor.__init__` gains `now_fn`; `load_cache()` (`:60`) returns a `TurnLedger` instead of an `int` and stops touching the status tracker; `run()` (`:86`) writes the seed to the log, loops on the ledger's `next_speaker` instead of `step % 2`, bounds on *responses*, rewrites the sidecar after each append; `_transform_conversation_history()` (`:171`) survives an agent with no system prompt; `create_dataset_file()` (`:203`) emits four columns. |
| `src/bespokelabs/curator/status_tracker/agent_status_tracker.py` | `num_cached` and `time_fn` fields; `start_time`/`last_update_time` come from `time_fn`; `update_turn()` (`:240`) stops counting a failure as a response; new `adopt_ledger()`; `stop_tracker()` (`:341`) drops `time_fn` from the telemetry payload. |
| `src/bespokelabs/curator/agent/agent.py` | `Agent.is_completed()` (`:40`) implements the sentinel; `MultiTurnAgents.__init__` accepts and forwards `now_fn`. |
| `src/bespokelabs/curator/agent/agent_response.py` | `MultiTurnResponse.update_tracker_stats()` (`:66`) fills `RequestStats.cached` from `tracker.num_cached`. |

Nothing in `llm/`, `request_processor/`, `client.py`, `db.py` or the viewer changes.
`Agent._hash_fingerprint` and the `xxh64(seed_message)` run identity (`agent.py:193-196`) are
**untouched** — out of scope by the brief.

**Existing machinery that may be REUSED**

- `AgentResponse` (`agent/agent_response.py:12`) and its `model_validate_json` / `model_dump` —
  the seed is written as an `AgentResponse` like every other line; no new record type.
- `GenericRequest` (`types/generic_request.py:18`) for the seed record's `generic_request` field.
- `MultiTurnAgenticProcessor.append_response()` (`processor.py:159`) verbatim — `model_dump()`,
  `response["name"] = name`, `json.dumps(response, default=str) + "\n"`. The seed goes through it.
- `PromptFormatter.create_generic_request()` (`llm/prompt_formatter.py:95`) and its
  `_put_system_prompt` behaviour — read, never modified.
- `AgentTurn` (`status_tracker/agent_status_tracker.py:26`), `AgentStatusTracker.update_turn`'s
  token/cost accumulation, `_TokenUsage`.
- `ArrowWriter` (`datasets.arrow_writer`) and `Dataset.from_file` as already used at
  `processor.py:218`/`:151`.
- `APIRequest` (`request_processor/online/base_online_request_processor.py`) — constructed exactly
  as today, only `task_id` changes meaning (P3).
- `pytest`, `pytest-asyncio`, `tmp_path`, `monkeypatch`, `types.SimpleNamespace`.

**What must be BUILT**

- `turn_ledger.py`: constants `TURN_LEDGER_VERSION`, `TURN_LEDGER_FILENAME`, `RESPONSES_FILENAME`,
  `SEED_FINISH_REASON`, `COMPLETION_SENTINEL`, `COMPLETION_REASONS`, `LEDGER_STATUSES`; exceptions
  `TurnLedgerError`, `TurnLedgerCorruptError`, `TurnLedgerDesyncError`; frozen dataclasses
  `TurnEntry`, `TurnLedger`; functions `build_seed_record`, `read_log`, `build_ledger`,
  `read_sidecar`, `write_sidecar`, `verify_sidecar`, `load_ledger`.
- `AgentStatusTracker.adopt_ledger`, `AgentStatusTracker.num_cached`, `AgentStatusTracker.time_fn`.
- `MultiTurnAgenticProcessor.now_fn` and the rewritten `run()` loop.

**Python / dependencies**

Python `^3.10` (verified against 3.10.12). `X | None`, `tuple[str, ...]`, `dict[str, Any]`,
`dataclasses(frozen=True)` and keyword-only `*` parameters are all available; no
`from __future__ import annotations` needed. Everything used is already a dependency:
`pydantic >=2.9.2`, `datasets ^3.0.2`, `aiofiles`, `aiohttp`, stdlib `json`/`os`/`datetime`/`typing`.
**No new dependency.** `turn_ledger.py` imports neither `time`, `random`, `uuid` nor
`os.urandom`; every timestamp it writes arrives as a parameter.

**Latent bugs in this area (all real, with lines)**

1. `processor.py:105` vs `processor.py:69-84` — the seed message is appended to
   `conversation_history` on a fresh run but never written to `responses_0.jsonl`, so a resumed
   run's history is the fresh run's minus its first element. Every role assignment in
   `_transform_conversation_history` shifts by one on resume. Fixed by P2.
2. `processor.py:112` — `step % 2 == 0 → partner` is a parity over a list whose length includes
   the seed on a fresh run and excludes it on a resume, so the same directory can have the same
   agent speak twice in a row across a restart. Fixed by P4.
3. `processor.py:79`/`:83` vs `:84` — `load_cache` returns `self.max_length` both as "this
   conversation finished" and as a plain message count, and `:101` compares the two. A log with
   exactly `max_length` messages and no completion signal is reported as finished. Fixed by P6.
4. `processor.py:110` — `range(start_step, self.max_length)` where `start_step` counts *messages*:
   a resume produces `max_length - len(history)` responses where the fresh run produced
   `max_length`, so the total work done depends on how many times the process restarted.
   Fixed by P3.
5. `processor.py:76-83` — `load_cache` calls `status_tracker.update_turn` once per *cached* line,
   so `num_responses` (reported as `RequestStats.succeeded`, `agent_response.py:89`, and printed as
   "Successful Responses", `agent_status_tracker.py:387`) counts every historical message again on
   every resume and can exceed `RequestStats.total` (= `max_turns`, `agent_response.py:88`).
   Fixed by P8.
6. `agent_status_tracker.py:249-253` — a failed turn increments `current_turn`, `num_responses`
   *and* `num_errors`, so a run of N attempts with E failures reports N successes and E errors,
   N + E > N. Fixed by P7.
7. `processor.py:194` — `[msg for msg in request.messages if msg["role"] == "system"][0]` raises
   `IndexError` for any agent constructed without `system_prompt=`, which the public `Agent`
   constructor happily allows. Fixed by P9.
8. `processor.py:184-185` — the `len(self.conversation_history) == 1` special case labels the seed
   `"user"` regardless of who is being asked; once the seed is durable and the seeder can be the
   first to be prompted after a resume, that is the wrong role. Removed by P9.
9. `agent.py:40-49` — `is_completed` returns `False` unconditionally, making
   `processor.py:78`, `:82` and `_check_stop_condition` (`:153`) dead code in every stock use.
   Fixed by P10.

## The API

### `src/bespokelabs/curator/agent/turn_ledger.py`

```python
"""The durable record of a multi-turn agent conversation."""

import datetime
import json
import os
import typing as t
from dataclasses import dataclass

from bespokelabs.curator.agent.agent_response import AgentResponse
from bespokelabs.curator.types.generic_request import GenericRequest

TURN_LEDGER_VERSION: int = 2
TURN_LEDGER_FILENAME: str = "turn_ledger.json"
RESPONSES_FILENAME: str = "responses_0.jsonl"
SEED_FINISH_REASON: str = "seed"
COMPLETION_SENTINEL: str = "<<END_OF_CONVERSATION>>"
COMPLETION_REASONS: tuple[str, ...] = ("open", "budget", "agent_signal")
LEDGER_STATUSES: tuple[str, ...] = ("created", "adopted", "verified")


class TurnLedgerError(RuntimeError):
    """Base class for every turn-ledger failure."""


class TurnLedgerCorruptError(TurnLedgerError):
    """Raised when a line of responses_0.jsonl cannot be read as an AgentResponse."""

    def __init__(self, path: str, line_number: int, reason: str) -> None:
        self.path: str = path
        self.line_number: int = line_number      # 1-based, counting every physical line
        self.reason: str = reason
        super().__init__(f"{path}:{line_number} is not a valid agent response ({reason})")


class TurnLedgerDesyncError(TurnLedgerError):
    """Raised when turn_ledger.json disagrees with the log it sits beside."""

    def __init__(
        self,
        path: str,
        log_responses: int,
        recorded_responses: int,
        log_last_author: t.Optional[str],
        recorded_last_author: t.Optional[str],
    ) -> None:
        self.path: str = path
        self.log_responses: int = log_responses
        self.recorded_responses: int = recorded_responses
        self.log_last_author: t.Optional[str] = log_last_author
        self.recorded_last_author: t.Optional[str] = recorded_last_author
        super().__init__(
            f"{path} records {recorded_responses} response(s) last authored by "
            f"{recorded_last_author!r}, the log holds {log_responses} last authored by "
            f"{log_last_author!r}"
        )


@dataclass(frozen=True)
class TurnEntry:
    turn: int          # 0-based index into the log; the seed is 0
    author: str        # the agent name the line was written under
    content: str       # response_message, coerced with str() when it is not already a str
    source: str        # "seed" for turn 0, "response" for every other turn


@dataclass(frozen=True)
class TurnLedger:
    entries: tuple[TurnEntry, ...]
    seeder_name: str
    partner_name: str
    max_responses: int
    responses: int                       # len(entries) - 1, never negative
    turns: int                           # len(entries)
    next_speaker: t.Optional[str]        # None iff completed
    last_author: t.Optional[str]         # None iff entries == ()
    interleave_faults: int
    completed: bool
    completion_reason: str               # one of COMPLETION_REASONS
    status: str                          # one of LEDGER_STATUSES

    def messages(self) -> list[dict[str, str]]:
        """[{"role": entry.author, "content": entry.content}, ...] in log order."""

    def sidecar_state(self) -> dict[str, t.Any]:
        """The exact dict written to turn_ledger.json (see P5)."""


def build_seed_record(
    *, seeder_name: str, seed_message: str, model_name: str, now: datetime.datetime
) -> AgentResponse: ...


def read_log(working_dir: str) -> list[AgentResponse]: ...


def build_ledger(
    records: t.Sequence[AgentResponse],
    *,
    seeder_name: str,
    partner_name: str,
    max_responses: int,
    is_completed: t.Callable[[str, t.Any], bool],
    status: str = "verified",
) -> TurnLedger: ...


def read_sidecar(working_dir: str) -> t.Optional[dict[str, t.Any]]: ...


def write_sidecar(working_dir: str, ledger: TurnLedger) -> str:
    """Writes TURN_LEDGER_FILENAME; returns its absolute path."""


def verify_sidecar(working_dir: str, ledger: TurnLedger) -> TurnLedger:
    """Returns `ledger` with `status` set to "verified" or "adopted"; raises TurnLedgerDesyncError."""


def load_ledger(
    working_dir: str,
    *,
    seeder_name: str,
    partner_name: str,
    max_responses: int,
    is_completed: t.Callable[[str, t.Any], bool],
) -> TurnLedger:
    """read_log + build_ledger + verify_sidecar. Never writes."""
```

### `src/bespokelabs/curator/agent/processor.py`

```python
class MultiTurnAgenticProcessor:
    def __init__(
        self,
        seeder: "Agent",
        partner: "Agent",
        max_length: int,
        seed_message: str,
        now_fn: t.Callable[[], datetime.datetime] = datetime.datetime.now,
    ) -> None:
        self.seeder = seeder
        self.partner = partner
        self.max_length = max_length          # a budget of generated responses (P3)
        self.seed_message = seed_message
        self.now_fn = now_fn
        self.conversation_history: list[dict[str, str]] = []
        self.ledger: t.Optional[TurnLedger] = None
        self.status_tracker = AgentStatusTracker(...)   # max_turns=self.max_length, unchanged

    def load_cache(self, working_dir: str) -> TurnLedger: ...
    async def run(self, working_dir: str) -> Dataset: ...
    async def append_response(self, name: str, f, response: GenericResponse) -> None: ...   # unchanged
    def _transform_conversation_history(self, target_agent: "Agent") -> GenericRequest: ...
    def create_dataset_file(self, working_dir: str) -> str: ...
    def _agent_for(self, name: str) -> "Agent": ...   # name -> seeder|partner, KeyError otherwise
```

`self.conversation_history` remains a `list[dict[str, str]]` with keys `"role"` (an agent *name*)
and `"content"`, and is always `self.ledger.messages()` after every ledger update.

### `src/bespokelabs/curator/status_tracker/agent_status_tracker.py`

```python
@dataclass
class AgentStatusTracker:
    ...
    num_cached: int = 0
    start_time: float = 0.0
    last_update_time: float = 0.0
    time_fn: t.Callable[[], float] = field(default=time.time, repr=False, compare=False)

    def update_turn(self, agent: AgentTurn, response_success: bool = True,
                    token_usage: t.Optional[_TokenUsage] = None,
                    cost: t.Optional[float] = None) -> None: ...

    def adopt_ledger(self, *, cached_responses: int) -> None: ...
```

### `src/bespokelabs/curator/agent/agent.py`

```python
class Agent(curator.LLM):
    def is_completed(self, response: t.Any) -> bool: ...

class MultiTurnAgents:
    def __init__(self, seeder: Agent, partner: Agent, max_length: int, seed_message: str,
                 *, now_fn: t.Callable[[], datetime.datetime] = datetime.datetime.now) -> None: ...
```

### `src/bespokelabs/curator/agent/agent_response.py`

```python
self.request_stats = RequestStats(
    total=tracker.max_turns,
    succeeded=tracker.num_responses,
    failed=tracker.num_errors,
    in_progress=0,
    cached=tracker.num_cached,
)
```

## Parts

### P1 — The `turn_ledger` module surface

**Behaviour.** The record lives in one new module `bespokelabs/curator/agent/turn_ledger.py`
exporting exactly the names above. `TurnEntry` and `TurnLedger` are **frozen dataclasses** — not
pydantic models, not `NamedTuple`s, not dicts — with the field orders given:
`TurnEntry(turn, author, content, source)` and `TurnLedger(entries, seeder_name, partner_name,
max_responses, responses, turns, next_speaker, last_author, interleave_faults, completed,
completion_reason, status)`. `entries` is a `tuple`, never a `list`. `TurnLedgerCorruptError` and
`TurnLedgerDesyncError` both subclass `TurnLedgerError`, which subclasses `RuntimeError`.
`MultiTurnAgenticProcessor.load_cache` returns a `TurnLedger` and the processor keeps the last one
built on `self.ledger`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep it all in `processor.py` next to `load_cache` — that is where the logic is today, the
   module is only 230 lines, and a new file for a resume cursor looks like over-engineering.
2. Keep `load_cache -> int` and add a second method or an out-parameter (`self._finished = True`)
   for the completed flag: the smallest diff that unpicks the overloaded sentinel, and it leaves
   every caller of `load_cache` compiling.
3. Make `TurnLedger` a pydantic `BaseModel` — `AgentResponse`, `GenericRequest` and
   `GenericResponse` in this package are all pydantic, `model_dump_json()` would give the sidecar
   for free, and `MultiTurnResponse`/`AgentStatusTracker` are mutable dataclasses, so a frozen one
   is against the local grain.

**The observable.**
`from bespokelabs.curator.agent.turn_ledger import TURN_LEDGER_VERSION, TURN_LEDGER_FILENAME, SEED_FINISH_REASON, COMPLETION_SENTINEL, COMPLETION_REASONS, LEDGER_STATUSES, TurnEntry, TurnLedger, TurnLedgerError, TurnLedgerCorruptError, TurnLedgerDesyncError, build_seed_record, read_log, build_ledger, read_sidecar, write_sidecar, verify_sidecar, load_ledger`
imports cleanly;
`TURN_LEDGER_VERSION == 2`; `TURN_LEDGER_FILENAME == "turn_ledger.json"`;
`COMPLETION_REASONS == ("open", "budget", "agent_signal")`;
`LEDGER_STATUSES == ("created", "adopted", "verified")`;
`[f.name for f in dataclasses.fields(TurnEntry)] == ["turn", "author", "content", "source"]`;
`[f.name for f in dataclasses.fields(TurnLedger)] == ["entries", "seeder_name", "partner_name", "max_responses", "responses", "turns", "next_speaker", "last_author", "interleave_faults", "completed", "completion_reason", "status"]`;
`isinstance(ledger.entries, tuple)`;
`pytest.raises(dataclasses.FrozenInstanceError)` on `ledger.responses = 9`;
`issubclass(TurnLedgerCorruptError, TurnLedgerError) and issubclass(TurnLedgerDesyncError, TurnLedgerError) and issubclass(TurnLedgerError, RuntimeError)`;
`isinstance(processor.load_cache(str(tmp_path)), TurnLedger)`.

**Arbitrary:** invented name — the module path, two dataclass names, three exception names, twelve
`TurnLedger` field names and two vocabularies. Nothing in the repository hints at any of them.

### P2 — The seed is a durable turn, written before anything is asked

**Behaviour.** When `responses_0.jsonl` does not exist (or exists and is empty), `run()` writes
**one line** — the seed — through the existing `append_response()` before the first request is
built, and only then enters the loop. The line is `build_seed_record(...)`, an `AgentResponse`
with `name = seeder.name`, `response_message = seed_message`, `finish_reason = "seed"`,
`response_cost = 0.0`, `token_usage = None`, `response_errors = None`, `raw_response = None`,
`raw_request = None`, `parsed_response_message = None`, `created_at = finished_at = now_fn()`, and
`generic_request = GenericRequest(model=seeder.model_name, messages=[{"role": "user", "content":
seed_message}], original_row={"prompt": seed_message}, original_row_idx=0, response_format=None,
generation_params={}, is_multimodal_prompt=False)`. `read_log` skips lines that are empty or
whitespace-only and raises `TurnLedgerCorruptError(path, line_number, reason)` — `line_number`
1-based over physical lines — for any other unparseable line, instead of letting pydantic's
`ValidationError` out.

**Alternatives a competent engineer would plausibly choose instead.**
1. Leave the seed out of the log entirely (today's behaviour) and instead re-derive it on resume
   from `self.seed_message`, which the processor already holds — no new record type, no synthetic
   response, and the log keeps its meaning of "things the API returned".
2. Persist the seed, but in its own file (`seed.json`) or as a header line with a distinguishing
   schema, so that `responses_0.jsonl` still contains only real responses and
   `create_dataset_file`/`AgentResponse.model_validate_json` need no synthetic fields.
3. Write it as an `AgentResponse` but with `finish_reason=None` and `response_cost=None` (the
   pydantic defaults), since inventing a fake finish reason pollutes a provider-supplied field.

**The observable.** Fresh run in an empty `tmp_path`, seeder `"client"`, model `"gpt-4o-mini"`,
`now_fn` returning `datetime(2025, 1, 2, 3, 4, 5)`, and a fake `call_single_request` that raises
`_Stop` on its first call:
`pytest.raises(_Stop)`, then `len(open(tmp_path/"responses_0.jsonl").read().splitlines()) == 1`;
`rec = AgentResponse.model_validate_json(that line)` gives
`rec.name == "client"`, `rec.response_message == seed_message`, `rec.finish_reason == "seed"`,
`rec.response_cost == 0.0`, `rec.token_usage is None`, `rec.raw_response is None`,
`rec.created_at == rec.finished_at == datetime(2025, 1, 2, 3, 4, 5)`,
`rec.generic_request.messages == [{"role": "user", "content": seed_message}]`,
`rec.generic_request.original_row == {"prompt": seed_message}`,
`rec.generic_request.original_row_idx == 0`;
and the fake's call count is `1` (the seed is written *before* the first request, not after it).
Corrupt case: a log whose lines are `[valid, "", "{not json"]` →
`pytest.raises(TurnLedgerCorruptError)` with `exc.value.line_number == 3`.

**Arbitrary:** deliberate departure + chosen value — the surrounding code deliberately never writes
the seed (`processor.py:105` appends it to memory only), and `finish_reason == "seed"` /
`response_cost == 0.0` are values nothing in the repo suggests.

### P3 — `max_length` is a budget of generated responses, not of messages

**Behaviour.** `max_length` counts **model-generated responses**. The seed is not one. A run that
is never stopped early therefore performs exactly `max_length` calls to `call_single_request` and
leaves `max_length + 1` lines in `responses_0.jsonl`, whether it ran in one process or resumed
five times: the loop condition is `while ledger.responses < self.max_length`, and
`ledger.responses == len(entries) - 1`. `AgentStatusTracker(max_turns=self.max_length)` is
unchanged, so the progress bar's unit is now the same as the budget's. `APIRequest(task_id=...)`
is given `ledger.responses` (0-based response index), not the old message-parity `step`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep `max_length` as a bound on total messages, seed included — this is what
   `processor.py:110` does today and what `tests/integrations/test_agent.py:56`
   (`max_length=4` → `len(result.dataset) == 4`) asserts, so it is the documented status quo.
2. Read it as "turns each", i.e. `max_length` responses per agent and `2 * max_length` in total —
   `test_agent.py:50` literally comments `max_length=4,  # 2 turns each`, and `agent.py:78`
   calls it "the maximum number of turns in the conversation".
3. Read it as exchanges (seeder+partner pairs) and stop after `max_length` complete pairs,
   refusing to end a conversation on a half-exchange.

**The observable.** Fake `call_single_request` counting calls, `max_length = 4`, `is_completed`
never true:
fresh run → call count `4`, `len(log lines) == 5`, `ledger.responses == 4`, `ledger.turns == 5`,
`tracker.current_turn == 4`, `tracker.max_turns == 4`;
then delete nothing, truncate the log to its first 3 lines, rewrite the sidecar to match, and run
again → the second process makes `2` further calls (not `1`, not `4`), ending again at
`len(log lines) == 5`;
and across the two processes the *sum* of calls for the same directory is `4 + 2`, i.e. the log
never exceeds `max_length + 1 == 5` lines.
`task_id` values seen by the fake on the fresh run are `[0, 1, 2, 3]`.

**Arbitrary:** deliberate departure — the existing integration test pins the opposite reading, and
alternative 2 is written in a comment in that same test.

### P4 — Whose turn it is comes from the log's last author, never from an index parity

**Behaviour.** `next_speaker` is the agent that did **not** write the last entry:
`partner_name if last_author == seeder_name else seeder_name`. It is never computed from
`len(entries) % 2` or from a step counter. A log in which the same author appears twice in a row is
**legal** — it is not an error, it does not truncate the log, and it does not raise; the ledger
counts such adjacencies in `interleave_faults` (the number of indices `i >= 1` with
`entries[i].author == entries[i - 1].author`) and still hands the next turn to the complement of
the last author. An entry whose author is neither `seeder_name` nor `partner_name` is treated as
"not the seeder", i.e. `next_speaker` becomes `seeder_name`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the parity dispatch and just fix its phase for the now-durable seed: even index → seeder,
   odd → partner. It is a one-character change to `processor.py:112`, it is correct for every log
   the code itself can produce, and it keeps `step` meaningful as `task_id`.
2. Keep parity but off the *response* count rather than the message count
   (`responses % 2 == 0 → partner`), which is the same edit expressed against the new budget.
3. Treat a repeated author as corruption and raise (or drop the duplicate line), on the grounds
   that a log which cannot have been produced by this loop should not be resumed silently.

**The observable.** Three hand-written logs, seeder `"client"`, partner `"advisor"`,
`max_responses = 9`, `is_completed` never true:
authors `["client"]` → `next_speaker == "advisor"`, `interleave_faults == 0`, `responses == 0`;
authors `["client", "advisor", "client"]` → `next_speaker == "advisor"`, `interleave_faults == 0`,
`last_author == "client"`, `responses == 2`;
authors `["client", "advisor", "advisor"]` → `next_speaker == "client"`,
`interleave_faults == 1`, `last_author == "advisor"`, `responses == 2`, and **no exception**.
The second and third logs have the same length, so no parity rule of either phase can produce
`"advisor"` for one and `"client"` for the other.

**Arbitrary:** policy with no local evidence — the code's only rule is parity; that a
non-alternating log is legal, is counted rather than repaired, and still alternates from its last
author is a decision nothing in the repository records.

### P5 — `turn_ledger.json`: written every append, and only three ways to read it

**Behaviour.** Beside the log sits `turn_ledger.json`, written by
`json.dumps(ledger.sidecar_state(), indent=2, sort_keys=True) + "\n"` immediately after the seed
line and again after **every** appended response — never batched to the end of the run.
`sidecar_state()` is exactly eight keys:
`{"version": TURN_LEDGER_VERSION, "responses": int, "turns": int, "last_author": str | None,
"next_speaker": str | None, "interleave_faults": int, "completed": bool,
"completion_reason": str}`. On load, `verify_sidecar` has exactly three arms:
(a) the file is absent, or unreadable as JSON, or its `"version"` is not `TURN_LEDGER_VERSION` →
`status = "adopted"`, no error, and the file is rewritten from the log on the next append;
(b) the version matches **and** both `"responses"` and `"last_author"` equal the log-derived
values → `status = "verified"`;
(c) the version matches and either differs → `TurnLedgerDesyncError`. The log wins in (a); nothing
in the log is ever rewritten from the sidecar.

**Alternatives a competent engineer would plausibly choose instead.**
1. No sidecar at all — the log is append-only and self-describing, so a second file is a second
   thing that can be wrong; rebuild everything from `responses_0.jsonl` (this is the design the
   current `load_cache` half-implements).
2. Keep the sidecar as the authority (a cursor persisted alongside) and trust it over the log when
   they differ, truncating or ignoring log lines beyond the cursor — the usual resumable-writer
   pattern, since the cursor is written after a successful append.
3. Write the sidecar once at the end of `run()`, or on the `stop_tracker()` path, which is one
   write instead of N and is what "checkpoint" usually means.

**The observable.** Fresh run, `now_fn` fixed, fake raising `_Stop` on its first call: the file
`tmp_path/"turn_ledger.json"` exists at that moment with byte length **186** and content exactly

```json
{
  "completed": false,
  "completion_reason": "open",
  "interleave_faults": 0,
  "last_author": "client",
  "next_speaker": "advisor",
  "responses": 0,
  "turns": 1,
  "version": 2
}
```
(trailing `"\n"` included in the 186).
Then, against a 3-line log whose authors are `["client", "advisor", "client"]`:
sidecar deleted → `load_ledger(...).status == "adopted"`;
sidecar `{"version": 1, "responses": 2, "last_author": "client"}` → `status == "adopted"`;
sidecar with `version=2, responses=2, last_author="client"` (plus the other five keys) →
`status == "verified"`;
sidecar with `version=2, responses=1, last_author="client"` →
`pytest.raises(TurnLedgerDesyncError)` with `exc.value.log_responses == 2`,
`exc.value.recorded_responses == 1`, `exc.value.log_last_author == "client"`,
`exc.value.recorded_last_author == "client"`;
sidecar with `version=2, responses=2, last_author="advisor"` → `TurnLedgerDesyncError` with
`exc.value.log_last_author == "client"` and `exc.value.recorded_last_author == "advisor"`.

**Arbitrary:** invented name + policy with no local evidence — the filename, the eight keys, the
`sort_keys=True, indent=2` spelling, `TURN_LEDGER_VERSION == 2`, and the three-arm rule in which a
*missing or old-version* sidecar is benign while a *disagreeing current-version* one is fatal.

### P6 — Completion is a flag and a reason, not an integer sentinel

**Behaviour.** `TurnLedger` reports `completed: bool` and `completion_reason: str`, and `run()`
short-circuits on `ledger.completed`, never on `start_step == self.max_length`.
`completion_reason` is `"agent_signal"` when the **last** entry's author's `is_completed` returns
true for its content (checked only on the last entry, not on every entry); otherwise `"budget"`
when `responses >= max_responses`; otherwise `"open"`. `completed` is `completion_reason != "open"`,
and `next_speaker is None` exactly when `completed` is true. `"agent_signal"` beats `"budget"` when
both hold. An empty log gives `("open", 0, 0, None, None)` for
`(completion_reason, responses, turns, last_author, next_speaker)` with `completed is False`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the integer contract and make the sentinel unambiguous instead — return `-1`, or
   `max_length + 1`, or `None`, for "finished". Minimal change, no new vocabulary, every caller
   still does one comparison.
2. Report completion as a bool alone and let the caller ask why, or reuse the last record's
   `finish_reason` (`"stop"`, `"length"`, …) as the reason string rather than minting a
   three-word vocabulary.
3. Scan every entry for the completion signal rather than only the last, so that a signal followed
   by a stray line still counts as finished.

**The observable.** `max_responses = 4`, `is_completed` = "content ends with the sentinel":
log authors `["client", "advisor", "client"]`, none signalling →
`(completed, completion_reason, next_speaker) == (False, "open", "advisor")`;
log of 5 lines (seed + 4 responses), none signalling →
`(True, "budget", None)`;
log of 3 lines whose last content ends with the sentinel →
`(True, "agent_signal", None)`;
log of 5 lines whose last content ends with the sentinel →
`(True, "agent_signal", None)` — `"agent_signal"`, not `"budget"`;
log of 5 lines where the *third* line signals but the fifth does not →
`(True, "budget", None)`;
empty log → `(False, "open", None)` with `turns == 0`, `responses == 0`.
Resuming a directory whose ledger is `completed` makes `0` calls to `call_single_request` and
returns a dataset of `len(log lines)` rows.

**Arbitrary:** invented name + policy — the three-word reason vocabulary, the precedence of
`"agent_signal"` over `"budget"`, and last-entry-only checking.

### P7 — A failed turn does not consume the budget

**Behaviour.** `update_turn(agent, response_success=False, ...)` increments **only** `num_errors`;
`current_turn` and `num_responses` are left alone, and token/cost arguments are still accumulated
if given. `current_agent` is still set to `agent`. Nothing is appended to `responses_0.jsonl` for a
failed turn, so the ledger's `responses` does not move and the retry (in a later process) is the
same speaker at the same budget position. `run()` keeps re-raising the exception after recording
it, and it records the failure against the agent named by `ledger.next_speaker` — not by step
parity.

**Alternatives a competent engineer would plausibly choose instead.**
1. Leave `update_turn` as it is (`agent_status_tracker.py:249-253`): a turn was attempted, so
   `current_turn` advances and `num_responses` counts the attempt — the field is called
   *responses*, not *successes*, and the progress bar should move.
2. Advance `current_turn` but not `num_responses`, so the budget is consumed by an attempt while
   the success count stays honest — the reading that makes `num_responses + num_errors ==
   current_turn`.
3. Rename nothing but subtract: keep the triple increment and report
   `succeeded = num_responses - num_errors` in `MultiTurnResponse`.

**The observable.** A tracker with `max_turns=4` (rich display disabled):
`update_turn(AgentTurn.PARTNER)` then `update_turn(AgentTurn.SEEDER, response_success=False)` then
`update_turn(AgentTurn.PARTNER)` →
`(current_turn, num_responses, num_errors) == (2, 2, 1)`, `current_agent is AgentTurn.PARTNER`.
End to end: fake `call_single_request` that raises `RuntimeError("boom")` on its second call, log
seeded, `max_length=4` → `pytest.raises(RuntimeError)`;
`len(log lines) == 2` (seed + one response); `tracker.current_turn == 1`;
`tracker.num_responses == 1`; `tracker.num_errors == 1`;
the sidecar on disk still reads `{"responses": 1, "last_author": "advisor",
"next_speaker": "client", ...}`;
and the failure was recorded against `AgentTurn.SEEDER` (the ledger's `next_speaker` at the moment
of the raise), where the dispatch expression still in `processor.py:112`
(`len(conversation_history) % 2 == 0 -> partner`, here `2 % 2 == 0`) would have said
`AgentTurn.PARTNER`.

**Arbitrary:** deliberate departure — the code in front of the engineer increments all three
counters in five consecutive lines, and every display string treats `num_responses` as the number
of turns taken.

### P8 — A resume adopts the past; it never re-counts it

**Behaviour.** `load_cache` does not touch the status tracker at all. `run()` calls
`status_tracker.adopt_ledger(cached_responses=ledger.responses)` exactly once, immediately after
the ledger is loaded and **before** the `ledger.completed` short-circuit. `adopt_ledger` sets
`current_turn = cached_responses`, `num_cached = cached_responses`, `num_responses = 0`,
`num_errors = 0`, `total_cost = 0.0` and all three `total_tokens` counters to `0`; it does not
touch `max_turns` and does not call `update_display`. So `num_responses` and `total_cost` describe
*this process*, `num_cached` describes what was inherited, and `current_turn` describes the
conversation. `MultiTurnResponse.update_tracker_stats` reports
`RequestStats(total=tracker.max_turns, succeeded=tracker.num_responses, failed=tracker.num_errors,
in_progress=0, cached=tracker.num_cached)`. `stop_tracker()` removes `"time_fn"` from the telemetry
metadata dict alongside `"pbar"`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep calling `update_turn` per cached line (today's `load_cache`, `:77`/`:81`), which is the
   only way `current_turn` ends up right at all without a new method, and leave `cached=0` as the
   comment at `agent_response.py:92` says.
2. Fold the cached work into the live totals deliberately — `num_responses` becomes "responses in
   this conversation", which is what a user reading "Successful Responses: 7" after a resume
   probably expects, and set `cached` from a separate counter only.
3. Leave `current_turn` at `0` on resume and let the bar fill from zero, since nothing was
   generated yet in this process.

**The observable.** A 3-line log (seed + 2 responses), `max_length = 6`, fake returning canned
responses, `is_completed` never true:
after `run()`, `(max_turns, current_turn, num_responses, num_cached, num_errors) ==
(6, 6, 4, 2, 0)` and the fake was called `4` times;
immediately after `adopt_ledger` (i.e. with a fake that raises `_Stop` on its first call),
`(current_turn, num_responses, num_cached) == (2, 0, 2)` and `total_cost == 0.0`;
resuming a *completed* 5-line log → `request_stats == RequestStats(total=4, succeeded=0, failed=0,
in_progress=0, cached=4)`;
and with `telemetry_client.capture` monkeypatched, the captured `metadata` satisfies
`"time_fn" not in metadata`, `"pbar" not in metadata`, `metadata["num_cached"] == 2`.

**Arbitrary:** invented name + policy — `adopt_ledger`, the field name `num_cached`, and the split
in which `num_responses` is per-process while `current_turn` is per-conversation.

### P9 — An agent with no system prompt is a conversation, not an `IndexError`

**Behaviour.** `_transform_conversation_history(target)` maps every ledger message to
`{"role": "assistant"}` when its author equals `target.name` and `{"role": "user"}` otherwise —
uniformly, with **no special case for a one-message history**. It then calls
`target.prompt_formatter.create_generic_request({"prompt": <content of the last message>}, 0)`,
partitions the result's messages into the system message and the rest, replaces the last mapped
message with that rest, and inserts the system message at index 0 **only if there is one**. When
the formatter produced no system message the request simply has none, and no exception is raised;
when it produced more than one, the first is used and the others stay in place in the body.

**Alternatives a competent engineer would plausibly choose instead.**
1. Raise a clear error (`ValueError("agent 'client' has no system prompt")`) instead of quietly
   producing a system-less request — the current `[...][0]` shows the author assumed a system
   prompt exists, and failing loudly beats sending a differently-shaped request.
2. Substitute a default system message (e.g. `f"You are {target.name}."` or `""`) so every request
   has the same shape and provider adapters that index `messages[0]` keep working.
3. Keep the `len(history) == 1` special case at `processor.py:184`, since the seed is addressed to
   the partner and "the first message is always a user message" is a defensible rule.

**The observable.** History `[{"role": "client", "content": "S"}, {"role": "advisor", "content":
"A"}, {"role": "client", "content": "B"}]`, formatter whose `prompt_func` returns
`[{"role": "user", "content": row["prompt"]}]`:
target `advisor` **with** `system_prompt="You are the advisor."` →
`req.messages == [{"role": "system", "content": "You are the advisor."}, {"role": "user",
"content": "S"}, {"role": "assistant", "content": "A"}, {"role": "user", "content": "B"}]`
(`len == 4`);
target `advisor` **without** a system prompt → the same list minus its first element (`len == 3`),
`[m["role"] for m in req.messages] == ["user", "assistant", "user"]`, and **no** `IndexError`;
single-entry history `[{"role": "client", "content": "S"}]` with target `client` and no system
prompt → `req.messages == [{"role": "user", "content": "S"}]` — one message, produced by the
formatter, with the mapped `"assistant"` copy of the seed deleted as the last entry.

**Arbitrary:** policy with no local evidence — the code raises today, so *something* must be
chosen; that the choice is "omit it silently" rather than "raise" or "synthesise a default" is not
recoverable from the file.

### P10 — The default completion signal

**Behaviour.** `Agent.is_completed(response)` returns `True` iff `response` is a `str` whose
right-stripped form ends with `COMPLETION_SENTINEL == "<<END_OF_CONVERSATION>>"`. Matching is
case-sensitive, suffix-only (a sentinel in the middle of a message does not end the conversation),
and insensitive to trailing whitespace. Any non-`str` `response_message` — the structured-output
`dict`, or `None` — returns `False` rather than raising. The message that carries the sentinel is
still a real turn: it is appended to the log, counted in `responses`, counted by `update_turn`, and
included in the dataset; the conversation stops *after* it.

**Alternatives a competent engineer would plausibly choose instead.**
1. Leave `is_completed` returning `False` (today's body) and treat it purely as a subclass hook —
   the docstring says "Check if the agent's response signals conversation completion" and the base
   class has no business inventing a protocol token.
2. Pick a different, equally plausible token or rule: `"[END]"`, `"<END>"`, `"TERMINATE"` (the
   AutoGen convention), `"DONE"`, or a substring test anywhere in the message rather than a suffix.
3. Drop the terminating message from the log or from the dataset, on the grounds that it is a
   control signal and not conversational content.

**The observable.** With `A = Agent(name="client", model_name="gpt-4o-mini", ...)`:
`A.is_completed("all set <<END_OF_CONVERSATION>>") is True`;
`A.is_completed("all set <<END_OF_CONVERSATION>>  \n") is True`;
`A.is_completed("<<END_OF_CONVERSATION>> but wait") is False`;
`A.is_completed("all set <<end_of_conversation>>") is False`;
`A.is_completed("all set") is False`;
`A.is_completed({"text": "<<END_OF_CONVERSATION>>"}) is False`;
`A.is_completed(None) is False`.
End to end with `max_length = 6` and a fake whose third response is
`"Then index funds. <<END_OF_CONVERSATION>>"`: the fake is called `3` times,
`len(log lines) == 4`, `tracker.num_responses == 3`, `ledger.completion_reason == "agent_signal"`,
and the dataset's last row's `content` is `"Then index funds. <<END_OF_CONVERSATION>>"`.

**Arbitrary:** chosen value + invented name — `"<<END_OF_CONVERSATION>>"` and the
suffix/rstrip/case rules exist nowhere in the repository.

### P11 — The dataset carries the seed, and says which row it is

**Behaviour.** `create_dataset_file` reads `responses_0.jsonl` and writes one row per line with
exactly four fields: `{"role": <the record's name>, "content": <str(response_message)>,
"turn": <0-based line index>, "source": "seed" if index == 0 else "response"}`. `source` is decided
by position, not by `finish_reason`. Row order is log order. The seed is row `0`, so a completed
conversation of `max_length` responses yields `max_length + 1` rows.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the two-column `{"content", "role"}` shape at `processor.py:223` — it is what the public
   integration test inspects (`test_agent.py:61-62`) and adding columns is a breaking change to
   anything that does `df.values.tolist()` (as `test_agent.py:58` does).
2. Add an index column but name it `"step"`, `"index"`, `"turn_index"` or `"idx"`, 1-based, and
   skip `source` entirely — the seed is identifiable as row 0 anyway.
3. Derive `source` from `finish_reason == "seed"` rather than from the position, which is the more
   "semantic" reading now that P2 stamps the record.

**The observable.** After the end-to-end run below,
`set(dataset.column_names) == {"role", "content", "turn", "source"}`;
`len(dataset) == 4`;
`dataset[0] == {"role": "client", "content": "I need help with my investment strategy. What should I do?", "turn": 0, "source": "seed"}`;
`dataset[1]["source"] == "response"` and `dataset[1]["turn"] == 1`;
`[r["turn"] for r in dataset] == [0, 1, 2, 3]`;
`[r["source"] for r in dataset] == ["seed", "response", "response", "response"]`;
and for a hand-written log whose **second** line carries `finish_reason == "seed"`,
`dataset[1]["source"] == "response"` (position decides, not the field).

**Arbitrary:** invented name + deliberate departure — the field names `"turn"`/`"source"`, the
value `"seed"`, and a row count that contradicts the assertion currently in
`tests/integrations/test_agent.py:56`.

## End to end

**Inputs.** No network, no real provider, no event-loop tricks beyond `asyncio.run`.

```python
import asyncio, datetime, json
from types import SimpleNamespace
from bespokelabs.curator.agent.processor import MultiTurnAgenticProcessor
from bespokelabs.curator.agent.turn_ledger import load_ledger, read_sidecar
from bespokelabs.curator.llm.prompt_formatter import PromptFormatter
from bespokelabs.curator.types.generic_response import GenericResponse
from bespokelabs.curator.types.token_usage import _TokenUsage

CLOCK = datetime.datetime(2025, 1, 2, 3, 4, 5)
SEED = "I need help with my investment strategy. What should I do?"
SENTINEL = "<<END_OF_CONVERSATION>>"
REPLIES = ["Start with your goals.",
           "My goal is retirement in 20 years.",
           f"Then index funds. {SENTINEL}"]

calls = []

def fake_agent(name, system_prompt):
    pf = PromptFormatter(model_name="gpt-4o-mini",
                         prompt_func=lambda row: [{"role": "user", "content": row["prompt"]}],
                         parse_func=None, system_prompt=system_prompt)
    async def call_single_request(request, session, status_tracker=None):
        calls.append((name, request.task_id))
        return GenericResponse(response_message=REPLIES[len(calls) - 1], raw_response=None,
                               generic_request=request.generic_request,
                               created_at=CLOCK, finished_at=CLOCK,
                               token_usage=_TokenUsage(input=10, output=5, total=15),
                               response_cost=0.001, finish_reason="stop")
    rp = SimpleNamespace(create_api_specific_request_online=lambda r: {"model": "gpt-4o-mini"},
                         call_single_request=call_single_request)
    return SimpleNamespace(name=name, model_name="gpt-4o-mini", prompt_formatter=pf,
                           _request_processor=rp,
                           is_completed=lambda r: isinstance(r, str)
                                                  and r.rstrip().endswith(SENTINEL))

seeder  = fake_agent("client",  "You are a client that asks questions to the advisor.")
partner = fake_agent("advisor", "You are a helpful advisor.")

p = MultiTurnAgenticProcessor(seeder, partner, max_length=4, seed_message=SEED,
                              now_fn=lambda: CLOCK)
dataset = asyncio.run(p.run(str(tmp_path)))
```

**Outputs — process 1.**

```python
calls == [("advisor", 0), ("client", 1), ("advisor", 2)]        # 3 calls, budget was 4
len((tmp_path / "responses_0.jsonl").read_text().splitlines())  # 4

p.ledger.responses            # 3
p.ledger.turns                # 4
p.ledger.last_author          # "advisor"
p.ledger.next_speaker         # None
p.ledger.interleave_faults    # 0
p.ledger.completed            # True
p.ledger.completion_reason    # "agent_signal"
p.ledger.status               # "created"

p.status_tracker.max_turns      # 4
p.status_tracker.current_turn   # 3
p.status_tracker.num_responses  # 3
p.status_tracker.num_cached     # 0
p.status_tracker.num_errors     # 0
p.status_tracker.total_cost     # 0.003
p.status_tracker.total_tokens.total  # 45

read_sidecar(str(tmp_path)) == {
    "version": 2, "responses": 3, "turns": 4, "last_author": "advisor",
    "next_speaker": None, "interleave_faults": 0, "completed": True,
    "completion_reason": "agent_signal",
}
(tmp_path / "turn_ledger.json").stat().st_size   # 189

dataset.column_names == ["role", "content", "turn", "source"]   # as a set, at minimum
len(dataset)                                                    # 4
dataset[0] == {"role": "client",  "content": SEED,                                 "turn": 0, "source": "seed"}
dataset[1] == {"role": "advisor", "content": "Start with your goals.",             "turn": 1, "source": "response"}
dataset[2] == {"role": "client",  "content": "My goal is retirement in 20 years.", "turn": 2, "source": "response"}
dataset[3] == {"role": "advisor", "content": f"Then index funds. {SENTINEL}",      "turn": 3, "source": "response"}
```

The first line of `responses_0.jsonl`, parsed back:

```python
rec = AgentResponse.model_validate_json(lines[0])
rec.name, rec.finish_reason, rec.response_cost, rec.token_usage
# ("client", "seed", 0.0, None)
rec.created_at == rec.finished_at == datetime.datetime(2025, 1, 2, 3, 4, 5)
rec.generic_request.messages     # [{"role": "user", "content": SEED}]
rec.generic_request.original_row # {"prompt": SEED}
```

**Outputs — process 2 (same directory, fresh processor, `calls` cleared).**

```python
p2 = MultiTurnAgenticProcessor(seeder, partner, max_length=4, seed_message=SEED, now_fn=lambda: CLOCK)
ds2 = asyncio.run(p2.run(str(tmp_path)))

calls                             # []            -- nothing was regenerated
len(ds2)                          # 4
p2.ledger.status                  # "verified"
p2.ledger.completion_reason       # "agent_signal"
p2.status_tracker.current_turn    # 3
p2.status_tracker.num_cached      # 3
p2.status_tracker.num_responses   # 0
p2.status_tracker.total_cost      # 0.0
# MultiTurnResponse.update_tracker_stats(p2.status_tracker).request_stats
# == RequestStats(total=4, succeeded=0, failed=0, in_progress=0, cached=3)
```

**Outputs — process 3 (the log is truncated to 3 lines, sidecar left stale).**

```python
lines = (tmp_path / "responses_0.jsonl").read_text().splitlines(keepends=True)
(tmp_path / "responses_0.jsonl").write_text("".join(lines[:3]))     # authors: client, advisor, client
p3 = MultiTurnAgenticProcessor(seeder, partner, max_length=4, seed_message=SEED, now_fn=lambda: CLOCK)
asyncio.run(p3.run(str(tmp_path)))
# TurnLedgerDesyncError:
#   .path                  == str(tmp_path / "turn_ledger.json")
#   .log_responses         == 2
#   .recorded_responses    == 3
#   .log_last_author       == "client"
#   .recorded_last_author  == "advisor"
# calls == []  -- nothing was generated, nothing was appended, the log is still 3 lines
```

**Outputs — process 4 (same truncated log, sidecar deleted, `calls` cleared).**

```python
(tmp_path / "turn_ledger.json").unlink()
calls.clear()
REPLIES[:] = [f"Then index funds. {SENTINEL}"]      # the one reply this process will generate
p4 = MultiTurnAgenticProcessor(seeder, partner, max_length=4, seed_message=SEED, now_fn=lambda: CLOCK)
ds4 = asyncio.run(p4.run(str(tmp_path)))

p4.ledger.status                 # "adopted"      -- a missing sidecar is not an error
calls == [("advisor", 2)]        # one call: next_speaker was "advisor", task_id was ledger.responses
len(ds4)                         # 4
p4.status_tracker.num_cached     # 2
p4.status_tracker.num_responses  # 1
p4.status_tracker.current_turn   # 3
p4.ledger.completion_reason      # "agent_signal"
```
