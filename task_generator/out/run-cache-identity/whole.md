# Versioned run identity for the curator cache

## Target

**Files that change**

| Path | Change |
|---|---|
| `src/bespokelabs/curator/run_identity.py` | **new module** — the whole identity rule: components, canonicalisation, digest, stamp file, directory reconciliation, exception family. Also the new home of `_get_function_hash` (moved verbatim out of `llm/llm.py`). |
| `src/bespokelabs/curator/llm/llm.py` | `_hash_fingerprint()` (`:144`) deleted, replaced by `LLM._run_identity()`; `LLM.__init__` records `_backend_params`; new `backend` / `backend_params` properties; `__call__` (`:187`) gains `run_id`, reconciles the directory before using it; `_get_cached_response` (`:171`) stops swallowing identity errors; `_get_function_hash` becomes a re-export. |
| `src/bespokelabs/curator/db.py` | `RUNS_COLUMNS`; `validate_schema()` migrates instead of refusing; `store_metadata()` writes `parse_func` and `identity_version` and returns a status string. |
| `src/bespokelabs/curator/types/curator_response.py` | `CuratorResponse.run_identity` field; `to_dict()` records it; `load()` verifies the dataset it is handed. |

`request_processor/base_request_processor.py` gains exactly one line (`self._is_cached_dataset = False` at the top of `run()`, P11). `attempt_loading_cached_dataset()` (`:364`) and the `f"{parse_func_hash}.arrow"` name (`:373`, `:451`) are deliberately **left alone**: once `parse_func_hash` participates in the run hash (P2), the directory can no longer hold two arrow files that disagree about the parse function, so the second key becomes redundant-but-harmless rather than wrong. Nothing in `client.py`, `_factory.py` or the viewer changes.

**Existing machinery that may be REUSED**

- `_get_function_hash(func)` (`llm/llm.py:337`) — moved, not rewritten: same body, same `datasets.utils._dill` `Pickler`, same `xxh64(...).hexdigest()`, same `xxh64("").hexdigest() == "ef46db3751d8e999"` for `func is None`.
- `xxhash.xxh64` (already a direct dependency) as the only digest function.
- `PromptFormatter` (`llm/prompt_formatter.py:45`) and its six fields — read, never modified.
- `BaseRequestProcessor.backend` (`base_request_processor.py:60`, an abstract property every processor implements) as the source of the *resolved* backend name.
- `MetadataDB._get_current_schema()` (`db.py:18`) via `PRAGMA table_info(runs)` for the migration check.
- `CuratorResponse.to_dict()`'s existing `"dataset": {"fingerprint", "size", "columns"}` record (`curator_response.py:260`) — already written, never read; P9 gives it a reader.
- `pytest` `tmp_path`, `monkeypatch`; `datasets.Dataset.from_list` for in-memory datasets.

**What must be BUILT**

- `run_identity.py`: `RUN_IDENTITY_VERSION`, `RUN_IDENTITY_FILENAME`, `IDENTITY_BACKEND_PARAM_KEYS`, `PAYLOAD_PREFIX`; exceptions `RunIdentityError`, `RunIdentityMismatch`, `CachedResponseMismatch`; frozen dataclasses `RunIdentity`, `RunStamp`, `RunDirectoryCheck`; functions `build_components`, `canonical_payload`, `hash_components`, `format_run_hash`, `compute_run_identity`, `write_run_stamp`, `read_run_stamp`, `reconcile_run_directory`.
- `db.py`: `RUNS_COLUMNS`, migration inside `validate_schema()`, two new columns, a return value from `store_metadata`.
- `curator_response.py`: `run_identity` field, `verify` keyword on `load`.
- `llm.py`: `LLM.backend`, `LLM.backend_params`, `LLM._run_identity`, `run_id` parameter on `__call__`.

**Python / dependencies**

Python `^3.10` (repo target; verified against 3.10.12). `str | None`, `dict[str, Any]`, `tuple[str, ...]`, `dataclasses(frozen=True)`, keyword-only `*` params are all available; no `from __future__ import annotations` needed. Dependencies already present: `xxhash ^3.5.0`, `datasets ^3.0.2`, `pydantic >=2.9.2`, stdlib `json`/`sqlite3`/`os`/`pathlib`. **No new dependency.** `run_identity.py` imports neither `datetime`, `time`, `random`, `uuid` nor `os.urandom` — every timestamp and every ephemeral run id is a parameter.

**Latent bugs in this area (all real, with lines)**

1. `db.py:126` — the INSERT lists ten columns; `metadata["parse_func"]`, handed in at `llm.py:257`, is silently dropped. Fixed by P8.
2. `db.py:49-52` — `total_cost_milli_dollars`, `total_requests`, `total_prompt_tokens`, `total_completion_tokens` are declared and validated but no code path in the repository ever writes them. **Left as-is on purpose** (out of scope for identity); P7 keeps them in `RUNS_COLUMNS` so the schema check still accounts for them.
3. `base_request_processor.py:57`/`:131` — `_is_cached_dataset` is set `False` only in `__init__` and `True` on a cache hit, never back. A second `__call__` on the same `LLM` that misses the cache still takes the cached branch at `llm.py:300` and returns a response with zeroed tracker stats. Fixed by P11.
4. `llm.py:145-146` — `xxh64(os.urandom(8))` mints an unlabelled directory and a metadata row per disabled-cache run, indistinguishable from a real run and never collected. Fixed by P4.
5. `curator_response.py:314` — `load()` accepts any dataset and pairs it with any recorded stats. Fixed by P9.
6. `llm.py:171-176` — `_get_cached_response` catches `Exception` and returns `None`, so a corrupt or foreign cache is reported as a `logger.warning` and a silently different result. Fixed by P10.

## The API

`src/bespokelabs/curator/run_identity.py`

```python
"""Run identity: what makes two curator runs the same run."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from xxhash import xxh64

RUN_IDENTITY_VERSION: int = 3
RUN_IDENTITY_FILENAME: str = "run_identity.json"
PAYLOAD_PREFIX: str = "curator-run-identity/v3\n"
IDENTITY_BACKEND_PARAM_KEYS: frozenset[str] = frozenset(
    {"azure_deployment", "base_url", "batch_size", "completion_window"}
)
IDENTITY_COMPONENT_KEYS: tuple[str, ...] = (
    "backend",
    "backend_params",
    "batch_mode",
    "dataset_hash",
    "generation_params",
    "model_name",
    "parse_func_hash",
    "prompt_func_hash",
    "response_format",
    "return_completions_object",
    "run_id",
    "system_prompt",
)


class RunIdentityError(RuntimeError):
    """Base class for every run-identity failure."""


class RunIdentityMismatch(RunIdentityError):
    """Raised when a run directory was written under a different identity."""

    def __init__(self, path: str, expected_run_hash: str, found_run_hash: Optional[str],
                 mismatched_components: tuple[str, ...]) -> None:
        self.path: str = path
        self.expected_run_hash: str = expected_run_hash
        self.found_run_hash: Optional[str] = found_run_hash
        self.mismatched_components: tuple[str, ...] = mismatched_components
        super().__init__(
            f"{path} was written under run identity {found_run_hash!r}, expected {expected_run_hash!r} "
            f"(differing: {', '.join(mismatched_components) or 'unknown'})"
        )


class CachedResponseMismatch(RunIdentityError):
    """Raised when a cached response.json does not describe the dataset it is loaded with."""

    def __init__(self, cache_dir: str, field: str, expected: Any, found: Any) -> None:
        self.cache_dir: str = cache_dir
        self.field: str = field
        self.expected: Any = expected
        self.found: Any = found
        super().__init__(f"cached response in {cache_dir} has {field}={expected!r}, dataset has {found!r}")


@dataclass(frozen=True)
class RunIdentity:
    run_hash: str
    digest: str
    identity_version: int
    cache_enabled: bool
    components: dict[str, Any]


@dataclass(frozen=True)
class RunStamp:
    identity_version: int
    run_hash: str
    digest: str
    components: dict[str, Any]
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]: ...

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RunStamp": ...


@dataclass(frozen=True)
class RunDirectoryCheck:
    status: str            # "created" | "adopted" | "upgraded" | "matched"
    stamp: RunStamp
    previous_version: Optional[int]


def _get_function_hash(func) -> str: ...                      # moved from llm/llm.py:337, unchanged

def build_components(llm, dataset_hash: str, *, cache_enabled: bool = True,
                     run_id: Optional[str] = None) -> dict[str, Any]: ...

def canonical_payload(components: Mapping[str, Any]) -> str: ...

def hash_components(components: Mapping[str, Any]) -> str: ...          # bare 16-char hex

def format_run_hash(digest: str, *, cache_enabled: bool) -> str: ...

def compute_run_identity(llm, dataset_hash: str, *, cache_enabled: bool = True,
                         run_id: Optional[str] = None) -> RunIdentity: ...

def write_run_stamp(run_cache_dir: Union[str, Path], identity: RunIdentity, *,
                    now: str, created_at: Optional[str] = None) -> RunStamp: ...

def read_run_stamp(run_cache_dir: Union[str, Path]) -> Optional[RunStamp]: ...

def reconcile_run_directory(run_cache_dir: Union[str, Path], identity: RunIdentity, *,
                            now: str) -> RunDirectoryCheck: ...
```

`build_components` reads exactly these attributes off `llm` (any object with them — no `isinstance` check, no import of `LLM`):
`llm.prompt_formatter.prompt_func`, `.parse_func`, `.model_name`, `.response_format`, `.generation_params`, `.system_prompt`; `llm.batch_mode`; `llm.backend`; `llm.backend_params`; `llm.return_completions_object`.

`build_components` return value — exactly the twelve keys of `IDENTITY_COMPONENT_KEYS`, no more, no fewer:

| key | type | value |
|---|---|---|
| `backend` | `str` | `str(llm.backend)` — the *resolved* backend name |
| `backend_params` | `dict[str, Any]` | `{k: v for k, v in llm.backend_params.items() if k in IDENTITY_BACKEND_PARAM_KEYS}` |
| `batch_mode` | `bool` | `bool(llm.batch_mode)` |
| `dataset_hash` | `str` | `str(dataset_hash)` |
| `generation_params` | `dict[str, Any]` | `dict(llm.prompt_formatter.generation_params or {})` |
| `model_name` | `str` | `str(llm.prompt_formatter.model_name)` |
| `parse_func_hash` | `str` | `_get_function_hash(llm.prompt_formatter.parse_func)` |
| `prompt_func_hash` | `str` | `_get_function_hash(llm.prompt_formatter.prompt_func)` |
| `response_format` | `str` | `json.dumps(rf.model_json_schema(), sort_keys=True, separators=(",", ":"))`, or `"text"` when `rf is None` |
| `return_completions_object` | `bool` | `bool(llm.return_completions_object)` |
| `run_id` | `str \| None` | `run_id` when `cache_enabled is False`, else `None` |
| `system_prompt` | `str \| None` | `llm.prompt_formatter.system_prompt` |

Any component value that `json.dumps` cannot serialise raises `RunIdentityError` (no `default=str`, no `repr` fallback — those are not deterministic across processes).

`src/bespokelabs/curator/db.py`

```python
RUNS_COLUMNS: tuple[tuple[str, str], ...] = (
    ("run_hash", "TEXT"),
    ("session_id", "TEXT"),
    ("dataset_hash", "TEXT"),
    ("prompt_func", "TEXT"),
    ("parse_func", "TEXT"),
    ("model_name", "TEXT"),
    ("response_format", "TEXT"),
    ("batch_mode", "BOOLEAN"),
    ("created_time", "TEXT"),
    ("last_edited_time", "TEXT"),
    ("is_hosted_viewer_synced", "BOOLEAN"),
    ("identity_version", "INTEGER"),
    ("total_cost_milli_dollars", "TEXT"),
    ("total_requests", "TEXT"),
    ("total_prompt_tokens", "TEXT"),
    ("total_completion_tokens", "TEXT"),
)

class MetadataDB:
    def validate_schema(self) -> tuple[str, ...]: ...      # returns columns added by migration
    def store_metadata(self, metadata: dict) -> str: ...   # "inserted" | "updated"
```

`src/bespokelabs/curator/types/curator_response.py`

```python
@dataclass
class CuratorResponse:
    ...
    metadata: Dict[str, Any] = field(default_factory=dict)
    run_identity: Optional[Dict[str, Any]] = None          # new, declared last

    def to_dict(self) -> Dict[str, Any]: ...               # gains top-level "run_identity"

    @classmethod
    def load(cls, cache_dir: Union[str, Path], dataset: Dataset, *,
             verify: bool = True) -> "CuratorResponse": ...
```

`src/bespokelabs/curator/llm/llm.py`

```python
class LLM:
    @property
    def backend(self) -> str:                 # self._request_processor.backend
    @property
    def backend_params(self) -> dict:         # copy of what was passed to __init__, {} if None

    def _run_identity(self, dataset_hash: str, *, cache_enabled: bool,
                      run_id: Optional[str] = None) -> RunIdentity: ...

    def __call__(self, dataset=None, working_dir: str = None, batch_cancel: bool = False,
                 batch_cancel_auto_confirm: bool = False,
                 cache_dir: Optional[Union[str, Path]] = None,
                 run_id: Optional[str] = None) -> CuratorResponse: ...
```

## Parts

### P1 — The `run_identity` module surface

**Behaviour.** Identity lives in one new top-level module `bespokelabs/curator/run_identity.py` (not under `llm/`, so `db.py` can import `RUN_IDENTITY_VERSION` without a cycle) exporting the names above. `RunIdentity`, `RunStamp` and `RunDirectoryCheck` are **frozen dataclasses** — not pydantic models, not `NamedTuple`s, not dicts — with the field orders given: `RunIdentity(run_hash, digest, identity_version, cache_enabled, components)`, `RunStamp(identity_version, run_hash, digest, components, created_at, updated_at)`, `RunDirectoryCheck(status, stamp, previous_version)`. `RunIdentityMismatch` and `CachedResponseMismatch` both subclass `RunIdentityError`, which subclasses `RuntimeError`. `llm.llm._get_function_hash` continues to resolve (re-export) so existing imports keep working.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep everything in `llm/llm.py` next to `_hash_fingerprint` — that is where the fingerprint is today, it is a private helper, and moving it costs an import cycle argument nobody has had yet.
2. Return a plain `dict` (or a `str` hash, as `_hash_fingerprint` does today) and skip the dataclasses entirely; `db.py` is a raw-sqlite module, `llm.py` passes a `metadata_dict` around, so dicts are the house style for run metadata.
3. Make them pydantic `BaseModel`s — `curator_response.py` and `config.py` are full of pydantic/dataclass result shapes, and pydantic gives `.model_dump()` for the JSON stamp for free.

**The observable.**
`from bespokelabs.curator.run_identity import RUN_IDENTITY_VERSION, RUN_IDENTITY_FILENAME, RunIdentity, RunStamp, RunDirectoryCheck, RunIdentityError, RunIdentityMismatch, CachedResponseMismatch, compute_run_identity, reconcile_run_directory` imports cleanly;
`dataclasses.is_dataclass(RunIdentity) and dataclasses.is_dataclass(RunStamp) and dataclasses.is_dataclass(RunDirectoryCheck)`;
`[f.name for f in dataclasses.fields(RunIdentity)] == ["run_hash", "digest", "identity_version", "cache_enabled", "components"]`;
`[f.name for f in dataclasses.fields(RunStamp)] == ["identity_version", "run_hash", "digest", "components", "created_at", "updated_at"]`;
`[f.name for f in dataclasses.fields(RunDirectoryCheck)] == ["status", "stamp", "previous_version"]`;
`issubclass(RunIdentityMismatch, RunIdentityError) and issubclass(CachedResponseMismatch, RunIdentityError) and issubclass(RunIdentityError, RuntimeError)`;
`pytest.raises(dataclasses.FrozenInstanceError)` on assigning to `.run_hash`;
`bespokelabs.curator.llm.llm._get_function_hash is bespokelabs.curator.run_identity._get_function_hash`.

**Arbitrary:** invented name — the module path, three dataclass names, three exception names and fourteen field names; nothing in the repo hints at any of them.

### P2 — The twelve components, and which `backend_params` count

**Behaviour.** The key is computed from exactly the twelve keys of `IDENTITY_COMPONENT_KEYS`. Beyond the five things `_hash_fingerprint` already uses, this adds `parse_func_hash`, `backend`, `backend_params`, `return_completions_object`, `system_prompt` and `run_id`, and it always carries `generation_params` (as `{}` when empty) rather than appending it conditionally. `backend` is the **resolved** name read from `llm.backend` (i.e. `self._request_processor.backend`), so `LLM(model_name="gpt-4o-mini")` and `LLM(model_name="gpt-4o-mini", backend="openai")` are the same run. `backend_params` is **filtered to the four keys** of `IDENTITY_BACKEND_PARAM_KEYS` — `azure_deployment`, `base_url`, `batch_size`, `completion_window` — so knobs that change only how the work is done (`max_retries`, `request_timeout`, `require_all_responses`, `batch_check_interval`, `seconds_to_pause_on_rate_limit`, `max_requests_per_minute`, `delete_successful_batch_files`, …) do not fork the cache, and `api_key` is excluded **even though it changes what comes back**, because the components are written to disk in cleartext (P5).

**Alternatives a competent engineer would plausibly choose instead.**
1. Hash the whole `backend_params` dict — it is one `sorted(params.items())` line, exactly what the existing code does for `generation_params` at `llm.py:161-163`, and "any config change is a new run" is the conservative reading.
2. Hash the *declared* `backend` argument (which is `None` for the common auto-detect path) rather than reaching into `self._request_processor.backend`; `backend` is a plain `__init__` parameter and the processor's `backend` property is not obviously public.
3. Leave `system_prompt`, `return_completions_object` and `run_id` out and add only `parse_func_hash` and backend information — the brief's headline complaint is the parse function, and the other three are easy to miss because `_hash_fingerprint` never mentions them.

**The observable.** With a stub LLM `S` (attributes as listed in The API), `dataset_hash="d0"`:
`tuple(sorted(build_components(S, "d0"))) == IDENTITY_COMPONENT_KEYS` and `len(...) == 12`;
`build_components(S, "d0")["backend_params"] == {"base_url": "https://x/v1"}` when `S.backend_params == {"base_url": "https://x/v1", "max_retries": 7, "api_key": "sk-secret", "request_timeout": 30}`;
`"sk-secret" not in canonical_payload(build_components(S, "d0"))`;
`compute_run_identity(S, "d0").run_hash == compute_run_identity(S2, "d0").run_hash` where `S2` differs from `S` only in `backend_params={"base_url": "https://x/v1", "max_retries": 999, "api_key": "sk-other"}`;
and all four of *parse_func differs*, *backend differs*, *system_prompt differs*, *return_completions_object differs* give a **different** `run_hash` from `S`.

**Arbitrary:** chosen value + policy with no local evidence — the four-key allowlist, and the decision that a differing `api_key` or `max_retries` is the *same* run.

### P3 — Canonical payload and the `v3-` run-hash format

**Behaviour.** `canonical_payload(components)` is the literal prefix `"curator-run-identity/v3\n"` followed by `json.dumps(components, sort_keys=True, separators=(",", ":"), ensure_ascii=True)` — one line of JSON, no spaces, keys sorted recursively, non-ASCII escaped. `hash_components` returns the bare `xxh64(payload.encode("utf-8")).hexdigest()` (16 lowercase hex chars). `format_run_hash(digest, cache_enabled=True)` returns `f"v3-{digest}"`; the run hash — and therefore the cache directory name — is that 19-character string, not a bare digest.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep the existing shape: `"_".join(str(x) for x in values)` in a fixed order, `xxh64(...).hexdigest()`, bare 16-char directory names. That is literally the code at `llm.py:151-166`; extending the join list is the minimal diff.
2. Hash a `repr(sorted(components.items()))`, or feed `hashlib.sha256` / `datasets.fingerprint.Hasher` (the library already uses `datasets` hashing machinery for `dataset._fingerprint`) and take the first 16 chars.
3. Version the directory the other way round — a `v3/` parent directory holding bare digests, or no version marker at all, since `run_identity.json` already records `identity_version`.

**The observable.** For the components dict `A` of the End-to-end section:
`canonical_payload(A)` equals, byte for byte, the 393-character string
`'curator-run-identity/v3\n{"backend":"openai","backend_params":{"base_url":"https://api.example.test/v1"},"batch_mode":false,"dataset_hash":"9f1c8e2b7d4a6053","generation_params":{"temperature":0.7},"model_name":"gpt-4o-mini","parse_func_hash":"ef46db3751d8e999","prompt_func_hash":"ef46db3751d8e999","response_format":"text","return_completions_object":false,"run_id":null,"system_prompt":null}'`;
`hash_components(A) == "2917e0582eb73e61"` (`len == 16`);
`format_run_hash("2917e0582eb73e61", cache_enabled=True) == "v3-2917e0582eb73e61"` (`len == 19`);
`hash_components(dict(A, backend="litellm")) == "b6c4a19e2fd0f57a"`.

**Arbitrary:** chosen value + deliberate departure — the prefix string, the compact-JSON canonicalisation and the `v3-` directory prefix all contradict the `"_".join(...)` + bare-hexdigest scheme the surrounding code plainly uses.

### P4 — Caching disabled: an injected `run_id`, never randomness

**Behaviour.** `compute_run_identity(..., cache_enabled=False, run_id=<str>)` puts `run_id` into the components and returns `run_hash == f"v3-nocache-{digest}"` (a 27-character string), so disabled-cache directories are greppable as `v3-nocache-*` and a caller that replays the same `run_id` lands in the same directory. `cache_enabled=False` with `run_id` `None` or `""` raises `RunIdentityError`; `cache_enabled=True` with a non-`None` `run_id` also raises `RunIdentityError`. No source of randomness or time is read anywhere in `run_identity.py`; `LLM.__call__` is the only place that mints a default id, from `os.environ.get("CURATOR_RUN_ID")` or `uuid.uuid4().hex`, and passes it in.

**Alternatives a competent engineer would plausibly choose instead.**
1. Keep `os.urandom(8)`/`uuid4()` inside the identity function guarded by `if disable_cache:` — the existing code at `llm.py:145-146`, one line, and "disabled cache means never reuse" argues for randomness at exactly that spot.
2. Use a timestamp instead of an opaque id (`datetime.now().isoformat()`, or `time.time_ns()`), which sorts nicely on disk and is what a person cleaning up a cache directory would want.
3. Make disabled runs share one directory (e.g. `v3-nocache`, or the normal hash with the arrow/`response.json` deleted first), on the grounds that "don't cache" should not mean "leak a directory per run".

**The observable.** `compute_run_identity(S, "d0", cache_enabled=False, run_id="local-run-7").run_hash` starts with `"v3-nocache-"`, has `len == 27`, and equals the value returned by a second identical call (byte-equal, twice in the same process and across processes);
`compute_run_identity(S, "d0", cache_enabled=False, run_id="other").run_hash != ` that value;
`pytest.raises(RunIdentityError)` for `cache_enabled=False, run_id=None`, for `run_id=""`, and for `cache_enabled=True, run_id="x"`;
`compute_run_identity(S, "d0").cache_enabled is True` and `.components["run_id"] is None`;
and an AST scan of `run_identity.py` finds no import of `datetime`, `time`, `random`, `secrets` or `uuid` and no `urandom` attribute access.

**Arbitrary:** policy with no local evidence + chosen value — the `nocache-` infix, the injected-id contract, and raising when `run_id` is supplied for a cached run.

### P5 — The `run_identity.json` stamp

**Behaviour.** `write_run_stamp` writes `RUN_IDENTITY_FILENAME == "run_identity.json"` into the run directory (creating it with `parents=True, exist_ok=True`) containing exactly six top-level keys — `identity_version`, `run_hash`, `digest`, `components`, `created_at`, `updated_at` — serialised with `json.dumps(payload, indent=2, sort_keys=True)` plus a single trailing `"\n"`. `created_at` is the `created_at` argument when given, otherwise `now`; `updated_at` is always `now`. `read_run_stamp` returns `None` if the file is absent, unreadable as JSON, or missing any of the six keys — it never raises. The stamp is the only place the components are written down, and it is written **before** the run touches the directory for anything else.

**Alternatives a competent engineer would plausibly choose instead.**
1. Don't write a stamp at all: put the components inside `response.json` (`CuratorResponse.metadata` already travels there) or in the `runs` table, both of which already exist, and read them back from there.
2. Name it `metadata.json` / `.curator_run` / `fingerprint.json`, and dump it compactly (`json.dumps(d)`) or with `default=str` so anything serialises.
3. Store only the hash — `run_identity.json` containing `{"run_hash": "..."}` — since the directory name already is the hash and the components are recoverable by recomputing them.

**The observable.** After `write_run_stamp(d, identity_A, now="2025-01-02T03:04:05")`:
`(d / "run_identity.json").read_bytes()` is exactly 663 bytes and 25 lines, its first line is `"{"`, `json.loads` of it has `sorted(keys) == ["components", "created_at", "digest", "identity_version", "run_hash", "updated_at"]`, `["identity_version"] == 3`, `["run_hash"] == "v3-2917e0582eb73e61"`, `["digest"] == "2917e0582eb73e61"`, `len(["components"]) == 12`, and both timestamps equal `"2025-01-02T03:04:05"`. A second `write_run_stamp(d, identity_A, now="2025-01-02T04:00:00", created_at="2025-01-02T03:04:05")` leaves `created_at` at `"2025-01-02T03:04:05"` and sets `updated_at` to `"2025-01-02T04:00:00"`, file still 663 bytes. `read_run_stamp` on a directory whose `run_identity.json` contains `"{not json"` returns `None`.

**Arbitrary:** invented name — filename, the six-key shape, `indent=2, sort_keys=True` + trailing newline; and the `created_at`-preservation policy.

### P6 — Reconciling a directory: four statuses, one raise

**Behaviour.** `reconcile_run_directory(dir, identity, now=...)` decides what a run does with the directory it is about to use, and returns `RunDirectoryCheck(status, stamp, previous_version)`:
- directory missing, or existing and containing **zero** entries → create it, write the stamp, `status="created"`, `previous_version=None`;
- directory non-empty with no readable stamp (a pre-v3 cache directory) → **adopt** it: write the stamp, delete nothing, `status="adopted"`, `previous_version=None`;
- readable stamp with `identity_version < 3` → rewrite the stamp with the current identity, preserving its `created_at`, `status="upgraded"`, `previous_version=<the old int>`;
- readable stamp with `identity_version == 3` and equal `run_hash` and equal `components` → refresh `updated_at` only, `status="matched"`, `previous_version=3`;
- readable stamp with `identity_version > 3` → raise `RunIdentityMismatch` with `mismatched_components == ("identity_version",)`;
- readable stamp with `identity_version == 3` and a different `run_hash` **or** differing `components` → raise `RunIdentityMismatch` with `mismatched_components` = the tuple of component keys whose values differ, sorted alphabetically (`("run_hash",)` if the stamp carries no comparable components), leaving every file on disk untouched.

**Alternatives a competent engineer would plausibly choose instead.**
1. On any mismatch, do what `db.validate_schema` (`db.py:56-62`) does today: raise `RuntimeError` telling the user to `rm -rf ~/.cache/curator` — the established house response to a stale-cache disagreement — or go further and clear the directory automatically, as `attempt_loading_cached_dataset` does for a corrupt arrow file (`base_request_processor.py:379`).
2. Treat a stamp-less non-empty directory as hostile and refuse it (raise), or as worthless and wipe it; adopting someone else's files under your own identity is a judgement call, not an obvious one.
3. Collapse the outcomes to a `bool` ("did we match?") or to `None`/raise, with no status vocabulary at all — the caller only needs to know whether it may reuse the cache.

**The observable.** With `identity_A` (`run_hash "v3-2917e0582eb73e61"`) and `now="2025-01-02T03:04:05"`:
empty `tmp_path/"a"` → `check.status == "created"`, `check.previous_version is None`, `len(os.listdir(a)) == 1`;
`tmp_path/"b"` containing `payload.txt` → `status == "adopted"`, `previous_version is None`, `sorted(os.listdir(b)) == ["payload.txt", "run_identity.json"]` (the file still there, byte-identical);
`tmp_path/"c"` pre-stamped with `identity_version=2` and `created_at="2024-06-01T00:00:00"` → `status == "upgraded"`, `previous_version == 2`, stamp on disk now `identity_version == 3` with `created_at == "2024-06-01T00:00:00"`;
same directory reconciled again → `status == "matched"`, `previous_version == 3`;
`tmp_path/"d"` stamped with `identity_version=4` → `pytest.raises(RunIdentityMismatch)` and `exc.value.mismatched_components == ("identity_version",)`;
`tmp_path/"e"` stamped with the v3 stamp of a *different* identity (components differing in `model_name` and `parse_func_hash`) → `pytest.raises(RunIdentityMismatch)`, `exc.value.mismatched_components == ("model_name", "parse_func_hash")`, `exc.value.found_run_hash` is the stamp's hash, and `os.listdir(e)` is unchanged.

**Arbitrary:** invented name + policy with no local evidence — the four status strings, `mismatched_components` and its alphabetical order, and adopt/upgrade-rather-than-delete, which is the opposite of the surrounding code's instinct.

### P7 — `validate_schema()` migrates forward instead of refusing

**Behaviour.** `MetadataDB.validate_schema()` compares the live `runs` columns to `RUNS_COLUMNS` (now **sixteen**: the fourteen of `db.py:38-52` plus `parse_func` and `identity_version`). Columns present in `RUNS_COLUMNS` and missing from the table are added in `RUNS_COLUMNS` order with `ALTER TABLE runs ADD COLUMN "<name>" <type>`, and the method returns the tuple of names it added (`()` when nothing was added). Columns in the table that are **not** in `RUNS_COLUMNS` are still fatal: `RuntimeError` with the existing "Detected a mismatch …" message. Existing rows keep their values; the added columns are `NULL` for them.

**Alternatives a competent engineer would plausibly choose instead.**
1. Leave `validate_schema` exactly as it is — a symmetric `set(current) != set(expected)` check that raises and tells the user to `rm -rf ~/.cache/curator`. It is the current code, the comment at `db.py:81-83` explicitly instructs you to keep `expected_columns` in sync with `CREATE TABLE`, and there is a test asserting the raise.
2. Migrate by rebuild: `CREATE TABLE runs_new … ; INSERT INTO runs_new SELECT …; DROP TABLE runs; ALTER TABLE runs_new RENAME TO runs` — the canonical sqlite migration, and the only way to also drop unexpected columns.
3. Add a `schema_version` table / `PRAGMA user_version` and run numbered migrations, the standard answer once a schema starts moving.

**The observable.** Against a temp-file DB pre-created with the old fourteen-column `CREATE TABLE` and one row (`run_hash="old"`):
`db.validate_schema() == ("parse_func", "identity_version")`;
afterwards `[c[1] for c in db._get_current_schema()]` has `len == 16` and its last two entries are `["parse_func", "identity_version"]`;
`SELECT parse_func, identity_version FROM runs WHERE run_hash='old'` returns `(None, None)` and the row's other columns are unchanged;
a second `db.validate_schema()` returns `()`;
and against a table created as `CREATE TABLE runs (wrong_col TEXT)`, `pytest.raises(RuntimeError, match="mismatch")` still holds (unexpected column present).

**Arbitrary:** deliberate departure — the code plainly does the opposite (raise on any difference, tell the user to delete their cache), so reading `db.py` leads you away from this.

### P8 — `store_metadata` writes twelve columns and reports what it did

**Behaviour.** The INSERT branch writes twelve columns: the existing ten plus `parse_func` (fixing the silent drop at `db.py:126`, taking `metadata.get("parse_func", "")`) and `identity_version` (`metadata.get("identity_version", RUN_IDENTITY_VERSION)`, stored as an `int`). The UPDATE branch (existing `run_hash`) sets `last_edited_time = metadata["timestamp"]` and sets `session_id` **only when the incoming `metadata["session_id"]` is not `None`**, and never touches `created_time`, `prompt_func`, `parse_func` or the cost columns. `store_metadata` returns the string `"inserted"` or `"updated"`. No clock is read inside `db.py`; `metadata["timestamp"]` remains the only time source.

**Alternatives a competent engineer would plausibly choose instead.**
1. `INSERT OR REPLACE` (or `INSERT … ON CONFLICT(run_hash) DO UPDATE SET …` refreshing every column) — shorter than the select-then-branch the file does today, and it makes the row always reflect the latest run.
2. Keep the update branch exactly as it is (`last_edited_time` only, `db.py:112-119`) and let a new `session_id` be dropped — it is the current behaviour and nothing says a session id may change.
3. Return `None` (as now), or return the row count / the `run_hash`; a status string is not an obvious choice in a module whose other methods return values or nothing.

**The observable.** Against a fresh temp DB, with `m = {"run_hash": "r1", "session_id": "s1", "dataset_hash": "d", "prompt_func": "def p(): pass", "parse_func": "def q(): pass", "model_name": "gpt-4o-mini", "response_format": "text", "batch_mode": False, "timestamp": "2025-01-02T03:04:05", "is_hosted_viewer_synced": False, "identity_version": 3}`:
`db.store_metadata(m) == "inserted"`; the row has `parse_func == "def q(): pass"`, `identity_version == 3`, `created_time == last_edited_time == "2025-01-02T03:04:05"`, and all four `total_*` columns `None`;
`db.store_metadata({**m, "session_id": None, "timestamp": "2025-01-02T04:00:00"}) == "updated"` leaves `session_id == "s1"` and `created_time == "2025-01-02T03:04:05"` while `last_edited_time == "2025-01-02T04:00:00"`;
`db.store_metadata({**m, "session_id": "s2", "timestamp": "2025-01-02T05:00:00"}) == "updated"` sets `session_id == "s2"`;
`SELECT COUNT(*) FROM runs == 1`.

**Arbitrary:** policy with no local evidence — the `None`-means-keep rule for `session_id` and the `"inserted"`/`"updated"` return vocabulary. (The `parse_func` column itself fixes a real bug, `db.py:126`.)

### P9 — `response.json` records the identity and `load` checks the dataset

**Behaviour.** `CuratorResponse` gains a `run_identity: Optional[Dict[str, Any]] = None` field, declared last, which `to_dict()` emits as a top-level `"run_identity"` key. `load(cache_dir, dataset, *, verify=True)` compares the recorded `data["dataset"]` block against the dataset it was handed, in the fixed order `("fingerprint", "size", "columns")` — `dataset._fingerprint`, `len(dataset)`, `list(dataset.column_names)` (ordered comparison) — and raises `CachedResponseMismatch(cache_dir, field, expected, found)` on the **first** field that differs, where `expected` is the recorded value and `found` the live one. `verify=False` skips all three checks. A `response.json` with no `"dataset"` key (written before this change) is loaded without any check, and `run_identity` defaults to `None` when the key is absent.

**Alternatives a competent engineer would plausibly choose instead.**
1. Leave `load` as it is (`curator_response.py:314-352`): it takes the dataset it is given precisely because "the dataset itself is not cached", and the docstring says so.
2. Verify but don't raise: log a warning and return the response anyway, or return `None`, which is what the only caller (`llm._get_cached_response`) does with anything that goes wrong.
3. Compare a different set / a different order — fingerprint only (it is a hash of the other two, so size and columns are redundant), or columns as a `set`, or size first because it is cheapest.

**The observable.** `ds = Dataset.from_list([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])`, response saved into `tmp_path`, then:
`CuratorResponse.load(tmp_path, ds).run_identity == {"identity_version": 3, "run_hash": "v3-2917e0582eb73e61", ...}` (round-trips equal to what was saved) and `json.loads((tmp_path/"response.json").read_text())["run_identity"]["run_hash"] == "v3-2917e0582eb73e61"`;
loading with `other = Dataset.from_list([{"a": 9, "b": "z"}, {"a": 8, "b": "w"}])` → `pytest.raises(CachedResponseMismatch)` with `exc.value.field == "fingerprint"`, `exc.value.expected == ds._fingerprint`, `exc.value.found == other._fingerprint`;
after rewriting `response.json` with `data["dataset"]["fingerprint"] = other._fingerprint` and `["size"] = 99` → `field == "size"`, `expected == 99`, `found == 2`;
after also fixing size and setting `["columns"] = ["b", "a"]` → `field == "columns"`, `expected == ["b", "a"]`, `found == ["a", "b"]`;
`CuratorResponse.load(tmp_path, other, verify=False)` returns a response with `len(r.dataset) == 2`;
and a `response.json` with the `"dataset"` key deleted loads without raising, `r.run_identity is None`.

**Arbitrary:** invented name + policy — `CachedResponseMismatch` with its four attributes, the fixed check order, ordered column comparison, and the legacy-tolerance rule.

### P10 — `_get_cached_response` stops swallowing identity errors

**Behaviour.** `LLM._get_cached_response` (`llm.py:171`) re-raises any `RunIdentityError` (hence `CachedResponseMismatch` and `RunIdentityMismatch`) unchanged, and keeps returning `None` — with the existing `logger.warning` — for every other exception, including `FileNotFoundError` and `json.JSONDecodeError`. A cache directory that does not describe this run therefore fails the call loudly instead of degrading to a stats-free response.

**Alternatives a competent engineer would plausibly choose instead.**
1. Leave the `except Exception: return None` as is — it is the current code and it is deliberately defensive; a cache that cannot be read should never break a run that has already produced its dataset.
2. Invert it: let everything propagate, since a missing `response.json` is now a genuine inconsistency once the directory is stamped.
3. Catch identity errors here and recover — delete the offending `response.json`/directory and re-run — which is what `attempt_loading_cached_dataset` does with a corrupt arrow file.

**The observable.** With `CuratorResponse.load` monkeypatched:
raising `CachedResponseMismatch("/c", "fingerprint", "a", "b")` → `pytest.raises(CachedResponseMismatch)` from `LLM._get_cached_response(stub_self, "/c", ds)` and the propagated object is the same instance (`exc.value.field == "fingerprint"`);
raising `RunIdentityMismatch("/c", "v3-a", "v3-b", ("model_name",))` → propagates;
raising `FileNotFoundError("response.json")` → returns `None`;
raising `ValueError("boom")` → returns `None`.

**Arbitrary:** deliberate departure — the surrounding code catches `Exception` and returns `None`, and an engineer touching this file has every reason to keep it that way.

### P11 — `_is_cached_dataset` is reset at the start of every run

**Behaviour.** `BaseRequestProcessor.run()` sets `self._is_cached_dataset = False` as its first statement, before `attempt_loading_cached_dataset` is consulted, so the flag describes *this* run rather than the most recent cache hit on this processor object. Nothing else about `run()` changes.

**Alternatives a competent engineer would plausibly choose instead.**
1. Leave it (`base_request_processor.py:57` is the only assignment to `False`): a processor is conceptually one run, and the stale-flag path only shows up when the same `LLM` object is called twice with different inputs.
2. Reset it from the caller in `LLM.__call__`, next to where it is read at `llm.py:300`, or read it as a return value from `run()` instead of an attribute.
3. Reset it in `attempt_loading_cached_dataset` — the function that also sets it — which looks tidier but leaves the flag stale on the branch that never calls it.

**The observable.** Call `BaseRequestProcessor.run` unbound on a `SimpleNamespace` stub with `_is_cached_dataset=True`, `attempt_loading_cached_dataset=lambda h: None`, `config=SimpleNamespace(model="m")`, `prompt_formatter=None`, and `validate_config` raising a sentinel `_Stop`: `pytest.raises(_Stop)` and, afterwards, `stub._is_cached_dataset is False`. With `attempt_loading_cached_dataset=lambda h: ds` instead, `run(...)` returns `ds` and `stub._is_cached_dataset is True`.

**Arbitrary:** none — derivable from `base_request_processor.py` (it is a plain bug fix); included because it is the concrete way "the caller gets whichever run finished last" shows up in the response object, and it is exactly measurable.

## End to end

**Inputs.** A stub LLM object (no processor, no event loop, no network):

```python
from types import SimpleNamespace

S = SimpleNamespace(
    prompt_formatter=SimpleNamespace(
        prompt_func=None,                 # _get_function_hash(None) -> "ef46db3751d8e999"
        parse_func=None,                  # same
        model_name="gpt-4o-mini",
        response_format=None,             # -> "text"
        generation_params={"temperature": 0.7},
        system_prompt=None,
    ),
    batch_mode=False,
    backend="openai",
    backend_params={"base_url": "https://api.example.test/v1", "max_retries": 7, "api_key": "sk-secret"},
    return_completions_object=False,
)
dataset_hash = "9f1c8e2b7d4a6053"
now = "2025-01-02T03:04:05"
```

**Step 1 — components and key.**

```python
A = build_components(S, dataset_hash)
# A == {
#   "backend": "openai",
#   "backend_params": {"base_url": "https://api.example.test/v1"},
#   "batch_mode": False,
#   "dataset_hash": "9f1c8e2b7d4a6053",
#   "generation_params": {"temperature": 0.7},
#   "model_name": "gpt-4o-mini",
#   "parse_func_hash": "ef46db3751d8e999",
#   "prompt_func_hash": "ef46db3751d8e999",
#   "response_format": "text",
#   "return_completions_object": False,
#   "run_id": None,
#   "system_prompt": None,
# }
canonical_payload(A)          # 393 chars, starts "curator-run-identity/v3\n{"backend":"openai",..."
hash_components(A)            # "2917e0582eb73e61"
identity = compute_run_identity(S, dataset_hash)
# RunIdentity(run_hash="v3-2917e0582eb73e61", digest="2917e0582eb73e61",
#             identity_version=3, cache_enabled=True, components=A)
```

**Step 2 — the directory.** `d = tmp_path / "v3-2917e0582eb73e61"` does not exist.

```python
check = reconcile_run_directory(d, identity, now=now)
# RunDirectoryCheck(status="created", stamp=RunStamp(3, "v3-2917e0582eb73e61",
#   "2917e0582eb73e61", A, "2025-01-02T03:04:05", "2025-01-02T03:04:05"), previous_version=None)
stamp = check.stamp
(d / "run_identity.json").stat().st_size        # 663
```

**Step 3 — the metadata row.**

```python
db = MetadataDB(str(tmp_path / "metadata.db"))
db.store_metadata({
    "run_hash": "v3-2917e0582eb73e61", "session_id": "s1", "dataset_hash": "9f1c8e2b7d4a6053",
    "prompt_func": "def prompt(self, input): return input", "parse_func": "def parse(self, i, r): return r",
    "model_name": "gpt-4o-mini", "response_format": "text", "batch_mode": False,
    "timestamp": now, "is_hosted_viewer_synced": False, "identity_version": 3,
})                                               # -> "inserted"
# row: parse_func == "def parse(self, i, r): return r", identity_version == 3,
#      created_time == last_edited_time == "2025-01-02T03:04:05",
#      total_cost_milli_dollars is None
```

**Step 4 — the response.**

```python
ds = Dataset.from_list([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])
resp = CuratorResponse(dataset=ds, cache_dir=str(d), model_name="gpt-4o-mini",
                       run_identity=stamp.to_dict())
resp.save(d)
json.loads((d / "response.json").read_text())["run_identity"]["run_hash"]   # "v3-2917e0582eb73e61"
CuratorResponse.load(d, ds).run_identity["digest"]                          # "2917e0582eb73e61"
CuratorResponse.load(d, Dataset.from_list([{"a": 9, "b": "z"}, {"a": 8, "b": "w"}]))
# CachedResponseMismatch: field == "fingerprint", expected == ds._fingerprint
```

**Step 5 — only the parse function changes.** `S.prompt_formatter.parse_func` is replaced by a function whose `_get_function_hash` is `"0123456789abcdef"`:

```python
hash_components(dict(A, parse_func_hash="0123456789abcdef"))   # "9287bfc821a74872"
# run_hash "v3-9287bfc821a74872" -> a different directory; the old response.json is not overwritten.
reconcile_run_directory(d, compute_run_identity(S, dataset_hash), now="2025-01-02T06:00:00")
# RunIdentityMismatch: mismatched_components == ("parse_func_hash",),
#                      found_run_hash == "v3-2917e0582eb73e61"
```

**Step 6 — knobs that are not identity.** `S.backend_params = {"base_url": "https://api.example.test/v1", "max_retries": 999, "api_key": "sk-other", "request_timeout": 5}` (parse function restored):

```python
compute_run_identity(S, dataset_hash).run_hash                 # "v3-2917e0582eb73e61"  (unchanged)
reconcile_run_directory(d, identity, now="2025-01-02T07:00:00").status   # "matched"
json.loads((d / "run_identity.json").read_text())["updated_at"]          # "2025-01-02T07:00:00"
json.loads((d / "run_identity.json").read_text())["created_at"]          # "2025-01-02T03:04:05"
```

**Step 7 — caching disabled.**

```python
compute_run_identity(S, dataset_hash, cache_enabled=False, run_id="local-run-7").run_hash
# "v3-nocache-b603a4eb3536a157"   (27 chars, identical on every repeat of the same run_id)
compute_run_identity(S, dataset_hash, cache_enabled=False, run_id=None)
# RunIdentityError
```
