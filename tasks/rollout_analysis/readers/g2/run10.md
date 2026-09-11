# g2 run 10 (rollout 7919e169, eval 9f2db992) — reward 0.7778

## What this run found

A thorough, well-organized rollout that got 7 of 9 hidden facts. The agent cloned the repo, read
the ticket, then worked its sources in a sensible order: wiki first (via `/api/pages/{id}`, so it
correctly pulled comments, not just `/api/search` snippets — it found all 3 wiki-comment clues,
including the two that fixed `r2`'s field name and semantics in the first 10 steps), then all 142
mail messages dumped to a local file and read/greped offline (5/5 mail clues found), then Mattermost
chat. Chat is where the run went from complete to incomplete: it started from the four channels that
Mattermost's own text search surfaced early (`#pipeline`, `#releases`, `#code-review`, `#viewer`) and
mined those exhaustively — this is where the large majority of the 29 found clues, and both
reversals with their herrings, came from. It never listed the full channel roster until step ~93,
well after the code had already been committed, pushed, and deployed. At that point it dumped
`#engineering`, `#incidents` and `#help`, but not `#cookbooks` or `#general` — and grepped the batch
with an already-known, narrow term list (`max_output_bytes|output_cap|truncated_streams|elided|capped`)
that misses plain-English phrasing ("output cap" without the underscore) and topically-disguised
remarks that never use a cap-related word at all.

## What it missed, and why

Both lost facts trace to the same unvisited channel. **`#cookbooks`** held 6 of the 46 remarks and
was never dumped anywhere in the 98-step run — its channel id appears exactly once, in a roster
listing at the very end, and never as an argument to any dump command. Three of those six are the
ones that would have closed both gaps:

- `g2.r1.failure_behavior` (0): the test wants `OutputCapError(ValueError)` with a `.max_bytes`
  attribute, importable from `output_cap.py`. The shipped code uses a plain `ValueError` instead —
  the agent's own closing summary says so outright ("implemented via ValueError in validate"). The
  remarks that name the class (`g2.r1.l-floor-nikolai`, `g2.r1.l-floor-konrad`) are both in
  `#cookbooks`; a third (`g2.r1.say26`, in `#incidents`, which *was* dumped) was missed anyway
  because its wording ("field_validator", "ValidationError", "the batch size check") shares no
  token with the grep list used. The agent did find the floor *value* (16) and the constant *name*
  (`MIN_MAX_OUTPUT_BYTES`) from `#pipeline`/`#code-review`, and implemented those correctly — only
  the exception class was lost, cause: **not_found**.

- `g2.r1.observability` (0): the shipped `_execute_in_sandbox` caps and logs once in the normal
  return path, and *again* inside the `except Exception` handler. In the failing fixture (a clean
  300-byte stdout capture followed by `__exit__` raising), Python fully evaluates the success-path
  `return CodeExecutionOutput(...)` — including its `_log_truncation` call — before the context
  manager's exception aborts the return and falls into the except block, which logs a second,
  identical warning. The one remark that would have prevented this, `g2.r1.l-log-konrad` ("the
  except handler's salvage cap logs nothing, we log where we cut"), lives in `#cookbooks` and was
  never seen. The agent *did* find and correctly implement the sibling remarks `l-log-gideon` and
  `l-log-emil` (both `#pipeline`) — exact template wording, sorted stream order, "only on runs that
  actually lost bytes" — everything except the except-path silence. Cause: **not_found**.

Both are retrieval failures, not reasoning failures: nothing in the agent's own analysis
contradicts the corpus, and nothing it read argued the other way. It simply never opened the one
channel that carried the missing half of `r1`'s failure/observability story.

## What it believed, and why

All four herrings were seen and correctly resisted. The two `r1` herrings (marker counts against
the budget; dropped-count = original − cap) were read together with their reversals in the same
`#pipeline` channel dump, and the agent's analysis explicitly names the supersession ("old rule ...
superseded") before implementing the reversed version. `g2.r2.h2` (the "`truncated_streams` lives on
both models" herring) was likewise seen alongside its reversal in one `#viewer` read. `g2.r2.h1`
("error rides in `truncated_streams` as a third entry") is the interesting case: its reversal
(`g2.r2.rev1`) is *also* stuck in `#cookbooks` and was never seen, yet the shipped code still gets
it right, because two independent, much earlier sources — wiki pages 132 and 133, read in the
run's first ten steps — had already settled the same correct answer (`error_truncated` on
`CodeExecutionOutput` only) before the agent ever encountered the herring text. Redundant planting
saved this fact even though one of its paths was completely closed off.

## Why each lost fact was lost

Both lost facts (`failure_behavior`, `observability` on `r1`) reduce to one search gap:
`#cookbooks` was never enumerated, let alone dumped, at any point in the run — not during the
initial exploration, and not even during the final "make sure I haven't missed anything" sweep,
which checked `#engineering`/`#incidents`/`#help` but stopped short of `#cookbooks` and `#general`.
That sweep also happened *after* the commit was pushed and CI had already gone green, so even a
late find would not have reached the shipped code without a further push, which never occurred.
