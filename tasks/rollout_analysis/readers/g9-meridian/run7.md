# g9-meridian run 7 (f7d0a487) — eval de47e209, reward 0.8571

## What this run found

The run pushed a clean, working `finetune/encoding.py` policy (commit `30bcd85`, CI green, 114/114
local finetune tests passing) and recovered six of seven hidden facts. It read mail thoroughly over
IMAP, opened six wiki pages whole with comments (132, 137, 144, 145, 153, 156 — correctly aware that
BookStack search does not index comments, transcript line 159), and picked up `r1.rule`, `r1.scope`,
`r1.exclusions_or_crossover`, `r2.rule` and `r2.scope` from a good spread of remarks across all three
surfaces (e.g. page144's comment at line 2385 states the sc-rule leap almost verbatim: "if a turn's
opening tokens fall outside the front edge of the window, that turn is not supervised at all").

## What it missed, and why

**`r1.failure_behavior` (0/1).** The grader's only complaint was `num_messages: None != 2` — every
other part of `ExampleTooLongError` (message string, the 129/40/0/16 numbers, `ValueError`
ancestry) was implemented correctly (judge.py:171-172). The run's own ruff-lint output (transcript
line 2904) shows the shipped constructor as `__init__(self, *, token_count, max_seq_length,
retained_prompt_tokens)` — `num_messages` never added. Of 57 planted remarks, exactly one
(`g9.r1.l-fail-3`, nils, `#pipeline`, 2025-03-19: "num_messages rides along as an attribute, not
printed") ties `num_messages` to the *exception's* constructor rather than to the kept datum's
metadata dict (which the ticket already specifies). Grepping both the rendered transcript and the
full rollout JSON for its distinctive phrases and for the literal string `#pipeline` returns zero
hits anywhere in the run. This is a clean **not_found**, not a misread or an implementation slip.

The deeper cause is structural: chat discovery in this run was seeded from a *single* Mattermost
keyword search (`"encoding"`, line 919), and every channel the agent ever paged came from the
`channel_id`s of the posts that one search matched. Every remark planted in `#pipeline` or `#viewer`
— six of them across the whole task — shows zero hits in this run, which is consistent with those
two channels never being fetched at all, not merely read narrowly. `l-fail-3` was therefore
unreachable by this run's method regardless of how carefully it read what it did fetch.

**Within fetched channels**, the agent additionally printed only hand-picked index ranges around
messages it already suspected mattered (line 1237: `[(830,854),(881,887),(918,930),(1100,1113),
(1208,1219)]`), so several remarks sitting in `#code-review`/`#engineering`/`#cookbooks` (`l-rule-3`,
`l-fw-4`, `l-fail-1`, `l-scope-2`, `l18`) were also never printed, though each was redundant with a
sibling remark the run did find.

## What it believed, and why

The two `r1` herrings (`h1`, `h2` — "any nonzero window refuses") were never seen standalone; the
agent only ever encountered them recapped inside their own reversals (`rev1` at line 1111, `rev2` at
line 919), which state the old rule and immediately correct it in the same message. The shipped code
implements the corrected 16-retained-token floor, so the herrings were never a live risk this run.
The two `r2` "tuple-return" herrings were seen together with their reversals in one printed block
(lines 918–932) and correctly not followed — `format_batch` returns a plain list, with the report on
`self.last_report`.

## Why `r2.failure_behavior` passed (7/10 runs failed this)

The agent never opened the mail thread carrying `g9.r2.say23`/`g9.r2.h-role-row` ("Length and role
sequence are row problems ... those get counted and skipped") or the wiki page carrying
`g9.r2.l17`/`g9.r2.rev3` — the clearest single statements of "role/tokenizer errors abort, they are
not counted as drops." It never saw the herring, so it was never at risk of being misled by it. What
it *did* rely on was `g9.r2.l19` (mail, "Re: Weekly update: week of Apr 7", found at line 1383):
the PR-632 review thread establishing "on an abort, do not write; whatever the attribute held going
in is what it holds coming out" — combined with the ticket's own text (lines 77–78, 99–100), which
already states that `InvalidRoleSequenceError` "propagates" from `to_jsonl_lines` and
`TokenizerCapabilityError` is raised by `to_tinker_datum` with no fallback. Its own Analysis at line
1321 ("format_batch skips only ExampleTooLongError") shows the inference forming from that
combination, not from any wiki/herring text. The shipped `format_batch` calls
`validate_role_sequence` unguarded (so `InvalidRoleSequenceError` propagates immediately), narrows
its `except` to `ExampleTooLongError` only (so `TokenizerCapabilityError` also propagates), and
accumulates counters into locals, assigning `self.last_report` exactly once after the loop — exactly
the PR-632 pattern from `l19` — so any exception raised mid-batch leaves the previous report intact.

`r2.scope` is a related, smaller finding: all three remarks that carry it (`l7`, `l8`, `say23`) were
missed, yet it scored 1 anyway — the single-example path never had any `last_report`-writing code
added to it at all, which is correct by omission rather than by recovery.

## Lost fact

- **`g9.r1.failure_behavior`** — cause `not_found`. The one carrying remark (`g9.r1.l-fail-3`,
  `#pipeline`) sat in a channel this run's single-keyword chat search structurally never reached.
