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

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
