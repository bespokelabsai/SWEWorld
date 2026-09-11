# g2 run 1 (6d73e7af, eval 9f2db992) — reward 0.8889

## What this run found

The agent's search across chat, wiki and mail was thorough and well-executed. In chat it built a
keyword-filtered chronological digest over *all* channels (258 matching lines, L1923-1936) and
read every chunk in order, correctly resolving each reversal against its herring rather than
taking the first-seen claim (e.g. L2031: "'error' as a third entry in truncated_streams — later
reversed on May 5 in favour of error_truncated bool on CodeExecutionOutput"). In the wiki it
side-stepped the trap the ticket itself warns about — `/api/search` not indexing comments — by
enumerating and fetching all 231 pages whole (L1195-1283), which is exactly how it caught all
three comment-only remarks (`g2.r2.l-cross-1`, `g2.r2.l-rule-4`, `g2.r1.l-log-nikolai`). In mail it
ran an IMAP `SEARCH` against the whole admin mailbox and read all five relevant threads. Of the 46
answer-key remarks, 44 were found and correctly acted on; all four herrings were identified as
superseded and none of them shows up in the shipped code.

The result: 8 of 9 hidden-requirement facts scored 1, plus all three provenance facts (pushed, CI
green, deployed). `g2.r1.rule`, `.scope`, `.exclusions_or_crossover` and `.observability` all
match the answer key's rule almost exactly — three-quarter head / one-quarter tail, marker outside
the budget, dropped-byte count as original-minus-kept, UTF-8 boundary backoff up to three bytes,
`0` as the off-switch, equal-to-budget not counted as truncated, and the
`sandbox output capped: {streams} exceeded the {budget}-byte budget` warning logged exactly once
at the cut site rather than in the `except` handler. All four `g2.r2` facts also passed:
`error_truncated` lives on `CodeExecutionOutput` only, defaults `False`, sits directly under
`truncated_streams`, and the composed exit-code/timeout sentences are correctly exempted from
re-capping.

## What it missed, and why

Only `g2.r1.failure_behavior` scored 0, and it traces to exactly two remarks — both carrying that
fact, and both with **zero hits** anywhere in the transcript:

- `g2.r1.l-floor-konrad` (#cookbooks, 2025-03-17 09:41): "...we hang the offending value on the
  exception as `.max_bytes` and the message can keep saying whatever it says" — the remark that
  states `OutputCapError` must expose the rejected value as an attribute.
- `g2.r1.say26` (#incidents, 2025-03-14): "...the field_validator hands the offending value
  straight into that error, and pydantic's ValidationError comes back out carrying its message
  verbatim" — the remark that says the floor check belongs in a `CodeExecutionBackendConfig`
  `@field_validator`, not only inside the backend.

Both are genuine search misses, not misreadings — the phrases never appear in the transcript at
all (verified by grep for `.max_bytes`, `field_validator`, `hang the offending value`, `regex the
traceback`). The cause is mechanical: the agent's chat digest used a fixed keyword list
(`truncat`, `output_cap`, `max_output_bytes`, `marker`, `budget`, `MIN_MAX`, `stdout`, `stderr`,
`" cap"`, `floor`; L1923), and neither remark contains any of those words — `l-floor-konrad` says
`max_bytes`, never `max_output_bytes`, and never says "cap" as a standalone word; `say26` never
mentions capping or truncation vocabulary at all, phrasing the same idea as an analogy about "the
batch size check". The mail IMAP search and the wiki full-page dump wouldn't have caught these two
either, since both live only in Mattermost. This is exactly the kind of remark the MuSR-style
planting is designed to hide from a keyword-driven search: it carries the fact's information
without ever using the fact's own vocabulary.

The consequence in the shipped code (transcript L3620-3670): `OutputCapError` is defined with no
custom `__init__` —

```python
class OutputCapError(ValueError):
    """Raised when a byte budget is too small to cap anything with. ..."""
```

— and raised as `raise OutputCapError(f"max_output_bytes must be 0 (uncapped) or at least
{MIN_MAX_OUTPUT_BYTES}, got {max_output_bytes}")`, a bare message string. `test_failure_behavior`
fails at `assert refused.value.max_bytes == 8` with `AttributeError: 'OutputCapError' object has
no attribute 'max_bytes'`. A second, related gap follows from the same missing remarks: the floor
check is only enforced in `SandboxCodeExecutionBackend.__init__` (`self.max_output_bytes: int =
validate_max_output_bytes(...)`, L3946), never as a `@field_validator` on
`CodeExecutionBackendConfig` itself (L3849-3907 shows only `Field(default=..., ge=0)`), so
`CodeExecutionBackendConfig(max_output_bytes=8)` alone would not raise — the "pulled forward to
config construction" half of the requirement is also missed, for the same reason: `say26` is the
only remark that names the field_validator explicitly, and it was never seen.

## What it believed, and why

All four herrings were correctly dismissed once their reversals turned up, and the agent's rolling
`Analysis` notes show it explicitly tracking each supersession chronologically rather than
committing early: "decisions keep evolving (marker now outside the budget, dropped count =
original minus kept)" (L2280), and "error_truncated bool on CodeExecutionOutput only" (L3417) after
having earlier logged the Jan-21 herring that `error` should ride as a third `truncated_streams`
entry. The shipped code follows every reversal and none of the four herrings.

## Summary of the one lost fact

`g2.r1.failure_behavior` = 0, cause **not_found**, on two remarks that deliberately avoided the
vocabulary every one of the agent's search passes was built around — a task-defect-adjacent near
miss rather than a reasoning error. Every other fact — all four `g2.r1` facts but this one, and all
four `g2.r2` facts — was correctly reconstructed and correctly shipped.
