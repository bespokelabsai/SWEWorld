# g6 run 7 (rollout e9fac7c8, eval 30b9f0dd, world-hosted v6) — reward 0.8571

## What this run found

The agent ran a genuinely thorough three-surface investigation: it cloned the repo, read the
existing `cost.py`/trackers, then worked chat, wiki and mail in that order. For chat it did not
rely on single searches — it dumped all 11 Mattermost channels to local files (`/tmp/mmdump/*.txt`,
2025–3200 posts each) and grepped repeatedly for domain terms (`resolve_model_price`,
`batch_multiplier`, `unknown_window`, "star entry", "canonical/consolidat/unified"), then read every
hit's surrounding conversation with `sed`. That discipline paid off on the hardest part of the
task: both herring↔reversal pairs were read as complete conversations (`g6.r2.rev1` at line 3401,
`g6.r2.rev2` at line 2893–2921) and the agent correctly concluded the reversed state — a single
`batch_multiplier()` owner, `1.0` on klusterai/inference.net with their old `x2` `cost()` overrides
deleted — is the one it should ship, never touching the herring's uniform-halve-then-cancel design
(`code_followed_herring: false` for both). For mail it dumped the entire admin mailbox over IMAP
(127 messages, `/tmp/mail/all.txt`) and read every relevant thread — PR 565's flag-not-name-match
decision, the REASONS-is-three-strings PR 681 thread, and the WS-054 "empty fields +
price_unavailable_reason" thread — in full.

## What it missed and why

Wiki was the weak spot, exactly where the ticket warned it would be: BookStack's `/api/search`
does not index page comments, and the agent's wiki reads were keyword-search-led rather than an
exhaustive page-by-page enumeration. It fetched ~8 pages whole (132, 139, 140, 142, 164, plus a
couple of release-notes pages) via a home-written script that does pull comments — which is why it
caught `g6.r1.l5`, `g6.r1.l8` and `g6.r2.g6r2-s3-l2`. But four comment-only clues that never
happened to sit on a page whose *body* matched one of its keyword searches were never opened at
all: `g6.r1.l2` and `g6.r1.l12` both live as comments on the "WS-050: Batch Mode" page, which
surfaced twice as a bare search-result title (lines 1735, 1746) and was never fetched by ID. Even
one page-*body* clue that BookStack search does index (`g6.r2.g6r2-s4-l2`, on the Jun 23
weekly-sync page) was missed simply because none of the keyword passes used happened to match it.
None of this cost the run a fact, though — every requirement had enough redundant carriers that the
misses were absorbed.

Chat had its own near-misses of a gentler kind: two broad "pricing"/"price" searches (lines
2480–2601) returned dozens of one-line snippets from Mattermost's search API, and several clues
(`g6.r2.g6r2-s1-l1`, `g6.r1.l6`, `g6.r1.l11`, `g6.r1.l14`, `g6.r2.g6r2-s1-l3`, `g6.r2.g6r2-s2-l1`,
`g6.r2.g6r2-s3-l1`) only ever appeared as one out-of-context fragment of a multi-line exchange, never
followed up with a full `sed` read of that region. Some of those fragments happened to carry the
substantive content anyway (`g6.r2.g6r2-s1-l3`'s "only one place in the tree gets to touch the price
for batch" came through verbatim); others didn't (`g6.r1.l6`, `g6.r2.g6r2-s1-l1` never surfaced at
all under any search term tried).

## A genuine task-version divergence, not an agent error

One mail thread is worth flagging on its own: `g6.r2.g6r2-s2-l4` ("Re: Weekly update: week of Apr
7"). In *this run's* v6 world, Konrad's closing reply says the klusterai halving he found was
**wrong** and needs correcting back up to the table rate — which matches the true rule that
klusterai must never be discounted. The repo's v7 answer key quotes a differently-worded exchange
in which Emil defends the halving as deliberate and correct, which would *contradict* the rule.
Per the reader brief, this is judged against what the transcript actually served: the v6 world here
happened to be the more consistent version, and the agent's own terminal separately truncated the
middle of that thread at a 10000-byte output cap (a self-inflicted near-miss, not a search failure)
— moot either way, since `rev1`, `rev2` and the `g6r2-s2-l2` mail thread independently nailed the
same conclusion in full.

## Why the one lost fact was lost

`g6.r1.observability` failed on a real implementation bug, not a missed remark. The grader's
failing assertion is `_KlusterAICostProcessor(batch=False).cost(...) == 0.0` for an unpriced model;
instead `UnpricedModelError` propagates straight out of `cost()`. Looking at the shipped code
(transcript lines 5086–5112), `_KlusterAICostProcessor.cost()` and `_InferenceNetCostProcessor.cost()`
both call `_register_external_model(...)`, which calls `resolve_model_price(...)` with **no**
`try/except` around it. Compare that to the two status trackers' `refresh_model_price()` (lines
5284–5299, 5388–5402), where the agent wrote the exact right pattern — `except UnpricedModelError as
err: self.price_unavailable_reason = err.reason`, plus a catch-all "never raise out of price
resolution" — twice. The agent clearly understood the requirement (it's stated in its own Analysis
at line 3999, and traces to remarks `g6.r1.l11`/`g6.r1.l12`/`g6.r2.fix18`) and applied it correctly
to both trackers, but never carried the same wrapper into the two external cost-processor overrides,
and never wrote a test that called `.cost()` on an unpriced model through those two processors before
declaring the ticket done. This is an `implementation_slip`, cleanly localized to two classes.

## Bottom line

29 of ~33 remarks were surfaced with enough fidelity to act on; the herrings were correctly
distinguished from their reversals; six r1/r2 facts scored 1 on solid, quotable grounds. The one
loss is not a corpus or search failure — it is a one-line gap between two otherwise-correct,
independently-written implementations of the same degrade contract.
