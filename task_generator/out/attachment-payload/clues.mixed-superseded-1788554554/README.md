# Clues for g8 — Canonical attachment blocks for multimodal prompts

43 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/runs/corpus`.

Clue window `2025-03-14` to `2026-01-27`; herrings before `2025-03-13`.

**Nothing here has been inserted into the corpus.** This is the plan: what each person says, where it goes, and why it belongs there.

## The task the agent is given

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

## Every remark, in the order a reader would meet them

| date | where | who | says | carries |
|---|---|---|---|---|
| 2025-01-21 | #code-review *(new)* | dario | one ceiling for both, 20 mb whether it's an image or a document - the size check in _canonical_attachment_block doesn't branch on block.kind at all. | *herring* |
| 2025-01-22 | #code-review *(new)* | emil | ordering is settled then: file_upload_limit_check runs first, our 20 MB ceiling only gets a say after the provider has already had the payload. | *herring* |
| 2025-02-03 | #pipeline | dario | one more from the 427 review while you're in there: detail goes to the provider exactly as the caller wrote it, no lowercasing, no checking it against a list | *herring* |
| 2025-02-12 | #engineering | konrad | Look, one that's settled: detail is pass-through, whatever string the caller sets is what lands in the request. Validating that vocabulary is the providers job, not ours. | *herring* |
| 2025-03-14 | #code-review *(new)* | emil | let me think through that - each block already carries size_mb off its encoded text, so the whole-prompt number is just summing size_mb, no re-reading anything. | `scope`, `rule` |
| 2025-03-14 | #engineering *(new)* | dario | one ceiling for both kinds was bouncing 22 meg pdfs anthropic takes happily, so `_canonical_attachment_block` branches on `block.kind` now: 20.0 image, 24.0 document, `AttachmentTooLarge` either way | `rule` |
| 2025-03-14 | #code-review | emil | same on 579 - dropped the ordering where file_upload_limit_check ran first, we kept handing it payloads we already knew were oversized. AttachmentTooLarge fires inside _canonical_attachment_block now, before the provider hook. | `rule` |
| 2025-03-17 | #pipeline *(new)* | gideon | so basically I spent a minute base64ing a 31 MB png and the provider bounced it in two lines, nothing on our side looked at the size first | `rule` |
| 2025-03-17 | #code-review *(new)* | nikolai | its `_ATTACHMENT_COUNT_LIMIT` in attachment.py not ATTACHMENT_MAX and we count the list before anythign gets read off disk or handed to the upload hook | `failure_behavior` |
| 2025-03-17 | #engineering *(new)* | konrad | review nit: you added `_ATTACHMENT_FINGERPRINT_HEX_LEN` but `attachment_fingerprint` still slices `12` off the hex by hand in two places. 12 is right, just use the constant in both. | `rule` |
| 2025-03-18 | #code-review *(new)* | nils | tried it with fourteen images and got `Prompt has 14 attachments, over the limit of 12.` — my forty text chunks didn't count toward it, which is right. | `failure_behavior` |
| 2025-03-19 | #pipeline *(new)* | dermot | the per-attachment path only ever sees one file, so the total gets summed in the multimodal handler once all the file_upload_limit_check calls have run | `scope` |
| 2025-03-19 | #engineering *(new)* | emil | my dedupe run yesterday - remote blocks came back with an empty `fingerprint`, inline ones had theirs, so every cdn image counted as new. url-sourced has to be covered too. | `exclusions_or_crossover` |
| 2025-03-19 | #releases *(new)* | dario | scratch what i said about detail passing straight through — a typo'd "hgih" 400'd a run mid-flight, so normalize_detail lowercases against _SUPPORTED_IMAGE_DETAILS and falls back to "auto" with one warning | `failure_behavior` |
| 2025-03-20 | #engineering *(new)* | dario | i think normalize_detail should trim and lowercase before it compares — whatever the caller typed stays on the image itself, we only fix the copy that goes on the block. | `failure_behavior` |
| 2025-03-20 | #cookbooks *(new)* | konrad | I said detail validation was the provider's job — not since the "hgih" 400. normalize_detail checks _SUPPORTED_IMAGE_DETAILS at block-build time, anything else lands as "auto" with one warning, Image.detail keeps the caller's string. | `failure_behavior`, `rule` |
| 2025-03-24 | #engineering *(new)* | gideon | so basically if someone puts junk in there we shouldnt kill the run, just fall back to auto and warn once. unset is auto too, silently, no log line. | `failure_behavior` |
| 2025-03-25 | #engineering | dermot | back on the fingerprint: for the inline ones we hash the b64 text we already hold, decoding a 40mb pdf back to bytes just to digest it is daft | `exclusions_or_crossover` |
| 2025-03-26 | #pipeline *(new)* | nils | my first pass sized the remote ones with a HEAD and the tests immediately started going out to the network. i'm not doing that in a formatter. | `exclusions_or_crossover` |
| 2025-03-27 | #viewer *(new)* | gideon | so basically we cap the name we derive at 64 but keep the extension on the end, a .pdf that loses its tail is useless in the viewer | `scope` |
| 2025-04-02 | thread:new|g8.r1.g8r1-l19 *(new)* | dermot | the document price sits next to the image table as `_OPENAI_TOKENS_PER_DOCUMENT`, and the anthropic-shaped document blocks take the same number as the openai file ones. | `observability` |
| 2025-04-02 | thread:new|g8.r2.g8r2-s3-l4 *(new)* | dermot | anything at or under `_MAX_ATTACHMENT_FILENAME_LEN` goes through exactly as it came in, no rewriting at all. people grep the logs for those names. | `scope` |
| 2025-04-14 | thread:<178769930038.2250839.2605881431154859866@world.local> | emil | on your cost question — last night's pdf run came out at about the text length. document and file blocks are priced at zero in the input estimate, which isn't right. | `observability` |
| 2025-04-22 | page:engineering/block-identity-and-cache-keys-for-strategy-recipes.md *(new)* | nils | i think `fingerprint` has to be required on the block, filled from the payload we already built there. optional is a field half the providers forget to set. | `rule` |
| 2025-04-24 | #pipeline *(new)* | gideon | so basically a 30 MB image sitting on a cdn is fine, they fetch it themselves - the ceiling only bites what we actually encode into the payload. | `exclusions_or_crossover`, `rule` |
| 2025-04-28 | thread:<178770450521.2334287.16901596979904917532@world.local> | dario | left it on 651: we hand a payload we already know is oversized to file_upload_limit_check. AttachmentTooLarge should have fired in the block builder, before that hook. | `rule` |
| 2025-04-29 | #pipeline *(new)* | dermot | anthropic takes a 22 meg pdf without blinking, an image that size comes straight back. one ceiling for both kinds is going to be wrong. | `rule` |
| 2025-05-02 | #pipeline | gideon | honestly though, I'm diffing two 200-line base64 blobs in the log just to tell if it's the same picture agian. want a short handle sitting on the block itself. | `rule` |
| 2025-05-06 | thread:new|g8.r1.g8r1-l13 *(new)* | konrad | Look, a cookbook user handed us a folder of 200 pngs — we base64'd every single one of them and then the API refused the request anyway. | `failure_behavior` |
| 2025-05-13 | page:engineering/attachment-limits-for-multimodal-requests-and-where-we-check-them.md *(new)* | emil | ok, 20 for images and 24 for documents then. and something landing exactly on the number should still go out, not get refused. | `rule` |
| 2025-05-13 | thread:new|g8.r2.g8r2-s4-l1 *(new)* | konrad | Look, the cookbook page still has detail="HIGH" on it and that went straight into the block as HIGH, untouched. two people copied that page this week. | `failure_behavior` |
| 2025-05-27 | page:engineering/ws-055-release-engineering-ci-test-suite.md | konrad | On the fingerprint rule: for url blocks we are going with A from the review thread, we hash the string we put in the payload, nobody fetches it. | `exclusions_or_crossover` |
| 2025-05-29 | page:engineering/viewer-download-row-long-dataset-names-in-the-summary-table.md *(new)* | nils | only shorten the name we display, not the url. i trimmed the link along with it once and the download 404'd, whole query string gone. | `scope` |
| 2025-06-10 | page:engineering/estimating-request-payload-size-before-chunking-a-batch-file.md *(new)* | konrad | look, call a document 1400 and move on. its an estimate not a bill. | `observability` |
| 2025-06-11 | page:engineering/attachment-payloads-where-they-get-assembled-and-which-limit-is-actually-checked.md *(new)* | gideon | so basically five pdfs, every one under its own ceiling, and the request still came back too large. about 60 across the lot, so per-attachment limits alone dont catch it. | `scope` |
| 2025-06-11 | thread:new|g8.r2.g8r2-s2-l3 *(new)* | dario | on the url ones i think we hash it as given, query and fragment included — `?size=large` and `?size=small` are different pictures, two rows beats one wrong one. | `exclusions_or_crossover` |
| 2025-06-12 | page:engineering/attachment-payload-filenames-we-send-to-providers.md *(new)* | nikolai | basename on the q4 statements pdf comes out at 73 chars and it blew out the providers filename field  not sending that through as it is | `scope` |
| 2025-06-17 | page:engineering/attachment-blocks-in-multimodal-requests-gemini-batch.md *(new)* | konrad | look, for a link we never hold the bytes on our side, so size_mb just stays empty on those blocks. | `exclusions_or_crossover`, `rule` |
| 2025-06-17 | thread:new|g8.r2.g8r2-s1-l4 *(new)* | dario | i pinned it in a scratch test: the `%PDF-1.4` fixture comes out sha256:fc1c4358d4aa and `Image(content=b"x")` sha256:5e21d86b709b, same every run. | `rule` |
| 2025-06-18 | thread:new|g8.r1.g8r1-l7 *(new)* | nikolai | also the running total shouldnt pick up linked attachements otherwise a prompt of ten cdn urls fails over bytes we never sent | `exclusions_or_crossover`, `scope` |
| 2025-06-19 | page:engineering/gemini-batch-attachments-the-two-size-ceilings-and-what-they-raise.md *(new)* | nikolai | mine came back prompt attachment is 51.2 MB over the 45.0 MB limit same exeption as the per file one kind just says prompt | `scope` |
| 2025-06-24 | page:engineering/attachment-limits-on-multimodal-requests.md *(new)* | dario | mhm, that tracks. and TooManyAttachments sits under the same base as the other attachment errors, callers catch the one thing. | `failure_behavior` |
| 2026-01-23 | page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md | nikolai | adding a wiki bullet for attachment.py while 690 is still moving the mime helper the fallback filename and now `_SUPPORTED_IMAGE_DETAILS` = auto / low / high thats the accepted set | `failure_behavior` |

## g8.r1

**The hidden requirement:**

- **rule** — Each base64 payload is measured in megabytes from its base64 length and recorded on the block as a `size_mb: float` field; a measurement strictly greater than 20.0 MB for a block whose kind is "image", or strictly greater than 24.0 MB for a block whose kind is "document", raises `AttachmentTooLarge(kind, size_mb, limit_mb)` — an `AttachmentError` subclass storing `.kind`, `.size_mb` and `.limit_mb`, message `f"{kind} attachment is {size_mb} MB, over the {limit_mb} MB limit."`. The measurement and the comparison happen inside `_canonical_attachment_block`, before the payload is offered to the provider's `file_upload_limit_check` hook.
- **scope** — A whole-prompt ceiling of 45.0 MB belongs to `_handle_multi_modal_prompt`: after every attachment has been converted to a block (all `file_upload_limit_check` calls have already run), the `size_mb` values of the `source == "base64"` blocks are summed and compared, strictly greater, against 45.0; on overflow the same exception type is raised with `kind == "prompt"`, `size_mb` equal to the whole-prompt sum and `limit_mb == 45.0`. `_canonical_attachment_block` / `_format_multimodal` never apply it.
- **exclusions_or_crossover** — A `source == "url"` block is never measured: its `size_mb` is `None`, it is not compared against any per-kind ceiling, and it contributes nothing to the 45.0 MB prompt sum.
- **failure_behavior** — More than 12 attachments is refused: `_ATTACHMENT_COUNT_LIMIT: int = 12` and `TooManyAttachments(AttachmentError)` with `__init__(self, count: int, limit: int)` storing `.count` and `.limit`, message `f"Prompt has {count} attachments, over the limit of {limit}."`. `_handle_multi_modal_prompt` counts `len(message.attachments())` first and raises when the count is strictly greater than 12; nothing is serialized and `file_upload_limit_check` is not called. 40 texts and one image is fine, and 12 attachments is fine.
- **observability** — In `calculate_input_tokens`, a `"file"` or `"document"` block costs 1400 tokens (`_OPENAI_TOKENS_PER_DOCUMENT = 1400`): with a 1-token-per-character encoder, `[text "hello", image_url, anthropic image, file, document, unknown "thinking"]` totals `5 + 85 + 85 + 1400 + 1400 + 0 == 2975`.

**Reversed earlier:** The first version used a single 20 MB ceiling for every kind and ran the provider's own `file_upload_limit_check` first; it was reversed after 22 MB PDFs that Anthropic accepts were rejected by the shared check, and the ordering was flipped so the shared ceiling speaks before the provider hook.

**What a reader has to infer along the way:**

- *Every attachment we encode ourselves carries its own measured size, taken in megabytes from the encoded text and kept on the block, and the block builder refuses it above 20 for images and 24 for documents with a dedicated attachment error naming the kind, the measured size and the ceiling it broke, before the provider's own upload hook is consulted.*
  - nobody says: a check that already knows the payload is too big should speak before one that has to go and ask
- *An attachment sent as a link is never measured: no size is recorded on its block, no per-kind ceiling is applied to it, and it adds nothing to any whole-prompt total.*
  - nobody says: you can only weigh bytes you are actually holding, and a link means somebody else is holding them
- *The measured sizes across a whole prompt are added up in the multimodal handler once every block has been built, and a total above 45.0 raises the same error type with its kind reading prompt; the single-attachment path never applies this.*
  - nobody says: limits on each file separately say nothing about the size of the one request they all go into
- *A prompt carrying more than twelve attachments is refused by its own error type against a named module constant, counted before anything is encoded or sent to the provider hook, with text entries excluded from the count.*
  - nobody says: if a request is doomed on the count alone there is no reason to spend minutes encoding it first
- *File and document blocks are priced at a flat 1400 tokens in the input token estimate, under a named constant, for both the openai and anthropic block shapes.*
  - nobody says: an attachment the model actually reads costs tokens, so estimating it at nothing makes the whole estimate useless

**Names the tests reach for that the ticket withholds:**

- said: `AttachmentTooLarge`, `MB`, `Prompt`, `TooManyAttachments`, `_ATTACHMENT_COUNT_LIMIT`, `_OPENAI_TOKENS_PER_DOCUMENT`, `calls`, `count`, `limit`, `size_mb`

> **Spread:** g8.r1.g8r1-s4: two remarks in #code-review within 1 days

### The remarks, by the step they build

### g8.r1.g8r1-s1 — Every attachment we encode ourselves carries its own measured size, taken in megabytes from the encoded text and kept on the block, and the block builder refuses it above 20 for images and 24 for documents with a dedicated attachment error naming the kind, the measured size and the ceiling it broke, before the provider's own upload hook is consulted.

*Nobody says:* a check that already knows the payload is too big should speak before one that has to go and ask

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g8.r1.g8r1-l1` — rule

**gideon**, 2025-03-17, #pipeline

> so basically I spent a minute base64ing a 31 MB png and the provider bounced it in two lines, nothing on our side looked at the size first

*What a reader should take from it:* the team agrees an oversized encoded payload is going out unchecked today and costing time before the provider refuses it

*Step it builds toward:* `g8.r1.g8r1-s1` — Every attachment we encode ourselves carries its own measured size, taken in megabytes from the encoded text and kept on the block, and the block builder refuses it above 20 for images and 24 for documents with a dedicated attachment error naming the kind, the measured size and the ceiling it broke, before the provider's own upload hook is consulted.

*Drafted as:* Spent a minute base64ing a 31 MB png and the provider bounced it in two lines. Nothing on our side looked at the size first.

*Why there:* None of the listed conversations is chewing on request payload validation. The closest by vocabulary is #code-review 2025-04-29, where Emil has PR 651 up as a "multimodal model update" — but that whole day is people failing to find reviewers, and a field report about an oversized base64 image would arrive as a new subject with nothing to attach to, and it isn't feedback on the PR either. #pipeline 2025-04-07 is the resume/cost-accounting thread and has nothing to do with what we send outbound. Subject-wise this is squarely the request layer: what goes out to a provider backend and what we check before it does, which is #pipeline's stated purpose. It wants a thread the day after the multimodal work is in review, where gideon reports the bounce and Emil/Dario supply the ceilings and where the check sits.

*Still leaves open:* what the ceilings are, what we raise instead, and where in the path the check sits

*Must appear literally:* `MB`

*A new conversation in #pipeline on 2025-03-17:*

```
```

#### `g8.r1.g8r1-l4` — rule

**dario**, 2025-04-28, thread:<178770450521.2334287.16901596979904917532@world.local>

> left it on 651: we hand a payload we already know is oversized to file_upload_limit_check. AttachmentTooLarge should have fired in the block builder, before that hook.

*What a reader should take from it:* the team agrees our own refusal fires inside the block builder ahead of the provider upload hook

*Step it builds toward:* `g8.r1.g8r1-s1` — Every attachment we encode ourselves carries its own measured size, taken in megabytes from the encoded text and kept on the block, and the block builder refuses it above 20 for images and 24 for documents with a dedicated attachment error naming the kind, the measured size and the ceiling it broke, before the provider's own upload hook is consulted.

*Drafted as:* left it on the pr: we hand a payload we already know is oversized to file_upload_limit_check. AttachmentTooLarge should have gone off before we got there.

*Why there:* Emil's Apr 28 weekly update lists "PR 651: multimodal support models update for openai, ready for review" and closes with "Nothing blocking on my end for the three ready PRs" — dario, who is on the thread, is exactly the person to reply that he did in fact leave something on 651, which is the attachment/payload path. It complicates a live claim in the thread rather than arriving from nowhere, and it stays off the numbers, the measurement and the error payload.

*Still leaves open:* the numbers themselves, how the size was measured, and what the error carries

*Must appear literally:* `AttachmentTooLarge`

*Goes as a reply into the real thread "Weekly update: week of Apr 21":*

```
Week of Apr 21 - quick rundown on where things stand from my end.

In progress:
- PR 468: n samples in generation params, ready for review
- PR 643: response object in curator, ready for review
- PR 651: multimodal support models update for openai, ready for review
- PR 652: download dataset from viewer, still has some work left before it's ready

Open:
- Trying to get a clearer picture of the serving infra scope and which services it actually touches. Haven't fully resolved that yet. If anyone has context, would appreciate it.

Nothing blocking on my end for the three ready PRs. Will work through the queue with Gideon this afternoon.
```

#### `g8.r1.g8r1-l2` — rule

**dermot**, 2025-04-29, #pipeline

> anthropic takes a 22 meg pdf without blinking, an image that size comes straight back. one ceiling for both kinds is going to be wrong.

*What a reader should take from it:* the team agrees images and documents cannot share the same ceiling

*Step it builds toward:* `g8.r1.g8r1-s1` — Every attachment we encode ourselves carries its own measured size, taken in megabytes from the encoded text and kept on the block, and the block builder refuses it above 20 for images and 24 for documents with a dedicated attachment error naming the kind, the measured size and the ceiling it broke, before the provider's own upload hook is consulted.

*Drafted as:* anthropic takes a 22 meg pdf without blinking; an image that size comes straight back. one number for both kinds is going to be wrong.

*Why there:* No candidate room is chewing on attachment payload sizes. The nearest by vocabulary, chat|pipeline|2025-04-23, only mentions multimodal-prompts in dermot's 09:00 standup line ("holding, nothing urgent there") and then spends the whole day on the cache fingerprint omitting model and the job record omitting it too — a size-ceiling remark there arrives from nowhere and gets no reaction. The 05-01 and 04-04 engineering threads are executor image defaults and llama4/KlusterAI scope. What's missing is a #pipeline thread on where we validate attachment size in the request layer: someone hits a rejected image while same-size PDFs go through, and dermot — who owns the provider side of bulk-llm-inference and keeps flagging multimodal-prompts — is the one who'd say the single constant can't cover both kinds. That leaves the two numbers, how size is measured, and which one gets raised still open for the sibling.

*Still leaves open:* which two numbers, how the size is arrived at, and what gets raised

*A new conversation in #pipeline on 2025-04-29:*

```
```

#### `g8.r1.g8r1-l3` — rule

**emil**, 2025-05-13, page:engineering/attachment-limits-for-multimodal-requests-and-where-we-check-them.md

> ok, 20 for images and 24 for documents then. and something landing exactly on the number should still go out, not get refused.

*What a reader should take from it:* the team agrees on the two per-kind ceilings and that the boundary value passes

*Step it builds toward:* `g8.r1.g8r1-s1` — Every attachment we encode ourselves carries its own measured size, taken in megabytes from the encoded text and kept on the block, and the block builder refuses it above 20 for images and 24 for documents with a dedicated attachment error naming the kind, the measured size and the ceiling it broke, before the provider's own upload hook is consulted.

*Drafted as:* 20 for images and 24 for documents then. Something landing exactly on the number should still go out.

*Why there:* Nothing in the listed set is about attachment payloads. The Docker page's "image" is a container image, not an image attachment, and a comment there setting a count of 20 images / 24 documents would read as a different conversation spliced in; the release notes, the three weekly notes pages and the structured-output and handover pages are about PR flow, release gating, response_format and cost/cache metadata respectively, and none of them has a live thread about how many of each attachment kind we let through. The right home is #pipeline, which owns what we actually put in a provider request: a short design page on per-kind attachment caps for multimodal requests, opened after the multimodal work (PR 651) surfaced runs failing on oversized payloads, with emil, dario and nikolai working through per-kind ceilings, what the count is measured from, what the refusal looks like, and whether URL-style attachments count at all. emil's line is the comment that settles the two numbers and the boundary case, leaving the rest to the page and the other commenters.

*Still leaves open:* what the units are measured from, what error the refusal is, and whether links are in scope at all

*A new page — **Attachment Limits for Multimodal Requests, and Where We Check Them** in `engineering`, 2025-05-13:*

> **Why This Page Exists**

> Since the PR 651 work landed, requests that attach more than a handful of images or documents have been coming back from the provider with errors that are, honestly, not very helpful. The message we get back is generic and does not name the attachment count as the cause, so the first two people who hit it went looking at the prompt template and at the encoder before anyone thought to count what was actually being attached.
> 
> So this is the write up of what we cap, what the numbers are, and where in the call path the check happens. Not a proposal, just what is being implemented on the multimodal-prompts branch this week so that people stop debugging the wrong layer.

> **Where the Check Lives**

> The validation runs client side, in the prompt formatter, **before** the request is built and sent. Not in the provider adapter, and not as a retry-on-error path.
> 
> Reasoning, briefly:
> 
> - a caller who attaches too much has almost always made a mistake in how they assembled the batch, and they want to hear about it immediately, not after a round trip
> - retrying on a generic provider error means guessing at the cause, and we would be guessing wrong a lot of the time
> - in batch mode a late failure costs us the whole submitted file, which is the expensive version of this mistake
> 
> The tradeoff we are accepting is that our numbers can drift from the provider's if they change theirs.

> **The Limits**

> 20 for images and 24 for documents, per request. The two are counted separately, so a request carrying 20 images and 24 documents is fine and does not need to trade one against the other.
> 
> Both bounds are inclusive. Something landing exactly on the number should still go out, so a request with exactly 20 images passes and a request with exactly 24 documents passes; only 21 and 25 respectively are rejected. Worth stating plainly because the first draft of the check used a strict comparison and rejected the exact-limit case, which is the kind of off by one that is easy to write and annoying to notice.
> 
> These are what the provider documents today. i am not entirely sure they are the sam

> **What the Caller Sees**

> A validation error raised at format time, naming the kind (image or document), the count that was supplied, and the limit. No truncation, no silent dropping of the tail of the list.
> 
> Dropping attachments quietly was discussed and rejected. we have been bitten by the silent-failure pattern recently enough (see the structured output revert notes from last week) that nobody wanted a second flavour of it. If the caller attached 30 images they meant to send 30 images, and the right answer is to tell them we cannot.

> **Not Covered Here**

> - **total payload size in bytes.** the attachment count is not the only thing the provider bounds, and a small number of very large images can still fail. that check is separate and is not part of this change.
> - **per attachment dimension or page limits.** same story, handled elsewhere or not at all yet.
> - **whether the numbers should be configurable per provider.** i believe they will need to be eventually, but hardcoding first and generalising once we have a second set of real numbers seems like the right order. worth revisiting when local-offline-inference needs its own values.

### g8.r1.g8r1-s2 — An attachment sent as a link is never measured: no size is recorded on its block, no per-kind ceiling is applied to it, and it adds nothing to any whole-prompt total.

*Nobody says:* you can only weigh bytes you are actually holding, and a link means somebody else is holding them

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g8.r1.g8r1-l5` — exclusions_or_crossover

**nils**, 2025-03-26, #pipeline

> my first pass sized the remote ones with a HEAD and the tests immediately started going out to the network. i'm not doing that in a formatter.

*What a reader should take from it:* the team agrees measuring a linked attachment would mean fetching it, which this path will not do

*Step it builds toward:* `g8.r1.g8r1-s2` — An attachment sent as a link is never measured: no size is recorded on its block, no per-kind ceiling is applied to it, and it adds nothing to any whole-prompt total.

*Drafted as:* my first pass sized the remote ones with a HEAD and the tests went out to the network. not doing that in a formatter.

*Why there:* Both candidate days are about provider test coverage for the Mistral batch processor (PR 584) and the cost-lookup VCR cassette. The 03-25 thread shares vocabulary — "nothing hitting a real endpoint" — but that phrase is about which fixture tests can be dropped from provider-integrations, not about attachment sizing; dropping a HEAD-request/formatter remark there changes the subject mid-review and answers nothing anyone asked. 03-21 is two people on cost lookup and has even less room for it. The remark needs a thread where someone is actually building the attachment payload formatter and hit the question of how to record size for a linked (remote) attachment versus an inline one — that's the request layer, #pipeline, where payload shaping and provider backends live.

*Still leaves open:* what is recorded for a link instead, and whether links count anywhere else

*A new conversation in #pipeline on 2025-03-26:*

```
```

#### `g8.r1.g8r1-l8` — exclusions_or_crossover, rule

**gideon**, 2025-04-24, #pipeline

> so basically a 30 MB image sitting on a cdn is fine, they fetch it themselves - the ceiling only bites what we actually encode into the payload.

*What a reader should take from it:* the team agrees a linked image is not weighed against the per-kind ceiling

*Step it builds toward:* `g8.r1.g8r1-s2` — An attachment sent as a link is never measured: no size is recorded on its block, no per-kind ceiling is applied to it, and it adds nothing to any whole-prompt total.

*Drafted as:* A 30 MB image sitting on a cdn is fine, they fetch it themselves; the ceiling only bites what we encode.

*Why there:* None of the eight candidates is anywhere near this subject. They're about schema_check/capability blocking (3/14, 3/26), PR triage and reviewer assignment (4/10, 4/4), cost-streaming skew and throttling (4/16), cache-vs-model-swap silence (3/18), stdout scope and structured output override (4/29), and Anthropic token counts (4/22). Not one of them is chewing on multimodal attachment payloads, per-kind size ceilings, or what counts as encoded bytes on a request block — the remark would arrive from nowhere and change the subject in every one of them. The right home is #pipeline, which owns the request layer and payload/token accounting: a thread where someone building attachment support asks whether a URL-referenced image is charged against the per-kind MB ceiling. Gideon is a natural person to settle that half of it (he opens most pipeline threads and takes positions on scope), and the sibling question — what a link contributes to the block and to any running total — stays open for someone else in the same thread.

*Still leaves open:* what value a link carries on the block and how it behaves in any total

*Must appear literally:* `MB`

*A new conversation in #pipeline on 2025-04-24:*

```
```

#### `g8.r1.g8r1-l6` — exclusions_or_crossover, rule

**konrad**, 2025-06-17, page:engineering/attachment-blocks-in-multimodal-requests-gemini-batch.md

> look, for a link we never hold the bytes on our side, so size_mb just stays empty on those blocks.

*What a reader should take from it:* the team agrees a link-sourced block records no size

*Step it builds toward:* `g8.r1.g8r1-s2` — An attachment sent as a link is never measured: no size is recorded on its block, no per-kind ceiling is applied to it, and it adds nothing to any whole-prompt total.

*Drafted as:* For a link we never hold the bytes, so size_mb just stays empty on those blocks.

*Why there:* Every listed candidate is either a release note, a meeting roundup of PR/issue numbers, or the Docker executor pinning page — none of them is chewing on attachment payloads at all. The nearest thread is PR 690 (multimodal Gemini batch request creation), but it appears in the Jun 16 and Jun 23 notes only as a line item waiting for a reviewer; a comment there about how a link-sourced block records no size_mb would be answering a question that page never asks, and meeting-notes comments in this wiki stay at the level of ownership and scheduling. The remark is a settled design point about how we build request payloads — inline bytes vs a link — which is squarely the request layer, so it wants a #pipeline page written while PR 690 is actually open: Konrad and Emil (who owns 690) working through what an attachment block carries, with Dario in on the accounting side, since the sibling question of whether an empty size_mb still counts toward a ceiling or a run total is exactly the kind of thing that page would leave open for a comment thread.

*Still leaves open:* whether an empty one is still weighed against a ceiling or added to any total

*Must appear literally:* `size_mb`

*A new page — **Attachment blocks in multimodal requests (Gemini batch)** in `engineering`, 2025-06-17:*

> **Why this note**

> PR 690 (Fix Multimodal Gemini Batch Request Creation) is open and waiting for review. While building the request I had to look closely at how an attachment is represented before it is written into the batch payload, and the answer was not written down anywhere.
> 
> So, writing it down. Nothing here is new behaviour, it is the shape that already exists in the code, just described.
> 
> We are at v0.1.25 and v0.1.26 is the next cut. Better this exists before then, than after.

> **The two shapes of an attachment block** **← carries the remark**

> An attachment block is one of two things, and the difference matters because the two do not travel through the same path.
> 
> - **inline** - we hold the bytes. Either the caller passed them to us directly, or we read them from a local file at request build time.
> - **link** - we hold only a URI. The bytes stay wherever they are, the provider is the one that fetches them (or does not).
> 
> Common to both: `mime_type`, and the block's position in the message. Those are always present, and both paths depend on them.
> 
> The field that is not common is `size_mb`. For a link we never hold the bytes, so `size_mb` just stays empty on those blocks. Anything downstream that reads it has to tolera

> **What the batch writer does with each**

> For inline: bytes get base64 encoded and go out as inline data on the part, together with the mime type.
> 
> For link: the URI goes out as a file reference and the provider resolves it. Nothing of ours is uploaded.
> 
> One consequence, which is the thing that actually bit me in 690 - the payload size we can compute locally is only the inline part. A request with ten link blocks is small for us and possibly very large for the provider. Our own size accounting is therefore a lower bound, not the real number.

> **If you are touching this code**

> Short list, from the review of 690.
> 
> - Do not assume a block has bytes. Check the shape first, then read.
> - Keep the block order. The parts array is ordered and the model sees the order, mixing text and attachment out of sequence changes the prompt.
> - Empty attachment list is legal. A multimodal-capable request with only text must still build.
> - Mime type should be passed through unchanged. We had a case where it was being normalised to lowercase somewhere, maybe harmless, but it is not our business to rewrite it.

> **Not settled**

> Anyway, two things I did not resolve and did not want to resolve inside 690.
> 
> - Do we validate that a link is reachable at request build time? Right now we do not. It would catch typos early but it also means network calls during what is currently a pure build step. Not entirely sure that trade is worth it.
> - What happens when the same attachment appears twice in one request - do we deduplicate? Off the top of my head the answer today is no, it goes out twice.
> 
> Both can wait until after v0.1.26.

#### `g8.r1.g8r1-l7` — exclusions_or_crossover, scope

**nikolai**, 2025-06-18, thread:new|g8.r1.g8r1-l7

> also the running total shouldnt pick up linked attachements otherwise a prompt of ten cdn urls fails over bytes we never sent

*What a reader should take from it:* the team agrees linked attachments contribute nothing to the whole-prompt total

*Step it builds toward:* `g8.r1.g8r1-s2` — An attachment sent as a link is never measured: no size is recorded on its block, no per-kind ceiling is applied to it, and it adds nothing to any whole-prompt total.

*Drafted as:* Also the running total shouldn't pick links up, otherwise a prompt of ten cdn urls fails over bytes we never sent.

*Why there:* Neither mail is in a room where this could be said. The Docker image-pinning thread (2025-04-16) is about backend_params={'image': ...} and container creation — nothing about prompt payload, byte accounting, or attachments, so the remark would change the subject and get no reply. The Jun 16 recap does touch multimodal Gemini batch request creation, but it is nikolai's own weekly status mail — a recap of what happened, PR 690/691 review load and whether PR 653 should be closed. A design ruling on what the running payload total counts is not a recap item, and it would be nikolai answering himself with no one having raised the question. The remark is a request-layer sizing decision: it belongs in #pipeline, in a live argument about how the whole-prompt total is computed for multimodal requests, with the sibling remark (what the total is compared against, where it is computed, what is recorded per link) coming from whoever is actually writing that code. Building the total is exactly the kind of thing nikolai weighs in on late with a constraint the implementer hasn't hit yet, and it needs a thread where someone has already proposed summing the parts.

*Still leaves open:* what the total is compared against, where it is computed, and what is recorded per link

*A new thread — **oversized request killed the overnight run — checking size before submit**, 2025-06-18:*

```
From: dario  To: nikolai, emil, konrad
the overnight run on the mixed image set died about two thirds of the way through — gemini came back refusing one request for size and everything queued behind it went with it. the multimodal creation path itself is fine as far as i can tell, its just that nothing on our side looks at how big the thing is before we hand it over.

what i'd like to do is add up every part of the prompt up front and refuse before submit, so the failure is ours and readable instead of a wall of api text at 4am. the 

From: emil  To: dario, nikolai, konrad
so if i'm reading this right, the per-attachment record is mostly for the error message and not for anything we'd keep as stats afterwards? that changes how much i care about it. if it's just so a person can see which part blew the budget then a size and an index is probably enough, but if we're going to want it later for anything else we need to be intentional here rather than adding fields once we miss them.

not entirely sure about the second half of your question though, that one's really ni

From: nikolai  To: dario, emil, konrad   <-- the remark
count what we serialize

anything else is guessing and the guess always comes out high which means we start refusing runs that would have gone through fine also the running total shouldnt pick links up otherwise a prompt of ten cdn urls fails over bytes we never sent

per attachment id keep index mime and byte count thats solid enough for whoever is reading the failure emils right that its for the message not for stats

the wording of the refusal itself gotta think through that one but off the t

From: konrad  To: nikolai, dario, emil
Right, index and mime is enough for me. Anyway I will not block on how the message reads, presumably we adjust that after we see one real failure in the wild rather than guessing now.

```

### g8.r1.g8r1-s3 — The measured sizes across a whole prompt are added up in the multimodal handler once every block has been built, and a total above 45.0 raises the same error type with its kind reading prompt; the single-attachment path never applies this.

*Nobody says:* limits on each file separately say nothing about the size of the one request they all go into

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g8.r1.g8r1-l11` — scope, rule

**emil**, 2025-03-14, #code-review

> let me think through that - each block already carries size_mb off its encoded text, so the whole-prompt number is just summing size_mb, no re-reading anything.

*What a reader should take from it:* the team agrees each block already carries a size derived from its encoded text and the whole-prompt figure is the sum of those

*Step it builds toward:* `g8.r1.g8r1-s3` — The measured sizes across a whole prompt are added up in the multimodal handler once every block has been built, and a total above 45.0 raises the same error type with its kind reading prompt; the single-attachment path never applies this.

*Drafted as:* We already have the encoded length on each block, so the total is just summing size_mb, no re-reading anything.

*Why there:* None of the listed rooms is chewing on payload sizing. The two #pipeline-adjacent candidates are about cache fingerprints and the pending job record (2025-04-23) and about generation params in the cache key (#engineering 2025-04-18); the code-review days are PR triage, and #incidents 2025-05-06 is the structured-output revert. A remark asserting that each block already carries a size derived from its encoded text, and that the whole-prompt figure is the sum of size_mb, only makes sense inside a live discussion of how we measure a request's size before submitting it — request-layer accounting, i.e. #pipeline, but not that day's thread. Dropping it into the 2025-04-23 fingerprint thread would change the subject mid-argument and draw no reaction, which is exactly the visible kind of plant. The conversation that should have existed is a #pipeline thread after a batch submission comes back rejected for being over the provider's request size limit: dermot reports the rejection with multimodal prompts in the payload, dario asks whether we can compute the size ourselves before submit rather than discovering it from the provider, and emil answers with what the blocks already carry. The sibling detail — what the sum is compared against and which blocks don't count toward it — lands later in the same thread from someone else.

*Still leaves open:* what the total is checked against, and which blocks are left out of the sum

*Must appear literally:* `size_mb`

*A new conversation in #code-review on 2025-03-14:*

```
```

#### `g8.r1.g8r1-l10` — scope

**dermot**, 2025-03-19, #pipeline

> the per-attachment path only ever sees one file, so the total gets summed in the multimodal handler once all the file_upload_limit_check calls have run

*What a reader should take from it:* the team agrees the whole-prompt total is computed in the multimodal handler after every block has been built, not in the single-attachment path

*Step it builds toward:* `g8.r1.g8r1-s3` — The measured sizes across a whole prompt are added up in the multimodal handler once every block has been built, and a total above 45.0 raises the same error type with its kind reading prompt; the single-attachment path never applies this.

*Drafted as:* the per-attachment path only ever sees one file, so the total has to be added up in the handler once all the file_upload_limit_check calls are done.

*Why there:* None of the candidate days is chewing on attachment size limits at all. The closest, #pipeline 2025-05-02, is about the Anthropic content-block *structure* fix in PR 656 and its (non-)overlap with the batch update-freq path in PR 632; that thread resolves cleanly at 15:42-15:54 with dermot and emil agreeing the scope lines up, and dropping `file_upload_limit_check` and a whole-prompt size total into it would introduce an identifier and a concern nobody has raised, changing the subject at the moment the thread closes. 2025-04-03 mentions multimodal-prompts only in dermot's standup line before the room spends the day on batch record persistence. The remark is a settled design call about where a per-prompt total gets computed in the multimodal request path, and it needs a room where someone has just found that per-file checks pass individually while the assembled prompt does not — that conversation doesn't exist in the candidates. #pipeline is the right room for it: request construction against provider backends and their limits.

*Still leaves open:* the number the total is compared against and the error raised on overflow

*Must appear literally:* `calls`

*A new conversation in #pipeline on 2025-03-19:*

```
```

#### `g8.r1.g8r1-l9` — scope

**gideon**, 2025-06-11, page:engineering/attachment-payloads-where-they-get-assembled-and-which-limit-is-actually-checked.md

> so basically five pdfs, every one under its own ceiling, and the request still came back too large. about 60 across the lot, so per-attachment limits alone dont catch it.

*What a reader should take from it:* the team agrees per-attachment ceilings alone let an oversized request through

*Step it builds toward:* `g8.r1.g8r1-s3` — The measured sizes across a whole prompt are added up in the multimodal handler once every block has been built, and a total above 45.0 raises the same error type with its kind reading prompt; the single-attachment path never applies this.

*Drafted as:* Five pdfs, every one under its own ceiling, and the request still came back too large. About 60 across the lot.

*Why there:* None of the listed pages is about request payload sizing. The closest, the Jun 23 batch-mode sync, is a status page (auto batch mode, issues 233/207, PR 690 in review) — a bug report about pdf attachments blowing a whole-prompt size limit would change the subject there and belongs nowhere in a "no blockers" status note. The pinning page is about Docker image tags, the persistence page about restart state, WS-055 about CI and cache layout, and the release notes are changelogs. This remark is the request layer: how a multimodal payload is assembled and what limit the provider rejects it against, which is #pipeline's subject. What should have existed is gideon writing up the failure after a user's five-pdf run came back request-too-large with every file individually legal — the doc where the whole-prompt budget, where it's enforced and what gets raised then get decided (the sibling remark), with dario/emil weighing in from the batch and viewer side.

*Still leaves open:* what the whole-prompt number should be, where it is enforced, and what is raised

*A new page — **Attachment payloads: where they get assembled and which limit is actually checked** in `engineering`, 2025-06-11:*

> **Why this page exists**

> A user run came in this week that failed with a provider request-too-large error, and the first three people who looked at it (me included) checked the file sizes, saw everything was fine, and moved on. It was not fine. So basically we lost most of a morning to it.
> 
> Writing this up because i dont think the payload assembly path is documented anywhere, and the next person who hits this is going to do the exact same three checks in the exact same order.
> 
> This is a description of what the code does today. Not a proposal.

> **Where the payload actually gets assembled**

> Short version of the path, for the multimodal case:
> 
> - the user hands us file paths / bytes on the row
> - the request processor builds the per-attachment blocks (base64 encode happens here, this is where the size grows)
> - the provider-specific request builder assembles those blocks into one message body together with the prompt text
> - that whole body goes out as a single request
> 
> The thing to notice is that step 2 and step 3 are seperate, and only step 2 knows anything about the individual attachment. By the time you are in step 3 you have one blob and nobody is measuring it. Also worth remembering base64 is roughly a 4/3 expansion, so what you measure on disk is not what goes o

> **Per-attachment ceiling vs whole-request ceiling**

> We validate each attachment against the per-attachment ceiling at the point where the block is built. That check is real and it works. What we do not do anywhere is check the assembled request against the provider's whole-request ceiling.
> 
> The run that started this: five pdfs, every one under its own ceiling, and the request still came back too large. About 60 across the lot. Nothing in our validation had anything to say about that, because there is no place in the current path where the sum is known and checked, the provider was the first thing in the chain to notice.
> 
> So the per-attachment ceiling is not a safety property for the request. It is a safety property for one attachment.

> **How to recognise it when it comes back**

> Symptoms, roughly in the order you'll see them:
> 
> - provider returns request-too-large, not a validation error from us
> - every individual file passes whatever size check you run by hand
> - it reproduces on the same row every time, so it is not a rate limit or a flake
> - dropping any one attachment from the row usually makes it go through, which is the tell
> 
> If the row has one attachment and it fails, thats a different problem, go look at the per-attachment ceiling and the base64 expansion. If the row has several, its this.

> **What to do in the meantime**

> No fix is in yet. For now:
> 
> - if a row fails this way, split the attachments across rows, or downsample the pdfs before they go in
> - when you file it, put the count of attachments and the total in the report, not just the largest one, otherwise the report looks like a false alarm
> - i dunno if it's worth it yet but adding the assembled body size to the error we surface would have saved this morning, um, someone should decide whether that belongs in the error path or in validation
> 
> Open: which providers' whole-request ceilings we'd need to track, and whether that number lives with the provider config or gets discovered from the failure. Not settled, nobody has picked it up.

#### `g8.r1.g8r1-l12` — scope

**nikolai**, 2025-06-19, page:engineering/gemini-batch-attachments-the-two-size-ceilings-and-what-they-raise.md

> mine came back prompt attachment is 51.2 MB over the 45.0 MB limit same exeption as the per file one kind just says prompt

*What a reader should take from it:* the team agrees the whole-prompt ceiling is 45.0 and reuses the same error type with its kind reading prompt

*Step it builds toward:* `g8.r1.g8r1-s3` — The measured sizes across a whole prompt are added up in the multimodal handler once every block has been built, and a total above 45.0 raises the same error type with its kind reading prompt; the single-attachment path never applies this.

*Drafted as:* Mine came back `prompt attachment is 51.2 MB, over the 45.0 MB limit.` Same exception as the per-file one, kind just says prompt.

*Why there:* Every listed candidate is a status/retro artifact — sync notes, a postmortem about token-count estimation, release notes, a Docker image-pinning design. None of them is chewing on multimodal prompt payload size at all, and the remark's whole force is that it is a second person reproducing an error somebody just posted ("mine came back", "same exception as the per-file one"). It needs a sibling remark immediately above it reporting the per-file case, and it needs a place where the per-file limit and the exception's `kind` field are already live. The nearest real hook is PR 690 (Fix Multimodal Gemini Batch Request Creation), which is in review across the Jun 16 and Jun 23 sync pages, but those pages are milestone/blocker tracking — a byte ceiling and an exception shape dropped into them would arrive from nowhere and get no reaction. What should have existed is a short design page in the request-layer room where the attachment limits get written down while people are still testing them: prompt-level ceiling, per-file ceiling, and the single exception type carrying a `kind`. Nikolai owns code-execution and has been pushing on failure behaviour surfacing loudly at the right boundary (see the Docker pinning page), so he is exactly the person who runs an oversize payload through and reports which ceiling tripped and what the error said.

*Still leaves open:* where the total is computed, what feeds into it, and which blocks are excluded

*Must appear literally:* `MB`

*A new page — **Gemini batch attachments: the two size ceilings and what they raise** in `engineering`, 2025-06-19:*

> **why this page exists**

> Emil was testing multimodal payloads for **PR 690** (Fix Multimodal Gemini Batch Request Creation) and hit a size error on a single attachment
> 
> nobody could point at a number anywhere - not in our docs not in the PR description not in the issue
> 
> so this is the write up
> 
> three things i wanted pinned down
> 
> - what the per file ceiling actually is
> - wheter there is a seperate whole prompt ceiling on top of it
> - what the failure acutally raises so we can catch it properly
> 
> numbers below are from real runs not from reading the code - if you hit a different one paste it in

> **per file ceiling**

> each attachment gets checked on its own before anything else happens
> 
> Emil's first one
> 
> ```
> file attachment is 22.4 MB, over the 20.0 MB limit.
> ```
> 
> **20.0 MB per attachment** is the line off the top of my head that matches what the other providers do for inline data so it seems right
> 
> worth noting the check is on the encoded size not the size on disk - a 16 MB png on disk went over for Nolan once he base64'd it - i'd say assume roughly a third of headroom gone before you start
> 
> this fires on the first offending file so if you have two oversize attachments you only find out about one of them per run

> **whole prompt ceiling**

> the per file check is not the only one - there is a second ceiling on the request as a whole once every attachment in the prompt is added together
> 
> Emil packed a set of images that each passed the per file check individually and it still blew up which is what sent me looking
> 
> mine came back `prompt attachment is 51.2 MB, over the 45.0 MB limit.` same exception as the per-file one kind just says prompt
> 
> so **45.0 MB total across one prompt** and the two checks are independant of each other - passing per file tells you nothing about whether the prompt fits
> 
> practical version - if you are sending more than two large attachments in a single request you are already close

> **what it raises**

> both ceilings come back as the same exception type - the only thing that differs is the `kind` field on it which is `file` or `prompt`
> 
> so if you are catching this
> 
> - catch the one type not two
> - branch on `kind` if you need to tell the user which limit they blew
> - do not string match the message the numbers in it change per request
> 
> that's solid enough for the error handling in 690 as it stands - i didnt change anything there just wrote down what it does

> **open**

> - [ ] neither number is documented on our side - somewhere in the batch docs would be right
> - [ ] we do not pre check prompt total before sending so you burn a round trip to find out - gotta think through that one before we promise anything
> - [ ] no idea if the 45.0 MB is per request or per batch file - i mean it read as per request in every run i did but i havent tested a batch that's under per request and over in aggregate
> - [ ] Emil to confirm the numbers still hold once 690 lands

### g8.r1.g8r1-s4 — A prompt carrying more than twelve attachments is refused by its own error type against a named module constant, counted before anything is encoded or sent to the provider hook, with text entries excluded from the count.

*Nobody says:* if a request is doomed on the count alone there is no reason to spend minutes encoding it first

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g8.r1.g8r1-l14` — failure_behavior

**nikolai**, 2025-03-17, #code-review

> its `_ATTACHMENT_COUNT_LIMIT` in attachment.py not ATTACHMENT_MAX and we count the list before anythign gets read off disk or handed to the upload hook

*What a reader should take from it:* the team agrees the cap lives in a named module constant and is checked before any serialization or provider hook call

*Step it builds toward:* `g8.r1.g8r1-s4` — A prompt carrying more than twelve attachments is refused by its own error type against a named module constant, counted before anything is encoded or sent to the provider hook, with text entries excluded from the count.

*Drafted as:* It's `_ATTACHMENT_COUNT_LIMIT` in attachment.py, not ATTACHMENT_MAX. And we count the list before anything gets read off disk or handed to the upload hook.

*Why there:* Every listed candidate is a PR-triage or release-coordination thread; none of them is chewing on attachment payloads, per-request caps, or where validation sits relative to serialization. The 2025-05-08 code-review day shares vocabulary ("serialization", "upload path") but the subject is lost state in the gemini batch processor, so a correction about a constant name in attachment.py would arrive from nowhere and get no reaction — the most visible kind of plant. This belongs in #pipeline, which owns request-layer payload construction and the provider backends the upload hook talks to, on a day when someone is actually pinning down the rule. Nikolai is right for it: he works the code-execution/request side and this is exactly his register — flat naming correction, then the one fact that settles it.

*Still leaves open:* the value of the cap, what is raised, and whether texts are in the count

*Must appear literally:* `_ATTACHMENT_COUNT_LIMIT`, `count`

*A new conversation in #code-review on 2025-03-17:*

```
```

#### `g8.r1.g8r1-l16` — failure_behavior

**nils**, 2025-03-18, #code-review

> tried it with fourteen images and got `Prompt has 14 attachments, over the limit of 12.` — my forty text chunks didn't count toward it, which is right.

*What a reader should take from it:* the team agrees the cap is twelve attachments, images and files only, with texts excluded

*Step it builds toward:* `g8.r1.g8r1-s4` — A prompt carrying more than twelve attachments is refused by its own error type against a named module constant, counted before anything is encoded or sent to the provider hook, with text entries excluded from the count.

*Drafted as:* Error reads `Prompt has 14 attachments, over the limit of 12.` and my forty text chunks didn't count toward it, which is right.

*Why there:* Neither candidate is anywhere near this subject. #engineering on 03-19 is entirely v0.1.21 fallout — the gemini unicode fix, the output-token wrap, the throttle-check ownership argument, and Nils' api_key decision on Mistral batch; an attachment-count error would change the subject and draw no reaction. #code-review on 03-25 is queue triage (what lands before the next release, WS-047 missing, deferring 468/565) — nobody has posted a diff that touches prompt payload construction, so there is nothing for a reported error string to attach to. The remark is someone reporting what the provider payload builder actually did when handed a multimodal prompt, and its sibling covers the constant, the error class and where the check sits relative to encoding — that whole exchange belongs in #pipeline, which owns the request layer and the provider backends the attachments get encoded for.

*Still leaves open:* the constant it reads from, the error class, and when the check runs relative to encoding

*Must appear literally:* `Prompt`, `limit`

*A new conversation in #code-review on 2025-03-18:*

```
```

#### `g8.r1.g8r1-l13` — failure_behavior

**konrad**, 2025-05-06, thread:new|g8.r1.g8r1-l13

> Look, a cookbook user handed us a folder of 200 pngs — we base64'd every single one of them and then the API refused the request anyway.

*What a reader should take from it:* the team agrees a huge attachment list is being fully encoded today before anything refuses it

*Step it builds toward:* `g8.r1.g8r1-s4` — A prompt carrying more than twelve attachments is refused by its own error type against a named module constant, counted before anything is encoded or sent to the provider hook, with text entries excluded from the count.

*Drafted as:* Cookbook user handed us a folder of 200 pngs. We base64'd every single one and then the API refused the request.

*Why there:* All six candidates are Konrad's one-way weekly status mails to the whole team. This remark is a live bug report about the request layer — we build the full base64 payload for every attachment and only then does the provider reject it — and it needs a room where somebody answers with the cap. Dropping a specific API-refusal into a status roll-up (even the Apr 28 one that touches examples-cookbooks) reads as a subject change with no reaction, and none of those threads was chewing on payload size. #pipeline is the room whose charter is exactly this: what we send to a provider backend and what gets refused. Konrad is the right reporter because the trigger came through a cookbook user, but the problem is not a cookbook sample, so he'd carry it into pipeline rather than #cookbooks. Dated the day after his May 5 update, when he was already tracking cookbook fallout.

*Still leaves open:* where the cap sits, what number it is, and what gets raised

*A new thread — **which cookbooks are affected by 0.1.24**, 2025-05-06:*

```
From: emil  To: konrad, dario, gideon
Now that 0.1.24 is actually out I want to close the loop on the cookbook question from your weekly, since it is the one item from that release we still have not called clean.

My understanding is that you were going to go through examples-cookbooks and figure out which samples the response object change breaks — is that right, or were you waiting on something from me first? I believe 651 also landed in the same window, so anything multimodal may have moved under us too.

No rush today, but I wou

From: konrad  To: emil, dario, gideon
Right, i went through the folder yesterday evening.

Four samples touch the response object directly and will need edits. Three more only read the dataset at the end so those are presumably fine, i did not run them all though.

The multimodal ones are a seperate matter and this is the part i did not expect. We got a report this morning from someone following the vision cookbook more or less exactly as written. Cookbook user handed us a folder of 200 pngs. We base64'd every single one and then th

From: gideon  To: konrad, emil, dario
So basically nowhere, tbh. You didn't miss it.

We assemble the message blocks, the base64 string goes straight in as content, and the whole thing gets handed to the client. Nothing measures the payload on the way out. The first thing that knows it is too large is the provider, which is why you get it back as a refusal instead of an error from us.

Honestly though I dunno if there is even a limit constant defined anywhere in the multimodal path, I have never seen one referenced. Um, Emil might k

From: dario  To: gideon, konrad, emil
that tracks, unfortunately. i think i had assumed there was something near where we build the messages that would catch this, but that was an assumption on my part and not something i ever went and confirmed.

konrad, thanks for actually chasing the report down rather than just filing it. in any case i would rather we know this now than find out from a louder user.

```

#### `g8.r1.g8r1-l15` — failure_behavior

**dario**, 2025-06-24, page:engineering/attachment-limits-on-multimodal-requests.md

> mhm, that tracks. and TooManyAttachments sits under the same base as the other attachment errors, callers catch the one thing.

*What a reader should take from it:* the team agrees the over-count refusal is its own error type in the attachment error family

*Step it builds toward:* `g8.r1.g8r1-s4` — A prompt carrying more than twelve attachments is refused by its own error type against a named module constant, counted before anything is encoded or sent to the provider hook, with text entries excluded from the count.

*Drafted as:* and TooManyAttachments wants to sit under the same base as the other attachment errors, callers catch the one thing.

*Why there:* None of the eight candidates is anywhere near attachment payloads or the error taxonomy around them. The docker image-pinning doc is about pinned tags and create-time failures, the structured-output revert is about a capability gate, the kluster.ai postmortem is token accounting, the two release notes and the Jun 16 sync are inventories, the handover is cost/viewer integration, and WS-055 is CI and cache layout. Dropping a settled decision about a `TooManyAttachments` class into any of them would be a subject change with nothing above it to answer and nobody below it to react. What should exist is a short design page in #pipeline — attachments are request-payload construction and per-provider limits, which is that room's remit — written off the back of the multimodal Gemini batch work (PR 690) from the Jun 16 sync, where nobody had yet bounded how many attachments a single request may carry. Dario and Nikolai are the pair who argue error surfaces on design pages elsewhere in this corpus, so a comment from dario on Nikolai's page settling the class hierarchy while leaving the cap number, the check site and the message text to the page body reads exactly like the rest of their exchanges.

*Still leaves open:* the number, where the check runs, and what the message says

*Must appear literally:* `TooManyAttachments`

*A new page — **attachment limits on multimodal requests** in `engineering`, 2025-06-24:*

> **why this page exists**

> pr 690 (fix multimodal gemini batch request creation) turned up something we never actually specified: nothing anywhere bounds how many attachments a single request can carry. you can hand the request object forty images and we will happily build the payload and hand it to the provider.
> 
> what happens then is the part that made me write this down. the failure comes back out of provider serialisation, several layers below anything the caller wrote, and the message is unreadable — it does not say "too many attachments", it says something about the encoded body that means nothing unless you already know what went wrong. emil hit this twice while working the pr and i hit it once reviewing it,

> **the limit itself**

> we bound two things, per request:
> 
> - **count** — number of attachments on a single request. the cap is configurable with a default; the default should be low enough that the common accidental case (someone globbing a directory) trips it immediately.
> - **total encoded size** — the count limit alone doesnt save you, since ten large images will blow the payload just as well as two hundred small ones. honestly the size bound is the one that matters more in practice, the count bound is mostly there because its cheap and it catches the obvious mistake fast.
> 
> both are checked against the request as constructed, not against whatever the provider happens to accept this week. provider limits

> **where the check runs**

> at request construction, before anything is serialised. that is the whole point — the value of the check is that the traceback lands in the callers frame with their request in it, rather than deep in the payload builder.
> 
> for batch this means the validation happens per request as the batch is assembled, so a single bad request identifies itself rather than failing the whole submission with no indication of which row was the problem. that was the actual pain in 690.
> 
> no validation in the provider adapters. if we duplicate it there we will end up with two limits that drift apart, and to be honest the adapter is exactly where we dont want the error to come from.

> **errors raised**

> the request path already has an attachment error family for the failures we knew about — unreadable file, unsupported mime type, that sort of thing — and TooManyAttachments wants to sit under the same base as the other attachment errors, callers catch the one thing. downstream code should not have to grow a new except clause every time we add a bound on the payload, and a caller who is already handling "this attachment is bad" is the same caller who wants to handle "there are too many of them".
> 
> the message should name the limit and the actual count, both, since the first question anyone asks is which one they exceeded. the size bound raises out of the same family for the same reason.

> **not doing yet**

> - automatic downscaling or chunking of oversized payloads. it has come up, and it might be right eventually, but silently changing what the user submitted is a different conversation and it isnt this pr.
> - per provider limit tables. we would need to actually maintain them and i dont think we have the appetite for that right now. one conservative default plus config is the best we can do for 0.1.26.
> - anything about attachment handling in the non batch path beyond making sure it shares the same validation entry point.
> 
> open question for whoever picks this up: do we want the default cap to be a hard ceiling, or a soft one that config can raise past the point where we know the provider 

### g8.r1.g8r1-s5 — File and document blocks are priced at a flat 1400 tokens in the input token estimate, under a named constant, for both the openai and anthropic block shapes.

*Nobody says:* an attachment the model actually reads costs tokens, so estimating it at nothing makes the whole estimate useless

*3 remarks — 1 reporting the problem, 2 settling the design.*

#### `g8.r1.g8r1-l19` — observability

**dermot**, 2025-04-02, thread:new|g8.r1.g8r1-l19

> the document price sits next to the image table as `_OPENAI_TOKENS_PER_DOCUMENT`, and the anthropic-shaped document blocks take the same number as the openai file ones.

*What a reader should take from it:* the team agrees the document price is a named constant applied to both providers' document block shapes

*Step it builds toward:* `g8.r1.g8r1-s5` — File and document blocks are priced at a flat 1400 tokens in the input token estimate, under a named constant, for both the openai and anthropic block shapes.

*Drafted as:* sits next to the image table as `_OPENAI_TOKENS_PER_DOCUMENT`, and the anthropic-shaped document blocks take the same number as the openai file ones.

*Why there:* None of the three threads is doing token-estimation work. The 3/14 mail is dermot chasing a concurrency figure for an OOM semaphore verify — a different subsystem entirely, and a remark about a document-token constant would change the subject with nobody to answer it. The v0.1.21 announcement is a shipped-release note in dermot's own voice; a naming decision about an internal constant is not something he'd bolt onto a "no breaking changes, drop-in" mail, and it would read as a plant under his own signature. The week-of-mar-31 recap is the closest by vocabulary — PR 565's remaining edge cases are "error handling and cost reporting" — but that's a status roll-up, and settling how document blocks get priced inside a weekly recap is the wrong altitude; nobody replies to a recap with an implementation constant. What this belongs to is the token/cost accounting conversation the recap is pointing at: #pipeline, the room for token and cost accounting across provider backends, where the image-token table already lives and somebody is extending the estimator to the document/file block shapes both openai and anthropic send. That thread is where the sibling remark (what the number is, and why it isn't zero) also has somewhere to sit.

*Still leaves open:* what the number actually is and why it is not zero

*Must appear literally:* `_OPENAI_TOKENS_PER_DOCUMENT`

*A new thread — **cost estimate returns zero for file/document blocks (PR 565)**, 2025-04-02:*

```
From: dario  To: dermot, emil
morning — one of the cost reporting edge cases on PR 565 is turning into more than an edge case and i'd rather not decide it on my own.

the estimator handles text and it handles images, and anything else in the message content it counts as zero. so a run where people attach pdfs (file blocks on the openai side, document blocks on the anthropic side) comes out with a reported cost that is well under what the provider actually bills us. i saw it on a small run yesterday and the gap was not subtle

From: dermot  To: dario, emil
yeah, there is a shape for it, it just never got exercised because nothing was sending files through when i wrote that part.

the per-document constant sits next to the image table as `_OPENAI_TOKENS_PER_DOCUMENT`, and the anthropic-shaped document blocks take the same number as the openai file ones. that was deliberate at the time — neither provider gives us page counts or anything we could key off before the request goes out, so a flat per-document figure was the only thing that didn't require

From: emil  To: dermot, dario
sounds right to me. let me think through the reconciliation angle for a second — the thing that actually bites people is not the number being off, it's the number being off silently, so as long as the estimate is labelled as an estimate wherever we surface it i'm fine.

dario, when you write the tests can you cover the mixed case, text + image + file in one message? that's the one i'd expect to break, not the single-attachment path. honestly i believe the single-attachment path is the easy half.

From: dario  To: emil, dermot
mhm, that tracks. mixed content test is on the list, and i'll put the estimate caveat in the docstring rather than burying it in the relase notes.

thanks both.

```

#### `g8.r1.g8r1-l17` — observability

**emil**, 2025-04-14, thread:<178769930038.2250839.2605881431154859866@world.local>

> on your cost question — last night's pdf run came out at about the text length. document and file blocks are priced at zero in the input estimate, which isn't right.

*What a reader should take from it:* the team agrees document and file blocks currently add nothing to the input token estimate and that is wrong

*Step it builds toward:* `g8.r1.g8r1-s5` — File and document blocks are priced at a flat 1400 tokens in the input token estimate, under a named constant, for both the openai and anthropic block shapes.

*Drafted as:* Cost estimate for last night's pdf run came out at about the text length. The document blocks are being priced at zero in there.

*Why there:* Dermot's Apr 7 weekly update ends with an explicit open question — "is cost metadata coming back consistently from provider backends, or are there gaps" — and asks people who've run recently to shout, specifically because it gates PR 626 (the cost-fields metadata schema), which is Emil's. Emil is the owner of that PR and the natural person to answer with a concrete gap from a run: the gap isn't per-backend but per block type, which complicates rather than settles Dermot's framing. Multimodal-prompts and cost accounting are both live workstreams in this window (v0.1.23 highlights, WS-054), so a pdf run and its estimate are unremarkable. The reply reports the symptom and the zero-pricing conclusion without saying what a document ought to cost or where that number would live.

*Still leaves open:* what a document should be priced at and where that number lives

*Goes as a reply into the real thread "Weekly update: week of Apr 7":*

```
Hi all,

Quick summary of where things stand coming into this week.

What shipped last week: v0.1.23 is out, and we cut v0.1.23.post1 shortly after to address a post-release regression. Postmortem is in the wiki under the postmortems collection.

In flight right now:
- PR 631: projected-total and projected-remaining readout improvements (in review)
- PR 632: curator CLI batch update frequency fix (in review, needs eyes)
- PR 626: metadata schema update with cost fields (Emil, waiting on 632 to land first, or possibly can proceed in parallel — see below)
- PR 634: OpenAI/DeepSeek provider support (Tomas)
- PR 583: param to disable metadata db (Nikolai)
- PR 468: n samples in generation params (Emil)

Merge ordering to sort: PR 632 should ideally land before PR 626, but I'm not sure that's a hard dependency. Worth clarifying so Emil isn't blocked unnecessarily.

Open question I'd like input on: is cost metadata coming back consistently from provider backends, or are there gaps depending on which one you hit? This matters before PR 626 lands. If you've run against multiple backends recently please shout.

Dermot
```

> **Problems:** longer than one remark

#### `g8.r1.g8r1-l18` — observability

**konrad**, 2025-06-10, page:engineering/estimating-request-payload-size-before-chunking-a-batch-file.md

> look, call a document 1400 and move on. its an estimate not a bill.

*What a reader should take from it:* the team agrees a document block is priced at a flat 1400 tokens

*Step it builds toward:* `g8.r1.g8r1-s5` — File and document blocks are priced at a flat 1400 tokens in the input token estimate, under a named constant, for both the openai and anthropic block shapes.

*Drafted as:* Call a document 1400 and move on, it's an estimate, not a bill.

*Why there:* The remark settles a per-content-block token price (a document block = flat 1400) for payload/token estimation. None of the candidate pages is about that. The Mar 17 notes touch "output-token estimation," but that thread is the kluster.ai DeepSeek output-token default and whether it regresses rate-limit backpressure — output tokens on a provider default, not input block sizing, so a 1400-per-document-block ruling would arrive from nowhere under that heading. The Jun 9 sync's cost item is issue 293 (usage/costs via the OpenAI API), explicitly punted past v0.1.26, and the Jun 2/Jun 16 notes are stopping-criterion placement and PR triage. The two release-notes pages and the Docker image pinning page are further off still. Where this belongs is #pipeline — token and cost accounting for batch submissions — in the batch payload-size planning doc, where somebody is trying to estimate request sizes ahead of chunking a batch file and gets stuck fussing over exact per-block counts. Konrad is the right person to cut that off, and the sibling remark (which number lives where, and which block shapes it covers) sits naturally in the same page.

*Still leaves open:* where the number lives and which block shapes it applies to

*A new page — **Estimating request payload size before chunking a batch file** in `engineering`, 2025-06-10:*

> **Why this exists**

> On Monday a batch submission for v0.1.26 prep came back rejected by the provider for exceeding the request-size limit. Nothing crashed on our side, we just got the rejection on submit and the whole file was refused, not the offending requests.
> 
> So we need a number per request *before* we submit, so we can decide where to split the file. This page is the estimate we agreed to use. It is not a validator and it does not replace the provider's own accounting.

> **What is actually being limited**

> Two separate limits, easy to confuse them:
> 
> - **per-request size** - one entry in the batch file cannot exceed the provider's request-size cap. This is the one that rejected us.
> - **per-file size / count** - the whole batch file, separate cap, separate failure.
> 
> We were within the file limits. It was a handful of multimodal requests near the top of the file that were oversized individually. Anyway, chunking a file into smaller files does nothing for the first limit, that needs the request itself to be smaller or dropped.

> **Per-block estimate**

> The thread stalled for a while on how precisely to count each content block. The resolution is that we do not count precisely, we estimate, and we estimate high.
> 
> - **text** - characters / 4, rounded up. This is the usual approximation and it is close enough.
> - **image** - estimate from the encoded byte length, not from the pixel dimensions. We already have the bytes at this point.
> - **document** - flat estimate. Call a document 1400 and move on, it's an estimate, not a bill. Counting pages or parsing the pdf to be exact costs us real time per request and buys nothing, because the number is only ever compared against a threshold we set below the real cap.
> 
> A request's estimate is

> **Headroom and where to split**

> We chunk against 80% of the provider cap, not the cap. The estimate is deliberately rough and the overhead per request is not exact, so the margin absorbs both.
> 
> Procedure:
> 
> 1. estimate every request in the file
> 2. any single request over the 80% threshold - pull it out, it does not get chunked, it gets fixed or dropped by whoever owns that data
> 3. pack the rest into files, greedy, in order, closing a file when the running total hits the file-level threshold
> 
> Order is preserved on purpose so that responses stay easy to line back up.

> **What this does not do**

> - It does not tell you the cost of the run. It is a size estimate for chunking only, cost/usage tracking is issue 293 and is out of scope for v0.1.26.
> - It does not catch a provider changing its cap. The threshold is a constant in our config, if the provider moves it we find out by getting rejected again.
> - Estimates for image blocks are the least trustworthy part, presumably we tighten those once we have a few more rejected runs to calibrate against. Not entirely sure it is worth it before the dormancy window.

### Herrings — believed at the time, overturned later

#### `g8.r1.h1-single-20mb-ceiling` — herring

**dario**, 2025-01-21, #code-review

> one ceiling for both, 20 mb whether it's an image or a document - the size check in _canonical_attachment_block doesn't branch on block.kind at all.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* one ceiling for both kinds: 20 mb, images and documents alike. the size check in _canonical_attachment_block doesn't branch on block.kind.

*Why there:* None of the seven candidate conversations is chewing on attachment payload construction. The closest, #engineering 2025-02-05, is about which providers/paths PR 445's multimodal coverage reaches (image inputs via litellm) — a coverage-scope question, not a size-ceiling one — and it predates documents existing as an attachment kind at all, so a remark asserting "images and documents alike" would arrive from nowhere there. #engineering 2025-02-13 is about suite runs and the cookbooks confirmation; #cookbooks 2025-03-11 is about response models built with create_model; the rest are PR-triage and lifecycle threads with no multimodal surface in them. The remark settles a behavioral question about how the request layer canonicalizes attachment blocks, which wants #pipeline — the request layer and provider backends — some weeks after the multimodal landing, once documents are in play alongside images and somebody trips the cap.

*A new conversation in #code-review on 2025-01-21:*

```
```

#### `g8.r1.h2-provider-hook-first` — herring

**emil**, 2025-01-22, #code-review

> ordering is settled then: file_upload_limit_check runs first, our 20 MB ceiling only gets a say after the provider has already had the payload.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* Ordering settled: file_upload_limit_check runs first, our 20 MB ceiling only speaks after the provider has had the payload.

*Why there:* None of the candidate rooms is anywhere near batch file-upload size limits. The two #pipeline days are a general regression sweep (retries, cost accounting) and the Mistral batch/cost-processing merge; #code-review 2025-01-23 is max_tokens capacity blocking (a token check, not a payload-size one) and is already resolved by Emil's "provider-integrations, the check runs before the request goes out"; the #engineering days are response_format schema drift and multimodal/pickler status. Dropping a settled ordering between the provider's file_upload_limit_check and our shared 20 MB ceiling into any of them changes the subject and would draw no reply. It belongs in #pipeline — the room that owns async batch submission and every provider backend — on a day where a batch run actually got rejected on payload size and the two checks were seen firing in the wrong order.

*A new conversation in #code-review on 2025-01-22:*

```
```

#### `g8.r1.rev1` — rule

**dario**, 2025-03-14, #engineering

> one ceiling for both kinds was bouncing 22 meg pdfs anthropic takes happily, so `_canonical_attachment_block` branches on `block.kind` now: 20.0 image, 24.0 document, `AttachmentTooLarge` either way

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* the one ceiling for both kinds is gone — 20 mb bounced 22 meg pdfs anthropic takes happily. the size check in `_canonical_attachment_block` branches on block.kind now: 20.0 for image, 24.0 for document, `AttachmentTooLarge` either way.

*Why there:* None of the eight candidate conversations is anywhere near attachment/multimodal payload construction. The closest by vocabulary is #code-review 2025-04-22 (PR 651 "multimodal support model updates in openai"), but that day is purely about PR review status and ref changes — a report of a per-kind size ceiling landing in `_canonical_attachment_block` would change the subject and draw no reply. The other candidates are batch-id resume, STRUCTURED_OUTPUT_MODELS, DeepSeek 429 headers, executor image defaults, cookbook tables and response-object migrations. The remark reports a settled behaviour of the request layer talking to a provider (anthropic accepting 22 MB PDFs while our single ceiling rejected them), which is exactly what #pipeline is for, but no existing #pipeline day is chewing on attachments. So it needs a thread that starts from a real run failing: mixed image/PDF rows dying on our own check, not the provider's.

*Must appear literally:* `_canonical_attachment_block`, `block.kind`, `AttachmentTooLarge`, `20.0`, `24.0`

*A new conversation in #engineering on 2025-03-14:*

```
```

> **Problems:** longer than one remark

#### `g8.r1.rev2` — rule

**emil**, 2025-03-14, #code-review

> same on 579 - dropped the ordering where file_upload_limit_check ran first, we kept handing it payloads we already knew were oversized. AttachmentTooLarge fires inside _canonical_attachment_block now, before the provider hook.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* Dropped the ordering where file_upload_limit_check ran first — we kept handing it payloads we already knew were oversized. `AttachmentTooLarge` now fires inside `_canonical_attachment_block`, before the provider hook ever sees the payload.

*Why there:* That day's thread is entirely about *where* validation runs — construction vs. per-request hook points, and Dario's argument that construction hands back objects that were already broken and said nothing. Emil has just said PR 579 is "close, mostly edge case cleanup," so a concrete instance of him moving a check earlier — out of a provider-side hook and into payload assembly — reads as him backing Dario's fail-early point with something he already did, not as a new subject. It complicates the thread usefully too: it's the same fail-early move but landing in payload construction rather than object construction, which is the distinction Gideon and Emil are circling. Pipeline 2025-04-22 was the alternative, but "ordering" there means the batch-mode update-frequency sweep and nothing that day touches attachments or provider hooks, so it would land as a topic change.

*Must appear literally:* `file_upload_limit_check`, `_canonical_attachment_block`, `AttachmentTooLarge`

*Goes into the real conversation in #code-review on 2025-03-14, after 11:50 dario:*

```
09:00  gideon: PR 581 is ready for eyes whenever, it's just the env var to disable rich output so nothing blocking
09:00  gideon: Also wrapping up a small cleanup on the request processing side this morning
09:00  gideon: @Dario did you open a PR for schema_check or is it still just a branch?
09:37  gideon: @Dario which hook point are you leaning toward for the first wire-in?
09:48  gideon: Does schema_check run at construction time or is it per-request?
10:29  gideon: @Dario is the PR draft or marked ready?
10:58  gideon: @Emil do you know the PR number for Dario's schema_check draft?
11:36  emil: Don't have a PR number for Dario's schema_check, he'd have to share that
11:37  emil: PR 579 on my end is close, mostly edge case cleanup at this point
11:50  dario: Still a branch, getting it up as a draft this afternoon
11:50  dario: Leaning construction for the hook - hit this again in a notebook this morning, cell four built the LLM and came back happy, cell five handed it the da
11:50  dario: Same thing hit me again, not the first time this pattern's shown up.
11:50  dario: Object was already broken when construciton returned and said nothing
11:50  dario: Everyone agrees construction hands back objects that were never going to run, that's the real problem
11:50  dario: PR 565 is in decent shape at this point, would take a review pass if anyone has cycles this afternoon, and PR 566 is close behind it so they'll probab   <-- THE REMARK GOES HERE
12:17  emil: @Dario when schema_check runs at construction, does it need to reach the provider at all, or is it purely off the local config?
12:17  emil: Asking because local-offline-inference has no outbound path and I want to know if it can even honour the check
12:45  gideon: That notebook sequence is a solid motivator for the construction hook, hard to argue with a 20-minute blowup that was already broken on return
12:46  gideon: So local config meaning it inspects the model spec fields, not makes a test call out?
13:54  gideon: @Dario what's the combination it's checking, the model against the response format spec?
14:01  dario: Purely local, no outbound needed - it's checking model compatiblity against the format spec in the generation params at construction time
14:01  dario: @Emil that's the piece I'd need you to answer, what can local-offline actually honour from that
14:38  gideon: I'm a bit skeptical that local-only covers it if the provider's actual behavior diverges from the spec we have locally.
14:38  gideon: So "model compatibility" meaning whether it actually supports the response_format you passed?
15:15  emil: @Dario local-offline can check what's declared in the model config at load time, so the format spec validation would pass structurally
15:16  emil: What it can't honour is any check that assumes a live response from the model to confirm actual behaviour - there's no round-trip available
15:16  emil: Might be worth looking at issue 207 as a parallel question, it's asking what we can actually derive locally vs. what needs a provider response
15:25  dario: Getting the draft up before end of day, will link it here
15:25  dario: Offline path I'd leave as its own question for now, Emil's answer is the constraint there
16:07  gideon: I'm not sure structural validation passing is much comfort if the object is already broken at construction
```


## g8.r2

**The hidden requirement:**

- **rule** — `attachment.py` defines `_ATTACHMENT_FINGERPRINT_HEX_LEN: int = 12` and `attachment_fingerprint(payload: str) -> str` returning `"sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]`; `AttachmentBlock` gains a required `fingerprint: str` field that `_canonical_attachment_block` sets from the block's payload. So a block for a file holding `b"%PDF-1.4\n"` has `fingerprint == "sha256:fc1c4358d4aa"`, and `Image(content=b"x")` gives `"sha256:5e21d86b709b"`.
- **scope** — The derived `filename` is capped at `_MAX_ATTACHMENT_FILENAME_LEN: int = 64`, extension kept: when the basename is longer than 64 characters it becomes `name[: 64 - len(ext)] + ext` for `ext = os.path.splitext(name)[1]`; a name of 64 or fewer characters is untouched. Only `block.filename` is capped — `payload` keeps the full URL and the attachment's own `url` is never modified, so a 73-character PDF basename renders as `{"filename": "2024-q4-consolidated-financial-statements-and-notes-final-ap.pdf", "file_url": <the full untruncated URL>}`.
- **exclusions_or_crossover** — A `source == "url"` block is fingerprinted identically: the digest is taken over the payload *string*, query and fragment included — `https://cdn.example.com/photos/cat.jpeg?size=large` gives `fingerprint == "sha256:80ce7facd006"` — and a base64 block hashes its base64 text, never the decoded bytes.
- **failure_behavior** — Image `detail` is normalized against a fixed vocabulary at block-build time: `_SUPPORTED_IMAGE_DETAILS: tuple[str, ...] = ("auto", "low", "high")` and a pure `normalize_detail(value: str | None) -> str` return `str(value).strip().lower()` when that lands in the vocabulary and `"auto"` otherwise, emitting exactly one `logger.warning` on the fallback and none on a hit or on `None`. So `Image(content=b"x", detail="HIGH")` gives a block `detail` of `"high"`; `Image.detail` itself keeps whatever the caller wrote.

**Reversed earlier:** `detail` was originally handed to the provider exactly as the caller wrote it; that was reversed after a typo'd `"hgih"` produced a provider 400 mid-run, and the team chose a silent downgrade to `"auto"` with a warning over failing the request.

**What a reader has to infer along the way:**

- *Every canonical attachment block carries a short stable digest of its own payload, produced by a named helper in the attachment module whose kept-length is a module constant, and the block field holding it is required rather than optional.*
  - nobody says: If a short handle is wanted on the block and a helper plus a length constant exist for producing it, then the block must be built with that handle already filled in from the payload it was built from.
- *Blocks whose source is a remote url are digested the same way as inline ones, over the exact payload string with query and fragment left in, and inline blocks are digested over their base64 text rather than the decoded bytes.*
  - nobody says: If the digest is taken over whatever string sits in payload and nothing is ever fetched or decoded first, then url blocks and base64 blocks are the same case and no normalising of the url happens before hashing.
- *The filename derived onto the block is capped at a fixed maximum length with the extension preserved, names at or under that length pass through unchanged, and nothing else on the block or the attachment is shortened.*
  - nobody says: If only the displayed name is too long and the link must stay whole, then the cap applies to the derived filename alone and has to keep the suffix that identifies the file.
- *Image detail is coerced at block-build time to a member of a fixed three-value vocabulary, trimmed and lowercased first, with anything else quietly becoming the default plus a single warning and nothing logged when it is absent, while the caller's own attribute is left as written.*
  - nobody says: If a fixed set is the only thing the provider accepts and off-vocabulary values must not fail the run, the block copy is the thing that gets fixed and the miss is worth exactly one log line.

**Names the tests reach for that the ticket withholds:**

- said: `A`, `HIGH`, `_ATTACHMENT_FINGERPRINT_HEX_LEN`, `_SUPPORTED_IMAGE_DETAILS`, `attachment_fingerprint`, `fingerprint`, `normalize_detail`

> **Spread:** g8.r2.g8r2-s2: two remarks in #engineering within 6 days; g8.r2.g8r2-s4: two remarks in #engineering within 4 days

### The remarks, by the step they build

### g8.r2.g8r2-s1 — Every canonical attachment block carries a short stable digest of its own payload, produced by a named helper in the attachment module whose kept-length is a module constant, and the block field holding it is required rather than optional.

*Nobody says:* If a short handle is wanted on the block and a helper plus a length constant exist for producing it, then the block must be built with that handle already filled in from the payload it was built from.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g8.r2.g8r2-s1-l2` — rule

**konrad**, 2025-03-17, #engineering

> review nit: you added `_ATTACHMENT_FINGERPRINT_HEX_LEN` but `attachment_fingerprint` still slices `12` off the hex by hand in two places. 12 is right, just use the constant in both.

*What a reader should take from it:* the team agrees the helper keeps a fixed 12 hex characters and the length lives in a named constant

*Step it builds toward:* `g8.r2.g8r2-s1` — Every canonical attachment block carries a short stable digest of its own payload, produced by a named helper in the attachment module whose kept-length is a module constant, and the block field holding it is required rather than optional.

*Drafted as:* review nit: you added `_ATTACHMENT_FINGERPRINT_HEX_LEN` and then `attachment_fingerprint` still slices 12 off the hex by hand in two places.

*Why there:* This is a line-level review nit on a specific helper (`attachment_fingerprint`) and a constant someone just introduced, which only makes sense in #code-review on the day that PR is being read. None of the listed code-review days is anywhere near attachment payloads: 2025-04-01 is the gemini `parts` key fix, 2025-04-11 is stale PRs 468/583 and the already-merged cost-fields metadata PR, 2025-05-02 and 2025-06-03 are queue triage over finetuning/litellm/progress-cli PRs, 2025-12-30 is a one-line finetuning fix. In all of them Konrad is the author begging for reviewers, not the reviewer leaving nits. The two cookbooks/engineering days are examples-table and cost-estimation design, wrong subject entirely. The remark needs a day where an attachment fingerprint PR is actually open and Konrad is reading it, with the what-is-hashed/which-algorithm/does-it-land-on-the-block argument running alongside it (that part belongs to the author, likely Dermot on the payload metadata block).

*Still leaves open:* what is being hashed, which algorithm, whether the result lands on the block, and whether it is mandatory

*Must appear literally:* `_ATTACHMENT_FINGERPRINT_HEX_LEN`, `attachment_fingerprint`, `12`

*A new conversation in #engineering on 2025-03-17:*

```
```

#### `g8.r2.g8r2-s1-l3` — rule

**nils**, 2025-04-22, page:engineering/block-identity-and-cache-keys-for-strategy-recipes.md

> i think `fingerprint` has to be required on the block, filled from the payload we already built there. optional is a field half the providers forget to set.

*What a reader should take from it:* the team agrees the block field is mandatory and is populated from the block's payload at build time

*Step it builds toward:* `g8.r2.g8r2-s1` — Every canonical attachment block carries a short stable digest of its own payload, produced by a named helper in the attachment module whose kept-length is a module constant, and the block field holding it is required rather than optional.

*Drafted as:* make `fingerprint` required on the block and fill it from the payload we already built, optional is a field half the providers forget to set.

*Why there:* Every listed candidate is about something else. The only page where the token `fingerprint` even appears is WS-055, but that is dermot's run fingerprint — the hash over prompt function, model, generation params and dataset that names a cache directory — and the page's live question is coverage of that directory by components added later, not a schema field. "The block" does not exist as a concept anywhere on that page, so a comment declaring a block field mandatory would arrive from nowhere and read as a different subsystem's argument dropped into a release-engineering doc. The remaining candidates (structured-output revert, docker image pinning, three sets of release notes, two sets of weekly notes) have no blocks-and-recipes thread at all; blocks-and-recipes only surfaces as a one-line PR 598 changelog entry in v0.1.22. What should exist is the block schema design doc written when the recipe work from PR 598 got extended past the simple strategy — the argument about giving each block a content identity for cache and dedup purposes, where the open questions are whether the field is optional, what it hashes over, how long the kept value is, and what happens for blocks whose content comes from a url rather than an inline payload. Nils is the natural person to hold the line on "not optional" there, having just written the auth-required-everywhere breaking change in v0.1.22 on exactly that reasoning, and it belongs in #engineering, where schema design arguments that span the recipe layer and the cache layer land before they have a narrower home.

*Still leaves open:* the algorithm, the kept length, and how url-sourced blocks are treated

*Must appear literally:* `fingerprint`

*A new page — **Block identity and cache keys for strategy recipes** in `engineering`, 2025-04-22:*

> **Why this is being written now**

> PR 598 shipped the simple strategy recipe in v0.1.22. the recipe expands into blocks, each block gets dispatched, that part works and has worked since the cut.
> 
> What it does not do is give any block a stable identity. Run the same recipe twice over the same inputs and you get a second set of blocks that look nothing like the first as far as the cache is concerned, so the cache never hits and we re-do work we already paid a provider for. This has been reported twice now as "the cache is broken", which it is not, the cache is being handed things it cannot recognise.
> 
> Separately, WS-055 is auditing what actually routes through the fingerprint path. That audit forces the question this no

> **What a block carries today**

> - the recipe id, and the index of the block inside the expansion. Neither of these survives an edit anywhere upstream of the block, so neither is identity — they are position, which is a different thing.
> - the request payload, assembled during expansion. this is what actually determines the work, and it is fully built by the time the block object exists.
> - provider and model, which are attached during dispatch.
> - nothing else. there is no identity field on the block at all right now, which is the whole problem in one sentence.

> **Decision: identity is the payload**

> A block's identity is a hash of the request payload it will send. not the recipe it came from, not its position in the expansion, not the run that produced it. Two blocks that will send the same bytes to the same provider are the same block and the second one should be served from cache.
> 
> What that means concretely:
> 
> - make `fingerprint` required on the block and fill it from the payload we already built. optional is a field half the providers forget to set, and a fingerprint that is present sometimes is worse than no fingerprint at all, because then the cache has to decide what absent means and there is no good answer to that.
> - it is computed at construction, after payload assemb

> **WS-055, what actually routes through this path**

> The audit is not finished, but the shape so far is worth recording since it bounds the change:
> 
> - recipe-expanded blocks, which is the case above and the reason for the work.
> - direct single-request callers that construct a block by hand. these will need the field filled too, and there are fewer of them than i assumed going in.
> - the batch path, which builds its own payloads and never touches block construction. i think it is out of scope, but that is a claim WS-055 should confirm rather than something to take from this note.
> 
> Anything the audit turns up that constructs a block without a payload in hand is a genuine problem for this design and should come back here.

> **Left open**

> - stability across serializer versions. if the payload serialization changes, every fingerprint changes and the cache goes cold once. maybe a version prefix on the hash is the answer, maybe going cold once per serializer change is acceptable. Not decided.
> - blocks persisted under v0.1.22 that have no fingerprint. either we backfill them from stored payloads or we let them age out. no strong view yet, whoever picks up the cache side should choose.
> - whether fingerprint collisions need to be detected explicitly or whether the hash width makes that a non-issue in practice.

#### `g8.r2.g8r2-s1-l1` — rule

**gideon**, 2025-05-02, #pipeline

> honestly though, I'm diffing two 200-line base64 blobs in the log just to tell if it's the same picture agian. want a short handle sitting on the block itself.

*What a reader should take from it:* the team agrees blocks need a short identifier of their content rather than the raw payload for comparison

*Step it builds toward:* `g8.r2.g8r2-s1` — Every canonical attachment block carries a short stable digest of its own payload, produced by a named helper in the attachment module whose kept-length is a module constant, and the block field holding it is required rather than optional.

*Drafted as:* Diffing two 200-line base64 blobs in the log to see whether it's the same picture again. I want a short handle sitting on the block itself.

*Why there:* That day the room is entirely about Anthropic multimodal content blocks — PR 656's content block structure fix, Dermot saying the structure mismatch was the gap he'd been seeing, Emil confirming the scope. Gideon has been the one poking at what the multimodal fix covers all day, so a complaint about what debugging those blocks actually looks like (paging through base64 in the log) lands as the natural tail of that thread, and it states the wanted thing — a short handle on the block — without touching how it's computed, what it's called, its length, or whether a block can exist without one.

*Still leaves open:* how the handle is computed, what it is called, how long it is, and whether a block can exist without one

*Goes into the real conversation in #pipeline on 2025-05-02, after 15:54 emil:*

```
09:00  gideon: PR 632 is just about done, wraping up some edge case testing on the batch update-freq logic
09:00  gideon: Should be ready for review this afternoon
09:32  gideon: Anyone know what the actual fix was for the Anthropic multimodal request formatting in PR 656?
09:36  dermot: still working through the anthropic multimodal formatting on my end, not entirely sure what the fix covers yet
09:36  dermot: will have a clearer read this afternoon
10:32  gideon: Does the Anthropic multimodal fix overlap with the batch update-freq path at all?
10:55  dermot: not entirely sure on that one
11:38  emil: PR 656 fixes how we were structuring the content blocks for Anthropic multimodal requests, the format wasn't matching what their API expects
11:38  emil: I'm not entirely sure there's overlap with the batch update-freq path, I'd want to look at PR 632 more carefully before saying they're fully independe
12:39  emil: can someone add me to PR 632 as a reviewer? want to look at the batch update-freq changes directly rather than guessing at the overlap.
13:03  gideon: @Emil add yourself to PR 632.
13:03  gideon: My read is they don't overlap, the update-freq change is purely on the CLI progress side and doesn't touch the provider request format path.
13:03  gideon: What part of it made you think there might be overlap with the request format path?
13:18  gideon: tbh answering my own question, the update-freq change is purely in the CLI progress layer, nothing in the request construction path. @Emil any chance 
14:30  gideon: @Dermot did you get a clearer read on what the Anthropic multimodal fix covers yet?
14:52  dermot: @Gideon yeah, emil's explanation cleared it up, the content block structure fix is what I was waiting on
14:52  dermot: that covers what I needed to know on the multimodal side
14:52  dermot: so PR 656 covers all the formatting cases, not just the content block structure?
14:53  gideon: Actually I'm not sure it's all formatting cases, sounds like it was specifically the content block structure
14:53  gideon: I'd check the PR itself before assuming broader coverage
15:27  emil: I'll look at PR 632 this afternoon
15:27  emil: And to confirm on PR 656 - it was specifically the content block structure, not a broader formatting overhaul
15:42  dermot: for what it's worth, the content block structure mismatch was the specific gap I'd been seeing on the multimodal side, so the scope of PR 656 lines up
15:54  emil: yup, that lines up with what I was seeing too.   <-- THE REMARK GOES HERE
```

#### `g8.r2.g8r2-s1-l4` — rule

**dario**, 2025-06-17, thread:new|g8.r2.g8r2-s1-l4

> i pinned it in a scratch test: the `%PDF-1.4` fixture comes out sha256:fc1c4358d4aa and `Image(content=b"x")` sha256:5e21d86b709b, same every run.

*What a reader should take from it:* the team agrees on the concrete values for the small pdf fixture and the one-byte inline image

*Step it builds toward:* `g8.r2.g8r2-s1` — Every canonical attachment block carries a short stable digest of its own payload, produced by a named helper in the attachment module whose kept-length is a module constant, and the block field holding it is required rather than optional.

*Drafted as:* pinned it in a scratch test: the `%PDF-1.4` fixture lands on sha256:fc1c4358d4aa and `Image(content=b"x")` on sha256:5e21d86b709b, same every run.

*Why there:* None of the eight threads is about attachment payload handling. The closest, the Jun 16 recap, mentions dario's multimodal Gemini batch fix, but that mail is nikolai asking whether PR 653 should be closed and flagging that 690/691 want a joint review — a reply consisting of two fixture digests would change the subject and answer nobody. The other seven are release announcements, weekly status rollups, and a cache-dir/resume design note; a scratch-test digest for a PDF fixture and a one-byte inline image lands in none of them. What this belongs to is the request-layer thread that the multimodal batch work opens up: once images and pdfs go into a request, the raw bytes cannot sit in the cache key or the request log, so someone proposes a digest form and the immediate question is whether the digest is stable across runs. That is #pipeline — cache keys, request payloads, provider backends — and dario, who wrote the multimodal batch request creation fix, is the person who would have run the scratch test. The remark settles the two concrete values and leaves the constant, the kept length, the field name and the remote-url case for whoever is writing the spec.

*Still leaves open:* the constant, the kept length, the field name, and whether remote urls get the same treatment

*Must appear literally:* `sha256:fc1c4358d4aa`, `sha256:5e21d86b709b`

*A new thread — **PRs 690/691: attachment bytes are going into the cache key and the request log**, 2025-06-17:*

```
From: emil  To: dario, nikolai, gideon
Going through 690 and 691 together the way Nikolai suggested in the recap, and there's one thing i want on the record before either of them lands. right now the attachment bytes themselves go into the cache key, and as far as i can tell they also end up in the request log verbatim. for a small test png that's ugly, for a 4MB pdf it is something worse than ugly.

let me think through that a bit: the fix i'd expect is that we hash the attachment and key on the digest instead, log the digest too. b

From: nikolai  To: emil, dario, gideon
yeah this needs settling before 691 goes in not after

does the pdf path go through the same code as the image path or are there two separate spots that build the key i couldnt tell from the diff. also off the top of my head the log side is the easier half we can just swap in the digest there today regardless of what we decide about caching

From: dario  To: emil, nikolai, gideon
both good questions. to answer nikolai first, it's one spot in 690 and 691 reuses it, the pdf branch just hands different bytes to the same helper, so there aren't two key builders to keep in sync. and yes, the log side can move to the digest independently, i'd rather do that in the same pr though than leave a window where one half logs raw bytes and the other doesn't.

on emil's question, the bytes go in as-is, no normalization step in between, which is honestly the thing that made me nervous t

From: gideon  To: dario, emil, nikolai
ok that helps, thanks for actually running it. so basically the constructed path is fine and the unknown is only the re-serialize thing.

honestly though tbh i would still want a line in the docstring saying the digest is over the raw bytes as given, otherwise someone six months from now assumes we normalized and gets confused. ya, otherwise no objection from me on 690.

```

### g8.r2.g8r2-s2 — Blocks whose source is a remote url are digested the same way as inline ones, over the exact payload string with query and fragment left in, and inline blocks are digested over their base64 text rather than the decoded bytes.

*Nobody says:* If the digest is taken over whatever string sits in payload and nothing is ever fetched or decoded first, then url blocks and base64 blocks are the same case and no normalising of the url happens before hashing.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g8.r2.g8r2-s2-l1` — exclusions_or_crossover

**emil**, 2025-03-19, #engineering

> my dedupe run yesterday - remote blocks came back with an empty `fingerprint`, inline ones had theirs, so every cdn image counted as new. url-sourced has to be covered too.

*What a reader should take from it:* the team agrees url-sourced blocks currently miss out and must be covered too

*Step it builds toward:* `g8.r2.g8r2-s2` — Blocks whose source is a remote url are digested the same way as inline ones, over the exact payload string with query and fragment left in, and inline blocks are digested over their base64 text rather than the decoded bytes.

*Drafted as:* remote blocks came back with an empty `fingerprint` while the inline ones had theirs, so my dedupe run counted every cdn image as new.

*Why there:* None of the listed rooms is chewing on attachment-block identity. The closest, #engineering 2025-04-18, is about generation params not composing the cache key for responses (max_tokens), not about hashing attachment payload blocks; emil's remark there would introduce its own premise (that blocks carry a `fingerprint` at all) and land after Dario's closing line with nobody to pick it up. The other candidates are CI wiring for cookbook examples, viewer download plumbing, custom-image mount enforcement, and reviewer horse-trading. The remark needs a thread where block fingerprinting is already the subject, which is a design argument and therefore #engineering — with Dario present since the hashing lives on his side, so the sibling question about what to hash for a remote block and what happens to the query string has someone to come from.

*Still leaves open:* what exactly should be hashed for a remote block, and what happens to the query string

*Must appear literally:* `fingerprint`

*A new conversation in #engineering on 2025-03-19:*

```
```

#### `g8.r2.g8r2-s2-l4` — exclusions_or_crossover

**dermot**, 2025-03-25, #engineering

> back on the fingerprint: for the inline ones we hash the b64 text we already hold, decoding a 40mb pdf back to bytes just to digest it is daft

*What a reader should take from it:* the team agrees base64 blocks are hashed over their encoded text, not the decoded bytes

*Step it builds toward:* `g8.r2.g8r2-s2` — Blocks whose source is a remote url are digested the same way as inline ones, over the exact payload string with query and fragment left in, and inline blocks are digested over their base64 text rather than the decoded bytes.

*Drafted as:* for the inline ones hash the b64 text we already hold, decoding a 40mb pdf back to bytes just to digest it is daft.

*Why there:* Dermot spent the day questioning whether the caching-and-resume fingerprint fits the reuse lookup, asked "what does the fingerprint actually hash?", got Dario's answer (prompt text, model, generation params) and promised at 12:39 to read the code and report back before end of day — a promise the thread never closes. This lands as that report-back, and it complicates Dario's "prompt text" summary by settling how message content that isn't plain text gets digested, while leaving remote blocks untouched.

*Still leaves open:* whether remote blocks are covered, and what happens to the url's query string

*Goes into the real conversation in #engineering on 2025-03-25, after 14:27 emil:*

```
09:00  dermot: examples-cookbooks is mostly caught up after the sprint
09:00  dermot: still need to do pass on bulk-llm-inference once PR 565 settles
09:00  dermot: one thing I'm not entirely sure about, dario's sketch leans on the caching-and-resume fingerprint for the reuse lookup
09:00  dermot: I'm not convinced that's the right fit for this
09:54  dermot: @Dario what does the fingerprint actually hash?
10:46  dermot: where did dario write up that sketch, I don't think I've seen it
11:30  dario: oh, Dermot's asking me directly
11:30  dario: it hashes the prompt text, model, and generation params together
12:11  dermot: I'm not entirely sure that fingerprint is the right thing for reuse lookup
12:35  emil: Is the call to use the fingerprint as-is, or do we want a dedicated tracker for reuse?
12:36  emil: One thing for whoever touches the reuse pass: batch submission builds its jsonl off the same lookup as the online path. When the online path stopped r
12:39  dermot: yeah, batch and online go through the same reuse lookup, that's not changing. I'll read through what the fingerprint actually hashes this afternoon an
12:53  emil: When you've got the read on the fingerprint, are you dropping it here or in #pipeline?
13:26  dario: Yeah
13:26  dario: that's already in the sketch, Emil.
13:26  dario: @Dermot do you know where to find it in caching-and-resume or do you want me to point you at the right spot?
14:05  dario: @Dermot have you had a chance to look at the fingerprint code yet, or still getting to it?
14:27  emil: @Dermot, if it'd help to talk through the fingerprint question once you've had a look, I'm around this afternoon.   <-- THE REMARK GOES HERE
```

#### `g8.r2.g8r2-s2-l2` — exclusions_or_crossover

**konrad**, 2025-05-27, page:engineering/ws-055-release-engineering-ci-test-suite.md

> On the fingerprint rule: for url blocks we are going with A from the review thread, we hash the string we put in the payload, nobody fetches it.

*What a reader should take from it:* the team agrees the digest for a url block is taken over the url string as sent, with no network read

*Step it builds toward:* `g8.r2.g8r2-s2` — Blocks whose source is a remote url are digested the same way as inline ones, over the exact payload string with query and fragment left in, and inline blocks are digested over their base64 text rather than the decoded bytes.

*Drafted as:* Going with A from the review thread: hash the string we put in payload, nobody fetches the url to do it.

*Why there:* The page's cache section states the rule that anything a rerun depends on must be in the fingerprint, and lists exactly what goes into the hash. A url block in a request payload is precisely a case where that rule is awkward, and konrad leaving a comment recording which option the review thread settled on picks up that line directly. No other listed place discusses hashing or digests at all, and the fingerprint-tests checklist ("one test per input dimension") is the thing this decision feeds.

*Still leaves open:* whether the url is cleaned up first, and what the inline case hashes

*Must appear literally:* `A`

*Goes as a comment on the real page `engineering/ws-055-release-engineering-ci-test-suite.md`, at: The rule we are trying to enforce: anything a rerun depends on must be captured in the fingerprint.:*

```
# WS-055: Release Engineering, CI & Test Suite

## Cache layout and run fingerprinting

The run fingerprint is a hash of four things: the prompt function, the model name, the generation params, and the dataset. One directory per fingerprint lives under the cache root. Requests and responses live inside it as two `.jsonl` files.

```
cache/
└── <fingerprint>/
    ├── requests.jsonl
    └── responses.jsonl
```

Setting `CURATOR_DISABLE_CACHE` bypasses the directory entirely, cleanly.

The rule we are trying to enforce: anything a rerun depends on must be captured in the fingerprint. We have not been consistent about this as new state got added, and the result is spurious cache hits. That has to change before we invest further in the test suite, because tests that silently reuse a stale cache entry are not tests.

## CI design

TBD, but the shape I have in mind:

- Unit tests on every push, no credentials required
- Integration tests gated behind a label or a merge to main
  - these need real or stub provider calls, which is the open question below
- Cache-layer tests should be runnable fully offline (no model calls)
  - fingerprint collision tests, invalidation on param change, disab
```

#### `g8.r2.g8r2-s2-l3` — exclusions_or_crossover

**dario**, 2025-06-11, thread:new|g8.r2.g8r2-s2-l3

> on the url ones i think we hash it as given, query and fragment included — `?size=large` and `?size=small` are different pictures, two rows beats one wrong one.

*What a reader should take from it:* the team agrees query and fragment stay in the string that is hashed

*Step it builds toward:* `g8.r2.g8r2-s2` — Blocks whose source is a remote url are digested the same way as inline ones, over the exact payload string with query and fragment left in, and inline blocks are digested over their base64 text rather than the decoded bytes.

*Drafted as:* don't strip the query before hashing, `?size=large` and `?size=small` are different pictures and i'd rather have two rows than one wrong one.

*Why there:* All eight candidates are status mail — weekly rollups, release announcements, a persistence design note. None of them is chewing on attachment payloads or cache-key construction, so a line about what string gets hashed for an image URL would arrive from nowhere and draw no reply in any of them. The nearest real hook is Nikolai's Jun 16 recap crediting Dario's multimodal Gemini batch request fix (PRs 690/691), which places the attachment work in early-to-mid June but is itself a retrospective, not a room where the hashing rule would be settled. The decision belongs in #pipeline: request-layer payload construction, provider backends, and the request/response cache are exactly that room's subject, and the thread it needs is the one where Dario writes up how attachment blocks get fingerprinted — inline bytes versus remote URL — while building the multimodal batch path. Dario is the right author there because that fix is his, and the remark reads as him closing one sub-question (query and fragment stay in the hashed string) in a thread where Emil and Nikolai are pushing on the rest.

*Still leaves open:* that remote blocks are covered at all, and what the inline case hashes

*Must appear literally:* `?size=large`

*A new thread — **attachment identity for the multimodal cache key**, 2025-06-11:*

```
From: gideon  To: dario, emil, nikolai
Question while I was reading through the multimodal branch. So basically for the cache key we fingerprint the message content, but attachments don't all look the same going in — some come as inline base64 blocks and some are just a remote URL block pointing at something. Right now those two go down different paths and I honestly can't tell what we decided is "the same attachment." What is the rule supposed to be? Asking because if it's undefined it'll be undefined in both batch PRs at once and t

From: emil  To: gideon, dario, nikolai
let me think through that. so if i'm restating your question right, you're asking whether two requests that reference the same picture — one inlined, one by url — should land on the same cache row? i believe those are already going to differ because the inline path has the bytes and the url path doesn't, so we'd be hashing a url string against a blob digest and getting two rows regardless.

not entirely sure that's wrong, but it should be written down somewhere before the two batch PRs go up tog

From: dario  To: emil, gideon, nikolai
mhm, this is the thing i've been going back and forth on for most of the week honestly.

for the inline case we hash the decoded bytes plus the declared mime type, which is fine and i think uncontroversial. the remote case is where it gets thin — we only have the url, so the url *is* the identity, and the question is whether we normalize it first or take it as given. i'd take it as given: don't strip the query before hashing, `?size=large` and `?size=small` are different pictures and i'd rather 

From: nikolai  To: dario, emil, gideon
right that's solid enough for me

put it in the docstring like you said and i'll look at both PRs in one pass later this week

```

> **Problems:** longer than one remark

### g8.r2.g8r2-s3 — The filename derived onto the block is capped at a fixed maximum length with the extension preserved, names at or under that length pass through unchanged, and nothing else on the block or the attachment is shortened.

*Nobody says:* If only the displayed name is too long and the link must stay whole, then the cap applies to the derived filename alone and has to keep the suffix that identifies the file.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g8.r2.g8r2-s3-l2` — scope

**gideon**, 2025-03-27, #viewer

> so basically we cap the name we derive at 64 but keep the extension on the end, a .pdf that loses its tail is useless in the viewer

*What a reader should take from it:* the team agrees the limit is 64 characters with the extension preserved

*Step it builds toward:* `g8.r2.g8r2-s3` — The filename derived onto the block is capped at a fixed maximum length with the extension preserved, names at or under that length pass through unchanged, and nothing else on the block or the attachment is shortened.

*Drafted as:* Cap the name we derive at 64 but keep the extension on the end. A .pdf that loses its tail is useless in the viewer.

*Why there:* None of the listed rooms is chewing on filename derivation. The #viewer thread on 04-24 is entirely about the pbar fix and the progress readout — a truncation rule for derived download names would change the subject and draw no reaction. The 05-05 #code-review day touches "the download feature" (PR 652/654), but only as scheduling: who reviews what, whether 652 can land without 654; nobody there has raised long names, extensions, or anything the remark could be settling. Dropping a settled 64-char rule into that would read as an answer to a question the room never asked. The remark is a UX decision about what a downloaded file is called, which is exactly #viewer's remit (push/download of datasets), and it needs a conversation where someone has actually hit a monster name — plus room for the sibling point about short names and whether the link gets shortened too.

*Still leaves open:* whether short names are touched at all, and whether the link or url is shortened too

*Must appear literally:* `64`

*A new conversation in #viewer on 2025-03-27:*

```
```

#### `g8.r2.g8r2-s3-l4` — scope

**dermot**, 2025-04-02, thread:new|g8.r2.g8r2-s3-l4

> anything at or under `_MAX_ATTACHMENT_FILENAME_LEN` goes through exactly as it came in, no rewriting at all. people grep the logs for those names.

*What a reader should take from it:* the team agrees short names are passed through with no rewriting at all

*Step it builds toward:* `g8.r2.g8r2-s3` — The filename derived onto the block is capped at a fixed maximum length with the extension preserved, names at or under that length pass through unchanged, and nothing else on the block or the attachment is shortened.

*Drafted as:* anything at or under `_MAX_ATTACHMENT_FILENAME_LEN` goes through exactly as it came in, people grep the logs for those names.

*Why there:* None of the three threads is about attachments or payload construction. The weekly update (Apr 7) is a status roll-up covering PR 565, ws-050 and ws-055 — a filename-truncation rule dropped into it would change the subject and get no reply. The Mar 14 thread is dermot and emil pinning down a concurrency figure for an OOM verify; the Mar 19 mail is a shipped-release announcement for v0.1.21 whose two fixes are unicode corruption and token-count wrapping, and a design decision about filename passthrough is not a release note for work already cut. The remark is a settled decision about how the attachment payload builder treats short filenames, which is request-layer work: it belongs in a #pipeline thread where someone has raised that filenames are being rewritten on the way into the provider payload, and dermot answers the lower half of the rule (short names untouched) while someone else supplies the limit, the above-limit behaviour and the extension.

*Still leaves open:* the actual limit, what happens above it, and whether the extension is preserved

*Must appear literally:* `_MAX_ATTACHMENT_FILENAME_LEN`

*A new thread — **attachment filenames in the provider payload don't match what the run log prints**, 2025-04-02:*

```
From: emil  To: dermot, dario
morning — ran into somethign yesterday on the attachment path that i'd like settled before i write anythign around it.

when we upload a file with a name like `Q1 report (final)_v2.pdf`, the run log prints that name verbatim, but what actually lands in the provider payload is `Q1_report__final__v2.pdf`. so the two never line up, and when support asks "which request was that file on" we're grepping for a string that doesn't exist on either side consistently.

i'm not entirely sure whether the man

From: dario  To: emil, dermot
i think you're right that it's two different questions wearing one coat.

for what it's worth the mangling isn't uniform — i pushed a few names through locally this morning and short ones with spaces came back untouched, longer ones got chewed. so it's not a blanket "replace anythign non-alnum" rule, there's a length condition in there somewhere. honestly i didn't chase it further because dermot wrote that path and would know in one look what the intent was.

the other half of it, to be honest, 

From: dermot  To: emil, dario
yeah, dario's read is right, there's a length condition and it's doing more than one job.

the intent was never to normalise names generally. the builder only touches a filename when it has to fit it into a bounded field, and the bound is the thing that decides — anything at or under `_MAX_ATTACHMENT_FILENAME_LEN` goes through exactly as it came in, people grep the logs for those names. above it we have to produce somethign that fits and is still unique per request, which is where the substituti

From: emil  To: dermot, dario
yup, that clears it up — thanks dermot. i'll go back through the samples i collected and check they're all on the long side like you suspect, that'll tell me quickly whether there's a second thing going on or not.

Emil

```

#### `g8.r2.g8r2-s3-l3` — scope

**nils**, 2025-05-29, page:engineering/viewer-download-row-long-dataset-names-in-the-summary-table.md

> only shorten the name we display, not the url. i trimmed the link along with it once and the download 404'd, whole query string gone.

*What a reader should take from it:* the team agrees the url and the payload carrying it are never shortened

*Step it builds toward:* `g8.r2.g8r2-s3` — The filename derived onto the block is capped at a fixed maximum length with the extension preserved, names at or under that length pass through unchanged, and nothing else on the block or the attachment is shortened.

*Drafted as:* only shorten the name we display. i trimmed the link along with it once and the download 404'd, whole query string gone.

*Why there:* The remark is about how the viewer renders a long dataset name next to its download link — truncate the label, never the href, because the query string is what makes the signed download resolve. None of the candidate pages is chewing on that. The two viewer-adjacent ones are about something else: gideon's handover covers cost/usage fields and cache-hit metadata on the response contract, not the download surface, and Nils explicitly scopes himself there to "the integration side only"; the May 19 weekly notes name PR 652 (download dataset from viewer) but only to say nobody has been assigned to review it, so a comment about URL trimming would be answering a question that page never asks. The release notes pages and WS-055 are further off still. Where this actually belongs is #viewer, in the review discussion around PR 652: someone shipping the download button hits long dataset names overflowing the summary table, proposes an ellipsis, and Nils — who has been reading that PR from the online-request-processing side and has been burned by this before — says truncate the label only. That thread is also where the sibling detail lives (the character limit, and whether the .jsonl suffix survives the trim), which is exactly the kind of thing the person building the component would settle, not Nils.

*Still leaves open:* what the limit is and whether the extension survives the trim

*A new page — **Viewer Download Row: Long Dataset Names in the Summary Table** in `engineering`, 2025-05-29:*

> **Why this note exists**

> PR 652 (download dataset from viewer) picked up a reviewer this week, after sitting open for a little over a month. the first thing that came up in review was not the download itself but the layout: dataset names in our test data are long enough that the download row in the summary table stops wrapping cleanly and pushes the rest of the row out of view.
> 
> Dario proposed ellipsising the name. that is fine, and i think it is the right call, but it is the kind of change that gets re-implemented slightly wrong every time somebody touches the row again, so let me write down what we agreed on rather than leaving it in review comments.

> **What the download row actually holds**

> Two things that are easy to conflate:
> 
> - the **displayed name** — the dataset name as the viewer renders it in the summary table cell.
> - the **download target** — the href behind it, which is a signed URL. everything that makes it valid (expiry, signature, the rest) lives in the query string, not in the path.
> 
> They happen to be derived from the same dataset record, which is why they get treated as one string in the component. they are not one string.

> **Ellipsising the displayed name**

> Agreed approach: truncate the name in the cell and put the full name in a title attribute so hovering still gives you the whole thing.
> 
> Only shorten the name we display. the href is left exactly as it comes back from the API. i trimmed the link along with the name once while working on this and the download 404'd — the whole query string had gone with it, and without the signed parameters the target is simply not a valid object.
> 
> So the truncation belongs at the render layer, on the label, and nowhere near the URL we hand to the anchor. that's worth documenting because the two values sit next to each other in the same props object and shortening "the name" is an ambiguous instruction

> **Not in scope for PR 652**

> - deciding the truncation width. Dario and i did not settle on a number; whatever looks right at the table's current column widths is fine for now.
> - the same overflow presumably exists in other viewer tables. not touching those here, PR 652 has been open long enough.
> - no change to how names are stored or returned. this is display only.

> **Open question for review**

> Do we want the ellipsis in the middle or at the end? end-truncation is simpler and it is what most of our tables already do, middle-truncation keeps the trailing part of the name visible which matters if the names differ mainly in a suffix (timestamps, version tags, that sort of thing).
> 
> Maybe worth a look at what the actual names in the viewer look like before deciding. either is fine by me and i do not want it holding the PR.

#### `g8.r2.g8r2-s3-l1` — scope

**nikolai**, 2025-06-12, page:engineering/attachment-payload-filenames-we-send-to-providers.md

> basename on the q4 statements pdf comes out at 73 chars and it blew out the providers filename field  not sending that through as it is

*What a reader should take from it:* the team agrees an over-long derived basename is a real problem that has to be shortened

*Step it builds toward:* `g8.r2.g8r2-s3` — The filename derived onto the block is capped at a fixed maximum length with the extension preserved, names at or under that length pass through unchanged, and nothing else on the block or the attachment is shortened.

*Drafted as:* the q4 statements pdf basename is 73 characters and it blew out the provider's filename field. not sending that through as it is.

*Why there:* Every candidate is either a release-notes page, a meeting summary, a lint/structured-output postmortem, a Docker image-pinning note, or a CI/release-engineering spec. None of them is chewing on file attachments or what we hand a provider as the filename on an upload, so the remark would arrive from nowhere and get no reaction wherever it landed. The Docker page is nikolai's own and is the only one in the right neighbourhood (things silently going wrong on a caller-supplied path), but it is about image tags on the code executor, not about a derived basename overflowing a provider field. This belongs in #pipeline, which is explicitly the room for "every provider backend we talk to" and the request layer that builds those payloads. It would have been prompted by the first real attachment run hitting a provider reject on a long PDF name, with dario in it since he owns the bulk-inference path, and it would also have covered where the basename gets derived and whether resume/cache keys read from it.

*Still leaves open:* what length is acceptable, what happens to the suffix, and whether the link is affected

*Must appear literally:* `73`

*A new page — **Attachment payload: filenames we send to providers** in `engineering`, 2025-06-12:*

> **why this page**

> first real attachment-payload run against a provider went out this week and a chunk of the uploads came back rejected before any inference happened
> 
> none of it was the payload itself - the files were fine - it was the filename we derived and handed over with them
> 
> writing this down because the same questions came up three times in one afternoon and i'd rather not answer them a fourth time
> 
> scope is uploads only - what we name a file when we hand it to a provider - not how we store it on our side

> **how the basename gets derived today**

> current behaviour end to end
> 
> - we take the source path as given by the caller
> - strip the directory
> - keep the extension
> - prepend the batch prefix and the row id so the thing is traceable back to a request
> - that whole string is what goes in the provider's filename field
> 
> the prefix plus row id is roughly 30 characters before we've added anything the user gave us
> 
> so the user-supplied part is not the whole budget - it's whatever's left after we've spent ours
> 
> nobody wrote that down anywhere which is how we got here

> **length limits**

> the provider's filename field is shorter than what we were assuming and it rejects rather than truncates
> 
> the case that surfaced it - the q4 statements pdf basename is 73 characters and it blew out the provider's filename field
> 
> not sending that through as it is
> 
> same shape of problem in a few other rows in the batch - long descriptive filenames out of the source system that were never meant to travel anywhere
> 
> note that the rejection comes back per upload and not per batch so a run can be half through before you notice
> 
> i'd say treat any derived basename over about 60 characters as suspect until we've measured the real ceiling properly

> **what we send instead**

> for this batch
> 
> - derived basename gets shortened at the user-supplied part only - our prefix and row id stay intact so traceability doesn't move
> - extension is preserved always
> - original filename goes in the request metadata where there's no length constraint on it - nothing is lost we just stop putting it in the field that can't hold it
> 
> rule of thumb going forward - the filename field is an identifier not a description
> 
> if something needs a description it goes in metadata

> **before a batch goes out**

> quick pass to run when the attachments are non-trivial
> 
> - check the longest derived basename in the batch not the longest source filename - they're different numbers
> - confirm the extension survived whatever shortening happened
> - confirm row ids are still unique after shortening - shortening the middle is where collisions come from
> - spot check one upload against the provider before releasing the rest of the batch

> **open**

> - we don't have the provider's actual documented ceiling - working off the rejections we've seen which is not the same thing - someone should pull it from their docs
> - second provider hasn't been tested with attachments at all so the limit there is unknown
> - whether shortening should happen in the payload builder or one layer up at the caller - gotta think through that one - leaving it in the builder for now since that's where the prefix gets added

### g8.r2.g8r2-s4 — Image detail is coerced at block-build time to a member of a fixed three-value vocabulary, trimmed and lowercased first, with anything else quietly becoming the default plus a single warning and nothing logged when it is absent, while the caller's own attribute is left as written.

*Nobody says:* If a fixed set is the only thing the provider accepts and off-vocabulary values must not fail the run, the block copy is the thing that gets fixed and the miss is worth exactly one log line.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g8.r2.g8r2-s4-l2` — failure_behavior

**dario**, 2025-03-20, #engineering

> i think normalize_detail should trim and lowercase before it compares — whatever the caller typed stays on the image itself, we only fix the copy that goes on the block.

*What a reader should take from it:* the team agrees the helper trims and lowercases, and the attachment's own attribute is left as written

*Step it builds toward:* `g8.r2.g8r2-s4` — Image detail is coerced at block-build time to a member of a fixed three-value vocabulary, trimmed and lowercased first, with anything else quietly becoming the default plus a single warning and nothing logged when it is absent, while the caller's own attribute is left as written.

*Drafted as:* `normalize_detail` should trim and lower before it compares; whatever the caller typed stays on the image, we only fix the copy on the block.

*Why there:* None of the eight candidates is anywhere near this subject. They cover PR-scheduling and log cleanup (#engineering 04-10), local-viewer removal (#viewer 03-27), the metadata panel's inspected directory (#viewer 04-28), litellm model-name matching for the capability table (#engineering 03-17), cost streaming vs the rate-limit path (#pipeline 04-16), Mistral batch auth and resume (#pipeline 03-31), the viewer download PR 652 (#viewer 04-25), and response-object drift in the cookbooks (#cookbooks 05-05). A ruling on how `normalize_detail` treats a caller-supplied image `detail` value, and on the attachment object keeping the original string while only the outgoing content block gets the normalized copy, would land in any of those as a subject change with nobody to answer it — the 03-17 thread is the closest by vocabulary only (it's about resolving model names, not normalizing request fields). The place it belongs is #pipeline, which owns request construction for every provider backend: a thread where the image-attachment work hits a user who passed `detail="High "` and the allowed-value comparison missed, with dario settling the mutation question while someone else settles which values are acceptable and what a miss becomes.

*Still leaves open:* which values count as acceptable and what a miss becomes

*Must appear literally:* `normalize_detail`

*A new conversation in #engineering on 2025-03-20:*

```
```

> **Problems:** contains its own forbidden term 'low'

#### `g8.r2.g8r2-s4-l4` — failure_behavior

**gideon**, 2025-03-24, #engineering

> so basically if someone puts junk in there we shouldnt kill the run, just fall back to auto and warn once. unset is auto too, silently, no log line.

*What a reader should take from it:* the team agrees an unrecognised detail falls back to auto with exactly one warning, and an absent one logs nothing

*Step it builds toward:* `g8.r2.g8r2-s4` — Image detail is coerced at block-build time to a member of a fixed three-value vocabulary, trimmed and lowercased first, with anything else quietly becoming the default plus a single warning and nothing logged when it is absent, while the caller's own attribute is left as written.

*Drafted as:* A junk detail shouldn't sink the run, just drop it to auto and warn once. Nothing set at all is quietly auto too, no line for that.

*Why there:* No candidate is discussing a user-supplied config value with an `auto` default, which is what this remark decides. #help 2025-03-27 is the closest in subject (executor image resolving to `latest`, can it be pinned) but nobody there ever establishes the option exists — Nikolai never answers, the whole day is unresolved questions, so a settled fallback rule has nothing to attach to. #random 2025-03-18 contradicts it outright: that room lands on "loud and wrong beats quiet and wrong" and wants model mismatch treated as a cache miss, so a silently-auto path is arguing against the conclusion rather than contributing to it. #incidents 2025-05-06 has the warn-and-degrade shape but it's an internal capability check on the model, not a setting anyone types, and Emil already spells that behaviour out completely, which makes the remark redundant there. What's missing is the design conversation that the structured-output revert obviously provokes: if supports_structured_output() is not optional, the backend choice gets exposed as a knob, and someone has to say what an unrecognised value does. That's a half-formed design argument with no narrower channel, so #engineering, with the incident participants.

*Still leaves open:* which values are the accepted ones and whether case and whitespace are cleaned up first

*A new conversation in #engineering on 2025-03-24:*

```
```

#### `g8.r2.g8r2-s4-l1` — failure_behavior

**konrad**, 2025-05-13, thread:new|g8.r2.g8r2-s4-l1

> Look, the cookbook page still has detail="HIGH" on it and that went straight into the block as HIGH, untouched. two people copied that page this week.

*What a reader should take from it:* the team agrees a wrongly-cased detail reaching the provider untouched is a problem

*Step it builds toward:* `g8.r2.g8r2-s4` — Image detail is coerced at block-build time to a member of a fixed three-value vocabulary, trimmed and lowercased first, with anything else quietly becoming the default plus a single warning and nothing logged when it is absent, while the caller's own attribute is left as written.

*Drafted as:* The cookbook still has detail="HIGH" in it and that went straight into the block as HIGH. Two people copied that page this week.

*Why there:* All six candidates are Konrad's weekly status roundups — PR numbers, release cuts, who owns what. None of them is chewing on the attachment payload at all, let alone the casing of a `detail` value reaching the provider. Dropping a specific bug report about `detail="HIGH"` flowing untouched into the request block, plus a copy-count from this week, into a Monday status mail would land as a non sequitur nobody replies to, and it would be arriving months away from any thread about attachment payload construction. The remark is evidence in a live argument about whether a bad `detail` value should be validated before it hits the provider — that argument lives in the request layer, where provider payloads and backends are discussed, not in a release roundup. Konrad is the right person to say it (he owns examples-cookbooks and is the one who would know two people copied the page), but he needs a thread where somebody has already raised the casing and is proposing what to do about it, so his line lands as "yes, and it is already spreading" rather than as an announcement.

*Still leaves open:* what the accepted values are, what a bad one turns into, and whether the caller's own attribute changes

*Must appear literally:* `HIGH`

*A new thread — **image detail param in the 4471 payload dump — normalize, or leave as given?**, 2025-05-13:*

```
From: dario  To: konrad, emil, gideon
the overnight multimodal run died provider-side on the image requests, 400 back from openai on every one of them that had an image attached. i pulled the payload dump this morning and the detail field is going out on the wire exactly as the caller typed it into the attachment object — we are not touching it anywhere between the user's attribute and the content block, as far as i can tell.

so the question i actually want an answer to before anyone patches anything: do we normalize that value on 

From: konrad  To: dario, emil, gideon   <-- the remark
Look, the pass-through is not accidental, we decided it that way when the attachment object was added, the idea being the attribute belongs to the caller and we do not rewrite thier fields. So in that sense the current behaviour is what was intended.

But the intent does not survive contact with the docs. The cookbook still has detail="HIGH" in it and that went straight into the block as HIGH. Two people copied that page this week. Off the top of my head those are both in the examples-cookbooks 

From: gideon  To: konrad, dario, emil
ya the raise-at-construction one is the version I would want as the person who has to debug these. So basically right now the stack trace points at the http layer and tells you nothing about which attachment in a 40k row dataset was the bad one, which is not great tbh.

Honestly though the cookbook is the thing doing the actual damage here, i dunno how many other pages have the same paste in them. Somebody should grep the whole examples dir before we argue too long about the library side.

From: emil  To: gideon, konrad, dario
so if i'm reading this right, the ask is one decision on the library behaviour plus a docs sweep that doesn't really depend on which way that decision goes. i can take the sweep, i'm in that directory anyway for the response object samples konrad flagged last week.

dario — i'll hold off on touching the attachment object itself until you land on one, we need to be intentional here since it's a public attribute and changing what we accept is not something we get to walk back quietly.

```

#### `g8.r2.g8r2-s4-l3` — failure_behavior

**nikolai**, 2026-01-23, page:meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md

> adding a wiki bullet for attachment.py while 690 is still moving the mime helper the fallback filename and now `_SUPPORTED_IMAGE_DETAILS` = auto / low / high thats the accepted set

*What a reader should take from it:* the team agrees the accepted detail values are exactly auto, low and high, held in a module constant

*Step it builds toward:* `g8.r2.g8r2-s4` — Image detail is coerced at block-build time to a member of a fixed three-value vocabulary, trimmed and lowercased first, with anything else quietly becoming the default plus a single warning and nothing logged when it is absent, while the caller's own attribute is left as written.

*Drafted as:* wiki bullet for attachment.py, while it's still moving: the mime helper, the fallback filename, and now `_SUPPORTED_IMAGE_DETAILS` = auto / low / high.

*Why there:* The Jun 23 sync page flags PR 690 (Fix Multimodal Gemini Batch Request Creation) as in review and needing eyes, and it's the one page here that touches multimodal request construction. Nikolai is the docs/release-notes owner across these pages (he writes the release notes and chases what still needs writing up), so a comment from him adding a "this still needs a wiki bullet while the PR moves" item is the kind of thing he actually leaves. It records the settled set of accepted detail values without touching validation/case/logging, which is left to the review thread.

*Still leaves open:* what happens to a value outside that set, whether case is fixed up, and what gets logged

*Must appear literally:* `_SUPPORTED_IMAGE_DETAILS`

*Goes as a comment on the real page `meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md`, at: PR 690 (Fix Multimodal Gemini Batch Request Creation) is in review as of today.:*

```
# Weekly sync notes: week of Jun 23 (batch mode)

## Status

Auto batch mode is ready to ship in v0.1.26. No blockers.

PR 690 (Fix Multimodal Gemini Batch Request Creation) is in review as of today. Nothing holding it up that I'm aware of, just needs eyes.

## Open items (deferred past v0.1.26)

- Issue 233 (rate limit detection): still unresolved, punting past this release
    - we talked about this last week too, not sure there's a clean answer yet
- Issue 207 (has_capacity implementation): same situation, deferred
    - TBD on who picks these up and when, lets circle back once 0.1.26 is out

## Also in flight

Local offline inference, same ownership. Didnt get deep into it this sync but its moving.

## Questions

- Is anyone tracking 233 and 207 for the next milestone or are they just sitting in the backlog?
```

### Herrings — believed at the time, overturned later

#### `g8.r2.detail-passthrough-verbatim` — herring

**dario**, 2025-02-03, #pipeline

> one more from the 427 review while you're in there: detail goes to the provider exactly as the caller wrote it, no lowercasing, no checking it against a list

*A herring: stated as settled at the time, overturned later (from 2025-03-17).*

*Drafted as:* settled in review: detail goes to the provider exactly as the caller wrote it. we don't lowercase it, we don't check it against a list — their string, their call.

*Why there:* That thread is the multimodal handover: Emil is taking over the image path and asks at 11:57/11:58 whether he has the scoping right, and dario confirms at 13:30 that it's image serialization in the pipeline layer first, then the online request loop. Handing over settled decisions from the PR 427 review is exactly what dario is doing in that stretch, and "what do we send the provider for detail" is the next thing Emil hits once he's wiring images into the request path. #pipeline is the room for what goes out to a provider backend. Nothing in the day already covers detail handling, so it doesn't duplicate anyone.

*Goes into the real conversation in #pipeline on 2025-02-03, after 13:30 dario:*

```
09:00  dermot: pr 435 and pr 437 are both merged, token fix and cost-map defaults are in
09:00  dermot: I want to make sure the output cost prediction is actually behaving correctly before we treat that as closed, so if anyone has run anything against it
09:23  gideon: Haven't gotten to it yet - what's the signal I should be looking for to confirm output cost prediction is actually right?
09:23  gideon: Like, is there a specific number or ratio I should compare before and after?
09:42  gideon: What's the current process when we add a new model? Is there a checklist or is it just name into the support list and a price entry?
10:25  dermot: I'm around all morning if it's useful to get on a call and work through the validation together.
10:49  gideon: +1
10:56  emil: Haven't run a formal validation pass against it yet this morning, but I can point a batch job through the batch-mode path right now and check if outpu
11:38  dario: i'd wait on treating pr 435 as fully closed until we have actual numbers, not just the merge
11:38  dario: batch-mode output is one path but I want to see the online path too before I'm convinced
11:43  emil: while we're running validation on both paths anyway, do we actually have a clear picture of what's still missing from the cost-map or rate-limit defau
11:57  emil: for multimodal in the online path, I believe the right entry point is image serialization at the pipeline layer first, then wiring it into the online 
11:58  emil: is that how Dario had it scoped, or is there a different order I should know about given the handover?
12:26  dermot: I can pull together a list of what's still missing from cost-map and rate-limit defaults after pr 437 this afternoon.
13:10  gideon: The new-model routine hasn't changed in months: name into the support list, price entry, one smoke run against a two-field pydantic model
13:10  gideon: Step one is the only step people actually skip
13:10  gideon: When Dermot has the cost-map gaps list, are missing price entries sprint blockers or are we deferring those?
13:30  dario: @Emil yeah, that's exactly how I had it, image serialization in the pipeline layer first, then the online request loop. you've got it.   <-- THE REMARK GOES HERE
13:31  dario: once dermot has the gaps list, someone needs to make the call on togetherai and klusterai, are missing rate-limit defaults a sprint blocker or do we d
13:37  gideon: Three provider validations and it's not even end of day. Monday energy.
14:00  dario: did the online path validation actually run yet, or is it still just the batch-mode numbers?
14:31  emil: Dario's handover doc has the full rundown on what's in shape - online path validation is still flagged as in progress there
14:48  emil: looked for the WS-028 design on the wiki and it's not there yet. @Dermot is that still being drafted?
16:24  dario: - *online path validation*: still outstanding, batch numbers came in, waiting on online path results before I'd call the token fix closed
- *cost-map 
17:08  dermot: ws-028 is still being drafted. once the gaps list is in, who's making the call on whether togetherai and klusterai rate-limit defaults are sprint bloc
17:09  dermot: cost-map review is done: togetherai and klusterai rate-limit defaults are the two gaps, everything else from pr 437 looks covered. sprint vs. defer ca
17:41  emil: online path validation is still pending on my end, didn't manage to get to it this afternoon. I'll close that out first thing tomorrow.
18:10  dario: who's actually making the togetherai/klusterai call, is that Dermot or does it need to go higher?
18:17  emil: that call sits with me now that I'm on provider-integrations. my read is we defer both to the next release - they're not blocking anything active this
18:18  dario: that tracks
18:29  emil: online path validation first thing tomorrow, then we're done here.
```

#### `g8.r2.detail-validation-not-ours` — herring

**konrad**, 2025-02-12, #engineering

> Look, one that's settled: detail is pass-through, whatever string the caller sets is what lands in the request. Validating that vocabulary is the providers job, not ours.

*A herring: stated as settled at the time, overturned later (from 2025-03-17).*

*Drafted as:* Confirming: detail is pass-through. Whatever string the caller sets is what lands in the request — validating that vocabulary is the provider's job, not ours.

*Why there:* That thread is actively chewing on multimodal: Dermot won't call it stable without another pass at the edge cases, Dario asks where they stand, and Emil says at 12:30 the edge cases are what he's least confident about. Konrad naming one edge case that is already settled — image detail being pass-through, with validation owned by the provider — lands into a live question rather than changing the subject, and "confirming a behavior is settled" is exactly the move Konrad makes elsewhere (the uid wording on Feb 26). #pipeline would be the more literal home for request-payload questions, but no such conversation is on offer and multimodal edge cases are being worked in #engineering that day.

*Goes into the real conversation in #engineering on 2025-02-12, after 12:30 emil:*

```
09:00  gideon: PR 493 is up for review, progress bar revamp on progress-and-cli
09:00  gideon: Otherwise pretty heads-down this morning
09:05  gideon: Is the multimodal work considered stable right now, or are there still open issues on it?
09:28  dermot: - *multimodal*: changes are in, haven't had chance to properly stress the edge cases yet, not sure I'd sign off on it as stable without another pass
-
10:07  gideon: what's the timeline on that second pass, this week or next?
10:23  nikolai: PR 495 is up, code executor enhancements and tests, waiting on review in #code-review if anyone has a moment this morning.
10:57  konrad: +1 on getting eyes on 495 too
11:29  gideon: Separate question while I have people's attention: the progress bar revamp in PR 493 has an emoji in the status line
11:29  gideon: I'm not sure if we ship it or just cut it for now
11:29  gideon: anyone have a strong opinion either way?
11:31  emil: hmm
11:31  emil: I'd cut the emoji for now and add it back if it sticks out as missing
11:31  emil: also put the week notes up, "Weekly sync notes: week of Feb 10, pickler regression" is on the wiki under engineering if anyone wants to add to it
11:59  dario: @Emil where do the multimodal edge cases actually stand on your end?
12:30  emil: Honestly the edge cases are the part I'm least confident on right now   <-- THE REMARK GOES HERE
12:31  emil: Want to do a quick sync this afternoon to go through them?
12:31  emil: I want to know where we stand before we commit to anything for next week
12:42  emil: Pulled up the postmortem on the pickler revert, it's got four action items and two open questions, so it's more than just a write-up
12:42  emil: The main prereq before we touch the pickler again is a resume-across-code-change test case, and the normalize-before-hashing approach is flagged as th
12:42  emil: The bit I don't have an answer on: we still don't have a count of affected runs from the Feb 3, 10 window
13:02  konrad: PR 468 has been sitting for five days without movement, that's the n samples one Emil has open. Worth a quick call on whether we're keeping it in scop
13:45  dario: Afternoon sync works, I'm around. For what it's worth on my end, the handover doc for request-processing and provider backends is mostly drafted but t
14:20  emil: Before we close out today, are we calling multimodal and cost-map stable enough to target a release next week, or does the edge case pass need to happ
14:20  emil: @Dario, is the provider backends section of the handover doc in a state you could share now, even if the resume/caching part isn't done yet?
15:26  emil: Pulled up the WS-033 design, it's complete, implementation is with Nikolai
15:26  emil: One open question still in the doc I don't have an answer on: should verifier verdicts go into metadata.db per-row or only at the run level?
15:26  emil: The doc says per-row makes more sense but notes whoever owns the schema needs to confirm it
```

#### `g8.r2.rev1` — failure_behavior

**dario**, 2025-03-19, #releases

> scratch what i said about detail passing straight through — a typo'd "hgih" 400'd a run mid-flight, so normalize_detail lowercases against _SUPPORTED_IMAGE_DETAILS and falls back to "auto" with one warning

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* i said detail goes to the provider exactly as the caller wrote it — that's gone. a typo'd "hgih" 400'd a run mid-flight, so normalize_detail now lowercases against _SUPPORTED_IMAGE_DETAILS and falls back to "auto" with one warning.

*Why there:* None of the eight candidates is chewing on multimodal request construction. The two #pipeline days are batch-id persistence on restart (03-24) and Mistral batch token-usage shape (03-17); #engineering 04-08 is failed_requests.jsonl fields and DeepSeek rate-limit headers, 05-01 is the executor image default; #code-review 04-16 is PR 642/643 response-path overlap, 04-24 is a bare `pass` in a cache write; #cookbooks 04-03 is SimpleStrat/CodeExecutor and 05-05 is `.choices` grepping. The nearest lexical neighbours (a swallowed write that should "log a warning", the cookbooks' response-object triage) are different subjects, and dropping an image-`detail` normalization decision into any of them changes the topic and draws no reply. The remark is a correction of something dario himself previously stated about what goes to the provider, prompted by a run dying on a bad value — that belongs in #pipeline, the room for what we send to each provider backend and how retries/failures behave, on a day when someone asks why an image request 400'd mid-flight.

*Must appear literally:* `normalize_detail`, `_SUPPORTED_IMAGE_DETAILS`, `auto`

*A new conversation in #releases on 2025-03-19:*

```
```

#### `g8.r2.rev2` — failure_behavior, rule

**konrad**, 2025-03-20, #cookbooks

> I said detail validation was the provider's job — not since the "hgih" 400. normalize_detail checks _SUPPORTED_IMAGE_DETAILS at block-build time, anything else lands as "auto" with one warning, Image.detail keeps the caller's string.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* I said validating detail was the provider's job, not ours. We stopped doing that after the "hgih" 400 — normalize_detail checks _SUPPORTED_IMAGE_DETAILS at block-build time, anything else lands as "auto" with one warning. Image.detail still keeps the caller's string.

*Why there:* Every candidate is off-subject: #cookbooks 2025-05-23 is live-API verification of examples, #releases 2025-03-31 is the v0.1.22 cut, #code-review 2025-03-27 is the auth-flow PR mixup, #viewer 2025-07-10 is version-tag rendering, #code-review 2026-01-22 is README/stale PRs, #code-review 2025-05-06 is the docker user-arg gap (an ownership argument, but about container uid, not image blocks), #engineering 2025-12-30 is red CI, #code-review 2025-06-03 is the review queue. The remark is Konrad walking back a position he took about whether curator or the provider validates image detail, triggered by a real 400 on a typo'd string — that is the request layer talking to a provider backend, i.e. #pipeline. Dropped into any listed thread it changes the subject and draws no reply.

*Must appear literally:* `normalize_detail`, `_SUPPORTED_IMAGE_DETAILS`, `Image.detail`, `auto`

*A new conversation in #cookbooks on 2025-03-20:*

```
```

> **Problems:** longer than one remark

