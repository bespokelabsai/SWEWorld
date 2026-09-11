# g9 run 10 (eval 3b0b259f, rollout 3f9184ba) — reward 0.8571

## Outcome

7 of 8 grader tests passed (`test_open`, all four `test_r1` facts, and two of three `test_r2`
facts). The run pushed, CI went green, and it deployed. The single failure is
`test_r2::test_failure_behavior__bad_roles_and_a_bad_tokenizer_abort_the_batch_and_write_no_report`,
reported as `bad roles abort: expected an exception, none raised` — `format_batch` on a batch
containing a malformed role sequence (`user, user`) should raise `InvalidRoleSequenceError` and
leave `self.last_report` untouched, but the agent's code absorbed it as a drop instead.

## What it recovered well

The agent's search was thorough by volume: 38 of 57 planted remarks were surfaced across chat
(dumped whole Mattermost channels to files, then grepped term clusters), mail (fetched by numeric
message-id ranges), and wiki (`/api/search` on 8 finetuning-vocabulary terms, then fetched every
matching page's full body *and comments* — it correctly knew BookStack search does not index
comments and fetched pages whole rather than relying on snippets). All three herring/reversal
pairs for `g9.r1` and the first `g9.r2` tuple-return herring were both seen, and the agent
correctly recognized the reversals as superseding (line 4285: *"That's the older (superseded)
decision. The newest word (engineering channel) is: refusal only when retained prompt tokens <
16."*). This produced clean, fully-passing implementations of `r1.rule`, `r1.scope`,
`r1.exclusions_or_crossover`, `r1.failure_behavior`, `r2.rule`, and `r2.scope` — including exact
string formats (`ExampleTooLongError`'s message), exact numeric fixtures (window_start, the 16-token
floor, the 3-byte-per-token Fireworks budget), and the frozen-dataclass shape of `EncodingReport`.

## Why `g9.r2.failure_behavior` was lost

The agent read the `g9.r2.h-role-row` herring directly, in a mail thread it genuinely opened
(line 3039/3045, "PR 653: which layer drops a bad row, and who counts it"): *"Length and role
sequence are row problems — one bad row says nothing about the next row, so those get counted and
skipped."* Its own Analysis when writing `format_batch` (line 4843) restates this almost verbatim
as the design: *"skip row-level failures (InvalidRoleSequenceError, ExampleTooLongError)... let
config-level failures (TokenizerCapabilityError) abort."* The shipped code (line 4884) implements
this with `except EncodingError: dropped_indices.append(index); continue` — and because
`InvalidRoleSequenceError` subclasses `EncodingError`, it is silently caught and counted as a drop
instead of propagating.

The retraction of exactly this herring, `g9.r2.rev3`, sits as a wiki-page comment on
`docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md`: *"and yes this is me
contradicting myself — the split I gave on the 653 thread back in may, length and role sequence
both being row problems, that half of it was wrong and I'm dropping it. only the over-long ones
are row problems."* This page was never fetched. Its title ("request builder") and body use
generic batching language — "row", "skip and count", "raise", "builder" — and never mention
"encoding", "tokenizer", "tinker", "fireworks", "training", "curator", or "finetune". None of the
agent's 8 wiki search queries (all built from that finetuning-specific vocabulary) would ever
return it, and the agent never enumerated the `docs/engineering` book by title to catch pages a
keyword search missed. A second independent chance existed at `g9.r2.l16` (#pipeline, "the tool
role example got swallowd into the drop count... thats not a drop") — also never surfaced, for the
same reason (fell outside the dumped channel-page range the agent happened to grep).

## Search strategy characterization

Chat and mail were read via full-channel/full-thread dumps rather than one-off searches, which is
generally sound — but the mail fetch used explicit numeric id ranges rather than a broad search, so
whole threads outside the chosen ranges were invisible regardless of relevance (`g9.r2.l19`,
`g9.r2.l13`, `g9.r2.l6`, `g9.r1.say23`). Wiki search was keyword-only against a fixed finetuning
vocabulary; every page it *did* find was fetched and read whole including comments, which is the
right behavior — the gap is structural (no enumeration fallback), not a matter of skipped effort.

## Bottom line

One lost fact, one clean root cause: the agent believed a herring it genuinely read, and the one
remark that would have corrected it was excluded by a search-vocabulary gap rather than skipped
through carelessness. Everything else — both requirements' other facts, all three herring/reversal
pairs it did encounter — was reasoned about correctly and shipped faithfully.
