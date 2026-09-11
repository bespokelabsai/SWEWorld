# g9 run 7 — eval fffbd350, rollout 5b62f13c — reward 0.7143

## What this run found

This is a strong, methodical run. After reading the repo and existing tests, the agent worked
every source the ticket points to: Gitea issues/PRs (a dead end — all bot summaries, nothing
useful), the BookStack wiki (13 keyword searches, then it fetched ~10 pages *whole*, including
comments, after building its own recursive comment-walker in three attempts), Mattermost chat
(dumped every channel to local files, then grepped a rotating vocabulary of terms), and IMAP mail
(dumped 153 messages, then read whole threads once a subject/content grep hit landed). This
recovered essentially all of `g9.r1`: the all-or-nothing turn-masking rule (wiki page 144/132,
`g9.r1.l-rule-1/3/4`), the no-tokenizer path honouring `train_on_assistant_only` via the same
`len//4`-both-ends span formula (mail `g9.r1.l-scope-1/4`, `say23`, wiki `l-scope-3`), and the
Fireworks byte-budget rule with `FIREWORKS_BYTES_PER_TOKEN=3` (chat `l-fw-1`, wiki `l-fw-2`, mail
`l-fw-3`). It also recovered the shape of `g9.r2`'s `EncodingReport` — frozen dataclass, five
named counters, `self.last_report` reassigned by both `format_batch` and `to_jsonl_lines`, empty
on a fresh formatter (wiki 135/145/137, mail `l1/l6/l15`) — and the failure-mode split between
`TokenizerCapabilityError` (aborts the whole pass) and the over-long refusal (skipped and
counted, wiki 149/155, chat `l18`). Both herrings on each requirement were seen and correctly
rejected in favour of their later reversals (transcript lines 2803, 3029, 3331) — the agent never
built the "any nonzero `window_start` refuses" rule or the `(data, report)` tuple return.

## What it missed, and why

Two facts scored 0, both from the same pattern: a remark that pins an *exact literal value* lived
in a channel the agent dumped to disk but never fully read.

**`g9.r1.failure_behavior` (0).** The shipped `ExampleTooLongError` uses a self-invented message
(`"example of {token_count} tokens windowed at {max_seq_length} retains only {retained_prompt_tokens}
token(s)..."`) and computes `retained_prompt_tokens = s_last - window_start` **without** clamping
to zero — the docstring literally says "Negative when that turn began before the cut" (transcript
line 4732). The test fails on `error.retained_prompt_tokens == 0` (actual `-61`). The two remarks
that would have fixed this — `g9.r1.l-fail-2` (#releases, the literal string `"example of 129
tokens exceeds max_seq_length=40: 0 prompt tokens would survive, minimum is 16"`) and
`g9.r1.l-fail-3` (#pipeline, the exact f-string template plus `num_messages` as an attribute) —
were never properly surfaced. `l-fail-2` was hit by a grep but only on a neighbouring line
("stopped. ExampleTooLongError, and the traceback right after it", transcript line 2967); the
literal error text one line above was never printed. `l-fail-3` sits in `#pipeline`, a channel the
agent dumped but never linearly read (see below) — 0 hits.

**`g9.r2.rule` (0).** Every part of `EncodingReport` shipped correctly except one: `dropped_indices`
is a plain `List[int]` (`field(default_factory=list)`, transcript line 4771) instead of a frozen
`Tuple[int, ...]`. The failing assertion is isolated to exactly this — `[1] != (1,)` in a dataclass
equality check; everything else about the report (frozen-ness, field order, defaults, the
individual counter values) is correct. The one place in the whole corpus that states this detail —
Konrad's mail in `g9.r2.l19` ("Re: Weekly update: week of Apr 7"): "the counters are local now,
... except `dropped_indices`, which I can collect in a list and **freeze into the tuple** at the
same point" — was never opened. The agent's mail search focused on the PR653 mega-thread and
related subjects; this thread's subject doesn't mention encoding/report/dropped_indices at all,
so nothing in the agent's grep vocabulary would have found it.

## Search-strategy gap

The agent dumped `#pipeline` and `#viewer` to local files exactly like the channels it *did* mine
successfully, but appears to have only grepped them for `EncodingReport`/`dropped_indices`-style
terms rather than reading them start to finish the way it read `#engineering` and `#code-review`
in full (transcript lines 2764-3280+). Seven of the eight remarks seated in those two channels
were never found (`l-fail-3`, `l-fail-4`, `r2.l7`, `r2.l16`, `r2.l9`, `r2.l10`, `fix28` — though
`fix25` in `#pipeline` *was* found via a lucky grep hit). Most of these were redundant with
material the agent found elsewhere, so only `l-fail-3` (paired with the partial `l-fail-2` miss)
actually cost a graded point. Two wiki pages (both meeting-notes pages holding one comment each,
`l11` and `l5`) never matched any of the ~20 BookStack keyword searches run and, being comments
rather than page bodies, would not have matched search even if the right keyword had been tried —
consistent with the ticket's own warning that BookStack search does not index comments.

## What it believed

The agent correctly tracked every herring-to-reversal pair and never shipped a herring's behaviour:
it explicitly reasoned through the Jan-21/22 "any nonzero `window_start` refuses" and "returns a
`(data, report)` tuple" decisions being superseded by the Mar/Apr reversals (lines 2803, 3029), and
the May "role sequence is a row problem" herring being retracted in June (`h-role-row`/`rev3`,
found together in the same wiki-149 comment read, line 2216) — though the ticket text itself
already specified `InvalidRoleSequenceError` propagating from `to_jsonl_lines`, so this particular
herring carried little risk regardless.

## Why the losses happened

Both zero-scored facts are single, isolated assertion failures inside otherwise-correct
implementations — not conceptual misunderstandings. In both cases the agent built a reasonable,
internally-consistent design (a custom but readable error message; a plain list for indices) in
the *absence* of the one corpus remark that would have pinned the exact contract, rather than
contradicting a remark it had actually read. Cause for both: **not_found**, traceable to specific,
identifiable gaps in channel/thread coverage rather than to misreading or to a corpus
contradiction.
