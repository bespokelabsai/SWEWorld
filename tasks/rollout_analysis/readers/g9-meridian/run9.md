# g9-meridian run 9 (3ca9c0ce) — reward 0.7143

This run shipped a clean, fully-deployed solution (PR #737 merged to main as `86fd382`, CI run 15
green including a strict regression gate the agent added itself, service healthy) and recovered
five of the task's seven hidden facts, largely through disciplined dump-and-grep reading of chat
and mail. Both misses are hidden-requirement failures, not infra: `g9.r1.failure_behavior` and
`g9.r2.failure_behavior` both scored 0.

**`g9.r1.failure_behavior` — not_found.** The shipped `ExampleTooLongError.__init__` (transcript
line 2817) takes only `token_count`, `max_seq_length`, `retained_prompt_tokens` — missing
`num_messages`, so the grader's `raised(..., num_messages=2, ...)` assertion failed with
`num_messages: None != 2`. Every other element of this fact (the exact refusal string, the
16-retained-token floor, the herring/reversal pair about "any nonzero window_start refuses") was
found and correctly implemented — this is a single missing attribute, not a misunderstanding of the
rule. The one remark that ties `num_messages` to this exception's constructor, `g9.r1.l-fail-3`
(#pipeline, 2025-03-19: "num_messages rides along as an attribute, not printed"), never appears
anywhere in the transcript; grepping for its distinctive phrases returns nothing. The agent's one
broad keyword grep over the dumped channel history (`EncodingReport|ExampleTooLong|last_report|
supervised|FIREWORKS|utf|non_alternating|362|format_batch`) doesn't contain any word from that
exchange, so it was never matched even though the day's channel was in the dump. The remark the
agent did find that mentions `num_messages` (`g9.r1.say22`, lines 1958-1963) is about the *returned
dict's* metadata block, not the exception, and is deliberately worded (forbidden_terms exclude
"attribute"/"max_seq_length") so it cannot substitute.

**`g9.r2.failure_behavior` — herring_followed.** The shipped `format_batch`
(`except (InvalidRoleSequenceError, ExampleTooLongError): ... continue`, line 2459) silently drops
a bad-role-sequence example instead of letting it abort the pass, so the grader's
"expected an exception, none raised" check failed. This exactly follows the herring
`g9.r2.h-role-row` (mail, dario, 2025-05-28: "Length and role sequence are row problems... those
get counted and skipped"), which the agent read twice (lines 1024 and 1454/1579). It never saw the
reversal: `g9.r2.rev3` is a **wiki comment** on
`docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md` ("this is me contradicting
myself... only the over-long ones are row problems"), and the same page also carries `g9.r2.l17`,
the plain statement of the correct rule. Neither surfaces in the transcript. This run's entire wiki
strategy was two `/api/search` calls (`encoding`, `EncodingReport`) and exactly one page ever opened
via `/api/pages/{id}` (page 156, from the first search's hits) — the second search returned
`{"data":[],"total":0}` because BookStack search does not index comments, precisely the trap the
ticket names at line 159. The wiki was never enumerated page-by-page, so all 14 other comment-only
remarks — including the one that would have overturned this herring — were structurally
unreachable this run.

**Everything else it got right** came from unusually thorough chat/mail reading: full-channel dumps
grepped and re-grepped with evolving keyword lists, and targeted `sed`/`grep` slices of an IMAP mail
dump. This recovered `r1.rule` (the all-or-nothing masking correction), `r1.scope` (fold the
no-tokenizer branch into the same masking function), `r1.exclusions_or_crossover` (UTF-8 byte
budget, `FIREWORKS_BYTES_PER_TOKEN=3`), `r2.rule` (frozen `EncodingReport` dataclass, field order,
`self.last_report` semantics), and all four non-role herring/reversal pairs correctly (it believed
every reversal it encountered — the one exception is the role-sequence herring, whose reversal it
never encountered). `r2.scope` also passed, but by omission rather than design: the two remarks
that state `to_tinker_datum` never touches `self.last_report` were both missed too, and the fact
only passed because the agent's `to_tinker_datum` was never given code to write that attribute in
the first place.

The agent's own 111-test suite passed throughout, which offered false confidence: it wrote tests
consistent with its own incomplete exception constructor and its own incorrect
role-sequence-absorbing `format_batch`, so a green suite could not have caught either miss.
