# g6 run 4 (rollout 18bbfdc9, eval 30b9f0dd, world-hosted v6) — reward 0.8571

## What this run found

The agent read the current `cost.py` and both status trackers exhaustively before
touching the corpus, correctly identifying the four scattered `cost()` implementations
and the external/litellm split the ticket names. Its corpus search was a genuine mix of
all three surfaces: full per-day Mattermost channel dumps plus the search API for
targeted terms, IMAP `SEARCH TEXT` for mail (fetching whole threads once a hit landed),
and a hand-rolled BookStack page-dumper (`bs.py`) that pulls `/api/pages/{id}` — body
and comments together — for a shortlist of six page ids (140, 142, 132, 139, 164, 209)
assembled from context mentions rather than from `/api/search`.

That combination recovered six of seven facts outright. It correctly reconstructed: the
provider→model→window precedence for the three `UnpricedModelError` reasons (l4, l5,
l10); that a null price leg in a table row is a miss, not a zero (l7, l8, both wiki
comments on page 140 — read alongside a genuine decoy on that same page describing an
older, never-raising `lookup_price` API, which the agent explicitly named and dismissed
as a decoy at line 1775 rather than letting it override the ticket's raise-based rule);
and the entire `batch_multiplier()` redesign — a single class-flag-driven method,
`offers_batch_discount` off by default, klusterai/inference.net never discounted because
their tables are already batch-tier, caller-supplied prices exempt via a
`_caller_supplied_price` flag, and azure sharing the base processor's multiplier rather
than carrying its own (s4-l1, s4-l2, s4-l3, s2-l1, s3-l2, rev1, rev2, and the PR 565
mail thread s3-l3 that supplies the exact "class flag, off by default" design). The
shipped code implements every one of these almost verbatim against what was read.

## What it missed, and why

The one lost fact, `g6.r1.observability`, fails on a narrow but real gap: the agent
wired non-raising ("degrade") behaviour into `BatchStatusTracker`/`OnlineStatusTracker`
via a new `refresh_model_price()` — which is exactly what the ticket's own item 8 asks
for — but never extended that pattern to the four cost-processor `cost()` methods. Two
of those (`_KlusterAICostProcessor`, `_InferenceNetCostProcessor`) call
`resolve_model_price()` directly inside `cost()` with no `try/except`, so an unpriced
model propagates `UnpricedModelError` instead of returning `0.0`, failing
`test_r1.py::test_observability...every_caller_above_the_lookup_degrades`.

The hidden requirement that states this in so many words — `g6.r1.l12`, a wiki comment
on `docs/engineering/ws-050-batch-mode-50-cost-async-batch-apis.md` ("Every cost()
method should be catching that and handing back 0.0 rather than ending a run over an
accounting number") — was never read. That page was never in the agent's fetch
shortlist even though chat names the "ws-050" workstream by name twice (lines 3799,
3804), and BookStack's title/full-text search was never invoked at all in this run. The
one related remark that was partially in view, `g6.r1.l11` (a keyword-search snippet at
line 2895), surfaced only nikolai's opening question — gideon's actual answer, carrying
the fact ("tracker took the whole online run down last night... Cost display, not the
work"), was never shown. The agent's own `test_cost.py` confirms it never registered
this as a requirement: it tests `batch_multiplier()` and `resolve_model_price()` raising
in isolation, but never tests that a processor's `cost()` survives an unpriced model.

## What it believed, and why it didn't matter

Both herrings (the January 27 "halve in the base, cancel with x2 in klusterai/
inference.net's own `cost()`" design) were never read directly — the agent never
searched or dumped `#pipeline`/`#engineering` for that date. It only encountered the
belief secondhand, restated inside the two reversal threads themselves (rev1 at line
3253, rev2 at line 2997), while reading those threads specifically to confirm the
*current* design. So the agent was never at risk of implementing the herring; the
shipped `offers_batch_discount` class-flag design matches the reversals exactly.

## A corpus note worth flagging

The mail thread carrying `g6.r2.g6r2-s2-l4` reads with the *opposite* polarity in this
run's world (v6) from the repo's answer key (v7): here, emil says the klusterai batch
halving "is the bug, not the answer... Put the table figure on the sheet, not the halved
one; I will raise it" (lines 2258-2271); the v7 key quotes the same thread saying the
halved figure "is the correct answer... put the halved number on the sheet." The two are
literal inversions on whether klusterai should be discounted in batch mode. This did not
hurt the agent — the v6 wording happens to argue for the actually-correct rule (klusterai
never discounted) — but it means the answer key's own quoted text should not be trusted
verbatim against this transcript for that one remark.
