# Durable response ledger with a single success count

## Target

### Files that change

| Path | Change |
|---|---|
| `src/bespokelabs/curator/request_processor/response_ledger.py` | **NEW.** The ledger: `LedgerStatus`, `classify_record`, `ledger_line`, `parse_ledger_line`, `LedgerTally`, `ResumeState`, `ResponseLedger`, `LedgerIntegrityError`, `LEDGER_SCHEMA_VERSION`, `ERROR_SAMPLE_LIMIT`. |
| `src/bespokelabs/curator/request_processor/base_request_processor.py` | `_process_response` (l.387) gains a `TypeError` catch; `_get_validated_response` (l.583) **deleted**; `validate_existing_response_file` (l.609) rewritten to return `ResumeState` and to stop rewriting the file (l.640-649 deleted); `create_dataset_files` (l.422) rewritten on top of `ResponseLedger` (deletes the hand counters at l.458/462/472, the arrow-derived `successful_indices` at l.510-517, and the `count_lines` reconciliation at l.543-545). |
| `src/bespokelabs/curator/request_processor/online/base_online_request_processor.py` | `handle_single_request_with_retries` exhausted-retry path (l.544-563) and `append_generic_response` (l.614-637: the `if not responses: return` at l.624-625 goes away). |
| `src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py` | `_process_single_response` (l.568-627: the `if processed_responses is None: return` at l.608-609 goes away); `submit_batches_from_request_files` (l.662-663) and `resubmit_batch` (l.731-736) adapt to `ResumeState`; `_update_final_stats` (l.794-805) rewritten on the ledger. |
| `src/bespokelabs/curator/request_processor/offline/base_offline_request_processor.py` | `process_requests_from_file` (l.149-192): adapt to `ResumeState`, write through `ledger_line`, fix the `idx + len(responses)` viewer-index bug at l.188. |
| `src/bespokelabs/curator/types/curator_response.py` | `update_tracker_stats` (l.168-225) takes an optional `LedgerTally` and derives `RequestStats` from it in both modes. |
| `src/bespokelabs/curator/llm/llm.py` | l.314 call site passes the tally. |

### Latent bugs this fixes (real, with locations)

1. **The online failure record is built and then thrown away.** `base_online_request_processor.py:552-561` builds `GenericResponse(response_message=None, response_errors=formatted_errors, ...)` and awaits `append_generic_response`; `append_generic_response` at l.624-625 does `if not responses: return`. `_process_response(data)` on that record calls `prompt_formatter.response_to_response_format(None)`, which at `prompt_formatter.py:175` evaluates `self.response_format(**response_dict)` with `response_dict is None` and raises `TypeError` — **not** caught by the `except (json.JSONDecodeError, ValidationError)` at `base_request_processor.py:390`. So with a `response_format` set, the exhausted-retry path raises `TypeError` out of `handle_single_request_with_retries`; without one, it returns silently and the line is never written while `num_tasks_failed` is incremented at l.563.
2. **`n_final_failed_requests` goes negative.** `base_batch_request_processor.py:520` opens the response file in `"a"`; `resubmit_batch` (l.731) resubmits the same `request_file`, so one `original_row_idx` can occupy two lines; `_update_final_stats` (l.799-805) counts *every line in every* `responses_*.jsonl` as a success and subtracts from `n_total_requests`. Two duplicated rows in a 10-request run report `succeeded=12, failed=-2` through `curator_response.py:205-206`.
3. **Resume assumes the file contains failures.** `validate_existing_response_file` (l.609-651) exists to *strip* failed lines, but no writer ever writes one, and it rewrites the file in place via `response_file + ".temp"` / `os.replace` (l.649) — data loss on a crash mid-rewrite.
4. **Two units in one return value.** l.651 returns `completed_request_ids` (requests) and `completed_parsed_responses` (parse rows, summed at l.638 *including* duplicate lines).
5. **`[]` from `parse_func` is indistinguishable from failure** online (`if not responses`, l.624) but is a hard failure in batch (`is None`, l.608) — the same `parse_func` behaves differently per backend.
6. **Double counting in `create_dataset_files`.** A response that both has `response_errors` and fails `_process_response` increments `failed_responses_count` at l.462 only (the `continue` saves it), but a response with `response_errors is not None` **and** an empty error list `[]` is counted failed at l.462 while `_get_validated_response` (l.585) treats the same record as *valid*.
7. **Pydantic rows are stringified on write.** `append_generic_response` l.630-631 does `json.dumps(data.model_dump(), default=str)`; `parsed_response_message` is typed `Optional[list]`, so a `parse_func` returning `BaseModel` rows survives `model_dump()` as model instances and `default=str` writes `"Answer(answer='A')"`.

### Machinery that may be REUSED (do not reimplement)

- `GenericResponse` / `GenericRequest` (`types/generic_response.py`, `types/generic_request.py`) — unchanged schema, including the `field_serializer` on `response_message`.
- `BaseRequestProcessor._process_response` (l.387) — the parse-and-dispatch itself; only its exception list changes.
- `PromptFormatter.response_to_response_format` (l.175) — unchanged.
- `bespokelabs.curator.file_utilities.count_lines` — for `n_declared_requests` cross-checks in tests only.
- `datasets.arrow_writer.ArrowWriter` and `BaseRequestProcessor._load_from_dataset_file` (l.541-...) — dataset materialisation and the `__original_row_idx` sort/drop.
- `RequestStats` (`types/curator_response.py:66`), `OnlineStatusTracker`, `BatchStatusTracker`, `OfflineStatusTracker` field names — unchanged.
- `read_metadata_file` (`base_request_processor.py:653`) — for `metadata_N.json`.

### Machinery that must be BUILT

`response_ledger.py` in full, plus the rewrites listed in the table. Nothing else. `create_request_files`, `_get_optimal_batch_size`, `create_batch_file`, the run-cache fingerprint, `attempt_loading_cached_dataset`, `MetadataDB` and `CuratorResponse.save`/`load` are out of scope and must not change.

### Python / dependencies

Python `^3.10` (dev env is 3.10.12). Available: `pydantic>=2.9.2`, `datasets^3.0.2`, `aiofiles>=22`, `pytest^8.3.3`, `pytest-asyncio^0.24`. Standard library `enum`, `dataclasses`, `json`, `glob`, `os`, `re`, `typing`. No new dependency. No network, no `time.time()`/`datetime.now()` inside `response_ledger.py` — every timestamp the ledger writes comes from a `GenericResponse` field the caller already populated.

---

## The API

```python
# src/bespokelabs/curator/request_processor/response_ledger.py
from __future__ import annotations

import dataclasses
import enum
from typing import Iterable, Optional

from bespokelabs.curator.types.generic_request import GenericRequest
from bespokelabs.curator.types.generic_response import GenericResponse

LEDGER_SCHEMA_VERSION: int = 2
ERROR_SAMPLE_LIMIT: int = 5


class LedgerStatus(str, enum.Enum):
    SUCCEEDED = "succeeded"
    EMPTY = "empty"
    UNPARSEABLE = "unparseable"
    FAILED = "failed"


# Highest precedence first. Exported, exactly this order.
STATUS_PRECEDENCE: tuple[LedgerStatus, ...] = (
    LedgerStatus.SUCCEEDED,
    LedgerStatus.EMPTY,
    LedgerStatus.UNPARSEABLE,
    LedgerStatus.FAILED,
)


class LedgerIntegrityError(ValueError):
    """A durable record refers to a request that no requests_*.jsonl declares."""

    def __init__(self, message: str, *, row_idx: int, source_file: str) -> None: ...

    row_idx: int      # the offending GenericRequest.original_row_idx
    source_file: str  # os.path.basename of the responses file, e.g. "responses_0.jsonl"


def classify_record(response: GenericResponse) -> LedgerStatus: ...


def ledger_line(response: GenericResponse) -> str:
    """Canonical serialisation of one durable record. Ends with exactly one '\\n'."""


def parse_ledger_line(line: str) -> Optional[GenericResponse]:
    """None if the line is blank or is not a valid GenericResponse JSON object."""


@dataclasses.dataclass(frozen=True)
class LedgerTally:
    n_requests: int              # unique original_row_idx across requests_*.jsonl
    n_declared_requests: int     # sum of metadata_N.json["num_jobs"]
    n_recorded: int              # unique original_row_idx with >= 1 durable record
    n_succeeded: int             # unique idx whose winning status is SUCCEEDED or EMPTY
    n_failed: int                # unique idx whose winning status is UNPARSEABLE or FAILED
    n_missing: int               # n_requests - n_recorded
    n_duplicate_lines: int       # parsed durable lines - n_recorded
    n_malformed_lines: int       # lines parse_ledger_line returned None for
    n_dataset_rows: int          # sum of len(parsed_response_message) over winning SUCCEEDED/EMPTY records
    error_sample: tuple[str, ...]
    schema_version: int = LEDGER_SCHEMA_VERSION


@dataclasses.dataclass(frozen=True)
class ResumeState:
    completed_row_indices: frozenset[int]
    retryable_row_indices: frozenset[int]
    n_dataset_rows: int


def read_resume_state(response_file: str) -> ResumeState:
    """Single-file resume view. Never writes, never raises LedgerIntegrityError."""


class ResponseLedger:
    working_dir: str

    def __init__(self, working_dir: str) -> None: ...

    @classmethod
    def load(cls, working_dir: str) -> "ResponseLedger":
        """Read every requests_N.jsonl / metadata_N.json / responses_N.jsonl under
        working_dir and resolve duplicates. Raises LedgerIntegrityError on an orphan."""

    def tally(self) -> LedgerTally: ...
    def winning_records(self) -> list[GenericResponse]:
        """Winning record per recorded row, ascending original_row_idx."""
    def missing_row_indices(self) -> list[int]:
        """Declared requests with no durable record, ascending."""
    def unresolved_row_indices(self) -> list[int]:
        """UNPARSEABLE + FAILED winners + missing rows, ascending. == failed_requests.jsonl order."""
    def request_line(self, row_idx: int) -> str:
        """Verbatim source line from requests_*.jsonl, exactly one trailing '\\n'."""
```

Changed signatures elsewhere:

```python
# base_request_processor.py
def validate_existing_response_file(self, response_file: str) -> ResumeState: ...
def _process_response(self, data: GenericResponse) -> list | None: ...   # unchanged shape
def create_dataset_files(self, parse_func_hash: str) -> "Dataset": ...   # unchanged shape
# _get_validated_response is REMOVED.

# online/base_online_request_processor.py  (signature unchanged)
async def append_generic_response(self, status_tracker: OnlineStatusTracker,
                                  data: GenericResponse, filename: str) -> None: ...

# batch/base_batch_request_processor.py  (signature unchanged)
async def _process_single_response(self, raw_response: dict, generic_request_map: dict,
                                   batch: GenericBatch, f, invalid_finish_responses: list,
                                   failed_processed_responses: list, streaming_tasks: list,
                                   total_token_usage: _TokenUsage, total_cost: float) -> None: ...

# types/curator_response.py
def update_tracker_stats(self, tracker, tally: "LedgerTally | None" = None) -> None: ...
```

---

## Parts

### P1 — Every terminal request leaves exactly one durable line

**Behaviour.** All three writers (`append_generic_response`, `_process_single_response`, `process_requests_from_file`) write a line for **every** response they are handed — permanent failures, unparseable responses and empty parses included. A record whose `response_errors` is truthy **or** whose `response_message is None` is written with `parsed_response_message = None` and is **not** passed to `_process_response` at all; every other record is written with `parsed_response_message` set to the return of `_process_response` (`None`, `[]`, or a non-empty list). The early returns at `base_online_request_processor.py:624-625` and `base_batch_request_processor.py:608-609` are deleted; `failed_processed_responses` still collects the index of every record whose `_process_response` returned `None`, but the record is written anyway.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the drop and instead delete the failure record construction at l.552-560 — "if we don't write it, don't build it" — so a permanently failed request leaves no trace and `num_tasks_failed` alone reports it. This is what the code most nearly says today.
2. Write failure records into a *separate* sidecar (`failed_responses_*.jsonl` / the existing `failed_requests.jsonl`), keeping `responses_*.jsonl` as a success-only log. That preserves `_update_final_stats`'s line-count-equals-successes assumption at l.799-805 unchanged, which is a strong pull.
3. Write the record but let `_process_response` run first and swallow the resulting `TypeError` with a bare `except Exception`, so failures get whatever `parsed_response_message` falls out.

**The observable.** Drive one concrete `BaseRequestProcessor` subclass stub under `asyncio.run` with a `prompt_formatter` whose `response_to_response_format` increments a counter, against three records: (a) `response_message='{"answer": "A"}'`, (b) `response_message=None, response_errors=["TimeoutError: boom(x3)"]`, (c) `response_message="ok"` with a `parse_func` returning `[]`. After the three awaits: `count_lines(responses_0.jsonl) == 3`; `[classify_record(r).value for r in records] == ["succeeded", "failed", "empty"]`; the counter on the formatter is `2`, not `3` (alt. 3 makes it 3); no `TypeError` escapes. Alternatives 1 and 2 leave `count_lines(...) == 1` and `== 2` respectively.

**Arbitrary:** deliberate departure — the surrounding source drops these records on two different predicates, and alternative 2 is what `_update_final_stats` currently assumes.

---

### P2 — `LedgerStatus`, and the order the predicates are applied

**Behaviour.** `classify_record` returns exactly one of four members whose `.value` strings are `"succeeded"`, `"empty"`, `"unparseable"`, `"failed"`, decided in this order and no other:

| # | Predicate on the `GenericResponse` | Result |
|---|---|---|
| 1 | `bool(response.response_errors)` is True | `FAILED` |
| 2 | `response.response_message is None` | `FAILED` |
| 3 | `response.parsed_response_message is None` | `UNPARSEABLE` |
| 4 | `len(response.parsed_response_message) == 0` | `EMPTY` |
| 5 | otherwise | `SUCCEEDED` |

Consequences fixed by the ordering: `response_errors=[]` (empty list) is **not** a failure (rule 1 is falsy, matching the existing `if not response_errors` at l.585 and contradicting `if response.response_errors is not None` at l.460); and a record carrying **both** `response_errors=["rate limit(x2)"]` and a non-empty `parsed_response_message` is `FAILED`, not `SUCCEEDED` — errors dominate rows.

**Alternatives a competent engineer would plausibly choose instead.**
1. Three states (`succeeded` / `failed` / `missing`), folding `empty` into `succeeded` and `unparseable` into `failed` — nothing in the repo asks for four, and the two writers between them only ever distinguish two.
2. Rows-dominate-errors: check `parsed_response_message` first, so a partially errored record that still produced rows counts as `SUCCEEDED`; and treat `response_errors is not None` as failure, copying `create_dataset_files` l.460 verbatim so `[]` means failure.

**The observable.** `[s.value for s in LedgerStatus] == ["succeeded", "empty", "unparseable", "failed"]` (exact spellings, exact declaration order). Then, over six hand-built `GenericResponse`s — `(msg="x", parsed=[{"a":1}])`, `(msg=None, errors=["e"])`, `(msg="x", parsed=None)`, `(msg="x", parsed=[])`, `(msg="x", errors=[], parsed=[{"a":1}])`, `(msg="x", errors=["e"], parsed=[{"a":1}])` — `[classify_record(r).value for r in six] == ["succeeded", "failed", "unparseable", "empty", "succeeded", "failed"]`. Alternative 1 cannot produce the strings at positions 2 and 3; alternative 2 gives `..., "failed", ..., "succeeded"` at positions 4 (errors `[]`) and 5.

**Arbitrary:** invented name (the four member spellings and their declaration order) + policy with no local evidence (errors dominate rows; `[]` is not an error).

---

### P3 — Duplicate resolution: best status wins, ties go to the first line

**Behaviour.** Records for the same `original_row_idx` are folded to one **winning** record. The winner is the record whose status ranks highest in `STATUS_PRECEDENCE` = `(SUCCEEDED, EMPTY, UNPARSEABLE, FAILED)`; ties are broken by **earliest** position, where position is `(natural index of the responses file, line number)` and *natural index* means the integer `N` parsed out of `responses_N.jsonl` (so `responses_2.jsonl` precedes `responses_10.jsonl`; lexicographic `glob` order would reverse them). Every non-winning record for that idx is counted in `LedgerTally.n_duplicate_lines` and is otherwise ignored — it contributes no dataset rows, no error sample entry, no count.

**Alternatives a competent engineer would plausibly choose instead.**
1. Last-writer-wins: the append-only file's most recent line for an idx is the current truth, since `resubmit_batch` (l.731) exists precisely to produce a newer, better answer. This is the standard reading of an append log.
2. First-writer-wins outright, ignoring status: keep whatever line arrived first for an idx and discard the rest, which is what a plain `if idx in seen: continue` scan produces.
3. No folding at all: keep every line and count lines, exactly like `_update_final_stats` l.799-802, treating duplicates as a caller bug.

**The observable.** Fixture `responses_0.jsonl` with four lines in this order — idx 7 `FAILED` errors `["Timeout(x3)"]`; idx 7 `SUCCEEDED` `parsed=[{"answer":"late"}]`; idx 5 `SUCCEEDED` `parsed=[{"answer":"first"}]`; idx 5 `SUCCEEDED` `parsed=[{"answer":"second"}]` — over `requests_0.jsonl` declaring idx 5 and 7. Then `[r.parsed_response_message[0]["answer"] for r in ledger.winning_records()] == ["first", "late"]` and `ledger.tally().n_duplicate_lines == 2` and `ledger.tally().n_succeeded == 2`. Alternative 1 gives `["second", "late"]`; alternative 2 gives `["first", ...]` with idx 7 `FAILED` and `n_succeeded == 1`; alternative 3 gives four records and `n_duplicate_lines == 0`. Cross-file ordering, same fixture split: idx 5 `SUCCEEDED "from-2"` alone in `responses_2.jsonl` and idx 5 `SUCCEEDED "from-10"` alone in `responses_10.jsonl` yields `"from-2"`; lexicographic file order yields `"from-10"`.

**Arbitrary:** policy with no local evidence (precedence-then-first, against the natural append-log reading) + a chosen ordering rule (numeric file order, which no existing `glob` call in this file uses).

---

### P4 — `LedgerTally`: one shape, requests as the unit, five error samples

**Behaviour.** `ResponseLedger.tally()` returns the frozen dataclass above. Every field is a count of **unique `original_row_idx`** except `n_duplicate_lines`, `n_malformed_lines` (lines) and `n_dataset_rows` (`parse_func` rows). `n_requests` counts unique `original_row_idx` across all `requests_*.jsonl` (a repeated idx counts once — not `count_lines`, as at l.543-545). `n_declared_requests` sums `metadata_N.json["num_jobs"]` for every `requests_N.jsonl`, contributing `0` for a missing or unreadable metadata file, and is **reported, never enforced** — a mismatch with `n_requests` raises nothing. `error_sample` holds `str(record.response_errors)` for the winning records whose status is `FAILED`, in ascending `original_row_idx`, truncated to the first `ERROR_SAMPLE_LIMIT = 5`; `UNPARSEABLE` winners contribute nothing to it. These invariants hold by construction: `n_recorded == n_succeeded + n_failed`, `n_succeeded + n_failed + n_missing == n_requests`, and `0 <= n_succeeded <= n_requests`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Trust the metadata: use `metadata_N.json["num_jobs"]` as `n_requests` (that is what it is for — `_verify_existing_request_files` l.184-190 and `submit_batches_from_request_files` l.664 both do exactly this), and raise or warn when the request file disagrees.
2. Reuse the existing sample cap of 10 from `create_dataset_files` l.462, and include every non-succeeding record (unparseable ones too) in the sample, since l.460-472 counts both toward `failed_responses_count`.
3. Count lines for `n_requests` via `count_lines(requests_*.jsonl)`, mirroring l.543-545, so a duplicated request line inflates the denominator.

**The observable.** Fixture: `requests_0.jsonl` with 8 lines for idx `0..6` where idx `3` appears twice; `metadata_0.json` `{"num_jobs": 8}`; `responses_0.jsonl` with `FAILED` winners for idx `0,1,2,3,4,5` (errors `["e0"]`.. `["e5"]`) and a `SUCCEEDED` winner for idx `6`. Then `tally.n_requests == 7`, `tally.n_declared_requests == 8`, `tally.n_missing == 0`, `len(tally.error_sample) == 5`, `tally.error_sample == ("['e0']", "['e1']", "['e2']", "['e3']", "['e4']")`, `tally.schema_version == 2`. Alternative 1 gives `n_requests == 8`; alternative 2 gives `len(...) == 6`; alternative 3 gives `n_requests == 8` and `n_missing == 1`.

**Arbitrary:** invented name (`LedgerTally` and all ten field spellings) + chosen value (`ERROR_SAMPLE_LIMIT = 5`, where the only number in the code is 10) + policy (unique-idx as the unit; metadata reported, not enforced).

---

### P5 — `LedgerIntegrityError` on an orphan record

**Behaviour.** During `ResponseLedger.load`, a durable record whose `original_row_idx` is not declared by any `requests_*.jsonl` in the working directory raises `LedgerIntegrityError`, a `ValueError` subclass carrying `row_idx: int` (the offending index) and `source_file: str` (the `os.path.basename` of the responses file the line came from — not the absolute path). Records are scanned in the `(natural file index, line number)` order of P3, so the **first** orphan encountered in that order is the one reported. Malformed lines are skipped and counted in `n_malformed_lines` before this check, so a malformed line never raises. `read_resume_state` reads a single file with no requests file in hand and therefore never raises this.

**Alternatives a competent engineer would plausibly choose instead.**
1. Ignore orphans: skip the line, log a warning and carry on — this is how `create_dataset_files` treats every other malformed input (l.531-535 `except json.JSONDecodeError: continue`) and how `_get_validated_response` treats an unparseable line.
2. Count the orphan anyway: let it contribute a dataset row and a success, which is exactly what `_update_final_stats` l.799-802 does today (it never looks at the request files at all).
3. Raise the plain `ValueError` the rest of `create_dataset_files` raises (l.474-476, l.485, l.507), with the index interpolated into the message.

**The observable.** Fixture: `requests_0.jsonl` declares idx `0,1`; `responses_0.jsonl` holds a `SUCCEEDED` record for idx `1` then a `SUCCEEDED` record for idx `9`. `pytest.raises(LedgerIntegrityError)` on `ResponseLedger.load(tmpdir)`, with `exc.value.row_idx == 9`, `exc.value.source_file == "responses_0.jsonl"`, and `isinstance(exc.value, ValueError) is True`. Alternatives 1 and 2 raise nothing (tally `n_succeeded == 1` and `== 2` respectively); alternative 3 raises a `ValueError` with no `.row_idx` attribute (`hasattr(exc.value, "row_idx") is False`).

**Arbitrary:** invented name — the exception class, both attribute spellings, and the basename-not-path rule are unguessable from this repository; the repository's own convention is alternative 1 or 3.

---

### P6 — Resume is read-only, and `ResumeState` names its two sets

**Behaviour.** `validate_existing_response_file(response_file)` returns a `ResumeState` and **opens the file only for reading**: no `.temp` file, no `os.replace`, no truncation — the response file is byte-identical afterwards. `completed_row_indices` holds the idx whose winning status (P3 folding applies within the file) is `SUCCEEDED` **or** `EMPTY`; `retryable_row_indices` holds the idx whose winning status is `UNPARSEABLE` or `FAILED`; the two sets are disjoint. `n_dataset_rows` sums `len(parsed_response_message)` over winning `SUCCEEDED`/`EMPTY` records only — duplicates excluded, unlike l.638. A legitimately empty parse is **complete**, never retried. Callers skip requests in `completed_row_indices` and re-issue everything else; a retry's new record supersedes the old one by precedence rather than by rewriting the file.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the strip-and-rewrite: now that failures are durable, delete the failed lines on resume so the file stays a success-only log, which is what l.640-649 exists to do and what the docstring at l.610 promises.
2. Treat `EMPTY` as unfinished and put it in `retryable_row_indices` — an empty parse produced no data, so re-running it is the charitable reading; equally, treat `UNPARSEABLE` as terminal (the response arrived; re-calling the provider will not change the parse) and mark it completed.
3. Keep returning the existing `(set[int], int)` tuple, unnamed.

**The observable.** Fixture `responses_0.jsonl` with four lines: idx 0 `SUCCEEDED` (`parsed` length 2), idx 1 `FAILED`, idx 2 `EMPTY`, idx 3 `UNPARSEABLE`. Then `state == ResumeState(completed_row_indices=frozenset({0, 2}), retryable_row_indices=frozenset({1, 3}), n_dataset_rows=2)`; and after the call `count_lines(responses_0.jsonl) == 4`, the SHA-256 of the file equals the pre-call SHA-256, and `[p for p in os.listdir(tmpdir) if p.endswith(".temp")] == []`. Alternative 1 leaves 2 lines and a changed hash; alternative 2 gives `completed={0}` / `retryable={1,2,3}` (or `completed={0,2,3}`); alternative 3 fails on `state.completed_row_indices` with an `AttributeError`.

**Arbitrary:** deliberate departure (the function's whole existing purpose is the rewrite it must no longer do) + policy (`EMPTY` complete / `UNPARSEABLE` retryable) + invented name (`ResumeState` and its three fields).

---

### P7 — `ledger_line`: one serialiser, raw message, normalised rows

**Behaviour.** Every writer serialises through `ledger_line(response) -> str`. It (a) leaves `response_message` as the **raw** value the provider returned — the pre-`_process_response` value, so a structured response stays the JSON *string* `'{"answer": "A"}'` rather than the validated model or its dict (online restores this at l.616/628; batch at l.606 writes the mutated one — unify on raw); (b) normalises every element of `parsed_response_message`: a `BaseModel` row becomes `row.model_dump(mode="json")`, a `dict` row is kept, and anything else raises `ValueError`; (c) emits `json.dumps(payload, default=str)` of `response.model_dump(mode="json")` with the two fields above substituted, followed by exactly one `"\n"`. `parse_ledger_line` is its inverse for well-formed input and returns `None` for a blank line or one that fails `GenericResponse.model_validate_json`.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep each writer's current serialisation (online: `json.dumps(data.model_dump(), default=str)`; batch: `json.dumps(generic_response.model_dump(mode="json"), default=str)`; offline: `json.dumps(response.model_dump(mode="json"), default=str)`) and just move the write; `default=str` "handles" pydantic rows.
2. Store the *parsed* `response_message` (the validated model dumped to a dict), since `_process_response` has already produced it and it is strictly more useful downstream.

**The observable.** A record with `response_message='{"answer": "A"}'`, a `response_format` model, and `parsed_response_message=[Answer(answer="A")]` where `Answer` is a `pydantic.BaseModel`. `line = ledger_line(record)`: `line.count("\n") == 1` and `line.endswith("\n")`; `json.loads(line)["parsed_response_message"] == [{"answer": "A"}]` (alternative 1 yields the string `"answer='A'"`); `json.loads(line)["response_message"] == '{"answer": "A"}'` — a `str`, not a `dict` (alternative 2 yields `{"answer": "A"}`). Round trip: `classify_record(parse_ledger_line(line)) is LedgerStatus.SUCCEEDED`. And `parse_ledger_line("\n") is None`, `parse_ledger_line("{oops") is None`.

**Arbitrary:** deliberate departure (batch and offline write the mutated message today; `default=str` silently "works") + policy (rows normalised at write time rather than at read time).

---

### P8 — The viewer index advances in parse rows, and only successes stream

**Behaviour.** In all three writers, after a line is written: `status_tracker.num_parsed_responses` advances by `len(parsed_response_message)`, i.e. by `0` for `FAILED`, `UNPARSEABLE` and `EMPTY` records and by the row count for `SUCCEEDED` ones (this fixes `base_offline_request_processor.py:188`, which advances by `len(responses)` — the whole batch — once per response). `viewer_client.stream_response(line, idx)` is called **only** for records whose status is `SUCCEEDED`, with `idx` equal to `num_parsed_responses` *before* the increment. Non-streaming records still advance nothing and still get written.

**Alternatives a competent engineer would plausibly choose instead.**
1. Stream every written line, including failures — the viewer should show what went wrong, and the current code streams unconditionally after any write.
2. Advance the index by 1 per record (a record index rather than a row index), or by `len(parsed or [1])`, so the viewer index and the file's line numbers stay aligned.

**The observable.** An async no-op viewer stub recording `(json_string, idx)` calls, driven under `asyncio.run` over four records in order: `SUCCEEDED` with 2 rows, `FAILED`, `EMPTY`, `SUCCEEDED` with 1 row. Afterwards: `len(stub.calls) == 2`, `[idx for _, idx in stub.calls] == [0, 2]`, `status_tracker.num_parsed_responses == 3`, and `count_lines(responses_0.jsonl) == 4`. Alternative 1 gives `len(stub.calls) == 4` and indices `[0, 2, 2, 2]`; alternative 2 gives `num_parsed_responses == 4`.

**Arbitrary:** policy with no local evidence — the code streams whatever it writes and never had a record it wrote but did not stream.

---

### P9 — `_process_response` is never called on a failed record, and it catches `TypeError`

**Behaviour.** Two changes that together close the `prompt_formatter.py:175` crash. (a) The writers short-circuit: a record with truthy `response_errors` or `response_message is None` never reaches `_process_response`, so neither `response_to_response_format` nor `parse_func` is called for it. (b) `_process_response`'s first `except` clause becomes `(json.JSONDecodeError, ValidationError, TypeError)` and returns `None`, so a response body that parses to JSON but not to a mapping (`"[1, 2]"`, `"null"`, `"7"` with a `response_format` set — `self.response_format(**[1, 2])` raises `TypeError`) is classified `UNPARSEABLE` instead of blowing up the request loop. The `parse_func` block's `except Exception` at l.404-406 is unchanged.

**Alternatives a competent engineer would plausibly choose instead.**
1. Let `_process_response` run for failure records and widen the catch to `except Exception` — one change instead of two, and it makes the crash go away just as well.
2. Guard inside `PromptFormatter.response_to_response_format` instead (`if response_message is None: return None` before l.175), fixing the crash at the site the traceback points at and leaving `_process_response` alone.

**The observable.** With a formatter stub counting calls to `response_to_response_format` and to `parse_func`: hand `append_generic_response` a `FAILED` record (`response_message=None`, `response_errors=["boom(x3)"]`) — afterwards `formatter.format_calls == 0` and `formatter.parse_calls == 0` (alternative 1 gives `1` and `0`; alternative 2 gives `1` and `1`, and its `parse_func` sees `None`), and the written record satisfies `json.loads(line)["parsed_response_message"] is None`. Separately, calling `_process_response` directly on a record with `response_message="[1, 2]"` and a `response_format` returns `None` rather than raising — `classify_record` of the written record is `LedgerStatus.UNPARSEABLE`.

**Arbitrary:** policy with no local evidence — the "obvious" repair is a wider `except`; requiring both the short-circuit (observable as a call count of 0) and the narrow named `TypeError` is the team's choice. The underlying crash is a genuine bug at `prompt_formatter.py:175` / `base_request_processor.py:390`.

---

### P10 — `create_dataset_files` and `_update_final_stats` read the ledger, and only the ledger

**Behaviour.** `create_dataset_files(parse_func_hash)` builds `ResponseLedger.load(self.working_dir)` once and derives everything from it:
- dataset rows come from the **stored** `parsed_response_message` of the winning `SUCCEEDED` records, ascending `original_row_idx`; `_process_response` is **not** called again (the `TODO` at l.450-452 is discharged), so a `parse_func` that would now raise or return differently cannot change a materialised run;
- the existing per-row checks are kept: a `BaseModel` row is `model_dump()`ed, a non-`dict` row raises `ValueError`, an empty `dict` row raises `ValueError`, and `row["__original_row_idx"]` is stamped;
- `failed_requests.jsonl` is `ledger.unresolved_row_indices()` — `FAILED` + `UNPARSEABLE` winners **and** missing rows, `EMPTY` and `SUCCEEDED` excluded — written in ascending `original_row_idx`, each line the verbatim source line from the request file with exactly one trailing newline; the file is always created, 0 bytes when there is nothing unresolved;
- `require_all_responses` raises `ValueError` **iff** `tally.n_succeeded < tally.n_requests` — one predicate replacing the two at l.468-472 and l.545-549;
- `raise ValueError` for an all-failed run iff `tally.n_succeeded == 0`, deleting `dataset_file` first, as today.

`_update_final_stats` becomes `t = ResponseLedger.load(self.working_dir).tally(); self.tracker.n_final_success_requests = t.n_succeeded; self.tracker.n_final_failed_requests = t.n_requests - t.n_succeeded` — no line counting, no `n_total_requests` subtraction, so the value cannot go negative.

**Alternatives a competent engineer would plausibly choose instead.**
1. Re-run `_process_response` per line while building the arrow file, exactly as l.453-456 does — it is the only thing that guarantees the dataset matches the *current* `parse_func`, and the existing `TODO` says the author wanted to but did not know how.
2. Keep `failed_requests.jsonl` as it is: derived from the arrow file's `__original_row_idx` set (l.510-535), streamed in request-file order rather than sorted, which is cheaper and needs no sort — and, since `EMPTY` records produce no arrow rows, includes empties.
3. Keep the two separate failure gates (`failed_responses_count > 0` and `n_requests != total_responses_count`), and keep `n_final_failed_requests = n_total_requests - line_count`.

**The observable.** Fixture: `requests_0.jsonl` declares idx `0,1,2`; `responses_0.jsonl` holds idx 0 `SUCCEEDED` `[{"answer": "A"}]`, idx 1 `EMPTY`, idx 2 `SUCCEEDED` `[{"answer": "C"}]`; the processor's `prompt_formatter.parse_func` **raises** `AssertionError` when called; `require_all_responses=True`. Then `create_dataset_files("h")` returns a `Dataset` of `len == 2` with `list(ds) == [{"answer": "A"}, {"answer": "C"}]`, raises nothing (alternative 1 raises / produces `len == 0`; a "require a dataset row per request" reading raises on the `EMPTY` row), and `os.path.getsize(failed_requests.jsonl) == 0` (alternative 2 writes the idx-1 request line). And for a duplicate-resubmission working dir — 3 requests, 5 response lines, 2 duplicates, all rows succeeding — `tracker.n_final_success_requests == 3` and `tracker.n_final_failed_requests == 0`; alternative 3 gives `5` and `-2`.

**Arbitrary:** deliberate departure (trusting the stored parse instead of re-running it; a single failure gate) + policy (`EMPTY` is not an unresolved request; `failed_requests.jsonl` sorted ascending).

---

### P11 — One number reaches the user, in requests

**Behaviour.** `CuratorResponse.update_tracker_stats(tracker, tally=None)`: when `tally` is not `None`, `RequestStats` is built from it in **both** batch and online mode — `total = tally.n_requests`, `succeeded = tally.n_succeeded`, `failed = tally.n_requests - tally.n_succeeded` (so missing rows count as failed and the value is never negative), `in_progress = 0`, `cached = getattr(tracker, "num_tasks_already_completed", 0)`. The online branch stops reading `tracker.num_tasks_succeeded` / `num_tasks_failed` (l.211-215), which count records rather than durable lines. When `tally is None`, the existing behaviour at l.203-216 is retained verbatim. `PerformanceStats.requests_per_minute` keeps using `self.request_stats.succeeded`, so it follows the ledger too.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the two branches and only repair the batch one, since the in-memory online counters are incremented right next to the write and are cheaper and "obviously" right — that is what the `if not self.batch_mode` split at l.202-216 invites.
2. Report `failed = tally.n_failed` (the recorded failures only) and expose `missing` separately or through `in_progress`, so `succeeded + failed != total` when rows are missing.

**The observable.** A `LedgerTally(n_requests=5, n_declared_requests=5, n_recorded=4, n_succeeded=2, n_failed=2, n_missing=1, n_duplicate_lines=1, n_malformed_lines=0, n_dataset_rows=1, error_sample=("['e']",))` and an `OnlineStatusTracker` with `num_tasks_succeeded=4`, `num_tasks_failed=0`, `num_tasks_in_progress=1`, `num_tasks_already_completed=1`, `total_requests=5`. After `resp.update_tracker_stats(tracker, tally)` with `batch_mode=False`: `resp.request_stats == RequestStats(total=5, succeeded=2, failed=3, in_progress=0, cached=1)`. Alternative 1 gives `RequestStats(total=5, succeeded=4, failed=0, in_progress=1, cached=1)`; alternative 2 gives `failed=2`.

**Arbitrary:** deliberate departure (online's user-visible numbers stop coming from the tracker that the writer increments) + policy (missing rolls into failed; `in_progress` forced to 0).

---

## End to end

### Input — one temp working directory

`requests_0.jsonl` (5 lines, verbatim, each a `GenericRequest`; `model`/`messages` elided here as `M` for brevity but present in the fixture):

```
{"model": "gpt-4o-mini", "messages": M, "response_format": null, "original_row": {"q": "q0"}, "original_row_idx": 0, "generation_params": {}, "is_multimodal_prompt": false}
{"model": "gpt-4o-mini", "messages": M, "response_format": null, "original_row": {"q": "q1"}, "original_row_idx": 1, "generation_params": {}, "is_multimodal_prompt": false}
{"model": "gpt-4o-mini", "messages": M, "response_format": null, "original_row": {"q": "q2"}, "original_row_idx": 2, "generation_params": {}, "is_multimodal_prompt": false}
{"model": "gpt-4o-mini", "messages": M, "response_format": null, "original_row": {"q": "q3"}, "original_row_idx": 3, "generation_params": {}, "is_multimodal_prompt": false}
{"model": "gpt-4o-mini", "messages": M, "response_format": null, "original_row": {"q": "q4"}, "original_row_idx": 4, "generation_params": {}, "is_multimodal_prompt": false}
```

`metadata_0.json`: `{"num_jobs": 5}`

`responses_0.jsonl` (5 lines, in this order; `created_at`/`finished_at` are the fixed literal `"2024-01-01T00:00:00"`, `raw_response` is `null`):

| line | `original_row_idx` | `response_message` | `response_errors` | `parsed_response_message` |
|---|---|---|---|---|
| 1 | 0 | `"ok0"` | `null` | `[{"answer": "A"}]` |
| 2 | 1 | `null` | `["TimeoutError: boom(x3)"]` | `null` |
| 3 | 0 | `"ok0-again"` | `null` | `[{"answer": "A2"}]` |
| 4 | 2 | `"raw text"` | `null` | `null` |
| 5 | 3 | `"ok3"` | `null` | `[]` |

Row 4 is declared by the requests file and has no response line at all. `config.require_all_responses = False`.

### Expected outputs, as literals

```python
ledger = ResponseLedger.load(working_dir)

ledger.tally() == LedgerTally(
    n_requests=5,
    n_declared_requests=5,
    n_recorded=4,
    n_succeeded=2,            # idx 0 (SUCCEEDED) + idx 3 (EMPTY)
    n_failed=2,               # idx 1 (FAILED) + idx 2 (UNPARSEABLE)
    n_missing=1,              # idx 4
    n_duplicate_lines=1,      # 5 parsed lines - 4 unique idx
    n_malformed_lines=0,
    n_dataset_rows=1,         # idx 0 contributes 1, idx 3 contributes 0
    error_sample=("['TimeoutError: boom(x3)']",),
    schema_version=2,
)

[classify_record(r).value for r in ledger.winning_records()] == \
    ["succeeded", "failed", "unparseable", "empty"]
[r.parsed_response_message for r in ledger.winning_records()] == \
    [[{"answer": "A"}], None, None, []]          # idx 0 keeps "A", not "A2"

ledger.missing_row_indices()    == [4]
ledger.unresolved_row_indices() == [1, 2, 4]

read_resume_state(os.path.join(working_dir, "responses_0.jsonl")) == ResumeState(
    completed_row_indices=frozenset({0, 3}),
    retryable_row_indices=frozenset({1, 2}),
    n_dataset_rows=1,
)
# and the file is unchanged:
count_lines(".../responses_0.jsonl") == 5
[p for p in os.listdir(working_dir) if p.endswith(".temp")] == []

ds = processor.create_dataset_files("hash0")
len(ds) == 1
list(ds) == [{"answer": "A"}]
count_lines(".../failed_requests.jsonl") == 3
[json.loads(l)["original_row_idx"] for l in open(".../failed_requests.jsonl")] == [1, 2, 4]

processor._update_final_stats()
processor.tracker.n_final_success_requests == 2
processor.tracker.n_final_failed_requests == 3        # 5 - 2, never negative

resp = CuratorResponse(dataset=ds, batch_mode=True)
resp.update_tracker_stats(processor.tracker, ledger.tally())
resp.request_stats == RequestStats(total=5, succeeded=2, failed=3, in_progress=0, cached=0)
```

With `config.require_all_responses = True` on the same directory, `create_dataset_files("hash0")` raises `ValueError` (because `n_succeeded=2 < n_requests=5`) and `os.path.exists(working_dir + "/hash0.arrow") is False`.

Appending a sixth line to `responses_0.jsonl` for `original_row_idx = 42` and re-running `ResponseLedger.load(working_dir)` raises `LedgerIntegrityError` with `row_idx == 42` and `source_file == "responses_0.jsonl"`.
