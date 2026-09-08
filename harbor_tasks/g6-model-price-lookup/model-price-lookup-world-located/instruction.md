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

## Where the conversations are

You do not have to go looking. Every conversation in this company that bears on this ticket is listed below — 33 of them, oldest first — with exactly where it sits.

The list says **where**, and nothing else. It does not say what was said, who was right, which conversations matter most, or how they relate to each other. That is the part left to you: open them, read them together with what is around them, and work out what they mean for this ticket.

Times are the world's own timestamps (UTC), as chat and mail record them.

| # | date | time | where |
|---|---|---|---|
| 1 | 2025-01-27 | 16:36–17:03 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 2 | 2025-01-27 | 18:30–18:47 | Mattermost `#engineering` — an exchange of 7 messages, opened by **dario** |
| 3 | 2025-03-14 | 13:11–13:21 | Mattermost `#engineering` — an exchange of 8 messages, opened by **dario** |
| 4 | 2025-03-19 | 11:44–11:53 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **emil** |
| 5 | 2025-03-21 | 09:02–09:09 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **dario** |
| 6 | 2025-03-24 | 15:25–10:57 | Mattermost `#engineering` — an exchange of 9 messages, opened by **nikolai** |
| 7 | 2025-03-25 | 13:14–13:35 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **gideon** |
| 8 | 2025-03-26 | 13:18–13:36 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **dario** |
| 9 | 2025-04-03 | 14:18–14:32 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **dermot** |
| 10 | 2025-04-03 | 16:07–16:21 | Mattermost `#cookbooks` — an exchange of 9 messages, opened by **emil** |
| 11 | 2025-04-07 | 13:51–14:07 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **gideon** |
| 12 | 2025-04-07 | 16:22–16:34 | Mattermost `#engineering` — an exchange of 8 messages, opened by **dermot** |
| 13 | 2025-04-08 | 13:12–14:26 | mail thread “PR 565: cost reporting before it lands” — an exchange of 3 messages from **dermot**. In `worldadmin@world.local`'s INBOX |
| 14 | 2025-04-14 | 09:16–11:47 | mail thread “Weekly update: week of Apr 7” — an exchange of 3 messages from **konrad**. In `worldadmin@world.local`'s INBOX |
| 15 | 2025-04-14 | 11:42–15:26 | the wiki page “v0.1.22 Release Notes” (`docs/releases/v0-1-22-release-notes.md`) — an exchange of 2 **comments** opened by **dermot**, not the page body |
| 16 | 2025-04-14 | 11:52–12:21 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **gideon** |
| 17 | 2025-04-15 | 18:30–18:43 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **dermot** |
| 18 | 2025-04-21 | 09:58–14:26 | the wiki page “WS-050: Batch Mode (50%-Cost Async Batch APIs)” (`docs/engineering/ws-050-batch-mode-50-cost-async-batch-apis.md`) — an exchange of 2 **comments** opened by **dermot**, not the page body |
| 19 | 2025-04-21 | 13:08–15:07 | mail thread “Weekly update: week of Apr 14” — an exchange of 4 messages from **dario**. In `worldadmin@world.local`'s INBOX |
| 20 | 2025-04-22 | 09:47–15:12 | the wiki page “Weekly Notes \u2014 Week of Apr 14” (`docs/meetings/weekly-notes-week-of-apr-14.md`) — an exchange of 2 **comments** opened by **dario**, not the page body |
| 21 | 2025-05-01 | 09:06–09:17 | Mattermost `#code-review` — an exchange of 7 messages, opened by **gideon** |
| 22 | 2025-05-02 | 12:26–12:36 | Mattermost `#code-review` — an exchange of 7 messages, opened by **dario** |
| 23 | 2025-05-13 | 10:42–14:05 | the wiki page “Price Lookup Errors: What Each Bad Argument Actually Raises” (`docs/engineering/price-lookup-errors-what-each-bad-argument-actually-raises.md`) — an exchange of 2 **comments** opened by **gideon**, not the page body |
| 24 | 2025-05-27 | 10:42–15:20 | the wiki page “WS-050: Batch Mode (50%-Cost Async Batch APIs)” (`docs/engineering/ws-050-batch-mode-50-cost-async-batch-apis.md`) — an exchange of 2 **comments** opened by **konrad**, not the page body |
| 25 | 2025-06-02 | 11:14–12:20 | mail thread “Week of May 26 recap: v0.1.25 shipped” — an exchange of 3 messages from **konrad**. In `worldadmin@world.local`'s INBOX |
| 26 | 2025-06-03 | 18:20–18:40 | Mattermost `#engineering` — an exchange of 8 messages, opened by **dermot** |
| 27 | 2025-06-10 | 10:41–15:02 | the wiki page “Cost estimates in batch mode: where the price numbers come from” (`docs/engineering/cost-estimates-in-batch-mode-where-the-price-numbers-come-from.md`) — an exchange of 2 **comments** opened by **nikolai**, not the page body |
| 28 | 2025-06-18 | 13:12–15:20 | mail thread “Week of Jun 9 rollup: gemini batch runs showing $0.00” — an exchange of 3 messages from **dermot**. In `worldadmin@world.local`'s INBOX |
| 29 | 2025-06-18 | 13:42–15:16 | mail thread “batch cost estimates: the 50% discount is being applied to every processor” — an exchange of 4 messages from **nikolai**. In `worldadmin@world.local`'s INBOX |
| 30 | 2025-06-25 | 09:28 | the wiki page “Weekly sync notes: week of Jun 23 (batch mode)” (`docs/meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md`) — in the **page body**, written by **emil** |
| 31 | 2025-06-25 | 15:44–15:57 | Mattermost `#code-review` — an exchange of 6 messages, opened by **gideon** |
| 32 | 2025-06-26 | 14:03–14:21 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **gideon** |
| 33 | 2025-07-02 | 10:24–15:47 | the wiki page “model price lookup: what a miss returns” (`docs/engineering/model-price-lookup-what-a-miss-returns.md`) — an exchange of 2 **comments** opened by **dermot**, not the page body |

A row gives the window an exchange runs in and how many messages it is — not how much is around it. A busy channel interleaves other talk with it, and a mail thread can have begun earlier and under someone else's name, so read the window and its surroundings rather than counting messages off.

A wiki **comment** is not in the page body and BookStack's search does not index it; `/api/pages/{id}` returns a page's `comments` alongside its text.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
