You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Unified model price resolution**

Consolidate the scattered, inconsistent model-price lookups into one canonical path.

Today that logic is spread across `src/bespokelabs/curator/cost.py` — which mixes external-table and litellm-table logic ad hoc across `external_model_cost()` and four separate `cost()` methods — and across the batch/online status trackers.

### 1. Add a frozen dataclass `ModelPrice`

With these fields:

- `model: str`
- `provider: str | None`
- `completion_window: str`
- `input_cost_per_million: float`
- `output_cost_per_million: float`
- `source: str` ("litellm" or "external")
- `batch: bool`
- `output_price_inferred: bool`
- `max_tokens: int | None`

Plus `input_cost_per_token`/`output_cost_per_token` properties (`round(value, 9)` for per-million figures, `round(per_million/1e6, 15)` for per-token).

### 2. Add `UnpricedModelError(LookupError)`

- A class-level `REASONS` frozenset naming the permitted reason strings.
- A keyword-only `__init__(*, model, provider, completion_window, reason)` that raises `ValueError` for an unrecognized `reason`.
- Otherwise it produces the message `f"{reason}: model={model!r} provider={provider!r} completion_window={completion_window!r}"`.

### 3. Add `resolve_model_price(model, *, provider=None, completion_window=None, batch=False) -> ModelPrice`

The single function that consults `_DEFAULT_COST_MAP`'s external provider tables and `litellm.model_cost`. It:

- Raises `UnpricedModelError` instead of ever returning a `None`-valued price.
- Applies a batch-rate discount to the returned per-million prices where the pricing data calls for it when `batch=True`.
- When a table entry has no explicit output price, copies the input price into the output price and sets `output_price_inferred=True`.

### 4. Add `register_price_with_litellm(price: ModelPrice) -> dict`

- Writes `{"max_tokens": ..., "input_cost_per_token": ..., "output_cost_per_token": ..., "litellm_provider": ...}` into `litellm.model_cost` via `litellm.register_model`.
- Raises `ValueError` if `price.batch` is `True`.
- Returns that same four-key `{"max_tokens": ..., "input_cost_per_token": ..., "output_cost_per_token": ..., "litellm_provider": ...}` dict — the entry it just wrote, not `{price.model: {...}}`.

### 5. Add `format_cost_strings(price: ModelPrice | None, *, rich: bool) -> tuple[str, str]`

The sole place display strings like `"$0.045"` (or `"[red]$0.045[/red]"` when `rich`) are built. It:

- Appends `"*"` to the output string when `output_price_inferred` is true.
- Returns `("N/A", "N/A")` (or the `[dim]`-wrapped equivalent) for `price is None`.

### 6. Rewrite `external_model_cost(model, completion_window="*", provider="default") -> dict[str, float]`

As a thin shim over `resolve_model_price(..., batch=False)`.

### 7. Delete `_get_litellm_cost_map`

### 8. Give `BatchStatusTracker`/`OnlineStatusTracker` two new fields and one new method

New fields:

- `price_unavailable_reason: Optional[str]`
- `output_price_inferred: bool`

New method `refresh_model_price(*, price_model: str | None = None) -> Optional[str]`, called from `model_post_init`/`__post_init__` and from the batch request processors' `set_model_cost()`. It:

- Re-resolves and assigns the two per-million prices, `output_price_inferred`, and `input_cost_str`/`output_cost_str` (via `format_cost_strings`).
- Sets `price_unavailable_reason` to `None` on success or to `err.reason` on `UnpricedModelError`.
- Never raises.

## What the team said

Chat, the wiki and internal mail, over the months this area was being worked on, oldest first. Some of it is people thinking aloud and some of it was settled later.

<!-- planted 2026-09-03T17:54:48+00:00 -->

**2025-01-27 · #pipeline · dario**

> went and looked - settled: the base cost processor halves every source, and klusterai/inference.net multiply their cost() by 2 to cancel it, their tables are already batch-tier

**2025-01-27 · #engineering · konrad**

> @Dario discount stays in the base, providers whose table already lists batch prices cancel it with a x2 in their own cost() override, klusterai and inference.net both do this

**2025-03-14 · #engineering · emil**

> Pasting what i got back: resolve_model_price("no-such-model", provider="not-a-provider", completion_window="96h") gives unknown_provider, not a word about the model or the window - yup, right call for an unregistered provider.

**2025-03-19 · #pipeline · gideon**

> The batch estimate came in at a quarter of the invoice again, so basically two separate layers each knocking half off the same price. Nobody's disputing that part at this point.

**2025-03-21 · #pipeline · nils**

> context on that fix - i burned twenty minutes chasing a window typo when the real problem was that I had misspelled the provider. the error should name the first thing that's wrong.

**2025-03-24 · #engineering · gideon**

> Ya, thats not theoretical - tracker took the whole online run down last night 4k requests in, on a model litellm has never heard of. Cost display, not the work.

**2025-03-25 · #pipeline · nils**

> on the adding side, my batch test pins resolve_model_price(m, provider="klusterai", completion_window="*", batch=True).input_cost_per_million at 4.0, same float as batch=False. same test, source == "litellm" halves input_cost_per_million and output_cost_per_million both.

**2025-03-26 · #pipeline · nils**

> let me think - klusterai's published per-million is already their batch rate, and we went and took another 50% off it in the estimate.

**2025-04-03 · #cookbooks · konrad**

> @Emil worth one, yes. A cookbook user put their negotiated input cost straight in the config and the batch run reported half of what they typed.

**2025-04-03 · #pipeline · gideon**

> so basically batch_multiplier() comes back 0.5 on the base cost processor and 0.5 on azure, tbh one number for both. outside batch mode both hand back 1.0.

**2025-04-07 · #pipeline · dario**

> while we're on cost numbers - i lost an hour today to a nonetype in the cost sum, the price came back with the input side empty and we summed it anyway

**2025-04-07 · #engineering · nikolai**

> for the record the klusterai row in pr 622 is 4.0 per million input straight off their pricing page. no window split on their table at all it just sits under "*"

**2025-04-08 · mail: PR 565: cost reporting before it lands · dermot**

> reading the cost path in 565 — we're picking who gets the batch discount with an if-chain on provider names inside batch_multiplier, that belongs on the class as a flag instead.

**2025-04-14 · wiki: v0.1.22 Release Notes · dermot**

> on the 50% line: resolve_model_price has no separate batch row, batch=True scales what batch=False returned. whichever number batch_multiplier() hands the processors, it should be reading that same one.

**2025-04-14 · mail: Weekly update: week of Apr 7 · emil**

> on your cost question — resolve_model_price with provider=klusterai and batch=True came back at half the table rate, and anything we read out of those provider tables should come back exactly as listed.

**2025-04-14 · #pipeline · dario**

> batch stats: two layers each halving is why estimates came in at a quarter of the invoice. batch_multiplier() is the only place that factor lives now, 1.0 on klusterai and inference.net, no cost() override.

**2025-04-15 · #pipeline · dario**

> while we're on the provider cost paths, i left the same note on the azure cost() override again: why is this dividing by two here when batch_multiplier already ran

**2025-04-21 · mail: Weekly update: week of Apr 14 · dario**

> on WS-054 — for the trackers input_cost_per_million and output_cost_per_million just stay empty and the reason sits on price_unavailable_reason, so we can show why rather than a number.

**2025-04-21 · wiki: WS-050: Batch Mode (50%-Cost Async Batch APIs) · dermot**

> if the table has no number for it i would rather the lookup raise UnpricedModelError at the call site than hand back a price with a hole in it.

**2025-04-22 · wiki: Weekly Notes \u2014 Week of Apr 14 · dario**

> re the batch vs online cost question — i had an online run showing batch pricing in the tracker all afternoon. outside batch mode the list price comes through untouched, thats settled at least.

**2025-05-01 · #code-review · dermot**

> that said, the pricing gaps part of that page: input_cost_per_million comes through None and the viewer renders it $0.00, which readers read as free. that zero shouldnt be shown.

**2025-05-02 · #code-review · emil**

> spent the morning working out which of the two subtracions was the real one. only one place in the tree gets to touch the price for batch, we agreed that much.

**2025-05-13 · wiki: Price Lookup Errors: What Each Bad Argument Actually Raises · gideon**

> so basically same args but with a provider we do have registered and it comes back unknown_model instead, so the junk window never even gets looked at.

**2025-05-27 · wiki: WS-050: Batch Mode (50%-Cost Async Batch APIs) · konrad**

> Related: sometimes the price cant be resolved at all. Every cost() method should be catching that and handing back 0.0 rather than ending a run over an accounting number.

**2025-06-02 · mail: Week of May 26 recap: v0.1.25 shipped · konrad**

> One note on PR 681: I passed reason='no_pricing_data' and the constructor threw ValueError straight back at me - it checks the arg against UnpricedModelError.REASONS, which is those three strings and nothing else.

**2025-06-03 · #engineering · konrad**

> Also scratch my reviewr note about the x2 in the provider's cost() override, those overrides are deleted. Where a table already lists batch prices, batch_multiplier() returns 1.0 and resolve_model_price leaves the external-sourced price as listed.

**2025-06-10 · wiki: Cost estimates in batch mode: where the price numbers come from · nikolai**

> if the price per million came from the user then thats already the number they pay so batch mode shouldnt be knocking anything off it either

**2025-06-18 · mail: Week of Jun 9 rollup: gemini batch runs showing $0.00 · nikolai**

> right that gemini row does exist in litellm.model_cost but input_cost_per_token on it is null and we priced a whole week of runs at zero off the back of it

**2025-06-18 · mail: batch cost estimates: the 50% discount is being applied to every processor · nikolai**

> same story with inference.net the number on their pricing page is already what a batch job costs so theres nothing left to take off it

**2025-06-25 · #code-review · emil**

> let me think through that - if a model's map has no row for the window you asked for thats unknown_window, we shouldnt be quietly borrowing the "*" tier.

**2025-06-25 · wiki: Weekly sync notes: week of Jun 23 (batch mode) · emil**

> On pricing: azure's batch_multiplier() keeps drifting from the base processor's; we agreed identical in and out of batch mode, with cost() just scaling the resolved price by self.batch_multiplier().

**2025-06-26 · wiki: Price Lookup Errors: What Each Bad Argument Actually Raises · emil**

> circling back on the paragraph above — the window case does have a name after all, its `unknown_window`. chased it down in #code-review yesterday: if the map has no row for the window you asked for, thats what comes back, it does not quietly borrow the `"*"` tier. so this page can stop calling it folklore; someone fold it into the table next time theyre in here.

**2025-06-26 · #pipeline · nils**

> while you're in there - there's no 24h row for that model so the lookup fell through to the star entry, and my batch report came out with online prices again

**2025-07-02 · wiki: model price lookup: what a miss returns · dermot**

> a row in the pricing table with a null input price is no more use to us than no row at all, it should come back exactly the way a missing key does.

## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>. Your account is `worldadmin`, password `worldadmin`; a token is readable at `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator` and its dependencies are installed in the virtualenv at `$CURATOR_VENV` (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the library and its tests. The library itself is NOT installed there — put your checkout's `src/` on `PYTHONPATH`.
- Complete this ticket to the best of your ability using every source of information you can reach: the repository's own history and issues, the company chat, the wiki, internal mail. Any of them may carry something the ticket does not say.
- Some of what this company decided, it never got round to doing. The history holds designs that were agreed and then parked — "that's its own ticket", "when we get to it" — and parked is not cancelled. Where a decision was settled and the code does not reflect it yet, carrying it out is part of this ticket, not a reason to leave it alone.
- The ticket is where the work starts, not a complete specification of it, and it is not the newest word on anything. It was written short. Where the record settles something the ticket leaves out, or names a field, a value or a behaviour the ticket does not, that is an addition to what you owe — not an earlier draft the ticket has replaced. So the record adds to the ticket. Where the ticket states something outright, that stands — a page that looks like it contradicts the ticket is nearly always about a neighbouring question, and the move is to find what it actually names rather than overrule the ticket with it.
- Chat is at <http://chat.world.local>, the wiki at <http://docs.world.local>, webmail at <http://mail.world.local>, and the service list at <http://pass.world.local>. Gitea and Mattermost want the username `worldadmin`; BookStack and Roundcube want the email `worldadmin@world.local`.
- The wiki has a REST API — `Authorization: Token $(cat /etc/sweworld/bookstack-token)` — and `/api/search?query=...`, `/api/pages/{id}` return JSON, which is easier to read than the HTML.
- Wiki pages carry **comments**, and BookStack's search does not index them — a term that exists only in a comment returns nothing from `/api/search`. `/api/pages/{id}` returns that page's `comments` alongside its body, so a page worth reading is worth fetching whole.
- Mail is readable over **IMAP on `:143`** as `worldadmin@world.local` (password `worldadmin`; plain `imaplib.IMAP4`, plaintext auth is allowed on this port, no TLS handshake needed). The admin mailbox holds a copy of every message in the company, so `SEARCH` and `FETCH` over `INBOX` reach all of it — Roundcube at <http://mail.world.local> is that same mailbox with a browser in front of it, which is harder to read from a shell, not easier.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
