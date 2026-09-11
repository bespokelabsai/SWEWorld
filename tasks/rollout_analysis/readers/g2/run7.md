# g2 run 7 (33b81bf0) eval 9f2db992 — reward 0.7778

## What this run found

A thorough, methodical rollout: dumped Gitea issues (nothing relevant), IMAP mail (142 messages,
found all 5 mail remarks), Mattermost chat (all 12 channels, 10181 lines), and — correctly
following the ticket's own warning that `/api/search` does not index comments — enumerated and
fetched all 231 wiki pages whole via `/api/pages/{id}`. From chat + mail alone it correctly
reconstructed nearly the entire hidden design: head = `(budget*3)//4` bytes, tail = the remainder,
spliced by `\n[[curator:elided {dropped} bytes]]\n` where `dropped` = original bytes minus bytes
actually kept (not original minus budget — the reversal of `g2.r1.herring-dropped-count-gideon`,
found and correctly believed), the marker charged *outside* the budget (the reversal of
`g2.r1.herring-marker-inside-budget-dario`, also found and correctly believed), `0` as an
unlimited sentinel exempt from the floor, a UTF-8 boundary walk bounded at three steps with
`errors="replace"` only past that, and — on the r2 side — the exception-path `error` field capped
by the same helper, `error_truncated: bool = False` declared directly under `truncated_streams` on
`CodeExecutionOutput` only, and the exit-code/timeout messages left uncapped. All four herrings
were identified as superseded before any code was written, and the shipped code follows every
reversal and none of the herrings.

## What it missed, and why

Two facts scored 0, `g2.r1.failure_behavior` and `g2.r1.observability`, and both fail at an
**import line**, before any behavioural assertion runs. The actual implementation (recovered
verbatim from the rollout JSON's tool-call arguments, since the transcript's rendered heredocs are
elided) gets every *behaviour* right: the floor is 16, `0` is exempt, the rejection happens at
`CodeExecutionBackendConfig` construction via a `field_validator`, the warning is logged exactly
once per run at the cut site (never from the `except` salvage path), sorted, and only when
something was actually shortened. What's missing is naming. `output_cap.py` raises a bare
`ValueError` instead of an importable class called `OutputCapError` (no `.max_bytes` attribute,
and different wording — `"max_output_bytes must be 0 (uncapped) or at least 16, got 8"` instead of
the pinned `"max_bytes must be 0 or at least 16, got 8"`), and it exports a function
`format_cap_warning()` that produces the exact right string at runtime instead of a module
constant named `TRUNCATION_LOG_TEMPLATE`. The grader imports both names directly, so both tests
`ImportError` before checking anything else. There is also a second, structural gap behind the
naming one: `_execute_in_sandbox` never calls the floor-validation function at all — only the
pydantic config path enforces it — so a below-floor budget passed directly to
`_execute_in_sandbox` (as the grader's own first assertion does) would not raise today even under
a hypothetical rename.

Three remarks state exactly what's missing, and none of them were ever surfaced: `g2.r1.l-floor-
nikolai` (#cookbooks) supplies the class name `OutputCapError` with `ValueError` as its base;
`g2.r1.l-floor-konrad` (#cookbooks) supplies the exact message text and the requirement to hang
the value on the exception as `.max_bytes`; `g2.r1.say26` (#incidents) supplies the field-
validator/`ValidationError`-verbatim framing. All three were invisible to the agent's chat grep
pattern (`max_output_bytes|elided|truncated_streams|output cap|output_cap`) because none of them
use that vocabulary — `l-floor-konrad` says `max_bytes` without the `output_` prefix, and
`l-floor-nikolai`/`say26` never say "cap" or "truncat" at all, discussing "the cap helper" and "the
batch size check" instead. This is a genuine near-miss, not a misread: the agent never had the raw
text in view.

The `TRUNCATION_LOG_TEMPLATE` name is carried by exactly one remark in the whole corpus —
`g2.r1.l-log-nikolai`, a wiki page *comment*. This one is more interesting: the comment's own text
contains the literal substring `output_cap.py`, which the agent's grep pattern (including
`output_cap` as a literal alternative) would have matched — and the agent's wiki dump did
enumerate all 231 pages including their `comments` field, exactly the right technique per the
ticket's own hint. Yet grepping the resulting `wiki.txt` for that pattern returned nothing relevant
(transcript ~L1613-1620). Since the corpus is fixed per task version, this looks like a
completeness gap in this specific rollout's wiki dump (a silent retry shortfall, or a duplicate-
book page copy without comments being the one fetched) rather than the comment being genuinely
absent from the world — flagged as `notable` rather than asserted as fact, since it wasn't
independently re-verified against the live world.

## Net effect

Every fact this run lost is one where the *behavior* was already correct and only a *name* — a
class identity, an attribute, an exact message, a constant — was missing, and in every case the
missing name traces to a specific remark (or, for observability, specifically a wiki comment) that
never appeared in this rollout's search output. The reward (0.78) meaningfully understates how
close the implementation is: 7 of 9 hidden facts passed outright, and the two that failed did so
on an import line rather than a behavioral disagreement.
