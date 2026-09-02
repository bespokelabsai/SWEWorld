Run cache identity: what makes two curator runs "the same run", and what a caller
gets back when the cache says they are.

The area, concretely:
- `src/bespokelabs/curator/llm/llm.py` — `_hash_fingerprint()` (line 144), which
  joins five things with `_` (lines 151-159: `dataset_hash`, `prompt_func_hash`,
  `model_name`, the `response_format` JSON schema, `batch_mode`) plus
  `generation_params` when set (lines 161-163) and xxh64s the result; the
  `disable_cache` branch (lines 145-146), which hashes `os.urandom(8)` instead, so
  every such run mints a fresh directory nothing ever removes; `__call__`
  (line 187), where `run_cache_dir = os.path.join(curator_cache_dir, fingerprint)`
  (line 224) is created before anything about it is validated; and
  `_get_function_hash()` (line 337), which pickles the function with
  `datasets.utils._dill` after mutating `func.__annotations__ = {}`.
- The things the fingerprint does NOT contain, each of which changes what comes
  back: `parse_func` — hashed separately at line 274 and handed to the processor
  as `parse_func_hash`; the backend and `backend_params`; and
  `return_completions_object`.
- `src/bespokelabs/curator/request_processor/base_request_processor.py` —
  `attempt_loading_cached_dataset()` (line 363), the second cache key: a file
  named `f"{parse_func_hash}.arrow"` (line 372) INSIDE the directory the first key
  chose, deleted and regenerated on `pyarrow.lib.ArrowInvalid` (lines 378-384).
- `src/bespokelabs/curator/db.py` — `MetadataDB`, the third account of the same
  run. `validate_schema()` (line 30) lists fourteen `expected_columns` (line 38)
  and raises `RuntimeError` telling the user to `rm -rf ~/.cache/curator` on any
  mismatch; `store_metadata()` (line 64) is handed a dict that also carries
  `timestamp` and `parse_func` (`llm.py` lines 253-262), and its INSERT (line 126)
  writes ten columns — dropping `parse_func` silently, and never writing any of
  the four `total_*` cost columns the schema declares (lines 49-52).
- `src/bespokelabs/curator/types/curator_response.py` — `save()` (line 297) and
  `load()` (line 314), the fourth. `to_dict()` (line 248) records the dataset's
  `fingerprint`, size and columns; `load(cache_dir, dataset)` takes the dataset it
  is handed and never compares it against what was recorded.
  `_get_cached_response()` (`llm.py` line 171) swallows every exception from it and
  returns `None`.

Four layers disagree about what makes two runs the same run, and the disagreement
is reachable. Change only the parse function and the fingerprint is identical, so
the run lands in the same directory, the same `response.json` is overwritten, and
the caller gets back whichever parse function ran last. Change the backend or
`backend_params` and none of the four keys notices. Set `CURATOR_DISABLE_CACHE`
and a directory and a metadata row are minted per run under a random `run_hash`,
and neither is ever collected. Read all four and design the fix as one fully
specified run-identity rule: what participates in the key, where the key is
written down so a later run can check it, and what happens when what is on disk
was written under a different one.

Constraints: pure and deterministic, no network, no sleeping, no threads. The
clock and any source of randomness are injected, never read from `datetime`,
`time` or `os.urandom` inside the identity code. The design must be testable by
calling the key function directly on an LLM-shaped object, by driving `MetadataDB`
against a temp-file database, and by round-tripping `CuratorResponse.save`/`load`
on a small in-memory `datasets.Dataset` — no provider, no event loop, no viewer
client.
