# g6 run 5 (rollout f6788014, eval 30b9f0dd, world-hosted v6) — reward 0.8571

## What this run found

The agent ran a thorough, well-organized investigation: platform search first to get pointers,
then bulk local dumps of 8 Mattermost channels (grepped repeatedly with widening keyword lists),
BookStack `/api/search` to find candidate pages followed by whole-page-plus-comments fetches once
it discovered the comments JSON shape (lines 1662–1717), and an IMAP script with iterative keyword
passes over the shared mailbox. This recovered 6/6 mail remarks, 7/7 wiki-comment remarks read
whole (including the one wiki page body carrier), and most of the chat remarks that were
grep-reachable. It built a correct, closed-book implementation of `ModelPrice`,
`UnpricedModelError` with the three-reason closed vocabulary and provider→model→window precedence
(g6.r1, all three facts pass), and a single-owner `batch_multiplier()` design with a class-level
`batch_pricing_in_table` flag replacing the old name-chain / herring arrangement (g6.r2.rule,
g6.r2.scope, g6.r2.observability all pass). Its own pre-push sanity check (line 8688–8692)
reproduced the settled numbers exactly: kluster 1.0, base 0.5, azure 0.5, online 1.0.

## What it missed, and why

**g6.r2.exclusions_or_crossover scored 0** — the one lost fact. The grader's failing assertion
(`test_exclusions__a_user_supplied_price_is_taken_as_given...`) shows `_LitellmCostProcessor`
discounting a user-supplied price by 0.5 instead of leaving it at 1.0. This is not a
not-found problem: the agent `cat`'d wiki page 132 in full at step 21 (transcript lines
1974–2061), which states in the page body — "The multiplier does not apply to caller supplied
prices - if the number came from the user it is already the number they pay so nothing should
come off it in batch mode either" — and again in Nikolai's comment on the same page — "if the
price per million came from the user then thats already the number they pay theres nothing left
to knock off it." The agent's own Analysis at line 2067 reduces this to one generic line, "Page
132 confirms batch discount rules," and never carries the caller-supplied exemption forward as a
design requirement. When it wrote `batch_multiplier()` (lines 5334–5338), the method checks only
`self.batch` and `self.batch_pricing_in_table` — never `self.config.in_mtok_cost`, the very field
its own `__init__` (line 5317) uses one paragraph earlier to detect a user-supplied price. Its
pre-push verification (line 8688–8692) never exercised a processor with an explicit config price,
so the gap surfaced only at grading. The final self-summary (line 9569) lists everything it
believes it shipped, and the user-price exemption is absent from that list — confirming the miss
was never re-registered after step 21. Cause: **implementation_slip** — the rule was read in full,
twice, and simply never made it from corpus to code.

A separate, structural gap compounds this: the bulk Mattermost channel dump (line 2518–2520)
omits **#cookbooks** entirely — the channel holding the single clearest statement of the same rule
(a cookbook user's negotiated price getting halved). It was not the deciding cause here, since the
wiki carrier of the identical rule was found and still not acted on, but it means a second,
independent path to the same requirement was closed off from the start.

Ten of 33 remarks were never surfaced at all (2 herrings/near-duplicates, 8 clues), all sharing
the same shape: the correct channel or the correct mail search was in scope, but the specific
grep keyword used for that date/topic was never tried (e.g. "quarter of the invoice",
"misspelled the provider", "nonetype", "24h row", "$0.00", "subtracions"). None of these
individually cost a fact, since each supporting sub-conclusion had 2–4 independent carriers and
enough were found; the one wiki-comment page never fetched (`v0-1-22-release-notes.md`) likewise
did not matter because its content (single-owner `batch_multiplier`) was independently recovered
from mail and the two reversal threads.

## Herrings

Both herrings (the pre-reversal "base halves everyone, klusterai/inference.net cancel with ×2")
were correctly not followed. The original 2025-01-27 posts were themselves barely surfaced (one
not at all, one only via a later recap inside the reversal thread), but both reversals
(g6.r2.rev1, g6.r2.rev2) were read in full and their content — "the factor lives in
`batch_multiplier()` now and thats the only place it lives" / "nothing has to [cancel it], where a
table already lists batch prices, `batch_multiplier()` returns 1.0" — is exactly what shipped.
`code_followed_herring: false` for both.
