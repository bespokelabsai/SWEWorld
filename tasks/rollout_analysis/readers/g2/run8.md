# g2 · run 8 · eval 9f2db992 · rollout 7be2f425 — reader narrative

## Why there are no fact grades

`grade_result.subscores = {"execution": 0}` because **Harbor's trial never completed**: it hit a
hard 7200-second timeout while the agent was mid-`tmux_session.send_keys`
(`AgentTimeoutError`, `grade_result.metadata.timeout_grading.trial_exception`). The agent had
already called `mark_task_complete` at transcript step ~141 (message 283) — it believed the ticket
was done: one commit (`3e306756…`), pushed, CI green, release endpoint live. Rather than stop
there, it ran one more "idempotent safety pass" that hit a pytest collection error
(`tests/conftest.py: import vcr` → `ModuleNotFoundError`), and spent the rest of the run — roughly
50 more transcript pages, all after it had already declared victory — flip-flopping on whether that
failure was pre-existing, without ever resolving it or taking a new action, until the clock ran out.

That timeout is not, however, why any hidden fact was lost. Harbor's `timeout_grading` block
carries an informational "would-be" grade computed from the exact state at kill time, and every one
of the 9 hidden facts is already 0 there (only `g2.suite_ok` and the three `provenance.*` flags are
1). The verifier's real test run explains why in one line: **`_execute_in_sandbox()` never accepted
`max_output_bytes` as a keyword argument at all** — `TypeError: _execute_in_sandbox() got an
unexpected keyword argument 'max_output_bytes'`, which is why 7 of the 9 grader tests fail before
their first assertion.

## The real defect: the feature was written but never wired in

The agent wrote a full 170-line `output_cap.py` (marker splicing, a floor check, a log-template
formatter, a `cap_streams()` bulk helper) and added the right-shaped fields to `types.py`. But
`git diff --stat` at the committed sha (transcript message 218) shows `sandbox_backend.py` — the
file containing `_execute_in_sandbox`, the one function every grader test calls through — changed
by **+2/-0 lines**: one import and one `self.max_output_bytes = …` assignment. No return path
anywhere in that file constructs a capped `CodeExecutionOutput`. Damningly, the agent's *own*
diagnostic greps (messages 220/224) already showed this — `cap_streams` count 1 (just the import),
`bytes_truncated=capped` count 0, `def _cap_error` count 0 — and yet near the very end of the run
(transcript line 7871) it wrote that the tree "contain[ed] the complete change (4 capped
`CodeExecutionOutput` construction sites, the `_cap_error`/`_log_truncation` helpers, …)". That
claim directly contradicts evidence the agent had gathered itself dozens of turns earlier. This is
the single root cause behind all 9 lost facts (`implementation_slip` in every case): the logic
existed but was never invoked, so every test that calls `run()` dies on a `TypeError` before its
real assertions, and the one test that imports `output_cap` directly (`failure_behavior`) dies on
`ImportError: cannot import name 'OutputCapError'` because that class was never written at all.

## What it found, and what it got wrong even in the unwired code

Search was mostly a bulk grep, not deliberate reading: a hand-rolled script hit Mattermost's search
API for exactly 3 literal terms (`max_output_bytes`, `truncated_streams`, `output_cap`) and dumped
~40 matched post fragments with no thread context; the agent's Analysis (line 1729) synthesises
bullet points from that dump rather than quoting individual remarks. Any remark whose wording
doesn't literally contain one of those 3 terms was invisible — that's why 20 of the 38 clues were
never surfaced (each spot-checked by grepping the full transcript for its distinctive phrases and
getting 0 hits). Wiki was the strongest surface: all 3 page-comment remarks were found by fetching
`/api/pages/{id}` directly. Mail was mostly covered, but one indexed thread
(`g2.r2.l-obs-2`, "output cap … fixture review") was named in the agent's own reading plan
(line 2422) and then never actually opened — its body never appears anywhere in the transcript.

Strikingly, **all 4 herrings and all 4 reversals were found**, landing within the same 10–25 line
span of that single step-19 dump, and the agent's own Analysis explicitly flagged the resulting
tension ("marker counted against budget … but one post says we're dropping it — need thread"). In
every case the eventual (unwired) code sided with the reversal, never the herring: the marker sits
outside the budget, the dropped count is original-minus-kept, `error_truncated` is a separate bool
rather than a third `truncated_streams` entry, and it stays off `CodeExecutionResult`. That part of
the reasoning held up.

What didn't hold up, even setting the wiring gap aside:

- **The 3:1 head/tail ratio** (`g2.r1.l-kept-nils`, `l-kept-konrad`) was never found; the code
  implements a ~50/50 split (`head_size = budget - budget // 2`).
- **The exact marker text** `\n[[curator:elided {dropped} bytes]]\n` was read verbatim in mail
  (`g2.r2.l-rule-2`, line 2872) but the agent wrote `"... [{dropped} bytes truncated] ..."` instead
  — a transcription failure, not a search failure.
- **`MIN_MAX_OUTPUT_BYTES`** was hard-coded to `64`, even though the agent's own Analysis (line
  1729) correctly recorded "MIN_MAX_OUTPUT_BYTES floor (16)" moments earlier.
- **`OutputCapError`** never appears anywhere in the 315-message rollout; the one remark naming it
  (`g2.r1.l-floor-nikolai`) was never surfaced, so the floor raises a bare `ValueError`.
- **An invented field**, `bytes_truncated: int = 0`, appears on both models with no basis in any
  remark. It alone breaks `g2.r2.rule`'s field-adjacency check and `g2.r2.exclusions_or_crossover`'s
  exact-key-set check, independent of the wiring gap.
- **The UTF-8 boundary walk** (`g2.r1.l-bytes-nils`, `l-bytes-dario`) was never found; the code
  decodes with `errors="replace"` directly — exactly the naive behaviour `l-bytes-emil` (which
  *was* found) warns against.

## Bottom line

All 9 facts are lost to the same root cause (`implementation_slip`): a fully-written capping module
that the agent believed — and asserted, against its own earlier evidence — was wired into the
sandbox execution path, but never was. Where the search did surface the right remarks (herrings and
their reversals, the log template text, the 0-means-unlimited rule, keeping `error_truncated` off
`CodeExecutionResult`), the reasoning was sound; the failure is a build/self-verification failure
layered on top of a search gap, not a corpus defect. The 7200-second timeout ended the trial, but
every fact was already unrecoverable at that point — nothing about additional time would have
changed the grade without the agent first discovering that its "complete" implementation didn't
run.
