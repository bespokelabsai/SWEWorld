# g9-meridian run 8 (eval de47e209, rollout 9ad48705) — reward 0.8571

## What it found

The run recovered six of the seven hidden facts. For `g9.r1` (span windowing) it correctly
derived the all-or-nothing boundary rule, the no-tokenizer path mirroring the same windowing and
masking, the Fireworks byte-budget exclusion (`FIREWORKS_BYTES_PER_TOKEN=3`, strict `>`, UTF-8
`json.dumps(ensure_ascii=False)` measurement), and the 16-retained-prompt-token refusal floor. For
`g9.r2` it correctly derived the `EncodingReport` frozen dataclass (fields, order, defaults) living
on `self.last_report` rather than a tuple return, and that `to_tinker_datum` never touches
`last_report`. All of this came from real corpus reading: two Mattermost channel dumps plus four
targeted term searches, one IMAP mailbox pull filtered by keyword and then fetched by id for ~20
messages, and four to six BookStack pages opened whole (body + comments) via `/api/pages/{id}`.

## What it missed, and why

It lost exactly one fact: `g9.r2.failure_behavior` (the failing assertion was `bad roles abort:
expected an exception, none raised`). The cause is `herring_followed`, not a misunderstanding of
the rule in general — the agent got the *other* half of this same fact right
(`TokenizerCapabilityError` correctly propagates and aborts the batch, verified by its own
regression test at transcript line 2380). What it got wrong is narrower and traceable to one
specific mail: at step 7 (transcript lines 1266–1281) it read, in full, mail 148 from dario —
`"Length and role sequence are row problems — one bad row says nothing about the next row, so
those get counted and skipped."` That sentence is `g9.r2.h-role-row`, a **herring**: the team
settled it, then reversed it three weeks later. The reversal, `g9.r2.rev3` (`"this is me
contradicting myself ... only the over-long ones are row problems"`), together with two
corroborating clues (`g9.r2.l17`, `g9.r2.say24`), sit exclusively as **wiki page comments** on two
pages — `docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md` and
`docs/engineering/what-format-batch-counts-as-a-drop-and-what-stops-the-pass-instead.md` — that the
agent never fetched. Neither page ever appeared in either of its two wiki searches (`encoding`;
`finetuning` + `EncodingReport`), and its page-fetch loop opened only four ids (132, 137, 145, 153,
plus 154/156 from the earlier search). The shipped `format_batch` treats `InvalidRoleSequenceError`
exactly like `ExampleTooLongError` — silently counted as a drop, no exception raised — which is
precisely what the herring, read in isolation, says to do.

## Search behavior worth flagging

Two self-inflicted near-misses compound the corpus's own herring trap. First, the agent ran a wiki
search for two terms in one loop (`for q in finetuning EncodingReport; do curl ...; done`) but its
follow-up Python only opened the `finetuning` result file — the `EncodingReport` search's results
were fetched and then never read. Second, its own printed "relevant mail" listing included ids 132
and 138 ("stats report branch — need someone to run it before the 0.1.25 cut", carrying
`g9.r2.rule`), sitting between ids it did fetch (131, 137, 143...), but the next fetch command
simply omitted them. Separately, the mail candidate list itself was built from a fixed 4-substring
keyword filter (`encod`, `finetun`, `tinker`, `fireworks`) applied to subject+body — threads whose
text used only "tokenizer" or "role sequence" without any of those four substrings (e.g. `PR 653:
formatter still takes tokenizer=None`, `PR 653 before the next cut`, the `sft export` thread) were
never even candidates.

## Why it stopped where it did

This is the shortest run in the eval (44 steps), but not because it ran out of turns or hit an
infra failure. By roughly step 9 it had already converged on an implementation plan and started
writing code; by step ~35–38 it had implemented, run 130 local tests green, committed, pushed,
watched Gitea CI go green, and confirmed the deployed release and health endpoint matched the
commit. It explicitly reasoned `"No further actions needed"` (line 3311) and, on the harness's
completion-confirmation prompt, answered yes. It never returned to search after implementation
began — no further wiki search, no search for "role sequence" or "InvalidRoleSequenceError" as
terms, no enumeration of the ~15 remaining pages its own `finetuning` search had already surfaced.
Both `g9.r1` herrings and one of the two `g9.r2` tuple-return herrings were correctly resolved in
favor of their reversals, often found one line apart in the same channel dump — so the run is not
naive to herrings as a category. It specifically missed the one reversal that its particular,
narrower-than-exhaustive search pattern never surfaced at all.
