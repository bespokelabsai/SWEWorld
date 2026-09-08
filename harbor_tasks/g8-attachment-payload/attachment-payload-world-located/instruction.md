You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Canonical attachment blocks for multimodal prompts**

Replace the three per-provider `_format_multimodal` overrides with one canonical attachment block that every provider renders from.

### New module — `src/bespokelabs/curator/types/attachment.py`
- `AttachmentBlock(BaseModel)` with `model_config = ConfigDict(frozen=True)` — a provider-independent description of one attachment. Fields:
  - `kind: t.Literal["image", "document"]`
  - `source: t.Literal["url", "base64"]`
  - `mime_type: str` — always lowercase, no `;`-parameters
  - `payload: str` — the URL when `source == "url"`, else the base64 text
  - `filename: str` — never empty
  - `detail: str | None = None` — a `str` when `kind == "image"`, `None` when `kind == "document"`
- `AttachmentError(ValueError)` — base class for every attachment rejection.
- `UnknownAttachmentMimeType(AttachmentError)` with `__init__(self, url: str, attachment_type: str)`, storing `self.url` and `self.attachment_type` (the `BaseType.type` ClassVar, i.e. `"image"` or `"file"` — not the block `kind`), message `f"Cannot determine MIME type for {attachment_type} attachment: {url!r}"`.
- `MissingLocalAttachment(AttachmentError)` with `__init__(self, url: str)`, storing `self.url`, message `f"Attachment path is neither an http(s) URL nor an existing file: {url!r}"`.
- `EmptyAttachment(AttachmentError)` with `__init__(self, url: str, filename: str)`, storing `self.url` and `self.filename`, message `f"Attachment {filename} has an empty payload: {url!r}"`.
- `normalize_mime_type(value: str | None) -> str | None` — lowercase, strip surrounding whitespace, drop everything from the first `;`; `None`/`""` map to `None`.
- `_FALLBACK_ATTACHMENT_FILENAME: str = "attachment.bin"`.

### `src/bespokelabs/curator/types/prompt.py`
- Add `BaseType.is_remote` as a property: true iff `url` starts with `http://` or `https://`, case-insensitive.
- Add `_MultiModalPrompt.attachments(self) -> list[BaseType]` returning `self.images + self.files`, in that order, as a new list, leaving the inputs untouched.
- One MIME policy shared by `Image.model_post_init` (line 87) and `File.set_mime_type` (line 103): every MIME value, supplied or guessed, goes through `normalize_mime_type`.
  - When no MIME was supplied and a `url` is present, guess with query and fragment removed: `mimetypes.guess_type(url.split("?", 1)[0].split("#", 1)[0])`, so `"https://cdn.example.com/photos/cat.jpeg?size=large"` resolves to `"image/jpeg"`.
  - If the guess fails, `mime_type` stays `None` on both classes and exactly one `logger.warning` is emitted. `Image` no longer falls back to `"image/png"` for a URL.
  - The one surviving default: an `Image` with inline `content`, no `url` and no supplied MIME gets `"image/png"` (matching `_pil_image_to_bytes`, which always saves PNG).
  - Worked values: `File(url="/tmp/x/report.PDF", mime_type="Application/PDF; charset=binary").mime_type == "application/pdf"`; `Image(url="https://example.com/asset").mime_type is None`; `Image(content=b"\x89PNG\r\n").mime_type == "image/png"`.

### `base_online_request_processor.py` — building the canonical block
`BaseOnlineRequestProcessor._canonical_attachment_block(self, data: BaseType) -> AttachmentBlock` converts any `Image` or `File` into a frozen block:
- `kind` is `"image"` when the resolved `mime_type` starts with the literal `"image/"`, `"document"` otherwise. The Python class is not consulted: `File(url=".../diagram.png")` yields `kind == "image"`, and `Image(content=b"...", mime_type="application/pdf")` yields `kind == "document"`.
- `detail` is derived from the attachment's `detail` attribute when `kind == "image"` (and is `"auto"` when the attribute is absent, as it is on `File`); it is `None` when `kind == "document"`.
- `filename` is derived from `os.path.basename(data.url.split("?", 1)[0])` when that is non-empty, else `_FALLBACK_ATTACHMENT_FILENAME`.
- A remote `url` (per `is_remote`) gives `source == "url"` with the URL as `payload`; anything else gives `source == "base64"` with `BaseType.serialize()` output as `payload`.
- Refusals, in this order:
  1. A non-empty `url` that is not remote must exist as a file (`BaseType.is_local`); when it does not, raise `MissingLocalAttachment(data.url)`. This precedes the MIME check, so `File(url="/tmp/definitely-missing/notes")` (missing *and* unguessable) raises `MissingLocalAttachment`, not `UnknownAttachmentMimeType`. `File(url="s3://bucket/report.pdf")` also raises `MissingLocalAttachment`. An attachment with inline `content` and no `url` is not subject to this check.
  2. When the resolved `mime_type` is `None`, raise `UnknownAttachmentMimeType(url=data.url, attachment_type=data.type)`. This happens at block-build time only: `Image(url=...)` / `File(url=...)` construction itself never raises for a missing MIME.
  3. A `source == "base64"` attachment whose `serialize()` returns `""` raises `EmptyAttachment(url=data.url, filename=<block filename>)`, after the MIME check. A remote URL is never read, so it is never checked for emptiness.

### `base_online_request_processor.py` — rendering and assembly
- `def _render_openai_block(block: AttachmentBlock) -> dict` — module level, pure, returning exactly one of:
  - image / url → `{"type": "image_url", "image_url": {"url": block.payload, "detail": block.detail}}`
  - image / base64 → `{"type": "image_url", "image_url": {"url": f"data:{block.mime_type};base64,{block.payload}", "detail": block.detail}}`
  - document / url → `{"type": "file", "file": {"filename": block.filename, "file_url": block.payload}}`
  - document / base64 → `{"type": "file", "file": {"filename": block.filename, "file_data": f"data:{block.mime_type};base64,{block.payload}"}}`
  - No other keys. `detail` is carried on image blocks in the URL case as well as the base64 case.
- `BaseOnlineRequestProcessor._render_attachment_block(self, block: AttachmentBlock) -> dict` returns `_render_openai_block(block)`. This method is the only provider seam; providers see `AttachmentBlock` and nothing else.
- `_format_multimodal(self, data, mime_type=None) -> dict` stays as a back-compatible one-shot: `return self._render_attachment_block(self._canonical_attachment_block(data))`. The `mime_type` argument is ignored.
- `_handle_multi_modal_prompt(self, message: _MultiModalPrompt) -> list[dict]` returns the rendered attachment blocks first — images in list order, then files in list order, exactly `attachments()` — followed by one `{"type": "text", "text": <str>}` per entry of `texts`, in list order. Result length is `len(images) + len(files) + len(texts)`; a new list each call. For `_MultiModalPrompt(texts=["a", "b"], images=[img], files=[doc])` the block types are `["image_url", "file", "text", "text"]`.

### `anthropic_online_request_processor.py`
- Delete the `_format_multimodal` override (lines 111-128).
- Add module-level pure `def _render_anthropic_block(block: AttachmentBlock) -> dict`:
  - url → `{"type": block.kind, "source": {"type": "url", "url": block.payload}}`
  - base64 → `{"type": block.kind, "source": {"type": "base64", "media_type": block.mime_type, "data": block.payload}}`
  - No other keys; `detail` and `filename` do not appear. `kind` passes through, so a PDF renders as a `document` block rather than an `image` one.
- `AnthropicOnlineRequestProcessor._render_attachment_block` returns `_render_anthropic_block(block)`.

### `litellm_online_request_processor.py`
- Delete the `_format_multimodal` override (lines 163-181).
- `LiteLLMOnlineRequestProcessor._render_attachment_block` returns `_render_anthropic_block(block)` when `self._uses_anthropic_multimodal_format()` (unchanged, reused as the dispatch key) and `_render_openai_block(block)` otherwise.

### `openai_request_mixin.py` — `calculate_input_tokens` (lines 9-24)
- Today the function does `msg = msg["image_url"]` for every non-`text` block, so an anthropic-shaped block (`{"type": "image", "source": ...}`) or any document block raises `KeyError: 'image_url'`. Rewrite it to dispatch on `block["type"]` using `.get`, never on the absence of a `"text"` key.
- `"text"` costs `len(token_encoding.encode(str(block.get("text", "")), disallowed_special=()))`.
- `"image_url"` and `"image"` both cost `_OPENAI_TOKENS_PER_IMAGE["low"]` (unchanged).
- `"file"` and `"document"` blocks must also be priced by this function.
- A `str` message keeps its current behaviour. The return is an `int`.

### Constraints and non-goals
- Python `^3.10`; pydantic `>=2.9.2`; no new dependency. Nothing here imports `aiohttp`, opens a socket, sleeps, or spawns anything.
- Reuse `BaseType.serialize()` (`prompt.py:60`, `prompt.py:110`), `BaseType._is_local_uri` / `_load_file_as_b64` / `is_local` (`prompt.py:21-34`), `_MultiModalPrompt.load` / `.model_validate`, and `_unpack_multimodal` (`base_online_request_processor.py:110`) as they are.
- Out of scope: the batch path (`openai_batch_request_processor.py:66`), `File` having no `detail` attribute, and the `self.config.model.split("/")[0]` gate at `litellm_online_request_processor.py:139`.
- Both renderers are module-level pure functions taking only an `AttachmentBlock`, so they can be exercised without constructing a configured processor.
- Tests construct processors with `object.__new__(StubOnline)` or a no-arg `__init__`: no config, no cost processor, no I/O beyond a `tmp_path` file.

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

You do not have to go looking. Every conversation in this company that bears on this ticket is listed below — 51 of them, oldest first — with exactly where it sits.

The list says **where**, and nothing else. It does not say what was said, who was right, which conversations matter most, or how they relate to each other. That is the part left to you: open them, read them together with what is around them, and work out what they mean for this ticket.

Times are the world's own timestamps (UTC), as chat and mail record them.

| # | date | time | where |
|---|---|---|---|
| 1 | 2025-01-21 | 15:22–15:38 | Mattermost `#releases` — an exchange of 9 messages, opened by **konrad** |
| 2 | 2025-01-22 | 15:31–15:42 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **dermot** |
| 3 | 2025-01-31 | 18:07–18:21 | Mattermost `#engineering` — an exchange of 7 messages, opened by **emil** |
| 4 | 2025-02-13 | 13:38–13:46 | Mattermost `#general` — an exchange of 7 messages, opened by **gideon** |
| 5 | 2025-03-14 | 12:48–12:59 | Mattermost `#code-review` — an exchange of 7 messages, opened by **dario** |
| 6 | 2025-03-14 | 13:06–13:15 | Mattermost `#engineering` — an exchange of 8 messages, opened by **dario** |
| 7 | 2025-03-14 | 13:41–13:52 | Mattermost `#code-review` — an exchange of 8 messages, opened by **gideon** |
| 8 | 2025-03-17 | 14:02–14:12 | Mattermost `#code-review` — an exchange of 7 messages, opened by **nikolai** |
| 9 | 2025-03-17 | 14:02–14:17 | Mattermost `#engineering` — an exchange of 7 messages, opened by **gideon** |
| 10 | 2025-03-18 | 14:02–14:12 | Mattermost `#code-review` — an exchange of 7 messages, opened by **gideon** |
| 11 | 2025-03-19 | 13:38–13:48 | Mattermost `#engineering` — an exchange of 7 messages, opened by **gideon** |
| 12 | 2025-03-19 | 14:02–14:12 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **petar** |
| 13 | 2025-03-19 | 14:02–14:12 | Mattermost `#code-review` — an exchange of 8 messages, opened by **nikolai** |
| 14 | 2025-03-20 | 13:31–13:44 | Mattermost `#cookbooks` — an exchange of 8 messages, opened by **dermot** |
| 15 | 2025-03-20 | 15:31–15:46 | Mattermost `#code-review` — an exchange of 8 messages, opened by **konrad** |
| 16 | 2025-03-20 | 16:02–16:16 | Mattermost `#engineering` — an exchange of 9 messages, opened by **dermot** |
| 17 | 2025-03-21 | 13:11–13:24 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **dario** |
| 18 | 2025-03-24 | 14:02–14:14 | Mattermost `#engineering` — an exchange of 8 messages, opened by **gideon** |
| 19 | 2025-03-24 | 15:06–15:18 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **nikolai** |
| 20 | 2025-03-31 | 15:38–15:49 | Mattermost `#releases` — an exchange of 8 messages, opened by **konrad** |
| 21 | 2025-04-03 | 14:02–14:11 | Mattermost `#viewer` — an exchange of 8 messages, opened by **konrad** |
| 22 | 2025-04-07 | 14:02–14:13 | Mattermost `#general` — an exchange of 8 messages, opened by **konrad** |
| 23 | 2025-04-09 | 13:21–13:31 | Mattermost `#incidents` — an exchange of 8 messages, opened by **emil** |
| 24 | 2025-04-10 | 13:12–13:26 | Mattermost `#viewer` — an exchange of 7 messages, opened by **konrad** |
| 25 | 2025-04-11 | 13:38–13:50 | Mattermost `#releases` — an exchange of 8 messages, opened by **nikolai** |
| 26 | 2025-04-11 | 13:41–13:51 | Mattermost `#incidents` — an exchange of 8 messages, opened by **gideon** |
| 27 | 2025-04-14 | 14:11–14:20 | Mattermost `#viewer` — an exchange of 7 messages, opened by **dermot** |
| 28 | 2025-04-15 | 15:47–16:00 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **dermot** |
| 29 | 2025-04-16 | 14:02–14:14 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **theo** |
| 30 | 2025-04-17 | 14:11–14:20 | Mattermost `#random` — an exchange of 8 messages, opened by **nikolai** |
| 31 | 2025-04-18 | 15:31–15:42 | Mattermost `#incidents` — an exchange of 9 messages, opened by **dermot** |
| 32 | 2025-04-21 | 14:04–14:15 | Mattermost `#general` — an exchange of 8 messages, opened by **gideon** |
| 33 | 2025-04-21 | 15:22–15:35 | Mattermost `#help` — an exchange of 7 messages, opened by **petar** |
| 34 | 2025-04-23 | 10:18–10:37 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **nils** |
| 35 | 2025-04-23 | 17:15–17:44 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **nils** |
| 36 | 2025-04-24 | 14:02–14:11 | Mattermost `#pipeline` — an exchange of 8 messages, opened by **emil** |
| 37 | 2025-04-24 | 14:21–14:31 | Mattermost `#viewer` — an exchange of 7 messages, opened by **konrad** |
| 38 | 2025-04-25 | 13:41–13:50 | Mattermost `#viewer` — an exchange of 7 messages, opened by **konrad** |
| 39 | 2025-04-25 | 14:07–14:19 | Mattermost `#random` — an exchange of 8 messages, opened by **dermot** |
| 40 | 2025-04-29 | 14:31–14:41 | Mattermost `#general` — an exchange of 9 messages, opened by **dermot** |
| 41 | 2025-04-29 | 14:47–15:01 | Mattermost `#pipeline` — an exchange of 6 messages, opened by **dermot** |
| 42 | 2025-05-02 | 15:56–16:06 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **dario** |
| 43 | 2025-05-05 | 14:02–14:15 | Mattermost `#cookbooks` — an exchange of 7 messages, opened by **konrad** |
| 44 | 2025-05-06 | 09:52–10:03 | Mattermost `#code-review` — an exchange of 8 messages, opened by **gideon** |
| 45 | 2025-05-06 | 14:07–14:16 | Mattermost `#incidents` — an exchange of 8 messages, opened by **dermot** |
| 46 | 2025-05-06 | 15:02–15:14 | Mattermost `#releases` — an exchange of 7 messages, opened by **konrad** |
| 47 | 2025-05-13 | 10:14–10:35 | Mattermost `#pipeline` — an exchange of 5 messages, opened by **emil** |
| 48 | 2025-05-13 | 15:22–15:31 | Mattermost `#pipeline` — an exchange of 7 messages, opened by **gideon** |
| 49 | 2025-05-30 | 13:52–14:07 | Mattermost `#releases` — an exchange of 8 messages, opened by **konrad** |
| 50 | 2025-06-02 | 11:02–11:18 | Mattermost `#general` — an exchange of 8 messages, opened by **dermot** |
| 51 | 2025-06-16 | 14:12–14:28 | Mattermost `#pipeline` — an exchange of 9 messages, opened by **gideon** |

A row gives the window an exchange runs in and how many messages it is — not how much is around it. A busy channel interleaves other talk with it, and a mail thread can have begun earlier and under someone else's name, so read the window and its surroundings rather than counting messages off.

A wiki **comment** is not in the page body and BookStack's search does not index it; `/api/pages/{id}` returns a page's `comments` alongside its text.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
