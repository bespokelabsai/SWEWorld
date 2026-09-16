# g9-meridian run4 (79ceb018) — eval de47e209 — reward 1.0

A clean pass: every one of the seven hidden facts (r1's rule/scope/exclusions_or_crossover/failure_behavior,
r2's rule/scope/failure_behavior) plus the unweighted open_feature scored 1, and provenance (pushed, CI
green, deployed) held. The interesting question for a 1.0 run isn't what was lost but *how* each fact was
actually recovered — and one of them, `g9.r2.failure_behavior`, was recovered without ever seeing the
remarks the answer key names as its carriers.

## r1 — the boundary/windowing requirements

All three graded r1 facts trace to real reads. `g9.r1.rule` (all-or-nothing at the window boundary) came
from wiki page 144's comment thread (transcript line 1484-1509), where Dermot states it almost verbatim:
"if a turn's opening tokens fall outside the front edge of the window, that turn is not supervised at
all... the entire remainder of that turn carries no weight" — reinforced by the reversal `g9.r1.rev1`
found via a targeted Mattermost full-text search for `"ExampleTooLongError"` (line 1760-1765). `g9.r1.scope`
(the no-tokenizer path sharing the same windowing/masking) came from wiki page 132's comment thread
(line 1321-1354): "leave the `<|role|>` text and `len(chat_text) // 4` as they are; a span's ends are that
count over messages[:i], then over messages[:i+1]." `g9.r1.exclusions_or_crossover` (the Fireworks byte
budget, strict `>`) came from a Mattermost search hit for `FIREWORKS_BYTES_PER_TOKEN` (line 1764-1767) and
the long inventory mail g9.r1.l-fw-3 (line 447 onward). `g9.r1.failure_behavior` (the 16-retained-token
floor, exact error string, skip-and-continue) is grounded in g9.r1.l-fail-2/l-fail-3 and both r1 herring
reversals — the shipped `ExampleTooLongError.__str__` matches the quoted refusal line character for
character. The two r1 herrings (h1: "any nonzero window_start raises"; h2: "windowed at all means
refused") were both seen inside bulk chat dumps and correctly discarded in favor of their reversals, which
happened to sit in the same dumps — the agent was never forced to resist one without its correction
nearby.

## r2 — the report/abort requirements

`g9.r2.rule` (the frozen `EncodingReport` dataclass, exact field order/defaults, both entry points
reassigning it) is well evidenced: wiki page 145's comment (line 1546-1548) states the field order
directly, and the mail g9.r2.l1 (line 1209-1210) lists the whole `finetune` surface including
`EncodingReport`. `g9.r2.scope` (only the batch entry points write it; `to_tinker_datum` never touches it)
rests almost entirely on the mail thread g9.r2.l19 ("Re: Weekly update: week of Apr 7", line 1163-1188),
which the agent read in full and paraphrased accurately in its own Analysis (line 1219): "initialize a
zero report, replace it only after successful batch completion, and preserve the previous report on
unexpected exceptions."

**`g9.r2.failure_behavior` is the one worth flagging.** The mechanical pre-pass reported zero hits for all
five of its canonical carriers (`l18`, `l16`, `l17`, `say24`, `rev3`), and a direct grep of the full
transcript for each one's distinctive phrasing ("chewed through"/"four hundred", "swallowd", "my data
being broken"/"quietly skip", "apply_chat_template"+"TokenizerCapabilityError" outside the ticket text,
"contradicting myself"/"im dropping it") confirms none of them appear anywhere — the wiki pages carrying
`l17`/`rev3`/`say24` (request-builder-what-we-drop, what-format-batch-counts-as-a-drop) were simply never
fetched, and the mail carrying the `h-role-row` herring/its reversal was never opened either (a grep for
"row problems" — the herring's own giveaway phrase — returns zero hits; the agent never saw it).

Yet the fact scored 1, because the shipped `format_batch` calls `validate_role_sequence(example.messages)`
**outside** the try block and catches **only** `ExampleTooLongError` inside it (transcript lines
2276-2286); `self.last_report` is built once, from locals, after the loop completes normally. Any exception
that escapes mid-loop — whether `InvalidRoleSequenceError` from validation or `TokenizerCapabilityError`
from `_encode_datum` — therefore propagates out of `format_batch` and leaves `last_report` at its prior
value by construction, exactly what `test_failure_behavior__bad_roles_and_a_bad_tokenizer_abort_the_batch...`
asserts. This is not a guess: it follows directly from (a) the ticket's own text, which already defines
`InvalidRoleSequenceError`/`TokenizerCapabilityError` and states `to_jsonl_lines` "propagates
`InvalidRoleSequenceError`" with no mention of catching it, and (b) `g9.r2.l19`'s general architecture
("accumulating into locals... assigning it to the attribute once, on the success path... If the loop
raises, no write ever happens"), which the agent generalized from l19's tokenizer-failure example to
role-sequence errors too — visible in its own added regression test (line 2403-2418) asserting
`formatter.last_report is saved` after `to_jsonl_lines` raises `InvalidRoleSequenceError`. What it never
had was any remark that said, in so many words, "role sequence errors are not counted as drops" — that
half of the MuSR tree (`g9.r2.sc5`) went completely unseen, and the fact passed on architectural inference
from an adjacent, correctly-read remark plus the ticket's own class definitions.

## Search strategy

Mattermost reads were mostly bulk channel dumps grepped with narrow keyword regexes that changed per
query — effective for the vocabulary anticipated, blind to anything phrased differently ("row problems",
"swallowd", "chewed through" never matched any regex run). Wiki coverage was thin: one `finetun` search
plus five or six page IDs fetched whole (with comments, correctly, since BookStack doesn't index them) —
but several fact-bearing pages (`request-builder-what-we-drop-and-what-we-raise-on`,
`what-format-batch-counts-as-a-drop-and-what-stops-the-pass-instead`,
`end-of-run-summary-tables-how-the-formatters-are-wired`, `weekly-notes-week-of-mar-31`) were never opened
at all. Mail relied on targeted IMAP `SEARCH TEXT` for a couple of terms plus one broad dump whose on-screen
output looks pty-truncated (several SUBJECT lines the answer key promises never appeared). No crashes or
dead helper scripts — truncation and narrow term lists, not tooling failure, explain the roughly half of
remarks never seen.

**Bottom line:** every lost-looking gap in this run's remark coverage was compensated by either a
different, correctly-read carrier of the same fact, or — for `g9.r2.failure_behavior` specifically — a
structurally sound generalization from one real carrier (`l19`) plus the ticket's own explicit class
definitions, rather than by chance.
