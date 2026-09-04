# Hidden requirements — g5 (response-ledger)

## r1
- **rule** — When `ResponseLedger.load` finds more than one response line for the same `original_row_idx`, the winner is the one with the best status — `SUCCEEDED` beats `EMPTY` beats `UNPARSEABLE` beats `FAILED` — never simply the most recently written line.
- **scope** — Applies across every `responses_N.jsonl` found under one `working_dir` (not per-file), including lines produced by a later batch resubmission of the same request.
- **exclusions_or_crossover** — A later-written `FAILED` retry for a request that already has an earlier `SUCCEEDED` line must NOT shadow that earlier success; the earlier success still wins even though it is not the last line in the append log.
- **observability** — Given `responses_0.jsonl` written in order — idx 7 `FAILED`, idx 7 `SUCCEEDED`, idx 5 `SUCCEEDED('first')`, idx 5 `SUCCEEDED('second')` — `ResponseLedger.load(...).winning_records()` yields idx 5 = `'first'` (tie broken by earliest position, not last-write) and idx 7 = the `SUCCEEDED` line (status beats recency), with `tally().n_duplicate_lines == 2`.
- *earlier, reversed*: an earlier build resolved duplicates by simply keeping the last line seen per idx (natural for an append-only log, and what `resubmit_batch` writing into the same file superficially suggests), which was reversed after a resubmitted-batch run showed a good earlier answer getting silently shadowed by a later timeout

## r2
- **rule** — `read_resume_state` (and `validate_existing_response_file` built on it) must never modify the response file it reads — no temp-file rewrite, no truncation — and must treat a winning `EMPTY` record's request as done while a winning `UNPARSEABLE` record's request is still retryable.
- **scope** — Applies to the single response file being resumed, using the same within-file duplicate-winner folding as the ledger, before any new requests are issued.
- **exclusions_or_crossover** — An `EMPTY` parse (the call succeeded but produced zero rows) is folded into the same completed set as `SUCCEEDED`, not into the retry set; an `UNPARSEABLE` response (a body that arrived but never parsed) is folded into the same retry set as `FAILED`, even though a response body did come back.
- **observability** — For a response file with one winning record each of `SUCCEEDED`, `FAILED`, `EMPTY`, and `UNPARSEABLE`, the returned `ResumeState` has `completed_row_indices` containing exactly the `SUCCEEDED` and `EMPTY` indices and `retryable_row_indices` containing exactly the `FAILED` and `UNPARSEABLE` indices, while the file's byte content and line count are identical before and after the call and no `*.temp` file appears in the directory afterward.
- *earlier, reversed*: the code this replaces opened the response file in "a", wrote a .temp copy stripped of failing lines, and os.replaced it into place on every resume so the file stayed a success-only log; that rewrite-on-resume behavior is what gets reversed here
