The response ledger: what counts as a recorded response in `responses_*.jsonl`, and
what "succeeded" means when somebody counts them.

The area, concretely:
- `src/bespokelabs/curator/request_processor/online/base_online_request_processor.py` —
  `handle_single_request_with_retries()`, whose exhausted-retry path (lines 544-563)
  builds an explicit failure record (`GenericResponse(response_message=None,
  response_errors=formatted_errors, ...)`), hands it to `append_generic_response`
  (line 561) and increments `status_tracker.num_tasks_failed` (line 563); and
  `append_generic_response()` (line 614), which computes
  `responses = self._process_response(data)` and returns at lines 624-625 on
  `if not responses:` — so that record is never written, and a `parse_func` that
  legitimately returns `[]` is dropped the same way. It advances the viewer index
  by `len(responses)` (line 635).
- `src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py` —
  `_process_single_response()` (line 568), which drops on a different predicate,
  `if processed_responses is None` (line 608), and records the index in
  `failed_processed_responses` (line 609); the writer at line 520 opens the file
  in `"a"` mode, and `resubmit_batch()` (line 731) re-submits the same
  `request_file`, so one `original_row_idx` can occupy two lines. And
  `_update_final_stats()` (line 794): `sucessful_responses += sum(1 for _ in f)`
  over every `responses_*.jsonl`, then
  `n_final_failed_requests = n_total_requests - sucessful_responses` (line 804).
- `src/bespokelabs/curator/request_processor/offline/base_offline_request_processor.py` —
  `process_requests_from_file()` (lines 179-189), the third answer: write every
  response unconditionally, and advance `num_parsed_responses` by the whole batch
  length (line 188) rather than by the parsed count.
- `src/bespokelabs/curator/request_processor/base_request_processor.py` —
  `_get_validated_response()` (line 583): valid iff `not response_errors` AND
  `response_message is not None`. `validate_existing_response_file()` (line 609):
  assumes failed lines ARE in the file so it can strip them, rewrites the file in
  place through `response_file + ".temp"` and `os.replace` (line 649), and returns
  two different units at once — `completed_request_ids` (requests) and
  `completed_parsed_responses` (`parse_func` rows, line 638).
  `create_dataset_files()` (line 422): a raw line count (line 458), its own failure
  predicate (lines 460-461 and 470-472, which double-count a response that is both
  errored and unparseable), `failed_requests.jsonl` derived from a third source
  (the arrow file’s `__original_row_idx`, lines 510-517), and a fourth
  reconciliation against `count_lines(requests_*.jsonl)` (lines 543-545).
  `_process_response()` (line 387) catches only
  `(json.JSONDecodeError, ValidationError)` at lines 389-391.
- `src/bespokelabs/curator/types/curator_response.py` — `update_tracker_stats()`
  (lines 203-216), the user-visible number, which reads the line-count ledger
  (`n_final_success_requests`) in batch mode and the in-memory counters
  (`num_tasks_succeeded` / `num_tasks_failed`) — incremented for records that were
  never written — in online mode.
- `src/bespokelabs/curator/llm/prompt_formatter.py` — `response_to_response_format()`
  (line 175) does `self.response_format(**response_dict)`; the failure record above
  carries `response_message=None`, so `response_dict` is `None` and this raises
  `TypeError`, which `_process_response` does not catch.

Three writers and four readers disagree about what a line in `responses_*.jsonl` is,
and the disagreement is reachable. The online writer says a permanently failed
request leaves no line while its tracker counts it as failed; the batch writer says
the same on a different predicate and appends, so a resubmission duplicates a row;
the offline writer says every response is written. Then `_update_final_stats` says
every line is a success — errors and duplicates included — so
`n_final_failed_requests` goes negative after a resubmission, while
`validate_existing_response_file` resumes on the opposite assumption, that failed
lines are there to be stripped. Read all of it and design the fix as one fully
specified ledger: what a durable record is, which requests must have one, the unit
every count is expressed in, and one place that answers "how many succeeded".

Out of scope, because other tasks own them: `create_request_files`,
`_get_optimal_batch_size` and `create_batch_file`; and the run cache fingerprint,
`attempt_loading_cached_dataset`, `MetadataDB` and `CuratorResponse.save`/`load`.

Constraints: pure and deterministic, no network, no sleeping, no threads. The clock
is injected, never read inside the ledger code. The design must be testable by
calling the validation and counting functions directly on hand-written
`requests_N.jsonl` / `metadata_N.json` / `responses_N.jsonl` files under a temp
directory, by driving `append_generic_response` and `_process_single_response`
under `asyncio.run` with a concrete `BaseRequestProcessor` subclass stub and an
async no-op viewer client, and by round-tripping `create_dataset_files` on a two-
or three-row in-memory `datasets.Dataset` — no provider, no event loop of its own,
no aiohttp session.
