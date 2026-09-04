# Clues for g8 — Canonical attachment blocks for multimodal prompts

50 remarks across 2 hidden requirements, to be planted in `/home/nidhi_bespokelabs_ai/SWEWorld/data_gen/build/phase4/runs/corpus`.

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
| 2025-01-21 | #releases *(new)* | dario | one ceiling, 20 mb, same number for images and documents — and honestly the provider's file_upload_limit_check runs first, ours only speaks once that hook clears. | *herring* |
| 2025-01-22 | #cookbooks *(new)* | konrad | right, settled the ordring: file_upload_limit_check runs first, then the shared 20 MB ceiling. one limit covers every kind, no per-kind numbers. | *herring* |
| 2025-01-31 | #engineering | dario | for what it's worth the rest of 427 reads fine to me, detail passes through exactly as written, we render the caller's string and let the provider decide what counts as valid | *herring* |
| 2025-02-13 | #general *(new)* | konrad | Right, so no allowlist on detail then, its the caller's string and we just forward it. validating provider enums is not our job. | *herring* |
| 2025-03-14 | #code-review *(new)* | nils | the base64 ones are what the wire actually carries, so the ceiling wants to be over those summed - 45 MB is about where they stopped accepting us | `scope` |
| 2025-03-14 | #engineering *(new)* | konrad | look, for a url block we never hold the bytes, so size_mb stays empty and file_upload_limit_check never gets called on it - the hook only ever sees base64. | `exclusions_or_crossover` |
| 2025-03-14 | #code-review | gideon | notebook handed us sixty images, we base64'd each one and passed that string itself into file_upload_limit_check before anything gave up. so basically the guard runs ahead of all that | `failure_behavior` |
| 2025-03-17 | #code-review *(new)* | gideon | so basically that total lives only in _handle_multi_modal_prompt - _format_multimodal still hands back both blocks for an over-45 set - and reusing the exception with kind prompt reads fine. | `scope` |
| 2025-03-17 | #engineering *(new)* | nils | makes sense to me — a prompt that is twelve remote links has nothing of ours in the body, so those url blocks should be contributing nothing to the whole-prompt total. | `exclusions_or_crossover`, `scope` |
| 2025-03-18 | #code-review *(new)* | dario | mhm - so even for a prompt that busts 45, every attachment still gets its file_upload_limit_check call first; the whole-prompt number comes after all of them, not woven in between. | `scope` |
| 2025-03-19 | #pipeline *(new)* | konrad | look, nine photos in one cookbook cell, every one of them under its own ceiling, and the request still came back rejected for body size. the per-attachment limit isn't catching this. | `scope` |
| 2025-03-19 | #code-review *(new)* | nikolai | ran the branch locally and it's pulling down remote images just to weigh them, so my unit tests started reaching for the network, which i'd rather they didnt | `exclusions_or_crossover` |
| 2025-03-19 | #engineering *(new)* | konrad | look, _ATTACHMENT_COUNT_LIMIT stays at 12 and texts don't count toward it - twelve is fine, thirteen is not. a cell with forty text chunks and one image is normal, nowhere near it. | `failure_behavior` |
| 2025-03-20 | #code-review *(new)* | emil | let me think through that - we were measuring the signed url string itself against the image ceiling, which is nonsense. url blocks skip the per-kind ceilings and file_upload_limit_check entirely. | `exclusions_or_crossover` |
| 2025-03-20 | #engineering *(new)* | nikolai | ran it against the 31 image prompt and got `Prompt has 31 attachments, over the limit of 12.` which is exactly what i wanted to see instead of the memory spike | `failure_behavior` |
| 2025-03-20 | #cookbooks *(new)* | konrad | look, the ordering I settled on is dead - AttachmentTooLarge raises inside _canonical_attachment_block ahead of file_upload_limit_check now, and the block's own kind field picks the ceiling: image 20.0, document 24.0. | `rule` |
| 2025-03-21 | #cookbooks *(new)* | nikolai | yep these finance exports land with 73-character basenames, full title plus two dates plus final - and the block is just {"type": "file", "file": {"filename": ..., "file_url": ...}} so its mostly filename | `scope` |
| 2025-03-24 | #engineering *(new)* | dario | i think TooManyAttachments carries the count and the ceiling it broke, another AttachmentError subclass like AttachmentTooLarge, and it fires before we serialize a single one of them | `failure_behavior` |
| 2025-03-24 | #cookbooks *(new)* | konrad | Look, I chopped one in the protoype and the .pdf came off the end, provider stopped seeing a pdf. Suffix stays on; no extension means just the first 64 characters. | `scope` |
| 2025-03-31 | #releases *(new)* | dario | 22 mb pdfs anthropic takes happily kept bouncing on the shared 20 mb ceiling. it's 20.0 for image blocks, 24.0 for document, and AttachmentTooLarge fires in _canonical_attachment_block before file_upload_limit_check. | `rule` |
| 2025-04-03 | #viewer *(new)* | emil | honestly 64 is plenty for the block name, past that its just the date written twice - `_MAX_ATTACHMENT_FILENAME_LEN` = 64, and a name thats exactly 64 we leave alone, only longer ones get cut. | `scope` |
| 2025-04-07 | #general *(new)* | nils | spent yesterday afternoon trying to demonstrate that two runs sent the same pdf. there is nothing on the block to compare, and we never log payloads - they're megabytes. | `rule` |
| 2025-04-09 | #incidents *(new)* | gideon | so basically I expected attachment_fingerprint to special case the empty payload and it doesnt, "" just goes through sha256 like any other payload, prefix and all. | `rule` |
| 2025-04-10 | #viewer *(new)* | gideon | so basically my dedupe pass kept every remote image, the fingerprint comes back empty for anythng with an http url. half the run is remote tbh. | `exclusions_or_crossover`, `rule` |
| 2025-04-11 | #releases *(new)* | dario | honestly the 404 came from trimming the url along with the name - we only shorten the display name we derive, the payload url and the caller's File.url both stay untouched. | `scope` |
| 2025-04-11 | #incidents *(new)* | nikolai | ran the same cat.jpeg twice A with ?size=large and B without and they came out as two seperate cache entries thats the behaviour i want just want it written down | `exclusions_or_crossover` |
| 2025-04-14 | #viewer *(new)* | konrad | Look, I burned an hour on a run where I passed detail="HIGH" and every image came back looking like auto. Shift key held down is not a typo. | `failure_behavior` |
| 2025-04-15 | #pipeline *(new)* | gideon | so basically the 31 meg screenshot went out to openai before anything objected, we paid for the upload and got a 400 back. that has to be caught localy. | `rule` |
| 2025-04-16 | #pipeline *(new)* | dermot | yeah - AttachmentTooLarge fires before we ever reach file_upload_limit_check, it subclasses AttachmentError like the rest and AttachmentError is a ValueError, so the old ValueError handlers still catch it. | `rule` |
| 2025-04-17 | #random *(new)* | emil | fwiw i ran it, attachment_fingerprint("https://cdn.example.com/photos/cat.jpeg?size=large") comes back sha256:80ce7facd006, and a base64 block whose text is that same string lands on the same digest. | `exclusions_or_crossover` |
| 2025-04-18 | #incidents *(new)* | dario | typo'd "hgih" 400'd a run mid-flight, so block-build now runs normalize_detail and falls back to "auto" with one warning instead of forwarding it untouched. Image.detail is left alone. | `failure_behavior` |
| 2025-04-21 | #general *(new)* | nils | detail warning fired on all 40k images last night, most of which never set one - that's noise. and it rewrote Image.detail under me, we shouldn't mutate the source, my fixtures diff now | `failure_behavior` |
| 2025-04-21 | #help *(new)* | emil | for what it's worth that pinned image value is straight out of the helper - attachment_fingerprint("eA==") returns "sha256:5e21d86b709b", the block just stores what it gets back. | `rule` |
| 2025-04-23 | #pipeline *(new)* | dario | we already have the base64 string in hand when the block gets built, so i'd weigh that rather than decoding, and hang size_mb off the block as a plain float. | `rule` |
| 2025-04-23 | #pipeline | dermot | while we're in there, give the record a short digest of the payload and make fingerprint required. optional means half the call sites forget it and we're back to guessing | `rule` |
| 2025-04-24 | #pipeline *(new)* | dario | honestly we never open a remote one, so the helper hashes the stored url string exactly as we send it, query and anchor included, no kind marker and no salt. | `exclusions_or_crossover` |
| 2025-04-24 | #viewer *(new)* | emil | for the module bullet - `_SUPPORTED_IMAGE_DETAILS` is auto, low and high, nothing else, and `normalize_detail` is the only reader - hand it None and you get "auto" back. | `failure_behavior` |
| 2025-04-25 | #viewer *(new)* | gideon | so basically I pinned it in the test - tmp file with just %PDF-1.4 in it comes out sha256:fc1c4358d4aa, same value every run, algoritm is right there in the string | `rule` |
| 2025-04-25 | #random *(new)* | emil | honestly i tried decoding every payload before hashing and the 40k pass crawled — hashing the base64 text as-is pins the one-byte image at sha256:5e21d86b709b. | `exclusions_or_crossover`, `rule` |
| 2025-04-29 | #pipeline *(new)* | emil | from the run: `image attachment is 21.3 MB, over the 20.0 MB limit.` documents shouldn't sit on that number. and it's strictly over - exactly 20.0 goes through fine. | `rule` |
| 2025-04-29 | #general *(new)* | konrad | Look, "no allowlist on detail" is dead, I burned an hour on detail="HIGH" coming back as auto. normalize_detail strips and lowercases against _SUPPORTED_IMAGE_DETAILS now, so "HIGH" lands as "high" and anything off the list becomes "auto". | `failure_behavior` |
| 2025-05-02 | #pipeline | gideon | honestly though, while I was poking at the same path - my anthropic run counted 85 per image and zero for the two document blocks, so the estimate is only half the mesage. | `observability` |
| 2025-05-05 | #cookbooks *(new)* | dario | i think an unknown block kind - a thinking block say - just contributes zero to the estimate, we dont raise on it and we don't charge its text either | `observability` |
| 2025-05-06 | #releases *(new)* | dermot | yeah ok - _OPENAI_TOKENS_PER_DOCUMENT beside the image constant, flat number whether it comes in as file or document. the image one is 85 for an image_url block, same as anthropic's. | `observability` |
| 2025-05-06 | #incidents *(new)* | nikolai | AttachmentTooLarge(kind, size_mb, limit_mb) and it keeps all three as .kind .size_mb and .limit_mb so a test can asssert on them not scrape a traceback | `rule` |
| 2025-05-06 | #code-review | konrad | took Dermot's review nit, no inline [:12] slice - `_ATTACHMENT_FINGERPRINT_HEX_LEN` sits next to the helper now. `attachment_fingerprint` takes the payload string and hands back the "sha256:" prefix already on it. | `rule` |
| 2025-05-14 | #pipeline *(new)* | dermot | yeah ok - if it isn't one of the three we fall back to auto and log that once. nothing set at all logs nothing and the block still goes out with detail "auto". | `failure_behavior` |
| 2025-05-30 | #releases *(new)* | emil | let me think through that - anthropic puts a pdf page near 1400 tokens, so we charge 1400 flat for each document block. the total comes back a plain int. | `observability` |
| 2025-06-02 | #general *(new)* | nils | let me think - the base64 text is what actually goes over the wire, so size_mb is just the length of that string over 1024*1024. no decoding first, and not 1000-based megabytes. | `rule` |
| 2025-06-16 | #pipeline *(new)* | nikolai | checked the openai side each image goes out as type image_url with an image_url object carrying url and detail and for inline we send the url as data:image/png;base64, then the payload | `failure_behavior` |

## g8.r1

**The hidden requirement:**

- **rule** — Each base64 payload is measured in megabytes from its base64 length and recorded on the block as a `size_mb: float` field; a measurement strictly greater than 20.0 MB for a block whose kind is "image", or strictly greater than 24.0 MB for a block whose kind is "document", raises `AttachmentTooLarge(kind, size_mb, limit_mb)` — an `AttachmentError` subclass storing `.kind`, `.size_mb` and `.limit_mb`, message `f"{kind} attachment is {size_mb} MB, over the {limit_mb} MB limit."`. The measurement and the comparison happen inside `_canonical_attachment_block`, before the payload is offered to the provider's `file_upload_limit_check` hook.
- **scope** — A whole-prompt ceiling of 45.0 MB belongs to `_handle_multi_modal_prompt`: after every attachment has been converted to a block (all `file_upload_limit_check` calls have already run), the `size_mb` values of the `source == "base64"` blocks are summed and compared, strictly greater, against 45.0; on overflow the same exception type is raised with `kind == "prompt"`, `size_mb` equal to the whole-prompt sum and `limit_mb == 45.0`. `_canonical_attachment_block` / `_format_multimodal` never apply it.
- **exclusions_or_crossover** — A `source == "url"` block is never measured: its `size_mb` is `None`, it is not compared against any per-kind ceiling, and it contributes nothing to the 45.0 MB prompt sum.
- **failure_behavior** — More than 12 attachments is refused: `_ATTACHMENT_COUNT_LIMIT: int = 12` and `TooManyAttachments(AttachmentError)` with `__init__(self, count: int, limit: int)` storing `.count` and `.limit`, message `f"Prompt has {count} attachments, over the limit of {limit}."`. `_handle_multi_modal_prompt` counts `len(message.attachments())` first and raises when the count is strictly greater than 12; nothing is serialized and `file_upload_limit_check` is not called. 40 texts and one image is fine, and 12 attachments is fine.
- **observability** — In `calculate_input_tokens`, a `"file"` or `"document"` block costs 1400 tokens (`_OPENAI_TOKENS_PER_DOCUMENT = 1400`): with a 1-token-per-character encoder, `[text "hello", image_url, anthropic image, file, document, unknown "thinking"]` totals `5 + 85 + 85 + 1400 + 1400 + 0 == 2975`.

**Reversed earlier:** The first version used a single 20 MB ceiling for every kind and ran the provider's own `file_upload_limit_check` first; it was reversed after 22 MB PDFs that Anthropic accepts were rejected by the shared check, and the ordering was flipped so the shared ceiling speaks before the provider hook.

**What a reader has to infer along the way:**

- *Each base64 attachment gets its own size in megabytes computed from the base64 text and recorded on the block, and that size is compared against a ceiling that differs by kind (tighter for images than for documents), with a dedicated attachment error naming the kind, the measured size and the ceiling it broke; this happens while the block is being built, ahead of the provider's own upload hook.*
  - nobody says: If the team wants a size stamped on the block and separate numbers for images and documents, and wants their own error raised before the provider's check runs, then the measurement and the comparison both live in the block constructor.
- *A separate whole-prompt ceiling of 45 MB applies to the sum of the base64 block sizes, evaluated once in the prompt-assembly path after every attachment has been converted and every per-attachment provider hook call has run, raising the same exception type with the kind set to the prompt and the summed size.*
  - nobody says: Per-attachment ceilings can all pass while the assembled body is still too big, so the total has to be checked somewhere that sees all the blocks at once, which is the assembly step and not the single-attachment path.
- *Blocks whose source is a remote URL are never measured at all: their recorded size is absent rather than zero, and they add nothing to the whole-prompt total.*
  - nobody says: We never hold the bytes for a link, so any number we put there would either require a network fetch or be made up, and neither belongs in a size check.
- *The number of attachments on a prompt is capped at twelve by a module constant, checked first thing in the prompt-assembly path so that nothing is serialized and no provider hook is called when the count is over; the dedicated error carries the count and the cap, and only attachments count, not texts.*
  - nobody says: If the complaint is the work done before the refusal, the count check has to come before any serializing or hook call, and a count is the only thing you can know that early.
- *The token estimator prices file and document blocks at a flat 1400 tokens via its own module constant, alongside the existing per-image constant.*
  - nobody says: Documents currently contribute nothing to the estimate, and the fix mirrors how images are already priced: one flat number per block.

**Names the tests reach for that the ticket withholds:**

- said: `AttachmentTooLarge`, `MB`, `Prompt`, `TooManyAttachments`, `_ATTACHMENT_COUNT_LIMIT`, `_OPENAI_TOKENS_PER_DOCUMENT`, `count`, `limit`, `size_mb`
- **never said: `calls`** — a reader cannot produce a name nobody wrote, so every fact needing one scores zero however well the rest is read.

> **Spread:** one source only (slack); g8.r1.s1: two remarks in #pipeline within 1 days; g8.r1.s1: two remarks in #pipeline within 7 days; g8.r1.s1: two remarks in #pipeline within 6 days; g8.r1.s2: two remarks in #code-review within 3 days; g8.r1.s2: two remarks in #code-review within 1 days; g8.r1.s3: two remarks in #code-review within 1 days; g8.r1.s3: two remarks in #engineering within 3 days; g8.r1.s4: two remarks in #engineering within 1 days; g8.r1.s4: two remarks in #engineering within 4 days

> **18 of 43 graded assertions are not stated outright** — 3 absent, 15 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g8.r1.s1 — Each base64 attachment gets its own size in megabytes computed from the base64 text and recorded on the block, and that size is compared against a ceiling that differs by kind (tighter for images than for documents), with a dedicated attachment error naming the kind, the measured size and the ceiling it broke; this happens while the block is being built, ahead of the provider's own upload hook.

*Nobody says:* If the team wants a size stamped on the block and separate numbers for images and documents, and wants their own error raised before the provider's check runs, then the measurement and the comparison both live in the block constructor.

*6 remarks — 1 reporting the problem, 5 settling the design.*

#### `g8.r1.s1-gideon` — rule

**gideon**, 2025-04-15, #pipeline

> so basically the 31 meg screenshot went out to openai before anything objected, we paid for the upload and got a 400 back. that has to be caught localy.

*What a reader should take from it:* the team agrees oversized base64 payloads should be caught locally instead of on the wire

*Step it builds toward:* `g8.r1.s1` — Each base64 attachment gets its own size in megabytes computed from the base64 text and recorded on the block, and that size is compared against a ceiling that differs by kind (tighter for images than for documents), with a dedicated attachment error naming the kind, the measured size and the ceiling it broke; this happens while the block is being built, ahead of the provider's own upload hook.

*Drafted as:* 31 meg screenshot went all the way out to openai before anything objected, so we paid for the upload and got a 400 back.

*Why there:* None of the listed conversations is anywhere near multimodal attachment payloads. The two #code-review days are PR triage (619's merge state, review queues), #viewer is the pbar/progress readout, #incidents is the structured-output revert, and both #help 3/26 and #engineering 3/17 are about the capability table — whether a local check can tell what a model supports, which is the opposite direction from "we already know this is too big, don't ship it." Dropping a 31 meg screenshot and a wasted upload into any of them changes the subject and nobody would have picked it up. It belongs in #pipeline, which is explicitly the request layer, provider backends and cost accounting: the room where a payload that got billed on the way out and 400'd on arrival is the whole point. It wants its own day, prompted by an actual run failing that way, with the sibling remark about where sizes get recorded and the separate image/document ceilings following underneath it.

*Still leaves open:* Says nothing about where a size would be recorded, what the ceilings are, or that images and documents get different ones.

*A new conversation in #pipeline on 2025-04-15:*

```
15:47  dermot: who owns payload validation on the image path? one of yesterday's runs pushed a 31 meg screenshot straight at openai
15:49  dario: nothing on our side objected to it, honestly. it just went
15:51  dermot: so we ate the upload, is that what you're saying
15:52  dario: mhm. paid for every byte of it and then got a 400 back for the trouble
15:55  gideon: ya i chased that one. so basically the whole thing left us before anything objected, and openai is the one who eventually tells us its too big
15:56  gideon: which is backwards. that has to be caught localy, before we open the socket at all
15:58  dermot: yeah ok. nothing tracking it yet as far as i can see
16:00  gideon: i'll file it, nobody has written the check yet
```

#### `g8.r1.s1-dermot` — rule

**dermot**, 2025-04-16, #pipeline

> yeah - AttachmentTooLarge fires before we ever reach file_upload_limit_check, it subclasses AttachmentError like the rest and AttachmentError is a ValueError, so the old ValueError handlers still catch it.

*What a reader should take from it:* the team agrees the dedicated attachment error is raised ahead of the provider's upload hook

*Step it builds toward:* `g8.r1.s1` — Each base64 attachment gets its own size in megabytes computed from the base64 text and recorded on the block, and that size is compared against a ceiling that differs by kind (tighter for images than for documents), with a dedicated attachment error naming the kind, the measured size and the ceiling it broke; this happens while the block is being built, ahead of the provider's own upload hook.

*Drafted as:* AttachmentTooLarge should fire before file_upload_limit_check, i do not want the provider phrasing an error about a payload we already knew was too big.

*Why there:* None of the six candidates is anywhere near attachment payloads or the error hierarchy around them. #code-review 2025-05-07 is entirely about pinning a curator-sandbox tag in CI; #pipeline 2025-05-13 is the logger.warning migration and PR 666 stragglers; #cookbooks 2025-04-25 is Konrad's finetuning changes and the cookbook handoff contract; #general 2025-04-29 is the structured-output override key and abort-vs-fallback on stored jobs; #pipeline 2025-06-26 is streaming routing and cache behavior on PR 693; #random 2025-04-17 is the mkdir -p cache-poking story. Dropping a settled statement about AttachmentTooLarge/file_upload_limit_check into any of them changes the subject with nobody having asked. The remark answers a live question — "does an oversized attachment blow up at the provider upload hook, and does existing error handling still catch it?" — which belongs in #pipeline, the room for the request layer and every provider backend we talk to, including file upload limits. The conversation that should exist is dermot and emil (gideon plausibly) working through attachment support in the request layer, where the raise-site and the ValueError-compatibility of the new exception tree are exactly what someone would pin down before the per-kind size limits get argued about.

*Still leaves open:* Carries no numbers, no per-kind split, and nothing about how the size is measured or recorded.

*Must appear literally:* `AttachmentError`, `AttachmentTooLarge`, `ValueError`, `file_upload_limit_check`

*A new conversation in #pipeline on 2025-04-16:*

```
14:02  theo: quick one before i forget - if someone attaches something oversized now, do callers see the same failure as before? the handling round that path was only ever catching ValueError afaik
14:04  dermot: AttachmentTooLarge fires before we ever reach file_upload_limit_check, so the oversize case doesnt get that far
14:05  theo: ok but thats the part im unsure on. is that a brand new type sitting on its own or does it hang off the tree we already have
14:07  dermot: it subclasses AttachmentError, like the rest of them
14:08  ilse: does that get us anything though, the callers i'm thinking of dont catch AttachmentError anywhere
14:10  dermot: AttachmentError is a ValueError, so the old ValueError handlers still catch it. nothing downstream has to change
14:11  ilse: huh, ok. thats not in the branch yet is it, i went looking earlier
14:12  dermot: no one's written it yet. we just know where it goes now
14:14  theo: so file_upload_limit_check basically never sees an oversized one after this
```

#### `g8.r1.s1-dario` — rule

**dario**, 2025-04-23, #pipeline

> we already have the base64 string in hand when the block gets built, so i'd weigh that rather than decoding, and hang size_mb off the block as a plain float.

*What a reader should take from it:* the team agrees the size is derived from the base64 text at block-build time and stored on the block

*Step it builds toward:* `g8.r1.s1` — Each base64 attachment gets its own size in megabytes computed from the base64 text and recorded on the block, and that size is compared against a ceiling that differs by kind (tighter for images than for documents), with a dedicated attachment error naming the kind, the measured size and the ceiling it broke; this happens while the block is being built, ahead of the provider's own upload hook.

*Drafted as:* we already hold the base64 text when the block gets built, so weigh that string right there and hang size_mb off the block instead of decoding anything back.

*Why there:* None of the eight rooms is anywhere near this. The two engineering threads are about model-name pattern matching and cache-key/env-var behaviour; the pipeline thread is about persisting batch job ids; incidents is about a double-submitted batch and an unwritable cache dir; the code-review threads are about PR state and the schema_check construction hook; general is PR triage. Nobody in any of them has raised multimodal attachments, base64 blocks, or payload size at all, so a line about hanging size_mb off a block would change the subject and draw no reply. The natural home is #pipeline — the request layer, payload construction and per-provider limits — on a day where a run dies because an oversized image went into a request. The conversation that should exist: dermot reports a run rejected by the provider for an oversized attachment, emil asks where in the block-building path we'd catch it, dario answers that the base64 text is already in hand at build time, and a sibling message supplies the actual thresholds and the separate image vs document numbers.

*Still leaves open:* Does not give any threshold, any error, or the fact that images and documents are held to different numbers.

*Must appear literally:* `size_mb`

*A new conversation in #pipeline on 2025-04-23:*

```
10:18  nils: quick one on the image blocks - do we know how big any given attachment is once its in the payload?
10:21  dario: not recorded anywhere at the moment, no. we'd have to put it there
10:22  nils: we could decode it and len() the bytes, but thats a full copy of every image per request
10:26  dario: yeah thats the bit i'd avoid honestly. we already have the base64 string in hand at the point the block gets built, so i'd weigh that rather than decoding it back down
10:28  dermot: mhm. base64 length tracks the real bytes closely enough for what we want out of it
10:30  nils: ok. and where does the number actually live, some metadata dict under the block?
10:33  dario: no, nothing nested. just hang it off the block itself, size_mb, plain float
10:35  nils: works, i'm in the block constructor for other reasons anyway
10:37  dermot: that said, blocks get built in two places on the encoder path last i looked
```

#### `g8.r1.s1-emil` — rule

**emil**, 2025-04-29, #pipeline

> from the run: `image attachment is 21.3 MB, over the 20.0 MB limit.` documents shouldn't sit on that number. and it's strictly over - exactly 20.0 goes through fine.

*What a reader should take from it:* the team agrees images and documents get different ceilings, 20 and 24 megabytes

*Step it builds toward:* `g8.r1.s1` — Each base64 attachment gets its own size in megabytes computed from the base64 text and recorded on the block, and that size is compared against a ceiling that differs by kind (tighter for images than for documents), with a dedicated attachment error naming the kind, the measured size and the ceiling it broke; this happens while the block is being built, ahead of the provider's own upload hook.

*Drafted as:* from the run: `image attachment is 21.3 MB, over the 20.0 MB limit.` documents should not be on that number, anthropic takes pdfs to 24 quite happily.

*Why there:* None of the candidate days are chewing on attachment payload limits. The closest is #pipeline 2025-04-23, but that day is entirely the cache-fingerprint/job-record gap; multimodal-prompts gets one "holding, nothing urgent" line at 09:00 and never comes back, so a run error about a 21.3 MB image would change the subject and draw no reply. The other candidates are viewer null-cost, PR triage, and cookbook verifier scope — all wrong subject. What should exist is a #pipeline thread where someone's run dies on an oversized attachment and the team settles that images and documents get separate ceilings; that's the request layer and provider backends, which is that room's whole remit, and it's where the sibling remark about which class raises it and when it runs relative to the provider hook would naturally sit.

*Still leaves open:* Does not say what class raises it, where the number is computed or stored, or when it runs relative to the provider hook.

*Must appear literally:* `20.0`, `MB`, `image attachment is 21.3 MB, over the 20.0 MB limit.`

*A new conversation in #pipeline on 2025-04-29:*

```
14:47  dermot: the run last night came back with `image attachment is 21.3 MB, over the 20.0 MB limit.` — i haven't touched the attachment doc yet, do i quote that verbatim or keep it loose
14:52  emil: keep it loose i think. the docs shouldn't sit on that number, the error already says it at runtime
14:54  dermot: yeah ok. prose then, no figure in the text
14:56  gideon: wait what about something landing exactly on the line though? does that get rejected or no
14:59  emil: goes through fine. its strictly over — 20.0 on the nose is not over, so it passes
15:01  gideon: ya thats what i had in my head, just wanted someone to say it out loud
```

> **Problems:** longer than one remark

#### `g8.r1.say24` — rule

**nikolai**, 2025-05-06, #incidents

> AttachmentTooLarge(kind, size_mb, limit_mb) and it keeps all three as .kind .size_mb and .limit_mb so a test can asssert on them not scrape a traceback

*What a reader should take from it:* the team agrees AttachmentTooLarge takes and stores kind, size_mb and limit_mb in that order

*Step it builds toward:* `g8.r1.s1` — Each base64 attachment gets its own size in megabytes computed from the base64 text and recorded on the block, and that size is compared against a ceiling that differs by kind (tighter for images than for documents), with a dedicated attachment error naming the kind, the measured size and the ceiling it broke; this happens while the block is being built, ahead of the provider's own upload hook.

*Drafted as:* reading a traceback off it - AttachmentTooLarge(kind, size_mb, limit_mb), and it keeps all three as .kind, .size_mb and .limit_mb so a test can asssert on them.

*Why there:* None of the listed conversations is anywhere near attachment payloads or exception design. 2026-01-23, 2025-06-16, 2025-05-13 and 2025-04-11 are pure PR-status triage; 2025-06-03 and 2025-04-29 are about torch import guards and num_gpus scope; 2025-04-24 is tagging v0.1.7; 2025-05-07 mentions Emil's multimodal work but only as "is the prescription example in the suite yet" logistics — a constructor signature for a new error class would land there as a subject change nobody answers. The remark settles the shape of an exception raised when an image/PDF attachment exceeds what a provider will accept in a request payload, which is the request layer's problem, so it wants #pipeline, in a thread where Emil (who owns the multimodal workstream that just landed) is working out per-kind limits and Nikolai is pushing for a typed error instead of a provider 400 mid-run.

*Still leaves open:* what the limits are per kind, whether the comparison is strict, where the raise happens, and what the message text reads like

*Must appear literally:* `AttachmentTooLarge(kind, size_mb, limit_mb)`, `.kind`, `.size_mb`, `.limit_mb`

*A new conversation in #incidents on 2025-05-06:*

```
14:07  dermot: the oversize attachment test is still matching on the traceback text. broke again this morning
14:08  gideon: ya someone reworded the message. so what do we raise instead tbh
14:10  nikolai: our own one AttachmentTooLarge(kind, size_mb, limit_mb)
14:11  dermot: three args in. are those kept or just for building the message string
14:13  nikolai: kept .kind .size_mb .limit_mb so a test asserts on the fields and not the traceback
14:14  gideon: exactly what i was after. nobody has written it yet though right
14:15  nikolai: nope still the plain string today
14:16  dermot: yeah ok, so the wording can move around later and nothing cares
```

> **Problems:** longer than one remark

#### `g8.r1.say23` — rule

**nils**, 2025-06-02, #general

> let me think - the base64 text is what actually goes over the wire, so size_mb is just the length of that string over 1024*1024. no decoding first, and not 1000-based megabytes.

*What a reader should take from it:* the team agrees size_mb is the base64 character count divided by 1024*1024

*Step it builds toward:* `g8.r1.s1` — Each base64 attachment gets its own size in megabytes computed from the base64 text and recorded on the block, and that size is compared against a ceiling that differs by kind (tighter for images than for documents), with a dedicated attachment error naming the kind, the measured size and the ceiling it broke; this happens while the block is being built, ahead of the provider's own upload hook.

*Drafted as:* the base64 text is what the wire carries, so size_mb is just len of that string over 1024*1024 - no decoding first, and not 1000-based megabytes.

*Why there:* Neither candidate is anywhere near attachment payloads. The 3/19 #engineering day is about v0.1.21, the token-count fix and whether anyone re-ran the throttle check; the 3/25 #pipeline day is entirely PR 584's fixture coverage and the missing WS-047 scope. A settled definition of size_mb for base64 payloads answers nothing either room is chewing on and would get no reaction in either — it would read as nils changing the subject mid-thread. The right home is #pipeline, which owns provider backends and what gets shaped into a request, on a day where attachment support is actually being designed and someone has asked how the size is measured before the sibling remark pins down the ceilings and where the check runs relative to the provider hook.

*Still leaves open:* what the ceilings are, which kinds they differ by, what happens when one is exceeded, and where the check runs relative to the provider hook

*Must appear literally:* `size_mb`, `1024*1024`

*A new conversation in #general on 2025-06-02:*

```
11:18  konrad: quick one, size_mb on an attachment - is that the raw file or the encoded blob? off the top of my head i assumed raw
11:20  nikolai: the base64 text is what actually goes over the wire not the file on disk so that one
11:22  konrad: ok so do i decode it back and measure that, or just measure the string. and which megabyte
11:24  nils: let me think through that. just the string - size_mb is its length over 1024*1024, theres no decode step in front of it
11:25  konrad: so 1024 and not 1000
11:27  nils: 1024*1024, yes. the 1000-based megabyte reads smaller for the same payload and thats not the number we want to be carrying around
11:28  nikolai: yep thats the one i'd expect
11:29  konrad: right. my branch has 1e6 sitting in it, that part is coming back out
```

> **Problems:** longer than one remark

### g8.r1.s2 — A separate whole-prompt ceiling of 45 MB applies to the sum of the base64 block sizes, evaluated once in the prompt-assembly path after every attachment has been converted and every per-attachment provider hook call has run, raising the same exception type with the kind set to the prompt and the summed size.

*Nobody says:* Per-attachment ceilings can all pass while the assembled body is still too big, so the total has to be checked somewhere that sees all the blocks at once, which is the assembly step and not the single-attachment path.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g8.r1.s2-nils` — scope

**nils**, 2025-03-14, #code-review

> the base64 ones are what the wire actually carries, so the ceiling wants to be over those summed - 45 MB is about where they stopped accepting us

*What a reader should take from it:* the team agrees the whole-prompt ceiling is 45 megabytes over the summed base64 sizes

*Step it builds toward:* `g8.r1.s2` — A separate whole-prompt ceiling of 45 MB applies to the sum of the base64 block sizes, evaluated once in the prompt-assembly path after every attachment has been converted and every per-attachment provider hook call has run, raising the same exception type with the kind set to the prompt and the summed size.

*Drafted as:* the base64 ones are what the wire actually carries, and 45 MB is about where they stopped accepting us.

*Why there:* Neither #pipeline day fits. 2025-03-17 is entirely about the Mistral batch client, token usage shape and whether cost accounting accepts it; 2025-03-25 is about which provider fixture tests can be dropped before PR 584 merges. Nothing in either thread is chewing on request payload size, attachments, or provider size rejections, so a sentence about base64 sizes and a 45 MB ceiling arrives from nowhere and would get no reaction — and nils dropping it mid-review of test coverage would read as a plant. The remark belongs in #pipeline, which owns the request layer and every provider backend we talk to, but on a day the room is actually working out why large-attachment prompts get refused and what total to measure. That conversation should exist: a run dies with the provider refusing oversized requests, the team compares raw bytes against what's actually transmitted, and settles the whole-prompt ceiling before arguing separately about where the check lives.

*Still leaves open:* Does not say which function owns the total, what error comes out, or when it runs relative to the per-attachment work.

*Must appear literally:* `MB`

*A new conversation in #code-review on 2025-03-14:*

```
13:41  gideon: quick one on the size check for image payloads — do we measure the bytes we read off disk, or the encoded ones?
13:43  dario: the numbers we log right now are the decoded ones i think
13:45  nils: which is the wrong thing to gate on. the base64 ones are what the wire actually carries, so the ceiling wants to be over those
13:46  gideon: over each one or over the whole request tho
13:48  nils: summed. one of them fitting means nothing if four go out together
13:48  gideon: ok. and the ceiling sits where
13:50  nils: 45 MB is about where they stopped accepting us, so under that
13:52  dario: mhm that tracks. the batch that fell over last week was four smallish ones, none of them anywhere near the line on their own
```

#### `g8.r1.s2-gideon` — scope

**gideon**, 2025-03-17, #code-review

> so basically that total lives only in _handle_multi_modal_prompt - _format_multimodal still hands back both blocks for an over-45 set - and reusing the exception with kind prompt reads fine.

*What a reader should take from it:* the team agrees the whole-prompt check lives in the assembly step and reuses the same exception type with a prompt kind

*Step it builds toward:* `g8.r1.s2` — A separate whole-prompt ceiling of 45 MB applies to the sum of the base64 block sizes, evaluated once in the prompt-assembly path after every attachment has been converted and every per-attachment provider hook call has run, raising the same exception type with the kind set to the prompt and the summed size.

*Drafted as:* that total belongs in _handle_multi_modal_prompt, one check at the end, and the same exception with the kind set to prompt reads fine in a traceback.

*Why there:* None of the eight rooms is chewing on multimodal prompt assembly or payload size limits. The nearest, #code-review 2025-03-14, is about schema_check running at construction against the response_format spec — a different check, a different call site, and it ends unresolved on the offline question, so a settled ruling about `_handle_multi_modal_prompt` and an exception kind would arrive from nowhere there. #pipeline 2025-04-17 is structured-output accounting, #viewer is the metadata panel, #help is capability-lookup caching. The remark presumes a live thread about per-block limits vs a whole-prompt total and a shared exception type carrying a kind, which exists nowhere in the record. #pipeline is the right room to invent it in: it owns request construction and what each provider backend will accept.

*Still leaves open:* Gives no number for the total and does not say what is summed or which blocks are eligible.

*Must appear literally:* `_format_multimodal`, `_handle_multi_modal_prompt`, `prompt`

*A new conversation in #code-review on 2025-03-17:*

```
14:02  nikolai: where does the count for the multimodal case actually get checked
14:04  gideon: so basically that total lives only in _handle_multi_modal_prompt. nothing above it counts anything
14:06  nikolai: so _format_multimodal is clean then
14:08  gideon: no thats the part that bit us. it still hands back both blocks for an over-45 set, it just doesnt look
14:10  konrad: ok. so what do we throw at the check, a new error type?
14:12  gideon: honestly though reusing the exception with kind prompt reads fine, no need for a second one
14:14  konrad: mhm. i had half of a seperate one written yesterday, glad i stopped
```

#### `g8.r1.s2-dario` — scope

**dario**, 2025-03-18, #code-review

> mhm - so even for a prompt that busts 45, every attachment still gets its file_upload_limit_check call first; the whole-prompt number comes after all of them, not woven in between.

*What a reader should take from it:* the team agrees the prompt total is evaluated once, after every per-attachment provider hook call

*Step it builds toward:* `g8.r1.s2` — A separate whole-prompt ceiling of 45 MB applies to the sum of the base64 block sizes, evaluated once in the prompt-assembly path after every attachment has been converted and every per-attachment provider hook call has run, raising the same exception type with the kind set to the prompt and the summed size.

*Drafted as:* do the whole-prompt number after all the per-attachment hook calls have gone through, not woven in between them.

*Why there:* Nothing in the listed threads is chewing on attachment payloads at all. The nearest neighbour is #code-review 2025-03-14, but that hook argument is about schema_check running at construction vs per-request against a local model/format spec — a single object-level check with no per-item iteration, so "after all the per-attachment hook calls" has nothing to attach to and would read as a topic swap. #pipeline 2025-04-03 and 2025-04-23 are on batch record persistence and the cache fingerprint; #viewer 2025-04-14 is summary tables; #engineering 2025-05-01 is executor images. The remark presumes a live design discussion about a per-attachment provider hook and a whole-prompt total, which the corpus hasn't opened yet. That belongs in #pipeline, which owns provider backends, multimodal-prompts and token accounting — dermot is already tracking multimodal-prompts there, so a provider rejecting an over-size multimodal request would surface in that room, and dario, who has been the one calling ordering questions, would be the one to settle the sequencing.

*Still leaves open:* Says nothing about the ceiling, what gets summed, or the exception it raises.

*Must appear literally:* `45`, `calls`, `file_upload_limit_check`

*A new conversation in #code-review on 2025-03-18:*

```
14:12  gideon: quick one on the upload path - if a prompt is already busting 45, do we even bother checking the attachments one by one?
14:15  emil: we do, yeah. every attachment still gets its own file_upload_limit_check call, no short circuit anywhere in there
14:16  gideon: ok but then where does the whole-prompt one land? the trace i read looked like it was interleaved with them
14:19  dario: its after. all the per attachment calls go first, then the whole prompt number gets looked at once at the end
14:20  dario: nothing woven in between them, honestly i think thats just how the log lines flush
14:22  emil: yup, that lines up with what i saw when i stepped through it
14:23  gideon: ya ok. i was reading the trace as the order of operations, my bad
```

> **Problems:** claims verbatim 'calls' but does not contain it

#### `g8.r1.s2-konrad` — scope

**konrad**, 2025-03-19, #pipeline

> look, nine photos in one cookbook cell, every one of them under its own ceiling, and the request still came back rejected for body size. the per-attachment limit isn't catching this.

*What a reader should take from it:* the team agrees per-attachment ceilings do not stop an oversized assembled prompt

*Step it builds toward:* `g8.r1.s2` — A separate whole-prompt ceiling of 45 MB applies to the sum of the base64 block sizes, evaluated once in the prompt-assembly path after every attachment has been converted and every per-attachment provider hook call has run, raising the same exception type with the kind set to the prompt and the summed size.

*Drafted as:* nine photos in one cookbook cell, every one of them under its own ceiling, and the request still came back rejected for body size.

*Why there:* No listed conversation is on the request layer. The two #cookbooks days are about whether the SimpleStrat example runs and whether the conftest importorskip wrapper affects the code-execution verifiers; neither touches prompt assembly or provider rejections. The #engineering days are cost/throttle accounting, o3 structured output, and release tag format — a body-size rejection would arrive from nowhere in all of them. The remark is about a provider refusing an assembled request, which is exactly what #pipeline exists for. It should have been said the day Konrad's multimodal cookbook example started failing: he had been treating the per-image size check as sufficient, hits a rejection anyway, and someone else (Dario or Gideon, who own the request-building path) supplies the actual total, what gets summed into the body, and where a pre-flight check would have to sit.

*Still leaves open:* Gives no total, no idea what is summed, and does not say where such a check would live.

*A new conversation in #pipeline on 2025-03-19:*

```
14:02  petar: cookbook run came back rejected this morning, body size. the cell has nine photos in it
14:04  konrad: nine in one cell? and each is under the limit i assume
14:05  petar: yep checked all nine, every one of them under its own ceiling
14:06  dario: and it still bounced?
14:07  petar: still rejected for body size, yeah
14:09  konrad: look thats the answer then. the per-attachment limit isnt catching this. nine legal photos in one cell and the request is still too big
14:11  dario: so the per file gate stays, its just not the one that decides
14:12  konrad: right, it never was. we just did not notice untill nine of them landed in the same cell
```

> **Problems:** longer than one remark

### g8.r1.s3 — Blocks whose source is a remote URL are never measured at all: their recorded size is absent rather than zero, and they add nothing to the whole-prompt total.

*Nobody says:* We never hold the bytes for a link, so any number we put there would either require a network fetch or be made up, and neither belongs in a size check.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g8.r1.s3-konrad` — exclusions_or_crossover

**konrad**, 2025-03-14, #engineering

> look, for a url block we never hold the bytes, so size_mb stays empty and file_upload_limit_check never gets called on it - the hook only ever sees base64.

*What a reader should take from it:* the team agrees a url block records no size rather than a placeholder number

*Step it builds toward:* `g8.r1.s3` — Blocks whose source is a remote URL are never measured at all: their recorded size is absent rather than zero, and they add nothing to the whole-prompt total.

*Drafted as:* for a url block we never hold the bytes at all, so size_mb stays empty rather than a made-up zero.

*Why there:* Every listed candidate is about something else: PR triage (gemini parts key, GEPA null score, wind-down backlog), release notes coordination, or throttle/token-count fallout. The nearest miss is #viewer 2025-06-03, but that thread is about the viewer formatting a None cost from a pricing lookup, not about what an attachment payload block records for its size; Konrad has already closed his side there and Emil owns the open question, so this would arrive from nowhere and change the subject. Attachment payload assembly and the size accounting on it is request-layer work, which is #pipeline, and the sibling remark about the whole-prompt total and per-kind ceilings only makes sense in that same room.

*Still leaves open:* Does not say anything about the whole-prompt total or the per-kind ceilings.

*Must appear literally:* `file_upload_limit_check`, `size_mb`

*A new conversation in #engineering on 2025-03-14:*

```
13:06  dario: quick one before i go back to the manifest - are url blocks supposed to come back with size_mb empty, or is that a bug on my side
13:08  konrad: not a bug. for a url block we never hold the bytes, so theres nothing to measure, it stays empty
13:09  dario: mhm ok. so does the limit check just read it as nothing and wave it through, or
13:09  dario: passing with an empty field and not being looked at at all are pretty different for what i'm writing
13:11  konrad: the second one. file_upload_limit_check never gets called on a url block, it isnt a pass, it just doesnt happen
13:12  dermot: so the hook only ever sees base64 blocks, that's the whole of its input
13:14  konrad: right. thats the only kind that ever reaches it
13:15  dario: ok. i had empty pencilled in as zero somewhere in my head, going to go unpick that
```

#### `g8.r1.s3-nils` — exclusions_or_crossover, scope

**nils**, 2025-03-17, #engineering

> makes sense to me — a prompt that is twelve remote links has nothing of ours in the body, so those url blocks should be contributing nothing to the whole-prompt total.

*What a reader should take from it:* the team agrees url blocks contribute nothing to the whole-prompt total

*Step it builds toward:* `g8.r1.s3` — Blocks whose source is a remote URL are never measured at all: their recorded size is absent rather than zero, and they add nothing to the whole-prompt total.

*Drafted as:* a prompt that is twelve remote links has nothing of ours in the body, so it should not be adding up to anything either.

*Why there:* Neither candidate is chewing on prompt-side token accounting. The 2025-03-25 #code-review day is pure PR triage — who owns WS-047, which of 584/585/579 targets the release — and a remark about what url blocks contribute to a prompt total would land as a subject change with nobody to answer it. The 2025-03-19 #engineering day does touch cost accounting, but specifically the output-token count wrapping on long responses and whether that shifted the throttle path; Nils is occupied there with the api_key approach for Mistral batch and says nothing about estimation. The remark is input-side: how attachment/url blocks in a prompt roll up into the whole-prompt token total, which is exactly what #pipeline is for (token and cost accounting, every provider backend). It needs a conversation where someone is actually adding url/attachment blocks to the prompt estimator and asking what each block type records, so the sibling remark (what a link block records, where the total is checked) has somewhere to sit.

*Still leaves open:* Does not say what is recorded on a link block, nor what the total is or where it is checked.

*A new conversation in #engineering on 2025-03-17:*

```
14:02  gideon: quick one — what should a url image block count as in the prompt size estimate?
14:05  dermot: none of those bytes are ours. the body just carries the link
14:07  gideon: ya but we still hand back one number for the whole prompt. does the link push that up or not
14:12  nils: makes sense to me — nothing of ours in that body, so the url blocks should be contributing nothing to the whole-prompt total
14:14  gideon: so my case thats twelve remote links plus a line of text comes back as just the line of text
14:15  nils: yes. thats the assert. nothing in the estimator does it that way today
14:17  dermot: mhm, the walk still visits them last i looked
```

> **Problems:** longer than one remark

#### `g8.r1.s3-nikolai` — exclusions_or_crossover

**nikolai**, 2025-03-19, #code-review

> ran the branch locally and it's pulling down remote images just to weigh them, so my unit tests started reaching for the network, which i'd rather they didnt

*What a reader should take from it:* the team agrees remote attachments are not fetched in order to size them

*Step it builds toward:* `g8.r1.s3` — Blocks whose source is a remote URL are never measured at all: their recorded size is absent rather than zero, and they add nothing to the whole-prompt total.

*Drafted as:* the branch was pulling down remote images just to weigh them and my unit tests started reaching for the network, which i would rather they did not.

*Why there:* All eight candidates are triage threads — who reviews which PR number, which curator-sandbox tag is pinned, where the plan doc lives. None of them is chewing on attachment payload sizing, and the one adjacent mention (PR 651, "multimodal model update", 2025-04-29) is a PR nobody actually reviewed that day; a concrete review finding about remote image fetches would arrive from nowhere and get no reaction. The remark is a live design point about how the request layer measures attachment payloads, which belongs in #pipeline — the room that owns request payloads, token and cost accounting, and provider backends — in a thread where someone is adding attachment size tracking and Nikolai has actually run the branch's tests.

*Still leaves open:* Does not say what the recorded size should be for a link, or whether links count toward any total.

*A new conversation in #code-review on 2025-03-19:*

```
13:39  dario: has anyone actually pulled that branch down and run it, or are we all just reading the diff
13:41  nikolai: i ran the branch locally last night
13:42  konrad: and? what did you see
13:44  nikolai: it goes and pulls the remote images down just to weigh them thats all it wants from them
13:45  dario: wait, weigh them as in the size? it downloads the whole thing for that
13:46  konrad: mhm that would explain why my run sat there
13:47  nikolai: yep and the knock on is my unit tests started reaching for the network which i'd rather they didnt
```

#### `g8.r1.s3-emil` — exclusions_or_crossover

**emil**, 2025-03-20, #code-review

> let me think through that - we were measuring the signed url string itself against the image ceiling, which is nonsense. url blocks skip the per-kind ceilings and file_upload_limit_check entirely.

*What a reader should take from it:* the team agrees url-sourced blocks must not be compared against the per-kind ceilings

*Step it builds toward:* `g8.r1.s3` — Blocks whose source is a remote URL are never measured at all: their recorded size is absent rather than zero, and they add nothing to the whole-prompt total.

*Drafted as:* a long signed url tripped the image ceiling because we were measuring the url string itself, which is nonsense.

*Why there:* None of the eight candidates is discussing attachment/multimodal payloads or per-kind size ceilings. The viewer, cookbooks, and code-review threads are on local-viewer removal, SimpleStrat/CodeExecutor, schema_check at construction, stopping criterion, PR ordering, and the dataset_not_ready response — a signed-URL sizing bug arrives from nowhere in all of them. #help 2025-04-21 is a perf thread (per-request capability lookup, 40k duplicate debug lines), and #engineering 2025-03-19 only brushes token counting via the output-token wrap fix and throttling; neither is about how a content block's size is measured. The right room is #pipeline, which owns the request layer and everything we send to provider backends — that's where a validation failure on an image block passed as a URL would get raised and where the call that URL-sourced blocks are exempt from the per-kind ceilings would be made. Emil is a plausible speaker there (he's the one who traces a symptom back to what the code is actually measuring, as with the 40k-lines-means-one-log-call-per-request read), and the sibling remark about what gets recorded instead and how links count toward the whole-prompt total is the natural next message from Gideon or Nikolai.

*Still leaves open:* Does not say what should be recorded instead, or how links behave in the whole-prompt total.

*Must appear literally:* `file_upload_limit_check`

*A new conversation in #code-review on 2025-03-20:*

```
15:31  konrad: quick one, a url image block got rejected as too big overnight. there is no image in it, it is a link
15:33  dario: the signed url one? honestly i saw the same thing on my side and assumed it was the fetcher
15:34  konrad: not the fetcher. presumably we are counting the wrong thing somewhere before that
15:38  emil: let me think through that - we were measuring the signed url string itself against the image ceiling, which is nonsense. long token, long url, over it goes
15:40  dario: ok so what does a url block get instead, its own ceiling or nothing at all
15:42  emil: nothing. url blocks skip the per-kind ceilings and file_upload_limit_check entirely
15:44  konrad: right, so on that path there is nothing to weigh in the first place
15:46  dario: mhm, that tracks with the overnight one. it never had bytes in hand to be big with
```

### g8.r1.s4 — The number of attachments on a prompt is capped at twelve by a module constant, checked first thing in the prompt-assembly path so that nothing is serialized and no provider hook is called when the count is over; the dedicated error carries the count and the cap, and only attachments count, not texts.

*Nobody says:* If the complaint is the work done before the refusal, the count check has to come before any serializing or hook call, and a count is the only thing you can know that early.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g8.r1.s4-gideon` — failure_behavior

**gideon**, 2025-03-14, #code-review

> notebook handed us sixty images, we base64'd each one and passed that string itself into file_upload_limit_check before anything gave up. so basically the guard runs ahead of all that

*What a reader should take from it:* the team agrees an over-long attachment list must not be serialized or sent through the provider hook first

*Step it builds toward:* `g8.r1.s4` — The number of attachments on a prompt is capped at twelve by a module constant, checked first thing in the prompt-assembly path so that nothing is serialized and no provider hook is called when the count is over; the dedicated error carries the count and the cap, and only attachments count, not texts.

*Drafted as:* notebook handed us sixty images and we base64'd every single one and called file_upload_limit_check on each of them before anything gave up.

*Why there:* That thread is already arguing about when a validation hook should fire and whether it has to reach the provider at all — Dario's notebook that came back "happy" at construction and blew up twenty minutes into the map, Emil asking whether schema_check needs an outbound path or is purely local. Gideon has already bought into the construction-hook framing at 12:45 ("hard to argue with a 20-minute blowup that was already broken on return"), so a second concrete case from him — an over-long attachment list that got fully base64'd and pushed through file_upload_limit_check per image before anything failed — extends his own burst rather than changing the subject, and it complicates Emil's local-vs-provider question by showing a check that does reach out, once per item. It settles the ordering (guard first, before serialization and before the hook) without touching the cap, the error, or what the check counts.

*Still leaves open:* Gives no cap, no error, and does not say the check is on the number of attachments rather than their size.

*Must appear literally:* `file_upload_limit_check`

*Goes into the real conversation in #code-review on 2025-03-14, after 12:46 gideon:*

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
11:50  dario: PR 565 is in decent shape at this point, would take a review pass if anyone has cycles this afternoon, and PR 566 is close behind it so they'll probab
12:17  emil: @Dario when schema_check runs at construction, does it need to reach the provider at all, or is it purely off the local config?
12:17  emil: Asking because local-offline-inference has no outbound path and I want to know if it can even honour the check
12:45  gideon: That notebook sequence is a solid motivator for the construction hook, hard to argue with a 20-minute blowup that was already broken on return
12:46  gideon: So local config meaning it inspects the model spec fields, not makes a test call out?   <-- THE REMARK GOES HERE
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

#### `g8.r1.s4-konrad` — failure_behavior

**konrad**, 2025-03-19, #engineering

> look, _ATTACHMENT_COUNT_LIMIT stays at 12 and texts don't count toward it - twelve is fine, thirteen is not. a cell with forty text chunks and one image is normal, nowhere near it.

*What a reader should take from it:* the team agrees the cap is twelve attachments, texts excluded, with twelve itself allowed

*Step it builds toward:* `g8.r1.s4` — The number of attachments on a prompt is capped at twelve by a module constant, checked first thing in the prompt-assembly path so that nothing is serialized and no provider hook is called when the count is over; the dedicated error carries the count and the cap, and only attachments count, not texts.

*Drafted as:* _ATTACHMENT_COUNT_LIMIT at 12, twelve is fine and thirteen is not; a cell with forty text chunks and one image is normal and should not go near it.

*Why there:* None of the candidate days are anywhere near this subject. 2025-05-30 and 2025-06-03 in #code-review are review-queue triage (PRs 652/653/663/681/683), 2026-01-02 is end-of-week PR carryover, 2025-04-11 in #incidents is the post1 announcement, and the two #cookbooks days are the examples table columns and the SimpleStrat/RAFT run. The closest is #engineering 2025-05-21, but that thread is the agent response shape (plain dict vs wrapped, issue 293, usage metadata) — a cap on attachments per cell would change the subject there and nobody would pick it up. Multimodal prompt construction is Emil's area (he flags multimodal-prompts on 05-21) and there is no channel dedicated to it, so a validation constant like this gets argued in #engineering, which is exactly the room for "design arguments and half-formed plans that haven't found a narrower channel." The sibling remark (error name, what it carries, how early the check runs) is the other half of the same design thread, so the conversation needs to be one where both land naturally — konrad settling the number, someone else settling the failure mode.

*Still leaves open:* Does not name the error, say what it carries, or say how early the check runs.

*Must appear literally:* `_ATTACHMENT_COUNT_LIMIT`

*A new conversation in #engineering on 2025-03-19:*

```
13:38  gideon: what does the attachment cap actually count, every part in the cell or only the real attachments?
13:40  konrad: only attachments. look, _ATTACHMENT_COUNT_LIMIT is 12 and it stays at 12, i see no reason to move it
13:41  gideon: ok but i have cells with a ton of text chunks in them. do those eat into the twelve or not
13:43  konrad: no. texts dont count toward it at all
13:44  dermot: so forty text chunks and one image in one cell, thats fine as far as the cap is concerned?
13:46  konrad: that one is normal, nowhere near it. twelve is fine, thirteen is not, and that cell has one
13:48  dermot: yeah ok. so the thing that got rejected yesterday genuinely had thirteen files in it
```

> **Problems:** longer than one remark

#### `g8.r1.s4-nikolai` — failure_behavior

**nikolai**, 2025-03-20, #engineering

> ran it against the 31 image prompt and got `Prompt has 31 attachments, over the limit of 12.` which is exactly what i wanted to see instead of the memory spike

*What a reader should take from it:* the team agrees the refusal message states the attachment count and the cap

*Step it builds toward:* `g8.r1.s4` — The number of attachments on a prompt is capped at twelve by a module constant, checked first thing in the prompt-assembly path so that nothing is serialized and no provider hook is called when the count is over; the dedicated error carries the count and the cap, and only attachments count, not texts.

*Drafted as:* got `Prompt has 31 attachments, over the limit of 12.` which is exactly what i wanted to see instead of the memory spike.

*Why there:* None of the eight candidates is anywhere near this subject. They are PR-state archaeology (2025-04-04, 04-08, 04-15), release-notes coordination (05-06), maintenance-mode planning (06-25), sandbox/viewer questions (05-30), GEPA null scores (2026-01-27), and `backend_params` defaulting (04-21). The closest, 04-21, is about unvalidated backend param keys, not prompt payload size or a memory spike — a refusal message for an attachment cap would change the subject there and draw no reaction. This remark is someone confirming a just-added guard in the request path, so the natural home is #pipeline, which owns request construction, payloads and provider backends, in a thread that starts from the run that blew up memory on prompts carrying dozens of images and ends with a cap that refuses instead of ballooning.

*Still leaves open:* Does not name the exception class or say what fields it holds, nor where in the path it is raised.

*Must appear literally:* `Prompt`, `limit`

*A new conversation in #engineering on 2025-03-20:*

```
16:02  dermot: the 31 image prompt from last week, the one that spiked. did anyone put it through the count up front yet or is that still just talk
16:04  nikolai: ran it against the 31 image prompt this morning
16:06  konrad: and what did it do
16:08  nikolai: stopped immediatly one line thats it
16:09  konrad: one line saying what though, does it give you the number or just a trace
16:11  nikolai: `Prompt has 31 attachments, over the limit of 12.` whole message
16:13  dermot: mhm so nothing climbed at all. that lands in the payload builder then, none of which is written
16:14  nikolai: nothing climbed no thats exactly what i wanted to see out of it instead of the memory spike
16:16  konrad: right so the count sits at the top, before we hand it anything. settled as far as im concerned
```

> **Problems:** longer than one remark

#### `g8.r1.s4-dario` — failure_behavior

**dario**, 2025-03-24, #engineering

> i think TooManyAttachments carries the count and the ceiling it broke, another AttachmentError subclass like AttachmentTooLarge, and it fires before we serialize a single one of them

*What a reader should take from it:* the team agrees the dedicated error holds the count and the cap and is raised before any serialization

*Step it builds toward:* `g8.r1.s4` — The number of attachments on a prompt is capped at twelve by a module constant, checked first thing in the prompt-assembly path so that nothing is serialized and no provider hook is called when the count is over; the dedicated error carries the count and the cap, and only attachments count, not texts.

*Drafted as:* TooManyAttachments should carry the count and the ceiling it broke, and it has to fire before we serialize a single one of them.

*Why there:* None of the seven candidate conversations touches attachments, payload construction, or error types at all — they're about cache-key invalidation and env vars (#engineering 04-18), PR sequencing and review sign-off (#code-review 03-20, 04-04, 04-10), a swallowed cache-write exception (#code-review 04-24), local-vs-hosted viewer and the metadata panel's report object (#viewer 03-27, 04-28), and `.choices` migration in the cookbooks (#cookbooks 05-05). Dropping a settled decision about a `TooManyAttachments` error class into any of them changes the subject with nothing before or after it. The closest neighbour is the 04-24 thread on error paths in bulk-llm-inference, but that one is specifically about a bare `pass` in a cache write, and dario's only contribution there is a "+1" — a design ruling on attachment caps would sit oddly. Attachment limits live in the request layer: building a provider payload, validating before serialization, failing with a typed error. That's #pipeline by its stated purpose (online requests, provider backends, what we send). The conversation that should exist is someone hitting a provider-side rejection after the client happily base64'd a pile of files, and the team deciding the check moves in front of the serialization step and the error carries the numbers.

*Still leaves open:* Does not give the cap itself, the message wording, or whether texts are included in the count.

*Must appear literally:* `AttachmentError`, `AttachmentTooLarge`, `TooManyAttachments`, `count`

*A new conversation in #engineering on 2025-03-24:*

```
14:12  nikolai: whats the error when someone hands us more attachments than we allow
14:14  dario: TooManyAttachments i think. it carries the count they sent plus the ceiling it broke, so nobody has to go count them by hand off a stack trace
14:15  nikolai: brand new exception or does it hang off something
14:16  dario: another AttachmentError subclass, same shelf as AttachmentTooLarge
14:18  gideon: ok but when does it fire tho, after we built the payload?
14:20  dario: no, before we serialize a single one of them. honestly no point encoding a pile we are going to reject anyway
14:21  gideon: ya ok, and we know how many there are before any of that so its cheap
14:22  nikolai: right and the test doesnt need real bytes then just a long enough list
```

### g8.r1.s5 — The token estimator prices file and document blocks at a flat 1400 tokens via its own module constant, alongside the existing per-image constant.

*Nobody says:* Documents currently contribute nothing to the estimate, and the fix mirrors how images are already priced: one flat number per block.

*4 remarks — 1 reporting the problem, 3 settling the design.*

#### `g8.r1.s5-gideon` — observability

**gideon**, 2025-05-02, #pipeline

> honestly though, while I was poking at the same path - my anthropic run counted 85 per image and zero for the two document blocks, so the estimate is only half the mesage.

*What a reader should take from it:* the team agrees document blocks are currently priced at nothing by the estimator

*Step it builds toward:* `g8.r1.s5` — The token estimator prices file and document blocks at a flat 1400 tokens via its own module constant, alongside the existing per-image constant.

*Drafted as:* my anthropic run counted 85 per image and zero for the two document blocks, so the estimate is only half the message.

*Why there:* That thread is already deep in Anthropic multimodal content blocks — emil and dermot just settled that PR 656 only fixed the content block *structure*, not "all the formatting cases." Gideon, who opened the day asking what the fix actually covers, adding that his own Anthropic run priced images at 85 each and the two document blocks at zero lands as the next gap on the same path, in the room that owns token and cost accounting. Nothing above it has made the point, and it doesn't say what a document ought to cost.

*Still leaves open:* Does not say what a document should cost or where the number would live.

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

> **Problems:** longer than one remark

#### `g8.r1.say25` — observability

**dario**, 2025-05-05, #cookbooks

> i think an unknown block kind - a thinking block say - just contributes zero to the estimate, we dont raise on it and we don't charge its text either

*What a reader should take from it:* the team agrees an unrecognised block type contributes zero tokens rather than raising or being charged its text length

*Step it builds toward:* `g8.r1.s5` — The token estimator prices file and document blocks at a flat 1400 tokens via its own module constant, alongside the existing per-image constant.

*Drafted as:* i think an unknown block kind - a thinking block, say - just contributes zero to the estimate. we don't raise on it and we don't charge its text.

*Why there:* The #cookbooks 2025-05-05 thread is about auth docs sign-off and which cookbooks still reference the old `.choices[0].message.content` response shape — a docs-triage problem. This remark settles how a token estimator treats an unrecognised content block, which is request-layer token/cost accounting, not example-corpus upkeep; dropping it after dermot's `.choices` grep would change the subject and get no reaction. #pipeline is the room that owns token and cost accounting for payloads, and the sibling remark (image/file/document block cost, return type) clearly belongs to the same estimator discussion there.

*Still leaves open:* says nothing about what image, file or document blocks cost, or what type the estimate comes back as

*Must appear literally:* `thinking`

*A new conversation in #cookbooks on 2025-05-05:*

```
14:02  konrad: quick one, what happens in the token estimate when a block kind isnt one we handle
14:04  dermot: not entirely sure. if i had to guess it hits the else and raises
14:06  konrad: thats what i was afraid of. a thinking block coming back would take the whole estimate down with it
14:10  dario: honestly i think it just contributes zero and we carry on, we dont raise on it
14:11  konrad: ok. and the text sitting inside it, that still counts toward the number?
14:13  dario: no we dont charge its text either. the block is zero, contents and all
14:15  dermot: yeah ok. simpler than i had it in my head
```

#### `g8.r1.s5-dermot` — observability

**dermot**, 2025-05-06, #releases

> yeah ok - _OPENAI_TOKENS_PER_DOCUMENT beside the image constant, flat number whether it comes in as file or document. the image one is 85 for an image_url block, same as anthropic's.

*What a reader should take from it:* the team agrees file and document blocks are priced by a flat module constant like images are

*Step it builds toward:* `g8.r1.s5` — The token estimator prices file and document blocks at a flat 1400 tokens via its own module constant, alongside the existing per-image constant.

*Drafted as:* add _OPENAI_TOKENS_PER_DOCUMENT beside the image constant, same idea, one flat number per block whether it came in as a file or a document.

*Why there:* All three candidates are about something else entirely. The 2025-05-07 #code-review thread is about pinning a curator-sandbox tag in CI; the 2025-06-26 #pipeline thread is about whether streaming shares the auto-batch routing path and how cache invalidation behaves; the 2025-05-13 #pipeline thread is about leftover logger.warning calls in the provider/request layer. A ruling on how file and document content blocks get priced — a flat module constant sitting next to the image constant — answers nothing any of those rooms is chewing on, and in each case it would arrive with no one having asked and no one able to react. It does belong in #pipeline, which owns token and cost accounting and every provider backend, but it needs its own thread: someone adds PDF/file input on the OpenAI side, the token estimator has no branch for the new block types, and the cost numbers come out wrong, at which point dermot settles the naming and the shape of the fix. That conversation would also cover whether the anthropic and openai estimators stay symmetric, since he's reaching for the anthropic image number as the precedent.

*Still leaves open:* Does not give the number itself, nor the symptom that made it necessary.

*Must appear literally:* `85`, `_OPENAI_TOKENS_PER_DOCUMENT`, `image_url`

*A new conversation in #releases on 2025-05-06:*

```
15:02  konrad: Quick one on the openai cost estimate. Do we have anything for pdfs there or is it only the image constant right now
15:05  dermot: only the image one at the moment. we'd sit a sibling next to it, _OPENAI_TOKENS_PER_DOCUMENT
15:07  konrad: And that scales per page? Also some of these arrive as a file block not a document one, presumably that changes the lookup
15:09  dermot: no, flat number whether it comes in as file or document. same value both ways, we are not counting pages
15:10  konrad: right. anyway what is the image one set to, I never actually looked at it
15:12  dermot: 85 for an image_url block. same as anthropic's
15:14  nikolai: yep and nobody has ever argued with that number on the anthropic side so
```

#### `g8.r1.s5-emil` — observability

**emil**, 2025-05-30, #releases

> let me think through that - anthropic puts a pdf page near 1400 tokens, so we charge 1400 flat for each document block. the total comes back a plain int.

*What a reader should take from it:* the team agrees the flat charge per document block is 1400 tokens

*Step it builds toward:* `g8.r1.s5` — The token estimator prices file and document blocks at a flat 1400 tokens via its own module constant, alongside the existing per-image constant.

*Drafted as:* a pdf page runs about 1400 tokens by anthropic's own numbers, close enough to charge that flat for each one.

*Why there:* This is a token-accounting decision for multimodal requests — how many tokens a document/PDF block costs and what the counter returns. None of the listed rooms is chewing on that. #pipeline on 2025-06-26 is entirely streaming routing and cache invalidation for PR 693; dropping a per-document-block token charge there changes the subject mid-thread. #engineering 2025-05-21 mentions "token counts" only as a question about whether usage metadata belongs in the agent response shape, which is a different argument (what the response carries, not how we estimate a PDF). #viewer 2025-07-10 is version-tag rendering, #releases and #cookbooks are tagging and examples, #incidents is the structured-output revert. The right home is #pipeline — token and cost accounting for provider backends — but on a day where the token estimator for multimodal prompts is actually the topic. Emil owns multimodal-prompts and PR 691 is his batch/multimodal work, so he'd be the one answering, and this is exactly the kind of "let me think through that" restate-then-commit he does.

*Still leaves open:* Does not say what the constant is called or that anthropic-shaped document blocks are covered too.

*Must appear literally:* `1400`

*A new conversation in #releases on 2025-05-30:*

```
13:52  konrad: the counter fell over on a pdf attachment yesterday. what do we count a document block as, off the top of my head we never picked a number
13:56  emil: let me think through that - anthropic puts a pdf page near 1400 tokens, so thats the number we work from
13:57  konrad: per page? we dont have the page count in hand at that point
14:00  emil: no, flat. 1400 for each document block, we dont open the file to look
14:02  dario: and what does the total come back as, i had it pencilled as a float in my head for some reason
14:04  emil: plain int, nothing wrapped round it
14:06  konrad: mhm. so a two page pdf and a two hundred page one land on the counter the same
14:07  emil: yup. untill someone hands us a page count thats where we are
```

### Herrings — believed at the time, overturned later

#### `g8.r1.g8-pre-r1-single-ceiling-dario` — herring

**dario**, 2025-01-21, #releases

> one ceiling, 20 mb, same number for images and documents — and honestly the provider's file_upload_limit_check runs first, ours only speaks once that hook clears.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* one ceiling, 20 mb, same number for images and documents, and the provider's file_upload_limit_check runs first — our check only speaks after the hook clears it.

*Why there:* None of the candidate days are about attachment payloads or upload validation. The closest is #pipeline 2025-02-03, where emil asks about multimodal scoping and dario confirms image serialization goes in the pipeline layer before the online request loop — but that thread is about ordering of work, not size ceilings, and it never touches documents or a provider-side hook. Dropping a settled 20 MB limit and the file_upload_limit_check ordering into that day would change the subject mid-thread and draw no reaction. The remark needs the conversation where the image path was being widened to documents and someone asked whether each attachment kind gets its own ceiling and who validates first — us or the provider. That belongs in #pipeline, which owns the request layer and every provider backend, with emil (now on provider-integrations, and the one who scoped multimodal off dario's handover) asking and dario, who scoped the original serialization path, answering.

*A new conversation in #releases on 2025-01-21:*

```
15:22  konrad: quick one on the attachment cap - is it one number, or do images and documents each get their own?
15:24  dermot: if i had to guess one, but i've only ever seen it come up for images
15:26  dario: one ceiling. same number for images and documents, i don't think theres a good reason to split it
15:27  konrad: ok. what is the number
15:28  dario: 20 mb
15:31  dermot: and when something comes in over that, we're the ones rejecting it? or is that upstream
15:34  dario: honestly the provider's file_upload_limit_check runs first. ours only speaks once that hook clears, so we're the second word not the first
15:36  dermot: yeah ok. that would explain why the one from last night came back in their wording and not ours
15:38  konrad: mhm. i went looking in our code for where it rejects and could not find it, presumably because nobody put it there yet
```

#### `g8.r1.g8-pre-r1-single-ceiling-konrad` — herring

**konrad**, 2025-01-22, #cookbooks

> right, settled the ordring: file_upload_limit_check runs first, then the shared 20 MB ceiling. one limit covers every kind, no per-kind numbers.

*A herring: stated as settled at the time, overturned later (from 2025-03-14).*

*Drafted as:* Settled on the ordering: file_upload_limit_check goes first, then the shared 20 MB ceiling. One limit covers every kind, no per-kind numbers.

*Why there:* None of the candidate threads is chewing on attachment size limits. The closest, #engineering 2025-03-11, is about mime-type defaults for Image types and whether providers regress on a guessed format — it never touches payload size, a provider hook, or a shared ceiling, so a decision naming `file_upload_limit_check` and 20 MB would land from nowhere and draw no reaction. The code-review threads are PR-triage (438/439/430, 547, 378/387/362) and the Feb engineering ones are release scope and multimodal edge-case sign-off. Size ceilings on attachments sent to providers are request-layer and provider-backend territory, which is #pipeline's stated purpose; that is where the ordering of a per-provider limit hook against a shared ceiling would actually be argued out, most naturally in the days right after the mime-type work made attachments flow through to providers.

*A new conversation in #cookbooks on 2025-01-22:*

```
15:31  dermot: on the upload path — does file_upload_limit_check run before the size ceiling, or after? i had the ceiling going first in my head
15:33  konrad: before. the check runs first, then the celing after it
15:35  dermot: ok. and the ceiling itself, one number or one per kind?
15:36  konrad: one. 20 MB, covers every kind, no per kind numbers anywhere
15:38  dario: so nothing in there keys off the file type at all, it's just the one gate
15:39  konrad: right
15:42  nikolai: yep thats the order the docstring already implies fwiw nobody wrote it down as such
```

#### `g8.r1.rev1` — rule

**dario**, 2025-03-31, #releases

> 22 mb pdfs anthropic takes happily kept bouncing on the shared 20 mb ceiling. it's 20.0 for image blocks, 24.0 for document, and AttachmentTooLarge fires in _canonical_attachment_block before file_upload_limit_check.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* the single 20 mb ceiling for both kinds is gone - 22 mb pdfs anthropic takes happily kept bouncing. it's 20.0 for image blocks, 24.0 for document, and AttachmentTooLarge fires inside _canonical_attachment_block before file_upload_limit_check, not after.

*Why there:* The remark settles how attachment size validation works in the payload construction path — per-kind ceilings, and ordering against the provider's own limit hook. That is request-layer/provider-backend territory, i.e. #pipeline, but none of the candidate #pipeline days is anywhere near it: 2025-03-24 is batch id persistence and resume, 2025-04-10 is DeepSeek 429 headers and PR 624 log removal, 2025-04-15 is cost streaming and Gemini response shapes. #code-review 2025-04-22 is the closest by vocabulary only — PR 651 is described as "multimodal support model updates in openai, ref change", a model-list/ref bump, and dario's only line there is "+1 on 649"; dropping a decided per-kind ceiling plus an exception-ordering detail into that thread would change the subject and draw no reply. #cookbooks and #engineering are wrong by purpose. What should exist is a #pipeline thread a couple of days after the multimodal PR work, where dario is the one who hits it: he is the person in this corpus who finds things by running real workloads and reports them days later (the apt-get entrypoint, the overwritten CSV, the lost 12hr batch), so 22 MB PDFs that Anthropic accepts bouncing on our own shared 20 MB ceiling is exactly his kind of find. The thread would also cover which providers publish which limits, and whether our ceiling should defer to file_upload_limit_check at all rather than pre-empting it — with dermot asking the framing question and emil confirming what the provider actually accepts.

*Must appear literally:* `AttachmentTooLarge`, `_canonical_attachment_block`, `file_upload_limit_check`, `20.0`, `24.0`

*A new conversation in #releases on 2025-03-31:*

```
15:38  konrad: quick one before it falls off my list. the 22 mb pdf from the support thread — that bounced on our side, not anthropic's. they take that size happily
15:39  konrad: and we have had one attachment ceiling, 20 mb, same number for images and documents, since forever
15:41  dario: ya thats the part thats gone. the one shared ceiling is dead, we're splitting it by block type. 20.0 for image blocks, 24.0 for document
15:43  dermot: so a 22 mb pdf goes through and a 22 mb png still does not?
15:44  dario: correct
15:45  konrad: what about the ordering though. my memory of what we agreed was we let the provider's file_upload_limit_check clear and only speak after that hook passes
15:47  dario: thats the other half thats being dropped, and honestly it was backwards. AttachmentTooLarge fires in _canonical_attachment_block, before file_upload_limit_check. waiting on the provider hook meant we sat there and then complained about a size the provider was perfectly fine with, which is exactly how the 22s kept bouncing
15:49  dermot: yeah ok. matches the ticket then, nothing anthropic-side ever rejected those. we told them to split the file for no reason
```

> **Problems:** longer than one remark

#### `g8.r1.rev2` — rule

**konrad**, 2025-03-20, #cookbooks

> look, the ordering I settled on is dead - AttachmentTooLarge raises inside _canonical_attachment_block ahead of file_upload_limit_check now, and the block's own kind field picks the ceiling: image 20.0, document 24.0.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* The ordering I settled on is dead - file_upload_limit_check no longer goes first, and there's no one shared 20 MB number. AttachmentTooLarge raises inside _canonical_attachment_block ahead of the hook, 20.0 MB for image kind, 24.0 for document.

*Why there:* Every listed candidate is about something else entirely — cookbook examples and verifier CI, the viewer's local-vs-hosted question, release notes for v0.1.23, agentic-curation factory cleanup, stopping criterion sign-off. None of them has attachments, multimodal payloads, provider upload limits, or _canonical_attachment_block anywhere in the thread, so the remark would arrive from nowhere and go unanswered. It belongs in #pipeline, which is explicitly the request layer and every provider backend we talk to: that room is where a shared 20 MB ceiling would have been agreed in the first place and where reversing it to per-kind limits is news people act on. Konrad is the right speaker — he is reporting that an ordering he himself settled no longer holds, which is the kind of self-correction he does elsewhere in these logs ("honestly, I'm not sure it was").

*Must appear literally:* `20.0`, `24.0`, `AttachmentTooLarge`, `_canonical_attachment_block`, `file_upload_limit_check`, `kind`

*A new conversation in #cookbooks on 2025-03-20:*

```
13:31  dermot: quick one on attachments - is the size check still the last thing before handoff? reading the encoder path and it doesn't match what i remember
13:33  konrad: it moved. look, the ordring we agreed back whenever is dead - file_upload_limit_check runs first, then the one shared 20 MB ceiling covering every kind, no per-kind numbers. thats gone
13:34  konrad: the single ceiling was bouncing documents the provider takes without complaint
13:36  dermot: so what raises now, and where
13:37  konrad: AttachmentTooLarge, inside _canonical_attachment_block, ahead of file_upload_limit_check
13:39  dermot: still one number though? or - restating, the block knows what it is by then, so if i had to guess it picks its own
13:40  konrad: right. the kind field on the block picks the ceiling. image 20.0, document 24.0
13:44  dario: mhm, that tracks. i have a pdf in the fixtures dir sitting just over the old number, been treating it as a bad fixture for months
```

> **Problems:** longer than one remark


## g8.r2

**The hidden requirement:**

- **rule** — `attachment.py` defines `_ATTACHMENT_FINGERPRINT_HEX_LEN: int = 12` and `attachment_fingerprint(payload: str) -> str` returning `"sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]`; `AttachmentBlock` gains a required `fingerprint: str` field that `_canonical_attachment_block` sets from the block's payload. So a block for a file holding `b"%PDF-1.4\n"` has `fingerprint == "sha256:fc1c4358d4aa"`, and `Image(content=b"x")` gives `"sha256:5e21d86b709b"`.
- **scope** — The derived `filename` is capped at `_MAX_ATTACHMENT_FILENAME_LEN: int = 64`, extension kept: when the basename is longer than 64 characters it becomes `name[: 64 - len(ext)] + ext` for `ext = os.path.splitext(name)[1]`; a name of 64 or fewer characters is untouched. Only `block.filename` is capped — `payload` keeps the full URL and the attachment's own `url` is never modified, so a 73-character PDF basename renders as `{"filename": "2024-q4-consolidated-financial-statements-and-notes-final-ap.pdf", "file_url": <the full untruncated URL>}`.
- **exclusions_or_crossover** — A `source == "url"` block is fingerprinted identically: the digest is taken over the payload *string*, query and fragment included — `https://cdn.example.com/photos/cat.jpeg?size=large` gives `fingerprint == "sha256:80ce7facd006"` — and a base64 block hashes its base64 text, never the decoded bytes.
- **failure_behavior** — Image `detail` is normalized against a fixed vocabulary at block-build time: `_SUPPORTED_IMAGE_DETAILS: tuple[str, ...] = ("auto", "low", "high")` and a pure `normalize_detail(value: str | None) -> str` return `str(value).strip().lower()` when that lands in the vocabulary and `"auto"` otherwise, emitting exactly one `logger.warning` on the fallback and none on a hit or on `None`. So `Image(content=b"x", detail="HIGH")` gives a block `detail` of `"high"`; `Image.detail` itself keeps whatever the caller wrote.

**Reversed earlier:** `detail` was originally handed to the provider exactly as the caller wrote it; that was reversed after a typo'd `"hgih"` produced a provider 400 mid-run, and the team chose a silent downgrade to `"auto"` with a warning over failing the request.

**What a reader has to infer along the way:**

- *Every canonical block must carry a required short digest of its own payload, computed by a named helper as a truncated sha256 hex string with the algorithm written into the value itself, and the truncation length must be a named constant rather than an inline slice.*
  - nobody says: If you cannot compare two attachments without shipping megabytes of payload around, the thing you put on the block has to be small, stable, and self-describing about how it was made.
- *The filename the block carries is capped in length with its extension preserved, and the cap applies only to that derived display name, never to the payload or the attachment's own url.*
  - nobody says: A name that got shortened for readability is only safe to shorten if the part carrying meaning survives and nothing that has to be fetched or sent was shortened with it.
- *Remote-url blocks get the same digest as inline ones, taken over the payload string exactly as stored, query and fragment included; base64 blocks hash their base64 text and not the decoded bytes.*
  - nobody says: If the digest is computed over whatever string the block already holds, the same rule covers both source kinds with no fetching and no decoding step.
- *Image detail is folded to lowercase and matched against a fixed three-value vocabulary when the block is built, falling back to the default with a single warning only when it misses, and leaving the caller's own attribute alone.*
  - nobody says: Case and whitespace differences are the user typing, not the user being wrong, so only a genuine miss deserves the fallback and the log line.

**Names the tests reach for that the ticket withholds:**

- said: `A`, `HIGH`, `_ATTACHMENT_FINGERPRINT_HEX_LEN`, `_SUPPORTED_IMAGE_DETAILS`, `attachment_fingerprint`, `fingerprint`, `normalize_detail`

> **Spread:** one source only (slack); g8.r2.sc2: two remarks in #cookbooks within 3 days; g8.r2.sc3: two remarks in #random within 8 days; g8.r2.sc4: two remarks in #viewer within 10 days

> **11 of 49 graded assertions are not stated outright** — 11 implied. A reader has to supply the rest themselves, and may not. See `settled.md`.

### The remarks, by the step they build

### g8.r2.sc1 — Every canonical block must carry a required short digest of its own payload, computed by a named helper as a truncated sha256 hex string with the algorithm written into the value itself, and the truncation length must be a named constant rather than an inline slice.

*Nobody says:* If you cannot compare two attachments without shipping megabytes of payload around, the thing you put on the block has to be small, stable, and self-describing about how it was made.

*5 remarks — 1 reporting the problem, 4 settling the design.*

#### `g8.r2.l1` — rule

**nils**, 2025-04-07, #general

> spent yesterday afternoon trying to demonstrate that two runs sent the same pdf. there is nothing on the block to compare, and we never log payloads - they're megabytes.

*What a reader should take from it:* the team agrees blocks are currently impossible to compare across runs without logging whole payloads

*Step it builds toward:* `g8.r2.sc1` — Every canonical block must carry a required short digest of its own payload, computed by a named helper as a truncated sha256 hex string with the algorithm written into the value itself, and the truncation length must be a named constant rather than an inline slice.

*Drafted as:* spent yesterday afternoon trying to show two runs sent the same pdf. nothing on the block to compare, and we never log payloads, they are megabytes.

*Why there:* Neither candidate day is chewing on attachment payload identity. #engineering 2025-03-19 is v0.1.21 release notes, the token-count/throttle regression check, and the api_key decision on PR 584 — nils's own contributions there are all about unblocking 584. #pipeline 2025-03-25 is entirely provider test coverage: what the Gemini example refactor removed, whether dropping the Mistral fixture tests thins coverage, WS-047, and who reviews 584. A remark about spending an afternoon trying to prove two runs sent the same pdf answers nothing anyone asked in either room, changes the subject, and would sit there without a reply — and nils is the one person in both rooms who is visibly heads-down on something else. It wants its own thread in #pipeline, which is the room for what we actually send to provider backends, with the sibling remark (the small derived thing that goes on the block) landing as the reply.

*Still leaves open:* what small thing goes on the block instead, how it is derived, and what it looks like

*A new conversation in #general on 2025-04-07:*

```
14:02  konrad: nils did the pdf comparison thing go anywhere in the end
14:04  nils: no. i spent yesterday afternoon trying to demonstrate that two runs sent the same pdf, and i could not get there
14:05  gideon: whats actually missing
14:07  nils: there is nothing on the block to compare. i have two blocks and neither one says anything about what went out
14:08  gideon: the payload though? off the request log somewhere
14:09  konrad: we never log payloads. they are megabytes, it would eat the log in a day
14:11  nils: yeah. so the block carries something comparable of its own, small enough that writing it down costs us nothing. that's worth documenting before anyone picks it up
14:13  gideon: honestly though i was pretty sure we had somthing like that on there already
```

#### `g8.r2.say22` — rule

**gideon**, 2025-04-09, #incidents

> so basically I expected attachment_fingerprint to special case the empty payload and it doesnt, "" just goes through sha256 like any other payload, prefix and all.

*What a reader should take from it:* the team agrees the empty payload is not special-cased and goes through the same hashing rule as any other payload

*Step it builds toward:* `g8.r2.sc1` — Every canonical block must carry a required short digest of its own payload, computed by a named helper as a truncated sha256 hex string with the algorithm written into the value itself, and the truncation length must be a named constant rather than an inline slice.

*Drafted as:* so basically I expected attachment_fingerprint to guard an empty payload and it doesn't - "" hashes like any other string, sha256 of nothing, prefix and all.

*Why there:* None of the five rooms is anywhere near attachments or payload hashing that week. #engineering 04-16 is cost-streaming skew and Gemini version branching; #help 04-21 is per-request capability lookups and container pull time; #viewer 04-10 is PR 624 log noise vs progress bars; #code-review 05-05 is 0.1.24 and PRs 652/654; #viewer 04-28 is the inspected-directory field on the report object. Dropping a fingerprint-hashing observation into any of them changes the subject and would draw no reply. attachment_fingerprint is a rule about how request payloads get hashed — attachment blocks, empty payloads, remote vs inline — which is the request layer, so it belongs in #pipeline, in a thread where someone is actually working through the hashing rule and its edge cases and gideon is reporting what he found when he read the function.

*Still leaves open:* Doesn't say what the prefix is, how long the hex is kept, what the argument is for a remote block, or which field on the block holds the result.

*Must appear literally:* `attachment_fingerprint`, `sha256`

*A new conversation in #incidents on 2025-04-09:*

```
13:21  emil: does attachment_fingerprint short circuit an empty payload, or does it hash it like anything else
13:22  gideon: no short circut. i went looking for that branch too, its not there
13:24  emil: so an empty one still comes back with something? i expected some kind of marker honestly
13:25  gideon: ya. so basically "" just goes through sha256 like any other payload
13:26  dermot: with the prefix on the front too, or is that skipped for empty
13:27  gideon: prefix and all. nothing about the empty case is special cased
13:29  emil: should be in the docstring then, its not written down anywhere
13:31  dermot: mhm. would explain the entry i couldnt account for in yesterdays index dump
```

#### `g8.r2.l2` — rule

**dermot**, 2025-04-23, #pipeline

> while we're in there, give the record a short digest of the payload and make fingerprint required. optional means half the call sites forget it and we're back to guessing

*What a reader should take from it:* the team agrees the block carries a payload-derived digest in a required field

*Step it builds toward:* `g8.r2.sc1` — Every canonical block must carry a required short digest of its own payload, computed by a named helper as a truncated sha256 hex string with the algorithm written into the value itself, and the truncation length must be a named constant rather than an inline slice.

*Drafted as:* so give the block a short digest of the payload and make fingerprint required. optional means half the call sites forget it and we are back to guessing.

*Why there:* The room is mid-thread on exactly this: emil reported the persisted job record carries only id, request file path and timestamp, dermot already said at 15:35 that "the fingerprint and the job record have the same gap", and emil at 17:13 proposed fixing the record side independently of the cache key. This is the shape that proposal was missing, and dermot is the one who named the gap, so he closes it. It doesn't touch dario's blocked cache-key change, and it leaves algorithm/length/self-describing unresolved.

*Still leaves open:* which algorithm, how much of it is kept, and whether the value says what made it

*Must appear literally:* `fingerprint`

*Goes into the real conversation in #pipeline on 2025-04-23, after 17:13 emil:*

```
09:00  dermot: bulk-llm-inference is mostly stable, few loose ends on the proivder side
09:00  dermot: multimodal-prompts is holding, nothing urgent there
09:27  gideon: Dario, does the request fingerprint factor in model at all, or is it just prompt + params?
09:35  dermot: I mean, it should be. same prompt on a different model is not the same request
11:13  gideon: yeah but do we know for sure it actually is, or is that the thing nobody's checked?
11:40  dario: Been in the caching code most of this morning looking at exactly this - from what I can see so far, model is not explicitly part of the fingerprint
11:40  dario: It hashes on promt content and the generation params that get passed in, but model comes in as its own thing and I'm not seeing it folded into the key
11:41  dario: Still working through it to make sure I'm reading that right
12:43  emil: huh
12:43  emil: that would explain a lot
13:15  gideon: If model gets added to the key, do we have any sense of how many existing cached entries would get blown away?
13:16  dario: Honestly I don't have that count, and I'd lean toward not moving on this until we do.
14:33  gideon: Is there a way to pull that count from the cache store, or does it need instrumentation first?
15:09  emil: Related: the persisted job record doesn't store the model either, just the id, the request file path, and a timestamp
15:09  emil: and this isn't the first time either, it's bitten me twice this week
15:09  emil: that's the whole record, nothing else on it
15:09  emil: so if someone hands me a run dir I can't tell what model it went out with, and that means I can't tell if picking it back up is safe
15:35  dermot: the fingerprint and the job record have the same gap
15:39  dario: I'd want @Nikolai Berresford in this before we touch anything - I dunno off the top of my head if the count is even pullable without adding instrument
16:59  gideon: Good call holding off
16:59  gideon: That's the right move
17:13  emil: We could fix the job record side independently, just write the model into the pending record without touching the cache key at all.   <-- THE REMARK GOES HERE
```

#### `g8.r2.l4` — rule

**gideon**, 2025-04-25, #viewer

> so basically I pinned it in the test - tmp file with just %PDF-1.4 in it comes out sha256:fc1c4358d4aa, same value every run, algoritm is right there in the string

*What a reader should take from it:* the team agrees the stored value names its algorithm inline and is stable for a given payload

*Step it builds toward:* `g8.r2.sc1` — Every canonical block must carry a required short digest of its own payload, computed by a named helper as a truncated sha256 hex string with the algorithm written into the value itself, and the truncation length must be a named constant rather than an inline slice.

*Drafted as:* Pinned it in the test: the tmp file holding just %PDF-1.4 lands on sha256:fc1c4358d4aa, same every run.

*Why there:* None of the five is anywhere near this. #random 04-25 is about disagreeing model-name lists, #random 04-17 is the mkdir -p billing scare, #pipeline 04-10 is DeepSeek 429 headers and PR 624's log lines, #viewer 04-28 is the metadata panel not showing the inspected directory, and #code-review 05-05 is 0.1.24 plus review requests on PR 652/654 with no diff discussed. A pinned test value for a content-addressed attachment payload id would land in none of them without changing the subject and getting no reply. The request layer is where attachment payloads get built, hashed and cached, so #pipeline is the room — just not that Thursday's thread. What's needed is a thread where someone is actually asking how an attached file is identified on the request object, so gideon reporting the pinned test value answers a live question.

*Still leaves open:* how much of the hex is kept, and what string was fed in to get there

*Must appear literally:* `sha256:fc1c4358d4aa`

*A new conversation in #viewer on 2025-04-25:*

```
13:41  konrad: the checksum the viewer shows on a download — is that stable or does it wander between runs
13:43  gideon: so basically i pinned it in the test. tmp file with just %PDF-1.4 in it, thats the entire fixture
13:44  konrad: pinned as in you assert the literal string? so if it wanders the test goes red
13:45  gideon: ya. sha256:fc1c4358d4aa, same value every run, i ran it a bunch
13:47  petar: and how does anyone reading it know what produced that. do we record it somewhere else
13:48  gideon: no need, the algoritm is right there in the string. thats what the bit before the colon is for
13:50  petar: ah. i wasnt reading the prefix as meaning anything
```

#### `g8.r2.l3` — rule

**konrad**, 2025-05-06, #code-review

> took Dermot's review nit, no inline [:12] slice - `_ATTACHMENT_FINGERPRINT_HEX_LEN` sits next to the helper now. `attachment_fingerprint` takes the payload string and hands back the "sha256:" prefix already on it.

*What a reader should take from it:* the team agrees twelve hex characters are kept, behind a named constant, via a named helper

*Step it builds toward:* `g8.r2.sc1` — Every canonical block must carry a required short digest of its own payload, computed by a named helper as a truncated sha256 hex string with the algorithm written into the value itself, and the truncation length must be a named constant rather than an inline slice.

*Drafted as:* Dermot's review nit: don't slice [:12] inline. So `_ATTACHMENT_FINGERPRINT_HEX_LEN` sits next to the helper, and the helper is `attachment_fingerprint`.

*Why there:* That day's #code-review already turns into a naming-in-code thread — Dermot's 09:57 "while we're naming things in code anyway, it occured to me..." presupposes a naming discussion just above it, and konrad reporting that he took Dermot's review nit and landed on a named constant plus a named helper is exactly the thing Dermot would be riffing off. Konrad is already the one driving review traffic that morning (09:36 on PR 661), so him closing out a nit of his own reads native, and nothing else in the day makes the point.

*Still leaves open:* which algorithm produces the hex, what string goes in, and what the stored value is prefixed with

*Must appear literally:* `[:12]`, `_ATTACHMENT_FINGERPRINT_HEX_LEN`, `attachment_fingerprint`, `sha256:`

*Goes into the real conversation in #code-review on 2025-05-06, after 09:50 gideon:*

```
09:00  nikolai: PR 653 is good to go on my end, been waiting on a review pass
09:28  gideon: - *PR 661* eyes still welcome, touches examples-cookbooks, not blocking but it's been sitting
- *PR 653* will take a look this morning
09:36  konrad: PR 661 could use another set of eyes when you get a chance, it's the prescription extraction example in examples-cookbooks
09:50  gideon: On PR 653 now, should have feedback before lunch   <-- THE REMARK GOES HERE
09:57  dermot: while we're naming things in code anyway, it occured to me we've never actually passed a user argument to docker on the create call
09:57  dermot: the uid is just left to the dockerfile, but that should be something the executor decides at create time
10:34  konrad: right
11:18  gideon: uh, not sure - if the image doesn't have that user set up, won't the container just fail to start?
11:38  emil: Anyone got eyes on PR 661 when they wrap up PR 653?
11:38  emil: It's the prescription extraction example in examples-cookbooks, not blocking anything
12:23  dermot: @Nikolai, gideon's question on the user setup is probably yours to answer. does code-execution handle that before the create call?
12:41  emil: Did PR 661 get any eyes yet?
12:41  emil: Trying to get it merged today, not carry it into tomorrow
12:51  nikolai: Available this afternoon
12:51  nikolai: And yes, @Dermot is right about the user arg, code-execution owns that, the executor passes it at create time
12:51  nikolai: The image shouldn't be making that call
13:13  konrad: @Nikolai if you're free this afternoon, PR 661 would be a good use of that time, it's a straightforward example and shouldn't take long
13:50  gideon: PR 653 still needs a merge-or-defer call, nobody's landed on that yet
14:10  dermot: @Gideon you were reviewing PR 653 this morning, where did you land on it?
14:40  gideon: Looked clean to me, I think it's ready to merge.
14:40  gideon: So are we merging PR 653 today or pushing it?
15:00  nikolai: Worth noting: code-execution isn't actually passing the user arg to docker at create time right now, the uid is landing via the image. That's the gap 
15:01  nikolai: I can merge PR 653 today, I'm just not sure the container user gap should go in separately or if it should be part of this first
15:39  emil: PR 661 is ready on my end, no outstanding changes, just waiting on a review pass.
15:51  nikolai: Merging PR 653 today, Gideon's review is in and the container user gap is a separate follow-up. PR 661 is next on my list.
16:21  konrad: PR 661 is still up for review if anyone else wants a look before Nikolai gets to it
16:54  gideon: @Emil good day for you overall, getting two PRs to the finish line?
17:25  dermot: @Nikolai is there an issue open for the container user fix, or do we need to open one?
17:26  dermot: the uid has to be an argument the executor passes at create time, not something the dockerfile decides.
17:26  dermot: I'll open an issue for it if there isn't one already.
```

### g8.r2.sc2 — The filename the block carries is capped in length with its extension preserved, and the cap applies only to that derived display name, never to the payload or the attachment's own url.

*Nobody says:* A name that got shortened for readability is only safe to shorten if the part carrying meaning survives and nothing that has to be fetched or sent was shortened with it.

*4 remarks — 0 reporting the problem, 4 settling the design.*

#### `g8.r2.l5` — scope

**nikolai**, 2025-03-21, #cookbooks

> yep these finance exports land with 73-character basenames, full title plus two dates plus final - and the block is just {"type": "file", "file": {"filename": ..., "file_url": ...}} so its mostly filename

*What a reader should take from it:* the team agrees derived basenames in practice run far longer than anything usable

*Step it builds toward:* `g8.r2.sc2` — The filename the block carries is capped in length with its extension preserved, and the cap applies only to that derived display name, never to the payload or the attachment's own url.

*Drafted as:* these finance exports arrive with 73-character basenames, full report title plus two dates plus the word final. the file block we send is mostly filename.

*Why there:* None of the listed conversations is anywhere near this subject. All eight are PR-status, release-coordination, or fix-ownership threads (torch guards, merge state of PR 639, release notes for v0.1.23) — none touches how we build the file block that goes out with a request, and a concrete complaint about 73-character derived basenames dropped into any of them would change the subject and get no reaction. The natural home is #pipeline: it owns the request layer and what we actually send to each provider backend, so payload bloat from derived filenames is exactly its business. The conversation that should exist is someone hitting oversized attachment payloads on a real run of finance-export PDFs and asking whether we truncate the basename we derive, with Nikolai supplying the field evidence for how long these actually get while someone else settles the budget and what's exempt.

*Still leaves open:* what length is acceptable, what survives the shortening, and what must not be shortened

*Must appear literally:* `"file"`, `"file_url"`, `"filename"`, `"type": "file"`, `73`

*A new conversation in #cookbooks on 2025-03-21:*

```
13:31  konrad: These finance exports, what is actually in the file name? They run very long and i want to know if thats normal
13:33  nikolai: normal yep thats just what they emit
13:35  dario: its the full title, then the two dates, then a trailing - on the end. nothing gets shortened anywhere
13:37  konrad: long how, roughly
13:39  nikolai: 73 characters on the basename for the batch i pulled this morning
13:40  konrad: so in the block we send, the name is most of it? presumably the url part is small
13:42  nikolai: right the block is just {"type": "file", "file": {"filename": ..., "file_url": ...}} so its mostly filename, anything we plan around the block we plan around the name
13:44  dario: that tracks. the export i had open monday was exactly that shape, title dates dash, i just never counted it
```

> **Problems:** longer than one remark

#### `g8.r2.l7` — scope

**konrad**, 2025-03-24, #cookbooks

> Look, I chopped one in the protoype and the .pdf came off the end, provider stopped seeing a pdf. Suffix stays on; no extension means just the first 64 characters.

*What a reader should take from it:* the team agrees the suffix survives shortening rather than being cut off the end

*Step it builds toward:* `g8.r2.sc2` — The filename the block carries is capped in length with its extension preserved, and the cap applies only to that derived display name, never to the payload or the attachment's own url.

*Drafted as:* Chopped a long one at the cap in the prototype and the .pdf came off the end, provider stopped treating it as a pdf. Keep the suffix on.

*Why there:* None of the eight candidates is anywhere near this. The remark is a hands-on finding about how a filename gets truncated inside an outbound provider payload — the provider stops recognizing the file once the extension is chopped. That's the request layer: what we send to a provider backend and how that backend reads it, which is #pipeline's whole remit. The engineering days on offer are milestone wrap-up, PR sequencing, README/cookbook coverage and the cost-estimation/examples-table thread; the releases days are bump and sign-off logistics; #viewer 2025-06-02 is dataset download plumbing and Gideon's missing handover doc, which shares the word "download" and nothing else; #code-review 2025-05-30 is a queue of unreviewed PRs plus the sandbox-image question. Dropping a truncation finding into any of them changes the subject and would draw no reply. What should have existed is a #pipeline thread settling how attachment filenames are capped in the payload — Konrad reporting what he hit in the prototype is exactly the kind of thing he posts there, and it leaves the actual cap value and the url question to someone else in the thread.

*Still leaves open:* what the actual limit is, and whether the url is shortened too

*Must appear literally:* `.pdf`, `64`

*A new conversation in #cookbooks on 2025-03-24:*

```
15:06  nikolai: the long attachment filenames are getting cut somewhere in the payload right
15:09  konrad: yes, we cap the name. Look, i chopped one in the protoype and the .pdf came off the end, provider stopped seeing a pdf
15:11  dermot: so whatever the cut is, the suffix rides along at the end of it
15:12  konrad: right. suffix stays on
15:14  nikolai: and the ones with no extension at all
15:15  konrad: then its just the first 64 characters, nothing to keep on the end
15:18  dermot: mhm. none of the example names in the cookbooks are anywhere near long enough to hit it, its the scanned uploads
```

> **Problems:** longer than one remark

#### `g8.r2.l6` — scope

**emil**, 2025-04-03, #viewer

> honestly 64 is plenty for the block name, past that its just the date written twice - `_MAX_ATTACHMENT_FILENAME_LEN` = 64, and a name thats exactly 64 we leave alone, only longer ones get cut.

*What a reader should take from it:* the team agrees the block's name is bounded at sixty-four characters behind a named constant

*Step it builds toward:* `g8.r2.sc2` — The filename the block carries is capped in length with its extension preserved, and the cap applies only to that derived display name, never to the payload or the attachment's own url.

*Drafted as:* 64 is plenty for the name we put on the block. past that it is the date written twice, so `_MAX_ATTACHMENT_FILENAME_LEN` = 64 and move on.

*Why there:* None of the candidates is anywhere near attachment rendering. #viewer 2025-03-27 is a governance argument about whether local viewer is being removed (PR 605) — a constant for how long a filename may be on an attachment block would change the subject entirely and get no reaction. #releases 06-06 and #code-review 06-25 are tag/blocker coordination (PR 653/675/690), #cookbooks 05-23 is example freshness, both #engineering days are cost-streaming skew and throttle-path ownership, #pipeline 03-31 is auth flow and issues 207/233. The remark is a small settled display decision about the name shown on an attachment block, which belongs in the room that owns the viewer surface — and it needs a day where multimodal attachments are actually being rendered, which is the week after emil's Gemini multimodal batch path (PR 690) lands in review, not March.

*Still leaves open:* what happens to the end of a name that gets cut, and whether anything else gets cut with it

*Must appear literally:* `64`, `_MAX_ATTACHMENT_FILENAME_LEN`

*A new conversation in #viewer on 2025-04-03:*

```
14:02  konrad: the attachment names we print in the block header, some of them are absurd. what do we cut them at
14:05  dario: the one from this morning wrapped twice in my terminal, so, yeah
14:06  emil: honestly 64 is plenty for the block name. past that its just the date written twice
14:07  konrad: ok. and that number sits where, inline in the builder?
14:08  emil: _MAX_ATTACHMENT_FILENAME_LEN, next to the other caps. nobody's typed it yet
14:09  konrad: one thing though - a name thats exactly 64, does that get cut or not
14:10  emil: we leave it alone. only longer ones get cut
14:11  dario: mhm. i was reading it as strictly under when you said it, good that you asked
```

> **Problems:** longer than one remark

#### `g8.r2.l8` — scope

**dario**, 2025-04-11, #releases

> honestly the 404 came from trimming the url along with the name - we only shorten the display name we derive, the payload url and the caller's File.url both stay untouched.

*What a reader should take from it:* the team agrees shortening touches the derived name only, leaving the payload and the attachment's url intact

*Step it builds toward:* `g8.r2.sc2` — The filename the block carries is capped in length with its extension preserved, and the cap applies only to that derived display name, never to the payload or the attachment's own url.

*Drafted as:* somebody trimmed the url along with the name and the fetch 404'd. only the name we display shrinks, the link we send stays whole.

*Why there:* Nothing in the candidate set is about attachments. #viewer 03-27 is local-viewer removal and PR 605; #cookbooks 05-05 is the response-object `.choices` grep; #code-review 04-14 is PR 632/626 ordering; #engineering 03-17 is litellm model-name matching; the three #pipeline days are Mistral auth/resume, DeepSeek 429 headers, and Nikolai's stdout scope. The remark decides where a shortening pass is allowed to reach — display name only, payload and attachment url untouched — which answers a live bug about a request we send to a provider. That is #pipeline (request layer, payload construction, provider backends), but no such thread exists in the candidates, so it needs one: someone reports the 404 from truncated attachment urls, the room works out whether shortening belongs on the derived name or the payload, dario settles that boundary, and the actual truncation rule (how short, which part survives) is still open for someone else to state.

*Still leaves open:* how short the name gets and what part of it survives

*Must appear literally:* `404`, `File.url`

*A new conversation in #releases on 2025-04-11:*

```
13:38  nikolai: anyone looked at the 404 from the attachment thing this morning
13:40  konrad: yes but i dont follow it. we only make the name shorter, why does a fetch die
13:43  dario: honestly thats where the 404 came from, we were trimming the url along with the name in the same pass
13:44  nikolai: so what actually gets cut now
13:46  dario: just the display name we derive. thats the only thing that shortens
13:47  konrad: and the url that goes in the payload, that one stays as is?
13:49  dario: stays untouched, and so does the caller's File.url. neither of those is ours to shorten. nobody has written the patch yet but thats the shape of it
13:50  nikolai: yep the short name was only ever cosmetic anyway
```

> **Problems:** longer than one remark

### g8.r2.sc3 — Remote-url blocks get the same digest as inline ones, taken over the payload string exactly as stored, query and fragment included; base64 blocks hash their base64 text and not the decoded bytes.

*Nobody says:* If the digest is computed over whatever string the block already holds, the same rule covers both source kinds with no fetching and no decoding step.

*6 remarks — 1 reporting the problem, 5 settling the design.*

#### `g8.r2.l9` — exclusions_or_crossover, rule

**gideon**, 2025-04-10, #viewer

> so basically my dedupe pass kept every remote image, the fingerprint comes back empty for anythng with an http url. half the run is remote tbh.

*What a reader should take from it:* the team agrees remote-source blocks currently get no digest and that is a problem

*Step it builds toward:* `g8.r2.sc3` — Remote-url blocks get the same digest as inline ones, taken over the payload string exactly as stored, query and fragment included; base64 blocks hash their base64 text and not the decoded bytes.

*Drafted as:* My dedupe pass kept every remote image because the fingerprint comes back empty for anything with an http url. Half the run is remote.

*Why there:* None of the listed threads is chewing on request/content fingerprinting for multimodal rows. #help 3/27 is about executor Docker image digests and `latest` (same word "image", entirely different subject); #random 3/18 is closest in family — cache keys silently ignoring the model — but that day is banter about the new Claude release and a model-swap cache hit, and a remote-image dedupe bug would land there as a subject change with nobody to answer it. The 4/04, 4/16, 4/23 and 5/05 #code-review threads are all PR-ownership/review-status logjams, 4/08 #pipeline is DeepSeek headers and failed_requests.jsonl, and 4/28 #viewer is the metadata panel's inspected directory. The right home is #pipeline, where cache/resume and request construction live and where Gideon owns caching-and-resume — a fresh thread where he hits it while prepping a multimodal batch, and Dermot/Dario work out what a remote block should hash versus what the inline base64 ones hash.

*Still leaves open:* what string a remote block should be hashing, and what the inline ones hash

*Must appear literally:* `fingerprint`

*A new conversation in #viewer on 2025-04-10:*

```
13:12  gideon: dedupe pass ran over the viewer images last night and dropped exactly nothing. every remote one still sitting in the list
13:14  konrad: local files collapse fine though?
13:16  gideon: ya those are fine. the fingerprint comes back empty for anythng with an http url
13:17  emil: so empty just gets kept instead of compared? small slice presumably
13:19  gideon: half the run is remote tbh. so basically empty cant keep meaning keep
13:21  gideon: we fingerprint the remote ones off what the local path already fingerprints, then dedupe once over the lot. no seperate branch for them
13:23  konrad: right, so the dropped count in yesterdays summary was only ever the local ones
13:24  gideon: exactly
```

#### `g8.r2.l10` — exclusions_or_crossover

**nikolai**, 2025-04-11, #incidents

> ran the same cat.jpeg twice A with ?size=large and B without and they came out as two seperate cache entries thats the behaviour i want just want it written down

*What a reader should take from it:* the team agrees two urls differing only after the question mark are treated as distinct

*Step it builds toward:* `g8.r2.sc3` — Remote-url blocks get the same digest as inline ones, taken over the payload string exactly as stored, query and fragment included; base64 blocks hash their base64 text and not the decoded bytes.

*Drafted as:* same cat.jpeg twice, A carries ?size=large and B does not, and they came out as two separate entries. that is what i want but wanted it written down.

*Why there:* None of the listed conversations is about attachments, image payloads, or cache keys. The three #code-review days are PR triage and release-blocking decisions; #releases 2025-04-24 is tagging v0.1.7; #engineering 2025-05-01 and 2026-01-23 are executor image tags and finetuning cleanup; #cookbooks 2025-04-16 is docker image pinning and batch-id resume ignoring the model param. The nearest vocabulary match (image, pinning, tags) is about container images, not inline attachment URLs — exactly the "both mention the cookbook" trap. Cache-key construction for request payloads is the request layer, which is #pipeline: caching, resume, and provider backends live there, and dario owns caching-and-resume. The thread that should exist is nikolai confirming, against dario's explanation of what actually goes into the hash for inline attachments, that two URLs differing only in query string produce distinct entries.

*Still leaves open:* what is hashed for inline attachments, and why the query string counts

*Must appear literally:* `A`

*A new conversation in #incidents on 2025-04-11:*

```
13:41  gideon: quick one before i forget, i put the same cat.jpeg through twice this morning and ended up with two cache entries for it
13:43  nikolai: twice how
13:44  gideon: call them A and B. A had ?size=large on it, B was just the plain url. same picture obviously
13:46  dermot: so the one with the query param and the one without landed as two seperate entries, and you're asking if that's a bug
13:46  gideon: ya basically. tbh i assumed one of them would hit the other
13:48  nikolai: no thats the behaviour i want A and B being two entries is correct
13:49  dermot: yeah ok. i went looking for that before i pinged and couldn't find it stated anywhere
13:51  nikolai: yep thats the gap i'd say its fine as is it just needs writing down
```

#### `g8.r2.say23` — exclusions_or_crossover

**emil**, 2025-04-17, #random

> fwiw i ran it, attachment_fingerprint("https://cdn.example.com/photos/cat.jpeg?size=large") comes back sha256:80ce7facd006, and a base64 block whose text is that same string lands on the same digest.

*What a reader should take from it:* the team agrees a url block and a base64 block with identical payload strings produce identical fingerprints, and pins the cat.jpeg digest.

*Step it builds toward:* `g8.r2.sc3` — Remote-url blocks get the same digest as inline ones, taken over the payload string exactly as stored, query and fragment included; base64 blocks hash their base64 text and not the decoded bytes.

*Drafted as:* for what it's worth attachment_fingerprint("https://cdn.example.com/photos/cat.jpeg?size=large") gives sha256:80ce7facd006, and a base64 block whose text was that same string lands on the same digest.

*Why there:* None of the eight candidates is anywhere near attachment payloads or fingerprint/cache identity. They're about PR triage before 0.1.26 (code-review 6/16, engineering 6/25), a model-swap cache miss and a postmortem (random 3/18), cookbook table structure and CI wiring (cookbooks 3/24), None-cost display in the viewer (viewer 6/3, 6/5), duplicate batch jobs from restarts (viewer 4/3), the agent response shape (engineering 5/21), and the structured-output revert (incidents 5/6). Dropping a concrete attachment_fingerprint digest into any of them changes the subject and would get no reaction. The natural home is #pipeline: attachment blocks are part of what we send to providers, and whether a url block and a base64 block collapse to the same fingerprint is a request-layer identity question, the same room where dario would answer from the bulk-llm-inference side. Emil owns multimodal-prompts (he says so himself on 2025-05-21, holding on it pending the response shape), so once that unblocks he's the person who'd actually run the helper and report the digest.

*Still leaves open:* doesn't say why they match - that the helper takes the payload string alone, with no source kind mixed in, comes from dario's remark, and the base64-text-not-decoded-bytes rule comes from l12.

*Must appear literally:* `attachment_fingerprint`, `https://cdn.example.com/photos/cat.jpeg?size=large`, `sha256:80ce7facd006`

*A new conversation in #random on 2025-04-17:*

```
13:21  nikolai: same image comes in twice, once as a link once pasted inline. two rows or one
13:23  emil: fwiw i ran it, attachment_fingerprint("https://cdn.example.com/photos/cat.jpeg?size=large") comes back sha256:80ce7facd006
13:24  nikolai: thats the link one. the pasted one is what im asking
13:25  gideon: ya same, thats the bit the ticket doesnt say
13:27  emil: a base64 block whose text is that same string lands on the same digest. 80ce7facd006 both times, i checked
13:28  nikolai: right. one row then
13:29  gideon: honestly though nobody has run this outside your repl yet has it
13:30  emil: nope, just the repl
```

> **Problems:** longer than one remark

#### `g8.r2.say21` — rule

**emil**, 2025-04-21, #help

> for what it's worth that pinned image value is straight out of the helper - attachment_fingerprint("eA==") returns "sha256:5e21d86b709b", the block just stores what it gets back.

*What a reader should take from it:* the team agrees the pinned one-byte-image value is the helper's own return value, not something assembled at the call site

*Step it builds toward:* `g8.r2.sc3` — Remote-url blocks get the same digest as inline ones, taken over the payload string exactly as stored, query and fragment included; base64 blocks hash their base64 text and not the decoded bytes.

*Drafted as:* for what it's worth that pinned image value is straight out of the helper - attachment_fingerprint("eA==") returns "sha256:5e21d86b709b", the block just stores what it gets.

*Why there:* None of the eight candidates is anywhere near attachment fingerprinting. The two #code-review days are pure PR-status triage (652/653/663/690/691) and a stats-rendering diff; #cookbooks is the examples table; the #engineering days are agent response shape and a version tag reference; #incidents is the post1 announce; #pipeline 2025-03-26 is the closest by vocabulary — it does touch cache key computation — but that thread is about `__internal_prompt` being stripped before prompt() and about Mistral batch usage extraction, and a defence of a pinned one-byte-image fingerprint would change the subject and draw no reaction. The remark is someone answering a reviewer who suspected the value in a doc/test block was hand-assembled, which needs a PR review of the fingerprint helper itself. Emil is the right speaker — he owns multimodal-prompts (he says so on 2025-05-21) — so this belongs in #code-review on a PR that adds attachment fingerprinting into the cache key, with the sibling questions about base64-vs-decoded-bytes, remote urls and the truncation constant coming from the reviewers in the same thread.

*Still leaves open:* Says nothing about why the base64 text is hashed rather than the decoded bytes, nothing about remote urls, and nothing about the truncation length or where the constant lives.

*Must appear literally:* `attachment_fingerprint`, `eA==`, `sha256:5e21d86b709b`

*A new conversation in #help on 2025-04-21:*

```
15:22  petar: that pinned value in the attachment fixture, the short sha looking one - is that hand written or does something generate it
15:25  emil: honestly nothing hand written in there. the block just stores what it gets back from the helper
15:27  petar: ok but is it the value for the input we actually pass, or a stale one somebody pasted in ages ago
15:30  emil: let me think through that - no its live. attachment_fingerprint("eA==") returns "sha256:5e21d86b709b", so that pinned value is straight out of the helper
15:32  dermot: mhm. so the assert belongs on the helper, not on the block side
15:33  emil: sounds right. nobody has written that one yet though
15:35  petar: ok. i'd copied my expected string out of an old run
```

#### `g8.r2.l11` — exclusions_or_crossover

**dario**, 2025-04-24, #pipeline

> honestly we never open a remote one, so the helper hashes the stored url string exactly as we send it, query and anchor included, no kind marker and no salt.

*What a reader should take from it:* the team agrees a remote block hashes its stored url string unmodified rather than any fetched content

*Step it builds toward:* `g8.r2.sc3` — Remote-url blocks get the same digest as inline ones, taken over the payload string exactly as stored, query and fragment included; base64 blocks hash their base64 text and not the decoded bytes.

*Drafted as:* we never open a remote link, so the only thing we can honestly hash is the link text exactly as we send it, query and anchor included.

*Why there:* None of the five sit anywhere near attachment payload hashing. The 05-01 and 04-16 #engineering threads are executor image defaults and cost-streaming skew; #general 04-21 is PR triage; #cookbooks 05-05 is the response object in examples. The closest is #cookbooks 04-11, which is genuinely about what a fingerprint keys on — but that thread is about script bodies, input rows and reattach state, and attachments are never in it, so a line about remote url hashing would change the subject and land unanswered. The remark belongs in #pipeline: how a request carrying attachments gets fingerprinted for the cache is request-layer business, and it needs the sibling remark about inline attachments in the same thread to be a complete decision.

*Still leaves open:* what the inline attachments hash, and how the resulting value is formatted

*A new conversation in #pipeline on 2025-04-24:*

```
14:02  emil: quick one on the url cache key — do we canonicalize first, or hash whatever string we were handed?
14:04  dario: what we were handed. the stored string, exactly as we send it
14:05  dario: honestly we never open a remote one, so theres nothing to canonicalize against anyway
14:06  emil: query survives that? i had it in my head we trimmed it. nobody's picked the ticket up yet fwiw
14:07  dario: query stays. anchor too, all of it goes in
14:08  dermot: restating to be sure: nothing prefixed to the input either? no kind marker for when a second source type shows up
14:09  dario: no marker, and no salt. its the url text and that is all
14:11  dermot: mhm. i had a salt in the thing i sketched late last night, scrapping that then
```

#### `g8.r2.l12` — exclusions_or_crossover, rule

**emil**, 2025-04-25, #random

> honestly i tried decoding every payload before hashing and the 40k pass crawled — hashing the base64 text as-is pins the one-byte image at sha256:5e21d86b709b.

*What a reader should take from it:* the team agrees an inline block hashes its base64 text rather than the decoded bytes

*Step it builds toward:* `g8.r2.sc3` — Remote-url blocks get the same digest as inline ones, taken over the payload string exactly as stored, query and fragment included; base64 blocks hash their base64 text and not the decoded bytes.

*Drafted as:* had it decoding every payload before hashing and the 40k pass crawled. hashing the base64 text as-is pins the one-byte image at sha256:5e21d86b709b.

*Why there:* None of the candidates is chewing on payload construction or content identity. The five #code-review days are pure review-queue triage (PR 632/637/639/653/663/675/681/683), #incidents 05-06 is the structured-output revert and `supports_structured_output()`, #incidents 04-11 is the v0.1.23.post1 announcement, #general 04-21 is weekly status and PR backlog, #engineering 07-10 is a doc version-tag format question. A finding about how an inline attachment block is hashed — base64 text vs decoded bytes, with a cost observed over a 40k-request pass — would land in #pipeline, which owns the request layer: batch submissions, payload building, and the cache/dedup keys those runs depend on. The conversation that should exist is emil reporting back after an overnight 40k run where rehashing decoded image bytes dominated, with dermot (who owns batch-mode and cost accounting) and nikolai pinning down the rule for inline blocks; the remote-block half of the rule and how much of the hex digest gets kept would be settled in the same thread by someone else.

*Still leaves open:* what a remote block hashes, and how much of the hex is kept

*Must appear literally:* `sha256:5e21d86b709b`

*A new conversation in #random on 2025-04-25:*

```
14:07  dermot: quick one — the image payloads, are we hashing the decoded bytes or the text sitting in the field
14:09  dermot: if i had to guess decoded, but i can't find where that would happen
14:11  emil: honestly i tried that. decoding every payload before hashing, and the 40k pass just crawled, it was not subtle
14:12  nikolai: so whats it doing instead
14:14  emil: hashing the base64 text as-is. no decode step at all
14:15  dermot: mhm. does the tiny one still come out distinct that way, thats the case i keep worrying about
14:17  emil: yup — the one byte image pins at sha256:5e21d86b709b. stable every run i did
14:19  nikolai: yep i mean the crawl was bad enough i noticed it from outside without knowing why
```

### g8.r2.sc4 — Image detail is folded to lowercase and matched against a fixed three-value vocabulary when the block is built, falling back to the default with a single warning only when it misses, and leaving the caller's own attribute alone.

*Nobody says:* Case and whitespace differences are the user typing, not the user being wrong, so only a genuine miss deserves the fallback and the log line.

*5 remarks — 1 reporting the problem, 4 settling the design.*

#### `g8.r2.l13` — failure_behavior

**konrad**, 2025-04-14, #viewer

> Look, I burned an hour on a run where I passed detail="HIGH" and every image came back looking like auto. Shift key held down is not a typo.

*What a reader should take from it:* the team agrees a correct value in the wrong case is currently treated as garbage

*Step it builds toward:* `g8.r2.sc4` — Image detail is folded to lowercase and matched against a fixed three-value vocabulary when the block is built, falling back to the default with a single warning only when it misses, and leaving the caller's own attribute alone.

*Drafted as:* Burned an hour on a run where I passed detail="HIGH" and every image came back looking like auto. Shift key held down is not a typo.

*Why there:* None of the seven candidate threads is chewing on multimodal image parameters or value validation. The closest, #engineering 2025-05-27, is about a null-handling fix on the default app id parameter, and konrad's multimodal question there is explicitly parked for Dario ("probably one for Dario, I'll follow up with him") — dropping a case-sensitivity bug report on `detail` into that thread would change the subject and get no reaction, since nobody in the room is in a position to agree with it. The remark is a run-level report about how a request parameter value is handled before it reaches the provider, which is #pipeline's stated territory (the request layer and every provider backend we talk to), and it needs a room where someone else can confirm the silent normalization and where a sibling remark can supply the accepted values and the unknown-value behavior.

*Still leaves open:* what the accepted values actually are, and what happens when a value genuinely is not one of them

*Must appear literally:* `HIGH`

*A new conversation in #viewer on 2025-04-14:*

```
14:11  dermot: does anything on our side normalise the detail value on image blocks, or is it passed through exactly as typed?
14:13  konrad: as typed. look, i burned an hour on a run last week beacuse of this
14:14  dermot: burned an hour on what, it rejected the value and you had to find the message?
14:15  konrad: no. no rejection at all, thats the whole problem. i passed detail="HIGH" and every image came back looking like auto
14:17  dario: so silent fallback. either we make it an error or we just accept the uppercase one, and honestly i'd rather accept it
14:18  konrad: accept it. shift key held down is not a typo, it should mean what it obviously means
14:20  dermot: yeah ok. an hour is charitable, i'd have blamed the images long before i blamed the string
```

#### `g8.r2.l15` — failure_behavior

**nils**, 2025-04-21, #general

> detail warning fired on all 40k images last night, most of which never set one - that's noise. and it rewrote Image.detail under me, we shouldn't mutate the source, my fixtures diff now

*What a reader should take from it:* the team agrees warning on untouched or unset values is noise and that the source object must not be mutated

*Step it builds toward:* `g8.r2.sc4` — Image detail is folded to lowercase and matched against a fixed three-value vocabulary when the block is built, falling back to the default with a single warning only when it misses, and leaving the caller's own attribute alone.

*Drafted as:* the detail warning fired on all 40k images last night, most of which never set one. and it rewrote Image.detail under me, my fixtures diff now.

*Why there:* Neither 03-20 nor 03-25 is chewing on image payloads or validation behavior — both days are pure release-sequencing traffic (PR 584/585/579, deferring 468 and 565) plus nils hunting for a WS-047 spec. Dropping a 40k-image run symptom and an in-place mutation of Image.detail into either would change the subject with nobody there holding context to answer it, and emil/dario's lines around it are about merge targets, not code semantics. It needs the thread where the detail-validation change itself was posted for review: nils runs the overnight batch, hits the warning on every image, finds his fixtures diffing, and takes it back to the PR. #code-review is the room for that — it's feedback on a specific change, not a broken run (#incidents) or a provider-backend question (#pipeline).

*Still leaves open:* when the warning is actually warranted, and what the accepted values are

*Must appear literally:* `Image.detail`

*A new conversation in #general on 2025-04-21:*

```
14:12  dermot: the overnight job logged the detail warning on every single image. all 40k of them
14:15  nils: all of them? most of that set never set one in the first place, i think
14:17  dermot: mhm. so we're warning people about something they didnt ask for, thats just noise in the log
14:20  nils: fair enough, it should only be saying anything where somebody actually made a choice. the part that got me though is it rewrote Image.detail under me
14:22  dermot: rewrote as in on the object we handed it? if i had to guess you mean in place
14:25  nils: in place, yes. my fixtures diff now, which is how i noticed. we shouldn't be mutating the source like that
14:28  nikolai: yep mine came back dirty friday too im leaving them till thats sorted
```

> **Problems:** longer than one remark

#### `g8.r2.l14` — failure_behavior

**emil**, 2025-04-24, #viewer

> for the module bullet - `_SUPPORTED_IMAGE_DETAILS` is auto, low and high, nothing else, and `normalize_detail` is the only reader - hand it None and you get "auto" back.

*What a reader should take from it:* the team agrees the accepted vocabulary is three fixed values behind a named constant, checked in one named place

*Step it builds toward:* `g8.r2.sc4` — Image detail is folded to lowercase and matched against a fixed three-value vocabulary when the block is built, falling back to the default with a single warning only when it misses, and leaving the caller's own attribute alone.

*Drafted as:* for the module bullet: `_SUPPORTED_IMAGE_DETAILS` is auto, low, high and nothing else, and `normalize_detail` is the only thing that reads it.

*Why there:* None of the eight candidates is discussing multimodal image-detail handling at all. code-review|2025-05-08 is the only one that touches multimodal, and only as "three cookbook PRs flagged as stalled" plus the model support table ownership question — that day is about the Gemini serialization/GCS bug and unreviewed PRs, so a settled statement about a supported-values constant and its single reader would arrive from nowhere and draw no reply. The other rooms are batch-id persistence, Mistral token usage shape, DeepSeek headers/llama4 registry, serving-infra scoping, PR triage, and a cache-dir postmortem. The conversation that should exist is the direct follow-on from Emil claiming the per-model capability/support-table action item on 05-08: writing up the request-layer helper that normalizes the image `detail` param before the provider call, in #pipeline where provider backends and request construction live. Dario would be on it (he owns bulk-llm-inference and has been the one asking "what does X actually expect" all spring), and the rest of the thread carries the sibling piece — what happens on a value outside the three, and whether the caller's own `detail` attribute is left alone.

*Still leaves open:* what happens on a value outside those three, and whether the caller's own attribute is touched

*Must appear literally:* `None`, `_SUPPORTED_IMAGE_DETAILS`, `auto`, `normalize_detail`

*A new conversation in #viewer on 2025-04-24:*

```
14:11  konrad: for the module bullet on image detail - what do i list as the accepted values? off the top of my head its auto and low, i think there is a third
14:14  emil: `_SUPPORTED_IMAGE_DETAILS` is auto, low and high. thats the whole set, nothing else goes in it
14:15  konrad: right. anything reading that set apart from the validator?
14:17  emil: `normalize_detail` is the only reader. i went looking yesterday and nothing else touches it
14:20  dario: what about when nobody passes detail at all though. does that raise or does it just land on something
14:22  emil: hand `normalize_detail` None and you get "auto" back. worth putting in the bullet plainly, people keep guessing at it
14:24  konrad: mhm. i had it down as raising, so thats one line less than i was going to write
```

#### `g8.r2.l16` — failure_behavior

**dermot**, 2025-05-14, #pipeline

> yeah ok - if it isn't one of the three we fall back to auto and log that once. nothing set at all logs nothing and the block still goes out with detail "auto".

*What a reader should take from it:* the team agrees an unrecognised value silently becomes the default with exactly one log line, and hits or absent values log nothing

*Step it builds toward:* `g8.r2.sc4` — Image detail is folded to lowercase and matched against a fixed three-value vocabulary when the block is built, falling back to the default with a single warning only when it misses, and leaving the caller's own attribute alone.

*Drafted as:* when it is not one of the three, send auto and say so once. nothing at all when the caller got it right or left it unset.

*Why there:* The remark settles the validation-and-default behaviour of the image `detail` field on an attachment/image payload block: three recognised values, unrecognised falls back to auto with exactly one log line, unset logs nothing and still ships `detail` "auto". None of the candidate days is chewing on payload block construction. #general 2025-04-29 is about a structured-output override key on non-docker backends and its open warn-vs-raise question — a different key with no three-value set and no "auto" default; dropping this there would answer a question nobody asked and pre-empt the one they deliberately left to review. #pipeline 2025-06-26 shares the word "auto" only because of auto batch mode routing; that thread is streaming routing and cache-on-drop, not field normalisation. #engineering 2025-05-07 is the room where emil's multimodal workstream and the prescription extraction example live, but that day is stalled cookbook PRs, the suite check and which cut things land in — the detail field never comes up. The right home is #pipeline, which owns the request layer and what we actually put on the wire to each provider backend, a week or so after the multimodal work landed, when someone notices image blocks going out with no detail set and a config value that isn't being honoured.

*Still leaves open:* which three values those are, and whether case and spacing are folded before the comparison

*Must appear literally:* `auto`, `detail`

*A new conversation in #pipeline on 2025-05-14:*

```
09:41  gideon: what do we do when the detail value isnt one of the three we accept? someone typo'd it in a config yesterday and i honestly could not tell what it ended up doing
09:43  dermot: falls back to auto. thats what we'd want anyway
09:44  dario: quietly though? nothing warns on it today, i'd want to know it happened
09:46  dermot: no we log it. once, not per call
09:47  gideon: and um, when its not set at all? same log or no
09:50  dermot: yeah ok - nothing set at all logs nothing. block still goes out with detail "auto" either way
```

> **Problems:** longer than one remark

#### `g8.r2.say20` — failure_behavior

**nikolai**, 2025-06-16, #pipeline

> checked the openai side each image goes out as type image_url with an image_url object carrying url and detail and for inline we send the url as data:image/png;base64, then the payload

*What a reader should take from it:* the team agrees the rendered openai image block is an image_url wrapper carrying a url and a detail, with inline payloads sent as a data:image/png;base64 uri

*Step it builds toward:* `g8.r2.sc4` — Image detail is folded to lowercase and matched against a fixed three-value vocabulary when the block is built, falling back to the default with a single warning only when it misses, and leaving the caller's own attribute alone.

*Drafted as:* checked the openai side - an image goes out as {"type": "image_url", "image_url": {"url": ..., "detail": ...}} and for inline the url is data:image/png;base64, then the payload

*Why there:* None of the listed conversations is chewing on outbound provider payload shape. The cookbooks 04-16 thread only matches on the word "image" (docker image pinning); code-review 05-30 is sandbox images and stale PRs; engineering 05-21 is the agent *response* shape; engineering 06-13 is the Pydantic confirmation plus review of Emil's Gemini multimodal PRs 690/691 — an OpenAI image_url block description would land there with no question to answer and nobody to react. The right home is #pipeline, the room for provider backends and what we actually send them, on the Monday after PR 690 lands Gemini multimodal batch creation and the OpenAI renderer is the next one to pin down — with Emil (multimodal-prompts) present and the sibling question about what goes in the detail slot and whether caller casing survives still open on the block-build side.

*Still leaves open:* what string ends up in the detail slot, and whether the caller's casing survives - that comes from the block-build side, not here

*Must appear literally:* `image_url`, `data:image/png;base64,`, `detail`, `url`, `type`

*A new conversation in #pipeline on 2025-06-16:*

```
14:12  gideon: quick one before i wire the vision path — what shape does an image actually go out in on the request? i keep guessing and getting 400s back
14:16  nikolai: checked the openai side this morning each image goes out as type image_url
14:18  emil: so one of those per image rather than one entry holding all of them, is that the read?
14:19  nikolai: yep one per image and it carries an image_url object alongside
14:21  gideon: ok but whats in that object? i had it in my head as just the url but i swear there was a second key
14:23  nikolai: url and detail
14:24  gideon: right and the inline ones? we dont have anything to put in url for those, theyre bytes in memory
14:26  nikolai: same object nothing special we send the url as data:image/png;base64, and then the payload straight after it
14:28  gideon: ahh. so the branch i wrote last week that dropped the raw b64 in bare was never going to work, that's the 400s right there
```

> **Problems:** longer than one remark

### Herrings — believed at the time, overturned later

#### `g8.r2.detail-passthrough-1` — herring

**dario**, 2025-01-31, #engineering

> for what it's worth the rest of 427 reads fine to me, detail passes through exactly as written, we render the caller's string and let the provider decide what counts as valid

*A herring: stated as settled at the time, overturned later (from 2025-03-21).*

*Drafted as:* detail passes through exactly as written; we render the caller's string and let the provider decide what counts as valid.

*Why there:* That day ends with dario doing the review pass on PR 427 that emil kept asking for, and reporting what he found in the multimodal path — he names the undefined non-multimodal-provider fallback as the one blocker. A note that the image `detail` field is forwarded verbatim, with no validation on our side, is exactly the other half of that pass: the part he checked and is not worried about. It complicates nothing already said (nobody has mentioned detail), it comes from the person who owns the call, and emil's 18:24 reply still lands on the fallback item.

*Goes into the real conversation in #engineering on 2025-01-31, after 18:05 dario:*

```
09:00  nikolai: Wrote up the postmortem for the v0.1.17.post1 hotfix on the wiki, "Postmortem: v0.1.17.post1 hotfix" under postmortems. Short version: the executor me
09:37  dermot: pr 428 and 429 consolidate the cost interface to single call path, partly for exactly that reason, fewer places for a rename to go unnoticed.
10:15  nikolai: Are we still targeting PR 427 to land this week, or is that moving to v0.1.18?
10:22  nikolai: Did the executor rename cause any breakage on your end, or did it land cleanly across the board?
11:04  dermot: cost consolidation is done on my end, pr 428 and pr 429 both in
11:04  dermot: executor rename didnt touch anything I own, all llm side
12:19  emil: Clean on my end too.
12:31  emil: PR 427, are we landing it this week or punting to v0.1.18?
12:39  dermot: simplellm consolidation is done, interface is clean on my end
12:41  emil: WS-028 isn't on the wiki yet, Dermot, when is it going up, and does it cover the CI picture for my part?
15:26  nikolai: sorry, was away for a bit, good to hear the executor rename landed clean on all sides, that confirms what i needed.
15:31  emil: Still waiting on a call for PR 427, this week or v0.1.18?
15:58  dario: I'm around for the next hour or so if someone wants to go through PR 427 and make the call before we're done for the week.
16:00  emil: @Dario I'm around
16:00  emil: Does it need review before we can make the call, or can we decide now based on where it sits?
16:11  dermot: pr 428 and 429 are confirmed clean, no regressions on the cost interface.
16:54  emil: @Dermot, WS-028 still isn't on the wiki, is that going up today, or is it carrying to next week?
17:32  dario: Nikolai's postmortem on the wiki (Postmortem: v0.1.17.post1 hotfix) is worth having in front of you for the PR 427 call if you haven't read it yet
17:32  nikolai: erm, which part are you thinking applies to 427 specifically?
17:32  dario: honestly, I hadn't read it yet when I posted that, I was going on what Nikolai summarized earlier. ignore it
17:36  emil: It's end of day Friday, can we just make the call on PR 427 now, land it or defer it to v0.1.18?
18:05  dario: PR 427 has no defined behavior when a non-multimodal provider receives multimodal input, so right now it's a silent failure path
18:05  dario: That's the specific thing that needs to land before I'd be comfortable merging it   <-- THE REMARK GOES HERE
18:24  emil: Got it, I'll handle the provider fallback and get it back to you for another look.
```

#### `g8.r2.detail-passthrough-2` — herring

**konrad**, 2025-02-13, #general

> Right, so no allowlist on detail then, its the caller's string and we just forward it. validating provider enums is not our job.

*A herring: stated as settled at the time, overturned later (from 2025-03-21).*

*Drafted as:* Right, no allowlist on detail. It's the caller's string, we just forward it — validating provider enums is not our job.

*Why there:* The remark settles a review decision about the multimodal message schema — whether the image `detail` string gets checked against a fixed set of provider values. None of the listed rooms is chewing on that. The two #code-review days are about batch request counting / README wording (Feb 13) and uid behavior in PR 547 plus the cost estimation chunk in PR 546 (Feb 26); #engineering Jan 27 and Feb 17 are param routing and release planning; the two #cookbooks days do touch PR 571, but only as "is the RAFT block API shape locked" and "what's the starting point for the finetuning example" — nobody there is reading the schema field by field, and a validation call landing in the examples room would change the subject. The place this belongs is the actual review pass on PR 571, which Emil explicitly asked for ("I'd really like a second set of eyes on the schema shape before anything else builds on top of it") and which Konrad said he'd answer with a yes/no on whether it wants another pass. That review happens in #code-review, the day after that ask.

*A new conversation in #general on 2025-02-13:*

```
13:38  gideon: whats the plan on detail, do we check the string before we send it or just pass it along
13:40  konrad: pass it along. its the callers string, not ours
13:41  gideon: ya but if they put garbage in there we only find out from the provider side
13:42  emil: so you're saying we'd be keeping a copy of their enum in sync with them? honestly that sounds like the worse deal
13:44  konrad: mhm, and its work we lose every time they add a value to it
13:45  gideon: so nothing on our end holds a set of accepted values at all
13:46  konrad: right, so no allowlist on detail then. we just forward what we got, validating provider enums is not our job anyway
```

#### `g8.r2.rev1` — failure_behavior

**dario**, 2025-04-18, #incidents

> typo'd "hgih" 400'd a run mid-flight, so block-build now runs normalize_detail and falls back to "auto" with one warning instead of forwarding it untouched. Image.detail is left alone.

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* forwarding the caller's detail string untouched is gone — a typo'd "hgih" 400'd a run mid-flight. block-build now runs normalize_detail and falls back to "auto" with one warning; Image.detail still keeps whatever the caller wrote.

*Why there:* The remark is request-layer/provider-backend work: an image block's caller-supplied detail value, a provider 400 mid-run, and normalization at block-build time. None of the seven threads is discussing message construction or provider request payloads. The nearest, #releases 2025-03-24, has dario posting openai-backend PR status, but that room is settling validator offline behaviour and has just agreed on hard failure over warn-and-continue — a fix that warns once and substitutes "auto" would read as contradicting the call they just made rather than contributing to it. The other six (executor image defaults, viewer progress tables, cookbook reattach keying, .choices migration, PR backlog triage) share no subject at all. #pipeline is the room for this and has no candidate conversation.

*Must appear literally:* `normalize_detail`, `Image.detail`, `auto`

*A new conversation in #incidents on 2025-04-18:*

```
15:31  dermot: the run that 400'd this morning - detail was spelled "hgih" in the config. went out to the provider exactly like that and fell over mid flight
15:33  gideon: oof. so basically nothing looks at that string at all before it leaves?
15:34  dermot: no, and that was deliberate. the call in 427 was detail passes through exactly as written, we render the caller's string and let the provider decide what counts as valid
15:36  dario: yeah that one is dead now to be honest. losing a run halfway through to a two letter swap isnt a trade i want to keep making
15:37  dario: block-build runs it through normalize_detail on the way out instead of forwarding it untouched
15:38  gideon: and when it doesnt normalize to anything? do we raise there or um
15:40  dario: no, falls back to auto. one warning and it carrys on, i'd rather the run finishes
15:41  dermot: so Image.detail picks up the same handling, is that the read
15:42  dario: no, Image.detail is left alone. just the block build path
```

> **Problems:** longer than one remark

#### `g8.r2.rev2` — failure_behavior

**konrad**, 2025-04-29, #general

> Look, "no allowlist on detail" is dead, I burned an hour on detail="HIGH" coming back as auto. normalize_detail strips and lowercases against _SUPPORTED_IMAGE_DETAILS now, so "HIGH" lands as "high" and anything off the list becomes "auto".

*A herring: stated as settled at the time, overturned later (from ?).*

*Drafted as:* Look, "no allowlist on detail" is dead — I burned an hour on detail="HIGH" coming back as auto. normalize_detail strips and lowercases against _SUPPORTED_IMAGE_DETAILS now, so "HIGH" lands as "high" and anything off the list becomes "auto".

*Why there:* None of the eight fits. Seven are PR-shepherding, release-cut, or viewer-render threads; the one adjacent-sounding thread (2026-01-23) is konrad checking Claude 4.x model identifier strings in finetuning against Anthropic's docs, not request-payload field normalization, and nikolai's live question there is doc accuracy. 2025-05-23 mentions "OpenAI-compatible response format" but that is the response shape, and the open question is compat testing. This remark reverses a prior "don't validate detail, pass it through" decision about image attachment payloads, which is request-layer/provider-backend territory — #pipeline. It needs the room where that original call was made, otherwise it lands as a stranger overturning a decision nobody present remembers making.

*Must appear literally:* `normalize_detail`, `_SUPPORTED_IMAGE_DETAILS`, `auto`, `high`

*A new conversation in #general on 2025-04-29:*

```
14:31  dermot: konrad, the detail field on image content, thats still passed through untouched yeah
14:32  konrad: it was. look, "no allowlist on detail, its the callers string" is dead
14:32  konrad: i burned an hour on detail="HIGH" comming back as auto
14:34  dermot: mhm, and validating provider enums is not our job was the whole argument for leaving it alone
14:35  emil: honestly that argument held right up until the casing bit us. "HIGH" isnt an invalid enum, its our enum with a shift key
14:37  konrad: right exactly. so normalize_detail strips it and lowercases it first, "HIGH" lands as high
14:38  dermot: and a value thats not in the vocabulary at all, does that one still get forwarded
14:40  konrad: no. it goes against _SUPPORTED_IMAGE_DETAILS and anything off the list becomes auto. none of it is typed yet, presumably it rides along with whatever ticket the content block stuff is on
14:41  emil: yup. so the caller with a typo gets auto instead of a 400 from the provider, sounds right to me
```

> **Problems:** longer than one remark

