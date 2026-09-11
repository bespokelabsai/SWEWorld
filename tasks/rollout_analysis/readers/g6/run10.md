# g6 run 10 (eval 30b9f0dd, rollout d949cdcf) — reward 0.8571

## What this run found

This rollout built the entire ticket correctly and recovered six of the seven hidden
facts. Its search was genuinely comprehensive by volume: it dumped all ~189 BookStack
pages with their full comment trees into one local file after discovering (the hard
way — an `AttributeError` on the first comment-parsing attempt) that comments needed a
separate walk from the page body; it logged into Mattermost's v4 API and pulled every
channel's complete history (10,824 lines, 12 channels) rather than relying on search;
and it used targeted IMAP fetches once it had a subject-line index from the weekly
digest mails. On the design side it correctly reconstructed r1's three-reason,
outermost-check-wins failure contract (line 2854, 4040-4062) and r2's single-owner
`batch_multiplier()` architecture including the azure/base symmetry (line 1858) and the
klusterai/inference.net non-discount exemption (line 2543, 3467-3477, 2504-2513) —
including correctly siding with the *reversal* of both January herrings rather than the
herrings themselves, even though it only ever encountered the herrings' content
secondhand, recapped inside the reversal conversations it actually read.

## What it missed, and why

Twelve of the 33 planted remarks never surfaced anywhere in the transcript, including
both original herring exchanges and one genuinely load-bearing wiki comment
(`g6.r1.l8`). The pattern is consistent: chat was grepped with narrow, topic-specific
term lists (`batch_multiplier|batch multiplier|inferred|asterisk|...`,
`unknown_provider|unknown_model|...|null price`) rather than swept broadly, so any
remark whose distinctive wording ("quarter of the invoice", "misspelled the provider",
"cookbook user", "nonetype in the cost sum") wasn't anticipated by a query term was
invisible even when the raw dump held it. The clearest case is `g6.r1.l8`: page 140
("model price lookup: what a miss returns") was fetched twice — once early, when a
comment-parsing bug silently returned zero comments (line 1231-1291), and once inside
the full 177-page bulk dump, where the comments *should* have been present — but no
later grep pattern used words like "null" or "no more use... than no row", so the
actual clue (dermot's comment that a null input price must miss exactly like an absent
key) was never read a second time. Worse, the page's own body is a real in-world
distractor here: it describes an older `lookup_price` function that explicitly "does
not raise", the opposite of r1's rule. The agent correctly refused to let that mislead
it (r1.rule still scored 1), but in dismissing the page as "likely a decoy" (line 1297)
it also stopped looking at its comments.

None of these twelve misses cost a fact on their own — every fact except one had
redundant carriers, which is exactly the resilience the spread requirement (≥2
sources, ≥3 weeks, ≥2 channels per requirement) is meant to buy.

## The one fact it believed and still shipped wrong

`g6.r2.exclusions_or_crossover` (a user-supplied price must never be discounted) is the
one real miss, and it is not a search failure — the agent read and correctly
paraphrased the requirement twice: at line 1527 ("the 0.5 batch multiplier belongs to
lookup-path prices only, not caller-supplied") after reading wiki page 132, and again
at line 2218 ("`batch_multiplier` should read a class flag... instead of an if-chain on
provider names") after reading the PR 565 mail thread. But those two readings never
met. When it actually wrote `batch_multiplier()` (line 4638-4639), its reasoning
reconciled the mail's "class flag" idea *only* with the klusterai/inference.net
provider-level exemption (`batch_pricing_already_listed`), landing on a data-driven
design that derives the discount ratio by calling `resolve_model_price()` for
batch=True and batch=False and comparing them. The base processor's `__init__` does
register a caller-supplied `in_mtok_cost` into litellm's price table — but
`batch_multiplier()` itself never checks `config.in_mtok_cost`, so once a user's price
is registered it is indistinguishable from any ordinary litellm list price and gets
halved anyway. This is exactly the failure the grader catches:
`_LitellmCostProcessor discounted a user-supplied price; assert 0.5 == 1.0`. The agent
never tested this path itself (no `in_mtok_cost=` appears anywhere in its own
verification commands), so the gap went unnoticed until grading.

## One thing worth flagging about the corpus

The answer key in the repo is written for task version 7, one version ahead of this
run. For one remark (`g6.r2.g6r2-s2-l4`, the "Re: Weekly update: week of Apr 7" mail),
the v7 key's quoted text has emil telling Konrad the klusterai batch half-price *is*
correct ("halved for the klusterai batch line, as listed everywhere else") — which
directly contradicts the grader's own `test_scope` (klusterai must never be
discounted). The v6 world this rollout actually ran against served the opposite-sense
email ("the half-of-table figure it returned is the bug, not the answer... Put the
table figure on the sheet, not the halved one" — line 3545-3556), which matches the
grader correctly. This did not cost the run anything since v6's wording pointed the
right way, but it means the v7 doc text for this remark should not be trusted as
written.
