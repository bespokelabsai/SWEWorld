# g9 run 9 (eval 3b0b259f, rollout 0b39d6d4) — reward 0.8571

## What this run found

This is one of the strongest g9 runs available: 6 of 7 hidden facts scored, provenance clean
(pushed, CI green, deployed), suite_ok. The agent's search was unusually disciplined for its
size — it read the entire source tree before touching any external source, then worked outward
through Gitea (nothing useful there for this task), BookStack (fetching whole pages *with
comments*, the one technique the ticket explicitly hints is necessary since BookStack search
doesn't index comments), Mattermost (dumping entire channel histories to files and grepping
them), and finally IMAP mail (dumped and read message-by-message across ~10 turns). By the time
it started writing code (around transcript line 4329) it had assembled essentially the entire
settled record: the all-or-nothing windowing rule, the no-tokenizer span arithmetic, the
Fireworks byte budget, the `EncodingReport` shape and `self.last_report` semantics, and the
April reversal of the refusal floor from "windowed at all" to "under 16 retained prompt tokens."

All five herrings (`g9.r1.h1`, `g9.r1.h2`, `g9.r2.g9-tuple-return-1`, `g9.r2.g9-tuple-return-2`,
`g9.r2.h-role-row`) were seen, correctly recognized as superseded, and overridden by their
reversals in the shipped code — the agent's own Analysis turns explicitly track "old Jan rule"
vs. the later thread that supersedes it (lines 2476, 2599, 2650, 2903, 3658). None of the loss in
this run is herring-related.

## What it missed and why

The one lost fact is `g9.r1.failure_behavior`: the grader's `test_failure_behavior__...` asserts
`error.retained_prompt_tokens == 0` and `error.num_messages == 2` on a raised `ExampleTooLongError`.
The shipped exception has neither attribute — the agent named its fields `surviving_prompt_tokens`
and `minimum` instead, and dropped `num_messages` entirely. The pytest failure trace confirms this
exactly: `over-long refusal: retained_prompt_tokens: None != 0`.

This is a clean `not_found`, not a misread or an implementation slip. The only remark in the whole
57-remark corpus that names `retained_prompt_tokens` and states that `num_messages` "rides along as
an attribute, not printed" is `g9.r1.l-fail-3` (chat #pipeline, nils/dermot/gideon, 2025-03-19
14:03). That exchange never uses the words `ExampleTooLongError`, `window_start`, or
`to_tinker_datum` — it opens with "when an example is too long to fit, what does the refusal
actually say?" and gets the literal f-string template as the answer. Those three strings were the
*only* keywords the agent ever grepped Mattermost dumps for (transcript line 2335:
`grep -n -i -E 'ExampleTooLongError|window_start|to_tinker_datum' /tmp/mm_*.txt`), so this remark
was invisible to every search it ran, even though the agent had dumped the entire #pipeline
channel (2193 lines) to a file and could in principle have read it straight through. It never did
a plain sequential read of that channel around the relevant date — every touch of #pipeline in the
transcript is a keyword-grep hit.

The agent did find the *instantiated* message string elsewhere (`g9.r1.l-fail-2`,
"example of 129 tokens exceeds max_seq_length=40: 0 prompt tokens would survive, minimum is 16")
and correctly reverse-engineered it into an f-string template (line 2752) — but with no field
name attached to the `0`, it had to invent one, and picked a reasonable paraphrase instead of the
corpus's actual spelling. It also separately saw `num_messages` discussed (`g9.r1.say22`, "every
datum's metadata block carries num_messages," line 3921) but only in the context of the datum's
metadata envelope, which it implemented correctly (the `test_open` assertions on
`metadata["num_messages"]` all pass) — that exposure never transferred to the exception object,
because the only remark that makes that specific tie is the one it never saw.

## Redundancy elsewhere

Of the 18 remarks the pointer sheet marks as never surfaced (independently re-verified here by
grepping the transcript for each one's distinctive phrasing — none were found), 17 carry facts
that scored 1 anyway, because every one of them is redundant with at least one other remark on
the same fact that the agent *did* find (e.g. `g9.r1.l-fail-4` restates `g9.r1.l-fail-1`'s
skip-and-continue rule; `g9.r2.l9`/`g9.r2.l11` restate `g9.r2.l10`/`g9.r2.fix25`'s dropped_indices
numbering; several wiki-comment-only remarks on pages the agent never fetched restate content
that also lives in mail threads it did read fully). Only `g9.r1.l-fail-3` sat alone on
information the fact actually needed, which is exactly why this run lost one fact instead of
zero — a single un-redundant keyword gap, not a systematic weakness in the search.
