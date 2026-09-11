# g6 run 2 (rollout ce421264, eval 30b9f0dd) — reward 0.857

## What this run found

This is a strong run: it recovered every subconclusion of `g6.r1` and three of four
subconclusions of `g6.r2`, missing only `r2.observability`. Of the 33 planted remarks
(29 clues, 2 herrings, 2 reversals), 23 were demonstrably surfaced and read in full;
10 never appeared in the transcript at all. Despite that 30% miss rate, no requirement
subconclusion was actually starved of evidence, because the plant gave every
subconclusion 3-4 independent carriers and the agent's search, while imperfect, was
never so narrow that it missed *all* of them for any one point.

Mail was the strongest surface: all 6 mail remarks were found, because once the agent
located the relevant thread subjects (PR 565, WS-054, PR 681/REASONS, the two
per-provider batch threads, the gemini-$0.00 rollup) it read every message in each
thread top to bottom (transcript lines 2503-2699). Chat was searched by dumping every
Mattermost channel to a file and grepping keyword families ('price'/'pricing'/'cost',
then 'reason'/'inferred'/'asterisk'/'register'), reading the surrounding date window
whenever a hit landed. This found 13 of 19 chat remarks but missed 6 whose wording
didn't contain the searched keywords (e.g. `g6.r1.l1`'s "nonetype in the cost sum",
`g6.r1.l6`'s "misspelled the provider", `g6.r1.l9`'s "fell through to the star entry")
— the agent never fell back to browsing a channel by date range once keyword search
went quiet. Wiki was weakest: a single `/api/search` for 'price'/'pricing'/'cost'
(never 'batch') returned exactly 6 pages, all correctly fetched whole with comments
(BookStack doesn't index comments, and the agent knew this from the ticket's own
notes at line 147) — but of those 6, page 33 (a same-titled duplicate of "WS-050:
Batch Mode" carrying konrad's `g6.r1.l12` comment) was saved to disk and never
actually opened; the agent read page 156 (the other copy, carrying dermot's `l2`
comment) instead and moved on. Two more wiki-comment remarks
(`g6.r2.g6r2-s1-l4` on `v0-1-22-release-notes.md`, `g6.r2.g6r2-s2-l3` on
`weekly-notes-week-of-apr-14.md`) live on pages the search never returned at all.

## What it believed, and why

Both herrings were correctly resisted. The original 1/27 exchanges (klusterai and
inference.net cancelling the base discount with a `*2` in their own `cost()`) were
barely glimpsed — herring1 not at all, herring2 only as one stray line in a keyword
grep dump (transcript line 3432). But both reversals (`g6.r2.rev1` at line 3687,
`g6.r2.rev2` at lines 3526-3546) were read in full, and each reversal thread happens
to recap the old, wrong belief in the sentence immediately before overturning it
("that was the arrangement as i remember it... that whole arrangement is gone" —
line 3685-3687). So the agent effectively received the herring's content packaged
inside its own retraction, and its shipped code reflects the reversal exactly: no
`*2` override on either provider's `cost()`, and `batch_multiplier()` is the single
place the factor lives (`_LitellmCostProcessor.batch_multiplier()`, with
`table_lists_batch_prices=True` making klusterai/inference.net return `1.0`).

## Why the lost fact was lost

`g6.r2.observability` fails on one assertion:
`resolve_model_price(LITELLM_MODEL, batch=True).input_cost_per_million == 1.0`,
which actually returns `2.0` — the litellm-sourced price comes back completely
undiscounted. This is **not** a missed remark or a misread world: the agent's own
final synthesis (transcript line 4681) correctly states "(c) caller-supplied
(in_mtok_cost/out_mtok_cost) prices must not be halved" — it understood
`r2.exclusions_or_crossover` fully, and that fact scored 1.

The bug is in the mechanism the agent built. `cost.py` declares a module-level
global, `_CALLER_SUPPLIED_MODELS: set = set()`. Whenever a cost processor is
constructed with a caller-supplied `in_mtok_cost`, `_LitellmCostProcessor.__init__`
adds `config.model` to this set — and never removes it. `_resolve_litellm` then
gates the batch discount on `if batch and key not in _CALLER_SUPPLIED_MODELS`. The
grader's own test file runs `test_exclusions` before `test_observability` (matching
pytest's definition order), and `test_exclusions` constructs
`BatchRequestProcessorConfig(model=LITELLM_MODEL, in_mtok_cost=3)` — permanently
poisoning the global set with `"g6-litellm-priced-model"`. By the time
`test_observability` calls `resolve_model_price(LITELLM_MODEL, batch=True)` on the
*same* model string with no caller-supplied cost in play, the stale entry still
suppresses the discount. This is exactly the anti-pattern the requirement's own
`exclusions` fact rules out — "decided by a class-level flag... not by a name
comparison at the call site" — reproduced one level up, as a name-keyed global cache
in the module-scoped lookup path, sitting alongside a per-instance flag
(`self._caller_supplied_price`) that *does* work correctly in isolation. The agent's
own test suite (`tests/unittests/test_model_price.py`) never exercises this
cross-call sequence either, so its own verification pass could not have caught it.

## Bottom line

One lost fact, `g6.r2.observability`, cause **implementation_slip**: correct
understanding, buggy global-state implementation that only misfires under a specific
call order the agent never tested. Every other fact — all of `r1`, and `r2.rule`,
`r2.scope`, `r2.exclusions_or_crossover` — is solidly grounded in remarks the agent
read and reasoned about explicitly, and the shipped code (pushed at `68f5f44`, CI
green, deployed) matches that reasoning.
