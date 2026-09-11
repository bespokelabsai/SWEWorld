# g6 model-price-lookup — run 9 (world-hosted v6, eval 30b9f0dd, rollout ed6472ea)

**Reward 0.8571 — 6 of 7 declared facts scored, one lost.**

## What this run found

The agent's search strategy was disciplined for a corpus it never searched live: it dumped
the entire Mattermost history via the API (10,068 lines to `/tmp/chat.txt`), the full admin
IMAP mailbox to `/tmp/mail.txt`, and — critically — walked BookStack's `/api/pages/{id}` for
every page so that comments (which `/api/search` does not index) came along with the body.
Working from those dumps with targeted `grep`/`grep -F` on function and field names it already
knew from the ticket, it recovered 25 of 33 planted remarks, both herrings, and both reversals.
It built the full `r1` design (three-reason vocabulary, provider→model→window precedence, null
price = miss, no wildcard-tier fallback, trackers degrade rather than raise) entirely from the
record, and even self-corrected a precedence bug against the record before shipping (line 8932:
"My fallback contradicts that precedence... Let me fix"). It also correctly identified the
`batch_multiplier()`/class-flag design from a mail thread (g6r2-s3-l3) and two herrings
(the "x2 in cost() to cancel the base halving" story) that it correctly recognized were
superseded by their reversals, never implementing them.

## What it missed, and why

Two wiki comments — `g6.r1.l2` and `g6.r1.l12` — were genuinely surfaced by the agent's own
greps but cut off mid-sentence by the fixed-height "Current Terminal Screen" view before their
scored clause rendered (`UnpricedModelError`'s name for l2; "Every cost() method should be
catching that and handing back 0.0" for l12). Neither string appears anywhere else in the
transcript. Six more remarks (`g6.r2.g6r2-s1-l1`, `g6.r1.l6`, `g6.r1.l11`,
`g6.r2.g6r2-s2-l1`, `g6.r2.g6r2-s3-l1`, `g6.r1.l1`, plus `g6.r2.g6r2-s1-l3` and
`g6.r2.g6r2-s2-l3`) never surfaced at all — not a corpus-access gap (the full dump existed
locally) but a grep-term gap: the agent had no reason to search for "cookbook user" or "nonetype
in the cost sum" wording it had never been given a hint to look for. None of this cost a fact
this run: every affected fact had a second, fully-surfaced carrier.

## What it believed

Both herrings (the January "base processor halves everyone, klusterai/inference.net cancel it
with `cost() *= 2`" story) were seen only as fragments via a later `cost(` grep sweep, but the
agent never treated them as live — it read the reversals (`rev1`, `rev2`, both fully surfaced)
and explicitly planned to "delete the ad-hoc halving/doubling overrides," which is what shipped.
No herring-following in the code.

## Why the lost fact was lost

`g6.r2.exclusions_or_crossover` — "a user-supplied per-million price is never discounted" —
is the one fact that failed, and it is not a missed clue. The agent read and correctly
registered the requirement from the wiki (page 132, Nikolai's and Dario's comments): "the
multiplier does not apply to caller-supplied prices... nothing should come off it in batch
mode either," recorded verbatim in its own Analysis at transcript line 2158/2177. It also
read the class-flag mail thread (`g6r2-s3-l3`) that says the exemption must be a class-level
property, not a name check. But the shipped `_LitellmCostProcessor.batch_multiplier()` —
written at full-JSON message 223, transcript lines ~5788–5800 — is:

```python
def batch_multiplier(self) -> float:
    if not self.batch or self._prices_are_batch_prices:
        return 1.0
    return BATCH_DISCOUNT
```

This is a function of `self.batch` and the per-*class* flag `_prices_are_batch_prices` only.
It never inspects anything on `self.config` — no check for `config.in_mtok_cost is not None`.
The `__init__` right above it even carries the correct reasoning as an inline comment — "A
caller-supplied price is a price, not a rate card: it is already the number they pay, so no
discount is applied to it in batch mode either" — directly over a call to
`register_price_with_litellm(...)` that folds the caller-supplied price into
`litellm.model_cost` with nothing marking it as caller-supplied, so by the time
`batch_multiplier()` runs there is no signal left to check even if it wanted to. The agent's
own words state the rule; the code nine lines below states something else. This is a textbook
`implementation_slip`, confirmed directly by the graded test's assertion: `_LitellmCostProcessor
discounted a user-supplied price / assert 0.5 == 1.0`.

## Notable: a task-version drift in the answer key itself

For `g6.r2.g6r2-s2-l4`, the transcript (line 1786–1789, Emil's mail reply) reads: *"the
half-of-table figure it returned is **the bug, not the answer**... Put the table figure on
the sheet, not the halved one; I will raise it."* The repository's answer key prints the
**opposite** sentence for the same remark id: *"the half-of-table figure it returned is **the
correct answer**, not a lost digit... you can put the halved number on the sheet with a clear
conscience."* The transcript's version is the one consistent with the actual `r2.scope`
requirement (klusterai always returns `1.0`, never halved); the key's printed quote is inverted
relative to it — evidence of a v7 corpus edit that was never carried back into this v6 world.
Per instructions, this run was graded against what it actually read, and the discrepancy cost
it nothing (the world's real text pointed the correct direction either way).
