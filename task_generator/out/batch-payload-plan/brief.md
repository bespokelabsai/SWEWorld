Batch payload planning: how curator decides how many requests go into one batch
file when `batch_size="auto"`, and how big that file will be.

The area, concretely:
- `src/bespokelabs/curator/request_processor/base_request_processor.py` —
  `create_request_files()` and the nested `_get_optimal_batch_size()` (~line 263),
  plus `acreate_request_file()` which writes the rows.
- `src/bespokelabs/curator/request_processor/batch/base_batch_request_processor.py` —
  `create_batch_file()` (~line 356), which builds the payload that is actually
  submitted and raises ValueError when it is too large.
- The per-provider limits: `max_requests_per_batch` / `max_bytes_per_batch` on the
  openai, anthropic, mistral and gemini batch processors.

The two sides currently disagree about how big a batch is, and the disagreement is
reachable. Read both and design the fix as one fully specified planner.

Constraints: pure and deterministic, no network, no sleeping, no threads. The
design must be testable by calling functions directly and by driving
`create_request_files` with a small in-memory `datasets.Dataset`.
